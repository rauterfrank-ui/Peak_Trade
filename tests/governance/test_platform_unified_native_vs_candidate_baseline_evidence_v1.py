"""D26 platform-unified native vs candidate baseline evidence closure tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.learning.test_deterministic_decision_outcome_control_plane_v0 import _envelope
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _replay_input
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    BASELINE_CANDIDATE_ID,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.baseline_evidence_classification_adapter_v1 import (
    bind_f1_parameter_research_candidate_baseline_classification_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    optimization_can_direct_write_runtime_seam_v1,
)
from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    DECISION_CONFIG,
    InfluenceClassificationV1,
    PlatformUnifiedBaselineEvidenceError,
    assert_baseline_reference_immutable_v1,
    assert_no_trading_decision_authority_from_evidence_v1,
    classify_canonical_trading_decision_evidence_v1,
    classify_ddo_counterfactual_record_v1,
    classify_f1_parameter_research_candidate_result_v1,
    derive_comparison_context_identity_v1,
    prove_d26_platform_unified_baseline_evidence_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.constants_v1 import (
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.platform_unified_baseline_evidence_integrated_replay_adapter_v1 import (
    bind_integrated_replay_native_baseline_classification_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def integrated_replay_input_v1():
    return _replay_input()


def _baseline_ref(*, decision_id: str, replay_id: str, semantic_digest: str) -> dict[str, str]:
    return {
        "decision_id": decision_id,
        "replay_id": replay_id,
        "semantic_digest": semantic_digest,
    }


def test_d26_closure_artifacts_and_decision_present() -> None:
    assert prove_d26_platform_unified_baseline_evidence_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["d26_status"] == "PROVEN_CURRENT"
    assert decision["d26_implemented"] is True
    assert decision["optimization_productive_authority"] == "NONE"
    assert decision["p5_authority_cutover_authorized"] is False


def test_native_integrated_replay_evidence_classifies_native_baseline(
    integrated_replay_input_v1,
) -> None:
    result = run_integrated_offline_trading_logic_replay_v1(integrated_replay_input_v1)
    record = classify_canonical_trading_decision_evidence_v1(result.evidence)
    assert record.influence_classification == InfluenceClassificationV1.NATIVE_BASELINE
    assert record.candidate_identity is None
    assert record.influence_provenance is None
    assert record.fail_closed_reasons == ()
    adapter = bind_integrated_replay_native_baseline_classification_v1(result.evidence)
    assert adapter["influence_classification"] == InfluenceClassificationV1.NATIVE_BASELINE.value


def test_forbidden_influence_markers_fail_closed(integrated_replay_input_v1) -> None:
    result = run_integrated_offline_trading_logic_replay_v1(integrated_replay_input_v1)
    record = classify_canonical_trading_decision_evidence_v1(
        result.evidence,
        influence_markers={"candidate_id": "rogue-candidate"},
    )
    assert record.influence_classification == InfluenceClassificationV1.INVALID
    assert any("FORBIDDEN_INFLUENCE_MARKER" in r for r in record.fail_closed_reasons)


def test_f1_candidates_never_native_baseline(integrated_replay_input_v1) -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(integrated_replay_input_v1)
    baseline = _baseline_ref(
        decision_id=replay.evidence.decision_id,
        replay_id=replay.evidence.replay_id,
        semantic_digest=replay.evidence.semantic_digest,
    )
    for candidate_id in (BASELINE_CANDIDATE_ID, "CAND_MAX_AGE_3600"):
        payload = {"candidate_id": candidate_id, "counterfactual_only": True}
        record = classify_f1_parameter_research_candidate_result_v1(
            candidate_result=payload,
            baseline_reference=baseline,
        )
        assert (
            record.influence_classification == InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL
        )
        assert record.influence_classification != InfluenceClassificationV1.NATIVE_BASELINE
        bound = bind_f1_parameter_research_candidate_baseline_classification_v1(
            candidate_result=payload,
            baseline_reference=baseline,
        )
        assert bound["baseline_reference_identity"] == record.baseline_reference_identity


def test_ddo_counterfactual_joins_baseline_reference(integrated_replay_input_v1) -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(integrated_replay_input_v1)
    baseline = _baseline_ref(
        decision_id=replay.evidence.decision_id,
        replay_id=replay.evidence.replay_id,
        semantic_digest=replay.evidence.semantic_digest,
    )
    decision_ref = "dec-0001"
    counterfactual = _envelope(
        schema_name="counterfactual_record",
        schema_version="counterfactual_record_v0",
        record_id="cfactual-0001",
        decision_event_ref=decision_ref,
        counterfactual_admissibility="UNAVAILABLE",
        alternative_result_ref=None,
        causal_parent_ids=[decision_ref],
    )
    baseline["decision_id"] = decision_ref
    record = classify_ddo_counterfactual_record_v1(
        counterfactual_record=counterfactual,
        baseline_reference=baseline,
    )
    assert record.influence_classification == InfluenceClassificationV1.CANDIDATE_OR_COUNTERFACTUAL
    assert record.comparison_context_identity is not None


def test_missing_baseline_reference_fail_closed() -> None:
    record = classify_f1_parameter_research_candidate_result_v1(
        candidate_result={"candidate_id": "CAND_X"},
        baseline_reference={},
    )
    assert record.influence_classification == InfluenceClassificationV1.UNKNOWN
    assert "BASELINE_REFERENCE_INCOMPLETE" in record.fail_closed_reasons


def test_comparison_context_deterministic(integrated_replay_input_v1) -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(integrated_replay_input_v1)
    native = classify_canonical_trading_decision_evidence_v1(replay.evidence)
    candidate = classify_f1_parameter_research_candidate_result_v1(
        candidate_result={"candidate_id": "CAND_MAX_AGE_7200"},
        baseline_reference=_baseline_ref(
            decision_id=replay.evidence.decision_id,
            replay_id=replay.evidence.replay_id,
            semantic_digest=replay.evidence.semantic_digest,
        ),
    )
    assert candidate.comparison_context_identity == derive_comparison_context_identity_v1(
        baseline_reference_identity=native.baseline_reference_identity,
        candidate_record_id=candidate.record_id,
    )
    assert_baseline_reference_immutable_v1(
        baseline_record=native,
        candidate_record=candidate,
    )


def test_baseline_overwrite_forbidden(integrated_replay_input_v1) -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(integrated_replay_input_v1)
    native = classify_canonical_trading_decision_evidence_v1(replay.evidence)
    rogue = classify_f1_parameter_research_candidate_result_v1(
        candidate_result={"candidate_id": "CAND_X"},
        baseline_reference={
            "decision_id": "other-decision",
            "replay_id": replay.evidence.replay_id,
            "semantic_digest": hashlib.sha256(b"rogue").hexdigest(),
        },
    )
    with pytest.raises(PlatformUnifiedBaselineEvidenceError):
        assert_baseline_reference_immutable_v1(baseline_record=native, candidate_record=rogue)


def test_no_trading_or_optimization_productive_authority_from_d26() -> None:
    assert_no_trading_decision_authority_from_evidence_v1()
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert optimization_can_direct_write_runtime_seam_v1() is False
