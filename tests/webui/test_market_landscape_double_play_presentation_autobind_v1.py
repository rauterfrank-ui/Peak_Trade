"""Focused tests: CAPABILITY_PRESENTATION_DOUBLE_PLAY_AUTOBIND_V1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    DOUBLE_PLAY_PRODUCER_MODULE,
    DOUBLE_PLAY_SOURCE_KIND,
    REASON_DOUBLE_PLAY_NOT_PERSISTED,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    DOUBLE_PLAY_AUTHORITY_EFFECT,
    LOAD_ERROR_ABSENT,
    LOAD_ERROR_AMBIGUOUS,
    LOAD_ERROR_AUTHORITY_CLAIM,
    LOAD_ERROR_DISPLAY_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    SCHEMA_NAME,
    STORAGE_RELATIVE_PATH,
    map_double_play_display_to_binder_fields_v1,
    try_load_double_play_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _display(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "overall_status": "display_ready",
        "panel_summaries": (
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "Composition: ELIGIBLE_MODEL_ONLY — data-only; not trading-ready.",
                "blockers": (),
            },
            {
                "name": "state_transition",
                "status": "display_ready",
                "summary": "Transition allowed (model label): NOOP",
                "blockers": (),
            },
        ),
        "blockers": (),
        "display_only": True,
        "live_authorization": False,
        "evidence_digest": "d" * 64,
    }
    base.update(overrides)
    return base


def _projection_payload(
    *,
    display: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": 1,
        "authority_effect": AUTHORITY_EFFECT,
        "double_play_authority_effect": DOUBLE_PLAY_AUTHORITY_EFFECT,
        "projection_role": "NON_AUTHORITATIVE_PRESENTATION_PROJECTION",
        "generated_at": PRODUCER_FRESH,
        "effective_at": PRODUCER_FRESH,
        "source_reference": "presentation://double_play_autobind_test",
        "display": display if display is not None else _display(),
    }
    payload.update(overrides)
    return payload


def _write_projection(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / STORAGE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_map_display_to_binder_fields_preserves_producer_facts() -> None:
    fields, errors = map_double_play_display_to_binder_fields_v1(
        display=_display(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://x",
    )
    assert errors == ()
    assert fields is not None
    assert fields["overall_status"] == "display_ready"
    assert fields["panel_summaries"][0]["name"] == "composition"
    assert fields["display_only"] is True
    assert fields["live_authorization"] is False
    assert fields["evidence_digest"] == "d" * 64
    assert fields["generated_at"] == PRODUCER_FRESH


def test_load_absent_projection_is_missing(tmp_path: Path) -> None:
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_ABSENT in loaded.load_errors
    assert loaded.binder_fields is None


def test_load_valid_projection_returns_binder_fields(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.binder_fields is not None
    assert loaded.overall_status == "display_ready"
    assert loaded.evidence_digest == "d" * 64
    assert STORAGE_RELATIVE_PATH in str(loaded.source_path)


def test_load_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(schema_name="wrong.schema"))
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_SCHEMA_MISMATCH in loaded.load_errors


def test_load_authority_claim_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(authority_effect="DECISION"))
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_AUTHORITY_CLAIM in loaded.load_errors


def test_load_invalid_display_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload(display={"overall_status": "x"}))
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False
    assert LOAD_ERROR_DISPLAY_INVALID in loaded.load_errors


def test_load_ambiguous_sibling_fail_closed(tmp_path: Path) -> None:
    _write_projection(tmp_path, _projection_payload())
    sibling = tmp_path / "readmodels" / "double_play_dashboard_display.v1.json"
    sibling.write_text(
        json.dumps({"evidence_digest": "e" * 64, "overall_status": "display_ready"}) + "\n",
        encoding="utf-8",
    )
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
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
    dp = slots["double_play"]
    assert dp.availability is Availability.AVAILABLE
    assert dp.overall_status == "display_ready"
    assert dp.panel_summaries[0]["name"] == "composition"
    assert dp.display_only is True
    assert dp.live_authorization is False
    assert dp.provenance.producer_module == DOUBLE_PLAY_PRODUCER_MODULE
    assert dp.provenance.source_kind == DOUBLE_PLAY_SOURCE_KIND
    assert dp.provenance.source_reference == "presentation://double_play_autobind_test"
    assert dp.provenance.evidence_digest == "d" * 64
    # Other injection-only slots remain unbound / missing.
    assert slots["dynamic_scope"].availability is Availability.MISSING_SOURCE
    assert slots["canonical_decision"].availability is Availability.MISSING_SOURCE
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
    assert slots["double_play"].availability is Availability.MISSING_SOURCE
    assert REASON_DOUBLE_PLAY_NOT_PERSISTED in slots["double_play"].blockers


def test_autobind_invalid_projection_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "bad_archive"
    _write_projection(archive, _projection_payload(schema_name="nope"))
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=STAMP)
    assert slots["double_play"].availability is Availability.INVALID
    assert LOAD_ERROR_SCHEMA_MISMATCH in slots["double_play"].blockers


def test_explicit_injection_still_overrides_durable_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    _write_projection(archive, _projection_payload())
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(
        generated_at=STAMP,
        double_play_fields={
            "overall_status": "display_warning",
            "panel_summaries": (
                {
                    "name": "composition",
                    "status": "display_warning",
                    "summary": "Injected warning panel",
                    "blockers": ("INJECTED",),
                },
            ),
            "blockers": ("INJECTED",),
            "display_only": True,
            "live_authorization": False,
            "evidence_digest": "b" * 64,
            "generated_at": PRODUCER_FRESH,
            "source_reference": "double-play://bounded-test-injection",
        },
    )
    dp = slots["double_play"]
    assert dp.availability is Availability.AVAILABLE
    assert dp.overall_status == "display_warning"
    assert dp.blockers == ("INJECTED",)
    assert dp.provenance.source_reference == "double-play://bounded-test-injection"


def test_get_market_autobinds_double_play_without_injection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    # Wall-clock GET /market uses datetime.now(UTC); keep producer fresh.
    fresh = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_projection(
        archive,
        _projection_payload(
            generated_at=fresh,
            effective_at=fresh,
            display=_display(
                overall_status="display_ready",
                blockers=("AUTOBIND_DP_OK",),
            ),
        ),
    )
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "display_ready" in html
    assert 'data-mdl-field="double_play"' in html
    assert 'data-mdl-field="double_play" data-availability="AVAILABLE"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_projection_module_has_no_forbidden_trading_imports() -> None:
    import ast

    path = (
        REPO / "src/webui/workflow_dashboard_readmodel_v1/double_play_presentation_projection_v1.py"
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
                "build_dashboard_display_snapshot",
                "KillSwitch",
            }
