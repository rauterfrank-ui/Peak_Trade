"""Mandatory §11.14 Live-metrics schema. Collector remains inactive."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    COLLECTOR_ACTIVATED,
    MANDATORY_LIVE_METRIC_COUNT,
    MANDATORY_LIVE_METRICS,
    METRIC_COUNT_DISCREPANCY_VS_PRIOR_CENSUS,
    METRICS_SCHEMA_VERSION,
    PRIOR_CENSUS_REPORTED_METRIC_COUNT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

_COUNT_METRICS = {
    "orders_planned",
    "orders_submitted",
    "orders_acknowledged",
    "orders_rejected",
    "orders_unknown",
    "partial_fills",
    "fills",
    "cancels",
    "amends",
    "duplicate_submit_prevented",
    "reconciliation_divergences",
    "autonomous_recoveries",
    "degradation_transitions",
    "kill_switch_events",
    "owner_interventions",
}
_DECIMAL_METRICS = {
    "fees_paid",
    "funding_paid_or_received",
    "realized_pnl",
    "unrealized_pnl",
    "margin_utilization",
}


def _metric_descriptor_v1(name: str) -> dict[str, Any]:
    if name in _COUNT_METRICS:
        value_type = "integer_count"
        unit = "count"
    elif name in _DECIMAL_METRICS:
        value_type = "decimal_string"
        unit = "unbound_until_live_observation"
    else:
        raise Section1114OfflineSurfaceError(f"UNKNOWN_MANDATORY_LIVE_METRIC:{name}")
    return {
        "name": name,
        "value_type": value_type,
        "unit": unit,
        "nullable": True,
        "live_value": None,
        "collection_status": "NOT_COLLECTED",
        "source": "LIVE_ONLY",
        "provenance": "NONE",
        "collector_activated": COLLECTOR_ACTIVATED,
        "paper_testnet_fixture_sim_inadmissible": True,
        "nullability_rule": "NULL_UNTIL_SEPARATE_LIVE_COLLECTION_GO",
    }


def build_mandatory_live_metrics_schema_v1() -> dict[str, Any]:
    if len(MANDATORY_LIVE_METRICS) != MANDATORY_LIVE_METRIC_COUNT:
        raise Section1114OfflineSurfaceError("MANDATORY_LIVE_METRIC_COUNT_MISMATCH")
    metrics = [_metric_descriptor_v1(name) for name in MANDATORY_LIVE_METRICS]
    return {
        "schema_version": METRICS_SCHEMA_VERSION,
        "canonical_cardinality": MANDATORY_LIVE_METRIC_COUNT,
        "prior_census_reported_cardinality": PRIOR_CENSUS_REPORTED_METRIC_COUNT,
        "cardinality_discrepancy_vs_prior_census": (METRIC_COUNT_DISCREPANCY_VS_PRIOR_CENSUS),
        "canonical_source": "Master Runbook §11.14 mandatory Live metrics include block",
        "collector_activated": COLLECTOR_ACTIVATED,
        "live_collection_authorized": False,
        "metrics": metrics,
        "names": list(MANDATORY_LIVE_METRICS),
    }
