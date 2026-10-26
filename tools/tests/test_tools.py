import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import check_fixtures  # noqa: E402
import check_readonly  # noqa: E402
import check_secrets  # noqa: E402
from sanitise_fixture import sanitise  # noqa: E402

REAL_HASH = "8c212779b4abde7c6bc608063a0d008b7e40ce32"
# Test addresses are built at runtime so the source itself holds none.
LAN_A = ".".join(["10", "0", "0", "12"])
LAN_B = ".".join(["10", "1", "2", "3"])
LAN_C = ".".join(["192", "168", "1", "20"])
WAN = ".".join(["81", "2", "69", "160"])
# A key-shaped test value, built at runtime so secret scanners see no literal.
FAKE_KEY = "A1b2C3d4" * 4


def test_sanitise_replaces_identifying_values_consistently():
    raw = {
        "torrents": {REAL_HASH: {"name": "Some.Show.S01E01", "save_path": "/home/deck/Downloads", "hash": REAL_HASH,
                                 "tracker": "http://tracker.example.net:6969/announce"}},
        "server_state": {"last_external_address_v4": WAN, "dl_info_speed": 12},
        "note": f"seen at {LAN_A} and nas.lan",
    }
    out = sanitise(raw)
    blob = json.dumps(out)
    for leaked in (REAL_HASH, "Some.Show", "/home/deck", WAN, LAN_A, "nas.lan", "tracker.example"):
        assert leaked not in blob
    (key,) = out["torrents"].keys()
    assert out["torrents"][key]["hash"] == key
    assert out["server_state"]["dl_info_speed"] == 12


def test_sanitised_output_passes_the_fixture_guard(tmp_path):
    raw = {"x": {REAL_HASH: {"name": "n", "ip": LAN_B, "k": FAKE_KEY}}}
    path = tmp_path / "fixtures" / "f.json"
    path.parent.mkdir()
    path.write_text(json.dumps(sanitise(raw)))
    assert check_fixtures.scan_file(str(path)) == []


def test_guard_flags_planted_offenders(tmp_path):
    path = tmp_path / "fixtures" / "bad.json"
    path.parent.mkdir()
    path.write_text('{"ip": "%s", "key": "%s", "ok": "192.0.2.5"}\n' % (LAN_C, FAKE_KEY))
    problems = check_fixtures.scan_file(str(path))
    assert len(problems) == 2
    assert check_fixtures.fixture_files(str(tmp_path)) == [str(path)]


def test_readonly_guard_catches_each_setter(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    lines = [
        "SteamClient.Apps.SetAppLaunchOptions(1, 'x')",
        "SteamClient.Apps.SpecifyCompatTool(1, 'proton')",
        "SteamClient.Settings.SetSetting('a', 1)",
        "window.SteamClient?.System?.SetPowerMode(1)",
        "store.UpdateSettings({})",
        "import subprocess",
    ]
    (src / "bad.ts").write_text("\n".join(lines) + "\n")
    (src / "ok.ts").write_text("const x = SteamClient.Apps.GetLaunchOptionsForApp(1)\n")
    problems = check_readonly.scan(str(tmp_path))
    flagged = {p.rsplit(":", 2)[-2] for p in problems}
    assert flagged == {str(n) for n in range(1, len(lines) + 1)}
    assert all("bad.ts" in p for p in problems)


def test_readonly_guard_refuses_an_empty_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["check_readonly.py", str(tmp_path)])
    assert check_readonly.main() == 1


def test_mock_sabnzbd_keys_and_incremental_history():
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", "shared", "py"))
    import mock_sabnzbd
    from plugin_core.http import HttpClient, parse_base_url

    key, nzb = "a" * 32, "b" * 32
    mock = mock_sabnzbd.MockSab(api_key=key, nzb_key=nzb)
    mock.start()
    try:
        client = HttpClient(parse_base_url(mock.url))

        def call(**params):
            return client.get("api", params={"output": "json", **params}).json()

        def denied(**params):
            res = client.get("api", params={"output": "json", **params})
            return res.status, res.text()

        assert call(mode="version")["version"] == "5.1.3"
        assert denied(mode="queue") == (403, "API Key Required")
        assert denied(mode="queue", apikey="x") == (403, "API Key Incorrect")
        assert denied(mode="queue", apikey=nzb) == (403, "API Key Incorrect")
        queue = call(mode="queue", apikey=key, start=0, limit=8)["queue"]
        assert queue["noofslots_total"] == 2 and isinstance(queue["slots"][0]["percentage"], str)
        first = call(mode="history", apikey=key, limit=10)["history"]
        assert call(mode="history", apikey=key, limit=10, last_history_update=first["last_history_update"])["history"] is False
        mock.state.config_locked = True
        assert call(mode="config", name="speedlimit", value="50", apikey=key)["error"] == "Configuration locked"
    finally:
        mock.stop()


def test_secret_check_flags_each_format_and_allows_placeholders():
    # Built from parts so this file holds no literal key.
    planted = [
        "-----BEGIN RSA " + "PRIVATE KEY-----",
        "token = " + "ghp_" + "A1b2C3d4E5" * 4,
        "AKIA" + "ABCDEFGH12345678",
        "sk-ant-" + "api03-Zx9Yw8Vu7Ts6Rq5Po4Nm3",
        "AIza" + "SyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q",
        "qbt_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4",
        'api_key = "' + "Zx9Yw8Vu7Ts6Rq5Po4" + '"',
    ]
    problems = check_secrets.scan_text("f.py", chr(10).join(planted))
    assert {int(p.split(":")[1]) for p in problems} == set(range(1, len(planted) + 1))
    safe = ["qbt_" + "k" * 28, 'api_key = "' + "f" * 32 + '"', 'password = "pw"', "sk-not-a-key"]
    assert check_secrets.scan_text("f.py", chr(10).join(safe)) == []


def test_secret_check_refuses_an_empty_repo(tmp_path, monkeypatch):
    import subprocess as sp

    sp.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.setattr(sys, "argv", ["check_secrets.py", str(tmp_path)])
    assert check_secrets.main() == 1
