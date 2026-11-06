"""Offline EXECUTION_PREREQUISITE_08 flatten-dependency cluster contract.

Adjudicates the post-Z2CP unresolved Class-D / send-time cluster from
prerequisite 08 forward. Evaluates caller-supplied snapshots only.
Never GETs, never POSTs, never invents HMAC, never claims 08 PROVEN,
and never authorizes flatten, live, testnet, or canary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)

EARLIEST_UNRESOLVED_DEPENDENCY = "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN"
Z2CN_COMMITTED_BODY_SHA256 = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"
Z2CN_CLASSIFICATION = TARGET_POSITION_NOT_OBSERVED
Z2CN_IS_NOT_CURRENT_PREREQUISITE_08_PROOF = True
LAST_CANONICALLY_CLOSED_11_13_5_SLICE = "SECTION_11_13_5_Z2CN"
Z2CP_CANONICALLY_CLOSED = False
SEND_TIME_PASS_18_19_21_24 = "UNPROVEN"
CLASS_D_CONSUMED = False
Z2AP_CONSUMED = False
EXECUTION_READY = False
LIVE_FLATTEN_PROVABILITY = "UNPROVEN"
PREREQUISITE_23_CURRENT_STATUS = "DEFINED_CHOICE_B"
PREREQUISITE_16_CURRENT_STATUS = "OFFLINE_IMPLEMENTED_RUNTIME_UNAUTHORIZED_STILL_BLOCKING"
PREREQUISITE_25_CURRENT_STATUS = (
    "FAIL_FLATTEN_EXECUTE_OWNER_GO_AND_AUTHENTICATED_POST_REMAIN_SEPARATE"
)
AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS = "REMAINS_UNRESOLVED"
POS_SIDE_STATUS = "UNPROVEN"
UNIT_CHAIN_VERDICT = "PASSTHROUGH_POS_TO_SZ_UNIT_IDENTITY_UNPROVEN"
EARLIER_THAN_08_UNRESOLVED_IN_NUMBERED_MATRIX = False

UNRESOLVED_CLUSTER: tuple[str, ...] = (
    "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC",
    "EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT",
    "EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE",
    "EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION",
    "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
    "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
    "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
    "SEND_TIME_PASS_18_19_21_24",
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT",
)

RUNTIME_FACT_REQUIRED_ITEMS: tuple[str, ...] = (
    "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC",
    "EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION",
    "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION",
)

HIGHER_AUTHORITY_BLOCKED_ITEMS: tuple[str, ...] = (
    "EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT",
    "EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE",
    "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED",
    "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED",
    "SEND_TIME_PASS_18_19_21_24",
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT",
)

OFFLINE_CLOSABLE_ITEMS: tuple[str, ...] = (
    "TARGET_POSITION_STATE_PRE_SEND_GATE",
    "CLUSTER_DEPENDENT_09_12_20_CANNOT_PASS_WITHOUT_08_NONZERO",
    "Z2CN_COMMITTED_SNAPSHOT_IS_NOT_CURRENT_08_PROOF",
    "THIS_OWNER_GO_FORBIDDEN_AS_FLATTEN_EXECUTE",
)

OBSOLETE_OR_SUPERSEDED_AS_CURRENT_UNRESOLVED: tuple[str, ...] = (
    "EXECUTION_PREREQUISITE_23_READBACK_SUCCESS_PREDICATE_DEFINED_BEFORE_POST",
)

REASON_DEPENDENT_BLOCKED = "DEPENDENT_PREREQUISITE_BLOCKED_BY_08"


class LiveCanaryExecutionPrerequisite08ClusterError(RuntimeError):
    """Fail-closed 08-cluster contract violation."""


@dataclass(frozen=True)
class ExecutionPrerequisite08ClusterVerdictV1:
    """Offline cluster classification. Not flatten authorization."""

    instrument_id: str
    target_position_state: str
    target_position_reason: str
    prerequisite_08_status: str
    prerequisite_08_proven: bool
    prerequisite_09_status: str
    prerequisite_12_status: str
    prerequisite_20_status: str
    earliest_unresolved_dependency: str
    z2cn_snapshot_is_current_08_proof: bool
    class_d_consumed: bool
    z2ap_consumed: bool
    execution_ready: bool
    live_flatten_provability: str
    send_time_pass_18_19_21_24: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "target_position_state": self.target_position_state,
            "target_position_reason": self.target_position_reason,
            "prerequisite_08_status": self.prerequisite_08_status,
            "prerequisite_08_proven": self.prerequisite_08_proven,
            "prerequisite_09_status": self.prerequisite_09_status,
            "prerequisite_12_status": self.prerequisite_12_status,
            "prerequisite_20_status": self.prerequisite_20_status,
            "earliest_unresolved_dependency": self.earliest_unresolved_dependency,
            "z2cn_snapshot_is_current_08_proof": self.z2cn_snapshot_is_current_08_proof,
            "class_d_consumed": self.class_d_consumed,
            "z2ap_consumed": self.z2ap_consumed,
            "execution_ready": self.execution_ready,
            "live_flatten_provability": self.live_flatten_provability,
            "send_time_pass_18_19_21_24": self.send_time_pass_18_19_21_24,
        }


def _08_status_for_state(state: str) -> str:
    if state == TARGET_POSITION_NONZERO_PROVEN:
        return "OBSERVED_NONZERO_THIS_PAYLOAD_NOT_SEND_TIME_PROVEN"
    if state == TARGET_POSITION_ZERO_PROVEN:
        return "UNRESOLVED_TARGET_ZERO_THIS_PAYLOAD"
    if state == TARGET_POSITION_UNKNOWN:
        return "UNRESOLVED_TARGET_UNKNOWN_THIS_PAYLOAD"
    return "UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW"


def evaluate_execution_prerequisite_08_cluster_v1(
    *,
    positions_payload: Mapping[str, Any] | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    claimed_body_sha256: str | None = None,
) -> ExecutionPrerequisite08ClusterVerdictV1:
    """Classify 08 and dependents for one caller-supplied envelope.

    A nonzero fixture payload is not a productive 08 proof and does not
    close send-time PASS, Class D, or flatten.
    """
    classified = classify_target_position_state_v1(
        positions_payload=positions_payload,
        instrument_id=instrument_id,
    )
    proven = classified.state == TARGET_POSITION_NONZERO_PROVEN
    status_08 = _08_status_for_state(classified.state)
    if proven:
        dep_status = "OFFLINE_DERIVABLE_ONLY_IF_08_NONZERO_SEND_TIME_UNPROVEN"
    else:
        dep_status = REASON_DEPENDENT_BLOCKED
    claimed = str(claimed_body_sha256 or "").strip().lower()
    z2cn_claimed_as_08 = claimed == Z2CN_COMMITTED_BODY_SHA256
    if z2cn_claimed_as_08 and proven:
        raise LiveCanaryExecutionPrerequisite08ClusterError(
            "Z2CN_EMPTY_SHA_CANNOT_BE_NONZERO_08_PROOF"
        )
    return ExecutionPrerequisite08ClusterVerdictV1(
        instrument_id=classified.instrument_id,
        target_position_state=classified.state,
        target_position_reason=classified.reason,
        prerequisite_08_status=status_08,
        prerequisite_08_proven=False,
        prerequisite_09_status=dep_status,
        prerequisite_12_status=dep_status,
        prerequisite_20_status=dep_status,
        earliest_unresolved_dependency=EARLIEST_UNRESOLVED_DEPENDENCY,
        z2cn_snapshot_is_current_08_proof=False,
        class_d_consumed=CLASS_D_CONSUMED,
        z2ap_consumed=Z2AP_CONSUMED,
        execution_ready=EXECUTION_READY,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY,
        send_time_pass_18_19_21_24=SEND_TIME_PASS_18_19_21_24,
    )


def reject_z2cn_snapshot_as_current_08_proof_v1(*, body_sha256: str | None) -> str:
    """Committed Z2CN empty envelope is not current 08 proof."""
    claimed = str(body_sha256 or "").strip().lower()
    if claimed == Z2CN_COMMITTED_BODY_SHA256:
        return "Z2CN_COMMITTED_SNAPSHOT_IS_NOT_CURRENT_08_PROOF"
    return "BODY_SHA_NOT_Z2CN_COMMITTED_EMPTY_ENVELOPE"


def dependent_prerequisites_blocked_unless_08_nonzero_v1(state: str) -> bool:
    """09/12/20 cannot PASS while 08 is not an observed nonzero row."""
    return state != TARGET_POSITION_NONZERO_PROVEN
