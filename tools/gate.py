"""Local gate. Run before every push. Nothing runs on GitHub.

Steps, in order, stopping at the first failure:
1. Secret pattern check (tools/check_secrets.py) on every file git would commit.
2. Fixture guard and tuning-advisor read-only guard.
3. pytest for shared code, tools and every plugin.
4. Per plugin: vendor shared code, pnpm install, vitest, build, then tsc last,
   package the zip, and smoke test it the way Decky loads it.

Usage: python tools/gate.py [plugin-id ...] [--skip-install]
"""

from __future__ import annotations

import argparse
import os
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugins", nargs="*", default=PLUGINS)
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    py = sys.executable

    run("secret pattern check", [py, "tools/check_secrets.py"])
    run("fixture guard", [py, "tools/check_fixtures.py"])
    run("read-only guard (tuning-advisor)", [py, "tools/check_readonly.py", "plugins/tuning-advisor"])
    # Vendor first. Plugin tests import the vendored copy, so a stale copy would
    # test old shared code.
    run("vendor shared code (all plugins)", [py, "tools/vendor_shared.py"])
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
