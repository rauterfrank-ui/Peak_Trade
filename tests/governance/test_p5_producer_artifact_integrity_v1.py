"""Original P5 artifacts must retain their own witnesses before Component A."""

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.ledger_v1 import (
    AdjudicationLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1 import (
    adapters_v1 as adapters,
    ingress_v1 as ingress,
    meta_learning_routed_evidence_v1 as meta_owner,
    optimization_envelope_evidence_v1 as opt_owner,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.p5_m4_m8_producer_bridge_v1 import (
    bridge_m5_to_optimization_envelope_evidence_v1,
    bridge_m6_to_meta_learning_routed_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.governance.test_p5_m4_m8_optimization_meta_producer_final_closure_v1 import (
    _m4_m8_cycle,
)
from tests.learning.test_loop_a_conditioned_learning_evidence_v1 import _observation_for_n
from tests.learning.test_market_context_realized_behavior_join_v1 import _context_for_observation

ROOT = Path(__file__).resolve().parents[2]
KINDS = ("optimization", "meta")
CONTROLS = ("original", "json", "annotation")
FAULTS = tuple(
    (fault, reseal)
    for fault in (
        "source_parent",
        "binding",
        "reproducibility",
        "identity",
        "domain",
        "producer_version",
        "binding_schema",
        "source_schema",
        "trading_effect",
    )
    for reseal in (False, True)
) + (("typed_payload", False),)


def source_packet(kind, root):
    cycle = _m4_m8_cycle(root)["cycle"]
    context = _context_for_observation(_observation_for_n(n_bars=2))
    termination = adapters.default_termination_context_from_market_context_v1(
        context, market_observation_epoch=0
    )
    if kind == "optimization":
        source = cycle["optimization_experiment_evidence"]
        artifact = bridge_m5_to_optimization_envelope_evidence_v1(
            optimization_experiment_evidence=source, market_context=context
        )
    else:
        source = cycle["meta_learning_evidence"]
        artifact = bridge_m6_to_meta_learning_routed_evidence_v1(
            meta_learning_evidence=source, market_context=context
        )
    return source, context, termination, artifact


def interfaces(kind):
    if kind == "optimization":
        return (
            opt_owner.validate_optimization_envelope_evidence_v1,
            opt_owner.OptimizationEnvelopeEvidenceError,
            adapters.adapt_optimization_envelope_evidence_v1,
            ingress.terminate_optimization_envelope_at_a_v1,
        )
    return (
        meta_owner.validate_meta_learning_routed_evidence_v1,
        meta_owner.MetaLearningRoutedEvidenceError,
        adapters.adapt_meta_learning_routed_evidence_v1,
        ingress.terminate_meta_learning_routed_at_a_v1,
    )


def changed_artifact(original, kind, fault, reseal):
    changed = plain_v1(original)
    if fault == "source_parent":
        key = (
            "source_optimization_experiment_evidence_digest"
            if kind == "optimization"
            else "source_meta_learning_reproducibility_digest"
        )
        changed[key] = "d" * 64
    elif fault == "binding":
        changed["binding_context_digest"] = "d" * 64
    elif fault == "reproducibility":
        changed["reproducibility_digest"] = "d" * 64
    elif fault == "identity":
        key = "envelope_evidence_id" if kind == "optimization" else "routed_evidence_id"
        changed[key] = "d" * 48
    elif fault == "domain":
        changed["domain"] = "foreign.p5.domain"
    elif fault == "producer_version":
        changed["producer_version"] = "foreign.v1"
    elif fault == "binding_schema":
        changed["binding_context_schema_version"] = "foreign.binding.v1"
    elif fault == "source_schema":
        key = (
            "source_optimization_experiment_evidence_schema_version"
            if kind == "optimization"
            else "source_meta_learning_evidence_schema_version"
        )
        changed[key] = "foreign.source.v1"
    elif fault == "trading_effect":
        changed["trading_selection_effect"] = "ACTIVE"
    else:
        changed["typed_payload_digest"] = "d" * 64
    if reseal:
        changed["content_hash"] = compute_content_sha256(
            {key: value for key, value in changed.items() if key != "content_hash"}
        )
    return changed


def terminate(kind, artifact, termination, ledger):
    _, _, _, entry = interfaces(kind)
    return entry(
        artifact,
        source_artifact_schema=artifact["schema_version"],
        source_content_digest=artifact["content_hash"],
        termination=termination,
        repo_root=ROOT,
        ledger=ledger,
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("fault,reseal", FAULTS)
@pytest.mark.parametrize("entry", ["validate", "adapter", "ingress"])
def test_changed_p5_witness_cannot_become_component_a_evidence(
    tmp_path, monkeypatch, kind, fault, reseal, entry
):
    _, _, termination, artifact = source_packet(kind, tmp_path)
    changed = changed_artifact(artifact, kind, fault, reseal)
    before = deepcopy(changed)
    validate, error, adapt, _ = interfaces(kind)
    if entry == "validate":
        with pytest.raises(error):
            validate(changed)
    elif entry == "adapter":
        with pytest.raises(adapters.ProducerAdapterError):
            adapt(changed, termination=termination)
    else:
        calls = []
        original = ingress.adjudicate_evidence_intake_v1

        def observe(*args, **kwargs):
            calls.append(True)
            return original(*args, **kwargs)

        monkeypatch.setattr(ingress, "adjudicate_evidence_intake_v1", observe)
        ledger = AdjudicationLedgerV1()
        result = terminate(kind, changed, termination, ledger)
        assert result.adjudication.disposition == "REJECT"
        assert result.adjudication.reason_codes == ("artifact_malformed",)
        assert result.adjudication.envelope is None
        assert calls == []
        assert ledger.delivery_results == ledger.admitted_slots == {}
    assert changed == before


def valid_packet(kind, root, control):
    source, context, termination, artifact = source_packet(kind, root)
    if control != "original":
        artifact = plain_v1(artifact)
    if control == "json":
        artifact = json.loads(json.dumps(artifact))
    if control == "annotation":
        artifact["source_note"] = "synthetic.opaque.annotation"
        artifact["content_hash"] = compute_content_sha256(
            {key: value for key, value in artifact.items() if key != "content_hash"}
        )
    validate, _, adapt, _ = interfaces(kind)
    validated = validate(artifact)
    assert plain_v1(validated) == plain_v1(artifact)
    intake = adapt(artifact, termination=termination)
    ledger = AdjudicationLedgerV1()
    result = terminate(kind, artifact, termination, ledger)
    replay = terminate(kind, artifact, termination, ledger)
    assert result.adjudication.disposition == replay.adjudication.disposition == "ADMIT"
    assert result.adjudication.envelope.trading_authority == "NONE"
    assert replay.adjudication is result.adjudication
    assert len(ledger.delivery_results) == 1
    return json.loads(
        json.dumps(
            {
                "source": source,
                "context": context,
                "artifact": artifact,
                "validated": validated,
                "intake": asdict(intake),
                "termination": asdict(result),
                "replay": asdict(replay),
                "ledger_results": {
                    key: asdict(value) for key, value in ledger.delivery_results.items()
                },
                "ledger_fingerprints": dict(ledger.delivery_fingerprints),
            },
            default=dict,
        )
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("control", CONTROLS)
def test_valid_p5_mapping_json_annotation_and_idempotency_survive(tmp_path, kind, control):
    valid_packet(kind, tmp_path, control)


@pytest.mark.parametrize("kind", KINDS)
def test_existing_forbidden_effect_error_keeps_precedence(tmp_path, kind):
    _, _, _, artifact = source_packet(kind, tmp_path)
    changed = plain_v1(artifact)
    changed["external_effect_authorized"] = True
    validate, error, _, _ = interfaces(kind)
    with pytest.raises(error, match="EXTERNAL_EFFECT_MUST_BE_FALSE"):
        validate(changed)
