"""RUNBOOK STEP 29M — versioned economic validity policy threshold values v1 tests."""

from __future__ import annotations

from typing import Any

import pytest

from src.backtest import economic_validity_policy_v1 as policy


def _fully_configured_cfg() -> dict[str, Any]:
    canonical = policy.canonical_economic_validity_policy_v1()
    thresholds: dict[str, Any] = {}
    for field_name in policy._NUMERIC_THRESHOLD_FIELDS:
        threshold = getattr(canonical, field_name)
        thresholds[field_name] = threshold.to_dict()
    for field_name in policy._POLICY_REF_FIELDS:
        threshold = getattr(canonical, field_name)
        thresholds[field_name] = threshold.to_dict()
    return {
        "economic_validity_policy": {
            "policy_version": policy.ECONOMIC_VALIDITY_POLICY_VERSION,
            "owner": policy.ECONOMIC_VALIDITY_POLICY_OWNER,
            "thresholds": thresholds,
        }
    }


def _metrics(**overrides: Any) -> policy.EconomicValidityEvidenceMetricsV1:
    base = {
        "net_expectancy": 0.01,
        "profit_factor": 1.5,
        "max_drawdown": -0.10,
        "trade_count": 100,
        "walk_forward_pass_ratio": 0.75,
        "out_of_sample_pass_ratio": 0.75,
        "monte_carlo_pass_ratio": 0.75,
        "stress_failure_count": 0,
        "parameter_robustness_pass": True,
        "parameter_neighbor_degradation": 0.05,
        "single_trade_profit_contribution": 0.10,
        "single_regime_profit_contribution": 0.20,
        "data_admissibility_status": "PASS",
        "cost_model_status": "PASS",
        "funding_binding_status": "PASS",
        "execution_model_status": "PASS",
        "reproducibility_status": "PASS",
        "digest_binding_status": "PASS",
        "manifest_binding_status": "PASS",
    }
    base.update(overrides)
    return policy.EconomicValidityEvidenceMetricsV1(**base)


class TestDefaultPolicyContract:
    def test_policy_version_bound(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        assert p.is_version_bound() is True
        assert p.policy_version == policy.ECONOMIC_VALIDITY_POLICY_VERSION

    def test_default_thresholds_not_configured(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        assert p.thresholds_configured() is False
        assert p.policy_threshold_status() == policy.POLICY_THRESHOLD_STATUS_BLOCKED
        assert len(p.unconfigured_fields()) == len(policy._ALL_THRESHOLD_FIELDS)

    def test_config_digest_stable(self) -> None:
        a = policy.default_economic_validity_policy_v1()
        b = policy.default_economic_validity_policy_v1()
        assert a.config_digest() == b.config_digest()
        assert len(a.config_digest()) == 64

    def test_no_runtime_or_promotion_effect(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        assert p.runtime_effect is False
        assert p.order_effect is False
        assert p.promotion_effect is False
        assert p.authority_effect == "NONE"
        assert p.futures_only is True
        assert p.bitcoin_direction_allowed is False


class TestCanonicalPolicyThresholdValues:
    def test_canonical_policy_contract_pass(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        policy.validate_economic_validity_policy_v1(p)
        assert p.thresholds_configured() is True
        assert p.policy_threshold_status() == policy.POLICY_THRESHOLD_STATUS_PASS

    def test_canonical_digest_deterministic(self) -> None:
        a = policy.canonical_economic_validity_policy_v1()
        b = policy.canonical_economic_validity_policy_v1()
        assert a.policy_digest() == b.policy_digest()

    def test_canonical_threshold_sources_documented(self) -> None:
        sources = policy.canonical_economic_validity_policy_threshold_sources_v1()
        assert (
            sources["minimum_profit_factor"]["classification"] == "REUSED_EXISTING_CANONICAL_VALUE"
        )
        assert sources["minimum_trade_count"]["value"] == "50"


class TestPolicyLoader:
    def test_load_without_section_returns_default(self) -> None:
        p = policy.load_economic_validity_policy_v1({})
        assert p.is_version_bound()
        assert not p.thresholds_configured()

    def test_resolve_step29m_binds_canonical(self) -> None:
        p = policy.resolve_economic_validity_policy_v1({"backtest": {"initial_cash": 10_000.0}})
        assert p.thresholds_configured() is True
        assert p.policy_threshold_status() == policy.POLICY_THRESHOLD_STATUS_PASS

    def test_resolve_explicit_unbound_fail_closed(self) -> None:
        cfg = {"backtest": {}, "economic_validity_policy": {"explicit_unbound": True}}
        p = policy.resolve_economic_validity_policy_v1(cfg)
        assert not p.thresholds_configured()

    def test_load_fully_configured(self) -> None:
        p = policy.load_economic_validity_policy_v1(_fully_configured_cfg())
        assert p.thresholds_configured() is True
        assert p.policy_threshold_status() == policy.POLICY_THRESHOLD_STATUS_PASS

    def test_version_mismatch_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        cfg["economic_validity_policy"]["policy_version"] = "wrong_v9"
        with pytest.raises(policy.EconomicValidityPolicyError, match="policy_version_mismatch"):
            policy.load_economic_validity_policy_v1(cfg)

    def test_missing_policy_version_fail_closed(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        object.__setattr__(p, "policy_version", "")
        with pytest.raises(policy.EconomicValidityPolicyError, match="policy_version_missing"):
            policy.validate_economic_validity_policy_v1(p)

    def test_invalid_threshold_section_rejected(self) -> None:
        with pytest.raises(policy.EconomicValidityPolicyError, match="not_mapping"):
            policy.load_economic_validity_policy_v1({"economic_validity_policy": "bad"})


class TestPolicyValidation:
    def test_validate_default_passes_structure(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        policy.validate_economic_validity_policy_v1(p)

    def test_nan_threshold_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        cfg["economic_validity_policy"]["thresholds"]["minimum_net_expectancy"]["value"] = float(
            "nan"
        )
        p = policy.load_economic_validity_policy_v1(cfg)
        with pytest.raises(
            policy.EconomicValidityPolicyError, match="configured_threshold_non_finite"
        ):
            policy.validate_economic_validity_policy_v1(p)

    def test_positive_inf_threshold_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        cfg["economic_validity_policy"]["thresholds"]["minimum_profit_factor"]["value"] = float(
            "inf"
        )
        p = policy.load_economic_validity_policy_v1(cfg)
        with pytest.raises(
            policy.EconomicValidityPolicyError, match="configured_threshold_non_finite"
        ):
            policy.validate_economic_validity_policy_v1(p)

    def test_negative_inf_threshold_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        cfg["economic_validity_policy"]["thresholds"]["minimum_profit_factor"]["value"] = float(
            "-inf"
        )
        p = policy.load_economic_validity_policy_v1(cfg)
        with pytest.raises(
            policy.EconomicValidityPolicyError, match="configured_threshold_non_finite"
        ):
            policy.validate_economic_validity_policy_v1(p)

    def test_configured_numeric_missing_value_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        del cfg["economic_validity_policy"]["thresholds"]["minimum_trade_count"]["value"]
        with pytest.raises(policy.EconomicValidityPolicyError, match="threshold_value_missing"):
            policy.load_economic_validity_policy_v1(cfg)

    def test_configured_policy_ref_missing_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        del cfg["economic_validity_policy"]["thresholds"]["stress_pass_policy"]["policy_ref"]
        with pytest.raises(
            policy.EconomicValidityPolicyError, match="threshold_policy_ref_missing"
        ):
            policy.load_economic_validity_policy_v1(cfg)

    def test_policy_digest_mismatch_fail_closed(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        with pytest.raises(policy.EconomicValidityPolicyError, match="policy_digest_mismatch"):
            policy.validate_policy_digest_binding_v1(
                policy=p,
                expected_digest="0" * 64,
            )

    def test_threshold_change_without_version_increment_detected(self) -> None:
        before = policy.canonical_economic_validity_policy_v1()
        cfg = _fully_configured_cfg()
        cfg["economic_validity_policy"]["thresholds"]["minimum_net_expectancy"]["value"] = 0.01
        after = policy.load_economic_validity_policy_v1(cfg)
        assert policy.detect_policy_mutation_without_version_change_v1(before=before, after=after)


class TestGateEvaluation:
    def test_missing_thresholds_fail_closed(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(),
        )
        assert result.gates_pass is False
        assert "economic_validity_policy_thresholds_not_configured" in result.reason_codes
        assert result.evaluation_status is policy.EconomicValidityEvaluationStatus.BLOCKED

    def test_all_gates_pass(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(),
            expected_policy_digest=p.policy_digest(),
        )
        assert result.gates_pass is True
        assert result.evaluation_status is policy.EconomicValidityEvaluationStatus.PASS

    def test_net_expectancy_at_boundary_passes(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(net_expectancy=0.0),
            expected_policy_digest=p.policy_digest(),
        )
        assert result.gates_pass is True

    def test_net_expectancy_below_threshold_fails(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(net_expectancy=-0.01),
            expected_policy_digest=p.policy_digest(),
        )
        assert "NET_EXPECTANCY_BELOW_THRESHOLD" in result.reason_codes

    def test_profit_factor_below_threshold_fails(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(profit_factor=1.0),
            expected_policy_digest=p.policy_digest(),
        )
        assert "PROFIT_FACTOR_BELOW_THRESHOLD" in result.reason_codes

    def test_max_drawdown_above_threshold_fails(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(max_drawdown=-0.30),
            expected_policy_digest=p.policy_digest(),
        )
        assert "MAX_DRAWDOWN_ABOVE_THRESHOLD" in result.reason_codes

    def test_trade_count_below_threshold_fails(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(trade_count=10),
            expected_policy_digest=p.policy_digest(),
        )
        assert "TRADE_COUNT_BELOW_THRESHOLD" in result.reason_codes

    def test_walk_forward_fail(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(walk_forward_pass_ratio=0.25),
            expected_policy_digest=p.policy_digest(),
        )
        assert "WALK_FORWARD_FAILED" in result.reason_codes

    def test_oos_fail(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(out_of_sample_pass_ratio=0.25),
            expected_policy_digest=p.policy_digest(),
        )
        assert "OUT_OF_SAMPLE_FAILED" in result.reason_codes

    def test_monte_carlo_fail(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(monte_carlo_pass_ratio=0.0),
            expected_policy_digest=p.policy_digest(),
        )
        assert "MONTE_CARLO_FAILED" in result.reason_codes

    def test_stress_fail(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(stress_failure_count=2),
            expected_policy_digest=p.policy_digest(),
        )
        assert "STRESS_FAILED" in result.reason_codes

    def test_parameter_robustness_fail(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(parameter_robustness_pass=False),
            expected_policy_digest=p.policy_digest(),
        )
        assert "PARAMETER_ROBUSTNESS_FAILED" in result.reason_codes

    def test_single_trade_dominance_exceeded(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(single_trade_profit_contribution=0.9),
            expected_policy_digest=p.policy_digest(),
        )
        assert "SINGLE_TRADE_DOMINANCE_EXCEEDED" in result.reason_codes

    def test_regime_dominance_exceeded(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(single_regime_profit_contribution=0.9),
            expected_policy_digest=p.policy_digest(),
        )
        assert "REGIME_DOMINANCE_EXCEEDED" in result.reason_codes

    def test_data_not_admissible_blocked(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(data_admissibility_status="FAIL"),
            expected_policy_digest=p.policy_digest(),
        )
        assert "DATA_NOT_ADMISSIBLE" in result.reason_codes

    def test_cost_model_not_bound_blocked(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(cost_model_status="FAIL"),
            expected_policy_digest=p.policy_digest(),
        )
        assert "COST_MODEL_NOT_BOUND" in result.reason_codes

    def test_funding_model_not_bound_blocked(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(funding_binding_status="FAIL"),
            expected_policy_digest=p.policy_digest(),
        )
        assert "FUNDING_MODEL_NOT_BOUND" in result.reason_codes

    def test_execution_model_not_bound_blocked(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(execution_model_status="FAIL"),
            expected_policy_digest=p.policy_digest(),
        )
        assert "EXECUTION_MODEL_NOT_BOUND" in result.reason_codes

    def test_digest_binding_failed_blocked(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(digest_binding_status="FAIL"),
            expected_policy_digest=p.policy_digest(),
        )
        assert "DIGEST_BINDING_FAILED" in result.reason_codes

    def test_manifest_binding_failed_blocked(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(manifest_binding_status="FAIL"),
            expected_policy_digest=p.policy_digest(),
        )
        assert "MANIFEST_BINDING_FAILED" in result.reason_codes

    def test_missing_metric_blocked(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(net_expectancy=None),
            expected_policy_digest=p.policy_digest(),
        )
        assert "METRIC_MISSING:net_expectancy" in result.reason_codes
        assert result.evaluation_status is policy.EconomicValidityEvaluationStatus.BLOCKED

    def test_nan_metric_fail_closed(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(profit_factor=float("nan")),
            expected_policy_digest=p.policy_digest(),
        )
        assert "METRIC_NON_FINITE:profit_factor" in result.reason_codes

    def test_hard_fail_not_compensated_by_strong_metrics(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(
                net_expectancy=-1.0,
                profit_factor=99.0,
                trade_count=999,
                walk_forward_pass_ratio=1.0,
            ),
            expected_policy_digest=p.policy_digest(),
        )
        assert result.gates_pass is False
        assert "NET_EXPECTANCY_BELOW_THRESHOLD" in result.reason_codes

    def test_evaluation_independent_of_dict_order(self) -> None:
        p = policy.canonical_economic_validity_policy_v1()
        metrics_a = _metrics(trade_count=10)
        metrics_b = _metrics(trade_count=10)
        result_a = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=metrics_a,
            expected_policy_digest=p.policy_digest(),
        )
        result_b = policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=metrics_b,
            expected_policy_digest=p.policy_digest(),
        )
        assert result_a.reason_codes == result_b.reason_codes

    def test_gate_evaluation_does_not_mutate_policy(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        before = p.to_dict()
        policy.evaluate_economic_validity_against_policy_v1(
            policy=p,
            metrics=_metrics(net_expectancy=999.0),
        )
        assert p.to_dict() == before

    def test_backward_compatible_narrow_gate_eval(self) -> None:
        p = policy.load_economic_validity_policy_v1(_fully_configured_cfg())
        result = policy.evaluate_economic_validity_gates_v1(
            policy=p,
            net_expectancy=0.01,
            profit_factor=1.5,
            max_drawdown=-0.10,
            trade_count=100,
        )
        assert result.gates_pass is True


class TestPolicySchema:
    def test_schema_contract(self) -> None:
        schema = policy.economic_validity_policy_schema_v1()
        assert schema["contract_name"] == "economic_validity_policy_v1"
        assert schema["runtime_effect"] is False
        assert schema["policy_threshold_status_pass"] == policy.POLICY_THRESHOLD_STATUS_PASS
        assert len(schema["numeric_threshold_fields"]) == len(policy._NUMERIC_THRESHOLD_FIELDS)
