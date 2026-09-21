"""Tests for CAPABILITY_REGIME_BULL_BEAR_SWITCH_ARCHIVE_SIBLING_EXPORTER_V1."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.family_export_adapter_v1 import (
    export_families_after_runtime_commit_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    ArchiveBindingV1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.state_root_layout_v1 import (
    materialize_state_root_layout_v1,
)
from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_EVIDENCE_READMODEL_SHORTCUT_FORBIDDEN,
    TARGET_RELATIVE_PATH,
)
from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.exporter_v1 import (
    export_regime_bull_bear_switch_to_archive_sibling_v1,
)
from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.replay_commit_source_v1 import (
    build_regime_bull_bear_switch_sibling_payload_from_replay_commit_v1,
)
from src.trading.master_v2.double_play_state import TransitionDecision
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    StateSwitchEvidenceV1,
)
from src.webui.market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_materializer_v1 import (
    SOURCE_REGIME_RELATIVE_PATH,
    materialize_bull_bear_regime_presentation_projection_v1,
    try_load_regime_bull_bear_switch_source_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH,
    try_load_bull_bear_regime_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
EXPORTER_DIR = REPO / "src/ops/regime_bull_bear_switch_archive_sibling_exporter_v1"


@dataclass
class _ReplayIntermediateStub:
    state_switch: StateSwitchEvidenceV1
    transition_decision: TransitionDecision


def _state_switch(**overrides: object) -> StateSwitchEvidenceV1:
    base = dict(
        state_switch_id="sw-1",
        instrument_id="BTC-USDT-SWAP",
        trading_epoch=42,
        previous_side_state="long_armed",
        next_side_state="long_active",
        scope_event_type="upscope_confirmed",
        transition_allowed=True,
        transition_reason_code="UPSCOPE_CONFIRMED",
        semantic_digest="a" * 64,
    )
    base.update(overrides)
    return StateSwitchEvidenceV1(**base)


def _intermediate(**overrides: object) -> _ReplayIntermediateStub:
    sw = _state_switch(**{k: v for k, v in overrides.items() if k != "transition"})
    transition = overrides.get(
        "transition",
        TransitionDecision(True, "UPSCOPE_CONFIRMED", False),
    )
    if not isinstance(transition, TransitionDecision):
        transition = TransitionDecision(True, str(transition), False)
    return _ReplayIntermediateStub(state_switch=sw, transition_decision=transition)


def test_capability_id_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_REGIME_BULL_BEAR_SWITCH_ARCHIVE_SIBLING_EXPORTER_V1"
    assert TARGET_RELATIVE_PATH == SOURCE_REGIME_RELATIVE_PATH


def test_build_sibling_from_replay_commit_fields() -> None:
    payload, errors = build_regime_bull_bear_switch_sibling_payload_from_replay_commit_v1(
        regime_id="trending",
        regime_status="known",
        replay_intermediate=_intermediate(),
    )
    assert errors == ()
    assert payload is not None
    assert payload["regime_id"] == "trending"
    assert payload["regime_status"] == "known"
    assert payload["side_state"] == "long_active"
    assert payload["next_side_state"] == "long_active"
    assert payload["transition_allowed"] is True


def test_evidence_readmodel_shortcut_forbidden() -> None:
    evidence_dict = {
        "schema_name": "regime_bull_bear_switch_evidence_readmodel.v1",
        "regime_id": "trending",
        "regime_status": "known",
        "side_state": "long_active",
        "previous_side_state": "long_armed",
        "next_side_state": "long_active",
        "scope_event_type": "noop",
        "transition_allowed": True,
        "transition_reason_code": "NOOP",
    }
    payload, errors = build_regime_bull_bear_switch_sibling_payload_from_replay_commit_v1(
        regime_id="trending",
        regime_status="known",
        replay_intermediate=evidence_dict,
    )
    assert payload is None
    assert ERROR_EVIDENCE_READMODEL_SHORTCUT_FORBIDDEN in errors


def test_transition_identity_mismatch_fail_closed() -> None:
    payload, errors = build_regime_bull_bear_switch_sibling_payload_from_replay_commit_v1(
        regime_id="trending",
        regime_status="known",
        replay_intermediate=_intermediate(
            transition=TransitionDecision(False, "BLOCKED", False),
        ),
    )
    assert payload is None
    assert errors


def test_export_materialize_loader_binder_chain(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    intermediate = _intermediate()
    export_out = export_regime_bull_bear_switch_to_archive_sibling_v1(
        archive_root=archive_root,
        regime_id="trending",
        regime_status="known",
        replay_intermediate=intermediate,
    )
    assert export_out.exported is True
    sibling_path = archive_root / SOURCE_REGIME_RELATIVE_PATH
    assert sibling_path.is_file()

    loaded, load_errors, _ = try_load_regime_bull_bear_switch_source_v1(archive_root)
    assert load_errors == ()
    assert loaded is not None

    mat = materialize_bull_bear_regime_presentation_projection_v1(
        archive_root,
        generated_at="2026-09-21T12:00:00Z",
        effective_at="2026-09-21T12:00:00Z",
    )
    assert mat.written is True
    assert (archive_root / STORAGE_RELATIVE_PATH).is_file()

    projection = try_load_bull_bear_regime_presentation_projection_v1(archive_root)
    assert projection.loaded is True
    assert projection.binder_fields is not None

    from datetime import datetime, timezone

    slots = bind_market_universe_slots(
        generated_at=datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc),
        archive_root=archive_root,
    )
    regime_slot = slots["regime_bull_bear_switch"]
    assert regime_slot.availability in (Availability.AVAILABLE, Availability.STALE)


def test_family_export_regime_does_not_break_double_play_hard_stop(tmp_path: Path) -> None:
    state_roots = materialize_state_root_layout_v1(runtime_root=tmp_path / "runtime")
    archive_root = tmp_path / "archive"
    readmodels = archive_root / "readmodels"
    readmodels.mkdir(parents=True)
    archive = ArchiveBindingV1(
        archive_root=str(archive_root.resolve()),
        resolution_precedence="test",
        readmodels_dir=str(readmodels.resolve()),
        dynamic_scope_sibling_path=str((readmodels / "dynamic_scope_state_v1.json").resolve()),
        canonical_decision_sibling_path=str(
            (readmodels / "canonical_trading_decision_evidence.v1.json").resolve()
        ),
        double_play_sibling_path=str(
            (readmodels / "double_play_dashboard_display.v1.json").resolve()
        ),
        regime_bull_bear_switch_sibling_path=str(
            (readmodels / "regime_bull_bear_switch.v1.json").resolve()
        ),
        writable=True,
    )

    partial_intermediate = type(
        "_PartialInter",
        (),
        {"transition_decision": TransitionDecision(True, "NOOP", False)},
    )()

    families = export_families_after_runtime_commit_v1(
        state_roots=state_roots,
        archive=archive,
        cycle_id="cycle-rg-1",
        cycle_index=0,
        dynamic_scope_persisted=False,
        evidence_payload=None,
        replay_intermediate=partial_intermediate,
        replay_regime_id="trending",
        replay_regime_status="known",
    )
    assert (
        families["double_play"].error_code
        == "HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH"
    )
    assert families["regime_bull_bear_switch"].exported is False

    families_ok = export_families_after_runtime_commit_v1(
        state_roots=state_roots,
        archive=archive,
        cycle_id="cycle-rg-2",
        cycle_index=1,
        dynamic_scope_persisted=False,
        evidence_payload=None,
        replay_intermediate=_intermediate(),
        replay_regime_id="trending",
        replay_regime_status="known",
        generated_at="2026-09-21T12:00:00Z",
    )
    rg = families_ok["regime_bull_bear_switch"]
    assert rg.exported is True
    assert rg.materialized is True
    assert rg.loader_ok is True
    assert (
        families_ok["double_play"].error_code
        == "HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH"
    )


def test_exporter_modules_do_not_import_trading_producers() -> None:
    forbidden = (
        "transition_state",
        "compose_double_play_decision",
        "build_dashboard_display_snapshot",
    )
    for path in EXPORTER_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for token in forbidden:
                    assert token not in node.module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for token in forbidden:
                        assert token not in alias.name


def test_missing_replay_intermediate_fail_closed(tmp_path: Path) -> None:
    out = export_regime_bull_bear_switch_to_archive_sibling_v1(
        archive_root=tmp_path,
        regime_id="trending",
        regime_status="known",
        replay_intermediate=None,
    )
    assert out.exported is False
    assert not (tmp_path / SOURCE_REGIME_RELATIVE_PATH).exists()
