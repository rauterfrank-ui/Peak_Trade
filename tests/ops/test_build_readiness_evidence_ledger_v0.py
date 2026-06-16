"""Tests for offline readiness evidence ledger v0 builder."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "build_readiness_evidence_ledger_v0.py"
FIXTURES = ROOT / "tests" / "fixtures" / "ops" / "readiness_evidence_ledger_v0"
REAL_ARCHIVE = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")

PLANNING_MARKERS = (
    "named_go_no_go_authority_selection_record",
    "explicit_go_no_go_decision_template",
    "production_secret_storage_mechanism_evaluation",
    "live_production_authority_boundary",
    "preflight_status_refresh_with_hold_decision_context",
    "hold_operator_global_clearance_decision_record",
    "glb014_015_operator_clearance_decision_record",
)

SAFE_GOVERNANCE_LINES = "\n".join(
    [
        "GO_DECISION_GRANTED=false",
        "NO_GO_DECISION_GRANTED=false",
        "HOLD_NO_PAPER_RUN_CLEARED=false",
        "GLB_014_CLEARED=false",
        "GLB_015_CLEARED=false",
        "PREFLIGHT_READY=false",
        "LIVE_ALLOWED=false",
        "BROKER_EXCHANGE_ALLOWED=false",
        "SECRET_VALUES_INCLUDED=false",
        "NAMED_GO_NO_GO_AUTHORITY_SELECTED=true",
    ]
)


def _load_module():
    spec = importlib.util.spec_from_file_location("build_readiness_evidence_ledger_v0", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_readiness_evidence_ledger_v0"] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(directory: Path) -> None:
    entries: list[str] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {"MANIFEST.sha256", "MANIFEST_VERIFY.log"}:
            continue
        rel = path.relative_to(directory).as_posix()
        entries.append(f"{_sha256_file(path)}  {rel}")
    (directory / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _write_review(run_dir: Path, verdict: str) -> None:
    review_dir = run_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "REVIEW_RESULT.json").write_text(
        json.dumps({"verdict": verdict, "issues": []}) + "\n",
        encoding="utf-8",
    )


def _write_run_lane(
    archive_root: Path, lane: str, run_id: str, *, review_verdict: str | None
) -> Path:
    run_dir = archive_root / "runs" / lane / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "evidence.txt").write_text(f"{lane}:{run_id}\n", encoding="utf-8")
    if review_verdict is not None:
        _write_review(run_dir, review_verdict)
    _write_manifest(run_dir)
    return run_dir


def _write_planning_surface(archive_root: Path, marker: str, extra: str = "") -> Path:
    planning_dir = archive_root / "planning" / f"{marker}_fixture_v0"
    planning_dir.mkdir(parents=True, exist_ok=True)
    content = SAFE_GOVERNANCE_LINES
    if extra:
        content += f"\n{extra}"
    (planning_dir / "RESULT.md").write_text(content + "\n", encoding="utf-8")
    _write_manifest(planning_dir)
    return planning_dir


def build_complete_archive(root: Path) -> None:
    _write_run_lane(root, "paper", "paper_run", review_verdict=None)
    _write_run_lane(root, "shadow", "shadow_run", review_verdict="PASS")
    _write_run_lane(root, "testnet", "testnet_run", review_verdict="PASS")
    for marker in PLANNING_MARKERS:
        _write_planning_surface(root, marker)


@pytest.fixture
def mod():
    return _load_module()


@pytest.fixture
def complete_archive(tmp_path: Path) -> Path:
    build_complete_archive(tmp_path)
    return tmp_path


def _build_ctx(mod, archive_root: Path, **kwargs):
    defaults = {
        "paper_run_id": "paper_run",
        "shadow_run_id": "shadow_run",
        "testnet_run_id": "testnet_run",
    }
    defaults.update(kwargs)
    return mod.BuildContext(archive_root=archive_root, **defaults)


def test_complete_fixture_returns_pass_blocked_safe(mod, complete_archive: Path) -> None:
    ctx = _build_ctx(mod, complete_archive, fixed_generated_at_utc="2026-05-21T00:00:00Z")
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_PASS_BLOCKED_SAFE
    assert ledger["evidence"]["triple_lane_primary_evidence"] is True
    assert ledger["planning"]["planning_chain_present"] is True
    assert ledger["governance"]["governance_blocked"] is True
    assert mod.BLOCKER_HOLD in ledger["blockers"]
    assert ledger["governance"]["live_allowed"] is False


def test_pass_blocked_safe_triple_lane_does_not_clear_glb015_or_preflight(
    mod, complete_archive: Path
) -> None:
    """GLB-015 semantics: PASS_BLOCKED_SAFE + triple_lane is completeness only, not approval."""
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_PASS_BLOCKED_SAFE
    assert ledger["evidence"]["triple_lane_primary_evidence"] is True
    assert ledger["governance"]["governance_blocked"] is True
    assert ledger["governance"]["preflight_ready"] is False
    assert ledger["governance"]["glb_015_cleared"] is False
    assert ledger["governance"]["go_decision_granted"] is False
    assert mod.BLOCKER_PREFLIGHT in ledger["blockers"]
    assert mod.BLOCKER_HOLD in ledger["blockers"]
    assert ledger["governance"]["hold_no_paper_run_cleared"] is False


def test_missing_paper_manifest_review_required(mod, complete_archive: Path) -> None:
    (complete_archive / "runs" / "paper" / "paper_run" / "MANIFEST.sha256").unlink()
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_REVIEW_REQUIRED
    assert ledger["evidence"]["paper_primary_evidence_verified"] is False


def test_missing_shadow_review_review_required(mod, complete_archive: Path) -> None:
    review = complete_archive / "runs" / "shadow" / "shadow_run" / "review" / "REVIEW_RESULT.json"
    review.unlink()
    _write_manifest(complete_archive / "runs" / "shadow" / "shadow_run")
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_REVIEW_REQUIRED
    assert any(i["code"] == "MISSING_REVIEW_JSON" for i in ledger["issues"])


def test_shadow_review_not_pass_fail_closed(mod, complete_archive: Path) -> None:
    _write_review(complete_archive / "runs" / "shadow" / "shadow_run", "FAIL")
    _write_manifest(complete_archive / "runs" / "shadow" / "shadow_run")
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_FAIL_CLOSED


def test_missing_testnet_review_review_required(mod, complete_archive: Path) -> None:
    review = complete_archive / "runs" / "testnet" / "testnet_run" / "review" / "REVIEW_RESULT.json"
    review.unlink()
    _write_manifest(complete_archive / "runs" / "testnet" / "testnet_run")
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_REVIEW_REQUIRED


def test_testnet_review_not_pass_fail_closed(mod, complete_archive: Path) -> None:
    _write_review(complete_archive / "runs" / "testnet" / "testnet_run", "REVIEW_REQUIRED")
    _write_manifest(complete_archive / "runs" / "testnet" / "testnet_run")
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_FAIL_CLOSED


def test_live_allowed_true_fail_closed(mod, complete_archive: Path) -> None:
    _write_planning_surface(
        complete_archive,
        "unsafe_live_marker",
        extra="LIVE_ALLOWED=true",
    )
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_FAIL_CLOSED
    assert any(i["code"] == "UNSAFE_LIVE_ALLOWED" for i in ledger["issues"])


def test_secret_values_included_fail_closed(mod, complete_archive: Path) -> None:
    _write_planning_surface(
        complete_archive,
        "unsafe_secret_marker",
        extra="SECRET_VALUES_INCLUDED=true",
    )
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_FAIL_CLOSED


def test_go_decision_granted_true_fail_closed(mod, complete_archive: Path) -> None:
    _write_planning_surface(
        complete_archive,
        "unsafe_go_marker",
        extra="GO_DECISION_GRANTED=true",
    )
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_FAIL_CLOSED


def test_missing_named_authority_review_required(mod, complete_archive: Path) -> None:
    marker_dir = (
        complete_archive / "planning" / "named_go_no_go_authority_selection_record_fixture_v0"
    )
    import shutil

    shutil.rmtree(marker_dir)
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["verdict"] == mod.VERDICT_REVIEW_REQUIRED
    assert ledger["planning"]["planning_chain_present"] is False
    assert any(i["code"] == "MISSING_PLANNING_SURFACE" for i in ledger["issues"])


def test_json_schema_stable(mod, complete_archive: Path) -> None:
    ctx = _build_ctx(mod, complete_archive, fixed_generated_at_utc="2026-05-21T00:00:00Z")
    ledger = mod.build_ledger(ctx)
    assert set(ledger) == {
        "schema",
        "generated_at_utc",
        "archive_root",
        "evidence",
        "planning",
        "governance",
        "blockers",
        "verdict",
        "issues",
    }
    assert ledger["schema"] == mod.SCHEMA


def test_cli_json_works(complete_archive: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--archive-root",
            str(complete_archive),
            "--paper-run-id",
            "paper_run",
            "--shadow-run-id",
            "shadow_run",
            "--testnet-run-id",
            "testnet_run",
            "--fixed-generated-at-utc",
            "2026-05-21T00:00:00Z",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE"


def test_deterministic_generated_at_via_env(mod, complete_archive: Path, monkeypatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-05-21T12:34:56Z")
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["generated_at_utc"] == "2026-05-21T12:34:56Z"


def test_blockers_sorted(mod, complete_archive: Path) -> None:
    ctx = _build_ctx(mod, complete_archive)
    ledger = mod.build_ledger(ctx)
    assert ledger["blockers"] == sorted(ledger["blockers"])


def test_no_subprocess_or_network_in_build(mod, complete_archive: Path, monkeypatch) -> None:
    def _blocked(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("subprocess usage is forbidden in ledger build")

    monkeypatch.setattr(subprocess, "run", _blocked)
    monkeypatch.setattr(subprocess, "Popen", _blocked)
    ctx = _build_ctx(mod, complete_archive)
    mod.build_ledger(ctx)


@pytest.mark.skipif(not REAL_ARCHIVE.is_dir(), reason="operator archive not present")
def test_real_archive_smoke_pass_blocked_safe() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--archive-root",
            str(REAL_ARCHIVE),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE"
    assert payload["evidence"]["triple_lane_primary_evidence"] is True
    assert payload["governance"]["live_allowed"] is False
    assert payload["governance"]["secret_values_included"] is False


def test_fixtures_dir_exists() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    assert FIXTURES.is_dir()
