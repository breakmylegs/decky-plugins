"""Package one plugin into the release zip Decky installs.

Layout:
  <id>.zip
    <id>/dist/index.js, package.json, plugin.json, main.py, py_modules/,
    build_info.json, LICENSE, README.md

The asset name, the zip root folder and plugin.json "name" are all the plugin
id. Decky v3.0.4 and later read the name from plugin.json, older loaders take it
from the URL, and a mismatch hangs the install on those older loaders.

Usage: python tools/package_zip.py <plugin-id> [--out out/] [--author NAME]
Run tools/vendor_shared.py and the frontend build first.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXED_TIME = (2020, 1, 1, 0, 0, 0)
REQUIRED = ["dist/index.js", "package.json", "plugin.json", "main.py", "py_modules", "build_info.json"]
SKIP_DIRS = {"__pycache__", "tests", "node_modules", ".pytest_cache"}


def collect(folder: str) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    for name in ("main.py", "package.json", "build_info.json", "README.md", "dist/index.js"):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            files.append((path, name))
    for top in ("py_modules", "defaults", "assets"):
        base = os.path.join(folder, top)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for filename in sorted(filenames):
                if filename.endswith((".pyc", ".pyo")):
                    continue
                full = os.path.join(dirpath, filename)
                files.append((full, os.path.relpath(full, folder).replace(os.sep, "/")))
    registry = os.path.join(folder, "registry")
    if os.path.isdir(registry):
        for filename in sorted(os.listdir(registry)):
            if filename.endswith(".json"):
                files.append((os.path.join(registry, filename), f"registry/{filename}"))
    return files


def add(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def package(plugin_id: str, out_dir: str, author: str | None) -> str:
    folder = os.path.join(ROOT, "plugins", plugin_id)
    missing = [r for r in REQUIRED if not os.path.exists(os.path.join(folder, r))]
    if missing:
        raise SystemExit(f"{plugin_id}: missing {', '.join(missing)}. Run vendor_shared.py and pnpm build first.")
    if not os.path.isdir(os.path.join(folder, "py_modules", "plugin_core")):
        raise SystemExit(f"{plugin_id}: py_modules/plugin_core missing. Run tools/vendor_shared.py.")
    with open(os.path.join(folder, "plugin.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("name") != plugin_id:
        raise SystemExit(f"{plugin_id}: plugin.json name must be {plugin_id!r}")
    if "_root" in manifest.get("flags", []) or "root" in manifest.get("flags", []):
        raise SystemExit(f"{plugin_id}: root flags are not allowed")
    if author:
        manifest["author"] = author
    with open(os.path.join(folder, "package.json"), encoding="utf-8") as handle:
        if json.load(handle).get("type") != "module":
            raise SystemExit(f'{plugin_id}: package.json must set "type": "module"')

    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, f"{plugin_id}.zip")
    with zipfile.ZipFile(target, "w") as zf:
        add(zf, f"{plugin_id}/plugin.json", (json.dumps(manifest, indent=2) + "\n").encode())
        for path, arc in collect(folder):
            with open(path, "rb") as handle:
                add(zf, f"{plugin_id}/{arc}", handle.read())
        licence = os.path.join(folder, "LICENSE")
        if not os.path.isfile(licence):
            licence = os.path.join(ROOT, "LICENSE")
        with open(licence, "rb") as handle:
            add(zf, f"{plugin_id}/LICENSE", handle.read())
    print(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin")
    parser.add_argument("--out", default=os.path.join(ROOT, "out"))
    parser.add_argument("--author", default=os.environ.get("PLUGIN_AUTHOR") or os.environ.get("GITHUB_REPOSITORY_OWNER"))
    args = parser.parse_args()
    package(args.plugin, args.out, args.author)
    return 0


if __name__ == "__main__":
    sys.exit(main())
