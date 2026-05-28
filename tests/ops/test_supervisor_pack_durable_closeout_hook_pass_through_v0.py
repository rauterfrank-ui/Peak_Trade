"""Tests for supervisor pack durable closeout hook pass-through (non-authorizing)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_SCRIPT = REPO_ROOT / "scripts" / "ops" / "pack_online_readiness_supervisor_evidence_v0.py"
DURABLE_HELPER = REPO_ROOT / "scripts" / "ops" / "durable_closeout_copy_verify_v0.py"
FORBIDDEN_CHAIN_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"
PYTEST_DURABLE_DEST_ROOT = (
    REPO_ROOT / "out" / "ops" / "_pytest_supervisor_pack_durable_closeout_hook"
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.ops.pack_online_readiness_supervisor_evidence_v0 as pack_mod
from scripts.ops.pack_online_readiness_supervisor_evidence_v0 import (
    CLOSEOUT_FILENAME,
    pack_supervisor_evidence,
)


def _durable_dest(tmp_path: Path, name: str = "dest") -> Path:
    safe = tmp_path.name.replace("/", "_")
    dest = PYTEST_DURABLE_DEST_ROOT / safe / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def _durable_archive(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="module")
def pm():
    return pack_mod


def test_forbidden_parallel_execute_script_absent():
    assert not FORBIDDEN_CHAIN_SCRIPT.exists()
    assert DURABLE_HELPER.is_file()


def test_cli_flags_present_in_source():
    text = PACK_SCRIPT.read_text(encoding="utf-8")
    assert "--invoke-durable-closeout-after-pack-v0" in text
    assert "--durable-closeout-dest-dir" in text
    assert "SUPERVISOR_PACK_DURABLE_CLOSEOUT_REQUESTED=" in text
    assert "--run-local-post-closeout-chain-v0" not in text
    assert "--require-durable-pointer-evidence" not in text


def test_hook_validate_requires_dest_dir(pm):
    assert (
        pm.validate_supervisor_pack_durable_closeout_hook_cli(
            invoke_durable_closeout_after_pack_v0=True,
            durable_closeout_dest_dir=None,
        )
        == 1
    )


def test_hook_validate_blocks_tmp_dest(pm):
    assert (
        pm.validate_supervisor_pack_durable_closeout_hook_cli(
            invoke_durable_closeout_after_pack_v0=True,
            durable_closeout_dest_dir=Path("/tmp/supervisor_durable_dest"),
        )
        == 1
    )


def test_main_hook_without_dest_fails_before_pack(pm, monkeypatch, tmp_path: Path):
    pack_calls: list[object] = []
    monkeypatch.setattr(
        pm,
        "pack_supervisor_evidence",
        lambda **kwargs: (
            pack_calls.append(kwargs)
            or pm.PackResult(
                out_dir="",
                archive_root="",
                closeout_path="",
                supervisor_session_dest="",
            )
        ),
    )
    rc = pm.main(
        [
            "--out-dir",
            str(tmp_path / "out"),
            "--archive-root",
            str(tmp_path / "archive"),
            "--invoke-durable-closeout-after-pack-v0",
        ]
    )
    assert rc == 1
    assert pack_calls == []


def test_invoke_calls_only_durable_helper(pm, tmp_path: Path):
    source = tmp_path / "archive"
    source.mkdir()
    (source / CLOSEOUT_FILENAME).write_text("{}\n", encoding="utf-8")
    dest = _durable_dest(tmp_path, "helper_only")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    rc = pm.invoke_supervisor_pack_durable_closeout_after_pack(
        source_dir=source,
        dest_dir=dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert rc == 0
    assert len(calls) == 1
    joined = " ".join(calls[0])
    assert calls[0][1].endswith("durable_closeout_copy_verify_v0.py")
    assert str(source.resolve()) in joined
    assert str(dest.resolve()) in joined
    assert "build_generic_evidence_run_registry_v1.py" not in joined
    assert "build_post_closeout_projection_payload_v0.py" not in joined
    assert "notion_post_closeout_sync_dry_run_v0.py" not in joined


def test_pack_invokes_hook_after_success_without_enforce(pm, tmp_path: Path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text("{}\n", encoding="utf-8")
    archive = tmp_path / "archive"
    dest = _durable_dest(tmp_path, "after_pack")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=archive,
        invoke_durable_closeout_after_pack_v0=True,
        durable_closeout_dest_dir=dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert result.exit_code == 0
    assert len(calls) == 1
    assert str(archive.resolve()) in " ".join(calls[0])


def test_pack_invokes_hook_after_primary_evidence_success(pm, monkeypatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text("{}\n", encoding="utf-8")
    archive = _durable_archive(tmp_path)
    dest = _durable_dest(tmp_path, "after_finalize")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(
        pack_mod,
        "finalize_primary_evidence_root",
        lambda _root: (True, ""),
    )

    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=archive,
        primary_evidence_enforce=True,
        invoke_durable_closeout_after_pack_v0=True,
        durable_closeout_dest_dir=dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert result.exit_code == 0
    assert result.manifest_verified is True
    assert len(calls) == 1
    assert (archive / CLOSEOUT_FILENAME).is_file()


def test_pack_hook_fail_closed_on_helper_nonzero(pm, monkeypatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text("{}\n", encoding="utf-8")
    archive = _durable_archive(tmp_path)
    dest = _durable_dest(tmp_path, "fail_closed")

    monkeypatch.setattr(
        pack_mod,
        "finalize_primary_evidence_root",
        lambda _root: (True, ""),
    )

    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=archive,
        primary_evidence_enforce=True,
        invoke_durable_closeout_after_pack_v0=True,
        durable_closeout_dest_dir=dest,
        durable_closeout_invoker=lambda _argv: 2,
    )
    assert result.exit_code == 2


def test_pack_skips_hook_when_primary_evidence_finalize_fails(
    pm, monkeypatch, tmp_path: Path
) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "meta.json").write_text("{}\n", encoding="utf-8")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(
        pack_mod,
        "finalize_primary_evidence_root",
        lambda _root: (False, "checksum mismatch"),
    )
    dest = _durable_dest(tmp_path, "no_hook")

    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=_durable_archive(tmp_path),
        primary_evidence_enforce=True,
        invoke_durable_closeout_after_pack_v0=True,
        durable_closeout_dest_dir=dest,
        durable_closeout_invoker=_recording_invoker,
    )
    assert result.exit_code == 1
    assert calls == []


def test_pack_skips_hook_when_pack_fails(pm, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    result = pack_supervisor_evidence(
        out_dir=tmp_path / "missing",
        archive_root=tmp_path / "archive",
        invoke_durable_closeout_after_pack_v0=True,
        durable_closeout_dest_dir=_durable_dest(tmp_path),
        durable_closeout_invoker=_recording_invoker,
    )
    assert result.exit_code == 1
    assert calls == []


def test_pack_default_off_no_hook(pm, monkeypatch, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "supervisor_meta.json").write_text("{}\n", encoding="utf-8")
    calls: list[list[str]] = []

    def _recording_invoker(argv: list[str]) -> int:
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(
        pack_mod,
        "finalize_primary_evidence_root",
        lambda _root: (True, ""),
    )

    result = pack_supervisor_evidence(
        out_dir=out_dir,
        archive_root=_durable_archive(tmp_path),
        primary_evidence_enforce=True,
        invoke_durable_closeout_after_pack_v0=False,
        durable_closeout_dest_dir=None,
        durable_closeout_invoker=_recording_invoker,
    )
    assert result.exit_code == 0
    assert calls == []


def test_maybe_invoke_emits_machine_lines(pm, tmp_path: Path, capsys):
    archive = tmp_path / "archive"
    archive.mkdir()
    dest = _durable_dest(tmp_path, "lines")

    rc = pm.maybe_invoke_supervisor_pack_durable_closeout_after_pack(
        archive_root=archive,
        invoke_durable_closeout_after_pack_v0=False,
        durable_closeout_dest_dir=dest,
        pack_evidence_finalized=True,
        durable_closeout_invoker=lambda _argv: 0,
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "SUPERVISOR_PACK_DURABLE_CLOSEOUT_REQUESTED=false" in out
    assert "SUPERVISOR_PACK_DURABLE_CLOSEOUT_INVOKED=false" in out


def test_pack_script_no_direct_chain_owners(pm):
    text = PACK_SCRIPT.read_text(encoding="utf-8")
    assert "build_generic_evidence_run_registry_v1" not in text
    assert "build_post_closeout_projection_payload_v0" not in text
    assert "notion_post_closeout_sync_dry_run_v0" not in text
    assert "launchctl " not in text
