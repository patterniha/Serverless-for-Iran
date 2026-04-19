#!/usr/bin/env bash
# Privacy-safe path diagnostics for censorship/debug scenarios.
# Usage: scripts/diagnose_path.sh [hostname]

set -u

TARGET="${1:-github.com}"
PORT="${PORT:-443}"
WORKDIR="$(mktemp -d 2>/dev/null || mktemp -d -t diagnose-path)"
RAW_LOG="$WORKDIR/diagnose-raw.log"
CURL_LOG="$WORKDIR/curl-http1.log"
OPENSSL_LOG="$WORKDIR/openssl-host.log"

cleanup() {
  :
}
trap cleanup EXIT

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

run_timeout() {
  local seconds="$1"
  shift
  if have_cmd timeout; then
    timeout "${seconds}s" "$@"
  else
    "$@"
  fi
}

trim_join_csv() {
  awk 'NF' | awk '!seen[$0]++' | paste -sd ',' -
}

csv_or_unknown() {
  local value
  value="$(printf '%s\n' "$1" | trim_join_csv)"
  if [ -z "$value" ]; then
    echo "unknown"
  else
    echo "$value"
  fi
}

dns_query() {
  local resolver="$1"
  local qtype="$2"

  if have_cmd dig; then
    if [ -n "$resolver" ]; then
      dig +time=3 +tries=1 +short @"$resolver" "$TARGET" "$qtype" 2>/dev/null | awk 'NF'
    else
      dig +time=3 +tries=1 +short "$TARGET" "$qtype" 2>/dev/null | awk 'NF'
    fi
    return
  fi

  if have_cmd nslookup; then
    if [ -n "$resolver" ]; then
      nslookup -type="$qtype" "$TARGET" "$resolver" 2>/dev/null | awk '/^Address: /{print $2}'
    else
      nslookup -type="$qtype" "$TARGET" 2>/dev/null | awk '/^Address: /{print $2}'
    fi
    return
  fi

  if have_cmd host; then
    if [ "$qtype" = "A" ]; then
      host "$TARGET" 2>/dev/null | awk '/has address/{print $NF}'
    else
      host "$TARGET" 2>/dev/null | awk '/has IPv6 address/{print $NF}'
    fi
  fi
}

extract_first_cert() {
  local input_file="$1"
  local output_file="$2"
  awk '
    /-----BEGIN CERTIFICATE-----/ {in_cert=1}
    in_cert {print}
    /-----END CERTIFICATE-----/ {exit}
  ' "$input_file" >"$output_file"
  if ! grep -q "BEGIN CERTIFICATE" "$output_file"; then
    return 1
  fi
  return 0
}

list_intersection() {
  local left="$1"
  local right="$2"
  comm -12 \
    <(printf '%s\n' "$left" | awk 'NF' | sort -u) \
    <(printf '%s\n' "$right" | awk 'NF' | sort -u)
}

DATE_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
HOST_OS="$(uname -a 2>/dev/null || echo unknown)"
CURL_VER="$(curl --version 2>/dev/null | head -n1 || echo unavailable)"
OPENSSL_VER="$(openssl version 2>/dev/null || echo unavailable)"

A_SYSTEM="$(dns_query "" A)"
AAAA_SYSTEM="$(dns_query "" AAAA)"
A_CF="$(dns_query "1.1.1.1" A)"
AAAA_CF="$(dns_query "1.1.1.1" AAAA)"
A_GOOGLE="$(dns_query "8.8.8.8" A)"
AAAA_GOOGLE="$(dns_query "8.8.8.8" AAAA)"
A_QUAD9="$(dns_query "9.9.9.9" A)"
AAAA_QUAD9="$(dns_query "9.9.9.9" AAAA)"

A_PUBLIC="$(printf '%s\n%s\n%s\n' "$A_CF" "$A_GOOGLE" "$A_QUAD9" | awk 'NF' | awk '!seen[$0]++')"
A_INTERSECTION="$(list_intersection "$A_SYSTEM" "$A_PUBLIC")"

# curl HTTP/1.1 diagnostic (checks renegotiation signals in verbose output)
CURL_HTTP_CODE="unknown"
CURL_CONNECTED_IP="unknown"
CURL_RENEG_COUNT="0"
CURL_ALPN="unknown"
CURL_STATUS="fail"

if have_cmd curl; then
  if run_timeout 20 curl -sS -o /dev/null -D "$WORKDIR/headers-http1.txt" -I -v --http1.1 --connect-timeout 8 --max-time 15 "https://$TARGET" 2>"$CURL_LOG"; then
    CURL_STATUS="ok"
  fi

  CURL_HTTP_CODE="$(awk 'toupper($1) ~ /^HTTP\// {code=$2} END{if(code) print code; else print "unknown"}' "$WORKDIR/headers-http1.txt" 2>/dev/null)"
  CURL_CONNECTED_IP="$(sed -nE 's/^\* Connected to [^ ]+ \(([0-9a-fA-F:.]+)\).*/\1/p' "$CURL_LOG" | head -n1)"
  if [ -z "$CURL_CONNECTED_IP" ]; then
    CURL_CONNECTED_IP="$(sed -nE 's/^\* +Trying ([0-9a-fA-F:.]+)\.\.\./\1/p' "$CURL_LOG" | head -n1)"
  fi
  [ -z "$CURL_CONNECTED_IP" ] && CURL_CONNECTED_IP="unknown"
  CURL_RENEG_COUNT="$(awk 'BEGIN{c=0} tolower($0) ~ /renegotiat/ {c++} END{print c}' "$CURL_LOG" 2>/dev/null)"
  CURL_ALPN="$(awk '
    /ALPN:/ {line=$0}
    END {
      if (line) {
        sub(/^.*ALPN:[[:space:]]*/, "", line)
        print line
      } else {
        print "unknown"
      }
    }
  ' "$CURL_LOG" 2>/dev/null)"
fi

# openssl handshake and certificate checks
TLS_VERIFY_CODE="unknown"
CERT_SUBJECT="unknown"
CERT_ISSUER="unknown"
CERT_SHA256="unknown"
CERT_SAN="unknown"
CERT_HOST_MATCH="unknown"

if have_cmd openssl; then
  run_timeout 20 sh -c "printf '' | openssl s_client -servername '$TARGET' -connect '$TARGET:$PORT' -showcerts" >"$OPENSSL_LOG" 2>&1 || true

  TLS_VERIFY_CODE="$(awk -F': ' '/Verify return code/ {code=$2} END{if(code) print code; else print "unknown"}' "$OPENSSL_LOG")"

  CERT_FILE="$WORKDIR/leaf.pem"
  if extract_first_cert "$OPENSSL_LOG" "$CERT_FILE"; then
    CERT_SUBJECT="$(openssl x509 -in "$CERT_FILE" -noout -subject 2>/dev/null | sed 's/^subject=//')"
    CERT_ISSUER="$(openssl x509 -in "$CERT_FILE" -noout -issuer 2>/dev/null | sed 's/^issuer=//')"
    CERT_SHA256="$(openssl x509 -in "$CERT_FILE" -noout -fingerprint -sha256 2>/dev/null | sed 's/^[^=]*=//')"
    CERT_SAN="$(openssl x509 -in "$CERT_FILE" -noout -ext subjectAltName 2>/dev/null | tail -n +2 | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' | sed 's/^ //;s/ $//')"

    if openssl x509 -in "$CERT_FILE" -noout -checkhost "$TARGET" >/dev/null 2>&1; then
      CERT_HOST_MATCH="yes"
    else
      CERT_HOST_MATCH="no"
    fi
  fi
fi

# Per-IP TLS probe (IPv4 only for portability)
IP_TLS_NOTES=""
CANDIDATE_V4="$(printf '%s\n%s\n%s\n%s\n' "$A_SYSTEM" "$A_CF" "$A_GOOGLE" "$A_QUAD9" | awk '/^[0-9]+\./' | awk '!seen[$0]++' | head -n 4)"

if [ -n "$CANDIDATE_V4" ] && have_cmd openssl; then
  while IFS= read -r ip; do
    [ -z "$ip" ] && continue

    IP_LOG="$WORKDIR/openssl-ip-$ip.log"
    run_timeout 12 sh -c "printf '' | openssl s_client -servername '$TARGET' -connect '$ip:$PORT' -showcerts" >"$IP_LOG" 2>&1 || true

    ip_verify="$(awk -F': ' '/Verify return code/ {code=$2} END{if(code) print code; else print "unknown"}' "$IP_LOG")"

    ip_cert="$WORKDIR/leaf-ip-$ip.pem"
    ip_host_match="unknown"
    if extract_first_cert "$IP_LOG" "$ip_cert"; then
      if openssl x509 -in "$ip_cert" -noout -checkhost "$TARGET" >/dev/null 2>&1; then
        ip_host_match="yes"
      else
        ip_host_match="no"
      fi
    fi

    IP_TLS_NOTES="${IP_TLS_NOTES}\n- ${ip}: verify='${ip_verify}', host_match='${ip_host_match}'"
  done <<<"$CANDIDATE_V4"
fi

WARNINGS=""

if [ -n "$A_SYSTEM" ] && [ -n "$A_PUBLIC" ] && [ -z "$A_INTERSECTION" ]; then
  WARNINGS="${WARNINGS}\n- System DNS A answers do not overlap with public resolver answers (possible DNS tamper/rewriting)."
fi

if [ "$CURL_RENEG_COUNT" -gt 0 ] 2>/dev/null; then
  WARNINGS="${WARNINGS}\n- curl verbose output includes TLS renegotiation signals (${CURL_RENEG_COUNT} occurrences)."
fi

if [ "$CERT_HOST_MATCH" = "no" ]; then
  WARNINGS="${WARNINGS}\n- TLS certificate does not match requested hostname."
fi

if [ "$TARGET" = "github.com" ] && printf '%s\n' "$A_SYSTEM" | awk 'NF' | grep -Eqv '^140\.82\.'; then
  WARNINGS="${WARNINGS}\n- github.com resolved to non-140.82.x.x IPv4 on system resolver (heuristic warning; verify with multiple resolvers)."
fi

if [ -z "$WARNINGS" ]; then
  WARNINGS="\n- No high-confidence anomaly detected by this script."
fi

{
  echo "=== Raw diagnostics ($DATE_UTC) ==="
  echo "target=$TARGET"
  echo "curl_status=$CURL_STATUS"
  echo "curl_http_code=$CURL_HTTP_CODE"
  echo "curl_connected_ip=$CURL_CONNECTED_IP"
  echo "curl_reneg_count=$CURL_RENEG_COUNT"
  echo "tls_verify_code=$TLS_VERIFY_CODE"
  echo "cert_host_match=$CERT_HOST_MATCH"
  echo "A_system=$(csv_or_unknown "$A_SYSTEM")"
  echo "A_cf=$(csv_or_unknown "$A_CF")"
  echo "A_google=$(csv_or_unknown "$A_GOOGLE")"
  echo "A_quad9=$(csv_or_unknown "$A_QUAD9")"
} >"$RAW_LOG"

cat <<EOF
Path diagnostics completed.
Raw local log: $RAW_LOG

## Quick Summary
- Target: $TARGET:$PORT
- Time (UTC): $DATE_UTC
- curl status/code: $CURL_STATUS / $CURL_HTTP_CODE
- curl connected IP: $CURL_CONNECTED_IP
- HTTP ALPN signal: $CURL_ALPN
- TLS renegotiation markers (curl): $CURL_RENEG_COUNT
- TLS verify code (openssl): $TLS_VERIFY_CODE
- Certificate hostname match: $CERT_HOST_MATCH

## DNS Results (A)
- System: $(csv_or_unknown "$A_SYSTEM")
- Cloudflare (1.1.1.1): $(csv_or_unknown "$A_CF")
- Google (8.8.8.8): $(csv_or_unknown "$A_GOOGLE")
- Quad9 (9.9.9.9): $(csv_or_unknown "$A_QUAD9")

## DNS Results (AAAA)
- System: $(csv_or_unknown "$AAAA_SYSTEM")
- Cloudflare (1.1.1.1): $(csv_or_unknown "$AAAA_CF")
- Google (8.8.8.8): $(csv_or_unknown "$AAAA_GOOGLE")
- Quad9 (9.9.9.9): $(csv_or_unknown "$AAAA_QUAD9")

## Certificate Snapshot
- Subject: $CERT_SUBJECT
- Issuer: $CERT_ISSUER
- SHA256: $CERT_SHA256
- SAN: $CERT_SAN

## Per-IP TLS Probe (IPv4)
$(printf '%b\n' "$IP_TLS_NOTES" | awk 'NF' || true)

## Heuristic Warnings
$(printf '%b\n' "$WARNINGS" | awk 'NF')

## Privacy-Safe Report (copy/paste)
### Result
- Works / Partly works / Does not work:
- Tested date (UTC): $DATE_UTC
- Approx region (province/city only):
- ISP/operator:
- Network: mobile data / home ISP / workplace / unknown
- IPv6 available: yes / no / unknown
- Client app:
- Xray-core version:
- Profile name:
- Host tested: $TARGET
- curl status/code: $CURL_STATUS / $CURL_HTTP_CODE
- Connected IP seen by curl: $CURL_CONNECTED_IP
- DNS A (system/cf/google/quad9): $(csv_or_unknown "$A_SYSTEM") / $(csv_or_unknown "$A_CF") / $(csv_or_unknown "$A_GOOGLE") / $(csv_or_unknown "$A_QUAD9")
- TLS verify code: $TLS_VERIFY_CODE
- Certificate hostname match: $CERT_HOST_MATCH
- TLS renegotiation markers: $CURL_RENEG_COUNT
- Failure type: DNS fails / TLS handshake fails / browser fails / app fails / slow / disconnect / battery-heat
- Notes:

### Do not include
- Full IP address of your own device
- Phone number
- Personal account handles
- Exact home/work location
- Screenshots with personal data
- Full device identifiers
EOF
