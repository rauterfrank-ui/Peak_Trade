"""Typed read-only consumer for an already published Master V2 decision.

The consumer validates identity, instrument, epoch, and the existing evidence
digest. It returns the same evidence object. It does not recompute a decision,
rewrite eligibility, or take trading authority.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Mapping

from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    EVIDENCE_SCHEMA_VERSION,
    CanonicalTradingDecisionEvidenceV1,
    compute_canonical_trading_decision_evidence_semantic_digest,
    derive_decision_id,
)

from src.ops.h1_decision_publication_consumer_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    ORDER_EFFECT,
    POST_ALLOWED,
    PRODUCTIVE_CYCLE_BINDING,
    PUBLICATION_REQUIRED_FIELDS,
    REASON_ACCEPTED,
    REASON_BINDING_INVALID,
    REASON_CONTRADICTORY_DECISION_FIELDS,
    REASON_DIGEST_MISMATCH,
    REASON_EPOCH_MISMATCH,
    REASON_IDENTITY_MISMATCH,
    REASON_INSTRUMENT_MISMATCH,
    REASON_MISSING_REQUIRED_FIELD,
    REASON_PUBLICATION_ABSENT,
    REASON_PUBLICATION_INVALID,
    REASON_SCHEMA_MISMATCH,
    STATE_WRITE,
)

_TUPLE_FIELDS = frozenset({"reason_codes", "decision_precedence_trace"})


@dataclass(frozen=True)
class DecisionPublicationReadResultV1:
    accepted: bool
    reason_code: str
    evidence: CanonicalTradingDecisionEvidenceV1 | None
    decision_outcome: str | None
    decision_id: str | None
    instrument_id: str | None
    trading_epoch: int | None
    semantic_digest: str | None
    consumer_authority_effect: str = AUTHORITY_EFFECT
    consumer_order_effect: str = ORDER_EFFECT
    external_effect_authorized: bool = False
    post_allowed: bool = POST_ALLOWED
    state_write: str = STATE_WRITE
    productive_cycle_binding: str = PRODUCTIVE_CYCLE_BINDING
    trading_authority_change: bool = False


def read_decision_publication_v1(
    publication: CanonicalTradingDecisionEvidenceV1 | Mapping[str, Any] | None,
    *,
    instrument_id: str,
    trading_epoch: int,
) -> DecisionPublicationReadResultV1:
    """Read one publication. Accepted means the evidence is intact, not authorized."""
    if publication is None:
        return _reject(REASON_PUBLICATION_ABSENT, evidence=None)
    if not isinstance(instrument_id, str) or not instrument_id.strip():
        return _reject(REASON_BINDING_INVALID, evidence=_typed_or_none(publication))
    if isinstance(trading_epoch, bool) or not isinstance(trading_epoch, int):
        return _reject(REASON_BINDING_INVALID, evidence=_typed_or_none(publication))

    if isinstance(publication, CanonicalTradingDecisionEvidenceV1):
        return _read_typed(
            publication,
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
        )
    if isinstance(publication, Mapping):
        return _read_mapping(
            publication,
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
        )
    return _reject(REASON_PUBLICATION_INVALID, evidence=None)


def _read_mapping(
    publication: Mapping[str, Any],
    *,
    instrument_id: str,
    trading_epoch: int,
) -> DecisionPublicationReadResultV1:
    if _decision_outcomes_conflict(publication):
        return _reject(REASON_CONTRADICTORY_DECISION_FIELDS, evidence=None)
    payload = _publication_payload(publication)
    missing = _first_missing_mapping_field(payload)
    if missing is not None:
        return _reject(REASON_MISSING_REQUIRED_FIELD, evidence=None)
    schema_version = payload.get("evidence_schema_version")
    if schema_version != EVIDENCE_SCHEMA_VERSION:
        return _reject(REASON_SCHEMA_MISMATCH, evidence=None)
    try:
        evidence = _coerce_evidence(payload)
    except (TypeError, ValueError):
        return _reject(REASON_PUBLICATION_INVALID, evidence=None)
    return _read_typed(evidence, instrument_id=instrument_id, trading_epoch=trading_epoch)


def _read_typed(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    instrument_id: str,
    trading_epoch: int,
) -> DecisionPublicationReadResultV1:
    missing = _first_missing_typed_field(evidence)
    if missing is not None:
        return _reject(REASON_MISSING_REQUIRED_FIELD, evidence=evidence)
    if evidence.evidence_schema_version != EVIDENCE_SCHEMA_VERSION:
        return _reject(REASON_SCHEMA_MISMATCH, evidence=evidence)
    if isinstance(evidence.trading_epoch, bool) or not isinstance(evidence.trading_epoch, int):
        return _reject(REASON_PUBLICATION_INVALID, evidence=evidence)
    if evidence.trading_epoch < 0:
        return _reject(REASON_PUBLICATION_INVALID, evidence=evidence)
    expected_id = derive_decision_id(
        replay_id=evidence.replay_id,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
        input_digest=evidence.input_digest,
    )
    if evidence.decision_id != expected_id:
        return _reject(REASON_IDENTITY_MISMATCH, evidence=evidence)
    if evidence.instrument_id != instrument_id:
        return _reject(REASON_INSTRUMENT_MISMATCH, evidence=evidence)
    if evidence.trading_epoch != trading_epoch:
        return _reject(REASON_EPOCH_MISMATCH, evidence=evidence)
    actual_digest = compute_canonical_trading_decision_evidence_semantic_digest(evidence)
    if evidence.semantic_digest != actual_digest:
        return _reject(REASON_DIGEST_MISMATCH, evidence=evidence)
    return DecisionPublicationReadResultV1(
        accepted=True,
        reason_code=REASON_ACCEPTED,
        evidence=evidence,
        decision_outcome=evidence.decision_outcome,
        decision_id=evidence.decision_id,
        instrument_id=evidence.instrument_id,
        trading_epoch=evidence.trading_epoch,
        semantic_digest=evidence.semantic_digest,
    )


def _reject(
    reason_code: str,
    *,
    evidence: CanonicalTradingDecisionEvidenceV1 | None,
) -> DecisionPublicationReadResultV1:
    return DecisionPublicationReadResultV1(
        accepted=False,
        reason_code=reason_code,
        evidence=evidence,
        decision_outcome=None if evidence is None else evidence.decision_outcome,
        decision_id=None if evidence is None else evidence.decision_id,
        instrument_id=None if evidence is None else evidence.instrument_id,
        trading_epoch=None if evidence is None else evidence.trading_epoch,
        semantic_digest=None if evidence is None else evidence.semantic_digest,
    )


def _typed_or_none(publication: object) -> CanonicalTradingDecisionEvidenceV1 | None:
    if isinstance(publication, CanonicalTradingDecisionEvidenceV1):
        return publication
    return None


def _decision_outcomes_conflict(publication: Mapping[str, Any]) -> bool:
    nested = publication.get("evidence")
    if not isinstance(nested, Mapping):
        return False
    outer = _nonempty_str(publication.get("decision_outcome"))
    inner = _nonempty_str(nested.get("decision_outcome"))
    return outer is not None and inner is not None and outer != inner


def _publication_payload(publication: Mapping[str, Any]) -> Mapping[str, Any]:
    nested = publication.get("evidence")
    if isinstance(nested, Mapping) and _first_missing_mapping_field(nested) is None:
        return nested
    return publication


def _first_missing_mapping_field(payload: Mapping[str, Any]) -> str | None:
    for key in PUBLICATION_REQUIRED_FIELDS:
        value = payload.get(key)
        if key == "trading_epoch":
            if isinstance(value, bool) or not isinstance(value, int):
                return key
            continue
        if _nonempty_str(value) is None:
            return key
    return None


def _first_missing_typed_field(evidence: CanonicalTradingDecisionEvidenceV1) -> str | None:
    for key in PUBLICATION_REQUIRED_FIELDS:
        value = getattr(evidence, key)
        if key == "trading_epoch":
            if isinstance(value, bool) or not isinstance(value, int):
                return key
            continue
        if _nonempty_str(value) is None:
            return key
    return None


def _nonempty_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def _coerce_evidence(payload: Mapping[str, Any]) -> CanonicalTradingDecisionEvidenceV1:
    kwargs: dict[str, Any] = {}
    for field in fields(CanonicalTradingDecisionEvidenceV1):
        if field.name not in payload:
            continue
        value = payload[field.name]
        if field.name in _TUPLE_FIELDS:
            if isinstance(value, str) or not isinstance(value, (list, tuple)):
                raise TypeError(field.name)
            value = tuple(value)
        kwargs[field.name] = value
    return CanonicalTradingDecisionEvidenceV1(**kwargs)
