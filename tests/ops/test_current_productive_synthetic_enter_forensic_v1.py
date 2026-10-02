"""Forensic synthetic ENTER overlay (default OFF). No POST. No natural-enter contamination."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    STATUS_MISSING,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    ENTRY_ORIGIN_SYNTHETIC_FORENSIC,
    INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1,
    SYNTHETIC_REASON_DOWNSTREAM_LIVENESS,
    SyntheticEnterForensicSessionV1,
    active_synthetic_enter_forensic_session_v1,
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    maybe_apply_synthetic_enter_forensic_overlay_v1,
    read_cycle_index_from_s5_evidence_root_v1,
    reset_synthetic_enter_forensic_session_v1,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _bound,
    _enter_replay,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)


def _observe_replay_from_enter_fixture():
    _, cycle_b, _ = _host_enter_cycle()
    enter_replay = _enter_replay(cycle_b)
    return replace(
        enter_replay,
        evidence=replace(enter_replay.evidence, decision_outcome="observe"),
    )


def test_synthetic_forensic_default_off_leaves_replay_unchanged() -> None:
    hold_replay = _observe_replay_from_enter_fixture()
    natural = str(hold_replay.evidence.decision_outcome or "").lower()
    result = maybe_apply_synthetic_enter_forensic_overlay_v1(
        hold_replay,
        cycle_index=1,
    )
    assert result.applied is False
    assert str(result.replay.evidence.decision_outcome or "").lower() == natural
    assert active_synthetic_enter_forensic_session_v1() is None


def test_synthetic_overlay_applies_once_and_persists_evidence(tmp_path: Path) -> None:
    enter_replay = _observe_replay_from_enter_fixture()
    cycle_root = tmp_path / "cycles" / "abc"
    s5_root = cycle_root / "s5"
    s5_root.mkdir(parents=True)
    (cycle_root / "s5_cycle_authorization_v1.json").write_text(
        json.dumps({"cycle_index": 1}, sort_keys=True),
        encoding="utf-8",
    )
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="run-test",
    )
    token = bind_synthetic_enter_forensic_session_v1(session)
    try:
        first = maybe_apply_synthetic_enter_forensic_overlay_v1(
            enter_replay,
            cycle_index=1,
            cycle_evidence_root=s5_root,
        )
        second = maybe_apply_synthetic_enter_forensic_overlay_v1(
            enter_replay,
            cycle_index=1,
            cycle_evidence_root=s5_root,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(token)

    assert first.applied is True
    assert second.applied is False
    assert str(first.replay.evidence.decision_outcome) == "enter_short"
    assert first.record is not None
    assert first.record["entry_origin"] == ENTRY_ORIGIN_SYNTHETIC_FORENSIC
    assert first.record["synthetic_enter"] is True
    assert first.record["natural_enter"] is False
    assert first.record["synthetic_injection_point"] == INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1
    assert first.record["synthetic_reason"] == SYNTHETIC_REASON_DOWNSTREAM_LIVENESS

    ledger = tmp_path / "synthetic_enter_forensic_v1.jsonl"
    assert ledger.is_file()
    row = json.loads(ledger.read_text(encoding="utf-8").strip())
    assert row["synthetic_side"] == "enter_short"
    assert (s5_root / "synthetic_enter_forensic_cycle_v1.json").is_file()


def test_synthetic_does_not_overlay_when_natural_enter_already_present(
    tmp_path: Path,
) -> None:
    _, cycle_b, _ = _host_enter_cycle()
    cycle_b = _enter_replay(cycle_b)
    session = SyntheticEnterForensicSessionV1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="run-test",
    )
    token = bind_synthetic_enter_forensic_session_v1(session)
    try:
        result = maybe_apply_synthetic_enter_forensic_overlay_v1(
            cycle_b,
            cycle_index=1,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(token)
    assert result.applied is False
    assert str(cycle_b.evidence.decision_outcome or "").lower() in {"enter_long", "enter_short"}


def test_synthetic_overlay_reaches_live_29p_join_without_get(tmp_path: Path) -> None:
    observe_replay = _observe_replay_from_enter_fixture()
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="run-live29p",
    )
    token = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=1,
        )
        join = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=overlay.replay,
            bound_instrument=_bound(),
            injected=None,
            decision_epoch=EPOCH,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(token)

    assert overlay.applied is True
    assert join.called is True
    assert join.get_count == 0
    assert join.status == STATUS_MISSING
    assert "LIVE_29P" in str(join.first_blocker or "")


def test_read_cycle_index_from_parent_s5_authorization(tmp_path: Path) -> None:
    cycle_root = tmp_path / "cycles" / "id1"
    (cycle_root / "s5").mkdir(parents=True)
    (cycle_root / "s5_cycle_authorization_v1.json").write_text(
        json.dumps({"cycle_index": 3}),
        encoding="utf-8",
    )
    assert read_cycle_index_from_s5_evidence_root_v1(cycle_root / "s5") == 3
