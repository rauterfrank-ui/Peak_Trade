"""Tests for policy v1 cost/edge gate."""

from src.observability.policy.policy_v1 import decide_policy_v1


def test_policy_v1_blocks_live():
    d = {"inputs": {"current_price": 100.0}, "costs": {"fees_bp": 1.0}, "forecast": {"mu_bp": 100.0}}
    p = decide_policy_v1(env="live", decision=d)
    assert p.action == "NO_TRADE"
    assert "ENV_LIVE" in p.reason_codes


def test_policy_v1_missing_current_price_no_trade():
    d = {"inputs": {}, "costs": {"fees_bp": 1.0}}
    p = decide_policy_v1(env="paper", decision=d)
    assert p.action == "NO_TRADE"
    assert "MISSING_CURRENT_PRICE" in p.reason_codes


def test_policy_v1_missing_costs_no_trade():
    d = {"inputs": {"current_price": 100.0}}
    p = decide_policy_v1(env="paper", decision=d)
    assert p.action == "NO_TRADE"
    assert "MISSING_COSTS_V1" in p.reason_codes


def test_policy_v1_edge_lt_costs_no_trade():
    d = {
        "inputs": {"current_price": 100.0},
        "costs": {"fees_bp": 2.0, "slippage_bp": 2.0, "impact_bp": 1.0, "latency_bp": 0.0},
        "forecast": {"mu_bp": 4.0},  # costs=5 => 4 <= 5+1 buffer => NO_TRADE
    }
    p = decide_policy_v1(env="paper", decision=d)
    assert p.action == "NO_TRADE"
    assert "EDGE_LT_COSTS_V1" in p.reason_codes


def test_policy_v1_edge_gt_costs_allow():
    d = {
        "inputs": {"current_price": 100.0},
        "costs": {"fees_bp": 1.0, "slippage_bp": 1.0, "impact_bp": 0.0, "latency_bp": 0.0},
        "forecast": {"mu_bp": 5.0},  # costs=2 => 5 > 2+1 buffer => ALLOW
    }
    p = decide_policy_v1(env="paper", decision=d)
    assert p.action == "ALLOW"
    assert "EDGE_GT_COSTS_V1" in p.reason_codes
