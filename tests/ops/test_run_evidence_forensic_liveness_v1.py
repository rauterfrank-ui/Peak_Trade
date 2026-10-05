"""Regression: consecutive zero-enter forensic liveness alarm (passive only)."""

from __future__ import annotations

from src.ops.paper_shadow_bounded_orchestrator_v1.run_evidence_v1 import (
    ZERO_ENTER_LIVENESS_INVESTIGATION_THRESHOLD,
    RunEvidenceAccumulatorV1,
)


def _cycle(outcome: str = "no_action") -> dict:
    return {"decision_outcome": outcome, "cycle_id": "c", "reason_codes": []}


def test_no_alarm_at_199_consecutive_zero_enter_cycles() -> None:
    ev = RunEvidenceAccumulatorV1(
        run_id="t",
        fixpoint_sha="x",
        fixpoint_tree="y",
        settings_digest="z",
    )
    ev.cycle_count = 199
    for _ in range(199):
        ev.record_productive_cycle(bridge_cycle=_cycle("observe"))
    assert ev.consecutive_zero_enter_cycles == 199
    assert ev.forensic_liveness_alarm_v1() is None


def test_alarm_at_200_consecutive_zero_enter_cycles() -> None:
    ev = RunEvidenceAccumulatorV1(
        run_id="t",
        fixpoint_sha="x",
        fixpoint_tree="y",
        settings_digest="z",
    )
    ev.cycle_count = ZERO_ENTER_LIVENESS_INVESTIGATION_THRESHOLD
    for _ in range(ZERO_ENTER_LIVENESS_INVESTIGATION_THRESHOLD):
        ev.record_productive_cycle(bridge_cycle=_cycle("blocked"))
    assert ev.forensic_liveness_alarm_v1() == "ZERO_ENTER_LIVENESS_INVESTIGATION"
    payload = ev.to_dict()
    assert payload["FORENSIC_LIVENESS_ALARM"] == "ZERO_ENTER_LIVENESS_INVESTIGATION"


def test_enter_resets_consecutive_zero_enter_streak() -> None:
    ev = RunEvidenceAccumulatorV1(
        run_id="t",
        fixpoint_sha="x",
        fixpoint_tree="y",
        settings_digest="z",
    )
    for _ in range(250):
        ev.record_productive_cycle(bridge_cycle=_cycle("no_action"))
    ev.record_productive_cycle(bridge_cycle=_cycle("enter_long"))
    assert ev.consecutive_zero_enter_cycles == 0
    assert ev.forensic_liveness_alarm_v1() is None
