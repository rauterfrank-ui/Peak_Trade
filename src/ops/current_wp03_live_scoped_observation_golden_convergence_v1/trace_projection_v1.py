"""Project standing supervisor runtime into GOLDEN_TRACE_KEYS shape."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorRunResultV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.golden_happy_path_trace_harness_v1 import (
    GOLDEN_TRACE_KEYS,
)

SideLabel = Literal["LONG", "SHORT", "HOLD"]


def assert_all_golden_trace_keys_present_v1(trace: Mapping[str, Any]) -> None:
    missing = [key for key in GOLDEN_TRACE_KEYS if key not in trace]
    if missing:
        raise ValueError(f"GOLDEN_TRACE_KEYS_MISSING:{','.join(missing)}")


def _wp02_chain_snapshot(extra: Mapping[str, Any]) -> Mapping[str, Any]:
    wp02 = extra.get("wp02") if isinstance(extra.get("wp02"), dict) else {}
    chain = wp02.get("chain_result")
    if chain is None:
        return {}
    if hasattr(chain, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(chain)
    if isinstance(chain, Mapping):
        return chain
    return {}


def project_supervisor_golden_trace_v1(
    result: StandingSupervisorRunResultV1,
    *,
    side: SideLabel,
    observation_scope: str,
    synthetic_b05_rejected: bool = True,
) -> dict[str, Any]:
    trace = result.trace
    policy = result.policy_result
    orch = policy.orchestrator_result if policy is not None else None
    last = orch.cycle_records[-1] if orch is not None and orch.cycle_records else None
    wp02 = _wp02_chain_snapshot(trace.extra)

    pre_external = bool(last and last.s5_disposition == "PRE_EXTERNAL_EFFECT")
    natural_decision = str(trace.extra.get("natural_enter_decision") or "")
    if side == "LONG" and natural_decision == "enter_long":
        pre_external = True
    if side == "SHORT" and natural_decision == "enter_short":
        pre_external = True
    if side == "HOLD":
        terminal_pre_external = False
    else:
        terminal_pre_external = pre_external

    ranking_id = str(
        trace.extra.get("wp02_ranking_snapshot_id")
        or wp02.get("ranking_snapshot_id")
        or wp02.get("ranking_observation_id")
        or ""
    )
    membership_id = (
        "persisted"
        if getattr(trace, "wp02_membership_persisted", False)
        else str(wp02.get("membership_artifact_id") or "")
    )

    projected: dict[str, Any] = {
        "RUN_ID": trace.run_id,
        "instrument": trace.bound_instrument_id or trace.venue_native_id,
        "instrument_epoch": trace.extra.get("instrument_epoch", "bound_from_cap24_context"),
        "ranking_snapshot": ranking_id
        or {"status": "wp02_not_wired", "marks": trace.public_marks_count},
        "membership_artifact": membership_id or {"status": "wp02_not_wired"},
        "lane_id": "LANE_1",
        "cap23_selection": {"side_intent": side, "source": "supervisor_continuous_path"},
        "cap24_binding": {
            "instrument_id": trace.bound_instrument_id,
            "venue_native_id": trace.venue_native_id,
        },
        "observation_epoch": {
            "accepted_c1_count": trace.accepted_c1_count,
            "last_accepted_c1": orch.last_accepted_c1 if orch is not None else None,
            "observation_scope": observation_scope,
        },
        "confirmation_epoch": {
            "governed_cycle_count": trace.governed_cycle_count,
            "cursor_floor_before": orch.cursor_floor_before if orch is not None else None,
            "cursor_floor_after": orch.cursor_floor_after if orch is not None else None,
            "contiguous_confirmation": trace.accepted_c1_count >= 2,
        },
        "g17": {
            "refreshed": trace.pretrade_truth_refreshed,
            "freshness": trace.pretrade_freshness_status,
        },
        "feature_regime": {
            "transport_scope": trace.extra.get("transport_scope", observation_scope)
        },
        "cmc": {"public_marks_count": trace.public_marks_count},
        "dynamic_scope": {"side": side},
        "mv2_double_play": {
            "last_s5_disposition": last.s5_disposition if last is not None else "",
            "last_s5_reason": last.s5_reason_code if last is not None else "",
        },
        "qualification": {"continuous_admission_granted": trace.continuous_admission_granted},
        "side_state": {"declared_side": side},
        "entry_exit_policy": {"terminal_disposition": trace.terminal_disposition},
        "quantity": {"post_count": trace.post_count},
        "reservation": {"permit_created": bool(orch.permit_created) if orch is not None else False},
        "final_order_envelope": {
            "pre_external_reached": terminal_pre_external,
            "envelope_identity": last.cycle_instance_id if last is not None else "",
        },
        "pre_external": terminal_pre_external,
        "observation_scope": observation_scope,
        "synthetic_b05_rejected": synthetic_b05_rejected,
        "side": side,
        "terminal": "PRE_EXTERNAL" if terminal_pre_external else "HOLD",
    }
    assert_all_golden_trace_keys_present_v1(projected)
    return projected


def prove_contiguous_confirmation_epochs_v1(
    *, accepted_c1_count: int, governed_cycle_count: int
) -> bool:
    return (
        accepted_c1_count >= 2
        and governed_cycle_count >= 2
        and accepted_c1_count == governed_cycle_count
    )
