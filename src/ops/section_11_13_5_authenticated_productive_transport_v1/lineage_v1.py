"""Machine-checkable AUTHENTICATED_PRODUCTIVE_TRANSPORT lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT,
    PRODUCTIVE_SIGNING_COMPONENT,
)
from src.ops.section_11_13_5_authenticated_productive_transport_v1.constants_v1 import (
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


AUTHENTICATED_PRODUCTIVE_TRANSPORT_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="SEND_TIME_PASS_CASE_B",
        field="SEND_TIME_PASS_18_19_21_24",
        source_path=("src/ops/section_11_13_5_send_time_pass_18_19_21_24_v1/contract_v1.py"),
        status="current_bound_predecessor",
        semantic_object="STP_PASS_OFFLINE_CONTRACT",
        observed_value="PASS_OFFLINE_CONTRACT",
        transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
        output_object="STP_CLOSED_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_PREDECESSOR_AUTHENTICATED_PRODUCTIVE_TRANSPORT_WAS_NEXT_RESIDUAL",
    ),
    _seam(
        producer="Z2CL_OFFLINE_PRODUCTIVE_URLLIB",
        field="PRODUCTIVE_URLLIB_SEND_IMPLEMENTED",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_productive_transport_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="UNSIGNED_GATED_PRODUCTIVE_FLATTEN_TRANSPORT",
        observed_value="OFFLINE_IMPLEMENTED_RUNTIME_UNAUTHORIZED_AND_UNAUTHENTICATED",
        transformation="UNSIGNED_PATH_PRESERVED_NOT_COUNTED_AS_AUTHENTICATED",
        output_object="GATED_PRODUCTIVE_FLATTEN_TRANSPORT_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNSIGNED_PATH_NOT_AUTHENTICATED_TRANSPORT",
    ),
    _seam(
        producer="build_okx_live_canary_auth_headers_v1",
        field="PRODUCTIVE_SIGNING_COMPONENT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/okx_live_canary_signer_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="EXISTING_HMAC_SIGNER_REUSE",
        observed_value=PRODUCTIVE_SIGNING_COMPONENT,
        transformation="REUSE_EXISTING_SIGNER_NO_NEW_ONTOLOGY",
        output_object="AUTHENTICATED_PRODUCTIVE_HEADER_CONTRACT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_WIRING_RUNTIME_SECRET_NOT_USED",
    ),
    _seam(
        producer="construct_okx_signing_input_v1",
        field="prehash",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "authenticated_productive_transport_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="OKX_HMAC_SIGNING_INPUT",
        observed_value="TIMESTAMP_METHOD_PATH_BODY_NO_SECRET",
        transformation="DETERMINISTIC_PREHASH_WITHOUT_SECRET",
        output_object="OKX_SIGNING_INPUT_V1",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OFFLINE_SIGNING_INPUT_SECRET_ABSENT",
    ),
    _seam(
        producer="evaluate_authenticated_productive_transport_v1",
        field="claimed_remaining_after_authenticated_productive_transport",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "authenticated_productive_transport_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT",
        observed_value=";".join(NAMED_REMAINING_AFTER_AUTHENTICATED_PRODUCTIVE_TRANSPORT),
        transformation="EXACT_SET_MATCH_OR_DENY",
        output_object="AUTHENTICATED_PRODUCTIVE_TRANSPORT_REMAINING_HIGHER_AUTHORITY_SET",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED_NOT_CLOSED_BY_AUTHENTICATED_PRODUCTIVE_TRANSPORT",
    ),
    _seam(
        producer="evaluate_flatten_execute_authority_v1",
        field="owner_go",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "flatten_execute_authority_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="FLATTEN_EXECUTE_OWNER_GO",
        observed_value="IMPLEMENTATION_GO_FORBIDDEN",
        transformation="APT_GO_FORBIDDEN_AS_EXECUTE",
        output_object="FLATTEN_EXECUTE_REMAINS_SEPARATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_AUTHENTICATED_PRODUCTIVE_TRANSPORT_CONTRACT",
    ),
    _seam(
        producer="AuthenticatedGatedProductiveFlattenTransportV1",
        field="network_session_authorized",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "authenticated_productive_transport_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="NETWORK_SESSION_AUTHORIZATION",
        observed_value="false",
        transformation="CLASS_NEVER_SETS_TRUE_DEFAULT_FALSE",
        output_object="PRODUCTIVE_NETWORK_SESSION",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_UNAUTHORIZED_DISTINCT_FROM_AUTHENTICATED_PRODUCTIVE_TRANSPORT_CONTRACT",
    ),
    _seam(
        producer="adjudicate_prerequisite_08_window_v1",
        field="EARLIEST_UNRESOLVED_DEPENDENCY",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "prerequisite_08_fresh_position_observation_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="WINDOW_EARLIEST_UNRESOLVED_DEPENDENCY",
        observed_value=EARLIEST_UNRESOLVED_DEPENDENCY,
        transformation="AUTHENTICATED_PRODUCTIVE_TRANSPORT_CLOSED_CLUSTER_REMAINDER_NEXT",
        output_object="SEND_TIME_POSITION_REOBSERVATION",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_NEXT_NOT_RUNTIME_AUTHORIZED",
    ),
    _seam(
        producer="evaluate_flatten_pre_send_gate_v1",
        field="AUTHENTICATED_PRODUCTIVE_TRANSPORT",
        source_path=(
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_pre_send_gate_v1.py"
        ),
        status="current_bound_producer",
        semantic_object="PRE_SEND_AUTHENTICATED_PRODUCTIVE_TRANSPORT_GATE",
        observed_value="DENY_IF_UNSIGNED_COUNTED_AS_AUTHENTICATED_OR_RUNTIME_CLAIM",
        transformation="NAMED_GATE_INDEPENDENT_OF_GLOBAL_LIVE_AUTHORIZED",
        output_object="AUTHENTICATED_PRODUCTIVE_TRANSPORT_GATE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_MECHANISM_RUNTIME_AUTHORITY_NOT_PERFORMED",
    ),
    _seam(
        producer="SEND_TIME_PASS_CASE_B",
        field="TARGET_INSTRUMENT_ID",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_scope",
        semantic_object="CANONICAL_INSTRUMENT_SCOPE",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="SCOPE_PRESERVED_NOT_MUTATED",
        output_object="AUTHENTICATED_PRODUCTIVE_TRANSPORT_INSTRUMENT_SCOPE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
)


def authenticated_productive_transport_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in AUTHENTICATED_PRODUCTIVE_TRANSPORT_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = authenticated_productive_transport_lineage_v1()
    counts: dict[str, int] = {}
    proven = 0
    not_promoted = 0
    for seam in seams:
        klass = str(seam.get("epistemic_class") or "")
        counts[klass] = counts.get(klass, 0) + 1
        status = str(seam.get("adjudication_status") or "")
        if status.startswith("PROVEN"):
            proven += 1
        if (
            "NOT_USED" in status
            or "UNAUTHORIZED" in status
            or "NOT_PERFORMED" in status
            or "HISTORICAL" in status
            or "SECRET_NOT_USED" in status
            or "SECRET_ABSENT" in status
        ):
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
