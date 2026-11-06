"""Unit tests for workflow_dashboard_readmodel.v1 builder."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.webui.workflow_dashboard_readmodel_v1 import (
    SCHEMA_VERSION,
    build_workflow_dashboard_readmodel_v1,
    to_json_dict,
)

FIXTURE_ARCHIVE = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "pipeline_minimal"
    / "archive_root"
).resolve()
UNIVERSE_FIXTURES = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "universe_selection_readmodel_v1"
)


@pytest.fixture(autouse=True)
def _fixed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")


def test_fixture_loads_ready() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    assert m.schema_version == SCHEMA_VERSION
    assert m.load_status in ("ready", "ready_with_warnings")
    assert m.pipeline.stage_count == 7


def test_pipeline_stages_include_t3_planned() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    keys = [s.stage_key for s in m.pipeline.stages]
    assert keys == ["P1", "P2", "S1", "T1_ORIGINAL", "T1_REPAIR", "T2", "T3"]
    t3 = m.pipeline.stages[-1]
    assert t3.verdict == "PLANNED_PARKED"
    assert t3.bundle_basename is None


def test_t1_original_reclassified() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    t1 = next(s for s in m.pipeline.stages if s.stage_key == "T1_ORIGINAL")
    assert t1.reclassification == "RECLASSIFIED_STAGING_ONLY"
    assert t1.verdict == "PASS"


def test_missing_truth_cards() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    assert m.universe_missing.truth_status == "UNIVERSE_SOURCE_NOT_PERSISTED"
    assert m.top20_missing.truth_status == "TOP20_RANKING_NOT_PERSISTED"
    assert m.selected_future_missing.truth_status == "SELECTED_FUTURE_NOT_PERSISTED"
    assert m.future_detail_missing.truth_status == "FUTURE_DETAIL_NOT_AVAILABLE"


def test_safety_all_false() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    assert m.safety.LIVE_AUTHORIZED is False
    assert m.safety.READY_FOR_OPERATOR_ARMING is False
    assert m.safety.PREFLIGHT_LIFT is False
    assert m.safety.GAP7 is False


def test_pnl_not_persisted() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    assert m.orders_fills_pnl.pnl_status == "NOT_PERSISTED"
    assert m.orders_fills_pnl.pnl_value is None


def test_no_btc_usd_in_readmodel() -> None:
    d = to_json_dict(build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE))
    assert "BTC/USD" not in str(d)
    assert "BTCUSD" not in str(d)


def test_next_go_from_t2() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    assert m.next_go.selected_next_go_token == "GO_T3_LONGER_TESTNET_STAGE_READY_PACKAGE_NO_RUN_V1"
    assert m.next_go.execute_requires_operator_go is True


def test_archive_root_not_directory_raises() -> None:
    with pytest.raises(ValueError, match="archive_root_not_directory"):
        build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE / "nonexistent_dir_xyz")


def _copy_pipeline_archive_with_readmodel(
    tmp_path: Path, fixture_dir: str, *, fixture_marked: bool | None = None
) -> Path:
    import json

    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    archive = tmp_path / "archive_with_universe"
    shutil.copytree(FIXTURE_ARCHIVE, archive)
    readmodels_dir = archive / "readmodels"
    readmodels_dir.mkdir(parents=True, exist_ok=True)
    src = UNIVERSE_FIXTURES / fixture_dir / "universe_selection_readmodel.v1.json"
    dest = readmodels_dir / "universe_selection_readmodel.v1.json"
    if fixture_marked is None:
        shutil.copy2(src, dest)
    else:
        payload = json.loads(src.read_text(encoding="utf-8"))
        payload["fixture_marked"] = fixture_marked
        if not fixture_marked:
            payload["source_run_id"] = f"test_persisted_{fixture_dir}_non_fixture_marked"
        dest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_manifest_sha256(readmodels_dir)
    return archive


def test_valid_readmodel_populates_model_fields(tmp_path: Path) -> None:
    archive = _copy_pipeline_archive_with_readmodel(
        tmp_path, "complete_minimal", fixture_marked=False
    )
    m = build_workflow_dashboard_readmodel_v1(archive)
    assert m.universe_selection.loaded is True
    assert m.universe_missing.truth_status == "PERSISTED"
    assert m.top20_missing.truth_status == "PERSISTED"
    assert m.selected_future_missing.truth_status == "PERSISTED"
    assert m.future_detail_missing.truth_status == "AVAILABLE"
    assert len(m.universe_selection.universe) == 3
    assert m.universe_selection.selected_future is not None
    assert m.universe_selection.selected_future.symbol == "SOLUSDT"
    assert "BTC/USD" not in str(to_json_dict(m))


def test_invalid_btc_readmodel_preserves_missing_truth(tmp_path: Path) -> None:
    archive = _copy_pipeline_archive_with_readmodel(tmp_path, "invalid_btc_usd_selected")
    m = build_workflow_dashboard_readmodel_v1(archive)
    assert m.universe_selection.loaded is False
    assert m.universe_missing.truth_status == "UNIVERSE_SOURCE_NOT_PERSISTED"
    assert "CONTRACT_INVALID" in m.load_errors or "MANIFEST" in str(m.load_errors)


def _copy_pipeline_archive_with_cvc_projection(tmp_path: Path) -> Path:
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    archive = tmp_path / "archive_with_cvc_projection"
    shutil.copytree(FIXTURE_ARCHIVE, archive)
    readmodels_dir = archive / "readmodels"
    readmodels_dir.mkdir(parents=True, exist_ok=True)
    src = UNIVERSE_FIXTURES / "complete_minimal" / "universe_selection_readmodel.v1.json"
    dest = readmodels_dir / "universe_selection_readmodel.v1.json"
    payload = json.loads(src.read_text(encoding="utf-8"))
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
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_manifest_sha256(readmodels_dir)
    return archive


def test_cvc_archive_truth_panels_remain_missing_truth(tmp_path: Path) -> None:
    archive = _copy_pipeline_archive_with_cvc_projection(tmp_path)
    m = build_workflow_dashboard_readmodel_v1(archive)
    assert m.universe_selection.loaded is False
    assert m.universe_missing.truth_status == "UNIVERSE_SOURCE_NOT_PERSISTED"
    assert m.top20_missing.truth_status == "TOP20_RANKING_NOT_PERSISTED"
    assert m.selected_future_missing.truth_status == "SELECTED_FUTURE_NOT_PERSISTED"
    assert "REAL_METADATA_NOT_OBSERVABILITY_TRUTH" in m.load_errors


def test_cvc_archive_projection_coverage_card_loaded(tmp_path: Path) -> None:
    archive = _copy_pipeline_archive_with_cvc_projection(tmp_path)
    m = build_workflow_dashboard_readmodel_v1(archive)
    card = m.universe_selection_projection_coverage
    assert card.loaded is True
    assert card.load_mode == "projection_coverage"
    assert card.display_kind == "projection_coverage"
    assert card.candidate_validation is True
    assert card.non_authorizing is True
    assert card.not_truth is True
    assert card.not_selected_future is True
    assert card.strict_upstream_blocked is True
    assert card.universe_count == len(card.universe) == 3
    assert card.ranking_count == len(card.ranking) == 2
    assert m.safety.LIVE_AUTHORIZED is False
    assert m.safety.PREFLIGHT_LIFT is False


def test_to_json_dict_exports_projection_coverage_separate_from_truth(tmp_path: Path) -> None:
    archive = _copy_pipeline_archive_with_cvc_projection(tmp_path)
    d = to_json_dict(build_workflow_dashboard_readmodel_v1(archive))
    assert d["universe_selection"]["loaded"] is False
    assert d["universe_selection"]["load_mode"] is None
    proj = d["universe_selection_projection_coverage"]
    assert proj["loaded"] is True
    assert proj["load_mode"] == "projection_coverage"
    assert proj["display_kind"] == "projection_coverage"
    assert proj["candidate_validation"] is True
    assert proj["non_authorizing"] is True
    assert proj["not_truth"] is True
    assert proj["not_selected_future"] is True


def test_pipeline_minimal_fixture_projection_card_not_loaded() -> None:
    m = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    card = m.universe_selection_projection_coverage
    assert card.loaded is False
    assert card.not_truth is True
    assert card.not_selected_future is True
