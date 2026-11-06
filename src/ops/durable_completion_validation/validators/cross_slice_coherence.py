"""PE-33 cross-slice proof coherence validator for durable completion binding."""

from __future__ import annotations

from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
    COHERENCE_OWNER as PE33_COHERENCE_OWNER,
    CONTRACT_VERSION as PE33_INTEGRATION_OWNER,
    compute_integration_input_digest as compute_pe33_integration_input_digest,
    compute_integration_proof_digest as compute_pe33_integration_proof_digest,
    evaluate_cross_slice_proof_coherence_integration,
)
from src.ops.durable_completion_validation.identity import sorted_unique, valid_sha256_digest
from src.ops.durable_completion_validation.models import ValidationContext, ValidationResult


def _pe33_slot_digest_by_id(integration_input) -> dict[str, str]:
    return {slot.slot_id: slot.proof_digest for slot in integration_input.proof_slots}


def validate_pe33_cross_slice_proof_coherence(context: ValidationContext) -> ValidationResult:
    """Fail-closed PE-33 cross-slice coherence binding against completion proof chain."""
    from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
        INVALID_PROOF_LIFECYCLE_STATES,
    )

    integration_input = context.integration_input
    fail_reasons: list[str] = []

    pe33_lifecycle = integration_input.pe33_proof_lifecycle
    if pe33_lifecycle.lifecycle_state in INVALID_PROOF_LIFECYCLE_STATES:
        fail_reasons.append(
            f"pe33_proof_lifecycle: invalid lifecycle state {pe33_lifecycle.lifecycle_state!r}"
        )

    pe33_input = integration_input.pe33_cross_slice_proof_coherence_integration_input
    pe33_proof = integration_input.pe33_cross_slice_proof_coherence_proof
    chain = integration_input.completion_proof_chain

    if pe33_proof.coherence_owner != PE33_COHERENCE_OWNER:
        fail_reasons.append(f"pe33_proof: coherence_owner must be {PE33_COHERENCE_OWNER!r}")
    if pe33_proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe33_proof: source_revision mismatch with completion input")
    if pe33_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe33_cross_slice_proof_coherence_integration_input: source_revision mismatch "
            "with completion input"
        )

    for field_name in (
        "integration_input_digest",
        "integration_proof_digest",
    ):
        value = getattr(pe33_proof, field_name)
        if not value:
            fail_reasons.append(f"pe33_proof: {field_name} required")
        elif not valid_sha256_digest(value):
            fail_reasons.append(f"pe33_proof: {field_name} must be 64-char lowercase sha256 hex")

    pe33_result = evaluate_cross_slice_proof_coherence_integration(pe33_input)
    if not pe33_result["integration_pass"]:
        fail_reasons.append(
            "pe33_cross_slice_proof_coherence_integration_input: PE-33 evaluation failed"
        )
        fail_reasons.extend(
            f"pe33_cross_slice_proof_coherence_integration_input: {reason}"
            for reason in pe33_result.get("fail_reasons", [])
        )
    elif not pe33_result["cross_slice_proof_coherence_for_separate_operator_review"]:
        fail_reasons.append(
            "pe33_cross_slice_proof_coherence_integration_input: "
            "cross_slice_proof_coherence_for_separate_operator_review required"
        )
    elif not pe33_result["static_pe12_lifecycle_chain_complete"]:
        fail_reasons.append(
            "pe33_cross_slice_proof_coherence_integration_input: "
            "static_pe12_lifecycle_chain_complete required"
        )

    computed_input_digest = compute_pe33_integration_input_digest(pe33_input)
    if pe33_proof.integration_input_digest != computed_input_digest:
        fail_reasons.append("pe33_proof: integration_input_digest mismatch")
    if chain.completion_referenced_pe33_integration_input_digest != computed_input_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe33_integration_input_digest mismatch"
        )

    if pe33_result["integration_pass"]:
        computed_proof_digest = compute_pe33_integration_proof_digest(
            pe33_input,
            cross_slice_proof_coherence_for_separate_operator_review=True,
        )
        if pe33_proof.integration_proof_digest != computed_proof_digest:
            fail_reasons.append("pe33_proof: integration_proof_digest mismatch")
        if chain.completion_referenced_pe33_integration_proof_digest != computed_proof_digest:
            fail_reasons.append(
                "completion_proof_chain: completion_referenced_pe33_integration_proof_digest mismatch"
            )

    if pe33_proof.integration_pass is not True:
        fail_reasons.append("pe33_proof: integration_pass must be true")
    if pe33_proof.cross_slice_proof_coherence_for_separate_operator_review is not True:
        fail_reasons.append(
            "pe33_proof: cross_slice_proof_coherence_for_separate_operator_review must be true"
        )
    if pe33_proof.static_pe12_lifecycle_chain_complete is not True:
        fail_reasons.append("pe33_proof: static_pe12_lifecycle_chain_complete must be true")

    slot_by_id = _pe33_slot_digest_by_id(pe33_input)
    completion_slot_checks = (
        ("pe21", integration_input.pe21_proof.integration_proof_digest),
        ("pe22", integration_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest),
        (
            "pe23",
            integration_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest,
        ),
        ("pe24", integration_input.pe24_pilot_envelope_lifecycle_proof.integration_proof_digest),
        (
            "pe31",
            integration_input.pe31_reconciliation_review_integration_proof.integration_proof_digest,
        ),
        ("pe25", integration_input.pe25_operator_closure_proof.closure_result_digest),
    )
    for slot_id, completion_digest in completion_slot_checks:
        pe33_digest = slot_by_id.get(slot_id)
        if pe33_digest is None:
            fail_reasons.append(f"pe33_proof: missing PE-33 slot {slot_id!r}")
        elif pe33_digest != completion_digest:
            fail_reasons.append(
                f"pe33_proof: PE-33 slot {slot_id} proof_digest mismatch with completion chain"
            )

    pe25_slot_digest = slot_by_id.get("pe25")
    if pe25_slot_digest is None:
        fail_reasons.append("pe33_proof: PE-33 pe25 slot digest required")
    elif chain.completion_referenced_pe33_pe25_slot_digest != pe25_slot_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe33_pe25_slot_digest mismatch"
        )

    if (
        integration_input.contract_versions.pe33_cross_slice_proof_coherence
        != PE33_INTEGRATION_OWNER
    ):
        fail_reasons.append(
            f"contract_versions: pe33_cross_slice_proof_coherence must be {PE33_INTEGRATION_OWNER!r}"
        )

    return ValidationResult(fail_reasons=tuple(sorted_unique(fail_reasons)))
