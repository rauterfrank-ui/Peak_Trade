"""Tests for universe_selection_reader_v1 (Slice 3 — read-only, no runtime)."""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp, verify_manifest_sha256
from scripts.ops.primary_evidence_retention_v0 import (
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    LOAD_ERROR_CONTRACT_INVALID,
    LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH,
    LOAD_ERROR_INVALID_JSON,
    LOAD_ERROR_MANIFEST_NOT_FOUND,
    LOAD_ERROR_MANIFEST_VERIFY_FAILED,
    LOAD_ERROR_NOT_CVC_PROJECTION,
    LOAD_ERROR_PROJECTION_NOT_CVC_ONLY,
    LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH,
    LOAD_ERROR_SELECTED_FUTURE_PERSISTED_NOT_PROJECTION,
    PROJECTION_COVERAGE_LOAD_MODE,
    try_load_universe_selection_for_dashboard,
    try_load_universe_selection_projection_coverage_for_dashboard,
)

SCRATCH_ROOT = project_root / "tests" / "_durable_archive_scratch"
FIXTURES_ROOT = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "universe_selection_readmodel_v1"
)


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(candidate):
        return candidate
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    durable = SCRATCH_ROOT / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


def _install_fixture(archive_root: Path, fixture_dir: str, *, write_manifest: bool = True) -> Path:
    src = FIXTURES_ROOT / fixture_dir / "universe_selection_readmodel.v1.json"
    readmodels_dir = archive_root / "readmodels"
    readmodels_dir.mkdir(parents=True, exist_ok=True)
    dest = readmodels_dir / "universe_selection_readmodel.v1.json"
    shutil.copy2(src, dest)
    if write_manifest:
        _write_manifest_sha256(readmodels_dir)
    return dest


def _install_cvc_projection_fixture(
    archive_root: Path,
    *,
    write_manifest: bool = True,
) -> Path:
    path = _install_fixture(archive_root, "complete_minimal", write_manifest=False)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["fixture_marked"] = False
    payload["real_metadata_source_marked"] = True
    payload["observability_truth_allowed"] = False
    payload["non_authorizing"] = True
    payload["selected_future"] = {"truth_status": "NOT_PERSISTED"}
    payload["missing_truth"]["selected_future"] = "SELECTED_FUTURE_NOT_PERSISTED"
    payload["missing_truth"]["future_detail"] = "FUTURE_DETAIL_NOT_AVAILABLE"
    payload["market_snapshot"] = {
        "truth_status": "NOT_PERSISTED",
        "source_kind": "NOT_PERSISTED",
        "snapshot_id": None,
        "exchange": None,
        "captured_at": None,
    }
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
        payload["evidence"] = evidence
    evidence["candidate_validation_projection"] = True
    evidence["projection_source"] = "candidate_validation_bridge"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if write_manifest:
        _write_manifest_sha256(path.parent)
    return path


def test_no_file_missing_truth_fallback(archive_root: Path) -> None:
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == ()
    assert result.universe == ()


def test_missing_manifest_fallback(archive_root: Path) -> None:
    _install_fixture(archive_root, "complete_minimal", write_manifest=False)
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_MANIFEST_NOT_FOUND,)


def test_manifest_verify_fail_fallback(archive_root: Path) -> None:
    path = _install_fixture(archive_root, "complete_minimal")
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_MANIFEST_VERIFY_FAILED,)


def test_invalid_json_fallback(archive_root: Path) -> None:
    readmodels_dir = archive_root / "readmodels"
    readmodels_dir.mkdir(parents=True)
    bad = readmodels_dir / "universe_selection_readmodel.v1.json"
    bad.write_text("{not-json", encoding="utf-8")
    _write_manifest_sha256(readmodels_dir)
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_INVALID_JSON,)


def test_invalid_btc_selected_fallback(archive_root: Path) -> None:
    _install_fixture(archive_root, "invalid_btc_usd_selected")
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_CONTRACT_INVALID,)
    assert "BTC/USD" not in str(result)


def test_valid_complete_minimal_fixture_marked_not_ssr_truth(archive_root: Path) -> None:
    _install_fixture(archive_root, "complete_minimal")
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH,)
    assert result.universe == ()
    assert result.selected_future is None
    ok, _ = verify_manifest_sha256(archive_root / "readmodels")
    assert ok


def test_reader_performs_no_writes(archive_root: Path) -> None:
    _install_fixture(archive_root, "complete_minimal")
    readmodels_dir = archive_root / "readmodels"
    before = {p.name: p.stat().st_mtime_ns for p in readmodels_dir.iterdir()}
    try_load_universe_selection_for_dashboard(archive_root)
    after = {p.name: p.stat().st_mtime_ns for p in readmodels_dir.iterdir()}
    assert before == after


def test_invalid_json_without_manifest_tamper(archive_root: Path) -> None:
    readmodels_dir = archive_root / "readmodels"
    readmodels_dir.mkdir(parents=True)
    bad = readmodels_dir / "universe_selection_readmodel.v1.json"
    bad.write_text("{not-json", encoding="utf-8")
    (readmodels_dir / "MANIFEST.sha256").write_text(
        f"{bad.name}  deadbeef\n",
        encoding="utf-8",
    )
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_MANIFEST_VERIFY_FAILED,)


def test_contract_invalid_after_valid_manifest(archive_root: Path) -> None:
    path = _install_fixture(archive_root, "complete_minimal")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = 999
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    _write_manifest_sha256(path.parent)
    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_CONTRACT_INVALID,)


def test_real_metadata_marked_without_observability_truth_not_ssr_truth(
    archive_root: Path,
) -> None:
    path = _install_fixture(archive_root, "complete_minimal")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["fixture_marked"] = False
    payload["real_metadata_source_marked"] = True
    payload["observability_truth_allowed"] = False
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_manifest_sha256(path.parent)

    result = try_load_universe_selection_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH,)
    assert result.universe == ()
    assert result.selected_future is None
    assert "BTC/USD" not in str(result)


def test_truth_reader_rejects_cvc_while_projection_reader_accepts(
    archive_root: Path,
) -> None:
    _install_cvc_projection_fixture(archive_root)
    truth = try_load_universe_selection_for_dashboard(archive_root)
    projection = try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    assert truth.loaded is False
    assert truth.load_errors == (LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH,)
    assert projection.loaded is True
    assert projection.load_mode == PROJECTION_COVERAGE_LOAD_MODE
    assert len(projection.universe) == 3
    assert len(projection.ranking) == 2
    assert projection.selected_future is None


def test_projection_reader_accepts_cvc_payload(archive_root: Path) -> None:
    _install_cvc_projection_fixture(archive_root)
    result = try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    assert result.loaded is True
    assert result.load_mode == PROJECTION_COVERAGE_LOAD_MODE
    assert result.load_errors == ()
    assert result.selected_future is None


def test_projection_reader_rejects_observability_truth_allowed(archive_root: Path) -> None:
    path = _install_cvc_projection_fixture(archive_root, write_manifest=False)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["observability_truth_allowed"] = True
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_manifest_sha256(path.parent)
    result = try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_PROJECTION_NOT_CVC_ONLY,)


def test_projection_reader_rejects_selected_future_persisted(archive_root: Path) -> None:
    path = _install_cvc_projection_fixture(archive_root, write_manifest=False)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["selected_future"] = {
        "row_id": "s-sol",
        "symbol": "SOLUSDT",
        "rank": 1,
        "truth_status": "PERSISTED",
        "selection_reason": "fixture_top_ranked_candidate",
    }
    payload["missing_truth"]["selected_future"] = "PERSISTED"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_manifest_sha256(path.parent)
    result = try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_SELECTED_FUTURE_PERSISTED_NOT_PROJECTION,)


def test_projection_reader_rejects_missing_candidate_validation_flag(
    archive_root: Path,
) -> None:
    path = _install_cvc_projection_fixture(archive_root, write_manifest=False)
    payload = json.loads(path.read_text(encoding="utf-8"))
    evidence = payload["evidence"]
    del evidence["candidate_validation_projection"]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_manifest_sha256(path.parent)
    result = try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_NOT_CVC_PROJECTION,)


def test_projection_reader_rejects_missing_manifest(archive_root: Path) -> None:
    _install_cvc_projection_fixture(archive_root, write_manifest=False)
    result = try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_MANIFEST_NOT_FOUND,)


def test_projection_reader_rejects_manifest_tamper(archive_root: Path) -> None:
    path = _install_cvc_projection_fixture(archive_root)
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    assert result.loaded is False
    assert result.load_errors == (LOAD_ERROR_MANIFEST_VERIFY_FAILED,)


def test_projection_reader_performs_no_writes(archive_root: Path) -> None:
    _install_cvc_projection_fixture(archive_root)
    readmodels_dir = archive_root / "readmodels"
    before = {p.name: p.stat().st_mtime_ns for p in readmodels_dir.iterdir()}
    try_load_universe_selection_projection_coverage_for_dashboard(archive_root)
    after = {p.name: p.stat().st_mtime_ns for p in readmodels_dir.iterdir()}
    assert before == after
