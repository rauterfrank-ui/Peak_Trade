import os

import pytest

pytestmark = pytest.mark.network

# PT_PORT_BIND_GUARD: skip in sandbox unless explicitly enabled
if os.environ.get("PEAKTRADE_ALLOW_PORT_BIND_TESTS", "0") != "1":
    pytest.skip(
        "port-bind tests disabled (set PEAKTRADE_ALLOW_PORT_BIND_TESTS=1 to enable)",
        allow_module_level=True,
    )
try:
    import socket as _pt_sock
    with _pt_sock.socket() as _s:
        _s.bind(("127.0.0.1", 0))
except (PermissionError, OSError):
    pytest.skip("port-bind not permitted in this environment (sandbox)", allow_module_level=True)

import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _PromHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send(self, code: int, body: str, *, content_type: str = "application/json") -> None:
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/-/ready":
            self._send(
                200, "Prometheus Server is Ready.\n", content_type="text/plain; charset=utf-8"
            )
            return

        if self.path.startswith("/api/v1/query"):
            q = parse_qs(urlparse(self.path).query).get("query", [""])[0]

            # Provide a non-empty response for the demo script's required queries.
            if q.startswith('up{job=~"ai_live|peak_trade_web|shadow_mvs"}'):
                payload = {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [
                            {"metric": {"job": "ai_live"}, "value": [0, "1"]},
                            {"metric": {"job": "peak_trade_web"}, "value": [0, "1"]},
                            {"metric": {"job": "shadow_mvs"}, "value": [0, "1"]},
                        ],
                    },
                }
                self._send(200, json.dumps(payload))
                return

            if q == "peaktrade_ai_live_heartbeat":
                payload = {
                    "status": "success",
                    "data": {"resultType": "vector", "result": [{"metric": {}, "value": [0, "1"]}]},
                }
                self._send(200, json.dumps(payload))
                return

            if q == "peaktrade_ai_decisions_total":
                payload = {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [
                            {
                                "metric": {"decision": "accept", "run_id": "demo"},
                                "value": [0, "1"],
                            },
                            {
                                "metric": {"decision": "reject", "run_id": "demo"},
                                "value": [0, "1"],
                            },
                        ],
                    },
                }
                self._send(200, json.dumps(payload))
                return

            if q == "peaktrade_ai_actions_total":
                payload = {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [{"metric": {"run_id": "demo"}, "value": [0, "1"]}],
                    },
                }
                self._send(200, json.dumps(payload))
                return

            if q == "count(count by (run_id) (peaktrade_ai_decisions_total))":
                payload = {
                    "status": "success",
                    "data": {"resultType": "vector", "result": [{"metric": {}, "value": [0, "1"]}]},
                }
                self._send(200, json.dumps(payload))
                return

            if q == "peaktrade_ai_last_event_timestamp_seconds_by_run_id":
                payload = {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [{"metric": {"run_id": "demo"}, "value": [0, "1"]}],
                    },
                }
                self._send(200, json.dumps(payload))
                return

            # Default: success, but empty.
            payload = {"status": "success", "data": {"resultType": "vector", "result": []}}
            self._send(200, json.dumps(payload))
            return

        self._send(404, json.dumps({"error": "not found"}))


class _ExporterHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send(
        self, code: int, body: str, *, content_type: str = "text/plain; charset=utf-8"
    ) -> None:
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/metrics":
            # Minimal exporter snapshot the demo script validates (accept + reject for run_id=demo).
            body = (
                "# HELP peaktrade_ai_decisions_total Total number of AI decisions made.\n"
                "# TYPE peaktrade_ai_decisions_total counter\n"
                'peaktrade_ai_decisions_total{component="execution_watch",decision="accept",reason="none",run_id="demo"} 1\n'
                'peaktrade_ai_decisions_total{component="execution_watch",decision="reject",reason="risk_limit",run_id="demo"} 1\n'
            )
            self._send(200, body)
            return
        self._send(404, "not found\n")


def test_ai_live_activity_demo_produces_file_backed_proof(tmp_path: Path) -> None:
    # Start a minimal fake Prometheus API server.
    prom_port = _free_port()
    prom = HTTPServer(("127.0.0.1", prom_port), _PromHandler)
    t = threading.Thread(target=prom.serve_forever, daemon=True)
    t.start()

    # Start a minimal fake exporter /metrics endpoint (hermetic).
    exporter_port = _free_port()
    exporter = HTTPServer(("127.0.0.1", exporter_port), _ExporterHandler)
    te = threading.Thread(target=exporter.serve_forever, daemon=True)
    te.start()

    try:
        out_dir = tmp_path / "out"
        jsonl = tmp_path / "events.jsonl"
        jsonl.write_text("", encoding="utf-8")
        demo = PROJECT_ROOT / "scripts" / "obs" / "ai_live_activity_demo.sh"
        demo_env = os.environ.copy()
        demo_env["PROM_URL"] = f"http://127.0.0.1:{prom_port}"
        demo_env["EXPORTER_URL"] = f"http://127.0.0.1:{exporter_port}/metrics"
        demo_env["RUN_ID"] = "demo"
        demo_env["COMPONENT"] = "execution_watch"
        demo_env["VERIFY_OUT_DIR"] = str(out_dir)
        demo_env["EVENTS_JSONL"] = str(jsonl)
        demo_env["SKIP_EXPORTER_START"] = "1"
        demo_env["SKIP_PORT_CHECK"] = "1"

        res = subprocess.run(
            ["bash", str(demo)], env=demo_env, capture_output=True, text=True, timeout=30
        )
        assert res.returncode == 0, f"stdout:\n{res.stdout}\n\nstderr:\n{res.stderr}"

        summary = (out_dir / "AI_ACTIVITY_DEMO_SUMMARY.txt").read_text(encoding="utf-8")
        assert "hard_ok=True" in summary

        # File-backed proof: exporter snapshot contains accept+reject for run_id=demo.
        metrics = (out_dir / "exporter_metrics.txt").read_text(encoding="utf-8", errors="replace")
        assert "peaktrade_ai_decisions_total" in metrics
        assert 'decision="accept"' in metrics and 'run_id="demo"' in metrics
        assert 'decision="reject"' in metrics and 'run_id="demo"' in metrics

        # Deterministic activity generation: events JSONL contains accept + reject under run_id=demo.
        events_txt = jsonl.read_text(encoding="utf-8")
        assert '"decision":"accept"' in events_txt and '"run_id":"demo"' in events_txt
        assert '"decision":"reject"' in events_txt and '"run_id":"demo"' in events_txt

        # Prom snapshots exist (file-backed).
        for name in [
            "up_jobs",
            "hb",
            "decisions",
            "actions",
            "run_id_count",
            "last_event_ts_by_run_id",
        ]:
            p = out_dir / "prom" / f"{name}.json"
            assert p.exists()
            doc = json.loads(p.read_text(encoding="utf-8"))
            assert doc.get("status") == "success"
    finally:
        exporter.shutdown()
        exporter.server_close()
        prom.shutdown()
        prom.server_close()
