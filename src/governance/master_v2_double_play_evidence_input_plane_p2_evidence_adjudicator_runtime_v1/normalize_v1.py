"""Canonical normalization without trading-semantics mutation."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    InstrumentBindingV1,
    envelope_forbidden_numeric_fields_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeRecordV1,
)


def _strip(value: str) -> str:
    return value.strip()


def _dedupe_sorted_refs(refs: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for ref in sorted(refs, key=lambda r: r.strip()):
        key = ref.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return tuple(out)


def _normalize_optional_unit_score(value: float | None) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value):
        return None
    clamped = max(0.0, min(1.0, float(value)))
    return round(clamped, 12)


def normalize_evidence_intake_record_v1(intake: EvidenceIntakeRecordV1) -> EvidenceIntakeRecordV1:
    instrument = InstrumentBindingV1(
        instrument_id=_strip(intake.instrument.instrument_id),
        venue=_strip(intake.instrument.venue),
        venue_instrument_id=_strip(intake.instrument.venue_instrument_id),
    )
    extra: dict[str, Any] = dict(intake.extra_fields)
    forbidden = envelope_forbidden_numeric_fields_v1(extra)
    for key in forbidden:
        extra.pop(key, None)
    confidence = _normalize_optional_unit_score(intake.confidence_score)
    quality = _normalize_optional_unit_score(intake.quality_score)
    if confidence is not None:
        extra["confidence_score"] = confidence
    if quality is not None:
        extra["quality_score"] = quality
    return replace(
        intake,
        delivery_id=_strip(intake.delivery_id),
        envelope_id=_strip(intake.envelope_id),
        producer_id=_strip(intake.producer_id),
        producer_version=_strip(intake.producer_version),
        evidence_type_version=_strip(intake.evidence_type_version),
        instrument=instrument,
        provenance_refs=_dedupe_sorted_refs(intake.provenance_refs),
        lineage_refs=_dedupe_sorted_refs(intake.lineage_refs),
        confidence_score=confidence,
        quality_score=quality,
        extra_fields=extra,
    )


def intake_malformed_fields_v1(intake: EvidenceIntakeRecordV1) -> tuple[str, ...]:
    from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.reason_codes_v1 import (
        AdjudicationIntakeFailureCodeV1,
    )

    failures: list[str] = []
    for field_name, code in (
        (intake.delivery_id, AdjudicationIntakeFailureCodeV1.DELIVERY_ID_MISSING),
        (intake.envelope_id, AdjudicationIntakeFailureCodeV1.ENVELOPE_ID_MISSING),
        (intake.producer_id, AdjudicationIntakeFailureCodeV1.PRODUCER_ID_MISSING),
        (intake.producer_version, AdjudicationIntakeFailureCodeV1.PRODUCER_VERSION_MISSING),
        (
            intake.evidence_type_version,
            AdjudicationIntakeFailureCodeV1.EVIDENCE_TYPE_VERSION_MISSING,
        ),
    ):
        if not str(field_name).strip():
            failures.append(code.value)
    if not intake.provenance_refs:
        failures.append(AdjudicationIntakeFailureCodeV1.INTAKE_MALFORMED.value)
    if not intake.lineage_refs:
        failures.append(AdjudicationIntakeFailureCodeV1.LINEAGE_MISSING.value)
    forbidden = envelope_forbidden_numeric_fields_v1(intake.extra_fields)
    if forbidden:
        failures.append(AdjudicationIntakeFailureCodeV1.INTAKE_MALFORMED.value)
    return tuple(dict.fromkeys(failures))
