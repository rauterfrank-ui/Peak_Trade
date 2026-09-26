"""B05 Cap 2.1 / Input-2 ranking feature production (raw B03 features only)."""

from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    B05_IMPLEMENTED,
    CAPABILITY_ID,
    OWNER_GO_THIS_SLICE,
)

__all__ = [
    "B05_IMPLEMENTED",
    "CAPABILITY_ID",
    "OWNER_GO_THIS_SLICE",
    "classify_peak_trade_ranking_feature_production_v1",
    "compute_b03_ratified_raw_features_pure_v1",
    "produce_ranking_feature_production_snapshot_v1",
    "produce_raw_ranking_features_for_instrument_v1",
    "validate_ranking_feature_production_snapshot_v1",
]


def __getattr__(name: str):
    from src.ops.peak_trade_ranking_feature_production_v1 import producer_v1 as mod

    if name in __all__ and hasattr(mod, name):
        return getattr(mod, name)
    raise AttributeError(name)
