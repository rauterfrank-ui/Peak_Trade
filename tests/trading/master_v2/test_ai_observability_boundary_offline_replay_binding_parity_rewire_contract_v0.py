"""Contract: AI Observability boundary offline replay binding parity rewire v0 (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    AiObservabilityBoundaryOfflineReplayContextV0,
    ai_observability_boundary_binding_non_authority_boundary_ok_v0,
    bind_ai_observability_boundary_offline_replay_evidence_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _base_evidence():
    return build_scenario_tick_decision_evidence_v0(
        decision_id="ai-obs-offline-replay",
        replay_id="ai-obs-offline-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome="enter_long",
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="config",
        implementation_digest="impl",
    )


def test_adapter_owner_v0() -> None:
    assert AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER.endswith(
        "ai_observability_boundary_offline_replay_binding_adapter_v0"
    )


def test_read_only_evidence_binding_does_not_mutate_evidence_v0() -> None:
    assert AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED is True
    evidence = _base_evidence()
    bound = bind_ai_observability_boundary_offline_replay_evidence_v0(
        evidence,
        context=AiObservabilityBoundaryOfflineReplayContextV0(),
    )
    assert bound.evidence is evidence
    assert bound.boundary.read_only_evidence_only is True
    assert ai_observability_boundary_binding_non_authority_boundary_ok_v0(bound)


def test_forbidden_runtime_imports_v0() -> None:
    path = (
        REPO_ROOT
        / "src/trading/master_v2/ai_observability_boundary_offline_replay_binding_adapter_v0.py"
    )
    forbidden = frozenset({"execution", "scheduler", "credentials", "live_runtime"})
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden):
                hits.append(node.module)
    assert hits == []
