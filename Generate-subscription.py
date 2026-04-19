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

BASE_CONFIGS: Sequence[str] = (
    "Serverless.jsonc",
    "Serverless-dynx.jsonc",
    "Serverless-shatel.jsonc",
    "Serverless-vanilla.jsonc",
    "Serverless-zeus.jsonc",
)

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

UDP_MODES: Sequence[str] = ("udp-light", "tcp443", "udp-heavy")
DNS_MODES: Sequence[str] = ("cf", "google", "quad9")

# Smaller public recommendation set (keeps originals for compatibility).
CURATED_MATRIX: Sequence[Tuple[str, str, str]] = (
    ("natA-tlshello-small", "tcp443", "cf"),
    ("natA-tlshello-small", "udp-light", "cf"),
    ("natB-stream-small", "tcp443", "cf"),
    ("mobile-soft", "tcp443", "cf"),
    ("legacy-v41", "udp-light", "cf"),
    ("natA-tlshello-small", "tcp443", "google"),
    ("natA-tlshello-small", "tcp443", "quad9"),
)

DNS_ADDRESSES: Dict[str, str] = {
    "cf": "https://cloudflare-dns.com/dns-query",
    "google": "https://dns.google/dns-query",
    "quad9": "https://dns.quad9.net/dns-query",
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


def get_dns_servers(config: JsonObject) -> List[JsonObject]:
    dns = config.get("dns")
    if not isinstance(dns, dict):
        fail(f"{profile_name(config)} dns must be an object")
    servers = dns.get("servers")
    if not isinstance(servers, list):
        fail(f"{profile_name(config)} dns.servers must be an array")
    return servers


def get_dns_hosts(config: JsonObject) -> JsonObject:
    dns = config.get("dns")
    if not isinstance(dns, dict):
        fail(f"{profile_name(config)} dns must be an object")
    hosts = dns.setdefault("hosts", {})
    if not isinstance(hosts, dict):
        fail(f"{profile_name(config)} dns.hosts must be an object")
    return hosts


def find_outbound(config: JsonObject, tag: str) -> Optional[JsonObject]:
    for outbound in get_outbounds(config):
        if isinstance(outbound, dict) and outbound.get("tag") == tag:
            return outbound
    return None


def find_dns_server(config: JsonObject, tag: str) -> Optional[JsonObject]:
    for server in get_dns_servers(config):
        if isinstance(server, dict) and server.get("tag") == tag:
            return server
    return None


def require_outbound(config: JsonObject, tag: str) -> JsonObject:
    outbound = find_outbound(config, tag)
    if outbound is None:
        fail(f"{profile_name(config)} missing outbound {tag!r}")
    return outbound


def require_dns_server(config: JsonObject, tag: str) -> JsonObject:
    server = find_dns_server(config, tag)
    if server is None:
        fail(f"{profile_name(config)} missing dns server {tag!r}")
    return server


def set_remarks(config: JsonObject, suffix: str) -> None:
    config["remarks"] = f"{profile_name(config)}-{suffix}"


def set_full_fragment(config: JsonObject, fragment: Dict[str, str]) -> None:
    outbound = require_outbound(config, "full-fragment")
    settings = outbound.setdefault("settings", {})
    if not isinstance(settings, dict):
        fail(f"{profile_name(config)} full-fragment settings must be an object")
    settings["fragment"] = dict(fragment)


def set_udp_light(config: JsonObject) -> None:
    outbound = require_outbound(config, "udp-noises")
    settings = outbound.setdefault("settings", {})
    if not isinstance(settings, dict):
        fail(f"{profile_name(config)} udp-noises settings must be an object")

    # Smaller noise envelope to reduce signature and app breakage risk.
    settings["noises"] = [
        {"type": "rand", "packet": "256", "delay": "3", "applyTo": "ipv4"},
        {"type": "rand", "packet": "256", "delay": "6", "applyTo": "ipv6"},
    ]


def force_tcp443_fallback(config: JsonObject) -> None:
    require_outbound(config, "block-out")
    for rule in get_routing_rules(config):
        if rule.get("outboundTag") == "udp-noises":
            rule["outboundTag"] = "block-out"


def apply_udp_mode(config: JsonObject, mode: str) -> None:
    if mode == "udp-light":
        set_udp_light(config)
        return
    if mode == "tcp443":
        force_tcp443_fallback(config)
        return
    if mode == "udp-heavy":
        # Keep source profile's current noise behavior.
        return
    fail(f"Unknown UDP mode {mode!r}")


def apply_dns_mode(config: JsonObject, mode: str) -> None:
    if mode not in DNS_ADDRESSES:
        fail(f"Unknown DNS mode {mode!r}")

    no_filter_dns = require_dns_server(config, "no-filter-dns")
    no_filter_dns["address"] = DNS_ADDRESSES[mode]

    hosts = get_dns_hosts(config)
    if mode == "google":
        hosts["dns.google"] = ["8.8.8.8", "8.8.4.4"]
    elif mode == "quad9":
        hosts["dns.quad9.net"] = ["9.9.9.9", "149.112.112.112"]


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


def main() -> None:
    full_profiles: List[JsonObject] = []
    curated_profiles: List[JsonObject] = []

    fragment_map = {name: settings for name, settings in FRAGMENT_PROFILES}

    for filename in BASE_CONFIGS:
        base_path = ROOT / filename
        base = load_json5(base_path)
        validate_profile(base)

        full_profiles.append(base)

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
                    full_profiles.append(variant)

        for fragment_name, udp_mode, dns_mode in CURATED_MATRIX:
            if fragment_name not in fragment_map:
                fail(f"CURATED_MATRIX uses unknown fragment profile {fragment_name!r}")
            curated_profiles.append(
                build_variant(
                    base_config=base,
                    fragment_name=fragment_name,
                    fragment_settings=fragment_map[fragment_name],
                    udp_mode=udp_mode,
                    dns_mode=dns_mode,
                )
            )

        # Keep original behavior as fallback, but after recommended variants.
        curated_profiles.append(copy.deepcopy(base))

    full_profiles = deduplicate_by_remarks(full_profiles)
    curated_profiles = deduplicate_by_remarks(curated_profiles)

    write_json(OUTPUT_CURATED, curated_profiles)
    write_json(OUTPUT_FULL, full_profiles)

    print(f"Generated {len(curated_profiles)} curated profiles -> {OUTPUT_CURATED}")
    print(f"Generated {len(full_profiles)} full profiles -> {OUTPUT_FULL}")


if __name__ == "__main__":
    main()
