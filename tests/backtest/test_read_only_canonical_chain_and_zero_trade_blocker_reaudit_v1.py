"""Static freeze for read-only canonical-chain + zero-trade blocker reaudit v1.

Freezes observed Ist-Zustand only. Non-authorizing: no productive src mutation,
no side activation, no runtime bridge activation.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOV_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "READ_ONLY_CANONICAL_CHAIN_AND_ZERO_TRADE_BLOCKER_REAUDIT_V1.md"
)
EVIDENCE_DIR = (
    REPO_ROOT
    / "docs"
    / "product"
    / "evidence"
    / "read_only_canonical_chain_and_zero_trade_blocker_reaudit_v1_20260717T235727Z"
)
DECISION = EVIDENCE_DIR / "decision.json"
CALL_GRAPH = EVIDENCE_DIR / "call_graph_links.json"
FUNNEL = EVIDENCE_DIR / "funnel_counts.json"
SAFETY = EVIDENCE_DIR / "safety_boundary.json"
BASELINE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "product"
    / "evidence"
    / "obl_b05_bollinger_long_semantic_decision_v1_20260717T231700Z"
    / "baseline_summary.json"
)

STRATEGY_BINDING = REPO_ROOT / "src" / "backtest" / "strategy_signal_binding_v1.py"
CMC = REPO_ROOT / "src" / "trading" / "master_v2" / "canonical_market_context_v1.py"
REPLAY = (
    REPO_ROOT / "src" / "trading" / "master_v2" / "integrated_offline_trading_logic_replay_v1.py"
)
ENGINE = REPO_ROOT / "src" / "backtest" / "engine.py"
BRIDGE = (
    REPO_ROOT / "src" / "trading" / "master_v2" / "canonical_core_runtime_integration_bridge_v0.py"
)
WIRING = REPO_ROOT / "src" / "backtest" / "mv2_research_wiring_v1.py"

EXPECTED_BASE_SHA = "aaf83d00341a7649a070b31a5170dfc49a646db3"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_def(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return True
    return False


def _source_mentions(path: Path, needle: str) -> bool:
    return needle in path.read_text(encoding="utf-8")


def test_governance_doc_and_evidence_exist_with_docs_token() -> None:
    assert GOV_DOC.is_file()
    body = GOV_DOC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_READ_ONLY_CANONICAL_CHAIN_AND_ZERO_TRADE_BLOCKER_REAUDIT_V1" in body
    assert "PRODUCTIVE_SRC_CHANGED: false" in body
    assert "BOLLINGER_ENTRY_SIDE_CURRENT: NONE" in body
    assert "SIDE_ACTIVATED: false" in body
    for name in (
        "decision.json",
        "call_graph_links.json",
        "funnel_counts.json",
        "safety_boundary.json",
        "repository_state.json",
        "AUDIT.md",
        "README.md",
    ):
        assert (EVIDENCE_DIR / name).is_file(), name


def test_decision_freezes_observed_classifications_and_safety() -> None:
    decision = _load(DECISION)
    safety = _load(SAFETY)
    assert decision["base_sha"] == EXPECTED_BASE_SHA
    assert decision["STATUS"] == "PASS"
    assert decision["STRATEGY_TO_CMC"] == "MISSING"
    assert decision["STRATEGY_TO_ORCHESTRATOR"] == "PRESENT_AND_PRODUCTIVE"
    assert decision["CLASSIC_ENGINE_TO_ORCHESTRATOR"] == "MISSING"
    assert decision["RUNTIME_BRIDGE_STATE"] == "BOUND_NOT_ACTIVATED"
    assert decision["BYPASS_PATH_COUNT"] == 7
    assert decision["confirmed_bypass_count_system_economic_decision_authority"] == 0
    assert decision["EVAL_ENTRY_COUNT"] == 1
    assert decision["PANEL_ENTRY_COUNT"] == 185
    assert decision["DOMINANT_FIRST_FAILED_STAGE"] == "directional_agreement"
    assert decision["TRADE_COUNT"] == 0
    assert decision["COUNTS_RECONCILED"] is True
    assert decision["BOLLINGER_ENTRY_SIDE_CURRENT"] == "NONE"
    assert decision["BOLLINGER_AUTHORITY_CHANGED"] is False
    assert decision["SIDE_ACTIVATED"] is False
    assert decision["LIVE_AUTHORIZED"] is False
    assert decision["ORDERS_ENABLED"] is False
    assert decision["PRODUCTIVE_SRC_CHANGED"] is False
    assert (
        decision["NEXT_RECOMMENDED_ACTION"]
        == "OBL_B05_BOLLINGER_ENTRY_SIDE_AUTHORITY_OPERATOR_GO_SELECTION_V1"
    )
    assert decision["implementation_authorized_now"] is False
    assert safety["FAIL_CLOSED"] is True
    assert safety["RUNTIME_BRIDGE_ACTIVATION"] is False
    assert safety["BOLLINGER_AUTHORITY_CHANGED"] is False


def test_call_graph_matches_source_anchors() -> None:
    graph = _load(CALL_GRAPH)
    assert graph["base_sha"] == EXPECTED_BASE_SHA
    anchors = graph["symbol_anchors"]
    assert _has_def(STRATEGY_BINDING, anchors["strategy_signal_producer"]["symbol"])
    assert _has_def(CMC, anchors["canonical_market_context"]["symbol"])
    assert _has_def(REPLAY, anchors["integrated_offline_orchestrator"]["symbol"])
    assert _has_def(ENGINE, "run_realistic")
    assert _has_def(BRIDGE, anchors["runtime_bridge"]["symbol"])
    assert _has_def(WIRING, anchors["productive_wiring_owner"]["symbol"])

    # Strategy producer does not call CMC or orchestrator directly.
    assert not _source_mentions(STRATEGY_BINDING, "bind_canonical_market_context_event")
    assert not _source_mentions(STRATEGY_BINDING, "run_integrated_offline_trading_logic_replay_v1")
    # Classic engine does not call orchestrator.
    assert not _source_mentions(ENGINE, "run_integrated_offline_trading_logic_replay_v1")
    # Productive wiring binds strategy -> agreement -> orchestrator -> fill engine.
    wiring = WIRING.read_text(encoding="utf-8")
    assert "execute_configured_strategy_signal_series_v1" in wiring
    assert "normalize_strategy_signal_to_suitability_agreement_material_v1" in wiring
    assert "run_integrated_offline_trading_logic_replay_v1" in wiring
    assert "run_realistic" in wiring
    # Orchestrator binds CMC events.
    assert "bind_canonical_market_context_event" in REPLAY.read_text(encoding="utf-8")
    # Runtime bridge remains BOUND_NOT_ACTIVATED.
    bridge = BRIDGE.read_text(encoding="utf-8")
    assert 'INTEGRATION_STATUS_BOUND_NOT_ACTIVATED = "BOUND_NOT_ACTIVATED"' in bridge

    by_id = {row["id"]: row["classification"] for row in graph["links"]}
    assert by_id["STRATEGY_TO_CMC"] == "MISSING"
    assert by_id["STRATEGY_TO_ORCHESTRATOR"] == "PRESENT_AND_PRODUCTIVE"
    assert by_id["CLASSIC_ENGINE_TO_ORCHESTRATOR"] == "MISSING"
    assert by_id["RUNTIME_BRIDGE_BOUND"] == "BOUND_NOT_ACTIVATED"
    assert by_id["RUNTIME_BRIDGE_ACTIVATED"] == "MISSING"
    assert graph["bypass_inventory"]["BYPASS_PATH_COUNT"] == 7


def test_funnel_reconciles_with_bollinger_baseline_ssot() -> None:
    funnel = _load(FUNNEL)
    baseline = _load(BASELINE_SUMMARY)
    panel = baseline["bollinger_panel_entry_mv2"]
    eval_ = baseline["bollinger_eval_entry_mv2"]

    assert funnel["EVAL_ENTRY_COUNT"] == eval_["entry_bar_count"] == 1
    assert funnel["PANEL_ENTRY_COUNT"] == panel["entry_bar_count"] == 185
    assert funnel["DOMINANT_FIRST_FAILED_STAGE"] == "directional_agreement"
    assert panel["dominant_first_failed_stage"] == "directional_agreement"
    assert eval_["dominant_first_failed_stage"] == "directional_agreement"
    assert panel["first_failed_stage_counts"]["directional_agreement"] == 185
    assert eval_["first_failed_stage_counts"]["directional_agreement"] == 1
    assert panel["entry_side_counts"]["NONE"] == 185
    assert eval_["entry_side_counts"]["NONE"] == 1
    assert panel["ENTER_LONG"] == 0
    assert panel["ENTER_SHORT"] == 0
    assert funnel["TRADE_COUNT"] == 0
    assert funnel["COUNTS_RECONCILED"] is True
    assert funnel["eval"]["reconciled"] is True
    assert funnel["panel"]["reconciled"] is True

    panel_outcome_sum = sum(
        v
        for k, v in panel.items()
        if k.startswith("BLOCKED_")
        or k
        in {"ENTER_LONG", "ENTER_SHORT", "EXIT_OR_DEMOTION", "HOLD", "UNOBSERVABLE_FAIL_CLOSED"}
    )
    assert panel_outcome_sum == panel["entry_bar_count"]
    assert sum(panel["first_failed_stage_counts"].values()) == panel["entry_bar_count"]
