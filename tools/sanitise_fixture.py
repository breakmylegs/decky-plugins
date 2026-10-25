"""Replace identifying values in a captured fixture with stable placeholders.

Replaces torrent and NZB names, hashes, nzo_ids, file paths, host names, IP
addresses, API keys, cookies and save paths. The same input value always maps
to the same placeholder within one run, so relationships between fields hold.

Usage: python tools/sanitise_fixture.py in.json out.json
"""

from __future__ import annotations

import ipaddress
import json
import re
import sys
from typing import Any

# Keys whose values are free text that may name content.
NAME_KEYS = {"name", "filename", "nzb_name", "title", "comment", "tracker", "magnet_uri", "content_path",
             "save_path", "download_path", "root_path", "storage", "path", "script_log", "fail_message",
             "action_line", "url", "url_info", "category_path", "savePath", "infohash_v1", "infohash_v2",
             "completed_dir", "download_dir", "incomplete_dir", "nzo_id", "hash", "password", "api_key",
             "apikey", "nzb_key", "username", "host", "hostname", "local_ipv4", "ipv6", "publicipv4",
             "dnslookup", "last_external_address_v4", "last_external_address_v6", "cookie", "sid"}

HASH_RE = re.compile(r"\b[0-9a-fA-F]{40}\b|\b[0-9a-fA-F]{64}\b")
KEY_RE = re.compile(r"\b[0-9a-zA-Z_]{24,}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HOST_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+(?:lan|local|home|internal|net|com|org|io|uk|de|nl)\b")
PATH_RE = re.compile(r"(?:/[^\s/\"']+){2,}")

# Documentation ranges (RFC 5737) used for placeholders.
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]


class Sanitiser:
    def __init__(self) -> None:
        self.maps: dict[str, dict[str, str]] = {}

    def token(self, kind: str, value: str) -> str:
        table = self.maps.setdefault(kind, {})
        if value not in table:
            n = len(table) + 1
            if kind == "hash":
                table[value] = f"{n:040x}"
            elif kind == "ip":
                table[value] = f"192.0.2.{n % 254 + 1}"
            elif kind == "host":
                table[value] = f"host{n}.example.com"
            elif kind == "path":
                table[value] = f"/data/path{n}"
            else:
                table[value] = f"{kind}-{n}"
        return table[value]

    def text(self, value: str) -> str:
        value = HASH_RE.sub(lambda m: self.token("hash", m.group(0)), value)
        value = IPV4_RE.sub(lambda m: m.group(0) if _is_safe_ip(m.group(0)) else self.token("ip", m.group(0)), value)
        value = HOST_RE.sub(lambda m: self.token("host", m.group(0)), value)
        value = PATH_RE.sub(lambda m: self.token("path", m.group(0)), value)
        value = KEY_RE.sub(lambda m: self.token("key", m.group(0)) if not m.group(0).isdigit() else m.group(0), value)
        return value

    def walk(self, node: Any, key: str | None = None) -> Any:
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                new_key = self.token("hash", k) if HASH_RE.fullmatch(str(k)) else (
                    self.token("nzo", k) if str(k).startswith("SABnzbd_nzo_") else k)
                out[new_key] = self.walk(v, str(k))
            return out
        if isinstance(node, list):
            return [self.walk(v, key) for v in node]
        if isinstance(node, str):
            if key in ("hash", "infohash_v1", "infohash_v2") and node:
                return self.token("hash", node)
            if key == "nzo_id" and node:
                return self.token("nzo", node)
            if key in NAME_KEYS and node:
                return self.token(key or "value", node)
            return self.text(node)
        return node


def _is_safe_ip(text: str) -> bool:
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return True  # not an address, for example a version string
    return ip.is_loopback or ip.is_unspecified or any(ip in net for net in DOC_NETS)


def sanitise(data: Any) -> Any:
    return Sanitiser().walk(data)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = json.load(handle)
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as handle:
        json.dump(sanitise(data), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
