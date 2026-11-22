"""Bind the retained P5 context body and record ID before either native producer."""

from copy import deepcopy
from dataclasses import asdict
import json

import pytest

from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.ledger_v1 import (
    AdjudicationLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1 import (
    meta_learning_routed_evidence_v1 as meta_owner,
    optimization_envelope_evidence_v1 as opt_owner,
    p5_m4_m8_governed_binding_context_v1 as owner,
    p5_m4_m8_producer_bridge_v1 as bridge,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.governance.test_p5_producer_artifact_integrity_v1 import (
    CONTROLS,
    KINDS,
    source_packet,
    terminate,
)

FAULTS = (
    "observed_at",
    "market_context_id",
    "market_context_content_digest",
    "market_observation_epoch",
    "freshness_horizon_seconds",
    "binding_digest",
    "binding_record_id",
    "domain_resealed",
    "missing_freshness",
)


def binding_packet(kind, root):
    source, context, termination, _ = source_packet(kind, root)
    if kind == "optimization":
        binding = bridge.build_optimization_binding_context_v1(
            market_context=context, optimization_experiment_evidence=source
        )
    else:
        binding = bridge.build_meta_learning_binding_context_v1(
            market_context=context, meta_learning_evidence=source
        )
    return source, context, termination, binding


def produce(kind, source, binding):
    if kind == "optimization":
        return opt_owner.produce_optimization_envelope_evidence_v1(
            optimization_experiment_evidence=source, binding_context=binding
        )
    return meta_owner.produce_meta_learning_routed_evidence_v1(
        meta_learning_evidence=source, binding_context=binding
    )


def reseal_binding(binding):
    # Original builder's two formulas; used for self-consistent foreign-domain
    # and mismatched-lineage counterexamples, not for asserting source truth.
    body = {k: v for k, v in binding.items() if k not in {"binding_digest", "binding_record_id"}}
    binding["binding_digest"] = compute_content_sha256(body)
    binding["binding_record_id"] = compute_content_sha256(
        {
            "binding_domain": owner.BINDING_DOMAIN,
            "binding_digest": binding["binding_digest"],
            "source_lineage_content_digest": binding["source_lineage_content_digest"],
        }
    )


def changed_binding(original, fault):
    changed = dict(original)
    if fault == "missing_freshness":
        del changed["freshness_horizon_seconds"]
    elif fault == "domain_resealed":
        changed["domain"] = "foreign.binding.domain"
        reseal_binding(changed)
    else:
        changed[fault] = {
            "observed_at": "2026-09-01T11:59:00Z",
            "market_context_id": "foreign.original.context",
            "market_context_content_digest": "d" * 64,
            "market_observation_epoch": 1,
            "freshness_horizon_seconds": 3601,
            "binding_digest": "d" * 64,
            "binding_record_id": "d" * 64,
        }[fault]
    return changed


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("fault", FAULTS)
@pytest.mark.parametrize("entry", ["validate", "producer"])
def test_inconsistent_binding_stops_before_new_p5_artifact(tmp_path, kind, fault, entry):
    source, _, _, binding = binding_packet(kind, tmp_path)
    changed = changed_binding(binding, fault)
    before = deepcopy(changed)
    with pytest.raises(owner.P5M4M8BindingContextError):
        if entry == "validate":
            owner.validate_p5_m4_m8_governed_evidence_binding_context_v1(changed)
        else:
            produce(kind, source, changed)
    assert changed == before


def valid_packet(kind, root, control):
    source, context, termination, binding = binding_packet(kind, root)
    if control == "json":
        binding = json.loads(json.dumps(dict(binding)))
    elif control == "annotation":
        binding = {**binding, "opaque_annotation": {"role": "context", "value": "retained"}}
    validated = owner.validate_p5_m4_m8_governed_evidence_binding_context_v1(binding)
    assert dict(validated) == dict(binding)
    artifact = produce(kind, source, validated)
    ledger = AdjudicationLedgerV1()
    result = terminate(kind, artifact, termination, ledger)
    replay = terminate(kind, artifact, termination, ledger)
    assert result.adjudication.disposition == "ADMIT"
    assert result.adjudication.envelope.trading_authority == "NONE"
    assert replay.adjudication is result.adjudication
    assert len(ledger.delivery_results) == 1
    return json.loads(
        json.dumps(
            {
                "source": source,
                "market_context": context,
                "binding": validated,
                "artifact": artifact,
                "termination": asdict(termination),
                "result": asdict(result),
                "replay": asdict(replay),
                "ledger_results": {k: asdict(v) for k, v in ledger.delivery_results.items()},
            },
            default=dict,
        )
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("control", CONTROLS)
def test_valid_binding_bytes_and_existing_a_replay_survive(tmp_path, kind, control):
    valid_packet(kind, tmp_path, control)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("fault", ["source_lineage_schema", "source_lineage_content_digest"])
def test_existing_native_source_join_remains_the_producers_responsibility(tmp_path, kind, fault):
    source, _, _, binding = binding_packet(kind, tmp_path)
    changed = dict(binding)
    changed[fault] = "foreign.source.schema" if fault.endswith("schema") else "d" * 64
    reseal_binding(changed)
    owner.validate_p5_m4_m8_governed_evidence_binding_context_v1(changed)
    error = (
        opt_owner.OptimizationEnvelopeEvidenceError
        if kind == "optimization"
        else meta_owner.MetaLearningRoutedEvidenceError
    )
    with pytest.raises(error, match="BINDING_"):
        produce(kind, source, changed)
