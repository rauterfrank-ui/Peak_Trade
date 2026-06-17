"""Static + offline bounded Futures Testnet cross-slice proof-coherence integration (v0).

Docs/tests-only. No runtime, network, credentials, readiness decisions, or Testnet start.
PE-33 static PE-21..PE-32 proof-slot coherence guard only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_READINESS_DECISION,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
    PHASE_PRIVATE_READONLY,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE23_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CANONICAL_SLOT_OWNERS,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLOBAL_CROSS_SLICE_PROOF_COHERENCE,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_BLOCKER_LIFT_EXECUTED,
    OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
    OPERATIVE_OPERATOR_DECISION_CREATED,
    OPERATIVE_PREFLIGHT_ASSEMBLY_CREATED,
    OPERATIVE_READINESS_DECISION_CREATED,
    REQUIRED_SLOT_IDS,
    RUNTIME_STARTED,
    TESTNET_RUN_STARTED,
    CrossSliceProofCoherenceIntegrationInput,
    ProofSlotBinding,
    UpstreamDigestBinding,
    build_coherent_proof_slots_from_pe32_default,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_cross_slice_proof_coherence_integration,
    replace_proof_slot,
    serialize_integration_input_canonical,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    CONTRACT_VERSION as PE21_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE28_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE32_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE31_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE30_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE29_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE27_CONTRACT_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0.py"
)
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_CROSS_SLICE_PROOF_COHERENCE_INTEGRATION_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_CROSS_SLICE_PROOF_COHERENCE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def _slot_by_id(slots: tuple[ProofSlotBinding, ...]) -> dict[str, ProofSlotBinding]:
    return {slot.slot_id: slot for slot in slots}


def _replace_slot(
    integration_input: CrossSliceProofCoherenceIntegrationInput,
    **kwargs: object,
) -> CrossSliceProofCoherenceIntegrationInput:
    slot_id = str(kwargs.pop("slot_id"))
    slots = _slot_by_id(integration_input.proof_slots)
    updated = replace(slots[slot_id], **kwargs)
    return replace(
        integration_input,
        proof_slots=replace_proof_slot(integration_input.proof_slots, updated),
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_CROSS_SLICE_PROOF_COHERENCE_INTEGRATION_CONTRACT_V0=true"
        in INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_pe21_through_pe32_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    for marker in (
        "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0",
        "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0",
        "bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0",
    ):
        assert marker in integration_text
    assert "evaluate_phase_transition" not in integration_text
    assert "KrakenTestnetClient" not in integration_text
    assert "import subprocess" not in integration_text
    assert "open(" not in integration_text
    assert PE12_PACKAGE_MARKER in LIFECYCLE_MODULE.read_text(encoding="utf-8")


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_CROSS_SLICE_PROOF_COHERENCE is False
    assert OPERATIVE_READINESS_DECISION_CREATED is False
    assert OPERATIVE_OPERATOR_DECISION_CREATED is False
    assert OPERATIVE_OPERATOR_CLOSURE_EXECUTED is False
    assert OPERATIVE_BLOCKER_LIFT_EXECUTED is False
    assert OPERATIVE_PREFLIGHT_ASSEMBLY_CREATED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert RUNTIME_STARTED is False
    assert AUTHORITY_LIFT is False


def test_valid_full_chain_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_cross_slice_proof_coherence_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["cross_slice_proof_coherence_for_separate_operator_review"] is True
    assert result["pe33_cross_slice_proof_coherence_static_integration_proven"] is True
    assert result["static_pe12_lifecycle_chain_complete"] is True
    assert result["source_revision_coherent"] is True
    assert result["owner_identities_coherent"] is True
    assert result["proof_digests_coherent"] is True
    assert result["lifecycle_sequence_coherent"] is True
    assert result["assigned_lifecycle_phase"] == PHASE_READINESS_DECISION
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_cross_slice_proof_coherence_integration(default_minimal_integration_input())
    assert result["integration_pass"] is True
    assert result["cross_slice_proof_coherence_for_separate_operator_review"] is True
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["global_blocker_lift_authorized"] is False
    assert result["preflight_lift_authorized"] is False
    assert result["ready_for_operator_arming"] is False
    assert result["readiness_decision_authorized"] is False
    assert result["operator_decision_authorized"] is False
    assert result["operator_closure_authorized"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
    assert result["private_readonly_authorized"] is False
    assert result["validate_only_authorized"] is False
    assert result["tiny_order_authorized"] is False
    assert result["reconciliation_authorized"] is False
    assert result["evidence_acceptance_authorized"] is False
    assert result["pilot_start_authorized"] is False
    assert result["promotion_authorized"] is False
    assert result["network_allowed"] is False
    assert result["credentials_allowed"] is False
    assert result["orders_allowed"] is False
    assert result["scheduler_runtime_allowed"] is False
    assert result["network_used"] is False
    assert result["credentials_used"] is False
    assert result["exchange_api_called"] is False
    assert result["exchange_request_count"] == 0
    assert result["orders_created"] == 0
    assert result["orders_cancelled"] == 0
    assert result["orders_amended"] == 0
    assert result["positions_changed"] == 0
    assert result["adapter_called"] is False
    assert result["testnet_started"] is False
    assert result["runtime_started"] is False
    assert result["harness_started"] is False
    assert result["subprocess_started"] is False
    assert result["account_state_queried"] is False


@pytest.mark.parametrize("missing_slot", REQUIRED_SLOT_IDS)
def test_missing_required_slot_fails_closed(missing_slot: str) -> None:
    integration_input = default_minimal_integration_input()
    remaining = tuple(
        slot for slot in integration_input.proof_slots if slot.slot_id != missing_slot
    )
    broken = replace(integration_input, proof_slots=remaining)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert result["cross_slice_proof_coherence_for_separate_operator_review"] is False
    assert any("missing required slot" in reason for reason in result["fail_reasons"])


@pytest.mark.parametrize(
    ("slot_id", "expected_owner"),
    [
        ("pe21", PE21_CONTRACT_VERSION),
        ("pe22", PE22_CONTRACT_VERSION),
        ("pe23", PE23_CONTRACT_VERSION),
        ("pe25", PE25_CONTRACT_VERSION),
        ("pe26", PE26_CONTRACT_VERSION),
        ("pe27", PE27_CONTRACT_VERSION),
        ("pe28", PE28_CONTRACT_VERSION),
        ("pe29", PE29_CONTRACT_VERSION),
        ("pe30", PE30_CONTRACT_VERSION),
        ("pe31", PE31_CONTRACT_VERSION),
        ("pe32", PE32_CONTRACT_VERSION),
    ],
)
def test_wrong_canonical_owner_fails_closed(slot_id: str, expected_owner: str) -> None:
    integration_input = default_minimal_integration_input()
    broken = _replace_slot(
        integration_input,
        slot_id=slot_id,
        canonical_owner=f"wrong.{slot_id}.owner",
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any("canonical_owner must be" in reason for reason in result["fail_reasons"])


@pytest.mark.parametrize("slot_id", REQUIRED_SLOT_IDS)
def test_mismatched_source_revision_per_slot_fails_closed(slot_id: str) -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    broken = _replace_slot(
        integration_input,
        slot_id=slot_id,
        source_revision=ALT_COMMIT_SHA,
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in reason for reason in result["fail_reasons"])


@pytest.mark.parametrize(
    "source_revision",
    [
        "",
        "abc",
        "ABCDEF0123456789ABCDEF0123456789ABCDEF01",
        "abcdef0123456789abcdef0123456789abcdef0",
    ],
)
def test_invalid_source_revision_fails_closed(source_revision: str) -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    broken = replace(integration_input, source_revision=source_revision)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False


@pytest.mark.parametrize(
    ("slot_id", "upstream_slot"),
    [
        ("pe27", "pe26"),
        ("pe28", "pe27"),
        ("pe29", "pe28"),
        ("pe30", "pe29"),
        ("pe31", "pe30"),
        ("pe32", "pe31"),
    ],
)
def test_wrong_upstream_lifecycle_digest_fails_closed(slot_id: str, upstream_slot: str) -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    target = slots[slot_id]
    bad_bindings = tuple(
        UpstreamDigestBinding(
            upstream_slot_id=binding.upstream_slot_id,
            upstream_proof_digest=(
                "0" * 64
                if binding.upstream_slot_id == upstream_slot
                else binding.upstream_proof_digest
            ),
        )
        for binding in target.upstream_bindings
    )
    broken = _replace_slot(integration_input, slot_id=slot_id, upstream_bindings=bad_bindings)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any("digest mismatch" in reason for reason in result["fail_reasons"])


def test_wrong_pe21_digest_in_pe31_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    pe31 = slots["pe31"]
    bad_bindings = tuple(
        UpstreamDigestBinding(
            upstream_slot_id=binding.upstream_slot_id,
            upstream_proof_digest=(
                "1" * 64 if binding.upstream_slot_id == "pe21" else binding.upstream_proof_digest
            ),
        )
        for binding in pe31.upstream_bindings
    )
    broken = _replace_slot(integration_input, slot_id="pe31", upstream_bindings=bad_bindings)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False


def test_wrong_pe22_digest_in_pe26_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    pe26 = slots["pe26"]
    bad_bindings = tuple(
        UpstreamDigestBinding(
            upstream_slot_id=binding.upstream_slot_id,
            upstream_proof_digest=(
                "2" * 64 if binding.upstream_slot_id == "pe22" else binding.upstream_proof_digest
            ),
        )
        for binding in pe26.upstream_bindings
    )
    broken = _replace_slot(integration_input, slot_id="pe26", upstream_bindings=bad_bindings)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False


def test_wrong_pe25_digest_in_pe32_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    pe32 = slots["pe32"]
    bad_bindings = tuple(
        UpstreamDigestBinding(
            upstream_slot_id=binding.upstream_slot_id,
            upstream_proof_digest=(
                "3" * 64 if binding.upstream_slot_id == "pe25" else binding.upstream_proof_digest
            ),
        )
        for binding in pe32.upstream_bindings
    )
    broken = _replace_slot(integration_input, slot_id="pe32", upstream_bindings=bad_bindings)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False


def test_swapped_lifecycle_phases_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    broken = _replace_slot(
        integration_input,
        slot_id="pe27",
        lifecycle_phase=PHASE_PRIVATE_READONLY,
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any("lifecycle_phase" in reason for reason in result["fail_reasons"])


def test_duplicate_lifecycle_phase_slot_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    broken = _replace_slot(
        integration_input,
        slot_id="pe28",
        lifecycle_phase=PHASE_ZERO_ORDER,
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False


def test_self_referential_proof_digest_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    pe27 = slots["pe27"]
    self_ref = UpstreamDigestBinding(
        upstream_slot_id="pe27",
        upstream_proof_digest=pe27.proof_digest,
    )
    broken = _replace_slot(
        integration_input,
        slot_id="pe27",
        upstream_bindings=pe27.upstream_bindings + (self_ref,),
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any("self-referential" in reason for reason in result["fail_reasons"])


def test_circular_proof_dependency_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    pe25 = slots["pe25"]
    pe32 = slots["pe32"]
    broken = _replace_slot(
        integration_input,
        slot_id="pe25",
        upstream_bindings=pe25.upstream_bindings
        + (
            UpstreamDigestBinding(
                upstream_slot_id="pe32",
                upstream_proof_digest=pe32.proof_digest,
            ),
        ),
    )
    broken = _replace_slot(
        broken,
        slot_id="pe32",
        upstream_bindings=pe32.upstream_bindings
        + (
            UpstreamDigestBinding(
                upstream_slot_id="pe25",
                upstream_proof_digest=pe25.proof_digest,
            ),
        ),
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any(
        "cycle" in reason or "upstream slot ids" in reason for reason in result["fail_reasons"]
    )


def test_unknown_additional_proof_slot_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    extra = ProofSlotBinding(
        slot_id="pe99_unknown",
        canonical_owner="unknown.owner",
        source_revision=VALID_COMMIT_SHA,
        proof_digest="a" * 64,
        integration_pass=True,
        upstream_bindings=(),
    )
    broken = replace(
        integration_input,
        proof_slots=integration_input.proof_slots + (extra,),
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any("unknown slot" in reason for reason in result["fail_reasons"])


def test_loose_boolean_eligibility_fails_closed() -> None:
    result = evaluate_cross_slice_proof_coherence_integration(
        default_minimal_integration_input(),
        loose_boolean_eligibility=True,
    )
    assert result["integration_pass"] is False
    assert result["cross_slice_proof_coherence_for_separate_operator_review"] is False
    assert any("loose boolean eligibility" in reason for reason in result["fail_reasons"])


def test_single_slice_integration_pass_true_insufficient() -> None:
    integration_input = default_minimal_integration_input()
    broken = _replace_slot(
        integration_input,
        slot_id="pe22",
        integration_pass=True,
        proof_digest="0" * 64,
    )
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert result["cross_slice_proof_coherence_for_separate_operator_review"] is False


def test_determinism_and_digest_stability() -> None:
    first = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    second = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_integration_input_canonical(first) == serialize_integration_input_canonical(
        second
    )
    assert compute_integration_input_digest(first) == compute_integration_input_digest(second)
    first_result = evaluate_cross_slice_proof_coherence_integration(first)
    second_result = evaluate_cross_slice_proof_coherence_integration(second)
    assert first_result["integration_proof_digest"] == second_result["integration_proof_digest"]


def test_input_change_changes_digest() -> None:
    first = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    second = default_minimal_integration_input(source_revision=ALT_COMMIT_SHA)
    assert compute_integration_input_digest(first) != compute_integration_input_digest(second)


def test_slot_order_does_not_change_canonical_result() -> None:
    integration_input = default_minimal_integration_input()
    reversed_slots = tuple(reversed(integration_input.proof_slots))
    reversed_input = replace(integration_input, proof_slots=reversed_slots)
    first = evaluate_cross_slice_proof_coherence_integration(integration_input)
    second = evaluate_cross_slice_proof_coherence_integration(reversed_input)
    assert first["integration_pass"] == second["integration_pass"]
    assert first["integration_input_digest"] == second["integration_input_digest"]
    assert first["integration_proof_digest"] == second["integration_proof_digest"]


def test_build_coherent_slots_cover_all_required_ids() -> None:
    slots = build_coherent_proof_slots_from_pe32_default(source_revision=VALID_COMMIT_SHA)
    assert tuple(slot.slot_id for slot in slots) == REQUIRED_SLOT_IDS
    for slot in slots:
        assert slot.canonical_owner == CANONICAL_SLOT_OWNERS[slot.slot_id]


def test_pe32_without_pe25_binding_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    pe32 = slots["pe32"]
    pe31_only = tuple(
        binding for binding in pe32.upstream_bindings if binding.upstream_slot_id == "pe31"
    )
    broken = _replace_slot(integration_input, slot_id="pe32", upstream_bindings=pe31_only)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any(
        "PE-25 cross-slice binding required" in reason or "upstream slot ids" in reason
        for reason in result["fail_reasons"]
    )


def test_contradictory_duplicate_upstream_binding_fails_closed() -> None:
    integration_input = default_minimal_integration_input()
    slots = _slot_by_id(integration_input.proof_slots)
    pe31 = slots["pe31"]
    duplicated = pe31.upstream_bindings + (
        UpstreamDigestBinding(
            upstream_slot_id="pe21",
            upstream_proof_digest="f" * 64,
        ),
    )
    broken = _replace_slot(integration_input, slot_id="pe31", upstream_bindings=duplicated)
    result = evaluate_cross_slice_proof_coherence_integration(broken)
    assert result["integration_pass"] is False
    assert any("duplicate upstream binding" in reason for reason in result["fail_reasons"])
