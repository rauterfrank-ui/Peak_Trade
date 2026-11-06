"""Post-D27 global test-entry lifecycle closure adjudication tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1 import (
    AdjudicationVerdict,
    adjudicate_v32_baseline_first_requirements_v1,
    earliest_missing_edge_v1,
)
from src.governance.v32_post_d27_test_entry_lifecycle_global_closure_adjudication_v1 import (
    DECISION_CONFIG,
    NEXT_TRUE_BLOCKER,
    WORKPACKAGE_ID,
    build_post_d27_closure_graph_v1,
    build_post_d27_closure_summary_v1,
    prove_v32_post_d27_test_entry_lifecycle_global_closure_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_global_closure_proof_and_decision() -> None:
    assert prove_v32_post_d27_test_entry_lifecycle_global_closure_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["d27_global_closure_implemented"] is True
    assert decision["d27_status"] == "PROVEN_CURRENT"
    assert decision["d27_closure_proven"] is True
    assert decision["earliest_remaining_d27_gap"] is None
    assert decision["next_true_blocker"] == NEXT_TRUE_BLOCKER
    assert decision["productive_numeric_values_set_current"] == 0
    assert decision["new_authority_created"] is False
    assert decision["external_effect_authorized"] is False


def test_closure_graph_covers_composed_proofs() -> None:
    edges = build_post_d27_closure_graph_v1(repo_root=REPO_ROOT)
    sources = {e.source for e in edges}
    assert any("prove_d27_f1_f2" in s for s in sources)
    assert any("prove_d27_f5_shadow" in s for s in sources)
    assert any("prove_d26_platform" in s for s in sources)
    assert any("prove_d26_f5_shadow" in s for s in sources)


def test_summary_aligns_with_naked_mv2_d27() -> None:
    summary = build_post_d27_closure_summary_v1(repo_root=REPO_ROOT)
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=REPO_ROOT)
    by_id = {r.requirement_id: r for r in rows}
    assert summary["naked_mv2_d27_verdict"] == AdjudicationVerdict.PROVEN_CURRENT.value
    assert summary["naked_mv2_d27_missing_edge"] is None
    assert by_id["D27"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert earliest_missing_edge_v1(rows) is None
    assert summary["productive_numeric_values_set"] == PRODUCTIVE_NUMERIC_VALUES_SET == 0


def test_next_true_blocker_documented() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["next_true_blocker_class"] == "OWNER_POLICY_REQUIRED"
    learning = json.loads(
        (
            REPO_ROOT
            / "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert learning["optimization_universe_join_authorized"] is False
