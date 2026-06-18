"""PE-25 operator closure lifecycle proof validator."""

from __future__ import annotations

from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_INTEGRATION_OWNER,
    compute_closure_input_digest as compute_pe25_closure_input_digest,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
)
from src.ops.durable_completion_validation.identity import valid_sha256_digest
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult


def _compute_completion_identity_digest(integration_input):
    from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
        compute_completion_identity_digest,
    )

    durable_root = integration_input.durable_run_root
    return compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=integration_input.manifest_proof.manifest_digest,
        source_revision=integration_input.source_revision,
    )


def validate_pe25_operator_closure_proof(context: ValidationContext) -> ValidationResult:
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    pe25_result = context.pe25_result or {}
    admission_result = context.admission_result or {}
    proof = integration_input.pe25_operator_closure_proof
    pe25_input = integration_input.pe25_closure_integration_input
    pe37_proof = integration_input.pe37_traceability_proof
    pe35_proof = integration_input.pe35_handoff_recovery_boundary_proof
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = _compute_completion_identity_digest(integration_input)
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    pe34_handoff = pe35_input.pe34_handoff
    pe22_proof = integration_input.pe22_risk_killswitch_flatten_proof
    pe23_proof = integration_input.pe23_capital_slot_ratchet_release_proof
    pe24_proof = integration_input.pe24_pilot_envelope_lifecycle_proof

    from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
        ALLOWED_PROOF_LIFECYCLE_STATES,
        INVALID_PROOF_LIFECYCLE_STATES,
    )

    pe25_lifecycle = integration_input.pe25_proof_lifecycle
    if pe25_lifecycle.lifecycle_state not in ALLOWED_PROOF_LIFECYCLE_STATES:
        fail_reasons.append(
            f"pe25_proof_lifecycle: unsupported lifecycle state {pe25_lifecycle.lifecycle_state!r}"
        )
    if pe25_lifecycle.lifecycle_state in INVALID_PROOF_LIFECYCLE_STATES:
        fail_reasons.append(
            f"pe25_proof_lifecycle: invalid lifecycle state {pe25_lifecycle.lifecycle_state!r}"
        )

    if proof.closure_owner != PE25_INTEGRATION_OWNER:
        fail_reasons.append(f"pe25_proof: closure_owner must be {PE25_INTEGRATION_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe25_proof: source_revision mismatch")
    if not proof.closure_input_digest:
        fail_reasons.append("pe25_proof: closure_input_digest required")
    elif not valid_sha256_digest(proof.closure_input_digest):
        fail_reasons.append("pe25_proof: closure_input_digest must be 64-char lowercase sha256 hex")
    elif proof.closure_input_digest != compute_pe25_closure_input_digest(pe25_input):
        fail_reasons.append("pe25_proof: closure_input_digest mismatch")

    if not proof.closure_result_digest:
        fail_reasons.append("pe25_proof: closure_result_digest required")
    elif not valid_sha256_digest(proof.closure_result_digest):
        fail_reasons.append(
            "pe25_proof: closure_result_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.closure_result_digest != pe25_result.get("closure_result_digest"):
        fail_reasons.append("pe25_proof: closure_result_digest mismatch")

    expected_admission_proof = admission_result.get("integration_proof_digest")
    if not proof.admission_integration_proof_digest:
        fail_reasons.append("pe25_proof: admission_integration_proof_digest required")
    elif expected_admission_proof is None:
        fail_reasons.append("pe25_proof: admission_integration_proof_digest unavailable")
    elif proof.admission_integration_proof_digest != expected_admission_proof:
        fail_reasons.append("pe25_proof: admission_integration_proof_digest mismatch")

    required_binding_flags = (
        ("pe25_integration_pass", True),
        ("operator_closure_static_complete", True),
        ("operator_closure_lifecycle_bound", True),
        ("pe25_operator_closure_bound", True),
        ("durable_run_primary_evidence_completion_operator_closure_bound", True),
        ("pe34_handoff_bound", True),
        ("pe35_staleness_revocation_recovery_bound", True),
        ("pe36_admission_presentation_bound", True),
        ("pe37_durable_traceability_bound", True),
        ("closure_coherence_proven", True),
    )
    for field_name, expected in required_binding_flags:
        actual = getattr(proof, field_name)
        if actual is not expected:
            fail_reasons.append(f"pe25_proof: {field_name} must be {expected}")

    digest_fields = (
        ("traceability_identity", proof.traceability_identity),
        ("admission_identity", proof.admission_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("manifest_identity_digest", proof.manifest_identity_digest),
        ("durable_artifact_identity", proof.durable_artifact_identity),
        ("pe34_handoff_digest", proof.pe34_handoff_digest),
        ("pe35_boundary_result_digest", proof.pe35_boundary_result_digest),
        ("pe36_boundary_result_digest", proof.pe36_boundary_result_digest),
        ("pe37_traceability_identity", proof.pe37_traceability_identity),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe25_proof: {field_name} required")
        elif not valid_sha256_digest(value):
            fail_reasons.append(f"pe25_proof: {field_name} must be 64-char lowercase sha256 hex")

    if proof.traceability_identity != pe37_proof.traceability_identity:
        fail_reasons.append("pe25_proof: traceability_identity mismatch with PE-37")
    if proof.admission_identity != pe37_proof.admission_identity:
        fail_reasons.append("pe25_proof: admission_identity mismatch with PE-37")
    if proof.durable_artifact_identity != durable_root.run_root_digest:
        fail_reasons.append("pe25_proof: durable_artifact_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe25_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe25_proof: completion_identity_digest mismatch")
    if proof.manifest_identity_digest != manifest_digest:
        fail_reasons.append("pe25_proof: manifest_identity_digest mismatch")

    computed_pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    if proof.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("pe25_proof: pe34_handoff_digest mismatch with PE-34 handoff")
    if proof.pe35_boundary_result_digest != pe35_proof.boundary_result_digest:
        fail_reasons.append("pe25_proof: pe35_boundary_result_digest mismatch with PE-35")
    if proof.pe36_boundary_result_digest != pe37_proof.pe36_boundary_result_digest:
        fail_reasons.append("pe25_proof: pe36_boundary_result_digest mismatch with PE-36")
    if proof.pe37_traceability_identity != pe37_proof.traceability_identity:
        fail_reasons.append("pe25_proof: pe37_traceability_identity mismatch with PE-37")

    if pe25_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe25_closure_integration_input: source_revision mismatch with completion input"
        )
    if (
        pe25_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest
        != pe22_proof.integration_proof_digest
    ):
        fail_reasons.append("pe25_proof: PE-22 integration_proof_digest drift from completion")
    if (
        pe25_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest
        != pe23_proof.integration_proof_digest
    ):
        fail_reasons.append("pe25_proof: PE-23 integration_proof_digest drift from completion")
    if (
        pe25_input.pe24_pilot_envelope_proof.integration_proof_digest
        != pe24_proof.integration_proof_digest
    ):
        fail_reasons.append("pe25_proof: PE-24 integration_proof_digest drift from completion")
    if pe25_input.lifecycle_matrix_proof.lifecycle_state_digest != durable_root.run_root_digest:
        fail_reasons.append("pe25_proof: lifecycle_state_digest mismatch with run_root_digest")

    from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
        _build_pe25_closure_input_from_completion,
    )

    if compute_pe25_closure_input_digest(pe25_input) != compute_pe25_closure_input_digest(
        _build_pe25_closure_input_from_completion(integration_input)
    ):
        fail_reasons.append(
            "pe25_closure_integration_input: PE-25 closure input drift from completion chain"
        )

    if not pe25_result.get("integration_pass"):
        fail_reasons.append("pe25_closure_integration_input: PE-25 evaluation failed")
        fail_reasons.extend(
            f"pe25_closure_integration_input: {reason}"
            for reason in pe25_result.get("fail_reasons", [])
        )
    elif not pe25_result.get("operator_closure_static_complete"):
        fail_reasons.append(
            "pe25_closure_integration_input: operator_closure_static_complete required"
        )
    elif pe25_result.get("operative_operator_closure_executed"):
        fail_reasons.append("pe25_proof: operative operator closure must not be executed")
    elif pe25_result.get("authority_lift"):
        fail_reasons.append("pe25_proof: authority_lift must remain false")

    if not admission_result.get("integration_pass"):
        fail_reasons.append(
            "pe25_proof: admission presentation lifecycle evaluation failed for PE-39 coherence"
        )

    return ValidationResult(fail_reasons=tuple(fail_reasons))
