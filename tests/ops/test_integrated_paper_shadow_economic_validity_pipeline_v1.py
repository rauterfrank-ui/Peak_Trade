"""Focused contract tests for integrated paper-shadow economic-validity pipeline v1."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_economic_validity_pipeline_v1 import (
    AUTHORITY_EFFECT_NONE,
    CANONICAL_PIPELINE_SEQUENCE,
    FORBIDDEN_ECONOMIC_PASS_EVIDENCE_CLASSES,
    LEGACY_OFFLINE_GATE_ROLE,
    LEGACY_OFFLINE_GATE_TOKEN,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    IntegratedPaperShadowEconomicValidityEvidenceInputV1,
    IntegratedPaperShadowEconomicValidityPipelineError,
    default_repo_pipeline_result_v1,
    evaluate_economic_validity_pass_v1,
    evaluate_integrated_paper_shadow_economic_validity_pipeline_v1,
    evaluate_paper_shadow_observation_readiness_v1,
    load_legacy_offline_gate_false_only,
    readiness_ignores_legacy_offline_gate,
)
from src.governance.promotion_loop import promotion_economic_gate_v1 as promo

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "ops" / "integrated_paper_shadow_economic_validity_pipeline_v1.toml"
CONTRACT_DOC = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "runbooks"
    / "INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1.md"
)
RUNBOOK = (
    REPO_ROOT / "docs" / "governance" / "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md"
)


def _readiness_ok(**overrides: object) -> IntegratedPaperShadowEconomicValidityEvidenceInputV1:
    base = {
        "full_canonical_system_parity": True,
        "system_correctness_pass": True,
        "integrated_offline_replay_pass": True,
        "backtest_runtime_decision_parity_pass": True,
        "canonical_decision_chain_bound": True,
        "master_v2_double_play_sole_decision_authority": True,
        "ai_layer_non_authority": True,
        "safety_kernel_killstate_fail_closed": True,
        "broker_write_path_unreachable": True,
        "order_authority_absent": True,
        "simulated_portfolio_fill_fee_slippage_pnl_model_defined": True,
        "evidence_directory_manifest_schema_config_digests_verifier_defined": True,
        "session_preregistration_and_operator_go_contract_present": True,
        "economic_validity_offline_gate_pass": False,
    }
    base.update(overrides)
    return IntegratedPaperShadowEconomicValidityEvidenceInputV1(**base)  # type: ignore[arg-type]


def _economic_bundle_ok(
    **overrides: object,
) -> IntegratedPaperShadowEconomicValidityEvidenceInputV1:
    base = {
        "integrated_economic_evidence_bundle_verified": True,
        "offline_economic_evidence_complete": True,
        "integrated_paper_shadow_evidence_complete": True,
        "fees_slippage_stops_fill_exposure_turnover_drawdown_present": True,
        "walk_forward_monte_carlo_stress_requirements_met": True,
        "digests_manifests_config_bindings_provenance_consistent": True,
        "economic_validity_operator_ratification": True,
        "economic_validity_offline_gate_pass": False,
        "single_positive_paper_shadow_run_only": False,
        "historical_terminal_negative_evidence_rebadged": False,
        "evidence_class": "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE",
    }
    base.update(overrides)
    return IntegratedPaperShadowEconomicValidityEvidenceInputV1(**base)  # type: ignore[arg-type]


def test_package_identity_and_config_defaults() -> None:
    assert PACKAGE_MARKER == "INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1=true"
    assert PRODUCER_FAMILY == "ops.integrated_paper_shadow_economic_validity_pipeline_v1"
    assert CONFIG.is_file()
    text = CONFIG.read_text(encoding="utf-8")
    assert "economic_validity_pass = false" in text
    assert "paper_shadow_observation_authorized = false" in text
    assert "orders_authorized = false" in text
    assert LEGACY_OFFLINE_GATE_TOKEN in text
    assert LEGACY_OFFLINE_GATE_ROLE in text


def test_1_legacy_offline_false_does_not_block_paper_shadow_readiness() -> None:
    evidence = _readiness_ok(economic_validity_offline_gate_pass=False)
    ready, blockers = evaluate_paper_shadow_observation_readiness_v1(evidence)
    assert ready is True
    assert not any("ECONOMIC_VALIDITY_OFFLINE_GATE" in b for b in blockers)
    assert readiness_ignores_legacy_offline_gate(
        economic_validity_offline_gate_pass=False, evidence=evidence
    )


def test_2_missing_correctness_parity_safety_preconditions_fail_closed() -> None:
    for field in (
        "system_correctness_pass",
        "integrated_offline_replay_pass",
        "backtest_runtime_decision_parity_pass",
        "safety_kernel_killstate_fail_closed",
        "broker_write_path_unreachable",
        "order_authority_absent",
    ):
        evidence = _readiness_ok(**{field: False})
        ready, blockers = evaluate_paper_shadow_observation_readiness_v1(evidence)
        assert ready is False
        assert any(
            field.upper() in b or field.replace("_", "_").upper() in b for b in blockers
        ) or any("FALSE" in b for b in blockers)
        evidence_missing = _readiness_ok(**{field: None})
        ready_m, blockers_m = evaluate_paper_shadow_observation_readiness_v1(evidence_missing)
        assert ready_m is False
        assert any("MISSING_FAIL_CLOSED" in b for b in blockers_m)


def test_3_and_4_readiness_never_implies_authorization() -> None:
    evidence = _readiness_ok(paper_shadow_observation_operator_go=None)
    result = evaluate_integrated_paper_shadow_economic_validity_pipeline_v1(evidence=evidence)
    assert result.paper_shadow_observation_readiness_pass is True
    assert result.paper_shadow_observation_authorized is False
    # Even synthetic GO must not flip capability authorization emission.
    evidence_go = _readiness_ok(paper_shadow_observation_operator_go=True)
    result_go = evaluate_integrated_paper_shadow_economic_validity_pipeline_v1(evidence=evidence_go)
    assert result_go.paper_shadow_observation_authorized is False


def test_5_paper_shadow_evidence_never_auto_sets_economic_validity_pass() -> None:
    evidence = _economic_bundle_ok(
        integrated_paper_shadow_evidence_complete=True,
        offline_economic_evidence_complete=False,
        integrated_economic_evidence_bundle_verified=False,
        economic_validity_operator_ratification=False,
    )
    passed, blockers = evaluate_economic_validity_pass_v1(evidence)
    assert passed is False
    assert any("OFFLINE_ECONOMIC_EVIDENCE_COMPLETE" in b for b in blockers)


def test_6_economic_validity_false_without_offline_evidence() -> None:
    evidence = _economic_bundle_ok(offline_economic_evidence_complete=False)
    passed, blockers = evaluate_economic_validity_pass_v1(evidence)
    assert passed is False
    assert any("OFFLINE_ECONOMIC_EVIDENCE_COMPLETE" in b for b in blockers)


def test_7_economic_validity_false_without_paper_shadow_evidence() -> None:
    evidence = _economic_bundle_ok(integrated_paper_shadow_evidence_complete=False)
    passed, blockers = evaluate_economic_validity_pass_v1(evidence)
    assert passed is False
    assert any("INTEGRATED_PAPER_SHADOW_EVIDENCE_COMPLETE" in b for b in blockers)


def test_8_economic_validity_false_on_contradictory_provenance() -> None:
    evidence = _economic_bundle_ok(digests_manifests_config_bindings_provenance_consistent=False)
    passed, blockers = evaluate_economic_validity_pass_v1(evidence)
    assert passed is False
    assert any("DIGESTS_MANIFESTS_CONFIG_BINDINGS_PROVENANCE" in b for b in blockers)


def test_9_single_positive_paper_shadow_run_insufficient() -> None:
    evidence = _economic_bundle_ok(single_positive_paper_shadow_run_only=True)
    passed, blockers = evaluate_economic_validity_pass_v1(evidence)
    assert passed is False
    assert "SINGLE_POSITIVE_PAPER_SHADOW_RUN_INSUFFICIENT" in blockers


def test_10_promotion_blocked_without_economic_validity_pass() -> None:
    result = default_repo_pipeline_result_v1()
    assert result.economic_validity_pass is False
    assert result.promotion_pass is False
    assert any(
        "PROMOTION_BLOCKED_WITHOUT_ECONOMIC_VALIDITY_PASS" in b for b in result.authority_blockers
    )

    # Promotion economic gate: offline alone must not yield system pass without bundle.
    policy = promo.canonical_promotion_economic_gate_policy_v1()
    from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1

    digest = canonical_economic_validity_policy_v1().policy_digest()
    input_data = promo.PromotionEconomicGateInputV1(
        strategy_id="mv2_offline_research",
        strategy_version="v1",
        candidate_id="candidate-001",
        economic_viability_evidence_ref="evidence://admissible/futures/v1/bundle-001",
        economic_validity_status=promo.PASS_STATUS,
        economic_validity_proven=True,
        profitability_claim_allowed=True,
        robustness_status=promo.PASS_STATUS,
        data_admissibility_status=promo.PASS_STATUS,
        evidence_admissibility_status=promo.PASS_STATUS,
        policy_threshold_status=promo.PASS_STATUS,
        walk_forward_status=promo.PASS_STATUS,
        out_of_sample_status=promo.PASS_STATUS,
        monte_carlo_status=promo.PASS_STATUS,
        stress_status=promo.PASS_STATUS,
        parameter_sensitivity_status=promo.PASS_STATUS,
        reproducibility_status=promo.PASS_STATUS,
        digest_binding_status=promo.PASS_STATUS,
        manifest_binding_status=promo.PASS_STATUS,
        safety_policy_status=promo.PASS_STATUS,
        futures_only=True,
        bitcoin_direction_allowed=False,
        config_digest="a" * 64,
        implementation_digest="b" * 64,
        policy_digest=digest,
        evidence_manifest_digest="c" * 64,
        dataset_digest="d" * 64,
        robustness_result_digests=("wf:" + "e" * 61,),
        safety_policy_digest="f" * 64,
        evidence_admissible=True,
        economic_validity_offline_gate_pass=True,
        integrated_economic_evidence_bundle_verified=False,
        offline_economic_evidence_complete=True,
        integrated_paper_shadow_evidence_complete=False,
    )
    gate_result = promo.evaluate_promotion_economic_gate_v1(
        policy=policy,
        input_data=input_data,
        evaluation_timestamp="2026-07-29T00:00:00Z",
    )
    assert gate_result.economic_validity_pass is False
    assert gate_result.promotion_eligible is False


def test_11_testnet_and_live_blocked_without_operator_gos() -> None:
    result = evaluate_integrated_paper_shadow_economic_validity_pipeline_v1(
        evidence=_readiness_ok(testnet_operator_go=None, live_operator_go=None)
    )
    assert result.testnet_authorized is False
    assert result.live_authorized is False
    assert any("TESTNET_OPERATOR_GO_ABSENT" in b for b in result.authority_blockers)
    assert any("LIVE_OPERATOR_GO_ABSENT" in b for b in result.authority_blockers)


def test_12_orders_independently_blocked() -> None:
    result = evaluate_integrated_paper_shadow_economic_validity_pipeline_v1(
        evidence=_readiness_ok(orders_operator_go=True)
    )
    assert result.orders_authorized is False
    assert "ORDERS_AUTHORIZED_INDEPENDENTLY_BLOCKED" in result.authority_blockers


def test_13_forbidden_evidence_classes_cannot_set_economic_pass() -> None:
    for evidence_class in sorted(FORBIDDEN_ECONOMIC_PASS_EVIDENCE_CLASSES):
        evidence = _economic_bundle_ok(evidence_class=evidence_class)
        passed, blockers = evaluate_economic_validity_pass_v1(evidence)
        assert passed is False
        assert any(evidence_class in b for b in blockers)


def test_14_legacy_configs_false_only_or_fail_closed() -> None:
    assert load_legacy_offline_gate_false_only(False) is False
    assert load_legacy_offline_gate_false_only(None) is False
    assert load_legacy_offline_gate_false_only("false") is False
    with pytest.raises(IntegratedPaperShadowEconomicValidityPipelineError):
        load_legacy_offline_gate_false_only(True)
    with pytest.raises(IntegratedPaperShadowEconomicValidityPipelineError):
        load_legacy_offline_gate_false_only("unknown")


def test_15_historical_terminal_negative_evidence_not_accepted() -> None:
    evidence = _economic_bundle_ok(historical_terminal_negative_evidence_rebadged=True)
    passed, blockers = evaluate_economic_validity_pass_v1(evidence)
    assert passed is False
    assert "HISTORICAL_TERMINAL_NEGATIVE_EVIDENCE_REBADGED_REJECTED" in blockers


def test_16_repo_defaults_preserve_safety_invariants() -> None:
    result = default_repo_pipeline_result_v1()
    assert result.authority_effect == AUTHORITY_EFFECT_NONE
    assert result.paper_shadow_observation_authorized is False
    assert result.testnet_authorized is False
    assert result.live_authorized is False
    assert result.orders_authorized is False
    assert result.economic_validity_pass is False
    assert result.promotion_pass is False
    assert result.economic_validity_offline_gate_pass is False
    assert result.canonical_pipeline_sequence == CANONICAL_PIPELINE_SEQUENCE


def test_contract_and_runbook_document_new_ladder() -> None:
    assert CONTRACT_DOC.is_file()
    contract = CONTRACT_DOC.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    for token in (
        "PAPER_SHADOW_OBSERVATION_READINESS_PASS",
        "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED",
        "ECONOMIC_VALIDITY_PASS",
        "LEGACY_OFFLINE_SUB_EVIDENCE_ONLY",
        "ZERO_ORDER_CONNECTIVITY_OR_RUNTIME_EVIDENCE",
        "INTEGRATED_PAPER_SHADOW_OBSERVATION",
    ):
        assert token in contract, token
    assert "INTEGRATED_PAPER_SHADOW_OBSERVATION_READINESS_PASS" in runbook
    assert "LEGACY_OFFLINE_SUB_EVIDENCE_ONLY" in runbook
