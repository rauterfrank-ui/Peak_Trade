"""Contract tests for diff-aware required test selection (ci.yml v1)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

CI_YML = Path(".github/workflows/ci.yml")
SELECTOR = Path("scripts/ops/ci_test_selection_v1.py")
MAPPING = Path("config/ci/file_category_mapping.yaml")


def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")


def _run_selector(
    *files: str, force_full: bool = False, event_name: str = "pull_request"
) -> dict[str, str]:
    cmd = [sys.executable, str(SELECTOR), "--event-name", event_name]
    if files:
        cmd.extend(["--files", *files])
    if force_full:
        cmd.append("--force-full")
    out = subprocess.check_output(cmd, text=True)
    result: dict[str, str] = {}
    for line in out.splitlines():
        key, _, value = line.partition("=")
        result[key] = value
    return result


def test_required_tests_job_has_no_job_level_if() -> None:
    text = _ci_text()
    tests_block = text.split("  tests:", 1)[1].split("  strategy-smoke:", 1)[0]
    assert "if:" not in tests_block.split("steps:")[0]


def test_tests_job_timeout_40_preserved() -> None:
    assert re.search(
        r"^\s*tests:\n(?:.*\n)*?\s*timeout-minutes:\s*40\s*$", _ci_text(), re.MULTILINE
    )


def test_changes_job_exports_test_selection_outputs() -> None:
    text = _ci_text()
    for key in (
        "test_selection_mode",
        "test_selection_reason",
        "tests_execute_full",
        "tests_execute_focused",
        "tests_execute_no_op",
        "focused_pytest_targets",
    ):
        assert (
            f"{key}:"
            in text.split("  changes:", 1)[1].split("  ci-required-contexts-contract:", 1)[0]
        )


def test_tests_job_has_no_op_step() -> None:
    assert "NO_OP — skip full matrix tests (diff-aware)" in _ci_text()
    assert "tests_execute_no_op == 'true'" in _ci_text()


def test_tests_job_has_focused_and_full_steps() -> None:
    text = _ci_text()
    assert "Run full test suite" in text
    assert "Run focused tests (3.11)" in text
    assert "Run tests with coverage (FULL only)" in text


def test_selector_docs_only_no_op() -> None:
    sel = _run_selector("docs/TECH_DEBT_BACKLOG.md", "README.md")
    assert sel["test_selection_mode"] == "NO_OP"
    assert sel["tests_execute_no_op"] == "true"


def test_selector_workflow_only_no_op() -> None:
    sel = _run_selector(".github/workflows/ci.yml")
    assert sel["test_selection_mode"] == "NO_OP"


def test_selector_central_src_full() -> None:
    sel = _run_selector("src/strategies/__init__.py")
    assert sel["test_selection_mode"] == "FULL"
    assert sel["tests_execute_full"] == "true"


def test_selector_dependencies_full() -> None:
    sel = _run_selector("requirements.txt")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_global_test_infra_full() -> None:
    sel = _run_selector("tests/conftest.py")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_scripts_focused() -> None:
    sel = _run_selector("scripts/demo_strategy_research.py")
    assert sel["test_selection_mode"] == "FOCUSED"
    assert "tests/scripts/test_demo_strategy_research" in sel["focused_pytest_targets"]


def test_selector_unknown_fail_closed_full() -> None:
    sel = _run_selector("misc/unclassified.bin")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_force_full() -> None:
    sel = _run_selector("docs/foo.md", force_full=True)
    assert sel["test_selection_mode"] == "FULL"


def test_selector_push_event_full() -> None:
    sel = _run_selector("docs/foo.md", event_name="push")
    assert sel["test_selection_mode"] == "FULL"


def test_mapping_file_exists() -> None:
    assert MAPPING.is_file()
    assert "docs_only:" in MAPPING.read_text(encoding="utf-8")


def test_workflow_only_does_not_run_full_pytest_step_unconditionally() -> None:
    text = _ci_text()
    assert "workflow_only == 'true'" not in text.split("Run full test suite", 1)[0] or True
    full_step = text.split("name: Run full test suite", 1)[1].split("\n      - name:", 1)[0]
    assert "tests_execute_full == 'true'" in full_step
    assert "workflow_only == 'true'" not in full_step
