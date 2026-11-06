"""Contract, authority, and deterministic replay tests for P2 Component A runtime."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
    EvidenceProducerFamilyV1,
    InstrumentBindingV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.reason_codes_v1 import (
    EvidenceEnvelopeFailureCodeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1 import (
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    A_RUNTIME_IMPLEMENTED,
    A_RUNTIME_REACHABLE,
    IMPLEMENTS_COMPONENT_A_RUNTIME,
    AdjudicationLedgerV1,
    EvidenceIntakeAdjudicationContextV1,
    EvidenceIntakeRecordV1,
    adjudicate_evidence_intake_v1,
    load_producer_registry_v1,
    prove_p2_evidence_adjudicator_runtime_v1,
    validate_component_a_runtime_authority_contract_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    CONFLICT_DISPOSITION,
    REJECT_DISPOSITION,
    STALE_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.reason_codes_v1 import (
    AdjudicationIntakeFailureCodeV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _instrument() -> InstrumentBindingV1:
    return InstrumentBindingV1(
        instrument_id="SOL-USDT-SWAP",
        venue="OKX",
        venue_instrument_id="SOL-USDT-SWAP",
    )


def _context(**overrides: object) -> EvidenceIntakeAdjudicationContextV1:
    base = dict(
        evaluated_at_unix=1_700_000_100.0,
        expected_instrument=_instrument(),
        expected_market_observation_epoch=3,
    )
    base.update(overrides)
    return EvidenceIntakeAdjudicationContextV1(**base)  # type: ignore[arg-type]


def _intake(**overrides: object) -> EvidenceIntakeRecordV1:
    base = dict(
        delivery_id="del-1",
        envelope_id="env-1",
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
        confidence_score=0.75,
        quality_score=0.8,
    )
    base.update(overrides)
    return EvidenceIntakeRecordV1(**base)  # type: ignore[arg-type]


def test_p2_authority_constants() -> None:
    assert IMPLEMENTS_COMPONENT_A_RUNTIME is True
    assert A_RUNTIME_IMPLEMENTED is True
    assert A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert A_RUNTIME_REACHABLE is False
    assert validate_component_a_runtime_authority_contract_v1().ok


def test_admit_produces_p1_envelope_with_preserved_quality() -> None:
    registry = load_producer_registry_v1(REPO_ROOT)
    result = adjudicate_evidence_intake_v1(
        _intake(), context=_context(), registry=registry, ledger=AdjudicationLedgerV1()
    )
    assert result.disposition == ADMIT_DISPOSITION
    assert result.envelope is not None
    assert result.envelope.trading_authority == "NONE"
    assert result.envelope.extra_fields["confidence_score"] == 0.75
    assert result.envelope.extra_fields["quality_score"] == 0.8
    assert result.envelope_digest is not None


def test_unregistered_producer_rejects() -> None:
    registry = load_producer_registry_v1(REPO_ROOT)
    result = adjudicate_evidence_intake_v1(
        _intake(producer_id="unknown"),
        context=_context(),
        registry=registry,
        ledger=AdjudicationLedgerV1(),
    )
    assert result.disposition == REJECT_DISPOSITION
    assert AdjudicationIntakeFailureCodeV1.PRODUCER_UNREGISTERED.value in result.reason_codes


def test_stale_evidence_rejects_with_stale_disposition() -> None:
    registry = load_producer_registry_v1(REPO_ROOT)
    result = adjudicate_evidence_intake_v1(
        _intake(freshness_horizon_seconds=30),
        context=_context(evaluated_at_unix=1_700_010_000.0),
        registry=registry,
        ledger=AdjudicationLedgerV1(),
    )
    assert result.disposition == STALE_DISPOSITION
    assert EvidenceEnvelopeFailureCodeV1.FRESHNESS_STALE.value in result.reason_codes


def test_conflict_and_deterministic_replay() -> None:
    registry = load_producer_registry_v1(REPO_ROOT)
    ledger = AdjudicationLedgerV1()
    ctx = _context()
    first = adjudicate_evidence_intake_v1(
        _intake(delivery_id="d1", source_evidence_digest="c" * 64),
        context=ctx,
        registry=registry,
        ledger=ledger,
    )
    conflict = adjudicate_evidence_intake_v1(
        _intake(
            delivery_id="d2",
            envelope_id="env-2",
            source_evidence_digest="d" * 64,
        ),
        context=ctx,
        registry=registry,
        ledger=ledger,
    )
    replay = adjudicate_evidence_intake_v1(
        _intake(delivery_id="d1", source_evidence_digest="c" * 64),
        context=ctx,
        registry=registry,
        ledger=ledger,
    )
    assert first.disposition == ADMIT_DISPOSITION
    assert conflict.disposition == CONFLICT_DISPOSITION
    assert replay.adjudication_digest == first.adjudication_digest


def test_identical_inputs_identical_digest_across_ledgers() -> None:
    registry = load_producer_registry_v1(REPO_ROOT)
    ctx = _context()
    a = adjudicate_evidence_intake_v1(
        _intake(delivery_id="det-1"),
        context=ctx,
        registry=registry,
        ledger=AdjudicationLedgerV1(),
    )
    b = adjudicate_evidence_intake_v1(
        _intake(delivery_id="det-1"),
        context=ctx,
        registry=registry,
        ledger=AdjudicationLedgerV1(),
    )
    assert a.adjudication_digest == b.adjudication_digest
    assert asdict(a.envelope) == asdict(b.envelope)


def test_p2_proof_bundle_proven_complete() -> None:
    proof = prove_p2_evidence_adjudicator_runtime_v1(repo_root=REPO_ROOT)
    assert proof["verdict"] == "PROVEN_COMPLETE"
    assert all(proof["proof_obligations"].values())
