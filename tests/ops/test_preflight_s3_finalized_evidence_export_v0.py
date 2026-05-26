"""Offline tests for local-only S3 finalized evidence export dry preflight CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "preflight_s3_finalized_evidence_export_v0.py"
TAXONOMY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)

BOUNDARY_BOOL_FIELDS = (
    "network_actions_called",
    "aws_cli_called",
    "rclone_called",
    "upload_called",
    "download_called",
    "mutation_called",
    "finalized_evidence_required",
    "active_staging_sync_forbidden",
    "s3_export_after_finalize_only",
    "upload_does_not_authorize_runtime",
    "notion_authority",
    "market_dashboard_authority",
    "live_authority",
    "testnet_authority",
)


def _import_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "preflight_s3_finalized_evidence_export_v0", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_eligible_root(root: Path) -> None:
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    root.mkdir(parents=True, exist_ok=True)
    (root / "scheduler_completion_closeout_v0.json").write_text("{}", encoding="utf-8")
    (root / "evidence.txt").write_text("finalized", encoding="utf-8")
    write_manifest_sha256(root)


@pytest.fixture
def mod():
    return _import_module()


@pytest.fixture
def durable_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.is_under_tmp",
        lambda _path: False,
    )
    import scripts.ops.preflight_s3_finalized_evidence_export_v0 as preflight_mod

    monkeypatch.setattr(preflight_mod, "is_under_tmp", lambda _path: False)
    root = tmp_path / "durable_evidence"
    _write_eligible_root(root)
    return root


def test_missing_dry_run_blocks(mod, durable_root: Path) -> None:
    result = mod.run_preflight(durable_root, dry_run=False, no_network=True)
    assert result["status"] == "invalid"
    assert "missing_required_flag:dry_run" in result["reasons"]


def test_missing_no_network_blocks(mod, durable_root: Path) -> None:
    result = mod.run_preflight(durable_root, dry_run=True, no_network=False)
    assert result["status"] == "invalid"
    assert "missing_required_flag:no_network" in result["reasons"]


def test_missing_evidence_root_blocks(mod, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.is_under_tmp",
        lambda _path: False,
    )
    missing = tmp_path / "missing"
    result = mod.run_preflight(missing, dry_run=True, no_network=True)
    assert result["status"] == "invalid"
    assert "evidence_root_missing" in result["reasons"]


def test_missing_manifest_blocks(mod, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.is_under_tmp",
        lambda _path: False,
    )
    root = tmp_path / "no_manifest"
    root.mkdir()
    (root / "scheduler_completion_closeout_v0.json").write_text("{}", encoding="utf-8")
    result = mod.run_preflight(root, dry_run=True, no_network=True)
    assert result["status"] == "blocked"
    assert result["manifest_present"] is False
    assert "MANIFEST.sha256 missing" in result["reasons"]


def test_bad_manifest_blocks(mod, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.primary_evidence_retention_v0.is_under_tmp",
        lambda _path: False,
    )
    root = tmp_path / "bad_manifest"
    root.mkdir()
    (root / "scheduler_completion_closeout_v0.json").write_text("{}", encoding="utf-8")
    (root / "evidence.txt").write_text("x", encoding="utf-8")
    (root / "MANIFEST.sha256").write_text("deadbeef  evidence.txt\n", encoding="utf-8")
    result = mod.run_preflight(root, dry_run=True, no_network=True)
    assert result["status"] == "blocked"
    assert result["manifest_verify_rc"] == 1


def test_valid_finalized_fixture_becomes_eligible(mod, durable_root: Path) -> None:
    result = mod.run_preflight(durable_root, dry_run=True, no_network=True)
    assert result["status"] == "eligible"
    assert result["manifest_present"] is True
    assert result["manifest_verify_rc"] == 0
    assert result["closeout_marker_present"] is True
    assert result["reasons"] == []


def test_json_contains_authority_and_network_boundary_fields(mod, durable_root: Path) -> None:
    result = mod.run_preflight(durable_root, dry_run=True, no_network=True)
    for field in BOUNDARY_BOOL_FIELDS:
        assert field in result
        if field.endswith("_authority") or field.endswith("_called"):
            assert result[field] is False
        else:
            assert result[field] is True
    assert result["schema_version"] == "peak_trade.s3_finalized_evidence_export_preflight.v0"
    assert result["preflight_name"] == "preflight_s3_finalized_evidence_export_v0"


def test_active_staging_sync_marker_blocks(mod, durable_root: Path) -> None:
    (durable_root / ".active_staging_sync").write_text("1", encoding="utf-8")
    result = mod.run_preflight(durable_root, dry_run=True, no_network=True)
    assert result["status"] == "blocked"
    assert "active_staging_sync_forbidden" in result["reasons"]


def test_cli_main_eligible_exit_zero(mod, durable_root: Path, tmp_path: Path) -> None:
    out = tmp_path / "result.json"
    rc = mod.main(
        [
            "--evidence-root",
            str(durable_root),
            "--dry-run",
            "--no-network",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "eligible"
    for field in BOUNDARY_BOOL_FIELDS:
        assert field in payload


def test_no_subprocess_network_aws_rclone_calls(mod, durable_root: Path) -> None:
    with mock.patch("subprocess.run", side_effect=AssertionError("subprocess.run called")):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("subprocess.Popen called")):
            result = mod.run_preflight(durable_root, dry_run=True, no_network=True)
    assert result["status"] == "eligible"


def test_taxonomy_references_preflight_script() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "preflight_s3_finalized_evidence_export_v0" in text
