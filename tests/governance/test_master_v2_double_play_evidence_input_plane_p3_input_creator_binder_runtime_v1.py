"""Contract, authority, and deterministic replay tests for P3 Component B runtime."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    L6_TYPED_INPUT_SCHEMA_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
    EvidenceProducerFamilyV1,
    InstrumentBindingV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1 import (
    AdjudicationLedgerV1,
    EvidenceIntakeAdjudicationContextV1,
    EvidenceIntakeRecordV1,
    adjudicate_evidence_intake_v1,
    load_producer_registry_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    REJECT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    MasterV2EvidenceAdjudicationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1 import (
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    B_RUNTIME_IMPLEMENTED,
    B_RUNTIME_REACHABLE,
    IMPLEMENTS_COMPONENT_B_RUNTIME,
    BindingLedgerV1,
    LayerInputBindingContextV1,
    LayerInputBindingRequestV1,
    bind_layer_input_from_adjudication_v1,
    prove_p3_input_creator_binder_runtime_v1,
    validate_component_b_runtime_authority_contract_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    BIND_DISPOSITION,
    NO_BIND_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.reason_codes_v1 import (
    LayerInputBindingIntakeFailureCodeV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1

REPO_ROOT = Path(__file__).resolve().parents[2]


def _instrument() -> InstrumentBindingV1:
    return InstrumentBindingV1(
        instrument_id="SOL-USDT-SWAP",
        venue="OKX",
        venue_instrument_id="SOL-USDT-SWAP",
    )


def _admit() -> MasterV2EvidenceAdjudicationResultV1:
    registry = load_producer_registry_v1(REPO_ROOT)
    intake = EvidenceIntakeRecordV1(
        delivery_id="del-b-1",
        envelope_id="env-b-1",
        producer_id="mi.market_context_descriptive.producer",
        producer_version="1.0.0",
        evidence_type_version="1.0.0",
        producer_family=EvidenceProducerFamilyV1.MARKET_INTELLIGENCE,
        evidence_kind=BoundedL6EvidenceKindV1.MI_MARKET_CONTEXT_DESCRIPTIVE_V1,
        instrument=_instrument(),
        market_observation_epoch=3,
        observed_at_unix=1_700_000_000.0,
        freshness_horizon_seconds=3600,
        source_evidence_digest="a" * 64,
        typed_payload_digest="b" * 64,
        provenance_refs=("prov:1",),
        lineage_refs=("lineage:1",),
    )
    ctx = EvidenceIntakeAdjudicationContextV1(
        evaluated_at_unix=1_700_000_100.0,
        expected_instrument=_instrument(),
        expected_market_observation_epoch=3,
    )
    return adjudicate_evidence_intake_v1(
        intake,
        context=ctx,
        registry=registry,
        ledger=AdjudicationLedgerV1(),
    )


def _context(**overrides: object) -> LayerInputBindingContextV1:
    base = dict(
        evaluated_at_unix=1_700_000_150.0,
        expected_instrument=_instrument(),
        expected_market_observation_epoch=3,
    )
    base.update(overrides)
    return LayerInputBindingContextV1(**base)  # type: ignore[arg-type]


def _request(
    adjudication: MasterV2EvidenceAdjudicationResultV1,
    **overrides: object,
) -> LayerInputBindingRequestV1:
    base = dict(
        binding_id="bind-test-1",
        target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
        target_contract_version=L6_TYPED_INPUT_SCHEMA_VERSION,
        nullline_provenance_epoch=3,
        adjudication=adjudication,
    )
    base.update(overrides)
    return LayerInputBindingRequestV1(**base)  # type: ignore[arg-type]


def test_p3_authority_constants() -> None:
    assert IMPLEMENTS_COMPONENT_B_RUNTIME is True
    assert B_RUNTIME_IMPLEMENTED is True
    assert B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert B_RUNTIME_REACHABLE is False
    assert validate_component_b_runtime_authority_contract_v1().ok


def test_bind_from_admit_produces_l6_typed_input() -> None:
    admit = _admit()
    assert admit.disposition == ADMIT_DISPOSITION
    result = bind_layer_input_from_adjudication_v1(
        _request(admit),
        context=_context(),
        ledger=BindingLedgerV1(),
    )
    assert result.disposition == BIND_DISPOSITION
    assert result.binding is not None
    assert result.typed_layer_input is not None
    assert result.typed_layer_input.interpretation_authority == "L6_ONLY"
    assert "proposed_d_t" not in asdict(result.typed_layer_input)


def test_reject_non_admit_adjudication() -> None:
    rejected = MasterV2EvidenceAdjudicationResultV1(
        delivery_id="r1",
        disposition=REJECT_DISPOSITION,
        reason_codes=("reject",),
        adjudication_digest="d" * 64,
        envelope=None,
        envelope_digest=None,
    )
    result = bind_layer_input_from_adjudication_v1(
        _request(rejected),
        context=_context(),
        ledger=BindingLedgerV1(),
    )
    assert result.disposition == NO_BIND_DISPOSITION
    assert LayerInputBindingIntakeFailureCodeV1.ADJUDICATION_NOT_ADMIT.value in result.reason_codes


def test_deterministic_replay_and_idempotency() -> None:
    admit = _admit()
    ctx = _context()
    a = bind_layer_input_from_adjudication_v1(
        _request(admit, binding_id="bind-det"),
        context=ctx,
        ledger=BindingLedgerV1(),
    )
    b = bind_layer_input_from_adjudication_v1(
        _request(admit, binding_id="bind-det"),
        context=ctx,
        ledger=BindingLedgerV1(),
    )
    assert a.binding_result_digest == b.binding_result_digest
    ledger = BindingLedgerV1()
    first = bind_layer_input_from_adjudication_v1(
        _request(admit, binding_id="bind-led"),
        context=ctx,
        ledger=ledger,
    )
    second = bind_layer_input_from_adjudication_v1(
        _request(admit, binding_id="bind-led"),
        context=ctx,
        ledger=ledger,
    )
    assert first.binding_result_digest == second.binding_result_digest
    assert second.dedup_replay is True


def test_p3_proof_bundle_proven_complete() -> None:
    proof = prove_p3_input_creator_binder_runtime_v1(repo_root=REPO_ROOT)
    assert proof["verdict"] == "PROVEN_COMPLETE"
    assert all(proof["proof_obligations"].values())
