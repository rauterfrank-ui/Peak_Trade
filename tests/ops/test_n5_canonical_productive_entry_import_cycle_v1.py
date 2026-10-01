"""Regression: canonical productive Level-A entry must import without N5 handoff cycle."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def test_invoke_join_and_cursor_floor_import_without_cycle() -> None:
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        _cursor_floor_or_zero,
        invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    )

    assert callable(_cursor_floor_or_zero)
    assert callable(invoke_occupied_lane_governed_cycle_n1_consumer_v1)


def test_canonical_live_c1_pre_external_entry_script_loads() -> None:
    repo = Path(__file__).resolve().parents[2]
    script = (
        repo
        / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
    )
    spec = importlib.util.spec_from_file_location("productive_live_c1_entry_v1", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module._main)
