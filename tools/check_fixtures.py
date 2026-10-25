"""Fail when a committed fixture holds a real address or something key-shaped.

Scans every file under */fixtures/ and */tests/data/. Allowed IPv4 addresses
are loopback, 0.0.0.0 and the RFC 5737 documentation ranges. Key-shaped strings
are long runs of letters and digits that are not hex placeholders made by
sanitise_fixture.py.

Usage: python tools/check_fixtures.py [root]
"""

from __future__ import annotations

import ipaddress
import os
import re
import sys

IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
KEY_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z0-9]{32,}(?![A-Za-z0-9_])")
PLACEHOLDER_HASH = re.compile(r"^0*[0-9a-f]{1,8}$")
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
FIXTURE_DIRS = ("fixtures", os.path.join("tests", "data"))


def ip_allowed(text: str) -> bool:
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return True
    return ip.is_loopback or ip.is_unspecified or any(ip in net for net in DOC_NETS)


def key_allowed(text: str) -> bool:
    if PLACEHOLDER_HASH.match(text):
        return True
    # A run of one repeated character is a test placeholder, not a key.
    return len(set(text)) <= 2


def scan_file(path: str) -> list[str]:
    problems = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for lineno, line in enumerate(handle, 1):
            for match in IPV4_RE.finditer(line):
                if not ip_allowed(match.group(0)):
                    problems.append(f"{path}:{lineno}: IPv4 address outside documentation ranges")
            for match in KEY_RE.finditer(line):
                if not key_allowed(match.group(0)):
                    problems.append(f"{path}:{lineno}: key-shaped string")
    return problems


def fixture_files(root: str) -> list[str]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "out", "dist")]
        rel = os.path.relpath(dirpath, root)
        if any(part in rel.split(os.sep) for part in ("fixtures",)) or rel.endswith(os.path.join("tests", "data")):
            found.extend(os.path.join(dirpath, f) for f in filenames)
    return sorted(found)


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = fixture_files(root)
    problems = [p for f in files for p in scan_file(f)]
    for problem in problems:
        print(problem)
    print(f"checked {len(files)} fixture files, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
