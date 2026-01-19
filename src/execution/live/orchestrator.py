"""
C2 Live Session Orchestrator (DRYRUN, deterministic, snapshot-only).

Constraints (NON-NEGOTIABLE):
- NO-LIVE: no broker deps, no network calls
- Deterministic: all time via injected clock, randomness via injected seed
- No unbounded loops; no sleeps unless explicitly injected
- IO only via provided sinks (list/file-like/custom)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Protocol, Sequence

from src.execution.determinism import SimClock, stable_id

from .audit import AuditLevel, AuditTrail, Clock
from .state import SessionStateSnapshot, SessionStatus, snapshot_json


class LineSink(Protocol):
    def write(self, line: str) -> None: ...


def _write_line(sink: Any, line: str) -> None:
    if sink is None:
        return
    append = getattr(sink, "append", None)
    if callable(append):
        append(line)
        return
    write = getattr(sink, "write", None)
    if callable(write):
        write(line)
        return
    raise TypeError("Unsupported sink type: expected .append(str) or .write(str)")


def _canonical_json(obj: Mapping[str, Any]) -> str:
    return json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class DryrunConfig:
    """
    Input contract for a deterministic dryrun session.
    """

    strategy_id: str
    run_id: str
    seed: int
    clock_mode: str = "injected"
    max_sink_retries: int = 0
    # Optional, purely local validation gate (no registry/network).
    strategy_allowlist: Optional[Sequence[str]] = None

    def normalized_allowlist(self) -> Optional[tuple[str, ...]]:
        if self.strategy_allowlist is None:
            return None
        return tuple(sorted(str(x) for x in self.strategy_allowlist))


@dataclass(frozen=True)
class DryrunResult:
    accepted: bool
    status: SessionStatus
    run_id: str
    strategy_id: str
    seed: int
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    state_snapshots: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)
    audit_events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    reject_code: Optional[str] = None
    reject_reason: Optional[str] = None
    fail_code: Optional[str] = None
    fail_reason: Optional[str] = None


class LiveSessionOrchestrator:
    """
    Deterministic dryrun orchestrator.

    Artifacts:
    - events JSONL (via event_sink)
    - state snapshots JSONL (via state_sink)
    - metrics snapshot JSON (via metrics_sink)
    - audit events JSONL (via audit_sink or direct AuditTrail sink)
    """

    def __init__(self) -> None:
        # Stateless by design; deterministic seq/clocks are per-run.
        pass

    def run_dryrun(
        self,
        config: DryrunConfig,
        *,
        clock: Clock,
        event_sink: Any = None,
        state_sink: Any = None,
        metrics_sink: Any = None,
        audit_sink: Any = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ) -> DryrunResult:
        event_clock = SimClock()
        state_clock = SimClock()
        audit = AuditTrail(clock=clock, sink=audit_sink, seq_start=0)
        allowlist = config.normalized_allowlist()

        events: list[dict[str, Any]] = []
        snapshots: list[dict[str, Any]] = []

        started_ts = clock.now().isoformat()

        def emit_state(snapshot: SessionStateSnapshot) -> None:
            obj = snapshot.to_dict()
            snapshots.append(obj)
            self._emit_with_retries(
                sink=state_sink,
                line=snapshot_json(obj) + "\n",
                max_retries=config.max_sink_retries,
                audit=audit,
                sleep_fn=sleep_fn,
                context={"artifact": "state", "status": snapshot.status.value},
            )

        def emit_event(event_type: str, payload: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
            ts_sim = event_clock.tick()
            payload_obj = dict(payload or {})

            canonical_fields = {
                "run_id": config.run_id,
                "strategy_id": config.strategy_id,
                "event_type": event_type,
                "ts_sim": ts_sim,
                "payload": payload_obj,
            }
            event_id = stable_id(kind="c2_dryrun_event", fields=canonical_fields)
            ev = {
                "schema_version": "C2_DRYRUN_V1",
                "event_id": event_id,
                "run_id": config.run_id,
                "strategy_id": config.strategy_id,
                "event_type": event_type,
                "ts_sim": ts_sim,
                "ts_utc": clock.now().isoformat(),
                "payload": payload_obj,
            }
            events.append(ev)
            self._emit_with_retries(
                sink=event_sink,
                line=_canonical_json(ev) + "\n",
                max_retries=config.max_sink_retries,
                audit=audit,
                sleep_fn=sleep_fn,
                context={"artifact": "events", "event_type": event_type},
            )
            return ev

        def fail_result(*, fail_code: str, fail_reason: str) -> DryrunResult:
            # Best-effort: do not let failures cascade if sinks are broken.
            try:
                audit.emit(
                    level=AuditLevel.ERROR,
                    code=fail_code,
                    message="dryrun failed",
                    meta={"reason": fail_reason},
                )
            except Exception:
                pass
            ended_ts = clock.now().isoformat()
            try:
                emit_state(
                    SessionStateSnapshot(
                        run_id=config.run_id,
                        strategy_id=config.strategy_id,
                        status=SessionStatus.FAILED,
                        ts_sim=state_clock.tick(),
                        started_ts=started_ts,
                        ended_ts=ended_ts,
                        fail_code=fail_code,
                        fail_reason=fail_reason,
                        events_emitted=len(events),
                        sink_retries=self._count_sink_retries(audit),
                        meta={"clock_mode": config.clock_mode},
                    )
                )
            except Exception:
                pass
            metrics = self._metrics_snapshot(
                config=config,
                status=SessionStatus.FAILED,
                events=events,
                audit=audit,
                sink_retries=self._count_sink_retries(audit),
            )
            try:
                self._emit_metrics(metrics_sink, metrics, audit=audit, max_retries=config.max_sink_retries, sleep_fn=sleep_fn)
            except Exception:
                pass
            return DryrunResult(
                accepted=False,
                status=SessionStatus.FAILED,
                run_id=config.run_id,
                strategy_id=config.strategy_id,
                seed=config.seed,
                events=tuple(events),
                state_snapshots=tuple(snapshots),
                metrics=metrics,
                audit_events=tuple(ev.to_dict() for ev in audit.events),
                fail_code=fail_code,
                fail_reason=fail_reason,
            )

        try:
            emit_state(
                SessionStateSnapshot(
                    run_id=config.run_id,
                    strategy_id=config.strategy_id,
                    status=SessionStatus.INIT,
                    ts_sim=state_clock.tick(),
                    started_ts=started_ts,
                    step=0,
                    events_emitted=0,
                    meta={"clock_mode": config.clock_mode},
                )
            )
            audit.emit(
                level=AuditLevel.INFO,
                code="C2_DRYRUN_START",
                message="dryrun start",
                meta={
                    "run_id": config.run_id,
                    "strategy_id": config.strategy_id,
                    "seed": config.seed,
                    "clock_mode": config.clock_mode,
                },
            )

        # ------------------------------------------------------------------
        # Preflight (reject rails)
        # ------------------------------------------------------------------
            reject_code, reject_reason = self._validate_config(config, allowlist=allowlist)
            if reject_code is not None:
                audit.emit(
                    level=AuditLevel.WARN,
                    code=reject_code,
                    message="dryrun rejected",
                    meta={"reason": reject_reason},
                )
                emit_event("REJECTED", {"code": reject_code, "reason": reject_reason})
                ended_ts = clock.now().isoformat()
                emit_state(
                    SessionStateSnapshot(
                        run_id=config.run_id,
                        strategy_id=config.strategy_id,
                        status=SessionStatus.REJECTED,
                        ts_sim=state_clock.tick(),
                        started_ts=started_ts,
                        ended_ts=ended_ts,
                        reject_code=reject_code,
                        reject_reason=reject_reason,
                        events_emitted=len(events),
                        meta={"clock_mode": config.clock_mode, "allowlist": list(allowlist or ())},
                    )
                )
                metrics = self._metrics_snapshot(
                    config=config,
                    status=SessionStatus.REJECTED,
                    events=events,
                    audit=audit,
                    sink_retries=self._count_sink_retries(audit),
                )
                self._emit_metrics(metrics_sink, metrics, audit=audit, max_retries=config.max_sink_retries, sleep_fn=sleep_fn)
                return DryrunResult(
                    accepted=False,
                    status=SessionStatus.REJECTED,
                    run_id=config.run_id,
                    strategy_id=config.strategy_id,
                    seed=config.seed,
                    events=tuple(events),
                    state_snapshots=tuple(snapshots),
                    metrics=metrics,
                    audit_events=tuple(ev.to_dict() for ev in audit.events),
                    reject_code=reject_code,
                    reject_reason=reject_reason,
                )

        # ------------------------------------------------------------------
        # Dryrun execution (bounded steps; no external deps)
        # ------------------------------------------------------------------
            emit_state(
                SessionStateSnapshot(
                    run_id=config.run_id,
                    strategy_id=config.strategy_id,
                    status=SessionStatus.RUNNING,
                    ts_sim=state_clock.tick(),
                    started_ts=started_ts,
                    step=1,
                    events_emitted=len(events),
                    meta={"clock_mode": config.clock_mode},
                )
            )
            emit_event("SESSION_START", {"clock_mode": config.clock_mode})

            rng = random.Random(config.seed)
            # Minimal deterministic "strategy step" simulation for end-to-end artifacts.
            decision = {
                "decision": rng.choice(["HOLD", "BUY", "SELL"]),
                "confidence": round(rng.random(), 6),
                "strategy_id": config.strategy_id,
            }
            emit_event("STRATEGY_TICK", decision)
            audit.emit(
                level=AuditLevel.INFO,
                code="C2_STRATEGY_TICK",
                message="strategy tick",
                meta=decision,
            )

            emit_event("SESSION_STOP", {"result": "ok"})
            audit.emit(level=AuditLevel.INFO, code="C2_DRYRUN_STOP", message="dryrun stop")

            ended_ts = clock.now().isoformat()
            emit_state(
                SessionStateSnapshot(
                    run_id=config.run_id,
                    strategy_id=config.strategy_id,
                    status=SessionStatus.COMPLETED,
                    ts_sim=state_clock.tick(),
                    started_ts=started_ts,
                    ended_ts=ended_ts,
                    step=2,
                    events_emitted=len(events),
                    sink_retries=self._count_sink_retries(audit),
                    meta={"clock_mode": config.clock_mode},
                )
            )

            metrics = self._metrics_snapshot(
                config=config,
                status=SessionStatus.COMPLETED,
                events=events,
                audit=audit,
                sink_retries=self._count_sink_retries(audit),
            )
            self._emit_metrics(metrics_sink, metrics, audit=audit, max_retries=config.max_sink_retries, sleep_fn=sleep_fn)

            return DryrunResult(
                accepted=True,
                status=SessionStatus.COMPLETED,
                run_id=config.run_id,
                strategy_id=config.strategy_id,
                seed=config.seed,
                events=tuple(events),
                state_snapshots=tuple(snapshots),
                metrics=metrics,
                audit_events=tuple(ev.to_dict() for ev in audit.events),
            )
        except Exception as e:
            # Prefer a deterministic failure code when sink write errors are present.
            fail_code = (
                "C2_ABORT_SINK_WRITE_FAILED"
                if any(ev.code == "C2_SINK_WRITE_FAILED" for ev in audit.events)
                else "C2_ABORT_EXCEPTION"
            )
            return fail_result(fail_code=fail_code, fail_reason=str(e))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _validate_config(
        self, config: DryrunConfig, *, allowlist: Optional[tuple[str, ...]]
    ) -> tuple[Optional[str], Optional[str]]:
        if not config.run_id or not str(config.run_id).strip():
            return ("C2_REJECT_MISSING_RUN_ID", "run_id is required")
        if not config.strategy_id or not str(config.strategy_id).strip():
            return ("C2_REJECT_MISSING_STRATEGY_ID", "strategy_id is required")
        if allowlist is not None and config.strategy_id not in allowlist:
            return ("C2_REJECT_STRATEGY_NOT_ALLOWED", "strategy_id not in allowlist")
        if config.max_sink_retries < 0:
            return ("C2_REJECT_BAD_RETRY_CONFIG", "max_sink_retries must be >= 0")
        return (None, None)

    def _emit_with_retries(
        self,
        *,
        sink: Any,
        line: str,
        max_retries: int,
        audit: AuditTrail,
        sleep_fn: Optional[Callable[[float], None]],
        context: Mapping[str, Any],
    ) -> None:
        attempts = 0
        while True:
            try:
                _write_line(sink, line)
                return
            except Exception as e:
                if attempts >= max_retries:
                    audit.emit(
                        level=AuditLevel.ERROR,
                        code="C2_SINK_WRITE_FAILED",
                        message="artifact sink write failed (aborting write)",
                        meta={"error": str(e), "attempts": attempts + 1, **dict(context)},
                    )
                    raise
                audit.emit(
                    level=AuditLevel.WARN,
                    code="C2_SINK_WRITE_RETRY",
                    message="artifact sink write failed (retrying)",
                    meta={"error": str(e), "attempt": attempts + 1, **dict(context)},
                )
                attempts += 1
                # No sleep unless explicitly injected.
                if sleep_fn is not None:
                    sleep_fn(0.0)

    def _emit_metrics(
        self,
        metrics_sink: Any,
        metrics: Mapping[str, Any],
        *,
        audit: AuditTrail,
        max_retries: int,
        sleep_fn: Optional[Callable[[float], None]],
    ) -> None:
        if metrics_sink is None:
            return
        self._emit_with_retries(
            sink=metrics_sink,
            line=_canonical_json(metrics) + "\n",
            max_retries=max_retries,
            audit=audit,
            sleep_fn=sleep_fn,
            context={"artifact": "metrics"},
        )

    def _metrics_snapshot(
        self,
        *,
        config: DryrunConfig,
        status: SessionStatus,
        events: Sequence[Mapping[str, Any]],
        audit: AuditTrail,
        sink_retries: int,
    ) -> dict[str, Any]:
        return {
            "schema_version": "C2_DRYRUN_METRICS_V1",
            "run_id": config.run_id,
            "strategy_id": config.strategy_id,
            "seed": config.seed,
            "status": status.value,
            "events_emitted": len(events),
            "audit_events": len(audit.events),
            "sink_retries": sink_retries,
        }

    def _count_sink_retries(self, audit: AuditTrail) -> int:
        return sum(1 for ev in audit.events if ev.code == "C2_SINK_WRITE_RETRY")
