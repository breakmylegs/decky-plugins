"""Build the ProtonDB index for tuning-advisor from a monthly ODbL dump.

Runs on this machine only. Nothing runs on GitHub.

Source: https://github.com/bdefore/protondb-data, reports/reports_<mon><n>_<year>.tar.gz,
one JSON array in reports_piiremoved.json (about 530 MB for October 2026).
Licence: ODbL 1.0 for the database, DbCL for its contents. The index is a
derived database, so it is published under ODbL too, with attribution.

Steps:
  survey   print the dump's shape (keys, handheld share), for the register
  build    stream the dump and write out/protondb-index.json.gz
  publish  upload that file to the rolling monorepo release protondb-index

Index format, gzipped UTF-8 text, so the plugin can find one app by reading
lines without holding the whole index in memory:
  line 1:   {"schema": 1, "dump": "oct1_2026", "licence": ..., ...}
  then:     <appid><TAB>{"n": .., "works": .., "handheld": .., "title": .., "reports": [...]}
  sorted by app ID as text.

Usage:
  python -I tools/protondb_index.py survey <dump.tar.gz>
  python -I tools/protondb_index.py build <dump.tar.gz> [--out out/]
  python tools/protondb_index.py publish out/protondb-index.json.gz
"""

from __future__ import annotations

import collections
import gzip
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from typing import Any, Iterator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBER = "reports_piiremoved.json"
INDEX_NAME = "protondb-index.json.gz"
RELEASE_TAG = "protondb-index"
WHITESPACE = " \t\r\n"
SCHEMA = 1

# Handheld chips, matched in the report's cpu or gpu string. Values are
# tuning-advisor registry families, or a registry id when one chip means one device.
HANDHELD_CHIPS = [
    (re.compile(r"custom (?:apu|gpu) 0405|aerith", re.I), "Steam Deck LCD", "AMD Aerith (Van Gogh)"),
    (re.compile(r"custom (?:apu|gpu) 0932|sephiroth", re.I), "Steam Deck OLED", "AMD Sephiroth"),
    (re.compile(r"z2 extreme", re.I), "Handheld with Ryzen Z2 Extreme", "AMD Ryzen Z2 Extreme"),
    (re.compile(r"z1 extreme", re.I), "Handheld with Ryzen Z1 Extreme", "AMD Ryzen Z1 Extreme"),
    (re.compile(r"z2 go", re.I), "Handheld with Ryzen Z2 Go", "AMD Ryzen Z2 Go"),
    (re.compile(r"\bz2 a\b", re.I), "Handheld with Ryzen Z2 A", "AMD Ryzen Z2 A"),
    (re.compile(r"\bryzen z2\b(?! (?:extreme|go|a)\b)", re.I), "Handheld with Ryzen Z2", "AMD Ryzen Z2"),
    (re.compile(r"\bryzen z1\b(?! extreme)", re.I), "Handheld with Ryzen Z1", "AMD Ryzen Z1"),
]
TIERS = ("borked", "bronze", "silver", "gold", "platinum")
MAX_REPORTS_PER_APP = 5
MAX_TEXT = 240


def records(text: io.TextIOBase, chunk: int = 1 << 22) -> Iterator[dict[str, Any]]:
    """Yield objects from a top-level JSON array without loading it all.

    Reads text, so multi-byte characters never split across chunks. Advances an
    index and trims the buffer only when a new chunk is read, so it stays linear.
    """
    decoder = json.JSONDecoder()
    buf = ""
    pos = 0
    eof = False
    opened = False
    while True:
        if not eof and len(buf) - pos < chunk:
            data = text.read(chunk)
            if data:
                buf = buf[pos:] + data
                pos = 0
            else:
                eof = True
        while pos < len(buf) and buf[pos] in WHITESPACE:
            pos += 1
        if not opened and pos < len(buf):
            if buf[pos] != "[":
                raise ValueError("the dump is not a JSON array")
            pos += 1
            opened = True
            continue
        while pos < len(buf) and buf[pos] in WHITESPACE + ",":
            pos += 1
        if pos >= len(buf):
            if eof:
                return
            continue
        if buf[pos] == "]":
            return
        try:
            obj, end = decoder.raw_decode(buf, pos)
        except ValueError:
            if eof:
                raise ValueError("the dump ends part way through a record") from None
            data = text.read(chunk)
            if not data:
                eof = True
            else:
                buf = buf[pos:] + data
                pos = 0
            continue
        if isinstance(obj, dict):
            yield obj
        pos = end


def open_dump(path: str) -> io.TextIOBase:
    tar = tarfile.open(path)
    member = tar.extractfile(MEMBER)
    if member is None:
        raise SystemExit(f"{MEMBER} not found in {path}")
    return io.TextIOWrapper(member, encoding="utf-8", errors="replace")


def dump_name(path: str) -> str:
    match = re.search(r"reports_([a-z]{3}\d+_\d{4})", os.path.basename(path))
    if not match:
        raise SystemExit("Name the dump as downloaded, for example reports_oct1_2026.tar.gz")
    return match.group(1)


def handheld(record: dict[str, Any]) -> tuple[str, str] | None:
    """(device label, chip) for reports from handheld chips, else None."""
    info = record.get("systemInfo") or {}
    text = f"{info.get('cpu') or ''} {info.get('gpu') or ''}"
    for pattern, label, chip in HANDHELD_CHIPS:
        if pattern.search(text):
            return label, chip
    return None


def survey(path: str) -> None:
    count = 0
    keys = collections.Counter()
    recent = collections.Counter()
    devices = collections.Counter()
    latest = 0
    apps = set()
    for rec in records(open_dump(path)):
        count += 1
        resp = rec.get("responses") or {}
        keys.update(resp.keys())
        ts = int(rec.get("timestamp") or 0)
        latest = max(latest, ts)
        apps.add(((rec.get("app") or {}).get("steam") or {}).get("appId"))
        if ts >= 1735689600:  # 2025 onwards
            recent.update(resp.keys())
            found = handheld(rec)
            devices[found[0] if found else "other"] += 1
    print(json.dumps({"records": count, "apps": len(apps), "latest": latest,
                      "response_keys": keys.most_common(), "response_keys_2025_on": recent.most_common(),
                      "handheld_2025_on": devices.most_common()}, indent=1))


# Index


def _text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"/home/[^/\s\"']+", "~", text)
    text = re.sub(r"https?://\S+", "[link]", text)
    return text[:MAX_TEXT]


def summarise(record: dict[str, Any]) -> dict[str, Any] | None:
    resp = record.get("responses") or {}
    if resp.get("type") not in (None, "steamPlay"):
        return None
    found = handheld(record)
    if found is None:
        return None
    notes = resp.get("notes") or {}
    if isinstance(notes, str):
        notes = {"verdict": notes}
    return {
        "t": int(record.get("timestamp") or 0),
        "device": found[0],
        "apu": found[1],
        "os": _text((record.get("systemInfo") or {}).get("os"))[:60],
        "verdict": resp.get("verdict"),
        "variant": resp.get("variant"),
        "proton": _text(resp.get("customProtonVersion") or resp.get("protonVersion"))[:40] or None,
        "battery": resp.get("batteryPerformance"),
        "launch": _text(resp.get("launchOptions"))[:200] or None,
        "notes": _text(notes.get("verdict") or notes.get("extra") or resp.get("concludingNotes") or "") or None,
        "tinker": bool(resp.get("tinkerOverride") or resp.get("launchOptions")),
    }


def build(path: str, out_dir: str) -> str:
    name = dump_name(path)
    per_app: dict[str, dict[str, Any]] = {}
    total = 0
    for rec in records(open_dump(path)):
        total += 1
        app = str(((rec.get("app") or {}).get("steam") or {}).get("appId") or "")
        if not app.isdigit():
            continue
        entry = per_app.setdefault(app, {"n": 0, "works": 0, "handheld": 0, "title": "", "reports": []})
        entry["n"] += 1
        resp = rec.get("responses") or {}
        if resp.get("verdict") == "yes":
            entry["works"] += 1
        title = (rec.get("app") or {}).get("title")
        if title and not entry["title"]:
            entry["title"] = _text(title)[:80]
        summary = summarise(rec)
        if summary:
            entry["handheld"] += 1
            entry["reports"].append(summary)
    for entry in per_app.values():
        entry["reports"].sort(key=lambda r: r["t"], reverse=True)
        entry["reports"] = entry["reports"][:MAX_REPORTS_PER_APP]
    kept = {app: e for app, e in per_app.items() if e["reports"]}
    header = {
        "schema": SCHEMA,
        "dump": name,
        "source": "https://github.com/bdefore/protondb-data",
        "licence": "ODbL 1.0 (database), DbCL 1.0 (contents). Derived from ProtonDB data.",
        "attribution": "Contains information from ProtonDB, made available under the ODbL.",
        "records_read": total,
        "apps": len(kept),
    }
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, INDEX_NAME)
    with gzip.open(target, "wt", encoding="utf-8", compresslevel=9, newline="\n") as handle:
        handle.write(json.dumps(header, separators=(",", ":")) + "\n")
        for app in sorted(kept):
            handle.write(f"{app}\t{json.dumps(kept[app], separators=(',', ':'), ensure_ascii=False)}\n")
    print(f"{target}: dump {name}, {total} records, {len(per_app)} apps, {len(kept)} with handheld reports, "
          f"{os.path.getsize(target) // 1024} KB")
    return target


def publish(target: str) -> None:
    """Upload to the one rolling release, so the plugin's URL never changes."""
    if os.path.basename(target) != INDEX_NAME:
        raise SystemExit(f"Pass the {INDEX_NAME} made by the build step")
    with gzip.open(target, "rt", encoding="utf-8") as handle:
        header = json.loads(handle.readline())
    notes = (f"ProtonDB index for tuning-advisor, built locally from {header['source']} reports_{header['dump']}.tar.gz. "
             f"{header['apps']} apps with handheld reports.\n\n"
             "Contains information from ProtonDB, made available under the Open Database License (ODbL) 1.0. "
             "Contents under the Database Contents License (DbCL) 1.0. This derived index is shared under the ODbL.")
    title = f"ProtonDB index ({header['dump']})"
    exists = subprocess.run(["gh", "release", "view", RELEASE_TAG], cwd=ROOT, capture_output=True, stdin=subprocess.DEVNULL)
    if exists.returncode == 0:
        subprocess.run(["gh", "release", "upload", RELEASE_TAG, target, "--clobber"], cwd=ROOT, check=True,
                       stdin=subprocess.DEVNULL)
        subprocess.run(["gh", "release", "edit", RELEASE_TAG, "--title", title, "--notes", notes], cwd=ROOT,
                       check=True, stdin=subprocess.DEVNULL, capture_output=True)
    else:
        subprocess.run(["gh", "release", "create", RELEASE_TAG, target, "--title", title, "--notes", notes,
                        "--latest=false"], cwd=ROOT, check=True, stdin=subprocess.DEVNULL)
    print(f"published {RELEASE_TAG} with dump {header['dump']}")


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in ("survey", "build", "publish"):
        print(__doc__, file=sys.stderr)
        return 2
    if sys.argv[1] == "survey":
        survey(sys.argv[2])
    elif sys.argv[1] == "build":
        out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "out")
        build(sys.argv[2], out)
    else:
        publish(sys.argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
