"""Focused tests: CAPABILITY_PRESENTATION_CANONICAL_DECISION_AUTOBIND_V1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    DECISION_EVIDENCE_SCHEMA_VERSION,
    DECISION_PRODUCER_MODULE,
    DECISION_SOURCE_KIND,
    REASON_DECISION_NOT_PERSISTED,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    DECISION_AUTHORITY_EFFECT,
    LOAD_ERROR_ABSENT,
    LOAD_ERROR_AMBIGUOUS,
    LOAD_ERROR_AUTHORITY_CLAIM,
    LOAD_ERROR_EVIDENCE_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    SCHEMA_NAME,
    STORAGE_RELATIVE_PATH,
    map_canonical_decision_evidence_to_binder_fields_v1,
    try_load_canonical_decision_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _evidence(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "instrument_id": "ETH-USDT-SWAP",
        "decision_outcome": "observe",
        "next_direction_state": "neutral_observe",
        "decision_id": "decision-autobind-1",
        "evidence_schema_version": DECISION_EVIDENCE_SCHEMA_VERSION,
        "reason_codes": ("WARMUP_ACTIVE", "NO_ENTRY"),
        "semantic_digest": "a" * 64,
    }
    base.update(overrides)
    return base


def _projection_payload(
    *,
    evidence: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": 1,
        "authority_effect": AUTHORITY_EFFECT,
        "decision_authority_effect": DECISION_AUTHORITY_EFFECT,
        "projection_role": "NON_AUTHORITATIVE_PRESENTATION_PROJECTION",
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "source_reference": "presentation://canonical_decision_autobind_test",
        "evidence": evidence if evidence is not None else _evidence(),
    }
    payload.update(overrides)
    return payload


def _write_projection(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_map_evidence_to_binder_fields_preserves_producer_facts() -> None:
    fields, errors = map_canonical_decision_evidence_to_binder_fields_v1(
        evidence=_evidence(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://x",
    )
    assert errors == ()
    assert fields is not None
    assert fields["instrument_id"] == "ETH-USDT-SWAP"
    assert fields["decision_outcome"] == "observe"
    assert fields["next_direction_state"] == "neutral_observe"
    assert fields["decision_id"] == "decision-autobind-1"
    assert fields["semantic_digest"] == "a" * 64
    assert fields["generated_at"] == PRODUCER_FRESH


def test_load_absent_projection_is_missing(tmp_path: Path) -> None:
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_ABSENT in loaded.load_errors
    assert loaded.binder_fields is None


def test_load_valid_projection_returns_binder_fields(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.binder_fields is not None
    assert loaded.decision_id == "decision-autobind-1"
    assert loaded.evidence_digest == "a" * 64
    assert STORAGE_RELATIVE_PATH in str(loaded.source_path)


def test_load_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_name="wrong.schema"))
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_authority_claim_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(authority_effect="DECISION"))
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AUTHORITY_CLAIM in loaded.load_errors


def test_load_invalid_evidence_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(evidence={"instrument_id": "X"}))
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_EVIDENCE_INVALID in loaded.load_errors


def test_load_ambiguous_sibling_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    sibling = tmp_path / "readmodels" / "canonical_trading_decision_evidence.v1.json"
    sibling.write_text(
        json.dumps({"decision_id": "other-decision", "instrument_id": "ETH-USDT-SWAP"}) + "\n",
        encoding="utf-8",
    )
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
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
    decision = slots["canonical_decision"]
    assert decision.availability is Availability.AVAILABLE
    assert decision.decision == "observe"
    assert decision.direction == "neutral_observe"
    assert decision.decision_id == "decision-autobind-1"
    assert decision.provenance.producer_module == DECISION_PRODUCER_MODULE
    assert decision.provenance.source_kind == DECISION_SOURCE_KIND
    assert decision.provenance.source_reference == "presentation://canonical_decision_autobind_test"
    assert decision.provenance.evidence_digest == "a" * 64
    # Other injection-only slots remain unbound / missing.
    assert slots["dynamic_scope"].availability is Availability.MISSING_SOURCE
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
    assert slots["canonical_decision"].availability is Availability.MISSING_SOURCE
    assert REASON_DECISION_NOT_PERSISTED in slots["canonical_decision"].reason_codes


def test_autobind_invalid_projection_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_archive"
    _write_projection(archive, _projection_payload(schema_name="nope"))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["canonical_decision"].availability is Availability.INVALID
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["canonical_decision"].reason_codes


def test_explicit_injection_still_overrides_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        canonical_decision_fields={
            "instrument_id": "BTC-USDT-SWAP",
            "decision_outcome": "hold",
            "next_direction_state": "flat",
            "decision_id": "injected-decision",
            "evidence_schema_version": DECISION_EVIDENCE_SCHEMA_VERSION,
            "reason_codes": ("INJECTED",),
            "semantic_digest": "b" * 64,
            "generated_at": PRODUCER_FRESH,
            "source_reference": "decision://bounded-test-injection",
        },
    )
    decision = slots["canonical_decision"]
    assert decision.availability is Availability.AVAILABLE
    assert decision.decision == "hold"
    assert decision.decision_id == "injected-decision"
    assert decision.provenance.source_reference == "decision://bounded-test-injection"


def test_get_market_autobinds_decision_without_injection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(
        archive,
        _projection_payload(
            evidence=_evidence(
                decision_outcome="observe",
                reason_codes=("AUTOBIND_OK",),
            )
        ),
    )
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "observe" in html
    assert "AUTOBIND_OK" in html
    assert 'data-mdl-region="CANONICAL_DECISION_STRIP"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_projection_module_has_no_forbidden_trading_imports() -> None:
    import ast

    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1/canonical_decision_presentation_projection_v1.py"
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
                "transition_state",
                "compose_double_play_decision",
                "KillSwitch",
            }
