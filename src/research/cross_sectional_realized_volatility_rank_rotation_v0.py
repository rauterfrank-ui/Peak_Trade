from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable

STRATEGY_ID: Final[str] = "cross_sectional_realized_volatility_rank_rotation"
STRATEGY_VERSION: Final[str] = "v0"
RUNTIME_AUTHORITY: Final[bool] = False
EVALUATION_AUTHORITY: Final[bool] = False
PROMOTION_GRANTED: Final[bool] = False

EXCLUDED_FAILED_BINDINGS: Final[tuple[str, ...]] = (
    "trend_following/v1",
    "bollinger_bands/v1",
    "momentum_1h/v1",
)

MATERIAL_DIFFERENCE_AXES: Final[tuple[str, ...]] = (
    "realized_volatility_rank_signal_family",
    "volatility_dispersion_rotation",
    "panel_ohlcv_realized_vol",
    "cross_sectional_rank_single_slot_rotation",
    "low_vol_long_high_vol_short",
    "non_bitcoin_perpetual_panel_vol_rank",
)

REUSE_FIRST_DECISION: Final[str] = (
    "REUSE_PIT_CROSS_SECTIONAL_PANEL_DATASET_AND_RELATIVE_STRENGTH_RANKING_SEMANTICS_PATTERN_"
    "WITH_NARROW_REALIZED_VOL_FEATURE_ADAPTER_ONLY"
)


@dataclass(frozen=True)
class RealizedVolatilityRankRotationScopeV0:
    strategy_id: str = STRATEGY_ID
    strategy_version: str = STRATEGY_VERSION
    evaluation_authority: bool = EVALUATION_AUTHORITY
    runtime_authority: bool = RUNTIME_AUTHORITY
    promotion_granted: bool = PROMOTION_GRANTED
    reuse_first_decision: str = REUSE_FIRST_DECISION
    material_difference_axes: tuple[str, ...] = MATERIAL_DIFFERENCE_AXES
    excluded_failed_bindings: tuple[str, ...] = EXCLUDED_FAILED_BINDINGS

    def assert_scope_only(self) -> None:
        if self.evaluation_authority or self.runtime_authority or self.promotion_granted:
            raise RuntimeError(
                "scope ratification must not grant evaluation, runtime, or promotion authority"
            )

    def excludes_binding(self, binding: str) -> bool:
        return binding in self.excluded_failed_bindings

    def material_axes(self) -> Iterable[str]:
        return self.material_difference_axes
