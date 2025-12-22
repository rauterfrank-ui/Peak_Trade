# tests/test_webui_knowledge_endpoints.py
"""
Tests for Knowledge DB WebUI API Endpoints

Tests access control matrix:
- GET endpoints: Always available (200 or 501 if backend missing)
- POST endpoints: Gated by KNOWLEDGE_READONLY and KNOWLEDGE_WEB_WRITE_ENABLED

Run:
    pytest tests/test_webui_knowledge_endpoints.py -v
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Check if chromadb is available
try:
    import chromadb  # noqa: F401

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

skip_if_no_chromadb = pytest.mark.skipif(
    not CHROMADB_AVAILABLE, reason="chromadb not installed (graceful degradation - returns 501)"
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from src.webui.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_env_flags():
    """Reset environment flags before each test."""
    original_readonly = os.environ.get("KNOWLEDGE_READONLY")
    original_web_write = os.environ.get("KNOWLEDGE_WEB_WRITE_ENABLED")

    # Clear flags
    os.environ.pop("KNOWLEDGE_READONLY", None)
    os.environ.pop("KNOWLEDGE_WEB_WRITE_ENABLED", None)

    yield

    # Restore
    if original_readonly is not None:
        os.environ["KNOWLEDGE_READONLY"] = original_readonly
    else:
        os.environ.pop("KNOWLEDGE_READONLY", None)

    if original_web_write is not None:
        os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = original_web_write
    else:
        os.environ.pop("KNOWLEDGE_WEB_WRITE_ENABLED", None)


@pytest.fixture
def mock_knowledge_service():
    """Mock Knowledge Service to avoid chromadb dependency."""
    with patch("src.webui.knowledge_api.get_knowledge_service") as mock:
        service = Mock()
        service.is_available.return_value = True
        service.list_snippets.return_value = [
            {
                "id": "snippet_001",
                "title": "Test Snippet",
                "content": "Test content",
                "category": "test",
                "tags": ["test"],
                "created_at": "2024-12-22T00:00:00Z",
            }
        ]
        service.list_strategies.return_value = [
            {
                "id": "strategy_test",
                "name": "Test Strategy",
                "description": "Test description",
                "status": "rd",
                "tier": "experimental",
                "created_at": "2024-12-22T00:00:00Z",
            }
        ]
        service.search.return_value = [
            ("Test document", 0.95, {"type": "snippet"}),
        ]
        service.get_stats.return_value = {
            "backend": "chroma",
            "available": True,
            "total_documents": 10,
        }
        mock.return_value = service
        yield service


# =============================================================================
# Tests: GET /api/knowledge/snippets
# =============================================================================


def test_get_snippets_success(client, mock_knowledge_service):
    """Test GET snippets returns 200."""
    response = client.get("/api/knowledge/snippets")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["backend_available"] is True


def test_get_snippets_with_filters(client, mock_knowledge_service):
    """Test GET snippets with query parameters."""
    response = client.get("/api/knowledge/snippets?limit=10&category=strategy&tag=rsi")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data

    # Verify service was called with correct params
    mock_knowledge_service.list_snippets.assert_called_once()


def test_get_snippets_backend_unavailable(client):
    """Test GET snippets returns empty list if backend unavailable."""
    with patch("src.webui.knowledge_api.get_knowledge_service") as mock:
        service = Mock()
        service.is_available.return_value = False
        mock.return_value = service

        response = client.get("/api/knowledge/snippets")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["backend_available"] is False


# =============================================================================
# Tests: POST /api/knowledge/snippets (Access Control)
# =============================================================================


def test_post_snippet_blocked_by_readonly(client, mock_knowledge_service):
    """Test POST snippet blocked when KNOWLEDGE_READONLY=true."""
    os.environ["KNOWLEDGE_READONLY"] = "true"
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = "true"  # Even with this enabled

    response = client.post(
        "/api/knowledge/snippets",
        json={
            "content": "Test content",
            "title": "Test",
        },
    )

    assert response.status_code == 403
    data = response.json()
    assert "readonly" in data["detail"]["error"].lower()


def test_post_snippet_blocked_by_web_write_disabled(client, mock_knowledge_service):
    """Test POST snippet blocked when KNOWLEDGE_WEB_WRITE_ENABLED not set."""
    os.environ["KNOWLEDGE_READONLY"] = "false"
    # KNOWLEDGE_WEB_WRITE_ENABLED not set (default false)

    response = client.post(
        "/api/knowledge/snippets",
        json={
            "content": "Test content",
            "title": "Test",
        },
    )

    assert response.status_code == 403
    data = response.json()
    assert "WebUI write" in data["detail"]["error"]


@skip_if_no_chromadb
def test_post_snippet_success_when_both_flags_enabled(client, mock_knowledge_service):
    """Test POST snippet succeeds when both flags are enabled."""
    os.environ["KNOWLEDGE_READONLY"] = "false"
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = "true"

    mock_knowledge_service.add_snippet.return_value = {
        "id": "snippet_new",
        "title": "Test",
        "content": "Test content",
        "category": "general",
        "tags": [],
        "created_at": "2024-12-22T00:00:00Z",
    }

    response = client.post(
        "/api/knowledge/snippets",
        json={
            "content": "Test content",
            "title": "Test",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "snippet" in data


def test_post_snippet_backend_unavailable(client):
    """Test POST snippet returns 501 if backend unavailable."""
    os.environ["KNOWLEDGE_READONLY"] = "false"
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = "true"

    with patch("src.webui.knowledge_api.is_vector_db_available") as mock_available:
        mock_available.return_value = False

        response = client.post(
            "/api/knowledge/snippets",
            json={
                "content": "Test content",
                "title": "Test",
            },
        )

        assert response.status_code == 501
        data = response.json()
        assert "not available" in data["detail"]["error"].lower()


# =============================================================================
# Tests: GET /api/knowledge/strategies
# =============================================================================


def test_get_strategies_success(client, mock_knowledge_service):
    """Test GET strategies returns 200."""
    response = client.get("/api/knowledge/strategies")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_strategies_with_filters(client, mock_knowledge_service):
    """Test GET strategies with filters."""
    response = client.get("/api/knowledge/strategies?status=rd&name=test&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


# =============================================================================
# Tests: POST /api/knowledge/strategies (Access Control)
# =============================================================================


def test_post_strategy_blocked_by_readonly(client, mock_knowledge_service):
    """Test POST strategy blocked when KNOWLEDGE_READONLY=true."""
    os.environ["KNOWLEDGE_READONLY"] = "true"
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = "true"

    response = client.post(
        "/api/knowledge/strategies",
        json={
            "name": "Test Strategy",
            "description": "Test description",
            "status": "rd",
            "tier": "experimental",
        },
    )

    assert response.status_code == 403


def test_post_strategy_blocked_by_web_write_disabled(client, mock_knowledge_service):
    """Test POST strategy blocked when KNOWLEDGE_WEB_WRITE_ENABLED not set."""
    os.environ["KNOWLEDGE_READONLY"] = "false"

    response = client.post(
        "/api/knowledge/strategies",
        json={
            "name": "Test Strategy",
            "description": "Test description",
            "status": "rd",
            "tier": "experimental",
        },
    )

    assert response.status_code == 403


def test_post_strategy_success_when_both_flags_enabled(client, mock_knowledge_service):
    """Test POST strategy succeeds when both flags enabled."""
    os.environ["KNOWLEDGE_READONLY"] = "false"
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = "true"

    mock_knowledge_service.add_strategy.return_value = {
        "id": "strategy_test",
        "name": "Test Strategy",
        "description": "Test description",
        "status": "rd",
        "tier": "experimental",
        "created_at": "2024-12-22T00:00:00Z",
    }

    response = client.post(
        "/api/knowledge/strategies",
        json={
            "name": "Test Strategy",
            "description": "Test description",
            "status": "rd",
            "tier": "experimental",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True


# =============================================================================
# Tests: GET /api/knowledge/search
# =============================================================================


def test_search_success(client, mock_knowledge_service):
    """Test GET search returns 200."""
    response = client.get("/api/knowledge/search?q=test+strategy&k=5")

    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert data["query"] == "test strategy"


def test_search_backend_unavailable(client):
    """Test search returns 501 if backend unavailable."""
    with patch("src.webui.knowledge_api.is_vector_db_available") as mock_available:
        mock_available.return_value = False

        response = client.get("/api/knowledge/search?q=test")

        assert response.status_code == 501
        data = response.json()
        assert "not available" in data["detail"]["error"].lower()


def test_search_with_type_filter(client, mock_knowledge_service):
    """Test search with type filter."""
    response = client.get("/api/knowledge/search?q=test&k=3&type=strategy")

    assert response.status_code == 200
    data = response.json()
    assert "results" in data


# =============================================================================
# Tests: GET /api/knowledge/stats
# =============================================================================


def test_get_stats_success(client, mock_knowledge_service):
    """Test GET stats returns 200."""
    response = client.get("/api/knowledge/stats")

    assert response.status_code == 200
    data = response.json()
    assert "backend" in data
    assert "available" in data
    assert "environment" in data


def test_get_stats_includes_env_flags(client, mock_knowledge_service):
    """Test stats includes environment flags."""
    os.environ["KNOWLEDGE_READONLY"] = "true"
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = "false"

    response = client.get("/api/knowledge/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["environment"]["KNOWLEDGE_READONLY"] is True
    assert data["environment"]["KNOWLEDGE_WEB_WRITE_ENABLED"] is False


# =============================================================================
# Tests: Access Control Matrix
# =============================================================================


@pytest.mark.parametrize(
    "readonly,web_write,endpoint,method,expected_status",
    [
        # GET endpoints: Always 200 (or 501 if backend missing)
        ("false", "false", "/api/knowledge/snippets", "GET", 200),
        ("true", "false", "/api/knowledge/snippets", "GET", 200),
        ("false", "true", "/api/knowledge/snippets", "GET", 200),
        ("true", "true", "/api/knowledge/snippets", "GET", 200),
        ("false", "false", "/api/knowledge/strategies", "GET", 200),
        ("true", "true", "/api/knowledge/strategies", "GET", 200),
        ("false", "false", "/api/knowledge/stats", "GET", 200),
        ("true", "true", "/api/knowledge/stats", "GET", 200),
        # POST endpoints: Only allowed when both flags are permissive
        ("false", "false", "/api/knowledge/snippets", "POST", 403),  # Web write disabled
        ("true", "false", "/api/knowledge/snippets", "POST", 403),  # Readonly
        ("false", "true", "/api/knowledge/snippets", "POST", 201),  # Success
        ("true", "true", "/api/knowledge/snippets", "POST", 403),  # Readonly blocks
        ("false", "false", "/api/knowledge/strategies", "POST", 403),
        ("true", "false", "/api/knowledge/strategies", "POST", 403),
        ("false", "true", "/api/knowledge/strategies", "POST", 201),
        ("true", "true", "/api/knowledge/strategies", "POST", 403),
    ],
)
def test_access_control_matrix(
    client,
    mock_knowledge_service,
    readonly,
    web_write,
    endpoint,
    method,
    expected_status,
):
    """Test access control matrix for all endpoints."""
    os.environ["KNOWLEDGE_READONLY"] = readonly
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = web_write

    # Mock successful creation for POST
    if method == "POST":
        mock_knowledge_service.add_snippet.return_value = {"id": "test"}
        mock_knowledge_service.add_strategy.return_value = {"id": "test"}

    # Make request
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        if "snippets" in endpoint:
            response = client.post(endpoint, json={"content": "Test", "title": "Test"})
        else:
            response = client.post(
                endpoint,
                json={
                    "name": "Test",
                    "description": "Test",
                    "status": "rd",
                    "tier": "experimental",
                },
            )

    assert response.status_code == expected_status


# =============================================================================
# Tests: Error Messages
# =============================================================================


def test_readonly_error_message_is_clear(client, mock_knowledge_service):
    """Test that readonly error has clear message."""
    os.environ["KNOWLEDGE_READONLY"] = "true"
    os.environ["KNOWLEDGE_WEB_WRITE_ENABLED"] = "true"

    response = client.post(
        "/api/knowledge/snippets",
        json={"content": "Test", "title": "Test"},
    )

    assert response.status_code == 403
    data = response.json()
    assert "readonly" in data["detail"]["error"].lower()
    assert "solution" in data["detail"]


def test_web_write_disabled_error_message_is_clear(client, mock_knowledge_service):
    """Test that web write disabled error has clear message."""
    os.environ["KNOWLEDGE_READONLY"] = "false"
    # KNOWLEDGE_WEB_WRITE_ENABLED not set

    response = client.post(
        "/api/knowledge/snippets",
        json={"content": "Test", "title": "Test"},
    )

    assert response.status_code == 403
    data = response.json()
    assert "WebUI" in data["detail"]["error"]
    assert "KNOWLEDGE_WEB_WRITE_ENABLED=true" in data["detail"]["solution"]
