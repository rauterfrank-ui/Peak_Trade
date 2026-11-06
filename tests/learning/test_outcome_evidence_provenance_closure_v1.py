"""WP REALM_OUTCOME_PROVENANCE_CLOSURE — C11/C12/C13/C18 and invariant probes."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    STATUS_REJECTED_PROVENANCE_INELIGIBLE,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_bindings_v1 import (
    ProvenanceBindingContextV1,
    ProvenanceProducerBindingV1,
    resolve_provenance_for_binding_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    ExternalCapitalFlowClassV1,
    OutcomeSemanticClassV1,
    build_outcome_evidence_provenance_v1,
    provenance_implies_productive_truth_v1,
)
from src.learning.deterministic_decision_outcome_v0.optimization_provenance_eligibility_v1 import (
    assert_optimization_pool_compatible_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.self_learning_provenance_eligibility_v1 import (
    evaluate_self_learning_provenance_eligibility_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _identity, _snapshot


def _productive_bundle(tmp_path: Path):
    decision = build_decision_event_v0(_decision())
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "prov.jsonl")
    ledger.append(decision)
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, _snapshot(), economic_score="LABEL_PROV"
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        horizon["evaluation_observation"],
        identity=_identity(),
        ledger=ledger,
    )
    return ledger, bundle


def test_n_bars_auto_provenance_productive_class(tmp_path: Path) -> None:
    _, bundle = _productive_bundle(tmp_path)
    prov = bundle["outcome_record"]["outcome_evidence_provenance"]
    assert prov["outcome_semantic_class"] == (
        OutcomeSemanticClassV1.OBSERVED_PRODUCTIVE_PRE_EXTERNAL.value
    )
    assert provenance_implies_productive_truth_v1(prov) is True


def test_c11_provenance_survives_ddo_to_export(tmp_path: Path) -> None:
    ledger, bundle = _productive_bundle(tmp_path)
    ing = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id="ddo.lscope.prov-closure",
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc="2026-09-01T15:00:00Z",
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    evidence = export_learning_evidence_from_state_v1(ing["learning_state_record"])
    assert evidence["outcome_semantic_class"] == evidence["evidence_pool_class"]
    assert (
        evidence["outcome_evidence_provenance"]["provenance_digest"]
        == (evidence["outcome_evidence_provenance_digest"])
    )


def test_c12_optimization_rejects_missing_provenance(tmp_path: Path) -> None:
    state = _productive_bundle(tmp_path)[1]
    bad_evidence = {
        "schema_name": "learning_evidence_record",
        "schema_version": "learning_evidence_record_v1",
        "record_id": "ddo.lev.bad0001",
        "source_learning_state_record_ref": "ls.bad",
        "state_scope_id": "scope",
        "state_version": 1,
        "evaluation_bundle_fingerprint": "a" * 64,
        "decision_event_ref": "ddo.dec.bad",
        "observed_at_utc": "2026-09-01T15:00:00Z",
        "economic_score_label": "X",
        "evaluation_horizon": "N_BARS",
        "actual_outcome_ref": "ref",
        "universe_class": "SELF_LEARNING_UNIVERSE",
        "evidence_class": "LEARNING_EVIDENCE",
        "event_time_utc": "2026-09-01T15:00:00Z",
        "correlation_id": "c",
        "causal_parent_ids": ["ls.bad"],
        "producer_id": "test",
        "authority_owner": "NONE",
        "code_sha": "UNKNOWN",
        "config_hash": "UNKNOWN",
        "evidence_hash": "b" * 64,
        "evidence_source_refs": ["ls.bad"],
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
        "can_mutate_core": False,
        "can_mutate_risk": False,
        "can_mutate_safety": False,
        "can_deploy": False,
        "outcome_semantic_class": OutcomeSemanticClassV1.OBSERVED_PRODUCTIVE_PRE_EXTERNAL.value,
        "outcome_evidence_provenance_digest": "c" * 64,
        "evidence_pool_class": OutcomeSemanticClassV1.OBSERVED_PRODUCTIVE_PRE_EXTERNAL.value,
    }
    result = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=bad_evidence)
    )
    assert result["status"] in {
        STATUS_REJECTED_PROVENANCE_INELIGIBLE,
        "REJECTED_INVALID_EVIDENCE",
    }


def test_c12_incompatible_pool_classes_fail_closed() -> None:
    ctx = ProvenanceBindingContextV1(
        decision_event_ref="ddo.dec.1",
        producer_id="test",
    )
    sim = resolve_provenance_for_binding_v1(ProvenanceProducerBindingV1.INTERNAL_SIM_BRIDGE, ctx)
    prod = resolve_provenance_for_binding_v1(
        ProvenanceProducerBindingV1.PRODUCTIVE_PRE_EXTERNAL_N_BARS, ctx
    )
    left = {
        "outcome_evidence_provenance": sim,
        "outcome_semantic_class": sim["outcome_semantic_class"],
        "evidence_pool_class": sim["outcome_semantic_class"],
    }
    right = {
        "outcome_evidence_provenance": prod,
        "outcome_semantic_class": prod["outcome_semantic_class"],
        "evidence_pool_class": prod["outcome_semantic_class"],
    }
    with pytest.raises(DdoValidationError, match="OPTIMIZATION_INCOMPATIBLE"):
        assert_optimization_pool_compatible_v1(left, right)


def test_c13_external_capital_rejected_at_learning_ingest(tmp_path: Path) -> None:
    _, bundle = _productive_bundle(tmp_path)
    outcome = dict(bundle["outcome_record"])
    prov = dict(outcome["outcome_evidence_provenance"])
    prov.pop("provenance_digest", None)
    prov["external_capital_flow_class"] = ExternalCapitalFlowClassV1.DEPOSIT.value
    outcome["outcome_evidence_provenance"] = dict(build_outcome_evidence_provenance_v1(prov))
    result = evaluate_self_learning_provenance_eligibility_v1(outcome)
    assert result.admitted is False
    assert result.reason_code == "EXTERNAL_CAPITAL_FLOW_NOT_TRADING_OUTCOME"


def test_c18_unknown_provenance_not_productive_truth() -> None:
    unk = build_outcome_evidence_provenance_v1(
        {
            "provenance_status": "UNKNOWN",
            "producer_id": "test",
            "market_observation_source": "UNKNOWN",
            "ddo_ledger_environment": "UNKNOWN",
            "decision_source": "UNKNOWN",
            "execution_mode_label": "UNKNOWN",
            "fill_source_type": "UNKNOWN",
            "outcome_semantic_class": OutcomeSemanticClassV1.UNKNOWN.value,
            "outcome_realization_kind": "UNKNOWN",
            "external_capital_flow_class": "NONE",
            "lineage_digest": "UNKNOWN",
        }
    )
    assert provenance_implies_productive_truth_v1(unk) is False
    result = evaluate_self_learning_provenance_eligibility_v1(
        {"outcome_evidence_provenance": dict(unk)}
    )
    assert result.admitted is False


def test_c18_legacy_missing_provenance_fail_closed() -> None:
    result = evaluate_self_learning_provenance_eligibility_v1({})
    assert result.admitted is False
    assert result.reason_code == "LEGACY_OUTCOME_MISSING_PROVENANCE"


def test_optimization_accepts_provenanced_export(tmp_path: Path) -> None:
    ledger, bundle = _productive_bundle(tmp_path)
    ing = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id="ddo.lscope.opt-accept",
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc="2026-09-01T15:00:00Z",
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    evidence = export_learning_evidence_from_state_v1(ing["learning_state_record"])
    result = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
    )
    assert result["status"] == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
