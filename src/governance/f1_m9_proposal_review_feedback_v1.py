"""Persist the original M9 review decision for an offline research caller."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    RISK_CONSTRAINTS_REF,
    SURFACE_ID,
    compute_m9_reproducibility_digest_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    ADMISSION_DENIED,
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
    validate_optimization_proposal_governance_ingress_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

SCHEMA_VERSION = "f1_m9_proposal_review_feedback_v1"


@dataclass(frozen=True, slots=True)
class F1M9ProposalReviewFeedbackV1:
    ingress_digest: str
    review_policy_digest: str
    proposal_identity_digest: str
    experiment_id: str
    candidate_ref: str
    admission_status: str
    reason_codes: tuple[str, ...]
    feedback_digest: str


def _bound_ingress(ingress: Mapping[str, Any]) -> dict[str, Any]:
    # Snapshot nested values before the owner and the feedback writer read them.
    payload = json.loads(deterministic_json_dumps(dict(ingress)))
    validate_optimization_proposal_governance_ingress_v1(payload)
    digest_body = {key: value for key, value in payload.items() if key != "ingress_digest"}
    if compute_content_sha256(digest_body) != payload["ingress_digest"]:
        raise ValueError("M9_REVIEW_INGRESS_DIGEST_MISMATCH")
    if payload["optimization_surface_id"] != SURFACE_ID:
        raise ValueError("M9_REVIEW_SURFACE_MISMATCH")
    if any(
        payload[key] != RISK_CONSTRAINTS_REF
        for key in ("risk_constraints_ref", "governance_risk_constraints_ref")
    ):
        raise ValueError("M9_REVIEW_RISK_REF_MISMATCH")
    for key in ("experiment_id", "candidate_ref", "optimization_evidence_record_id"):
        if not isinstance(payload[key], str) or not payload[key]:
            raise ValueError(f"M9_REVIEW_IDENTITY_MISSING:{key}")
    if not is_valid_sha256_hex(payload["optimization_provenance"].get("identity_digest")):
        raise ValueError("M9_REVIEW_PROPOSAL_IDENTITY_INVALID")
    return payload


def _lineage(ingress: Mapping[str, Any], policy_digest: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_id": SURFACE_ID,
        "ingress_digest": ingress["ingress_digest"],
        "review_policy_digest": policy_digest,
        "proposal_identity_digest": ingress["optimization_provenance"]["identity_digest"],
        "experiment_id": ingress["experiment_id"],
        "candidate_ref": ingress["candidate_ref"],
        "optimization_evidence_record_id": ingress["optimization_evidence_record_id"],
        "optimization_evidence_content_hash": ingress["optimization_evidence_content_hash"],
        "authority": "NONE",
    }


def _feedback_path(store_root: Path, lineage: Mapping[str, Any]) -> Path:
    return store_root / lineage["ingress_digest"] / f"{lineage['review_policy_digest']}.json"


def read_f1_m9_proposal_review_feedback_v1(
    *,
    store_root: Path,
    ingress: Mapping[str, Any],
    review_policy_digest: str,
    expected_feedback_digest: str,
) -> F1M9ProposalReviewFeedbackV1:
    """Read the historical review response against the caller's original proposal."""
    if not is_valid_sha256_hex(review_policy_digest):
        raise ValueError("M9_REVIEW_POLICY_DIGEST_INVALID")
    if not is_valid_sha256_hex(expected_feedback_digest):
        raise ValueError("M9_REVIEW_EXPECTED_FEEDBACK_DIGEST_INVALID")
    lineage = _lineage(_bound_ingress(ingress), review_policy_digest)
    payload = json.loads(_feedback_path(store_root, lineage).read_bytes())
    if not isinstance(payload, dict) or payload.keys() != lineage.keys() | {
        "admission_status",
        "reason_codes",
        "feedback_digest",
    }:
        raise ValueError("M9_REVIEW_FEEDBACK_SCHEMA_INVALID")
    if any(payload[key] != value for key, value in lineage.items()):
        raise ValueError("M9_REVIEW_FEEDBACK_LINEAGE_MISMATCH")
    feedback_digest = payload.pop("feedback_digest")
    if (
        compute_content_sha256(payload) != feedback_digest
        or feedback_digest != expected_feedback_digest
    ):
        raise ValueError("M9_REVIEW_FEEDBACK_DIGEST_MISMATCH")
    status = payload["admission_status"]
    reasons = payload["reason_codes"]
    if (
        status not in (ADMISSION_ADMITTED, ADMISSION_DENIED)
        or not isinstance(reasons, list)
        or not reasons
        or any(not isinstance(reason, str) or not reason for reason in reasons)
    ):
        raise ValueError("M9_REVIEW_FEEDBACK_DECISION_INVALID")
    return F1M9ProposalReviewFeedbackV1(
        ingress_digest=payload["ingress_digest"],
        review_policy_digest=review_policy_digest,
        proposal_identity_digest=payload["proposal_identity_digest"],
        experiment_id=payload["experiment_id"],
        candidate_ref=payload["candidate_ref"],
        admission_status=status,
        reason_codes=tuple(reasons),
        feedback_digest=feedback_digest,
    )


def evaluate_and_store_f1_m9_proposal_review_feedback_v1(
    *, store_root: Path, ingress: Mapping[str, Any]
) -> F1M9ProposalReviewFeedbackV1:
    """Run the existing proposal-only reviewer and publish its exact response."""
    ingress = _bound_ingress(ingress)
    policy_digest = compute_m9_reproducibility_digest_v1()
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    if (
        result.ingress_digest != ingress["ingress_digest"]
        or result.admission_status not in (ADMISSION_ADMITTED, ADMISSION_DENIED)
        or result.promotion_authority != "NONE"
        or result.productive_apply_authority != "NONE"
        or compute_m9_reproducibility_digest_v1() != policy_digest
    ):
        raise ValueError("M9_REVIEW_OWNER_RESULT_UNBOUND")

    lineage = _lineage(ingress, policy_digest)
    payload = {
        **lineage,
        "admission_status": result.admission_status,
        "reason_codes": list(result.reason_codes),
    }
    payload["feedback_digest"] = compute_content_sha256(payload)
    dest = _feedback_path(store_root, lineage)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=dest.parent, prefix=".review-", delete=False) as stream:
        staging = Path(stream.name)
        try:
            stream.write((deterministic_json_dumps(payload) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
            try:
                os.link(staging, dest)
            except FileExistsError:
                pass
        finally:
            staging.unlink()
    return read_f1_m9_proposal_review_feedback_v1(
        store_root=store_root,
        ingress=ingress,
        review_policy_digest=policy_digest,
        expected_feedback_digest=payload["feedback_digest"],
    )
