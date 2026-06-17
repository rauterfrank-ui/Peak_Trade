"""Static + offline bounded Futures Testnet operator review admission presentation lifecycle integration (v0).

Docs/tests-only. No runtime, network, credentials, operator review, admission, or Testnet start.
PE-34/PE-35/PE-36/PE-37 static lifecycle binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE35_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE35_CONTRACT_VERSION,
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE36_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE36_CONTRACT_VERSION,
    default_minimal_pe35_proof_binding,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
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
    RUN_STARTED,
    IntegrationProofChainBinding,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_operator_review_admission_presentation_lifecycle_integration,
    serialize_integration_input_canonical,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE37_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE37_CONTRACT_VERSION,
    evaluate_durable_evidence_traceability_boundary,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
    HANDOFF_OWNER as PE34_HANDOFF_OWNER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0.py"
)
PE34_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_handoff_boundary_contract_v0.py"
)
PE35_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0.py"
)
PE36_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0.py"
)
PE37_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
REVIEW_IDENTITY = "glb-016-bounded-futures-testnet-operator-review"


def _valid_integration_input(
    source_revision: str = VALID_COMMIT_SHA,
):
    return default_minimal_integration_input(
        source_revision=source_revision,
        instrument=GENERIC_FUTURES_INSTRUMENT,
        review_identity=REVIEW_IDENTITY,
    )


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
        "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
        in INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_upstream_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert (
        "bounded_futures_testnet_operator_review_handoff_boundary_contract_v0" in integration_text
    )
    assert (
        "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0"
        in integration_text
    )
    assert "evaluate_operator_review(" not in integration_text
    assert "import subprocess" not in integration_text
    assert "open(" not in integration_text
    assert PE34_MODULE.exists()
    assert PE35_MODULE.exists()
    assert PE36_MODULE.exists()
    assert PE37_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
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


def test_happy_path_coherent_pe34_pe35_pe36_pe37_composition_passes() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input
    )
    assert result["integration_pass"] is True
    assert result["operator_review_admission_presentation_lifecycle_eligibility"] is True
    assert result["pe34_handoff_bound"] is True
    assert result["pe35_staleness_revocation_recovery_bound"] is True
    assert result["pe36_admission_presentation_bound"] is True
    assert result["pe37_durable_traceability_bound"] is True
    assert result["fail_reasons"] == []
    _assert_all_authorization_flags_false(result)


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        _valid_integration_input()
    )
    assert result["integration_pass"] is True
    assert result["contract_implementation_only"] is True
    assert result["admission_executed"] is False
    assert result["presentation_executed"] is False
    assert result["authority_lift"] is False
    _assert_all_authorization_flags_false(result)


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = _valid_integration_input()
    right = _valid_integration_input()
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_operator_review_admission_presentation_lifecycle_integration(left)
    right_result = evaluate_operator_review_admission_presentation_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]
    assert left_result["integration_proof_digest"] == compute_integration_proof_digest(
        left,
        operator_review_admission_presentation_lifecycle_eligibility=True,
    )


def test_missing_pe34_handoff_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe34_handoff_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe34_handoff_digest required" in r for r in result["fail_reasons"])


def test_stale_handoff_fails() -> None:
    integration_input = _valid_integration_input()
    broken_pe35 = replace(
        integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        integration_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    broken_pe37 = replace(
        integration_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    broken = replace(
        integration_input,
        pe35_boundary_input=broken_pe35,
        pe36_boundary_input=broken_pe36,
        pe37_traceability_boundary_input=broken_pe37,
    )
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False


def test_revoked_handoff_fails() -> None:
    integration_input = _valid_integration_input()
    broken_pe35 = replace(
        integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_REVOKED,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        integration_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    broken_pe37 = replace(
        integration_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    broken = replace(
        integration_input,
        pe35_boundary_input=broken_pe35,
        pe36_boundary_input=broken_pe36,
        pe37_traceability_boundary_input=broken_pe37,
    )
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False


def test_superseded_handoff_fails() -> None:
    integration_input = _valid_integration_input()
    broken_pe35 = replace(
        integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_SUPERSEDED,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        integration_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    broken_pe37 = replace(
        integration_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    broken = replace(
        integration_input,
        pe35_boundary_input=broken_pe35,
        pe36_boundary_input=broken_pe36,
        pe37_traceability_boundary_input=broken_pe37,
    )
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False


def test_source_revision_drift_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        expected_source_revision=ALT_COMMIT_SHA,
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe34_handoff_digest_drift_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        expected_pe34_handoff_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe34_handoff_digest mismatch" in r for r in result["fail_reasons"])


def test_pe35_boundary_result_digest_drift_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        expected_pe35_boundary_result_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe35_boundary_result_digest mismatch" in r for r in result["fail_reasons"])


def test_pe36_presentation_projection_digest_drift_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        expected_pe36_presentation_projection_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe36_presentation_projection_digest mismatch" in r for r in result["fail_reasons"])


def test_pe37_traceability_identity_drift_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        expected_pe37_traceability_identity="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe37_traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_missing_traceability_identity_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe37_traceability_identity="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe37_traceability_identity required" in r for r in result["fail_reasons"])


def test_durable_traceability_drift_fails() -> None:
    integration_input = _valid_integration_input()
    baseline = evaluate_durable_evidence_traceability_boundary(
        integration_input.pe37_traceability_boundary_input
    )
    assert baseline["traceability_identity"] is not None
    broken = replace(
        integration_input,
        bound_traceability_identities=(baseline["traceability_identity"],),
    )
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("replay" in r for r in result["fail_reasons"])


def test_unknown_extra_fields_fail() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        extra_fields={"unexpected_field": "value"},
    )
    assert result["integration_pass"] is False
    assert any("unknown extra field" in r for r in result["fail_reasons"])


def test_secret_credential_command_authority_decision_fields_fail() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        extra_fields={
            "api_key": "secret-value",
            "operator_decision": True,
            "execution_authorized": True,
        },
    )
    assert result["integration_pass"] is False
    assert any("forbidden extra field" in r for r in result["fail_reasons"])


def test_loose_boolean_eligibility_rejected() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input,
        loose_boolean_eligibility=True,
    )
    assert result["integration_pass"] is False
    assert any("loose_boolean_eligibility" in r for r in result["fail_reasons"])


def test_loose_authority_booleans_rejected() -> None:
    integration_input = _valid_integration_input()
    for kwargs in (
        {"readiness_decision_authorized": True},
        {"operator_review_authorized": True},
        {"operator_decision_authorized": True},
        {"operator_closure_authorized": True},
        {"global_blocker_lift_authorized": True},
        {"preflight_lift_authorized": True},
        {"execution_authorized": True},
        {"live_authorized": True},
        {"pilot_start_authorized": True},
        {"promotion_authorized": True},
        {"network_allowed": True},
        {"credentials_allowed": True},
        {"orders_allowed": True},
        {"runtime_started": True},
        {"adapter_called": True},
        {"selected_decision": "approve"},
        {"default_approve": True},
        {"implicit_approve": True},
    ):
        result = evaluate_operator_review_admission_presentation_lifecycle_integration(
            integration_input, **kwargs
        )
        assert result["integration_pass"] is False


def test_wrong_pe34_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe34_handoff_proof,
        handoff_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe34_handoff_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("handoff_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe35_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe35_staleness_proof,
        boundary_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe35_staleness_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("boundary_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe36_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe36_admission_presentation_proof,
        boundary_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe36_admission_presentation_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("boundary_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe37_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe37_traceability_proof,
        traceability_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe37_traceability_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("traceability_owner must be" in r for r in result["fail_reasons"])


def test_inputs_not_mutated() -> None:
    integration_input = _valid_integration_input()
    before = serialize_integration_input_canonical(integration_input)
    evaluate_operator_review_admission_presentation_lifecycle_integration(integration_input)
    after = serialize_integration_input_canonical(integration_input)
    assert before == after


def test_no_file_git_network_subprocess_usage_in_module_text() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "import subprocess" not in integration_text
    assert "import os" not in integration_text
    assert "open(" not in integration_text
    assert "git." not in integration_text
    assert "requests." not in integration_text
    assert "urllib" not in integration_text


def test_no_positive_btc_xbt_spot_fixtures() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    assert integration_input.instrument == GENERIC_FUTURES_INSTRUMENT
    assert "XBT" not in integration_input.instrument
    assert "BTC" not in integration_input.instrument
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        integration_input
    )
    assert result["integration_pass"] is True


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration.v0"
    )


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.global_blocker_lift_authorized is False
    assert snapshot.operator_review_authorized is False
    assert snapshot.futures_only is True


def test_owner_constants_coherent() -> None:
    integration_input = _valid_integration_input()
    assert integration_input.pe34_handoff_proof.handoff_owner == PE34_HANDOFF_OWNER
    assert integration_input.pe35_staleness_proof.boundary_owner == PE35_BOUNDARY_OWNER
    assert integration_input.pe36_admission_presentation_proof.boundary_owner == PE36_BOUNDARY_OWNER
    assert integration_input.pe37_traceability_proof.traceability_owner == PE37_BOUNDARY_OWNER
    assert integration_input.contract_versions.pe34_handoff == PE34_CONTRACT_VERSION
    assert integration_input.contract_versions.pe35_staleness == PE35_CONTRACT_VERSION
    assert integration_input.contract_versions.pe36_admission_presentation == PE36_CONTRACT_VERSION
    assert integration_input.contract_versions.pe37_traceability == PE37_CONTRACT_VERSION


def test_input_mutation_changes_digest() -> None:
    left = _valid_integration_input()
    right = replace(left, integration_id="mutated-integration-id")
    assert compute_integration_input_digest(left) != compute_integration_input_digest(right)
    left_result = evaluate_operator_review_admission_presentation_lifecycle_integration(left)
    right_result = evaluate_operator_review_admission_presentation_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] != right_result["integration_proof_digest"]


def test_no_filesystem_git_network_subprocess_at_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file/archive/environment access not allowed in lifecycle tests")

    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)
    result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        _valid_integration_input()
    )
    assert result["integration_pass"] is True
