"""Load DEVELOPMENT-only panel into InstrumentPanelSeriesV1 for CS RS momentum eval.

Reuses sealed independent DEVELOPMENT panel loader. Holdout paths are rejected.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEVELOPMENT_END_EXCLUSIVE,
    DEVELOPMENT_START,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1
from src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1 import (
    REQUIRED_DATASET_ID,
    assert_not_holdout_path,
    included_panel_members,
    load_member_bars,
    verify_development_panel_hashes,
)


def load_instrument_panel_series_from_development_archive_v1(
    archive_root: Path,
    *,
    start_inclusive: str = DEVELOPMENT_START,
    end_exclusive: str = DEVELOPMENT_END_EXCLUSIVE,
) -> tuple[tuple[InstrumentPanelSeriesV1, ...], tuple[str, ...], str]:
    """Materialize aligned InstrumentPanelSeriesV1 from DEVELOPMENT archive only."""
    assert_not_holdout_path(archive_root)
    hashes = verify_development_panel_hashes(archive_root)
    if hashes["dataset_id"] != DATASET_ID or REQUIRED_DATASET_ID != DATASET_ID:
        raise ValueError("DATASET_ID_MISMATCH")

    members = included_panel_members(archive_root)
    frames: dict[str, pd.DataFrame] = {}
    for member in members:
        canon = member["canonical_instrument_id"]
        native = member["native_instrument_id"]
        frames[canon] = load_member_bars(
            archive_root,
            native_instrument_id=native,
            start_inclusive=start_inclusive,
            end_exclusive=end_exclusive,
        )

    # Align on intersection of timestamps (canonical PT1H grid subset).
    common_index = None
    for frame in frames.values():
        idx = pd.to_datetime(frame.index, utc=True)
        common_index = idx if common_index is None else common_index.intersection(idx)
    if common_index is None or len(common_index) == 0:
        raise ValueError("EMPTY_ALIGNED_PANEL")
    common_index = common_index.sort_values()
    timestamps = tuple(
        ts.strftime("%Y-%m-%dT%H:%M:%SZ") for ts in pd.to_datetime(common_index, utc=True)
    )

    series_list: list[InstrumentPanelSeriesV1] = []
    for canon, frame in sorted(frames.items()):
        aligned = frame.reindex(common_index)
        if aligned.isna().any().any():
            aligned = aligned.dropna()
            # Fail closed if alignment drops rows — intersection should already be clean.
            if len(aligned) != len(common_index):
                raise ValueError(f"ALIGNMENT_GAP:{canon}")
        bars: list[PanelBarV1] = []
        for ts, row in zip(timestamps, aligned.itertuples(index=False), strict=True):
            bars.append(
                PanelBarV1(
                    instrument_id=canon,
                    timestamp_utc=ts,
                    open=str(float(row.open)),
                    high=str(float(row.high)),
                    low=str(float(row.low)),
                    close=str(float(row.close)),
                    volume=str(float(row.volume)),
                    is_final=True,
                )
            )
        series_list.append(
            InstrumentPanelSeriesV1(
                instrument_id=canon,
                native_instrument_id=canon,
                bars=tuple(bars),
                series_digest=str(hashes.get("content_hash") or ""),
            )
        )
    return tuple(series_list), timestamps, str(hashes.get("content_hash") or "")
