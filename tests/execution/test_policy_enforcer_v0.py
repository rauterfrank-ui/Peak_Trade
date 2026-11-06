"""Tests for PolicyEnforcerV0."""

from src.execution.policy import PolicyEnforcerV0


def test_policy_enforcer_off_allows():
    en = PolicyEnforcerV0(enforce=False)
    res = en.evaluate(env="paper", policy={"action": "NO_TRADE", "reason_codes": ["X"]})
    assert res.allowed is True
    assert res.reason_code == "POLICY_ENFORCE_OFF"


def test_policy_enforcer_blocks_live():
    en = PolicyEnforcerV0(enforce=True)
    res = en.evaluate(env="live", policy={"action": "ALLOW"})
    assert res.allowed is False
    assert res.reason_code == "ENV_LIVE"


def test_policy_enforcer_blocks_no_trade():
    en = PolicyEnforcerV0(enforce=True)
    res = en.evaluate(
        env="paper", policy={"action": "NO_TRADE", "reason_codes": ["NO_MODEL_EDGE_V0"]}
    )
    assert res.allowed is False
    assert res.reason_code == "NO_TRADE"
