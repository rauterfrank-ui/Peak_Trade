"""Focused tests: CAPABILITY_PRESENTATION_DYNAMIC_SCOPE_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    REASON_SCOPE_NOT_PERSISTED,
    SCOPE_PRODUCER_MODULE,
    SCOPE_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    DYNAMIC_SCOPE_AUTHORITY_EFFECT,
    LOAD_ERROR_ABSENT,
    LOAD_ERROR_AMBIGUOUS,
    LOAD_ERROR_AUTHORITY_CLAIM,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_SCOPE_INVALID,
    SCHEMA_NAME,
    STORAGE_RELATIVE_PATH,
    map_dynamic_scope_fields_to_binder_fields_v1,
    try_load_dynamic_scope_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _scope(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "scope_state": "scope_valid",
        "current_scope_ref": "scope-autobind-1",
        "next_scope_ref": "scope-autobind-2",
        "reason_codes": ("SCOPE_INITIALIZED",),
        "semantic_digest": "a" * 64,
    }
    base.update(overrides)
    return base


def _projection_payload(
    *,
    dynamic_scope: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": 1,
        "authority_effect": AUTHORITY_EFFECT,
        "dynamic_scope_authority_effect": DYNAMIC_SCOPE_AUTHORITY_EFFECT,
        "projection_role": "NON_AUTHORITATIVE_PRESENTATION_PROJECTION",
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "source_reference": "presentation://dynamic_scope_autobind_test",
        "dynamic_scope": dynamic_scope if dynamic_scope is not None else _scope(),
    }
    payload.update(overrides)
    return payload


def _write_projection(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_map_scope_to_binder_fields_preserves_producer_facts() -> None:
    fields, errors = map_dynamic_scope_fields_to_binder_fields_v1(
        dynamic_scope=_scope(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://x",
    )
    assert errors == ()
    assert fields is not None
    assert fields["scope_state"] == "scope_valid"
    assert fields["current_scope_ref"] == "scope-autobind-1"
    assert fields["next_scope_ref"] == "scope-autobind-2"
    assert fields["semantic_digest"] == "a" * 64
    assert fields["generated_at"] == PRODUCER_FRESH


def test_load_absent_projection_is_missing(tmp_path: Path) -> None:
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_ABSENT in loaded.load_errors
    assert loaded.binder_fields is None


def test_load_valid_projection_returns_binder_fields(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.binder_fields is not None
    assert loaded.current_scope_ref == "scope-autobind-1"
    assert loaded.evidence_digest == "a" * 64
    assert STORAGE_RELATIVE_PATH in str(loaded.source_path)


def test_load_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_name="wrong.schema"))
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_authority_claim_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(authority_effect="SCOPE"))
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AUTHORITY_CLAIM in loaded.load_errors


def test_load_invalid_scope_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(dynamic_scope={"scope_state": "scope_valid"}))
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCOPE_INVALID in loaded.load_errors


def test_load_ambiguous_sibling_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    sibling = tmp_path / "readmodels" / "dynamic_scope_state_v1.json"
    sibling.write_text(
        json.dumps(
            {
                "existing_scope": {
                    "scope_id": "other-scope",
                    "lifecycle_state": "scope_valid",
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AMBIGUOUS in loaded.load_errors


def test_autobind_available_from_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    scope = slots["dynamic_scope"]
    assert scope.availability is Availability.AVAILABLE
    assert scope.scope_state == "scope_valid"
    assert scope.current_scope_ref == "scope-autobind-1"
    assert scope.next_scope_ref == "scope-autobind-2"
    assert scope.provenance.producer_module == SCOPE_PRODUCER_MODULE
    assert scope.provenance.source_kind == SCOPE_SOURCE_KIND
    assert scope.provenance.source_reference == "presentation://dynamic_scope_autobind_test"
    assert scope.provenance.evidence_digest == "a" * 64
    # Other injection-only slots remain unbound / missing.
    assert slots["canonical_decision"].availability is Availability.MISSING_SOURCE
    assert slots["double_play"].availability is Availability.MISSING_SOURCE
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert slots["risk_sizing_capital"].availability is Availability.MISSING_SOURCE
    assert slots["execution_reconciliation"].availability is Availability.MISSING_SOURCE
    assert slots["economic_summary"].availability is Availability.MISSING_SOURCE
    assert slots["regime_bull_bear_switch"].availability is Availability.MISSING_SOURCE


def test_autobind_missing_projection_is_missing_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "empty_archive"
    archive.mkdir()
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["dynamic_scope"].availability is Availability.MISSING_SOURCE
    assert REASON_SCOPE_NOT_PERSISTED in slots["dynamic_scope"].reason_codes


def test_autobind_invalid_projection_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_archive"
    _write_projection(archive, _projection_payload(schema_name="nope"))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["dynamic_scope"].availability is Availability.INVALID
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["dynamic_scope"].reason_codes


def test_explicit_injection_still_overrides_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        dynamic_scope_fields={
            "lifecycle_state": "scope_stale",
            "scope_id": "injected-scope",
            "next_scope_ref": "injected-next",
            "reason_codes": ("INJECTED",),
            "semantic_digest": "b" * 64,
            "generated_at": PRODUCER_FRESH,
            "source_reference": "scope://bounded-test-injection",
        },
    )
    scope = slots["dynamic_scope"]
    assert scope.availability is Availability.AVAILABLE
    assert scope.scope_state == "scope_stale"
    assert scope.current_scope_ref == "injected-scope"
    assert scope.next_scope_ref == "injected-next"
    assert scope.provenance.source_reference == "scope://bounded-test-injection"


def test_get_market_autobinds_dynamic_scope_without_injection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(
        archive,
        _projection_payload(
            dynamic_scope=_scope(
                scope_state="scope_valid",
                current_scope_ref="scope-shell-1",
                next_scope_ref=None,
                reason_codes=("AUTOBIND_OK",),
            )
        ),
    )
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "scope_valid" in html
    assert "scope-shell-1" in html
    assert 'data-mdl-field="scope_lifecycle"' in html
    assert 'data-mdl-field="current_scope_ref"' in html
    assert 'data-mdl-region="SYSTEM_CONTEXT_RAIL"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_projection_module_has_no_forbidden_trading_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1/dynamic_scope_presentation_projection_v1.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                imported.add(node.module.split(".", 1)[0])
    assert "trading" not in imported
    assert "src" not in imported
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "persist_dynamic_scope_state_atomic_v1",
                "transition_state",
                "compose_double_play_decision",
                "KillSwitch",
            }
