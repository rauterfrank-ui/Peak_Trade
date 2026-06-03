"""Unit and static tests for durable_closeout_copy_verify_v0 (OP-CLOSEOUT-HELPER-IMPL-V0)."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
HELPER = REPO_ROOT / "scripts/ops/durable_closeout_copy_verify_v0.py"
FIXTURE_SOURCE = REPO_ROOT / "tests/fixtures/ops/durable_closeout_copy_verify_source_v0"
POST_MERGE_CLOSEOUT = REPO_ROOT / "scripts/governance/post_merge_closeout.sh"
APPEND_CLOSEOUT_INDEX = REPO_ROOT / "scripts/ops/append_closeout_index.py"
PYTEST_ARCHIVE_ROOT = REPO_ROOT / "out" / "ops" / "_pytest_durable_closeout_copy_verify"

FORBIDDEN_HELPER_SUBSTRINGS = (
    "aws ",
    "rclone",
    "ssh ",
    "scp ",
    "systemctl",
    "docker",
    "podman",
    "curl ",
    "wget ",
    "boto3",
    "requests",
    "paramiko",
    "subprocess.run",
    "os.system",
    "Popen",
)

FORBIDDEN_IMPORT_MARKERS = (
    "preflight_remote_runtime_runner",
    "remote_paper_validator",
    "market_dashboard",
    "notion",
    "scheduler",
)


def _load_helper():
    spec = importlib.util.spec_from_file_location("durable_closeout_copy_verify_v0", HELPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _archive_like_dest(tmp_path: Path, name: str = "dest") -> Path:
    """Durable dest outside /tmp (CI tmp_path lives under /tmp)."""
    safe_test_id = tmp_path.name.replace("/", "_")
    dest = (
        PYTEST_ARCHIVE_ROOT
        / safe_test_id
        / "Peak_Trade_runtime_evidence_archive_fixture"
        / "closeout"
        / name
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def _cleanup_archive_like_dest(path: Path) -> None:
    shutil.rmtree(path.parents[2], ignore_errors=True)


def _minimal_source(
    tmp_path: Path,
    *,
    with_closeout: bool = True,
    closeout_json_name: str | None = None,
    closeout_json_content: str = '{"status":"ok"}\n',
    with_pr: bool = False,
    with_pointer: bool = False,
) -> Path:
    src = tmp_path / "source"
    src.mkdir()
    (src / "note.txt").write_text("fixture\n", encoding="utf-8")
    if with_closeout:
        (src / "AFTER_FIXTURE_CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    if closeout_json_name:
        (src / closeout_json_name).write_text(closeout_json_content, encoding="utf-8")
    if with_pr:
        (src / "PR42.json").write_text('{"number": 42}\n', encoding="utf-8")
    if with_pointer:
        (src / "PR_URL.txt").write_text("https://example.invalid/pr/42\n", encoding="utf-8")
    return src


def _tmp_source_args() -> list[str]:
    return ["--allow-tmp-source"]


@pytest.fixture(scope="module")
def helper():
    return _load_helper()


def test_dry_run_writes_nothing(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
                "--dry-run",
            ]
        )
        assert rc == 0
        assert not (dest / "DURABLE_COPY_README.md").exists()
        assert not (dest / "MANIFEST.sha256").exists()
    finally:
        _cleanup_archive_like_dest(dest)


def test_missing_source_fails(helper, tmp_path):
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(["--source-dir", str(tmp_path / "missing"), "--dest-dir", str(dest)])
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_non_directory_source_fails(helper, tmp_path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("x", encoding="utf-8")
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src_file),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_empty_source_fails(helper, tmp_path):
    src = tmp_path / "empty"
    src.mkdir()
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_source_under_tmp_without_allow_fails(helper, tmp_path):
    src = _minimal_source(tmp_path)
    tmp_src = Path("/tmp") / f"peak_trade_test_src_{tmp_path.name}"
    if tmp_src.exists():
        shutil.rmtree(tmp_src)
    shutil.copytree(src, tmp_src)
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(["--source-dir", str(tmp_src), "--dest-dir", str(dest)])
        assert rc == 1
    finally:
        if tmp_src.exists():
            shutil.rmtree(tmp_src)
        _cleanup_archive_like_dest(dest)


def test_dest_under_tmp_fails(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = Path("/tmp") / f"peak_trade_test_dest_{tmp_path.name}"
    dest.mkdir(parents=True, exist_ok=True)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 1
    finally:
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)


def test_missing_closeout_report_fails_by_default(helper, tmp_path):
    src = _minimal_source(tmp_path, with_closeout=False)
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_valid_scheduler_json_closeout_is_accepted(helper, tmp_path):
    src = _minimal_source(
        tmp_path,
        with_closeout=False,
        closeout_json_name="scheduler_completion_closeout_v0.json",
    )
    dest = _archive_like_dest(tmp_path, "scheduler_json_closeout")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 0
    finally:
        _cleanup_archive_like_dest(dest)


def test_malformed_scheduler_json_closeout_is_rejected(helper, tmp_path):
    src = _minimal_source(
        tmp_path,
        with_closeout=False,
        closeout_json_name="scheduler_completion_closeout_v0.json",
        closeout_json_content="{not-json\n",
    )
    dest = _archive_like_dest(tmp_path, "scheduler_json_closeout_malformed")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_no_require_closeout_report_permits_valid_source(helper, tmp_path):
    src = _minimal_source(tmp_path, with_closeout=False)
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
                "--no-require-closeout-report",
                "--dry-run",
            ]
        )
        assert rc == 0
    finally:
        _cleanup_archive_like_dest(dest)


def test_pr_number_requires_pr_json(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
                "--pr-number",
                "99",
                "--dry-run",
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_pr_json_supplied_passes_dry_run(helper, tmp_path):
    src = _minimal_source(tmp_path)
    pr_file = tmp_path / "pr.json"
    pr_file.write_text('{"number": 1}\n', encoding="utf-8")
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
                "--pr-number",
                "1",
                "--pr-json",
                str(pr_file),
                "--dry-run",
            ]
        )
        assert rc == 0
    finally:
        _cleanup_archive_like_dest(dest)


def test_non_dry_copy_creates_readme_and_manifest(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 0
        assert (dest / "DURABLE_COPY_README.md").is_file()
        assert (dest / "MANIFEST.sha256").is_file()
        assert (dest / "MANIFEST_VERIFY.log").is_file()
    finally:
        _cleanup_archive_like_dest(dest)


def test_non_dry_copy_verifies_manifest(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path, "verify_dest")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 0
        from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

        ok, _ = verify_manifest_sha256(dest)
        assert ok
    finally:
        _cleanup_archive_like_dest(dest)


def test_duplicate_dest_without_force_fails(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path, "dup")
    try:
        args = ["--source-dir", str(src), "--dest-dir", str(dest), *_tmp_source_args()]
        assert helper.main(args) == 0
        rc = helper.main(args)
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_duplicate_dest_with_force_succeeds(helper, tmp_path, capsys):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path, "force_dest")
    try:
        base_args = ["--source-dir", str(src), "--dest-dir", str(dest), *_tmp_source_args()]
        assert helper.main(base_args) == 0
        (src / "note.txt").write_text("updated\n", encoding="utf-8")
        rc = helper.main([*base_args, "--force"])
        assert rc == 0
        assert "FORCE_OVERWRITE=true" in capsys.readouterr().err
    finally:
        _cleanup_archive_like_dest(dest)


def test_pointer_enforcement_enabled_blocks_without_pointer(helper, tmp_path):
    src = _minimal_source(tmp_path, with_pointer=False)
    dest = _archive_like_dest(tmp_path, "pointer_missing")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
                "--require-durable-pointer-evidence",
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_pointer_enforcement_enabled_passes_with_pointer(helper, tmp_path):
    src = _minimal_source(tmp_path, with_pointer=True)
    dest = _archive_like_dest(tmp_path, "pointer_present")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
                "--require-durable-pointer-evidence",
            ]
        )
        assert rc == 0
    finally:
        _cleanup_archive_like_dest(dest)


def test_pointer_enforcement_disabled_is_backward_compatible(helper, tmp_path):
    src = _minimal_source(tmp_path, with_pointer=False)
    dest = _archive_like_dest(tmp_path, "pointer_optional")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 0
    finally:
        _cleanup_archive_like_dest(dest)


def test_missing_manifest_verify_log_blocks(helper, tmp_path, monkeypatch):
    src = _minimal_source(tmp_path, with_pointer=True)
    dest = _archive_like_dest(tmp_path, "missing_manifest_log")
    try:
        monkeypatch.setattr(helper, "_manifest_verify_log_is_success", lambda _dest: False)
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
                "--require-durable-pointer-evidence",
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_manifest_must_cover_recognized_closeout_artifact(helper, tmp_path, monkeypatch):
    src = _minimal_source(
        tmp_path,
        with_closeout=False,
        closeout_json_name="scheduler_completion_closeout_v0.json",
    )
    dest = _archive_like_dest(tmp_path, "manifest_missing_closeout_artifact")
    try:
        original_write_manifest = helper.write_manifest_sha256

        def _write_manifest_without_closeout(dest_dir: Path) -> None:
            original_write_manifest(dest_dir)
            manifest = dest_dir / "MANIFEST.sha256"
            filtered = [
                line
                for line in manifest.read_text(encoding="utf-8").splitlines()
                if "scheduler_completion_closeout_v0.json" not in line
            ]
            manifest.write_text("\n".join(filtered) + "\n", encoding="utf-8")

        monkeypatch.setattr(helper, "write_manifest_sha256", _write_manifest_without_closeout)
        rc = helper.main(
            [
                "--source-dir",
                str(src),
                "--dest-dir",
                str(dest),
                *_tmp_source_args(),
            ]
        )
        assert rc == 1
    finally:
        _cleanup_archive_like_dest(dest)


def test_fixture_source_usable(helper, tmp_path):
    dest = _archive_like_dest(tmp_path, "from_repo_fixture")
    try:
        rc = helper.main(
            [
                "--source-dir",
                str(FIXTURE_SOURCE),
                "--dest-dir",
                str(dest),
                "--dry-run",
            ]
        )
        assert rc == 0
    finally:
        _cleanup_archive_like_dest(dest)


def _helper_logic_source_text() -> str:
    text = HELPER.read_text(encoding="utf-8")
    start = text.find("def emit_machine_lines")
    end = text.find("def build_arg_parser")
    if start != -1 and end != -1 and end > start:
        return text[:start] + text[end:]
    return text


def test_helper_source_forbidden_substrings_absent():
    lower = _helper_logic_source_text().lower()
    for token in FORBIDDEN_HELPER_SUBSTRINGS:
        assert token.lower() not in lower, f"forbidden token: {token!r}"


def test_helper_no_forbidden_imports():
    text = HELPER.read_text(encoding="utf-8")
    for marker in FORBIDDEN_IMPORT_MARKERS:
        assert marker not in text


def test_governance_scripts_unchanged():
    assert POST_MERGE_CLOSEOUT.is_file()
    assert APPEND_CLOSEOUT_INDEX.is_file()


def test_pe4_preflight_references_durable_closeout_helper_for_mandatory_wiring_v0() -> None:
    section = PREFLIGHT.read_text(encoding="utf-8").split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    assert "PE4_BOUNDED_OBSERVATION_MANDATORY_CLOSEOUT_WIRING_GUARD_V0=true" in section
    assert "durable_closeout_copy_verify_v0.py" in section
    assert "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_NON_AUTHORIZING=true" in PREFLIGHT.read_text(
        encoding="utf-8"
    )
    assert HELPER.is_file()
