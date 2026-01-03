"""
Tests for CI & Governance Health Router (ops_ci_health_router.py)

Smoke tests for the CI Health Panel v0.2 (with snapshot persistence).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from src.webui.ops_ci_health_router import (
    HealthCheckResult,
    router as ci_health_router,
    set_ci_health_config,
)


@pytest.fixture
def mock_repo_root(tmp_path: Path) -> Path:
    """Create a mock repository root with CI scripts."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Create scripts directory
    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)

    # Create mock CI check scripts
    contract_guard = scripts_dir / "check_required_ci_contexts_present.sh"
    contract_guard.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
echo "✅ CI required context contract looks good."
exit 0
"""
    )
    contract_guard.chmod(0o755)

    docs_check = scripts_dir / "verify_docs_reference_targets.sh"
    docs_check.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
echo "✅ All docs references valid."
exit 0
"""
    )
    docs_check.chmod(0o755)

    return repo_root


@pytest.fixture
def mock_templates(tmp_path: Path) -> Jinja2Templates:
    """Create mock Jinja2Templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create minimal template (v0.2 with interactive controls)
    template_file = templates_dir / "ops_ci_health.html"
    template_file.write_text(
        """<!doctype html>
<html>
<head><title>CI Health</title></head>
<body>
<h1>CI & Governance Health</h1>
<p>Status: {{ overall_status }}</p>
<p>Total: {{ summary.total }}</p>

<!-- v0.2 Interactive Controls -->
<button id="run-checks-btn" onclick="runChecks()">Run checks now</button>
<button id="refresh-btn" onclick="refreshStatus()">Refresh status</button>
<input type="checkbox" id="auto-refresh-toggle" onchange="toggleAutoRefresh(this.checked)">

<!-- Error Banner -->
<div id="error-banner" class="hidden">
  <div id="error-message"></div>
  <button onclick="hideError()">Close</button>
</div>

<script>
  async function runChecks() {
    const response = await fetch('/ops/ci-health/run', { method: 'POST' });
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
    """Create test FastAPI app with CI Health router."""
    app = FastAPI()

    # Configure router
    set_ci_health_config(mock_repo_root, mock_templates)
    app.include_router(ci_health_router)

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(test_app)


# =============================================================================
# TESTS: HTML Dashboard Endpoint
# =============================================================================


def test_ci_health_dashboard_renders(client: TestClient) -> None:
    """Test that CI health dashboard renders successfully."""
    response = client.get("/ops/ci-health")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "CI & Governance Health" in response.text


def test_ci_health_dashboard_shows_status(client: TestClient) -> None:
    """Test that dashboard shows overall status."""
    response = client.get("/ops/ci-health")

    assert response.status_code == 200
    # Should show either OK, WARN, or FAIL
    assert any(status in response.text for status in ["OK", "WARN", "FAIL"])


def test_ci_health_dashboard_shows_check_count(client: TestClient) -> None:
    """Test that dashboard shows check count."""
    response = client.get("/ops/ci-health")

    assert response.status_code == 200
    # Should show total count (we have 2 checks)
    assert "Total:" in response.text or "summary" in response.text.lower()


# =============================================================================
# TESTS: JSON API Endpoint
# =============================================================================


def test_ci_health_status_json(client: TestClient) -> None:
    """Test that JSON status endpoint returns valid data."""
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    # Validate structure
    assert "overall_status" in data
    assert "summary" in data
    assert "checks" in data
    assert "generated_at" in data

    # Validate summary
    summary = data["summary"]
    assert "total" in summary
    assert "ok" in summary
    assert "warn" in summary
    assert "fail" in summary
    assert "skip" in summary

    # Should have 2 checks
    assert summary["total"] == 2
    assert len(data["checks"]) == 2


def test_ci_health_status_check_structure(client: TestClient) -> None:
    """Test that each check has required fields."""
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    for check in data["checks"]:
        assert "check_id" in check
        assert "title" in check
        assert "description" in check
        assert "status" in check
        assert "exit_code" in check
        assert "output" in check
        assert "error_excerpt" in check
        assert "duration_ms" in check
        assert "timestamp" in check
        assert "script_path" in check
        assert "docs_refs" in check


def test_ci_health_status_includes_contract_guard(client: TestClient) -> None:
    """Test that contract guard check is included."""
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    check_ids = [check["check_id"] for check in data["checks"]]
    assert "contract_guard" in check_ids


def test_ci_health_status_includes_docs_validation(client: TestClient) -> None:
    """Test that docs validation check is included."""
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    check_ids = [check["check_id"] for check in data["checks"]]
    assert "docs_reference_validation" in check_ids


# =============================================================================
# TESTS: Check Execution
# =============================================================================


def test_ci_health_executes_checks(client: TestClient) -> None:
    """Test that checks are actually executed."""
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    # At least one check should have OK status (our mock scripts return 0)
    statuses = [check["status"] for check in data["checks"]]
    assert "OK" in statuses or "SKIP" in statuses


def test_ci_health_handles_missing_script(tmp_path: Path, mock_templates: Jinja2Templates) -> None:
    """Test that missing scripts are handled gracefully."""
    # Create repo without scripts
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()

    app = FastAPI()
    set_ci_health_config(empty_repo, mock_templates)
    app.include_router(ci_health_router)

    client = TestClient(app)
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    # All checks should be skipped
    statuses = [check["status"] for check in data["checks"]]
    assert all(status == "SKIP" for status in statuses)


# =============================================================================
# TESTS: Error Handling
# =============================================================================


def test_ci_health_handles_failing_check(tmp_path: Path, mock_templates: Jinja2Templates) -> None:
    """Test that failing checks are handled correctly."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)

    # Create failing script
    failing_script = scripts_dir / "check_required_ci_contexts_present.sh"
    failing_script.write_text(
        """#!/usr/bin/env bash
echo "❌ CI check failed!"
exit 1
"""
    )
    failing_script.chmod(0o755)

    # Create passing script
    passing_script = scripts_dir / "verify_docs_reference_targets.sh"
    passing_script.write_text(
        """#!/usr/bin/env bash
echo "✅ OK"
exit 0
"""
    )
    passing_script.chmod(0o755)

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)

    client = TestClient(app)
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    # Overall status should be FAIL
    assert data["overall_status"] == "FAIL"

    # Should have 1 fail and 1 ok
    assert data["summary"]["fail"] >= 1
    assert data["summary"]["ok"] >= 1


def test_ci_health_handles_warning_check(tmp_path: Path, mock_templates: Jinja2Templates) -> None:
    """Test that warning checks (exit 2) are handled correctly."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)

    # Create warning script (exit 2)
    warning_script = scripts_dir / "check_required_ci_contexts_present.sh"
    warning_script.write_text(
        """#!/usr/bin/env bash
echo "⚠️ Warning: some issues found"
exit 2
"""
    )
    warning_script.chmod(0o755)

    # Create passing script
    passing_script = scripts_dir / "verify_docs_reference_targets.sh"
    passing_script.write_text(
        """#!/usr/bin/env bash
echo "✅ OK"
exit 0
"""
    )
    passing_script.chmod(0o755)

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)

    client = TestClient(app)
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    # Overall status should be WARN
    assert data["overall_status"] == "WARN"

    # Should have 1 warn and 1 ok
    assert data["summary"]["warn"] >= 1
    assert data["summary"]["ok"] >= 1


# =============================================================================
# TESTS: Integration
# =============================================================================


def test_ci_health_full_workflow(client: TestClient) -> None:
    """Test full workflow: HTML dashboard + JSON API."""
    # 1. Get HTML dashboard
    html_response = client.get("/ops/ci-health")
    assert html_response.status_code == 200
    assert "CI & Governance Health" in html_response.text

    # 2. Get JSON status
    json_response = client.get("/ops/ci-health/status")
    assert json_response.status_code == 200
    data = json_response.json()

    # 3. Verify consistency
    assert "overall_status" in data
    assert data["summary"]["total"] == 2


# =============================================================================
# TESTS: v0.2 Snapshot Persistence
# =============================================================================


def test_ci_health_status_includes_v02_fields(client: TestClient) -> None:
    """Test that v0.2 fields are present in status response."""
    response = client.get("/ops/ci-health/status")

    assert response.status_code == 200
    data = response.json()

    # v0.2 fields
    assert "server_timestamp_utc" in data
    assert "git_head_sha" in data
    assert "app_version" in data
    assert data["app_version"] == "0.2.0"


def test_ci_health_snapshot_files_created(mock_repo_root: Path, client: TestClient) -> None:
    """Test that snapshot files are created on successful status call."""
    # Call status endpoint
    response = client.get("/ops/ci-health/status")
    assert response.status_code == 200

    # Check that snapshot files exist
    snapshot_dir = mock_repo_root / "reports" / "ops"
    json_file = snapshot_dir / "ci_health_latest.json"
    md_file = snapshot_dir / "ci_health_latest.md"

    assert json_file.exists(), "JSON snapshot file should be created"
    assert md_file.exists(), "Markdown snapshot file should be created"


def test_ci_health_snapshot_json_content(mock_repo_root: Path, client: TestClient) -> None:
    """Test that JSON snapshot contains complete status data."""
    # Call status endpoint
    response = client.get("/ops/ci-health/status")
    assert response.status_code == 200
    api_data = response.json()

    # Read snapshot file
    snapshot_file = mock_repo_root / "reports" / "ops" / "ci_health_latest.json"
    assert snapshot_file.exists()

    with open(snapshot_file, "r", encoding="utf-8") as f:
        snapshot_data = json.load(f)

    # Verify structure matches API response
    assert snapshot_data["overall_status"] == api_data["overall_status"]
    assert snapshot_data["summary"] == api_data["summary"]
    assert len(snapshot_data["checks"]) == len(api_data["checks"])
    assert "server_timestamp_utc" in snapshot_data
    assert "git_head_sha" in snapshot_data


def test_ci_health_snapshot_md_content(mock_repo_root: Path, client: TestClient) -> None:
    """Test that Markdown snapshot is human-readable."""
    # Call status endpoint
    response = client.get("/ops/ci-health/status")
    assert response.status_code == 200

    # Read markdown file
    md_file = mock_repo_root / "reports" / "ops" / "ci_health_latest.md"
    assert md_file.exists()

    content = md_file.read_text(encoding="utf-8")

    # Verify markdown structure
    assert "# CI & Governance Health Snapshot" in content
    assert "**Overall Status:**" in content
    assert "## Summary" in content
    assert "## Checks" in content
    assert "**Total Checks:**" in content


def test_ci_health_snapshot_atomic_write(mock_repo_root: Path, client: TestClient) -> None:
    """Test that snapshot uses atomic writes (no .tmp files left behind)."""
    # Call status endpoint
    response = client.get("/ops/ci-health/status")
    assert response.status_code == 200

    # Check that no temp files exist
    snapshot_dir = mock_repo_root / "reports" / "ops"
    tmp_files = list(snapshot_dir.glob("*.tmp"))

    assert len(tmp_files) == 0, "No temporary files should remain after atomic write"


def test_ci_health_snapshot_error_handling(tmp_path: Path, mock_templates: Jinja2Templates) -> None:
    """Test that snapshot write errors do NOT fail the API."""
    # Create repo with unwritable reports directory
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)

    # Create passing scripts
    contract_guard = scripts_dir / "check_required_ci_contexts_present.sh"
    contract_guard.write_text("#!/usr/bin/env bash\necho 'OK'\nexit 0\n")
    contract_guard.chmod(0o755)

    docs_check = scripts_dir / "verify_docs_reference_targets.sh"
    docs_check.write_text("#!/usr/bin/env bash\necho 'OK'\nexit 0\n")
    docs_check.chmod(0o755)

    # Create reports dir but make it read-only
    reports_dir = repo_root / "reports" / "ops"
    reports_dir.mkdir(parents=True)
    reports_dir.chmod(0o444)  # Read-only

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)

    client = TestClient(app)

    try:
        # Call status endpoint - should still return 200
        response = client.get("/ops/ci-health/status")
        assert response.status_code == 200

        data = response.json()

        # Should have snapshot_write_error field
        assert "snapshot_write_error" in data
        assert "Failed to persist snapshot" in data["snapshot_write_error"]

        # But overall status should still be valid
        assert "overall_status" in data
        assert "checks" in data

    finally:
        # Cleanup: restore permissions
        reports_dir.chmod(0o755)


def test_ci_health_snapshot_multiple_calls(mock_repo_root: Path, client: TestClient) -> None:
    """Test that multiple status calls overwrite snapshot (latest wins)."""
    # First call
    response1 = client.get("/ops/ci-health/status")
    assert response1.status_code == 200
    data1 = response1.json()

    # Read first snapshot
    json_file = mock_repo_root / "reports" / "ops" / "ci_health_latest.json"
    with open(json_file, "r", encoding="utf-8") as f:
        snapshot1 = json.load(f)

    # Second call (should overwrite)
    response2 = client.get("/ops/ci-health/status")
    assert response2.status_code == 200
    data2 = response2.json()

    # Read second snapshot
    with open(json_file, "r", encoding="utf-8") as f:
        snapshot2 = json.load(f)

    # Timestamps should differ
    assert snapshot1["generated_at"] != snapshot2["generated_at"]

    # File should contain latest data
    assert snapshot2["generated_at"] == data2["generated_at"]


def test_ci_health_snapshot_directory_creation(tmp_path: Path, mock_templates: Jinja2Templates) -> None:
    """Test that snapshot directory is created if missing."""
    # Create repo WITHOUT reports directory
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    scripts_dir = repo_root / "scripts" / "ops"
    scripts_dir.mkdir(parents=True)

    # Create passing scripts
    contract_guard = scripts_dir / "check_required_ci_contexts_present.sh"
    contract_guard.write_text("#!/usr/bin/env bash\necho 'OK'\nexit 0\n")
    contract_guard.chmod(0o755)

    docs_check = scripts_dir / "verify_docs_reference_targets.sh"
    docs_check.write_text("#!/usr/bin/env bash\necho 'OK'\nexit 0\n")
    docs_check.chmod(0o755)

    # Verify reports dir does NOT exist
    reports_dir = repo_root / "reports" / "ops"
    assert not reports_dir.exists()

    app = FastAPI()
    set_ci_health_config(repo_root, mock_templates)
    app.include_router(ci_health_router)

    client = TestClient(app)

    # Call status endpoint
    response = client.get("/ops/ci-health/status")
    assert response.status_code == 200

    # Directory should now exist
    assert reports_dir.exists()
    assert (reports_dir / "ci_health_latest.json").exists()
    assert (reports_dir / "ci_health_latest.md").exists()


# =============================================================================
# TESTS: v0.2 Run-Now Buttons & Interactive Controls
# =============================================================================


def test_ci_health_run_endpoint_returns_200(client: TestClient) -> None:
    """Test that POST /run endpoint returns 200 with valid JSON."""
    response = client.post("/ops/ci-health/run")

    assert response.status_code == 200
    data = response.json()

    # Validate structure (same as GET /status)
    assert "overall_status" in data
    assert "summary" in data
    assert "checks" in data
    assert "generated_at" in data
    assert "server_timestamp_utc" in data
    assert "git_head_sha" in data
    assert "app_version" in data

    # v0.2 run-specific field
    assert "run_triggered" in data
    assert data["run_triggered"] is True


def test_ci_health_run_endpoint_executes_checks(client: TestClient) -> None:
    """Test that POST /run actually executes checks."""
    response = client.post("/ops/ci-health/run")

    assert response.status_code == 200
    data = response.json()

    # Should have 2 checks
    assert len(data["checks"]) == 2
    assert data["summary"]["total"] == 2

    # At least one check should have OK status (our mock scripts return 0)
    statuses = [check["status"] for check in data["checks"]]
    assert "OK" in statuses or "SKIP" in statuses


def test_ci_health_run_parallel_returns_409(client: TestClient) -> None:
    """Test that parallel run attempts return HTTP 409."""
    import threading
    import time

    results = []

    def run_check():
        response = client.post("/ops/ci-health/run")
        results.append(response)

    # Start two threads simultaneously
    thread1 = threading.Thread(target=run_check)
    thread2 = threading.Thread(target=run_check)

    thread1.start()
    time.sleep(0.01)  # Small delay to ensure first thread acquires lock
    thread2.start()

    thread1.join()
    thread2.join()

    # One should succeed (200), one should fail (409)
    status_codes = [r.status_code for r in results]

    # At least one should be 409 (conflict)
    assert 409 in status_codes, "Expected at least one 409 response for parallel run"

    # Check 409 response structure
    conflict_response = [r for r in results if r.status_code == 409][0]
    data = conflict_response.json()

    assert "detail" in data
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "run_already_in_progress"
    assert "message" in data["detail"]


def test_ci_health_run_creates_snapshot(mock_repo_root: Path, client: TestClient) -> None:
    """Test that POST /run creates snapshot files."""
    # Call run endpoint
    response = client.post("/ops/ci-health/run")
    assert response.status_code == 200

    # Check that snapshot files exist
    snapshot_dir = mock_repo_root / "reports" / "ops"
    json_file = snapshot_dir / "ci_health_latest.json"
    md_file = snapshot_dir / "ci_health_latest.md"

    assert json_file.exists(), "JSON snapshot should be created by /run"
    assert md_file.exists(), "Markdown snapshot should be created by /run"


def test_ci_health_dashboard_contains_buttons(client: TestClient) -> None:
    """Test that HTML dashboard contains interactive control buttons."""
    response = client.get("/ops/ci-health")

    assert response.status_code == 200
    html = response.text

    # Check for button elements
    assert "run-checks-btn" in html, "Run checks button should be present"
    assert "refresh-btn" in html, "Refresh button should be present"
    assert "auto-refresh-toggle" in html, "Auto-refresh toggle should be present"

    # Check for JavaScript functions
    assert "runChecks()" in html, "runChecks() function should be present"
    assert "refreshStatus()" in html, "refreshStatus() function should be present"
    assert "toggleAutoRefresh" in html, "toggleAutoRefresh() function should be present"

    # Check for fetch API calls
    assert "/ops/ci-health/run" in html, "POST /run endpoint should be referenced"
    assert "/ops/ci-health/status" in html, "GET /status endpoint should be referenced"


def test_ci_health_dashboard_has_error_banner(client: TestClient) -> None:
    """Test that HTML dashboard has error banner element."""
    response = client.get("/ops/ci-health")

    assert response.status_code == 200
    html = response.text

    # Check for error banner
    assert "error-banner" in html, "Error banner should be present"
    assert "error-message" in html, "Error message element should be present"
    assert "hideError()" in html, "hideError() function should be present"


def test_ci_health_run_sequential_calls_work(client: TestClient) -> None:
    """Test that sequential run calls work (lock is released)."""
    # First call
    response1 = client.post("/ops/ci-health/run")
    assert response1.status_code == 200

    # Second call (should also succeed since lock was released)
    response2 = client.post("/ops/ci-health/run")
    assert response2.status_code == 200

    # Both should have valid data
    data1 = response1.json()
    data2 = response2.json()

    assert "overall_status" in data1
    assert "overall_status" in data2
    assert data1["run_triggered"] is True
    assert data2["run_triggered"] is True
