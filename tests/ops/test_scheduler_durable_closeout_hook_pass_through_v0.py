"""Tests for scheduler durable closeout hook pass-through (non-authorizing)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_SCHEDULER = REPO_ROOT / "scripts" / "run_scheduler.py"
DURABLE_HELPER = REPO_ROOT / "scripts" / "ops" / "durable_closeout_copy_verify_v0.py"
FORBIDDEN_CHAIN_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"
PYTEST_DURABLE_DEST_ROOT = REPO_ROOT / "out" / "ops" / "_pytest_scheduler_durable_closeout_hook"


def _load_run_scheduler():
    spec = importlib.util.spec_from_file_location("run_scheduler_hook", RUN_SCHEDULER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _durable_dest(tmp_path: Path, name: str = "dest") -> Path:
    safe = tmp_path.name.replace("/", "_")
    dest = PYTEST_DURABLE_DEST_ROOT / safe / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


@pytest.fixture(scope="module")
def rs():
    return _load_run_scheduler()


def test_forbidden_parallel_execute_script_absent():
    assert not FORBIDDEN_CHAIN_SCRIPT.exists()
    assert DURABLE_HELPER.is_file()


def test_cli_flags_present_in_source():
    text = RUN_SCHEDULER.read_text(encoding="utf-8")
    assert "--invoke-durable-closeout-after-completion-v0" in text
    assert "--durable-closeout-dest-dir" in text
    assert "SCHEDULER_DURABLE_CLOSEOUT_REQUESTED=" in text


def test_hook_validate_requires_dest_dir(rs):
    assert (
        rs.validate_scheduler_durable_closeout_hook_cli(
            invoke_durable_closeout_after_completion_v0=True,
            durable_closeout_dest_dir=None,
            evidence_dir=Path("/var/tmp/evidence"),
        )
        == 1
    )


def test_hook_validate_requires_evidence_dir(rs, tmp_path):
    dest = _durable_dest(tmp_path)
    assert (
        rs.validate_scheduler_durable_closeout_hook_cli(
            invoke_durable_closeout_after_completion_v0=True,
            durable_closeout_dest_dir=dest,
            evidence_dir=None,
        )
        == 1
    )


def test_hook_validate_blocks_tmp_dest(rs, tmp_path):
    assert (
        rs.validate_scheduler_durable_closeout_hook_cli(
            invoke_durable_closeout_after_completion_v0=True,
            durable_closeout_dest_dir=Path("/tmp/scheduler_durable_dest"),
            evidence_dir=tmp_path,
        )
        == 1
    )


def test_main_hook_without_dest_fails_before_loop(rs, monkeypatch):
    loop_calls: list[object] = []
    monkeypatch.setattr(rs, "run_scheduler_loop", lambda **kwargs: loop_calls.append(kwargs) or 0)

    rc = rs.main(
        [
            "--once",
            "--config",
            "config/scheduler/jobs.toml",
            "--evidence-dir",
            str(_durable_dest(Path("no_loop"))),
            "--invoke-durable-closeout-after-completion-v0",
        ]
    )
    assert rc == 1
    assert loop_calls == []


def test_invoke_calls_only_durable_helper(rs, tmp_path):
    source = tmp_path / "evidence"
    source.mkdir()
    (source / "scheduler_completion_closeout_v0.json").write_text("{}\n", encoding="utf-8")
    dest = _durable_dest(tmp_path, "helper_only")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    rc = rs.invoke_scheduler_durable_closeout_after_completion(
        source_dir=source,
        dest_dir=dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert len(calls) == 1
    joined = " ".join(calls[0])
    assert calls[0][1].endswith("durable_closeout_copy_verify_v0.py")
    assert str(source.resolve()) in joined
    assert str(dest.resolve()) in joined
    assert "build_generic_evidence_run_registry_v1.py" not in joined
    assert "build_post_closeout_projection_payload_v0.py" not in joined
    assert "post_closeout_sync_dry_run_v0.py" not in joined


def test_finalize_invokes_hook_after_primary_evidence_success(
    rs, monkeypatch, tmp_path: Path
) -> None:
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.finalize_primary_evidence_root",
        lambda _root: (True, ""),
    )
    dest = _durable_dest(tmp_path, "after_finalize")

    rc = rs.finalize_scheduler_completion_evidence(
        tmp_path,
        primary_evidence_enforce=True,
        dry_run=False,
        once=True,
        config_path=Path("config/scheduler/jobs.toml"),
        iterations=1,
        jobs_dispatched=0,
        exit_status=0,
        invoke_durable_closeout_after_completion_v0=True,
        durable_closeout_dest_dir=dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert len(calls) == 1
    assert (tmp_path / "scheduler_completion_closeout_v0.json").is_file()


def test_finalize_hook_fail_closed_on_helper_nonzero(rs, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.finalize_primary_evidence_root",
        lambda _root: (True, ""),
    )
    dest = _durable_dest(tmp_path, "fail_closed")

    def _failing_invoker(_argv: list[str]) -> int:
        return 2

    rc = rs.finalize_scheduler_completion_evidence(
        tmp_path,
        primary_evidence_enforce=True,
        dry_run=False,
        once=True,
        config_path=Path("config/scheduler/jobs.toml"),
        iterations=1,
        jobs_dispatched=0,
        exit_status=0,
        invoke_durable_closeout_after_completion_v0=True,
        durable_closeout_dest_dir=dest,
        durable_closeout_invoker=_failing_invoker,
    )
    assert rc == 2


def test_finalize_skips_hook_when_primary_evidence_finalize_fails(
    rs, monkeypatch, tmp_path: Path
) -> None:
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.finalize_primary_evidence_root",
        lambda _root: (False, "checksum mismatch"),
    )
    dest = _durable_dest(tmp_path, "no_hook")

    rc = rs.finalize_scheduler_completion_evidence(
        tmp_path,
        primary_evidence_enforce=True,
        dry_run=False,
        once=True,
        config_path=Path("config/scheduler/jobs.toml"),
        iterations=1,
        jobs_dispatched=0,
        exit_status=0,
        invoke_durable_closeout_after_completion_v0=True,
        durable_closeout_dest_dir=dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 1
    assert calls == []


def test_finalize_default_off_no_hook(rs, monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.finalize_primary_evidence_root",
        lambda _root: (True, ""),
    )

    rc = rs.finalize_scheduler_completion_evidence(
        tmp_path,
        primary_evidence_enforce=True,
        dry_run=False,
        once=True,
        config_path=Path("config/scheduler/jobs.toml"),
        iterations=1,
        jobs_dispatched=0,
        exit_status=0,
        invoke_durable_closeout_after_completion_v0=False,
        durable_closeout_dest_dir=None,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert calls == []


def test_maybe_invoke_emits_machine_lines(rs, tmp_path, capsys):
    source = tmp_path / "evidence"
    source.mkdir()
    dest = _durable_dest(tmp_path, "lines")

    rc = rs.maybe_invoke_scheduler_durable_closeout_after_completion(
        evidence_dir=source,
        invoke_durable_closeout_after_completion_v0=False,
        durable_closeout_dest_dir=dest,
        completion_evidence_finalized=True,
        durable_closeout_invoker=lambda _argv: 0,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "SCHEDULER_DURABLE_CLOSEOUT_REQUESTED=false" in out
    assert "SCHEDULER_DURABLE_CLOSEOUT_INVOKED=false" in out
