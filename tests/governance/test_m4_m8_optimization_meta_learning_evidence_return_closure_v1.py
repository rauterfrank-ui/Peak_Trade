"""M4–M8 optimization/meta-learning evidence return closure adjudication tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.m4_m8_optimization_meta_learning_evidence_return_closure_v1 import (
    CensusClassification,
    DECISION_CONFIG,
    WORKPACKAGE_ID,
    build_current_census_v1,
    build_m4_m8_closure_summary_v1,
    prove_m4_m8_optimization_meta_learning_evidence_return_closure_v1,
    prove_m4_m8_runtime_lineage_v1,
    prove_p5_final_closure_still_blocked_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_census_classifies_p5_bridges_conflicting() -> None:
    census = build_current_census_v1(repo_root=REPO_ROOT)
    by_id = {e["component_id"]: e for e in census["entries"]}
    assert (
        by_id["P5_OPTIMIZATION_PRODUCER_BRIDGE"]["classification"]
        == CensusClassification.CONFLICTING.value
    )
    assert by_id["M4_EXPERIMENT_PLANE"]["classification"] == CensusClassification.REUSE_AS_IS.value
    assert by_id["M4_EXPERIMENT_PLANE"]["owner_present"] is True


def test_runtime_lineage_and_m8_replay_proven() -> None:
    assert prove_m4_m8_runtime_lineage_v1(repo_root=REPO_ROOT) is True


def test_p5_final_closure_remains_blocked() -> None:
    assert prove_p5_final_closure_still_blocked_v1() is True


def test_closure_proof_and_decision_binding() -> None:
    assert prove_m4_m8_optimization_meta_learning_evidence_return_closure_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["p5_final_closure_ready"] is False
    assert decision["m4_status"] == "PROVEN_CANONICAL_OFFLINE_PLANE"
    assert decision["m8_status"] == "PROVEN_DETERMINISTIC_MULTI_CYCLE_REPLAY"
    assert decision["external_effect_authorized"] is False
    assert decision["mv2_double_play_sole_trading_decision_authority_preserved"] is True


def test_summary_reflects_closure_without_p5() -> None:
    summary = build_m4_m8_closure_summary_v1(repo_root=REPO_ROOT)
    assert summary["workpackage_id"] == WORKPACKAGE_ID
    assert summary["p5_final_closure_ready"] is False
    assert summary["runtime_lineage_proven"] is True
    assert summary["p5_optimization_blocker"] is not None
    assert summary["p5_meta_learning_blocker"] is not None
