"""Typed producer adapters mapping CURRENT artifacts to P2 A intake (representation only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
    EvidenceProducerFamilyV1,
    InstrumentBindingV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeRecordV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    EVIDENCE_TYPE_VERSION,
    LEARNING_PRODUCER_ID,
    LEARNING_PRODUCER_VERSION,
    MI_PRODUCER_ID,
    MI_PRODUCER_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.models_v1 import (
    ProducerEvidenceTerminationContextV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.reason_codes_v1 import (
    ProducerIngressFailureCodeV1,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import require_event_time_utc
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    validate_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
    CONDITIONED_BINDING_SCHEMA,
    validate_mi_learning_evidence_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex


class ProducerAdapterError(ValueError):
    """Fail-closed producer adapter mapping."""


def _parse_observed_at_unix(observed_at: str) -> float:
    text = require_event_time_utc(observed_at, "observed_at")
    dt = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.timestamp()


def instrument_binding_from_ref_v1(instrument_ref: str) -> InstrumentBindingV1:
    ref = instrument_ref.strip()
    if not ref:
        raise ProducerAdapterError(
            ProducerIngressFailureCodeV1.INSTRUMENT_BINDING_DERIVATION_FAILED.value
        )
    return InstrumentBindingV1(
        instrument_id=ref,
        venue="OFFLINE_CONTEXT",
        venue_instrument_id=ref,
    )


def default_termination_context_from_market_context_v1(
    market_context: Mapping[str, Any],
    *,
    market_observation_epoch: int,
    freshness_horizon_seconds: int = 86_400,
) -> ProducerEvidenceTerminationContextV1:
    validated = validate_market_context_v1(market_context)
    instrument = instrument_binding_from_ref_v1(str(validated["instrument_ref"]))
    observed_at_unix = _parse_observed_at_unix(str(validated["observed_at"]))
    return ProducerEvidenceTerminationContextV1(
        market_observation_epoch=market_observation_epoch,
        instrument=instrument,
        freshness_horizon_seconds=freshness_horizon_seconds,
        evaluated_at_unix=observed_at_unix + 1.0,
    )


def adapt_market_intelligence_market_context_v1(
    artifact: Mapping[str, Any],
    *,
    termination: ProducerEvidenceTerminationContextV1,
) -> EvidenceIntakeRecordV1:
    validated = validate_market_context_v1(artifact)
    content_digest = str(validated["content_digest"])
    if not is_valid_sha256_hex(content_digest):
        raise ProducerAdapterError(ProducerIngressFailureCodeV1.ARTIFACT_MALFORMED.value)
    instrument = termination.instrument
    ref = str(validated["instrument_ref"])
    if instrument.instrument_id != ref and instrument.venue_instrument_id != ref:
        raise ProducerAdapterError(
            ProducerIngressFailureCodeV1.INSTRUMENT_BINDING_DERIVATION_FAILED.value
        )
    observed_at_unix = _parse_observed_at_unix(str(validated["observed_at"]))
    evaluated = (
        termination.evaluated_at_unix
        if termination.evaluated_at_unix is not None
        else (observed_at_unix + 1.0)
    )
    provenance = tuple(str(p) for p in validated.get("provenance_refs", ()))
    envelope_id = str(validated["context_id"])
    delivery_id = f"mi-del-{content_digest[:32]}"
    quality = validated.get("quality_state_ref")
    quality_score = None
    if isinstance(quality, Mapping):
        raw_score = quality.get("quality_score")
        if isinstance(raw_score, (int, float)):
            quality_score = float(raw_score)
    return EvidenceIntakeRecordV1(
        delivery_id=delivery_id,
        envelope_id=envelope_id,
        producer_id=MI_PRODUCER_ID,
        producer_version=MI_PRODUCER_VERSION,
        evidence_type_version=EVIDENCE_TYPE_VERSION,
        producer_family=EvidenceProducerFamilyV1.MARKET_INTELLIGENCE,
        evidence_kind=BoundedL6EvidenceKindV1.MI_MARKET_CONTEXT_DESCRIPTIVE_V1,
        instrument=instrument,
        market_observation_epoch=termination.market_observation_epoch,
        observed_at_unix=observed_at_unix,
        freshness_horizon_seconds=termination.freshness_horizon_seconds,
        source_evidence_digest=content_digest,
        typed_payload_digest=content_digest,
        provenance_refs=provenance or (f"mi:context:{envelope_id}",),
        lineage_refs=(str(validated["information_set_ref"]),),
        quality_score=quality_score,
        extra_fields={
            "p5_adapter": "market_intelligence_market_context_v1",
            "evaluated_at_unix_hint": evaluated,
        },
    )


def adapt_learning_conditioned_evaluative_v1(
    artifact: Mapping[str, Any],
    *,
    termination: ProducerEvidenceTerminationContextV1,
) -> EvidenceIntakeRecordV1:
    validated = validate_mi_learning_evidence_record_v1(artifact)
    if validated.get("conditioned_binding_schema") != CONDITIONED_BINDING_SCHEMA:
        raise ProducerAdapterError(ProducerIngressFailureCodeV1.CONDITIONED_BINDING_REQUIRED.value)
    digest = str(validated["reproducibility_digest"])
    if not is_valid_sha256_hex(digest):
        raise ProducerAdapterError(ProducerIngressFailureCodeV1.ARTIFACT_MALFORMED.value)
    observed_at_unix = _parse_observed_at_unix(str(validated["forecast_created_at_utc"]))
    envelope_id = str(validated["mi_learning_evidence_id"])
    delivery_id = f"learn-del-{digest[:32]}"
    prov = validated.get("provenance")
    provenance_refs: tuple[str, ...]
    if isinstance(prov, Mapping):
        provenance_refs = tuple(
            str(prov[k])
            for k in sorted(prov.keys())
            if isinstance(prov[k], str) and prov[k].strip()
        )
    else:
        provenance_refs = (f"learning:mi_record:{envelope_id}",)
    return EvidenceIntakeRecordV1(
        delivery_id=delivery_id,
        envelope_id=envelope_id,
        producer_id=LEARNING_PRODUCER_ID,
        producer_version=LEARNING_PRODUCER_VERSION,
        evidence_type_version=EVIDENCE_TYPE_VERSION,
        producer_family=EvidenceProducerFamilyV1.LEARNING,
        evidence_kind=BoundedL6EvidenceKindV1.LEARNING_CONDITIONED_EVALUATIVE_V1,
        instrument=termination.instrument,
        market_observation_epoch=termination.market_observation_epoch,
        observed_at_unix=observed_at_unix,
        freshness_horizon_seconds=termination.freshness_horizon_seconds,
        source_evidence_digest=digest,
        typed_payload_digest=digest,
        provenance_refs=provenance_refs,
        lineage_refs=(str(validated.get("market_context_ref", "")),),
        extra_fields={
            "p5_adapter": "learning_conditioned_evaluative_v1",
            "evaluability": validated.get("evaluability"),
        },
    )
