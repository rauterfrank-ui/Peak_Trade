"""Owner grants materialization v1 — D1-D4 records and family-set closure helpers."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f3_strategy_hyperparameter_optimizable_surface_exclusion_v1 import (
    GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED,
    build_f3_exclusion_record_v1,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_f5_shadow_per_token_calibration_test_entry_v1 import (
    build_shadow_calibration_registry_v1,
)
from src.experiments.canonical_optimizable_envelope_v1 import build_authorized_surface_registry_v1

WORKPACKAGE_ID: Final[str] = "OPTIMIZATION_SURFACE_OWNER_GRANTS_MATERIALIZATION_V1"
DECISION_CONFIG: Final[str] = (
    "config/governance/optimization_surface_owner_grants_materialization_v1_decision_v1.json"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/OPTIMIZATION_SURFACE_OWNER_GRANTS_MATERIALIZATION_V1.md"
)


def build_owner_decisions_materialized_v1() -> Mapping[str, Any]:
    registry = build_authorized_surface_registry_v1()
    return MappingProxyType(
        {
            "workpackage_id": WORKPACKAGE_ID,
            "d1_f5_fresh_surface_id": F5_FRESH_SURFACE_ID,
            "d2_d3_shadow_registry": build_shadow_calibration_registry_v1(),
            "d4_f3_exclusion": build_f3_exclusion_record_v1(),
            "authorized_surface_ids": registry["authorized_surface_ids"],
            "global_f3_optimizable_surface_authorized": GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED,
        }
    )
