"""Bounded execution disclosure inventory. Not functional membership."""

from __future__ import annotations

from typing import Final

PIN: Final = "37e51e3c7988026d2caa8c9a83ff46a056e416a8"
TREE: Final = "4619907408f709ba6781377b853d7efb682bc49d"
PATH: Final = "src/execution/telemetry_health.py"

OBSERVED_SUBJECTS: Final = (
    {
        "subject_id": "execution.telemetry_health.get_directory_size_mb",
        "qualified_symbol": "src.execution.telemetry_health.get_directory_size_mb",
        "symbol": "get_directory_size_mb",
        "path": PATH,
        "start_line": 107,
        "end_line": 121,
        "source_sha256": "ba77629e6b157f916aa51d4d37918f789bfdfce3e419aa4ac821a68413ffd347",
        "classification": "OBSERVED",
    },
    {
        "subject_id": "execution.telemetry_health.check_disk_usage",
        "qualified_symbol": "src.execution.telemetry_health.check_disk_usage",
        "symbol": "check_disk_usage",
        "path": PATH,
        "start_line": 124,
        "end_line": 145,
        "source_sha256": "ddd9d2701b4304f924b02fd5ead90f908158abf3e4072c832eb7b4b02bef51b8",
        "classification": "OBSERVED",
    },
    {
        "subject_id": "execution.telemetry_health.run_health_checks",
        "qualified_symbol": "src.execution.telemetry_health.run_health_checks",
        "symbol": "run_health_checks",
        "path": PATH,
        "start_line": 348,
        "end_line": 364,
        "source_sha256": "c033a909bf748d019c6d7943e4764c14ab92690724cc2b75e67579a66eaf19c0",
        "classification": "OBSERVED",
    },
)

UNKNOWN_SUBJECT: Final = {
    "subject_id": "execution.order_submission.not_in_inventory",
    "qualified_symbol": "UNKNOWN",
    "classification": "UNKNOWN",
    "unknown_reason": "order submission is outside this bounded inventory",
}

CALL_EDGES: Final = (
    {
        "edge_id": "execution.telemetry_health.run_health_checks.CALLS.check_disk_usage",
        "source_subject_id": "execution.telemetry_health.run_health_checks",
        "target_subject_id": "execution.telemetry_health.check_disk_usage",
        "callee_symbol": "check_disk_usage",
        "evidence_line": 359,
    },
    {
        "edge_id": "execution.telemetry_health.check_disk_usage.CALLS.get_directory_size_mb",
        "source_subject_id": "execution.telemetry_health.check_disk_usage",
        "target_subject_id": "execution.telemetry_health.get_directory_size_mb",
        "callee_symbol": "get_directory_size_mb",
        "evidence_line": 126,
    },
)

UNKNOWN_EDGE: Final = {
    "edge_id": "execution.order_submission.edge.not_in_inventory",
    "classification": "UNKNOWN",
    "unknown_reason": "no order-submission edge was read for this inventory",
    "functional_membership": False,
}

FORWARD_ORIGIN: Final = "execution.telemetry_health.run_health_checks"
REVERSE_ORIGIN: Final = "execution.telemetry_health.get_directory_size_mb"
DIRECT_DEPTH: Final = 1
TRANSITIVE_DEPTH: Final = 2
