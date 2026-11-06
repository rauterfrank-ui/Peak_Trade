from __future__ import annotations


def test_operator_wiring_defaults_off():
    from src.live.operator_context import OperatorWiringInput, build_live_context_from_operator

    ctx = build_live_context_from_operator(inp=OperatorWiringInput())
    assert ctx["double_play_enabled"] is False
    assert ctx["dynamic_leverage_enabled"] is False
    assert ctx["enabled"] is False
    assert ctx["armed"] is False


def test_operator_wiring_enables_features_when_all_conditions_true():
    from src.live.operator_context import OperatorWiringInput, build_live_context_from_operator
    from src.ops.double_play.specialists import evaluate_double_play
    from src.live.dynamic_leverage_live import evaluate_dynamic_leverage_for_live

    ctx = build_live_context_from_operator(
        inp=OperatorWiringInput(
            enabled=True,
            armed=True,
            confirm_token_present=True,
            allow_double_play=True,
            allow_dynamic_leverage=True,
            strength=1.0,
            switch_gate={
                "score": -1.0,
                "state": {
                    "active": "bull",
                    "hold_remaining": 0,
                    "cooldown_remaining": 0,
                },
                "cfg": {"hysteresis": 0.1, "min_hold_steps": 0, "cooldown_steps": 0},
            },
            dynamic_leverage_cfg={
                "min_leverage": 1.0,
                "max_leverage": 50.0,
                "gamma": 2.0,
            },
        )
    )

    assert ctx["double_play_enabled"] is True
    assert ctx["dynamic_leverage_enabled"] is True

    dp = evaluate_double_play(context=ctx)
    assert dp.enabled is True
    assert dp.active_specialist == "bear"

    dl = evaluate_dynamic_leverage_for_live(context=ctx)
    assert dl.enabled is True
    assert dl.leverage == 50.0
