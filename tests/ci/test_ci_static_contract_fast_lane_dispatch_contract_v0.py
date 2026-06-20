"""Contract tests for Fast-Lane static contract selector dispatch (PKG-CI-01)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CI_YML = Path(".github/workflows/ci.yml")
SELECTOR = Path("scripts/ops/ci_test_selection_v1.py")
REQUIRED_CHECKS = Path("config/ci/required_status_checks.json")


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


def _targets(raw: str) -> list[str]:
    return sorted(raw.split()) if raw else []


def test_changes_job_exports_fast_lane_selector_outputs() -> None:
    block = _ci_text().split("  changes:", 1)[1].split("  ci-required-contexts-contract:", 1)[0]
    for key in (
        "fast_lane_pytest_targets",
        "fast_lane_execute_static_contract",
        "focused_cross_version_matrix",
    ):
        assert f"{key}:" in block


def test_fast_lane_blocks_legacy_ops_fullsweep() -> None:
    text = _ci_text()
    assert "find tests/ops -name 'test_*.py'" not in text
    assert "OPS_SHARD_COUNT=8" not in text
    assert "pytest tests/ci tests/ops" not in text
    assert (
        "needs.changes.outputs.static_contract_changed == 'true'"
        not in text.split("  fast-lane:", 1)[1].split("  tests:", 1)[0]
    )
    assert "needs.changes.outputs.fast_lane_execute_static_contract == 'true'" in text


def test_fast_lane_no_op_skip_step_present() -> None:
    text = _ci_text()
    assert "NO_OP — skip Fast-Lane static contract dispatch (selector)" in text
    assert "fast_lane_execute_static_contract != 'true'" in text


def test_fast_lane_focused_full_skip_step_present() -> None:
    text = _ci_text()
    assert "FOCUSED/FULL — skip Fast-Lane static contract dispatch (selector)" in text
    assert "tests_execute_no_op != 'true'" in text


def test_tests_job_primary_python_focused_dispatch() -> None:
    text = _ci_text()
    assert "Primary Python — skip focused pytest (3.9/3.10)" in text
    assert "focused_cross_version_matrix != 'true'" in text
    assert "matrix.python-version == '3.11'" in text


def test_required_check_names_unchanged() -> None:
    text = _ci_text()
    assert "name: tests (${{ matrix.python-version }})" in text
    assert "name: strategy-smoke" in text
    assert "name: Fast-Lane" in text
    assert "python-version: ['3.9', '3.10', '3.11']" in text
    required = REQUIRED_CHECKS.read_text(encoding="utf-8")
    assert '"tests (3.11)"' in required


@pytest.mark.parametrize(
    ("files", "expect_mode", "expect_fast_lane", "expect_targets_nonempty"),
    [
        (("docs/TECH_DEBT_BACKLOG.md",), "NO_OP", "false", False),
        ((".github/workflows/ci.yml",), "NO_OP", "false", False),
        (("tests/ops/test_report_readiness_gate_snapshot_v0.py",), "NO_OP", "true", True),
        (("tests/test_stability_smoke.py",), "FOCUSED", "false", False),
        (
            ("tests/fixtures/ops/pe38_readiness_review/minimal_proof_chain.json",),
            "FOCUSED",
            "false",
            False,
        ),
        (
            ("src/strategies/vol_breakout.py", "tests/test_strategies_phase27.py"),
            "FOCUSED",
            "false",
            False,
        ),
        (("src/execution/module.py",), "FULL", "false", False),
        (
            (
                "scripts/ops/ci_test_selection_v1.py",
                "config/ci/file_category_mapping.yaml",
                ".github/workflows/ci.yml",
            ),
            "FULL",
            "false",
            False,
        ),
        (("requirements.txt", "scripts/demo_strategy_research.py"), "FULL", "false", False),
        (("mystery/unknown.file",), "FULL", "false", False),
    ],
)
def test_selector_dispatch_modes_regression(
    files: tuple[str, ...],
    expect_mode: str,
    expect_fast_lane: str,
    expect_targets_nonempty: bool,
) -> None:
    sel = _run_selector(*files)
    assert sel["test_selection_mode"] == expect_mode
    assert sel["fast_lane_execute_static_contract"] == expect_fast_lane
    if expect_targets_nonempty:
        assert _targets(sel.get("fast_lane_pytest_targets", ""))
    else:
        assert not sel.get("fast_lane_pytest_targets", "")


def test_selector_static_contract_no_op_maps_changed_test_owner() -> None:
    sel = _run_selector("tests/ops/test_report_readiness_gate_snapshot_v0.py")
    assert sel["tests_execute_no_op"] == "true"
    assert sel["fast_lane_execute_static_contract"] == "true"
    assert "tests/ops/test_report_readiness_gate_snapshot_v0.py" in _targets(
        sel.get("fast_lane_pytest_targets", "")
    )


def test_selector_static_contract_src_ops_maps_test_owner() -> None:
    prod = "src/ops/bounded_futures_testnet_contract_v0.py"
    sel = _run_selector(prod)
    assert sel["test_selection_mode"] == "NO_OP"
    assert sel["fast_lane_execute_static_contract"] == "true"
    assert "tests/ops/test_bounded_futures_testnet_contract_v0.py" in _targets(
        sel.get("fast_lane_pytest_targets", "")
    )


def test_selector_static_contract_wide_diff_fail_closed_full() -> None:
    files = (
        "tests/ops/test_report_readiness_gate_snapshot_v0.py",
        "tests/ops/test_mandatory_durable_closeout_contract_v0.py",
        "tests/ops/test_durable_closeout_copy_verify_v0.py",
        "tests/ops/test_build_readiness_evidence_ledger_v0.py",
        "tests/ops/test_gap7_risk_boundary_drift_guard_contract_v0.py",
        "tests/ops/test_primary_evidence_retention_invariant_contract_v0.py",
    )
    sel = _run_selector(*files)
    assert sel["test_selection_mode"] == "FULL"
    assert sel["test_selection_reason"] == "static_contract_wide_diff_requires_full"


def test_selector_focused_primary_python_by_default() -> None:
    sel = _run_selector("tests/test_stability_smoke.py")
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["focused_cross_version_matrix"] == "false"


def test_selector_focused_cross_version_on_dependencies() -> None:
    sel = _run_selector("scripts/demo_strategy_research.py", "requirements.txt")
    assert sel["test_selection_mode"] == "FULL"


def test_selector_unknown_mode_fail_closed_full() -> None:
    sel = _run_selector("mystery/unknown.file")
    assert sel["test_selection_mode"] == "FULL"
    assert sel["tests_execute_full"] == "true"
