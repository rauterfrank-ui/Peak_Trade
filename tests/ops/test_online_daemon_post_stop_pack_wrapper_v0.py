"""Contract tests for online readiness post-stop pack wrapper (no runtime workloads)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "ops" / "run_online_readiness_post_stop_pack_v0.sh"
PACK_SCRIPT = "pack_online_readiness_supervisor_evidence_v0.py"
P79_SCRIPT = "p79_supervisor_health_gate_v1.sh"

MARKERS = (
    "ONLINE_DAEMON_POST_STOP_PACK_WRAPPER_V0=true",
    "OPERATOR_INVOKED_ONLY=true",
    "DAEMON_NOT_STARTED=true",
    "DAEMON_NOT_STOPPED=true",
    "SUPERVISOR_NOT_STARTED=true",
    "SUPERVISOR_NOT_STOPPED=true",
    "LAUNCHCTL_CALLED=false",
    "PACK_SCRIPT_DELEGATED=true",
    "P79_ARCHIVE_VERIFY_EXPLICIT_ONLY=true",
    "EVIDENCE_NON_AUTHORIZING=true",
)


def _script_lines() -> list[str]:
    return WRAPPER.read_text(encoding="utf-8").splitlines()


def _durable_archive(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(autouse=True)
def _cleanup_durable_archive_dirs() -> None:
    yield
    archive_roots = REPO_ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def test_wrapper_exists_and_contains_operator_markers() -> None:
    assert WRAPPER.is_file()
    text = WRAPPER.read_text(encoding="utf-8")
    for marker in MARKERS:
        assert marker in text


def test_wrapper_references_pack_and_p79_archive_root() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert PACK_SCRIPT in text
    assert P79_SCRIPT in text
    assert "ARCHIVE_ROOT=" in text
    assert "--p79-archive-verify" in text
    assert "P79_ARCHIVE_VERIFY_SKIPPED=true" in text


def test_wrapper_does_not_invoke_launchctl_or_start_daemon_supervisor() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "launchctl " not in text
    assert "online_readiness_supervisor_v1.sh" not in text
    assert "online_readiness_daemon_v1.sh" not in text


def test_wrapper_delegates_pack_does_not_reimplement_manifest_logic() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
    assert "verify_manifest_sha256" not in text
    assert "finalize_primary_evidence_root" not in text


def test_p79_verify_gated_behind_explicit_flag() -> None:
    lines = _script_lines()
    p79_invocations = [
        line
        for line in lines
        if P79_SCRIPT in line
        and not line.strip().startswith("#")
        and not line.strip().startswith("echo")
    ]
    assert len(p79_invocations) == 1
    assert 'if [ "${P79_ARCHIVE_VERIFY}" -eq 1 ]' in WRAPPER.read_text(encoding="utf-8")


def test_wrapper_delegates_to_pack_on_temp_dirs_without_p79_verify(tmp_path: Path) -> None:
    out_dir = tmp_path / "supervisor_out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text('{"version":"test"}\n', encoding="utf-8")

    archive = _durable_archive(tmp_path)
    result = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "--out-dir",
            str(out_dir),
            "--archive-root",
            str(archive),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "P79_ARCHIVE_VERIFY_SKIPPED=true" in result.stdout
    assert (archive / "supervisor_session_closeout_v0.json").is_file()
    assert "POST_STOP_PACK_WRAPPER_RC=0" in result.stdout
