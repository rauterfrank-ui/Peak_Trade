"""Market dashboard current-state sync + PR #5242 freshness contract (view-only, SSR)."""

from __future__ import annotations

import json
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
    CLOSEOUT_MANIFEST_VERIFY_RC,
    CURRENT_ORIGIN_MAIN,
    CURRENT_RESEARCH_BINDING_ID,
    CURRENT_RESEARCH_STATUS,
    CURRENT_RESEARCH_STRATEGY_ID,
    CURRENT_RESEARCH_STRATEGY_VERSION,
    CURRENT_STATE_CLOSEOUT_EVIDENCE_DIR,
    CURRENT_STATE_PRIMARY_EVIDENCE_DIR,
    CURRENT_STATE_REPAIR_EVIDENCE_DIR,
    CURRENT_STATE_RESULT_JSON,
    CURRENT_STATE_SOURCE_HEAD,
    CURRENT_STATE_SOURCE_PR,
    DOCUMENTED_ONLY_LATER_PATH,
    ECONOMIC_EVALUATION_EXECUTED,
    ECONOMIC_STATUS,
    ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
    EVIDENCE_RESULTS_REMATERIALIZED,
    LATEST_MERGED_PR_NUMBER,
    LATEST_MERGED_PR_STATE,
    LATEST_MERGED_PR_TITLE,
    NET_RETURN,
    NEXT_BLOCKER,
    NEXT_PARITY_SLICE,
    PARITY_SURFACES_COMPLETED,
    PRIMARY_SOURCE_MANIFEST_VERIFY_RC,
    SNAPSHOT_OWNER,
    SOURCE_REPAIR_MANIFEST_VERIFY_RC,
    TRADE_COUNT,
    UNCHANGED_RETRY_FORBIDDEN,
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
BITCOIN_RE = re.compile(r"\b(BTC|XBT|BITCOIN)\b", re.IGNORECASE)

PARITY_SURFACE_IDS = (
    "bull_bear_state_switch",
    "scope_adverse_exit_reversal",
    "flat_before_opposite_side",
    "survival_suitability",
    "double_play_composition",
    "entry_position_exit_policy",
)

PARITY_SURFACE_STATUSES = (
    "CLOSED_ASSESSMENT",
    "CLOSED_ASSESSMENT",
    "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
    "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
    "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
    "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
)

PR5242_SOURCE_HEAD = "0fdacfae2aa3180925a8b625267de5eb5761eccb"
CANONICAL_RESULT_JSON_REL = "config/research/full_canonical_system_economic_evidence_generation_v1_offline_execution_result_v0.json"


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


def test_freshness_pr5242_source_head_and_pr_binding() -> None:
    """Independent freshness: snapshot PR/HEAD must match frozen PR #5242 closeout identity."""
    assert CURRENT_STATE_SOURCE_PR == 5242
    assert LATEST_MERGED_PR_NUMBER == 5242
    assert CURRENT_ORIGIN_MAIN == PR5242_SOURCE_HEAD
    assert CURRENT_STATE_SOURCE_HEAD == PR5242_SOURCE_HEAD
    assert CURRENT_STATE_SOURCE_HEAD == CURRENT_ORIGIN_MAIN
    assert LATEST_MERGED_PR_STATE == "MERGED"
    assert CURRENT_STATE_RESULT_JSON == CANONICAL_RESULT_JSON_REL
    result_path = project_root / CURRENT_STATE_RESULT_JSON
    assert result_path.is_file()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["strategy_id"] == CURRENT_RESEARCH_STRATEGY_ID
    assert result["strategy_version"] == CURRENT_RESEARCH_STRATEGY_VERSION
    assert result["binding_id"] == CURRENT_RESEARCH_BINDING_ID
    assert result["status"] == CURRENT_RESEARCH_STATUS
    assert result["economic_status"] == ECONOMIC_STATUS
    assert result["economic_validity_offline_gate_pass"] is False
    assert int(result["trade_count"]) == TRADE_COUNT
    assert float(result["net_return"]) == float(NET_RETURN)
    assert result["authority_effect"] == "NONE"
    assert result["durable_evidence_dir"] == CURRENT_STATE_PRIMARY_EVIDENCE_DIR


def test_staleness_guard_pr_head_fields_do_not_diverge() -> None:
    system = market_dashboard_current_state_snapshot_v0()["current_system_state"]
    provenance = market_dashboard_current_state_snapshot_v0()["provenance"]
    assert system["CURRENT_ORIGIN_MAIN"] == CURRENT_ORIGIN_MAIN
    assert system["LATEST_MERGED_PR_NUMBER"] == LATEST_MERGED_PR_NUMBER
    assert provenance["CURRENT_STATE_SOURCE_PR"] == CURRENT_STATE_SOURCE_PR
    assert provenance["CURRENT_STATE_SOURCE_HEAD"] == CURRENT_STATE_SOURCE_HEAD
    assert system["LATEST_MERGED_PR_NUMBER"] == provenance["CURRENT_STATE_SOURCE_PR"]
    assert system["CURRENT_ORIGIN_MAIN"] == provenance["CURRENT_STATE_SOURCE_HEAD"]
    assert system["LATEST_MERGED_PR_SQUASH_COMMIT"] == system["CURRENT_ORIGIN_MAIN"]


def test_current_system_state_snapshot_values() -> None:
    system = market_dashboard_current_state_snapshot_v0()["current_system_state"]
    assert system["CURRENT_ORIGIN_MAIN"] == CURRENT_ORIGIN_MAIN
    assert system["LATEST_MERGED_PR_NUMBER"] == LATEST_MERGED_PR_NUMBER
    assert system["LATEST_MERGED_PR_TITLE"] == LATEST_MERGED_PR_TITLE
    assert system["FULL_CANONICAL_CHAIN_WIRED"] is True
    assert system["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is True
    assert system["SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE"] is False
    assert system["RUNTIME_REWIRE_ADMISSIBLE"] is False
    assert system["NEXT_BLOCKER"] == NEXT_BLOCKER
    assert system["STEP29M_EXECUTION_COMPLETE"] is True
    assert system["ECONOMIC_VALIDITY_OBJECTIVE_ACHIEVED"] is False
    assert system["CURRENT_FLEET_ECONOMIC_VALIDITY_PASS"] is False
    assert system["AUTHORIZED_PENDING_EVALUATION_COUNT"] == 0
    assert system["NEXT_EVALUATION_STRATEGY_ID"] == "NONE"
    assert system["NEXT_EVALUATION_CONFIG_STATUS"] == "NONE"
    assert system["CURRENT_RESEARCH_STRATEGY_ID"] == "bollinger_bands"
    assert system["CURRENT_RESEARCH_STRATEGY_VERSION"] == "v2"
    assert system["CURRENT_RESEARCH_STATUS"] == "COMPLETE_FAIL"
    assert system["ECONOMIC_STATUS"] == "FAIL"
    assert system["ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"] is False
    assert system["TRADE_COUNT"] == 0
    assert system["NET_RETURN"] == 0.0
    assert system["UNCHANGED_RETRY_FORBIDDEN"] is True
    assert system["POLICY_RESCUE_ALLOWED"] is False
    assert system["ECONOMIC_EVALUATION_EXECUTED"] is False
    assert system["EVIDENCE_RESULTS_REMATERIALIZED"] is False
    assert system["STEP29N_AUTHORIZED"] is False
    assert system["STEP29R_AUTHORIZED"] is False
    assert system["PROMOTION_ALLOWED"] is False
    assert system["RUNTIME_AUTHORIZED"] is False
    assert system["LIVE_AUTHORIZED"] is False
    assert system["SCHEDULER_RUNTIME_ALLOWED"] is False
    assert system["ORDERS_ALLOWED"] is False
    assert system["AUTHORITY_EFFECT"] == "NONE"
    assert system["RUNTIME_EFFECT"] == "NONE"
    assert system["NOTION_CURRENT"] is True
    assert system["NOTION_UPDATED"] is True
    assert system["NEXT_PARITY_SLICE"] == NEXT_PARITY_SLICE
    assert system["DOCUMENTED_ONLY_LATER_PATH"] == DOCUMENTED_ONLY_LATER_PATH


def test_parity_surfaces_snapshot_count_and_status() -> None:
    surfaces = market_dashboard_current_state_snapshot_v0()["parity_surfaces_completed"]
    assert len(surfaces) == 6
    for surface, expected_id, expected_status in zip(
        surfaces, PARITY_SURFACE_IDS, PARITY_SURFACE_STATUSES
    ):
        assert surface["surface_id"] == expected_id
        assert surface["assessment_status"] == expected_status


def test_technical_completion_distinct_from_economic_fail() -> None:
    snapshot = market_dashboard_current_state_snapshot_v0()
    tech = snapshot["technical_completion"]
    econ = snapshot["economic_result"]
    assert tech["FULL_CANONICAL_CHAIN_WIRED"] is True
    assert tech["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is True
    assert tech["not_economic_validity"] is True
    assert econ["ECONOMIC_STATUS"] == "FAIL"
    assert econ["ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"] is False
    assert econ["TRADE_COUNT"] == 0
    assert econ["NET_RETURN"] == 0.0
    assert econ["ECONOMIC_EVALUATION_EXECUTED"] is False
    assert econ["EVIDENCE_RESULTS_REMATERIALIZED"] is False
    assert econ["UNCHANGED_RETRY_FORBIDDEN"] is True


def test_blocked_main_gates_snapshot_values() -> None:
    gates = market_dashboard_current_state_snapshot_v0()["blocked_main_gates"]
    assert gates["FULL_CANONICAL_CHAIN_WIRED"] is True
    assert gates["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is True
    assert gates["SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE"] is False
    assert gates["RUNTIME_REWIRE_ADMISSIBLE"] is False
    assert gates["ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"] is False


def test_technical_and_economic_sections_visible(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-technical-completion-v1="true"' in html
    assert 'data-market-full-canonical-chain-wired-v1="true">true' in html
    assert 'data-market-backtest-runtime-parity-pass-v1="true">true' in html
    assert 'data-market-economic-evidence-admissible-v1="true">false' in html
    assert 'data-market-runtime-rewire-admissible-v1="true">false' in html
    assert f'data-market-next-blocker-v1="true">NEXT_BLOCKER={NEXT_BLOCKER}' in html
    assert CURRENT_ORIGIN_MAIN in html
    assert 'data-market-economic-result-v1="true"' in html
    assert 'data-market-economic-status-v1="true">FAIL' in html
    assert 'data-market-trade-count-v1="true">0' in html
    assert 'data-market-economic-validity-offline-gate-v1="true">false' in html
    assert "UNCHANGED_RETRY_FORBIDDEN=true" in html


def test_all_six_parity_surfaces_visible(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-parity-surfaces-completed-v1="true"' in html
    for surface_id, status in zip(PARITY_SURFACE_IDS, PARITY_SURFACE_STATUSES):
        assert f'data-market-parity-surface-id="{surface_id}"' in html
        assert f'data-market-parity-surface-status="{status}"' in html


def test_strategy_fleet_snapshot(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-strategy-fleet-compact-v1="true"' in html
    assert 'data-market-fleet-strategy-id="macd"' in html
    assert 'data-market-fleet-status="TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"' in html
    assert 'data-market-fleet-strategy-id="breakout_donchian"' in html
    assert 'data-market-fleet-strategy-id="vol_breakout"' in html
    assert 'data-market-fleet-status="AUTHORIZED_PENDING_EVALUATION"' not in html
    assert 'data-market-fleet-strategy-id="bollinger_bands"' in html
    assert 'data-market-fleet-status="COMPLETE_FAIL"' in html
    assert 'data-market-current-research-strategy-v1="true">bollinger_bands/v2' in html
    assert 'data-market-current-research-status-v1="true">COMPLETE_FAIL' in html
    assert CURRENT_RESEARCH_BINDING_ID in html
    assert "POLICY_RATIFIED" in html
    assert "ECONOMIC_EVALUATION_EXECUTED=false" in html
    assert "EVIDENCE_RESULTS_REMATERIALIZED=false" in html


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
    assert "live ready" not in lowered
    assert "production ready" not in lowered
    assert "economically viable" not in lowered


def test_next_parity_slice_visible_and_separate_from_step31f(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-next-parity-slice-v1="true"' in html
    assert NEXT_PARITY_SLICE in html
    assert 'data-market-documented-only-later-path-v1="true"' in html
    assert DOCUMENTED_ONLY_LATER_PATH in html
    assert "Next executable parity slice" in html
    assert "Documented-only later path" in html
    assert "DOCUMENTED_ONLY_NOT_EXECUTABLE" in html
    slice_pos = html.index(NEXT_PARITY_SLICE)
    step31f_pos = html.index(DOCUMENTED_ONLY_LATER_PATH)
    assert slice_pos < step31f_pos


def test_runtime_gates_remain_blocked(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-live-authorized-v1="true">false' in html
    assert 'data-market-governance-orders-allowed-v1="true">false' in html
    assert 'data-market-scheduler-runtime-allowed-v1="true">false' in html
    assert 'data-market-authority-effect-v1="true">NONE' in html
    assert 'data-market-runtime-effect-v1="true">NONE' in html
    assert 'data-market-promotion-allowed-v1="true">false' in html
    assert 'data-market-runtime-authorized-v1="true">false' in html
    assert 'data-market-economic-validity-pass-v1="true">false' in html
    assert 'data-market-authorized-pending-count-v1="true">0' in html
    assert 'data-market-trading-authority-v1="false"' in html


def test_governance_safety_flags_visible(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-governance-safety-compact-v1="true"' in html
    assert "FUTURES_ONLY" in html
    assert "COIN_DIRECTION_ALLOWED=false" in html
    assert "SPOT_ALLOWED=false" in html
    assert "SYNTHETIC_SPOT_ALLOWED=false" in html
    assert "MAX_POSITIONS=1" in html
    assert "MAX_ACTIVE_DIRECTIONAL_SIDE=1" in html


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


def test_futures_only_no_bitcoin_or_spot_tradeable(client: TestClient) -> None:
    html = _html(client)
    assert not BITCOIN_RE.search(html)
    lowered = html.lower()
    assert "spot trade" not in lowered
    assert "synthetic spot trade" not in lowered


def test_provenance_visible_and_bound(client: TestClient) -> None:
    html = _html(client)
    provenance = market_dashboard_current_state_snapshot_v0()["provenance"]
    assert 'data-market-current-state-provenance-v1="true"' in html
    assert 'data-market-source-pr-v1="true">5242' in html
    assert CURRENT_STATE_SOURCE_HEAD in html
    assert CURRENT_STATE_RESULT_JSON in html
    assert provenance["CURRENT_STATE_PRIMARY_EVIDENCE_DIR"] == CURRENT_STATE_PRIMARY_EVIDENCE_DIR
    assert provenance["CURRENT_STATE_REPAIR_EVIDENCE_DIR"] == CURRENT_STATE_REPAIR_EVIDENCE_DIR
    assert provenance["CURRENT_STATE_CLOSEOUT_EVIDENCE_DIR"] == CURRENT_STATE_CLOSEOUT_EVIDENCE_DIR
    assert provenance["PRIMARY_SOURCE_MANIFEST_VERIFY_RC"] == PRIMARY_SOURCE_MANIFEST_VERIFY_RC
    assert provenance["SOURCE_REPAIR_MANIFEST_VERIFY_RC"] == SOURCE_REPAIR_MANIFEST_VERIFY_RC
    assert provenance["CLOSEOUT_MANIFEST_VERIFY_RC"] == CLOSEOUT_MANIFEST_VERIFY_RC
    assert provenance["ECONOMIC_EVALUATION_EXECUTED"] is ECONOMIC_EVALUATION_EXECUTED
    assert provenance["EVIDENCE_RESULTS_REMATERIALIZED"] is EVIDENCE_RESULTS_REMATERIALIZED
    assert "MANIFESTS_VERIFIED=true" in html
    assert "ECONOMIC_EVALUATION_EXECUTED=false" in html
    assert "EVIDENCE_RESULTS_REMATERIALIZED=false" in html


def test_evidence_integrity_secondary_not_dominant_alarm(client: TestClient) -> None:
    html = _html(client)
    assert 'data-market-evidence-primary-v1="true"' in html
    assert f"PR #{LATEST_MERGED_PR_NUMBER} MERGED" in html
    assert "FULL_CANONICAL_CHAIN_WIRED=true" in html
    assert "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true" in html
    assert "ECONOMIC_STATUS=FAIL" in html
    assert "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false" in html
    assert "RUNTIME_REWIRE_ADMISSIBLE=false" in html
    assert 'data-market-diagnostics-evidence-integrity-v1="true"' in html
    assert 'data-market-ratification-manifest-drift-v1="true"' in html
    assert "REPORT.md hash drift" in html
    assert "not a current system fault" in html
    assert "NOTION_UPDATED=true" in html


def test_historical_stale_states_not_primary(client: TestClient) -> None:
    html = _html(client)
    lowered = html.lower()
    assert "fleet fully exhausted" not in lowered
    assert "operator decision still open" not in lowered
    assert "policy selection" not in lowered
    assert "economic validity pass achieved" not in lowered
    assert "authorized_pending_evaluation" not in lowered
    assert 'data-market-authorized-pending-count-v1="true">1' not in html
    assert 'data-market-fleet-status="AUTHORIZED_PENDING_EVALUATION"' not in html
    # Technical completion true may coexist with economic fail false.
    assert 'data-market-full-canonical-chain-wired-v1="true">true' in html
    assert 'data-market-economic-status-v1="true">FAIL' in html


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
