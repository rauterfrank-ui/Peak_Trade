"""PE-51 manifest integrity and PE-31 reconciliation review proof validators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    ARTIFACT_RECONCILIATION_RESULT,
    compute_integration_input_digest as compute_pe21_integration_input_digest,
    compute_manifest_digest,
    evaluate_reconciliation_static,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE31_INTEGRATION_OWNER,
    compute_integration_input_digest as compute_pe31_integration_input_digest,
    compute_integration_proof_digest as compute_pe31_integration_proof_digest,
)
from src.ops.durable_completion_validation.identity import sorted_unique, valid_sha256_digest
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult

if TYPE_CHECKING:
    from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
        DurableRunPrimaryEvidenceCompletionIntegrationInput,
    )


def _compute_completion_identity_digest(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> str:
    from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
        compute_completion_identity_digest,
    )

    durable_root = integration_input.durable_run_root
    return compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=integration_input.manifest_proof.manifest_digest,
        source_revision=integration_input.source_revision,
    )


def validate_pe21_reconciliation_result_manifest_integrity(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> list[str]:
    """Fail-closed PE-21 RECONCILIATION_RESULT.json manifest entry integrity enforcement."""
    fail_reasons: list[str] = []
    pe21_input = integration_input.pe21_integration_input
    pe21_binding = pe21_input.primary_evidence_binding
    recon = pe21_input.reconciliation_binding
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    prefix = "pe21_reconciliation_result_manifest"

    for entry in pe21_binding.manifest_entries:
        if not entry.relative_path:
            fail_reasons.append(f"{prefix}: empty manifest artifact path")

    canonical_entries = [
        entry
        for entry in pe21_binding.manifest_entries
        if entry.relative_path == ARTIFACT_RECONCILIATION_RESULT
    ]
    alias_entries = [
        entry
        for entry in pe21_binding.manifest_entries
        if entry.relative_path != ARTIFACT_RECONCILIATION_RESULT
        and (
            entry.relative_path.endswith(ARTIFACT_RECONCILIATION_RESULT)
            or "RECONCILIATION_RESULT" in entry.relative_path
        )
    ]

    if not canonical_entries:
        fail_reasons.append(f"{prefix}: {ARTIFACT_RECONCILIATION_RESULT} manifest entry required")
    elif len(canonical_entries) > 1:
        fail_reasons.append(
            f"{prefix}: duplicate {ARTIFACT_RECONCILIATION_RESULT} manifest entries"
        )

    if alias_entries:
        fail_reasons.append(f"{prefix}: alias or alternate reconciliation result manifest path")

    if ARTIFACT_RECONCILIATION_RESULT not in pe21_binding.expected_artifact_filenames:
        fail_reasons.append(
            f"{prefix}: {ARTIFACT_RECONCILIATION_RESULT} required in expected_artifact_filenames"
        )

    expected_result_digest = recon.result_digest
    if not expected_result_digest:
        fail_reasons.append(f"{prefix}: reconciliation_binding.result_digest required")
    elif not valid_sha256_digest(expected_result_digest):
        fail_reasons.append(
            f"{prefix}: reconciliation_binding.result_digest must be 64-char lowercase sha256 hex"
        )
    else:
        static_recon = evaluate_reconciliation_static(
            expected_position=recon.expected_position,
            observed_position=recon.observed_position,
            expected_orders=recon.expected_orders,
            observed_orders=recon.observed_orders,
            instrument=pe21_input.instrument,
        )
        if expected_result_digest != static_recon["result_digest"]:
            fail_reasons.append(
                f"{prefix}: reconciliation_binding.result_digest mismatch with canonical algorithm"
            )

    if canonical_entries:
        entry = canonical_entries[0]
        if not entry.relative_path:
            fail_reasons.append(f"{prefix}: empty manifest artifact path")
        elif entry.relative_path != ARTIFACT_RECONCILIATION_RESULT:
            fail_reasons.append(
                f"{prefix}: manifest artifact path must be {ARTIFACT_RECONCILIATION_RESULT!r}"
            )
        if not entry.digest:
            fail_reasons.append(
                f"{prefix}: manifest digest required for {ARTIFACT_RECONCILIATION_RESULT}"
            )
        elif not valid_sha256_digest(entry.digest):
            fail_reasons.append(f"{prefix}: manifest digest must be 64-char lowercase sha256 hex")
        elif expected_result_digest and entry.digest != expected_result_digest:
            fail_reasons.append(
                f"{prefix}: manifest digest mismatch with reconciliation_binding.result_digest"
            )

    if pe21_input.source_revision != integration_input.source_revision:
        fail_reasons.append(f"{prefix}: source_revision drift breaks run identity chain")

    if pe21_binding.durable_archive_root != durable_root.durable_archive_root:
        fail_reasons.append(f"{prefix}: durable_archive_root drift breaks evidence root chain")

    computed_pe21_manifest = compute_manifest_digest(pe21_binding.manifest_entries)
    if pe21_binding.manifest_digest != computed_pe21_manifest:
        fail_reasons.append(
            f"{prefix}: pe21 manifest_digest drift invalidates reconciliation result manifest entry"
        )
    if pe21_binding.manifest_proof_identity != computed_pe21_manifest:
        fail_reasons.append(
            f"{prefix}: pe21 manifest_proof_identity drift invalidates reconciliation result "
            "manifest entry"
        )

    completion_identity = _compute_completion_identity_digest(integration_input)
    if not run_identity.run_identity_digest:
        fail_reasons.append(f"{prefix}: run_identity_digest required for evidence chain")
    elif not valid_sha256_digest(run_identity.run_identity_digest):
        fail_reasons.append(f"{prefix}: run_identity_digest must be 64-char lowercase sha256 hex")
    if not manifest_digest:
        fail_reasons.append(f"{prefix}: completion manifest_digest required for evidence chain")
    elif not valid_sha256_digest(manifest_digest):
        fail_reasons.append(
            f"{prefix}: completion manifest_digest must be 64-char lowercase sha256 hex"
        )
    if not completion_identity:
        fail_reasons.append(f"{prefix}: completion_identity_digest unavailable for evidence chain")

    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))


def validate_pe31_integration_proof(context: ValidationContext) -> ValidationResult:
    fail_reasons: list[str] = []
    integration_input = context.integration_input
    pe31_result = context.pe31_result or {}
    proof = integration_input.pe31_reconciliation_review_integration_proof
    pe31_input = integration_input.pe31_reconciliation_review_integration_input

    if proof.integration_owner != PE31_INTEGRATION_OWNER:
        fail_reasons.append(f"pe31_proof: integration_owner must be {PE31_INTEGRATION_OWNER!r}")
    if not proof.integration_input_digest:
        fail_reasons.append("pe31_proof: integration_input_digest required")
    elif not valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe31_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe31_integration_input_digest(pe31_input):
        fail_reasons.append("pe31_proof: integration_input_digest mismatch")

    if not proof.integration_proof_digest:
        fail_reasons.append("pe31_proof: integration_proof_digest required")
    elif not valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe31_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe31_integration_proof_digest(
            pe31_input,
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review=True,
        )
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append("pe31_proof: integration_proof_digest mismatch")

    if proof.pe31_integration_pass is not True:
        fail_reasons.append("pe31_proof: pe31_integration_pass must be true")
    if proof.reconciliation_review_lifecycle_eligibility is not True:
        fail_reasons.append("pe31_proof: reconciliation_review_lifecycle_eligibility must be true")

    if not pe31_result.get("integration_pass"):
        fail_reasons.append("pe31_reconciliation_review_integration_input: PE-31 evaluation failed")
        fail_reasons.extend(
            f"pe31_reconciliation_review_integration_input: {reason}"
            for reason in pe31_result.get("fail_reasons", [])
        )
    elif not pe31_result.get(
        "reconciliation_review_lifecycle_eligibility_for_separate_operator_review"
    ):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: "
            "reconciliation_review_lifecycle_eligibility required"
        )

    if pe31_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: source_revision mismatch"
        )

    pe31_pe21_input = pe31_input.pe21_reconciliation_primary_evidence_integration_input
    if compute_pe21_integration_input_digest(
        pe31_pe21_input
    ) != compute_pe21_integration_input_digest(integration_input.pe21_integration_input):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: pe21_integration_input_digest mismatch "
            "with completion pe21_integration_input"
        )

    pe31_pe21_proof = pe31_input.pe21_reconciliation_primary_evidence_integration_proof
    if (
        pe31_pe21_proof.integration_proof_digest
        != integration_input.pe21_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: pe21_integration_proof_digest mismatch "
            "with completion pe21_proof"
        )
    if pe31_pe21_proof.reconciled is not True:
        fail_reasons.append("pe31_reconciliation_review_integration_input: reconciled must be true")

    review_proof = pe31_input.reconciliation_review_proof
    if review_proof.static_review_consistency_proven is not True:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: static_review_consistency_proven required"
        )
    if review_proof.orders_created != 0 or review_proof.orders_cancelled != 0:
        fail_reasons.append("pe31_reconciliation_review_integration_input: unresolved order state")
    if review_proof.positions_changed != 0:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: unresolved position state"
        )

    return ValidationResult(fail_reasons=tuple(fail_reasons))
