"""Contract tests for P79 offline supervisor evidence pack manifest gate (no runtime workloads)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
P79_SHELL = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_health_gate_v1.sh"
P79_VERIFY = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_evidence_manifest_verify_v0.py"
PACK_SCRIPT = REPO_ROOT / "scripts" / "ops" / "pack_online_readiness_supervisor_evidence_v0.py"
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ops.pack_online_readiness_supervisor_evidence_v0 import (
    CLOSEOUT_FILENAME,
    pack_supervisor_evidence,
)
from scripts.ops.p79_supervisor_evidence_manifest_verify_v0 import (
    ARCHIVE_GATE_MODE,
    verify_supervisor_evidence_archive,
)
from scripts.ops.primary_evidence_retention_v0 import MANIFEST_FILENAME


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


def _build_valid_pack(tmp_path: Path) -> Path:
    out_dir = tmp_path / "supervisor_out"
    out_dir.mkdir()
    tick = out_dir / "tick_20260101T000000Z"
    tick.mkdir()
    (tick / "manifest.json").write_text("{}\n", encoding="utf-8")
    (tick / "P76_RESULT.txt").write_text("P76_READY\n", encoding="utf-8")

    archive = _durable_archive(tmp_path)
    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=archive,
        primary_evidence_enforce=True,
    )
    assert result.exit_code == 0, result.error
    return archive


def test_verify_module_reuses_shared_helper_not_duplicate() -> None:
    text = P79_VERIFY.read_text(encoding="utf-8")
    assert "verify_manifest_sha256" in text
    assert "primary_evidence_retention_v0" in text
    assert "def verify_manifest_sha256" not in text
    assert "launchctl" not in text
    assert "subprocess" not in text


def test_shell_documents_archive_root_mode() -> None:
    text = P79_SHELL.read_text(encoding="utf-8")
    assert "ARCHIVE_ROOT" in text
    assert "mutually exclusive" in text
    assert "p79_supervisor_evidence_manifest_verify_v0.py" in text


def test_archive_mode_accepts_valid_pack(tmp_path: Path) -> None:
    archive = _build_valid_pack(tmp_path)
    result = verify_supervisor_evidence_archive(archive)
    assert result.exit_code == 0
    assert result.manifest_verified is True
    assert result.closeout_parse_ok is True
    assert result.gate_mode == ARCHIVE_GATE_MODE
    assert (archive / CLOSEOUT_FILENAME).is_file()
    assert (archive / MANIFEST_FILENAME).is_file()


def test_archive_mode_fails_missing_manifest(tmp_path: Path) -> None:
    archive = _build_valid_pack(tmp_path)
    (archive / MANIFEST_FILENAME).unlink()
    result = verify_supervisor_evidence_archive(archive)
    assert result.exit_code != 0
    assert result.manifest_verified is False
    assert "MANIFEST.sha256 missing" in result.error


def test_archive_mode_fails_manifest_mismatch(tmp_path: Path) -> None:
    archive = _build_valid_pack(tmp_path)
    session_file = archive / "supervisor_session" / "tick_20260101T000000Z" / "P76_RESULT.txt"
    session_file.write_text("tampered\n", encoding="utf-8")
    result = verify_supervisor_evidence_archive(archive)
    assert result.exit_code != 0
    assert result.manifest_verified is False
    assert "manifest verify failed" in result.error


def test_archive_mode_fails_missing_closeout(tmp_path: Path) -> None:
    archive = _build_valid_pack(tmp_path)
    (archive / CLOSEOUT_FILENAME).unlink()
    result = verify_supervisor_evidence_archive(archive)
    assert result.exit_code != 0
    assert "supervisor_session_closeout_v0.json missing" in result.error


def test_archive_mode_fails_closeout_pack_failure(tmp_path: Path) -> None:
    archive = _build_valid_pack(tmp_path)
    closeout = json.loads((archive / CLOSEOUT_FILENAME).read_text(encoding="utf-8"))
    closeout["exit_code"] = 1
    closeout["error"] = "pack failed"
    (archive / CLOSEOUT_FILENAME).write_text(json.dumps(closeout) + "\n", encoding="utf-8")
    result = verify_supervisor_evidence_archive(archive)
    assert result.exit_code != 0
    assert "pack failure" in result.error


def test_missing_optional_supporting_does_not_false_pass_on_closeout_error(tmp_path: Path) -> None:
    archive = _build_valid_pack(tmp_path)
    closeout = json.loads((archive / CLOSEOUT_FILENAME).read_text(encoding="utf-8"))
    closeout["optional_artifacts"] = [
        {
            "source": "/tmp/missing.pid",
            "dest": "supporting/missing.pid",
            "status": "missing",
            "reason": "x",
        }
    ]
    closeout["error"] = "required optional artifact missing"
    closeout["exit_code"] = 1
    (archive / CLOSEOUT_FILENAME).write_text(json.dumps(closeout) + "\n", encoding="utf-8")
    result = verify_supervisor_evidence_archive(archive)
    assert result.exit_code != 0


def test_cli_main_writes_non_authorizing_evidence(tmp_path: Path) -> None:
    import scripts.ops.p79_supervisor_evidence_manifest_verify_v0 as mod

    archive = _build_valid_pack(tmp_path)
    rc = mod.main(["--archive-root", str(archive)])
    assert rc == 0
    evidence = json.loads((archive / "p79_health_gate_v1.json").read_text(encoding="utf-8"))
    assert evidence["evidence_non_authorizing"] is True
    assert evidence["gate_mode"] == ARCHIVE_GATE_MODE
    assert evidence["manifest_verified"] is True
    assert evidence["overall_ok"] is True


def test_runtime_tick_manifest_path_unchanged_in_shell() -> None:
    text = P79_SHELL.read_text(encoding="utf-8")
    assert "manifest.json" in text
    assert "runtime_ticks" in text or "gate_mode" in text


def test_preflight_documents_p79_archive_manifest_check() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert (
        "p79_supervisor_evidence_manifest_verify_v0.py" in text
        or "p79_supervisor_health_gate_v1.sh" in text
    )
