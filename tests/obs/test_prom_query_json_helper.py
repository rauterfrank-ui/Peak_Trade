from __future__ import annotations

import pytest

pytestmark = pytest.mark.network

import subprocess
import threading
import urllib.parse
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class _State:
    calls: int = 0


class _Handler(BaseHTTPRequestHandler):
    server_version = "pt-test/1.0"

    @property
    def state(self) -> _State:
        return self.server.state  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/v1/query":
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        self.state.calls += 1

        # First two calls: return non-JSON / empty to simulate transient bad reads.
        if self.state.calls == 1:
            body = b""
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.state.calls == 2:
            body = b"<html>not json</html>"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Third call: valid Prometheus JSON.
        body = b'{"status":"success","data":{"resultType":"vector","result":[]}}'
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _start_server() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    state = _State()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.state = state  # type: ignore[attr-defined]
    host, port = srv.server_address
    t = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    t.start()
    return srv, t, f"http://{host}:{port}"


def test_prom_query_json_helper_retries_and_succeeds(tmp_path) -> None:
    srv, _, base = _start_server()
    try:
        out = tmp_path / "out.json"
        proc = subprocess.run(
            [
                "bash",
                "scripts/obs/_prom_query_json.sh",
                "--base",
                base,
                "--query",
                "up",
                "--out",
                str(out),
                "--retries",
                "5",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
        # Deterministic diagnostics on stderr.
        assert (
            "PROM_QUERY_RETRY attempt=1 " in proc.stderr
            or "PROM_QUERY_RETRY attempt=1" in proc.stderr
        )
        assert "PROM_QUERY_OK bytes=" in proc.stderr
        assert out.exists()
        assert '"status":"success"' in out.read_text(encoding="utf-8")
    finally:
        srv.shutdown()
        srv.server_close()


def test_prom_query_json_helper_supports_positional_alias(tmp_path) -> None:
    srv, _, base = _start_server()
    try:
        out = tmp_path / "out.json"
        proc = subprocess.run(
            [
                "bash",
                "scripts/obs/_prom_query_json.sh",
                base,
                "up",
                "--out",
                str(out),
                "--retries",
                "5",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
        assert "PROM_QUERY_OK bytes=" in proc.stderr
        assert out.exists()
        assert '"status":"success"' in out.read_text(encoding="utf-8")
    finally:
        srv.shutdown()
        srv.server_close()
