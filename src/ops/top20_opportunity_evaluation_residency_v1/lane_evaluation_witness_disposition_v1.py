"""N5-compatible lane disposition → evaluation witness disposition (read-only).

Trading/lane dispositions and residency evaluation completion are distinct.
This module normalizes **lane/governed-cycle** outcomes into witness dispositions
consumed by ``is_canonical_evaluation_complete_v1`` — same contract as
``witnesses_from_orchestrator_lane_map_v1`` in the N5 control plane.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    GOVERNED_CYCLE_SUCCESS_DISPOSITIONS,
)

# Governed single-cycle orchestrator (N5 lane rollup source).
LANE_DISPOSITION_HOLD_CLOSED = "HOLD_CLOSED"
LANE_DISPOSITION_HOLD_CONTINUE = "HOLD_CONTINUE_CLOSED"

# Continuous observation orchestrator terminals (not evaluation success alone).
CONTINUOUS_TERMINAL_MAX_CYCLES = "MAX_CYCLES_BOUND_STOP"
CONTINUOUS_TERMINAL_MAX_DURATION = "MAX_DURATION_BOUND_STOP"

# Normalized witness tokens (subset of GOVERNED_CYCLE_SUCCESS_DISPOSITIONS).
WITNESS_DISPOSITION_HOLD = "HOLD"
WITNESS_DISPOSITION_PRE_EXTERNAL = "PRE_EXTERNAL_EFFECT"
WITNESS_DISPOSITION_COMPLETED = "COMPLETED"


def normalize_lane_disposition_to_evaluation_witness_v1(
    lane_disposition: str,
) -> str | None:
    """Map a lane/governed-cycle disposition to a canonical witness token."""

    raw = str(lane_disposition or "").strip()
    if not raw:
        return None
    if raw in GOVERNED_CYCLE_SUCCESS_DISPOSITIONS:
        return raw
    if raw == LANE_DISPOSITION_HOLD_CLOSED:
        return WITNESS_DISPOSITION_HOLD
    if raw == LANE_DISPOSITION_HOLD_CONTINUE:
        return WITNESS_DISPOSITION_HOLD
    return None


def _cycle_trace_fail_closed_v1(trace: Mapping[str, Any]) -> bool:
    decision = str(trace.get("DECISION_RESULT") or "").upper()
    if "FAIL_CLOSED" in decision or decision == "FAIL_CLOSED":
        return True
    blocker = str(trace.get("BLOCKER_CLASS") or "").upper()
    if blocker in {"FAIL_CLOSED", "GOVERNANCE_FAIL_CLOSED"}:
        return True
    return False


def evaluation_witness_disposition_from_n5_compatible_integrated_replay_v1(
    replay: Mapping[str, Any],
) -> tuple[bool, str, Mapping[str, Any]]:
    """Derive evaluation completion disposition from integrated replay (GHV path).

    Does **not** treat continuous-runner budget terminals alone as evaluation success.
    Reuses N5 semantics: governed-cycle / lane-level observe-hold → witness HOLD when
    integrated offline replay executed and cycles completed without lane fail-closed.
    """

    forensic: dict[str, Any] = {
        "terminal_disposition": str(replay.get("DISPOSITION") or ""),
        "terminal_class": str(replay.get("TERMINAL_CLASS") or ""),
        "cycles_completed": int(replay.get("CYCLES_COMPLETED") or 0),
    }
    terminal = forensic["terminal_disposition"]
    normalized_terminal = normalize_lane_disposition_to_evaluation_witness_v1(terminal)
    if normalized_terminal is not None:
        forensic["mapping"] = "terminal_lane_compatible"
        return True, normalized_terminal, forensic

    traces = replay.get("CYCLE_TRACES") or ()
    forensic["cycle_trace_count"] = len(traces)
    if not traces or int(replay.get("CYCLES_COMPLETED") or 0) < 1:
        forensic["mapping"] = "no_completed_cycles"
        return False, terminal or "NO_CYCLES_COMPLETED", forensic

    for idx, row in enumerate(traces):
        if not isinstance(row, Mapping):
            continue
        if _cycle_trace_fail_closed_v1(row):
            forensic["mapping"] = "lane_fail_closed"
            forensic["fail_cycle_index"] = idx + 1
            return False, str(row.get("DECISION_RESULT") or "FAIL_CLOSED"), forensic

    last = traces[-1]
    if not isinstance(last, Mapping):
        forensic["mapping"] = "invalid_last_trace"
        return False, terminal or "EVALUATION_DISPOSITION_NOT_SUCCESS", forensic

    decision = str(last.get("DECISION_RESULT") or "")
    forensic["last_decision_result"] = decision
    forensic["last_master_v2_decision"] = str(last.get("MASTER_V2_DECISION") or "")

    # Evidence-backed: post6999 ON-USDT 4×180s → OBSERVE_HOLD / no_action per cycle.
    if decision.upper().startswith("OBSERVE") or "OBSERVE_HOLD" in decision.upper():
        forensic["mapping"] = "n5_compatible_observe_hold_to_witness_hold"
        return True, WITNESS_DISPOSITION_HOLD, forensic

    normalized = normalize_lane_disposition_to_evaluation_witness_v1(decision)
    if normalized is not None:
        forensic["mapping"] = "last_trace_lane_disposition"
        return True, normalized, forensic

    forensic["mapping"] = "unmapped_lane_semantics"
    return False, terminal or "EVALUATION_DISPOSITION_NOT_SUCCESS", forensic
