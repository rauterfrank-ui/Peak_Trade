"""Regression tests for PRE_EXTERNAL convergence runtime duration transparency."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.pre_external_convergence_runtime_duration_transparency_v1 import (
    FIELD_MAX_RUN_DURATION_SECONDS_SCOPE,
    FIELD_PREFLIGHT_ELAPSED_SECONDS,
    FIELD_SEQUENCER_ELAPSED_SECONDS,
    FIELD_TOTAL_WALLCLOCK_SECONDS,
    MAX_RUN_DURATION_SECONDS_SCOPE,
    build_pre_external_convergence_runtime_duration_transparency_v1,
    merge_duration_transparency_into_report_v1,
)


def test_duration_fields_use_monotonic_segments_and_do_not_conflate_total_with_sequencer() -> None:
    origin = 100.0
    preflight_end = 150.0
    sequencer = 42.5
    post_sequencer = 195.0
    report_end = 200.0
    fields = build_pre_external_convergence_runtime_duration_transparency_v1(
        launcher_monotonic_origin=origin,
        preflight_monotonic_end=preflight_end,
        sequencer_elapsed_monotonic_seconds=sequencer,
        post_sequencer_monotonic_end=post_sequencer,
        report_monotonic_end=report_end,
    )
    assert fields[FIELD_PREFLIGHT_ELAPSED_SECONDS] == 50.0
    assert fields[FIELD_SEQUENCER_ELAPSED_SECONDS] == 42.5
    assert fields[FIELD_TOTAL_WALLCLOCK_SECONDS] == 100.0
    assert fields[FIELD_MAX_RUN_DURATION_SECONDS_SCOPE] == MAX_RUN_DURATION_SECONDS_SCOPE
    assert fields[FIELD_SEQUENCER_ELAPSED_SECONDS] != fields[FIELD_TOTAL_WALLCLOCK_SECONDS]


def test_merge_preserves_existing_report_keys() -> None:
    base = {"RUN_ID": "abc", "CYCLE_COUNT": 4, "POST_COUNT": 0}
    fields = build_pre_external_convergence_runtime_duration_transparency_v1(
        launcher_monotonic_origin=0.0,
        preflight_monotonic_end=10.0,
        sequencer_elapsed_monotonic_seconds=5.0,
        post_sequencer_monotonic_end=16.0,
        report_monotonic_end=18.0,
    )
    merged = merge_duration_transparency_into_report_v1(base, fields)
    assert merged["RUN_ID"] == "abc"
    assert merged["CYCLE_COUNT"] == 4
    assert merged["POST_COUNT"] == 0
    assert merged["SEQUENCER_ELAPSED_SECONDS"] == 5.0
    assert base["RUN_ID"] == "abc"
    assert "SEQUENCER_ELAPSED_SECONDS" not in base
