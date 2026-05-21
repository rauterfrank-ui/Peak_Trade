"""Contract tests for offline supervisor evidence pack closeout (no runtime workloads)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_SCRIPT = REPO_ROOT / "scripts" / "ops" / "pack_online_readiness_supervisor_evidence_v0.py"
SHARED_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ops.pack_online_readiness_supervisor_evidence_v0 import (
    CLOSEOUT_FILENAME,
    pack_supervisor_evidence,
)


def _durable_archive(tmp_path: Path) -> Path:
    # pytest tmp_path on Linux CI lives under /tmp; pack rejects archive roots there.
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(autouse=True)
def _cleanup_durable_archive_dirs() -> None:
    yield
    archive_roots = REPO_ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def test_pack_script_exists_and_reuses_shared_helper() -> None:
    text = PACK_SCRIPT.read_text(encoding="utf-8")
    assert "finalize_primary_evidence_root" in text
    assert "subprocess" not in text
    assert "launchctl " not in text
    assert "def verify_manifest_sha256" not in text


def test_pack_copies_out_dir_and_writes_closeout(tmp_path: Path) -> None:
    out_dir = tmp_path / "supervisor_out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text('{"version":"test"}\n', encoding="utf-8")
    tick = out_dir / "tick_20260101T000000Z"
    tick.mkdir()
    (tick / "P76_RESULT.txt").write_text("P76_READY\n", encoding="utf-8")

    archive = tmp_path / "archive"
    result = pack_supervisor_evidence(out_dir=out_dir, archive_root=archive)

    assert result.exit_code == 0
    assert (archive / "supervisor_session" / "supervisor_meta.json").is_file()
    assert (archive / "supervisor_session" / "tick_20260101T000000Z" / "P76_RESULT.txt").is_file()
    closeout = json.loads((archive / CLOSEOUT_FILENAME).read_text(encoding="utf-8"))
    assert closeout["evidence_non_authorizing"] is True
    assert closeout["manifest_verified"] is False
    assert not (archive / "MANIFEST.sha256").exists()


def test_pack_records_missing_optional_artifact_without_enforce(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text("{}\n", encoding="utf-8")

    missing = tmp_path / "missing.pid"
    archive = tmp_path / "archive"
    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=archive,
        optional_artifacts=(missing,),
    )

    assert result.exit_code == 0
    assert len(result.optional_artifacts) == 1
    assert result.optional_artifacts[0].status == "missing"
    closeout = json.loads((archive / CLOSEOUT_FILENAME).read_text(encoding="utf-8"))
    assert closeout["optional_artifacts"][0]["status"] == "missing"


def test_pack_copies_optional_artifact_when_present(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "P78_SUPERVISOR.ndjson").write_text('{"tick":1}\n', encoding="utf-8")

    pidfile = tmp_path / "supervisor.pid"
    pidfile.write_text("12345\n", encoding="utf-8")

    archive = tmp_path / "archive"
    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=archive,
        optional_artifacts=(pidfile,),
    )

    assert result.exit_code == 0
    assert (archive / "supporting" / "supervisor.pid").read_text(encoding="utf-8") == "12345\n"
    assert result.optional_artifacts[0].status == "copied"


def test_pack_enforce_writes_and_verifies_manifest(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text("{}\n", encoding="utf-8")

    archive = _durable_archive(tmp_path)
    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=archive,
        primary_evidence_enforce=True,
    )

    assert result.exit_code == 0
    assert result.manifest_verified is True
    assert (archive / "MANIFEST.sha256").is_file()

    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    ok, msg = verify_manifest_sha256(archive)
    assert ok is True, msg


def test_pack_enforce_fails_closed_on_missing_out_dir(tmp_path: Path) -> None:
    result = pack_supervisor_evidence(
        out_dir=tmp_path / "missing",
        archive_root=tmp_path / "archive",
        primary_evidence_enforce=True,
    )
    assert result.exit_code == 1
    assert "out_dir missing" in result.error


def test_pack_enforce_fails_closed_on_finalize_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "meta.json").write_text("{}\n", encoding="utf-8")

    def _fail(_root: Path) -> tuple[bool, str]:
        return False, "checksum mismatch"

    monkeypatch.setattr(
        "scripts.ops.pack_online_readiness_supervisor_evidence_v0.finalize_primary_evidence_root",
        _fail,
    )

    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=_durable_archive(tmp_path),
        primary_evidence_enforce=True,
    )
    assert result.exit_code == 1
    assert "finalize failed" in result.error


def test_pack_enforce_rejects_tmp_archive_root(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "meta.json").write_text("{}\n", encoding="utf-8")

    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=Path("/tmp/supervisor_pack_test"),
        primary_evidence_enforce=True,
    )
    assert result.exit_code == 1
    assert "outside /tmp" in result.error


def test_cli_main_parses_without_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import scripts.ops.pack_online_readiness_supervisor_evidence_v0 as mod

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text("{}\n", encoding="utf-8")
    archive = tmp_path / "archive"

    rc = mod.main(["--out-dir", str(out_dir), "--archive-root", str(archive)])
    assert rc == 0


def test_preflight_documents_supervisor_pack_closeout() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text
