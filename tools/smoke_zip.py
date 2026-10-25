"""Load a packaged plugin the way Decky does and exercise its backend.

Extracts the zip to a temp folder, installs a stand-in `decky` module, appends
py_modules to sys.path (Decky appends, so a stdlib name always wins), imports
main.py, runs _main, calls get_snapshot, then _unload. With --mock-qbt it also
points the plugin at a mock qBittorrent and checks one poll arrives.

Run in a fresh interpreter: python -I tools/smoke_zip.py out/<id>.zip [--mock-qbt]
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import sys
import tempfile
import types
import zipfile

TOOLS = os.path.dirname(os.path.abspath(__file__))


def fake_decky(home: str, plugin_dir: str, name: str, events: list) -> types.ModuleType:
    mod = types.ModuleType("decky")
    mod.DECKY_USER_HOME = os.path.join(home, "user")
    mod.DECKY_HOME = os.path.join(home, "homebrew")
    mod.DECKY_PLUGIN_DIR = plugin_dir
    mod.DECKY_PLUGIN_SETTINGS_DIR = os.path.join(home, "homebrew", "settings", name)
    mod.DECKY_PLUGIN_RUNTIME_DIR = os.path.join(home, "homebrew", "data", name)
    mod.DECKY_PLUGIN_LOG_DIR = os.path.join(home, "homebrew", "logs", name)
    for path in (mod.DECKY_PLUGIN_SETTINGS_DIR, mod.DECKY_PLUGIN_RUNTIME_DIR, mod.DECKY_PLUGIN_LOG_DIR):
        os.makedirs(path, exist_ok=True)
    mod.logger = logging.getLogger(name)

    async def emit(event, *args):
        events.append((event, args))

    mod.emit = emit
    return mod


async def exercise(plugin, events: list, mock_url: str | None, key: str) -> None:
    await plugin._main()
    if not hasattr(plugin, "get_snapshot"):
        # A scaffold with no frontend API yet. Loading and unloading is the test.
        await plugin._unload()
        return
    snap = await plugin.get_snapshot()
    assert snap["status"]["state"] in ("connecting", "unconfigured"), snap["status"]
    if mock_url:
        assert (await plugin.save_settings({"base_url": mock_url}))["ok"]
        assert (await plugin.set_secret("api_key", key))["ok"]
        report = await plugin.test_connection()
        assert report["ok"], report
        for _ in range(50):
            if any(e[0] == "data" for e in events):
                break
            await asyncio.sleep(0.1)
        data = [e[1][0] for e in events if e[0] == "data"]
        assert data and data[-1]["total"] == 3, data
        blob = json.dumps(events) + json.dumps(await plugin.get_snapshot())
        assert key not in blob, "secret leaked into an event or snapshot"
    await plugin._unload()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip")
    parser.add_argument("--mock-qbt", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(args.zip) as zf:
            roots = {n.split("/")[0] for n in zf.namelist()}
            assert len(roots) == 1, f"zip must have one root folder, found {roots}"
            zf.extractall(os.path.join(tmp, "plugins"))
        name = roots.pop()
        plugin_dir = os.path.join(tmp, "plugins", name)
        with open(os.path.join(plugin_dir, "plugin.json"), encoding="utf-8") as handle:
            assert json.load(handle)["name"] == name, "plugin.json name must match the zip root"
        events: list = []
        sys.modules["decky"] = fake_decky(tmp, plugin_dir, name, events)
        sys.path.append(os.path.join(plugin_dir, "py_modules"))
        spec = importlib.util.spec_from_file_location("_plugin_main", os.path.join(plugin_dir, "main.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin = module.Plugin()

        mock = None
        key = "smoke_" + "k" * 26
        if args.mock_qbt:
            sys.path.insert(0, TOOLS)
            import mock_qbittorrent

            mock = mock_qbittorrent.MockQbt(api_key=key)
            mock.start()
        try:
            asyncio.run(exercise(plugin, events, mock.url if mock else None, key))
        finally:
            if mock:
                mock.stop()
    print(f"smoke ok: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
