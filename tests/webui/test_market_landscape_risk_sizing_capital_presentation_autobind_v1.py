"""Focused autobind tests: CAPABILITY_PRESENTATION_RISK_SIZING_CAPITAL_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    REASON_RISK_SIZING_NOT_PERSISTED,
    RISK_SIZING_PRODUCER_MODULE,
    RISK_SIZING_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    LOAD_ERROR_ABSENT,
    LOAD_ERROR_AMBIGUOUS,
    LOAD_ERROR_AUTHORITY_CLAIM,
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    RISK_SIZING_AUTHORITY_EFFECT,
    SCHEMA_NAME,
    SOURCE_FIELDS_RELATIVE_PATH,
    STORAGE_RELATIVE_PATH,
    map_risk_sizing_capital_fields_to_binder_fields_v1,
    try_load_risk_sizing_capital_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _fields(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "risk_status": "PASS",
        "sizing_status": "PASS",
        "capital_status": "PASS",
        "quantity": 0.25,
        "reason_codes": ("PASS",),
        "evidence_digest": "a" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _projection_payload(
    *,
    risk_sizing_capital: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": 1,
        "authority_effect": AUTHORITY_EFFECT,
        "risk_sizing_authority_effect": RISK_SIZING_AUTHORITY_EFFECT,
        "projection_role": "NON_AUTHORITATIVE_PRESENTATION_PROJECTION",
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "source_reference": "presentation://risk_sizing_autobind_test",
        "risk_sizing_capital": (
            risk_sizing_capital if risk_sizing_capital is not None else _fields()
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
    fields, errors = map_risk_sizing_capital_fields_to_binder_fields_v1(
        risk_sizing_capital=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://x",
    )
    assert errors == ()
    assert fields is not None
    assert fields["risk_status"] == "PASS"
    assert fields["sizing_status"] == "PASS"
    assert fields["capital_status"] == "PASS"
    assert fields["quantity"] == 0.25
    assert fields["evidence_digest"] == "a" * 64
    assert fields["generated_at"] == PRODUCER_FRESH


def test_load_absent_projection_is_missing(tmp_path: Path) -> None:
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_ABSENT in loaded.load_errors
    assert loaded.binder_fields is None


def test_load_valid_projection_returns_binder_fields(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.binder_fields is not None
    assert loaded.risk_status == "PASS"
    assert loaded.evidence_digest == "a" * 64
    assert STORAGE_RELATIVE_PATH in str(loaded.source_path)


def test_load_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_name="wrong.schema"))
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_authority_claim_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(authority_effect="RISK"))
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AUTHORITY_CLAIM in loaded.load_errors


def test_load_invalid_fields_fail_closed(tmp_path: Path) -> None:
    _write_projection(
        tmp_path,
        _projection_payload(risk_sizing_capital={"risk_status": "PASS"}),
    )
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_FIELDS_INVALID in loaded.load_errors


def test_load_ambiguous_sibling_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    sibling = tmp_path / SOURCE_FIELDS_RELATIVE_PATH
    sibling.write_text(
        json.dumps(
            {
                "risk_status": "BLOCKED",
                "sizing_status": "PASS",
                "capital_status": "PASS",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
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
    risk = slots["risk_sizing_capital"]
    assert risk.availability is Availability.AVAILABLE
    assert risk.risk_status == "PASS"
    assert risk.sizing_status == "PASS"
    assert risk.capital_status == "PASS"
    assert risk.quantity == 0.25
    assert risk.provenance.producer_module == RISK_SIZING_PRODUCER_MODULE
    assert risk.provenance.source_kind == RISK_SIZING_SOURCE_KIND
    assert risk.provenance.source_reference == "presentation://risk_sizing_autobind_test"
    assert risk.provenance.evidence_digest == "a" * 64
    # Other injection-only slots remain unbound / missing.
    assert slots["canonical_decision"].availability is Availability.MISSING_SOURCE
    assert slots["double_play"].availability is Availability.MISSING_SOURCE
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert slots["dynamic_scope"].availability is Availability.MISSING_SOURCE
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
    assert slots["risk_sizing_capital"].availability is Availability.MISSING_SOURCE
    assert REASON_RISK_SIZING_NOT_PERSISTED in slots["risk_sizing_capital"].reason_codes


def test_autobind_invalid_projection_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_archive"
    _write_projection(archive, _projection_payload(schema_name="nope"))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["risk_sizing_capital"].availability is Availability.INVALID
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["risk_sizing_capital"].reason_codes


def test_explicit_injection_still_overrides_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        risk_sizing_capital_fields={
            "risk_status": "BLOCKED",
            "sizing_status": "BLOCKED",
            "capital_status": "BLOCKED",
            "quantity": 0.0,
            "reason_codes": ("INJECTED",),
            "risk_sizing_ref": "b" * 64,
            "generated_at": PRODUCER_FRESH,
            "source_reference": "risk://bounded-test-injection",
            "schema_version": "v1",
        },
    )
    risk = slots["risk_sizing_capital"]
    assert risk.availability is Availability.AVAILABLE
    assert risk.risk_status == "BLOCKED"
    assert risk.sizing_status == "BLOCKED"
    assert risk.capital_status == "BLOCKED"
    assert risk.quantity == 0.0
    assert risk.provenance.source_reference == "risk://bounded-test-injection"


def test_get_market_autobinds_risk_sizing_without_injection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(
        archive,
        _projection_payload(
            risk_sizing_capital=_fields(
                risk_status="PASS",
                sizing_status="PASS",
                capital_status="PASS",
                quantity=1.5,
                reason_codes=("AUTOBIND_OK",),
            )
        ),
    )
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "PASS" in html
    assert "1.5" in html
    assert 'data-mdl-ops="risk_sizing_capital"' in html
    assert 'data-mdl-field="risk_status"' in html
    assert 'data-mdl-field="sizing_status"' in html
    assert 'data-mdl-field="capital_status"' in html
    assert 'data-mdl-field="risk_quantity"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_projection_module_has_no_forbidden_trading_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "risk_sizing_capital_presentation_projection_v1.py"
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
                "evaluate_capital_risk_sizing_v1",
                "compose_double_play_decision",
                "KillSwitch",
            }
