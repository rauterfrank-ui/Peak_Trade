"""Narrow offline adapter for dual-leg spread v1 bound funding panel dataset materialization.

Reuses cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0
as the canonical materialization owner. This module only supplies the ratified v1 data digest
that includes selection_mode (material difference vs PR4925 delta single-slot rotation).

Not a Prometheus/Metrics SSOT. Not a parallel materialization stack.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    BoundFundingPanelMaterializationResultV0,
    MaterializationTerminalStatus,
    load_funding_panel_from_staging,
    materialization_result_to_dict,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_ranking_semantics_binding_v1 import (
    SELECTION_MODE,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
    PANEL_DATASET_EXTENSION,
    PANEL_DATASET_ID,
    PANEL_FUNDING_DATASET_MANIFEST_REF,
    PIT_UNIVERSE_MANIFEST_REF,
    build_period_binding_v1,
)
from src.research.pit_okx_pt1h_panel_funding_dataset_v1 import FUNDING_FIELD

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_V1_BOUND_PANEL_DATASET_MATERIALIZATION_V0=true"
)
MATERIALIZATION_VERSION = (
    "cross_sectional_funding_rate_dual_leg_spread_v1_bound_panel_dataset_materialization.v0"
)
CANONICAL_MATERIALIZATION_OWNER = (
    "cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0"
)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_bound_funding_data_digest_v1() -> str:
    """Ratified dual-leg spread v1 digest includes selection_mode per PR4926 binding."""
    return _stable_digest(
        {
            "dataset_id": PANEL_DATASET_ID,
            "dataset_extension": PANEL_DATASET_EXTENSION,
            "panel_funding_manifest_ref": PANEL_FUNDING_DATASET_MANIFEST_REF,
            "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
            "funding_field": FUNDING_FIELD,
            "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
            "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
            "selection_mode": SELECTION_MODE,
        }
    )


def materialize_bound_funding_panel_dataset_v1(
    staging_root: Path,
    *,
    period_binding: Mapping[str, Any] | None = None,
    expected_data_digest: str | None = None,
) -> BoundFundingPanelMaterializationResultV0:
    """Delegate to canonical v0 owner with ratified v1 bound data digest."""
    bound_digest = compute_bound_funding_data_digest_v1()
    return materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=period_binding or build_period_binding_v1(),
        expected_data_digest=expected_data_digest or bound_digest,
        bound_data_digest=bound_digest,
    )


__all__ = [
    "BoundFundingPanelMaterializationResultV0",
    "CANONICAL_MATERIALIZATION_OWNER",
    "MaterializationTerminalStatus",
    "MATERIALIZATION_VERSION",
    "compute_bound_funding_data_digest_v1",
    "load_funding_panel_from_staging",
    "materialization_result_to_dict",
    "materialize_bound_funding_panel_dataset_v1",
]
