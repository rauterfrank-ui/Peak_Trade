"""R6 S4 multi-future shadow/sim evidence tests (offline, unauthorized, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    R6S3RuntimeArchitectureError,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    default_single_future_request_v1,
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    FIXTURE_INSTRUMENT_A,
    FIXTURE_INSTRUMENT_B,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    NEGATIVE_CASE_IDS,
    S4_AUTHORIZED,
    S4_EVIDENCE_PREPARED,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.models_v1 import (
    R6S4ShadowSimEvidenceError,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.negative_v1 import (
    run_negative_matrix_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.producer_v1 import (
    produce_shadow_sim_evidence_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.verifier_v1 import (
    evaluate_r6_s4_multi_future_shadow_sim_evidence_v1,
    validate_layer_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_authorization_flags_remain_fail_closed() -> None:
    assert MULTI_FUTURE_RUNTIME_IMPLEMENTED is True
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert S4_AUTHORIZED is False
    assert S4_EVIDENCE_PREPARED is True
    assert CURRENT_EFFECTIVE_RUNTIME_MODE == "SINGLE_SELECTED_FUTURE"
    assert MAX_POSITIONS_EFFECTIVE == 1


def test_shadow_sim_evidence_uses_two_instrument_contexts_without_authorization() -> None:
    bundle = produce_shadow_sim_evidence_v1()
    body = bundle["body"]
    assert FIXTURE_INSTRUMENT_A in body["instrument_contexts"]
    assert FIXTURE_INSTRUMENT_B in body["instrument_contexts"]
    assert body["state_isolation"][FIXTURE_INSTRUMENT_A] == FIXTURE_INSTRUMENT_A
    assert body["state_isolation"][FIXTURE_INSTRUMENT_B] == FIXTURE_INSTRUMENT_B
    assert body["active_set"]["effective_active_ids"] == [FIXTURE_INSTRUMENT_A]
    assert body["active_set"]["top_n_active_set_authority"] is False
    assert body["authority"]["multi_future_runtime_authorized"] is False
    assert body["authority"]["s4_authorized"] is False
    assert body["authority"]["current_effective_runtime_mode"] == "SINGLE_SELECTED_FUTURE"
    assert body["authority"]["max_positions_effective"] == 1
    assert body["simulated_execution"]["order_effect"] == "NONE"
    assert body["simulated_execution"]["network_effect"] == "NONE"
    assert body["simulated_execution"]["account_mutation_effect"] == "NONE"
    assert body["simulated_execution"]["exchange_submit_attempted"] is False
    assert body["source_evidence"]["s3_config"]["status"] == "MANIFEST_VERIFIED"
    assert body["source_evidence"]["external"]["status"] == "NOT_REFERENCED"
    assert len(bundle["identity"]["experiment_identity_id"]) == 64
    assert bundle["manifest"]["content_hash"] == bundle["evidence_digest"]
    second = produce_shadow_sim_evidence_v1()
    assert second["evidence_digest"] == bundle["evidence_digest"]
    assert (
        second["identity"]["experiment_identity_id"] == bundle["identity"]["experiment_identity_id"]
    )


def test_portfolio_risk_and_arbitration_are_recorded() -> None:
    body = produce_shadow_sim_evidence_v1()["body"]
    assert body["portfolio_risk"]["s2_consumed"] is True
    assert body["portfolio_risk"]["second_risk_engine_created"] is False
    assert body["portfolio_risk"]["numeric_policy_status"] == "DEFERRED_UNRATIFIED"
    assert body["portfolio_risk"]["zero_correlation_optimistic_fallback_forbidden"] is True
    assert body["portfolio_risk"]["sim_instrument_context_count"] == 2
    assert body["portfolio_risk"]["effective_active_count"] == 1
    assert body["arbitration"]["identical_input_identical_order"] is True
    assert body["reconciliation"]["per_instrument"][FIXTURE_INSTRUMENT_A] == "RECONCILED"
    assert body["restart"]["authorized_after_restart"] is False


def test_negative_matrix_is_complete_and_fail_closed() -> None:
    results = run_negative_matrix_v1()
    assert tuple(results) == NEGATIVE_CASE_IDS
    for case_id, row in results.items():
        assert row["fail_closed"] is True, case_id


def test_single_future_authorized_behavior_unchanged() -> None:
    result = evaluate_phase_82_graph_v1(
        default_single_future_request_v1("BTC-USDT-SWAP", extra_candidates=("ETH-USDT-SWAP",))
    )
    assert result.effective_active_ids == ("BTC-USDT-SWAP",)
    assert result.max_positions_effective == 1
    assert result.authorized is False
    assert result.submit_unlocked is False
    assert cap23.MAX_POSITIONS_EFFECTIVE == 1
    assert cap23.MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert getattr(cap72, "MULTI_FUTURE_RUNTIME_IMPLEMENTED", False) is False


def test_evidence_pass_cannot_be_read_as_authorization() -> None:
    claims = evaluate_r6_s4_multi_future_shadow_sim_evidence_v1()
    assert claims["verdict"] == "PASS_R6_S4_MULTI_FUTURE_SHADOW_SIM_EVIDENCE_V1"
    assert claims["r6_s4_status"] == "PREPARED"
    assert claims["s4_authorized"] is False
    assert claims["s4_evidence_prepared"] is True
    assert claims["evidence_is_not_authorization"] is True
    assert claims["multi_future_runtime_authorized"] is False
    assert claims["multi_future_runtime_implemented"] is True
    assert claims["g13_unchanged"] is True
    assert claims["current_effective_runtime_mode"] == "SINGLE_SELECTED_FUTURE"
    assert claims["max_positions_effective"] == 1
    assert claims["second_execution_authority_created"] is False
    assert claims["second_accounting_authority_created"] is False
    assert claims["live_authorized"] is False
    assert claims["testnet_authorized"] is False
    assert claims["canary_authorized"] is False
    assert claims["funding_runtime_activated"] is False
    assert claims["network_effect"] == "NONE"
    assert claims["order_effect"] == "NONE"
    assert claims["account_mutation_effect"] == "NONE"
    assert claims["multi_instrument_sim_evidence"] is True
    assert claims["state_isolation_evidence"] is True
    assert claims["deterministic_arbitration_evidence"] is True
    assert claims["portfolio_risk_evidence"] is True
    assert claims["per_instrument_recon_evidence"] is True
    assert claims["restart_recovery_evidence"] is True
    assert claims["fail_closed_negative_evidence"] is True
    assert claims["single_global_execution_writer_proven"] is True
    assert claims["single_global_accounting_writer_proven"] is True
    assert claims["single_future_authorized_behavior_unchanged"] is True
    assert claims["s5_authorization_granted"] is False
    assert claims["next_stage_automatically_authorized"] is False


def test_config_cannot_authorize_or_raise_positions() -> None:
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_authorized"] = True
    with pytest.raises(R6S4ShadowSimEvidenceError, match="multi_future_runtime_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["s4_authorized"] = True
    with pytest.raises(R6S4ShadowSimEvidenceError, match="s4_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_positions_effective"] = 2
    with pytest.raises(R6S4ShadowSimEvidenceError, match="max_positions_effective"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["submit_unlocked"] = True
    with pytest.raises(R6S4ShadowSimEvidenceError, match="submit_unlocked"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["evidence_is_not_authorization"] = False
    with pytest.raises(R6S4ShadowSimEvidenceError, match="evidence_is_not_authorization"):
        validate_layer_config_v1(payload)


def test_s3_unauthorized_activation_still_rejected() -> None:
    request = default_single_future_request_v1("AAA-FUT")
    with pytest.raises(R6S3RuntimeArchitectureError, match="authorized_rejected"):
        evaluate_phase_82_graph_v1(
            request.__class__(
                selected_future_id=request.selected_future_id,
                ranking_candidates=request.ranking_candidates,
                instrument_contexts=request.instrument_contexts,
                requested_authorized=True,
            )
        )
