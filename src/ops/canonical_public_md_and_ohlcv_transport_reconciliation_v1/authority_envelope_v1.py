"""Authoritative OHLCV bar envelope with required provenance fields."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    normalize_bar_state_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    AUTHORITY_ENVELOPE_FIELDS,
    BAR_STATE_IN_PROGRESS,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.interval_contract_v1 import (
    normalize_interval_id_v1,
)


class AuthorityEnvelopeErrorV1(ValueError):
    """Fail-closed envelope validation error."""


def _req_str(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthorityEnvelopeErrorV1(f"INVALID_ENVELOPE_FIELD:{name}")
    return value.strip()


def _req_float(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuthorityEnvelopeErrorV1(f"INVALID_ENVELOPE_FIELD:{name}")
    return float(value)


def _req_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AuthorityEnvelopeErrorV1(f"INVALID_ENVELOPE_FIELD:{name}")
    if value < 0:
        raise AuthorityEnvelopeErrorV1(f"INVALID_ENVELOPE_FIELD_NEGATIVE:{name}")
    return value


@dataclass(frozen=True)
class AuthoritativeOhlcvBarEnvelopeV1:
    canonical_instrument_id: str
    venue_instrument_id: str
    venue: str
    interval: str
    bar_open_time: float
    bar_close_time: float
    event_time: float
    receive_time: float
    first_observation_identity: Mapping[str, Any]
    last_observation_identity: Mapping[str, Any]
    session_id: str
    repository_sha: str
    config_digest: str
    transport_lag: float
    quality_state: str
    finalization_state: str
    revision: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    sample_count: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_instrument_id",
            _req_str("canonical_instrument_id", self.canonical_instrument_id),
        )
        object.__setattr__(
            self, "venue_instrument_id", _req_str("venue_instrument_id", self.venue_instrument_id)
        )
        object.__setattr__(self, "venue", _req_str("venue", self.venue))
        object.__setattr__(self, "interval", normalize_interval_id_v1(self.interval))
        object.__setattr__(self, "bar_open_time", _req_float("bar_open_time", self.bar_open_time))
        object.__setattr__(
            self, "bar_close_time", _req_float("bar_close_time", self.bar_close_time)
        )
        object.__setattr__(self, "event_time", _req_float("event_time", self.event_time))
        object.__setattr__(self, "receive_time", _req_float("receive_time", self.receive_time))
        if not isinstance(self.first_observation_identity, Mapping):
            raise AuthorityEnvelopeErrorV1("INVALID_ENVELOPE_FIELD:first_observation_identity")
        if not isinstance(self.last_observation_identity, Mapping):
            raise AuthorityEnvelopeErrorV1("INVALID_ENVELOPE_FIELD:last_observation_identity")
        object.__setattr__(self, "session_id", _req_str("session_id", self.session_id))
        object.__setattr__(self, "repository_sha", _req_str("repository_sha", self.repository_sha))
        object.__setattr__(self, "config_digest", _req_str("config_digest", self.config_digest))
        object.__setattr__(self, "transport_lag", _req_float("transport_lag", self.transport_lag))
        object.__setattr__(self, "quality_state", normalize_bar_state_v1(self.quality_state))
        object.__setattr__(
            self, "finalization_state", normalize_bar_state_v1(self.finalization_state)
        )
        object.__setattr__(self, "revision", _req_int("revision", self.revision))
        for name in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, name, _req_float(name, getattr(self, name)))
        object.__setattr__(self, "sample_count", _req_int("sample_count", self.sample_count))
        if self.bar_close_time <= self.bar_open_time:
            raise AuthorityEnvelopeErrorV1("INVALID_BAR_WINDOW")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise AuthorityEnvelopeErrorV1("INVALID_OHLC_RELATIONS")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["first_observation_identity"] = dict(self.first_observation_identity)
        payload["last_observation_identity"] = dict(self.last_observation_identity)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AuthoritativeOhlcvBarEnvelopeV1":
        return cls(
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_instrument_id=str(payload["venue_instrument_id"]),
            venue=str(payload["venue"]),
            interval=str(payload["interval"]),
            bar_open_time=float(payload["bar_open_time"]),
            bar_close_time=float(payload["bar_close_time"]),
            event_time=float(payload["event_time"]),
            receive_time=float(payload["receive_time"]),
            first_observation_identity=dict(payload["first_observation_identity"]),
            last_observation_identity=dict(payload["last_observation_identity"]),
            session_id=str(payload["session_id"]),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            transport_lag=float(payload["transport_lag"]),
            quality_state=str(payload["quality_state"]),
            finalization_state=str(payload.get("finalization_state") or payload["quality_state"]),
            revision=int(payload["revision"]),
            open=float(payload["open"]),
            high=float(payload["high"]),
            low=float(payload["low"]),
            close=float(payload["close"]),
            volume=float(payload.get("volume", 0.0)),
            sample_count=int(payload.get("sample_count", 1)),
        )


def authority_envelope_field_contract_v1() -> dict[str, Any]:
    return {
        "required_fields": list(AUTHORITY_ENVELOPE_FIELDS),
        "default_quality_state": BAR_STATE_IN_PROGRESS,
        "field_count": len(AUTHORITY_ENVELOPE_FIELDS),
    }


def assert_envelope_has_required_fields_v1(payload: Mapping[str, Any]) -> None:
    missing = [f for f in AUTHORITY_ENVELOPE_FIELDS if f not in payload]
    if missing:
        raise AuthorityEnvelopeErrorV1(f"MISSING_ENVELOPE_FIELDS:{','.join(missing)}")
