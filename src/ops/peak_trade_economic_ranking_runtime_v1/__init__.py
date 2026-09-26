"""B06 Cap 2.2 Peak_Trade economic ranking runtime."""

from src.ops.peak_trade_economic_ranking_runtime_v1.constants_v1 import (
    B06_IMPLEMENTED,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CAPABILITY_ID,
    ECONOMIC_RANK_ACTIVATED,
    OWNER_GO_THIS_SLICE,
)

__all__ = [
    "B06_IMPLEMENTED",
    "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED",
    "CAPABILITY_ID",
    "ECONOMIC_RANK_ACTIVATED",
    "EconomicRankingResultV1",
    "OWNER_GO_THIS_SLICE",
    "build_balanced_movement_scores_v1",
    "classify_and_rank_economic_candidates_v1",
    "midrank_higher_is_better_v1",
    "synthesize_ready_feature_production_snapshot_v1",
]


def __getattr__(name: str):
    if name in {"EconomicRankingResultV1", "classify_and_rank_economic_candidates_v1"}:
        from src.ops.peak_trade_economic_ranking_runtime_v1 import economic_rank_v1 as mod

        return getattr(mod, name)
    if name in {"build_balanced_movement_scores_v1", "midrank_higher_is_better_v1"}:
        from src.ops.peak_trade_economic_ranking_runtime_v1 import score_construction_v1 as mod

        return getattr(mod, name)
    if name == "synthesize_ready_feature_production_snapshot_v1":
        from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
            synthesize_ready_feature_production_snapshot_v1,
        )

        return synthesize_ready_feature_production_snapshot_v1
    raise AttributeError(name)
