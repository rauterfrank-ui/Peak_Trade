"""Ratified constants for comparison_ssot.v1."""

from __future__ import annotations

from typing import Final

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    METRIC_KEYS,
    METRIC_SET_VERSION,
    PARETO_DIRECTIONALITY,
    TIE_TOLERANCE_CATALOG,
    TIE_TOLERANCE_VERSION,
)

COMPARISON_CONTRACT_VERSION: Final = "comparison_ssot.v1"
COMPARABILITY_GATE_VERSION: Final = "comparison_gates.v1"
NORMALIZATION_POLICY_VERSION: Final = "NONE_V1"
RANKING_RULE_NONE: Final = "NONE_V1"
LEXICOGRAPHIC_RANKING_RULE_V1: Final = "lexicographic_ranking_v1"
ELIGIBILITY_RULES_VERSION: Final = "comparison_eligibility_rules.v1"
IDENTITY_DOMAIN_SEPARATOR: Final = "peak_trade.comparison_definition.v1"
DEFINITION_ARTIFACT_FILENAME: Final = "comparison_definition_manifest_v1.json"
RESULT_ARTIFACT_FILENAME: Final = "comparison_result_manifest_v1.json"
STAGING_DIRNAME_PREFIX: Final = ".comparison_ssot_staging_"

MIN_INPUT_COUNT: Final = 2
MAX_INPUT_COUNT: Final = 32

ALLOWED_SOURCE_DOMAINS: frozenset[str] = frozenset({"EXPERIMENT", "BACKTEST", "VAR_SUITE"})

LEXICOGRAPHIC_RANKING_SEQUENCE: tuple[tuple[str, str], ...] = (
    ("sharpe", "MAXIMIZE"),
    ("max_drawdown", "MINIMIZE"),
    ("profit_factor", "MAXIMIZE"),
    ("total_return", "MAXIMIZE"),
    ("volatility", "MINIMIZE"),
)

CANONICAL_AUTHORITY_INVARIANTS: dict[str, str | bool] = {
    "comparison_is_descriptive_only": True,
    "comparison_does_not_select": True,
    "comparison_does_not_accept": True,
    "comparison_does_not_promote": True,
    "comparison_does_not_authorize_runtime": True,
    "comparison_does_not_authorize_shadow": True,
    "comparison_does_not_authorize_testnet": True,
    "comparison_does_not_authorize_live": True,
    "comparison_does_not_mutate_inputs": True,
    "comparison_does_not_mutate_strategy_params": True,
    "comparison_does_not_change_trading_logic": True,
    "comparison_does_not_trigger_runs": True,
    "evidence_does_not_authorize_runtime": True,
    "promotion_authority_impact": "NONE",
    "completion_authority_impact": "NONE",
    "runtime_authority_impact": "NONE",
    "trading_logic_impact": "NONE",
    "experiment_config_impact": "NONE",
}

__all__ = [
    "ALLOWED_SOURCE_DOMAINS",
    "CANONICAL_AUTHORITY_INVARIANTS",
    "COMPARABILITY_GATE_VERSION",
    "COMPARISON_CONTRACT_VERSION",
    "DEFINITION_ARTIFACT_FILENAME",
    "ELIGIBILITY_RULES_VERSION",
    "IDENTITY_DOMAIN_SEPARATOR",
    "LEXICOGRAPHIC_RANKING_RULE_V1",
    "LEXICOGRAPHIC_RANKING_SEQUENCE",
    "MAX_INPUT_COUNT",
    "METRIC_KEYS",
    "METRIC_SET_VERSION",
    "MIN_INPUT_COUNT",
    "NORMALIZATION_POLICY_VERSION",
    "PARETO_DIRECTIONALITY",
    "RANKING_RULE_NONE",
    "RESULT_ARTIFACT_FILENAME",
    "STAGING_DIRNAME_PREFIX",
    "TIE_TOLERANCE_CATALOG",
    "TIE_TOLERANCE_VERSION",
]
