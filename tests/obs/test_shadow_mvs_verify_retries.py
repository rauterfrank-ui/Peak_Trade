"""
Snapshot-only tests for Shadow MVS verify retries/warmup.

We do NOT start docker compose here. Instead we stub the HTTP endpoints that
the (now removed) shadow_mvs_local_verify.sh used to talk to:
- Exporter (/metrics)
- Prometheus (/-/ready, /api/v1/targets, /api/v1/query)
- Grafana (/api/health, /api/datasources, /api/search)

Goal:
- Verify succeeds with bounded retries when endpoints are briefly "not ready".
- Validate `targets_retry` emits attempts_used and that warmup queries retry.
"""

from __future__ import annotations

import json
import os

import pytest

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
import re
import subprocess
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

pytestmark = pytest.mark.network


@dataclass
class _State:
    grafana_health_calls: int = 0
    prom_targets_calls: int = 0
    prom_query_calls: dict[str, int] = field(default_factory=dict)


class _Handler(BaseHTTPRequestHandler):
    server_version = "pt-test/1.0"

    def _json(self, code: int, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, code: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    @property
    def state(self) -> _State:
        return self.server.state  # type: ignore[attr-defined]

    @property
    def kind(self) -> str:
        return self.server.kind  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if self.kind == "exporter":
            if path not in ("/metrics", "/"):
                self._text(HTTPStatus.NOT_FOUND, "not found\n")
                return
            self._text(
                HTTPStatus.OK,
                "\n".join(
                    [
                        "# HELP shadow_mvs_up 1 when exporter is serving.",
                        "# TYPE shadow_mvs_up gauge",
                        'shadow_mvs_up{mode="shadow",exchange="sim"} 1',
                        "# HELP peak_trade_pipeline_events_total Shadow pipeline stage events (mock).",
                        "# TYPE peak_trade_pipeline_events_total counter",
                        'peak_trade_pipeline_events_total{mode="shadow",stage="intent",exchange="sim"} 1',
                        "# HELP peak_trade_pipeline_latency_seconds Pipeline latency histogram seconds (mock).",
                        "# TYPE peak_trade_pipeline_latency_seconds histogram",
                        'peak_trade_pipeline_latency_seconds_bucket{mode="shadow",edge="intent_to_ack",exchange="sim",le="0.1"} 1',
                        'peak_trade_pipeline_latency_seconds_bucket{mode="shadow",edge="intent_to_ack",exchange="sim",le="+Inf"} 1',
                        'peak_trade_pipeline_latency_seconds_sum{mode="shadow",edge="intent_to_ack",exchange="sim"} 0.1',
                        'peak_trade_pipeline_latency_seconds_count{mode="shadow",edge="intent_to_ack",exchange="sim"} 1',
                        "# HELP peak_trade_risk_blocks_total Risk blocks by reason (mock).",
                        "# TYPE peak_trade_risk_blocks_total counter",
                        'peak_trade_risk_blocks_total{mode="shadow",reason="other",exchange="sim"} 1',
                        "",
                    ]
                ),
            )
            return

        if self.kind == "grafana":
            if path == "/api/health":
                self.state.grafana_health_calls += 1
                # Fail first 2 calls, then succeed.
                if self.state.grafana_health_calls < 3:
                    self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"database": "starting"})
                else:
                    self._json(HTTPStatus.OK, {"database": "ok"})
                return

            if path == "/api/datasources":
                self._json(
                    HTTPStatus.OK,
                    [
                        {
                            "name": "prometheus-local",
                            "uid": "peaktrade-prometheus-local",
                            "type": "prometheus",
                            "isDefault": True,
                            "url": "http://host.docker.internal:9092",
                        }
                    ],
                )
                return

            if path == "/api/search":
                self._json(
                    HTTPStatus.OK,
                    [
                        {
                            "uid": os.environ.get("DASH_UID", "peaktrade-shadow-pipeline-mvs"),
                            "type": "dash-db",
                        }
                    ],
                )
                return

            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        if self.kind == "prometheus":
            if path == "/-/ready":
                self._text(HTTPStatus.OK, "ready\n")
                return

            if path == "/api/v1/targets":
                self.state.prom_targets_calls += 1
                if self.state.prom_targets_calls < 3:
                    active = []
                else:
                    active = [
                        {
                            "labels": {"job": "shadow_mvs"},
                            "health": "up",
                        }
                    ]
                self._json(
                    HTTPStatus.OK,
                    {"status": "success", "data": {"activeTargets": active}},
                )
                return

            if path == "/api/v1/query":
                q = (qs.get("query") or [""])[0]
                self.state.prom_query_calls[q] = self.state.prom_query_calls.get(q, 0) + 1
                n = self.state.prom_query_calls[q]

                # up is always available
                if q.startswith('up{job="shadow_mvs"}'):
                    result = [{"metric": {}, "value": [time.time(), "1"]}]
                    self._json(
                        HTTPStatus.OK,
                        {"status": "success", "data": {"resultType": "vector", "result": result}},
                    )
                    return

                # Warmup-sensitive queries: return NaN first 2 calls, then a value.
                if "rate(" in q or "histogram_quantile" in q:
                    if n < 3:
                        result = [{"metric": {}, "value": [time.time(), "NaN"]}]
                    else:
                        result = [{"metric": {}, "value": [time.time(), "0.1"]}]
                    self._json(
                        HTTPStatus.OK,
                        {"status": "success", "data": {"resultType": "vector", "result": result}},
                    )
                    return

                # Default: empty (should not be used by verify)
                self._json(
                    HTTPStatus.OK,
                    {"status": "success", "data": {"resultType": "vector", "result": []}},
                )
                return

            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        self._text(HTTPStatus.INTERNAL_SERVER_ERROR, "bad server kind\n")

    def log_message(self, fmt: str, *args: object) -> None:
        return


def _start_server(kind: str, state: _State) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.kind = kind  # type: ignore[attr-defined]
    srv.state = state  # type: ignore[attr-defined]
    host, port = srv.server_address
    t = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    t.start()
    return srv, t, f"http://{host}:{port}"


def test_shadow_mvs_verify_retries_and_warmup_passes(tmp_path):
    state = _State()
    prom_srv, _, prom_url = _start_server("prometheus", state)
    graf_srv, _, graf_url = _start_server("grafana", state)
    exp_srv, _, exp_url = _start_server("exporter", state)
    try:
        env = os.environ.copy()
        env.update(
            {
                "PROM_URL": prom_url,
                "GRAFANA_URL": graf_url,
                "EXPORTER_URL": f"{exp_url}/metrics",
                "GRAFANA_AUTH": "testuser:testpass",  # explicit test credentials (no repo default)
                "DASH_UID": "peaktrade-shadow-pipeline-mvs",
                # Fast retries for test runtime
                "TARGETS_MAX_ATTEMPTS": "5",
                "TARGETS_SLEEP_S": "0.01",
                "GRAFANA_HEALTH_MAX_ATTEMPTS": "5",
                "GRAFANA_HEALTH_SLEEP_S": "0.01",
                "WARMUP_MAX_ATTEMPTS": "5",
                "WARMUP_SLEEP_S": "0.01",
                "UP_QUERY_MAX_ATTEMPTS": "3",
                "UP_QUERY_SLEEP_S": "0.01",
            }
        )

        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / "obs" / "shadow_mvs_local_verify.sh"
        if not script.exists():
            pytest.skip("shadow_mvs_local_verify.sh removed (Grafana/Dashboard legacy cleanup)")
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=str(root),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        out = proc.stdout + "\n" + proc.stderr
        assert proc.returncode == 0, out

        # targets_retry contract lines must be present and attempts_used should be >= 2.
        assert "INFO|targets_retry=max_attempts=5|sleep_s=0.01" in out
        m = re.search(r"INFO\|targets_retry=attempts_used=(\d+)", out)
        assert m, out
        assert int(m.group(1)) >= 2

        # Warmup-sensitive queries must have been called multiple times due to NaN.
        warmup_queries = [
            q for q in state.prom_query_calls if "rate(" in q or "histogram_quantile" in q
        ]
        assert warmup_queries, state.prom_query_calls
        assert any(state.prom_query_calls[q] >= 2 for q in warmup_queries)
    finally:
        for s in (prom_srv, graf_srv, exp_srv):
            s.shutdown()
            s.server_close()
