"""Whole-system connection closure bounded WP v1 — census + static proof."""

from __future__ import annotations

from src.ops.whole_system_connection_closure_bounded_wp_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CURSORLESS_CALLER_ADJUDICATION_CLASS,
    CUTOVER_FLAGS_ADJUDICATION_CLASS,
    FINAL_D_T_ADJUDICATION_CLASS,
    INTENTIONALLY_LEGACY_CYCLE_CALLERS,
    MECHANICAL_COMPLETION_ADJUDICATION_CLASS,
    PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS,
    REQUIRED_CLOSURE_COUNT,
    UNKNOWN_PRODUCTIVE_PATH_COUNT,
    WHOLE_SYSTEM_CONNECTION_COMPLETE,
    prove_whole_system_connection_closure_v1,
)


def test_census_verdict_frozen() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "46037a171cb7c41d3e1663d92b6db80335a85260"
    assert REQUIRED_CLOSURE_COUNT == 0
    assert UNKNOWN_PRODUCTIVE_PATH_COUNT == 0
    assert WHOLE_SYSTEM_CONNECTION_COMPLETE is True
    assert FINAL_D_T_ADJUDICATION_CLASS == "INTENTIONALLY_ISOLATED"
    assert CURSORLESS_CALLER_ADJUDICATION_CLASS == "INTENTIONALLY_LEGACY"
    assert MECHANICAL_COMPLETION_ADJUDICATION_CLASS == "ALREADY_ADJUDICATED"
    assert CUTOVER_FLAGS_ADJUDICATION_CLASS == "REMAIN_FALSE_BY_DESIGN"
    assert len(PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS) == 4
    assert len(INTENTIONALLY_LEGACY_CYCLE_CALLERS) == 4


def test_static_whole_system_connection_proof() -> None:
    result = prove_whole_system_connection_closure_v1()
    assert result.ok is True, (
        f"guard={result.guard_failures} unknown={result.unknown_callers} "
        f"miswired={result.miswired_productive_callers} p5_in_cycle="
        f"{result.competing_p5_seam_in_cycle} reselect={result.reselection_markers_in_productive_bind} "
        f"backflow={result.backflow_markers}"
    )
