"""GVEF domain evaluators (BWP-3 through BWP-6). AUTHORITY=NONE."""

from __future__ import annotations

from src.evaluation.golden_vectors.evaluators.market_intelligence_v1 import (
    MARKET_INTELLIGENCE_EVALUATOR_ID,
    MarketIntelligenceEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.optimization_universe_v1 import (
    OPTIMIZATION_UNIVERSE_EVALUATOR_ID,
    OptimizationUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.productive_trading_path_v1 import (
    PRODUCTIVE_TRADING_PATH_EVALUATOR_ID,
    ProductiveTradingPathEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.ranking_universe_v1 import (
    RANKING_UNIVERSE_EVALUATOR_ID,
    RankingUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.self_learning_v1 import (
    SELF_LEARNING_EVALUATOR_ID,
    SelfLearningEvaluatorV1,
)

__all__ = [
    "PRODUCTIVE_TRADING_PATH_EVALUATOR_ID",
    "ProductiveTradingPathEvaluatorV1",
    "RANKING_UNIVERSE_EVALUATOR_ID",
    "RankingUniverseEvaluatorV1",
    "OPTIMIZATION_UNIVERSE_EVALUATOR_ID",
    "OptimizationUniverseEvaluatorV1",
    "SELF_LEARNING_EVALUATOR_ID",
    "SelfLearningEvaluatorV1",
    "MARKET_INTELLIGENCE_EVALUATOR_ID",
    "MarketIntelligenceEvaluatorV1",
]
