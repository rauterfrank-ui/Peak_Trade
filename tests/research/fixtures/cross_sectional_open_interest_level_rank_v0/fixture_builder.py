"""Synthetic fixtures for cross-sectional open-interest level rank v0 infrastructure tests."""

from __future__ import annotations

from tests.research.fixtures.cross_sectional_open_interest_delta_rank_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0 as _build_synthetic_ohlcv_panel_v0,
    write_oi_materialization_root_v0,
)

from src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0 import (
    RATIFIED_PANEL_DATASET_DIGEST,
)

__all__ = [
    "build_synthetic_ohlcv_panel_v0",
    "write_oi_materialization_root_v0",
    "RATIFIED_PANEL_DATASET_DIGEST",
]


def build_synthetic_ohlcv_panel_v0():
    return _build_synthetic_ohlcv_panel_v0()
