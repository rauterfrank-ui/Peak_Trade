"""Autonomous Ops Control Plane v0 — fixture-driven transition contracts (tests-only).

Loads JSON fixtures under ``tests/fixtures/ops/control_plane_transition_v0/``.
Reuses frozen literals from PR #3754 state-model contract tests. Does not implement
the offline plan generator and never imports or executes runtime/scheduler paths.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from tests.ops.test_autonomous_ops_control_plane_state_model_contract_v0 import (
    CONTROL_PLANE_STATES_V0,
    FORBIDDEN_TRANSITIONS_V0,
    REQUIRED_INTERMEDIATE_FOR_TARGET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests/fixtures/ops/control_plane_transition_v0"
STATE_MODEL_TEST = (
    REPO_ROOT / "tests/ops/test_autonomous_ops_control_plane_state_model_contract_v0.py"
)

REQUIRED_FIXTURE_KEYS: frozenset[str] = frozenset(
    {
        "case_id",
        "initial_state",
        "target_state",
        "steps",
        "expected_forbidden",
        "required_intermediate_states",
        "expected_machine_lines",
    }
)

REQUIRED_MACHINE_LINE_KEYS: frozenset[str] = frozenset(
    {
        "RUNTIME_START_REQUIRED",
        "SCHEDULER_START_REQUIRED",
        "SUPERVISOR_START_REQUIRED",
        "DAEMON_START_REQUIRED",
        "PAPER_SHADOW_TESTNET_LIVE_START_REQUIRED",
        "AWS_REMOTE_REQUIRED",
        "S3_UPLOAD_REQUIRED",
        "SSH_REQUIRED",
        "NETWORK_REQUIRED",
        "LIVE_AUTHORITY_CHANGED",
        "MASTER_V2_DOUBLE_PLAY_TOUCHED",
    }
)

_FORBIDDEN_SOURCE_PATTERNS: tuple[str, ...] = (
    "subprocess.run",
    "subprocess.Popen",
    "os.system",
    "boto3",
    "paramiko",
    "import requests",
    "import urllib",
    "import socket",
    "run_scheduler.main(",
)


def _this_module_source() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def _load_fixtures() -> list[dict[str, Any]]:
    assert FIXTURE_DIR.is_dir(), f"missing fixture dir: {FIXTURE_DIR}"
    paths = sorted(FIXTURE_DIR.glob("*.json"))
    assert paths, f"no JSON fixtures in {FIXTURE_DIR}"
    fixtures: list[dict[str, Any]] = []
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        fixtures.append(json.loads(raw))
    return fixtures


def _edges(steps: list[str]) -> list[tuple[str, str]]:
    return list(zip(steps, steps[1:]))


def _has_forbidden_direct_edge(steps: list[str]) -> bool:
    return any(edge in FORBIDDEN_TRANSITIONS_V0 for edge in _edges(steps))


def _missing_required_intermediate(steps: list[str]) -> bool:
    step_set = set(steps)
    for (src, dst), required in REQUIRED_INTERMEDIATE_FOR_TARGET.items():
        if src in step_set and dst in step_set:
            for mid in required:
                if mid not in step_set:
                    return True
    return False


def _transition_violation(steps: list[str]) -> bool:
    return _has_forbidden_direct_edge(steps) or _missing_required_intermediate(steps)


def test_state_model_contract_module_crosslink_v0() -> None:
    text = STATE_MODEL_TEST.read_text(encoding="utf-8")
    assert "CONTROL_PLANE_STATES_V0" in text
    assert len(CONTROL_PLANE_STATES_V0) == 8


def test_fixture_directory_has_unique_case_ids_v0() -> None:
    fixtures = _load_fixtures()
    case_ids = [f["case_id"] for f in fixtures]
    assert len(case_ids) == len(set(case_ids))


def test_all_fixtures_have_stable_minimal_schema_v0() -> None:
    for fixture in _load_fixtures():
        assert REQUIRED_FIXTURE_KEYS <= fixture.keys()
        assert isinstance(fixture["case_id"], str) and fixture["case_id"]
        assert isinstance(fixture["steps"], list)
        assert isinstance(fixture["expected_forbidden"], bool)
        assert isinstance(fixture["required_intermediate_states"], list)
        machine = fixture["expected_machine_lines"]
        assert isinstance(machine, dict)
        assert REQUIRED_MACHINE_LINE_KEYS <= machine.keys()


@pytest.mark.parametrize("fixture", _load_fixtures(), ids=lambda f: f["case_id"])
def test_fixture_states_belong_to_eight_state_model_v0(fixture: dict[str, Any]) -> None:
    states = set(CONTROL_PLANE_STATES_V0)
    assert fixture["initial_state"] in states
    assert fixture["target_state"] in states
    for step in fixture["steps"]:
        assert step in states, f"unknown state in steps: {step!r}"


@pytest.mark.parametrize("fixture", _load_fixtures(), ids=lambda f: f["case_id"])
def test_fixture_steps_begin_with_initial_and_end_at_target_v0(fixture: dict[str, Any]) -> None:
    steps = fixture["steps"]
    assert steps, "steps must be non-empty"
    assert steps[0] == fixture["initial_state"]
    assert steps[-1] == fixture["target_state"]


@pytest.mark.parametrize("fixture", _load_fixtures(), ids=lambda f: f["case_id"])
def test_fixture_forbidden_expectation_matches_transition_rules_v0(
    fixture: dict[str, Any],
) -> None:
    violated = _transition_violation(fixture["steps"])
    assert fixture["expected_forbidden"] == violated, (
        f"case_id={fixture['case_id']!r} expected_forbidden={fixture['expected_forbidden']} "
        f"computed_violation={violated}"
    )


@pytest.mark.parametrize("fixture", _load_fixtures(), ids=lambda f: f["case_id"])
def test_legal_path_required_intermediates_present_v0(fixture: dict[str, Any]) -> None:
    if fixture["expected_forbidden"]:
        return
    step_set = set(fixture["steps"])
    for required in fixture["required_intermediate_states"]:
        assert required in step_set, (
            f"case_id={fixture['case_id']!r} missing required intermediate {required!r}"
        )


def test_forbidden_direct_transitions_covered_by_fixtures_v0() -> None:
    fixtures = _load_fixtures()
    forbidden_cases = {f["case_id"] for f in fixtures if f["expected_forbidden"]}
    assert "forbidden_stop_idle_to_running_v0" in forbidden_cases
    assert "forbidden_preflight_blocked_to_running_v0" in forbidden_cases
    assert "forbidden_preflight_pass_to_running_without_operator_token_v0" in forbidden_cases
    assert "forbidden_running_to_evidence_verified_without_closeout_v0" in forbidden_cases


def test_legal_running_path_requires_ready_for_operator_token_v0() -> None:
    legal = next(
        f for f in _load_fixtures() if f["case_id"] == "legal_ready_for_operator_token_path_v0"
    )
    assert "READY_FOR_OPERATOR_TOKEN" in legal["steps"]
    assert "READY_FOR_OPERATOR_TOKEN" in legal["required_intermediate_states"]
    assert not _transition_violation(legal["steps"])


def test_fail_closed_fixture_never_authorizes_starts_v0() -> None:
    fail_closed = next(
        f for f in _load_fixtures() if f["case_id"] == "fail_closed_missing_evidence_v0"
    )
    assert fail_closed["target_state"] == "FAILED_CLOSED"
    machine = fail_closed["expected_machine_lines"]
    for key in (
        "RUNTIME_START_REQUIRED",
        "SCHEDULER_START_REQUIRED",
        "PAPER_SHADOW_TESTNET_LIVE_START_REQUIRED",
    ):
        assert machine[key] is False


@pytest.mark.parametrize("fixture", _load_fixtures(), ids=lambda f: f["case_id"])
def test_fixture_machine_lines_keep_authority_false_v0(fixture: dict[str, Any]) -> None:
    machine = fixture["expected_machine_lines"]
    for key in REQUIRED_MACHINE_LINE_KEYS:
        assert machine[key] is False, f"{fixture['case_id']}: {key} must be false"


def test_module_imports_are_stdlib_and_state_model_only_v0() -> None:
    allowed_roots = frozenset({"__future__", "ast", "json", "pathlib", "pytest", "typing", "tests"})
    tree = ast.parse(_this_module_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module is not None
            root = node.module.split(".")[0]
            assert root in allowed_roots, f"unexpected import from: {node.module!r}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_roots, f"unexpected import: {alias.name!r}"


def test_module_has_no_runtime_or_network_patterns_v0() -> None:
    in_forbidden_tuple = False
    for line in _this_module_source().splitlines():
        if "_FORBIDDEN_SOURCE_PATTERNS" in line:
            in_forbidden_tuple = True
            continue
        if in_forbidden_tuple:
            if line.strip().startswith(")"):
                in_forbidden_tuple = False
            continue
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert pattern not in line, (
                f"forbidden pattern in contract test source: {pattern!r} line={line!r}"
            )
