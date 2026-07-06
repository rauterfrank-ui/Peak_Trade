"""Post-PR4941 material-different offline-only research scope discovery and ratification prep v0.

Deterministic, fail-closed validation of scope discovery output after PR4939/PR4940
terminal negative evidence. No economic evaluation, no binding ratification, no runtime
or order effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_"
    "RATIFICATION_PREP_V0=true"
)

SCHEMA_VERSION = (
    "post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep.v0"
)
SCOPE_ID = (
    "POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_V0"
)
CONFIG_REL_PATH = (
    "config/research/post_pr4941_material_different_offline_only_research_scope_"
    "discovery_and_ratification_prep_v0.json"
)
GO_TOKEN = (
    "GO_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_"
    "RATIFICATION_PREP_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
PROCESS_CLASSIFICATION = (
    "MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP"
)
SCOPE_CLASSIFICATION = (
    "PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_"
    "PREP_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
VERDICT = "SCOPE_DISCOVERY_AND_RATIFICATION_PREP_COMPLETE"
SELECTED_NEXT_SCOPE_BOUNDARY = "cross_sectional_realized_volatility_rank_rotation/v0"
SELECTED_STRATEGY_ID = "cross_sectional_realized_volatility_rank_rotation"
SELECTED_STRATEGY_VERSION = "v0"
BASE_HEAD = "f75e32a19f6708c8be1ab313636a1f0047e6cab1"
EXCLUDED_FAILED_BINDINGS = (
    "trend_following/v1",
    "bollinger_bands/v1",
    "momentum_1h/v1",
)
REQUIRED_MATERIAL_DIFFERENCE_AXES = (
    "signal_family:realized_volatility_rank_vs_price_return_rank_funding_score_single_slot_trend_mr_momentum",
    "target_phenomenon:volatility_dispersion_rotation_hypothesis",
    "data_feature_class:panel_ohlcv_derived_realized_volatility",
    "portfolio_aggregation:cross_sectional_rank_single_slot_rotation",
    "entry_exit_hypothesis:low_realized_vol_long_high_realized_vol_short",
    "universe_ranking:non_bitcoin_perpetual_panel_volatility_rank",
)

REQUIRED_CONTRACT_FLAGS: tuple[tuple[str, Any], ...] = (
    ("scope_discovery_and_ratification_prep_only", True),
    ("ratification_prep_only", True),
    ("discovery_and_ratification_prep_only", True),
    ("offline_only", True),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_executed", False),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("unchanged_retry_allowed", False),
    ("negative_evidence_terminal_for_unchanged_bindings", True),
    ("economic_validity_offline_gate_pass", False),
    ("runtime_rewire_admissible", False),
    ("live_authorized", False),
    ("no_runtime_authority", True),
    ("market_airport_excluded", True),
    ("futures_only", True),
    ("bitcoin_direction_allowed", False),
)


@dataclass(frozen=True)
class DiscoveryValidationResultV0:
    valid: bool
    reasons: tuple[str, ...]


def validate_discovery_config_v0(
    config: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
) -> DiscoveryValidationResultV0:
    reasons: list[str] = []

    if config.get("scope_id") != SCOPE_ID:
        reasons.append("UNEXPECTED_SCOPE_ID")
    if config.get("go_token") != GO_TOKEN:
        reasons.append("UNEXPECTED_GO_TOKEN")
    if config.get("verdict") != VERDICT:
        reasons.append("UNEXPECTED_VERDICT")
    if config.get("process_classification") != PROCESS_CLASSIFICATION:
        reasons.append("UNEXPECTED_PROCESS_CLASSIFICATION")
    if config.get("scope_classification") != SCOPE_CLASSIFICATION:
        reasons.append("UNEXPECTED_SCOPE_CLASSIFICATION")
    if config.get("selected_next_scope_boundary") != SELECTED_NEXT_SCOPE_BOUNDARY:
        reasons.append("UNEXPECTED_SELECTED_NEXT_SCOPE_BOUNDARY")
    if config.get("selected_strategy_id") != SELECTED_STRATEGY_ID:
        reasons.append("UNEXPECTED_SELECTED_STRATEGY_ID")
    if config.get("selected_strategy_version") != SELECTED_STRATEGY_VERSION:
        reasons.append("UNEXPECTED_SELECTED_STRATEGY_VERSION")
    if list(config.get("excluded_failed_bindings", [])) != list(EXCLUDED_FAILED_BINDINGS):
        reasons.append("EXCLUDED_FAILED_BINDINGS_MISMATCH")

    axes = config.get("material_difference_axes", [])
    if list(axes) != list(REQUIRED_MATERIAL_DIFFERENCE_AXES):
        reasons.append("MATERIAL_DIFFERENCE_AXES_MISMATCH")

    for field, expected in REQUIRED_CONTRACT_FLAGS:
        if config.get(field) is not expected:
            reasons.append(f"CONTRACT_FLAG_MISMATCH:{field}")

    inventory = config.get("candidate_family_inventory", [])
    selected = [entry for entry in inventory if entry.get("disposition") == "SELECTED_RECOMMENDED"]
    if len(selected) != 1:
        reasons.append("EXACTLY_ONE_SELECTED_CANDIDATE_FAMILY_REQUIRED")
    elif selected[0].get("candidate_family") != SELECTED_NEXT_SCOPE_BOUNDARY:
        reasons.append("SELECTED_INVENTORY_FAMILY_MISMATCH")

    blocked = set(config.get("blocked_actions", []))
    for forbidden in (
        "THRESHOLD_LOWERING",
        "UNCHANGED_BINDING_RETRY",
        "EVALUATION_EXECUTION_IN_THIS_SCOPE",
        "BINDING_RATIFICATION_IN_THIS_SCOPE",
        "MARKET_AIRPORT",
        "LIVE",
        "ORDERS",
    ):
        if forbidden not in blocked:
            reasons.append(f"MISSING_BLOCKED_ACTION:{forbidden}")

    if repo_root is not None and not (repo_root / CONFIG_REL_PATH).is_file():
        reasons.append("CONFIG_OWNER_MISSING")

    return DiscoveryValidationResultV0(valid=not reasons, reasons=tuple(reasons))


def load_discovery_config_v0(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{CONFIG_REL_PATH}")
    return payload


__all__ = [
    "BASE_HEAD",
    "CONFIG_REL_PATH",
    "EXCLUDED_FAILED_BINDINGS",
    "GO_TOKEN",
    "PROCESS_CLASSIFICATION",
    "REQUIRED_MATERIAL_DIFFERENCE_AXES",
    "SCOPE_CLASSIFICATION",
    "SCOPE_ID",
    "SELECTED_NEXT_SCOPE_BOUNDARY",
    "SELECTED_STRATEGY_ID",
    "SELECTED_STRATEGY_VERSION",
    "VERDICT",
    "DiscoveryValidationResultV0",
    "load_discovery_config_v0",
    "validate_discovery_config_v0",
]
