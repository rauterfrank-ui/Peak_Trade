"""Contract: AI Observability boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.ai_observability_boundary_backtest_state_file_binding_adapter_v0 import (
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    backtest_ai_observability_state_file_binding_non_authority_ok_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_ai_observability_state_file_boundary_only_v0,
    parse_ai_observability_backtest_state_file_v0,
)
from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import EVIDENCE_SCHEMA_VERSION
from trading.master_v2.decision_packet_v1 import MASTER_V2_DECISION_PACKET_LAYER_VERSION

REPO_ROOT = Path(__file__).resolve().parents[3]


def _payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "explainability_envelope_mode": EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY,
        "ai_layer_owner_digest_ref": EVIDENCE_SCHEMA_VERSION,
        "decision_packet_owner_digest_ref": MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        **kwargs,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def test_adapter_owner_v0() -> None:
    assert AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "ai_observability_boundary_backtest_state_file_binding_adapter_v0"
    )


def test_boundary_documented_and_non_authority_v0() -> None:
    assert AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED is True
    evidence = evaluate_backtest_ai_observability_state_file_boundary_only_v0(
        parse_ai_observability_backtest_state_file_v0(payload=_payload())
    )
    assert evidence.read_only_evidence_only is True
    assert backtest_ai_observability_state_file_binding_non_authority_ok_v0(evidence)


def test_forbidden_runtime_imports_v0() -> None:
    path = (
        REPO_ROOT
        / "src/trading/master_v2/ai_observability_boundary_backtest_state_file_binding_adapter_v0.py"
    )
    forbidden = frozenset({"execution", "scheduler", "credentials", "live_runtime"})
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden):
                hits.append(node.module)
    assert hits == []
