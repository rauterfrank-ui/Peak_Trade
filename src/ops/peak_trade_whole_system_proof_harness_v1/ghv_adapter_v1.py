"""Normalized GHV witness adapter (does not rewrite GHV vectors)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_ghv_adapter_report_v1(repo: Path) -> dict[str, Any]:
    tests = [
        {
            "GHV_VECTOR_ID": "ghv_synthetic_enter_short_offline_pre_external",
            "PATH": "tests/ops/test_ghv_pre_external_offline_convergence_v1.py",
            "TEST_ID": "test_ghv_synthetic_enter_short_offline_reaches_pre_external_terminal",
            "WITNESS_CLASS": "POSITIVE_LIVENESS",
            "PRODUCTIVE_PATH": False,
        },
        {
            "GHV_VECTOR_ID": "ghv_e2e_pre_decision_productive_closure_entry",
            "PATH": "tests/ops/test_ghv_e2e_pre_decision_productive_closure_entry_regression_v1.py",
            "WITNESS_CLASS": "POSITIVE_LIVENESS",
            "PRODUCTIVE_PATH": "PARTIAL",
        },
        {
            "GHV_VECTOR_ID": "ghv_pre_external_runtime_flight_recorder",
            "PATH": "tests/ops/test_ghv_pre_external_runtime_flight_recorder_v1.py",
            "WITNESS_CLASS": "RUNTIME_TRACE",
        },
    ]
    observability_modules = [
        "src/ops/full_core_live_path_composition_root_v1/productive_golden_happy_vector_forensic_observability_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/ghv_pre_external_whole_cycle_causal_observability_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/ghv_system_wide_canary_surface_discovery_v1.py",
    ]
    present = [m for m in observability_modules if (repo / m).is_file()]
    return {
        "GHV_TEST_WITNESSES": tests,
        "GHV_OBSERVABILITY_MODULES": present,
        "GHV_COMPONENTS_EXECUTED": "see test witnesses — not inferred from PASS alone",
        "GHV_TERMINAL_DISPOSITION": "PRE_EXTERNAL contract tests",
        "NEGATIVE_CORRECT_REJECTION": "tests/ops/test_ghv_pre_external_offline_convergence_v1.py (guards)",
        "TERMINAL_SAFETY": "EXTERNAL_EFFECT_AUTHORIZED=false enforced in offline tests",
    }
