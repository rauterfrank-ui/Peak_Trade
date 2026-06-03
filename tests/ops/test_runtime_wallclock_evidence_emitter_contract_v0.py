"""Static + offline runtime wall-clock evidence emitter contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Charter: runtime_wallclock_production_integration_charter_no_run_v0_20260603T193440Z
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.ops.test_testnet_wallclock_duration_evidence_contract_v0 import (
    REQUIRED_WALLCLOCK_FIELD_NAMES,
    evaluate_wallclock_duration_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
ENTRYPOINT_FAIL_CLOSED_TEST = (
    REPO_ROOT / "tests/ops" / "test_run_testnet_session_entrypoint_fail_closed_contract_v0.py"
)
WALLCLOCK_CONTRACT_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_testnet_wallclock_duration_evidence_contract_v0.py"
)
PREFLIGHT_CONTRACT_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_network_testnet_preflight_contract_v0.py"
)

PACKAGE_MARKER = "RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_CONTRACT_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
CHARTER_BUNDLE_SUFFIX = (
    "runtime_wallclock_production_integration_charter_no_run_v0_20260603T193440Z"
)

# Future repo-native session emitter artifact (production GO; not implemented in this guard PR).
EMITTER_ARTIFACT_FILENAME = "WALLCLOCK_EVIDENCE.json"

# Zero-order first-session tier defaults (authority charter).
ZERO_ORDER_PLANNED_DURATION_SECONDS = 300
ZERO_ORDER_MIN_REQUIRED_WALL_CLOCK_SECONDS = 240
ZERO_ORDER_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS = 360
ZERO_ORDER_WALL_CLOCK_SLACK_SECONDS = 60

CONTRACT_GOVERNANCE_TOKEN_MAP: dict[str, str] = {
    "REAL_TESTNET_SESSION_NOW_ALLOWED": "RUN_TESTNET_SESSION_ALLOWED_NOW=false",
    "REPO_NATIVE_SESSION_EVIDENCE_COMPLETE": "Does not authorize repo-native session closeout",
    "PRODUCTION_EMITTER_REQUIRED": "PRODUCTION_EMITTER_PR_REQUIRED_BEFORE_REPO_NATIVE_SESSION_EVIDENCE",
    "EXTERNAL_WRAPPER_NOT_REPO_NATIVE": "evidence_source=external_harness",
    "DURABLE_MANIFEST_REQUIRED": "MANIFEST.sha256",
}


def evaluate_runtime_session_wallclock_emitter_evidence(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed reference evaluator for future repo-native session emitter closeout (offline)."""
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
    elif source != "repo_native_session":
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

    if evidence.get("run_testnet_session_invoked") is False and source == "repo_native_session":
        result["fail_reasons"].append(
            "repo-native evidence must attest run_testnet_session_invoked (E9)"
        )

    wallclock = evaluate_wallclock_duration_evidence(evidence)
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


def _valid_repo_native_emitter_evidence() -> dict[str, Any]:
    return {
        "evidence_source": "repo_native_session",
        "emitter_artifact_present": True,
        "emitter_artifact_filename": EMITTER_ARTIFACT_FILENAME,
        "run_testnet_session_invoked": True,
        "manifest_present": True,
        "manifest_verify_rc": 0,
        "final_machine_lines_present": True,
        "planned_duration_seconds": ZERO_ORDER_PLANNED_DURATION_SECONDS,
        "min_required_wall_clock_seconds": ZERO_ORDER_MIN_REQUIRED_WALL_CLOCK_SECONDS,
        "max_acceptable_wall_clock_seconds": ZERO_ORDER_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS,
        "wall_clock_slack_seconds": ZERO_ORDER_WALL_CLOCK_SLACK_SECONDS,
        "start_wall_clock_iso": "2026-06-03T20:00:00Z",
        "end_wall_clock_iso": "2026-06-03T20:05:01Z",
        "start_monotonic_seconds": 500.0,
        "end_monotonic_seconds": 801.2,
        "elapsed_wall_clock_seconds": 301.0,
        "elapsed_monotonic_seconds": 301.2,
        "duration_proven": True,
        "duration_evidence_valid": True,
        "early_exit_detected": False,
        "early_exit_reason": "",
        "invalid_if_elapsed_below_min": True,
        "real_sleep_used": True,
        "simulation_forbidden": True,
    }


def test_package_and_class4_markers_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert CHARTER_BUNDLE_SUFFIX in text


def test_required_wallclock_fields_reused_from_duration_contract() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for field in REQUIRED_WALLCLOCK_FIELD_NAMES:
        assert field in text, f"missing field {field!r}"


def test_contract_governance_tokens_map_to_repo_native_markers() -> None:
    entrypoint_source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    self_text = Path(__file__).read_text(encoding="utf-8")
    for external_token, repo_marker in CONTRACT_GOVERNANCE_TOKEN_MAP.items():
        if external_token in {
            "REPO_NATIVE_SESSION_EVIDENCE_COMPLETE",
            "PRODUCTION_EMITTER_REQUIRED",
            "EXTERNAL_WRAPPER_NOT_REPO_NATIVE",
            "DURABLE_MANIFEST_REQUIRED",
        }:
            assert repo_marker in self_text
        else:
            assert repo_marker in entrypoint_source, f"{external_token} -> missing {repo_marker!r}"


def test_guard_crosslinks_present() -> None:
    assert ENTRYPOINT_FAIL_CLOSED_TEST.is_file()
    assert WALLCLOCK_CONTRACT_TEST.is_file()
    assert PREFLIGHT_CONTRACT_TEST.is_file()
    assert "TESTNET_WALLCLOCK_DURATION_EVIDENCE_CONTRACT_V0=true" in (
        WALLCLOCK_CONTRACT_TEST.read_text(encoding="utf-8")
    )
    assert "BOUNDED_NETWORK_TESTNET_PREFLIGHT_CONTRACT_V0=true" in (
        PREFLIGHT_CONTRACT_TEST.read_text(encoding="utf-8")
    )


def test_run_testnet_session_lacks_runtime_wallclock_emitter() -> None:
    """Gap guard: production emitter PR required before repo-native session evidence is complete."""
    source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    assert EMITTER_ARTIFACT_FILENAME not in source
    for field in REQUIRED_WALLCLOCK_FIELD_NAMES:
        assert f"{field}=" not in source
        assert f'"{field}"' not in source
    assert "def get_execution_summary" in source
    assert "duration_proven" not in source


def test_production_emitter_pr_required_before_repo_native_session_evidence() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert "PRODUCTION_EMITTER_PR_REQUIRED_BEFORE_REPO_NATIVE_SESSION_EVIDENCE" in text
    assert "repo_native_session_evidence_complete" in text


def test_external_wrapper_does_not_satisfy_repo_native_emitter() -> None:
    external = _valid_repo_native_emitter_evidence()
    external["evidence_source"] = "external_harness"
    external["run_testnet_session_invoked"] = False
    result = evaluate_runtime_session_wallclock_emitter_evidence(external)
    assert result["emitter_evidence_valid"] is False
    assert result["repo_native_session_evidence_complete"] is False
    assert any("external harness" in r for r in result["fail_reasons"])


def test_valid_repo_native_emitter_evidence_passes_evaluator() -> None:
    result = evaluate_runtime_session_wallclock_emitter_evidence(
        _valid_repo_native_emitter_evidence()
    )
    assert result["emitter_evidence_valid"] is True
    assert result["repo_native_session_evidence_complete"] is True
    assert result["fail_reasons"] == []


def test_missing_wallclock_field_invalidates_emitter_evidence() -> None:
    bad = _valid_repo_native_emitter_evidence()
    bad.pop("start_wall_clock_iso")
    result = evaluate_runtime_session_wallclock_emitter_evidence(bad)
    assert result["emitter_evidence_valid"] is False
    assert any("start_wall_clock_iso" in r for r in result["fail_reasons"])


def test_elapsed_below_min_invalidates_emitter_evidence() -> None:
    bad = _valid_repo_native_emitter_evidence()
    bad["elapsed_wall_clock_seconds"] = 30.0
    bad["elapsed_monotonic_seconds"] = 30.0
    result = evaluate_runtime_session_wallclock_emitter_evidence(bad)
    assert result["emitter_evidence_valid"] is False
    assert any("R1" in r for r in result["fail_reasons"])


def test_early_exit_before_planned_duration_invalidates_emitter_evidence() -> None:
    bad = _valid_repo_native_emitter_evidence()
    bad["early_exit_detected"] = True
    bad["early_exit_reason"] = "SIGINT"
    bad["elapsed_wall_clock_seconds"] = 60.0
    bad["elapsed_monotonic_seconds"] = 60.0
    result = evaluate_runtime_session_wallclock_emitter_evidence(bad)
    assert result["emitter_evidence_valid"] is False


def test_missing_manifest_invalidates_emitter_evidence() -> None:
    bad = _valid_repo_native_emitter_evidence()
    bad["manifest_present"] = False
    result = evaluate_runtime_session_wallclock_emitter_evidence(bad)
    assert result["emitter_evidence_valid"] is False
    assert any("MANIFEST" in r for r in result["fail_reasons"])


def test_zero_order_session_tier_constants_documented() -> None:
    assert ZERO_ORDER_PLANNED_DURATION_SECONDS == 300
    assert ZERO_ORDER_MIN_REQUIRED_WALL_CLOCK_SECONDS == 240
    assert ZERO_ORDER_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS == 360
    assert ZERO_ORDER_WALL_CLOCK_SLACK_SECONDS == 60


def test_future_repo_native_closeout_must_include_planned_vs_elapsed_fields() -> None:
    required = {
        "planned_duration_seconds",
        "elapsed_wall_clock_seconds",
        "duration_proven",
        "duration_evidence_valid",
        "evidence_source",
    }
    sample = _valid_repo_native_emitter_evidence()
    assert required.issubset(sample.keys())
    serialized = json.dumps(sample)
    for key in required:
        assert key in serialized
