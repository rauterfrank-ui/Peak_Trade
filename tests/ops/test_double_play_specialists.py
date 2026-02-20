from __future__ import annotations


def test_double_play_default_off_is_noop():
    from src.ops.double_play.specialists import evaluate_double_play

    d = evaluate_double_play(context={})
    assert d.enabled is False
    assert d.active_specialist in ("bull", "bear")


def test_double_play_enabled_switches_to_bear_on_negative_score():
    from src.ops.double_play.specialists import evaluate_double_play

    d = evaluate_double_play(
        context={
            "double_play_enabled": True,
            "switch_gate": {
                "score": -1.0,
                "state": {"active": "bull", "hold_remaining": 0, "cooldown_remaining": 0},
                "cfg": {"hysteresis": 0.1, "min_hold_steps": 0, "cooldown_steps": 0},
            },
        }
    )
    assert d.enabled is True
    assert d.active_specialist == "bear"


def test_double_play_enabled_stays_bull_in_hysteresis_band():
    from src.ops.double_play.specialists import evaluate_double_play

    d = evaluate_double_play(
        context={
            "double_play_enabled": True,
            "switch_gate": {
                "score": 0.05,
                "state": {"active": "bull", "hold_remaining": 0, "cooldown_remaining": 0},
                "cfg": {"hysteresis": 0.2, "min_hold_steps": 0, "cooldown_steps": 0},
            },
        }
    )
    assert d.active_specialist == "bull"


def test_live_gates_integration_details_contain_double_play():
    """LiveGateResult.details includes double_play (SAFE DEFAULT OFF)."""
    from src.live.live_gates import check_strategy_live_eligibility

    result = check_strategy_live_eligibility("rsi_reversion", context={})
    assert "double_play" in result.details
    dp = result.details["double_play"]
    assert "enabled" in dp
    assert dp.get("active_specialist") in ("bull", "bear")
