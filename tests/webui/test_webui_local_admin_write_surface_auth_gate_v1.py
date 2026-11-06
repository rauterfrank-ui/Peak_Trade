"""Contract tests for WEBUI_LOCAL_ADMIN_WRITE_SURFACE_AUTH_GATE_V1.

Proves fail-closed local-admin auth on administrative write/trigger surfaces.
Never embeds production-shaped secrets; fixture tokens are clearly synthetic.
"""

from __future__ import annotations

import hmac
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
from starlette.requests import Request

from src.webui import local_admin_write_auth_v1 as auth
from src.webui.knowledge_api import router as knowledge_router
from src.webui.ops_ci_health_router import router as ci_health_router
from src.webui.ops_ci_health_router import set_ci_health_config

# Synthetic fixture tokens — deliberately not shaped like production secrets.
_FIXTURE_OK = "fixture-token-not-a-secret"
_FIXTURE_OTHER = "fixture-token-also-not-a-secret"


def _make_request(headers: dict[str, str] | None = None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/probe",
        "raw_path": b"/probe",
        "query_string": b"",
        "headers": [
            (k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }
    return Request(scope)


@pytest.fixture
def configured_token(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv(auth.AUTH_TOKEN_ENV_NAME, _FIXTURE_OK)
    return _FIXTURE_OK


def test_owner_identity_is_unique() -> None:
    identity = auth.owner_identity()
    assert identity["capability_id"] == "WEBUI_LOCAL_ADMIN_WRITE_SURFACE_AUTH_GATE_V1"
    assert identity["contract_id"] == "webui_local_admin_write_auth_v1"
    assert identity["module"] == "src.webui.local_admin_write_auth_v1"
    assert identity["auth_token_env_name"] == "PEAK_TRADE_WEBUI_LOCAL_ADMIN_TOKEN"
    assert identity["auth_header_name"] == "X-Peak-Trade-Local-Admin-Token"


def test_not_configured_when_env_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException

    monkeypatch.delenv(auth.AUTH_TOKEN_ENV_NAME, raising=False)
    with pytest.raises(HTTPException) as exc:
        auth.require_local_admin_write_auth(_make_request({auth.AUTH_HEADER_NAME: _FIXTURE_OK}))
    assert exc.value.status_code == 503
    assert exc.value.detail["error"] == auth.REASON_NOT_CONFIGURED
    assert _FIXTURE_OK not in repr(exc.value.detail)


def test_not_configured_when_env_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException

    monkeypatch.setenv(auth.AUTH_TOKEN_ENV_NAME, "")
    with pytest.raises(HTTPException) as exc:
        auth.require_local_admin_write_auth(_make_request({auth.AUTH_HEADER_NAME: _FIXTURE_OK}))
    assert exc.value.status_code == 503
    assert exc.value.detail["error"] == auth.REASON_NOT_CONFIGURED


def test_not_configured_when_env_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException

    monkeypatch.setenv(auth.AUTH_TOKEN_ENV_NAME, "   \t  ")
    with pytest.raises(HTTPException) as exc:
        auth.require_local_admin_write_auth(_make_request({auth.AUTH_HEADER_NAME: _FIXTURE_OK}))
    assert exc.value.status_code == 503
    assert exc.value.detail["error"] == auth.REASON_NOT_CONFIGURED


def test_missing_header_rejected(configured_token: str) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        auth.require_local_admin_write_auth(_make_request())
    assert exc.value.status_code == 401
    assert exc.value.detail["error"] == auth.REASON_MISSING
    assert configured_token not in repr(exc.value.detail)


def test_empty_header_rejected(configured_token: str) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        auth.require_local_admin_write_auth(_make_request({auth.AUTH_HEADER_NAME: ""}))
    assert exc.value.status_code == 401
    assert exc.value.detail["error"] == auth.REASON_MISSING


def test_invalid_token_rejected(configured_token: str) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        auth.require_local_admin_write_auth(_make_request({auth.AUTH_HEADER_NAME: _FIXTURE_OTHER}))
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == auth.REASON_INVALID
    assert configured_token not in repr(exc.value.detail)
    assert _FIXTURE_OTHER not in repr(exc.value.detail)


def test_valid_token_accepted(configured_token: str) -> None:
    auth.require_local_admin_write_auth(_make_request({auth.AUTH_HEADER_NAME: configured_token}))


def test_tokens_match_uses_hmac_compare_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[bytes, bytes]] = []
    original = hmac.compare_digest

    def _spy(a: bytes, b: bytes) -> bool:
        calls.append((a, b))
        return original(a, b)

    monkeypatch.setattr(auth.hmac, "compare_digest", _spy)
    assert auth.tokens_match(provided=_FIXTURE_OK, expected=_FIXTURE_OK) is True
    assert auth.tokens_match(provided=_FIXTURE_OK, expected=_FIXTURE_OTHER) is False
    assert calls, "constant-time compare_digest must be used"


def test_query_param_token_is_ignored(configured_token: str) -> None:
    from fastapi import HTTPException

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/probe",
        "raw_path": b"/probe",
        "query_string": f"{auth.AUTH_TOKEN_ENV_NAME}={configured_token}".encode(),
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }
    with pytest.raises(HTTPException) as exc:
        auth.require_local_admin_write_auth(Request(scope))
    assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# Ops CI-health route integration
# ---------------------------------------------------------------------------


@pytest.fixture
def ci_health_client(tmp_path: Path, configured_token: str) -> TestClient:
    repo_root = tmp_path / "repo"
    scripts = repo_root / "scripts" / "ops"
    scripts.mkdir(parents=True)
    for name in (
        "check_required_ci_contexts_present.sh",
        "verify_docs_reference_targets.sh",
    ):
        path = scripts / name
        path.write_text("#!/usr/bin/env bash\necho OK\nexit 0\n")
        path.chmod(0o755)

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "ops_ci_health.html").write_text(
        "<html><body>{{ overall_status }}</body></html>"
    )
    set_ci_health_config(repo_root, Jinja2Templates(directory=str(templates_dir)))
    app = FastAPI()
    app.include_router(ci_health_router)
    return TestClient(app)


def test_ci_health_post_valid_token_succeeds(ci_health_client: TestClient) -> None:
    response = ci_health_client.post(
        "/ops/ci-health/run",
        headers={auth.AUTH_HEADER_NAME: _FIXTURE_OK},
    )
    assert response.status_code == 200
    assert response.json()["run_triggered"] is True
    assert _FIXTURE_OK not in response.text


def test_ci_health_post_missing_token_no_subprocess(
    ci_health_client: TestClient, tmp_path: Path
) -> None:
    with patch(
        "src.webui.ops_ci_health_router._run_all_checks",
        side_effect=AssertionError("must not run"),
    ) as mocked:
        response = ci_health_client.post("/ops/ci-health/run")
    assert response.status_code == 401
    mocked.assert_not_called()
    assert not (tmp_path / "repo" / "reports" / "ops").exists()


# ---------------------------------------------------------------------------
# Knowledge write surfaces
# ---------------------------------------------------------------------------


@pytest.fixture
def knowledge_client(configured_token: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("KNOWLEDGE_READONLY", "false")
    monkeypatch.setenv("KNOWLEDGE_WEB_WRITE_ENABLED", "true")
    monkeypatch.setenv("WEBUI_KNOWLEDGE_ALLOW_FALLBACK", "true")
    app = FastAPI()
    app.include_router(knowledge_router)
    return TestClient(app)


@pytest.mark.parametrize(
    "path,payload",
    [
        (
            "/api/knowledge/snippets",
            {
                "content": "fixture snippet body",
                "title": "t",
                "category": "c",
                "tags": [],
            },
        ),
        (
            "/api/knowledge/strategies",
            {
                "name": "fixture-strategy",
                "description": "d",
                "status": "rd",
                "tier": "experimental",
            },
        ),
    ],
)
def test_knowledge_post_requires_local_admin_when_env_enabled(
    knowledge_client: TestClient, path: str, payload: dict
) -> None:
    missing = knowledge_client.post(path, json=payload)
    assert missing.status_code == 401
    assert missing.json()["detail"]["error"] == auth.REASON_MISSING

    invalid = knowledge_client.post(
        path, json=payload, headers={auth.AUTH_HEADER_NAME: _FIXTURE_OTHER}
    )
    assert invalid.status_code == 403
    assert invalid.json()["detail"]["error"] == auth.REASON_INVALID

    ok = knowledge_client.post(path, json=payload, headers={auth.AUTH_HEADER_NAME: _FIXTURE_OK})
    assert ok.status_code == 201
    assert ok.json()["success"] is True
    assert _FIXTURE_OK not in ok.text


def test_knowledge_post_env_gate_still_blocks_with_valid_token(
    configured_token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KNOWLEDGE_READONLY", "false")
    monkeypatch.delenv("KNOWLEDGE_WEB_WRITE_ENABLED", raising=False)
    monkeypatch.setenv("WEBUI_KNOWLEDGE_ALLOW_FALLBACK", "true")
    app = FastAPI()
    app.include_router(knowledge_router)
    client = TestClient(app)

    response = client.post(
        "/api/knowledge/snippets",
        json={"content": "x", "title": "t", "category": "c", "tags": []},
        headers={auth.AUTH_HEADER_NAME: configured_token},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "WebUI write access disabled"


def test_knowledge_denied_auth_performs_no_mutation(
    knowledge_client: TestClient,
) -> None:
    with patch(
        "src.webui.knowledge_api.get_knowledge_service",
        side_effect=AssertionError("service must not be touched"),
    ):
        response = knowledge_client.post(
            "/api/knowledge/snippets",
            json={"content": "x", "title": "t", "category": "c", "tags": []},
        )
    assert response.status_code == 401


def test_token_not_logged_on_denial(
    configured_token: str, caplog: pytest.LogCaptureFixture
) -> None:
    from fastapi import HTTPException

    with caplog.at_level(logging.INFO, logger=auth.logger.name):
        with pytest.raises(HTTPException):
            auth.require_local_admin_write_auth(
                _make_request({auth.AUTH_HEADER_NAME: _FIXTURE_OTHER})
            )
    joined = "\n".join(r.getMessage() for r in caplog.records)
    assert configured_token not in joined
    assert _FIXTURE_OTHER not in joined
    assert "LOCAL_ADMIN_AUTH_INVALID" in joined


def test_real_template_has_header_name_but_no_token_literal() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    html = (repo_root / "templates" / "peak_trade_dashboard" / "ops_ci_health.html").read_text(
        encoding="utf-8"
    )
    assert auth.AUTH_HEADER_NAME in html
    assert "window.prompt" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert auth.AUTH_TOKEN_ENV_NAME not in html
    assert _FIXTURE_OK not in html
    # Token must not be embedded as a literal assignment value.
    assert "PEAK_TRADE_WEBUI_LOCAL_ADMIN_TOKEN=" not in html
