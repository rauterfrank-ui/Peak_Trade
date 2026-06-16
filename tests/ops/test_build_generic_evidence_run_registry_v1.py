"""Tests for offline generic evidence run registry v1 builder."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
REAL_ARCHIVE = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")

SAFE_GOVERNANCE = "\n".join(
    [
        "GO_DECISION_GRANTED=false",
        "HOLD_NO_PAPER_RUN_CLEARED=false",
        "GLB_014_CLEARED=false",
        "GLB_015_CLEARED=false",
        "PREFLIGHT_READY=false",
        "LIVE_ALLOWED=false",
        "BROKER_EXCHANGE_ALLOWED=false",
        "SECRET_VALUES_INCLUDED=false",
    ]
)


def _load_module():
    spec = importlib.util.spec_from_file_location("build_generic_evidence_run_registry_v1", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_generic_evidence_run_registry_v1"] = mod
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


def _write_run(
    archive: Path,
    lane: str,
    run_id: str,
    *,
    review_verdict: str | None = None,
    extra_text: str = "",
    write_manifest: bool = True,
) -> Path:
    run_dir = archive / "runs" / lane / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    content = f"{lane}:{run_id}\n"
    if extra_text:
        content += extra_text + "\n"
    (run_dir / "evidence.txt").write_text(content, encoding="utf-8")
    if review_verdict is not None:
        _write_review(run_dir, review_verdict)
    if write_manifest:
        _write_manifest(run_dir)
    return run_dir


def _complete_archive(root: Path) -> None:
    _write_run(root, "paper", "paper_run", review_verdict=None)
    _write_run(root, "shadow", "shadow_run", review_verdict="PASS")
    _write_run(root, "testnet", "testnet_run", review_verdict="PASS")
    planning = root / "planning" / "governance_fixture_v0"
    planning.mkdir(parents=True, exist_ok=True)
    (planning / "GOVERNANCE.md").write_text(SAFE_GOVERNANCE + "\n", encoding="utf-8")
    _write_manifest(planning)


def _build(mod, archive: Path, *, fixed: str = "2026-05-21T00:00:00Z") -> dict:
    ctx = mod.BuildContext(
        archive_root=archive,
        repo_root=ROOT,
        fixed_generated_at_utc=fixed,
    )
    return mod.build_registry(ctx)


@pytest.fixture
def mod():
    return _load_module()


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_schema_constant(mod) -> None:
    assert mod.SCHEMA == "peak_trade.generic_evidence_run_registry.v1"


def test_help_works() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--archive-root" in proc.stdout


def test_complete_fixture_pass_blocked_safe(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _complete_archive(root)
    payload = _build(mod, root)
    assert payload["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert payload["verdict"] == mod.VERDICT_PASS_BLOCKED_SAFE
    assert payload["summaries"]["total_runs"] == 3
    assert payload["authority"]["live_allowed"] is False
    assert payload["authority"]["scheduler_boundary_gap_acknowledged"] is True
    assert payload["blockers"]
    lane_ids = {r["lane_id"] for r in payload["runs"]}
    assert lane_ids == {"paper", "shadow", "testnet"}


def test_missing_manifest_review_required(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(root, "paper", "paper_run", write_manifest=False)
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_REVIEW_REQUIRED
    codes = {i["code"] for i in payload["issues"]}
    assert "MISSING_MANIFEST" in codes


def test_manifest_hash_mismatch_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    run_dir = _write_run(root, "paper", "paper_run")
    (run_dir / "MANIFEST.sha256").write_text("deadbeef  evidence.txt\n", encoding="utf-8")
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    assert any(i["code"] == "MANIFEST_HASH_MISMATCH" for i in payload["issues"])


def test_shadow_review_missing_review_required(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(root, "shadow", "shadow_run", review_verdict=None)
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_REVIEW_REQUIRED
    assert any(i["code"] == "MISSING_REVIEW_JSON" for i in payload["issues"])


def test_shadow_review_not_pass_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(root, "shadow", "shadow_run", review_verdict="FAIL")
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    assert any(i["code"] == "REVIEW_VERDICT_NOT_PASS" for i in payload["issues"])


def test_testnet_review_missing_review_required(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(root, "testnet", "testnet_run", review_verdict=None)
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_REVIEW_REQUIRED


def test_testnet_review_not_pass_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(root, "testnet", "testnet_run", review_verdict="REVIEW_REQUIRED")
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED


def test_scheduler_runtime_allowed_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(
        root,
        "scheduler",
        "sched_run",
        extra_text="RUNTIME_ALLOWED_BY_DEFAULT=true",
    )
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    assert any(i["code"] == "UNSAFE_SCHEDULER_RUNTIME_DEFAULT" for i in payload["issues"])


def test_testnet_can_authorize_live_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(
        root,
        "testnet",
        "testnet_run",
        review_verdict="PASS",
        extra_text="CAN_AUTHORIZE_LIVE=true",
    )
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    assert any(i["code"] == "UNSAFE_LIVE_AUTHORITY" for i in payload["issues"])


def test_dashboard_lane_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(root, "dashboard", "dash_run")
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    assert any(i["code"] == "UNSAFE_NON_RUN_SURFACE_AUTHORITY" for i in payload["issues"])


def test_live_production_without_record_review_required(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _write_run(root, "live_production", "live_run")
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_REVIEW_REQUIRED
    assert any(i["code"] == "MISSING_EXTERNAL_LIVE_RECORD" for i in payload["issues"])


def test_secret_values_included_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _complete_archive(root)
    planning = root / "planning" / "governance_fixture_v0" / "GOVERNANCE.md"
    planning.write_text(SAFE_GOVERNANCE + "\nSECRET_VALUES_INCLUDED=true\n", encoding="utf-8")
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED
    assert any(i["code"] == "UNSAFE_SECRET_VALUES_INCLUDED" for i in payload["issues"])


def test_go_decision_granted_fail_closed(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _complete_archive(root)
    planning = root / "planning" / "governance_fixture_v0" / "GOVERNANCE.md"
    planning.write_text(SAFE_GOVERNANCE + "\nGO_DECISION_GRANTED=true\n", encoding="utf-8")
    payload = _build(mod, root)
    assert payload["verdict"] == mod.VERDICT_FAIL_CLOSED


def test_deterministic_timestamp(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _complete_archive(root)
    payload = _build(mod, root, fixed="2026-05-21T00:00:00Z")
    assert payload["generated_at_utc"] == "2026-05-21T00:00:00Z"


def test_cli_json_only_stdout(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _complete_archive(root)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(
            [
                "--archive-root",
                str(root),
                "--repo-root",
                str(ROOT),
                "--fixed-generated-at-utc",
                "2026-05-21T00:00:00Z",
                "--json",
            ]
        )
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["verdict"] == mod.VERDICT_PASS_BLOCKED_SAFE


def test_per_run_registry_fields_present(mod, tmp_path: Path) -> None:
    root = tmp_path / "archive"
    _complete_archive(root)
    payload = _build(mod, root)
    required = {
        "run_id",
        "lane_id",
        "lane_kind",
        "archive_path",
        "manifest_present",
        "manifest_verified",
        "review_required",
        "review_present",
        "review_verdict",
        "durable_retention_required",
        "durable_retention_verified",
        "notion_link_allowed",
        "notion_link_present",
        "authority_level",
        "runtime_allowed_by_default",
        "requires_approval_record",
        "can_clear_hold",
        "can_clear_glb",
        "can_authorize_live",
        "can_touch_broker_exchange",
        "protected_master_v2_boundary",
        "evidence_status",
        "issues",
    }
    for run in payload["runs"]:
        assert required <= set(run.keys())
        assert run["can_authorize_live"] is False
        assert run["protected_master_v2_boundary"] is True


@pytest.mark.skipif(
    os.environ.get("PEAK_TRADE_RUN_REGISTRY_REAL_ARCHIVE") != "1",
    reason="set PEAK_TRADE_RUN_REGISTRY_REAL_ARCHIVE=1 to run real archive smoke",
)
def test_real_archive_smoke_pass_blocked_safe(mod) -> None:
    if not REAL_ARCHIVE.is_dir():
        pytest.skip("real archive not present")
    payload = _build(mod, REAL_ARCHIVE)
    assert payload["verdict"] == mod.VERDICT_PASS_BLOCKED_SAFE
    assert payload["authority"]["live_allowed"] is False
    assert payload["authority"]["broker_exchange_allowed"] is False
    assert payload["summaries"]["scheduler_boundary_gap_acknowledged"] is True
    lane_ids = {r["lane_id"] for r in payload["runs"]}
    assert {"paper", "shadow", "testnet"} <= lane_ids
