"""Synthetic fixtures for cross-sectional open-interest delta rank v0 infrastructure tests."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    SIGNAL_LAG_BARS,
    SOURCE_SCHEMA_VERSION,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
    RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
    RATIFIED_PANEL_DATASET_DIGEST,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    compute_availability_time_utc_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (
    DATASET_EXTENSION,
    DATASET_ID,
    PANEL_DATASET_SCHEMA,
    PANEL_ID,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)
from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import (
    OPEN_INTEREST_UNIT,
    PanelBarWithOpenInterestV1,
    compute_panel_open_interest_digest_v1,
    serialize_panel_bar_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1

PANEL_CALENDAR_START = datetime.strptime(PANEL_CALENDAR_START_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(
    tzinfo=timezone.utc
)
PANEL_CALENDAR_END = datetime.strptime(PANEL_CALENDAR_END_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(
    tzinfo=timezone.utc
)


def _stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _panel_calendar_timestamps() -> tuple[str, ...]:
    timestamps: list[str] = []
    cursor = PANEL_CALENDAR_START
    while cursor < PANEL_CALENDAR_END:
        timestamps.append(cursor.strftime("%Y-%m-%dT%H:%M:%SZ"))
        cursor += timedelta(hours=1)
    return tuple(timestamps)


def _bars(
    instrument_id: str,
    *,
    base_close: float,
    timestamps: tuple[str, ...],
) -> tuple[PanelBarV1, ...]:
    bars: list[PanelBarV1] = []
    for idx, ts in enumerate(timestamps):
        close = base_close + idx * 0.01
        bars.append(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts,
                open=str(close - 0.01),
                high=str(close + 0.02),
                low=str(close - 0.02),
                close=str(close),
                volume="1000",
                is_final=True,
            )
        )
    return tuple(bars)


def build_synthetic_ohlcv_panel_v0() -> tuple[InstrumentPanelSeriesV1, ...]:
    timestamps = _panel_calendar_timestamps()
    instruments = (
        ("okx:linear_perpetual:AVAX:USDT:USDT:perp", 35.0),
        ("okx:linear_perpetual:ETH:USDT:USDT:perp", 3000.0),
        ("okx:linear_perpetual:LINK:USDT:USDT:perp", 15.0),
        ("okx:linear_perpetual:POL:USDT:USDT:perp", 0.55),
        ("okx:linear_perpetual:SOL:USDT:USDT:perp", 150.0),
    )
    series: list[InstrumentPanelSeriesV1] = []
    for instrument_id, base_close in instruments:
        bars = _bars(instrument_id, base_close=base_close, timestamps=timestamps)
        series.append(
            InstrumentPanelSeriesV1(
                instrument_id=instrument_id,
                native_instrument_id=instrument_id,
                bars=bars,
                series_digest="fixture",
            )
        )
    return tuple(series)


def _make_oi_bar(
    instrument_id: str,
    native_id: str,
    ts: str,
    *,
    series_idx: int,
    bar_idx: int,
) -> dict[str, object]:
    bar = PanelBarWithOpenInterestV1(
        instrument_id=instrument_id,
        native_instrument_id=native_id,
        timestamp_utc=ts,
        open_interest=str(1000.0 + series_idx * 100.0 + bar_idx * 0.5),
        open_interest_unit=OPEN_INTEREST_UNIT,
        availability_time_utc=compute_availability_time_utc_v0(ts, signal_lag_bars=SIGNAL_LAG_BARS),
        is_final=True,
        data_quality_status="OK",
        stale_flag=False,
        missing_flag=False,
        universe_membership_status="ELIGIBLE",
        source_schema_version=SOURCE_SCHEMA_VERSION,
    )
    return serialize_panel_bar_v1(bar)


def write_oi_materialization_root_v0(
    root: Path,
    *,
    panel_dataset_digest: str | None = None,
) -> dict[str, str]:
    panel_dir = root / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    timestamps = _panel_calendar_timestamps()
    rows: list[dict[str, object]] = []
    for series_idx, (inst_id, native_id) in enumerate(CANONICAL_UNIVERSE_BINDING):
        for bar_idx, ts in enumerate(timestamps):
            rows.append(
                _make_oi_bar(inst_id, native_id, ts, series_idx=series_idx, bar_idx=bar_idx)
            )
    rows.sort(key=lambda row: (str(row["instrument_id"]), str(row["timestamp_utc"])))
    computed_digest = compute_panel_open_interest_digest_v1(rows)
    manifest_digest = panel_dataset_digest or computed_digest
    (panel_dir / "normalized_panel_bars_with_open_interest.json").write_text(
        json.dumps({"bars": rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "pit_okx_pt1h_panel_open_interest_dataset_manifest_v1",
        "panel_id": PANEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_extension": DATASET_EXTENSION,
        "panel_dataset_schema": PANEL_DATASET_SCHEMA,
        "instrument_ids": [inst for inst, _ in CANONICAL_UNIVERSE_BINDING],
        "native_instrument_ids": [native for _, native in CANONICAL_UNIVERSE_BINDING],
        "panel_calendar_timestamps_utc": list(timestamps),
        "open_interest_panel_digest": manifest_digest,
        "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
        "row_count_total": len(rows),
    }
    (panel_dir / "panel_open_interest_dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "panel_dataset_digest": manifest_digest,
        "computed_panel_dataset_digest": computed_digest,
        "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
    }


def sync_binding_to_fixture_digests_v0(
    binding: dict[str, Any],
    *,
    panel_dataset_digest: str,
) -> dict[str, Any]:
    synced = copy.deepcopy(binding)
    synced["data_digest"] = panel_dataset_digest
    synced["binding"]["digest_bindings"]["data_digest"]["value"] = panel_dataset_digest
    synced["binding_digest"] = _stable_digest(
        {
            "config_digest": synced["config_digest"],
            "data_digest": panel_dataset_digest,
            "implementation_digest": synced["binding"]["digest_bindings"]["implementation_digest"][
                "value"
            ],
        }
    )
    return synced
