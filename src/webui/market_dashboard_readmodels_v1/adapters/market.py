"""Market instrument adapter: futures OHLCV readmodel → MarketInstrumentSnapshotV1."""

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
    MarketInstrumentSnapshotV1,
    OhlcvBarV1,
    UnavailableSnapshotV1,
    new_market_instrument_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.provenance import (
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    new_dashboard_snapshot_provenance_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

EXPECTED_SOURCE = "market_futures_ohlcv_readmodel.v0"
PRODUCER_MODULE = "src.webui.market_futures_ohlcv_readmodel_v0.builder"
READMODEL_ID = "market_futures_ohlcv_readmodel.v0"


def adapt_market_instrument_snapshot_v1(
    source: Mapping[str, Any] | None,
    *,
    instrument_id: str,
    venue: str,
    generated_at: datetime,
    source_reference: str | None = None,
) -> MarketInstrumentSnapshotV1 | UnavailableSnapshotV1:
    """Project an already-built futures OHLCV readmodel dict for one instrument.

    ``instrument_id`` and ``venue`` are explicit selection/context parameters
    supplied by the caller (bundle identity). They are not inferred from price
    data. Missing series, dummy sources, and BTC/spot identities fail closed.
    """

    if source is None:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="MARKET_OHLCV_SOURCE_ABSENT",
            detail="No futures OHLCV readmodel payload was supplied.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    if not isinstance(source, Mapping):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_SOURCE_TYPE_INVALID",
            detail="Futures OHLCV source must be a mapping.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    if not instrument_id or not instrument_id.strip():
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_INSTRUMENT_ID_MISSING",
            detail="instrument_id must be a non-empty string.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )
    instrument_id = instrument_id.strip()
    if is_forbidden_instrument(instrument_id):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_INSTRUMENT_FORBIDDEN",
            detail="BTC/spot instruments are forbidden for MarketInstrumentSnapshotV1.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )
    if not venue or not venue.strip():
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_VENUE_MISSING",
            detail="venue must be supplied explicitly; adapters do not invent venue.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )
    venue = venue.strip()

    readmodel_id = source_get(source, "readmodel_id")
    if readmodel_id != READMODEL_ID:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_SCHEMA_MISMATCH",
            detail=f"Expected readmodel_id={READMODEL_ID!r}, got {readmodel_id!r}.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    if source_get(source, "non_authorizing") is not True:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_AUTHORIZING_FORBIDDEN",
            detail="Futures OHLCV readmodel must declare non_authorizing=true.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    source_kind_text = source_get(source, "source")
    if not isinstance(source_kind_text, str) or not source_kind_text.strip():
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_SOURCE_FIELD_MISSING",
            detail="Futures OHLCV payload missing source provenance field.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )
    if is_dummy_source(source_kind_text):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_DUMMY_FORBIDDEN",
            detail="Dummy market data sources are prohibited.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    try:
        generated_at_iso = parse_aware_datetime(
            source_get(source, "generated_at_iso"), field="generated_at_iso"
        )
    except MarketDashboardReadModelContractError as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_TIMESTAMP_INVALID",
            detail=str(exc),
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    series = source_get(source, "series")
    if not isinstance(series, Mapping) or instrument_id not in series:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="MARKET_OHLCV_SERIES_MISSING",
            detail=f"Instrument {instrument_id!r} is absent from futures OHLCV series.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    instrument_series = series[instrument_id]
    if not isinstance(instrument_series, Mapping):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_SERIES_MALFORMED",
            detail=f"Series for {instrument_id!r} must be a mapping.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    bars = instrument_series.get("bars")
    if not isinstance(bars, list) or not bars:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="MARKET_OHLCV_BARS_MISSING",
            detail=f"No OHLCV bars available for {instrument_id!r}.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    last_bar = bars[-1]
    if not isinstance(last_bar, Mapping):
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_BAR_MALFORMED",
            detail=f"Last bar for {instrument_id!r} must be a mapping.",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    try:
        effective_at = parse_aware_datetime(last_bar.get("ts"), field="bars[-1].ts")
        ohlcv = OhlcvBarV1(
            open=float(last_bar["open"]),
            high=float(last_bar["high"]),
            low=float(last_bar["low"]),
            close=float(last_bar["close"]),
            volume=float(last_bar["volume"]) if last_bar.get("volume") is not None else None,
        )
    except (KeyError, TypeError, ValueError, MarketDashboardReadModelContractError) as exc:
        return unavailable(
            availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE,
            reason_code="MARKET_OHLCV_BAR_INVALID",
            detail=f"Invalid OHLCV bar for {instrument_id!r}: {exc}",
            expected_source=EXPECTED_SOURCE,
            generated_at=generated_at,
            source_reference=source_reference,
        )

    stale = bool(source_get(source, "stale") is True)
    freshness_state = DashboardFreshnessStateV1.STALE if stale else DashboardFreshnessStateV1.FRESH
    # Provenance generated_at must be >= effective_at.
    prov_generated_at = generated_at if generated_at >= effective_at else generated_at_iso
    if prov_generated_at < effective_at:
        prov_generated_at = effective_at

    provenance = new_dashboard_snapshot_provenance_v1(
        producer_module=PRODUCER_MODULE,
        generated_at=prov_generated_at,
        effective_at=effective_at,
        source_kind=DashboardSourceKindV1.EVIDENCE_BUNDLE,
        freshness_state=freshness_state,
        producer_version=ADAPTER_PRODUCER_VERSION,
        source_reference=source_reference or source_kind_text,
    )

    return new_market_instrument_snapshot_v1(
        instrument_id=instrument_id,
        venue=venue,
        effective_at=effective_at,
        freshness_state=freshness_state,
        provenance=provenance,
        mark_price=None,
        last_price=ohlcv.close,
        change_abs=None,
        change_pct=None,
        volume=ohlcv.volume,
        ohlcv=ohlcv,
        market_series_reference=f"{READMODEL_ID}:{instrument_id}",
    )


__all__ = ["adapt_market_instrument_snapshot_v1"]
