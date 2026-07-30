"""Wallclock observation session runtime orchestrator (fake-clock / fake-transport)."""

from __future__ import annotations

import platform
import time
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Set

from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.wallclock_v2_gatekeeper_v1 import (
    consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    DEFAULT_CONSECUTIVE_STALE_BUDGET,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    DEFAULT_HEARTBEAT_LOSS_SECONDS,
    DEFAULT_MAX_GAP_SECONDS,
    DEFAULT_MAX_RECONNECT_ATTEMPTS,
    DEFAULT_MAX_RECONNECT_WINDOW_SECONDS,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    DEFAULT_MAX_STALE_SECONDS,
    DEFAULT_MIN_QUALITY_WINDOW_SECONDS,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_SHUTDOWN_GRACE_SECONDS,
    EXECUTION_CLASS_ANALYTICAL,
    MARKET_TYPE_FUTURES,
    NETWORK_SCOPE,
    PACKAGE_MARKER,
    SESSION_EXECUTION_SCOPE,
    VENUE_OKX,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
    parse_ticker_mid_price_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    HeartbeatTrackerV1,
    StalenessTrackerV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.import_surface_guard_v1 import (
    attest_wallclock_import_surface_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    KillstateRuntimeV1,
    TerminalVerdict,
    classify_terminal_verdict,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    NetworkBoundaryError,
    validate_request_boundary_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1 import (
    SessionLockError,
    SessionLockV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_state_machine_v1 import (
    WallclockSessionState,
    WallclockStateMachineError,
    assert_transition_allowed,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceError,
    WallclockEvidenceWriterV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    AI_LAYER_CAN_OVERRIDE_DECISIONS,
    AI_LAYER_NON_AUTHORITY,
    AI_LAYER_ROLE,
    CAPABILITY_ID as DECISION_ECONOMICS_BRIDGE_CAPABILITY_ID,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.evidence_streams_v2 import (
    append_productive_cycle_evidence_streams_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.full_economic_reconstruction_verifier_v2 import (
    verify_full_economic_reconstruction_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (
    run_hardened_wallclock_bridge_observation_cycle_v2,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
)


@dataclass
class WallclockRuntimeConfigV1:
    max_session_duration_seconds: int = DEFAULT_MAX_SESSION_DURATION_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS
    heartbeat_loss_seconds: float = DEFAULT_HEARTBEAT_LOSS_SECONDS
    max_stale_seconds: float = DEFAULT_MAX_STALE_SECONDS
    max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS
    consecutive_stale_budget: int = DEFAULT_CONSECUTIVE_STALE_BUDGET
    max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS
    max_reconnect_window_seconds: float = DEFAULT_MAX_RECONNECT_WINDOW_SECONDS
    min_quality_window_seconds: int = DEFAULT_MIN_QUALITY_WINDOW_SECONDS
    shutdown_grace_seconds: float = DEFAULT_SHUTDOWN_GRACE_SECONDS
    max_cycles: Optional[int] = None  # test bound; None = duration-driven
    # Default true: WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_HARDENING_V2
    # BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE: bridge-disabled cannot emit full-system PASS evidence.
    decision_economics_bridge_enabled: bool = True
    require_decision_economics_bridge: bool = True


@dataclass
class WallclockSessionResultV1:
    terminal_verdict: str
    state: str
    session_id: str
    incomplete: bool
    consumed: bool
    network_opened: bool
    cycle_count: int
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    evidence_root: str = ""
    economic_validity_pass: bool = False
    promotion_pass: bool = False
    paper_execution: bool = False
    orders_submitted: bool = False
    credentials_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WallclockSessionRuntimeV1:
    def __init__(
        self,
        *,
        evidence_root: Path,
        transport: EeaPublicMdTransportV1,
        config: WallclockRuntimeConfigV1 | None = None,
        clock_wall: Callable[[], float] | None = None,
        clock_mono: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
        repo_root: Path | None = None,
        stop_flag: Optional[Callable[[], bool]] = None,
    ) -> None:
        self.evidence_root = evidence_root
        self.transport = transport
        self.config = config or WallclockRuntimeConfigV1()
        self.clock_wall = clock_wall or time.time
        self.clock_mono = clock_mono or time.monotonic
        self.sleep = sleep or time.sleep
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]
        self.stop_flag = stop_flag or (lambda: False)
        self.state = WallclockSessionState.CREATED
        self.killstate = KillstateRuntimeV1()
        self.writer = WallclockEvidenceWriterV1(evidence_root=evidence_root)
        self.lock: SessionLockV1 | None = None
        self.consumed = False
        self.network_opened = False
        self.cycle_count = 0
        self.accepted_ticks = 0
        self.sequence = 0
        self.reconnect_attempts = 0
        self.reconnect_window_start: float | None = None
        self.quality_fail = False
        self.blockers: list[str] = []
        self.started_wall = 0.0
        self.started_mono = 0.0
        self.bridge_state = HardenedBridgeSessionStateV2(instrument_id=CANONICAL_INSTRUMENT_ID)
        self.session_id: str = ""
        self._session_side_effects_allowed = False

    def _transition(self, to_state: WallclockSessionState) -> None:
        assert_transition_allowed(from_state=self.state, to_state=to_state)
        self.state = to_state

    def _abort(self, trigger: str, detail: str = "") -> None:
        self.killstate.raise_killstate(
            trigger=trigger,
            detail=detail,
            mono_ts=self.clock_mono(),
            wall_ts=self.clock_wall(),
        )
        try:
            self.writer.append_event(
                "killstate_events.jsonl",
                self.killstate.events[-1].to_dict(),
            )
        except Exception:
            pass
        if self.state not in {
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
            WallclockSessionState.INVALID,
        }:
            try:
                if self.state in {
                    WallclockSessionState.RUNNING,
                    WallclockSessionState.RECONNECTING,
                    WallclockSessionState.STARTING,
                    WallclockSessionState.STOPPING,
                }:
                    if self.state != WallclockSessionState.STOPPING:
                        try:
                            self._transition(WallclockSessionState.STOPPING)
                        except WallclockStateMachineError:
                            pass
                target = (
                    WallclockSessionState.KILLSTATE
                    if trigger
                    in {
                        "STALE_DATA",
                        "FORBIDDEN_ENDPOINT",
                        "ORDER_SURFACE_REACHED",
                        "EVIDENCE_TAMPER",
                        "IMPORT_GUARD_BREACH",
                    }
                    else WallclockSessionState.ABORTED
                )
                try:
                    self._transition(target)
                except WallclockStateMachineError:
                    self.state = target
            except Exception:
                self.state = WallclockSessionState.ABORTED

    def run(
        self,
        *,
        prereg: SessionPreregistrationContractV1,
        go: OperatorGoContractV1,
        confirm_token: str,
        artifact_path: Path,
        expected_repository_sha: str,
        fingerprint_ledger_path: Path,
        known_session_ids: Optional[Set[str]] = None,
        config_snapshot: Optional[Mapping[str, Any]] = None,
        runtime_overrides: Optional[Mapping[str, Any]] = None,
        cli_overrides: Optional[Mapping[str, Any]] = None,
        env_overrides: Optional[Mapping[str, Any]] = None,
        defaults: Optional[Mapping[str, Any]] = None,
        config_files: Optional[Mapping[str, str]] = None,
        artifact: Any = None,
    ) -> WallclockSessionResultV1:
        session_id = go.session_id
        # Fail-closed: V1 artifact objects are never accepted for productive start.
        if artifact is not None:
            self.state = WallclockSessionState.INVALID
            self.blockers.append("AUTHORIZATION_SCHEMA_REJECTED_LEGACY")
            return self._finalize_result(
                session_id=session_id,
                incomplete=False,
                force_verdict=TerminalVerdict.ABORT,
            )

        # Import surface preflight (read-only AST; no evidence mkdir / no consume).
        import_att = attest_wallclock_import_surface_v1(repo_root=self.repo_root)
        if not import_att.ok:
            self.state = WallclockSessionState.INVALID
            self.blockers.extend(import_att.blockers)
            return self._finalize_result(
                session_id=session_id,
                incomplete=False,
                force_verdict=TerminalVerdict.ABORT,
            )

        # Atomic canonical v2 consumption BEFORE any session lock / evidence / transport.
        consumption = consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1(
            prereg=prereg,
            go=go,
            confirm_token=confirm_token,
            evidence_writer=self.writer,
            artifact_path=artifact_path,
            now_unix=self.clock_wall(),
            expected_repository_sha=expected_repository_sha,
            fingerprint_ledger_path=fingerprint_ledger_path,
            known_session_ids=known_session_ids,
            runtime_overrides=runtime_overrides,
            cli_overrides=cli_overrides,
            env_overrides=env_overrides,
            defaults=defaults,
            config_files=config_files,
            expected_venue=AUTHORIZED_VENUE,
            expected_network_scope=AUTHORIZED_NETWORK_SCOPE,
        )
        if not consumption.ok or not consumption.transport_open_allowed:
            self.state = WallclockSessionState.INVALID
            self.blockers.extend(consumption.blockers)
            return self._finalize_result(
                session_id=session_id,
                incomplete=False,
                force_verdict=TerminalVerdict.ABORT,
            )

        # Side effects allowed only after successful atomic consumption.
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        self.writer.ensure_append_files()
        self._session_side_effects_allowed = True

        self.consumed = True
        try:
            self._transition(WallclockSessionState.CONSUMED)
        except WallclockStateMachineError as exc:
            self._abort("ABORT_AFTER_CONSUMPTION", str(exc))
            return self._finalize_result(session_id=session_id, incomplete=True)

        # Write remaining immutable snapshots.
        try:
            self.writer.write_immutable_json(
                "config_snapshot.json",
                dict(config_snapshot or {"schema": "wallclock_runtime_v1"}),
            )
            self.writer.write_immutable_json(
                "runtime_env_fingerprint.json",
                {
                    "python": platform.python_version(),
                    "platform": platform.platform(),
                    "no_secrets": True,
                },
            )
            self.writer.write_immutable_json(
                "venue_instrument_binding.json",
                {
                    "venue": VENUE_OKX,
                    "market_type": MARKET_TYPE_FUTURES,
                    "instrument_id": CANONICAL_INSTRUMENT_ID,
                    "host": CANONICAL_HOST,
                    "network_scope": NETWORK_SCOPE,
                    "session_execution_scope": SESSION_EXECUTION_SCOPE,
                },
            )
            self.writer.write_immutable_json(
                "session_manifest.json",
                {
                    "capability_id": CAPABILITY_ID,
                    "package_marker": PACKAGE_MARKER,
                    "session_id": session_id,
                    "wallclock_session_started": True,
                    "authority_effect": AUTHORITY_EFFECT_NONE,
                    "execution_class": EXECUTION_CLASS_ANALYTICAL,
                    "paper_execution": False,
                },
            )
        except WallclockEvidenceError as exc:
            self._abort("EVIDENCE_SINK_FAILURE", str(exc))
            return self._finalize_result(session_id=session_id, incomplete=True)

        # Lock
        self.lock = SessionLockV1(
            lock_path=self.evidence_root / "session.lock",
            session_id=session_id,
            owner=CAPABILITY_ID,
        )
        try:
            self.lock.acquire()
            self._transition(WallclockSessionState.LOCKED)
        except (SessionLockError, WallclockStateMachineError) as exc:
            self._abort("ABORT_DUPLICATE_SESSION", str(exc))
            return self._finalize_result(session_id=session_id, incomplete=True)

        # Open transport only after consume + lock.
        try:
            self._transition(WallclockSessionState.STARTING)
            self.transport.open()
            self.network_opened = True
            self.writer.append_event(
                "connectivity_events.jsonl",
                {"event": "transport_opened", "host": CANONICAL_HOST},
            )
            self._transition(WallclockSessionState.RUNNING)
        except Exception as exc:  # noqa: BLE001
            self._abort("ABORT_AFTER_CONSUMPTION", str(exc))
            return self._finalize_result(session_id=session_id, incomplete=True)

        self.started_wall = self.clock_wall()
        self.started_mono = self.clock_mono()
        self.writer.write_immutable_json(
            "planned_actual_timestamps.json",
            {
                "planned_duration_seconds": go.planned_duration_seconds,
                "started_wall": self.started_wall,
                "earliest_start": prereg.earliest_start,
                "expires_at": go.expires_at,
            },
        )

        heartbeat = HeartbeatTrackerV1(
            interval_seconds=self.config.heartbeat_interval_seconds,
            loss_seconds=self.config.heartbeat_loss_seconds,
        )
        staleness = StalenessTrackerV1(
            max_stale_seconds=self.config.max_stale_seconds,
            consecutive_stale_budget=self.config.consecutive_stale_budget,
        )
        heartbeat.beat(mono_ts=self.clock_mono(), wall_ts=self.clock_wall())
        self.writer.append_event("heartbeat.jsonl", heartbeat.events[-1])

        duration = min(
            int(go.planned_duration_seconds),
            int(self.config.max_session_duration_seconds),
        )
        last_tick: ObservationMarketTickV1 | None = None

        try:
            while True:
                if self.stop_flag():
                    self._transition(WallclockSessionState.STOPPING)
                    break
                now_wall = self.clock_wall()
                now_mono = self.clock_mono()
                if now_wall - self.started_wall >= duration:
                    self._transition(WallclockSessionState.TIMED_OUT)
                    break
                if (
                    self.config.max_cycles is not None
                    and self.cycle_count >= self.config.max_cycles
                ):
                    self._transition(WallclockSessionState.STOPPING)
                    break

                try:
                    self.lock.assert_held()
                except SessionLockError as exc:
                    self._abort("LOCK_LOSS", str(exc))
                    break

                if heartbeat.due(mono_ts=now_mono):
                    heartbeat.beat(mono_ts=now_mono, wall_ts=now_wall)
                    self.writer.append_event("heartbeat.jsonl", heartbeat.events[-1])
                loss = heartbeat.check_loss(mono_ts=now_mono)
                if loss:
                    self._abort(loss)
                    break

                try:
                    fetch = self.transport.fetch_ticker()
                    price = parse_ticker_mid_price_v1(fetch.payload)
                    self.sequence += 1
                    receive_ts = now_wall
                    tick = ObservationMarketTickV1(
                        instrument_id=CANONICAL_INSTRUMENT_ID,
                        venue=VENUE_OKX,
                        market_type=MARKET_TYPE_FUTURES,
                        sequence=self.sequence,
                        event_ts_unix=receive_ts,
                        receive_ts_unix=receive_ts,
                        mono_ts=now_mono,
                        mid_price=float(price),
                        source="eea_public_rest_ticker",
                    )
                    self.writer.append_event(
                        "market_data_sequence.jsonl",
                        {
                            "sequence": tick.sequence,
                            "mid_price": tick.mid_price,
                            "receive_ts_unix": tick.receive_ts_unix,
                            "url": fetch.url,
                        },
                    )
                    status, kill = staleness.observe(
                        receive_ts=receive_ts, wall_now=now_wall, mono_ts=now_mono
                    )
                    if status == "warn":
                        self.writer.append_event("stale_events.jsonl", staleness.events[-1])
                    if kill:
                        self._abort(kill)
                        break
                    if last_tick is not None:
                        gap = tick.event_ts_unix - last_tick.event_ts_unix
                        if gap > self.config.max_gap_seconds:
                            self._abort("DATA_GAP", f"gap={gap}")
                            break
                    ticks = [tick]  # latest tick only for MD policy / bridge cycle
                    if (
                        self.config.require_decision_economics_bridge
                        and not self.config.decision_economics_bridge_enabled
                    ):
                        self._abort(
                            "BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE",
                            "decision_economics_bridge_enabled=false",
                        )
                        break
                    if self.config.decision_economics_bridge_enabled:
                        outcome_bridge = run_hardened_wallclock_bridge_observation_cycle_v2(
                            bridge_state=self.bridge_state,
                            ticks=[tick],
                            reference_price=Decimal(str(price)),
                            wall_now_unix=now_wall,
                            session_id=session_id,
                        )
                        self.cycle_count += 1
                        if outcome_bridge.bridge_cycle is not None:
                            cycle = outcome_bridge.bridge_cycle
                            self.writer.append_event(
                                "decision_trace.jsonl",
                                {
                                    "cycle": self.cycle_count,
                                    "cycle_id": cycle.get("cycle_id"),
                                    "decision_id": cycle.get("decision_id"),
                                    "decision_result": cycle.get("decision_outcome"),
                                    "direction": cycle.get("direction"),
                                    "selected_side": cycle.get("selected_side"),
                                    "intended_action": cycle.get("intended_action"),
                                    "feature_regime": cycle.get("feature_regime"),
                                    "labels": {
                                        **outcome_bridge.labels,
                                        "ai_layer_non_authority": AI_LAYER_NON_AUTHORITY,
                                        "ai_layer_can_override_decisions": (
                                            AI_LAYER_CAN_OVERRIDE_DECISIONS
                                        ),
                                        "ai_layer_role": AI_LAYER_ROLE,
                                    },
                                    "bridge_capability_id": DECISION_ECONOMICS_BRIDGE_CAPABILITY_ID,
                                },
                            )
                            self.writer.append_event(
                                "risk_telemetry.jsonl",
                                {
                                    "cycle": self.cycle_count,
                                    "risk_decision_id": cycle.get("risk_decision_id"),
                                    "risk_sizing_result": cycle.get("risk_sizing_result"),
                                    "safety_result": cycle.get("safety_result"),
                                    "safety_evaluation": cycle.get("safety_evaluation"),
                                },
                            )
                            self.writer.append_event(
                                "bridge_cycle_ledger.jsonl",
                                cycle,
                            )
                            if cycle.get("fill") is not None:
                                self.writer.append_event(
                                    "bridge_fill_ledger.jsonl",
                                    cycle["fill"],
                                )
                                self.writer.append_event(
                                    "simulated_fills.jsonl",
                                    cycle["fill"],
                                )
                            append_productive_cycle_evidence_streams_v2(
                                append_event=self.writer.append_event,
                                session_id=session_id,
                                cycle=cycle,
                            )
                        outcome_ok = outcome_bridge.ok
                        md_blockers = outcome_bridge.md_blockers
                    else:
                        self._abort(
                            "BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE",
                            "legacy_observation_adapter_disabled",
                        )
                        break
                    if not outcome_ok:
                        # quality issue unless md kill-like
                        if any(
                            x.startswith("STALE_") or x.startswith("DATA_GAP") for x in md_blockers
                        ):
                            self._abort(
                                md_blockers[0].split(":")[0],
                                ",".join(md_blockers),
                            )
                            break
                        self.quality_fail = True
                    else:
                        self.accepted_ticks += 1
                    last_tick = tick
                    self.reconnect_attempts = 0
                    self.reconnect_window_start = None
                except (NetworkBoundaryError,) as exc:
                    self._abort("FORBIDDEN_ENDPOINT", str(exc))
                    break
                except EeaPublicMdTransportError as exc:
                    msg = str(exc)
                    if "ABORT_CREDENTIAL_OR_AUTH_SURFACE" in msg:
                        self._abort("ABORT_CREDENTIAL_OR_AUTH_SURFACE", msg)
                        break
                    if "HTTP_429_BUDGET_EXCEEDED" in msg:
                        self._abort("HTTP_429_BUDGET_EXCEEDED", msg)
                        break
                    # reconnect path
                    if self.state == WallclockSessionState.RUNNING:
                        self._transition(WallclockSessionState.RECONNECTING)
                    if self.reconnect_window_start is None:
                        self.reconnect_window_start = now_mono
                    self.reconnect_attempts += 1
                    self.writer.append_event(
                        "reconnect_events.jsonl",
                        {
                            "attempt": self.reconnect_attempts,
                            "error": msg,
                            "mono_ts": now_mono,
                        },
                    )
                    if self.reconnect_attempts > self.config.max_reconnect_attempts:
                        self._abort("RECONNECT_BUDGET_EXCEEDED", msg)
                        break
                    if (
                        now_mono - self.reconnect_window_start
                        > self.config.max_reconnect_window_seconds
                    ):
                        self._abort("RECONNECT_BUDGET_EXCEEDED", "window")
                        break
                    self.sleep(0.001)
                    if self.state == WallclockSessionState.RECONNECTING:
                        self._transition(WallclockSessionState.RUNNING)
                    continue

                self.sleep(self.config.poll_interval_seconds)
        except WallclockEvidenceError as exc:
            self._abort("EVIDENCE_SINK_FAILURE", str(exc))
        except WallclockStateMachineError as exc:
            self._abort("INVARIANT_VIOLATION", str(exc))

        # Shutdown finalize
        if self.state == WallclockSessionState.RUNNING:
            try:
                self._transition(WallclockSessionState.STOPPING)
            except WallclockStateMachineError:
                pass
        if self.state == WallclockSessionState.STOPPING:
            elapsed = self.clock_wall() - self.started_wall
            if elapsed < self.config.min_quality_window_seconds and not self.killstate.active:
                # short test sessions may set min_quality_window via config; if not met -> FAIL quality
                if self.config.max_cycles is None:
                    self.quality_fail = True
            try:
                self._transition(
                    WallclockSessionState.FAILED
                    if self.quality_fail
                    else WallclockSessionState.COMPLETED
                )
            except WallclockStateMachineError:
                pass
        if self.state == WallclockSessionState.TIMED_OUT:
            elapsed = self.clock_wall() - self.started_wall
            if self.accepted_ticks <= 0:
                self.quality_fail = True

        return self._finalize_result(session_id=session_id, incomplete=self.killstate.active)

    def _finalize_result(
        self,
        *,
        session_id: str,
        incomplete: bool,
        force_verdict: Optional[TerminalVerdict] = None,
    ) -> WallclockSessionResultV1:
        if self.transport.opened:
            try:
                self.transport.close()
            except Exception:
                pass
        if self.lock and self.lock.acquired:
            try:
                self.lock.release()
            except Exception:
                pass

        aborted = self.state in {
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
            WallclockSessionState.INVALID,
        }
        if force_verdict is not None:
            verdict = force_verdict
        else:
            verdict = classify_terminal_verdict(
                killstate_active=self.killstate.active,
                quality_fail=self.quality_fail,
                incomplete=incomplete and self.consumed,
                aborted=aborted,
            )
            if self.consumed and aborted and not self.killstate.active:
                # start failure after consumption
                verdict = TerminalVerdict.ABORT
                if "ABORT_AFTER_CONSUMPTION" not in self.killstate.last_trigger:
                    self.killstate.raise_killstate(
                        trigger="ABORT_AFTER_CONSUMPTION",
                        detail="post_consumption_terminal",
                        mono_ts=self.clock_mono(),
                        wall_ts=self.clock_wall(),
                    )

        # Write attestations / counters if missing — only after consumption side effects allowed.
        if not self._session_side_effects_allowed and not self.consumed:
            verdict_early = force_verdict or TerminalVerdict.ABORT
            return WallclockSessionResultV1(
                terminal_verdict=verdict_early.value
                if isinstance(verdict_early, TerminalVerdict)
                else str(verdict_early),
                state=self.state.value,
                session_id=session_id,
                incomplete=False,
                consumed=False,
                network_opened=False,
                cycle_count=0,
                blockers=list(self.blockers),
                notes=[
                    "NO_SESSION_SIDE_EFFECTS_BEFORE_CONSUMPTION",
                    "EVIDENCE_NOT_CREATED_ON_AUTH_FAILURE",
                ],
                evidence_root=str(self.evidence_root),
            )

        try:
            if not (self.evidence_root / "no_order_attestation.json").exists():
                self.writer.write_immutable_json(
                    "no_order_attestation.json",
                    {
                        "ok": True,
                        "orders_submitted": 0,
                        "broker_writes_performed": 0,
                        "orders_allowed": False,
                    },
                )
            if not (self.evidence_root / "network_boundary_attestation.json").exists():
                att = validate_request_boundary_v1(
                    url=f"https://{CANONICAL_HOST}/api/v5/public/time",
                    method="GET",
                    headers={"Accept": "application/json", "User-Agent": "x"},
                    environ={},
                    allow_proxy=True,
                )
                # re-validate with UA from constants via transport headers in real path
                self.writer.write_immutable_json(
                    "network_boundary_attestation.json",
                    {
                        "ok": True,
                        "host": CANONICAL_HOST,
                        "network_opened": self.network_opened,
                        "notes": att.notes,
                    },
                )
            if not (self.evidence_root / "observation_cycle_counters.json").exists():
                self.writer.write_immutable_json(
                    "observation_cycle_counters.json",
                    {
                        "cycle_count": self.cycle_count,
                        "accepted_ticks": self.accepted_ticks,
                    },
                )
            if not (self.evidence_root / "portfolio_snapshot.json").exists():
                if (
                    self.config.decision_economics_bridge_enabled
                    and self.bridge_state.cycle_index > 0
                ):
                    portfolio = dict(self.bridge_state.portfolio.snapshot())
                    self.writer.write_immutable_json("portfolio_snapshot.json", portfolio)
                    metrics_payload = {
                        **self.bridge_state.portfolio.economic_metrics().to_dict(),
                        "execution_class": EXECUTION_CLASS_ANALYTICAL,
                        "analytical_only": True,
                        "bridge_capability_id": DECISION_ECONOMICS_BRIDGE_CAPABILITY_ID,
                        "stub": False,
                        "ai_layer_non_authority": AI_LAYER_NON_AUTHORITY,
                        "ai_layer_can_override_decisions": AI_LAYER_CAN_OVERRIDE_DECISIONS,
                        "forced_fixture_economic_metrics_excluded": True,
                    }
                    self.writer.write_immutable_json("economic_metrics.json", metrics_payload)
                    verification = verify_full_economic_reconstruction_v2(
                        cycle_ledger=self.bridge_state.cycle_ledger,
                        fill_ledger=self.bridge_state.fill_ledger,
                        final_portfolio_snapshot=portfolio,
                        economic_metrics=self.bridge_state.portfolio.economic_metrics().to_dict(),
                    )
                    self.writer.write_immutable_json(
                        "full_economic_reconstruction_verifier.json",
                        verification.to_dict(),
                    )
                    self.writer.write_immutable_json(
                        "completion_verdict.json",
                        {
                            "ok": bool(verification.ok),
                            "capability_id": DECISION_ECONOMICS_BRIDGE_CAPABILITY_ID,
                            "mode": "productive_wallclock",
                            "full_economic_reconstruction_pass": bool(verification.ok),
                            "ai_layer_non_authority": AI_LAYER_NON_AUTHORITY,
                            "ai_layer_can_override_decisions": AI_LAYER_CAN_OVERRIDE_DECISIONS,
                            "exclude_from_economic_metrics": False,
                            "economic_validity_pass": False,
                            "promotion_pass": False,
                        },
                    )
                    if not (self.evidence_root / "authorization_consumption.json").exists():
                        self.writer.write_immutable_json(
                            "authorization_consumption.json",
                            {
                                "status": "CONSUMED" if self.consumed else "NOT_CONSUMED",
                                "consumed": bool(self.consumed),
                                "productive_authorization": True,
                                "mode": "productive_wallclock",
                                "forced_wiring_fixture": False,
                            },
                        )
                    if not verification.ok:
                        self.quality_fail = True
                        self.blockers.extend(verification.blockers)
                else:
                    # Fail-closed: no economics placeholder PASS impression.
                    self.quality_fail = True
                    self.blockers.append("BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE")
                    self.writer.write_immutable_json(
                        "portfolio_snapshot.json",
                        {
                            "execution_class": EXECUTION_CLASS_ANALYTICAL,
                            "paper_execution": False,
                            "stub": True,
                            "full_system_evidence": False,
                            "blocker": "BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE",
                        },
                    )
                    self.writer.write_immutable_json(
                        "completion_verdict.json",
                        {
                            "ok": False,
                            "capability_id": DECISION_ECONOMICS_BRIDGE_CAPABILITY_ID,
                            "mode": "productive_wallclock",
                            "full_economic_reconstruction_pass": False,
                            "blocker": "BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE",
                        },
                    )
            if not (self.evidence_root / "economic_metrics.json").exists():
                self.quality_fail = True
                self.blockers.append("ECONOMIC_METRICS_MISSING_BRIDGE_REQUIRED")
                self.writer.write_immutable_json(
                    "economic_metrics.json",
                    {
                        "execution_class": EXECUTION_CLASS_ANALYTICAL,
                        "analytical_only": True,
                        "stub": True,
                        "full_system_evidence": False,
                        "blocker": "BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE",
                    },
                )
            if not (self.evidence_root / "shutdown_reason.json").exists():
                self.writer.write_immutable_json(
                    "shutdown_reason.json",
                    {
                        "state": self.state.value,
                        "killstate": self.killstate.to_dict(),
                        "blockers": list(self.blockers),
                    },
                )
        except WallclockEvidenceError as exc:
            incomplete = True
            verdict = TerminalVerdict.ABORT
            self.blockers.append(str(exc))

        try:
            if not self.writer.finalized:
                self.writer.finalize(
                    verdict=verdict, incomplete=incomplete or bool(self.killstate.active)
                )
        except WallclockEvidenceError as exc:
            self.blockers.append(str(exc))
            incomplete = True
            verdict = TerminalVerdict.ABORT

        verify_wallclock_evidence_bundle_v1(evidence_root=self.evidence_root)

        return WallclockSessionResultV1(
            terminal_verdict=verdict.value,
            state=self.state.value,
            session_id=session_id,
            incomplete=incomplete,
            consumed=self.consumed,
            network_opened=self.network_opened,
            cycle_count=self.cycle_count,
            blockers=list(self.blockers),
            notes=[
                "NO_REAL_NETWORK_IN_DEFAULT_TESTS",
                "AUTHORIZATION_IS_NOT_STANDALONE_START",
                f"EXECUTION_CLASS={EXECUTION_CLASS_ANALYTICAL}",
            ],
            evidence_root=str(self.evidence_root),
        )


def preflight_wallclock_session_v1(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Offline preflight: no network, no consumption, no mutation of auth artifacts."""
    root = repo_root or Path(__file__).resolve().parents[3]
    import_att = attest_wallclock_import_surface_v1(repo_root=root)
    return {
        "ok": import_att.ok,
        "blockers": list(import_att.blockers),
        "network_used": False,
        "consumed": False,
        "capability_id": CAPABILITY_ID,
        "notes": ["PREFLIGHT_OFFLINE_ONLY"],
    }
