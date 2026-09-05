"""Isolate bounded canary venue-proof from FULL_CORE_LIVE_PATH."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    CANARY_DEFAULT_SIDE,
    CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
    CANARY_VENUE_PROOF_PATH_KIND,
    CANARY_VENUE_PROOF_PATH_ROLE,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
    PATH_KIND,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_SIDE,
)


def canary_venue_proof_path_kind_v1() -> str:
    return CANARY_VENUE_PROOF_PATH_KIND


def refuse_canary_plan_as_full_core_e2e_v1(
    plan: Mapping[str, Any] | None,
    *,
    quantity_source: str | None = None,
    side_source: str | None = None,
) -> dict[str, Any]:
    instrument = str((plan or {}).get("instrument_id") or "")
    side = str((plan or {}).get("side") or "").upper()
    qty_src = str(quantity_source or (plan or {}).get("quantity_source") or "")
    side_src = str(side_source or (plan or {}).get("side_source") or "")
    uses_canary_defaults = instrument == DEFAULT_INSTRUMENT_ID or side == DEFAULT_SIDE
    uses_minsz = "minsz" in qty_src.lower() or qty_src in {"", "VENUE_MINSZ", "minSz"}
    core_provenance = (
        qty_src == "STEP_29Q_CANONICAL_ORDER_INTENT"
        and side_src == "STEP_29Q_CANONICAL_ORDER_INTENT"
        and str((plan or {}).get("path_kind") or "") == PATH_KIND
    )
    return {
        "CANARY_VENUE_PROOF_PATH": True,
        "FULL_CORE_LIVE_PATH": False,
        "CANARY_PATH_DISTINCT_FROM_FULL_CORE_LIVE_PATH": True,
        "CANARY_VENUE_PROOF_PATH_ROLE": CANARY_VENUE_PROOF_PATH_ROLE,
        "CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E": CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
        "CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY": (
            CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH": FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
        "FULL_CORE_SYSTEM_E2E_PROVEN": FULL_CORE_SYSTEM_E2E_PROVEN,
        "uses_canary_defaults": bool(uses_canary_defaults),
        "uses_minsz_quantity": bool(uses_minsz),
        "core_provenance": bool(core_provenance),
        "admissible_as_full_core_e2e": False,
        "DEFAULT_INSTRUMENT_ID": DEFAULT_INSTRUMENT_ID,
        "DEFAULT_SIDE": DEFAULT_SIDE,
        "CANARY_DEFAULT_INSTRUMENT_ID": CANARY_DEFAULT_INSTRUMENT_ID,
        "CANARY_DEFAULT_SIDE": CANARY_DEFAULT_SIDE,
        "path_kind": canary_venue_proof_path_kind_v1(),
    }
