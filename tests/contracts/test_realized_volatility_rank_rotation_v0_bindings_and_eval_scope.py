from scripts.ops.ratify_cross_sectional_realized_volatility_rank_rotation_v0_bindings_and_eval_scope_v0 import (
    load_binding,
    validate_binding,
)


def test_bindings_validate() -> None:
    validate_binding(load_binding())


def test_scope_does_not_authorize_evaluation_execution_runtime_or_promotion() -> None:
    binding = load_binding()
    assert binding["evaluation_execution_authorized"] is False
    assert binding["runtime_authority_touched"] is False
    assert binding["promotion_granted"] is False


def test_cost_realism_and_no_retry_rescue_are_bound() -> None:
    binding = load_binding()
    assert binding["cost_execution_bindings"]["no_implicit_zero_cost_backtest"] is True
    assert binding["parameter_binding"]["unchanged_retry_or_threshold_rescue_allowed"] is False


def test_failed_bindings_remain_excluded() -> None:
    binding = load_binding()
    assert binding["excluded_failed_bindings"] == [
        "trend_following/v1",
        "bollinger_bands/v1",
        "momentum_1h/v1",
    ]
