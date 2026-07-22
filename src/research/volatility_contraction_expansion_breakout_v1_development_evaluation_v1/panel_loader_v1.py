"""Load DEVELOPMENT-only panel into InstrumentPanelSeriesV1 for VCEB v1 eval.

Reuses the sealed DEVELOPMENT panel loader owner (identical dataset binding as
VCB/VEP/VDB/VDBX). Holdout paths are rejected. BTC/spot exclusion is enforced by
sealed panel membership.
"""

from __future__ import annotations

from pathlib import Path

from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_loader_v1 import (
    REQUIRED_PANEL_BAR_COLUMNS,
    load_instrument_panel_series_from_development_archive_v1 as _load_vcb_panel,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEVELOPMENT_END_EXCLUSIVE,
    DEVELOPMENT_START,
)

__all__ = (
    "REQUIRED_PANEL_BAR_COLUMNS",
    "load_instrument_panel_series_from_development_archive_v1",
)


def load_instrument_panel_series_from_development_archive_v1(
    archive_root: Path,
    *,
    start_inclusive: str = DEVELOPMENT_START,
    end_exclusive: str = DEVELOPMENT_END_EXCLUSIVE,
    expected_dataset_id: str = DATASET_ID,
    expected_dataset_digest: str | None = None,
):
    """Materialize aligned InstrumentPanelSeriesV1 from DEVELOPMENT archive only."""
    if expected_dataset_id != DATASET_ID:
        raise ValueError("DATASET_ID_NOT_BOUND")
    return _load_vcb_panel(
        archive_root,
        start_inclusive=start_inclusive,
        end_exclusive=end_exclusive,
        expected_dataset_id=expected_dataset_id,
        expected_dataset_digest=expected_dataset_digest,
    )
