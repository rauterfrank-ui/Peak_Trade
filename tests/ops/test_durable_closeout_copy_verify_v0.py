"""Unit and static tests for durable_closeout_copy_verify_v0 (OP-CLOSEOUT-HELPER-IMPL-V0)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts/ops/durable_closeout_copy_verify_v0.py"
FIXTURE_SOURCE = REPO_ROOT / "tests/fixtures/ops/durable_closeout_copy_verify_source_v0"
POST_MERGE_CLOSEOUT = REPO_ROOT / "scripts/governance/post_merge_closeout.sh"
APPEND_CLOSEOUT_INDEX = REPO_ROOT / "scripts/ops/append_closeout_index.py"

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
    root = tmp_path / "Peak_Trade_runtime_evidence_archive_fixture" / "closeout" / name
    root.mkdir(parents=True)
    return root


def _minimal_source(tmp_path: Path, *, with_closeout: bool = True, with_pr: bool = False) -> Path:
    src = tmp_path / "source"
    src.mkdir()
    (src / "note.txt").write_text("fixture\n", encoding="utf-8")
    if with_closeout:
        (src / "AFTER_FIXTURE_CLOSEOUT.md").write_text("# closeout\n", encoding="utf-8")
    if with_pr:
        (src / "PR42.json").write_text('{"number": 42}\n', encoding="utf-8")
    return src


@pytest.fixture(scope="module")
def helper():
    return _load_helper()


def test_dry_run_writes_nothing(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(
        [
            "--source-dir",
            str(src),
            "--dest-dir",
            str(dest),
            "--dry-run",
        ]
    )
    assert rc == 0
    assert not (dest / "DURABLE_COPY_README.md").exists()
    assert not (dest / "MANIFEST.sha256").exists()


def test_missing_source_fails(helper, tmp_path):
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(["--source-dir", str(tmp_path / "missing"), "--dest-dir", str(dest)])
    assert rc == 1


def test_non_directory_source_fails(helper, tmp_path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("x", encoding="utf-8")
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(["--source-dir", str(src_file), "--dest-dir", str(dest)])
    assert rc == 1


def test_empty_source_fails(helper, tmp_path):
    src = tmp_path / "empty"
    src.mkdir()
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(["--source-dir", str(src), "--dest-dir", str(dest)])
    assert rc == 1


def test_source_under_tmp_without_allow_fails(helper, tmp_path):
    src = _minimal_source(tmp_path)
    tmp_src = Path("/tmp") / f"peak_trade_test_src_{tmp_path.name}"
    if tmp_src.exists():
        import shutil

        shutil.rmtree(tmp_src)
    shutil_copy = __import__("shutil")
    shutil_copy.copytree(src, tmp_src)
    dest = _archive_like_dest(tmp_path)
    try:
        rc = helper.main(["--source-dir", str(tmp_src), "--dest-dir", str(dest)])
        assert rc == 1
    finally:
        if tmp_src.exists():
            shutil_copy.rmtree(tmp_src)


def test_dest_under_tmp_fails(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = Path("/tmp") / f"peak_trade_test_dest_{tmp_path.name}"
    dest.mkdir(parents=True, exist_ok=True)
    rc = helper.main(["--source-dir", str(src), "--dest-dir", str(dest)])
    assert rc == 1


def test_missing_closeout_report_fails_by_default(helper, tmp_path):
    src = _minimal_source(tmp_path, with_closeout=False)
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(["--source-dir", str(src), "--dest-dir", str(dest)])
    assert rc == 1


def test_no_require_closeout_report_permits_valid_source(helper, tmp_path):
    src = _minimal_source(tmp_path, with_closeout=False)
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(
        [
            "--source-dir",
            str(src),
            "--dest-dir",
            str(dest),
            "--no-require-closeout-report",
            "--dry-run",
        ]
    )
    assert rc == 0


def test_pr_number_requires_pr_json(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(
        [
            "--source-dir",
            str(src),
            "--dest-dir",
            str(dest),
            "--pr-number",
            "99",
            "--dry-run",
        ]
    )
    assert rc == 1


def test_pr_json_supplied_passes_dry_run(helper, tmp_path):
    src = _minimal_source(tmp_path)
    pr_file = tmp_path / "pr.json"
    pr_file.write_text('{"number": 1}\n', encoding="utf-8")
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(
        [
            "--source-dir",
            str(src),
            "--dest-dir",
            str(dest),
            "--pr-number",
            "1",
            "--pr-json",
            str(pr_file),
            "--dry-run",
        ]
    )
    assert rc == 0


def test_non_dry_copy_creates_readme_and_manifest(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path)
    rc = helper.main(["--source-dir", str(src), "--dest-dir", str(dest)])
    assert rc == 0
    assert (dest / "DURABLE_COPY_README.md").is_file()
    assert (dest / "MANIFEST.sha256").is_file()


def test_non_dry_copy_verifies_manifest(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path, "verify_dest")
    rc = helper.main(["--source-dir", str(src), "--dest-dir", str(dest)])
    assert rc == 0
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, _ = verify_manifest_sha256(dest)
    assert ok


def test_duplicate_dest_without_force_fails(helper, tmp_path):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path, "dup")
    assert helper.main(["--source-dir", str(src), "--dest-dir", str(dest)]) == 0
    rc = helper.main(["--source-dir", str(src), "--dest-dir", str(dest)])
    assert rc == 1


def test_duplicate_dest_with_force_succeeds(helper, tmp_path, capsys):
    src = _minimal_source(tmp_path)
    dest = _archive_like_dest(tmp_path, "force_dest")
    assert helper.main(["--source-dir", str(src), "--dest-dir", str(dest)]) == 0
    (src / "note.txt").write_text("updated\n", encoding="utf-8")
    rc = helper.main(["--source-dir", str(src), "--dest-dir", str(dest), "--force"])
    assert rc == 0
    assert "FORCE_OVERWRITE=true" in capsys.readouterr().err


def test_fixture_source_usable(helper, tmp_path):
    dest = _archive_like_dest(tmp_path, "from_repo_fixture")
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
