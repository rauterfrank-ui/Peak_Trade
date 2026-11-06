"""Lane → evaluation witness disposition (N5-compatible)."""

from __future__ import annotations

from src.ops.top20_opportunity_evaluation_residency_v1.lane_evaluation_witness_disposition_v1 import (
    CONTINUOUS_TERMINAL_MAX_CYCLES,
    evaluation_witness_disposition_from_n5_compatible_integrated_replay_v1,
    normalize_lane_disposition_to_evaluation_witness_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
    is_canonical_evaluation_complete_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    EvaluationCompletionWitnessV1,
)


def test_hold_closed_normalizes_to_hold_witness() -> None:
    assert normalize_lane_disposition_to_evaluation_witness_v1("HOLD_CLOSED") == "HOLD"


def test_pre_external_passthrough() -> None:
    assert (
        normalize_lane_disposition_to_evaluation_witness_v1("PRE_EXTERNAL_EFFECT")
        == "PRE_EXTERNAL_EFFECT"
    )


def test_max_cycles_bound_stop_alone_not_success() -> None:
    ok, disp, meta = evaluation_witness_disposition_from_n5_compatible_integrated_replay_v1(
        {"DISPOSITION": CONTINUOUS_TERMINAL_MAX_CYCLES, "CYCLES_COMPLETED": 0, "CYCLE_TRACES": ()}
    )
    assert ok is False
    assert meta["mapping"] == "no_completed_cycles"


def test_observe_hold_cycles_map_to_hold_witness() -> None:
    replay = {
        "DISPOSITION": CONTINUOUS_TERMINAL_MAX_CYCLES,
        "TERMINAL_CLASS": "MAX_CYCLES_BOUND",
        "CYCLES_COMPLETED": 4,
        "CYCLE_TRACES": [
            {"DECISION_RESULT": "OBSERVE_HOLD", "MASTER_V2_DECISION": "no_action"},
            {"DECISION_RESULT": "OBSERVE_HOLD", "MASTER_V2_DECISION": "no_action"},
        ],
    }
    ok, disp, meta = evaluation_witness_disposition_from_n5_compatible_integrated_replay_v1(replay)
    assert ok is True
    assert disp == "HOLD"
    assert meta["mapping"] == "n5_compatible_observe_hold_to_witness_hold"
    witness = EvaluationCompletionWitnessV1("id", "epoch", True, disp)
    assert is_canonical_evaluation_complete_v1(witness)


def test_fail_closed_cycle_not_success() -> None:
    replay = {
        "DISPOSITION": CONTINUOUS_TERMINAL_MAX_CYCLES,
        "CYCLES_COMPLETED": 1,
        "CYCLE_TRACES": [{"DECISION_RESULT": "FAIL_CLOSED", "BLOCKER_CLASS": "FAIL_CLOSED"}],
    }
    ok, _, meta = evaluation_witness_disposition_from_n5_compatible_integrated_replay_v1(replay)
    assert ok is False
    assert meta["mapping"] == "lane_fail_closed"
