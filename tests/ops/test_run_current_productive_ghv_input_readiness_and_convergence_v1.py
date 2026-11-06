"""Orchestration safety tests for GHV input readiness WP runner (no live network)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts.ops.run_current_productive_ghv_input_readiness_and_convergence_v1 import (
    BOUNDED_CHILD_MAX_RUN_DURATION_SECONDS,
    PARENT_OUTER_WATCHDOG_MARGIN_SECONDS,
    TERMINATION_CHILD_COMPLETED,
    TERMINATION_PARENT_OUTER_WATCHDOG,
    build_bounded_pre_external_launcher_argv_v1,
    compute_bounded_child_outer_watchdog_seconds_v1,
    invoke_bounded_pre_external_child_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_outer_watchdog_exceeds_inner_bound() -> None:
    outer = compute_bounded_child_outer_watchdog_seconds_v1(
        inner_max_run_duration_seconds=BOUNDED_CHILD_MAX_RUN_DURATION_SECONDS,
    )
    assert outer == BOUNDED_CHILD_MAX_RUN_DURATION_SECONDS + PARENT_OUTER_WATCHDOG_MARGIN_SECONDS


def test_build_launcher_argv_uses_scripts_pt() -> None:
    launcher = (
        REPO
        / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
    )
    argv = build_bounded_pre_external_launcher_argv_v1(
        repo_root=REPO,
        launcher=launcher,
        run_evidence=Path("/tmp/evidence"),
        run_lane=Path("/tmp/lane"),
        run_prod=Path("/tmp/prod"),
    )
    assert argv[0].endswith("scripts/pt")
    assert str(launcher) in argv


def test_invoke_bounded_child_passes_outer_timeout_to_subprocess(tmp_path: Path) -> None:
    launcher = tmp_path / "launcher.py"
    launcher.write_text("# stub\n", encoding="utf-8")
    run_evidence = tmp_path / "bounded_run"
    run_evidence.mkdir()
    expected_timeout = compute_bounded_child_outer_watchdog_seconds_v1(
        inner_max_run_duration_seconds=120.0,
    )

    class _Proc:
        returncode = 0
        stdout = "{}"
        stderr = ""

    with patch(
        "scripts.ops.run_current_productive_ghv_input_readiness_and_convergence_v1.subprocess.run",
        return_value=_Proc(),
    ) as mock_run:
        result = invoke_bounded_pre_external_child_v1(
            repo_root=REPO,
            launcher=launcher,
            run_evidence=run_evidence,
            run_lane=tmp_path / "lane",
            run_prod=tmp_path / "prod",
        )
    assert mock_run.call_args.kwargs["timeout"] == expected_timeout
    assert result.termination_reason == TERMINATION_CHILD_COMPLETED
    assert result.parent_timeout is False


def test_invoke_bounded_child_parent_timeout_classified(tmp_path: Path) -> None:
    import subprocess

    launcher = tmp_path / "launcher.py"
    launcher.write_text("# stub\n", encoding="utf-8")
    run_evidence = tmp_path / "bounded_run"
    run_evidence.mkdir()

    with patch(
        "scripts.ops.run_current_productive_ghv_input_readiness_and_convergence_v1.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1),
    ):
        result = invoke_bounded_pre_external_child_v1(
            repo_root=REPO,
            launcher=launcher,
            run_evidence=run_evidence,
            run_lane=tmp_path / "lane",
            run_prod=tmp_path / "prod",
        )
    assert result.parent_timeout is True
    assert result.termination_reason == TERMINATION_PARENT_OUTER_WATCHDOG
