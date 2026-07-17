"""Economic adapter: EconomicViabilityEvidenceV1 → EconomicSummarySnapshotV1."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.webui.market_dashboard_readmodels_v1.adapters._common import (
    ADAPTER_PRODUCER_VERSION,
    enum_text,
    require_sha256_or_none,
    source_get,
    unavailable,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    DashboardAvailabilityStateV1,
    EconomicGateStatusV1,
    EconomicSummarySnapshotV1,
    UnavailableSnapshotV1,
    new_economic_summary_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

EXPECTED_SOURCE = "EconomicViabilityEvidenceV1"
PRODUCER_MODULE = "src.backtest.economic_viability_evidence_v1"

# Explicit status projection table — no metric recalculation.
_STATUS_TO_GATE: dict[str, EconomicGateStatusV1] = {
    "ECONOMICALLY_VIABLE_OFFLINE": EconomicGateStatusV1.PASS,
    "ROBUSTNESS_FAILED": EconomicGateStatusV1.FAIL,
    "RESEARCH_ONLY": EconomicGateStatusV1.DIAGNOSTIC_ONLY,
    "PROMISING": EconomicGateStatusV1.DIAGNOSTIC_ONLY,
}


def _metric_value(field: Any) -> float | None:
    """Extract COMPUTED metric values only; never fabricate zeros."""

    if field is None:
        return None
    if isinstance(field, (int, float)) and not isinstance(field, bool):
        return float(field)
    semantic = enum_text(source_get(field, "semantic"))
    if semantic is None:
        return None
    if semantic.upper() != "COMPUTED":
        return None
    value = source_get(field, "value")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketDashboardReadModelContractError("metric value must be numeric when COMPUTED")
    return float(value)


def adapt_economic_summary_snapshot_v1(
    source: Any | None,
    *,
    generated_at: datetime,
    effective_at: datetime,
    evidence_reference: str | None = None,
) -> EconomicSummarySnapshotV1 | UnavailableSnapshotV1:
    """Project existing economic evidence metrics only (single source)."""

    if source is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="ECONOMIC_SOURCE_ABSENT",
            detail="No EconomicViabilityEvidenceV1 source was supplied.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    status_raw = enum_text(source_get(source, "status"))
    if status_raw is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="ECONOMIC_STATUS_MISSING",
            detail="status is required on economic evidence.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    gate = _STATUS_TO_GATE.get(status_raw.upper(), EconomicGateStatusV1.UNKNOWN)
    authoritative_gate = gate == EconomicGateStatusV1.PASS
    if gate == EconomicGateStatusV1.DIAGNOSTIC_ONLY:
        authoritative_gate = False

    try:
        digest = require_sha256_or_none(source_get(source, "manifest_digest"))
        gross_return = _metric_value(source_get(source, "gross_return"))
        net_return = _metric_value(source_get(source, "net_return"))
        profit_factor = _metric_value(source_get(source, "profit_factor"))
        drawdown = _metric_value(source_get(source, "max_drawdown"))
        fee_drag = _metric_value(source_get(source, "fee_drag"))
        expectancy = _metric_value(source_get(source, "net_expectancy"))
        trade_count_metric = _metric_value(source_get(source, "trade_count"))
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="ECONOMIC_FIELDS_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=evidence_reference,
        )

    # Project fee_drag as cost_drag only when present — never sum/recalculate costs.
    cost_drag = fee_drag

    sample_size: int | None = None
    if trade_count_metric is not None:
        sample_size = int(trade_count_metric)

    owner = enum_text(source_get(source, "owner"))
    reference = evidence_reference or owner
    if digest is None and reference is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="ECONOMIC_PROVENANCE_MISSING",
            detail="manifest_digest or evidence_reference is required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
        )

    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module=PRODUCER_MODULE,
        generated_at=generated_at if generated_at >= effective_at else effective_at,
        effective_at=effective_at,
        source_kind=DashboardSourceKindV1.EVIDENCE_BUNDLE,
        freshness_state=DashboardFreshnessStateV1.UNKNOWN,
        producer_version=ADAPTER_PRODUCER_VERSION,
        source_reference=reference,
        evidence_digest=digest,
    )

    return new_economic_summary_snapshot_v1(
        economic_gate_status=gate,
        sample_size=sample_size,
        evidence_digest=digest,
        evidence_reference=reference,
        effective_at=effective_at,
        provenance=provenance,
        gross_return=gross_return,
        net_return=net_return,
        profit_factor=profit_factor,
        drawdown=drawdown,
        cost_drag=cost_drag,
        expectancy=expectancy,
        authoritative_gate=authoritative_gate,
    )


__all__ = ["adapt_economic_summary_snapshot_v1"]
