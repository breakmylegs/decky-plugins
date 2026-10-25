"""Capture raw API replies from a real server for use as test fixtures.

Writes to captures/ (gitignored). Always run sanitise_fixture.py on the output
before copying anything into a fixtures folder.

Credentials come from environment variables so they never land in shell history
or in this repo:
  QBT_URL, QBT_API_KEY or QBT_USERNAME + QBT_PASSWORD
  SAB_URL, SAB_API_KEY

Usage:
  python tools/capture_fixture.py qbittorrent
  python tools/capture_fixture.py sabnzbd
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shared", "py"))
sys.path.insert(0, os.path.join(ROOT, "plugins", "qbittorrent-monitor", "py_modules"))

from plugin_core.http import HttpClient, parse_base_url  # noqa: E402

OUT = os.path.join(ROOT, "captures")


def save(name: str, res) -> None:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    try:
        body = json.dumps(res.json(), indent=2, sort_keys=True)
        path += ".json"
    except Exception:  # noqa: BLE001, keep non-JSON replies as text
        body = res.text()
        path += ".txt"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{body}\n")
    print(f"{res.status} {path}")


def qbittorrent() -> None:
    from qbtmon.client import MODE_API_KEY, MODE_PASSWORD, Credentials, QbtClient

    key = os.environ.get("QBT_API_KEY", "")
    user = os.environ.get("QBT_USERNAME", "")
    mode = MODE_API_KEY if key else MODE_PASSWORD
    client = QbtClient(parse_base_url(os.environ["QBT_URL"]),
                       Credentials(mode, api_key=key, username=user, password=os.environ.get("QBT_PASSWORD", "")))
    for name, path, params in [
        ("qbt_app_version", "app/version", None),
        ("qbt_webapi_version", "app/webapiVersion", None),
        ("qbt_maindata_full", "sync/maindata", {"rid": 0}),
        ("qbt_transfer_info", "transfer/info", None),
        ("qbt_categories", "torrents/categories", None),
        ("qbt_tags", "torrents/tags", None),
    ]:
        save(name, client._call("GET", path, params=params))
    first = client._call("GET", "sync/maindata", params={"rid": 0}).json()
    save("qbt_maindata_incremental", client._call("GET", "sync/maindata", params={"rid": first.get("rid", 0)}))


def sabnzbd() -> None:
    client = HttpClient(parse_base_url(os.environ["SAB_URL"]))
    key = os.environ["SAB_API_KEY"]
    for mode, extra in [
        ("version", {}), ("queue", {"start": 0, "limit": 8}), ("history", {"limit": 10}),
        ("warnings", {}), ("fullstatus", {"skip_dashboard": 1}),
    ]:
        params = {"mode": mode, "output": "json", "apikey": key, **extra}
        save(f"sab_{mode}", client.get("api", params=params))


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("qbittorrent", "sabnzbd"):
        print(__doc__, file=sys.stderr)
        return 2
    qbittorrent() if sys.argv[1] == "qbittorrent" else sabnzbd()
    print("Now run tools/sanitise_fixture.py on each file before committing it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
