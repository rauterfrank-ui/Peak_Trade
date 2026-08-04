"""Focused autobind tests: CAPABILITY_PRESENTATION_ECONOMIC_SUMMARY_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    ECONOMIC_PRODUCER_MODULE,
    ECONOMIC_SOURCE_KIND,
    REASON_ECONOMIC_NOT_PERSISTED,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    ECONOMIC_AUTHORITY_EFFECT,
    LOAD_ERROR_ABSENT,
    LOAD_ERROR_AMBIGUOUS,
    LOAD_ERROR_AUTHORITY_CLAIM,
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    SCHEMA_NAME,
    SOURCE_FIELDS_RELATIVE_PATH,
    STORAGE_RELATIVE_PATH,
    map_economic_summary_fields_to_binder_fields_v1,
    try_load_economic_summary_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _metric(*, value: float | None = None, semantic: str = "COMPUTED") -> dict[str, object]:
    payload: dict[str, object] = {"semantic": semantic}
    if value is not None:
        payload["value"] = value
    return payload


def _fields(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "status": "ECONOMICALLY_VIABLE_OFFLINE",
        "economic_validity_proven": True,
        "profitability_claim_allowed": False,
        "policy_threshold_status": "PASS",
        "policy_version": "economic_validity_policy_v1",
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
        "reason_codes": ("PASS",),
        "profit_factor": _metric(value=1.77),
        "net_return": _metric(value=0.123),
        "max_drawdown": _metric(value=-0.045),
        "sharpe": _metric(value=0.88),
        "trade_count": _metric(value=42.0),
        "funding_drag": _metric(value=-0.003),
        "contract_version": "v1",
        "owner": "backtest.economic_viability_evidence_v1",
        "strategy_id": "sentinel_strategy",
        "strategy_version": "sentinel_v9",
        "config_digest": "c" * 64,
        "implementation_digest": "i" * 64,
        "data_digest": "d" * 64,
        "manifest_digest": "m" * 64,
        "wiring_chain_digest": "w" * 64,
        "policy_digest": "p" * 64,
        "evidence_digest": "m" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _projection_payload(
    *,
    economic_summary: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": 1,
        "authority_effect": AUTHORITY_EFFECT,
        "economic_authority_effect": ECONOMIC_AUTHORITY_EFFECT,
        "projection_role": "NON_AUTHORITATIVE_PRESENTATION_PROJECTION",
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "source_reference": "presentation://economic_autobind_test",
        "economic_summary": (economic_summary if economic_summary is not None else _fields()),
    }
    payload.update(overrides)
    return payload


def _write_projection(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_map_fields_to_binder_fields_preserves_producer_facts() -> None:
    fields, errors = map_economic_summary_fields_to_binder_fields_v1(
        economic_summary=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://x",
    )
    assert errors == ()
    assert fields is not None
    assert fields["status"] == "ECONOMICALLY_VIABLE_OFFLINE"
    assert fields["policy_threshold_status"] == "PASS"
    assert fields["profit_factor"]["value"] == 1.77
    assert fields["evidence_digest"] == "m" * 64
    assert fields["generated_at"] == PRODUCER_FRESH


def test_load_absent_projection_is_missing(tmp_path: Path) -> None:
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_ABSENT in loaded.load_errors
    assert loaded.binder_fields is None


def test_load_valid_projection_returns_binder_fields(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.binder_fields is not None
    assert loaded.status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert loaded.evidence_digest == "m" * 64
    assert STORAGE_RELATIVE_PATH in str(loaded.source_path)


def test_load_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_name="wrong.schema"))
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_authority_claim_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(authority_effect="AUTHORIZE"))
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AUTHORITY_CLAIM in loaded.load_errors


def test_load_invalid_fields_fail_closed(tmp_path: Path) -> None:
    _write_projection(
        tmp_path,
        _projection_payload(economic_summary={"status": "ECONOMICALLY_VIABLE_OFFLINE"}),
    )
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_FIELDS_INVALID in loaded.load_errors


def test_load_ambiguous_sibling_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    sibling = tmp_path / SOURCE_FIELDS_RELATIVE_PATH
    sibling.write_text(
        json.dumps({"status": "RESEARCH_ONLY", "manifest_digest": "z" * 64}) + "\n",
        encoding="utf-8",
    )
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
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
    economic = slots["economic_summary"]
    assert economic.availability is Availability.AVAILABLE
    assert economic.economic_viability_status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert economic.economic_validity_proven is True
    assert economic.policy_threshold_status == "PASS"
    assert economic.profit_factor == {"semantic": "COMPUTED", "value": 1.77}
    assert economic.provenance.producer_module == ECONOMIC_PRODUCER_MODULE
    assert economic.provenance.source_kind == ECONOMIC_SOURCE_KIND
    assert economic.provenance.source_reference == "presentation://economic_autobind_test"
    assert economic.provenance.evidence_digest == "m" * 64
    assert slots["canonical_decision"].availability is Availability.MISSING_SOURCE
    assert slots["double_play"].availability is Availability.MISSING_SOURCE
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert slots["dynamic_scope"].availability is Availability.MISSING_SOURCE
    assert slots["execution_reconciliation"].availability is Availability.MISSING_SOURCE
    assert slots["risk_sizing_capital"].availability is Availability.MISSING_SOURCE
    assert slots["regime_bull_bear_switch"].availability is Availability.MISSING_SOURCE


def test_autobind_missing_projection_is_missing_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "empty_archive"
    archive.mkdir()
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["economic_summary"].availability is Availability.MISSING_SOURCE
    assert REASON_ECONOMIC_NOT_PERSISTED in slots["economic_summary"].reason_codes


def test_autobind_invalid_projection_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_archive"
    _write_projection(archive, _projection_payload(schema_name="nope"))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["economic_summary"].availability is Availability.INVALID
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["economic_summary"].reason_codes


def test_explicit_injection_still_overrides_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        economic_viability_evidence_fields={
            **_fields(
                status="RESEARCH_ONLY",
                economic_validity_proven=False,
                policy_threshold_status="FAIL",
                profit_factor=_metric(value=0.5),
                reason_codes=("INJECTED",),
                evidence_digest="b" * 64,
                manifest_digest="b" * 64,
            ),
            "generated_at": PRODUCER_FRESH,
            "source_reference": "economic://bounded-test-injection",
        },
    )
    economic = slots["economic_summary"]
    assert economic.availability is Availability.AVAILABLE
    assert economic.economic_viability_status == "RESEARCH_ONLY"
    assert economic.economic_validity_proven is False
    assert economic.policy_threshold_status == "FAIL"
    assert economic.profit_factor == {"semantic": "COMPUTED", "value": 0.5}
    assert economic.provenance.source_reference == "economic://bounded-test-injection"


def test_get_market_autobinds_economic_without_injection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(
        archive,
        _projection_payload(
            economic_summary=_fields(
                status="ECONOMICALLY_VIABLE_OFFLINE",
                reason_codes=("AUTOBIND_OK",),
            )
        ),
    )
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "ECONOMICALLY_VIABLE_OFFLINE" in html
    assert 'data-mdl-ops="economic_summary"' in html
    assert 'data-mdl-field="economic"' in html
    assert 'data-mdl-field="economic_validity"' in html
    assert 'data-mdl-field="economic_policy_threshold"' in html
    assert 'data-mdl-field="economic_profit_factor"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_projection_module_has_no_forbidden_trading_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "economic_summary_presentation_projection_v1.py"
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
    assert "backtest" not in imported
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "evaluate_promotion_economic_gate_v1",
                "compose_double_play_decision",
                "KillSwitch",
            }
