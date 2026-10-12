"""Additive PRE_EXTERNAL convergence report duration transparency (monotonic clocks only)."""

from __future__ import annotations

from typing import Any, Mapping

RUNTIME_DURATION_TRANSPARENCY_SCHEMA_VERSION = "v1"
RUNTIME_DURATION_CLOCK = "monotonic"
MAX_RUN_DURATION_SECONDS_SCOPE = "S6_OBSERVATION_SEQUENCER_ONLY"

FIELD_TOTAL_WALLCLOCK_SECONDS = "TOTAL_WALLCLOCK_SECONDS"
FIELD_PREFLIGHT_ELAPSED_SECONDS = "PREFLIGHT_ELAPSED_SECONDS"
FIELD_SEQUENCER_ELAPSED_SECONDS = "SEQUENCER_ELAPSED_SECONDS"
FIELD_FINALIZATION_ELAPSED_SECONDS = "FINALIZATION_ELAPSED_SECONDS"
FIELD_MAX_RUN_DURATION_SECONDS_SCOPE = "MAX_RUN_DURATION_SECONDS_SCOPE"
FIELD_RUNTIME_DURATION_CLOCK = "RUNTIME_DURATION_CLOCK"
FIELD_RUNTIME_DURATION_TRANSPARENCY_SCHEMA_VERSION = "RUNTIME_DURATION_TRANSPARENCY_SCHEMA_VERSION"


def build_pre_external_convergence_runtime_duration_transparency_v1(
    *,
    launcher_monotonic_origin: float,
    preflight_monotonic_end: float,
    sequencer_elapsed_monotonic_seconds: float,
    post_sequencer_monotonic_end: float,
    report_monotonic_end: float,
) -> dict[str, Any]:
    """Build additive duration fields for PRE_EXTERNAL_CONVERGENCE_REPORT.json.

    PREFLIGHT: launcher origin through completion of transport/G17/obs wiring before S6 call.
    SEQUENCER: S6 orchestrator monotonic elapsed (same clock as max_run_duration enforcement).
    FINALIZATION: post-S6 policy run return through report serialization.
    TOTAL_WALLCLOCK_SECONDS: full launcher monotonic span (not UTC wall clock).
    """
    origin = float(launcher_monotonic_origin)
    preflight_end = float(preflight_monotonic_end)
    sequencer = max(0.0, float(sequencer_elapsed_monotonic_seconds))
    post_sequencer = float(post_sequencer_monotonic_end)
    report_end = float(report_monotonic_end)

    preflight = max(0.0, preflight_end - origin)
    finalization = max(0.0, report_end - post_sequencer)
    total = max(0.0, report_end - origin)

    return {
        FIELD_RUNTIME_DURATION_TRANSPARENCY_SCHEMA_VERSION: (
            RUNTIME_DURATION_TRANSPARENCY_SCHEMA_VERSION
        ),
        FIELD_RUNTIME_DURATION_CLOCK: RUNTIME_DURATION_CLOCK,
        FIELD_MAX_RUN_DURATION_SECONDS_SCOPE: MAX_RUN_DURATION_SECONDS_SCOPE,
        FIELD_PREFLIGHT_ELAPSED_SECONDS: round(preflight, 6),
        FIELD_SEQUENCER_ELAPSED_SECONDS: round(sequencer, 6),
        FIELD_FINALIZATION_ELAPSED_SECONDS: round(finalization, 6),
        FIELD_TOTAL_WALLCLOCK_SECONDS: round(total, 6),
    }


def merge_duration_transparency_into_report_v1(
    report: Mapping[str, Any],
    duration_fields: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a new report dict with additive duration keys (does not mutate input)."""
    merged = dict(report)
    merged.update(dict(duration_fields))
    return merged
