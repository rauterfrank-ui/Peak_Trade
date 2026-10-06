"""Tests for simple run evidence retention v1 (owner index; non-authorizing)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
    BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    MANIFEST_FILENAME,
    PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    write_manifest_sha256,
)
from src.ops.wallclock_session_evidence_v0 import (
    WALLCLOCK_EVIDENCE_FILENAME,
    build_wallclock_evidence_from_manifest_fields,
    write_wallclock_evidence,
)
from src.ops.simple_run_evidence_retention_v1.constants_v1 import (
    ENV_DATA_ARCHIVE_ROOT,
    ENV_OWNER_RUN_EVIDENCE_ROOT,
    OWNER_HOME_DIR_NAME,
    OWNER_INDEX_DIRNAME,
    OWNER_INDEX_FILENAME,
    RETENTION_CANARY,
    RETENTION_KEEP,
    RUN_CLASS_CANARY,
    RUN_CLASS_PAPER,
    RUN_CLASS_SHADOW,
    RUN_STATUS_COMPLETE,
    RUN_STATUS_INCOMPLETE,
    SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1,
)
from src.ops.simple_run_evidence_retention_v1.storage_v1 import (
    OwnerRunEvidenceRootError,
    default_owner_index_path,
    resolve_owner_run_evidence_root,
)
from src.ops.simple_run_evidence_retention_v1.discover_v1 import (
    discover_archive_runs,
    discover_repo_canary_evidence,
)
from src.ops.simple_run_evidence_retention_v1.index_v1 import (
    build_archive_run_entry,
    build_canary_entry,
    build_index_entries,
    infer_archive_run_status,
)
from src.ops.simple_run_evidence_retention_v1.persist_v1 import (
    persist_bounded_run_to_owner_evidence,
)
from src.ops.simple_run_evidence_retention_v1.discover_v1 import ArchiveRunRef

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ARCHIVE = (
    ROOT / "tests/fixtures/workflow_dashboard_readmodel_v1/pipeline_minimal/archive_root"
)
BUILD_SCRIPT = ROOT / "scripts/ops/build_simple_run_evidence_index_v1.py"
CLI_SCRIPT = ROOT / "scripts/ops/simple_run_evidence_v1.py"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_wallclock(run_dir: Path, *, duration_minutes: int = 10) -> None:
    planned_seconds = duration_minutes * 60
    start = datetime(2026, 6, 22, 10, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(seconds=planned_seconds + 1)
    evidence = build_wallclock_evidence_from_manifest_fields(
        utc_started=start.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        utc_completed=end.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        duration_minutes=duration_minutes,
        start_monotonic_seconds=1000.0,
        end_monotonic_seconds=1000.0 + planned_seconds + 1.0,
    )
    write_wallclock_evidence(run_dir / WALLCLOCK_EVIDENCE_FILENAME, evidence)


def _write_complete_bounded_run(
    run_dir: Path,
    run_class: str,
    *,
    run_id: str = "fixture_run",
) -> None:
    if run_class == RUN_CLASS_PAPER:
        required = PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    elif run_class == RUN_CLASS_SHADOW:
        required = BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS
    else:
        required = BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS
    metadata = {
        "utc_start": "2026-06-22T10:00:00Z",
        "utc_end": "2026-06-22T10:10:00Z",
        "verdict": "PASS",
        "adapter_rc": 0,
        "stage": f"{run_class.upper()}_FIXTURE",
    }
    for rel in required:
        path = run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".json"):
            if rel == "review/REVIEW_RESULT.json":
                path.write_text(json.dumps({"verdict": "PASS"}) + "\n", encoding="utf-8")
            elif rel == "RUN_METADATA.json":
                path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")
            else:
                path.write_text("{}\n", encoding="utf-8")
        elif rel.endswith(".jsonl"):
            path.write_text("{}\n", encoding="utf-8")
        else:
            path.write_text("fixture\n", encoding="utf-8")
    if WALLCLOCK_EVIDENCE_FILENAME in required:
        _write_wallclock(run_dir)
    write_manifest_sha256(run_dir)


def _write_manifest(directory: Path) -> None:
    entries: list[str] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {MANIFEST_FILENAME, "MANIFEST_VERIFY.log"}:
            continue
        rel = path.relative_to(directory).as_posix()
        entries.append(f"{_sha256_file(path)}  {rel}")
    (directory / MANIFEST_FILENAME).write_text("\n".join(entries) + "\n", encoding="utf-8")


def test_discover_fixture_archive_runs():
    refs = discover_archive_runs(FIXTURE_ARCHIVE)
    classes = {r.run_class for r in refs}
    assert RUN_CLASS_PAPER in classes
    assert RUN_CLASS_SHADOW in classes
    assert "testnet" in classes
    assert len(refs) >= 5


def test_complete_paper_run_index_entry():
    refs = [r for r in discover_archive_runs(FIXTURE_ARCHIVE) if r.run_id.startswith("p1_")]
    assert refs
    entry = build_archive_run_entry(refs[0])
    assert entry["schema"] == SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1
    assert entry["run_class"] == RUN_CLASS_PAPER
    assert entry["config_ref"] == "P1_SHORT_BOUNDED_PAPER"
    assert entry["evidence_location"].startswith("runs/")
    assert entry["status"] in (RUN_STATUS_COMPLETE, RUN_STATUS_INCOMPLETE)


def test_incomplete_run_not_complete(tmp_path: Path):
    run_dir = tmp_path / "runs" / "shadow" / "partial_shadow"
    run_dir.mkdir(parents=True)
    (run_dir / "RUN_METADATA.json").write_text(
        json.dumps({"utc_start": "2026-01-01T00:00:00Z", "adapter_rc": 0}) + "\n",
        encoding="utf-8",
    )
    status = infer_archive_run_status(run_dir, RUN_CLASS_SHADOW)
    assert status == RUN_STATUS_INCOMPLETE
    entry = build_archive_run_entry(
        ArchiveRunRef(
            run_class=RUN_CLASS_SHADOW,
            run_id="partial_shadow",
            run_dir=run_dir,
            archive_root=tmp_path,
        )
    )
    assert entry["status"] != RUN_STATUS_COMPLETE
    assert entry["index_finalized"] is False


def test_canary_discovery_and_retention_class():
    refs = discover_repo_canary_evidence(ROOT)
    assert refs, "expected at least one canary evidence bundle in evidence/ops"
    ref = refs[0]
    assert ref.evidence_dir.is_relative_to(ROOT / "evidence" / "ops")
    entry = build_canary_entry(ref, ROOT)
    assert entry["run_class"] == RUN_CLASS_CANARY
    assert entry["retention_class"] == RETENTION_CANARY
    assert entry["evidence_storage_kind"] == "repo_evidence_ops"
    assert entry["evidence_location"].startswith("evidence/ops/")


def test_retention_sidecar_keep(tmp_path: Path):
    run_dir = tmp_path / "runs" / "paper" / "keep_me"
    run_dir.mkdir(parents=True)
    for rel in PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS:
        path = run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    (run_dir / "review" / "REVIEW_RESULT.json").write_text(
        json.dumps({"verdict": "PASS"}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "RETENTION.json").write_text(
        json.dumps({"retention_class": RETENTION_KEEP}) + "\n",
        encoding="utf-8",
    )
    _write_manifest(run_dir)
    entry = build_archive_run_entry(
        ArchiveRunRef(
            run_class=RUN_CLASS_PAPER,
            run_id="keep_me",
            run_dir=run_dir,
            archive_root=tmp_path,
        )
    )
    assert entry["retention_class"] == RETENTION_KEEP


def test_build_index_cli(tmp_path: Path):
    out = tmp_path / "index.jsonl"
    proc = subprocess.run(
        [
            str(ROOT / "scripts/pt"),
            str(BUILD_SCRIPT),
            "--repo-root",
            str(ROOT),
            "--archive-root",
            str(FIXTURE_ARCHIVE),
            "--out",
            str(out),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1 in text
    list_proc = subprocess.run(
        [
            str(ROOT / "scripts/pt"),
            str(CLI_SCRIPT),
            "--index",
            str(out),
            "list",
            "--run-class",
            "paper",
            "--limit",
            "5",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert list_proc.returncode == 0, list_proc.stderr
    assert "paper" in list_proc.stdout


def test_shadow_required_paths_match_primary_owner():
    assert "WALLCLOCK_EVIDENCE.json" in BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS


def test_build_index_entries_merge_archive_and_canary():
    entries = build_index_entries(repo_root=ROOT, archive_root=FIXTURE_ARCHIVE)
    classes = {e["run_class"] for e in entries}
    assert RUN_CLASS_PAPER in classes
    assert RUN_CLASS_CANARY in classes


@pytest.mark.parametrize("run_class", (RUN_CLASS_PAPER, RUN_CLASS_SHADOW, "testnet"))
def test_persist_bounded_run_to_owner_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_class: str
):
    owner_root = tmp_path / "owner_evidence"
    monkeypatch.setenv(ENV_OWNER_RUN_EVIDENCE_ROOT, str(owner_root))
    monkeypatch.setenv(ENV_DATA_ARCHIVE_ROOT, "/Volumes/OTHER_DISK/ignored")
    source = tmp_path / "external_archive" / "runs" / run_class / "run_fixture_001"
    source.mkdir(parents=True)
    _write_complete_bounded_run(source, run_class, run_id="run_fixture_001")
    result = persist_bounded_run_to_owner_evidence(
        source,
        run_class=run_class,
        run_id="run_fixture_001",
        env={ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root)},
    )
    assert result.rc == 0
    dest = owner_root / "runs" / run_class / "run_fixture_001"
    assert dest.is_dir()
    assert (dest / MANIFEST_FILENAME).is_file()
    entries = build_index_entries(
        repo_root=ROOT,
        archive_root=None,
        env={ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root)},
    )
    assert any(
        e.get("run_id") == "run_fixture_001" and e.get("run_class") == run_class for e in entries
    )


def test_persist_idempotent_identical(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    owner_root = tmp_path / "owner_evidence"
    monkeypatch.setenv(ENV_OWNER_RUN_EVIDENCE_ROOT, str(owner_root))
    source = tmp_path / "source"
    source.mkdir()
    _write_complete_bounded_run(source, RUN_CLASS_PAPER)
    env = {ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root)}
    first = persist_bounded_run_to_owner_evidence(
        source, run_class=RUN_CLASS_PAPER, run_id="fixture_run", env=env
    )
    second = persist_bounded_run_to_owner_evidence(
        source, run_class=RUN_CLASS_PAPER, run_id="fixture_run", env=env
    )
    assert first.rc == 0
    assert second.rc == 0
    assert second.status == "verified_existing"


def test_persist_collision_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    owner_root = tmp_path / "owner_evidence"
    monkeypatch.setenv(ENV_OWNER_RUN_EVIDENCE_ROOT, str(owner_root))
    source = tmp_path / "source"
    source.mkdir()
    _write_complete_bounded_run(source, RUN_CLASS_PAPER)
    env = {ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root)}
    assert (
        persist_bounded_run_to_owner_evidence(
            source, run_class=RUN_CLASS_PAPER, run_id="fixture_run", env=env
        ).rc
        == 0
    )
    (source / "RUN_METADATA.json").write_text(
        json.dumps({"utc_start": "2026-01-02T00:00:00Z", "verdict": "PASS", "adapter_rc": 0})
        + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(source)
    collision = persist_bounded_run_to_owner_evidence(
        source, run_class=RUN_CLASS_PAPER, run_id="fixture_run", env=env
    )
    assert collision.rc != 0
    assert collision.status == "collision"


def test_persist_incomplete_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    owner_root = tmp_path / "owner_evidence"
    monkeypatch.setenv(ENV_OWNER_RUN_EVIDENCE_ROOT, str(owner_root))
    source = tmp_path / "source"
    source.mkdir()
    (source / "RUN_METADATA.json").write_text("{}\n", encoding="utf-8")
    result = persist_bounded_run_to_owner_evidence(
        source,
        run_class=RUN_CLASS_PAPER,
        run_id="partial",
        env={ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root)},
    )
    assert result.rc != 0


def test_owner_index_finds_persisted_run_without_archive_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    owner_root = tmp_path / "owner_evidence"
    monkeypatch.setenv(ENV_OWNER_RUN_EVIDENCE_ROOT, str(owner_root))
    source = tmp_path / "source"
    source.mkdir()
    _write_complete_bounded_run(source, RUN_CLASS_PAPER, run_id="indexed_run")
    env = {ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root)}
    assert (
        persist_bounded_run_to_owner_evidence(
            source, run_class=RUN_CLASS_PAPER, run_id="indexed_run", env=env
        ).rc
        == 0
    )
    entries = build_index_entries(repo_root=ROOT, archive_root=None, env=env)
    match = [e for e in entries if e.get("run_id") == "indexed_run"]
    assert match
    assert match[0]["evidence_storage_kind"] == "owner_evidence_home"


def test_owner_root_default_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.delenv(ENV_OWNER_RUN_EVIDENCE_ROOT, raising=False)
    root = resolve_owner_run_evidence_root(env={})
    assert root == (fake_home / OWNER_HOME_DIR_NAME).resolve()


def test_data_archive_env_does_not_change_owner_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    env = {
        ENV_DATA_ARCHIVE_ROOT: "/Volumes/SOME_OTHER_DISK/whatever",
    }
    root = resolve_owner_run_evidence_root(env=env)
    assert root == (fake_home / OWNER_HOME_DIR_NAME).resolve()


def test_owner_override_env(tmp_path: Path):
    override = tmp_path / "custom_owner_root"
    root = resolve_owner_run_evidence_root(env={ENV_OWNER_RUN_EVIDENCE_ROOT: str(override)})
    assert root == override.resolve()


def test_default_index_path_under_owner_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    index_path = default_owner_index_path(env={})
    expected = fake_home / OWNER_HOME_DIR_NAME / OWNER_INDEX_DIRNAME / OWNER_INDEX_FILENAME
    assert index_path == expected.resolve()


def test_archive_root_does_not_change_index_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    owner_root = tmp_path / "owner_storage"
    discovery = tmp_path / "Volumes" / "OTHER_DISK" / "archive"
    discovery.mkdir(parents=True)
    env = {
        ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root),
        ENV_DATA_ARCHIVE_ROOT: str(discovery),
    }
    proc = subprocess.run(
        [
            str(ROOT / "scripts/pt"),
            str(BUILD_SCRIPT),
            "--repo-root",
            str(ROOT),
            "--archive-root",
            str(discovery),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **env},
    )
    assert proc.returncode == 0, proc.stderr
    index_path = owner_root / OWNER_INDEX_DIRNAME / OWNER_INDEX_FILENAME
    assert index_path.is_file()
    assert not (discovery / OWNER_INDEX_DIRNAME).exists()


def test_relative_owner_override_fail_closed():
    with pytest.raises(OwnerRunEvidenceRootError):
        resolve_owner_run_evidence_root(
            env={ENV_OWNER_RUN_EVIDENCE_ROOT: "relative/owner_evidence"}
        )


def test_index_removal_does_not_remove_primary_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    owner_root = tmp_path / "owner_evidence"
    monkeypatch.setenv(ENV_OWNER_RUN_EVIDENCE_ROOT, str(owner_root))
    source = tmp_path / "source"
    source.mkdir()
    _write_complete_bounded_run(source, RUN_CLASS_PAPER, run_id="primary_only")
    env = {ENV_OWNER_RUN_EVIDENCE_ROOT: str(owner_root)}
    assert (
        persist_bounded_run_to_owner_evidence(
            source, run_class=RUN_CLASS_PAPER, run_id="primary_only", env=env
        ).rc
        == 0
    )
    bundle = owner_root / "runs" / RUN_CLASS_PAPER / "primary_only"
    index_path = default_owner_index_path(env=env)
    if index_path.is_file():
        index_path.unlink()
    assert bundle.is_dir()
    assert (bundle / MANIFEST_FILENAME).is_file()


def test_home_unresolvable_fail_closed(monkeypatch: pytest.MonkeyPatch):
    def _broken_home() -> Path:
        raise RuntimeError("no home")

    monkeypatch.setattr(Path, "home", _broken_home)
    monkeypatch.delenv(ENV_OWNER_RUN_EVIDENCE_ROOT, raising=False)
    try:
        resolve_owner_run_evidence_root(env={})
    except OwnerRunEvidenceRootError:
        pass
    else:
        raise AssertionError("expected OwnerRunEvidenceRootError")
