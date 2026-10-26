"""Fail when a tracked or new file holds something that looks like a secret.

A plain pattern check, readable in one sitting. It scans every file git would
commit: tracked files plus untracked files that are not ignored. Each pattern
names a known key format, or a secret-looking assignment with a long literal
value. Placeholders made of one repeated character are allowed, because the
tests build their fake keys that way.

Usage: python tools/check_secrets.py [root]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

PATTERNS = [
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("OpenAI key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b")),
    ("Google API key", re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b")),
    ("qBittorrent API key", re.compile(r"\bqbt_[A-Za-z0-9]{28}\b")),
    ("secret assignment", re.compile(
        r"""(?i)\b(?:api[_-]?key|apikey|secret|password|passwd|token|auth)\b["']?\s*[:=]\s*["']([^"'\s]{16,})["']""")),
]
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".woff", ".woff2", ".pdf")
SKIP_NAMES = {"pnpm-lock.yaml", "LICENSE"}


def placeholder(text: str) -> bool:
    """A run of one repeated character after any prefix, such as "qbt_" + "k" * 28."""
    tail = re.sub(r"^[a-z]+[_-]", "", text)
    return len(set(tail)) <= 2


def files(root: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root,
                         capture_output=True, text=True, stdin=subprocess.DEVNULL, check=True).stdout
    names = [n for n in out.splitlines() if n]
    return [n for n in names if os.path.basename(n) not in SKIP_NAMES and not n.lower().endswith(SKIP_SUFFIXES)
            and os.path.isfile(os.path.join(root, n))]


def scan_text(path: str, text: str) -> list[str]:
    problems = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, pattern in PATTERNS:
            for match in pattern.finditer(line):
                value = match.group(1) if match.groups() else match.group(0)
                if placeholder(value):
                    continue
                problems.append(f"{path}:{lineno}: {label}")
    return problems


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    names = files(root)
    if not names:
        # A check that finds no files proves nothing. Refuse rather than pass.
        print("no files to scan", file=sys.stderr)
        return 1
    problems: list[str] = []
    for name in names:
        try:
            with open(os.path.join(root, name), encoding="utf-8", errors="replace") as handle:
                problems += scan_text(name, handle.read())
        except OSError:
            continue
    for problem in problems:
        print(problem)
    print(f"scanned {len(names)} files, {len(problems)} possible secrets")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
