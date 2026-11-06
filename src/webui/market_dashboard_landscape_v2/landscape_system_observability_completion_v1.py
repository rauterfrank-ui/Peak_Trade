"""S03/S04/S08/S09/S10/V07 Landscape system observability completion (consumer-only)."""

from __future__ import annotations

from typing import Any, Mapping

from .availability import Availability
from .contracts import (
    DynamicScopeSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionReconciliationSnapshotV1,
    RegimeBullBearSwitchSnapshotV1,
    RiskSizingCapitalSnapshotV1,
)
from .landscape_observability_common_v1 import (
    AVAILABILITY_LABELS,
    fail_closed_component_display_v1,
    fail_closed_scalar_display_v1,
    field_row_v1,
    metric_field_display_v1,
    provenance_and_freshness_envelope_v1,
    reason_codes_display_v1,
    scalar_field_display_v1,
)
from .source_health_projection_fidelity_v1 import FRESHNESS_UNAVAILABLE

CAPABILITY_ID = "LANDSCAPE_CURRENT_SYSTEM_OBSERVABILITY_COMPLETION_V1"


def build_s03_dynamic_scope_observability_v1(snap: DynamicScopeSnapshotV1) -> dict[str, Any]:
    env = provenance_and_freshness_envelope_v1(snap)
    av = snap.availability
    fields = [
        field_row_v1(
            field_id="scope_state",
            label="Scope state",
            display=scalar_field_display_v1(snap.scope_state, availability=av),
        ),
        field_row_v1(
            field_id="current_scope_ref",
            label="Current scope",
            display=scalar_field_display_v1(snap.current_scope_ref, availability=av),
        ),
        field_row_v1(
            field_id="next_scope_ref",
            label="Next scope",
            display=scalar_field_display_v1(snap.next_scope_ref, availability=av),
        ),
        field_row_v1(
            field_id="reason_codes",
            label="Reasons",
            display=reason_codes_display_v1(snap.reason_codes, availability=av),
        ),
    ]
    return {
        **env,
        "family_id": "S03_DYNAMIC_SCOPE",
        "source_family": "S03",
        "slot": "dynamic_scope",
        "title": "S03 · Dynamic Scope",
        "fields": fields,
    }


def build_s04_regime_bull_bear_observability_v1(
    snap: RegimeBullBearSwitchSnapshotV1,
) -> dict[str, Any]:
    env = provenance_and_freshness_envelope_v1(snap)
    av = snap.availability
    fields = [
        field_row_v1(
            field_id="regime_id",
            label="Regime",
            display=scalar_field_display_v1(snap.regime_id, availability=av),
        ),
        field_row_v1(
            field_id="regime_status",
            label="Regime status",
            display=scalar_field_display_v1(snap.regime_status, availability=av),
        ),
        field_row_v1(
            field_id="side_state",
            label="Bull/Bear",
            display=scalar_field_display_v1(snap.side_state, availability=av),
        ),
        field_row_v1(
            field_id="switch",
            label="Switch",
            display=(
                fail_closed_scalar_display_v1(None, availability=av)
                if av not in (Availability.AVAILABLE, Availability.STALE)
                else (
                    f"{fail_closed_component_display_v1(snap.previous_side_state)}→"
                    f"{fail_closed_component_display_v1(snap.next_side_state)} "
                    f"allowed={fail_closed_component_display_v1(snap.transition_allowed)} "
                    f"({fail_closed_component_display_v1(snap.transition_reason_code)})"
                )
            ),
        ),
        field_row_v1(
            field_id="scope_event_type",
            label="Scope event",
            display=scalar_field_display_v1(snap.scope_event_type, availability=av),
        ),
        field_row_v1(
            field_id="reason_codes",
            label="Reasons",
            display=reason_codes_display_v1(snap.reason_codes, availability=av),
        ),
    ]
    return {
        **env,
        "family_id": "S04_REGIME_BULL_BEAR_SWITCH",
        "source_family": "S04",
        "slot": "regime_bull_bear_switch",
        "title": "S04 · Regime / Bull-Bear / Switch",
        "fields": fields,
    }


def build_s08_risk_sizing_capital_observability_v1(
    snap: RiskSizingCapitalSnapshotV1,
) -> dict[str, Any]:
    env = provenance_and_freshness_envelope_v1(snap)
    av = snap.availability
    quantity_display = fail_closed_scalar_display_v1(snap.quantity, availability=av)
    fields = [
        field_row_v1(
            field_id="risk_status",
            label="Risk",
            display=scalar_field_display_v1(snap.risk_status, availability=av),
        ),
        field_row_v1(
            field_id="sizing_status",
            label="Sizing",
            display=scalar_field_display_v1(snap.sizing_status, availability=av),
        ),
        field_row_v1(
            field_id="capital_status",
            label="Capital",
            display=scalar_field_display_v1(snap.capital_status, availability=av),
        ),
        field_row_v1(field_id="quantity", label="Quantity", display=quantity_display),
        field_row_v1(
            field_id="reason_codes",
            label="Reasons",
            display=reason_codes_display_v1(snap.reason_codes, availability=av),
        ),
    ]
    return {
        **env,
        "family_id": "S08_RISK_SIZING_CAPITAL",
        "source_family": "S08",
        "slot": "risk_sizing_capital",
        "title": "S08 · Risk / Sizing / Capital",
        "fields": fields,
    }


def build_s09_execution_reconciliation_observability_v1(
    snap: ExecutionReconciliationSnapshotV1,
) -> dict[str, Any]:
    env = provenance_and_freshness_envelope_v1(snap)
    av = snap.availability
    fields = [
        field_row_v1(
            field_id="execution_status",
            label="Execution",
            display=scalar_field_display_v1(snap.execution_status, availability=av),
        ),
        field_row_v1(
            field_id="reconciliation_status",
            label="Reconciliation",
            display=scalar_field_display_v1(snap.reconciliation_status, availability=av),
        ),
        field_row_v1(
            field_id="order_intent_ref",
            label="Intent ref",
            display=scalar_field_display_v1(snap.order_intent_ref, availability=av),
        ),
        field_row_v1(
            field_id="reason_codes",
            label="Reasons",
            display=reason_codes_display_v1(snap.reason_codes, availability=av),
        ),
    ]
    return {
        **env,
        "family_id": "S09_EXECUTION_RECONCILIATION",
        "source_family": "S09",
        "slot": "execution_reconciliation",
        "title": "S09 · Execution / Reconciliation",
        "fields": fields,
    }


def build_s10_economic_summary_observability_v1(
    snap: EconomicSummarySnapshotV1,
) -> dict[str, Any]:
    env = provenance_and_freshness_envelope_v1(snap)
    av = snap.availability
    evidence_digest = env.get("evidence_digest")
    if evidence_digest in (None, "") and snap.manifest_digest is not None:
        evidence_digest = str(snap.manifest_digest)
    fields = [
        field_row_v1(
            field_id="economic_viability_status",
            label="Viability status",
            display=scalar_field_display_v1(snap.economic_viability_status, availability=av),
        ),
        field_row_v1(
            field_id="economic_validity_proven",
            label="Validity proven",
            display=scalar_field_display_v1(snap.economic_validity_proven, availability=av),
        ),
        field_row_v1(
            field_id="policy_threshold_status",
            label="Policy threshold",
            display=scalar_field_display_v1(snap.policy_threshold_status, availability=av),
        ),
        field_row_v1(
            field_id="profit_factor",
            label="Profit factor",
            display=metric_field_display_v1(snap.profit_factor, availability=av),
        ),
        field_row_v1(
            field_id="net_return",
            label="Net return",
            display=metric_field_display_v1(snap.net_return, availability=av),
        ),
        field_row_v1(
            field_id="max_drawdown",
            label="Max drawdown",
            display=metric_field_display_v1(snap.max_drawdown, availability=av),
        ),
        field_row_v1(
            field_id="funding_drag",
            label="Funding drag",
            display=metric_field_display_v1(snap.funding_drag, availability=av),
        ),
        field_row_v1(
            field_id="trade_count",
            label="Trade count",
            display=metric_field_display_v1(snap.trade_count, availability=av),
        ),
        field_row_v1(
            field_id="evidence_ref",
            label="Evidence ref",
            display=scalar_field_display_v1(snap.evidence_ref, availability=av),
        ),
        field_row_v1(
            field_id="evidence_digest",
            label="Evidence digest",
            display=fail_closed_scalar_display_v1(
                None if evidence_digest in (None, "") else evidence_digest,
                availability=av,
            ),
        ),
        field_row_v1(
            field_id="reason_codes",
            label="Reasons",
            display=reason_codes_display_v1(snap.reason_codes, availability=av),
        ),
        field_row_v1(
            field_id="classification",
            label="Classification",
            display="EVIDENCE_ONLY",
        ),
    ]
    return {
        **env,
        "family_id": "S10_ECONOMIC_SUMMARY",
        "source_family": "S10",
        "slot": "economic_summary",
        "title": "S10 · Economic Summary",
        "fields": fields,
    }


def build_v07_ohlcv_live_mark_fidelity_v1(*, chart: Mapping[str, Any]) -> dict[str, Any]:
    """V07 from chart presentation binding only (OHLCV readmodel + connection chrome)."""
    availability_raw = str(chart.get("availability") or Availability.NOT_BOUND.value)
    try:
        availability = Availability(availability_raw)
    except ValueError:
        availability = Availability.NOT_BOUND
    freshness_state = chart.get("freshness_state")
    is_stale = bool(chart.get("is_stale"))
    captured = chart.get("captured_at")
    observed_display = (
        str(captured).strip()
        if isinstance(captured, str) and captured.strip()
        else FRESHNESS_UNAVAILABLE
    )
    bar_count = chart.get("bar_count")
    bar_count_display = (
        str(bar_count)
        if isinstance(bar_count, int) and not isinstance(bar_count, bool) and bar_count > 0
        else fail_closed_scalar_display_v1(None, availability=availability)
    )
    bound_raw = chart.get("bound")
    if bound_raw is True:
        bound_display = "BOUND"
    else:
        bound_display = fail_closed_scalar_display_v1(None, availability=availability)
        if availability in (Availability.AVAILABLE, Availability.STALE):
            bound_display = Availability.NOT_BOUND.value
    fields = [
        field_row_v1(
            field_id="data_connection_state",
            label="Connection",
            display=fail_closed_scalar_display_v1(
                chart.get("data_connection_state") or None,
                availability=availability,
            ),
        ),
        field_row_v1(
            field_id="chart_availability",
            label="Chart availability",
            display=availability_raw,
        ),
        field_row_v1(
            field_id="bound",
            label="Series bound",
            display=bound_display,
        ),
        field_row_v1(
            field_id="bar_count",
            label="Bar count",
            display=bar_count_display,
        ),
        field_row_v1(
            field_id="interval",
            label="Interval",
            display=fail_closed_scalar_display_v1(
                chart.get("interval") or None, availability=availability
            ),
        ),
        field_row_v1(
            field_id="freshness_state",
            label="Freshness state",
            display=fail_closed_scalar_display_v1(
                freshness_state or None, availability=availability
            ),
        ),
        field_row_v1(
            field_id="captured_at",
            label="Captured at",
            display=fail_closed_scalar_display_v1(captured or None, availability=availability),
        ),
        field_row_v1(
            field_id="live_mark_price",
            label="Live mark",
            display=fail_closed_scalar_display_v1(
                chart.get("live_mark_price"),
                availability=availability,
            ),
        ),
        field_row_v1(
            field_id="last_timestamp",
            label="Last candle",
            display=fail_closed_scalar_display_v1(
                chart.get("last_timestamp") or None,
                availability=availability,
            ),
        ),
    ]
    return {
        "family_id": "V07_OHLCV_LIVE_MARK",
        "source_family": "V07",
        "slot": "ohlcv_chart",
        "title": "V07 · OHLCV / Live Mark",
        "schema_id": "market_landscape_ohlcv_browser_payload.v1",
        "availability": availability_raw,
        "availability_label": AVAILABILITY_LABELS[availability],
        "is_available": availability is Availability.AVAILABLE,
        "is_stale": availability is Availability.STALE or is_stale,
        "freshness_display": observed_display,
        "is_stale_flag": is_stale or availability is Availability.STALE,
        "stale_reason": freshness_state if is_stale else None,
        "source_kind": "okx_selected_instrument_ohlcv_readmodel",
        "source_reference": chart.get("poll_path"),
        "fields": fields,
    }


def build_landscape_system_observability_completion_v1(
    *,
    dynamic_scope: DynamicScopeSnapshotV1,
    regime_bull_bear_switch: RegimeBullBearSwitchSnapshotV1,
    risk_sizing_capital: RiskSizingCapitalSnapshotV1,
    execution_reconciliation: ExecutionReconciliationSnapshotV1,
    economic_summary: EconomicSummarySnapshotV1,
    chart: Mapping[str, Any],
) -> dict[str, Any]:
    families = [
        build_s03_dynamic_scope_observability_v1(dynamic_scope),
        build_s04_regime_bull_bear_observability_v1(regime_bull_bear_switch),
        build_s08_risk_sizing_capital_observability_v1(risk_sizing_capital),
        build_s09_execution_reconciliation_observability_v1(execution_reconciliation),
        build_s10_economic_summary_observability_v1(economic_summary),
        build_v07_ohlcv_live_mark_fidelity_v1(chart=chart),
    ]
    summary = ", ".join(f"{f['family_id']}={f['availability']}" for f in families)
    return {
        "capability_id": CAPABILITY_ID,
        "consumer_role": "read_only_consumer",
        "authority": "NONE",
        "family_count": len(families),
        "families": families,
        "summary_display": summary,
        "status_ribbon": [
            {
                "family_id": f["family_id"],
                "availability": f["availability"],
                "freshness_display": f.get("freshness_display") or FRESHNESS_UNAVAILABLE,
            }
            for f in families
        ],
    }
