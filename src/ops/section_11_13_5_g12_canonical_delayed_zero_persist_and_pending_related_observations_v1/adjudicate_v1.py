"""Evaluate the merged delayed G12 conjunction on persisted/fresh slots."""

from __future__ import annotations

from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.constants_v1 import (
    CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN,
    EARLIEST_UNRESOLVED_DEPENDENCY_IF_UNPROVEN,
    G12_STATUS_CLOSED,
    G12_STATUS_OPEN,
    NEXT_OWNER_GO_IF_G12_CLOSED,
    TARGET_INSTRUMENT_ID_VALUE,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.contract_v1 import (
    assert_contract_invariants_v1,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.evaluate_v1 import (
    DelayedG12ConjunctionVerdictV1,
    evaluate_delayed_g12_conjunction_v1,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.types_v1 import (
    DelayedG12ConjunctionInputV1,
    FlattenLineageSlotV1,
    ObservationSlotV1,
)


def evaluate_full_g12_conjunction_v1(
    *,
    flatten_lineage: FlattenLineageSlotV1,
    delayed_target_zero: ObservationSlotV1,
    pending_orders: ObservationSlotV1 | None,
    related_positions: ObservationSlotV1 | None,
) -> DelayedG12ConjunctionVerdictV1:
    payload = DelayedG12ConjunctionInputV1(
        instrument_id=TARGET_INSTRUMENT_ID_VALUE,
        flatten_lineage=flatten_lineage,
        delayed_target_zero=delayed_target_zero,
        pending_orders=pending_orders,
        related_positions=related_positions,
        forensic_local_treated_as_canonical=False,
    )
    verdict = evaluate_delayed_g12_conjunction_v1(payload)
    status_map = {item.proposition: item.status for item in verdict.conjuncts}
    closeout = {
        "full_conjunction_proven": verdict.full_conjunction_proven,
        "LIVE_FLATTEN_PROVABILITY_PROVEN": verdict.live_flatten_provability_proven,
        "G12_STATUS": (G12_STATUS_CLOSED if verdict.full_conjunction_proven else G12_STATUS_OPEN),
        "EMPTY_DATA_IS_ZERO": False,
        "forensic_local_treated_as_canonical": False,
    }
    assert_contract_invariants_v1(closeout)
    return verdict


def closeout_fields_v1(
    *,
    verdict: DelayedG12ConjunctionVerdictV1,
    delayed_window_proven: bool,
) -> dict[str, Any]:
    status_map = {
        item.proposition: {"status": item.status, "reason": item.reason}
        for item in verdict.conjuncts
    }
    full = bool(verdict.full_conjunction_proven)
    remaining = [item.proposition for item in verdict.conjuncts if item.status != "PASS"]
    return {
        "P1_AUTHORIZED_FLATTEN": status_map["P1_AUTHORIZED_FLATTEN"]["status"],
        "P2_VENUE_ACCEPTED": status_map["P2_VENUE_ACCEPTED"]["status"],
        "P3_ORDER_FILLED": status_map["P3_ORDER_FILLED"]["status"],
        "P4_PRE_ACTION_NONZERO": status_map["P4_PRE_ACTION_NONZERO"]["status"],
        "P5_DELAYED_TARGET_ZERO": status_map["P5_DELAYED_TARGET_ZERO"]["status"],
        "P6_CAUSAL_LINEAGE": status_map["P6_CAUSAL_LINEAGE"]["status"],
        "P7_PENDING_EMPTY": status_map["P7_PENDING_EMPTY"]["status"],
        "P8_NO_FLIP": status_map["P8_NO_FLIP"]["status"],
        "P9_NO_UNEXPECTED_RELATED_NONZERO": status_map["P9_NO_UNEXPECTED_RELATED_NONZERO"][
            "status"
        ],
        "P10_TEMPORAL_ORDER": status_map["P10_TEMPORAL_ORDER"]["status"],
        "CONJUNCT_REASONS": {key: value["reason"] for key, value in status_map.items()},
        "FULL_G12_CONJUNCTION_CURRENTLY_PROVEN": full,
        "LIVE_FLATTEN_PROVABILITY_PROVEN": bool(verdict.live_flatten_provability_proven),
        "DELAYED_EXPLICIT_TARGET_ZERO": bool(verdict.delayed_explicit_target_zero),
        "TARGET_POSITION_ZERO_WINDOW_PROVEN": bool(delayed_window_proven),
        "CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN": bool(full and delayed_window_proven),
        "CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN_FROM_P5_ALONE": CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN,
        "G12_STATUS": G12_STATUS_CLOSED if full else G12_STATUS_OPEN,
        "G12_CLOSURE_CRITERIA_STATUS": "CLOSED" if full else "OPEN",
        "EXACT_REMAINING_G12_BLOCKER": remaining[0] if remaining else "",
        "REMAINING_CONJUNCTS": remaining,
        "EARLIEST_UNRESOLVED_DEPENDENCY": (
            "SECTION_11_14_NOT_AUTHORIZED" if full else EARLIEST_UNRESOLVED_DEPENDENCY_IF_UNPROVEN
        ),
        "NEXT_CANONICAL_POINTER": (
            NEXT_OWNER_GO_IF_G12_CLOSED if full else EARLIEST_UNRESOLVED_DEPENDENCY_IF_UNPROVEN
        ),
        "BLOCKING_REASONS": list(verdict.blocking_reasons),
        "EVALUATOR_PROVENANCE_SHA256": verdict.provenance_sha256,
        "SECTION_11_14_AUTHORIZED": False,
    }
