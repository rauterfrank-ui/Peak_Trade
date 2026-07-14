#!/usr/bin/env python3
"""Materialize canonical economic observability metric registry v1 from discovery evidence."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (_REPO_ROOT / "src", _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from src.backtest.economic_observability_registry_v1 import (
    DISCOVERY_METRIC_COUNT,
    SCHEMA_VERSION,
    REGISTRY_OWNER,
)

DEFAULT_DISCOVERY_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/canonical_economic_observability_metric_lineage_and_reporting_gap_discovery_read_only_v0_20260714T185419Z"
)
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2] / "config/economic_observability_metric_registry_v1.json"
)

PRIORITY_MAP = {
    "P0": "P0_DECISION_CRITICAL",
    "P1": "P1_HIGH_VALUE_DIAGNOSTIC",
    "P2": "P2_ADVANCED_ANALYTIC",
    "P3": "P3_OPTIONAL_OR_PRESENTATIONAL",
}

DOMAIN_BY_CATEGORY = {
    "PERFORMANCE": "economic",
    "COSTS": "costs",
    "RISK": "risk",
    "TRADE_QUALITY": "trade_analytics",
    "DECISION_FUNNEL": "decision_funnel",
    "ROBUSTNESS": "robustness",
    "ATTRIBUTION": "strategy_quality",
}

EXPOSURE_METRICS = frozenset(
    {
        "exposure",
        "time_in_market",
        "margin_utilization",
        "capital_utilization",
        "average_notional",
        "median_notional",
        "minimum_notional",
        "maximum_notional",
        "average_position_size",
    }
)

PORTFOLIO_METRICS = frozenset(
    {
        "portfolio_admissible_count",
        "long_contribution",
        "short_contribution",
        "regime_breakdown",
        "instrument_breakdown",
        "portfolio_contribution",
        "winner_concentration",
        "single_trade_dominance",
        "regime_dominance",
    }
)

PROVENANCE_METRICS = frozenset(
    {
        "config_digest",
        "implementation_digest",
        "data_digest",
        "manifest_digest",
        "wiring_chain_digest",
    }
)

DATA_QUALITY_METRICS = frozenset(
    {
        "sample_sufficiency",
        "coefficient_stability",
    }
)

OWNER_BY_METRIC: dict[str, str] = {
    "net_return": "backtest.economic_viability_evidence_v1",
    "gross_return": "backtest.economic_viability_evidence_v1",
    "profit_factor_net": "backtest.stats",
    "expectancy_net": "backtest.economic_viability_evidence_v1",
    "funding_drag": "backtest.funding_model_v1",
    "net_funding": "backtest.funding_model_v1",
    "fee_drag": "backtest.cost_config_v0",
    "slippage_drag": "backtest.cost_config_v0",
    "spread_drag": "backtest.cost_config_v0",
    "spread_cost": "backtest.cost_config_v0",
    "total_slippage": "backtest.cost_config_v0",
    "total_fees": "backtest.cost_config_v0",
    "total_cost": "backtest.cost_config_v0",
    "gross_pnl": "backtest.engine",
    "net_pnl": "backtest.engine",
    "trade_count": "backtest.stats",
    "win_rate": "backtest.stats",
    "turnover": "backtest.stats",
    "decision_funnel": "research.cross_sectional_offline_economic_evaluation_decision_funnel_v0",
    "zero_trade_causal_classification": "research.cross_sectional_offline_economic_evaluation_decision_funnel_v0",
    "top_block_reasons": "research.cross_sectional_offline_economic_evaluation_decision_funnel_v0",
    "walk_forward_results": "backtest.mv2_research_wiring_v1",
    "Monte-Carlo distributions": "experiments.monte_carlo",
    "stress_results": "experiments.stress_tests",
    "parameter_sensitivity": "backtest.parameter_sensitivity_v1",
    "gross_edge_per_trade": "backtest.engine",
    "net_edge_per_trade": "backtest.stats",
    "signal_contribution": "trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "entry_contribution": "trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "exit_contribution": "trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "sizing_contribution": "backtest.offline_evaluation_sizing_contract_v1",
    "long_contribution": "experiments.portfolio_robustness",
    "short_contribution": "experiments.portfolio_robustness",
    "regime_breakdown": "backtest.compute_single_regime_profit_contribution_v1",
    "instrument_breakdown": "backtest.mv2_research_wiring_v1",
    "portfolio_contribution": "experiments.portfolio_robustness",
    "MAE": "backtest.economic_observability_advanced_capabilities_v1",
    "MFE": "backtest.economic_observability_advanced_capabilities_v1",
    "profit_factor_gross": "future_capability.gross_net_cost_decomposition_v0",
    "break_even_cost": "backtest.economic_observability_advanced_capabilities_v1",
    "break_even_cost_bps": "backtest.economic_observability_advanced_capabilities_v1",
    "VaR": "future_capability.tail_risk_analytics_v0",
    "CVaR": "future_capability.tail_risk_analytics_v0",
    "required_gross_edge_for_break_even": "backtest.economic_observability_advanced_capabilities_v1",
}

CATEGORY_DEFAULT_OWNER = {
    "PERFORMANCE": "backtest.stats",
    "COSTS": "backtest.cost_config_v0",
    "RISK": "backtest.stats",
    "TRADE_QUALITY": "backtest.stats",
    "DECISION_FUNNEL": "research.cross_sectional_offline_economic_evaluation_decision_funnel_v0",
    "ROBUSTNESS": "backtest.mv2_research_wiring_v1",
    "ATTRIBUTION": "backtest.offline_evaluation_sizing_contract_v1",
}

ROBUSTNESS_OWNER = {
    "walk_forward_results": "backtest.mv2_research_wiring_v1",
    "Monte-Carlo distributions": "experiments.monte_carlo",
    "stress_results": "experiments.stress_tests",
    "parameter_sensitivity": "backtest.parameter_sensitivity_v1",
    "OOS metrics": "backtest.walkforward",
    "confidence intervals": "experiments.monte_carlo",
    "fee_multiplier stress": "experiments.stress_tests",
    "slippage_multiplier stress": "experiments.stress_tests",
    "funding_stress": "experiments.stress_tests",
    "spread_expansion_stress": "experiments.stress_tests",
    "fill_quality_stress": "experiments.stress_tests",
    "latency_stress": "experiments.stress_tests",
    "trade_omission stress": "experiments.stress_tests",
}

FUNNEL_METRICS = frozenset(
    {
        "market_epochs_total",
        "directional_candidate_count",
        "directional_confirmed_count",
        "survival_pass_count",
        "survival_block_count",
        "suitability_pass_count",
        "suitability_block_count",
        "double_play_entry_eligible_count",
        "entry_preconditions_pass_count",
        "risk_sizing_admissible_count",
        "portfolio_admissible_count",
        "trades_opened_count",
        "conversion_rate_per_stage",
    }
)

NOT_APPLICABLE_STATUSES = frozenset({"NOT_SUPPORTED"})


def _normalize_availability(raw_status: str, row: dict[str, str]) -> str:
    if raw_status in NOT_APPLICABLE_STATUSES:
        return "NOT_APPLICABLE"
    if raw_status == "PARTIALLY_AVAILABLE":
        if row["persisted"] == "True" and row["in_final_report"] == "False":
            return "COMPUTED_AND_PERSISTED_NOT_REPORTED"
        if row["computed_in_canonical_path"] == "True" and row["persisted"] == "False":
            return "COMPUTED_NOT_PERSISTED"
        if row["reconstructable"] == "True":
            return "RAW_DATA_PERSISTED_RECONSTRUCTABLE"
        return "NOT_COMPUTED"
    return raw_status


def _resolve_domain(metric_id: str, category: str) -> str:
    if metric_id in EXPOSURE_METRICS:
        return "exposure"
    if metric_id in PORTFOLIO_METRICS:
        return "portfolio"
    if metric_id in PROVENANCE_METRICS:
        return "provenance"
    if metric_id in DATA_QUALITY_METRICS:
        return "data_quality"
    if metric_id in FUNNEL_METRICS or category == "DECISION_FUNNEL":
        return "decision_funnel"
    return DOMAIN_BY_CATEGORY[category]


def _resolve_owner(metric_id: str, category: str, catalog_entry: dict[str, Any]) -> str:
    if metric_id in OWNER_BY_METRIC:
        return OWNER_BY_METRIC[metric_id]
    if category == "ROBUSTNESS":
        return ROBUSTNESS_OWNER.get(metric_id, "backtest.mv2_research_wiring_v1")
    if category == "COSTS" and metric_id.startswith(("funding", "net_funding")):
        return "backtest.funding_model_v1"
    call_site = str(catalog_entry.get("production_call_site", ""))
    if "economic_viability_evidence_v1" in call_site:
        return "backtest.economic_viability_evidence_v1"
    if "compute_backtest_stats" in call_site or "backtest.stats" in call_site:
        return "backtest.stats"
    if "trade_ledger" in call_site:
        return "research.trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0"
    if "decision_funnel" in call_site:
        return "research.cross_sectional_offline_economic_evaluation_decision_funnel_v0"
    if category == "TRADE_QUALITY" and any(
        token in metric_id for token in ("fee", "slippage", "funding", "cost", "spread")
    ):
        return "backtest.cost_config_v0"
    if category == "TRADE_QUALITY" and any(
        token in metric_id
        for token in ("trade", "holding", "winner", "loser", "notional", "position")
    ):
        return "backtest.engine"
    return CATEGORY_DEFAULT_OWNER[category]


def _source_reference(metric_id: str, owner: str, catalog_entry: dict[str, Any]) -> str:
    if owner.startswith("future_capability."):
        return owner
    persistence_field = catalog_entry.get("persistence_field_path")
    if (
        isinstance(persistence_field, str)
        and persistence_field
        and persistence_field != "see code refs"
    ):
        return f"{owner}:{persistence_field}"
    return f"{owner}:{metric_id}"


def _derive_status_fields(availability: str, row: dict[str, str]) -> tuple[str, str, str]:
    if availability == "FULLY_AVAILABLE_AND_REPORTED":
        return "PERSISTED", "REPORTED", "NONE"
    if availability == "COMPUTED_AND_PERSISTED_NOT_REPORTED":
        return "PERSISTED", "NOT_REPORTED", "NONE"
    if availability == "COMPUTED_NOT_PERSISTED":
        return "NOT_PERSISTED", "NOT_REPORTED", "IN_MEMORY_ONLY"
    if availability == "RAW_DATA_PERSISTED_RECONSTRUCTABLE":
        return "RAW_ONLY", "NOT_REPORTED", "RECONSTRUCTABLE_FROM_RAW"
    if availability == "CAPABILITY_PRESENT_NOT_WIRED":
        return "NOT_PERSISTED", "NOT_REPORTED", "CAPABILITY_PRESENT_NOT_WIRED"
    if availability == "NOT_APPLICABLE":
        return "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE"
    return "NOT_PERSISTED", "NOT_REPORTED", "NOT_COMPUTED"


def _relevance_flags(category: str, priority: str) -> dict[str, bool]:
    return {
        "decision_relevance": priority.startswith("P0"),
        "economic_relevance": category in {"PERFORMANCE", "COSTS", "ATTRIBUTION"},
        "risk_relevance": category in {"RISK", "TRADE_QUALITY"} and priority in {"P0", "P1"},
        "research_relevance": category in {"ROBUSTNESS", "TRADE_QUALITY", "ATTRIBUTION"},
        "promotion_relevance": priority.startswith("P0"),
        "runtime_relevance": False,
    }


def _consumer_list(metric_id: str, availability: str) -> list[str]:
    consumers = [
        "backtest.economic_viability_evidence_v1",
        "persist_economic_viability_evidence_bundle_v1",
    ]
    if availability in {"COMPUTED_AND_PERSISTED_NOT_REPORTED", "FULLY_AVAILABLE_AND_REPORTED"}:
        consumers.append("economic_report_consumer_v0")
    consumers.append("backtest.economic_observability_snapshot_v1")
    return sorted(set(consumers))


def materialize_registry(discovery_dir: Path, output_path: Path) -> dict[str, Any]:
    catalog = json.loads((discovery_dir / "metric_catalog.json").read_text(encoding="utf-8"))
    coverage_rows: dict[str, dict[str, str]] = {}
    with (discovery_dir / "metric_coverage_matrix.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            coverage_rows[row["metric_id"]] = row
    catalog_by_id = {entry["metric_id"]: entry for entry in catalog["metrics"]}
    if len(catalog_by_id) != DISCOVERY_METRIC_COUNT:
        raise SystemExit(f"unexpected metric count: {len(catalog_by_id)}")
    entries: list[dict[str, Any]] = []
    for metric_id in sorted(catalog_by_id):
        catalog_entry = catalog_by_id[metric_id]
        row = coverage_rows[metric_id]
        category = row["category"]
        availability = _normalize_availability(row["status"], row)
        owner = _resolve_owner(metric_id, category, catalog_entry)
        persistence_status, reporting_status, reconstructability = _derive_status_fields(
            availability, row
        )
        priority = PRIORITY_MAP[row["decision_value"]]
        relevance = _relevance_flags(category, row["decision_value"])
        entries.append(
            {
                "metric_id": metric_id,
                "display_name": catalog_entry.get("display_name", metric_id),
                "domain": _resolve_domain(metric_id, category),
                "description": catalog_entry.get("precise_definition", metric_id),
                "unit": catalog_entry.get("unit", "mixed"),
                "data_type": "numeric"
                if metric_id not in {"decision_funnel", "top_block_reasons"}
                else "structured",
                "canonical_owner": owner,
                "source_field_or_formula": _source_reference(metric_id, owner, catalog_entry),
                "raw_inputs": list(catalog_entry.get("raw_input_fields") or []),
                "availability_status": availability,
                "persistence_status": persistence_status,
                "reporting_status": reporting_status,
                "reconstructability": reconstructability,
                **relevance,
                "priority": priority,
                "null_semantics": "NULL_MEANS_ABSENT_OR_UNAVAILABLE",
                "zero_semantics": "ZERO_IS_A_VALID_VALUE",
                "sample_requirements": catalog_entry.get("notes") or "see_discovery_catalog",
                "consumer_list": _consumer_list(metric_id, availability),
                "schema_version": SCHEMA_VERSION,
            }
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "registry_owner": REGISTRY_OWNER,
        "discovery_source_ref": str(discovery_dir),
        "metric_count": len(entries),
        "entries": entries,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery-dir", type=Path, default=DEFAULT_DISCOVERY_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = materialize_registry(args.discovery_dir, args.output)
    print(f"METRIC_COUNT={payload['metric_count']}")
    print(f"OUTPUT={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
