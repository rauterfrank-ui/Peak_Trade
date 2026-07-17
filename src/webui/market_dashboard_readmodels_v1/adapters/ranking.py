"""Market ranking adapter: ranking funnel readmodel → MarketRankingSnapshotV1."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from src.webui.market_dashboard_readmodels_v1.adapters._common import (
    ADAPTER_PRODUCER_VERSION,
    is_dummy_source,
    is_forbidden_instrument,
    parse_aware_datetime,
    source_get,
    unavailable,
)
from src.webui.market_dashboard_readmodels_v1.contracts import (
    DashboardAvailabilityStateV1,
    EligibilityStatusV1,
    MarketRankingItemV1,
    MarketRankingSnapshotV1,
    UnavailableSnapshotV1,
    new_market_ranking_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

EXPECTED_SOURCE = "market_ranking_funnel_readmodel.v0"
PRODUCER_MODULE = "src.webui.market_ranking_funnel_readmodel_v0.builder"
READMODEL_ID = "market_ranking_funnel_readmodel.v0"


def adapt_market_ranking_snapshot_v1(
    source: Mapping[str, Any] | None,
    *,
    generated_at: datetime,
    stage: str = "universe",
    source_reference: str | None = None,
) -> MarketRankingSnapshotV1 | UnavailableSnapshotV1:
    """Project ranking funnel rows without inferring eligibility or scores."""

    if source is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="RANKING_SOURCE_ABSENT",
            detail="No ranking funnel readmodel payload was supplied.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    if not isinstance(source, Mapping):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_SOURCE_TYPE_INVALID",
            detail="Ranking funnel source must be a mapping.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    if source_get(source, "readmodel_id") != READMODEL_ID:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_SCHEMA_MISMATCH",
            detail=f"Expected readmodel_id={READMODEL_ID!r}.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    if source_get(source, "non_authorizing") is not True:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_AUTHORIZING_FORBIDDEN",
            detail="Ranking funnel readmodel must declare non_authorizing=true.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    source_kind_text = source_get(source, "source")
    if not isinstance(source_kind_text, str) or not source_kind_text.strip():
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_SOURCE_FIELD_MISSING",
            detail="Ranking funnel payload missing source provenance field.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )
    if is_dummy_source(source_kind_text):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_DUMMY_FORBIDDEN",
            detail="Dummy ranking sources are prohibited.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    try:
        effective_at = parse_aware_datetime(
            source_get(source, "generated_at_iso"), field="generated_at_iso"
        )
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_TIMESTAMP_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    stages = source_get(source, "stages")
    if not isinstance(stages, Mapping):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_STAGES_MISSING",
            detail="Ranking funnel stages mapping is required.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    rows = stages.get(stage)
    if not isinstance(rows, list):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="RANKING_STAGE_MISSING",
            detail=f"Ranking stage {stage!r} is absent.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    items: list[MarketRankingItemV1] = []
    try:
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise MarketDashboardReadModelContractError(
                    f"stages.{stage}[{index}] must be mapping"
                )
            symbol = str(row.get("symbol", "")).strip()
            if not symbol:
                raise MarketDashboardReadModelContractError(
                    f"stages.{stage}[{index}].symbol missing"
                )
            if is_forbidden_instrument(symbol):
                raise MarketDashboardReadModelContractError(
                    f"forbidden instrument in ranking: {symbol}"
                )
            rank = row.get("rank")
            if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
                raise MarketDashboardReadModelContractError(f"stages.{stage}[{index}].rank invalid")
            score = row.get("display_score")
            if score is not None and (
                isinstance(score, bool) or not isinstance(score, (int, float))
            ):
                raise MarketDashboardReadModelContractError(
                    f"stages.{stage}[{index}].display_score invalid"
                )
            items.append(
                MarketRankingItemV1(
                    instrument_id=symbol,
                    rank=rank,
                    score=float(score) if score is not None else None,
                    eligibility_status=EligibilityStatusV1.NOT_PROVIDED,
                    reason_codes=(),
                )
            )
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="RANKING_ROWS_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    selected_instrument_id: str | None = None
    selected_rows = stages.get("selected")
    if isinstance(selected_rows, list) and selected_rows:
        first = selected_rows[0]
        if isinstance(first, Mapping):
            candidate = str(first.get("symbol", "")).strip()
            if candidate and any(item.instrument_id == candidate for item in items):
                selected_instrument_id = candidate

    stale = bool(source_get(source, "stale") is True)
    freshness_state = DashboardFreshnessStateV1.STALE if stale else DashboardFreshnessStateV1.FRESH
    prov_generated_at = generated_at if generated_at >= effective_at else effective_at

    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module=PRODUCER_MODULE,
        generated_at=prov_generated_at,
        effective_at=effective_at,
        source_kind=DashboardSourceKindV1.EVIDENCE_BUNDLE,
        freshness_state=freshness_state,
        producer_version=ADAPTER_PRODUCER_VERSION,
        source_reference=source_reference or source_kind_text,
    )

    return new_market_ranking_snapshot_v1(
        ranked_items=tuple(items),
        selected_instrument_id=selected_instrument_id,
        effective_at=effective_at,
        provenance=provenance,
    )


__all__ = ["adapt_market_ranking_snapshot_v1"]
