"""Contract tests for P1 Master V2 / Double Play Evidence & Input Plane."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1 import (
    BoundedL6EvidenceKindV1,
    CanonicalDpLayerInputBindingV1,
    CanonicalMasterV2EvidenceEnvelopeV1,
    EvidenceProducerFamilyV1,
    InstrumentBindingV1,
    prove_p1_authority_contracts_and_schemas_v1,
    validate_canonical_dp_layer_input_binding_v1,
    validate_canonical_master_v2_evidence_envelope_v1,
    validate_component_a_authority_contract_v1,
    validate_component_b_authority_contract_v1,
    validate_l6_bounded_typed_external_evidence_input_v1,
    materialize_l6_bounded_typed_external_evidence_input_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.digest_v1 import (
    compute_envelope_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    AdjudicationContextV1,
    BindingContextV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.reason_codes_v1 import (
    DpLayerBindingFailureCodeV1,
    EvidenceEnvelopeFailureCodeV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1

REPO_ROOT = Path(__file__).resolve().parents[2]


def _instrument() -> InstrumentBindingV1:
    return InstrumentBindingV1(
        instrument_id="SOL-USDT-SWAP",
        venue="OKX",
        venue_instrument_id="SOL-USDT-SWAP",
    )


def _valid_envelope(**overrides: object) -> CanonicalMasterV2EvidenceEnvelopeV1:
    base = dict(
        envelope_id="env-1",
        producer_family=EvidenceProducerFamilyV1.MARKET_INTELLIGENCE,
        evidence_kind=BoundedL6EvidenceKindV1.MI_MARKET_CONTEXT_DESCRIPTIVE_V1,
        instrument=_instrument(),
        market_observation_epoch=3,
        observed_at_unix=1_700_000_000.0,
        freshness_horizon_seconds=3600,
        source_evidence_digest="a" * 64,
        typed_payload_digest="b" * 64,
        provenance_refs=("prov:1",),
    )
    base.update(overrides)
    return CanonicalMasterV2EvidenceEnvelopeV1(**base)  # type: ignore[arg-type]


def test_component_authority_contracts_ok() -> None:
    assert validate_component_a_authority_contract_v1().ok
    assert validate_component_b_authority_contract_v1().ok


def test_envelope_fail_closed_on_stale_freshness() -> None:
    env = _valid_envelope(observed_at_unix=1_700_000_000.0, freshness_horizon_seconds=60)
    result = validate_canonical_master_v2_evidence_envelope_v1(
        env,
        context=AdjudicationContextV1(evaluated_at_unix=1_700_010_000.0),
    )
    assert not result.ok
    assert EvidenceEnvelopeFailureCodeV1.FRESHNESS_STALE.value in result.failure_codes


def test_envelope_rejects_proposed_d_t_in_extra_fields() -> None:
    env = _valid_envelope(extra_fields={"proposed_d_t": 25.0})
    result = validate_canonical_master_v2_evidence_envelope_v1(
        env,
        context=AdjudicationContextV1(evaluated_at_unix=1_700_000_100.0),
    )
    assert not result.ok
    assert DpLayerBindingFailureCodeV1.PROPOSED_D_T_FIELD_FORBIDDEN.value in result.failure_codes


def test_binding_rejects_direct_producer_to_b() -> None:
    env = _valid_envelope()
    digest = compute_envelope_digest_v1(asdict(env))
    binding = CanonicalDpLayerInputBindingV1(
        binding_id="bind-1",
        target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
        envelope_digest=digest,
        instrument=_instrument(),
        market_observation_epoch=3,
        nullline_provenance_epoch=3,
        binding_evaluated_at_unix=1_700_000_100.0,
        producer_to_b_direct=True,
    )
    result = validate_canonical_dp_layer_input_binding_v1(
        binding,
        context=BindingContextV1(
            evaluated_at_unix=1_700_000_100.0,
            expected_envelope_digest=digest,
            adjudicated_envelope=env,
        ),
    )
    assert not result.ok
    assert DpLayerBindingFailureCodeV1.DIRECT_PRODUCER_TO_B_FORBIDDEN.value in result.failure_codes


def test_typed_l6_input_materialization_has_no_d_t_fields() -> None:
    env = _valid_envelope()
    digest = compute_envelope_digest_v1(asdict(env))
    binding = CanonicalDpLayerInputBindingV1(
        binding_id="bind-1",
        target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
        envelope_digest=digest,
        instrument=_instrument(),
        market_observation_epoch=3,
        nullline_provenance_epoch=3,
        binding_evaluated_at_unix=1_700_000_100.0,
    )
    assert validate_canonical_dp_layer_input_binding_v1(
        binding,
        context=BindingContextV1(
            evaluated_at_unix=1_700_000_100.0,
            expected_envelope_digest=digest,
            adjudicated_envelope=env,
        ),
    ).ok
    typed = materialize_l6_bounded_typed_external_evidence_input_v1(
        binding=binding,
        envelope=env,
        input_id="l6-in-1",
    )
    payload = asdict(typed)
    assert "proposed_d_t" not in payload
    assert "d_t" not in payload
    assert typed.interpretation_authority == "L6_ONLY"
    assert validate_l6_bounded_typed_external_evidence_input_v1(
        typed,
        binding=binding,
        envelope=env,
    ).ok


def test_p1_proof_bundle_proven_complete() -> None:
    proof = prove_p1_authority_contracts_and_schemas_v1(repo_root=REPO_ROOT)
    assert proof["verdict"] == "PROVEN_COMPLETE"
    assert proof["runtime_ab_implementation_detected"] is False
