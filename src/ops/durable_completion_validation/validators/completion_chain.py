"""Completion proof chain cross-slice digest binding validator."""

from __future__ import annotations

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    MASTER_V2_BINDING_TO_COMPLETION_CHAIN_FIELD_NAMES,
    MASTER_V2_DECISION_STATE_DIGEST_BINDING_OWNER,
    classify_master_v2_binding_presence,
    master_v2_completion_chain_binding_is_present,
    master_v2_decision_state_digest_binding_is_present,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    compute_integration_input_digest as compute_pe21_integration_input_digest,
)
from src.ops.durable_completion_validation.identity import sorted_unique, valid_sha256_digest
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult


def _validate_master_v2_completion_chain_digest_binding(context: ValidationContext) -> list[str]:
    """Optional Master-V2 digest binding: absent for legacy ops-only; complete-or-fail when present."""
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    chain = integration_input.completion_proof_chain
    binding = integration_input.master_v2_decision_state_digest_binding
    prefix = "completion_proof_chain.master_v2"
    binding_present = master_v2_decision_state_digest_binding_is_present(binding)
    chain_present = master_v2_completion_chain_binding_is_present(chain)

    if not binding_present and not chain_present:
        return fail_reasons

    if binding_present != chain_present:
        fail_reasons.append(
            f"{prefix}: partial binding forbidden (integration and completion chain must both "
            "provide complete Master-V2 digest references or neither)"
        )
        return fail_reasons

    assert binding is not None
    if binding.binding_owner != MASTER_V2_DECISION_STATE_DIGEST_BINDING_OWNER:
        fail_reasons.append(
            f"{prefix}: binding_owner must be {MASTER_V2_DECISION_STATE_DIGEST_BINDING_OWNER!r}"
        )
    if binding.source_revision != integration_input.source_revision:
        fail_reasons.append(f"{prefix}: source_revision mismatch")

    chain_values = [
        getattr(chain, chain_field)
        for _, chain_field in MASTER_V2_BINDING_TO_COMPLETION_CHAIN_FIELD_NAMES
    ]
    if any(value is None for value in chain_values):
        fail_reasons.append(f"{prefix}: all Master-V2 completion chain reference fields required")
    if any(value is not None for value in chain_values) and any(
        value is None for value in chain_values
    ):
        fail_reasons.append(f"{prefix}: partial Master-V2 completion chain reference forbidden")

    for binding_field, chain_field in MASTER_V2_BINDING_TO_COMPLETION_CHAIN_FIELD_NAMES:
        chain_value = getattr(chain, chain_field)
        binding_value = getattr(binding, binding_field)
        if chain_value != binding_value:
            fail_reasons.append(f"{prefix}: {chain_field} mismatch with {binding_field}")
        if binding_field.endswith("_digest"):
            if not valid_sha256_digest(binding_value):
                fail_reasons.append(
                    f"{prefix}: {binding_field} must be 64-char lowercase sha256 hex"
                )
        elif not binding_value:
            fail_reasons.append(f"{prefix}: {binding_field} required when binding present")

    if (
        classify_master_v2_binding_presence(binding=binding, chain=chain)
        != "MASTER_V2_BINDING_PRESENT"
    ):
        fail_reasons.append(f"{prefix}: binding classification must be MASTER_V2_BINDING_PRESENT")

    return fail_reasons


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
    pe38_proof = integration_input.pe38_readiness_review_integration_proof
    pe33_proof = integration_input.pe33_cross_slice_proof_coherence_proof
    pe33_input = integration_input.pe33_cross_slice_proof_coherence_integration_input
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
        (
            "completion_referenced_pe38_readiness_review_proof_digest",
            chain.completion_referenced_pe38_readiness_review_proof_digest,
        ),
        (
            "completion_referenced_pe33_integration_proof_digest",
            chain.completion_referenced_pe33_integration_proof_digest,
        ),
        (
            "completion_referenced_pe33_integration_input_digest",
            chain.completion_referenced_pe33_integration_input_digest,
        ),
        (
            "completion_referenced_pe33_pe25_slot_digest",
            chain.completion_referenced_pe33_pe25_slot_digest,
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
    if (
        chain.completion_referenced_pe38_readiness_review_proof_digest
        != pe38_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe38_readiness_review_proof_digest mismatch"
        )
    if (
        chain.completion_referenced_pe33_integration_proof_digest
        != pe33_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe33_integration_proof_digest mismatch"
        )
    if (
        chain.completion_referenced_pe33_integration_input_digest
        != pe33_proof.integration_input_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe33_integration_input_digest mismatch"
        )
    pe25_slot_digest = next(
        (slot.proof_digest for slot in pe33_input.proof_slots if slot.slot_id == "pe25"),
        None,
    )
    if pe25_slot_digest is None:
        fail_reasons.append("completion_proof_chain: PE-33 pe25 slot digest unavailable")
    elif chain.completion_referenced_pe33_pe25_slot_digest != pe25_slot_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe33_pe25_slot_digest mismatch"
        )

    fail_reasons.extend(_validate_master_v2_completion_chain_digest_binding(context))

    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))
