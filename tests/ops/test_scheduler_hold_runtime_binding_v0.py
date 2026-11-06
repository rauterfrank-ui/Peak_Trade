"""Contract tests for RUN_ID-scoped scheduler HOLD runtime binding v0."""

from __future__ import annotations

import importlib.util
import stat
import sys
from pathlib import Path

import pytest

from scripts.ops.paper_shadow_247_scheduler_hold_runtime_binding_v0 import (
    build_scheduler_hold_runtime_binding_v0,
)
from scripts.ops.report_paper_shadow_247_preflight_status import (
    build_paper_shadow_247_preflight_status,
)
from scripts.ops.scheduler_start_boundary_guard_v0 import (
    SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV,
    SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV,
    SCHEDULER_START_BLOCKED_EXIT,
)
from tests.ops.test_paper_shadow_247_execution_prep_readiness_binding_v0 import (
    _materialize_valid_outroot as _materialize_execution_prep_outroot,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_GUARD = REPO_ROOT / "scripts" / "ops" / "scheduler_start_boundary_guard_v0.py"
BINDING_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "ops" / "scheduler_hold_runtime_binding_v0"
RUN_ID = "daemon_paper_24h_test_fixture_v0"


def _load_guard_module():
    spec = importlib.util.spec_from_file_location("scheduler_start_boundary_guard_v0", SHARED_GUARD)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_adapter_approval_records(outroot: Path, *, run_id: str = RUN_ID) -> None:
    text = (
        (BINDING_FIXTURES / "BOUNDED_ADAPTER_24H_EXECUTE_APPROVAL_RECORD_V0.md")
        .read_text(encoding="utf-8")
        .replace("__RUN_ID__", run_id)
    )
    for rel in (
        "preflight/BOUNDED_ADAPTER_24H_EXECUTE_APPROVAL_RECORD_V0.md",
        "closeout/BOUNDED_ADAPTER_24H_EXECUTE_APPROVAL_RECORD_ARCHIVE_ONLY_V0.md",
    ):
        path = outroot / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _write_canonical_combined_command(outroot: Path, *, run_id: str = RUN_ID) -> None:
    text = (
        (BINDING_FIXTURES / "CANONICAL_COMBINED_PAPER_SHADOW_START_COMMAND_V0.sh")
        .read_text(encoding="utf-8")
        .replace("__RUN_ID__", run_id)
        .replace("__OUTROOT__", str(outroot))
    )
    path = outroot / "commands" / "CANONICAL_COMBINED_PAPER_SHADOW_START_COMMAND_V0.sh"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _materialize_valid_binding_outroot(tmp_path: Path, **kwargs: object) -> Path:
    outroot = _materialize_execution_prep_outroot(tmp_path, **kwargs)
    _write_adapter_approval_records(outroot)
    _write_canonical_combined_command(outroot)
    return outroot


def test_binding_module_valid_fixture(tmp_path: Path) -> None:
    outroot = _materialize_valid_binding_outroot(tmp_path)
    binding = build_scheduler_hold_runtime_binding_v0(outroot, expected_run_id=RUN_ID)
    assert binding["valid"] is True
    assert binding["clearance_granted"] is True
    assert binding["binding_scope"] == "bounded_24h_daemon_paper_shadow_dry_run_only"
    assert binding["clears_global_hold_no_paper_run"] is False
    assert binding["permits_testnet_live_broker_exchange"] is False


def test_binding_fails_closed_wrong_run_id(tmp_path: Path) -> None:
    outroot = _materialize_valid_binding_outroot(tmp_path)
    binding = build_scheduler_hold_runtime_binding_v0(outroot, expected_run_id="wrong_run_id")
    assert binding["valid"] is False


def test_binding_fails_closed_missing_adapter_approval(tmp_path: Path) -> None:
    outroot = _materialize_valid_binding_outroot(tmp_path)
    (outroot / "preflight" / "BOUNDED_ADAPTER_24H_EXECUTE_APPROVAL_RECORD_V0.md").unlink()
    binding = build_scheduler_hold_runtime_binding_v0(outroot, expected_run_id=RUN_ID)
    assert binding["valid"] is False
    assert binding["adapter_execute_approval_valid"] is False


def test_binding_fails_closed_missing_canonical_command(tmp_path: Path) -> None:
    outroot = _materialize_valid_binding_outroot(tmp_path)
    (outroot / "commands" / "CANONICAL_COMBINED_PAPER_SHADOW_START_COMMAND_V0.sh").unlink()
    binding = build_scheduler_hold_runtime_binding_v0(outroot, expected_run_id=RUN_ID)
    assert binding["valid"] is False
    assert binding["canonical_combined_command_valid"] is False


def test_binding_fails_closed_missing_governance(tmp_path: Path) -> None:
    outroot = _materialize_valid_binding_outroot(tmp_path, include_governance=False)
    binding = build_scheduler_hold_runtime_binding_v0(outroot, expected_run_id=RUN_ID)
    assert binding["valid"] is False


def test_reporter_default_unchanged_without_outroot_bridge(tmp_path: Path) -> None:
    from tests.ops.test_report_paper_shadow_247_preflight_status_cli_v0 import (
        _assert_hold_context_v0,
        _materialize_minimal_preflight_repo,
    )

    repo = _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    payload = build_paper_shadow_247_preflight_status(repo)
    assert payload["status"] == "BLOCKED"
    assert payload["scheduler_execution_authorized"] is False
    _assert_hold_context_v0(payload)
    assert payload.get("scheduler_hold_runtime_binding_v0") is None


def test_guard_blocks_without_env_bridge(monkeypatch) -> None:
    mod = _load_guard_module()
    monkeypatch.delenv(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV, raising=False)
    monkeypatch.delenv(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV, raising=False)
    with pytest.raises(SystemExit) as exc:
        mod.assert_scheduler_start_authorized()
    assert exc.value.code == SCHEDULER_START_BLOCKED_EXIT


def test_guard_allows_valid_env_binding(tmp_path: Path, monkeypatch, capsys) -> None:
    mod = _load_guard_module()
    outroot = _materialize_valid_binding_outroot(tmp_path)
    monkeypatch.setenv(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV, str(outroot))
    monkeypatch.setenv(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV, RUN_ID)
    mod.assert_scheduler_start_authorized()
    out = capsys.readouterr().out
    assert "SCHEDULER_HOLD_RUNTIME_BINDING_CLEARANCE=true" in out
    assert "SCHEDULER_START_AUTHORIZED_FOR_RUN_ID_SCOPED_BOUNDED_24H=true" in out
    assert "HOLD_NO_PAPER_RUN_ACTIVE=true" not in out


def test_guard_blocks_invalid_env_binding(tmp_path: Path, monkeypatch) -> None:
    mod = _load_guard_module()
    outroot = _materialize_valid_binding_outroot(tmp_path)
    monkeypatch.setenv(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV, str(outroot))
    monkeypatch.setenv(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV, "wrong_run_id")
    with pytest.raises(SystemExit) as exc:
        mod.assert_scheduler_start_authorized()
    assert exc.value.code == SCHEDULER_START_BLOCKED_EXIT


def test_guard_blocks_partial_env(monkeypatch, tmp_path: Path) -> None:
    mod = _load_guard_module()
    outroot = _materialize_valid_binding_outroot(tmp_path)
    monkeypatch.setenv(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV, str(outroot))
    monkeypatch.delenv(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV, raising=False)
    with pytest.raises(SystemExit) as exc:
        mod.assert_scheduler_start_authorized()
    assert exc.value.code == SCHEDULER_START_BLOCKED_EXIT


def test_guard_injected_preflight_still_blocks_hold(monkeypatch) -> None:
    mod = _load_guard_module()
    monkeypatch.delenv(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV, raising=False)
    monkeypatch.delenv(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV, raising=False)
    with pytest.raises(SystemExit) as exc:
        mod.assert_scheduler_start_authorized(
            {
                "status": "BLOCKED",
                "scheduler_execution_authorized": False,
                "hold_context_v0": {"current_state": "HOLD_NO_PAPER_RUN"},
            }
        )
    assert exc.value.code == SCHEDULER_START_BLOCKED_EXIT


def test_paper_adapter_scheduler_bridge_sets_env_for_24h_profile(
    tmp_path: Path, monkeypatch
) -> None:
    from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import (
        ExecuteContext,
        build_plan,
        execute_plan,
    )
    import argparse

    outroot = _materialize_valid_binding_outroot(tmp_path)
    approval = outroot / "preflight" / "BOUNDED_ADAPTER_24H_EXECUTE_APPROVAL_RECORD_V0.md"
    staging = tmp_path / "staging"
    for sub in ("plan", "runtime_out", "logs", "review"):
        (staging / sub).mkdir(parents=True)

    captured_env: dict[str, str | None] = {}

    def _runner(argv, cwd, stdout_path, stderr_path, *, extra_env=None):
        if "run_with_timeout.py" in " ".join(argv):
            captured_env["extra_env"] = dict(extra_env) if extra_env else None
        if stdout_path is not None:
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text("", encoding="utf-8")
        return 0

    def _sequenced_runner(
        argv,
        cwd,
        stdout_path,
        stderr_path,
        *,
        extra_env=None,
    ):
        argv_joined = " ".join(argv)
        if "run_with_timeout.py" in argv_joined:
            return _runner(argv, cwd, stdout_path, stderr_path, extra_env=extra_env)
        if "review_scheduler_paper_runtime_evidence.py" in argv_joined:
            if stdout_path is not None:
                stdout_path.parent.mkdir(parents=True, exist_ok=True)
                stdout_path.write_text('{"verdict":"PASS"}', encoding="utf-8")
            return 0
        return 0

    monkeypatch.setattr(
        "scripts.ops.run_paper_only_bounded_observation_adapter_v0._write_manifest_sha256",
        lambda _root: None,
    )
    monkeypatch.setattr(
        "scripts.ops.run_paper_only_bounded_observation_adapter_v0.verify_manifest_sha256",
        lambda _dest: (True, ""),
    )

    args = argparse.Namespace(
        profile="daemon_paper_shadow_24h_v0",
        approval_record=approval,
        duration_seconds=86400,
        poll_interval=30,
        execute=True,
        strict_repo_clean=False,
    )
    ctx = ExecuteContext(
        args=args,
        repo_root=REPO_ROOT,
        staging_root=staging,
        archive_root=tmp_path / "archive",
        runtime_out=staging / "runtime_out",
        logs_dir=staging / "logs",
        plan_dir=staging / "plan",
        review_dir=staging / "review",
        temp_jobs=staging / "plan" / "temp_jobs.toml",
        run_id=RUN_ID,
    )
    plan = build_plan(
        mode="execute",
        staging_root=staging,
        archive_root=tmp_path / "archive",
        repo_root=REPO_ROOT,
        source_jobs_toml=REPO_ROOT / "config/scheduler/jobs.toml",
        duration_seconds=86400,
        poll_interval_seconds=30,
        run_id=RUN_ID,
        contract_profile="daemon_paper_shadow_24h_v0",
    )

    rc = execute_plan(ctx, plan, subprocess_runner=_sequenced_runner)
    assert rc == 0
    extra = captured_env.get("extra_env") or {}
    assert extra.get(SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV) == str(outroot.resolve())
    assert extra.get(SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV) == RUN_ID
