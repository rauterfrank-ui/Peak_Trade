"""Repo-native runtime wall-clock evidence emitter contract (v0).

Offline fail-closed evaluator for repo-native session emitter closeout evidence.
Does not authorize Testnet execute, network access, credentials, or runtime start.
Charter: runtime_wallclock_production_integration_charter_no_run_v0_20260603T193440Z
"""

from __future__ import annotations

from typing import Any

from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields

PACKAGE_MARKER = "RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_CONTRACT_V0=true"
CLASS4_SCOPED_EXCEPTION_MARKER = (
    "RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
CHARTER_BUNDLE_SUFFIX = (
    "runtime_wallclock_production_integration_charter_no_run_v0_20260603T193440Z"
)
EMITTER_ARTIFACT_FILENAME = "WALLCLOCK_EVIDENCE.json"
EVIDENCE_SOURCE_REPO_NATIVE = "repo_native_session"

REQUIRED_WALLCLOCK_FIELD_NAMES: tuple[str, ...] = (
    "planned_duration_seconds",
    "min_required_wall_clock_seconds",
    "start_wall_clock_iso",
    "end_wall_clock_iso",
    "start_monotonic_seconds",
    "end_monotonic_seconds",
    "elapsed_wall_clock_seconds",
    "elapsed_monotonic_seconds",
    "wall_clock_slack_seconds",
    "duration_proven",
    "duration_evidence_valid",
    "early_exit_detected",
    "early_exit_reason",
    "invalid_if_elapsed_below_min",
)


def evaluate_runtime_session_wallclock_emitter_evidence(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed evaluator for repo-native session emitter closeout (offline)."""
    result: dict[str, Any] = {
        "emitter_evidence_valid": False,
        "repo_native_session_evidence_complete": False,
        "fail_reasons": [],
    }

    source = evidence.get("evidence_source")
    if source == "external_harness":
        result["fail_reasons"].append(
            "external harness evidence does not satisfy repo-native emitter integration (E1)"
        )
    elif source != EVIDENCE_SOURCE_REPO_NATIVE:
        result["fail_reasons"].append(
            "evidence_source must be repo_native_session for repo-native closeout (E2)"
        )

    for field in REQUIRED_WALLCLOCK_FIELD_NAMES:
        if field not in evidence:
            result["fail_reasons"].append(f"missing required wall-clock field: {field} (E3)")

    if evidence.get("invalid_if_elapsed_below_min") is not True:
        result["fail_reasons"].append("invalid_if_elapsed_below_min must be true (E4)")

    if evidence.get("emitter_artifact_present") is False:
        result["fail_reasons"].append(f"missing {EMITTER_ARTIFACT_FILENAME} artifact (E5)")

    if evidence.get("manifest_present") is False:
        result["fail_reasons"].append("missing MANIFEST.sha256 (E6)")
    if evidence.get("manifest_verify_rc", 0) != 0:
        result["fail_reasons"].append("MANIFEST_VERIFY_RC != 0 (E7)")

    if evidence.get("final_machine_lines_present") is False:
        result["fail_reasons"].append("missing FINAL_MACHINE_LINES.txt (E8)")

    if (
        evidence.get("run_testnet_session_invoked") is False
        and source == EVIDENCE_SOURCE_REPO_NATIVE
    ):
        result["fail_reasons"].append(
            "repo-native evidence must attest run_testnet_session_invoked (E9)"
        )

    wallclock = evaluate_wallclock_evidence_fields(evidence)
    result["fail_reasons"].extend(wallclock["fail_reasons"])

    if evidence.get("early_exit_detected") is True and wallclock.get("duration_evidence_valid"):
        planned = evidence.get("planned_duration_seconds")
        elapsed = evidence.get("elapsed_wall_clock_seconds")
        if planned is not None and elapsed is not None and elapsed < planned * 0.95:
            result["fail_reasons"].append(
                "early exit must not count as successful planned duration (E10)"
            )

    if not result["fail_reasons"]:
        result["emitter_evidence_valid"] = True
        result["repo_native_session_evidence_complete"] = True

    return result
