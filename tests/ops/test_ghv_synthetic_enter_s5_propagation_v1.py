"""GHV synthetic enter_short must propagate through T2/S5 (no stale OBSERVE_HOLD)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    DECISION_ENTER,
    current_productive_decision_class_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    maybe_apply_synthetic_enter_forensic_overlay_v1,
    reset_synthetic_enter_forensic_session_v1,
)
from tests.ops.test_current_productive_synthetic_enter_forensic_v1 import (
    _observe_replay_from_enter_fixture,
)


def test_post_overlay_replay_classifies_enter_when_join_hold_replay_is_stale() -> None:
    """T2 must classify ENTER from post-overlay replay, not NOT_CALLED_HOLD join replay."""
    observe = _observe_replay_from_enter_fixture()
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=Path(tempfile.mkdtemp()),
        continuous_run_id="s5-propagation-unit",
    )
    reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe,
            cycle_index=1,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(reset)
    assert overlay.applied is True
    assert current_productive_decision_class_v1(overlay.replay) == DECISION_ENTER
    assert current_productive_decision_class_v1(observe) != DECISION_ENTER
    assert overlay.replay.evidence.selected_side == "short"


def test_synthetic_forensic_record_includes_selected_side_after_overlay(tmp_path: Path) -> None:
    observe = _observe_replay_from_enter_fixture()
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="side-record",
    )
    reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        maybe_apply_synthetic_enter_forensic_overlay_v1(observe, cycle_index=1)
    finally:
        reset_synthetic_enter_forensic_session_v1(reset)
    row = json.loads(
        (tmp_path / "synthetic_enter_forensic_v1.jsonl").read_text(encoding="utf-8").strip()
    )
    assert row["selected_side_after_overlay"] == "short"
    assert row["decision_outcome_after_overlay"] == "enter_short"
