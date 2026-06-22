"""Static + offline wall-clock duration evidence contract for future Testnet execute (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Charter: testnet_wallclock_duration_guard_external_charter_no_run_v0_20260603T182859Z
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.ops.testnet_wallclock_duration_evidence_contract_v0 import (
    evaluate_wallclock_duration_evidence,
)
from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "testnet_wallclock_duration_evidence_contract_v0.py"
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
TESTNET_BOUNDED_ADAPTER = (
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
)
TESTNET_ADAPTER_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_run_testnet_bounded_observation_adapter_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
ENTRYPOINT_FAIL_CLOSED_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_run_testnet_session_entrypoint_fail_closed_contract_v0.py"
)
CLOSEOUT_MACHINE_LINES_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_closeout_final_machine_lines_contract_v0.py"
)

PACKAGE_MARKER = "TESTNET_WALLCLOCK_DURATION_EVIDENCE_CONTRACT_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "TESTNET_WALLCLOCK_DURATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
CHARTER_BUNDLE_SUFFIX = (
    "testnet_wallclock_duration_guard_external_charter_no_run_v0_20260603T182859Z"
)

# Charter-required fields (closeout FINAL_MACHINE_LINES + durable JSON).
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

# External archive harness → charter field mapping (reference only; no archive read at test time).
EXTERNAL_HARNESS_FIELD_MAP: dict[str, str] = {
    "REQUIRED_WALL_CLOCK_DURATION_SECONDS": "planned_duration_seconds",
    "MIN_ACCEPTABLE_WALL_CLOCK_DURATION_SECONDS": "min_required_wall_clock_seconds",
    "MAX_ACCEPTABLE_WALL_CLOCK_DURATION_SECONDS": "max_acceptable_wall_clock_seconds",
    "SESSION_DURATION_SECONDS": "elapsed_monotonic_seconds",
    "WALL_CLOCK_DURATION_SECONDS": "elapsed_wall_clock_seconds",
    "DURATION_PROVEN": "duration_proven",
}

CONTRACT_GOVERNANCE_TOKEN_MAP: dict[str, str] = {
    "TESTNET_NOW_EXECUTE_ALLOWED": "RUN_TESTNET_SESSION_ALLOWED_NOW=false",
    "TESTNET_NOW_RECOMMENDED": "Does not authorize NORMAL_TESTNET_RUN",
    "FUTURE_TESTNET_REQUIRES_WALLCLOCK_EVIDENCE": "invalid_if_elapsed_below_min=true",
}

# Default slack for 1800s tier (from proven external harness closeout).
DEFAULT_WALL_CLOCK_SLACK_SECONDS = 60
THIRTY_MIN_PLANNED_SECONDS = 1800
THIRTY_MIN_MIN_REQUIRED_SECONDS = THIRTY_MIN_PLANNED_SECONDS - DEFAULT_WALL_CLOCK_SLACK_SECONDS


def _valid_thirty_min_evidence() -> dict[str, object]:
    return {
        "planned_duration_seconds": THIRTY_MIN_PLANNED_SECONDS,
        "min_required_wall_clock_seconds": THIRTY_MIN_MIN_REQUIRED_SECONDS,
        "max_acceptable_wall_clock_seconds": THIRTY_MIN_PLANNED_SECONDS
        + DEFAULT_WALL_CLOCK_SLACK_SECONDS,
        "wall_clock_slack_seconds": DEFAULT_WALL_CLOCK_SLACK_SECONDS,
        "start_wall_clock_iso": "2026-06-03T07:00:51Z",
        "end_wall_clock_iso": "2026-06-03T07:30:52Z",
        "start_monotonic_seconds": 1000.0,
        "end_monotonic_seconds": 2800.172,
        "elapsed_wall_clock_seconds": 1801.0,
        "elapsed_monotonic_seconds": 1800.172,
        "duration_proven": True,
        "duration_evidence_valid": True,
        "early_exit_detected": False,
        "early_exit_reason": "",
        "invalid_if_elapsed_below_min": True,
        "simulation_forbidden": True,
        "real_sleep_used": True,
    }


def test_package_and_class4_markers_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert CHARTER_BUNDLE_SUFFIX in text


def test_canonical_owner_imported_not_duplicated() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    local_evaluators = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("evaluate_wallclock")
    ]
    assert local_evaluators == []
    text = Path(__file__).read_text(encoding="utf-8")
    assert "from src.ops.testnet_wallclock_duration_evidence_contract_v0 import" in text
    assert evaluate_wallclock_duration_evidence.__module__ == (
        "src.ops.testnet_wallclock_duration_evidence_contract_v0"
    )


def test_wallclock_binding_uses_canonical_evaluator() -> None:
    contract_source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert (
        "from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields"
        in contract_source
    )
    assert evaluate_wallclock_evidence_fields.__module__ == "src.ops.wallclock_session_evidence_v0"


def test_required_wallclock_field_names_complete() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for field in REQUIRED_WALLCLOCK_FIELD_NAMES:
        assert field in text, f"missing charter field name {field!r}"


def test_contract_governance_tokens_map_to_repo_native_markers() -> None:
    entrypoint_source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    for external_token, repo_marker in CONTRACT_GOVERNANCE_TOKEN_MAP.items():
        if external_token == "FUTURE_TESTNET_REQUIRES_WALLCLOCK_EVIDENCE":
            assert repo_marker in Path(__file__).read_text(encoding="utf-8")
        else:
            assert repo_marker in entrypoint_source, f"{external_token} -> missing {repo_marker!r}"


def test_external_harness_field_map_documents_archive_to_charter_mapping() -> None:
    assert EXTERNAL_HARNESS_FIELD_MAP["DURATION_PROVEN"] == "duration_proven"
    assert (
        EXTERNAL_HARNESS_FIELD_MAP["REQUIRED_WALL_CLOCK_DURATION_SECONDS"]
        == "planned_duration_seconds"
    )


def test_entrypoint_fail_closed_guard_crosslink_present() -> None:
    assert ENTRYPOINT_FAIL_CLOSED_TEST.is_file()
    text = ENTRYPOINT_FAIL_CLOSED_TEST.read_text(encoding="utf-8")
    assert "RUN_TESTNET_SESSION_ENTRYPOINT_FAIL_CLOSED_CONTRACT_V0=true" in text


def test_closeout_projection_ready_not_duration_proof_crosslink_present() -> None:
    text = CLOSEOUT_MACHINE_LINES_TEST.read_text(encoding="utf-8")
    assert "test_projection_ready_is_not_wall_clock_duration_evidence" in text


def test_section5_preflight_wall_clock_review_still_blocked() -> None:
    gap_map = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "REVIEW_VALIDATES_WALL_CLOCK_DURATION=false" in gap_map
    assert "ACTUAL_WALL_CLOCK_SECONDS=0" in gap_map


def test_run_testnet_session_integrates_wallclock_session_evidence_module() -> None:
    """Bounded session delegates wall-clock emission to repo-native helper module."""
    source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    assert "wallclock_session_evidence_v0" in source
    assert "WallClockSessionTracker" in source
    assert "write_wallclock_evidence" in source


def test_run_testnet_session_uses_wall_clock_loop_with_emitter_hook() -> None:
    source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    assert "def run_for_duration" in source
    assert "time.time()" in source
    assert "_emit_wallclock_evidence" in source


def test_valid_thirty_min_evidence_passes_evaluator() -> None:
    result = evaluate_wallclock_duration_evidence(_valid_thirty_min_evidence())
    assert result["duration_evidence_valid"] is True
    assert result["duration_proven"] is True
    assert result["fail_reasons"] == []


def test_thirty_min_complete_claim_with_seconds_elapsed_is_invalid() -> None:
    """Prevents '30min passed' when run finished in seconds."""
    bad = _valid_thirty_min_evidence()
    bad["elapsed_wall_clock_seconds"] = 5.0
    bad["elapsed_monotonic_seconds"] = 5.0
    result = evaluate_wallclock_duration_evidence(bad)
    assert result["duration_evidence_valid"] is False
    assert result["duration_proven"] is False
    assert any("R1" in r for r in result["fail_reasons"])


def test_missing_start_or_end_timestamps_invalid() -> None:
    for missing in ("start_wall_clock_iso", "end_wall_clock_iso"):
        bad = _valid_thirty_min_evidence()
        bad[missing] = ""
        result = evaluate_wallclock_duration_evidence(bad)
        assert result["duration_evidence_valid"] is False
        assert any("R2" in r for r in result["fail_reasons"])


def test_projection_ready_alone_is_not_duration_proof() -> None:
    result = evaluate_wallclock_duration_evidence({"projection_ready": True})
    assert result["duration_evidence_valid"] is False
    assert any("R4" in r for r in result["fail_reasons"])


def test_missing_planned_or_elapsed_invalidates_future_testnet_evidence() -> None:
    result = evaluate_wallclock_duration_evidence({"planned_duration_seconds": 1800})
    assert result["duration_evidence_valid"] is False
    assert any("R7" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    ("elapsed_wall", "elapsed_mono", "valid"),
    [
        (1801.0, 1800.172, True),
        (1801.0, 1798.0, True),
        (1801.0, 1700.0, False),
    ],
)
def test_monotonic_cross_check_tolerance(
    elapsed_wall: float, elapsed_mono: float, valid: bool
) -> None:
    evidence = _valid_thirty_min_evidence()
    evidence["elapsed_wall_clock_seconds"] = elapsed_wall
    evidence["elapsed_monotonic_seconds"] = elapsed_mono
    result = evaluate_wallclock_duration_evidence(evidence)
    assert result["duration_evidence_valid"] is valid


def test_early_exit_without_reason_invalid() -> None:
    bad = _valid_thirty_min_evidence()
    bad["early_exit_detected"] = True
    bad["early_exit_reason"] = ""
    bad["elapsed_wall_clock_seconds"] = 900.0
    bad["elapsed_monotonic_seconds"] = 900.0
    result = evaluate_wallclock_duration_evidence(bad)
    assert result["duration_evidence_valid"] is False


def test_elapsed_above_max_acceptable_invalid() -> None:
    bad = _valid_thirty_min_evidence()
    bad["elapsed_wall_clock_seconds"] = 2000.0
    bad["elapsed_monotonic_seconds"] = 2000.0
    result = evaluate_wallclock_duration_evidence(bad)
    assert result["duration_evidence_valid"] is False
    assert any("R8" in r for r in result["fail_reasons"])


def test_simulation_forbidden_without_real_sleep_invalid() -> None:
    bad = _valid_thirty_min_evidence()
    bad["simulation_forbidden"] = True
    bad["real_sleep_used"] = False
    result = evaluate_wallclock_duration_evidence(bad)
    assert result["duration_evidence_valid"] is False
    assert any("R6" in r for r in result["fail_reasons"])


def test_invalid_if_elapsed_below_min_charter_invariant() -> None:
    assert evaluate_wallclock_duration_evidence({})["invalid_if_elapsed_below_min"] is True
    bad = _valid_thirty_min_evidence()
    bad["invalid_if_elapsed_below_min"] = False
    result = evaluate_wallclock_duration_evidence(bad)
    assert result["duration_evidence_valid"] is False


def test_future_testnet_closeout_must_include_planned_vs_elapsed_fields() -> None:
    """Contract documents mandatory closeout keys without requiring runtime implementation."""
    required_closeout_keys = {"planned_duration_seconds", "elapsed_wall_clock_seconds"}
    sample = _valid_thirty_min_evidence()
    assert required_closeout_keys.issubset(sample.keys())
    serialized = json.dumps(sample)
    for key in required_closeout_keys:
        assert key in serialized


def test_testnet_bounded_adapter_integrates_wallclock_session_evidence_module() -> None:
    """Bounded testnet adapter delegates wall-clock emission to repo-native helper module."""
    source = TESTNET_BOUNDED_ADAPTER.read_text(encoding="utf-8")
    assert "wallclock_session_evidence_v0" in source
    assert "build_wallclock_evidence_from_manifest_fields" in source
    assert "write_wallclock_evidence" in source
    assert "WALLCLOCK_EVIDENCE_FILENAME" in source


def test_testnet_bounded_adapter_testowner_wallclock_crosslink_present() -> None:
    assert TESTNET_ADAPTER_TEST.is_file()
    text = TESTNET_ADAPTER_TEST.read_text(encoding="utf-8")
    assert "test_execute_emits_wallclock_evidence_pass_standard_tier" in text
    assert "test_execute_fast_sim_false_claim_fails_closed" in text
    assert "test_execute_missing_wallclock_inputs_fail_closed" in text


def test_testnet_bounded_adapter_reuses_canonical_evaluator_not_duplicate_logic() -> None:
    adapter_source = TESTNET_BOUNDED_ADAPTER.read_text(encoding="utf-8")
    assert "evaluate_wallclock_evidence_fields" not in adapter_source
    assert "build_wallclock_evidence_from_manifest_fields" in adapter_source
