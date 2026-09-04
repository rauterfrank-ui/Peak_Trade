"""Machine-checkable P16 bounded-activation lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.constants_v1 import (
    BOUNDED_ACTIVATION_OWNER_GO_CANONICAL_VALUE,
    BOUNDED_ACTIVATION_PERMIT_KIND_VALUE,
    BOUNDED_ACTIVATION_PURPOSE_VALUE,
    OWNER_GO,
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


BOUNDED_ACTIVATION_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="constants_v1.LIVE_AUTHORIZED",
        field="LIVE_AUTHORIZED",
        source_path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py"),
        status="current_bound_producer",
        semantic_object="STANDING_GLOBAL_LIVE_AUTHORIZED",
        observed_value="false",
        transformation="STANDING_CONSTANT_REMAINS_FALSE",
        output_object="STANDING_LIVE_AUTHORIZED",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_STANDING_FALSE",
    ),
    _seam(
        producer="evaluate_flatten_pre_send_gate_v1",
        field="LIVE_AUTHORIZED_CLAIM",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="INVOCATION_LIVE_AUTHORIZED_CLAIM",
        observed_value="DENY_IF_TRUE_PASS_IF_FALSE",
        transformation="GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_BOUNDED_PERMIT",
        output_object="LIVE_AUTHORIZED_CLAIM_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_NOT_REQUIRED_DENY_IF_TRUE",
    ),
    _seam(
        producer="evaluate_bounded_activation_permit_v1",
        field="BOUNDED_ACTIVATION_PERMIT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_activation_permit_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="BOUNDED_ACTIVATION_PERMIT",
        observed_value=BOUNDED_ACTIVATION_PERMIT_KIND_VALUE,
        transformation="MISSING_EXPIRED_WRONG_BOUND_FORBIDDEN_GO_DENY",
        output_object="BOUNDED_ACTIVATION_PERMIT_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_MECHANISM_RUNTIME_PERMIT_NOT_ISSUED",
    ),
    _seam(
        producer="BoundedActivationPermitV1",
        field="purpose",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_activation_permit_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="BOUNDED_ACTIVATION_PURPOSE",
        observed_value=BOUNDED_ACTIVATION_PURPOSE_VALUE,
        transformation="EXACT_PURPOSE_MATCH_OR_DENY",
        output_object="PERMIT_PURPOSE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_EXPECTED_VALUE_NOT_ACTIVATION",
    ),
    _seam(
        producer="BoundedActivationPermitV1",
        field="owner_go",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_activation_permit_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="BOUNDED_ACTIVATION_OWNER_GO",
        observed_value=BOUNDED_ACTIVATION_OWNER_GO_CANONICAL_VALUE,
        transformation="IMPLEMENTATION_GO_FORBIDDEN_CANONICAL_EXPECTED_VALUE_NOT_ISSUED",
        output_object="PERMIT_OWNER_GO",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_THIS_GO_FORBIDDEN",
    ),
    _seam(
        producer="BoundedActivationPermitV1",
        field="bound_origin_main_sha",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_activation_permit_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PERMIT_ORIGIN_MAIN_BINDING",
        observed_value="sha1_40_hex_must_match_gate_origin_main_sha",
        transformation="MISSING_MALFORMED_STALE_DENY",
        output_object="PERMIT_SHA_BINDING",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="BoundedActivationPermitV1",
        field="instrument_id",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_activation_permit_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PERMIT_INSTRUMENT_BINDING",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="MISMATCH_DENY",
        output_object="PERMIT_INSTRUMENT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="BoundedActivationPermitV1",
        field="not_after_monotonic_ms",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "bounded_activation_permit_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PERMIT_EXPIRY",
        observed_value="evaluation_ms_gt_not_after_denies",
        transformation="EXPIRED_OR_MALFORMED_DENY",
        output_object="PERMIT_EXPIRY_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="GatedProductiveFlattenTransportV1",
        field="network_session_authorized",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_productive_transport_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NETWORK_SESSION_AUTHORIZATION",
        observed_value="false",
        transformation="CLASS_NEVER_SETS_TRUE_DEFAULT_FALSE",
        output_object="PRODUCTIVE_NETWORK_SESSION",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_BOUNDED_PERMIT",
    ),
    _seam(
        producer="evaluate_flatten_execute_authority_v1",
        field="flatten_execute_owner_go",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_execute_authority_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="FLATTEN_EXECUTE_AUTHORITY",
        observed_value=OWNER_GO,
        transformation="THIS_IMPLEMENTATION_GO_FORBIDDEN_AS_FLATTEN_EXECUTE",
        output_object="FLATTEN_EXECUTE_AUTHORITY_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_REMAINS_SEPARATE",
    ),
)


def bounded_activation_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in BOUNDED_ACTIVATION_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = bounded_activation_lineage_v1()
    counts: dict[str, int] = {}
    proven = 0
    not_promoted = 0
    for seam in seams:
        klass = str(seam.get("epistemic_class") or "")
        counts[klass] = counts.get(klass, 0) + 1
        status = str(seam.get("adjudication_status") or "")
        if status.startswith("PROVEN"):
            proven += 1
        if "NOT_ISSUED" in status or "UNAUTHORIZED" in status or "FORBIDDEN" in status:
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
