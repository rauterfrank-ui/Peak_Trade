"""Focused tests: CAPABILITY_PRESENTATION_DOUBLE_PLAY_PROJECTION_MATERIALIZER_V1."""

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
    DOUBLE_PLAY_PRODUCER_MODULE,
    DOUBLE_PLAY_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1 import (
    CAPABILITY_ID,
    LEGACY_ROUTE_NON_SOURCE,
    MATERIALIZE_ERROR_MISSING_SOURCE,
    SOURCE_DISPLAY_RELATIVE_PATH,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_WRITTEN,
    build_double_play_presentation_projection_payload_v1,
    materialize_double_play_presentation_projection_v1,
    serialize_double_play_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1 import (
    LOAD_ERROR_DISPLAY_INVALID,
    LOAD_ERROR_TIMESTAMP_MISSING,
    STORAGE_RELATIVE_PATH,
    try_load_double_play_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
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


def _write_source_display(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / SOURCE_DISPLAY_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == ("CAPABILITY_PRESENTATION_DOUBLE_PLAY_PROJECTION_MATERIALIZER_V1")
    assert LEGACY_ROUTE_NON_SOURCE == "double_play_dashboard_display_json_route_v0"


def test_build_payload_is_deterministic() -> None:
    display = _display()
    first, err_a = build_double_play_presentation_projection_payload_v1(
        display=display,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    second, err_b = build_double_play_presentation_projection_payload_v1(
        display=display,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    assert err_a == ()
    assert err_b == ()
    assert first is not None and second is not None
    assert first == second
    assert serialize_double_play_presentation_projection_v1(
        first
    ) == serialize_double_play_presentation_projection_v1(second)


def test_materialize_writes_loader_expected_path(tmp_path: Path) -> None:
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=_display(),
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
    materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=_display(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://materializer-compat",
    )
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.overall_status == "display_ready"
    assert loaded.evidence_digest == "d" * 64
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["panel_summaries"][0]["name"] == "composition"
    assert loaded.binder_fields["display_only"] is True
    assert loaded.binder_fields["live_authorization"] is False


def test_missing_source_does_not_invent_artifact(tmp_path: Path) -> None:
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=None,
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_MISSING_SOURCE
    assert MATERIALIZE_ERROR_MISSING_SOURCE in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False


def test_invalid_source_fail_closed(tmp_path: Path) -> None:
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display={"overall_status": "display_ready"},
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_DISPLAY_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_invalid_live_authorization_fail_closed(tmp_path: Path) -> None:
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=_display(live_authorization=True),
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_DISPLAY_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=_display(),
        generated_at=None,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_TIMESTAMP_MISSING in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_does_not_mutate_canonical_inputs(tmp_path: Path) -> None:
    display = _display()
    snapshot = deepcopy(display)
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=display,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert display == snapshot


def test_materialize_from_durable_producer_display_source(tmp_path: Path) -> None:
    _write_source_display(tmp_path, _display())
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.source_path is not None
    assert SOURCE_DISPLAY_RELATIVE_PATH in result.source_path
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.overall_status == "display_ready"


def test_materialize_from_snapshot_shaped_panels(tmp_path: Path) -> None:
    snapshot_shaped = {
        "overall_status": "display_ready",
        "panels": (
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "Composition panel",
                "blockers": (),
            },
        ),
        "display_only": True,
        "live_authorization": False,
        "evidence_digest": "a" * 64,
    }
    result = materialize_double_play_presentation_projection_v1(
        tmp_path,
        display=snapshot_shaped,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    loaded = try_load_double_play_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["panel_summaries"][0]["name"] == "composition"
    assert loaded.evidence_digest == "a" * 64


def test_end_to_end_snapshot_to_presentation_projection_to_autobind_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    # Wall-clock GET /market uses datetime.now(UTC); keep producer fresh.
    fresh = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_source_display(archive, _display(overall_status="display_ready"))
    result = materialize_double_play_presentation_projection_v1(
        archive,
        display=None,
        generated_at=fresh,
        effective_at=fresh,
        source_reference="presentation://e2e-materializer",
    )
    assert result.written is True
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=datetime.now(timezone.utc))
    dp = slots["double_play"]
    assert dp.availability is Availability.AVAILABLE
    assert dp.overall_status == "display_ready"
    assert dp.panel_summaries[0]["name"] == "composition"
    assert dp.display_only is True
    assert dp.live_authorization is False
    assert dp.provenance.producer_module == DOUBLE_PLAY_PRODUCER_MODULE
    assert dp.provenance.source_kind == DOUBLE_PLAY_SOURCE_KIND
    assert dp.provenance.source_reference == "presentation://e2e-materializer"
    assert dp.provenance.evidence_digest == "d" * 64

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "display_ready" in html
    assert 'data-mdl-field="double_play"' in html
    assert 'data-mdl-field="double_play" data-availability="AVAILABLE"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_materializer_module_has_no_forbidden_trading_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "double_play_presentation_projection_materializer_v1.py"
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
    source = path.read_text(encoding="utf-8")
    assert CAPABILITY_ID in source
    assert "STORAGE_RELATIVE_PATH" in source
    assert "map_double_play_display_to_binder_fields_v1" in source
    assert LEGACY_ROUTE_NON_SOURCE in source
    assert "NON_SOURCE" in source
