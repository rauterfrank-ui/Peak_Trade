"""Public OKX source discovery — deterministic locators, no network."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from src.research.longer_chronological_pit_acquisition_v1 import (
    FREQUENCY,
    MARKET_TYPE,
    OKX_BAR_PARAM,
    SOURCE_ID_CDN_FUNDING_ARCHIVE,
    SOURCE_ID_FUNDING,
    SOURCE_ID_HISTORY_CANDLES,
    VENUE,
)


@dataclass(frozen=True)
class SourceDefinitionV1:
    source_id: str
    venue: str
    kind: str
    locator_template: str
    network_required: bool
    coverage_certainty: str  # KNOWN | UNCERTAIN | PARTIAL
    notes: str


PUBLIC_SOURCES: tuple[SourceDefinitionV1, ...] = (
    SourceDefinitionV1(
        source_id=SOURCE_ID_HISTORY_CANDLES,
        venue=VENUE,
        kind="ohlcv_pt1h",
        locator_template=(
            "https://www.okx.com/api/v5/market/history-candles"
            "?instId={native_instrument_id}&bar={bar}&after={after_ms}&limit={limit}"
        ),
        network_required=True,
        coverage_certainty="UNCERTAIN",
        notes=(
            "Public REST history depth per instrument is UNCERTAIN until a bounded probe; "
            "no bulk download in scaffold."
        ),
    ),
    SourceDefinitionV1(
        source_id=SOURCE_ID_FUNDING,
        venue=VENUE,
        kind="funding_rate",
        locator_template=(
            "https://www.okx.com/api/v5/public/funding-rate-history"
            "?instId={native_instrument_id}&after={after_ms}&limit={limit}"
        ),
        network_required=True,
        coverage_certainty="UNCERTAIN",
        notes="Funding history depth UNCERTAIN; join optional for OHLCV-first qualification.",
    ),
    SourceDefinitionV1(
        source_id=SOURCE_ID_CDN_FUNDING_ARCHIVE,
        venue=VENUE,
        kind="funding_archive_monthly",
        locator_template=(
            "https://static.okx.com/cdn/okex/traderecords/swaprates/monthly/"
            "{yyyy}{mm}/allswaprate-swaprate-{yyyy}{mm}.zip"
        ),
        network_required=True,
        coverage_certainty="PARTIAL",
        notes=(
            "CDN monthly swap-rate archives reused by existing funding ingest owners; "
            "availability outside previously sealed months is UNCERTAIN."
        ),
    ),
)


def list_public_sources() -> list[dict[str, Any]]:
    return [asdict(s) for s in PUBLIC_SOURCES]


def build_history_candle_locator(
    *,
    native_instrument_id: str,
    after_ms: int,
    limit: int = 100,
    bar: str = OKX_BAR_PARAM,
) -> str:
    src = next(s for s in PUBLIC_SOURCES if s.source_id == SOURCE_ID_HISTORY_CANDLES)
    return src.locator_template.format(
        native_instrument_id=native_instrument_id,
        bar=bar,
        after_ms=after_ms,
        limit=limit,
    )


def build_cdn_funding_locator(*, year: int, month: int) -> str:
    src = next(s for s in PUBLIC_SOURCES if s.source_id == SOURCE_ID_CDN_FUNDING_ARCHIVE)
    return src.locator_template.format(yyyy=f"{year:04d}", mm=f"{month:02d}")


def discover_sources_for_partition(partition: Mapping[str, Any]) -> dict[str, Any]:
    """Attach deterministic locators to a planned partition (no network)."""
    native = str(partition["native_instrument_id"])
    period_end = str(partition["period_end"])
    # after cursor = end exclusive epoch ms (OKX pagination convention in bounded fetch)
    from datetime import datetime, timezone

    end = datetime.fromisoformat(period_end.replace("Z", "+00:00")).astimezone(timezone.utc)
    after_ms = int(end.timestamp() * 1000)
    kind = str(partition.get("kind") or "ohlcv_pt1h")
    if kind == "ohlcv_pt1h":
        locator = build_history_candle_locator(native_instrument_id=native, after_ms=after_ms)
        source_id = SOURCE_ID_HISTORY_CANDLES
        certainty = "UNCERTAIN"
    elif kind == "funding_archive_monthly":
        y = int(str(partition["period_start"])[0:4])
        m = int(str(partition["period_start"])[5:7])
        locator = build_cdn_funding_locator(year=y, month=m)
        source_id = SOURCE_ID_CDN_FUNDING_ARCHIVE
        certainty = "PARTIAL"
    else:
        locator = build_history_candle_locator(native_instrument_id=native, after_ms=after_ms)
        source_id = SOURCE_ID_HISTORY_CANDLES
        certainty = "UNCERTAIN"
    return {
        "source_id": source_id,
        "source_locator": locator,
        "coverage_certainty": certainty,
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "frequency": FREQUENCY,
        "network_required_for_acquire": True,
    }
