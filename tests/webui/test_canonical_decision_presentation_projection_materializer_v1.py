"""Focused tests: CAPABILITY_PRESENTATION_CANONICAL_DECISION_PROJECTION_MATERIALIZER_V1."""

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
    DECISION_EVIDENCE_SCHEMA_VERSION,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_materializer_v1 import (
    CAPABILITY_ID,
    MATERIALIZE_ERROR_MISSING_SOURCE,
    SOURCE_EVIDENCE_RELATIVE_PATH,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_WRITTEN,
    build_canonical_decision_presentation_projection_payload_v1,
    materialize_canonical_decision_presentation_projection_v1,
    serialize_canonical_decision_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_v1 import (
    LOAD_ERROR_EVIDENCE_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_TIMESTAMP_MISSING,
    STORAGE_RELATIVE_PATH,
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
        "decision_id": "decision-materializer-1",
        "evidence_schema_version": DECISION_EVIDENCE_SCHEMA_VERSION,
        "reason_codes": ("WARMUP_ACTIVE", "NO_ENTRY"),
        "semantic_digest": "b" * 64,
    }
    base.update(overrides)
    return base


def _write_source_evidence(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / SOURCE_EVIDENCE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == (
        "CAPABILITY_PRESENTATION_CANONICAL_DECISION_PROJECTION_MATERIALIZER_V1"
    )


def test_build_payload_is_deterministic() -> None:
    evidence = _evidence()
    first, err_a = build_canonical_decision_presentation_projection_payload_v1(
        evidence=evidence,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    second, err_b = build_canonical_decision_presentation_projection_payload_v1(
        evidence=evidence,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    assert err_a == ()
    assert err_b == ()
    assert first is not None and second is not None
    assert first == second
    assert serialize_canonical_decision_presentation_projection_v1(
        first
    ) == serialize_canonical_decision_presentation_projection_v1(second)


def test_materialize_writes_loader_expected_path(tmp_path: Path) -> None:
    result = materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence=_evidence(),
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
    materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence=_evidence(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://materializer-compat",
    )
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.decision_id == "decision-materializer-1"
    assert loaded.evidence_digest == "b" * 64
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["decision_outcome"] == "observe"
    assert loaded.binder_fields["next_direction_state"] == "neutral_observe"


def test_missing_source_does_not_invent_artifact(tmp_path: Path) -> None:
    result = materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence=None,
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_MISSING_SOURCE
    assert MATERIALIZE_ERROR_MISSING_SOURCE in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False


def test_invalid_source_fail_closed(tmp_path: Path) -> None:
    result = materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence={"instrument_id": "ETH-USDT-SWAP"},
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_EVIDENCE_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_invalid_schema_version_fail_closed(tmp_path: Path) -> None:
    result = materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence=_evidence(evidence_schema_version="wrong_schema"),
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_SCHEMA_MISMATCH in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    result = materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence=_evidence(),
        generated_at=None,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_TIMESTAMP_MISSING in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_does_not_mutate_canonical_inputs(tmp_path: Path) -> None:
    evidence = _evidence()
    snapshot = deepcopy(evidence)
    result = materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence=evidence,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert evidence == snapshot


def test_materialize_from_durable_producer_evidence_source(tmp_path: Path) -> None:
    _write_source_evidence(tmp_path, _evidence())
    result = materialize_canonical_decision_presentation_projection_v1(
        tmp_path,
        evidence=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.source_path is not None
    assert SOURCE_EVIDENCE_RELATIVE_PATH in result.source_path
    loaded = try_load_canonical_decision_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.decision_id == "decision-materializer-1"


def test_end_to_end_producer_evidence_to_autobind_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    _write_source_evidence(archive, _evidence(decision_outcome="observe"))
    result = materialize_canonical_decision_presentation_projection_v1(
        archive,
        evidence=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://e2e-materializer",
    )
    assert result.written is True
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    decision = slots["canonical_decision"]
    assert decision.availability is Availability.AVAILABLE
    assert decision.decision == "observe"
    assert decision.direction == "neutral_observe"
    assert decision.decision_id == "decision-materializer-1"

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "observe" in html
    assert 'data-mdl-region="CANONICAL_DECISION_STRIP"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_materializer_module_has_no_forbidden_trading_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "canonical_decision_presentation_projection_materializer_v1.py"
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
    source = path.read_text(encoding="utf-8")
    assert CAPABILITY_ID in source
    assert "STORAGE_RELATIVE_PATH" in source
    assert "map_canonical_decision_evidence_to_binder_fields_v1" in source
