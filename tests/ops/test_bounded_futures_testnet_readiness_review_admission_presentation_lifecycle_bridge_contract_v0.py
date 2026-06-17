"""Static + offline bounded Futures Testnet readiness review ↔ admission lifecycle bridge (v0).

Docs/tests-only. No runtime, network, credentials, operator review, admission, or Testnet start.
PE-38 ↔ PE-34/35/36/37 admission presentation lifecycle static bridge binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    default_minimal_pe35_proof_binding,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as ADMISSION_LIFECYCLE_CONTRACT_VERSION,
    default_minimal_integration_input as default_minimal_admission_input,
    evaluate_operator_review_admission_presentation_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    evaluate_durable_evidence_traceability_boundary,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE38_CONTRACT_VERSION,
    default_minimal_integration_input as default_minimal_pe38_input,
    evaluate_preflight_execution_readiness_review_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_readiness_review_admission_presentation_lifecycle_bridge_contract_v0 import (
    ADMISSION_EXECUTED,
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    EVIDENCE_OPERATIONALLY_ACCEPTED,
    NEW_AUTHORITY_SURFACE_CREATED,
    OPERATOR_CLOSURE_EXECUTED,
    OPERATOR_DECISION_EXECUTED,
    OPERATOR_REVIEW_EXECUTED,
    PRESENTATION_EXECUTED,
    PREFLIGHT_REMAINS_BLOCKED,
    READINESS_REVIEW_EXECUTED,
    RUN_STARTED,
    compute_bridge_input_digest,
    compute_bridge_proof_digest,
    default_minimal_bridge_input,
    default_minimal_safety_snapshot,
    evaluate_readiness_review_admission_presentation_lifecycle_bridge,
    serialize_bridge_input_canonical,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_readiness_review_admission_presentation_lifecycle_bridge_contract_v0.py"
)
PE38_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0.py"
)
ADMISSION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_READINESS_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_BRIDGE_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_READINESS_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_BRIDGE_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"

_CACHED_VALID_BRIDGE_INPUT = None


def _valid_bridge_input(source_revision: str = VALID_COMMIT_SHA):
    global _CACHED_VALID_BRIDGE_INPUT
    if source_revision != VALID_COMMIT_SHA:
        return default_minimal_bridge_input(
            source_revision=source_revision,
            instrument=GENERIC_FUTURES_INSTRUMENT,
        )
    if _CACHED_VALID_BRIDGE_INPUT is None:
        _CACHED_VALID_BRIDGE_INPUT = default_minimal_bridge_input(
            source_revision=VALID_COMMIT_SHA,
            instrument=GENERIC_FUTURES_INSTRUMENT,
        )
    return _CACHED_VALID_BRIDGE_INPUT


def _assert_all_authorization_flags_false(result: dict[str, object]) -> None:
    assert result["preflight_remains_blocked"] is True
    assert result["global_blocker_lift_authorized"] is False
    assert result["preflight_lift_authorized"] is False
    assert result["ready_for_operator_arming"] is False
    assert result["readiness_decision_authorized"] is False
    assert result["operator_review_authorized"] is False
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


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_READINESS_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_BRIDGE_CONTRACT_V0=true"
        in BRIDGE_MODULE.read_text(encoding="utf-8")
    )


def test_upstream_owners_referenced_not_duplicated() -> None:
    bridge_text = BRIDGE_MODULE.read_text(encoding="utf-8")
    assert (
        "bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0"
        in bridge_text
    )
    assert (
        "bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0"
        in bridge_text
    )
    assert "evaluate_operator_review(" not in bridge_text
    assert "import subprocess" not in bridge_text
    assert "open(" not in bridge_text
    assert PE38_MODULE.exists()
    assert ADMISSION_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert READINESS_REVIEW_EXECUTED is False
    assert OPERATOR_REVIEW_EXECUTED is False
    assert OPERATOR_DECISION_EXECUTED is False
    assert OPERATOR_CLOSURE_EXECUTED is False
    assert ADMISSION_EXECUTED is False
    assert PRESENTATION_EXECUTED is False
    assert EVIDENCE_OPERATIONALLY_ACCEPTED is False
    assert NEW_AUTHORITY_SURFACE_CREATED is False
    assert RUN_STARTED is False
    assert AUTHORITY_LIFT is False
    assert PREFLIGHT_REMAINS_BLOCKED is True


def test_happy_path_coherent_pe38_and_admission_composition_passes() -> None:
    bridge_input = _valid_bridge_input()
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(bridge_input)
    assert result["bridge_pass"] is True
    assert result["readiness_review_admission_presentation_lifecycle_bridge_eligibility"] is True
    assert result["readiness_review_lifecycle_bound"] is True
    assert result["pe38_durable_traceability_bound"] is True
    assert result["admission_presentation_lifecycle_bound"] is True
    assert result["pe34_handoff_bound"] is True
    assert result["pe35_staleness_revocation_recovery_bound"] is True
    assert result["pe36_admission_presentation_bound"] is True
    assert result["pe37_durable_traceability_bound"] is True
    assert result["fail_reasons"] == []
    _assert_all_authorization_flags_false(result)


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
        _valid_bridge_input()
    )
    assert result["bridge_pass"] is True
    assert result["contract_implementation_only"] is True
    assert result["readiness_review_executed"] is False
    assert result["admission_executed"] is False
    assert result["presentation_executed"] is False
    assert result["authority_lift"] is False
    _assert_all_authorization_flags_false(result)


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = _valid_bridge_input()
    right = _valid_bridge_input()
    assert serialize_bridge_input_canonical(left) == serialize_bridge_input_canonical(right)
    assert compute_bridge_input_digest(left) == compute_bridge_input_digest(right)
    left_result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(left)
    right_result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(right)
    assert left_result["bridge_proof_digest"] == right_result["bridge_proof_digest"]
    assert left_result["bridge_proof_digest"] == compute_bridge_proof_digest(
        left,
        readiness_review_admission_presentation_lifecycle_bridge_eligibility=True,
    )


def test_missing_pe38_readiness_review_lifecycle_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_pe38 = replace(
        bridge_input.pe38_integration_input,
        integration_id="",
    )
    broken = replace(bridge_input, pe38_integration_input=broken_pe38)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("pe38_integration_input" in r for r in result["fail_reasons"])


def test_missing_admission_presentation_lifecycle_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_admission = replace(
        bridge_input.admission_presentation_integration_input,
        integration_id="",
    )
    broken = replace(bridge_input, admission_presentation_integration_input=broken_admission)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("admission_presentation_integration_input" in r for r in result["fail_reasons"])


def test_missing_pe38_traceability_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_chain = replace(bridge_input.proof_chain, pe38_pe37_traceability_identity="")
    broken = replace(bridge_input, proof_chain=broken_chain)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("pe38_pe37_traceability_identity required" in r for r in result["fail_reasons"])


def test_missing_pe34_pe35_pe36_pe37_binding_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_proof = replace(
        bridge_input.admission_presentation_lifecycle_proof,
        pe34_handoff_bound=False,
    )
    broken = replace(bridge_input, admission_presentation_lifecycle_proof=broken_proof)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("pe34_handoff_bound must be true" in r for r in result["fail_reasons"])


def test_source_revision_drift_fails() -> None:
    bridge_input = _valid_bridge_input()
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
        bridge_input,
        expected_source_revision=ALT_COMMIT_SHA,
    )
    assert result["bridge_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_owner_identity_drift_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_proof = replace(
        bridge_input.pe38_readiness_review_proof,
        integration_owner="wrong.owner.v0",
    )
    broken = replace(bridge_input, pe38_readiness_review_proof=broken_proof)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_proof_digest_drift_fails() -> None:
    bridge_input = _valid_bridge_input()
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
        bridge_input,
        expected_pe38_integration_proof_digest="0" * 64,
    )
    assert result["bridge_pass"] is False
    assert any("pe38_integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_traceability_identity_drift_fails() -> None:
    bridge_input = _valid_bridge_input()
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
        bridge_input,
        expected_shared_pe37_traceability_identity="0" * 64,
    )
    assert result["bridge_pass"] is False
    assert any("shared_pe37_traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_stale_handoff_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_pe35 = replace(
        bridge_input.pe38_integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            bridge_input.pe38_integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_pe38 = replace(bridge_input.pe38_integration_input, pe35_boundary_input=broken_pe35)
    broken = replace(bridge_input, pe38_integration_input=broken_pe38)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False


def test_revoked_handoff_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_pe35 = replace(
        bridge_input.pe38_integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            bridge_input.pe38_integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_REVOKED,
        ),
    )
    broken_pe38 = replace(bridge_input.pe38_integration_input, pe35_boundary_input=broken_pe35)
    broken = replace(bridge_input, pe38_integration_input=broken_pe38)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False


def test_superseded_handoff_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_pe35 = replace(
        bridge_input.pe38_integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            bridge_input.pe38_integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_SUPERSEDED,
        ),
    )
    broken_pe38 = replace(bridge_input.pe38_integration_input, pe35_boundary_input=broken_pe35)
    broken = replace(bridge_input, pe38_integration_input=broken_pe38)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False


def test_empty_bridge_id_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken = replace(bridge_input, bridge_id="")
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("bridge_id required" in r for r in result["fail_reasons"])


def test_empty_adapter_id_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken = replace(bridge_input, adapter_id="")
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("adapter_id required" in r for r in result["fail_reasons"])


def test_cross_lifecycle_pe34_handoff_mismatch_fails() -> None:
    bridge_input = _valid_bridge_input()
    admission_only = default_minimal_admission_input(
        source_revision=VALID_COMMIT_SHA,
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    broken = replace(bridge_input, admission_presentation_integration_input=admission_only)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("pe34_handoff_digest mismatch" in r for r in result["fail_reasons"])


def test_unknown_extra_fields_fail() -> None:
    bridge_input = _valid_bridge_input()
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
        bridge_input,
        extra_fields={"unexpected_field": "value"},
    )
    assert result["bridge_pass"] is False
    assert any("unknown extra field" in r for r in result["fail_reasons"])


def test_secret_credential_command_authority_decision_fields_fail() -> None:
    bridge_input = _valid_bridge_input()
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
        bridge_input,
        extra_fields={
            "api_key": "secret-value",
            "operator_decision": True,
            "execution_authorized": True,
        },
    )
    assert result["bridge_pass"] is False
    assert any("forbidden extra field" in r for r in result["fail_reasons"])


def test_loose_boolean_eligibility_rejected() -> None:
    bridge_input = _valid_bridge_input()
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
        bridge_input,
        loose_boolean_eligibility=True,
    )
    assert result["bridge_pass"] is False
    assert any("loose_boolean_eligibility" in r for r in result["fail_reasons"])


def test_loose_authority_booleans_rejected() -> None:
    bridge_input = _valid_bridge_input()
    for kwargs in (
        {"readiness_decision_authorized": True},
        {"operator_review_authorized": True},
        {"operator_decision_authorized": True},
        {"operator_closure_authorized": True},
        {"global_blocker_lift_authorized": True},
        {"preflight_lift_authorized": True},
        {"execution_authorized": True},
        {"live_authorized": True},
        {"network_allowed": True},
        {"credentials_allowed": True},
        {"orders_allowed": True},
        {"runtime_started": True},
        {"adapter_called": True},
        {"evidence_acceptance_authorized": True},
        {"pilot_start_authorized": True},
        {"promotion_authorized": True},
    ):
        result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(
            bridge_input,
            **kwargs,
        )
        assert result["bridge_pass"] is False, f"expected fail for {kwargs}"


def test_safety_snapshot_drift_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_snapshot = replace(default_minimal_safety_snapshot(), preflight_remains_blocked=False)
    broken = replace(bridge_input, safety_snapshot=broken_snapshot)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("preflight_remains_blocked must be True" in r for r in result["fail_reasons"])


def test_wrong_bridge_contract_version_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_versions = replace(bridge_input.contract_versions, bridge="wrong.bridge.v0")
    broken = replace(bridge_input, contract_versions=broken_versions)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("contract_versions: bridge must be" in r for r in result["fail_reasons"])


def test_pe38_upstream_still_passes_independently() -> None:
    pe38_input = default_minimal_pe38_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(pe38_input)
    assert result["integration_pass"] is True


def test_admission_upstream_still_passes_independently() -> None:
    admission_input = default_minimal_admission_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(admission_input)
    assert result["integration_pass"] is True


def test_durable_traceability_replay_drift_fails() -> None:
    bridge_input = _valid_bridge_input()
    baseline = evaluate_durable_evidence_traceability_boundary(
        bridge_input.admission_presentation_integration_input.pe37_traceability_boundary_input
    )
    assert baseline["traceability_identity"] is not None
    bound = (baseline["traceability_identity"],)
    broken = replace(
        bridge_input,
        bound_traceability_identities=bound,
        pe38_integration_input=replace(
            bridge_input.pe38_integration_input,
            bound_traceability_identities=bound,
        ),
        admission_presentation_integration_input=replace(
            bridge_input.admission_presentation_integration_input,
            bound_traceability_identities=bound,
        ),
    )
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("replay" in r for r in result["fail_reasons"])


def test_missing_shared_pe37_traceability_identity_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_chain = replace(bridge_input.proof_chain, shared_pe37_traceability_identity="")
    broken = replace(bridge_input, proof_chain=broken_chain)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("shared_pe37_traceability_identity required" in r for r in result["fail_reasons"])


def test_pe38_integration_proof_digest_mismatch_in_proof_binding_fails() -> None:
    bridge_input = _valid_bridge_input()
    broken_proof = replace(
        bridge_input.pe38_readiness_review_proof,
        integration_proof_digest="0" * 64,
    )
    broken = replace(bridge_input, pe38_readiness_review_proof=broken_proof)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_admission_integration_owner_must_match_canonical() -> None:
    bridge_input = _valid_bridge_input()
    broken_proof = replace(
        bridge_input.admission_presentation_lifecycle_proof,
        integration_owner="wrong.owner.v0",
    )
    broken = replace(bridge_input, admission_presentation_lifecycle_proof=broken_proof)
    result = evaluate_readiness_review_admission_presentation_lifecycle_bridge(broken)
    assert result["bridge_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_canonical_owners_match_expected() -> None:
    assert PE38_CONTRACT_VERSION == (
        "bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration.v0"
    )
    assert ADMISSION_LIFECYCLE_CONTRACT_VERSION == (
        "bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration.v0"
    )
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_readiness_review_admission_presentation_lifecycle_bridge.v0"
    )
