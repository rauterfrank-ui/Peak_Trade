"""Completion proof chain cross-slice digest binding validator."""

from __future__ import annotations

from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    compute_integration_input_digest as compute_pe21_integration_input_digest,
)
from src.ops.durable_completion_validation.identity import sorted_unique, valid_sha256_digest
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult


def validate_completion_proof_chain_binding(context: ValidationContext) -> ValidationResult:
    """Graph completion_chain node: cross-slice completion proof chain digest coherence."""
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    chain = integration_input.completion_proof_chain
    pe31_proof = integration_input.pe31_reconciliation_review_integration_proof
    pe22_proof = integration_input.pe22_risk_killswitch_flatten_proof
    pe23_proof = integration_input.pe23_capital_slot_ratchet_release_proof
    pe24_proof = integration_input.pe24_pilot_envelope_lifecycle_proof
    pe35_proof = integration_input.pe35_handoff_recovery_boundary_proof
    pe37_proof = integration_input.pe37_traceability_proof
    pe25_proof = integration_input.pe25_operator_closure_proof
    pe21_proof = integration_input.pe21_proof
    pe31_pe21_proof = integration_input.pe31_reconciliation_review_integration_input.pe21_reconciliation_primary_evidence_integration_proof
    wallclock_proof = integration_input.wallclock_evidence_proof
    checksum_by_path = {
        entry.relative_path: entry.digest for entry in integration_input.artifact_checksums
    }
    canonical_wallclock_evidence_digest = checksum_by_path.get(wallclock_proof.artifact_filename)
    pe21_input_digest = compute_pe21_integration_input_digest(
        integration_input.pe21_integration_input
    )

    digest_fields = (
        ("completion_referenced_pe31_proof_digest", chain.completion_referenced_pe31_proof_digest),
        ("completion_referenced_pe22_proof_digest", chain.completion_referenced_pe22_proof_digest),
        ("completion_referenced_pe23_proof_digest", chain.completion_referenced_pe23_proof_digest),
        ("completion_referenced_pe24_proof_digest", chain.completion_referenced_pe24_proof_digest),
        (
            "completion_referenced_pe35_boundary_result_digest",
            chain.completion_referenced_pe35_boundary_result_digest,
        ),
        (
            "completion_referenced_pe37_boundary_result_digest",
            chain.completion_referenced_pe37_boundary_result_digest,
        ),
        ("pe37_traceability_identity", chain.pe37_traceability_identity),
        (
            "completion_referenced_pe25_closure_result_digest",
            chain.completion_referenced_pe25_closure_result_digest,
        ),
        ("pe25_closure_input_digest", chain.pe25_closure_input_digest),
        (
            "closure_referenced_admission_proof_digest",
            chain.closure_referenced_admission_proof_digest,
        ),
        (
            "pe31_referenced_pe21_integration_proof_digest",
            chain.pe31_referenced_pe21_integration_proof_digest,
        ),
        (
            "completion_referenced_pe21_integration_proof_digest",
            chain.completion_referenced_pe21_integration_proof_digest,
        ),
        ("shared_pe21_integration_input_digest", chain.shared_pe21_integration_input_digest),
        ("shared_traceability_identity", chain.shared_traceability_identity),
        (
            "completion_referenced_wallclock_evidence_digest",
            chain.completion_referenced_wallclock_evidence_digest,
        ),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"completion_proof_chain: {field_name} required")
        elif not valid_sha256_digest(value):
            fail_reasons.append(
                f"completion_proof_chain: {field_name} must be 64-char lowercase sha256 hex"
            )

    if chain.completion_referenced_pe31_proof_digest != pe31_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe31_proof_digest mismatch"
        )
    if chain.completion_referenced_pe22_proof_digest != pe22_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe22_proof_digest mismatch"
        )
    if chain.completion_referenced_pe23_proof_digest != pe23_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe23_proof_digest mismatch"
        )
    if chain.completion_referenced_pe24_proof_digest != pe24_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe24_proof_digest mismatch"
        )
    if chain.completion_referenced_pe35_boundary_result_digest != pe35_proof.boundary_result_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe35_boundary_result_digest mismatch"
        )
    if chain.completion_referenced_pe37_boundary_result_digest != pe37_proof.boundary_result_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe37_boundary_result_digest mismatch"
        )
    if chain.pe37_traceability_identity != pe37_proof.traceability_identity:
        fail_reasons.append("completion_proof_chain: pe37_traceability_identity mismatch")
    if chain.completion_referenced_pe25_closure_result_digest != pe25_proof.closure_result_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe25_closure_result_digest mismatch"
        )
    if chain.pe25_closure_input_digest != pe25_proof.closure_input_digest:
        fail_reasons.append("completion_proof_chain: pe25_closure_input_digest mismatch")
    if (
        chain.closure_referenced_admission_proof_digest
        != pe25_proof.admission_integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: closure_referenced_admission_proof_digest mismatch"
        )
    if (
        chain.pe31_referenced_pe21_integration_proof_digest
        != pe31_pe21_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: pe31_referenced_pe21_integration_proof_digest mismatch"
        )
    if (
        chain.completion_referenced_pe21_integration_proof_digest
        != pe21_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe21_integration_proof_digest mismatch"
        )
    if chain.shared_pe21_integration_input_digest != pe21_input_digest:
        fail_reasons.append("completion_proof_chain: shared_pe21_integration_input_digest mismatch")
    if chain.shared_traceability_identity != integration_input.durable_run_root.run_root_digest:
        fail_reasons.append("completion_proof_chain: shared_traceability_identity mismatch")
    if canonical_wallclock_evidence_digest is None:
        fail_reasons.append(
            "completion_proof_chain: wallclock evidence artifact digest unavailable"
        )
    elif (
        chain.completion_referenced_wallclock_evidence_digest != canonical_wallclock_evidence_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_wallclock_evidence_digest mismatch"
        )

    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))
