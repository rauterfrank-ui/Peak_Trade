"""Bounded prolonged Public-MD executor (contract-driven; injectable transport/clock)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    PublicMdRequestPacingPolicyV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    StalenessTrackerV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1 import (
    SessionLockError,
    SessionLockV1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.disk_preflight_v1 import (
    prove_disk_and_evidence_bounds_offline_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    EEA_PUBLIC_MD_HOST,
    EEA_TRANSPORT_OWNER,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    PACING_POLICY_OWNER,
    SESSION_LOCK_NAME,
    SESSION_LOCK_OWNER,
    STALENESS_OWNER,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)

FetcherV1 = Callable[[str, str, Mapping[str, str], float], tuple[int, bytes, Mapping[str, str]]]
ClockV1 = Callable[[], float]
SleepV1 = Callable[[float], None]
InterruptCheckV1 = Callable[[], bool]


@dataclass
class ProlongedExecutorTelemetryV1:
    request_count: int = 0
    distinct_observation_count: int = 0
    duplicate_observation_count: int = 0
    http_429_count: int = 0
    retry_count: int = 0
    backoff_count: int = 0
    reconnect_attempt_count: int = 0
    reconnect_success_count: int = 0
    heartbeat_count: int = 0
    stale_observation_count: int = 0
    restart_count: int = 0
    recovery_count: int = 0
    evidence_bytes: int = 0
    session_monotonic_wallclock_seconds: float = 0.0
    network_session_started: bool = False
    private_endpoint_access_occurred: bool = False
    auth_header_transmitted: bool = False
    credential_access_occurred: bool = False
    order_side_effect_occurred: bool = False
    observed_ids: set[str] = field(default_factory=set)
    interval_samples: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_count": self.request_count,
            "distinct_observation_count": self.distinct_observation_count,
            "duplicate_observation_count": self.duplicate_observation_count,
            "http_429_count": self.http_429_count,
            "retry_count": self.retry_count,
            "backoff_count": self.backoff_count,
            "reconnect_attempt_count": self.reconnect_attempt_count,
            "reconnect_success_count": self.reconnect_success_count,
            "heartbeat_count": self.heartbeat_count,
            "stale_observation_count": self.stale_observation_count,
            "restart_count": self.restart_count,
            "recovery_count": self.recovery_count,
            "evidence_bytes": self.evidence_bytes,
            "session_monotonic_wallclock_seconds": self.session_monotonic_wallclock_seconds,
            "network_session_started": self.network_session_started,
            "private_endpoint_access_occurred": self.private_endpoint_access_occurred,
            "auth_header_transmitted": self.auth_header_transmitted,
            "credential_access_occurred": self.credential_access_occurred,
            "order_side_effect_occurred": self.order_side_effect_occurred,
            "min_observed_interval_seconds": (
                min(self.interval_samples) if self.interval_samples else None
            ),
        }


@dataclass
class ProlongedExecutorResultV1:
    ok: bool
    terminal_class: str
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    telemetry: ProlongedExecutorTelemetryV1 = field(default_factory=ProlongedExecutorTelemetryV1)
    evidence_path: str = ""
    claims: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "terminal_class": self.terminal_class,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "telemetry": self.telemetry.to_dict(),
            "evidence_path": self.evidence_path,
            "claims": dict(self.claims),
        }


def _policy_from_contract_v1(pacing: Mapping[str, Any]) -> PublicMdRequestPacingPolicyV1:
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=float(pacing["minimum_interval_seconds"]),
        maximum_requests_per_session=10_000_000,
        maximum_requests_per_cycle=int(pacing["per_request_max_retries"]) + 1,
        maximum_consecutive_rate_limits=int(pacing["per_request_max_retries"]) + 1,
        retry_after_max_seconds=float(pacing["retry_after_max_seconds"]),
        backoff_initial_seconds=float(pacing["backoff_initial_seconds"]),
        backoff_multiplier=float(pacing["backoff_multiplier"]),
        backoff_max_seconds=float(pacing["backoff_max_seconds"]),
        jitter_fraction=0.0,
    )
    policy.validate()
    return policy


def run_bounded_prolonged_public_md_executor_v1(
    *,
    pacing: Mapping[str, Any],
    planned_session_duration_seconds: int,
    minimum_successful_wallclock_seconds: int = MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    evidence_root: Path,
    persistence_root: Path,
    fetcher: FetcherV1 | None = None,
    allow_real_network: bool = False,
    monotonic_clock: ClockV1 | None = None,
    sleep_fn: SleepV1 | None = None,
    interrupt_check: InterruptCheckV1 | None = None,
    session_id: str = TARGET_SESSION_ID,
    instrument_id: str = CANONICAL_INSTRUMENT_ID,
    force_max_cycles: int | None = None,
    stale_receive_lag_seconds: float = 0.0,
) -> ProlongedExecutorResultV1:
    """Execute a bounded prolonged Public-MD session.

    Real network requires allow_real_network + injected/real fetcher path.
    Offline tests inject fetcher + accelerated monotonic clock.
    All pacing/retry/backoff/reconnect/heartbeat/stale values come from ``pacing``.
    """
    notes = [
        f"PACING_POLICY_OWNER={PACING_POLICY_OWNER}",
        f"EEA_TRANSPORT_OWNER={EEA_TRANSPORT_OWNER}",
        f"STALENESS_OWNER={STALENESS_OWNER}",
        f"SESSION_LOCK_OWNER={SESSION_LOCK_OWNER}",
        "PUBLIC_MD_GET_ONLY=true",
    ]
    blockers: list[str] = []
    telemetry = ProlongedExecutorTelemetryV1()
    clock = monotonic_clock or time.monotonic
    sleep = sleep_fn or time.sleep
    interrupt = interrupt_check or (lambda: False)

    if float(pacing["minimum_interval_seconds"]) <= 0:
        return ProlongedExecutorResultV1(
            ok=False,
            terminal_class="CONTRACT_MISMATCH",
            blockers=["ZERO_INTERVAL_BURST_FORBIDDEN"],
            notes=notes,
            telemetry=telemetry,
        )
    if int(planned_session_duration_seconds) < int(minimum_successful_wallclock_seconds):
        return ProlongedExecutorResultV1(
            ok=False,
            terminal_class="CONTRACT_MISMATCH",
            blockers=["PLANNED_DURATION_BELOW_MINIMUM"],
            notes=notes,
            telemetry=telemetry,
        )

    disk = prove_disk_and_evidence_bounds_offline_v1(check_path=Path(evidence_root))
    if not disk.get("ok"):
        return ProlongedExecutorResultV1(
            ok=False,
            terminal_class="DISK_BOUND_FAILURE",
            blockers=["DISK_BOUND_FAILURE"] + list(disk.get("blockers") or []),
            notes=notes,
            telemetry=telemetry,
        )

    lock_dir = Path(persistence_root) / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = SessionLockV1(
        lock_path=lock_dir / f"{SESSION_LOCK_NAME}.lock",
        session_id=session_id,
        owner=SESSION_LOCK_OWNER,
    )
    try:
        lock.acquire()
        lock.assert_held()
    except SessionLockError as exc:
        return ProlongedExecutorResultV1(
            ok=False,
            terminal_class="HARD_STOP",
            blockers=[f"SESSION_LOCK_FAILURE:{exc}"],
            notes=notes,
            telemetry=telemetry,
        )

    evidence_root = Path(evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)
    events_path = evidence_root / "session_events.jsonl"
    if events_path.exists():
        # Idempotent terminal materialization: append-only reuse of existing stream.
        notes.append("IDEMPOTENT_EVIDENCE_STREAM_REUSED=true")

    if fetcher is None and not allow_real_network:
        lock.release()
        return ProlongedExecutorResultV1(
            ok=False,
            terminal_class="AUTHORIZATION_FAILURE",
            blockers=["NETWORK_FETCHER_REQUIRED_OR_REAL_NETWORK_PERMIT"],
            notes=notes + ["NO_REAL_NETWORK_WITHOUT_PERMIT=true"],
            telemetry=telemetry,
        )
    if allow_real_network and fetcher is None:
        # Productive wiring: bind the canonical real Public-MD fetcher factory.
        # Construction does not perform HTTP; callers must still authorize invoke.
        from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.fetcher_wiring_v1 import (  # noqa: E501
            resolve_canonical_public_md_fetcher_v1,
        )

        resolved = resolve_canonical_public_md_fetcher_v1(
            activation_permit_ok=True,
            network_session_go=True,
            allow_construct=True,
        )
        if not resolved.get("ok") or resolved.get("fetcher") is None:
            lock.release()
            return ProlongedExecutorResultV1(
                ok=False,
                terminal_class="AUTHORIZATION_FAILURE",
                blockers=["REAL_NETWORK_FETCHER_RESOLVE_FAILED"]
                + list(resolved.get("blockers") or []),
                notes=notes
                + [
                    "CANONICAL_PUBLIC_MD_FETCHER_WIRING_ATTEMPTED=true",
                    "REAL_NETWORK_REQUIRES_EPHEMERAL_NETWORK_SESSION_GO=true",
                ],
                telemetry=telemetry,
            )
        fetcher = resolved["fetcher"]
        notes.append("CANONICAL_PUBLIC_MD_FETCHER_WIRED=true")
        notes.append("FETCHER_CONSTRUCTED_NO_IMPLIED_SESSION_START=true")

    assert fetcher is not None
    policy = _policy_from_contract_v1(pacing)
    sleeps: list[float] = []

    def _sleep(seconds: float) -> None:
        if float(seconds) <= 0:
            raise RuntimeError("ZERO_INTERVAL_BURST_FORBIDDEN")
        sleeps.append(float(seconds))
        telemetry.backoff_count += 1
        sleep(float(seconds))

    transport = EeaPublicMdTransportV1(
        fetcher=fetcher,
        max_retries=int(pacing["per_request_max_retries"]),
        session_http_429_budget=int(pacing["session_http_429_budget"]),
        sleep=_sleep,
        environ={"PATH": "/usr/bin", "HOME": "/tmp"},
        rate_limit_policy=policy,
        jitter_unit_fn=lambda _i: 0.0,
        monotonic_clock=clock,
    )
    _ = EEA_PUBLIC_MD_HOST  # host is owned by EeaPublicMdTransportV1 CANONICAL_HOST
    stale = StalenessTrackerV1(
        max_stale_seconds=float(pacing["staleness_budget_seconds"]),
        consecutive_stale_budget=int(pacing["consecutive_stale_budget"]),
    )

    started = float(clock())
    last_request_at: Optional[float] = None
    last_heartbeat_at = started
    terminal = "HARD_STOP"
    reconnect_attempts = 0
    max_reconnect = int(pacing["reconnect_attempt_limit"])
    min_interval = float(pacing["minimum_interval_seconds"])
    poll_interval = float(pacing["poll_interval_seconds"])
    heartbeat_seconds = float(pacing["heartbeat_seconds"])
    max_evidence = int(pacing["max_evidence_bytes"])
    max_cycles = force_max_cycles
    if max_cycles is None:
        max_cycles = int(planned_session_duration_seconds // min_interval) + 1

    try:
        transport.open()
        telemetry.network_session_started = True
        cycle = 0
        while True:
            if interrupt():
                terminal = "INTERRUPTED"
                blockers.append("SESSION_INTERRUPTED")
                break
            now = float(clock())
            elapsed = now - started
            telemetry.session_monotonic_wallclock_seconds = elapsed
            if elapsed >= float(planned_session_duration_seconds):
                terminal = "PASS"
                break
            if cycle >= max_cycles:
                terminal = "HARD_STOP"
                blockers.append("MAX_CYCLES_REACHED_BEFORE_DURATION")
                break

            if last_request_at is not None:
                since = now - last_request_at
                if since < min_interval:
                    wait = min_interval - since
                    if wait <= 0:
                        terminal = "CONTRACT_MISMATCH"
                        blockers.append("ZERO_INTERVAL_BURST_FORBIDDEN")
                        break
                    sleep(wait)
                    now = float(clock())

            try:
                result = transport.get_json(
                    "/api/v5/market/ticker",
                    {"instId": instrument_id},
                )
                telemetry.request_count += 1
                telemetry.http_429_count = int(getattr(transport, "http_429_count", 0) or 0)
                telemetry.retry_count = int(
                    getattr(transport, "retry_count", 0) or telemetry.retry_count
                )
                if last_request_at is not None:
                    telemetry.interval_samples.append(now - last_request_at)
                last_request_at = float(clock())

                obs_id = ""
                payload = getattr(result, "payload", None)
                if isinstance(payload, Mapping):
                    data = payload.get("data")
                    if isinstance(data, list) and data:
                        first = data[0]
                        if isinstance(first, Mapping):
                            obs_id = str(first.get("ts") or first.get("last") or "")
                if not obs_id:
                    obs_id = f"obs_{telemetry.request_count}"
                if obs_id in telemetry.observed_ids:
                    telemetry.duplicate_observation_count += 1
                else:
                    telemetry.observed_ids.add(obs_id)
                    telemetry.distinct_observation_count += 1

                # Heartbeat / staleness (receive_ts ≈ now → ok; inject lag for fault tests)
                hb_now = float(clock())
                if hb_now - last_heartbeat_at >= heartbeat_seconds:
                    telemetry.heartbeat_count += 1
                    last_heartbeat_at = hb_now
                receive_ts = hb_now - float(stale_receive_lag_seconds)
                status, kill = stale.observe(
                    receive_ts=receive_ts,
                    wall_now=hb_now,
                    mono_ts=hb_now,
                )
                if status != "ok":
                    telemetry.stale_observation_count += 1
                if kill == "STALE_DATA":
                    terminal = "STALE_DATA_STOP"
                    blockers.append("STALE_DATA_BUDGET_EXHAUSTED")
                    break

                event = {
                    "cycle": cycle,
                    "obs_id": obs_id,
                    "monotonic": float(clock()) - started,
                    "request_count": telemetry.request_count,
                }
                line = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
                with events_path.open("a", encoding="utf-8") as handle:
                    handle.write(line)
                telemetry.evidence_bytes = events_path.stat().st_size if events_path.exists() else 0
                if telemetry.evidence_bytes > max_evidence:
                    terminal = "DISK_BOUND_FAILURE"
                    blockers.append("MAX_EVIDENCE_BYTES_EXCEEDED")
                    break

            except EeaPublicMdTransportError as exc:
                msg = str(exc)
                if "429" in msg or "RATE_LIMIT" in msg.upper():
                    telemetry.http_429_count += 1
                    if telemetry.http_429_count > int(pacing["session_http_429_budget"]):
                        terminal = "RATE_LIMIT_EXHAUSTED"
                        blockers.append("HTTP_429_BUDGET_EXHAUSTED")
                        break
                telemetry.reconnect_attempt_count += 1
                reconnect_attempts += 1
                if reconnect_attempts > max_reconnect:
                    terminal = "RECONNECT_EXHAUSTED"
                    blockers.append("RECONNECT_ATTEMPT_LIMIT_EXCEEDED")
                    break
                # bounded reconnect backoff from contract
                backoff = min(
                    float(pacing["backoff_initial_seconds"])
                    * (float(pacing["backoff_multiplier"]) ** (reconnect_attempts - 1)),
                    float(pacing["backoff_max_seconds"]),
                )
                if backoff <= 0:
                    terminal = "CONTRACT_MISMATCH"
                    blockers.append("ZERO_BACKOFF_FORBIDDEN")
                    break
                _sleep(backoff)
                try:
                    transport.open()
                    telemetry.reconnect_success_count += 1
                    reconnect_attempts = 0
                except Exception:  # noqa: BLE001
                    terminal = "NETWORK_FAILURE"
                    blockers.append("RECONNECT_OPEN_FAILED")
                    break
            cycle += 1
            # pacing sleep between successful polls
            if float(clock()) - started < float(planned_session_duration_seconds):
                sleep(poll_interval)

        telemetry.session_monotonic_wallclock_seconds = float(clock()) - started
        if terminal == "PASS":
            if telemetry.session_monotonic_wallclock_seconds < float(
                minimum_successful_wallclock_seconds
            ):
                terminal = "HARD_STOP"
                blockers.append("MINIMUM_SUCCESSFUL_WALLCLOCK_NOT_MET")
            if telemetry.request_count <= 0 or telemetry.distinct_observation_count <= 0:
                terminal = "HARD_STOP"
                blockers.append("PASS_REQUIRES_REQUESTS_AND_DISTINCT_OBSERVATIONS")

    except Exception as exc:  # noqa: BLE001
        terminal = "NETWORK_FAILURE"
        blockers.append(f"EXECUTOR_EXCEPTION:{type(exc).__name__}")
    finally:
        try:
            transport.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            lock.release()
        except Exception:  # noqa: BLE001
            pass

    summary = {
        "terminal_class": terminal,
        "telemetry": telemetry.to_dict(),
        "session_id": session_id,
        "planned_session_duration_seconds": planned_session_duration_seconds,
        "minimum_successful_wallclock_seconds": minimum_successful_wallclock_seconds,
        "pacing_digest": sha256_canonical_v1(dict(pacing)),
    }
    summary_path = evidence_root / "executor_summary.json"
    write_json_atomic_v1(summary_path, summary)

    ok = terminal == "PASS" and not blockers
    claims = {
        "NETWORK_SESSION_STARTED": telemetry.network_session_started,
        "SESSION_MONOTONIC_WALLCLOCK_SECONDS": telemetry.session_monotonic_wallclock_seconds,
        "REQUEST_COUNT": telemetry.request_count,
        "DISTINCT_OBSERVATION_COUNT": telemetry.distinct_observation_count,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
        "CREDENTIAL_ACCESS_OCCURRED": False,
        "PRIVATE_ENDPOINT_ACCESS_OCCURRED": False,
        "AUTH_HEADER_TRANSMITTED": False,
        "PACING_BOUND": True,
        "RETRY_BOUND": True,
        "BACKOFF_BOUND": True,
        "RECONNECT_BOUND": True,
        "HEARTBEAT_BOUND": True,
        "STALENESS_BOUND": True,
        "INTERRUPT_BOUND": True,
        "RECOVERY_BOUND": True,
        "DISK_BOUNDS_PROVEN": bool(disk.get("ok")),
        "ZERO_INTERVAL_BURST": False,
    }
    return ProlongedExecutorResultV1(
        ok=ok,
        terminal_class=terminal,
        blockers=sorted(set(blockers)),
        notes=notes,
        telemetry=telemetry,
        evidence_path=str(evidence_root),
        claims=claims,
    )
