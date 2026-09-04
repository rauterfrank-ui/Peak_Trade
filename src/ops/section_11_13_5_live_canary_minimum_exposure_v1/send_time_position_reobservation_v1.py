"""Fail-closed SEND_TIME_POSITION_REOBSERVATION offline contract.

Named residual after AUTHENTICATED_PRODUCTIVE_TRANSPORT. Reobserves the
canonical target-instrument position at the flatten pre-send permit
decision. Reuses classify_target_position_state_v1 and the ratified
position-observation freshness contract. Empty data[] is not zero.
Historical P08 slices are not current proof. Fake/no-wire producers are
not a runtime GET.

Does not GET, POST, flatten, issue a runtime permit, open a network
session, or claim PROVEN_AT_SEND.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_POSITIONS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    PASS_OFFLINE_CONTRACT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    AGE_EVALUATION_POINT,
    CLOCK_DOMAIN,
    OBSERVATION_TIMESTAMP_FIELD,
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
    evaluate_position_observation_freshness_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)

STPR_IMPLEMENTATION_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SEND_TIME_POSITION_REOBSERVATION_MAXIMUM_SAFE_LEVERAGE_V1"
)
NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION: tuple[str, ...] = (
    "BOUNDED_RUNTIME_PERMIT_ISSUANCE",
    "FLATTEN_EXECUTE",
    "NETWORK_SESSION",
)
NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION_SET = frozenset(
    NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION
)

PRODUCER_CLASS_FAKE_OFFLINE = "FAKE_OFFLINE_NO_WIRE"
PRODUCER_CLASS_CALLER_SUPPLIED = "CALLER_SUPPLIED_NO_WIRE"
PRODUCER_CLASS_AUTHENTICATED_PRIVATE_GET = "AUTHENTICATED_PRIVATE_GET"
ALLOWED_OFFLINE_PRODUCER_CLASSES = frozenset(
    {PRODUCER_CLASS_FAKE_OFFLINE, PRODUCER_CLASS_CALLER_SUPPLIED}
)
CANONICAL_POSITION_GET_ENDPOINT = ENDPOINT_ACCOUNT_POSITIONS
CANONICAL_POSITION_GET_METHOD = "GET"
SEND_TIME_EVALUATION_POINT = AGE_EVALUATION_POINT
FORBIDDEN_HISTORICAL_OBSERVATION_IDENTITIES: frozenset[str] = frozenset(
    {
        "20260903T223726Z",
        "20260903T210159Z",
        "P08_CASE_A",
        "Z2AX",
        "Z2AW",
    }
)

REASON_APT_NOT_PASS = "APT_NOT_PASS_OFFLINE_CONTRACT"
REASON_MISSING_APT = "APT_STATUS_MISSING"
REASON_MISSING_REMAINING = "REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION_SET_MISSING"
REASON_REMAINING_MISMATCH = "REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION_SET_MISMATCH"
REASON_INSTRUMENT_MISMATCH = "PREREQUISITE_19_INSTRUMENT_SCOPE_MISMATCH"
REASON_OBSERVATION_MISSING = "SEND_TIME_POSITION_OBSERVATION_MISSING"
REASON_EMPTY_DATA_NOT_ZERO = "EMPTY_DATA_MUST_NOT_BE_TREATED_AS_ZERO"
REASON_TARGET_NOT_OBSERVED = "TARGET_INSTRUMENT_NOT_OBSERVED"
REASON_ZERO_POSITION = "ZERO_POSITION_IS_NOT_FLATTENABLE_REOBSERVATION_PASS"
REASON_MALFORMED_PAYLOAD = "MALFORMED_POSITIONS_PAYLOAD"
REASON_TRANSPORT_FAILURE = "POSITION_REOBSERVATION_TRANSPORT_FAILURE"
REASON_AUTHENTICATION_FAILURE = "POSITION_REOBSERVATION_AUTHENTICATION_FAILURE"
REASON_HTTP_OK_INSUFFICIENT = "HTTP_OK_MUST_NOT_IMPLY_SEMANTIC_OBSERVATION"
REASON_HISTORICAL_REUSE = "HISTORICAL_POSITION_EVIDENCE_MUST_NOT_BE_REUSED"
REASON_FAKE_COUNTED_AS_GET = "FAKE_PRODUCER_MUST_NOT_COUNT_AS_RUNTIME_GET"
REASON_AUTHENTICATED_GET_PRODUCER = (
    "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_USE_AUTHENTICATED_GET_PRODUCER"
)
REASON_RUNTIME_OBSERVATION_CLAIM = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_CLAIM_RUNTIME_PROVEN"
REASON_PROVEN_AT_SEND_CLAIM = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_CLAIM_PROVEN_AT_SEND"
REASON_LIVE_AUTHORIZED_SUBSTITUTE = (
    "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_SEND_TIME_POSITION_REOBSERVATION"
)
REASON_RUNTIME_PERMIT = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_ISSUE_RUNTIME_PERMIT"
REASON_FLATTEN_EXECUTE = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_AUTHORIZE_FLATTEN_EXECUTE"
REASON_NETWORK_SESSION = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_AUTHORIZE_NETWORK_SESSION"
REASON_POST = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_POST"
REASON_GET = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_GET"
REASON_PRIVATE_GET_CLAIM = "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_CLAIM_PRIVATE_GET_PROVEN"
REASON_CREDENTIAL_USE_CLAIM = (
    "SEND_TIME_POSITION_REOBSERVATION_MUST_NOT_CLAIM_CREDENTIAL_USE_PROVEN"
)
REASON_IMPLEMENTATION_GO_AS_EXECUTE = "IMPLEMENTATION_GO_USED_AS_FLATTEN_EXECUTE"
REASON_LINEAGE_MISMATCH = "SEND_TIME_POSITION_REOBSERVATION_PREDECESSOR_LINEAGE_MISMATCH"


class SendTimePositionReobservationError(RuntimeError):
    """Fail-closed SEND_TIME_POSITION_REOBSERVATION contract violation."""


@dataclass(frozen=True)
class SendTimePositionObservationV1:
    """Typed send-time observation primitive. Never invented by the evaluator."""

    instrument_id: str
    positions_payload: Mapping[str, Any] | None
    response_received_monotonic_ms: Any = None
    observation_identity: str | None = None
    evidence_kind: str = PRE_SEND_EVIDENCE_KIND
    producer_class: str = PRODUCER_CLASS_FAKE_OFFLINE
    decision_id: str | None = None
    source_response_timestamp: str | None = None
    venue_utime: str | None = None
    transport_error: str | None = None
    authentication_failure: str | None = None
    historical_slice_id: str | None = None

    def freshness_evidence(self) -> PositionObservationFreshnessEvidenceV1:
        return PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=self.response_received_monotonic_ms,
            decision_id=self.decision_id,
            evidence_kind=self.evidence_kind,
            observation_get_identity=self.observation_identity,
        )


def _norm_items(values: Sequence[str] | Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


def _empty_data_envelope(payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(payload, Mapping):
        return False
    if str(payload.get("code") or "") != "0":
        return False
    data = payload.get("data")
    return isinstance(data, list) and len(data) == 0


def evaluate_send_time_position_reobservation_v1(
    *,
    apt_status: str | None,
    positions_payload: Mapping[str, Any] | None,
    instrument_id: str | None,
    expected_instrument_id: str = DEFAULT_INSTRUMENT_ID,
    freshness_evidence: PositionObservationFreshnessEvidenceV1 | None,
    evaluation_monotonic_ms: Any,
    current_decision_id: str | None,
    claimed_remaining_after_send_time_position_reobservation: Sequence[str] | None,
    producer_class: str | None = PRODUCER_CLASS_CALLER_SUPPLIED,
    observation_identity: str | None = None,
    historical_reuse_claim: bool = False,
    runtime_observation_proven_claim: bool = False,
    proven_at_send_18: bool = False,
    proven_at_send_19: bool = False,
    proven_at_send_21: bool = False,
    proven_at_send_24: bool = False,
    live_authorized_claim: bool = False,
    runtime_permit_issuance_claim: bool = False,
    flatten_execute_authorized_claim: bool = False,
    network_session_authorized_claim: bool = False,
    post_performed_claim: bool = False,
    get_performed_claim: bool = False,
    private_get_proven_claim: bool = False,
    credential_use_proven_claim: bool = False,
    empty_data_treated_as_zero_claim: bool = False,
    flatten_execute_owner_go: str | None = None,
    predecessor_lineage_ok: bool = True,
    transport_error: str | None = None,
    authentication_failure: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never transmits. Never issues a permit.

    Offline PASS proves the send-time reobservation evaluation contract.
    It does not prove a venue GET, zero/nonzero at send, or PROVEN_AT_SEND.
    """
    reasons: list[str] = []
    apt = str(apt_status or "").strip()
    if not apt:
        reasons.append(REASON_MISSING_APT)
    elif apt != PASS_OFFLINE_CONTRACT:
        reasons.append(REASON_APT_NOT_PASS)
    if claimed_remaining_after_send_time_position_reobservation is None:
        reasons.append(REASON_MISSING_REMAINING)
    else:
        claimed = frozenset(_norm_items(claimed_remaining_after_send_time_position_reobservation))
        if claimed != NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION_SET:
            reasons.append(REASON_REMAINING_MISMATCH)
    target = str(instrument_id or "").strip()
    expected = str(expected_instrument_id or "").strip() or DEFAULT_INSTRUMENT_ID
    if not target or target != expected:
        reasons.append(REASON_INSTRUMENT_MISMATCH)
    producer = str(producer_class or "").strip()
    if producer == PRODUCER_CLASS_AUTHENTICATED_PRIVATE_GET:
        reasons.append(REASON_AUTHENTICATED_GET_PRODUCER)
    elif producer not in ALLOWED_OFFLINE_PRODUCER_CLASSES:
        reasons.append(REASON_AUTHENTICATED_GET_PRODUCER)
    identity = str(observation_identity or "").strip()
    if historical_reuse_claim is True or identity in FORBIDDEN_HISTORICAL_OBSERVATION_IDENTITIES:
        reasons.append(REASON_HISTORICAL_REUSE)
    if transport_error:
        reasons.append(REASON_TRANSPORT_FAILURE)
    if authentication_failure:
        reasons.append(REASON_AUTHENTICATION_FAILURE)
    if empty_data_treated_as_zero_claim is True:
        reasons.append(REASON_EMPTY_DATA_NOT_ZERO)
    if positions_payload is None and not transport_error and not authentication_failure:
        reasons.append(REASON_OBSERVATION_MISSING)
    elif positions_payload is not None:
        classified = classify_target_position_state_v1(
            positions_payload=positions_payload,
            instrument_id=expected,
        )
        if _empty_data_envelope(positions_payload):
            reasons.append(REASON_EMPTY_DATA_NOT_ZERO)
            reasons.append(REASON_TARGET_NOT_OBSERVED)
        elif classified.state == TARGET_POSITION_NOT_OBSERVED:
            reasons.append(REASON_TARGET_NOT_OBSERVED)
        elif classified.state == TARGET_POSITION_ZERO_PROVEN:
            reasons.append(REASON_ZERO_POSITION)
        elif classified.state == TARGET_POSITION_UNKNOWN:
            reasons.append(REASON_MALFORMED_PAYLOAD)
        elif classified.state != TARGET_POSITION_NONZERO_PROVEN:
            reasons.append(REASON_MALFORMED_PAYLOAD)
        if (
            isinstance(positions_payload, Mapping)
            and str(positions_payload.get("code") or "") == "0"
            and classified.state != TARGET_POSITION_NONZERO_PROVEN
        ):
            reasons.append(REASON_HTTP_OK_INSUFFICIENT)
    freshness = evaluate_position_observation_freshness_v1(
        evidence=freshness_evidence,
        evaluation_monotonic_ms=evaluation_monotonic_ms,
        current_decision_id=current_decision_id,
    )
    if not freshness.allowed:
        reasons.append(freshness.reject_reason)
    if runtime_observation_proven_claim is True:
        reasons.append(REASON_RUNTIME_OBSERVATION_CLAIM)
    if (
        proven_at_send_18 is True
        or proven_at_send_19 is True
        or proven_at_send_21 is True
        or proven_at_send_24 is True
    ):
        reasons.append(REASON_PROVEN_AT_SEND_CLAIM)
    if live_authorized_claim is True:
        reasons.append(REASON_LIVE_AUTHORIZED_SUBSTITUTE)
    if runtime_permit_issuance_claim is True:
        reasons.append(REASON_RUNTIME_PERMIT)
    if flatten_execute_authorized_claim is True:
        reasons.append(REASON_FLATTEN_EXECUTE)
    if network_session_authorized_claim is True:
        reasons.append(REASON_NETWORK_SESSION)
    if post_performed_claim is True:
        reasons.append(REASON_POST)
    if get_performed_claim is True:
        reasons.append(REASON_GET)
        if producer in ALLOWED_OFFLINE_PRODUCER_CLASSES:
            reasons.append(REASON_FAKE_COUNTED_AS_GET)
    if private_get_proven_claim is True:
        reasons.append(REASON_PRIVATE_GET_CLAIM)
    if credential_use_proven_claim is True:
        reasons.append(REASON_CREDENTIAL_USE_CLAIM)
    execute_go = str(flatten_execute_owner_go or "").strip()
    if execute_go == STPR_IMPLEMENTATION_OWNER_GO:
        reasons.append(REASON_IMPLEMENTATION_GO_AS_EXECUTE)
    if predecessor_lineage_ok is not True:
        reasons.append(REASON_LINEAGE_MISMATCH)
    deduped: list[str] = []
    seen_reasons: set[str] = set()
    for reason in reasons:
        if reason in seen_reasons:
            continue
        seen_reasons.add(reason)
        deduped.append(reason)
    return (not deduped), tuple(deduped)


def canonical_remaining_after_send_time_position_reobservation_v1() -> tuple[str, ...]:
    return NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN") is True:
        raise SendTimePositionReobservationError("RUNTIME_OBSERVATION_CLAIMED")
    if payload.get("PREREQUISITE_18_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationError("PROVEN_AT_SEND_18_CLAIMED")
    if payload.get("PREREQUISITE_19_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationError("PROVEN_AT_SEND_19_CLAIMED")
    if payload.get("PREREQUISITE_21_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationError("PROVEN_AT_SEND_21_CLAIMED")
    if payload.get("PREREQUISITE_24_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationError("PROVEN_AT_SEND_24_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise SendTimePositionReobservationError("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise SendTimePositionReobservationError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise SendTimePositionReobservationError("POST_CLAIMED")
    if payload.get("PRIVATE_GET_USED") is True or payload.get("GET_PERFORMED_THIS_PERSIST") is True:
        raise SendTimePositionReobservationError("GET_CLAIMED")


@dataclass
class RecordingSendTimePositionReobservationProducerV1:
    """No-wire fake producer. Never opens a network session. Never GETs."""

    is_fake_offline_producer: bool = True
    venue_live_contact: bool = False
    network_session_authorized: bool = False
    last_get_attempted: bool = False
    producer_class: str = PRODUCER_CLASS_FAKE_OFFLINE
    instrument_id: str = DEFAULT_INSTRUMENT_ID
    payload: dict[str, Any] = field(
        default_factory=lambda: {
            "code": "0",
            "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1"}],
        }
    )
    response_received_monotonic_ms: int = 0
    decision_id: str = "stpr-offline-contract-decision"
    observation_identity: str | None = "FAKE_OFFLINE_FIXTURE"
    transport_error: str | None = None
    authentication_failure: str | None = None

    def observe(self) -> SendTimePositionObservationV1:
        self.last_get_attempted = False
        if self.network_session_authorized is True:
            raise SendTimePositionReobservationError("NETWORK_SESSION_CLAIMED_BY_FAKE_PRODUCER")
        return SendTimePositionObservationV1(
            instrument_id=self.instrument_id,
            positions_payload=self.payload,
            response_received_monotonic_ms=self.response_received_monotonic_ms,
            observation_identity=self.observation_identity,
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
            producer_class=self.producer_class,
            decision_id=self.decision_id,
            transport_error=self.transport_error,
            authentication_failure=self.authentication_failure,
        )


def send_time_reobservation_clock_doc_v1() -> dict[str, Any]:
    return {
        "SEND_TIME_EVALUATION_POINT": SEND_TIME_EVALUATION_POINT,
        "CLOCK_DOMAIN": CLOCK_DOMAIN,
        "OBSERVATION_TIMESTAMP_FIELD": OBSERVATION_TIMESTAMP_FIELD,
        "POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS": POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
        "VENUE_UTIME_IS_NOT_FRESHNESS_CLOCK": True,
        "WALL_CLOCK_IS_NOT_FRESHNESS_CLOCK": True,
        "HMAC_TIMESTAMP_IS_NOT_FRESHNESS_CLOCK": True,
        "CANONICAL_POSITION_GET_ENDPOINT": CANONICAL_POSITION_GET_ENDPOINT,
        "CANONICAL_POSITION_GET_METHOD": CANONICAL_POSITION_GET_METHOD,
        "EMPTY_DATA_IS_NOT_ZERO": True,
        "HTTP_OK_DOES_NOT_PROVE_COMPLETENESS": True,
    }
