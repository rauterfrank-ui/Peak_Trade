from src.research.cross_sectional_realized_volatility_rank_rotation_v0 import (
    EXCLUDED_FAILED_BINDINGS,
    MATERIAL_DIFFERENCE_AXES,
    RealizedVolatilityRankRotationScopeV0,
)


def test_scope_ratification_is_no_eval_no_runtime_no_promotion() -> None:
    scope = RealizedVolatilityRankRotationScopeV0()
    scope.assert_scope_only()
    assert scope.evaluation_authority is False
    assert scope.runtime_authority is False
    assert scope.promotion_granted is False


def test_failed_bindings_are_excluded_not_rescued() -> None:
    scope = RealizedVolatilityRankRotationScopeV0()
    assert "trend_following/v1" in EXCLUDED_FAILED_BINDINGS
    assert "bollinger_bands/v1" in EXCLUDED_FAILED_BINDINGS
    assert "momentum_1h/v1" in EXCLUDED_FAILED_BINDINGS
    assert scope.excludes_binding("trend_following/v1")


def test_material_difference_axes_are_bound() -> None:
    assert "realized_volatility_rank_signal_family" in MATERIAL_DIFFERENCE_AXES
    assert "panel_ohlcv_realized_vol" in MATERIAL_DIFFERENCE_AXES
    assert "non_bitcoin_perpetual_panel_vol_rank" in MATERIAL_DIFFERENCE_AXES
