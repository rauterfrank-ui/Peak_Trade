"""
Tests for Ops Workflows Router
"""

from pathlib import Path

import pytest

# Skip if FastAPI not installed
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from src.webui.app import create_app

# Mark all tests in this module as web tests
pytestmark = pytest.mark.web


def test_workflows_router_imports():
    """Smoke test: Ensure router can be imported and app includes it."""
    from src.webui.ops_workflows_router import router
    
    assert router is not None
    assert router.prefix == "/ops/workflows"


def test_workflows_html_endpoint():
    """Test that HTML endpoint returns 200 and contains expected content."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/ops/workflows")
    assert response.status_code == 200
    
    # Check content
    content = response.text
    assert "Ops Workflow Hub" in content
    assert "scripts/quick_pr_merge.sh" in content
    assert "scripts/post_merge_workflow.sh" in content


def test_workflows_json_endpoint():
    """Test that JSON endpoint returns valid workflow list."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/ops/workflows/list")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    
    # Check structure of first workflow
    wf = data[0]
    assert "id" in wf
    assert "title" in wf
    assert "description" in wf
    assert "script_path" in wf
    assert "commands" in wf
    assert "exists" in wf
    assert isinstance(wf["commands"], list)


def test_api_workflows_alias():
    """Test that /api/ops/workflows alias works."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/api/ops/workflows")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4


def test_workflow_filesystem_metadata():
    """Test that filesystem metadata is computed correctly."""
    from src.webui.ops_workflows_router import (
        _get_workflow_definitions,
        _enrich_with_filesystem_metadata,
        set_workflows_config,
    )
    from fastapi.templating import Jinja2Templates
    
    # Use real repo root
    repo_root = Path(__file__).resolve().parents[1]
    templates_dir = repo_root / "templates" / "peak_trade_dashboard"
    templates = Jinja2Templates(directory=str(templates_dir))
    
    # Configure router
    set_workflows_config(repo_root, templates)
    
    # Get workflows
    workflow_defs = _get_workflow_definitions()
    workflows = _enrich_with_filesystem_metadata(workflow_defs)
    
    # All 4 workflows should exist
    assert len(workflows) == 4
    
    # Check that at least one workflow exists on filesystem
    exists_count = sum(1 for wf in workflows if wf.exists)
    assert exists_count > 0, "At least one workflow script should exist"
    
    # Check metadata for existing scripts
    for wf in workflows:
        if wf.exists:
            assert wf.size_bytes is not None
            assert wf.size_bytes > 0
            assert wf.last_modified is not None

