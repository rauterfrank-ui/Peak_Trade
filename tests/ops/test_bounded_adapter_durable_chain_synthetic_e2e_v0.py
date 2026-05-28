"""Synthetic E2E: bounded adapter durable helper argv -> local post-closeout chain (tests-only).

Proves Adapter -> durable_closeout_copy_verify_v0.py wiring is coherent without starting
runtime, scheduler, AWS, or direct Registry/Projection/Notion invocation from adapters.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.ops import test_bounded_adapter_invoke_durable_closeout_v0 as adapter_tests
from tests.ops import test_durable_closeout_copy_verify_v0 as closeout_tests
from tests.ops import test_durable_closeout_local_post_closeout_chain_v0 as chain_tests

REPO_ROOT = Path(__file__).resolve().parents[2]
PAPER_ADAPTER = REPO_ROOT / "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts/ops/run_shadow_bounded_observation_adapter_v0.py"
DURABLE_HELPER = REPO_ROOT / "scripts/ops/durable_closeout_copy_verify_v0.py"
REGISTRY_SCRIPT = REPO_ROOT / "scripts/ops/build_generic_evidence_run_registry_v1.py"
PROJECTION_SCRIPT = REPO_ROOT / "scripts/ops/build_post_closeout_projection_payload_v0.py"
NOTION_DRY_RUN_SCRIPT = "notion_post_closeout_sync_dry_run_v0.py"
FORBIDDEN_CHAIN_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"

FORBIDDEN_DIRECT_SCRIPTS = (
    REGISTRY_SCRIPT.name,
    PROJECTION_SCRIPT.name,
    NOTION_DRY_RUN_SCRIPT,
)


def _load_paper():
    return adapter_tests._load_paper()


def _load_shadow():
    return adapter_tests._load_shadow()


def _load_helper():
    return chain_tests._load_helper()


def _assert_argv_targets_helper_only(argv: list[str]) -> None:
    assert argv[1].endswith("durable_closeout_copy_verify_v0.py")
    joined = " ".join(argv)
    for forbidden in FORBIDDEN_DIRECT_SCRIPTS:
        assert forbidden not in joined


def _helper_main_from_invoke_argv(helper, argv: list[str]) -> int:
    """Run durable helper with adapter-built argv (skip python executable + script path)."""
    return int(helper.main(argv[2:]))


@pytest.fixture(scope="module")
def paper():
    return _load_paper()


@pytest.fixture(scope="module")
def shadow():
    return _load_shadow()


@pytest.fixture(scope="module")
def helper():
    return _load_helper()


def test_forbidden_parallel_execute_script_absent():
    assert not FORBIDDEN_CHAIN_SCRIPT.exists()
    assert DURABLE_HELPER.is_file()


def test_adapter_full_chain_and_pointer_argv_includes_required_flags(paper, tmp_path):
    archive_source = tmp_path / "archive" / "runs" / "paper" / "run_id"
    archive_source.mkdir(parents=True)
    durable_dest = adapter_tests._durable_dest(tmp_path, "argv_chain_pointer")
    chain_archive = adapter_tests._chain_archive_root(tmp_path)

    argv = paper.build_durable_closeout_invoke_argv(
        source_dir=archive_source,
        dest_dir=durable_dest,
        run_local_post_closeout_chain_v0=True,
        chain_archive_root=chain_archive,
        chain_run_id="paper_chain_e2e",
        require_durable_pointer_evidence=True,
        durable_pointer_patterns=("ARCHIVE_POINTER.md",),
    )
    joined = " ".join(argv)
    _assert_argv_targets_helper_only(argv)
    assert "--run-local-post-closeout-chain-v0" in joined
    assert "--require-durable-pointer-evidence" in joined
    assert "--durable-pointer-pattern" in joined


def test_adapter_full_chain_argv_includes_required_flags(paper, tmp_path):
    archive_source = tmp_path / "archive" / "runs" / "paper" / "run_id"
    archive_source.mkdir(parents=True)
    (archive_source / "CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    durable_dest = adapter_tests._durable_dest(tmp_path, "argv_full")
    chain_archive = adapter_tests._chain_archive_root(tmp_path)

    argv = paper.build_durable_closeout_invoke_argv(
        source_dir=archive_source,
        dest_dir=durable_dest,
        run_local_post_closeout_chain_v0=True,
        chain_archive_root=chain_archive,
        chain_run_id="paper_chain_e2e",
    )
    joined = " ".join(argv)
    _assert_argv_targets_helper_only(argv)
    assert "--run-local-post-closeout-chain-v0" in joined
    assert "--chain-archive-root" in joined
    assert str(chain_archive.resolve()) in joined
    assert "--chain-run-id" in joined
    assert "paper_chain_e2e" in joined


def test_adapter_maybe_invoke_records_only_helper_subprocess(paper, tmp_path):
    archive_source = tmp_path / "archive_run"
    archive_source.mkdir()
    (archive_source / "note.txt").write_text("fixture\n", encoding="utf-8")
    durable_dest = adapter_tests._durable_dest(tmp_path, "recorded_e2e")
    chain_archive = adapter_tests._chain_archive_root(tmp_path)
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        _assert_argv_targets_helper_only(argv)
        return 0

    args = adapter_tests._durable_args(
        invoke_durable_closeout_v0=True,
        durable_closeout_dest_dir=durable_dest,
        run_local_post_closeout_chain_v0=True,
        chain_archive_root=chain_archive,
        chain_run_id="explicit_chain_run",
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
        run_id="adapter_default_run_id",
    )
    rc = paper.maybe_invoke_durable_closeout_after_archive(
        ctx,
        archive_source,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert len(calls) == 1
    joined = " ".join(calls[0])
    assert "--run-local-post-closeout-chain-v0" in joined
    assert "explicit_chain_run" in joined


def test_shadow_reuses_paper_durable_closeout_helpers(shadow, paper, tmp_path):
    import scripts.ops.run_paper_only_bounded_observation_adapter_v0 as paper_mod
    import scripts.ops.run_shadow_bounded_observation_adapter_v0 as shadow_mod

    assert shadow_mod.validate_durable_closeout_invoke_cli_args is (
        paper_mod.validate_durable_closeout_invoke_cli_args
    )
    assert shadow_mod.maybe_invoke_durable_closeout_after_archive is (
        paper_mod.maybe_invoke_durable_closeout_after_archive
    )
    assert shadow_mod.add_bounded_adapter_durable_closeout_cli_args is (
        paper_mod.add_bounded_adapter_durable_closeout_cli_args
    )
    args = adapter_tests._durable_args(
        run_local_post_closeout_chain_v0=True,
        chain_archive_root=adapter_tests._chain_archive_root(tmp_path),
    )
    assert shadow.validate_durable_closeout_invoke_cli_args(args) == (
        paper.validate_durable_closeout_invoke_cli_args(args)
    )
    shadow_flags = {a.dest for a in shadow.build_arg_parser()._actions if a.dest}
    for dest in (
        "invoke_durable_closeout_v0",
        "durable_closeout_dest_dir",
        "run_local_post_closeout_chain_v0",
        "chain_archive_root",
        "chain_run_id",
    ):
        assert dest in shadow_flags


def test_synthetic_e2e_adapter_argv_drives_helper_local_chain(paper, helper, tmp_path, monkeypatch):
    """Adapter-built argv runs real helper; chain steps mocked (offline, non-authorizing)."""
    src, archive = chain_tests._write_source_with_chain_inputs(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, "adapter_e2e_chain")
    chain_run_id = "paper_chain_v0"

    argv = paper.build_durable_closeout_invoke_argv(
        source_dir=src,
        dest_dir=dest,
        run_local_post_closeout_chain_v0=True,
        chain_archive_root=archive,
        chain_run_id=chain_run_id,
    )
    _assert_argv_targets_helper_only(argv)

    invoker, chain_calls = chain_tests._mock_invoker_factory(tmp_path)
    monkeypatch.setattr(helper, "_default_cli_invoker", invoker)
    try:
        rc = _helper_main_from_invoke_argv(helper, argv)
        assert rc == 0
        assert len(chain_calls) == 3
        assert chain_calls[0][1].endswith(REGISTRY_SCRIPT.name)
        assert chain_calls[1][1].endswith(PROJECTION_SCRIPT.name)
        assert chain_calls[2][1].endswith(NOTION_DRY_RUN_SCRIPT)
        status_path = dest / helper.LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME
        assert status_path.is_file()
        status = json.loads(status_path.read_text(encoding="utf-8"))
        assert status["status"] == "pass"
        assert status["safety"]["REMOTE_AWS_TOUCHED"] is False
        assert status["safety"]["RUNTIME_STARTED"] is False
        assert status["safety"]["SCHEDULER_STARTED"] is False
        assert status["safety"]["PAPER_SHADOW_TESTNET_LIVE_STARTED"] is False
        assert status["safety"]["LIVE_AUTHORITY_CHANGED"] is False
        assert status["safety"]["DUPLICATE_SURFACE_CREATED"] is False
        chain_dir = dest / helper.POST_CLOSEOUT_CHAIN_SUBDIR
        assert (chain_dir / helper.REGISTRY_CHAIN_ARTIFACT).is_file()
        assert (chain_dir / helper.PROJECTION_CHAIN_ARTIFACT).is_file()
        assert (chain_dir / helper.POST_CLOSEOUT_SYNC_DRY_RUN_ARTIFACT).is_file()
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_synthetic_e2e_maybe_invoke_wires_adapter_to_helper_chain(
    paper, helper, tmp_path, monkeypatch
):
    src, archive = chain_tests._write_source_with_chain_inputs(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, "maybe_invoke_e2e")
    invoker, chain_calls = chain_tests._mock_invoker_factory(tmp_path)
    monkeypatch.setattr(helper, "_default_cli_invoker", invoker)

    args = adapter_tests._durable_args(
        invoke_durable_closeout_v0=True,
        durable_closeout_dest_dir=dest,
        run_local_post_closeout_chain_v0=True,
        chain_archive_root=archive,
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
        run_id="paper_chain_v0",
    )

    def _helper_subprocess_invoker(argv: list[str]) -> int:
        _assert_argv_targets_helper_only(argv)
        return _helper_main_from_invoke_argv(helper, argv)

    try:
        rc = paper.maybe_invoke_durable_closeout_after_archive(
            ctx,
            src,
            durable_closeout_invoker=_helper_subprocess_invoker,
        )
        assert rc == 0
        assert len(chain_calls) == 3
        assert (dest / helper.LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME).is_file()
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_chain_run_id_defaults_through_maybe_invoke(paper, tmp_path):
    archive_source = tmp_path / "archive_run"
    archive_source.mkdir()
    durable_dest = adapter_tests._durable_dest(tmp_path, "default_run_id")
    chain_archive = adapter_tests._chain_archive_root(tmp_path)
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    args = adapter_tests._durable_args(
        invoke_durable_closeout_v0=True,
        durable_closeout_dest_dir=durable_dest,
        run_local_post_closeout_chain_v0=True,
        chain_archive_root=chain_archive,
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
        run_id="paper_chain_v0",
    )
    paper.maybe_invoke_durable_closeout_after_archive(
        ctx,
        archive_source,
        durable_closeout_invoker=_recording_invoker,
    )
    assert len(calls) == 1
    assert "paper_chain_v0" in " ".join(calls[0])
