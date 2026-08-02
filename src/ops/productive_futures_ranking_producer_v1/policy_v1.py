"""Structural ranking policy reconstructed from Cap 2.1 + Cap 2.2 owner requirements.

Classification of existing repo ranking surfaces (forensic inventory):

- ops.governed_futures_universe_producer_v1 → PRODUCTIVE_REUSABLE (input authority only)
- research/cross_sectional_* ranking bindings → RESEARCH_ONLY
- webui universe_selection / landscape ranking projections → DASHBOARD_CONSUMER_ONLY
- analytics.portfolio_builder select_top_* → LEGACY_DEAUTHORIZED for trading authority
- master_v2.FuturesRankingSnapshot DTO → ORPHANED_REUSABLE_IMPLEMENTATION (shape only)
- suitability_ranking_policy_v1 → INSUFFICIENT_EVIDENCE for universe ranking

This policy uses ONLY Cap 2.1 instrument structural gates as equal binary score
components. It does not invent trading-alpha heuristics or arbitrary market weights.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    ACTIVE_TRADING_STATES,
    DATA_QUALITY_PASS,
    RANKING_POLICY_ID,
    RANKING_POLICY_PROVENANCE,
    RANKING_POLICY_VERSION,
    SCORE_COMPONENT_KEYS,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import RankingFailureCodeV1


def policy_descriptor_v1() -> dict[str, Any]:
    return {
        "ranking_policy_id": RANKING_POLICY_ID,
        "ranking_policy_version": RANKING_POLICY_VERSION,
        "ranking_policy_provenance": RANKING_POLICY_PROVENANCE,
        "score_component_keys": list(SCORE_COMPONENT_KEYS),
        "component_weight_semantics": "EQUAL_STRUCTURAL_GATE_BINARY_1",
        "trading_alpha_heuristic": False,
        "dashboard_heuristic": False,
        "research_formula_imported": False,
        "tie_break_order": (
            "total_score_desc",
            "venue_native_id_asc",
            "canonical_instrument_id_asc",
        ),
        "top20_semantics": "TOP20_CANDIDATE_CONTEXT_ONLY",
        "selection_authority": False,
    }


def compute_score_components_v1(instrument: Mapping[str, Any]) -> dict[str, float]:
    """Equal binary structural gates from Cap 2.1 instrument fields."""
    tick = str(instrument.get("tick_size") or "").strip()
    lot = str(instrument.get("lot_size") or "").strip()
    min_sz = str(instrument.get("minimum_order_size") or "").strip()
    ct_val = str(instrument.get("contract_value") or "").strip()
    base = str(instrument.get("base_currency") or "").strip()
    quote = str(instrument.get("quote_currency") or "").strip()
    settle = str(instrument.get("settlement_currency") or "").strip()
    canonical = str(instrument.get("canonical_instrument_id") or "").strip()
    native = str(
        instrument.get("venue_native_inst_id") or instrument.get("venue_native_id") or ""
    ).strip()

    metadata_complete = all(
        [
            bool(tick),
            bool(lot),
            bool(min_sz),
            bool(ct_val),
            bool(base),
            bool(quote),
            bool(settle),
            bool(canonical) and not canonical.startswith("excluded:"),
            bool(native),
        ]
    )

    components = {
        "universe_eligibility": 1.0 if bool(instrument.get("eligibility")) else 0.0,
        "data_quality_pass": (
            1.0 if str(instrument.get("data_quality_status") or "") == DATA_QUALITY_PASS else 0.0
        ),
        "mark_price_supported": 1.0 if bool(instrument.get("mark_price_supported")) else 0.0,
        "market_data_supported": 1.0 if bool(instrument.get("market_data_supported")) else 0.0,
        "trading_status_live": (
            1.0
            if str(instrument.get("trading_status") or "").strip().lower() in ACTIVE_TRADING_STATES
            else 0.0
        ),
        "metadata_complete": 1.0 if metadata_complete else 0.0,
    }
    # Stable key order for digest consumers.
    return {k: float(components[k]) for k in SCORE_COMPONENT_KEYS}


def classify_exclusion_codes_v1(
    instrument: Mapping[str, Any],
    components: Mapping[str, float],
) -> tuple[str, ...]:
    codes: list[str] = []
    if components["universe_eligibility"] < 1.0:
        codes.append(RankingFailureCodeV1.UNIVERSE_ELIGIBILITY_FALSE.value)
        for code in instrument.get("exclusion_reason_codes") or ():
            c = str(code)
            if c and c not in codes:
                codes.append(c)
    if components["data_quality_pass"] < 1.0:
        codes.append(RankingFailureCodeV1.DATA_QUALITY_FAIL.value)
    if components["mark_price_supported"] < 1.0:
        codes.append(RankingFailureCodeV1.MARK_PRICE_UNSUPPORTED.value)
    if components["market_data_supported"] < 1.0:
        codes.append(RankingFailureCodeV1.MARKET_DATA_UNSUPPORTED.value)
    if components["trading_status_live"] < 1.0:
        codes.append(RankingFailureCodeV1.INACTIVE_OR_SUSPENDED.value)
    if components["metadata_complete"] < 1.0:
        codes.append(RankingFailureCodeV1.MISSING_REQUIRED_METADATA.value)
        codes.append(RankingFailureCodeV1.INVALID_INSTRUMENT_METADATA.value)
    return tuple(sorted(set(codes)))


def is_ranking_eligible_v1(components: Mapping[str, float]) -> bool:
    return all(float(components.get(k, 0.0)) >= 1.0 for k in SCORE_COMPONENT_KEYS)


def total_score_v1(components: Mapping[str, float]) -> float:
    return float(sum(float(components[k]) for k in SCORE_COMPONENT_KEYS))
