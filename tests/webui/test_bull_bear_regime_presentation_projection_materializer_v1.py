"""Focused tests: CAPABILITY_PRESENTATION_BULL_BEAR_REGIME_PROJECTION_MATERIALIZER_V1."""

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
    REGIME_BULL_BEAR_SWITCH_PRODUCER_MODULE,
    REGIME_BULL_BEAR_SWITCH_SOURCE_KIND,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_materializer_v1 import (
    CAPABILITY_ID,
    LEGACY_ROUTE_NON_SOURCE,
    MATERIALIZE_ERROR_MISSING_SOURCE,
    SOURCE_REGIME_RELATIVE_PATH,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_NOT_BOUND,
    STATUS_WRITTEN,
    build_bull_bear_regime_presentation_projection_payload_v1,
    materialize_bull_bear_regime_presentation_projection_v1,
    serialize_bull_bear_regime_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_v1 import (
    LOAD_ERROR_REGIME_INVALID,
    LOAD_ERROR_TIMESTAMP_MISSING,
    STORAGE_RELATIVE_PATH,
    try_load_bull_bear_regime_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
PRODUCER_FRESH = "2026-07-24T17:30:00Z"


def _regime(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "regime_id": "trending",
        "regime_status": "known",
        "side_state": "long_active",
        "previous_side_state": "long_armed",
        "next_side_state": "long_active",
        "scope_event_type": "upscope_confirmed",
        "transition_allowed": True,
        "transition_reason_code": "UPSCOPE_CONFIRMED",
        "reason_codes": ("STATE_SWITCH_OK",),
        "evidence_digest": "b" * 64,
    }
    base.update(overrides)
    return base


def _write_source_regime(archive_root: Path, payload: dict[str, object]) -> Path:
    path = archive_root / SOURCE_REGIME_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_capability_id_and_artifact_path_are_stable() -> None:
    assert CAPABILITY_ID == ("CAPABILITY_PRESENTATION_BULL_BEAR_REGIME_PROJECTION_MATERIALIZER_V1")
    assert STORAGE_RELATIVE_PATH == ("readmodels/bull_bear_regime_presentation_projection.v1.json")
    assert SOURCE_REGIME_RELATIVE_PATH == "readmodels/regime_bull_bear_switch.v1.json"
    assert LEGACY_ROUTE_NON_SOURCE == "double_play_dashboard_display_json_route_v0"
    assert STATUS_NOT_BOUND == "NOT_BOUND"
    assert STATUS_MISSING_SOURCE == "MISSING_SOURCE"


def test_build_payload_is_deterministic() -> None:
    regime = _regime()
    first, err_a = build_bull_bear_regime_presentation_projection_payload_v1(
        regime_bull_bear_switch=regime,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    second, err_b = build_bull_bear_regime_presentation_projection_payload_v1(
        regime_bull_bear_switch=regime,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://unit-test",
    )
    assert err_a == ()
    assert err_b == ()
    assert first is not None and second is not None
    assert first == second
    assert serialize_bull_bear_regime_presentation_projection_v1(
        first
    ) == serialize_bull_bear_regime_presentation_projection_v1(second)


@pytest.mark.parametrize(
    ("side_state", "label"),
    [
        ("long_active", "BULL"),
        ("short_active", "BEAR"),
        ("neutral_observe", "NEUTRAL"),
    ],
)
def test_canonical_side_state_pass_through_without_reinterpretation(
    side_state: str,
    label: str,
    tmp_path: Path,
) -> None:
    """Canonical SideState values pass through; no invented BULL/BEAR gloss."""
    _ = label  # vocabulary coverage marker for BULL/BEAR/NEUTRAL distinctions
    regime = _regime(
        side_state=side_state,
        previous_side_state=side_state,
        next_side_state=side_state,
        scope_event_type="noop",
        transition_allowed=False,
        transition_reason_code="NOOP",
    )
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=regime,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.side_state == side_state
    loaded = try_load_bull_bear_regime_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.side_state == side_state
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["side_state"] == side_state
    # Must not invent directional gloss strings.
    body = (tmp_path / STORAGE_RELATIVE_PATH).read_text(encoding="utf-8")
    assert "bullish" not in body.lower()
    assert "bearish" not in body.lower()
    assert '"BULL"' not in body
    assert '"BEAR"' not in body


def test_materialize_writes_loader_expected_path(tmp_path: Path) -> None:
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=_regime(),
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
    materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=_regime(),
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
        source_reference="presentation://materializer-compat",
    )
    loaded = try_load_bull_bear_regime_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.load_errors == ()
    assert loaded.side_state == "long_active"
    assert loaded.evidence_digest == "b" * 64
    assert loaded.binder_fields is not None
    assert loaded.binder_fields["regime_id"] == "trending"
    assert loaded.binder_fields["regime_status"] == "known"
    assert loaded.binder_fields["transition_allowed"] is True


def test_missing_source_does_not_invent_artifact(tmp_path: Path) -> None:
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=None,
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_MISSING_SOURCE
    assert MATERIALIZE_ERROR_MISSING_SOURCE in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()
    loaded = try_load_bull_bear_regime_presentation_projection_v1(tmp_path)
    assert loaded.loaded is False


def test_unbound_vocabulary_is_explicit() -> None:
    assert STATUS_NOT_BOUND == "NOT_BOUND"
    assert STATUS_MISSING_SOURCE == "MISSING_SOURCE"


def test_invalid_source_fail_closed(tmp_path: Path) -> None:
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch={"regime_id": "trending", "side_state": "long_active"},
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_REGIME_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_contradiction_fail_closed(tmp_path: Path) -> None:
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=_regime(
            side_state="long_active",
            next_side_state="short_active",
        ),
        generated_at=PRODUCER_FRESH,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_REGIME_INVALID in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_missing_generated_at_fail_closed(tmp_path: Path) -> None:
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=_regime(),
        generated_at=None,
    )
    assert result.written is False
    assert result.status == STATUS_FAIL_CLOSED
    assert LOAD_ERROR_TIMESTAMP_MISSING in result.errors
    assert not (tmp_path / STORAGE_RELATIVE_PATH).exists()


def test_does_not_mutate_canonical_inputs(tmp_path: Path) -> None:
    regime = _regime()
    snapshot = deepcopy(regime)
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=regime,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert regime == snapshot


def test_materialize_from_durable_producer_regime_source(tmp_path: Path) -> None:
    _write_source_regime(tmp_path, _regime())
    result = materialize_bull_bear_regime_presentation_projection_v1(
        tmp_path,
        regime_bull_bear_switch=None,
        generated_at=PRODUCER_FRESH,
        effective_at=PRODUCER_FRESH,
    )
    assert result.written is True
    assert result.status == STATUS_WRITTEN
    assert result.source_path is not None
    assert SOURCE_REGIME_RELATIVE_PATH in result.source_path
    loaded = try_load_bull_bear_regime_presentation_projection_v1(tmp_path)
    assert loaded.loaded is True
    assert loaded.side_state == "long_active"


def test_legacy_route_is_non_source_and_unused() -> None:
    materializer = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "bull_bear_regime_presentation_projection_materializer_v1.py"
    ).read_text(encoding="utf-8")
    assert LEGACY_ROUTE_NON_SOURCE in materializer
    assert "NON_SOURCE" in materializer
    assert "double_play_dashboard_display_json_route_v0" in materializer
    # Must never import or call the legacy route module as truth.
    assert "from src.webui.double_play_dashboard_display_json_route_v0" not in materializer
    assert "build_static_dashboard_display_dict" not in materializer


def test_end_to_end_projection_to_autobind_consumer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    fresh = datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_source_regime(archive, _regime(side_state="long_active", next_side_state="long_active"))
    result = materialize_bull_bear_regime_presentation_projection_v1(
        archive,
        regime_bull_bear_switch=None,
        generated_at=fresh,
        effective_at=fresh,
        source_reference="presentation://e2e-materializer",
    )
    assert result.written is True
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=datetime.now(timezone.utc))
    snap = slots["regime_bull_bear_switch"]
    assert snap.availability is Availability.AVAILABLE
    assert snap.side_state == "long_active"
    assert snap.regime_id == "trending"
    assert snap.regime_status == "known"
    assert snap.provenance.producer_module == REGIME_BULL_BEAR_SWITCH_PRODUCER_MODULE
    assert snap.provenance.source_kind == REGIME_BULL_BEAR_SWITCH_SOURCE_KIND
    assert snap.provenance.source_reference == "presentation://e2e-materializer"
    assert snap.provenance.evidence_digest == "b" * 64

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "long_active" in html
    assert 'data-mdl-field="bull_bear"' in html
    assert 'data-mdl-field="bull_bear" data-availability="AVAILABLE"' in html
    assert "<form" not in html.lower()
    assert "place_order" not in html.lower()


def test_existing_presentation_autobind_paths_remain_compatible(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Decision/Double-Play autobind remains MISSING_SOURCE when absent; no crash."""
    archive = tmp_path / "archive"
    archive.mkdir()
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    slots = bind_market_universe_slots(generated_at=datetime.now(timezone.utc))
    assert slots["regime_bull_bear_switch"].availability is Availability.MISSING_SOURCE
    assert slots["canonical_decision"].availability is Availability.MISSING_SOURCE
    assert slots["double_play"].availability is Availability.MISSING_SOURCE


def test_materializer_module_has_no_forbidden_trading_imports() -> None:
    path = (
        REPO
        / "src/webui/workflow_dashboard_readmodel_v1"
        / "bull_bear_regime_presentation_projection_materializer_v1.py"
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
                "derive_active_side",
            }
    source = path.read_text(encoding="utf-8")
    assert CAPABILITY_ID in source
    assert "STORAGE_RELATIVE_PATH" in source
    assert "map_regime_bull_bear_switch_to_binder_fields_v1" in source
    assert LEGACY_ROUTE_NON_SOURCE in source
    assert "NON_SOURCE" in source
