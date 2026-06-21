"""PE-37 durable evidence traceability boundary proof validator."""

from __future__ import annotations

from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE36_BOUNDARY_OWNER,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE37_BOUNDARY_OWNER,
    compute_boundary_input_digest as compute_pe37_boundary_input_digest,
    validate_durable_evidence_traceability_boundary_input,
)
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    compute_boundary_input_digest as compute_pe35_boundary_input_digest,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
)
from src.ops.durable_completion_validation.identity import sorted_unique, valid_sha256_digest
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


def validate_pe37_traceability_proof(context: ValidationContext) -> ValidationResult:
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    pe37_result = context.pe37_result or {}
    proof = integration_input.pe37_traceability_proof
    pe37_input = integration_input.pe37_traceability_boundary_input
    pe36_input = pe37_input.pe36_boundary_input
    pe35_input = pe36_input.pe35_boundary_input
    pe34_handoff = pe35_input.pe34_handoff
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = _compute_completion_identity_digest(integration_input)
    completion_pe35 = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input

    if proof.traceability_owner != PE37_BOUNDARY_OWNER:
        fail_reasons.append(f"pe37_proof: traceability_owner must be {PE37_BOUNDARY_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe37_proof: source_revision mismatch")
    if not proof.boundary_input_digest:
        fail_reasons.append("pe37_proof: boundary_input_digest required")
    elif not valid_sha256_digest(proof.boundary_input_digest):
        fail_reasons.append(
            "pe37_proof: boundary_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.boundary_input_digest != compute_pe37_boundary_input_digest(pe37_input):
        fail_reasons.append("pe37_proof: boundary_input_digest mismatch")

    if not proof.boundary_result_digest:
        fail_reasons.append("pe37_proof: boundary_result_digest required")
    elif not valid_sha256_digest(proof.boundary_result_digest):
        fail_reasons.append(
            "pe37_proof: boundary_result_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.boundary_result_digest != pe37_result.get("boundary_result_digest"):
        fail_reasons.append("pe37_proof: boundary_result_digest mismatch")

    required_binding_flags = (
        ("pe37_boundary_pass", True),
        ("durable_evidence_traceability_boundary_satisfied", True),
        ("pe34_handoff_bound", True),
        ("pe35_staleness_revocation_recovery_bound", True),
        ("pe36_admission_presentation_bound", True),
        ("durable_run_primary_evidence_completion_traceability_bound", True),
        ("operator_review_chain_durable_evidence_traceability_bound", True),
        ("traceability_coherence_proven", True),
    )
    for field_name, expected in required_binding_flags:
        actual = getattr(proof, field_name)
        if actual is not expected:
            fail_reasons.append(f"pe37_proof: {field_name} must be {expected}")

    digest_fields = (
        ("traceability_identity", proof.traceability_identity),
        ("admission_identity", proof.admission_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("manifest_identity_digest", proof.manifest_identity_digest),
        ("durable_artifact_identity", proof.durable_artifact_identity),
        ("review_chain_identity", proof.review_chain_identity),
        ("pe34_handoff_digest", proof.pe34_handoff_digest),
        ("pe36_boundary_result_digest", proof.pe36_boundary_result_digest),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe37_proof: {field_name} required")
        elif not valid_sha256_digest(value):
            fail_reasons.append(f"pe37_proof: {field_name} must be 64-char lowercase sha256 hex")

    expected_traceability = pe37_result.get("traceability_identity")
    if expected_traceability is None:
        fail_reasons.append("pe37_proof: traceability_identity unavailable")
    elif proof.traceability_identity != expected_traceability:
        fail_reasons.append("pe37_proof: traceability_identity mismatch")
    if proof.admission_identity != pe37_result.get("admission_identity"):
        fail_reasons.append("pe37_proof: admission_identity mismatch")
    if proof.review_chain_identity != proof.traceability_identity:
        fail_reasons.append("pe37_proof: review_chain_identity mismatch with traceability_identity")
    if proof.durable_artifact_identity != durable_root.run_root_digest:
        fail_reasons.append("pe37_proof: durable_artifact_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe37_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe37_proof: completion_identity_digest mismatch")
    if proof.manifest_identity_digest != manifest_digest:
        fail_reasons.append("pe37_proof: manifest_identity_digest mismatch")

    computed_pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    if proof.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("pe37_proof: pe34_handoff_digest mismatch with PE-34 handoff")
    computed_pe36_result = pe37_result.get("pe36_boundary_result_digest")
    if proof.pe36_boundary_result_digest != computed_pe36_result:
        fail_reasons.append("pe37_proof: pe36_boundary_result_digest mismatch")

    if compute_pe35_boundary_input_digest(completion_pe35) != compute_pe35_boundary_input_digest(
        pe35_input
    ):
        fail_reasons.append(
            "pe37_traceability_boundary_input: PE-35 boundary input drift from completion PE-35"
        )

    if pe34_handoff.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe37_traceability_boundary_input: source_revision mismatch with completion input"
        )

    pe37_archive = pe37_input.pe16_archive_binding
    if pe37_archive.archive_manifest_digest != manifest_digest:
        fail_reasons.append(
            "pe37_traceability_boundary_input: archive_manifest_digest mismatch with completion "
            "manifest"
        )

    if pe37_input.pe36_proof.boundary_owner != PE36_BOUNDARY_OWNER:
        fail_reasons.append("pe37_proof: PE-36 boundary_owner mismatch in embedded chain")
    if pe37_input.proof_chain.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("pe37_proof: proof_chain pe34_handoff_digest drift")

    if not pe37_result.get("boundary_pass"):
        fail_reasons.append("pe37_traceability_boundary_input: PE-37 evaluation failed")
        fail_reasons.extend(
            f"pe37_traceability_boundary_input: {reason}"
            for reason in pe37_result.get("fail_reasons", [])
        )
    elif not pe37_result.get("durable_evidence_traceability_boundary_satisfied"):
        fail_reasons.append(
            "pe37_traceability_boundary_input: "
            "durable_evidence_traceability_boundary_satisfied required"
        )
    elif pe37_result.get("operator_review_executed"):
        fail_reasons.append("pe37_proof: operative operator review must not be executed")
    elif pe37_result.get("admission_executed"):
        fail_reasons.append("pe37_proof: operative admission must not be executed")
    elif pe37_result.get("authority_lift"):
        fail_reasons.append("pe37_proof: authority_lift must remain false")

    return ValidationResult(fail_reasons=tuple(fail_reasons))


def validate_traceability_proof_binding(context: ValidationContext) -> ValidationResult:
    """Graph traceability node: PE-37 handoff input validation plus PE-37 proof binding."""
    fail_reasons: list[str] = []
    pe37_input = context.integration_input.pe37_traceability_boundary_input
    fail_reasons.extend(validate_durable_evidence_traceability_boundary_input(pe37_input))
    pe37_proof = validate_pe37_traceability_proof(context)
    fail_reasons.extend(pe37_proof.fail_reasons)
    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))
