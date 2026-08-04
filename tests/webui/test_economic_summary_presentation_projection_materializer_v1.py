"""Focused tests: CAPABILITY_PRESENTATION_ECONOMIC_SUMMARY_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

from __future__ import annotations

import ast
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    ECONOMIC_PRODUCER_MODULE,
    ECONOMIC_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_materializer_v1 import (
    CAPABILITY_ID,
    MATERIALIZE_ERROR_MISSING_SOURCE,
    SOURCE_FIELDS_RELATIVE_PATH,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_WRITTEN,
    build_economic_summary_presentation_projection_payload_v1,
    materialize_economic_summary_presentation_projection_v1,
    serialize_economic_summary_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_v1 import (
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_TIMESTAMP_MISSING,
    STORAGE_RELATIVE_PATH,
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
        "reason_codes": ("SENTINEL_REASON_A", "SENTINEL_REASON_B"),
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


def _write_source_fields(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / SOURCE_FIELDS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == (
        "CAPABILITY_PRESENTATION_ECONOMIC_SUMMARY_PROJECTION_MATERIALIZER_AUTOBIND_V1"
    )


def test_build_payload_is_deterministic() -> None:
    fields = _fields()
    first, err_a = build_economic_summary_presentation_projection_payload_v1(
        economic_summary=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    second, err_b = build_economic_summary_presentation_projection_payload_v1(
        economic_summary=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    assert err_a == ()
    assert err_b == ()
    assert first is not None and second is not None
    assert first == second
    assert serialize_economic_summary_presentation_projection_v1(
        first
    ) == serialize_economic_summary_presentation_projection_v1(second)
    assert first["schema_name"] == "economic_summary_presentation_projection.v1"
    assert first["schema_version"] == 1
    assert first["economic_summary"]["status"] == "ECONOMICALLY_VIABLE_OFFLINE"
    assert first["economic_summary"]["profit_factor"]["value"] == 1.77


def test_materialize_writes_loader_expected_path(tmp_path: Path) -> None:
    result = materialize_economic_summary_presentation_projection_v1(
        tmp_path,
        economic_summary=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.errors == ()
    assert result.projection_path is not None
    assert result.projection_path.endswith(STORAGE_RELATIVE_PATH)
    assert (tmp_path / STORAGE_RELATIVE_PATH).is_file()


def test_materialize_loader_compatible(tmp_path: Path) -> None:
    materialize_economic_summary_presentation_projection_v1(
        tmp_path,
        economic_summary=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://materializer-compat",
    )
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert loaded.evidence_digest == "m" * 64
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["policy_threshold_status"] == "PASS"
    assert loaded.binder_fields["profit_factor"]["value"] == 1.77


def test_missing_source_does_not_invent_artifact(tmp_path: Path) -> None:
    result = materialize_economic_summary_presentation_projection_v1(
        tmp_path,
        economic_summary=None,
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_MISSING_SOURCE
    assert MATERIALIZE_ERROR_MISSING_SOURCE in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False


def test_invalid_source_fail_closed(tmp_path: Path) -> None:
    result = materialize_economic_summary_presentation_projection_v1(
        tmp_path,
        economic_summary={"status": "ECONOMICALLY_VIABLE_OFFLINE"},
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_FIELDS_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    result = materialize_economic_summary_presentation_projection_v1(
        tmp_path,
        economic_summary=_fields(),
        generated_at=None,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_TIMESTAMP_MISSING in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_does_not_mutate_canonical_inputs(tmp_path: Path) -> None:
    fields = _fields()
    snapshot = deepcopy(fields)
    result = materialize_economic_summary_presentation_projection_v1(
        tmp_path,
        economic_summary=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert fields == snapshot


def test_materialize_from_durable_fields_source(tmp_path: Path) -> None:
    _write_source_fields(tmp_path, _fields())
    result = materialize_economic_summary_presentation_projection_v1(
        tmp_path,
        economic_summary=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.source_path is not None
    assert SOURCE_FIELDS_RELATIVE_PATH in result.source_path
    assert (tmp_path / SOURCE_FIELDS_RELATIVE_PATH).is_file()
    loaded = try_load_economic_summary_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.status == "ECONOMICALLY_VIABLE_OFFLINE"


def test_end_to_end_durable_source_to_autobind_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    _write_source_fields(archive, _fields())
    result = materialize_economic_summary_presentation_projection_v1(
        archive,
        economic_summary=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://e2e-economic-materializer",
    )
    assert result.written is True
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    economic = slots["economic_summary"]
    assert economic.availability is Availability.AVAILABLE
    assert economic.economic_viability_status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert economic.policy_threshold_status == "PASS"
    assert economic.profit_factor == {"semantic": "COMPUTED", "value": 1.77}
    assert economic.provenance.producer_module == ECONOMIC_PRODUCER_MODULE
    assert economic.provenance.source_kind == ECONOMIC_SOURCE_KIND

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "ECONOMICALLY_VIABLE_OFFLINE" in html
    assert 'data-mdl-ops="economic_summary"' in html
    assert 'data-mdl-field="economic"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_materializer_module_has_no_forbidden_trading_or_backtest_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "economic_summary_presentation_projection_materializer_v1.py"
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
