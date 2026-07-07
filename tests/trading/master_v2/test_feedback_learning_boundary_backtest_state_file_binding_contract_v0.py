"""Contract: Feedback Learning boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from src.meta.learning_loop.deploy_inactive_v1 import DEPLOYMENT_CANDIDATE_CONTRACT_NAME
from src.meta.learning_loop.runtime_observation_feedback_v1 import OBSERVATION_CONTRACT_NAME
from trading.master_v2.feedback_learning_boundary_backtest_state_file_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    backtest_feedback_learning_state_file_binding_non_authority_ok_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_feedback_learning_state_file_boundary_only_v0,
    parse_feedback_learning_backtest_state_file_v0,
)
from trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
    FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "feedback_learning_mode": FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
        "feedback_observation_contract_ref": OBSERVATION_CONTRACT_NAME,
        "learning_deploy_inactive_contract_ref": DEPLOYMENT_CANDIDATE_CONTRACT_NAME,
        **kwargs,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def test_adapter_owner_v0() -> None:
    assert FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "feedback_learning_boundary_backtest_state_file_binding_adapter_v0"
    )


def test_boundary_documented_and_non_authority_v0() -> None:
    assert FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED is True
    evidence = evaluate_backtest_feedback_learning_state_file_boundary_only_v0(
        parse_feedback_learning_backtest_state_file_v0(payload=_payload())
    )
    assert evidence.observe_only_no_mutation_in_backtest is True
    assert backtest_feedback_learning_state_file_binding_non_authority_ok_v0(evidence)


def test_forbidden_runtime_imports_v0() -> None:
    path = (
        REPO_ROOT
        / "src/trading/master_v2/feedback_learning_boundary_backtest_state_file_binding_adapter_v0.py"
    )
    forbidden = frozenset({"execution", "scheduler", "credentials", "live_runtime"})
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden):
                hits.append(node.module)
    assert hits == []
