#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_OUTBOUND_TAGS = {
    "block-out",
    "tcp-direct-out",
    "udp-direct-out",
    "dns-out",
    "full-fragment",
}
KNOWN_DOH_HOSTS = {
    "cloudflare-dns.com",
    "dns.google",
    "dns.quad9.net",
}


def fail(path: Path, index: int | None, message: str) -> None:
    location = f"{path}"
    if index is not None:
        location += f"[{index}]"
    raise SystemExit(f"{location}: {message}")


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise SystemExit(f"{path}: failed to read JSON: {exc}") from exc


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def get_outbound_tags(config: dict[str, Any]) -> list[str]:
    outbounds = config.get("outbounds")
    if not isinstance(outbounds, list):
        return []
    tags: list[str] = []
    for outbound in outbounds:
        if isinstance(outbound, dict) and isinstance(outbound.get("tag"), str):
            tags.append(outbound["tag"])
    return tags


def validate_unique_remarks(path: Path, configs: list[Any]) -> None:
    seen: set[str] = set()
    for index, config in enumerate(configs):
        if not isinstance(config, dict):
            fail(path, index, "profile must be an object")
        remarks = config.get("remarks")
        if not isinstance(remarks, str) or not remarks.strip():
            fail(path, index, "missing non-empty remarks")
        if remarks in seen:
            fail(path, index, f"duplicate remarks: {remarks}")
        seen.add(remarks)


def validate_outbounds(path: Path, index: int, config: dict[str, Any]) -> None:
    tags = get_outbound_tags(config)
    tag_set = set(tags)
    if len(tags) != len(tag_set):
        fail(path, index, "duplicate outbound tags")

    missing = REQUIRED_OUTBOUND_TAGS - tag_set
    if missing:
        fail(path, index, f"missing required outbound tags: {sorted(missing)}")

    routing = config.get("routing", {})
    if not isinstance(routing, dict):
        fail(path, index, "routing must be an object")
    rules = routing.get("rules", [])
    if not isinstance(rules, list):
        fail(path, index, "routing.rules must be a list")

    for rule_index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            fail(path, index, f"routing.rules[{rule_index}] must be an object")
        outbound_tag = rule.get("outboundTag")
        if outbound_tag is not None and outbound_tag not in tag_set:
            fail(
                path,
                index,
                f"routing.rules[{rule_index}] references missing outboundTag: {outbound_tag}",
            )


def validate_dns(path: Path, index: int, config: dict[str, Any]) -> None:
    dns = config.get("dns")
    if not isinstance(dns, dict):
        fail(path, index, "dns must be an object")
    hosts = dns.get("hosts", {})
    if not isinstance(hosts, dict):
        fail(path, index, "dns.hosts must be an object")
    servers = dns.get("servers", [])
    if not isinstance(servers, list):
        fail(path, index, "dns.servers must be a list")

    no_filter_servers = [
        server
        for server in servers
        if isinstance(server, dict) and server.get("tag") == "no-filter-dns"
    ]
    if len(no_filter_servers) != 1:
        fail(path, index, "must contain exactly one no-filter-dns server")

    address = no_filter_servers[0].get("address")
    if not isinstance(address, str) or not address.startswith("https://"):
        fail(path, index, "no-filter-dns.address must be an https DoH URL")

    active_hosts = {host for host in KNOWN_DOH_HOSTS if host in address}
    for host in active_hosts:
        if host not in hosts:
            fail(path, index, f"active DoH hostname lacks dns.hosts bootstrap: {host}")

    stale_hosts = [host for host in KNOWN_DOH_HOSTS if host in hosts and host not in active_hosts]
    if len(stale_hosts) > 1:
        fail(path, index, f"too many stale DoH bootstrap hosts: {stale_hosts}")


def validate_fragment(path: Path, index: int, config: dict[str, Any]) -> None:
    outbounds = config.get("outbounds", [])
    if not isinstance(outbounds, list):
        fail(path, index, "outbounds must be a list")

    full_fragment = None
    for outbound in outbounds:
        if isinstance(outbound, dict) and outbound.get("tag") == "full-fragment":
            full_fragment = outbound
            break
    if full_fragment is None:
        fail(path, index, "missing full-fragment outbound")

    settings = full_fragment.get("settings")
    if not isinstance(settings, dict):
        fail(path, index, "full-fragment.settings must be an object")
    fragment = settings.get("fragment")
    if not isinstance(fragment, dict):
        fail(path, index, "full-fragment.settings.fragment must be an object")

    for key in ("packets", "length", "interval"):
        if key not in fragment:
            fail(path, index, f"fragment missing key: {key}")


def validate_dns_block_types(path: Path, index: int, config: dict[str, Any]) -> None:
    outbounds = config.get("outbounds")
    if not isinstance(outbounds, list):
        fail(path, index, "outbounds must be a list")

    dns_out = None
    for outbound in outbounds:
        if isinstance(outbound, dict) and outbound.get("tag") == "dns-out":
            dns_out = outbound
            break

    if dns_out is None:
        fail(path, index, "missing dns-out outbound")

    settings = dns_out.get("settings")
    if not isinstance(settings, dict):
        fail(path, index, "dns-out.settings must be an object")

    block_types = settings.get("blockTypes")
    if not isinstance(block_types, list) or 65 not in block_types:
        fail(path, index, "dns-out.settings.blockTypes must include 65")


def validate_manifest(path: Path) -> None:
    data = load_json(path)
    if not isinstance(data, list):
        raise SystemExit(f"{path}: top-level JSON must be a list")
    if not data:
        raise SystemExit(f"{path}: manifest must not be empty")

    seen: set[str] = set()
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            fail(path, index, "manifest entry must be an object")
        remarks = entry.get("remarks")
        if not isinstance(remarks, str) or not remarks.strip():
            fail(path, index, "manifest entry missing remarks")
        if remarks in seen:
            fail(path, index, f"duplicate manifest remarks: {remarks}")
        seen.add(remarks)

        tier = entry.get("tier")
        if tier not in {"default", "compatibility", "lab"}:
            fail(path, index, f"invalid manifest tier: {tier}")

        for list_field in ("good_for", "avoid_if"):
            value = entry.get(list_field)
            if not isinstance(value, list):
                fail(path, index, f"manifest field {list_field} must be a list")


def validate_subscription(path: Path) -> None:
    data = load_json(path)
    if not isinstance(data, list):
        raise SystemExit(f"{path}: top-level JSON must be a list")
    if not data:
        raise SystemExit(f"{path}: subscription must not be empty")

    validate_unique_remarks(path, data)
    for index, config in enumerate(data):
        if not isinstance(config, dict):
            fail(path, index, "profile must be an object")
        validate_outbounds(path, index, config)
        validate_dns(path, index, config)
        validate_fragment(path, index, config)
        validate_dns_block_types(path, index, config)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: validate_subscription.py <file.json> [...]")

    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.name == "profiles-manifest.json":
            validate_manifest(path)
        else:
            validate_subscription(path)

    print("OK")


if __name__ == "__main__":
    main()
