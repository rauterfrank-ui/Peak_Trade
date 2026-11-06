"""D28/D29 optimization productive join policy adjudication tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.explicit_productive_authorization_v1 import (
    AUTHORIZED_FOR_PRODUCTIVE_APPLY,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    optimization_can_direct_write_runtime_seam_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG,
)
from src.governance.v32_d28_d29_optimization_productive_join_policy_adjudication_v1 import (
    DECISION_CONFIG,
    JoinEdgeStatusV1,
    MINIMAL_OWNER_POLICY_QUESTION,
    NEXT_TRUE_BLOCKER,
    WORKPACKAGE_ID,
    build_d28_d29_join_adjudication_summary_v1,
    build_d28_d29_join_closure_graph_v1,
    build_optimization_productive_join_matrix_v1,
    prove_v32_d28_d29_optimization_productive_join_policy_adjudication_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_join_adjudication_proof_and_decision() -> None:
    assert prove_v32_d28_d29_optimization_productive_join_policy_adjudication_v1(
        repo_root=REPO_ROOT
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert (
        decision["workpackage_id"]
        == "V32_D28_D29_OPTIMIZATION_PRODUCTIVE_JOIN_POLICY_ADJUDICATION_AND_MAX_PRE_BLOCKER_BUILD_V1"
    )
    assert decision["d28_d29_adjudication_implemented"] is True
    assert decision["d28_status"] == "OWNER_POLICY_REQUIRED"
    assert decision["d29_status"] == "OWNER_POLICY_REQUIRED"
    assert decision["optimization_universe_join_authorized_current"] is False
    assert decision["optimization_universe_join_authorized_changed"] is False
    assert decision["next_true_blocker"] == NEXT_TRUE_BLOCKER
    assert decision["minimal_owner_policy_question"] == MINIMAL_OWNER_POLICY_QUESTION
    assert decision["productive_numeric_values_set_current"] == 0
    assert decision["new_authority_created"] is False
    assert decision["external_effect_authorized"] is False


def test_join_matrix_status_partition() -> None:
    rows = build_optimization_productive_join_matrix_v1(repo_root=REPO_ROOT)
    assert len(rows) == 8
    by_id = {r.row_id: r for r in rows}
    assert by_id["F1-M9-M10-PARAMETER-LINEAGE"].status == JoinEdgeStatusV1.PROVEN_CURRENT
    assert (
        by_id["GLOBAL-OPTIMIZATION-UNIVERSE-PRODUCTIVE-JOIN"].status
        == JoinEdgeStatusV1.OWNER_POLICY_REQUIRED
    )
    for rid in (
        "F2-RESEARCH-COUNTERFACTUAL",
        "F5-FRESH-SHADOW-RESEARCH",
        "F5-SURV-PER-TOKEN-SHADOW",
        "F5-CAP-PER-TOKEN-SHADOW",
        "OPTIMIZATION-DIRECT-RUNTIME-SEAM-WRITE",
    ):
        assert by_id[rid].status == JoinEdgeStatusV1.FORBIDDEN


def test_closure_graph_composes_post_d27() -> None:
    edges = build_d28_d29_join_closure_graph_v1(repo_root=REPO_ROOT)
    assert len(edges) >= 4
    assert any("post_d27" in e.source for e in edges)
    assert any(e.kind.value == "OWNER_POLICY_BOUNDARY" for e in edges)


def test_summary_guardrails() -> None:
    summary = build_d28_d29_join_adjudication_summary_v1(repo_root=REPO_ROOT)
    assert summary["workpackage_id"] == WORKPACKAGE_ID
    assert summary["productive_numeric_values_set"] == PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert summary["optimization_universe_join_authorized_current"] is False
    assert summary["promotion_authorized"] is False
    assert summary["productive_apply_authorized"] is False
    assert AUTHORIZED_FOR_PRODUCTIVE_APPLY is False
    assert optimization_can_direct_write_runtime_seam_v1() is False
    assert OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG is False


def test_learning_decision_join_still_false() -> None:
    learning = json.loads(
        (
            REPO_ROOT
            / "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert learning["optimization_universe_join_authorized"] is False
    assert learning.get("promotion_join_authorized") is False
