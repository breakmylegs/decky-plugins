import asyncio
import json
import os
import socket
import ssl
import stat
import sys
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from plugin_core import errors
from plugin_core import http as core_http
from plugin_core.conntest import Report, check_url
from plugin_core.http import HttpClient, parse_base_url, port_warning
from plugin_core.poller import (
    BACKOFF_MAX,
    HIDDEN_INTERVAL,
    OFFLINE,
    ONLINE,
    VISIBLE_INTERVAL,
    Poller,
)
from plugin_core.secrets import SecretStore, mask, read_import_file
from plugin_core.settings import JsonStore
from plugin_core.update_check import UpdateChecker, parse_version


# URL parsing and the port warning


@pytest.mark.parametrize(
    "raw,host,port,prefix",
    [
        ("http://localhost:8090", "localhost", 8090, ""),
        ("http://127.0.0.1:8090/", "127.0.0.1", 8090, ""),
        ("http://192.0.2.10:8080", "192.0.2.10", 8080, ""),
        ("https://qbt.example.com", "qbt.example.com", 443, ""),
        ("http://nas.example.com/sabnzbd/", "nas.example.com", 80, "/sabnzbd"),
        ("http://[::1]:9000", "::1", 9000, ""),
    ],
)
def test_parse_base_url(raw, host, port, prefix):
    base = parse_base_url(raw)
    assert (base.host, base.port, base.prefix) == (host, port, prefix)


@pytest.mark.parametrize(
    "raw",
    ["", "192.0.2.10:8080", "ftp://x", "http://user:pw@host", "http://host:99999", "http://bad_host", "http://h/?a=1"],
)
def test_parse_base_url_rejects(raw):
    with pytest.raises(ValueError):
        parse_base_url(raw)


def test_port_warning_only_for_local_8080():
    assert port_warning(parse_base_url("http://localhost:8080"))
    assert port_warning(parse_base_url("http://127.0.0.1:8080"))
    assert port_warning(parse_base_url("http://localhost:8090")) is None
    assert port_warning(parse_base_url("http://192.0.2.10:8080")) is None


def test_conntest_reports_url_failure():
    report = Report()
    assert check_url(report, "not a url") is None
    assert report.failed_step == "url"


def test_conntest_warns_on_8080():
    report = Report()
    assert check_url(report, "http://localhost:8080") is not None
    assert report.warnings and "8090" in report.warnings[0]


# Error classification


def test_classify_kinds():
    assert errors.classify(urllib.error.URLError(socket.gaierror())).kind == errors.DNS
    assert errors.classify(urllib.error.URLError(ConnectionRefusedError())).kind == errors.REFUSED
    assert errors.classify(urllib.error.URLError(socket.timeout())).kind == errors.TIMEOUT
    assert errors.classify(TimeoutError()).kind == errors.TIMEOUT
    import ssl

    assert errors.classify(urllib.error.URLError(ssl.SSLError())).kind == errors.TLS
    assert errors.classify(urllib.error.URLError(OSError(101, "unreachable"))).kind == errors.OFFLINE
    assert errors.classify(ValueError()).kind == errors.BAD_RESPONSE
    assert errors.from_status(401).kind == errors.AUTH
    assert errors.from_status(403).kind == errors.FORBIDDEN
    assert errors.from_status(500).kind == errors.HTTP_ERROR


def test_every_kind_has_a_message():
    for kind in errors.KINDS:
        assert errors.MESSAGES[kind]


# HTTP client against a local server


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/json"):
            body = json.dumps({"ok": True, "auth": self.headers.get("Authorization"),
                               "ua": self.headers.get("User-Agent")}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "QBT_SID_1=abc; path=/")
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/cookie"):
            body = json.dumps({"cookie": self.headers.get("Cookie")}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture()
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_http_json_headers_and_status(server):
    client = HttpClient(parse_base_url(server), headers={"Authorization": "Bearer k"})
    res = client.get("json")
    assert res.status == 200 and res.json()["auth"] == "Bearer k"
    assert client.get("missing").status == 404


def test_http_form_encoding(server):
    client = HttpClient(parse_base_url(server))
    res = client.post("form", form={"hashes": "a|b", "deleteFiles": False, "skip": None})
    assert res.text() == "hashes=a%7Cb&deleteFiles=false"


def test_http_json_body(server):
    client = HttpClient(parse_base_url(server))
    res = client.post("echo", json_body={"model": "m", "n": 1})
    assert json.loads(res.text()) == {"model": "m", "n": 1}


def test_http_cookie_jar_replays_any_cookie_name(server):
    client = HttpClient(parse_base_url(server), use_cookies=True)
    client.get("json")
    assert client.get("cookie").json()["cookie"] == "QBT_SID_1=abc"


def test_http_refused_is_classified():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    client = HttpClient(parse_base_url(f"http://127.0.0.1:{port}"), timeout=2)
    with pytest.raises(errors.PluginError) as info:
        client.get("x")
    # Windows retries a refused SYN until the timeout. Linux, where Decky runs, refuses at once.
    expected = (errors.REFUSED, errors.TIMEOUT) if sys.platform == "win32" else (errors.REFUSED,)
    assert info.value.kind in expected


# Settings and secrets


def test_json_store_defaults_types_and_atomic_save(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"base_url": 5, "notify": False, "stale": 1}))
    store = JsonStore(str(path), {"base_url": "", "notify": True})
    assert store.get("base_url") == "" and store.get("notify") is False
    assert store.update({"base_url": "http://x", "unknown": 1}) == ["base_url"]
    assert json.loads(path.read_text()) == {"base_url": "http://x", "notify": False}
    with pytest.raises(ValueError):
        store.update({"notify": "yes"})
    if sys.platform != "win32":
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert not [p for p in os.listdir(tmp_path) if p.startswith(".tmp-")]


def test_secret_store_never_exposes_values(tmp_path):
    store = SecretStore(str(tmp_path / "secrets.json"), ["api_key", "password"])
    store.set("api_key", "abcdefghijklmnop")
    view = store.public_view()
    assert view["api_key"] == {"set": True, "masked": "****mnop"}
    assert view["password"] == {"set": False, "masked": ""}
    assert "abcdefghijklmnop" not in json.dumps(view)
    store.set("api_key", "  ")
    assert not store.has("api_key")
    with pytest.raises(ValueError):
        store.set("other", "x")


def test_mask_hides_short_secrets():
    assert mask("short") == "set"
    assert mask("") == ""


def test_import_file_validation(tmp_path):
    path = tmp_path / "plugin.json"
    with pytest.raises(ValueError, match="No import file"):
        read_import_file(str(path), ["base_url"], ["api_key"])
    path.write_text("{bad")
    with pytest.raises(ValueError, match="not valid JSON"):
        read_import_file(str(path), ["base_url"], ["api_key"])
    path.write_text(json.dumps({"api_key": "secretvalue", "nope": 1}))
    with pytest.raises(ValueError) as info:
        read_import_file(str(path), ["base_url"], ["api_key"])
    assert "nope" in str(info.value) and "secretvalue" not in str(info.value)
    path.write_text(json.dumps({"api_key": "k", "base_url": "http://x"}))
    assert read_import_file(str(path), ["base_url"], ["api_key"]) == ({"base_url": "http://x"}, {"api_key": "k"})


# Poller


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_poller_intervals_and_backoff():
    poller = Poller(None, None, None)
    assert poller.interval() == HIDDEN_INTERVAL
    poller.set_visible(True)
    poller.set_game_running(True)
    assert poller.interval() == VISIBLE_INTERVAL
    poller.failures = 1
    assert poller.interval() == 5
    poller.failures = 4
    assert poller.interval() == 40
    poller.failures = 20
    assert poller.interval() == BACKOFF_MAX


def test_poller_goes_offline_once_and_recovers():
    statuses, data = [], []
    fail = {"on": True}

    async def fetch():
        if fail["on"]:
            raise errors.PluginError(errors.TIMEOUT)
        return {"n": 1}

    async def on_data(d):
        data.append(d)

    async def on_status(s):
        statuses.append(s["state"])

    poller = Poller(fetch, on_data, on_status)

    async def scenario():
        for _ in range(6):
            await poller.poll_once()
        fail["on"] = False
        await poller.poll_once()
        await poller.poll_once()

    _run(scenario())
    assert statuses.count(OFFLINE) == 1
    assert statuses[-1] == ONLINE
    assert data == [{"n": 1}, {"n": 1}]
    assert poller.failures == 0


def test_poller_auth_error_is_not_offline():
    statuses = []

    async def fetch():
        raise errors.PluginError(errors.AUTH)

    async def noop(_):
        pass

    async def on_status(s):
        statuses.append(s)

    poller = Poller(fetch, noop, on_status)

    async def scenario():
        for _ in range(4):
            await poller.poll_once()

    _run(scenario())
    assert [s["state"] for s in statuses] == ["error"]
    assert statuses[0]["error"]["kind"] == "auth"


# Update check


def test_update_checker_daily_and_compare(tmp_path):
    calls = []
    now = {"t": 1000.0}

    def fetch(url):
        calls.append(url)
        return {"tag_name": "v0.2.0"}

    checker = UpdateChecker(
        {"repo": "owner/mirror", "asset": "p.zip"}, "0.1.0", str(tmp_path / "u.json"), fetch, now=lambda: now["t"]
    )
    result = checker.check()
    assert result["available"] and result["latest"] == "0.2.0"
    assert result["install_url"] == "https://github.com/owner/mirror/releases/latest/download/p.zip"
    checker.check()
    assert len(calls) == 1
    now["t"] += 86400
    checker.check()
    assert len(calls) == 2


def test_update_checker_without_build_info_does_nothing(tmp_path):
    checker = UpdateChecker({}, "0.1.0", str(tmp_path / "u.json"), lambda url: 1 / 0)
    assert checker.check() == {"current": "0.1.0", "latest": None, "available": False, "install_url": None,
                               "checked_at": None, "check_failed": False}


def test_update_checker_survives_fetch_failure(tmp_path):
    def fetch(url):
        raise errors.PluginError(errors.OFFLINE)

    checker = UpdateChecker({"repo": "o/m", "asset": "a.zip"}, "0.1.0", str(tmp_path / "u.json"), fetch,
                            now=lambda: 5000.0)
    result = checker.check()
    assert result["available"] is False
    # The panel says the check failed, instead of "you have the latest".
    assert result["check_failed"] is True and result["checked_at"] == 5000.0
    assert result["install_url"] == "https://github.com/o/m/releases/latest/download/a.zip"


def test_update_checker_known_needs_no_network(tmp_path):
    def fetch(url):
        return {"tag_name": "v0.3.0"}

    path = str(tmp_path / "u.json")
    UpdateChecker({"repo": "o/m", "asset": "a.zip"}, "0.1.0", path, fetch, now=lambda: 10.0).check()
    offline = UpdateChecker({"repo": "o/m", "asset": "a.zip"}, "0.1.0", path, lambda url: 1 / 0)
    known = offline.known()
    assert known["latest"] == "0.3.0" and known["available"] and known["checked_at"] == 10.0
    assert known["check_failed"] is False
    # Never checked: still has the version and the install link.
    fresh = UpdateChecker({"repo": "o/m", "asset": "a.zip"}, "0.1.0", str(tmp_path / "none.json"), lambda url: 1 / 0)
    assert fresh.known()["install_url"] and fresh.known()["latest"] is None


def test_parse_version():
    assert parse_version("qbittorrent-monitor-v1.2.3") == (1, 2, 3)
    assert parse_version("nope") is None


class _Paths:
    def __init__(self, cafile, capath):
        self.cafile = cafile
        self.capath = capath


def test_default_ca_file_keeps_working_defaults(monkeypatch, tmp_path):
    good = tmp_path / "ca.pem"
    good.write_text("x")
    monkeypatch.setattr(core_http.ssl, "get_default_verify_paths", lambda: _Paths(str(good), None))
    assert core_http.default_ca_file((str(good),)) is None


def test_default_ca_file_finds_system_bundle_when_defaults_missing(monkeypatch, tmp_path):
    # Decky's bundled Python on SteamOS: the default paths point at the build machine.
    monkeypatch.setattr(core_http.ssl, "get_default_verify_paths",
                        lambda: _Paths("/usr/lib/ssl/cert.pem", "/usr/lib/ssl/certs"))
    bundle = tmp_path / "ca-certificates.crt"
    bundle.write_text("x")
    assert core_http.default_ca_file((str(tmp_path / "missing.pem"), str(bundle))) == str(bundle)


def test_default_ca_file_falls_back_to_certifi(monkeypatch, tmp_path):
    monkeypatch.setattr(core_http.ssl, "get_default_verify_paths", lambda: _Paths(None, None))
    fake = type(sys)("certifi")
    fake.where = lambda: "/bundle/certifi.pem"
    monkeypatch.setitem(sys.modules, "certifi", fake)
    assert core_http.default_ca_file((str(tmp_path / "missing.pem"),)) == "/bundle/certifi.pem"



def test_tls_error_carries_openssl_reason_and_ca_source():
    err = ssl.SSLCertVerificationError(1, "certificate verify failed")
    err.reason = "CERTIFICATE_VERIFY_FAILED"
    err.verify_message = "unable to get local issuer certificate"
    classified = errors.classify(urllib.error.URLError(err))
    assert classified.kind == errors.TLS
    assert classified.to_dict()["detail"] == "CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate"
    # Other kinds keep their dict shape.
    assert "detail" not in errors.PluginError(errors.AUTH, "HTTP 401").to_dict()


def test_certificate_load_failure_is_reported_on_request(tmp_path):
    missing = str(tmp_path / "missing-ca.pem")
    client = HttpClient(parse_base_url("https://example.invalid"), tls=core_http.TlsOptions(ca_file=missing))
    with pytest.raises(errors.PluginError) as info:
        client.get("/x")
    assert info.value.kind == errors.TLS
    detail = info.value.to_dict()["detail"]
    assert "could not load certificates" in detail and f"CA file {missing}" in detail


def test_requests_name_the_plugin_not_python(server, monkeypatch):
    # Cloudflare in front of Deck Verified answers 403 to "Python-urllib/3.x".
    monkeypatch.setattr(core_http, "USER_AGENT", core_http.USER_AGENT)
    ua = core_http.set_user_agent({"plugin": "tuning-advisor", "monorepo": "example/decky-plugins"}, "0.7.2")
    assert ua == "tuning-advisor/0.7.2 (+https://github.com/example/decky-plugins)"
    got = HttpClient(parse_base_url(server)).get("json").json()["ua"]
    assert got == ua and "urllib" not in got.lower()
    # A caller's own header still wins.
    own = HttpClient(parse_base_url(server), headers={"User-Agent": "own/1"}).get("json").json()["ua"]
    assert own == "own/1"
