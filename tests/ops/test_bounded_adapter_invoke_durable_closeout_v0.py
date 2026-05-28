"""Tests for bounded adapter optional durable closeout invocation (non-authorizing)."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PAPER_ADAPTER = REPO_ROOT / "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts/ops/run_shadow_bounded_observation_adapter_v0.py"
DURABLE_HELPER = REPO_ROOT / "scripts/ops/durable_closeout_copy_verify_v0.py"
FORBIDDEN_CHAIN_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"
PYTEST_DURABLE_DEST_ROOT = REPO_ROOT / "out" / "ops" / "_pytest_bounded_adapter_durable_closeout"


def _load_paper():
    spec = importlib.util.spec_from_file_location("paper_adapter_invoke_durable", PAPER_ADAPTER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_shadow():
    spec = importlib.util.spec_from_file_location("shadow_adapter_invoke_durable", SHADOW_ADAPTER)
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
def paper():
    return _load_paper()


@pytest.fixture(scope="module")
def shadow():
    return _load_shadow()


def test_default_off_validate_returns_no_issues(paper):
    args = argparse.Namespace(invoke_durable_closeout_v0=False, durable_closeout_dest_dir=None)
    assert paper.validate_durable_closeout_invoke_cli_args(args) == []


def test_missing_dest_when_flag_enabled(paper):
    args = argparse.Namespace(invoke_durable_closeout_v0=True, durable_closeout_dest_dir=None)
    issues = paper.validate_durable_closeout_invoke_cli_args(args)
    assert any("durable-closeout-dest-dir" in issue for issue in issues)


def test_tmp_dest_blocked_when_flag_enabled(paper):
    args = argparse.Namespace(
        invoke_durable_closeout_v0=True,
        durable_closeout_dest_dir=Path("/tmp/peak_trade_bounded_adapter_durable_dest_fixture"),
    )
    issues = paper.validate_durable_closeout_invoke_cli_args(args)
    assert any("outside /tmp" in issue for issue in issues)


def test_build_argv_uses_archive_source_and_durable_helper_only(paper, tmp_path):
    archive_source = tmp_path / "archive" / "runs" / "paper" / "run_id"
    archive_source.mkdir(parents=True)
    (archive_source / "CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    (archive_source / "evidence.txt").write_text("fixture\n", encoding="utf-8")
    durable_dest = _durable_dest(tmp_path)

    argv = paper.build_durable_closeout_invoke_argv(
        source_dir=archive_source,
        dest_dir=durable_dest,
    )
    assert argv[1].endswith("durable_closeout_copy_verify_v0.py")
    assert str(archive_source.resolve()) in argv
    assert str(durable_dest.resolve()) in argv
    joined = " ".join(argv)
    assert "build_generic_evidence_run_registry_v1.py" not in joined
    assert "build_post_closeout_projection_payload_v0.py" not in joined
    assert "post_closeout_sync_dry_run_v0.py" not in joined
    assert "run-local-post-closeout-chain-v0" not in joined


def test_invoke_fail_closed_on_nonzero_rc(paper, tmp_path):
    archive_source = tmp_path / "archive_run"
    archive_source.mkdir()
    (archive_source / "note.txt").write_text("x\n", encoding="utf-8")
    durable_dest = _durable_dest(tmp_path, "fail_closed")

    def _failing_invoker(_argv: list[str]) -> int:
        return 1

    rc = paper.invoke_durable_closeout_after_archive(
        source_dir=archive_source,
        dest_dir=durable_dest,
        durable_closeout_invoker=_failing_invoker,
    )
    assert rc == 1


def test_invoke_records_helper_call(paper, tmp_path):
    archive_source = tmp_path / "archive_run"
    archive_source.mkdir()
    (archive_source / "note.txt").write_text("x\n", encoding="utf-8")
    durable_dest = _durable_dest(tmp_path, "recorded")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    rc = paper.invoke_durable_closeout_after_archive(
        source_dir=archive_source,
        dest_dir=durable_dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert len(calls) == 1
    assert calls[0][1].endswith("durable_closeout_copy_verify_v0.py")


def test_maybe_invoke_without_flag_does_not_call_helper(paper, tmp_path, capsys):
    archive_source = tmp_path / "archive_run"
    archive_source.mkdir()
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    args = argparse.Namespace(
        invoke_durable_closeout_v0=False,
        durable_closeout_dest_dir=None,
    )
    ctx = paper.ExecuteContext(
        args=args,
        repo_root=REPO_ROOT,
        staging_root=tmp_path / "staging",
        archive_root=tmp_path / "archive",
        runtime_out=tmp_path / "staging" / "runtime_out",
        logs_dir=tmp_path / "staging" / "logs",
        plan_dir=tmp_path / "staging" / "plan",
        review_dir=tmp_path / "staging" / "review",
        temp_jobs=tmp_path / "staging" / "plan" / "temp_jobs.toml",
        run_id="paper_run",
    )
    rc = paper.maybe_invoke_durable_closeout_after_archive(
        ctx,
        archive_source,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert calls == []
    out = capsys.readouterr().out
    assert "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_INVOKED=false" in out


def test_maybe_invoke_with_flag_calls_helper(paper, tmp_path, capsys):
    archive_source = tmp_path / "archive_run"
    archive_source.mkdir()
    (archive_source / "note.txt").write_text("x\n", encoding="utf-8")
    durable_dest = _durable_dest(tmp_path, "invoked")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    args = argparse.Namespace(
        invoke_durable_closeout_v0=True,
        durable_closeout_dest_dir=durable_dest,
    )
    ctx = paper.ExecuteContext(
        args=args,
        repo_root=REPO_ROOT,
        staging_root=tmp_path / "staging",
        archive_root=tmp_path / "archive",
        runtime_out=tmp_path / "staging" / "runtime_out",
        logs_dir=tmp_path / "staging" / "logs",
        plan_dir=tmp_path / "staging" / "plan",
        review_dir=tmp_path / "staging" / "review",
        temp_jobs=tmp_path / "staging" / "plan" / "temp_jobs.toml",
        run_id="paper_run",
    )
    rc = paper.maybe_invoke_durable_closeout_after_archive(
        ctx,
        archive_source,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert len(calls) == 1
    out = capsys.readouterr().out
    assert "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_INVOKED=true" in out
    assert "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_STATUS=pass" in out


def test_paper_and_shadow_expose_cli_flags(paper, shadow):
    paper_flags = {
        a.option_strings[0] for a in paper.build_arg_parser()._actions if a.option_strings
    }
    shadow_flags = {
        a.option_strings[0] for a in shadow.build_arg_parser()._actions if a.option_strings
    }
    assert "--invoke-durable-closeout-v0" in paper_flags
    assert "--durable-closeout-dest-dir" in paper_flags
    assert "--invoke-durable-closeout-v0" in shadow_flags
    assert "--durable-closeout-dest-dir" in shadow_flags


def test_forbidden_parallel_execute_script_absent():
    assert not FORBIDDEN_CHAIN_SCRIPT.exists()
    assert DURABLE_HELPER.is_file()


def test_shadow_validate_delegates_same_rules(shadow):
    args = argparse.Namespace(invoke_durable_closeout_v0=True, durable_closeout_dest_dir=None)
    issues = shadow.validate_durable_closeout_invoke_cli_args(args)
    assert any("durable-closeout-dest-dir" in issue for issue in issues)
