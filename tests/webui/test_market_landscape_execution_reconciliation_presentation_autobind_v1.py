"""Focused autobind tests: CAPABILITY_PRESENTATION_EXECUTION_RECONCILIATION_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    EXECUTION_PRODUCER_MODULE,
    EXECUTION_SOURCE_KIND,
    REASON_EXECUTION_NOT_PERSISTED,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    EXECUTION_AUTHORITY_EFFECT,
    LOAD_ERROR_ABSENT,
    LOAD_ERROR_AMBIGUOUS,
    LOAD_ERROR_AUTHORITY_CLAIM,
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    SCHEMA_NAME,
    SOURCE_FIELDS_RELATIVE_PATH,
    STORAGE_RELATIVE_PATH,
    map_execution_reconciliation_fields_to_binder_fields_v1,
    try_load_execution_reconciliation_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _fields(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "execution_status": "BOUND_OFFLINE",
        "reconciliation_status": "RECONCILED",
        "order_intent_ref": "intent://" + ("a" * 16),
        "reason_codes": ("PASS",),
        "evidence_digest": "a" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _projection_payload(
    *,
    execution_reconciliation: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": 1,
        "authority_effect": AUTHORITY_EFFECT,
        "execution_authority_effect": EXECUTION_AUTHORITY_EFFECT,
        "projection_role": "NON_AUTHORITATIVE_PRESENTATION_PROJECTION",
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "source_reference": "presentation://execution_autobind_test",
        "execution_reconciliation": (
            execution_reconciliation if execution_reconciliation is not None else _fields()
        ),
    }
    payload.update(overrides)
    return payload


def _write_projection(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_map_fields_to_binder_fields_preserves_producer_facts() -> None:
    fields, errors = map_execution_reconciliation_fields_to_binder_fields_v1(
        execution_reconciliation=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://x",
    )
    assert errors == ()
    assert fields is not None
    assert fields["execution_status"] == "BOUND_OFFLINE"
    assert fields["reconciliation_status"] == "RECONCILED"
    assert fields["order_intent_ref"] == "intent://" + ("a" * 16)
    assert fields["evidence_digest"] == "a" * 64
    assert fields["generated_at"] == PRODUCER_FRESH


def test_load_absent_projection_is_missing(tmp_path: Path) -> None:
    loaded = try_load_execution_reconciliation_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_ABSENT in loaded.load_errors
    assert loaded.binder_fields is None


def test_load_valid_projection_returns_binder_fields(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    loaded = try_load_execution_reconciliation_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.binder_fields is not None
    assert loaded.execution_status == "BOUND_OFFLINE"
    assert loaded.evidence_digest == "a" * 64
    assert STORAGE_RELATIVE_PATH in str(loaded.source_path)


def test_load_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_name="wrong.schema"))
    loaded = try_load_execution_reconciliation_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_authority_claim_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(authority_effect="EXECUTION"))
    loaded = try_load_execution_reconciliation_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AUTHORITY_CLAIM in loaded.load_errors


def test_load_invalid_fields_fail_closed(tmp_path: Path) -> None:
    _write_projection(
        tmp_path,
        _projection_payload(execution_reconciliation={"reconciliation_status": "RECONCILED"}),
    )
    loaded = try_load_execution_reconciliation_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_FIELDS_INVALID in loaded.load_errors


def test_load_ambiguous_sibling_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    sibling = tmp_path / SOURCE_FIELDS_RELATIVE_PATH
    sibling.write_text(
        json.dumps(
            {
                "execution_status": "FAILED",
                "reconciliation_status": "RECONCILED",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = try_load_execution_reconciliation_presentation_projection_v1(tmp_path)
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
    execution = slots["execution_reconciliation"]
    assert execution.availability is Availability.AVAILABLE
    assert execution.execution_status == "BOUND_OFFLINE"
    assert execution.reconciliation_status == "RECONCILED"
    assert execution.order_intent_ref == "intent://" + ("a" * 16)
    assert execution.provenance.producer_module == EXECUTION_PRODUCER_MODULE
    assert execution.provenance.source_kind == EXECUTION_SOURCE_KIND
    assert execution.provenance.source_reference == "presentation://execution_autobind_test"
    assert execution.provenance.evidence_digest == "a" * 64
    # Other injection-only / unbound slots remain missing when not projected.
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert slots["economic_summary"].availability is Availability.MISSING_SOURCE


def test_autobind_missing_projection_is_missing_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "empty_archive"
    archive.mkdir()
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["execution_reconciliation"].availability is Availability.MISSING_SOURCE
    assert REASON_EXECUTION_NOT_PERSISTED in slots["execution_reconciliation"].reason_codes


def test_autobind_invalid_projection_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_archive"
    _write_projection(archive, _projection_payload(schema_name="nope"))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["execution_reconciliation"].availability is Availability.INVALID
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["execution_reconciliation"].reason_codes


def test_explicit_injection_still_overrides_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        execution_reconciliation_fields={
            "execution_status": "FAILED",
            "reconciliation_status": "UNKNOWN",
            "order_intent_ref": "intent://injected",
            "reason_codes": ("INJECTED",),
            "semantic_digest": "b" * 64,
            "generated_at": PRODUCER_FRESH,
            "source_reference": "execution://bounded-test-injection",
            "schema_version": "v1",
        },
    )
    execution = slots["execution_reconciliation"]
    assert execution.availability is Availability.AVAILABLE
    assert execution.execution_status == "FAILED"
    assert execution.reconciliation_status == "UNKNOWN"
    assert execution.order_intent_ref == "intent://injected"
    assert execution.provenance.source_reference == "execution://bounded-test-injection"


def test_get_market_autobinds_execution_without_injection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(
        archive,
        _projection_payload(
            execution_reconciliation=_fields(
                execution_status="BOUND_OFFLINE",
                reconciliation_status="RECONCILED",
                reason_codes=("AUTOBIND_OK",),
            )
        ),
    )
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "BOUND_OFFLINE" in html
    assert "RECONCILED" in html
    assert 'data-mdl-ops="execution_reconciliation"' in html
    assert 'data-mdl-field="execution_status"' in html
    assert 'data-mdl-field="reconciliation_status"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_projection_module_has_no_forbidden_trading_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "execution_reconciliation_presentation_projection_v1.py"
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
                "build_canonical_order_intent_v1",
                "compose_double_play_decision",
                "KillSwitch",
            }
