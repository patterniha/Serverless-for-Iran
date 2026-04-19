#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence, Set, Tuple

import json5


ROOT = Path(__file__).resolve().parent
OUTPUT_CURATED = ROOT / "Subscription" / "Serverless-for-Iran.json"
OUTPUT_FULL = ROOT / "Subscription" / "Serverless-for-Iran-full.json"
OUTPUT_MANIFEST = ROOT / "Subscription" / "profiles-manifest.json"

BASE_CONFIGS: Sequence[str] = (
    "Serverless.jsonc",
    "Serverless-dynx.jsonc",
    "Serverless-shatel.jsonc",
    "Serverless-vanilla.jsonc",
    "Serverless-zeus.jsonc",
)
PRIMARY_CURATED_BASE = "Serverless.jsonc"

# Valid-fragment profiles (no invalid-checksum dependency).
FRAGMENT_PROFILES: Sequence[Tuple[str, Dict[str, str]]] = (
    (
        "natA-tlshello-small",
        {
            "packets": "tlshello",
            "length": "4-12",
            "interval": "0",
            "maxSplit": "32",
        },
    ),
    (
        "natB-stream-small",
        {
            "packets": "1-2",
            "length": "2-24",
            "interval": "1-8",
            "maxSplit": "96",
        },
    ),
    (
        "mobile-soft",
        {
            "packets": "tlshello",
            "length": "16-48",
            "interval": "8-24",
            "maxSplit": "8",
        },
    ),
    (
        "skip-soft",
        {
            "packets": "1-1",
            "length": "64-160",
            "interval": "120-620",
            "maxSplit": "4",
        },
    ),
    (
        "legacy-v41",
        {
            "packets": "1-1",
            "length": "1",
            "interval": "4",
            "maxSplit": "517",
        },
    ),
)

UDP_MODE_HELP: Dict[str, str] = {
    "quic-block": "Block QUIC/UDP443 so apps may fall back to TCP/TLS",
    "udp-light": "Light UDP noise",
    "udp-heavy": "Heavy UDP noise; lab only",
}
UDP_MODES: Sequence[str] = tuple(UDP_MODE_HELP.keys())

# Keep default subscription small and compatibility-oriented.
CURATED_MATRIX: Sequence[Tuple[str, str, str]] = (
    ("natA-tlshello-small", "quic-block", "cf"),
    ("natA-tlshello-small", "udp-light", "cf"),
    ("natB-stream-small", "quic-block", "google"),
    ("natB-stream-small", "udp-light", "quad9"),
    ("mobile-soft", "quic-block", "cf"),
    ("mobile-soft", "udp-light", "google"),
    ("skip-soft", "quic-block", "quad9"),
    ("legacy-v41", "quic-block", "cf"),
)

DNS_PROFILES: Dict[str, Dict[str, Any]] = {
    "cf": {
        "address": "https://cloudflare-dns.com/dns-query",
        "hosts": {
            "cloudflare-dns.com": [
                "1.1.1.1",
                "1.0.0.1",
                "2606:4700:4700::1111",
                "2606:4700:4700::1001",
            ]
        },
    },
    "google": {
        "address": "https://dns.google/dns-query",
        "hosts": {
            "dns.google": [
                "8.8.8.8",
                "8.8.4.4",
                "2001:4860:4860::8888",
                "2001:4860:4860::8844",
            ]
        },
    },
    "quad9": {
        "address": "https://dns.quad9.net/dns-query",
        "hosts": {
            "dns.quad9.net": [
                "9.9.9.9",
                "149.112.112.112",
                "2620:fe::fe",
                "2620:fe::9",
            ]
        },
    },
}
DNS_MODES: Sequence[str] = tuple(DNS_PROFILES.keys())
DNS_HOST_KEYS: Set[str] = {
    host for profile in DNS_PROFILES.values() for host in profile["hosts"].keys()
}

JsonObject = MutableMapping[str, Any]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_json5(path: Path) -> JsonObject:
    if not path.exists():
        fail(f"Missing config file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json5.load(file)
    except Exception as exc:
        fail(f"Could not parse {path}: {exc}")

    if not isinstance(data, dict):
        fail(f"{path} must contain a JSON object at top-level")

    return data


def profile_name(config: JsonObject) -> str:
    remarks = config.get("remarks")
    if isinstance(remarks, str) and remarks.strip():
        return remarks.strip()
    return "Serverless"


def get_outbounds(config: JsonObject) -> List[JsonObject]:
    outbounds = config.get("outbounds")
    if not isinstance(outbounds, list):
        fail(f"{profile_name(config)} has no outbounds array")
    return outbounds


def get_routing_rules(config: JsonObject) -> List[JsonObject]:
    routing = config.get("routing")
    if routing is None:
        return []
    if not isinstance(routing, dict):
        fail(f"{profile_name(config)} routing must be an object")

    rules = routing.get("rules")
    if rules is None:
        return []
    if not isinstance(rules, list):
        fail(f"{profile_name(config)} routing.rules must be an array")
    return rules


def require_dns(config: JsonObject) -> JsonObject:
    dns = config.get("dns")
    if not isinstance(dns, dict):
        fail(f"{profile_name(config)} dns must be an object")

    hosts = dns.setdefault("hosts", {})
    if not isinstance(hosts, dict):
        fail(f"{profile_name(config)} dns.hosts must be an object")

    servers = dns.setdefault("servers", [])
    if not isinstance(servers, list):
        fail(f"{profile_name(config)} dns.servers must be an array")

    return dns


def get_dns_servers(config: JsonObject) -> List[JsonObject]:
    dns = require_dns(config)
    servers = dns["servers"]
    if not isinstance(servers, list):
        fail(f"{profile_name(config)} dns.servers must be an array")
    return servers


def find_outbound(config: JsonObject, tag: str) -> Optional[JsonObject]:
    for outbound in get_outbounds(config):
        if isinstance(outbound, dict) and outbound.get("tag") == tag:
            return outbound
    return None


def require_outbound(config: JsonObject, tag: str) -> JsonObject:
    outbound = find_outbound(config, tag)
    if outbound is None:
        fail(f"{profile_name(config)} missing outbound {tag!r}")
    return outbound


def require_dns_server(config: JsonObject, tag: str) -> JsonObject:
    for server in get_dns_servers(config):
        if isinstance(server, dict) and server.get("tag") == tag:
            return server
    fail(f"{profile_name(config)} missing dns server {tag!r}")


def set_remarks(config: JsonObject, suffix: str) -> None:
    config["remarks"] = f"{profile_name(config)}-{suffix}"


def set_full_fragment(config: JsonObject, fragment: Dict[str, str]) -> None:
    outbound = require_outbound(config, "full-fragment")
    settings = outbound.setdefault("settings", {})
    if not isinstance(settings, dict):
        fail(f"{profile_name(config)} full-fragment settings must be an object")
    settings["fragment"] = dict(fragment)


def set_udp_light(config: JsonObject) -> None:
    udp_noises = require_outbound(config, "udp-noises")
    settings = udp_noises.setdefault("settings", {})
    if not isinstance(settings, dict):
        fail(f"{profile_name(config)} udp-noises settings must be an object")

    settings["noises"] = [
        {
            "type": "rand",
            "packet": "96-384",
            "delay": "2-12",
            "applyTo": "ipv4",
        },
        {
            "type": "rand",
            "packet": "96-320",
            "delay": "2-16",
            "applyTo": "ipv6",
        },
    ]


def keep_udp_heavy(config: JsonObject) -> None:
    require_outbound(config, "udp-noises")


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def rule_targets_quic_or_udp443(rule: JsonObject) -> bool:
    network = str(rule.get("network", "")).lower()
    port = str(rule.get("port", "")).strip()
    protocols = {str(item).lower() for item in as_list(rule.get("protocol"))}
    return network == "udp" and (port == "443" or "quic" in protocols)


def block_quic_udp443(config: JsonObject) -> None:
    require_outbound(config, "block-out")

    changed = 0
    for rule in get_routing_rules(config):
        if not isinstance(rule, dict):
            continue
        if rule.get("outboundTag") != "udp-noises":
            continue
        if rule_targets_quic_or_udp443(rule):
            rule["outboundTag"] = "block-out"
            changed += 1

    if changed == 0:
        fail(f"{profile_name(config)} quic-block mode found no QUIC/UDP443 udp-noises rule")


def apply_udp_mode(config: JsonObject, mode: str) -> None:
    if mode == "quic-block":
        block_quic_udp443(config)
        return
    if mode == "udp-light":
        set_udp_light(config)
        return
    if mode == "udp-heavy":
        keep_udp_heavy(config)
        return
    fail(f"Unknown UDP mode {mode!r}")


def apply_dns_mode(config: JsonObject, mode: str) -> None:
    profile = DNS_PROFILES.get(mode)
    if profile is None:
        fail(f"Unknown DNS mode {mode!r}")

    dns = require_dns(config)
    hosts = dns["hosts"]
    if not isinstance(hosts, dict):
        fail(f"{profile_name(config)} dns.hosts must be an object")

    no_filter_dns = require_dns_server(config, "no-filter-dns")
    no_filter_dns["address"] = profile["address"]
    no_filter_dns["finalQuery"] = True

    for stale_host in DNS_HOST_KEYS:
        hosts.pop(stale_host, None)
    hosts.update(profile["hosts"])


def outbound_tags(config: JsonObject) -> Set[str]:
    tags: Set[str] = set()
    for outbound in get_outbounds(config):
        tag = outbound.get("tag")
        if isinstance(tag, str) and tag:
            tags.add(tag)
    return tags


def validate_profile(config: JsonObject) -> None:
    name = profile_name(config)
    tags = outbound_tags(config)
    if not tags:
        fail(f"{name} has no outbound tags")

    for index, rule in enumerate(get_routing_rules(config), start=1):
        outbound_tag = rule.get("outboundTag")
        if isinstance(outbound_tag, str) and outbound_tag not in tags:
            fail(f"{name} routing.rules[{index}] outboundTag {outbound_tag!r} not found")

    inbounds = config.get("inbounds")
    if inbounds is not None and not isinstance(inbounds, list):
        fail(f"{name} inbounds must be an array")

    dns = config.get("dns")
    if dns is not None and not isinstance(dns, dict):
        fail(f"{name} dns must be an object")


def deduplicate_by_remarks(configs: Iterable[JsonObject]) -> List[JsonObject]:
    seen: Set[str] = set()
    result: List[JsonObject] = []

    for config in configs:
        remarks = profile_name(config)
        if remarks in seen:
            fail(f"Duplicate remarks detected: {remarks}")
        seen.add(remarks)
        result.append(config)

    return result


def build_variant(
    base_config: JsonObject,
    fragment_name: str,
    fragment_settings: Dict[str, str],
    udp_mode: str,
    dns_mode: str,
) -> JsonObject:
    variant = copy.deepcopy(base_config)
    set_remarks(variant, f"{fragment_name}-{udp_mode}-{dns_mode}")
    set_full_fragment(variant, fragment_settings)
    apply_udp_mode(variant, udp_mode)
    apply_dns_mode(variant, dns_mode)
    validate_profile(variant)
    return variant


def write_json(path: Path, data: List[JsonObject]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def get_manifest_profile_hints(
    fragment_name: str,
    udp_mode: str,
    dns_mode: str,
) -> Tuple[List[str], List[str]]:
    good_for: List[str] = ["browser"]
    avoid_if: List[str] = []

    if udp_mode == "quic-block":
        good_for.extend(["android-apps-that-fallback-to-tcp", "restricted-quic-paths"])
        avoid_if.extend(["app-requires-quic", "gaming", "voip"])
    elif udp_mode == "udp-light":
        good_for.extend(["mobile-data", "mixed-app-traffic"])
        avoid_if.append("udp-sensitive-apps")
    else:
        good_for.append("lab-testing")
        avoid_if.extend(["normal-daily-use", "battery-sensitive"])

    if fragment_name == "mobile-soft":
        good_for.extend(["battery-sensitive", "lossy-mobile-networks"])
    if fragment_name == "legacy-v41":
        avoid_if.append("first-choice")

    if dns_mode in {"google", "quad9"}:
        good_for.append("doh-diversity")

    return sorted(set(good_for)), sorted(set(avoid_if))


def make_manifest_entry(
    remarks: str,
    tier: str,
    fragment_name: str,
    udp_mode: str,
    dns_mode: str,
) -> Dict[str, Any]:
    good_for, avoid_if = get_manifest_profile_hints(fragment_name, udp_mode, dns_mode)
    return {
        "remarks": remarks,
        "tier": tier,
        "fragment": fragment_name,
        "udp": udp_mode,
        "dns": dns_mode,
        "good_for": good_for,
        "avoid_if": avoid_if,
    }


def make_base_manifest_entry(remarks: str) -> Dict[str, Any]:
    return {
        "remarks": remarks,
        "tier": "compatibility",
        "fragment": "legacy-base",
        "udp": "as-is",
        "dns": "as-is",
        "good_for": ["backward-compatibility"],
        "avoid_if": ["first-choice"],
    }


def upsert_manifest(
    manifest_by_remarks: Dict[str, Dict[str, Any]],
    entry: Dict[str, Any],
) -> None:
    tier_priority = {"default": 0, "compatibility": 1, "lab": 2}
    remarks = entry["remarks"]

    existing = manifest_by_remarks.get(remarks)
    if existing is None:
        manifest_by_remarks[remarks] = entry
        return

    existing_priority = tier_priority.get(str(existing.get("tier")), 10)
    new_priority = tier_priority.get(str(entry.get("tier")), 10)
    if new_priority < existing_priority:
        manifest_by_remarks[remarks] = entry


def main() -> None:
    full_profiles: List[JsonObject] = []
    curated_profiles: List[JsonObject] = []
    manifest_by_remarks: Dict[str, Dict[str, Any]] = {}

    fragment_map = {name: settings for name, settings in FRAGMENT_PROFILES}
    base_by_filename: Dict[str, JsonObject] = {}

    for filename in BASE_CONFIGS:
        base_path = ROOT / filename
        base = load_json5(base_path)
        validate_profile(base)
        base_by_filename[filename] = base

    if PRIMARY_CURATED_BASE not in base_by_filename:
        fail(f"Missing PRIMARY_CURATED_BASE {PRIMARY_CURATED_BASE!r}")

    # Keep original base profiles in both outputs for compatibility.
    for filename in BASE_CONFIGS:
        base = base_by_filename[filename]
        base_copy_for_full = copy.deepcopy(base)
        base_copy_for_curated = copy.deepcopy(base)

        full_profiles.append(base_copy_for_full)
        curated_profiles.append(base_copy_for_curated)
        upsert_manifest(manifest_by_remarks, make_base_manifest_entry(profile_name(base)))

    # Full matrix for lab/advanced testing.
    for filename in BASE_CONFIGS:
        base = base_by_filename[filename]
        for fragment_name, fragment_settings in FRAGMENT_PROFILES:
            for udp_mode in UDP_MODES:
                for dns_mode in DNS_MODES:
                    variant = build_variant(
                        base_config=base,
                        fragment_name=fragment_name,
                        fragment_settings=fragment_settings,
                        udp_mode=udp_mode,
                        dns_mode=dns_mode,
                    )
                    remarks = profile_name(variant)
                    full_profiles.append(variant)
                    upsert_manifest(
                        manifest_by_remarks,
                        make_manifest_entry(
                            remarks=remarks,
                            tier="lab",
                            fragment_name=fragment_name,
                            udp_mode=udp_mode,
                            dns_mode=dns_mode,
                        ),
                    )

    # Small curated defaults from primary base only.
    curated_base = base_by_filename[PRIMARY_CURATED_BASE]
    for fragment_name, udp_mode, dns_mode in CURATED_MATRIX:
        if fragment_name not in fragment_map:
            fail(f"CURATED_MATRIX uses unknown fragment profile {fragment_name!r}")

        variant = build_variant(
            base_config=curated_base,
            fragment_name=fragment_name,
            fragment_settings=fragment_map[fragment_name],
            udp_mode=udp_mode,
            dns_mode=dns_mode,
        )
        remarks = profile_name(variant)
        curated_profiles.append(variant)
        upsert_manifest(
            manifest_by_remarks,
            make_manifest_entry(
                remarks=remarks,
                tier="default",
                fragment_name=fragment_name,
                udp_mode=udp_mode,
                dns_mode=dns_mode,
            ),
        )

    full_profiles = deduplicate_by_remarks(full_profiles)
    curated_profiles = deduplicate_by_remarks(curated_profiles)

    manifest = sorted(
        manifest_by_remarks.values(),
        key=lambda item: (
            {"default": 0, "compatibility": 1, "lab": 2}.get(str(item.get("tier")), 3),
            str(item.get("remarks", "")),
        ),
    )

    write_json(OUTPUT_CURATED, curated_profiles)
    write_json(OUTPUT_FULL, full_profiles)
    write_json(OUTPUT_MANIFEST, manifest)

    print(f"Generated {len(curated_profiles)} curated profiles -> {OUTPUT_CURATED}")
    print(f"Generated {len(full_profiles)} full profiles -> {OUTPUT_FULL}")
    print(f"Generated {len(manifest)} manifest entries -> {OUTPUT_MANIFEST}")


if __name__ == "__main__":
    main()
