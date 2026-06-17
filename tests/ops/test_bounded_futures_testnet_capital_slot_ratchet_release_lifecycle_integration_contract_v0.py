"""Static + offline bounded Futures Testnet capital slot ratchet/release lifecycle integration (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
PE-23 static PE-12 reconciliation_review capital slot ratchet/release binding only.
"""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_TINY_ORDER,
)
from src.ops.bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLOBAL_CAPITAL_SLOT_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_CAPITAL_REALLOCATION_EXECUTED,
    OPERATIVE_RATCHET_APPLIED,
    OPERATIVE_RESERVE_MOVEMENT_EXECUTED,
    OPERATIVE_SLOT_RELEASE_EXECUTED,
    PACKAGE_MARKER,
    TESTNET_RUN_STARTED,
    ActivityMetricsBinding,
    CapitalSlotConfigBinding,
    CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    CapitalSlotSpecProof,
    CapitalSlotStateBinding,
    ContractVersionsInput,
    EquityBasisBinding,
    IntegrationSafetySnapshot,
    LifecycleMatrixProof,
    LifecycleStateBinding,
    ObservationWindowBinding,
    Pe22UpstreamSafetyProof,
    RatchetEvaluationProof,
    RatchetStageBinding,
    ReleaseEligibilityProof,
    ReserveTopupBlockProof,
    SlotIdentityBinding,
    compute_activity_metrics_digest,
    compute_capital_slot_spec_digest,
    compute_equity_basis_digest,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    compute_observation_window_digest,
    compute_pe22_upstream_safety_digest,
    compute_ratchet_stage_digest,
    compute_slot_identity_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_capital_slot_ratchet_release_lifecycle_integration,
    evaluate_ratchet_static_proof,
    evaluate_release_static_proof,
    serialize_integration_input_canonical,
    validate_capital_slot_ratchet_release_lifecycle_integration_input,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import FOLLOWUP_RUN_GATE
from src.trading.master_v2.double_play_capital_slot import (
    DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION,
    CapitalSlotReleaseReason,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py"
)
CAPITAL_SLOT_MODULE = REPO_ROOT / "src" / "trading" / "master_v2" / "double_play_capital_slot.py"
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)
PE22_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_CAPITAL_SLOT_RATCHET_RELEASE_LIFECYCLE_INTEGRATION_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_CAPITAL_SLOT_RATCHET_RELEASE_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in INTEGRATION_MODULE.read_text(encoding="utf-8")


def test_pe12_capital_slot_pe22_owners_referenced_not_duplicated() -> None:
    lifecycle_text = LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE12_PACKAGE_MARKER in lifecycle_text
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert "double_play_capital_slot" in integration_text
    assert (
        "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert "evaluate_capital_slot_ratchet" in integration_text
    assert "evaluate_capital_slot_release" in integration_text
    assert "evaluate_phase_transition" not in integration_text
    assert CAPITAL_SLOT_MODULE.exists()
    assert PE22_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATIVE_RATCHET_APPLIED is False
    assert OPERATIVE_SLOT_RELEASE_EXECUTED is False
    assert OPERATIVE_CAPITAL_REALLOCATION_EXECUTED is False
    assert OPERATIVE_RESERVE_MOVEMENT_EXECUTED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert AUTHORITY_LIFT is False
    assert GLOBAL_CAPITAL_SLOT_READINESS is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_capital_slot_ratchet_release_lifecycle_integration(left)
    right_result = evaluate_capital_slot_ratchet_release_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]


def test_valid_settled_equity_ratchet_binding_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["pe12_capital_slot_ratchet_release_static_integration_proven"] is True
    assert result["integration_proof_digest"] == compute_integration_proof_digest(
        integration_input,
        pe23_proven=True,
        release_eligibility_proven=False,
    )
    assert result["fail_reasons"] == []
    assert integration_input.ratchet_evaluation_proof.can_ratchet is True


def test_valid_inactivity_release_eligibility_passes() -> None:
    integration_input = default_minimal_integration_input(
        source_revision=VALID_COMMIT_SHA,
        release_eligible=True,
    )
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["release_eligibility_proven"] is True
    assert integration_input.release_eligibility_proof.release_reason_code == (
        CapitalSlotReleaseReason.INACTIVITY.value
    )


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        default_minimal_integration_input()
    )
    assert result["integration_pass"] is True
    assert result["operative_ratchet_applied"] is False
    assert result["operative_slot_release_executed"] is False
    assert result["operative_capital_reallocation_executed"] is False
    assert result["operative_reserve_movement_executed"] is False
    assert result["lifecycle_transition_executed"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False
    assert result["contract_implementation_only"] is True
    assert result["capital_reallocation_authorized"] is False
    assert result["reserve_topup_allowed"] is False


def test_missing_capital_slot_spec_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_spec = replace(integration_input.capital_slot_spec_proof, spec_digest="")
    bad = replace(integration_input, capital_slot_spec_proof=bad_spec)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("capital_slot_spec_proof: spec_digest required" in r for r in result["fail_reasons"])


def test_missing_pe12_lifecycle_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(integration_input.lifecycle_matrix_proof, lifecycle_matrix_digest="")
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "lifecycle_matrix_proof: lifecycle_matrix_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe22_safety_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe22 = replace(integration_input.pe22_upstream_safety_proof, integration_proof_digest="")
    bad = replace(integration_input, pe22_upstream_safety_proof=bad_pe22)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe22_upstream_safety_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        integration_input,
        expected_source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_incomplete_commit_sha_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision="abc123")
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("source_revision must be full 40-char" in r for r in result["fail_reasons"])


def test_unknown_contract_version_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_versions = replace(
        integration_input.contract_versions,
        integration="unknown.integration.v99",
    )
    bad = replace(integration_input, contract_versions=bad_versions)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("contract_versions: integration must be" in r for r in result["fail_reasons"])


def test_instrument_slot_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_slot = replace(
        integration_input.slot_identity,
        selected_future="PF_SOLUSD",
        slot_digest="",
    )
    bad_slot = replace(bad_slot, slot_digest=compute_slot_identity_digest(bad_slot))
    bad = replace(integration_input, slot_identity=bad_slot)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("selected_future must match instrument" in r for r in result["fail_reasons"])


def test_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        lifecycle_matrix_digest="f" * 64,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_matrix_digest mismatch" in r for r in result["fail_reasons"])


def test_negative_equity_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_state = replace(integration_input.capital_slot_state, active_slot_base=-1.0)
    bad_equity = replace(
        integration_input.equity_basis,
        current_slot_basis=-1.0,
        basis_digest="",
    )
    bad_equity = replace(bad_equity, basis_digest=compute_equity_basis_digest(bad_equity))
    bad = replace(integration_input, capital_slot_state=bad_state, equity_basis=bad_equity)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("current_slot_basis must be non-negative" in r for r in result["fail_reasons"])


def test_nan_infinity_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_state = replace(
        integration_input.capital_slot_state,
        realized_or_settled_slot_equity=math.nan,
    )
    bad_equity = replace(
        integration_input.equity_basis,
        new_settled_realized_equity=math.nan,
        basis_digest="",
    )
    bad_equity = replace(bad_equity, basis_digest=compute_equity_basis_digest(bad_equity))
    bad = replace(integration_input, capital_slot_state=bad_state, equity_basis=bad_equity)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("must be finite" in r for r in result["fail_reasons"])


def test_settled_realized_equity_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_equity = replace(integration_input.equity_basis, new_settled_realized_equity=999.0)
    bad_equity = replace(
        bad_equity,
        basis_digest=compute_equity_basis_digest(bad_equity),
    )
    bad = replace(integration_input, equity_basis=bad_equity)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("settled/realized equity mismatch" in r for r in result["fail_reasons"])


def test_unrealized_equity_as_reset_basis_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_equity = replace(integration_input.equity_basis, use_unrealized_as_reset_basis=True)
    bad_equity = replace(
        bad_equity,
        basis_digest=compute_equity_basis_digest(bad_equity),
    )
    bad = replace(integration_input, equity_basis=bad_equity)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("use_unrealized_as_reset_basis must be false" in r for r in result["fail_reasons"])


def test_reserve_topup_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_config = replace(integration_input.capital_slot_config, allow_auto_top_up=True)
    bad = replace(integration_input, capital_slot_config=bad_config)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("allow_auto_top_up must be false" in r for r in result["fail_reasons"])


def test_unallowable_slot_basis_increase_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_equity = replace(
        integration_input.equity_basis,
        current_slot_basis=500.0,
        new_settled_realized_equity=340.0,
        basis_digest="",
    )
    bad_equity = replace(bad_equity, basis_digest=compute_equity_basis_digest(bad_equity))
    bad_state = replace(integration_input.capital_slot_state, active_slot_base=500.0)
    bad = replace(integration_input, equity_basis=bad_equity, capital_slot_state=bad_state)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("unallowable slot basis increase" in r for r in result["fail_reasons"])


def test_unallowable_ratchet_jump_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.ratchet_evaluation_proof,
        can_ratchet=True,
        new_active_slot_base=999.0,
    )
    bad = replace(integration_input, ratchet_evaluation_proof=bad_proof)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("new_active_slot_base mismatch" in r for r in result["fail_reasons"])


def test_missing_ratchet_stage_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_stage = replace(integration_input.ratchet_stage, stage_digest="")
    bad = replace(integration_input, ratchet_stage=bad_stage)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("ratchet_stage: stage_digest required" in r for r in result["fail_reasons"])


def test_inactivity_window_incomplete_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_window = replace(
        integration_input.inactivity_observation_window,
        duration_seconds=0,
        end_epoch=integration_input.inactivity_observation_window.start_epoch,
    )
    bad = replace(integration_input, inactivity_observation_window=bad_window)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("inactivity_observation_window" in r for r in result["fail_reasons"])


def test_opportunity_cost_window_incomplete_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_window = ObservationWindowBinding(
        window_id="bad-window",
        window_digest="",
        start_epoch=100,
        end_epoch=200,
        duration_seconds=50,
    )
    bad = replace(integration_input, opportunity_cost_observation_window=bad_window)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "opportunity_cost_observation_window: duration_seconds mismatch" in r
        for r in result["fail_reasons"]
    )


def test_missing_activity_metric_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_metrics = replace(integration_input.activity_metrics, realized_volatility=-1.0)
    bad_metrics = replace(
        bad_metrics,
        metrics_digest=compute_activity_metrics_digest(bad_metrics),
    )
    bad = replace(integration_input, activity_metrics=bad_metrics)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("realized_volatility must be non-negative" in r for r in result["fail_reasons"])


def test_manipulated_release_reason_code_fails() -> None:
    integration_input = default_minimal_integration_input(release_eligible=True)
    bad_release = replace(
        integration_input.release_eligibility_proof,
        release_reason_code="fabricated_reason",
    )
    bad = replace(integration_input, release_eligibility_proof=bad_release)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("release_reason_code mismatch" in r for r in result["fail_reasons"])


def test_release_eligible_without_proof_chain_fails() -> None:
    integration_input = default_minimal_integration_input(release_eligible=True)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        integration_input,
        release_eligible_without_proof_chain=True,
    )
    assert result["integration_pass"] is False
    assert any("without full proof chain" in r for r in result["fail_reasons"])


def test_unsupported_lifecycle_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase="unsupported_phase",
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_lifecycle_slot_contradiction_fails() -> None:
    integration_input = default_minimal_integration_input(release_eligible=True)
    bad_release = replace(
        integration_input.release_eligibility_proof,
        release_reason_code=CapitalSlotReleaseReason.INACTIVITY.value,
        release_eligible=True,
        released=True,
        proof_pass=True,
    )
    bad_metrics = replace(
        integration_input.activity_metrics,
        realized_volatility=0.9,
        atr_or_range=0.9,
        time_without_cashflow_step=0,
        metrics_digest="",
    )
    bad_metrics = replace(
        bad_metrics,
        metrics_digest=compute_activity_metrics_digest(bad_metrics),
    )
    bad = replace(
        integration_input,
        release_eligibility_proof=bad_release,
        activity_metrics=bad_metrics,
    )
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("release_eligible mismatch" in r for r in result["fail_reasons"])


def test_positive_reallocation_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        integration_input,
        capital_reallocation_authorized=True,
    )
    assert result["integration_pass"] is False
    assert any("capital_reallocation_authorized=true" in r for r in result["fail_reasons"])


def test_positive_reserve_movement_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        integration_input,
        reserve_movement_authorized=True,
    )
    assert result["integration_pass"] is False
    assert any("reserve_movement_authorized=true" in r for r in result["fail_reasons"])


def test_positive_network_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, network_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_allowed must be False" in r for r in result["fail_reasons"])


def test_positive_runtime_execution_authority_live_flags_fail() -> None:
    integration_input = default_minimal_integration_input()
    for flag_name, kwarg in (
        ("execution_authorized", {"execution_authorized": True}),
        ("live_authorized", {"live_authorized": True}),
        ("runtime_started", {"runtime_started": True}),
        ("network_run_started", {"network_run_started": True}),
    ):
        result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
            integration_input,
            **kwarg,
        )
        assert result["integration_pass"] is False, flag_name
        assert result["fail_reasons"]


def test_positive_credential_order_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        integration_input,
        credentials_allowed=True,
    )
    assert result["integration_pass"] is False
    assert any("credentials_allowed=true" in r for r in result["fail_reasons"])
    result2 = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        integration_input,
        orders_allowed=True,
    )
    assert result2["integration_pass"] is False
    assert any("orders_allowed=true" in r for r in result2["fail_reasons"])


@pytest.mark.parametrize(
    "instrument",
    ["BTC/EUR", "BTCUSDT", "PF_XBTUSD"],
)
def test_btc_xbt_spot_oriented_input_fails(instrument: str) -> None:
    integration_input = default_minimal_integration_input(instrument=instrument)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False


def test_safety_snapshot_drift_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, followup_run_gate="AUTO_GO")
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("followup_run_gate must be" in r for r in result["fail_reasons"])


def test_capital_slot_model_reused_not_duplicated() -> None:
    integration_input = default_minimal_integration_input()
    static_ratchet = evaluate_ratchet_static_proof(
        config_binding=integration_input.capital_slot_config,
        state_binding=integration_input.capital_slot_state,
        slot_identity=integration_input.slot_identity,
        activity_metrics=integration_input.activity_metrics,
    )
    static_release = evaluate_release_static_proof(
        config_binding=integration_input.capital_slot_config,
        state_binding=integration_input.capital_slot_state,
        slot_identity=integration_input.slot_identity,
        activity_metrics=integration_input.activity_metrics,
    )
    assert static_ratchet["can_ratchet"] is True
    assert static_release["release_eligible"] is False


def test_pilot_envelope_operator_closure_not_included() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "pilot_envelope" not in integration_text.lower()
    assert "operator_closure" not in integration_text.lower()


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_capital_slot_spec_digest_matches_canonical_identity() -> None:
    digest = compute_capital_slot_spec_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.capital_slot_spec_proof.spec_digest == digest


def test_contract_version_constants() -> None:
    assert (
        CONTRACT_VERSION
        == "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration.v0"
    )


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.capital_reallocation_authorized is False
    assert snapshot.reserve_topup_allowed is False
    assert snapshot.followup_run_gate == FOLLOWUP_RUN_GATE


def test_generic_futures_instrument_passes() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_lifecycle_before_must_be_tiny_order() -> None:
    integration_input = default_minimal_integration_input()
    bad_before = replace(
        integration_input.lifecycle_state_before,
        assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
    )
    bad = replace(integration_input, lifecycle_state_before=bad_before)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_before" in r for r in result["fail_reasons"])


def test_lifecycle_after_must_be_reconciliation_review() -> None:
    integration_input = default_minimal_integration_input()
    bad_after = replace(
        integration_input.declared_lifecycle_state_after,
        assigned_lifecycle_phase=PHASE_TINY_ORDER,
    )
    bad = replace(integration_input, declared_lifecycle_state_after=bad_after)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("declared_lifecycle_state_after" in r for r in result["fail_reasons"])


def test_pe22_upstream_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe22 = replace(integration_input.pe22_upstream_safety_proof, proof_digest="0" * 64)
    bad = replace(integration_input, pe22_upstream_safety_proof=bad_pe22)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe22_upstream_safety_proof: proof_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe22_upstream_integration_pass_false_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe22 = replace(integration_input.pe22_upstream_safety_proof, pe22_integration_pass=False)
    bad_pe22 = replace(
        bad_pe22,
        proof_digest=compute_pe22_upstream_safety_digest(bad_pe22),
    )
    bad = replace(integration_input, pe22_upstream_safety_proof=bad_pe22)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe22_integration_pass must be true" in r for r in result["fail_reasons"])


def test_observation_window_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_window = replace(
        integration_input.inactivity_observation_window,
        window_digest="0" * 64,
    )
    bad = replace(integration_input, inactivity_observation_window=bad_window)
    result = evaluate_capital_slot_ratchet_release_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "inactivity_observation_window: window_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_validate_input_returns_sorted_unique_fail_reasons() -> None:
    integration_input = default_minimal_integration_input(source_revision="short")
    reasons = validate_capital_slot_ratchet_release_lifecycle_integration_input(integration_input)
    assert reasons == sorted(set(reasons))
