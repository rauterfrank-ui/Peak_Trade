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


def _write_source_without_lifecycle_closeout_marker(tmp_path: Path) -> tuple[Path, Path]:
    """Paper bounded observation fixture: FINAL_MACHINE_LINES only (no lifecycle slice marker)."""
    archive = tmp_path / "archive"
    run_dir = pc.write_minimal_paper_run(archive, "paper_no_lifecycle_marker")
    payload_tests._write_machine_lines(run_dir / "FINAL_MACHINE_LINES.txt", CHAIN_MACHINE_LINES)
    src = tmp_path / "source"
    shutil.copytree(run_dir, src)
    return src, archive


def _durable_lifecycle_closeout_dest(tmp_path: Path, name: str) -> Path:
    return closeout_tests._archive_like_dest(tmp_path, name)


def _write_lifecycle_closeout_chain_dest(
    tmp_path: Path,
    *,
    name: str = "lifecycle_chain",
    verify_log_name: str = "MANIFEST_VERIFY.log",
    verify_rc: int = 0,
    marker_name: str = "HOST_TEARDOWN_EXECUTION_SLICE_V0_REPORT.md",
    nested_mirror: bool = False,
    with_final_stop_idle: bool = False,
) -> Path:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    dest = _durable_lifecycle_closeout_dest(tmp_path, name)
    dest.mkdir(parents=True, exist_ok=True)
    if with_final_stop_idle:
        marker_name = "BOUNDED_REMOTE_LIFECYCLE_FINAL_STOP_IDLE_RECORD.md"
    (dest / marker_name).write_text("# lifecycle closeout\n", encoding="utf-8")
    (dest / verify_log_name).write_text(f"MANIFEST_VERIFY_RC={verify_rc}\n", encoding="utf-8")
    if with_final_stop_idle:
        (dest / "BOUNDED_REMOTE_LIFECYCLE_FINAL_STOP_IDLE_MACHINE_LINES.txt").write_text(
            "NEXT_ACTION=STOP_IDLE_LIFECYCLE_COMPLETE_KEEP_IAM_FOR_REUSE\n",
            encoding="utf-8",
        )
    if nested_mirror:
        mirror = dest / "remote_archive_mirror"
        mirror.mkdir(parents=True, exist_ok=True)
        (mirror / "evidence.txt").write_text("nested evidence\n", encoding="utf-8")
        (mirror / "MANIFEST.sha256").write_text("# nested-local manifest\n", encoding="utf-8")
    payload_tests._write_machine_lines(dest / "FINAL_MACHINE_LINES.txt", CHAIN_MACHINE_LINES)
    write_manifest_sha256(dest)
    return dest


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


def test_lifecycle_closeout_hook_happy_path_runs_chain_steps(helper, tmp_path, monkeypatch):
    archive = tmp_path / "lifecycle_archive"
    pc.write_minimal_paper_run(archive, "lifecycle_chain_v0")
    dest = _write_lifecycle_closeout_chain_dest(
        tmp_path,
        nested_mirror=True,
        marker_name="SG_CLEANUP_EXECUTION_SLICE_V0_REPORT.md",
    )
    invoker, calls = _mock_invoker_factory(tmp_path)
    monkeypatch.setattr(helper, "_default_cli_invoker", invoker)
    try:
        chain = helper.run_local_post_closeout_chain_v0(
            dest_dir=dest,
            archive_root=archive,
            run_id="lifecycle_chain_v0",
            fixed_generated_at_utc=None,
        )
        assert chain.status == "pass"
        assert chain.steps[0].step == "validate_durable_lifecycle_closeout_root_v0"
        assert chain.steps[0].status == "ok"
        assert chain.steps[0].detail == "lifecycle_closeout_slice_v0"
        assert len(calls) == 3
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_lifecycle_closeout_hook_fail_closed_skips_registry_projection_notion(
    helper, tmp_path, monkeypatch
):
    archive = tmp_path / "lifecycle_archive_fail"
    pc.write_minimal_paper_run(archive, "lifecycle_chain_fail")
    dest = _write_lifecycle_closeout_chain_dest(
        tmp_path,
        name="lifecycle_chain_fail",
        verify_rc=1,
        marker_name="HOST_TEARDOWN_PLANNING_SLICE_V0_READONLY.md",
    )
    invoker, calls = _mock_invoker_factory(tmp_path)
    monkeypatch.setattr(helper, "_default_cli_invoker", invoker)
    try:
        chain = helper.run_local_post_closeout_chain_v0(
            dest_dir=dest,
            archive_root=archive,
            run_id=None,
            fixed_generated_at_utc=None,
        )
        assert chain.status == "invalid"
        assert chain.steps[0].step == "validate_durable_lifecycle_closeout_root_v0"
        assert chain.steps[0].status == "failed"
        assert "manifest verify RC must be 0" in chain.error
        assert calls == []
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_paper_chain_without_lifecycle_marker_skips_lifecycle_hook(helper, tmp_path, monkeypatch):
    src, archive = _write_source_without_lifecycle_closeout_marker(tmp_path)
    dest = closeout_tests._archive_like_dest(tmp_path, "paper_no_lifecycle_hook")
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
                "--no-require-closeout-report",
                "--force",
                "--run-local-post-closeout-chain-v0",
                "--chain-archive-root",
                str(archive),
                "--chain-run-id",
                "paper_no_lifecycle_marker",
            ]
        )
        assert rc == 0
        status = json.loads(
            (dest / helper.LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME).read_text(encoding="utf-8")
        )
        assert status["status"] == "pass"
        step_names = [step["step"] for step in status["steps"]]
        assert "validate_durable_lifecycle_closeout_root_v0" not in step_names
        assert len(calls) == 3
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)


def test_lifecycle_closeout_hook_via_main_after_durable_copy(helper, tmp_path, monkeypatch):
    archive = tmp_path / "lifecycle_main_archive"
    run_dir = archive / "lifecycle_main_v0"
    run_dir.mkdir(parents=True)
    (run_dir / "BOUNDED_RUNTIME_GRACEFUL_STOP_AND_DURABLE_CLOSEOUT_REPORT.md").write_text(
        "# lifecycle\n",
        encoding="utf-8",
    )
    payload_tests._write_machine_lines(run_dir / "FINAL_MACHINE_LINES.txt", CHAIN_MACHINE_LINES)
    src = tmp_path / "lifecycle_source"
    shutil.copytree(run_dir, src)
    dest = closeout_tests._archive_like_dest(tmp_path, "lifecycle_main_chain")
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
                "--no-require-closeout-report",
                "--force",
                "--run-local-post-closeout-chain-v0",
                "--chain-archive-root",
                str(archive),
            ]
        )
        assert rc == 0
        status = json.loads(
            (dest / helper.LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME).read_text(encoding="utf-8")
        )
        assert status["status"] == "pass"
        assert status["steps"][0]["step"] == "validate_durable_lifecycle_closeout_root_v0"
        assert status["steps"][0]["status"] == "ok"
        assert len(calls) == 3
    finally:
        closeout_tests._cleanup_archive_like_dest(dest)
