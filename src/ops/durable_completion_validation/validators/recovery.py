"""PE-35 handoff staleness/revocation/recovery boundary proof validator."""

from __future__ import annotations

from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    HANDOFF_STATE_CURRENT,
    HANDOFF_STATE_RECOVERED,
    HANDOFF_STATE_RECOVERY_REQUIRED,
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
    BOUNDARY_OWNER as PE35_INTEGRATION_OWNER,
    compute_boundary_input_digest as compute_pe35_boundary_input_digest,
    compute_boundary_result_digest as compute_pe35_boundary_result_digest,
    validate_handoff_staleness_revocation_recovery_boundary_input,
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


def validate_pe35_recovery_boundary_proof(context: ValidationContext) -> ValidationResult:
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    pe35_result = context.pe35_result or {}
    proof = integration_input.pe35_handoff_recovery_boundary_proof
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = _compute_completion_identity_digest(integration_input)
    lifecycle = pe35_input.lifecycle_metadata
    recovery = pe35_input.recovery_proof

    if proof.boundary_owner != PE35_INTEGRATION_OWNER:
        fail_reasons.append(f"pe35_proof: boundary_owner must be {PE35_INTEGRATION_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe35_proof: source_revision mismatch")
    if not proof.boundary_input_digest:
        fail_reasons.append("pe35_proof: boundary_input_digest required")
    elif not valid_sha256_digest(proof.boundary_input_digest):
        fail_reasons.append(
            "pe35_proof: boundary_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.boundary_input_digest != compute_pe35_boundary_input_digest(pe35_input):
        fail_reasons.append("pe35_proof: boundary_input_digest mismatch")

    if not proof.boundary_result_digest:
        fail_reasons.append("pe35_proof: boundary_result_digest required")
    elif not valid_sha256_digest(proof.boundary_result_digest):
        fail_reasons.append(
            "pe35_proof: boundary_result_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_result_digest = compute_pe35_boundary_result_digest(
            pe35_input,
            handoff_staleness_revocation_recovery_boundary_satisfied=True,
        )
        if proof.pe35_boundary_pass is not True:
            fail_reasons.append("pe35_proof: pe35_boundary_pass must be true")
        elif proof.boundary_result_digest != expected_result_digest:
            fail_reasons.append("pe35_proof: boundary_result_digest mismatch")

    if proof.pe35_boundary_pass is not True:
        fail_reasons.append("pe35_proof: pe35_boundary_pass must be true")
    if proof.handoff_staleness_revocation_recovery_boundary_satisfied is not True:
        fail_reasons.append(
            "pe35_proof: handoff_staleness_revocation_recovery_boundary_satisfied must be true"
        )
    if proof.durable_run_primary_evidence_completion_boundary_bound is not True:
        fail_reasons.append(
            "pe35_proof: durable_run_primary_evidence_completion_boundary_bound must be true"
        )
    if proof.recovery_boundary_bound is not True:
        fail_reasons.append("pe35_proof: recovery_boundary_bound must be true")
    if proof.partial_failure_recovery_bound is not True:
        fail_reasons.append("pe35_proof: partial_failure_recovery_bound must be true")
    if proof.idempotency_bound is not True:
        fail_reasons.append("pe35_proof: idempotency_bound must be true")
    if proof.resume_boundary_bound is not True:
        fail_reasons.append("pe35_proof: resume_boundary_bound must be true")
    if proof.retry_boundary_bound is not True:
        fail_reasons.append("pe35_proof: retry_boundary_bound must be true")
    if proof.replay_boundary_bound is not True:
        fail_reasons.append("pe35_proof: replay_boundary_bound must be true")
    if proof.supersession_bound is not True:
        fail_reasons.append("pe35_proof: supersession_bound must be true")
    if proof.recovery_coherence_proven is not True:
        fail_reasons.append("pe35_proof: recovery_coherence_proven must be true")

    digest_fields = (
        ("traceability_identity", proof.traceability_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("manifest_identity_digest", proof.manifest_identity_digest),
        ("handoff_digest", proof.handoff_digest),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe35_proof: {field_name} required")
        elif field_name != "handoff_digest" and not valid_sha256_digest(value):
            fail_reasons.append(f"pe35_proof: {field_name} must be 64-char lowercase sha256 hex")
        elif field_name == "handoff_digest" and not valid_sha256_digest(value):
            fail_reasons.append(f"pe35_proof: {field_name} must be 64-char lowercase sha256 hex")

    if proof.traceability_identity != durable_root.run_root_digest:
        fail_reasons.append("pe35_proof: traceability_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe35_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe35_proof: completion_identity_digest mismatch")
    if proof.manifest_identity_digest != manifest_digest:
        fail_reasons.append("pe35_proof: manifest_identity_digest mismatch")

    computed_handoff_digest = compute_pe34_boundary_input_digest(pe35_input.pe34_handoff)
    if proof.handoff_digest != computed_handoff_digest:
        fail_reasons.append("pe35_proof: handoff_digest mismatch with PE-34 handoff")
    if proof.handoff_generation != lifecycle.generation:
        fail_reasons.append("pe35_proof: handoff_generation mismatch with lifecycle metadata")

    expected_recovery_generation = recovery.recovery_generation if recovery is not None else 0
    if proof.recovery_generation != expected_recovery_generation:
        fail_reasons.append("pe35_proof: recovery_generation mismatch")

    if pe35_input.pe34_handoff.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe35_handoff_staleness_revocation_recovery_boundary_input: source_revision mismatch "
            "with completion input"
        )

    canonical = pe35_input.canonical_current
    if canonical.archive_manifest_digest is not None:
        if canonical.archive_manifest_digest != manifest_digest:
            fail_reasons.append(
                "pe35_handoff_staleness_revocation_recovery_boundary_input: "
                "archive_manifest_digest mismatch with completion manifest"
            )

    if lifecycle.lifecycle_state in {
        HANDOFF_STATE_STALE,
        HANDOFF_STATE_SUPERSEDED,
        HANDOFF_STATE_REVOKED,
        HANDOFF_STATE_RECOVERY_REQUIRED,
    }:
        fail_reasons.append(
            f"pe35_proof: open partial-failure lifecycle state {lifecycle.lifecycle_state!r}"
        )
    elif lifecycle.lifecycle_state == HANDOFF_STATE_RECOVERED and recovery is None:
        fail_reasons.append("pe35_proof: recovered lifecycle_state requires recovery_proof")
    elif lifecycle.lifecycle_state not in {HANDOFF_STATE_CURRENT, HANDOFF_STATE_RECOVERED}:
        fail_reasons.append(f"pe35_proof: unknown lifecycle_state {lifecycle.lifecycle_state!r}")

    if pe35_input.active_successor_handoff_digests:
        fail_reasons.append("pe35_proof: active successor handoff digests present")
    for link in pe35_input.supersession_links:
        if link.predecessor_handoff_digest == computed_handoff_digest:
            fail_reasons.append("pe35_proof: handoff superseded by successor link")

    if not pe35_result.get("boundary_pass"):
        fail_reasons.append(
            "pe35_handoff_staleness_revocation_recovery_boundary_input: PE-35 evaluation failed"
        )
        fail_reasons.extend(
            f"pe35_handoff_staleness_revocation_recovery_boundary_input: {reason}"
            for reason in pe35_result.get("fail_reasons", [])
        )
    elif not pe35_result.get("handoff_staleness_revocation_recovery_boundary_satisfied"):
        fail_reasons.append(
            "pe35_handoff_staleness_revocation_recovery_boundary_input: "
            "handoff_staleness_revocation_recovery_boundary_satisfied required"
        )
    elif pe35_result.get("recovery_executed"):
        fail_reasons.append("pe35_proof: operative recovery must not be executed")
    elif pe35_result.get("authority_lift"):
        fail_reasons.append("pe35_proof: authority_lift must remain false")

    return ValidationResult(fail_reasons=tuple(fail_reasons))


def validate_recovery_proof_binding(context: ValidationContext) -> ValidationResult:
    """Graph recovery node: PE-35 handoff input validation plus PE-35 proof binding."""
    fail_reasons: list[str] = []
    pe35_input = context.integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    fail_reasons.extend(validate_handoff_staleness_revocation_recovery_boundary_input(pe35_input))
    pe35_proof = validate_pe35_recovery_boundary_proof(context)
    fail_reasons.extend(pe35_proof.fail_reasons)
    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))
