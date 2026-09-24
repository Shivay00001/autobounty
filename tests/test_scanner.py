"""Tests use REAL local servers — no mocks of the network layer.

- header audit + robots checks run against a local HTTP server with known headers
- port scan runs against a real open TCP port and a real closed one
- TLS check runs against a local TLS server with a real self-signed cert
"""

import http.server
import os
import socket
import ssl
import subprocess
import threading

import pytest

# loopback must bypass the sandbox egress proxy (its NO_PROXY pattern breaks
# httpx's parser, so we set a clean one here for the local test servers)
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"

import scanner


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, body: bytes, ctype="text/html"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/robots.txt":
            self._send(b"User-agent: *\nDisallow: /admin\n", "text/plain")
        elif self.path == "/sitemap.xml":
            self._send(b"<urlset/>", "application/xml")
        else:
            self._send(b"<html>hi</html>")

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def http_host():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"127.0.0.1:{srv.server_port}"
    srv.shutdown()


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def test_headers_audit_reports_missing_and_present(http_host):
    res = scanner.check_headers(http_host)
    assert res["check"] == "security-headers"
    assert res["observations"]["status_code"] == 200
    titles = [f["finding"] for f in res["findings"]]
    # our test server sends X-Content-Type-Options but not HSTS/CSP
    assert any("Strict-Transport-Security" in t for t in titles)
    assert not any("X-Content-Type-Options" in t for t in titles)


def test_robots_exposure_noted(http_host):
    res = scanner.check_robots(http_host)
    titles = [f["finding"] for f in res["findings"]]
    assert any("robots.txt exposed (observed: HTTP 200" in t for t in titles), titles
    assert any("1 Disallow rules" in t for t in titles), titles


def test_port_scan_real_open_and_closed():
    open_port = _free_port()
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", open_port))
    srv.listen(1)
    closed_port = _free_port()  # nothing listening
    try:
        res = scanner.check_ports("127.0.0.1", ports=[open_port, closed_port])
    finally:
        srv.close()
    assert res["observations"]["open"] == [open_port]
    assert res["observations"]["closed_or_filtered"] == [closed_port]
    assert any(f"port {open_port} reachable (observed" in f["finding"]
               for f in res["findings"])


def test_port_scan_inconclusive_when_everything_connects(monkeypatch):
    # simulate an intercepting middlebox: every connect "succeeds"
    class FakeSock:
        def settimeout(self, t): pass
        def recv(self, n): return b""
        def close(self): pass
    monkeypatch.setattr(
        scanner.socket, "create_connection", lambda *a, **k: FakeSock()
    )
    res = scanner.check_ports("10.0.0.1", ports=[21, 22, 80, 443])
    assert res["observations"].get("verdict") == "INCONCLUSIVE"
    assert res["findings"] == []
    assert "intercepting" in res["observations"]["note"]


def test_tls_reports_real_expiry(tmp_path):
    key = tmp_path / "k.pem"
    crt = tmp_path / "c.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(key), "-out", str(crt), "-days", "10",
         "-subj", "/CN=127.0.0.1"],
        check=True, capture_output=True,
    )
    port = _free_port()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(crt), str(key))
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(1)
    stop = threading.Event()

    def serve():
        while not stop.is_set():
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            try:
                with ctx.wrap_socket(conn, server_side=True) as tls:
                    tls.recv(1024)
            except Exception:
                pass

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    try:
        res = scanner.check_tls("127.0.0.1", port=port)
    finally:
        stop.set()
        srv.close()
    obs = res["observations"]
    assert obs["subject_CN"] == "127.0.0.1"
    assert 9.0 < obs["days_until_expiry"] <= 10.0
    assert any("expires in" in f["finding"] for f in res["findings"])
    assert all(f["severity"] == "medium" for f in res["findings"])


def test_scan_rejects_bad_target():
    import app as appmod  # noqa
    from fastapi.testclient import TestClient

    c = TestClient(appmod.app)
    r = c.post("/scan", json={"target": "not a host!!"})
    assert r.status_code == 400
