"""
Tests for WebUI API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from src.webui.api.app import app

client = TestClient(app)


def test_health_endpoint():
    """Test health endpoint returns expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in data


def test_health_detailed_endpoint():
    """Test detailed health endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "service" in data[0]
        assert "healthy" in data[0]


def test_portfolio_summary_endpoint():
    """Test portfolio summary endpoint."""
    response = client.get("/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_value" in data
    assert "cash" in data
    assert "positions" in data
    assert "pnl" in data
    assert "pnl_percent" in data


def test_portfolio_positions_endpoint():
    """Test portfolio positions endpoint."""
    response = client.get("/portfolio/positions")
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert isinstance(data["positions"], list)


def test_performance_metrics_endpoint():
    """Test performance metrics endpoint."""
    response = client.get("/metrics/performance")
    assert response.status_code == 200
    data = response.json()
    assert "operations" in data
    assert isinstance(data["operations"], list)


def test_circuit_breakers_endpoint():
    """Test circuit breakers endpoint."""
    response = client.get("/circuit-breakers")
    assert response.status_code == 200
    data = response.json()
    assert "circuit_breakers" in data


def test_backups_list_endpoint():
    """Test backups list endpoint."""
    response = client.get("/backups/list")
    assert response.status_code == 200
    data = response.json()
    assert "backups" in data


def test_backtest_results_endpoint():
    """Test backtest results endpoint."""
    response = client.get("/backtest/results")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


def test_api_docs_available():
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data
