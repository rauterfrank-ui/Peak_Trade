"""Machine-checkable lineage for productive flatten POST and reconciliation."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    TARGET_INSTRUMENT_ID,
)

LINEAGE_FIELD_NAMES: tuple[str, ...] = (
    "producer",
    "field",
    "source_path",
    "status",
    "semantic_object",
    "observed_value",
    "transformation",
    "output_object",
    "epistemic_class",
    "adjudication_status",
)


def _seam(
    *,
    producer: str,
    field: str,
    source_path: str,
    status: str,
    semantic_object: str,
    observed_value: str,
    transformation: str,
    output_object: str,
    epistemic_class: str,
    adjudication_status: str,
) -> dict[str, str]:
    return {
        "producer": producer,
        "field": field,
        "source_path": source_path,
        "status": status,
        "semantic_object": semantic_object,
        "observed_value": observed_value,
        "transformation": transformation,
        "output_object": output_object,
        "epistemic_class": epistemic_class,
        "adjudication_status": adjudication_status,
    }


def productive_flatten_post_lineage_v1(
    *,
    runtime_facts: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    observation = runtime_facts.get("OBSERVATION") or {}
    return (
        _seam(
            producer="AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE",
            field="PREDECESSOR",
            source_path=(
                "src/ops/section_11_13_5_authenticated_private_runtime_read_and_"
                "runtime_permit_issuance_v1/contract_v1.py"
            ),
            status="current_bound_predecessor",
            semantic_object="VALID_RUNTIME_PERMIT_THEN_FLATTEN_POST",
            observed_value="PREDECESSOR_CLOSED",
            transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
            output_object="CENSUS_CLOSED_INPUT",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_PREDECESSOR_WAS_PERMIT_ISSUANCE",
        ),
        _seam(
            producer="execute_productive_flatten_post_and_reconciliation_v1",
            field="PRE_WIRE_POSITION",
            source_path=(
                "src/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/"
                "execute_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="GET_API_V5_ACCOUNT_POSITIONS",
            observed_value=str(observation.get("POSITION_OBSERVATION_CLASS") or ""),
            transformation="FRESH_HMAC_GET_THEN_CLASSIFY_EMPTY_NOT_ZERO",
            output_object="PRE_WIRE_POSITION_OBSERVATION",
            epistemic_class="FORENSIC_RAW",
            adjudication_status="PROVEN_GET_PERFORMED",
        ),
        _seam(
            producer="evaluate_runtime_permit_issuance_v1",
            field="RUNTIME_PERMIT",
            source_path=(
                "src/ops/section_11_13_5_authenticated_private_runtime_read_and_"
                "runtime_permit_issuance_v1/runtime_permit_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="RUNTIME_ISSUED_PERMIT",
            observed_value=str((runtime_facts.get("PERMIT_AUDIT") or {}).get("issued")),
            transformation="FRESH_CASE_A_SIZE_AND_OBSERVATION_OR_DENY",
            output_object="PERMIT_OR_DENY_REASONS",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_ISSUANCE_OR_FAIL_CLOSED",
        ),
        _seam(
            producer="submit_productive_flatten_v1",
            field="PRODUCTIVE_FLATTEN_POST",
            source_path=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_gated_submit_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="POST_API_V5_TRADE_ORDER_REDUCE_ONLY_LIMIT",
            observed_value=str(runtime_facts.get("POST_RESULT") or "NOT_ATTEMPTED"),
            transformation="ONE_SHOT_HMAC_POST_NO_RETRY",
            output_object="POST_RESPONSE",
            epistemic_class="FORENSIC_RAW",
            adjudication_status="PROVEN_POST_OR_FAIL_CLOSED",
        ),
        _seam(
            producer="evaluate_canary_flatten_post_action_proof_contract_v1",
            field="LIVE_FLATTEN_PROVABILITY",
            source_path=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "flatten_post_action_proof_contract_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="POST_ACTION_POS_ZERO_LINEAGE",
            observed_value=str(runtime_facts.get("LIVE_FLATTEN_PROVABILITY_PROVEN")),
            transformation="VENUE_ACCEPTED_NOT_COLLAPSED_ONTO_ZERO",
            output_object="FLATTEN_PROVABILITY_ADJUDICATION",
            epistemic_class="INTERPRETATION",
            adjudication_status="PROVEN_SEPARATE_FROM_HTTP_200",
        ),
        _seam(
            producer="adjudicate_gaps_v1",
            field="EARLIEST_UNRESOLVED_DEPENDENCY",
            source_path=(
                "src/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/"
                "gap_adjudication_v1.py"
            ),
            status="current_bound_producer",
            semantic_object="NEXT_AUTHORITY_BOUNDARY",
            observed_value=EARLIEST_UNRESOLVED_DEPENDENCY,
            transformation="HARD_STOP_BEFORE_MERGE",
            output_object="OWNER_MERGE_GO",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_NEXT_NOT_AUTHORIZED",
        ),
        _seam(
            producer="SEND_TIME_POSITION_REOBSERVATION_CASE_B",
            field="TARGET_INSTRUMENT_ID",
            source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
            status="current_bound_scope",
            semantic_object="CANONICAL_INSTRUMENT_SCOPE",
            observed_value=TARGET_INSTRUMENT_ID,
            transformation="SCOPE_PRESERVED_NOT_MUTATED",
            output_object="PERMIT_INSTRUMENT_BINDING",
            epistemic_class="CANONICAL_AUTHORITY",
            adjudication_status="PROVEN_FAIL_CLOSED",
        ),
    )


def lineage_summary_v1(*, runtime_facts: Mapping[str, Any]) -> dict[str, Any]:
    seams = productive_flatten_post_lineage_v1(runtime_facts=runtime_facts)
    counts: dict[str, int] = {}
    proven = 0
    for seam in seams:
        klass = str(seam.get("epistemic_class") or "")
        counts[klass] = counts.get(klass, 0) + 1
        if str(seam.get("adjudication_status") or "").startswith("PROVEN"):
            proven += 1
    return {
        "SEAM_COUNT": len(seams),
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": 0,
        "EPISTEMIC_CLASS_COUNTS": counts,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
