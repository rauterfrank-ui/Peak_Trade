"""Focused tests: CAPABILITY_PRESENTATION_DYNAMIC_SCOPE_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

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
    SCOPE_PRODUCER_MODULE,
    SCOPE_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_materializer_v1 import (
    CAPABILITY_ID,
    MATERIALIZE_ERROR_MISSING_SOURCE,
    PRODUCER_STATE_SCHEMA_VERSION,
    SOURCE_STATE_RELATIVE_PATH,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_WRITTEN,
    build_dynamic_scope_presentation_projection_payload_v1,
    materialize_dynamic_scope_presentation_projection_v1,
    serialize_dynamic_scope_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_v1 import (
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_SCOPE_INVALID,
    LOAD_ERROR_TIMESTAMP_MISSING,
    STORAGE_RELATIVE_PATH,
    try_load_dynamic_scope_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _binder_scope(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "scope_state": "scope_valid",
        "current_scope_ref": "scope-eth-1",
        "next_scope_ref": None,
        "reason_codes": ("SCOPE_INITIALIZED",),
        "semantic_digest": "c" * 64,
    }
    base.update(overrides)
    return base


def _durable_state(**overrides: object) -> dict[str, object]:
    existing: dict[str, object] = {
        "scope_id": "scope-eth-1",
        "instrument_id": "ETH-USDT-SWAP",
        "initialized_at_trading_epoch": 1,
        "source_market_context_id": "ctx-1",
        "source_input_digest": "d" * 64,
        "lifecycle_state": "scope_valid",
        "reference_price": 100.0,
        "volatility_estimate": 0.01,
        "initial_volatility_distance": 1.0,
        "scope_band": 2.0,
        "neutral_upper_boundary": 102.0,
        "neutral_lower_boundary": 98.0,
        "trailing_anchor": 100.0,
        "min_scope_band": 0.5,
        "max_scope_band": 5.0,
        "policy_version": "canonical_scope_initialization_policy_v1",
        "semantic_digest": "c" * 64,
        "reason_codes": ["SCOPE_INITIALIZED"],
    }
    base: dict[str, object] = {
        "schema_version": PRODUCER_STATE_SCHEMA_VERSION,
        "capability_id": "CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1",
        "state_version": "v1",
        "scope_session_id": "session-1",
        "instrument_id": "ETH-USDT-SWAP",
        "venue": "OKX",
        "existing_scope": existing,
        "runtime_scope_state": None,
        "runtime_scope_bound_instrument_id": "ETH-USDT-SWAP",
        "confirmation_session_id": "",
        "market_observation_epoch": 1,
        "last_market_event_time": 1700000006.0,
        "last_accepted_observation_identity_digest": "e" * 64,
        "position_context": {},
        "scope_direction_state": "LONG",
        "side_state": "neutral_observe",
        "host_trading_epoch": 1,
        "price_path_tail": [],
        "repository_sha": "a" * 40,
        "config_digest": "f" * 64,
    }
    base.update(overrides)
    return base


def _write_source_state(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / SOURCE_STATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == (
        "CAPABILITY_PRESENTATION_DYNAMIC_SCOPE_PROJECTION_MATERIALIZER_AUTOBIND_V1"
    )


def test_build_payload_is_deterministic() -> None:
    scope = _binder_scope()
    first, err_a = build_dynamic_scope_presentation_projection_payload_v1(
        dynamic_scope=scope,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    second, err_b = build_dynamic_scope_presentation_projection_payload_v1(
        dynamic_scope=scope,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    assert err_a == ()
    assert err_b == ()
    assert first is not None and second is not None
    assert first == second
    assert serialize_dynamic_scope_presentation_projection_v1(
        first
    ) == serialize_dynamic_scope_presentation_projection_v1(second)
    assert first["schema_name"] == "dynamic_scope_presentation_projection.v1"
    assert first["schema_version"] == 1
    assert first["dynamic_scope"]["scope_state"] == "scope_valid"
    assert first["dynamic_scope"]["current_scope_ref"] == "scope-eth-1"
    assert first["dynamic_scope"]["next_scope_ref"] is None


def test_invalid_schema_rejected_by_contract(tmp_path: Path) -> None:
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope=_binder_scope(scope_state="not_a_known_lifecycle"),
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_SCHEMA_MISMATCH in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_materialize_writes_loader_expected_path(tmp_path: Path) -> None:
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope=_binder_scope(next_scope_ref="scope-eth-2"),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.errors == ()
    assert result.projection_path is not None
    assert result.projection_path.endswith(STORAGE_RELATIVE_PATH)
    assert (tmp_path / STORAGE_RELATIVE_PATH).is_file()


def test_materialize_from_durable_state_projection_exact(tmp_path: Path) -> None:
    source = _durable_state()
    source_snapshot = deepcopy(source)
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope=source,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://durable-scope",
    )
    assert result.written is True
    assert source == source_snapshot  # source unchanged
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["scope_state"] == "scope_valid"
    assert loaded.binder_fields["current_scope_ref"] == "scope-eth-1"
    assert "next_scope_ref" not in loaded.binder_fields  # not invented
    assert loaded.binder_fields["semantic_digest"] == "c" * 64
    # No invented productive fields beyond landscape contract.
    assert set(loaded.binder_fields.keys()) <= {
        "scope_state",
        "current_scope_ref",
        "next_scope_ref",
        "reason_codes",
        "semantic_digest",
        "evidence_digest",
        "generated_at",
        "effective_at",
        "source_reference",
    }


def test_missing_source_does_not_invent_artifact(tmp_path: Path) -> None:
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope=None,
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_MISSING_SOURCE
    assert MATERIALIZE_ERROR_MISSING_SOURCE in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False


def test_invalid_source_fail_closed(tmp_path: Path) -> None:
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope={"scope_state": "scope_valid"},
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_SCOPE_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_invalid_durable_schema_fail_closed(tmp_path: Path) -> None:
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope=_durable_state(schema_version="wrong.schema"),
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_SCHEMA_MISMATCH in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope=_binder_scope(),
        generated_at=None,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_TIMESTAMP_MISSING in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_materialize_from_durable_producer_state_source(tmp_path: Path) -> None:
    _write_source_state(tmp_path, _durable_state())
    result = materialize_dynamic_scope_presentation_projection_v1(
        tmp_path,
        dynamic_scope=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.source_path is not None
    assert SOURCE_STATE_RELATIVE_PATH in result.source_path
    # Source file remains present and unchanged relative path.
    assert (tmp_path / SOURCE_STATE_RELATIVE_PATH).is_file()
    loaded = try_load_dynamic_scope_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.current_scope_ref == "scope-eth-1"


def test_end_to_end_durable_state_to_autobind_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    _write_source_state(archive, _durable_state())
    result = materialize_dynamic_scope_presentation_projection_v1(
        archive,
        dynamic_scope=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://e2e-scope-materializer",
    )
    assert result.written is True
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    scope = slots["dynamic_scope"]
    assert scope.availability is Availability.AVAILABLE
    assert scope.scope_state == "scope_valid"
    assert scope.current_scope_ref == "scope-eth-1"
    assert scope.next_scope_ref is None
    assert scope.provenance.producer_module == SCOPE_PRODUCER_MODULE
    assert scope.provenance.source_kind == SCOPE_SOURCE_KIND

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "scope_valid" in html
    assert "scope-eth-1" in html
    assert 'data-mdl-field="scope_lifecycle"' in html
    assert 'data-mdl-region="SYSTEM_CONTEXT_RAIL"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_materializer_module_has_no_forbidden_trading_or_ops_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "dynamic_scope_presentation_projection_materializer_v1.py"
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
                "initialize_canonical_scope",
                "compose_double_play_decision",
                "KillSwitch",
            }
