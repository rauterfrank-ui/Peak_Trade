"""Static + offline runtime wall-clock evidence emitter contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Charter: runtime_wallclock_production_integration_charter_no_run_v0_20260603T193440Z
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from src.ops.runtime_wallclock_evidence_emitter_contract_v0 import (
    EMITTER_ARTIFACT_FILENAME,
    REQUIRED_WALLCLOCK_FIELD_NAMES,
    evaluate_runtime_session_wallclock_emitter_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "runtime_wallclock_evidence_emitter_contract_v0.py"
PREFLIGHT_CONTRACT_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_network_testnet_preflight_contract_v0.py"
)
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
WALLCLOCK_SESSION_EVIDENCE = REPO_ROOT / "src" / "ops" / "wallclock_session_evidence_v0.py"
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


def test_canonical_owner_imported_not_duplicated() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    local_evaluators = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("evaluate_runtime_session_wallclock_emitter")
    ]
    assert local_evaluators == []
    local_field_name_constants = [
        node.targets[0].id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "REQUIRED_WALLCLOCK_FIELD_NAMES"
    ]
    assert local_field_name_constants == []
    test_module_imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("tests.")
    ]
    assert test_module_imports == []
    text = Path(__file__).read_text(encoding="utf-8")
    assert "from src.ops.runtime_wallclock_evidence_emitter_contract_v0 import" in text
    assert evaluate_runtime_session_wallclock_emitter_evidence.__module__ == (
        "src.ops.runtime_wallclock_evidence_emitter_contract_v0"
    )

    contract_tree = ast.parse(CONTRACT_MODULE.read_text(encoding="utf-8"))
    src_local_field_name_constants = [
        node.targets[0].id
        for node in ast.walk(contract_tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "REQUIRED_WALLCLOCK_FIELD_NAMES"
    ]
    assert src_local_field_name_constants == []
    contract_source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert "from src.ops.testnet_wallclock_duration_evidence_contract_v0 import" in contract_source
    import src.ops.testnet_wallclock_duration_evidence_contract_v0 as canonical_owner

    assert REQUIRED_WALLCLOCK_FIELD_NAMES == canonical_owner.REQUIRED_WALLCLOCK_FIELD_NAMES


def test_emitter_evaluator_uses_wallclock_session_evidence_ssot() -> None:
    contract_source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert "evaluate_wallclock_evidence_fields" in contract_source
    assert "wallclock_session_evidence_v0" in contract_source
    assert "evaluate_wallclock_duration_evidence" not in contract_source


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
        PREFLIGHT_CONTRACT_MODULE.read_text(encoding="utf-8")
    )


def test_run_testnet_session_integrates_runtime_wallclock_emitter() -> None:
    """Production emitter hook present on bounded session path."""
    source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    assert "wallclock_session_evidence_v0" in source
    assert "WallClockSessionTracker" in source
    assert "_emit_wallclock_evidence" in source
    assert "wallclock_evidence" in source
    assert WALLCLOCK_SESSION_EVIDENCE.is_file()
    assert "RUNTIME_WALLCLOCK_SESSION_EVIDENCE_V0=true" in (
        WALLCLOCK_SESSION_EVIDENCE.read_text(encoding="utf-8")
    )


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


def test_wallclock_session_tracker_emits_required_fields() -> None:
    from src.ops.wallclock_session_evidence_v0 import (
        INVALID_IF_ELAPSED_BELOW_MIN,
        WallClockSessionTracker,
    )

    tracker = WallClockSessionTracker.begin(
        300,
        start_wall_clock_iso="2026-06-03T20:00:00Z",
        start_monotonic_seconds=1000.0,
    )
    evidence = tracker.finalize(
        end_wall_clock_iso="2026-06-03T20:05:01Z",
        end_monotonic_seconds=1301.2,
    )
    for field in REQUIRED_WALLCLOCK_FIELD_NAMES:
        assert field in evidence
    assert evidence["invalid_if_elapsed_below_min"] is INVALID_IF_ELAPSED_BELOW_MIN
    assert evidence["evidence_source"] == "repo_native_session"
    assert evidence["duration_evidence_valid"] is True
    assert evidence["duration_proven"] is True


def test_wallclock_session_tracker_invalid_if_elapsed_below_min() -> None:
    from src.ops.wallclock_session_evidence_v0 import WallClockSessionTracker

    tracker = WallClockSessionTracker.begin(
        300,
        start_wall_clock_iso="2026-06-03T20:00:00Z",
        start_monotonic_seconds=1000.0,
    )
    evidence = tracker.finalize(
        end_wall_clock_iso="2026-06-03T20:00:30Z",
        end_monotonic_seconds=1030.0,
    )
    assert evidence["invalid_if_elapsed_below_min"] is True
    assert evidence["duration_evidence_valid"] is False
    assert evidence["duration_proven"] is False
