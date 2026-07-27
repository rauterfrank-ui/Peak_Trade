"""
Tests for CI & Governance Health Router (ops_ci_health_router.py)

Covers:
- WEBUI_CI_HEALTH_READ_SURFACE_SIDE_EFFECT_ELIMINATION_V1 (GET read-only)
- POST /ops/ci-health/run auth-gated execution + snapshot write
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from src.webui.local_admin_write_auth_v1 import (
    AUTH_HEADER_NAME,
    AUTH_TOKEN_ENV_NAME,
)
from src.webui.ops_ci_health_router import (
    SNAPSHOT_STATE_ABSENT,
    SNAPSHOT_STATE_AVAILABLE,
    SNAPSHOT_STATE_INVALID,
    SNAPSHOT_STATE_STALE,
    router as ci_health_router,
    set_ci_health_config,
)

# Synthetic fixture token — deliberately not shaped like a production secret.
_FIXTURE_LOCAL_ADMIN_TOKEN = "fixture-token-not-a-secret"


def _admin_headers() -> dict[str, str]:
    return {AUTH_HEADER_NAME: _FIXTURE_LOCAL_ADMIN_TOKEN}


def _sample_snapshot(*, age: timedelta = timedelta(minutes=5), overall: str = "OK") -> dict:
    ts = datetime.now(timezone.utc) - age
    return {
        "overall_status": overall,
        "summary": {"total": 2, "ok": 2, "warn": 0, "fail": 0, "skip": 0},
        "checks": [
            {
                "check_id": "contract_guard",
                "title": "Contract Guard",
                "description": "desc",
                "status": "OK",
                "exit_code": 0,
                "output": "ok",
                "error_excerpt": "",
                "duration_ms": 12,
                "timestamp": ts.isoformat(),
                "script_path": "scripts/ops/check_required_ci_contexts_present.sh",
                "docs_refs": ["docs/ops/README.md"],
            },
            {
                "check_id": "docs_reference_validation",
                "title": "Docs Reference Validation",
                "description": "desc",
                "status": "OK",
                "exit_code": 0,
                "output": "ok",
                "error_excerpt": "",
                "duration_ms": 8,
                "timestamp": ts.isoformat(),
                "script_path": "scripts/ops/verify_docs_reference_targets.sh",
                "docs_refs": ["docs/ops/README.md"],
            },
        ],
        "generated_at": ts.isoformat(),
        "server_timestamp_utc": ts.isoformat(),
        "git_head_sha": "deadbeef",
        "app_version": "0.2.0",
    }


def _write_snapshot(repo_root: Path, payload: dict) -> Path:
    path = repo_root / "reports" / "ops" / "ci_health_latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture
def local_admin_token_env(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv(AUTH_TOKEN_ENV_NAME, _FIXTURE_LOCAL_ADMIN_TOKEN)
    return _FIXTURE_LOCAL_ADMIN_TOKEN


@pytest.fixture
def mock_repo_root(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)
    for name in (
        "check_required_ci_contexts_present.sh",
        "verify_docs_reference_targets.sh",
    ):
        script = scripts_dir / name
        script.write_text("#!/usr/bin/env bash\nset -euo pipefail\necho OK\nexit 0\n")
        script.chmod(0o755)
    return repo_root


@pytest.fixture
def mock_templates(tmp_path: Path) -> Jinja2Templates:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "ops_ci_health.html").write_text(
        """<!doctype html>
<html>
<head><title>CI Health</title></head>
<body>
<h1>CI & Governance Health</h1>
<p>Status: {{ overall_status }}</p>
<p>Snapshot: {{ snapshot_state }}</p>
<p>Total: {{ summary.total }}</p>
<button id="run-checks-btn" onclick="runChecks()">Run checks now</button>
<button id="refresh-btn" onclick="refreshStatus()">Refresh status</button>
<input type="checkbox" id="auto-refresh-toggle" onchange="toggleAutoRefresh(this.checked)">
<div id="error-banner" class="hidden"><div id="error-message"></div><button onclick="hideError()">Close</button></div>
<script>
  async function runChecks() {
    const headers = {'Accept': 'application/json', 'Content-Type': 'application/json'};
    headers['X-Peak-Trade-Local-Admin-Token'] = window.prompt('token');
    const response = await fetch('/ops/ci-health/run', { method: 'POST', headers: headers });
  }
  async function refreshStatus() {
    const response = await fetch('/ops/ci-health/status', { method: 'GET' });
  }
  function toggleAutoRefresh(enabled) {}
  function hideError() {}
</script>
</body>
</html>
"""
    )
    return Jinja2Templates(directory=str(templates_dir))


@pytest.fixture
def test_app(mock_repo_root: Path, mock_templates: Jinja2Templates) -> FastAPI:
    app = FastAPI()
    set_ci_health_config(mock_repo_root, mock_templates)
    app.include_router(ci_health_router)
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def client_real_ops_ci_health_template(mock_repo_root: Path) -> TestClient:
    repo_root = Path(__file__).resolve().parents[2]
    templates = Jinja2Templates(directory=str(repo_root / "templates" / "peak_trade_dashboard"))
    set_ci_health_config(mock_repo_root, templates)
    app = FastAPI()
    app.include_router(ci_health_router)
    return TestClient(app)


def _assert_get_no_side_effects(client: TestClient, mock_repo_root: Path, path: str) -> None:
    reports = mock_repo_root / "reports"
    before_exists = reports.exists()
    snapshot = mock_repo_root / "reports" / "ops" / "ci_health_latest.json"
    before_mtime = snapshot.stat().st_mtime_ns if snapshot.exists() else None
    before_content = snapshot.read_bytes() if snapshot.exists() else None

    with (
        patch("src.webui.ops_ci_health_router._run_all_checks") as run_all,
        patch("src.webui.ops_ci_health_router._run_check") as run_one,
        patch("src.webui.ops_ci_health_router._persist_snapshot") as persist,
        patch("src.webui.ops_ci_health_router._get_git_head_sha") as git_sha,
        patch("src.webui.ops_ci_health_router.subprocess.run") as sp_run,
    ):
        response = client.get(path)
        assert response.status_code == 200
        run_all.assert_not_called()
        run_one.assert_not_called()
        persist.assert_not_called()
        git_sha.assert_not_called()
        sp_run.assert_not_called()

    if before_exists:
        assert reports.exists()
    else:
        assert not reports.exists()

    if before_mtime is not None and before_content is not None:
        assert snapshot.exists()
        assert snapshot.stat().st_mtime_ns == before_mtime
        assert snapshot.read_bytes() == before_content


# =============================================================================
# GET root / status — no side effects
# =============================================================================


def test_ci_health_dashboard_renders(client: TestClient) -> None:
    response = client.get("/ops/ci-health")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "CI & Governance Health" in response.text
    assert SNAPSHOT_STATE_ABSENT in response.text


def test_ci_health_dashboard_standalone_hub_nav(
    client_real_ops_ci_health_template: TestClient,
) -> None:
    response = client_real_ops_ci_health_template.get("/ops/ci-health")
    assert response.status_code == 200
    html = response.text
    assert 'href="/ops"' in html
    assert "Ops Cockpit" in html
    assert 'href="/ops/stage1"' in html
    assert 'href="/ops/workflows"' in html
    assert 'href="/ops/ci-health"' in html
    assert "http://127.0.0.1:8010/" in html
    assert "Run UI (companion)" in html


def test_get_root_no_side_effects_absent(client: TestClient, mock_repo_root: Path) -> None:
    _assert_get_no_side_effects(client, mock_repo_root, "/ops/ci-health")
    assert not (mock_repo_root / "reports").exists()


def test_get_status_no_side_effects_absent(client: TestClient, mock_repo_root: Path) -> None:
    _assert_get_no_side_effects(client, mock_repo_root, "/ops/ci-health/status")
    data = client.get("/ops/ci-health/status").json()
    assert data["snapshot_state"] == SNAPSHOT_STATE_ABSENT
    assert data["read_only"] is True
    assert data["execution_triggered"] is False
    assert data["checks"] == []
    assert not (mock_repo_root / "reports").exists()


def test_get_root_and_status_preserve_existing_snapshot(
    client: TestClient, mock_repo_root: Path
) -> None:
    path = _write_snapshot(mock_repo_root, _sample_snapshot())
    # Stabilize mtime across rapid successive stats on some filesystems.
    os.utime(path, None)
    time.sleep(0.01)
    _assert_get_no_side_effects(client, mock_repo_root, "/ops/ci-health")
    _assert_get_no_side_effects(client, mock_repo_root, "/ops/ci-health/status")


def test_get_status_available_snapshot(client: TestClient, mock_repo_root: Path) -> None:
    _write_snapshot(mock_repo_root, _sample_snapshot(age=timedelta(minutes=1)))
    response = client.get("/ops/ci-health/status")
    assert response.status_code == 200
    data = response.json()
    assert data["snapshot_state"] == SNAPSHOT_STATE_AVAILABLE
    assert data["overall_status"] == "OK"
    assert data["summary"]["total"] == 2
    assert len(data["checks"]) == 2
    assert data["git_head_sha"] == "deadbeef"
    assert data["read_only"] is True


def test_get_status_stale_snapshot(client: TestClient, mock_repo_root: Path) -> None:
    _write_snapshot(mock_repo_root, _sample_snapshot(age=timedelta(hours=48)))
    data = client.get("/ops/ci-health/status").json()
    assert data["snapshot_state"] == SNAPSHOT_STATE_STALE
    assert data["overall_status"] == "OK"
    assert len(data["checks"]) == 2


def test_get_status_invalid_json(client: TestClient, mock_repo_root: Path) -> None:
    path = mock_repo_root / "reports" / "ops" / "ci_health_latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")
    data = client.get("/ops/ci-health/status").json()
    assert data["snapshot_state"] == SNAPSHOT_STATE_INVALID
    assert data["checks"] == []
    assert data["overall_status"] == "UNKNOWN"


def test_get_status_invalid_structure(client: TestClient, mock_repo_root: Path) -> None:
    _write_snapshot(mock_repo_root, {"overall_status": "OK", "checks": []})
    data = client.get("/ops/ci-health/status").json()
    assert data["snapshot_state"] == SNAPSHOT_STATE_INVALID
    assert data["checks"] == []


def test_get_status_does_not_depend_on_admin_token(
    client: TestClient, mock_repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(AUTH_TOKEN_ENV_NAME, raising=False)
    _write_snapshot(mock_repo_root, _sample_snapshot())
    response = client.get("/ops/ci-health/status")
    assert response.status_code == 200
    assert response.json()["snapshot_state"] == SNAPSHOT_STATE_AVAILABLE


def test_get_root_renders_available_snapshot(client: TestClient, mock_repo_root: Path) -> None:
    _write_snapshot(mock_repo_root, _sample_snapshot())
    response = client.get("/ops/ci-health")
    assert response.status_code == 200
    assert SNAPSHOT_STATE_AVAILABLE in response.text
    assert "OK" in response.text
    assert "Total: 2" in response.text


def test_ci_health_dashboard_contains_buttons(client: TestClient) -> None:
    response = client.get("/ops/ci-health")
    assert response.status_code == 200
    html = response.text
    assert "run-checks-btn" in html
    assert "refresh-btn" in html
    assert "auto-refresh-toggle" in html
    assert "runChecks()" in html
    assert "refreshStatus()" in html
    assert "/ops/ci-health/run" in html
    assert "/ops/ci-health/status" in html
    assert AUTH_HEADER_NAME in html
    assert AUTH_TOKEN_ENV_NAME not in html
    assert _FIXTURE_LOCAL_ADMIN_TOKEN not in html


def test_ci_health_dashboard_has_error_banner(client: TestClient) -> None:
    response = client.get("/ops/ci-health")
    assert response.status_code == 200
    assert "error-banner" in response.text
    assert "hideError()" in response.text


def test_ci_health_full_workflow_read_then_run(
    client: TestClient, mock_repo_root: Path, local_admin_token_env: str
) -> None:
    absent = client.get("/ops/ci-health/status").json()
    assert absent["snapshot_state"] == SNAPSHOT_STATE_ABSENT

    run = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert run.status_code == 200
    assert run.json()["run_triggered"] is True

    status = client.get("/ops/ci-health/status").json()
    assert status["snapshot_state"] in {SNAPSHOT_STATE_AVAILABLE, SNAPSHOT_STATE_STALE}
    assert status["summary"]["total"] == 2
    assert local_admin_token_env not in run.text


# =============================================================================
# POST /run — execution + auth (unchanged contract)
# =============================================================================


def test_ci_health_run_endpoint_returns_200(client: TestClient, local_admin_token_env: str) -> None:
    response = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert "overall_status" in data
    assert "summary" in data
    assert "checks" in data
    assert data["run_triggered"] is True
    assert data["app_version"] == "0.2.0"
    assert local_admin_token_env not in response.text


def test_ci_health_run_endpoint_executes_checks(
    client: TestClient, local_admin_token_env: str
) -> None:
    response = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert len(data["checks"]) == 2
    assert data["summary"]["total"] == 2
    statuses = [check["status"] for check in data["checks"]]
    assert "OK" in statuses or "SKIP" in statuses


def test_ci_health_run_creates_snapshot(
    mock_repo_root: Path, client: TestClient, local_admin_token_env: str
) -> None:
    response = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response.status_code == 200
    snapshot_dir = mock_repo_root / "reports" / "ops"
    assert (snapshot_dir / "ci_health_latest.json").exists()
    assert (snapshot_dir / "ci_health_latest.md").exists()


def test_ci_health_run_snapshot_json_content(
    mock_repo_root: Path, client: TestClient, local_admin_token_env: str
) -> None:
    response = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response.status_code == 200
    api_data = response.json()
    snapshot_file = mock_repo_root / "reports" / "ops" / "ci_health_latest.json"
    snapshot_data = json.loads(snapshot_file.read_text(encoding="utf-8"))
    assert snapshot_data["overall_status"] == api_data["overall_status"]
    assert snapshot_data["summary"] == api_data["summary"]
    assert len(snapshot_data["checks"]) == len(api_data["checks"])


def test_ci_health_run_snapshot_md_content(
    mock_repo_root: Path, client: TestClient, local_admin_token_env: str
) -> None:
    response = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response.status_code == 200
    content = (mock_repo_root / "reports" / "ops" / "ci_health_latest.md").read_text(
        encoding="utf-8"
    )
    assert "# CI & Governance Health Snapshot" in content
    assert "**Overall Status:**" in content


def test_ci_health_run_atomic_write(
    mock_repo_root: Path, client: TestClient, local_admin_token_env: str
) -> None:
    response = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response.status_code == 200
    tmp_files = list((mock_repo_root / "reports" / "ops").glob("*.tmp"))
    assert tmp_files == []


def test_ci_health_run_directory_creation(
    tmp_path: Path, mock_templates: Jinja2Templates, local_admin_token_env: str
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)
    for name in (
        "check_required_ci_contexts_present.sh",
        "verify_docs_reference_targets.sh",
    ):
        script = scripts_dir / name
        script.write_text("#!/usr/bin/env bash\necho OK\nexit 0\n")
        script.chmod(0o755)

    reports_dir = repo_root / "reports" / "ops"
    assert not reports_dir.exists()

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)
    client = TestClient(app)

    response = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response.status_code == 200
    assert reports_dir.exists()
    assert (reports_dir / "ci_health_latest.json").exists()


def test_ci_health_run_handles_failing_check(
    tmp_path: Path, mock_templates: Jinja2Templates, local_admin_token_env: str
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)
    failing = scripts_dir / "check_required_ci_contexts_present.sh"
    failing.write_text("#!/usr/bin/env bash\necho FAIL\nexit 1\n")
    failing.chmod(0o755)
    passing = scripts_dir / "verify_docs_reference_targets.sh"
    passing.write_text("#!/usr/bin/env bash\necho OK\nexit 0\n")
    passing.chmod(0o755)

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)
    client = TestClient(app)

    data = client.post("/ops/ci-health/run", headers=_admin_headers()).json()
    assert data["overall_status"] == "FAIL"
    assert data["summary"]["fail"] >= 1


def test_ci_health_run_handles_warning_check(
    tmp_path: Path, mock_templates: Jinja2Templates, local_admin_token_env: str
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)
    warning = scripts_dir / "check_required_ci_contexts_present.sh"
    warning.write_text("#!/usr/bin/env bash\necho WARN\nexit 2\n")
    warning.chmod(0o755)
    passing = scripts_dir / "verify_docs_reference_targets.sh"
    passing.write_text("#!/usr/bin/env bash\necho OK\nexit 0\n")
    passing.chmod(0o755)

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)
    client = TestClient(app)

    data = client.post("/ops/ci-health/run", headers=_admin_headers()).json()
    assert data["overall_status"] == "WARN"
    assert data["summary"]["warn"] >= 1


def test_ci_health_run_handles_missing_script(
    tmp_path: Path, mock_templates: Jinja2Templates, local_admin_token_env: str
) -> None:
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()
    app = FastAPI()
    set_ci_health_config(empty_repo, mock_templates)
    app.include_router(ci_health_router)
    client = TestClient(app)
    data = client.post("/ops/ci-health/run", headers=_admin_headers()).json()
    assert all(status == "SKIP" for status in [c["status"] for c in data["checks"]])


def test_ci_health_run_snapshot_error_handling(
    tmp_path: Path, mock_templates: Jinja2Templates, local_admin_token_env: str
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)
    for name in (
        "check_required_ci_contexts_present.sh",
        "verify_docs_reference_targets.sh",
    ):
        script = scripts_dir / name
        script.write_text("#!/usr/bin/env bash\necho OK\nexit 0\n")
        script.chmod(0o755)

    reports_dir = repo_root / "reports" / "ops"
    reports_dir.mkdir(parents=True)
    reports_dir.chmod(0o444)

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)
    client = TestClient(app)
    try:
        response = client.post("/ops/ci-health/run", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert "snapshot_write_error" in data
        assert "Failed to persist snapshot" in data["snapshot_write_error"]
        assert "overall_status" in data
    finally:
        reports_dir.chmod(0o755)


def test_ci_health_run_sequential_calls_work(
    client: TestClient, local_admin_token_env: str
) -> None:
    response1 = client.post("/ops/ci-health/run", headers=_admin_headers())
    response2 = client.post("/ops/ci-health/run", headers=_admin_headers())
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["run_triggered"] is True
    assert response2.json()["run_triggered"] is True


def test_ci_health_run_rejects_missing_auth_without_side_effects(
    mock_repo_root: Path, client: TestClient, local_admin_token_env: str
) -> None:
    snapshot_dir = mock_repo_root / "reports" / "ops"
    assert not snapshot_dir.exists()
    with patch(
        "src.webui.ops_ci_health_router._run_all_checks",
        side_effect=AssertionError("subprocess path must not run"),
    ) as mocked:
        response = client.post("/ops/ci-health/run")
        assert response.status_code == 401
        assert response.json()["detail"]["error"] == "LOCAL_ADMIN_AUTH_MISSING"
        mocked.assert_not_called()
    assert not snapshot_dir.exists()


def test_ci_health_run_rejects_invalid_auth_without_side_effects(
    mock_repo_root: Path, client: TestClient, local_admin_token_env: str
) -> None:
    snapshot_dir = mock_repo_root / "reports" / "ops"
    assert not snapshot_dir.exists()
    with patch(
        "src.webui.ops_ci_health_router._run_all_checks",
        side_effect=AssertionError("subprocess path must not run"),
    ) as mocked:
        response = client.post(
            "/ops/ci-health/run",
            headers={AUTH_HEADER_NAME: "wrong-fixture-token"},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "LOCAL_ADMIN_AUTH_INVALID"
        mocked.assert_not_called()
    assert not snapshot_dir.exists()
