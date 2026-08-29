"""§5.3 host-graph SSOT: post-Replay Risk/Safety/Intent are stage labels, not owner calls."""

from __future__ import annotations

from pathlib import Path

from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1 import (
    CALL_GRAPH_V1 as CAP71_CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    CALL_GRAPH_V2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1 as CAP72_CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_HOST_GRAPH_SSOT_AND_OWNER_COMPOSED_FULL_CHAIN_PROOF_V1.md"
)

_POST_REPLAY_STAGE_LABELS = (
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
)
_REPLAY_NODE = "master_v2_double_play_integrated_offline_replay"


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_section_5_3_classifies_post_replay_labels_as_evidence_or_consumption_only() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    section = _section_5_3(text)
    assert "CANONICAL_OWNER_GRAPH=" in section
    assert "POST_REPLAY_RISK_OWNER_REINVOKED=false" in section
    assert "POST_REPLAY_SAFETY_OWNER_REINVOKED=false" in section
    assert "POST_REPLAY_INTENT_OWNER_REINVOKED=false" in section
    assert "SECOND_COMPUTE_OWNER_EXISTS=false" in section
    assert "SECOND_RISK_OWNER_EXISTS=false" in section
    assert "SECOND_SAFETY_OWNER_EXISTS=false" in section
    assert "SECOND_INTENT_OWNER_EXISTS=false" in section
    assert "HOST_MAPPER_ROLE=CONSUMER_TRANSLATOR_ONLY" in section
    assert "BRIDGE_SAFETY_ROLE=INPUT_PRODUCER_ONLY" in section
    assert "POST_REPLAY_EVIDENCE_OR_CONSUMPTION_STAGE_LABEL_ONLY" in section
    assert "POST_REPLAY_COMPUTE_OWNER_CALL" in section
    assert "HOST_GRAPH_SSOT_STATUS=CORRECTED" in section
    assert "DOC_RUNTIME_MATCH=true" in section
    # Historical stage labels remain for evidence/compatibility.
    assert "→ Risk → Safety → Intent" in section
    assert "risk_position_sizing" in section
    assert "safety_kernel" in section
    assert "intended_side_quantity" in section
    assert "[POST_REPLAY_EVIDENCE_OR_CONSUMPTION_STAGE_LABEL_ONLY]" in section
    assert "POST_REPLAY_COMPUTE_OWNER_CALL" in section


def test_call_graph_tuples_keep_post_replay_stage_labels_after_replay_node() -> None:
    for graph in (CAP72_CALL_GRAPH_V1, REQUIRED_CALL_GRAPH, CAP71_CALL_GRAPH_V1, CALL_GRAPH_V2):
        assert _REPLAY_NODE in graph
        replay_i = graph.index(_REPLAY_NODE)
        for label in _POST_REPLAY_STAGE_LABELS:
            assert label in graph
            assert graph.index(label) > replay_i


def test_spec_attests_stage_label_class_and_no_second_owners() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "HOST_GRAPH_SSOT_STATUS=CORRECTED" in spec
    assert (
        "POST_REPLAY_STAGE_LABEL_CLASS=POST_REPLAY_EVIDENCE_OR_CONSUMPTION_STAGE_LABEL_ONLY" in spec
    )
    assert "POST_REPLAY_COMPUTE_OWNER_CALL=false" in spec
    assert "RUNTIME_MUTATION=false" in spec
    assert "GOLDEN_VECTOR_CORPUS_STATUS=ABSENT" in spec
    assert "FULL_CHAIN_GOLDEN_VECTOR_STRATEGY=OWNER_COMPOSED" in spec
    assert (
        "SIMULATED_EXECUTIONPORT_IS_CANONICAL_OWNER=true_for_cap72_activated_no_order_host" in spec
    )
    assert "DIRECT_PORTFOLIO_MUTATION_BYPASS_CLASS=MODE_SPECIFIC_VALID" in spec
    assert "POST_SIM_OBLIGATION_IN_REPLAY=false" in spec
    assert "NEW_SEMANTIC_POLICY=false" in spec
