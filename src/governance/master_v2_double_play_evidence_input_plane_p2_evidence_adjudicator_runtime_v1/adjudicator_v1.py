"""Bounded Component A evidence intake + adjudication runtime."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    AdjudicationContextV1,
    CanonicalMasterV2EvidenceEnvelopeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.reason_codes_v1 import (
    EvidenceEnvelopeFailureCodeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.validator_v1 import (
    validate_canonical_master_v2_evidence_envelope_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    CONFLICT_DISPOSITION,
    REJECT_DISPOSITION,
    STALE_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.digest_v1 import (
    compute_intake_fingerprint_digest_v1,
    envelope_digest_from_model_v1,
    finalize_adjudication_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.ledger_v1 import (
    AdjudicationLedgerV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeAdjudicationContextV1,
    EvidenceIntakeRecordV1,
    MasterV2EvidenceAdjudicationResultV1,
    RegisteredProducerEntryV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.normalize_v1 import (
    intake_malformed_fields_v1,
    normalize_evidence_intake_record_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.reason_codes_v1 import (
    AdjudicationIntakeFailureCodeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.registry_v1 import (
    lookup_registered_producer_v1,
)


def _reject(
    intake: EvidenceIntakeRecordV1,
    *,
    disposition: str,
    reason_codes: tuple[str, ...],
) -> MasterV2EvidenceAdjudicationResultV1:
    return finalize_adjudication_digest_v1(
        MasterV2EvidenceAdjudicationResultV1(
            delivery_id=intake.delivery_id,
            disposition=disposition,
            reason_codes=reason_codes,
            adjudication_digest="",
            envelope=None,
            envelope_digest=None,
            dedup_replay=False,
        )
    )


def _materialize_envelope_v1(intake: EvidenceIntakeRecordV1) -> CanonicalMasterV2EvidenceEnvelopeV1:
    extra = dict(intake.extra_fields)
    if intake.confidence_score is not None:
        extra.setdefault("confidence_score", intake.confidence_score)
    if intake.quality_score is not None:
        extra.setdefault("quality_score", intake.quality_score)
    if intake.lineage_refs:
        extra["lineage_refs"] = list(intake.lineage_refs)
    return CanonicalMasterV2EvidenceEnvelopeV1(
        envelope_id=intake.envelope_id,
        producer_family=intake.producer_family,
        evidence_kind=intake.evidence_kind,
        instrument=intake.instrument,
        market_observation_epoch=intake.market_observation_epoch,
        observed_at_unix=intake.observed_at_unix,
        freshness_horizon_seconds=intake.freshness_horizon_seconds,
        source_evidence_digest=intake.source_evidence_digest,
        typed_payload_digest=intake.typed_payload_digest,
        provenance_refs=intake.provenance_refs,
        extra_fields=extra,
    )


def adjudicate_evidence_intake_v1(
    intake: EvidenceIntakeRecordV1 | None,
    *,
    context: EvidenceIntakeAdjudicationContextV1,
    registry: Iterable[RegisteredProducerEntryV1],
    ledger: AdjudicationLedgerV1 | None = None,
) -> MasterV2EvidenceAdjudicationResultV1:
    if intake is None:
        return finalize_adjudication_digest_v1(
            MasterV2EvidenceAdjudicationResultV1(
                delivery_id="",
                disposition=REJECT_DISPOSITION,
                reason_codes=(AdjudicationIntakeFailureCodeV1.INTAKE_MISSING.value,),
                adjudication_digest="",
                envelope=None,
                envelope_digest=None,
                dedup_replay=False,
            )
        )
    ledger = ledger or AdjudicationLedgerV1()
    normalized = normalize_evidence_intake_record_v1(intake)
    if normalized.delivery_id in ledger.delivery_results:
        fingerprint = compute_intake_fingerprint_digest_v1(normalized)
        if ledger.delivery_fingerprints.get(normalized.delivery_id) != fingerprint:
            result = _reject(
                normalized,
                disposition=REJECT_DISPOSITION,
                reason_codes=(AdjudicationIntakeFailureCodeV1.DUPLICATE_DELIVERY_DIVERGENT.value,),
            )
            return result
    prior = ledger.prior_delivery_result(normalized)
    if prior is not None:
        return prior

    malformed = intake_malformed_fields_v1(normalized)
    if malformed:
        result = _reject(normalized, disposition=REJECT_DISPOSITION, reason_codes=malformed)
        ledger.record_result(normalized, result)
        return result

    if (
        context.expected_instrument is not None
        and normalized.instrument != context.expected_instrument
    ):
        result = _reject(
            normalized,
            disposition=REJECT_DISPOSITION,
            reason_codes=(AdjudicationIntakeFailureCodeV1.INSTRUMENT_BINDING_MISMATCH.value,),
        )
        ledger.record_result(normalized, result)
        return result

    if context.expected_market_observation_epoch is not None and not context.allow_epoch_mismatch:
        if normalized.market_observation_epoch != context.expected_market_observation_epoch:
            result = _reject(
                normalized,
                disposition=REJECT_DISPOSITION,
                reason_codes=(AdjudicationIntakeFailureCodeV1.EPOCH_BINDING_MISMATCH.value,),
            )
            ledger.record_result(normalized, result)
            return result

    _, registry_failures = lookup_registered_producer_v1(normalized, registry)
    if registry_failures:
        result = _reject(normalized, disposition=REJECT_DISPOSITION, reason_codes=registry_failures)
        ledger.record_result(normalized, result)
        return result

    slot = ledger.slot_key(normalized)
    existing_digest = ledger.admitted_slots.get(slot)
    if existing_digest is not None and existing_digest != normalized.source_evidence_digest:
        result = _reject(
            normalized,
            disposition=CONFLICT_DISPOSITION,
            reason_codes=(AdjudicationIntakeFailureCodeV1.EVIDENCE_CONFLICT.value,),
        )
        ledger.record_result(normalized, result)
        return result

    envelope = _materialize_envelope_v1(normalized)
    validation = validate_canonical_master_v2_evidence_envelope_v1(
        envelope,
        context=AdjudicationContextV1(evaluated_at_unix=context.evaluated_at_unix),
    )
    if not validation.ok:
        stale_only = validation.failure_codes == (
            EvidenceEnvelopeFailureCodeV1.FRESHNESS_STALE.value,
        )
        disposition = STALE_DISPOSITION if stale_only else REJECT_DISPOSITION
        result = _reject(
            normalized,
            disposition=disposition,
            reason_codes=validation.failure_codes,
        )
        ledger.record_result(normalized, result)
        return result

    env_digest = envelope_digest_from_model_v1(asdict(envelope))
    admit = finalize_adjudication_digest_v1(
        MasterV2EvidenceAdjudicationResultV1(
            delivery_id=normalized.delivery_id,
            disposition=ADMIT_DISPOSITION,
            reason_codes=(),
            adjudication_digest="",
            envelope=envelope,
            envelope_digest=env_digest,
            dedup_replay=False,
        )
    )
    ledger.record_result(normalized, admit)
    return admit


def run_component_a_runtime_v1(
    intake: EvidenceIntakeRecordV1,
    *,
    context: EvidenceIntakeAdjudicationContextV1,
    registry: Iterable[RegisteredProducerEntryV1],
    ledger: AdjudicationLedgerV1 | None = None,
) -> MasterV2EvidenceAdjudicationResultV1:
    """Stable entrypoint name for bounded Component A runtime (isolated; not productively bound)."""
    return adjudicate_evidence_intake_v1(
        intake,
        context=context,
        registry=registry,
        ledger=ledger,
    )
