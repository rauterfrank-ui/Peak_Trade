"""GHV executed graph vs required productive operation graph."""

from __future__ import annotations

from typing import Any, Mapping


def build_ghv_productive_differential_v1(
    required_graph: Mapping[str, Any],
    ghv_report: Mapping[str, Any],
) -> dict[str, Any]:
    required_nodes = {n["id"] for n in required_graph.get("nodes", [])}
    ghv_covers = {
        "N_S8_CONVERGENCE",
        "N_S6_ORCH",
        "N_N1_JOIN",
        "N_MV2_DP_S7",
        "N_TERMINAL_GUARD",
    }
    real_not_ghv = sorted(required_nodes - ghv_covers - {"N_LAUNCHER"})
    ghv_only = [
        "synthetic_enter_forensic overlays in GHV offline harness",
        "GHV observability session bind layers",
    ]
    return {
        "REAL_PATH_GHV_COVERAGE_COMPLETE": False,
        "REAL_REQUIRED_NOT_COVERED_BY_GHV": real_not_ghv,
        "GHV_ONLY_NOT_USED_BY_REAL_OPERATION": ghv_only,
        "DIFFERENT_IMPLEMENTATION_BINDINGS": [],
        "DIFFERENT_CONFIG": [],
        "DIFFERENT_STATE": ["natural_enter_requires_market_outcome_not_synthesized_in_productive"],
        "DIFFERENT_AUTHORITY": [],
        "DIFFERENT_GUARDS": [],
        "EVIDENCE": ghv_report.get("GHV_TEST_WITNESSES", []),
    }
