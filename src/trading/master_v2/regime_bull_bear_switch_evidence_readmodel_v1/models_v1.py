"""EVIDENCE_ONLY regime/bull-bear/switch readmodel carrier (non-restart)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from trading.master_v2.double_play_state import ScopeEvent, SideState, TransitionDecision
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.constants_v1 import (
    ARTIFACT_FILENAME,
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    CAPTURE_MODE,
    DECISION_AUTHORITY,
    ERROR_CLASSIFICATION_MISMATCH,
    ERROR_INVALID_ENUM,
    ERROR_INVALID_PAYLOAD,
    ERROR_MISSING_FIELD,
    ERROR_SCHEMA_MISMATCH,
    ERROR_SIDE_NEXT_MISMATCH,
    EVIDENCE_CLASSIFICATION,
    FAMILY_ID,
    ORDER_EFFECT,
    OWNER,
    PARALLEL_PERSISTENCE_DOMAIN,
    PRESENTATION_AUTHORITY,
    RESTART_AUTHORITY,
    RUNTIME_CAPTURE_POINT,
    RUNTIME_EFFECT,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TRADING_INPUT,
)
from trading.master_v2.suitability_binding_v1 import SuitabilityRegimeStatus

_REQUIRED_FIELDS: tuple[str, ...] = (
    "regime_id",
    "regime_status",
    "side_state",
    "previous_side_state",
    "next_side_state",
    "scope_event_type",
    "transition_allowed",
    "transition_reason_code",
)


class RegimeBullBearSwitchEvidenceError(ValueError):
    """Fail-closed validation / load error for the evidence readmodel."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}:{detail}" if detail else code)


def _require_nonempty_str(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegimeBullBearSwitchEvidenceError(ERROR_MISSING_FIELD, field)
    return value.strip()


def _parse_side_state(value: object, *, field: str) -> SideState:
    text = _require_nonempty_str(value, field=field)
    try:
        return SideState(text)
    except ValueError as exc:
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, field) from exc


def _parse_scope_event(value: object, *, field: str) -> ScopeEvent:
    text = _require_nonempty_str(value, field=field)
    try:
        return ScopeEvent(text)
    except ValueError as exc:
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, field) from exc


def _parse_regime_status(value: object, *, field: str) -> SuitabilityRegimeStatus:
    text = _require_nonempty_str(value, field=field)
    try:
        return SuitabilityRegimeStatus(text)
    except ValueError as exc:
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, field) from exc


@dataclass(frozen=True)
class RegimeBullBearSwitchEvidenceReadmodelV1:
    """Immutable capture of eight authorized runtime fields (evidence only)."""

    regime_id: str
    regime_status: SuitabilityRegimeStatus
    side_state: SideState
    previous_side_state: SideState
    next_side_state: SideState
    scope_event_type: ScopeEvent
    transition_allowed: bool
    transition_reason_code: str
    instrument_id: str
    trading_epoch: int
    schema_name: str = SCHEMA_NAME
    schema_version: int = SCHEMA_VERSION
    family_id: str = FAMILY_ID
    capability_id: str = CAPABILITY_ID
    owner: str = OWNER
    evidence_classification: str = EVIDENCE_CLASSIFICATION
    restart_authority: bool = RESTART_AUTHORITY
    trading_input: bool = TRADING_INPUT
    decision_authority: bool = DECISION_AUTHORITY
    presentation_authority: bool = PRESENTATION_AUTHORITY
    parallel_persistence_domain: bool = PARALLEL_PERSISTENCE_DOMAIN
    capture_mode: str = CAPTURE_MODE
    runtime_capture_point: str = RUNTIME_CAPTURE_POINT
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT
    order_effect: str = ORDER_EFFECT
    artifact_filename: str = ARTIFACT_FILENAME

    def __post_init__(self) -> None:
        if not self.regime_id.strip():
            raise RegimeBullBearSwitchEvidenceError(ERROR_MISSING_FIELD, "regime_id")
        if not isinstance(self.regime_status, SuitabilityRegimeStatus):
            raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, "regime_status")
        for field_name, value in (
            ("side_state", self.side_state),
            ("previous_side_state", self.previous_side_state),
            ("next_side_state", self.next_side_state),
        ):
            if not isinstance(value, SideState):
                raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, field_name)
        if not isinstance(self.scope_event_type, ScopeEvent):
            raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, "scope_event_type")
        if not isinstance(self.transition_allowed, bool):
            raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_PAYLOAD, "transition_allowed")
        if not self.transition_reason_code.strip():
            raise RegimeBullBearSwitchEvidenceError(ERROR_MISSING_FIELD, "transition_reason_code")
        # Ratified consumer contract: current side_state == post-transition next.
        if self.side_state is not self.next_side_state:
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_SIDE_NEXT_MISMATCH,
                f"{self.side_state.value}!={self.next_side_state.value}",
            )
        if self.evidence_classification != EVIDENCE_CLASSIFICATION:
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_CLASSIFICATION_MISMATCH, "evidence_classification"
            )
        if self.restart_authority or self.trading_input or self.decision_authority:
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_CLASSIFICATION_MISMATCH, "authority_flags"
            )
        if self.parallel_persistence_domain:
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_CLASSIFICATION_MISMATCH, "parallel_persistence_domain"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": int(self.schema_version),
            "family_id": self.family_id,
            "capability_id": self.capability_id,
            "owner": self.owner,
            "evidence_classification": self.evidence_classification,
            "restart_authority": bool(self.restart_authority),
            "trading_input": bool(self.trading_input),
            "decision_authority": bool(self.decision_authority),
            "presentation_authority": bool(self.presentation_authority),
            "parallel_persistence_domain": bool(self.parallel_persistence_domain),
            "capture_mode": self.capture_mode,
            "runtime_capture_point": self.runtime_capture_point,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "order_effect": self.order_effect,
            "artifact_filename": self.artifact_filename,
            "instrument_id": self.instrument_id,
            "trading_epoch": int(self.trading_epoch),
            "regime_id": self.regime_id,
            "regime_status": self.regime_status.value,
            "side_state": self.side_state.value,
            "previous_side_state": self.previous_side_state.value,
            "next_side_state": self.next_side_state.value,
            "scope_event_type": self.scope_event_type.value,
            "transition_allowed": bool(self.transition_allowed),
            "transition_reason_code": self.transition_reason_code,
        }

    def content_digest(self) -> str:
        body = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RegimeBullBearSwitchEvidenceReadmodelV1":
        if not isinstance(payload, Mapping):
            raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_PAYLOAD, "not_mapping")
        schema_name = payload.get("schema_name")
        if schema_name != SCHEMA_NAME:
            raise RegimeBullBearSwitchEvidenceError(ERROR_SCHEMA_MISMATCH, "schema_name")
        schema_version = payload.get("schema_version")
        try:
            schema_version_i = int(schema_version)
        except (TypeError, ValueError) as exc:
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_SCHEMA_MISMATCH, "schema_version"
            ) from exc
        if schema_version_i != SCHEMA_VERSION:
            raise RegimeBullBearSwitchEvidenceError(ERROR_SCHEMA_MISMATCH, "schema_version")

        missing = [key for key in _REQUIRED_FIELDS if key not in payload]
        if missing:
            raise RegimeBullBearSwitchEvidenceError(ERROR_MISSING_FIELD, ",".join(missing))

        classification = payload.get("evidence_classification", EVIDENCE_CLASSIFICATION)
        if classification != EVIDENCE_CLASSIFICATION:
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_CLASSIFICATION_MISMATCH, "evidence_classification"
            )
        if bool(payload.get("restart_authority", False)):
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_CLASSIFICATION_MISMATCH, "restart_authority"
            )
        if bool(payload.get("trading_input", False)):
            raise RegimeBullBearSwitchEvidenceError(ERROR_CLASSIFICATION_MISMATCH, "trading_input")
        if bool(payload.get("decision_authority", False)):
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_CLASSIFICATION_MISMATCH, "decision_authority"
            )
        if bool(payload.get("parallel_persistence_domain", False)):
            raise RegimeBullBearSwitchEvidenceError(
                ERROR_CLASSIFICATION_MISMATCH, "parallel_persistence_domain"
            )

        transition_allowed = payload.get("transition_allowed")
        if not isinstance(transition_allowed, bool):
            raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_PAYLOAD, "transition_allowed")

        instrument_id = _require_nonempty_str(payload.get("instrument_id"), field="instrument_id")
        try:
            trading_epoch = int(payload.get("trading_epoch"))
        except (TypeError, ValueError) as exc:
            raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_PAYLOAD, "trading_epoch") from exc

        return cls(
            regime_id=_require_nonempty_str(payload.get("regime_id"), field="regime_id"),
            regime_status=_parse_regime_status(payload.get("regime_status"), field="regime_status"),
            side_state=_parse_side_state(payload.get("side_state"), field="side_state"),
            previous_side_state=_parse_side_state(
                payload.get("previous_side_state"), field="previous_side_state"
            ),
            next_side_state=_parse_side_state(
                payload.get("next_side_state"), field="next_side_state"
            ),
            scope_event_type=_parse_scope_event(
                payload.get("scope_event_type"), field="scope_event_type"
            ),
            transition_allowed=transition_allowed,
            transition_reason_code=_require_nonempty_str(
                payload.get("transition_reason_code"), field="transition_reason_code"
            ),
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
        )


def build_from_authorized_capture_inputs_v1(
    *,
    regime_id: str,
    regime_status: SuitabilityRegimeStatus,
    previous_side_state: SideState,
    next_side_state: SideState,
    scope_event_type: ScopeEvent,
    transition: TransitionDecision,
    instrument_id: str,
    trading_epoch: int,
) -> RegimeBullBearSwitchEvidenceReadmodelV1:
    """Build evidence by immutable copy of authorized capture-point values.

    ``side_state`` is set to ``next_side_state`` per ratified consumer contract
    (current bull/bear side equals post-transition next).
    """
    if not isinstance(regime_status, SuitabilityRegimeStatus):
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, "regime_status")
    if not isinstance(previous_side_state, SideState):
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, "previous_side_state")
    if not isinstance(next_side_state, SideState):
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, "next_side_state")
    if not isinstance(scope_event_type, ScopeEvent):
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_ENUM, "scope_event_type")
    if not isinstance(transition, TransitionDecision):
        raise RegimeBullBearSwitchEvidenceError(ERROR_INVALID_PAYLOAD, "transition")
    reason = transition.reason_code
    if not isinstance(reason, str) or not reason.strip():
        raise RegimeBullBearSwitchEvidenceError(ERROR_MISSING_FIELD, "transition_reason_code")
    return RegimeBullBearSwitchEvidenceReadmodelV1(
        regime_id=_require_nonempty_str(regime_id, field="regime_id"),
        regime_status=regime_status,
        side_state=next_side_state,
        previous_side_state=previous_side_state,
        next_side_state=next_side_state,
        scope_event_type=scope_event_type,
        transition_allowed=bool(transition.allowed),
        transition_reason_code=reason.strip(),
        instrument_id=_require_nonempty_str(instrument_id, field="instrument_id"),
        trading_epoch=int(trading_epoch),
    )
