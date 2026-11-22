"""Original M5 reproducibility scopes are distinct from the full transport hash."""

from copy import deepcopy
import json

import pytest

from src.experiments.canonical_federated_m5_m6_return_join_v1 import (
    JOIN_STATUS_COMPLETE,
    FederatedM5M6ReturnJoinRequestV1,
    _join_payload,
    derive_federated_return_join_identity_v1,
    perform_federated_m5_m6_return_join_v1,
)
from src.experiments.canonical_meta_evidence_dual_router_v1 import (
    MetaEvidenceDualRouterRequestV1,
    run_meta_evidence_dual_routing_cycle_v1,
)
from src.experiments.canonical_meta_learning_ingest_v1 import (
    INGEST_STATUS_COMPLETE,
    FederatedMetaLearningIngestRequestV1,
    MetaLearningIngestRequestV1,
    ingest_meta_learning_evidence_from_federated_return_join_v1,
    ingest_meta_learning_evidence_from_return_input_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    CanonicalOptimizationExperimentEvidenceError,
    derive_optimization_experiment_evidence_id_v1,
    validate_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
    SelfLearningOptimizationReturnInputRequestV1,
    _ack_payload,
    validate_self_learning_optimization_return_input_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

KINDS = ("native", "mi", "f1", "f2")
FAULTS = ("digest", "slice", "bindings", "identity", "source_digest", "lineage")
CONTROLS = ("original", "json", "unscoped_annotation")


def source_evidence(kind, root):
    if kind == "native":
        from tests.learning.test_meta_learning_ingest_v1 import _m5_outputs

        return plain_v1(_m5_outputs(root)[0])
    if kind == "mi":
        from src.experiments.canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 import (
            run_mi_crossing_offline_evidence_cycle_v1,
        )
        from tests.experiments.test_canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 import (
            _two_cycle_request,
        )

        result = run_mi_crossing_offline_evidence_cycle_v1(_two_cycle_request(root).cycles[0])
        return plain_v1(result["optimization_experiment_evidence"])
    if kind == "f1":
        from tests.experiments.test_canonical_federated_m5_m6_return_join_v1 import _federated_m5

        return plain_v1(_federated_m5())
    from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
        SURFACE_ID,
    )
    from src.experiments.canonical_federated_surface_optimization_experiment_evidence_projection_v1 import (
        bind_f2_surface_execution_projection_request_v1,
        build_federated_surface_optimization_experiment_evidence_projection_v1,
    )
    from tests.experiments.test_canonical_federated_surface_optimization_experiment_evidence_projection_v1 import (
        _envelope_for,
        _minimal_f2_result,
    )

    identity, digest = _envelope_for(SURFACE_ID)
    request = bind_f2_surface_execution_projection_request_v1(
        _minimal_f2_result(),
        surface_native_evidence_ref="fixture/f2/reproducibility",
        envelope_identity=identity,
        envelope_resolution_digest=digest,
    )
    return plain_v1(build_federated_surface_optimization_experiment_evidence_projection_v1(request))


def reseal_transport(evidence):
    evidence["content_hash"] = compute_content_sha256(
        {k: v for k, v in evidence.items() if k != "content_hash"}
    )
    return evidence


def changed_evidence(original, fault):
    evidence = deepcopy(original)
    federated = evidence.get("federated_projection") is True
    if fault == "digest":
        evidence["reproducibility_digest"] = "d" * 64
    elif fault == "slice":
        evidence["evidence_slices"]["FAILURE_EVIDENCE"]["source_note"] = "changed.scoped.slice"
    elif fault == "bindings":
        evidence["version_bindings"]["optimizable_envelope_contract_version"] = "foreign.v1"
    elif fault == "identity":
        if federated:
            evidence["surface_execution_identity"] = "d" * 64
            evidence["provenance"]["surface_execution_identity"] = "d" * 64
        else:
            evidence["plane_identity"] = "d" * 64
            evidence["record_id"] = derive_optimization_experiment_evidence_id_v1(
                plane_identity=evidence["plane_identity"]
            )
    elif fault == "source_digest":
        if federated:
            evidence["provenance"]["surface_native_evidence_digest"] = "d" * 64
        else:
            evidence["learning_evidence_digest"] = "d" * 64
    elif federated:
        evidence["provenance"]["envelope_identity"] = "d" * 64
    else:
        evidence["evidence_slices"]["ECONOMIC_EVIDENCE"]["mi_enriched_lineage_digest"] = "d" * 64
    return reseal_transport(evidence)


def return_input(evidence):
    if evidence.get("federated_projection") is True:
        return perform_federated_m5_m6_return_join_v1(
            FederatedM5M6ReturnJoinRequestV1(optimization_experiment_evidence=evidence)
        )
    return validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(optimization_experiment_evidence=evidence)
    )


def claimed_original_receipt(evidence):
    """Original receipt factories model an already transported acceptance claim."""
    if evidence.get("federated_projection") is True:
        return _join_payload(
            status=JOIN_STATUS_COMPLETE,
            reason="FEDERATED_OFFLINE_EVIDENCE_RETURN_JOIN_ONLY_NOT_M4_NOT_LEARNED",
            surface_execution_identity=evidence["surface_execution_identity"],
            evidence_digest=evidence["content_hash"],
            record_id=evidence["record_id"],
            return_join_identity=derive_federated_return_join_identity_v1(
                surface_execution_identity=evidence["surface_execution_identity"],
                optimization_experiment_evidence_digest=evidence["content_hash"],
            ),
            reproducibility_digest=evidence["reproducibility_digest"],
        )
    return _ack_payload(
        status=STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
        reason="OFFLINE_EVIDENCE_INPUT_ONLY_NOT_LEARNED_NOT_APPLIED",
        evidence_digest=evidence["content_hash"],
        plane_identity=evidence["plane_identity"],
        reproducibility_digest=evidence["reproducibility_digest"],
        record_id=evidence["record_id"],
        target_universe_class="SELF_LEARNING_UNIVERSE",
    )


def ingest(evidence, receipt):
    if evidence.get("federated_projection") is True:
        return ingest_meta_learning_evidence_from_federated_return_join_v1(
            FederatedMetaLearningIngestRequestV1(
                federated_return_join=receipt, optimization_experiment_evidence=evidence
            )
        )
    return ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=receipt, optimization_experiment_evidence=evidence
        )
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("fault", FAULTS)
@pytest.mark.parametrize("entry", ["validate", "return", "ingest"])
def test_transport_hash_does_not_repair_a_changed_reproducibility_scope(
    tmp_path, kind, fault, entry
):
    evidence = changed_evidence(source_evidence(kind, tmp_path), fault)
    before = deepcopy(evidence)
    if entry == "validate":
        with pytest.raises(CanonicalOptimizationExperimentEvidenceError):
            validate_optimization_experiment_evidence_v1(evidence)
    elif entry == "return":
        result = return_input(evidence)
        assert result["status"] not in {
            STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
            JOIN_STATUS_COMPLETE,
        }
    else:
        result = ingest(evidence, claimed_original_receipt(evidence))
        assert result["status"] != INGEST_STATUS_COMPLETE
        assert result["meta_learning_evidence"] is None
    assert evidence == before


def valid_packet(kind, root, control):
    evidence = source_evidence(kind, root)
    original_repro = evidence["reproducibility_digest"]
    if control == "json":
        evidence = json.loads(json.dumps(evidence))
    elif control == "unscoped_annotation":
        evidence["source_note"] = "synthetic.opaque.unscoped.annotation"
        reseal_transport(evidence)
    before = deepcopy(evidence)
    validated = validate_optimization_experiment_evidence_v1(evidence)
    assert plain_v1(validated) == evidence == before
    assert evidence["reproducibility_digest"] == original_repro
    receipt = return_input(evidence)
    assert plain_v1(receipt) == plain_v1(claimed_original_receipt(evidence))
    result = ingest(evidence, receipt)
    assert result["status"] == INGEST_STATUS_COMPLETE
    meta = result["meta_learning_evidence"]
    assert meta["uncertainty"] == "UNKNOWN_UNAVAILABLE"
    assert result["canonical_meta_learning_analyzer_invoked"] is False
    route = run_meta_evidence_dual_routing_cycle_v1(
        MetaEvidenceDualRouterRequestV1(
            meta_learning_evidence=meta, semantic_routing_class="RESEARCH_CHOICE"
        )
    )
    assert route["routing_result"]["optimization_consumer_invoked"] is True
    assert route["routing_result"]["learning_consumer_invoked"] is False
    return plain_v1(
        {
            "evidence": evidence,
            "validated": validated,
            "receipt": receipt,
            "ingest": result,
            "route": route,
        }
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("control", CONTROLS)
def test_original_m5_scopes_and_unavailable_meanings_survive(tmp_path, kind, control):
    packet = valid_packet(kind, tmp_path, control)
    if kind in {"f1", "f2"}:
        assert "plane_identity" not in packet["evidence"]
        assert packet["ingest"]["meta_learning_evidence"]["support_count"] == 0
