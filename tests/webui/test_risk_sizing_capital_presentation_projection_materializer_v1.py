"""Focused tests: CAPABILITY_PRESENTATION_RISK_SIZING_CAPITAL_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

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
    RISK_SIZING_PRODUCER_MODULE,
    RISK_SIZING_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_materializer_v1 import (
    CAPABILITY_ID,
    MATERIALIZE_ERROR_MISSING_SOURCE,
    SOURCE_FIELDS_RELATIVE_PATH,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_WRITTEN,
    build_risk_sizing_capital_presentation_projection_payload_v1,
    materialize_risk_sizing_capital_presentation_projection_v1,
    serialize_risk_sizing_capital_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_v1 import (
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_TIMESTAMP_MISSING,
    STORAGE_RELATIVE_PATH,
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
        "evidence_digest": "r" * 64,
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
        "CAPABILITY_PRESENTATION_RISK_SIZING_CAPITAL_PROJECTION_MATERIALIZER_AUTOBIND_V1"
    )


def test_build_payload_is_deterministic() -> None:
    fields = _fields()
    first, err_a = build_risk_sizing_capital_presentation_projection_payload_v1(
        risk_sizing_capital=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    second, err_b = build_risk_sizing_capital_presentation_projection_payload_v1(
        risk_sizing_capital=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    assert err_a == ()
    assert err_b == ()
    assert first is not None and second is not None
    assert first == second
    assert serialize_risk_sizing_capital_presentation_projection_v1(
        first
    ) == serialize_risk_sizing_capital_presentation_projection_v1(second)
    assert first["schema_name"] == "risk_sizing_capital_presentation_projection.v1"
    assert first["schema_version"] == 1
    assert first["risk_sizing_capital"]["risk_status"] == "PASS"
    assert first["risk_sizing_capital"]["quantity"] == 0.25


def test_materialize_writes_loader_expected_path(tmp_path: Path) -> None:
    result = materialize_risk_sizing_capital_presentation_projection_v1(
        tmp_path,
        risk_sizing_capital=_fields(),
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
    materialize_risk_sizing_capital_presentation_projection_v1(
        tmp_path,
        risk_sizing_capital=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://materializer-compat",
    )
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.risk_status == "PASS"
    assert loaded.evidence_digest == "r" * 64
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["sizing_status"] == "PASS"
    assert loaded.binder_fields["capital_status"] == "PASS"
    assert loaded.binder_fields["quantity"] == 0.25


def test_missing_source_does_not_invent_artifact(tmp_path: Path) -> None:
    result = materialize_risk_sizing_capital_presentation_projection_v1(
        tmp_path,
        risk_sizing_capital=None,
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_MISSING_SOURCE
    assert MATERIALIZE_ERROR_MISSING_SOURCE in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False


def test_invalid_source_fail_closed(tmp_path: Path) -> None:
    result = materialize_risk_sizing_capital_presentation_projection_v1(
        tmp_path,
        risk_sizing_capital={"risk_status": "PASS"},
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_FIELDS_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    result = materialize_risk_sizing_capital_presentation_projection_v1(
        tmp_path,
        risk_sizing_capital=_fields(),
        generated_at=None,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_TIMESTAMP_MISSING in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_does_not_mutate_canonical_inputs(tmp_path: Path) -> None:
    fields = _fields()
    snapshot = deepcopy(fields)
    result = materialize_risk_sizing_capital_presentation_projection_v1(
        tmp_path,
        risk_sizing_capital=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert fields == snapshot


def test_materialize_from_durable_fields_source(tmp_path: Path) -> None:
    _write_source_fields(tmp_path, _fields())
    result = materialize_risk_sizing_capital_presentation_projection_v1(
        tmp_path,
        risk_sizing_capital=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.source_path is not None
    assert SOURCE_FIELDS_RELATIVE_PATH in result.source_path
    assert (tmp_path / SOURCE_FIELDS_RELATIVE_PATH).is_file()
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.risk_status == "PASS"


def test_end_to_end_durable_source_to_autobind_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    _write_source_fields(archive, _fields())
    result = materialize_risk_sizing_capital_presentation_projection_v1(
        archive,
        risk_sizing_capital=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://e2e-risk-materializer",
    )
    assert result.written is True
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

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "PASS" in html
    assert 'data-mdl-ops="risk_sizing_capital"' in html
    assert 'data-mdl-field="risk_status"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_materializer_module_has_no_forbidden_trading_or_governance_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "risk_sizing_capital_presentation_projection_materializer_v1.py"
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
                "bind_capital_risk_sizing_offline_replay_evidence_v0",
                "compose_double_play_decision",
                "KillSwitch",
            }
