"""Local gate. Run before every push. Nothing runs on GitHub.

Steps, in order, stopping at the first failure:
1. Secret scan with gitleaks (on PATH or .tools/gitleaks). Missing gitleaks fails
   the gate unless --skip-secrets is given, so a missing tool never passes silently.
2. Fixture guard and tuning-advisor read-only guard.
3. pytest for shared code, tools and every plugin.
4. Per plugin: vendor shared code, pnpm install, vitest, build, then tsc last,
   package the zip, and smoke test it the way Decky loads it.

Usage: python tools/gate.py [plugin-id ...] [--skip-secrets] [--skip-install]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = ["qbittorrent-monitor", "sabnzbd-monitor", "tuning-advisor"]
SMOKE_FLAGS = {"qbittorrent-monitor": ["--mock-qbt"], "sabnzbd-monitor": ["--mock-sab"]}


def run(label: str, cmd: list[str], cwd: str = ROOT) -> None:
    started = time.time()
    print(f"\n== {label}", flush=True)
    result = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, shell=(os.name == "nt" and cmd[0] in ("pnpm", "npx")))
    took = time.time() - started
    if result.returncode != 0:
        print(f"\nFAILED: {label} (exit {result.returncode}, {took:.0f}s)", flush=True)
        sys.exit(result.returncode or 1)
    print(f"ok: {label} ({took:.0f}s)", flush=True)


def gitleaks() -> str | None:
    found = shutil.which("gitleaks")
    if found:
        return found
    for name in ("gitleaks.exe", "gitleaks"):
        local = os.path.join(ROOT, ".tools", name)
        if os.path.isfile(local):
            return local
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugins", nargs="*", default=PLUGINS)
    parser.add_argument("--skip-secrets", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    py = sys.executable

    tool = gitleaks()
    if tool:
        run("secret scan (gitleaks, history and working tree)", [tool, "git", "--config", ".gitleaks.toml", "--no-banner", "--redact", "."])
        run("secret scan (uncommitted files)", [tool, "dir", "--config", ".gitleaks.toml", "--no-banner", "--redact",
                                                "shared", "plugins/qbittorrent-monitor/src", "plugins/sabnzbd-monitor/src",
                                                "plugins/tuning-advisor/src", "tools", "docs"])
    elif args.skip_secrets:
        print("\n== secret scan SKIPPED (--skip-secrets). Do not push without one.", flush=True)
    else:
        print("\nFAILED: gitleaks not found on PATH or in .tools/. Install it, or pass --skip-secrets.", flush=True)
        return 1

    run("fixture guard", [py, "tools/check_fixtures.py"])
    run("read-only guard (tuning-advisor)", [py, "tools/check_readonly.py", "plugins/tuning-advisor"])
    tests = ["shared/py/tests", "tools/tests"] + [f"plugins/{p}/tests" for p in PLUGINS]
    run("pytest", [py, "-m", "pytest", "-q", *tests])

    for plugin in args.plugins:
        folder = os.path.join(ROOT, "plugins", plugin)
        run(f"{plugin}: vendor shared code", [py, "tools/vendor_shared.py", plugin])
        if not args.skip_install:
            run(f"{plugin}: pnpm install", ["pnpm", "install", "--frozen-lockfile", "--prefer-offline"], cwd=folder)
        run(f"{plugin}: vitest", ["pnpm", "test"], cwd=folder)
        run(f"{plugin}: build", ["pnpm", "build"], cwd=folder)
        # tsc after the build, so it checks the final files.
        run(f"{plugin}: typecheck", ["pnpm", "typecheck"], cwd=folder)
        run(f"{plugin}: package", [py, "tools/package_zip.py", plugin])
        run(f"{plugin}: smoke", [py, "-I", "tools/smoke_zip.py", f"out/{plugin}.zip", *SMOKE_FLAGS.get(plugin, [])])

    print("\nGATE PASSED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
