"""Unit tests for last_paper_run_panel_readmodel.v0 builder."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.webui.last_paper_run_panel_readmodel_v0 import (
    SCHEMA_VERSION,
    build_last_paper_run_panel_readmodel_v0,
    to_json_dict,
)

FIXTURES = project_root / "tests" / "fixtures" / "last_paper_run_panel_readmodel_v0"


@pytest.fixture(autouse=True)
def _fixed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T00:00:02+00:00")


def test_p1_fixture_loads_ready() -> None:
    root = FIXTURES / "p1_complete_minimal"
    m = build_last_paper_run_panel_readmodel_v0(root)
    assert m.schema_version == SCHEMA_VERSION
    assert m.load_status == "ready"
    assert m.last_run.run_id == "daemon_paper_24h_test_fixture_v0"
    assert m.last_run.job_name == "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"
    assert m.last_run.status == "PASS"
    assert m.last_run.job_accepted is True
    assert m.orders_fills.fills_count == 0


def test_p1_instrument_not_persisted() -> None:
    root = FIXTURES / "p1_complete_minimal"
    m = build_last_paper_run_panel_readmodel_v0(root)
    assert m.instrument.instrument_truth_status == "NOT_PERSISTED"
    assert m.instrument.selected_instrument is None
    assert m.instrument.selected_future is None
    assert m.instrument.selected_symbol is None


def test_no_forbidden_authority_keys() -> None:
    root = FIXTURES / "p1_complete_minimal"
    d = to_json_dict(build_last_paper_run_panel_readmodel_v0(root))
    blob = str(d).lower()
    for forbidden in ("ready_to_trade", "live_ready", "trading_authorized", "approved"):
        assert forbidden not in blob


def test_missing_run_metadata_raises() -> None:
    empty = FIXTURES / "p1_complete_minimal"
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="run_metadata_missing"):
            build_last_paper_run_panel_readmodel_v0(Path(tmp))
