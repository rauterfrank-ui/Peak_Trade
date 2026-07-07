"""Contract: Feedback Learning boundary offline replay binding parity rewire v0 (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
    FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    FeedbackLearningBoundaryOfflineReplayContextV0,
    bind_feedback_learning_boundary_offline_replay_evidence_v0,
    feedback_learning_boundary_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _base_evidence():
    return build_scenario_tick_decision_evidence_v0(
        decision_id="feedback-learning-offline-replay",
        replay_id="feedback-learning-offline-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="none",
        decision_outcome="observe",
        reason_codes=("PASS",),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )


def test_adapter_owner_v0() -> None:
    assert FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER.endswith(
        "feedback_learning_boundary_offline_replay_binding_adapter_v0"
    )


def test_observe_only_binding_does_not_mutate_evidence_v0() -> None:
    assert FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED is True
    evidence = _base_evidence()
    bound = bind_feedback_learning_boundary_offline_replay_evidence_v0(
        evidence,
        context=FeedbackLearningBoundaryOfflineReplayContextV0(),
    )
    assert bound.evidence is evidence
    assert bound.boundary.observe_only_no_mutation is True
    assert bound.boundary.no_promotion_mutation is True
    assert feedback_learning_boundary_binding_non_authority_boundary_ok_v0(bound)


def test_forbidden_runtime_imports_v0() -> None:
    path = (
        REPO_ROOT
        / "src/trading/master_v2/feedback_learning_boundary_offline_replay_binding_adapter_v0.py"
    )
    forbidden = frozenset({"execution", "scheduler", "credentials", "live_runtime"})
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden):
                hits.append(node.module)
    assert hits == []
