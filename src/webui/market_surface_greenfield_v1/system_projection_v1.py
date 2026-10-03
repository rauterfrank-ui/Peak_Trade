"""System truth projection from CURRENT read-only dashboard sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.webui.workflow_dashboard_readmodel_v1.types import UniverseSelectionDashboardSliceV1
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    try_load_universe_selection_for_dashboard,
)

from .contracts_v1 import UNKNOWN_SOURCE_SLOTS
from .trade_counters_v1 import aggregate_trade_counters


def _unknown_slots_payload() -> dict[str, dict[str, str]]:
    return {key: {"status": "UNKNOWN", "label": label} for key, label in UNKNOWN_SOURCE_SLOTS}


def project_system_state(
    *,
    archive_root: Any,
    trade_events: list[dict[str, Any]] | None,
    run_id: str | None,
    observed_at: str,
    r_and_d_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    if archive_root is None:
        selection_slice = UniverseSelectionDashboardSliceV1(
            loaded=False,
            load_errors=("ARCHIVE_ROOT_NOT_CONFIGURED",),
        )
    else:
        selection_slice = try_load_universe_selection_for_dashboard(Path(archive_root))
    selected_future = None
    if selection_slice.loaded and selection_slice.selected_future is not None:
        sf = selection_slice.selected_future
        selected_future = {
            "symbol": sf.symbol,
            "row_id": sf.row_id,
            "rank": sf.rank,
            "classification": "PROVEN_CURRENT",
            "source_producer": "universe_selection_readmodel.v1",
        }
    elif selection_slice.loaded:
        selected_future = {
            "symbol": None,
            "classification": "UNKNOWN_CURRENT",
            "source_producer": "universe_selection_readmodel.v1",
            "load_errors": list(selection_slice.load_errors),
        }
    else:
        selected_future = {
            "symbol": None,
            "classification": "UNKNOWN_CURRENT",
            "source_producer": "universe_selection_readmodel.v1",
            "load_errors": list(selection_slice.load_errors),
        }

    counters: dict[str, Any]
    if trade_events is not None:
        counters = {
            **aggregate_trade_counters(trade_events),
            "run_id": run_id,
            "classification": "PROVEN_CURRENT",
            "source_producer": "GET /api/execution/runs/{run_id}/events",
        }
    else:
        counters = {
            "trades_set": None,
            "trades_rejected": None,
            "rejection_classes": {},
            "run_id": run_id,
            "classification": "UNKNOWN_CURRENT",
            "source_producer": "execution_watch (no run_id / no events)",
        }

    optimization = {
        "classification": "UNKNOWN_CURRENT",
        "note": "no canonical slot in v1 aggregate",
    }
    mi_evidence = {"classification": "UNKNOWN_CURRENT", "note": "no canonical slot in v1 aggregate"}
    if r_and_d_summary:
        optimization = {
            "classification": "PROVEN_CURRENT",
            "source_producer": "r_and_d_api.compute_summary",
            "experiment_count": r_and_d_summary.get("total_experiments"),
        }
        mi_evidence = {
            "classification": "PROVEN_CURRENT",
            "source_producer": "r_and_d_api.compute_summary",
            "note": "R&D summary aggregate only — not MI promotion",
        }

    return {
        "selected_future": selected_future,
        "trade_counters": counters,
        "optimization": optimization,
        "mi_evidence": mi_evidence,
        "unknown_sources": _unknown_slots_payload(),
        "system_observed_at": observed_at,
    }
