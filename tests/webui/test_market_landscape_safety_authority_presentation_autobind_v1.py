"""Focused autobind tests: CAPABILITY_PRESENTATION_SAFETY_AUTHORITY_PROJECTION_MATERIALIZER_AUTOBIND_V1."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    REASON_SAFETY_NOT_PERSISTED,
    SAFETY_AUTHORITY_OWNER_MODULE,
    SAFETY_EVIDENCE_PRODUCER_MODULE,
    SAFETY_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    LOAD_ERROR_ABSENT,
    LOAD_ERROR_AUTHORITY_CLAIM,
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_INVALID_JSON,
    LOAD_ERROR_SCHEMA_MISMATCH,
    SAFETY_AUTHORITY_EFFECT,
    SCHEMA_NAME,
    STORAGE_RELATIVE_PATH,
    map_safety_authority_fields_to_binder_fields_v1,
    try_load_safety_authority_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"
FORBIDDEN_LIVE_STATE = "live data/kill_switch/state.json"


def _fields(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "kill_switch_state": "KILLED",
        "veto_active": True,
        "reason_codes": ("killswitch_block_new", "reconciliation_required"),
        "evidence_digest": "a" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _projection_payload(
    *,
    safety_authority: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": 1,
        "authority_effect": AUTHORITY_EFFECT,
        "safety_authority_effect": SAFETY_AUTHORITY_EFFECT,
        "projection_role": "NON_AUTHORITATIVE_PRESENTATION_PROJECTION",
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "saved_at": PRODUCER_FRESH,
        "source_reference": "presentation://safety_autobind_test",
        "safety_authority": (safety_authority if safety_authority is not None else _fields()),
    }
    payload.update(overrides)
    return payload


def _write_projection(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_map_fields_to_binder_fields_preserves_producer_facts() -> None:
    fields, errors = map_safety_authority_fields_to_binder_fields_v1(
        safety_authority=_fields(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        saved_at=PRODUCER_FRESH,
        source_reference="presentation://x",
    )
    assert errors == ()
    assert fields is not None
    assert fields["kill_switch_state"] == "KILLED"
    assert fields["veto_active"] is True
    assert fields["reason_codes"] == ("killswitch_block_new", "reconciliation_required")
    assert fields["evidence_digest"] == "a" * 64
    assert fields["generated_at"] == PRODUCER_FRESH
    assert fields["saved_at"] == PRODUCER_FRESH


def test_load_absent_projection_is_missing(tmp_path: Path) -> None:
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_ABSENT in loaded.load_errors
    assert loaded.binder_fields is None


def test_load_valid_projection_returns_binder_fields(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.binder_fields is not None
    assert loaded.kill_switch_state == "KILLED"
    assert loaded.veto_active is True
    assert loaded.evidence_digest == "a" * 64
    assert STORAGE_RELATIVE_PATH in str(loaded.source_path)


def test_load_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_name="wrong.schema"))
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_wrong_schema_version_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_version=99))
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_authority_claim_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(authority_effect="SAFETY"))
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AUTHORITY_CLAIM in loaded.load_errors


def test_load_invalid_fields_fail_closed(tmp_path: Path) -> None:
    _write_projection(
        tmp_path,
        _projection_payload(safety_authority={"veto_active": True}),
    )
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_FIELDS_INVALID in loaded.load_errors


def test_load_invalid_json_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")
    loaded = try_load_safety_authority_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_INVALID_JSON in loaded.load_errors


def test_autobind_available_from_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    safety = slots["safety_authority"]
    assert safety.availability is Availability.AVAILABLE
    assert safety.kill_switch_state == "KILLED"
    assert safety.veto_active is True
    assert safety.reason_codes == ("killswitch_block_new", "reconciliation_required")
    assert safety.provenance.producer_module == SAFETY_EVIDENCE_PRODUCER_MODULE
    assert safety.provenance.source_kind == SAFETY_SOURCE_KIND
    assert safety.provenance.source_reference == "presentation://safety_autobind_test"
    assert safety.provenance.evidence_digest == "a" * 64
    assert slots["economic_summary"].availability is Availability.MISSING_SOURCE


def test_autobind_missing_projection_is_missing_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "empty_archive"
    archive.mkdir()
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert REASON_SAFETY_NOT_PERSISTED in slots["safety_authority"].reason_codes


def test_autobind_invalid_json_is_missing_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_json_archive"
    path = archive / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{broken", encoding="utf-8")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert LOAD_ERROR_INVALID_JSON in slots["safety_authority"].reason_codes


def test_autobind_wrong_version_is_missing_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_version_archive"
    _write_projection(archive, _projection_payload(schema_version=7))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["safety_authority"].reason_codes


def test_autobind_schema_error_is_missing_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_schema_archive"
    _write_projection(archive, _projection_payload(schema_name="nope"))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["safety_authority"].availability is Availability.MISSING_SOURCE
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["safety_authority"].reason_codes


def test_explicit_injection_still_overrides_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        safety_authority_fields={
            "kill_switch_state": "ARMED",
            "veto_active": False,
            "reason_codes": ("INJECTED",),
            "semantic_digest": "b" * 64,
            "generated_at": PRODUCER_FRESH,
            "saved_at": PRODUCER_FRESH,
            "source_reference": "safety://bounded-test-injection",
            "schema_version": "v1",
        },
    )
    safety = slots["safety_authority"]
    assert safety.availability is Availability.AVAILABLE
    assert safety.kill_switch_state == "ARMED"
    assert safety.veto_active is False
    assert safety.reason_codes == ("INJECTED",)
    assert safety.provenance.source_reference == "safety://bounded-test-injection"


def test_get_market_autobinds_safety_without_injection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(
        archive,
        _projection_payload(
            safety_authority=_fields(
                kill_switch_state="KILLED",
                veto_active=True,
                reason_codes=("AUTOBIND_OK",),
            )
        ),
    )
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "KILLED" in html
    assert "veto=True" in html
    assert 'data-mdl-field="safety"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()
    assert FORBIDDEN_LIVE_STATE not in html


def test_projection_and_binding_have_no_forbidden_killswitch_imports() -> None:
    projection_paths = [
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "safety_authority_presentation_projection_v1.py",
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "safety_authority_presentation_projection_materializer_v1.py",
    ]
    binding_path = REPO / "src/webui/market_dashboard_landscape_producer_binding_v2.py"
    for path in [*projection_paths, binding_path]:
        text = path.read_text(encoding="utf-8")
        assert FORBIDDEN_LIVE_STATE not in text
        assert "kill_switch/state.json" not in text
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.startswith("src.risk_layer")
                assert "killswitch_boundary" not in module
                assert module != "src.risk_layer.kill_switch"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("src.risk_layer")
                    assert "killswitch_boundary" not in alias.name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "KillSwitch",
                    "evaluate_offline_killswitch_boundary_v0",
                    "bind_killswitch_boundary_offline_replay_evidence_v0",
                    "derive_killswitch_boundary_mode_v0",
                }
    for path in projection_paths:
        text = path.read_text(encoding="utf-8")
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
        for module in imported:
            assert not module.startswith("src.risk_layer")
            assert "killswitch_boundary" not in module
            assert module.split(".", 1)[0] not in {"trading", "src", "risk_layer"}


def test_owner_registry_documents_durable_projection_and_injection_priority() -> None:
    registry = (REPO / "src/webui/market_dashboard_landscape_v2/owner_registry.py").read_text(
        encoding="utf-8"
    )
    safety_block = registry.split('slot="safety_authority"', 1)[1].split("CanonicalOwnerRefV1(", 1)[
        0
    ]
    assert "safety_authority_presentation_projection.v1" in safety_block
    assert "readmodels/safety_authority.v1.json" in safety_block
    assert "explicit injection remains priority" in safety_block
    assert "no productive KillSwitch state-file autoload" in safety_block
    assert "AUTHORITY_EFFECT=NONE" in safety_block
    assert SAFETY_AUTHORITY_OWNER_MODULE in safety_block
