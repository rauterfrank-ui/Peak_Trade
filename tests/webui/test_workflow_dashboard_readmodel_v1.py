"""Unit tests for workflow_dashboard_readmodel.v1 builder."""

from __future__ import annotations

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
    project_root / "tests" / "fixtures" / "workflow_dashboard_readmodel_v1" / "pipeline_minimal" / "archive_root"
).resolve()


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
