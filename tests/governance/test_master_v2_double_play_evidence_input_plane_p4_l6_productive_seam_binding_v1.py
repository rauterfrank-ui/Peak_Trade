"""Contract, authority, and deterministic replay tests for P4 productive L6 seam binding."""

from __future__ import annotations

from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    L6_TYPED_INPUT_SCHEMA_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
    EvidenceProducerFamilyV1,
    InstrumentBindingV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeRecordV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1 import (
    IMPLEMENTS_PRODUCTIVE_L6_SEAM_BINDING,
    L6_PRODUCTIVE_BINDING,
    PRODUCTIVE_DP_SEAM_BOUND,
    PRODUCTIVE_L6_BINDING_AUTHORIZED,
    ProductiveL6SeamBindingContextV1,
    ProductiveL6SeamBindingRequestV1,
    ProductiveL6SeamLedgerV1,
    prove_p4_l6_productive_seam_binding_v1,
    run_productive_l6_seam_binding_v1,
    validate_productive_l6_seam_authority_contract_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    SEAM_BIND_DISPOSITION,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import NullLineStateV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1

REPO_ROOT = Path(__file__).resolve().parents[2]


def _instrument() -> InstrumentBindingV1:
    return InstrumentBindingV1(
        instrument_id="SOL-USDT-SWAP",
        venue="OKX",
        venue_instrument_id="SOL-USDT-SWAP",
    )


def _request() -> ProductiveL6SeamBindingRequestV1:
    intake = EvidenceIntakeRecordV1(
        delivery_id="del-p4-test",
        envelope_id="env-p4-test",
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
    return ProductiveL6SeamBindingRequestV1(
        seam_id="seam-test-1",
        intake=intake,
        binding_id="bind-test-1",
        target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
        target_contract_version=L6_TYPED_INPUT_SCHEMA_VERSION,
        nullline_provenance_epoch=3,
    )


def _context() -> ProductiveL6SeamBindingContextV1:
    return ProductiveL6SeamBindingContextV1(
        evaluated_at_unix=1_700_000_200.0,
        expected_instrument=_instrument(),
        expected_market_observation_epoch=3,
        expected_nullline_provenance_epoch=3,
        mechanical_proposed_d_t=0.02,
        nullline_for_mechanical_l6=NullLineStateV1(
            instrument_id="SOL-USDT-SWAP",
            nullline_price=120.0,
            provenance_mark_epoch=3,
        ),
    )


def test_p4_authority_constants() -> None:
    assert IMPLEMENTS_PRODUCTIVE_L6_SEAM_BINDING is True
    assert PRODUCTIVE_L6_BINDING_AUTHORIZED is True
    assert L6_PRODUCTIVE_BINDING is True
    assert PRODUCTIVE_DP_SEAM_BOUND is True
    assert validate_productive_l6_seam_authority_contract_v1().ok


def test_productive_seam_bind_end_to_end() -> None:
    result = run_productive_l6_seam_binding_v1(
        _request(),
        context=_context(),
        repo_root=REPO_ROOT,
        seam_ledger=ProductiveL6SeamLedgerV1(),
    )
    assert result.disposition == SEAM_BIND_DISPOSITION
    assert result.l6_admission is not None
    assert result.l6_consumption_evidence_id is not None
    assert result.l6_generator_output is not None
    assert result.l6_generator_output.fail_closed is False


def test_p4_proof_bundle_proven_complete() -> None:
    proof = prove_p4_l6_productive_seam_binding_v1(repo_root=REPO_ROOT)
    assert proof["verdict"] == "PROVEN_COMPLETE"
    assert all(proof["proof_obligations"].values())
