"""
Tests for Stage1 Router (Phase 16K)
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app


def test_stage1_router_imports():
    """Smoke test: Ensure router can be imported and app includes it."""
    from src.webui.ops_stage1_router import router
    
    assert router is not None
    assert router.prefix == "/ops/stage1"


def test_stage1_endpoints_in_app():
    """Test that Stage1 endpoints are registered in the app."""
    app = create_app()
    client = TestClient(app)
    
    # Test that routes exist (may return 404 for data, but should not 404 for route)
    response = client.get("/ops/stage1/latest")
    # Should return 404 (no data) or 200 (if test data exists), not 405/422
    assert response.status_code in [200, 404]
    
    response = client.get("/ops/stage1/trend")
    assert response.status_code in [200, 404]
    
    response = client.get("/ops/stage1")
    # HTML endpoint should always return 200 (may show empty state)
    assert response.status_code == 200


def test_stage1_latest_endpoint_with_data(tmp_path):
    """Test /latest endpoint returns data when available."""
    # Create test app with custom report root
    from src.webui.ops_stage1_router import set_stage1_config
    from fastapi.templating import Jinja2Templates
    
    # Create test summary
    summary_data = {
        "schema_version": 1,
        "date": "2025-12-20",
        "created_at_utc": "2025-12-20T10:00:00+00:00",
        "report_dir": str(tmp_path),
        "metrics": {
            "new_alerts": 5,
            "critical_alerts": 1,
            "parse_errors": 0,
            "operator_actions": 2,
            "legacy_alerts": 10,
        },
        "notes": ["test"],
    }
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "2025-12-20_summary.json").write_text(json.dumps(summary_data))
    
    # Create app and configure
    app = create_app()
    
    # Override report root for testing
    from src.webui.ops_stage1_router import router as stage1_router
    template_dir = Path(__file__).parents[1] / "templates" / "peak_trade_dashboard"
    templates = Jinja2Templates(directory=str(template_dir))
    set_stage1_config(tmp_path, templates)
    
    client = TestClient(app)
    response = client.get("/ops/stage1/latest")
    
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2025-12-20"
    assert data["metrics"]["new_alerts"] == 5


def test_stage1_trend_endpoint_query_params():
    """Test that trend endpoint accepts days parameter."""
    app = create_app()
    client = TestClient(app)
    
    # Test with different days values
    response = client.get("/ops/stage1/trend?days=7")
    assert response.status_code in [200, 404]
    
    response = client.get("/ops/stage1/trend?days=30")
    assert response.status_code in [200, 404]
    
    # Test invalid days (should reject)
    response = client.get("/ops/stage1/trend?days=0")
    assert response.status_code == 422  # Validation error
    
    response = client.get("/ops/stage1/trend?days=100")
    assert response.status_code == 422  # Validation error (max 90)

