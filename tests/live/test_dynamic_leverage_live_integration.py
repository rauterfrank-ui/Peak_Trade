from __future__ import annotations


def test_dynamic_leverage_default_off():
    from src.live.dynamic_leverage_live import evaluate_dynamic_leverage_for_live

    d = evaluate_dynamic_leverage_for_live(context={})
    assert d.enabled is False
    assert d.leverage is None
    assert "cap" in d.details
    assert d.details["cap"] == 50.0


def test_dynamic_leverage_enabled_caps_at_50():
    from src.live.dynamic_leverage_live import evaluate_dynamic_leverage_for_live

    d = evaluate_dynamic_leverage_for_live(
        context={
            "dynamic_leverage_enabled": True,
            "strength": 1.0,
            "dynamic_leverage_cfg": {"min_leverage": 1.0, "max_leverage": 50.0, "gamma": 2.0},
        }
    )
    assert d.enabled is True
    assert d.leverage == 50.0


def test_dynamic_leverage_invalid_cfg_fails_closed():
    from src.live.dynamic_leverage_live import evaluate_dynamic_leverage_for_live

    d = evaluate_dynamic_leverage_for_live(
        context={
            "dynamic_leverage_enabled": True,
            "strength": 1.0,
            "dynamic_leverage_cfg": {"min_leverage": 10.0, "max_leverage": 5.0, "gamma": 2.0},
        }
    )
    assert d.enabled is False
    assert d.leverage is None
    assert any("dynamic_leverage_exception" in r for r in d.reasons)


def test_live_gates_integration_details_contain_dynamic_leverage():
    """LiveGateResult.details includes dynamic_leverage (SAFE DEFAULT OFF)."""
    from src.live.live_gates import check_strategy_live_eligibility

    # Use a strategy that exists in tiering (or mock); minimal: we need a result
    result = check_strategy_live_eligibility(
        "rsi_reversion",  # common fixture strategy
        context={},
    )
    assert "dynamic_leverage" in result.details
    dl = result.details["dynamic_leverage"]
    assert "enabled" in dl
    assert dl.get("cap") == 50.0
