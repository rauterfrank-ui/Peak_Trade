"""Productive Master-V2 cycle must not enable P5 cutover in P5.1."""

from __future__ import annotations

from pathlib import Path

from src.ops.p5_productive_layered_core_authority_seam_v1.constants_v1 import (
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
)

_CYCLE_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)


def test_productive_cycle_module_asserts_cutover_disabled() -> None:
    text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert "assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False" in text
    assert "assert PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is False" in text
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is False


def test_productive_cycle_source_has_no_p5_seam_invoke() -> None:
    text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert "run_p5_layered_core_authority_seam_v1" not in text
