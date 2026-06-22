"""Static + offline wall-clock duration evidence contract for Shadow bounded dry-run (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Shadow start.
Reuses the canonical repo-native evaluator from ``src/ops/wallclock_session_evidence_v0.py``.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from src.ops.testnet_wallclock_duration_evidence_contract_v0 import (
    REQUIRED_WALLCLOCK_FIELD_NAMES,
)
from src.ops.wallclock_session_evidence_v0 import (
    DEFAULT_WALL_CLOCK_SLACK_SECONDS,
    INVALID_IF_ELAPSED_BELOW_MIN,
    WALLCLOCK_EVIDENCE_FILENAME,
    bounds_from_planned_duration,
    build_wallclock_evidence_from_manifest_fields,
    evaluate_wallclock_evidence_fields,
    write_wallclock_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SHADOW_WRAPPER = REPO_ROOT / "scripts" / "ops" / "shadow_247_futures_start_wrapper_skeleton_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
TESTNET_WALLCLOCK_CONTRACT = (
    REPO_ROOT / "tests" / "ops" / "test_testnet_wallclock_duration_evidence_contract_v0.py"
)
WRAPPER_TEST = REPO_ROOT / "tests" / "ops" / "test_shadow_247_futures_start_wrapper_skeleton_v0.py"
ADAPTER_TEST = REPO_ROOT / "tests" / "ops" / "test_run_shadow_bounded_observation_adapter_v0.py"
CANONICAL_EVALUATOR = REPO_ROOT / "src" / "ops" / "wallclock_session_evidence_v0.py"

PACKAGE_MARKER = "SHADOW_WALLCLOCK_DURATION_EVIDENCE_CONTRACT_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "SHADOW_WALLCLOCK_DURATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
CHARTER_BUNDLE_SUFFIX = "shadow_bounded_wallclock_duration_evidence_contract_v1_20260622T052918Z"

STANDARD_DURATION_MINUTES = 10
EXTENDED_DURATION_MINUTES_30 = 30
EXTENDED_DURATION_MINUTES_60 = 60


def _parse_utc_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _format_utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def _synthetic_shadow_pass_evidence(
    duration_minutes: int,
    *,
    start_iso: str = "2026-06-22T10:00:00Z",
    monotonic_base: float = 1000.0,
) -> dict[str, Any]:
    planned_seconds = duration_minutes * 60
    end_dt = _parse_utc_iso(start_iso) + timedelta(seconds=planned_seconds + 1)
    return build_wallclock_evidence_from_manifest_fields(
        utc_started=start_iso,
        utc_completed=_format_utc_iso(end_dt),
        duration_minutes=duration_minutes,
        start_monotonic_seconds=monotonic_base,
        end_monotonic_seconds=monotonic_base + planned_seconds + 1.0,
    )


def test_package_and_class4_markers_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert CHARTER_BUNDLE_SUFFIX in text


def test_canonical_evaluator_imported_not_duplicated() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    local_evaluators = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("evaluate_wallclock")
    ]
    assert local_evaluators == []
    test_module_imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("tests.")
    ]
    assert test_module_imports == []
    text = Path(__file__).read_text(encoding="utf-8")
    assert "from src.ops.wallclock_session_evidence_v0 import" in text
    assert "from src.ops.testnet_wallclock_duration_evidence_contract_v0 import" in text
    assert "evaluate_wallclock_evidence_fields" in text
    import src.ops.testnet_wallclock_duration_evidence_contract_v0 as canonical_field_owner

    assert REQUIRED_WALLCLOCK_FIELD_NAMES == canonical_field_owner.REQUIRED_WALLCLOCK_FIELD_NAMES


def test_testnet_precedent_field_names_reused() -> None:
    sample = build_wallclock_evidence_from_manifest_fields(
        utc_started="2026-06-22T10:00:00Z",
        utc_completed="2026-06-22T10:10:01Z",
        duration_minutes=STANDARD_DURATION_MINUTES,
        start_monotonic_seconds=1000.0,
        end_monotonic_seconds=1601.0,
    )
    for field in REQUIRED_WALLCLOCK_FIELD_NAMES:
        assert field in sample


def test_testnet_wallclock_contract_crosslink_present() -> None:
    assert TESTNET_WALLCLOCK_CONTRACT.is_file()
    assert "TESTNET_WALLCLOCK_DURATION_EVIDENCE_CONTRACT_V0=true" in (
        TESTNET_WALLCLOCK_CONTRACT.read_text(encoding="utf-8")
    )


def test_shadow_wrapper_and_adapter_test_owners_crosslinked() -> None:
    assert WRAPPER_TEST.is_file()
    assert ADAPTER_TEST.is_file()
    wrapper_text = WRAPPER_TEST.read_text(encoding="utf-8")
    adapter_text = ADAPTER_TEST.read_text(encoding="utf-8")
    assert Path(__file__).name in wrapper_text
    assert Path(__file__).name in adapter_text


def test_shadow_wrapper_exposes_manifest_duration_and_timestamp_fields() -> None:
    source = SHADOW_WRAPPER.read_text(encoding="utf-8")
    for marker in (
        "duration_minutes_requested",
        "duration_minutes_cap_enforced",
        "utc_started",
        "utc_completed",
    ):
        assert marker in source


def test_shadow_adapter_plan_delegates_declared_duration_to_wrapper() -> None:
    source = SHADOW_ADAPTER.read_text(encoding="utf-8")
    assert "duration_minutes" in source
    assert "--duration-minutes" in source
    assert "extended_tier_active" in source
    assert "EXTENDED_BOUNDED_SHADOW_CONFIRM_TOKEN_V0" in source


def test_standard_tier_ten_minute_pass() -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is True
    assert result["duration_proven"] is True
    assert evidence["planned_duration_seconds"] == STANDARD_DURATION_MINUTES * 60


def test_extended_tier_thirty_minute_pass() -> None:
    evidence = _synthetic_shadow_pass_evidence(EXTENDED_DURATION_MINUTES_30)
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is True
    assert result["duration_proven"] is True
    assert evidence["planned_duration_seconds"] == EXTENDED_DURATION_MINUTES_30 * 60


def test_extended_tier_sixty_minute_pass() -> None:
    evidence = _synthetic_shadow_pass_evidence(EXTENDED_DURATION_MINUTES_60)
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is True
    assert result["duration_proven"] is True
    assert evidence["planned_duration_seconds"] == EXTENDED_DURATION_MINUTES_60 * 60


def test_fast_sim_false_claim_multi_minute_tier_fails_closed() -> None:
    """Seconds-long actual run must not pass a multi-minute declared tier."""
    evidence = build_wallclock_evidence_from_manifest_fields(
        utc_started="2026-06-22T10:00:00Z",
        utc_completed="2026-06-22T10:00:05Z",
        duration_minutes=EXTENDED_DURATION_MINUTES_30,
        start_monotonic_seconds=1000.0,
        end_monotonic_seconds=1005.0,
    )
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False
    assert result["duration_proven"] is False
    assert any("R1" in reason for reason in result["fail_reasons"])


@pytest.mark.parametrize("missing_field", ("start_wall_clock_iso", "end_wall_clock_iso"))
def test_missing_start_or_end_timestamps_fail_closed(missing_field: str) -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    evidence[missing_field] = ""
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False
    assert any("R2" in reason for reason in result["fail_reasons"])


def test_negative_elapsed_wall_clock_fails_closed() -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    evidence["elapsed_wall_clock_seconds"] = -1.0
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False
    assert any("R1" in reason for reason in result["fail_reasons"])


def test_non_finite_elapsed_wall_clock_inf_fails_closed() -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    evidence["elapsed_wall_clock_seconds"] = math.inf
    evidence["elapsed_monotonic_seconds"] = math.inf
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False
    assert any("R8" in reason for reason in result["fail_reasons"])


def test_end_before_start_fails_closed() -> None:
    evidence = build_wallclock_evidence_from_manifest_fields(
        utc_started="2026-06-22T10:10:00Z",
        utc_completed="2026-06-22T10:00:00Z",
        duration_minutes=STANDARD_DURATION_MINUTES,
        start_monotonic_seconds=1600.0,
        end_monotonic_seconds=1000.0,
    )
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False


def test_null_declared_duration_fails_closed() -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    evidence.pop("planned_duration_seconds")
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False
    assert any("R7" in reason for reason in result["fail_reasons"])


def test_negative_declared_duration_maps_to_canonical_bounds() -> None:
    evidence = build_wallclock_evidence_from_manifest_fields(
        utc_started="2026-06-22T10:00:00Z",
        utc_completed="2026-06-22T10:00:01Z",
        duration_minutes=-5,
        start_monotonic_seconds=1000.0,
        end_monotonic_seconds=1001.0,
    )
    assert evidence["planned_duration_seconds"] == -300


def test_missing_planned_or_elapsed_invalidates_evidence() -> None:
    result = evaluate_wallclock_evidence_fields({"planned_duration_seconds": 600})
    assert result["duration_evidence_valid"] is False
    assert any("R7" in reason for reason in result["fail_reasons"])


@pytest.mark.parametrize(
    ("duration_minutes", "elapsed_offset_seconds", "valid"),
    [
        (STANDARD_DURATION_MINUTES, 0, True),
        (STANDARD_DURATION_MINUTES, -1, False),
        (EXTENDED_DURATION_MINUTES_30, 0, True),
        (EXTENDED_DURATION_MINUTES_30, -1, False),
    ],
)
def test_tolerance_boundaries_at_min_required_wall_clock(
    duration_minutes: int,
    elapsed_offset_seconds: int,
    valid: bool,
) -> None:
    planned = duration_minutes * 60
    bounds = bounds_from_planned_duration(planned)
    min_required = bounds["min_required_wall_clock_seconds"]
    start_iso = "2026-06-22T10:00:00Z"
    end_dt = _parse_utc_iso(start_iso) + timedelta(seconds=min_required + elapsed_offset_seconds)
    evidence = build_wallclock_evidence_from_manifest_fields(
        utc_started=start_iso,
        utc_completed=_format_utc_iso(end_dt),
        duration_minutes=duration_minutes,
        start_monotonic_seconds=1000.0,
        end_monotonic_seconds=1000.0 + min_required + elapsed_offset_seconds,
    )
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is valid


@pytest.mark.parametrize(
    ("elapsed_wall", "elapsed_mono", "valid"),
    [
        (1801.0, 1800.172, True),
        (1801.0, 1798.0, True),
        (1801.0, 1700.0, False),
    ],
)
def test_monotonic_cross_check_uses_canonical_tolerance(
    elapsed_wall: float,
    elapsed_mono: float,
    valid: bool,
) -> None:
    evidence = _synthetic_shadow_pass_evidence(EXTENDED_DURATION_MINUTES_30)
    evidence["elapsed_wall_clock_seconds"] = elapsed_wall
    evidence["elapsed_monotonic_seconds"] = elapsed_mono
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is valid


def test_inconsistent_elapsed_field_fails_closed() -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    evidence["elapsed_wall_clock_seconds"] = 999.0
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False


def test_elapsed_above_max_acceptable_fails_closed() -> None:
    evidence = _synthetic_shadow_pass_evidence(EXTENDED_DURATION_MINUTES_30)
    evidence["elapsed_wall_clock_seconds"] = evidence["max_acceptable_wall_clock_seconds"] + 1.0
    evidence["elapsed_monotonic_seconds"] = evidence["elapsed_wall_clock_seconds"]
    result = evaluate_wallclock_evidence_fields(evidence)
    assert result["duration_evidence_valid"] is False
    assert any("R8" in reason for reason in result["fail_reasons"])


def test_invalid_if_elapsed_below_min_charter_invariant() -> None:
    assert evaluate_wallclock_evidence_fields({})["fail_reasons"]
    bad = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    bad["invalid_if_elapsed_below_min"] = False
    result = evaluate_wallclock_evidence_fields(bad)
    assert result["duration_evidence_valid"] is False


def test_identical_inputs_produce_identical_evidence() -> None:
    kwargs = {
        "utc_started": "2026-06-22T12:00:00Z",
        "utc_completed": "2026-06-22T12:10:01Z",
        "duration_minutes": STANDARD_DURATION_MINUTES,
        "start_monotonic_seconds": 2000.0,
        "end_monotonic_seconds": 2601.0,
    }
    first = build_wallclock_evidence_from_manifest_fields(**kwargs)
    second = build_wallclock_evidence_from_manifest_fields(**kwargs)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_canonical_evaluator_module_unchanged_marker() -> None:
    source = CANONICAL_EVALUATOR.read_text(encoding="utf-8")
    assert "RUNTIME_WALLCLOCK_SESSION_EVIDENCE_V0=true" in source
    assert "evaluate_wallclock_evidence_fields" in source
    assert WALLCLOCK_EVIDENCE_FILENAME in source


def test_shadow_closeout_must_include_planned_vs_elapsed_fields() -> None:
    required = {"planned_duration_seconds", "elapsed_wall_clock_seconds", "duration_proven"}
    sample = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    assert required.issubset(sample.keys())
    serialized = json.dumps(sample)
    for key in required:
        assert key in serialized


def test_default_wall_clock_slack_matches_testnet_precedent() -> None:
    assert DEFAULT_WALL_CLOCK_SLACK_SECONDS == 60
    bounds = bounds_from_planned_duration(STANDARD_DURATION_MINUTES * 60)
    assert bounds["wall_clock_slack_seconds"] == DEFAULT_WALL_CLOCK_SLACK_SECONDS


def test_canonical_writer_serializes_evaluator_result_deterministically(tmp_path: Path) -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    out_path = tmp_path / WALLCLOCK_EVIDENCE_FILENAME
    write_wallclock_evidence(out_path, evidence)
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written == evidence
    assert out_path.name == WALLCLOCK_EVIDENCE_FILENAME
    assert json.dumps(written, indent=2, sort_keys=True) + "\n" == out_path.read_text(
        encoding="utf-8"
    )


def test_canonical_writer_does_not_recompute_evaluation(tmp_path: Path) -> None:
    evidence = _synthetic_shadow_pass_evidence(STANDARD_DURATION_MINUTES)
    evidence["duration_proven"] = False
    evidence["duration_evidence_valid"] = False
    out_path = tmp_path / WALLCLOCK_EVIDENCE_FILENAME
    write_wallclock_evidence(out_path, evidence)
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["duration_proven"] is False
    assert written["duration_evidence_valid"] is False


def test_shadow_adapter_emits_wallclock_evidence_filename() -> None:
    source = SHADOW_ADAPTER.read_text(encoding="utf-8")
    assert "WALLCLOCK_EVIDENCE_FILENAME" in source
    assert "build_wallclock_evidence_from_manifest_fields" in source
    assert "write_wallclock_evidence" in source
