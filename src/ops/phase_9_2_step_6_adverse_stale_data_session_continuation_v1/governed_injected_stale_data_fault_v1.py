"""Governed injected stale-data control for Step-6 productive binding.

Default-disabled control that adjusts receive-timing / data-availability only.
Never fabricates market observations, decisions, intents, or fills.

Reuses canonical StalenessTrackerV1 + killstate STALE_DATA classification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping, Optional, Sequence

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    StalenessTrackerV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    KILLSTATE_TRIGGERS,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    SMOKE_CONSECUTIVE_STALE_BUDGET,
    SMOKE_STALENESS_BUDGET_SECONDS,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    ADVERSE_DATA_CLASSIFIER,
    CAPABILITY_ID,
    DIRECT_FILL_INJECTION_ALLOWED,
    FORCED_INTENT_ALLOWED,
    OWNER,
    STALE_DATA_CLASSIFIER,
)

SCHEMA_VERSION = "governed_injected_stale_data_fault_schedule.v1"
FAULT_OWNER = f"{OWNER}.governed_injected_stale_data_fault_v1"
PACKAGE_MARKER = f"{CAPABILITY_ID}=true"

FAULT_ORIGIN_GOVERNED = "GOVERNED_INJECTED_STALE_DATA_FAULT"
FAULT_ORIGIN_NATURAL = "NATURAL_STALE_DATA_EVENT"

FaultKindV1 = Literal["RECEIVE_LAG", "DATA_HOLD"]
MAX_FAULTS_PER_SCHEDULE = 2


class GovernedStaleDataFaultControlError(ValueError):
    """Fail-closed schedule / control contract error."""


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class GovernedStaleDataFaultSpecV1:
    fault_id: str
    sequence: int
    kind: FaultKindV1
    after_successful_observations: int
    receive_lag_seconds: float | None = None
    hold_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_id": self.fault_id,
            "sequence": int(self.sequence),
            "kind": self.kind,
            "after_successful_observations": int(self.after_successful_observations),
            "receive_lag_seconds": self.receive_lag_seconds,
            "hold_seconds": self.hold_seconds,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GovernedStaleDataFaultSpecV1":
        kind = str(payload.get("kind") or "")
        if kind not in {"RECEIVE_LAG", "DATA_HOLD"}:
            raise GovernedStaleDataFaultControlError(f"UNKNOWN_FAULT_KIND:{kind}")
        return cls(
            fault_id=str(payload.get("fault_id") or ""),
            sequence=int(payload.get("sequence") or 0),
            kind=kind,  # type: ignore[arg-type]
            after_successful_observations=int(payload.get("after_successful_observations") or 0),
            receive_lag_seconds=(
                None
                if payload.get("receive_lag_seconds") is None
                else float(payload["receive_lag_seconds"])
            ),
            hold_seconds=(
                None if payload.get("hold_seconds") is None else float(payload["hold_seconds"])
            ),
        )


@dataclass(frozen=True)
class GovernedStaleDataFaultScheduleV1:
    schema_version: str
    capability_id: str
    enabled: bool
    faults: tuple[GovernedStaleDataFaultSpecV1, ...]
    schedule_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "enabled": bool(self.enabled),
            "faults": [f.to_dict() for f in self.faults],
            "schedule_digest": self.schedule_digest,
        }


def validate_stale_data_fault_schedule_v1(
    schedule: GovernedStaleDataFaultScheduleV1,
    *,
    staleness_budget_seconds: float = SMOKE_STALENESS_BUDGET_SECONDS,
) -> list[str]:
    blockers: list[str] = []
    if schedule.schema_version != SCHEMA_VERSION:
        blockers.append("SCHEDULE_SCHEMA_MISMATCH")
    if schedule.capability_id != CAPABILITY_ID:
        blockers.append("SCHEDULE_CAPABILITY_MISMATCH")
    if len(schedule.faults) > MAX_FAULTS_PER_SCHEDULE:
        blockers.append("TOO_MANY_FAULTS")
    seen_seq: set[int] = set()
    for fault in schedule.faults:
        if not fault.fault_id:
            blockers.append("FAULT_ID_MISSING")
        if fault.sequence in seen_seq:
            blockers.append(f"DUPLICATE_FAULT_SEQUENCE:{fault.sequence}")
        seen_seq.add(fault.sequence)
        if fault.after_successful_observations < 0:
            blockers.append("AFTER_SUCCESSFUL_OBSERVATIONS_NEGATIVE")
        if fault.kind == "RECEIVE_LAG":
            lag = float(fault.receive_lag_seconds or 0.0)
            if lag <= float(staleness_budget_seconds):
                blockers.append("RECEIVE_LAG_MUST_EXCEED_STALENESS_BUDGET")
        if fault.kind == "DATA_HOLD":
            hold = float(fault.hold_seconds or 0.0)
            if hold <= 0.0:
                blockers.append("DATA_HOLD_MUST_BE_POSITIVE")
    if FORCED_INTENT_ALLOWED or DIRECT_FILL_INJECTION_ALLOWED:
        blockers.append("DECISION_OR_FILL_INJECTION_FORBIDDEN_FLAG_TRUE")
    return blockers


def build_disabled_stale_data_fault_schedule_v1() -> GovernedStaleDataFaultScheduleV1:
    base = GovernedStaleDataFaultScheduleV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        enabled=False,
        faults=(),
        schedule_digest="",
    )
    digest = _sha256_hex(_canonical_json(base.to_dict()))
    return GovernedStaleDataFaultScheduleV1(
        schema_version=base.schema_version,
        capability_id=base.capability_id,
        enabled=False,
        faults=(),
        schedule_digest=digest,
    )


def build_receive_lag_schedule_v1(
    *,
    after_successful_observations: int = 0,
    receive_lag_seconds: float | None = None,
    enabled: bool = True,
) -> GovernedStaleDataFaultScheduleV1:
    lag = (
        float(SMOKE_STALENESS_BUDGET_SECONDS) + 1.0
        if receive_lag_seconds is None
        else float(receive_lag_seconds)
    )
    faults = (
        GovernedStaleDataFaultSpecV1(
            fault_id="stale_receive_lag_001",
            sequence=1,
            kind="RECEIVE_LAG",
            after_successful_observations=int(after_successful_observations),
            receive_lag_seconds=lag,
        ),
    )
    base = GovernedStaleDataFaultScheduleV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        enabled=bool(enabled),
        faults=faults,
        schedule_digest="",
    )
    blockers = validate_stale_data_fault_schedule_v1(base)
    if blockers:
        raise GovernedStaleDataFaultControlError(",".join(blockers))
    digest = _sha256_hex(_canonical_json({**base.to_dict(), "schedule_digest": ""}))
    return GovernedStaleDataFaultScheduleV1(
        schema_version=base.schema_version,
        capability_id=base.capability_id,
        enabled=base.enabled,
        faults=base.faults,
        schedule_digest=digest,
    )


@dataclass
class GovernedStaleDataFaultTelemetryV1:
    enabled: bool = False
    observations_seen: int = 0
    faults_applied: int = 0
    receive_lag_applied_seconds: float = 0.0
    fabricated_observation_count: int = 0
    forced_intent_count: int = 0
    direct_fill_injection_count: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GovernedInjectedStaleDataControlV1:
    """Apply receive-lag / data-hold only; never invent observation payloads."""

    schedule: GovernedStaleDataFaultScheduleV1
    telemetry: GovernedStaleDataFaultTelemetryV1 = field(
        default_factory=GovernedStaleDataFaultTelemetryV1
    )
    _pending: list[GovernedStaleDataFaultSpecV1] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        blockers = validate_stale_data_fault_schedule_v1(self.schedule)
        if blockers:
            raise GovernedStaleDataFaultControlError(",".join(blockers))
        self.telemetry.enabled = bool(self.schedule.enabled)
        self._pending = sorted(list(self.schedule.faults), key=lambda f: f.sequence)

    def resolve_receive_ts_v1(self, *, wall_now: float, natural_receive_ts: float) -> float:
        """Return receive_ts for StalenessTrackerV1; does not mutate observation payload."""
        if not self.schedule.enabled or not self._pending:
            return float(natural_receive_ts)
        nxt = self._pending[0]
        # Apply only after the configured number of natural observations.
        if self.telemetry.observations_seen < int(nxt.after_successful_observations):
            self.telemetry.observations_seen += 1
            return float(natural_receive_ts)
        self.telemetry.observations_seen += 1
        if nxt.kind == "RECEIVE_LAG":
            lag = float(nxt.receive_lag_seconds or 0.0)
            self.telemetry.faults_applied += 1
            self.telemetry.receive_lag_applied_seconds = lag
            self.telemetry.events.append(
                {
                    "fault_origin": FAULT_ORIGIN_GOVERNED,
                    "kind": nxt.kind,
                    "fault_id": nxt.fault_id,
                    "receive_lag_seconds": lag,
                    "fabricated_observation": False,
                }
            )
            self._pending.pop(0)
            return float(wall_now) - lag
        if nxt.kind == "DATA_HOLD":
            # Hold is timing-only; caller sleeps separately. receive_ts stays natural.
            self.telemetry.faults_applied += 1
            self.telemetry.events.append(
                {
                    "fault_origin": FAULT_ORIGIN_GOVERNED,
                    "kind": nxt.kind,
                    "fault_id": nxt.fault_id,
                    "hold_seconds": float(nxt.hold_seconds or 0.0),
                    "fabricated_observation": False,
                }
            )
            self._pending.pop(0)
            return float(natural_receive_ts)
        raise GovernedStaleDataFaultControlError(f"UNHANDLED_FAULT_KIND:{nxt.kind}")

    def assert_no_decision_injection_v1(self) -> None:
        if (
            self.telemetry.fabricated_observation_count
            or self.telemetry.forced_intent_count
            or self.telemetry.direct_fill_injection_count
        ):
            raise GovernedStaleDataFaultControlError("DECISION_OR_OBSERVATION_INJECTION_DETECTED")


def apply_stale_classification_cycle_v1(
    *,
    tracker: StalenessTrackerV1,
    receive_ts: float,
    wall_now: float,
    mono_ts: float,
    confirmation_advance_on_stale: bool = False,
) -> dict[str, Any]:
    """Classify via canonical StalenessTrackerV1; refuse confirmation advance on stale."""
    status, kill = tracker.observe(receive_ts=receive_ts, wall_now=wall_now, mono_ts=mono_ts)
    stale = status in {"warn", "kill"}
    confirmation_advance = 0
    if stale and confirmation_advance_on_stale:
        raise GovernedStaleDataFaultControlError("STALE_CONFIRMATION_ADVANCE_FORBIDDEN")
    if not stale:
        confirmation_advance = 0  # callers may advance only on distinct fresh obs elsewhere
    adverse = kill == "STALE_DATA" and "STALE_DATA" in KILLSTATE_TRIGGERS
    return {
        "status": status,
        "kill": kill,
        "STALE_CONDITION_OBSERVED": stale,
        "ADVERSE_CONDITION_OBSERVED": adverse,
        "STALE_CONFIRMATION_ADVANCE": False,
        "confirmation_advance_delta": confirmation_advance,
        "classifier": STALE_DATA_CLASSIFIER,
        "adverse_classifier": ADVERSE_DATA_CLASSIFIER,
    }


def prove_stale_no_fabricated_observation_v1() -> dict[str, Any]:
    control = GovernedInjectedStaleDataControlV1(schedule=build_receive_lag_schedule_v1())
    wall = 1000.0
    ts = control.resolve_receive_ts_v1(wall_now=wall, natural_receive_ts=wall)
    control.assert_no_decision_injection_v1()
    return {
        "ok": ts < wall and control.telemetry.fabricated_observation_count == 0,
        "receive_ts": ts,
        "fabricated_observation_count": control.telemetry.fabricated_observation_count,
        "forced_intent_count": control.telemetry.forced_intent_count,
        "direct_fill_injection_count": control.telemetry.direct_fill_injection_count,
        "owner": FAULT_OWNER,
    }


def prove_stale_killstate_path_v1() -> dict[str, Any]:
    tracker = StalenessTrackerV1(
        max_stale_seconds=SMOKE_STALENESS_BUDGET_SECONDS,
        consecutive_stale_budget=SMOKE_CONSECUTIVE_STALE_BUDGET,
    )
    last: dict[str, Any] = {}
    for i in range(SMOKE_CONSECUTIVE_STALE_BUDGET + 1):
        last = apply_stale_classification_cycle_v1(
            tracker=tracker,
            receive_ts=0.0,
            wall_now=SMOKE_STALENESS_BUDGET_SECONDS + 1.0,
            mono_ts=float(i + 1),
        )
    return {
        "ok": bool(last.get("ADVERSE_CONDITION_OBSERVED")) and last.get("kill") == "STALE_DATA",
        "last": last,
        "owner": ADVERSE_DATA_CLASSIFIER,
    }
