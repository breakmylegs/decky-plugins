"""Copy shared code into each plugin.

shared/py/plugin_core -> plugins/<id>/py_modules/plugin_core
shared/ts             -> plugins/<id>/src/shared

The copies are gitignored in the monorepo and committed in the mirrors, so a
mirror builds without the monorepo. Also writes build_info.json, which the
update check reads. The mirror repo comes from --repo or the MIRROR_REPO_<ID>
environment variable, never from source.

Usage: python tools/vendor_shared.py [plugin-id ...] [--owner OWNER]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")
SHARED_PY = os.path.join(ROOT, "shared", "py", "plugin_core")
SHARED_TS = os.path.join(ROOT, "shared", "ts")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "tests", "*.test.ts")
# Mock servers each plugin's tests use, so a mirror's tests run without the monorepo.
MOCKS = {"qbittorrent-monitor": ["mock_qbittorrent.py"], "sabnzbd-monitor": ["mock_sabnzbd.py"]}


def plugin_ids() -> list[str]:
    return sorted(d for d in os.listdir(PLUGINS) if os.path.isfile(os.path.join(PLUGINS, d, "plugin.json")))


def copy_tree(src: str, dst: str) -> None:
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=IGNORE)


def mirror_repo(plugin_id: str, owner: str | None) -> str:
    env = os.environ.get("MIRROR_REPO_" + plugin_id.upper().replace("-", "_"))
    if env:
        return env
    if owner:
        return f"{owner}/{plugin_id}"
    return ""


def vendor(plugin_id: str, owner: str | None) -> None:
    folder = os.path.join(PLUGINS, plugin_id)
    copy_tree(SHARED_PY, os.path.join(folder, "py_modules", "plugin_core"))
    copy_tree(SHARED_TS, os.path.join(folder, "src", "shared"))
    mocks = MOCKS.get(plugin_id, [])
    if mocks:
        target = os.path.join(folder, "tests", "mocks")
        os.makedirs(target, exist_ok=True)
        for name in mocks:
            shutil.copy2(os.path.join(ROOT, "tools", name), os.path.join(target, name))
    with open(os.path.join(folder, "package.json"), encoding="utf-8") as handle:
        version = json.load(handle)["version"]
    info = {"plugin": plugin_id, "version": version, "repo": mirror_repo(plugin_id, owner), "asset": f"{plugin_id}.zip"}
    with open(os.path.join(folder, "build_info.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(info, handle, indent=2)
        handle.write("\n")
    print(f"vendored shared code into {plugin_id} (repo: {info['repo'] or 'not set, update check off'})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugins", nargs="*")
    parser.add_argument("--owner", default=os.environ.get("MIRROR_OWNER") or os.environ.get("GITHUB_REPOSITORY_OWNER"))
    args = parser.parse_args()
    ids = args.plugins or plugin_ids()
    unknown = [p for p in ids if p not in plugin_ids()]
    if unknown:
        print("unknown plugin: " + ", ".join(unknown), file=sys.stderr)
        return 2
    for plugin_id in ids:
        vendor(plugin_id, args.owner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
