"""Market dashboard STEP29M current-state sync contract (view-only, SSR)."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.market_dashboard_current_state_snapshot_v0 import (
    NEXT_CANONICAL_STEP,
    SNAPSHOT_OWNER,
    market_dashboard_current_state_snapshot_v0,
)
from src.webui.market_surface import (
    CANONICAL_CURRENT_STATE_RUNTIME_OWNER,
    CANONICAL_CURRENT_STATE_SNAPSHOT_OWNER,
    CANONICAL_CURRENT_STATE_TEMPLATE_OWNER,
    CANONICAL_MARKET_ROUTE,
    PAGE_TITLE,
)

FORM_ACTION_RE = re.compile(
    r"<form\b[^>]*\baction\s*=\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)
POST_METHOD_RE = re.compile(r"<form\b[^>]*\bmethod\s*=\s*[\"']post[\"']", re.IGNORECASE)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def client_ranking_funnel_fixture_bundle_on(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", "1")
    bundle = (
        project_root
        / "tests"
        / "fixtures"
        / "market_ranking_funnel_readmodel_v0"
        / "complete_minimal"
    ).resolve()
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", str(bundle))
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str = "/market") -> str:
    response = client.get(path)
    assert response.status_code == 200
    return response.text


def test_market_route_and_title_unchanged(client: TestClient) -> None:
    html = _html(client)
    assert CANONICAL_MARKET_ROUTE == "/market"
    assert f"<title>{PAGE_TITLE}</title>" in html or PAGE_TITLE in html
    assert 'data-market-page-title-v1="true"' in html
    assert PAGE_TITLE in html


def test_single_current_state_ssot_owner() -> None:
    snapshot = market_dashboard_current_state_snapshot_v0()
    assert snapshot["snapshot_owner"] == SNAPSHOT_OWNER
    assert CANONICAL_CURRENT_STATE_SNAPSHOT_OWNER == SNAPSHOT_OWNER
    assert CANONICAL_CURRENT_STATE_RUNTIME_OWNER.endswith(
        "market_dashboard_current_state_runtime_v0.py"
    )
    assert CANONICAL_CURRENT_STATE_TEMPLATE_OWNER.endswith("market_current_state_compact_v1.html")


def test_current_system_state_snapshot_values() -> None:
    system = market_dashboard_current_state_snapshot_v0()["current_system_state"]
    assert system["CURRENT_ORIGIN_MAIN"] == "f37f20008bfaee613f8d7e5005acd80da62db78e"
    assert system["STEP29M_EXECUTION_COMPLETE"] is True
    assert system["ECONOMIC_VALIDITY_OBJECTIVE_ACHIEVED"] is False
    assert system["CURRENT_FLEET_ECONOMIC_VALIDITY_PASS"] is False
    assert system["AUTHORIZED_PENDING_EVALUATION_COUNT"] == 1
    assert system["NEXT_EVALUATION_STRATEGY_ID"] == "ma_crossover"
    assert system["NEXT_EVALUATION_CONFIG_STATUS"] == "AUTHORIZED_PENDING_EVALUATION"
    assert system["STEP29N_AUTHORIZED"] is False
    assert system["STEP29R_AUTHORIZED"] is False
    assert system["PROMOTION_ALLOWED"] is False
    assert system["RUNTIME_AUTHORIZED"] is False
    assert system["PROFITABILITY_CLAIM_ALLOWED"] is False
    assert system["NEXT_CANONICAL_STEP"] == NEXT_CANONICAL_STEP


def test_strategy_fleet_snapshot(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-strategy-fleet-compact-v1="true"' in html
    assert 'data-market-fleet-strategy-id="macd"' in html
    assert 'data-market-fleet-status="TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"' in html
    assert 'data-market-fleet-strategy-id="breakout_donchian"' in html
    assert 'data-market-fleet-strategy-id="ma_crossover"' in html
    assert 'data-market-fleet-status="AUTHORIZED_PENDING_EVALUATION"' in html
    assert "POLICY_RATIFIED" in html
    assert "ECONOMIC_EVALUATION_EXECUTED=false" in html


def test_ma_crossover_fixed_config_display(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-ma-crossover-config-v1="true"' in html
    assert "fast/slow" in html.lower() or "20/50" in html
    assert "inst-eth-usdt-perp" in html
    assert "REJECT_OVERSIZE" in html
    assert "0.005" in html
    assert "0.025" in html
    assert "0.25" in html
    lowered = html.lower()
    assert "profitable" not in lowered
    assert "performance pass" not in lowered


def test_next_canonical_step_exact(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-next-canonical-step-v1="true"' in html
    assert NEXT_CANONICAL_STEP in html
    assert "PREFLIGHT_ONLY=true" in html
    assert "ECONOMIC_EVALUATION_AUTHORIZED=false" in html
    assert "PRODUCTIVE_RUNNER_INVOCATIONS=0" in html


def test_governance_safety_flags_visible(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-governance-safety-compact-v1="true"' in html
    assert "FUTURES_ONLY" in html
    assert "COIN_DIRECTION_ALLOWED=false" in html
    assert "SPOT_ALLOWED=false" in html
    assert "SYNTHETIC_SPOT_ALLOWED=false" in html
    assert "MAX_POSITIONS=1" in html
    assert "MAX_ACTIVE_DIRECTIONAL_SIDE=1" in html


def test_authority_flags_remain_false(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-promotion-allowed-v1="true">false' in html
    assert 'data-market-runtime-authorized-v1="true">false' in html
    assert 'data-market-economic-validity-pass-v1="true">false' in html
    assert 'data-market-authorized-pending-count-v1="true">1' in html
    assert 'data-market-trading-authority-v1="false"' in html


def test_no_post_or_order_controls(client: TestClient) -> None:
    html = _html(client)
    assert not POST_METHOD_RE.search(html)
    for match in FORM_ACTION_RE.finditer(html):
        action = match.group(1).strip().lower()
        assert action in {"", "#", "javascript:void(0)"}
    lowered = html.lower()
    assert "place order" not in lowered
    assert "arm runtime" not in lowered
    assert "start backtest" not in lowered


def test_evidence_integrity_secondary_not_dominant_alarm(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-evidence-primary-v1="true"' in html
    assert "Notion sync MANIFEST_VERIFY_RC=0" in html
    assert 'data-market-diagnostics-evidence-integrity-v1="true"' in html
    assert 'data-market-ratification-manifest-drift-v1="true"' in html
    assert "REPORT.md hash drift" in html
    assert "not a current system fault" in html


def test_historical_stale_states_not_primary(client: TestClient) -> None:
    html = _html(client)
    lowered = html.lower()
    assert "fleet fully exhausted" not in lowered
    assert "operator decision still open" not in lowered
    assert "policy selection" not in lowered
    assert "economic validity pass achieved" not in lowered


def test_existing_market_surfaces_remain_rendered(
    client_ranking_funnel_fixture_bundle_on: TestClient,
) -> None:
    html = _html(client_ranking_funnel_fixture_bundle_on)
    assert 'data-market-governed-top20-primary-slot-v1="true"' in html
    assert 'data-market-chart-primary-v1="true"' in html
    assert 'data-market-double-play-visual-grid-v1="true"' in html
    assert 'data-market-safety-rail-compact-v1="true"' in html
    assert 'data-market-watchlist-compact-v1="true"' in html or "watchlist" in html.lower()
    assert 'data-market-current-state-compact-v1="true"' in html
