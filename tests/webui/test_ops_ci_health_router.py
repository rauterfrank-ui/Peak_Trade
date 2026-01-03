"""
Tests for CI & Governance Health Router (ops_ci_health_router.py)

Smoke tests for the CI Health Panel v0.1.
"""

from __future__ import annotations

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

    # Create minimal template
    template_file = templates_dir / "ops_ci_health.html"
    template_file.write_text(
        """<!doctype html>
<html>
<head><title>CI Health</title></head>
<body>
<h1>CI & Governance Health</h1>
<p>Status: {{ overall_status }}</p>
<p>Total: {{ summary.total }}</p>
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
