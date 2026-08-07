"""Governed injected transport-fault control for Step-4 productive binding.

Default-disabled wrapper that sits strictly between the real Public-MD fetcher
and ``EeaPublicMdTransportV1``. Injects typed HTTP-429 responses or reconnectable
transport errors only; never market observations, decisions, intents, or fills.

fault_origin values:
  GOVERNED_INJECTED_TRANSPORT_FAULT
  NATURAL_EXCHANGE_TRANSPORT_EVENT
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal, Mapping, Optional, Sequence

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    HttpFetcher,
)


class GovernedInjectedTransportDisconnectError(RuntimeError):
    """Reconnectable transport disconnect injected on the fetcher edge."""


SCHEMA_VERSION = "governed_injected_transport_fault_schedule.v1"
CAPABILITY_ID = (
    "PHASE_9_2_STEP_4_GOVERNED_PRODUCTIVE_TRANSPORT_FAULT_CONTROL_BINDING_IMPLEMENTATION_V1"
)
OWNER = (
    "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1."
    "governed_injected_transport_fault_v1"
)
PACKAGE_MARKER = f"{CAPABILITY_ID}=true"

FAULT_ORIGIN_GOVERNED = "GOVERNED_INJECTED_TRANSPORT_FAULT"
FAULT_ORIGIN_NATURAL = "NATURAL_EXCHANGE_TRANSPORT_EVENT"

FaultKindV1 = Literal["HTTP_429", "TRANSPORT_DISCONNECT"]

ALLOWED_DISCONNECT_TOKENS: frozenset[str] = frozenset(
    {
        "URL_ERROR",
        "TIMEOUT",
        "CONNECTION_RESET",
        "TLS_ERROR",
    }
)

MAX_FAULTS_PER_SCHEDULE = 2
DEFAULT_RETRY_AFTER_SECONDS = 1.0


class GovernedTransportFaultControlError(ValueError):
    """Fail-closed schedule / wrapper contract error."""


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class GovernedTransportFaultSpecV1:
    fault_id: str
    sequence: int
    kind: FaultKindV1
    after_successful_gets: int
    retry_after_seconds: float | None = None
    disconnect_error_token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_id": self.fault_id,
            "sequence": int(self.sequence),
            "kind": self.kind,
            "after_successful_gets": int(self.after_successful_gets),
            "retry_after_seconds": self.retry_after_seconds,
            "disconnect_error_token": self.disconnect_error_token,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GovernedTransportFaultSpecV1":
        kind = str(payload.get("kind") or "")
        if kind not in {"HTTP_429", "TRANSPORT_DISCONNECT"}:
            raise GovernedTransportFaultControlError(f"UNKNOWN_FAULT_KIND:{kind}")
        return cls(
            fault_id=str(payload.get("fault_id") or ""),
            sequence=int(payload.get("sequence") or 0),
            kind=kind,  # type: ignore[arg-type]
            after_successful_gets=int(payload.get("after_successful_gets") or 0),
            retry_after_seconds=(
                None
                if payload.get("retry_after_seconds") is None
                else float(payload["retry_after_seconds"])
            ),
            disconnect_error_token=(
                None
                if payload.get("disconnect_error_token") is None
                else str(payload["disconnect_error_token"])
            ),
        )


@dataclass(frozen=True)
class GovernedTransportFaultScheduleV1:
    schedule_id: str
    session_id: str
    expected_repository_sha: str
    expected_config_digest: str
    authorization_id: str
    faults: tuple[GovernedTransportFaultSpecV1, ...]
    enabled: bool = False
    schema_version: str = SCHEMA_VERSION
    capability_id: str = CAPABILITY_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "schedule_id": self.schedule_id,
            "session_id": self.session_id,
            "expected_repository_sha": self.expected_repository_sha,
            "expected_config_digest": self.expected_config_digest,
            "authorization_id": self.authorization_id,
            "enabled": bool(self.enabled),
            "faults": [f.to_dict() for f in self.faults],
        }

    def digest(self) -> str:
        material = dict(self.to_dict())
        # Digest excludes enabled so disable/enable does not rewrite identity of content.
        material.pop("enabled", None)
        return _sha256_hex(_canonical_json(material))

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise GovernedTransportFaultControlError("SCHEDULE_SCHEMA_MISMATCH")
        if self.capability_id != CAPABILITY_ID:
            raise GovernedTransportFaultControlError("SCHEDULE_CAPABILITY_MISMATCH")
        if not self.schedule_id.strip():
            raise GovernedTransportFaultControlError("SCHEDULE_ID_REQUIRED")
        if not self.session_id.strip():
            raise GovernedTransportFaultControlError("SESSION_ID_REQUIRED")
        if not self.expected_repository_sha.strip():
            raise GovernedTransportFaultControlError("REPOSITORY_SHA_REQUIRED")
        if not self.expected_config_digest.strip():
            raise GovernedTransportFaultControlError("CONFIG_DIGEST_REQUIRED")
        if not self.authorization_id.strip():
            raise GovernedTransportFaultControlError("AUTHORIZATION_ID_REQUIRED")
        if len(self.faults) == 0:
            raise GovernedTransportFaultControlError("FAULTS_REQUIRED")
        if len(self.faults) > MAX_FAULTS_PER_SCHEDULE:
            raise GovernedTransportFaultControlError("FAULT_COUNT_UNBOUNDED")
        seen_ids: set[str] = set()
        seen_seq: set[int] = set()
        prev_after = -1
        kinds_seen: set[str] = set()
        for fault in self.faults:
            if not fault.fault_id.strip():
                raise GovernedTransportFaultControlError("FAULT_ID_REQUIRED")
            if fault.fault_id in seen_ids:
                raise GovernedTransportFaultControlError(f"DUPLICATE_FAULT_ID:{fault.fault_id}")
            seen_ids.add(fault.fault_id)
            if int(fault.sequence) < 1:
                raise GovernedTransportFaultControlError("FAULT_SEQUENCE_INVALID")
            if int(fault.sequence) in seen_seq:
                raise GovernedTransportFaultControlError(
                    f"DUPLICATE_FAULT_SEQUENCE:{fault.sequence}"
                )
            seen_seq.add(int(fault.sequence))
            if int(fault.after_successful_gets) < 1:
                raise GovernedTransportFaultControlError("AFTER_SUCCESSFUL_GETS_MUST_BE_POSITIVE")
            if int(fault.after_successful_gets) <= prev_after:
                raise GovernedTransportFaultControlError("FAULT_AFTER_GETS_NOT_STRICTLY_INCREASING")
            prev_after = int(fault.after_successful_gets)
            if fault.kind in kinds_seen:
                raise GovernedTransportFaultControlError(f"DUPLICATE_FAULT_KIND:{fault.kind}")
            kinds_seen.add(fault.kind)
            if fault.kind == "HTTP_429":
                if fault.retry_after_seconds is None:
                    raise GovernedTransportFaultControlError("RETRY_AFTER_REQUIRED_FOR_HTTP_429")
                if float(fault.retry_after_seconds) <= 0.0:
                    raise GovernedTransportFaultControlError("RETRY_AFTER_MUST_BE_POSITIVE")
                if fault.disconnect_error_token is not None:
                    raise GovernedTransportFaultControlError(
                        "DISCONNECT_TOKEN_FORBIDDEN_ON_HTTP_429"
                    )
            else:
                token = str(fault.disconnect_error_token or "").strip()
                if not token:
                    raise GovernedTransportFaultControlError("DISCONNECT_TOKEN_REQUIRED")
                if token not in ALLOWED_DISCONNECT_TOKENS:
                    raise GovernedTransportFaultControlError(
                        f"DISCONNECT_TOKEN_NOT_ALLOWED:{token}"
                    )
                if fault.retry_after_seconds is not None:
                    raise GovernedTransportFaultControlError(
                        "RETRY_AFTER_FORBIDDEN_ON_TRANSPORT_DISCONNECT"
                    )
        # Sequences must be contiguous 1..N in order of faults tuple.
        expected = list(range(1, len(self.faults) + 1))
        actual = [int(f.sequence) for f in self.faults]
        if actual != expected:
            raise GovernedTransportFaultControlError("FAULT_SEQUENCE_OUT_OF_ORDER")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GovernedTransportFaultScheduleV1":
        faults_raw = payload.get("faults") or []
        if not isinstance(faults_raw, list):
            raise GovernedTransportFaultControlError("FAULTS_NOT_LIST")
        faults = tuple(GovernedTransportFaultSpecV1.from_dict(item) for item in faults_raw)
        schedule = cls(
            schedule_id=str(payload.get("schedule_id") or ""),
            session_id=str(payload.get("session_id") or ""),
            expected_repository_sha=str(payload.get("expected_repository_sha") or ""),
            expected_config_digest=str(payload.get("expected_config_digest") or ""),
            authorization_id=str(payload.get("authorization_id") or ""),
            faults=faults,
            enabled=bool(payload.get("enabled")),
            schema_version=str(payload.get("schema_version") or SCHEMA_VERSION),
            capability_id=str(payload.get("capability_id") or CAPABILITY_ID),
        )
        schedule.validate()
        return schedule


def build_default_step4_fault_schedule_v1(
    *,
    schedule_id: str,
    session_id: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    authorization_id: str,
    http_429_after_successful_gets: int = 2,
    disconnect_after_successful_gets: int = 4,
    retry_after_seconds: float = DEFAULT_RETRY_AFTER_SECONDS,
    disconnect_error_token: str = "URL_ERROR",
    enabled: bool = False,
) -> GovernedTransportFaultScheduleV1:
    """Canonical bounded Step-4 schedule: one 429 then one disconnect; default disabled."""
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id=schedule_id,
        session_id=session_id,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id=authorization_id,
        enabled=enabled,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="fault_http_429_v1",
                sequence=1,
                kind="HTTP_429",
                after_successful_gets=int(http_429_after_successful_gets),
                retry_after_seconds=float(retry_after_seconds),
            ),
            GovernedTransportFaultSpecV1(
                fault_id="fault_transport_disconnect_v1",
                sequence=2,
                kind="TRANSPORT_DISCONNECT",
                after_successful_gets=int(disconnect_after_successful_gets),
                disconnect_error_token=str(disconnect_error_token),
            ),
        ),
    )
    schedule.validate()
    return schedule


def assert_schedule_bindings_v1(
    schedule: GovernedTransportFaultScheduleV1,
    *,
    session_id: str,
    repository_sha: str,
    config_digest: str,
    authorization_id: str | None = None,
) -> None:
    """Fail-closed session/auth/sha/digest binding check."""
    schedule.validate()
    if not schedule.enabled:
        raise GovernedTransportFaultControlError("SCHEDULE_NOT_ENABLED")
    if schedule.session_id != session_id:
        raise GovernedTransportFaultControlError("SCHEDULE_SESSION_ID_MISMATCH")
    if schedule.expected_repository_sha != repository_sha:
        raise GovernedTransportFaultControlError("SCHEDULE_REPOSITORY_SHA_MISMATCH")
    if schedule.expected_config_digest != config_digest:
        raise GovernedTransportFaultControlError("SCHEDULE_CONFIG_DIGEST_MISMATCH")
    if authorization_id is not None and schedule.authorization_id != authorization_id:
        raise GovernedTransportFaultControlError("SCHEDULE_AUTHORIZATION_ID_MISMATCH")


@dataclass
class GovernedInjectedTransportFaultEventV1:
    fault_id: str
    sequence: int
    kind: FaultKindV1
    fault_origin: str
    successful_gets_before: int
    retry_after_raw: str | None = None
    retry_after_parsed_seconds: float | None = None
    disconnect_error_token: str | None = None
    mono_ts: float | None = None
    wall_ts: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GovernedInjectedTransportFaultTelemetryV1:
    schema_version: str = "governed_injected_transport_fault_telemetry.v1"
    capability_id: str = CAPABILITY_ID
    schedule_id: str = ""
    schedule_digest: str = ""
    session_id: str = ""
    enabled: bool = False
    successful_real_get_count: int = 0
    governed_injected_fault_count: int = 0
    http_429_injected_count: int = 0
    reconnectable_transport_error_injected_count: int = 0
    fabricated_observation_count: int = 0
    consumed_fault_ids: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "schedule_id": self.schedule_id,
            "schedule_digest": self.schedule_digest,
            "session_id": self.session_id,
            "enabled": bool(self.enabled),
            "successful_real_get_count": int(self.successful_real_get_count),
            "governed_injected_fault_count": int(self.governed_injected_fault_count),
            "http_429_injected_count": int(self.http_429_injected_count),
            "reconnectable_transport_error_injected_count": int(
                self.reconnectable_transport_error_injected_count
            ),
            "fabricated_observation_count": int(self.fabricated_observation_count),
            "consumed_fault_ids": list(self.consumed_fault_ids),
            "events": list(self.events),
            "fault_origin_governed": FAULT_ORIGIN_GOVERNED,
            "fault_origin_natural": FAULT_ORIGIN_NATURAL,
        }


@dataclass
class GovernedInjectedTransportFaultWrapperV1:
    """HttpFetcher wrapper. Default: pass-through when schedule disabled/absent."""

    real_fetcher: HttpFetcher
    schedule: GovernedTransportFaultScheduleV1 | None = None
    wall_clock: Callable[[], float] = time.time
    mono_clock: Callable[[], float] = time.monotonic
    telemetry: GovernedInjectedTransportFaultTelemetryV1 = field(
        default_factory=GovernedInjectedTransportFaultTelemetryV1
    )
    _consumed: set[str] = field(default_factory=set, init=False, repr=False)
    _next_index: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.schedule is None:
            self.telemetry.enabled = False
            return
        self.schedule.validate()
        self.telemetry.enabled = bool(self.schedule.enabled)
        self.telemetry.schedule_id = self.schedule.schedule_id
        self.telemetry.schedule_digest = self.schedule.digest()
        self.telemetry.session_id = self.schedule.session_id

    @property
    def enabled(self) -> bool:
        return self.schedule is not None and bool(self.schedule.enabled)

    def _pending_fault(self) -> GovernedTransportFaultSpecV1 | None:
        if not self.enabled or self.schedule is None:
            return None
        if self._next_index >= len(self.schedule.faults):
            return None
        return self.schedule.faults[self._next_index]

    def _consume(self, fault: GovernedTransportFaultSpecV1) -> None:
        if fault.fault_id in self._consumed:
            raise GovernedTransportFaultControlError(f"FAULT_ALREADY_CONSUMED:{fault.fault_id}")
        self._consumed.add(fault.fault_id)
        self._next_index += 1
        self.telemetry.consumed_fault_ids.append(fault.fault_id)
        self.telemetry.governed_injected_fault_count += 1

    def __call__(
        self,
        url: str,
        method: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> tuple[int, bytes, Mapping[str, str]]:
        pending = self._pending_fault()
        if pending is not None and self.telemetry.successful_real_get_count >= int(
            pending.after_successful_gets
        ):
            return self._inject(pending)

        status, body, resp_headers = self.real_fetcher(url, method, headers, timeout)
        # Count only successful real public GETs toward schedule thresholds.
        if int(status) < 400:
            self.telemetry.successful_real_get_count += 1
        # Natural path: never rewrite body / status.
        return status, body, resp_headers

    def _inject(self, fault: GovernedTransportFaultSpecV1) -> tuple[int, bytes, Mapping[str, str]]:
        wall = float(self.wall_clock())
        mono = float(self.mono_clock())
        if fault.kind == "HTTP_429":
            retry_after = float(fault.retry_after_seconds or DEFAULT_RETRY_AFTER_SECONDS)
            raw = str(int(retry_after) if retry_after == int(retry_after) else retry_after)
            self._consume(fault)
            self.telemetry.http_429_injected_count += 1
            event = GovernedInjectedTransportFaultEventV1(
                fault_id=fault.fault_id,
                sequence=int(fault.sequence),
                kind="HTTP_429",
                fault_origin=FAULT_ORIGIN_GOVERNED,
                successful_gets_before=int(self.telemetry.successful_real_get_count),
                retry_after_raw=raw,
                retry_after_parsed_seconds=float(retry_after),
                mono_ts=mono,
                wall_ts=wall,
            )
            payload = event.to_dict()
            payload["http_status"] = 429
            self.telemetry.events.append(payload)
            # Empty JSON object — not a market observation payload.
            headers = {
                "Retry-After": raw,
                "Content-Type": "application/json",
                "X-Peak-Trade-Fault-Origin": FAULT_ORIGIN_GOVERNED,
                "X-Peak-Trade-Fault-Id": fault.fault_id,
            }
            return 429, b"{}", headers

        token = str(fault.disconnect_error_token or "URL_ERROR")
        self._consume(fault)
        self.telemetry.reconnectable_transport_error_injected_count += 1
        event = GovernedInjectedTransportFaultEventV1(
            fault_id=fault.fault_id,
            sequence=int(fault.sequence),
            kind="TRANSPORT_DISCONNECT",
            fault_origin=FAULT_ORIGIN_GOVERNED,
            successful_gets_before=int(self.telemetry.successful_real_get_count),
            disconnect_error_token=token,
            mono_ts=mono,
            wall_ts=wall,
        )
        self.telemetry.events.append(event.to_dict())
        raise GovernedInjectedTransportDisconnectError(
            f"{token}:{FAULT_ORIGIN_GOVERNED}:{fault.fault_id}"
        )

    def schedule_fully_consumed(self) -> bool:
        if self.schedule is None or not self.enabled:
            return True
        return len(self._consumed) == len(self.schedule.faults)


def wrap_fetcher_with_governed_fault_control_v1(
    real_fetcher: HttpFetcher,
    schedule: GovernedTransportFaultScheduleV1 | None,
) -> HttpFetcher:
    """Return real fetcher unchanged when schedule is None or disabled."""
    if schedule is None or not bool(schedule.enabled):
        return real_fetcher
    schedule.validate()
    return GovernedInjectedTransportFaultWrapperV1(real_fetcher=real_fetcher, schedule=schedule)


def extract_wrapper_telemetry_v1(
    fetcher: Any,
) -> GovernedInjectedTransportFaultTelemetryV1 | None:
    if isinstance(fetcher, GovernedInjectedTransportFaultWrapperV1):
        return fetcher.telemetry
    return None


def build_transport_telemetry_document_v1(
    *,
    session_id: str,
    transport_http_429_count: int,
    transport_events: Sequence[Mapping[str, Any]] | None,
    wrapper_telemetry: GovernedInjectedTransportFaultTelemetryV1 | None,
    reconnect_attempt_count: int,
    reconnect_success_count: int,
    post_reconnect_continuation_count: int,
    post_reconnect_reconciliation_count: int,
    stale_gate_activation_count: int,
    rate_limit_event_count: int,
    natural_transport_fault_count: int = 0,
    last_retry_after_raw: str | None = None,
    last_retry_after_parsed_seconds: float | None = None,
    last_backoff_source: str | None = None,
    last_backoff_seconds: float | None = None,
) -> dict[str, Any]:
    """Canonical transport_telemetry.json payload for wallclock evidence."""
    governed = int(
        wrapper_telemetry.governed_injected_fault_count if wrapper_telemetry is not None else 0
    )
    events: list[dict[str, Any]] = []
    if wrapper_telemetry is not None:
        events.extend(list(wrapper_telemetry.events))
    for ev in transport_events or ():
        row = dict(ev)
        if "fault_origin" not in row:
            # Transport-native events without injection marker are natural.
            row["fault_origin"] = FAULT_ORIGIN_NATURAL
        events.append(row)
    return {
        "schema_version": "phase_9_2_step_4_transport_telemetry.v1",
        "capability_id": CAPABILITY_ID,
        "session_id": session_id,
        "schedule_id": (wrapper_telemetry.schedule_id if wrapper_telemetry is not None else ""),
        "schedule_digest": (
            wrapper_telemetry.schedule_digest if wrapper_telemetry is not None else ""
        ),
        "fault_events_total": governed + int(natural_transport_fault_count),
        "governed_injected_fault_count": governed,
        "natural_transport_fault_count": int(natural_transport_fault_count),
        "http_429_count": int(transport_http_429_count),
        "rate_limit_event_count": int(rate_limit_event_count),
        "retry_after_raw": last_retry_after_raw,
        "retry_after_parsed_seconds": last_retry_after_parsed_seconds,
        "backoff_source": last_backoff_source,
        "backoff_seconds": last_backoff_seconds,
        "reconnectable_transport_error_count": int(
            wrapper_telemetry.reconnectable_transport_error_injected_count
            if wrapper_telemetry is not None
            else 0
        )
        + int(natural_transport_fault_count),
        "reconnect_attempt_count": int(reconnect_attempt_count),
        "reconnect_success_count": int(reconnect_success_count),
        "post_reconnect_continuation_count": int(post_reconnect_continuation_count),
        "post_reconnect_reconciliation_count": int(post_reconnect_reconciliation_count),
        "stale_gate_activation_count": int(stale_gate_activation_count),
        "fabricated_observation_count": int(
            wrapper_telemetry.fabricated_observation_count if wrapper_telemetry is not None else 0
        ),
        "events": events,
        "fault_origin_values": [FAULT_ORIGIN_GOVERNED, FAULT_ORIGIN_NATURAL],
        "substring_rate_limit_count_authority_effect": "NONE",
        "rate_limit_metric_owner": (
            "ops.phase_9_2_public_md_session_preflight_v1.rate_limit_metric_v1"
        ),
    }
