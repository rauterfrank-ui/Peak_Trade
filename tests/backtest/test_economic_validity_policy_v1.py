"""RUNBOOK STEP 29M — versioned economic validity policy v1 contract tests."""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping

import pytest

from src.backtest import economic_validity_policy_v1 as policy


def _fully_configured_cfg() -> dict[str, Any]:
    return {
        "economic_validity_policy": {
            "policy_version": policy.ECONOMIC_VALIDITY_POLICY_VERSION,
            "owner": policy.ECONOMIC_VALIDITY_POLICY_OWNER,
            "thresholds": {
                "minimum_net_expectancy": {"status": "CONFIGURED", "value": 0.0},
                "minimum_profit_factor": {"status": "CONFIGURED", "value": 1.0},
                "maximum_max_drawdown": {"status": "CONFIGURED", "value": 0.25},
                "walk_forward_stability_threshold": {"status": "CONFIGURED", "value": 0.5},
                "out_of_sample_pass_policy": {
                    "status": "CONFIGURED",
                    "policy_ref": "oos_pass_v1",
                },
                "parameter_robustness_policy": {
                    "status": "CONFIGURED",
                    "policy_ref": "param_robust_v1",
                },
                "monte_carlo_pass_policy": {
                    "status": "CONFIGURED",
                    "policy_ref": "mc_pass_v1",
                },
                "stress_pass_policy": {"status": "CONFIGURED", "policy_ref": "stress_pass_v1"},
                "minimum_trade_count": {"status": "CONFIGURED", "value": 10.0},
                "single_trade_dominance_limit": {"status": "CONFIGURED", "value": 0.5},
                "regime_dominance_limit": {"status": "CONFIGURED", "value": 0.6},
            },
        }
    }


class TestDefaultPolicyContract:
    def test_policy_version_bound(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        assert p.is_version_bound() is True
        assert p.policy_version == policy.ECONOMIC_VALIDITY_POLICY_VERSION

    def test_default_thresholds_not_configured(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        assert p.thresholds_configured() is False
        assert p.policy_threshold_status() == policy.POLICY_THRESHOLD_STATUS_BLOCKED
        assert len(p.unconfigured_fields()) == 11

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


class TestPolicyLoader:
    def test_load_without_section_returns_default(self) -> None:
        p = policy.load_economic_validity_policy_v1({})
        assert p.is_version_bound()
        assert not p.thresholds_configured()

    def test_load_fully_configured(self) -> None:
        p = policy.load_economic_validity_policy_v1(_fully_configured_cfg())
        assert p.thresholds_configured() is True
        assert p.policy_threshold_status() == "CONFIGURED"

    def test_version_mismatch_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        cfg["economic_validity_policy"]["policy_version"] = "wrong_v9"
        with pytest.raises(policy.EconomicValidityPolicyError, match="policy_version_mismatch"):
            policy.load_economic_validity_policy_v1(cfg)

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

    def test_inf_threshold_rejected(self) -> None:
        cfg = _fully_configured_cfg()
        cfg["economic_validity_policy"]["thresholds"]["minimum_profit_factor"]["value"] = float(
            "inf"
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


class TestGateEvaluation:
    def test_missing_thresholds_fail_closed(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        result = policy.evaluate_economic_validity_gates_v1(
            policy=p,
            net_expectancy=1.0,
            profit_factor=2.0,
            max_drawdown=-0.05,
            trade_count=100,
        )
        assert result.gates_pass is False
        assert "economic_validity_policy_thresholds_not_configured" in result.reason_codes

    def test_configured_gates_pass(self) -> None:
        p = policy.load_economic_validity_policy_v1(_fully_configured_cfg())
        result = policy.evaluate_economic_validity_gates_v1(
            policy=p,
            net_expectancy=0.01,
            profit_factor=1.5,
            max_drawdown=-0.10,
            trade_count=20,
        )
        assert result.gates_pass is True
        assert result.reason_codes == ()

    def test_configured_gates_fail_on_expectancy(self) -> None:
        p = policy.load_economic_validity_policy_v1(_fully_configured_cfg())
        result = policy.evaluate_economic_validity_gates_v1(
            policy=p,
            net_expectancy=-0.01,
            profit_factor=1.5,
            max_drawdown=-0.10,
            trade_count=20,
        )
        assert result.gates_pass is False
        assert "gate_failed:minimum_net_expectancy" in result.reason_codes

    def test_configured_gates_fail_on_drawdown(self) -> None:
        p = policy.load_economic_validity_policy_v1(_fully_configured_cfg())
        result = policy.evaluate_economic_validity_gates_v1(
            policy=p,
            net_expectancy=0.01,
            profit_factor=1.5,
            max_drawdown=-0.30,
            trade_count=20,
        )
        assert result.gates_pass is False
        assert "gate_failed:maximum_max_drawdown" in result.reason_codes

    def test_gate_evaluation_does_not_mutate_policy(self) -> None:
        p = policy.default_economic_validity_policy_v1()
        before = p.to_dict()
        policy.evaluate_economic_validity_gates_v1(
            policy=p,
            net_expectancy=999.0,
            profit_factor=999.0,
            max_drawdown=-0.01,
            trade_count=999,
        )
        assert p.to_dict() == before


class TestPolicySchema:
    def test_schema_contract(self) -> None:
        schema = policy.economic_validity_policy_schema_v1()
        assert schema["contract_name"] == "economic_validity_policy_v1"
        assert schema["runtime_effect"] is False
        assert len(schema["numeric_threshold_fields"]) == 7
        assert len(schema["policy_ref_fields"]) == 4
