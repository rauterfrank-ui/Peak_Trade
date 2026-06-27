"""Ratified constants for comparison_metric_input.v1."""

from __future__ import annotations

from typing import Final, Literal

COMPARISON_METRIC_INPUT_CONTRACT_VERSION: Final = "comparison_metric_input.v1"
METRIC_SET_VERSION: Final = "comparison_metrics.v1"
METRIC_SEMANTICS_VERSION: Final = "comparison_metric_semantics.v1"
COMPARABILITY_METADATA_VERSION: Final = "comparison_comparability_metadata.v1"
PARETO_DIRECTIONALITY_VERSION: Final = "comparison_metric_directionality.v1"
TIE_TOLERANCE_VERSION: Final = "comparison_metric_tolerances.v1"
IDENTITY_DOMAIN_SEPARATOR: Final = "peak_trade.comparison_metric_input.v1"
ARTIFACT_FILENAME: Final = "comparison_metric_input_manifest_v1.json"
SOURCE_DIGEST_RULE_VERSION: Final = "equity_trade_source_digest_v1"
STAGING_DIRNAME_PREFIX: Final = ".comparison_metric_input_staging_"
MINIMUM_RETURN_OBSERVATIONS: Final = 2

ALLOWED_SOURCE_DOMAINS: frozenset[str] = frozenset({"EXPERIMENT", "BACKTEST", "VAR_SUITE"})

METRIC_KEYS: tuple[str, ...] = (
    "sharpe",
    "max_drawdown",
    "profit_factor",
    "total_return",
    "volatility",
    "trade_count",
)

ANNUALIZATION_PROFILE_V1: dict[str, int] = {
    "1m": 525600,
    "5m": 105120,
    "15m": 35040,
    "1h": 8760,
    "4h": 2190,
    "1d": 252,
    "1w": 52,
}

MetricDirection = Literal[
    "MAXIMIZE",
    "MINIMIZE",
    "ELIGIBILITY_ONLY_NOT_OBJECTIVE",
]

PARETO_DIRECTIONALITY: dict[str, MetricDirection] = {
    "sharpe": "MAXIMIZE",
    "max_drawdown": "MINIMIZE",
    "profit_factor": "MAXIMIZE",
    "total_return": "MAXIMIZE",
    "volatility": "MINIMIZE",
    "trade_count": "ELIGIBILITY_ONLY_NOT_OBJECTIVE",
}

TIE_TOLERANCE_CATALOG: dict[str, float | None] = {
    "sharpe": 1e-10,
    "max_drawdown": 1e-12,
    "profit_factor": 1e-10,
    "total_return": 1e-12,
    "volatility": 1e-10,
    "trade_count": None,
}

CANONICAL_AUTHORITY_INVARIANTS: dict[str, str | bool] = {
    "evidence_does_not_authorize_runtime": True,
    "promotion_authority_impact": "NONE",
    "runtime_authority_impact": "NONE",
    "trading_logic_impact": "NONE",
}

COMPARISON_METRIC_INPUT_AUTHORITY_FLAGS: dict[str, bool | str] = {
    "comparison_metric_input_is_offline_only": True,
    "comparison_metric_input_does_not_compare": True,
    "comparison_metric_input_does_not_rank": True,
    "comparison_metric_input_does_not_select": True,
    "comparison_metric_input_does_not_accept": True,
    "comparison_metric_input_does_not_promote": True,
    "comparison_metric_input_does_not_authorize_runtime": True,
    "comparison_metric_input_does_not_authorize_shadow": True,
    "comparison_metric_input_does_not_authorize_testnet": True,
    "comparison_metric_input_does_not_authorize_live": True,
    "comparison_metric_input_does_not_mutate_sources": True,
    "evidence_does_not_authorize_runtime": True,
    "promotion_authority_impact": "NONE",
    "completion_authority_impact": "NONE",
    "runtime_authority_impact": "NONE",
    "trading_logic_impact": "NONE",
    "experiment_config_impact": "NONE",
}

BACKTEST_OWNER_DOMAIN: Final = "experiments/tracking"
EXPERIMENT_OWNER_DOMAIN: Final = "experiments/base"
VAR_SUITE_OWNER_DOMAIN: Final = "risk/validation/var_suite_backtest_wiring_v1"
