"""Wallclock evidence semantic and digest binding validator."""

from __future__ import annotations

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    WALLCLOCK_EVIDENCE_CONTRACT_OWNER,
)
from src.ops.durable_completion_validation.identity import sorted_unique, valid_sha256_digest
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult
from src.ops.testnet_wallclock_duration_evidence_contract_v0 import (
    REQUIRED_WALLCLOCK_FIELD_NAMES,
    evaluate_wallclock_duration_evidence,
)
from src.ops.wallclock_session_evidence_v0 import (
    WALLCLOCK_EVIDENCE_FILENAME,
    evaluate_wallclock_evidence_fields,
)


def validate_wallclock_proof_binding(context: ValidationContext) -> ValidationResult:
    """Graph wallclock node: canonical wallclock semantic proof binding with digest coherence."""
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    proof = integration_input.wallclock_evidence_proof
    chain = integration_input.completion_proof_chain
    source_revision = integration_input.source_revision

    if proof.wallclock_evidence_owner != WALLCLOCK_EVIDENCE_CONTRACT_OWNER:
        fail_reasons.append(
            "wallclock_proof: wallclock_evidence_owner must be "
            f"{WALLCLOCK_EVIDENCE_CONTRACT_OWNER!r}"
        )
    if proof.source_revision != source_revision:
        fail_reasons.append("wallclock_proof: source_revision mismatch")
    if proof.artifact_filename != WALLCLOCK_EVIDENCE_FILENAME:
        fail_reasons.append(
            f"wallclock_proof: artifact_filename must be {WALLCLOCK_EVIDENCE_FILENAME!r}"
        )

    checksum_by_path = {
        entry.relative_path: entry.digest for entry in integration_input.artifact_checksums
    }
    if WALLCLOCK_EVIDENCE_FILENAME not in checksum_by_path:
        fail_reasons.append(
            "wallclock_proof: wallclock evidence path binding required: "
            f"{WALLCLOCK_EVIDENCE_FILENAME!r}"
        )

    evidence = proof.wallclock_evidence
    if not isinstance(evidence, dict):
        fail_reasons.append("wallclock_proof: wallclock_evidence must be a dict")
        return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))

    missing_fields = sorted(
        field for field in REQUIRED_WALLCLOCK_FIELD_NAMES if field not in evidence
    )
    if missing_fields:
        fail_reasons.append(f"wallclock_proof: missing required fields: {missing_fields}")

    field_evaluation = evaluate_wallclock_evidence_fields(evidence)
    duration_evaluation = evaluate_wallclock_duration_evidence(evidence)
    if not field_evaluation.get("duration_evidence_valid"):
        fail_reasons.append(
            f"wallclock_proof: field validation failed: {field_evaluation.get('fail_reasons', [])}"
        )
    if not duration_evaluation.get("duration_evidence_valid"):
        fail_reasons.append(
            "wallclock_proof: semantic validation failed: "
            f"{duration_evaluation.get('fail_reasons', [])}"
        )

    if proof.duration_evidence_valid is not True:
        fail_reasons.append("wallclock_proof: duration_evidence_valid must be true")
    if proof.duration_proven is not True:
        fail_reasons.append("wallclock_proof: duration_proven must be true")

    canonical_duration_valid = bool(duration_evaluation.get("duration_evidence_valid"))
    canonical_duration_proven = bool(duration_evaluation.get("duration_proven"))
    if proof.duration_evidence_valid != canonical_duration_valid:
        fail_reasons.append(
            "wallclock_proof: duration_evidence_valid drift from canonical evaluation"
        )
    if proof.duration_proven != canonical_duration_proven:
        fail_reasons.append("wallclock_proof: duration_proven drift from canonical evaluation")

    canonical_wallclock_evidence_digest = checksum_by_path.get(WALLCLOCK_EVIDENCE_FILENAME)
    chain_wallclock_digest = chain.completion_referenced_wallclock_evidence_digest

    if not chain_wallclock_digest:
        fail_reasons.append(
            "wallclock_proof: completion_referenced_wallclock_evidence_digest required"
        )
    elif not valid_sha256_digest(chain_wallclock_digest):
        fail_reasons.append(
            "wallclock_proof: completion_referenced_wallclock_evidence_digest must be "
            "64-char lowercase sha256 hex"
        )

    if canonical_wallclock_evidence_digest is None:
        fail_reasons.append("wallclock_proof: wallclock evidence artifact digest unavailable")
    elif not valid_sha256_digest(canonical_wallclock_evidence_digest):
        fail_reasons.append(
            "wallclock_proof: wallclock evidence artifact digest must be "
            "64-char lowercase sha256 hex"
        )

    if (
        canonical_wallclock_evidence_digest is not None
        and chain_wallclock_digest
        and chain_wallclock_digest != canonical_wallclock_evidence_digest
    ):
        fail_reasons.append(
            "wallclock_proof: completion_referenced_wallclock_evidence_digest mismatch"
        )

    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))
