"""Offline deterministic promotion eligibility controller v0.

Evaluates PromotionPolicy against a ValidationEvidencePack. Does not activate
promotion, deployment, or execution authority. Cannot change policy.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    PROMOTION_AUTHORITY_ACTIVATION,
    PROMOTION_AUTHORITY_EFFECT,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    VALIDATION_GATE_IDS_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    all_named_gates_pass_v0,
    hard_gate_failures_v0,
    validate_candidate_artifact_v0,
    validate_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.promotion_records_v0 import (
    build_promotion_eligibility_record_v0,
    validate_promotion_policy_v0,
)

PROMOTION_CONTROLLER_CAN_CHANGE_OWN_POLICY: Final[bool] = False
PROMOTION_ELIGIBLE_EQUALS_DEPLOYMENT_AUTHORIZED: Final[bool] = False


def evaluate_promotion_eligibility_v0(
    *,
    policy: Mapping[str, Any],
    candidate: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
    eligibility_record_id: str,
    event_time_utc: str,
    correlation_id: str,
    producer_id: str,
    causal_parent_ids: list[str] | None = None,
    cycle_id: str | None = None,
    code_sha: str = "UNKNOWN",
    config_hash: str = "UNKNOWN",
    evidence_hash: str = "UNKNOWN",
    evidence_source_refs: list[str] | None = None,
    authority_owner: str = "UNKNOWN",
) -> MappingProxyType[str, Any]:
    if PROMOTION_AUTHORITY_ACTIVATION or PROMOTION_AUTHORITY_EFFECT != "NONE":
        raise DdoValidationError("PROMOTION_AUTHORITY_ACTIVATION_MUST_REMAIN_FALSE")
    policy_rec = validate_promotion_policy_v0(policy)
    candidate_rec = validate_candidate_artifact_v0(candidate)
    pack = validate_validation_evidence_pack_v0(evidence_pack)
    if pack["candidate_artifact_ref"] != candidate_rec["record_id"]:
        raise DdoValidationError("ELIGIBILITY_PACK_CANDIDATE_MISMATCH")
    promotion_class = str(candidate_rec["promotion_class"])
    failed = [gate for gate in VALIDATION_GATE_IDS_V0 if pack["gates"][gate] != "PASS"]
    class_allowed = promotion_class in policy_rec["allowed_promotion_classes"]
    hard_failed = hard_gate_failures_v0(pack["gates"])
    if candidate_rec["rejected"]:
        failed = [*failed, "candidate_rejected"]
    if not class_allowed:
        failed = [*failed, "promotion_class_not_allowed"]
    eligible = (
        all_named_gates_pass_v0(pack["gates"])
        and class_allowed
        and not candidate_rec["rejected"]
        and not hard_failed
    )
    if (
        pack["gates"]["safety_regression_pass"] != "PASS"
        and pack["gates"]["economic_policy_pass"] == "PASS"
    ):
        eligible = False
        if "safety_regression_pass" not in failed:
            failed.append("safety_regression_pass")
    return build_promotion_eligibility_record_v0(
        {
            "schema_name": "promotion_eligibility_record",
            "schema_version": "promotion_eligibility_record_v0",
            "record_id": eligibility_record_id,
            "event_time_utc": event_time_utc,
            "correlation_id": correlation_id,
            "cycle_id": cycle_id,
            "causal_parent_ids": causal_parent_ids
            or [
                candidate_rec["record_id"],
                pack["record_id"],
                policy_rec["record_id"],
            ],
            "producer_id": producer_id,
            "authority_owner": authority_owner,
            "code_sha": code_sha,
            "config_hash": config_hash,
            "evidence_hash": evidence_hash,
            "evidence_source_refs": evidence_source_refs or [],
            "candidate_artifact_ref": candidate_rec["record_id"],
            "validation_evidence_pack_ref": pack["record_id"],
            "promotion_policy_ref": policy_rec["record_id"],
            "promotion_class": promotion_class,
            "eligible": eligible,
            "failed_gates": failed,
            "deployment_authorized": False,
            "execution_authorized": False,
        }
    )
