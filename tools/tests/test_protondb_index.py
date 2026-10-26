import gzip
import io
import json
import os
import sys
import tarfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import protondb_index as pdb  # noqa: E402


def report(appid, cpu, verdict="yes", ts=1790000000, **resp):
    return {"app": {"steam": {"appId": str(appid)}, "title": f"Game {appid}"}, "timestamp": ts,
            "systemInfo": {"cpu": cpu, "gpu": "", "os": "SteamOS Holo"},
            "responses": {"verdict": verdict, "type": "steamPlay", **resp}}


def make_dump(tmp_path, items, name="reports_oct1_2026.tar.gz"):
    data = json.dumps(items, indent=2, ensure_ascii=False).encode("utf-8")
    path = tmp_path / name
    with tarfile.open(path, "w:gz") as tar:
        info = tarfile.TarInfo(pdb.MEMBER)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return str(path)


def test_records_streams_across_tiny_chunks_and_multibyte_text():
    items = [{"a": i, "text": "café ünïcode " * (i + 1), "nested": [1, {"b": [2, 3]}]} for i in range(50)]
    text = io.StringIO(json.dumps(items, indent=1, ensure_ascii=False))
    got = list(pdb.records(text, chunk=7))
    assert got == items


def test_records_rejects_non_array_and_truncated_input():
    with pytest.raises(ValueError):
        list(pdb.records(io.StringIO('{"a": 1}')))
    with pytest.raises(ValueError):
        list(pdb.records(io.StringIO('[{"a": 1}, {"b": '), chunk=4))
    assert list(pdb.records(io.StringIO("[]"))) == []


@pytest.mark.parametrize("cpu,label", [
    ("AMD Custom APU 0405", "Steam Deck LCD"),
    ("AMD Custom APU 0932", "Steam Deck OLED"),
    ("AMD Ryzen Z1 Extreme", "Handheld with Ryzen Z1 Extreme"),
    ("AMD Ryzen Z1", "Handheld with Ryzen Z1"),
    ("AMD Ryzen AI Z2 Extreme", "Handheld with Ryzen Z2 Extreme"),
    ("AMD Ryzen Z2 Go", "Handheld with Ryzen Z2 Go"),
    ("AMD Ryzen Z2 A", "Handheld with Ryzen Z2 A"),
    ("AMD Ryzen Z2", "Handheld with Ryzen Z2"),
    ("AMD Ryzen 7 7840HS", None),
    ("Intel Core i5-6600K", None),
])
def test_handheld_chips(cpu, label):
    found = pdb.handheld(report(1, cpu))
    assert (found[0] if found else None) == label


def test_build_writes_sorted_lines_with_header_and_scrubbed_text(tmp_path):
    items = [
        report(620, "AMD Custom APU 0405", launchOptions="/home/alice/run.sh %command%",
               notes={"verdict": "great, see https://example.com/x"}, variant="ge", customProtonVersion="GE-Proton10-34"),
        report(620, "Intel Core i7", verdict="no"),
        report(30, "AMD Ryzen Z1 Extreme", ts=1790000500, notes={"verdict": "fine"}),
        report(999, "Intel Core i7"),
    ] + [report(620, "AMD Custom APU 0932", ts=1700000000 + i) for i in range(8)]
    out = pdb.build(make_dump(tmp_path, items), str(tmp_path / "out"))
    assert os.path.basename(out) == pdb.INDEX_NAME
    with gzip.open(out, "rt", encoding="utf-8") as handle:
        header = json.loads(handle.readline())
        lines = handle.read().splitlines()
    assert header["dump"] == "oct1_2026" and header["records_read"] == 12 and "ODbL" in header["licence"]
    assert [line.split("\t")[0] for line in lines] == ["30", "620"], "999 has no handheld reports"
    entry = json.loads(lines[1].split("\t", 1)[1])
    assert entry["n"] == 10 and entry["works"] == 9 and entry["handheld"] == 9
    assert len(entry["reports"]) == pdb.MAX_REPORTS_PER_APP
    newest = entry["reports"][0]
    assert newest["device"] == "Steam Deck LCD" and newest["proton"] == "GE-Proton10-34"
    assert newest["launch"] == "~/run.sh %command%" and "[link]" in newest["notes"]
    assert "/home/" not in lines[1] and "example.com" not in lines[1]


def test_dump_name_required(tmp_path):
    with pytest.raises(SystemExit):
        pdb.dump_name(str(tmp_path / "dump.tar.gz"))
    assert pdb.dump_name("reports_oct1_2026.tar.gz") == "oct1_2026"
