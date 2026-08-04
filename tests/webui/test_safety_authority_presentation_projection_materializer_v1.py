"""Focused tests: CAPABILITY_PRESENTATION_SAFETY_AUTHORITY_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

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
    SAFETY_EVIDENCE_PRODUCER_MODULE,
    SAFETY_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import (
    ENV_ARCHIVE_ROOT,
    SAFETY_AUTHORITY_PRESENTATION_PROJECTION_RELATIVE,
)
from src.webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_materializer_v1 import (
    CAPABILITY_ID,
    MATERIALIZE_ERROR_MISSING_SOURCE,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_WRITTEN,
    build_safety_authority_presentation_projection_payload_v1,
    materialize_safety_authority_presentation_projection_v1,
    serialize_safety_authority_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_v1 import (
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_TIMESTAMP_MISSING,
    SCHEMA_NAME,
    STORAGE_RELATIVE_PATH,
    project_safety_authority_presentation_projection_v1,
    try_load_safety_authority_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _fields(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "kill_switch_state": "KILLED",
        "veto_active": True,
        "reason_codes": ("killswitch_block_new", "reconciliation_required"),
        "evidence_digest": "e" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == (
        "CAPABILITY_PRESENTATION_SAFETY_AUTHORITY_PROJECTION_MATERIALIZER_AUTOBIND_V1"
    )


def test_archive_root_registers_exact_presentation_path() -> None:
    assert SAFETY_AUTHORITY_PRESENTATION_PROJECTION_RELATIVE == STORAGE_RELATIVE_PATH
    assert STORAGE_RELATIVE_PATH == "readmodels/safety_authority.v1.json"


def test_project_payload_is_field_faithful_and_deterministic() -> None:
    fields = _fields()
    first, err_a = project_safety_authority_presentation_projection_v1(
        safety_authority=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        saved_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    second, err_b = build_safety_authority_presentation_projection_payload_v1(
        safety_authority=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        saved_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    assert err_a == ()
    assert err_b == ()
    assert first is not None and second is not None
    assert first == second
    assert serialize_safety_authority_presentation_projection_v1(
        first
    ) == serialize_safety_authority_presentation_projection_v1(second)
    assert first["schema_name"] == SCHEMA_NAME
    assert first["schema_version"] == 1
    assert first["authority_effect"] == "NONE"
    assert first["safety_authority_effect"] == "NONE"
    assert first["safety_authority"]["kill_switch_state"] == "KILLED"
    assert first["safety_authority"]["veto_active"] is True
    assert first["safety_authority"]["reason_codes"] == [
        "killswitch_block_new",
        "reconciliation_required",
    ]
    assert first["generated_at"] == PRODUCER_FRESH
    assert first["effective_at"] == PRODUCER_FRESH
    assert first["saved_at"] == PRODUCER_FRESH


def test_reason_codes_normalize_deterministically_without_invention() -> None:
    payload, errors = project_safety_authority_presentation_projection_v1(
        safety_authority=_fields(reason_codes=["A", 2, "B"]),
        generated_at=PRODUCER_FRESH,
    )
    assert errors == ()
    assert payload is not None
    assert payload["safety_authority"]["reason_codes"] == ["A", "2", "B"]


def test_materialize_writes_exact_archive_path(tmp_path: Path) -> None:
    result = materialize_safety_authority_presentation_projection_v1(
        tmp_path,
        safety_authority=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        saved_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.errors == ()
    assert result.projection_path is not None
    assert result.projection_path.endswith(STORAGE_RELATIVE_PATH)
    written = tmp_path / STORAGE_RELATIVE_PATH
    assert written.is_file()
    assert written == tmp_path / "readmodels" / "safety_authority.v1.json"


def test_materialize_atomic_conventions(tmp_path: Path) -> None:
    result = materialize_safety_authority_presentation_projection_v1(
        tmp_path,
        safety_authority=_fields(),
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is True
    readmodels = tmp_path / "readmodels"
    leftovers = [p for p in readmodels.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []
    assert (readmodels / "safety_authority.v1.json").is_file()


def test_materialize_roundtrip(tmp_path: Path) -> None:
    materialize_safety_authority_presentation_projection_v1(
        tmp_path,
        safety_authority=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        saved_at=PRODUCER_FRESH,
        source_reference="presentation://materializer-compat",
    )
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.kill_switch_state == "KILLED"
    assert loaded.veto_active is True
    assert loaded.evidence_digest == "e" * 64
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["reason_codes"] == (
        "killswitch_block_new",
        "reconciliation_required",
    )
    assert loaded.binder_fields["generated_at"] == PRODUCER_FRESH
    assert loaded.binder_fields["effective_at"] == PRODUCER_FRESH
    assert loaded.binder_fields["saved_at"] == PRODUCER_FRESH


def test_missing_source_does_not_invent_artifact(tmp_path: Path) -> None:
    result = materialize_safety_authority_presentation_projection_v1(
        tmp_path,
        safety_authority=None,
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_MISSING_SOURCE
    assert MATERIALIZE_ERROR_MISSING_SOURCE in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False


def test_invalid_source_fail_closed(tmp_path: Path) -> None:
    result = materialize_safety_authority_presentation_projection_v1(
        tmp_path,
        safety_authority={"veto_active": True},
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_FIELDS_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    result = materialize_safety_authority_presentation_projection_v1(
        tmp_path,
        safety_authority=_fields(),
        generated_at=None,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_TIMESTAMP_MISSING in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_does_not_mutate_caller_inputs(tmp_path: Path) -> None:
    fields = _fields()
    snapshot = deepcopy(fields)
    result = materialize_safety_authority_presentation_projection_v1(
        tmp_path,
        safety_authority=fields,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert fields == snapshot


def test_end_to_end_materialize_to_autobind_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    result = materialize_safety_authority_presentation_projection_v1(
        archive,
        safety_authority=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://e2e-safety-materializer",
    )
    assert result.written is True
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    safety = slots["safety_authority"]
    assert safety.availability is Availability.AVAILABLE
    assert safety.kill_switch_state == "KILLED"
    assert safety.veto_active is True
    assert safety.provenance.producer_module == SAFETY_EVIDENCE_PRODUCER_MODULE
    assert safety.provenance.source_kind == SAFETY_SOURCE_KIND

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "KILLED" in html
    assert 'data-mdl-field="safety"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_materializer_and_projection_have_no_forbidden_imports() -> None:
    for relative in (
        "src/webui/workflow_dashboard_readmodel_v1/safety_authority_presentation_projection_v1.py",
        "src/webui/workflow_dashboard_readmodel_v1/"
        "safety_authority_presentation_projection_materializer_v1.py",
    ):
        path = REPO / relative
        text = path.read_text(encoding="utf-8")
        assert "live data/kill_switch" not in text
        assert "KillSwitch(" not in text
        tree = ast.parse(text)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                if node.module:
                    imported.add(node.module)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "KillSwitch",
                    "evaluate_offline_killswitch_boundary_v0",
                    "bind_killswitch_boundary_offline_replay_evidence_v0",
                }
        for module in imported:
            root = module.split(".", 1)[0]
            assert root not in {"trading", "src", "risk_layer"}
            assert not module.startswith("src.risk_layer")
            assert "killswitch_boundary" not in module
