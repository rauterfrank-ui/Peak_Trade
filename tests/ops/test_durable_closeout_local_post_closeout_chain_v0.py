"""Tests for durable closeout local post-closeout chain mode (offline, non-authorizing)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc
from tests.ops import test_build_post_closeout_projection_payload_v0 as payload_tests
from tests.ops import test_durable_closeout_copy_verify_v0 as closeout_tests

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts/ops/durable_closeout_copy_verify_v0.py"
FORBIDDEN_PARALLEL_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"

CHAIN_MACHINE_LINES = dict(payload_tests.REQUIRED_MACHINE_LINES)


def _load_helper():
    spec = importlib.util.spec_from_file_location("durable_closeout_copy_verify_chain", HELPER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _minimal_registry_json(tmp_path: Path) -> str:
    archive = tmp_path / "registry_archive"
    pc.write_minimal_paper_run(archive, "paper_run")
    registry = pc.build_registry(archive)
    return json.dumps(registry, indent=2, sort_keys=True)


def _write_source_with_chain_inputs(tmp_path: Path) -> tuple[Path, Path]:
    archive = tmp_path / "archive"
    run_dir = pc.write_minimal_paper_run(archive, "paper_chain_v0")
    (run_dir / "AFTER_FIXTURE_CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    payload_tests._write_machine_lines(run_dir / "FINAL_MACHINE_LINES.txt", CHAIN_MACHINE_LINES)
    src = tmp_path / "source"
    shutil.copytree(run_dir, src)
    return src, archive


def _mock_invoker_factory(
    tmp_path: Path,
    *,
    registry_rc: int = 0,
    projection_rc: int = 0,
    dry_run_rc: int = 0,
    registry_json: str | None = None,
) -> tuple[callable, list[list[str]]]:
    calls: list[list[str]] = []
    registry_body = registry_json or _minimal_registry_json(tmp_path)

    def _invoker(argv: list[str], _cwd: Path) -> tuple[int, str]:
        calls.append(list(argv))
        script = Path(argv[1]).name
        if script == "build_generic_evidence_run_registry_v1.py":
            return registry_rc, registry_body if registry_rc == 0 else "registry failed"
        if script == "build_post_closeout_projection_payload_v0.py":
            out_idx = argv.index("--output-json") + 1
            Path(argv[out_idx]).write_text(
                json.dumps(
                    {
                        "schema_version": "peak_trade.post_closeout_projection_payload.v0",
                        "projection_ready": True,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            return projection_rc, "" if projection_rc == 0 else "projection failed"
        if script.endswith("post_closeout_sync_dry_run_v0.py"):
            out_idx = argv.index("--output-report-json") + 1
            Path(argv[out_idx]).write_text(
                json.dumps(
                    {
                        "schema_version": "peak_trade.notion_post_closeout_sync_dry_run_report.v0",
                        "dry_run": True,
                        "write_allowed": False,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            return dry_run_rc, "" if dry_run_rc == 0 else "dry-run failed"
        return 127, f"unexpected script: {script}"

    return _invoker, calls


@pytest.fixture(scope="module")
def helper():
    return _load_helper()


def test_default_behavior_without_chain_flag_unchanged(helper, tmp_path):
    src = closeout_tests._minimal_source(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, "no_chain")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *closeout_tests._tmp_source_args(),
                "--force",
            ]
        )
        assert rc == 0
        assert not (dest / helper.LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME).exists()
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_chain_flag_invokes_steps_in_order(helper, tmp_path, monkeypatch):
    src, archive = _write_source_with_chain_inputs(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, "chain_order")
    invoker, calls = _mock_invoker_factory(tmp_path)
    monkeypatch.setattr(helper, "_default_cli_invoker", invoker)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *closeout_tests._tmp_source_args(),
                "--force",
                "--run-local-post-closeout-chain-v0",
                "--chain-archive-root",
                str(archive),
                "--chain-run-id",
                "paper_chain_v0",
            ]
        )
        assert rc == 0
        assert len(calls) == 3
        assert calls[0][1].endswith("build_generic_evidence_run_registry_v1.py")
        assert calls[1][1].endswith("build_post_closeout_projection_payload_v0.py")
        assert calls[2][1].endswith("post_closeout_sync_dry_run_v0.py")
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_chain_writes_status_into_durable_target(helper, tmp_path, monkeypatch):
    src, archive = _write_source_with_chain_inputs(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, "chain_status")
    invoker, _calls = _mock_invoker_factory(tmp_path)
    monkeypatch.setattr(helper, "_default_cli_invoker", invoker)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *closeout_tests._tmp_source_args(),
                "--force",
                "--run-local-post-closeout-chain-v0",
                "--chain-archive-root",
                str(archive),
            ]
        )
        assert rc == 0
        status_path = dest / helper.LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME
        assert status_path.is_file()
        status = json.loads(status_path.read_text(encoding="utf-8"))
        assert status["status"] == "pass"
        assert status["safety"]["REMOTE_AWS_TOUCHED"] is False
        assert status["safety"]["DUPLICATE_SURFACE_CREATED"] is False
        assert (dest / helper.POST_CLOSEOUT_CHAIN_SUBDIR / helper.REGISTRY_CHAIN_ARTIFACT).is_file()
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


@pytest.mark.parametrize(
    ("registry_rc", "projection_rc", "dry_run_rc"),
    [
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
    ],
)
def test_chain_fail_closed_on_step_failure(
    helper, tmp_path, monkeypatch, registry_rc, projection_rc, dry_run_rc
):
    src, archive = _write_source_with_chain_inputs(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, f"chain_fail_{registry_rc}_{projection_rc}")
    invoker, _calls = _mock_invoker_factory(
        tmp_path,
        registry_rc=registry_rc,
        projection_rc=projection_rc,
        dry_run_rc=dry_run_rc,
    )
    monkeypatch.setattr(helper, "_default_cli_invoker", invoker)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *closeout_tests._tmp_source_args(),
                "--force",
                "--run-local-post-closeout-chain-v0",
                "--chain-archive-root",
                str(archive),
            ]
        )
        assert rc == 1
        status = json.loads(
            (dest / helper.LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME).read_text(encoding="utf-8")
        )
        assert status["status"] in {"invalid", "blocked"}
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_chain_blocked_without_archive_root(helper, tmp_path):
    src = closeout_tests._minimal_source(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, "chain_blocked")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *closeout_tests._tmp_source_args(),
                "--force",
                "--run-local-post-closeout-chain-v0",
            ]
        )
        assert rc == 2
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_forbidden_parallel_execute_script_absent():
    assert not FORBIDDEN_PARALLEL_SCRIPT.exists()
