import pytest

# Patched: skip cleanly if optional dependency is not installed
pytest.importorskip("yaml")
import json
import os
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_prometheus_local_compose_mounts_rules_dir_deterministically() -> None:
    p = PROJECT_ROOT / "docs" / "webui" / "observability" / "DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml"
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    svc = (doc.get("services") or {}).get("prometheus-local") or {}
    vols = svc.get("volumes") or []
    assert any(
        isinstance(v, str) and v.strip().startswith("./prometheus/rules:/etc/prometheus/rules")
        for v in vols
    ), "expected bind mount for ./prometheus/rules -> /etc/prometheus/rules"


def test_prometheus_local_scrape_config_has_rule_files_path() -> None:
    p = PROJECT_ROOT / "docs" / "webui" / "observability" / "PROMETHEUS_LOCAL_SCRAPE.yml"
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    rf = doc.get("rule_files") or []
    assert "/etc/prometheus/rules/*.yml" in rf
    assert "/etc/prometheus/rules/*.yaml" in rf


def test_ai_live_ops_verify_script_exists_and_is_strict_shell() -> None:
    p = PROJECT_ROOT / "scripts" / "obs" / "ai_live_ops_verify.sh"
    txt = p.read_text(encoding="utf-8")
    assert txt.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in txt
    assert (p.stat().st_mode & 0o111) != 0, "script must be executable"
    assert "git status -sb" in txt
    assert "port_check 9092" in txt
    assert "port_check 3000" in txt
    assert 'port_check "$AI_LIVE_PORT"' in txt or "port_check 9110" in txt
    assert "AI_LIVE_LatencyP99High" in txt


class _Handler(BaseHTTPRequestHandler):
    # Minimal fake Prometheus + Grafana + exporter endpoints for script test.
    def _send(self, code: int, body: str, *, content_type: str = "application/json") -> None:
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, fmt: str, *args: Any) -> None:  # silence test output
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/-/ready":
            self._send(
                200, "Prometheus Server is Ready.\n", content_type="text/plain; charset=utf-8"
            )
            return

        if self.path.startswith("/api/v1/targets"):
            self._send(
                200,
                json.dumps(
                    {
                        "status": "success",
                        "data": {
                            "activeTargets": [
                                {
                                    "labels": {
                                        "job": "ai_live",
                                        "instance": "host.docker.internal:9110",
                                    },
                                    "scrapeUrl": "http://host.docker.internal:9110/metrics",
                                    "health": "up",
                                    "lastError": "",
                                }
                            ]
                        },
                    }
                ),
            )
            return

        if self.path.startswith("/api/v1/query"):
            # _prom_query_json.sh uses /api/v1/query?query=... (GET).
            self._send(
                200,
                json.dumps(
                    {
                        "status": "success",
                        "data": {
                            "resultType": "vector",
                            "result": [{"metric": {}, "value": [0, "1"]}],
                        },
                    }
                ),
            )
            return

        if self.path.startswith("/api/v1/rules"):
            self._send(
                200,
                json.dumps(
                    {
                        "status": "success",
                        "data": {
                            "groups": [
                                {
                                    "name": "ai_live_ops_pack_v1",
                                    "rules": [
                                        {"type": "alerting", "name": "AI_LIVE_ExporterDown"},
                                        {"type": "alerting", "name": "AI_LIVE_StaleEvents"},
                                        {"type": "alerting", "name": "AI_LIVE_ParseErrorsSpike"},
                                        {"type": "alerting", "name": "AI_LIVE_DroppedEventsSpike"},
                                        {"type": "alerting", "name": "AI_LIVE_LatencyP95High"},
                                        {"type": "alerting", "name": "AI_LIVE_LatencyP99High"},
                                    ],
                                }
                            ]
                        },
                    }
                ),
            )
            return

        if self.path.startswith("/api/v1/alerts"):
            self._send(200, json.dumps({"status": "success", "data": {"alerts": []}}))
            return

        # Grafana endpoints (same base in this test)
        if self.path.startswith("/api/health"):
            self._send(200, json.dumps({"database": "ok"}))
            return

        if self.path.startswith("/api/user"):
            self._send(200, json.dumps({"login": "admin"}))
            return

        if self.path.startswith("/api/dashboards/uid/peaktrade-execution-watch-overview"):
            dash = {
                "dashboard": {
                    "uid": "peaktrade-execution-watch-overview",
                    "title": "Peak_Trade — Execution Watch Overview",
                    "panels": [
                        {
                            "type": "row",
                            "title": "AI Live — Ops Summary",
                            "gridPos": {"x": 0, "y": 0, "w": 24, "h": 1},
                        },
                        {
                            "type": "stat",
                            "title": "Active alerts (firing)",
                            "gridPos": {"x": 20, "y": 1, "w": 4, "h": 4},
                            "targets": [
                                {"expr": '(count(ALERTS{alertstate="firing"}) or on() vector(0))'}
                            ],
                        },
                    ],
                }
            }
            self._send(200, json.dumps(dash))
            return

        if self.path == "/metrics":
            self._send(
                200,
                "# HELP peaktrade_ai_live_heartbeat Heartbeat\npeaktrade_ai_live_heartbeat 1\n",
                content_type="text/plain; charset=utf-8",
            )
            return

        self._send(404, json.dumps({"error": "not found"}))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_ai_live_ops_verify_script_can_run_against_mock_endpoints(tmp_path: Path) -> None:
    port = _free_port()
    httpd = HTTPServer(("127.0.0.1", port), _Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    try:
        env = os.environ.copy()
        base = f"http://127.0.0.1:{port}"
        env["PROM_URL"] = base
        env["GRAFANA_URL"] = base
        env["GRAFANA_AUTH"] = ""  # avoid auth in test
        env["EXPORTER_URL"] = f"{base}/metrics"
        env["SKIP_PORT_CHECK"] = "1"

        p = PROJECT_ROOT / "scripts" / "obs" / "ai_live_ops_verify.sh"
        res = subprocess.run(["bash", str(p)], env=env, capture_output=True, text=True, timeout=30)
        assert res.returncode == 0, f"stdout:\n{res.stdout}\n\nstderr:\n{res.stderr}"
    finally:
        httpd.shutdown()
        httpd.server_close()
