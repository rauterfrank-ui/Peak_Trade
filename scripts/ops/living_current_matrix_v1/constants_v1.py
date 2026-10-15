"""Constants for Living CURRENT Matrix orchestration (AUTHORITY=NONE)."""

from __future__ import annotations

OWNER = "scripts.ops.living_current_matrix_v1"
MATRIX_AUTHORITY = "NONE"

MANIFEST_SCHEMA = "living_current_matrix_manifest.v1"
CHANGE_REPORT_SCHEMA = "current_matrix_change_report.v1"
TERMINAL_REPORT_SCHEMA = "living_current_matrix_terminal_report.v1"

MATRIX_STATUS_COMPLETE = "COMPLETE"
MATRIX_STATUS_PARTIAL = "PARTIAL"
MATRIX_STATUS_UNAVAILABLE = "UNAVAILABLE"

WP1_RULES_REL = "scripts/ops/ghv_forensic_whole_system_crosswalk_v1/crosswalk_rules.v1.json"

KNOWN_COVERAGE_GAP_IDS = frozenset(
    {
        "unresolved_wp1_census_edges",
        "empty_stage_to_cfi_mapping",
        "ghv_runtime_correlation_not_implemented",
        "navigation_only_snapshot_drift",
        "overlay_runtime_evidence_binding_readability",
    }
)
