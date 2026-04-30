"""CLI contract tests for scripts/ops/validate_merge_logs_setup.sh (fixture repo + script copy)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SOURCE_SCRIPT = ROOT / "scripts" / "ops" / "validate_merge_logs_setup.sh"

START_MARKER = "<!-- MERGE_LOG_EXAMPLES:START -->"
END_MARKER = "<!-- MERGE_LOG_EXAMPLES:END -->"


def _install_script(fake_repo: Path) -> Path:
    dest = fake_repo / "scripts" / "ops" / "validate_merge_logs_setup.sh"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_SOURCE_SCRIPT, dest)
    dest.chmod(0o755)
    return dest


def _doc_with_markers() -> str:
    return f"""# Doc\n\n{START_MARKER}\n\nExamples here.\n\n{END_MARKER}\n"""


def _write_pass_fixtures(fake_repo: Path) -> None:
    ops = fake_repo / "scripts" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    batch = ops / "generate_merge_logs_batch.sh"
    batch.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    batch.chmod(0o755)
    (fake_repo / "docs" / "ops").mkdir(parents=True, exist_ok=True)
    (fake_repo / "docs" / "ops" / "README.md").write_text(_doc_with_markers(), encoding="utf-8")
    (fake_repo / "docs" / "ops" / "MERGE_LOG_WORKFLOW.md").write_text(
        _doc_with_markers(), encoding="utf-8"
    )
    (ops / "ops_center.sh").write_text(
        "# fixture ops center\n"
        "cmd_merge_log() { true; }\n"
        "# delegate to generate_merge_logs_batch.sh\n",
        encoding="utf-8",
    )


def _run(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_passes_when_merge_log_setup_complete(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    _write_pass_fixtures(tmp_path)
    p = _run(script)
    assert p.returncode == 0
    assert "✅ All checks passed" in p.stdout
    assert "Exists + executable" in p.stdout
    assert "Markers present" in p.stdout
    assert "merge-log subcommand with batch support present" in p.stdout
    assert p.stderr == ""


def test_fails_when_batch_script_missing(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    _write_pass_fixtures(tmp_path)
    (tmp_path / "scripts" / "ops" / "generate_merge_logs_batch.sh").unlink()
    p = _run(script)
    assert p.returncode == 1
    assert "File not found" in p.stdout
    assert "❌ One or more checks failed" in p.stdout
    assert p.stderr == ""


def test_fails_when_batch_script_not_executable(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    _write_pass_fixtures(tmp_path)
    (tmp_path / "scripts" / "ops" / "generate_merge_logs_batch.sh").chmod(0o644)
    p = _run(script)
    assert p.returncode == 1
    assert "Not executable" in p.stdout
    assert p.stderr == ""


def test_fails_when_doc_missing_start_marker(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    _write_pass_fixtures(tmp_path)
    (tmp_path / "docs" / "ops" / "README.md").write_text(
        f"# x\n\n{END_MARKER}\n",
        encoding="utf-8",
    )
    p = _run(script)
    assert p.returncode == 1
    assert "Missing marker" in p.stdout
    assert START_MARKER in p.stdout
    assert p.stderr == ""


def test_fails_when_ops_center_missing_cmd_merge_log(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    _write_pass_fixtures(tmp_path)
    (tmp_path / "scripts" / "ops" / "ops_center.sh").write_text(
        "# no cmd_merge_log\n# generate_merge_logs_batch.sh only\n",
        encoding="utf-8",
    )
    p = _run(script)
    assert p.returncode == 1
    assert "Missing cmd_merge_log() function" in p.stdout
    assert p.stderr == ""


def test_fails_when_ops_center_missing_batch_reference(tmp_path: Path) -> None:
    script = _install_script(tmp_path)
    _write_pass_fixtures(tmp_path)
    (tmp_path / "scripts" / "ops" / "ops_center.sh").write_text(
        "cmd_merge_log() { true; }\n",
        encoding="utf-8",
    )
    p = _run(script)
    assert p.returncode == 1
    assert "Missing batch generator integration" in p.stdout
    assert p.stderr == ""
