"""Fail the build if tuning-advisor source can write to Steam or anything else.

The tuning advisor recommends settings and never applies them. This scans its
TypeScript and Python source for known setter calls. Extend DENY as new setters
are found.

Usage: python tools/check_readonly.py plugins/tuning-advisor
"""

from __future__ import annotations

import os
import re
import sys

DENY = [
    (re.compile(r"\bSetAppLaunchOptions\b"), "SetAppLaunchOptions"),
    (re.compile(r"\bSpecifyCompatTool\b"), "SpecifyCompatTool"),
    (re.compile(r"\bUpdateSettings\b"), "UpdateSettings"),
    (re.compile(r"\bSteamClient\s*(?:\?\.|\.)\s*\w+\s*(?:\?\.|\.)\s*Set\w*"), "SteamClient.*.Set*"),
    (re.compile(r"\bSetPerAppSettings\b|\bSetTDPLimit\b|\bSetGPUPerformanceLevel\b"), "Steam per-app setter"),
    (re.compile(r"\bSetShortcut\w*\b"), "shortcut setter"),
    (re.compile(r"\bexecuteInTab\b|\binjectCssIntoTab\b"), "tab injection"),
    (re.compile(r"\bsubprocess\b|\bos\.system\b|\bos\.popen\b"), "process execution"),
]
SOURCE_EXT = (".ts", ".tsx", ".py", ".js", ".jsx")
SKIP_DIRS = {"node_modules", "dist", "shared", "plugin_core", "__pycache__", "tests"}


def scan(root: str) -> list[str]:
    problems = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(SOURCE_EXT) or ".test." in filename:
                continue
            path = os.path.join(dirpath, filename)
            with open(path, encoding="utf-8", errors="replace") as handle:
                for lineno, line in enumerate(handle, 1):
                    for pattern, label in DENY:
                        if pattern.search(line):
                            problems.append(f"{path}:{lineno}: {label} is not allowed in a read-only plugin")
    return problems


def count_sources(root: str) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        total += sum(1 for f in filenames if f.endswith(SOURCE_EXT))
    return total


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = sys.argv[1]
    sources = count_sources(root)
    if sources == 0:
        # A guard that finds no files proves nothing. Refuse rather than pass.
        print(f"no source files under {root}", file=sys.stderr)
        return 1
    problems = scan(root)
    for problem in problems:
        print(problem)
    print(f"scanned {sources} source files, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
