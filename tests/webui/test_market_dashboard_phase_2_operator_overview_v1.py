"""Phase 2 Operator Overview: decision sentence, activity states, consumer-only safety."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
)
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT as OHLCV_ENV_BUNDLE_ROOT,
    ENV_ENABLED as OHLCV_ENV_ENABLED,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
)
from src.webui.market_visual_operator_surface_v1 import ENV_EVIDENCE_ROOT
from src.webui.market_visual_operator_surface_v1.operator_overview_display_v1 import (
    build_operator_overview_display_v1,
)

RANKING_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "complete_minimal"
).resolve()
OHLCV_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_futures_ohlcv_readmodel_v0" / "complete_minimal"
).resolve()
F5_FIXTURE = (
    project_root
    / "tests"
    / "fixtures"
    / "futures_read_only_market_dashboard_v0"
    / "complete_minimal"
).resolve()


@pytest.fixture()
def client_phase_2(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    evidence = tmp_path / "economic_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "compact_decision_funnel.json").write_text(
        '{"bar_count": 0, "trade_count": 0, "stages": {}}', encoding="utf-8"
    )
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2030-01-15T12:34:56.000000+00:00")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    monkeypatch.setenv(ENV_EVIDENCE_ROOT, str(evidence))
    monkeypatch.setattr(
        "src.data.kraken.fetch_ohlcv_df",
        MagicMock(side_effect=AssertionError("no request-time kraken")),
    )
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient) -> str:
    resp = client.get("/market?timeframe=1h")
    assert resp.status_code == 200
    return resp.text


def test_decision_sentence_contract_unit() -> None:
    vm = build_operator_overview_display_v1(
        primary_values={"symbol": "AAAUSDT", "timeframe": "1h", "last_close_display": "1.0"},
        selected_instrument_workspace={
            "symbol": "AAAUSDT",
            "ranking_rank": 3,
            "ranking_regime": "unavailable",
            "ranking_score_display": "0.5",
            "data_quality_status": "ok",
            "contract_metadata": {"exchange": "okx", "contract_type": "swap"},
        },
        visual_operator_header={
            "ai_activity_state": "ACTIVE",
            "economic_gate_status": "FAIL",
            "runtime_authority": "NONE",
            "data_freshness": "2030-01-01T00:00:00Z",
        },
        decision_funnel_visual={"most_frequent_block_reasons": []},
        safety_matrix={"preflight_blocked": True, "rows": []},
        ai_activity_state="ACTIVE",
        governed_top20={"rows": [{"symbol": "AAAUSDT", "regime": "unavailable"}]},
    )
    sentence = vm["decision_sentence"]
    assert "AAAUSDT" in sentence
    assert "ranked #3" in sentence
    assert "Regime unavailable" in sentence
    assert "Decision Blocked" in sentence
    assert "Primary blocker: Preflight blocked" in sentence
    assert vm["current_decision"]["ai_activity_state"] == "PROCESSED"
    assert vm["current_decision"]["ai_activity_state_raw"] == "ACTIVE"
    assert "ACTIVE" not in sentence
    assert vm["critical_system_state"]["orders"] == "ORDERS_DISABLED"
    assert vm["critical_system_state"]["live"] == "LIVE_DISABLED"


def test_phase_2_markers_and_sentence_in_html(client_phase_2: TestClient) -> None:
    body = _html(client_phase_2)
    assert 'data-market-phase-2-operator-overview-v1="true"' in body
    assert 'data-market-phase-2-decision-sentence-v1="true"' in body
    assert 'data-market-phase-2-critical-system-state-v1="true"' in body
    assert 'data-market-operator-decision-narrative-v1="true"' in body
    assert "is ranked #" in body
    assert "Primary blocker:" in body
    assert "Preflight blocked · Authority NONE" not in body
    assert "AI ACTIVE" not in body
    assert (
        re.search(r"data-market-phase-2-ai-activity-v1=\"true\"[^>]*>\s*ACTIVE\s*<", body) is None
    )


def test_phase_2_preserves_phase_1a_dom_order(client_phase_2: TestClient) -> None:
    body = re.sub(r"<style>.*?</style>", "", _html(client_phase_2), flags=re.S)
    header_i = body.find('data-market-phase-1a-global-header-v1="true"')
    rail_i = body.find('data-market-phase-1a-single-safety-rail-v1="true"')
    hero_i = body.find('data-market-phase-1a-hero-compact-v1="true"')
    chart_i = body.find('data-market-phase-1a-chart-above-fold-v1="true"')
    assert min(header_i, rail_i, hero_i, chart_i) >= 0
    assert header_i < rail_i < hero_i < chart_i


def test_phase_2_consumer_only_no_semantics_mutation(client_phase_2: TestClient) -> None:
    body = _html(client_phase_2)
    assert 'data-market-trading-authority-v1="false"' in body
    assert "LIVE_AUTHORIZED_NOW=true" not in body
    assert "ORDERS_ALLOWED=true" not in body
    assert re.search(r'type=["\']submit["\']', body, re.I) is None
    assert "cdn.tailwindcss.com" not in body
    assert "cdn.jsdelivr.net" not in body


def test_phase_2_scope_markers_present(client_phase_2: TestClient) -> None:
    body = _html(client_phase_2)
    assert "data-market-phase-2-blocker-scope-v1=" in body
    assert "data-market-phase-2-regime-scope-v1=" in body
    assert "ORDERS_DISABLED" in body
    assert "LIVE_DISABLED" in body


def test_activity_state_distinctions_unit() -> None:
    base_ws = {
        "symbol": "AAAUSDT",
        "ranking_rank": 1,
        "ranking_regime": "unavailable",
        "ranking_score_display": "0.1",
        "data_quality_status": "ok",
        "contract_metadata": {"exchange": "okx", "contract_type": "swap"},
    }
    header = {
        "ai_activity_state": "AVAILABLE_NOT_RUN",
        "economic_gate_status": "FAIL",
        "runtime_authority": "NONE",
        "data_freshness": "2030-01-01T00:00:00Z",
    }
    processed = build_operator_overview_display_v1(
        primary_values={"symbol": "AAAUSDT", "timeframe": "1h"},
        selected_instrument_workspace=base_ws,
        visual_operator_header=header,
        decision_funnel_visual={"most_frequent_block_reasons": []},
        safety_matrix={"preflight_blocked": False, "rows": []},
        ai_activity_state="ACTIVE",
    )
    assert processed["current_decision"]["ai_activity_state"] == "PROCESSED"
    assert processed["current_decision"]["ai_activity_state_raw"] == "ACTIVE"

    not_run = build_operator_overview_display_v1(
        primary_values={"symbol": "AAAUSDT", "timeframe": "1h"},
        selected_instrument_workspace=base_ws,
        visual_operator_header=header,
        decision_funnel_visual={"most_frequent_block_reasons": []},
        safety_matrix={"preflight_blocked": False, "rows": []},
        ai_activity_state="AVAILABLE_NOT_RUN",
    )
    assert not_run["current_decision"]["ai_activity_state"] == "AVAILABLE_NOT_RUN"
    assert not_run["current_decision"]["ai_activity_state"] != "PROCESSED"

    blocked = build_operator_overview_display_v1(
        primary_values={"symbol": "AAAUSDT", "timeframe": "1h"},
        selected_instrument_workspace=base_ws,
        visual_operator_header=header,
        decision_funnel_visual={
            "most_frequent_block_reasons": [{"label": "Rank gate"}],
            "stages": [],
        },
        safety_matrix={"preflight_blocked": False, "rows": []},
        ai_activity_state="BLOCKED",
    )
    assert blocked["current_decision"]["ai_activity_state"] == "BLOCKED"
    assert blocked["current_decision"]["state"] == "Blocked"
    assert blocked["current_decision"]["ai_activity_state"] != "FAILED"

    stale = build_operator_overview_display_v1(
        primary_values={"symbol": "AAAUSDT", "timeframe": "1h"},
        selected_instrument_workspace=base_ws,
        visual_operator_header=header,
        decision_funnel_visual={"most_frequent_block_reasons": []},
        safety_matrix={"preflight_blocked": False, "rows": []},
        ai_activity_state="STALE",
    )
    assert stale["current_decision"]["ai_activity_state"] == "STALE"
    assert stale["current_decision"]["ai_activity_state"] != "NOT_AVAILABLE"


def test_operator_overview_adapter_is_presentation_only() -> None:
    src = (
        project_root
        / "src"
        / "webui"
        / "market_visual_operator_surface_v1"
        / "operator_overview_display_v1.py"
    ).read_text(encoding="utf-8")
    assert "presentation-only" in src
    assert "No trading/decision/risk/economic/authority semantics" in src
    # Narrow adapter must not call venues / credentials
    assert "fetch_ohlcv" not in src
    assert "kraken" not in src.lower()
    assert "api_key" not in src.lower()
