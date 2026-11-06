from __future__ import annotations

from src.live.feature_activation import evaluate_feature_activation


def test_defaults_fail_closed():
    a = evaluate_feature_activation(context={})
    assert a.allow_double_play is False
    assert a.allow_dynamic_leverage is False
    assert "not_enabled" in a.reasons_double_play
    assert "not_armed" in a.reasons_double_play
    assert "confirm_token_missing_or_invalid" in a.reasons_double_play


def test_requires_all_conditions_and_allow_flags():
    ctx = {
        "enabled": True,
        "armed": True,
        "confirm_token_present": True,
        "allow_double_play": True,
        "allow_dynamic_leverage": True,
    }
    a = evaluate_feature_activation(context=ctx)
    assert a.allow_double_play is True
    assert a.allow_dynamic_leverage is True


def test_denies_when_allow_flags_false_even_if_armed():
    ctx = {"enabled": True, "armed": True, "confirm_token_present": True}
    a = evaluate_feature_activation(context=ctx)
    assert a.allow_double_play is False
    assert a.allow_dynamic_leverage is False
    assert "allow_double_play_false" in a.reasons_double_play
    assert "allow_dynamic_leverage_false" in a.reasons_dynamic_leverage


def test_live_gates_integration_details_contain_features():
    """LiveGateResult.details includes features (activation gate)."""
    from src.live.live_gates import check_strategy_live_eligibility

    result = check_strategy_live_eligibility("rsi_reversion", context={})
    assert "features" in result.details
    f = result.details["features"]
    assert "enabled" in f
    assert "armed" in f
    assert "allow_double_play" in f
    assert "allow_dynamic_leverage" in f
