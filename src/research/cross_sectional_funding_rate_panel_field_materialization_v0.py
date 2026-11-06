"""Narrow adapter: attach versioned funding_rate field to PIT cross-sectional panel bars.

Reuses OHLCV panel alignment from pit_okx_pt1h_panel_ohlcv_dataset_v1 without
parallel ingestion stacks. Research-only; no network or credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest
from src.research.pit_okx_pt1h_panel_funding_dataset_v1 import (
    FUNDING_FIELD,
    InstrumentFundingPanelSeriesV1,
    PanelBarWithFundingV1,
    panel_bar_with_funding_from_ohlcv_v1,
    validate_funding_panel_series_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_PANEL_FIELD_MATERIALIZATION_V0=true"
ADAPTER_VERSION = "pit_okx_pt1h_panel_funding_field_materialization.v0"


@dataclass(frozen=True)
class FundingFieldMaterializationResultV0:
    series: tuple[InstrumentFundingPanelSeriesV1, ...]
    adapter_version: str
    funding_field: str
    materialization_digest: str


def _series_digest(bars: Sequence[PanelBarWithFundingV1]) -> str:
    payload = [
        {
            "instrument_id": bar.instrument_id,
            "timestamp_utc": bar.timestamp_utc,
            "funding_rate": bar.funding_rate,
            "close": bar.close,
        }
        for bar in bars
    ]
    return compute_sha256_digest({"bars": payload})


def materialize_funding_field_for_panel_v0(
    ohlcv_series: Sequence[InstrumentPanelSeriesV1],
    funding_rates_by_instrument: Mapping[str, Mapping[str, str]],
) -> FundingFieldMaterializationResultV0:
    """Attach funding_rate per instrument/timestamp from pre-staged offline inputs."""
    output: list[InstrumentFundingPanelSeriesV1] = []
    for series in ohlcv_series:
        rates = funding_rates_by_instrument.get(series.instrument_id, {})
        bars: list[PanelBarWithFundingV1] = []
        for bar in series.bars:
            funding_rate = rates.get(bar.timestamp_utc)
            if funding_rate is None:
                raise ValueError(
                    f"missing funding_rate for {series.instrument_id}@{bar.timestamp_utc}"
                )
            bars.append(panel_bar_with_funding_from_ohlcv_v1(bar, funding_rate=funding_rate))
        funding_series = InstrumentFundingPanelSeriesV1(
            instrument_id=series.instrument_id,
            native_instrument_id=series.native_instrument_id,
            bars=tuple(bars),
            series_digest=_series_digest(bars),
        )
        validation = validate_funding_panel_series_v1(funding_series)
        if not validation.valid:
            raise ValueError(
                f"funding panel validation failed for {series.instrument_id}: "
                f"{validation.error_codes}"
            )
        output.append(funding_series)
    digest = compute_sha256_digest(
        {
            "adapter_version": ADAPTER_VERSION,
            "funding_field": FUNDING_FIELD,
            "instrument_count": len(output),
            "series_digests": [item.series_digest for item in output],
        }
    )
    return FundingFieldMaterializationResultV0(
        series=tuple(output),
        adapter_version=ADAPTER_VERSION,
        funding_field=FUNDING_FIELD,
        materialization_digest=digest,
    )
