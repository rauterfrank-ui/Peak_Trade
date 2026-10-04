"""Bounded operational Run-001 loop (authorized only; fail-closed)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.bounded_limits_v1 import (
    BoundedRunCountersV1,
    check_operational_bounds_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.fixpoint_self_check_v1 import (
    evaluate_fixpoint_self_check_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (
    REAL_NETWORK_ENV,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.observation_tick_source_v1 import (
    ObservationTickSourceV1,
    PublicEeaObservationTickSourceV1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.owner_go_validator_v1 import (
    OwnerGoValidationResultV1,
    validate_owner_go_authorization_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.productive_cycle_step_v1 import (
    ProductiveCycleStepFnV1,
    default_productive_cycle_step_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import PaperShadowRunContractV1
from src.ops.paper_shadow_bounded_orchestrator_v1.run_evidence_v1 import RunEvidenceAccumulatorV1
from src.ops.paper_shadow_bounded_orchestrator_v1.run_state_machine_v1 import RunStateMachineV1
from src.ops.paper_shadow_bounded_orchestrator_v1.shadow_routing_v1 import (
    default_shadow_session_bundle_v1,
    route_pre_external_to_shadow_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
)


@dataclass
class OperationalRunResultV1:
    ok: bool
    run_started: bool
    stop_reason: str
    counters: BoundedRunCountersV1
    evidence: dict[str, Any]
    blockers: tuple[str, ...]
    state_machine: dict[str, Any]
    owner_go_consumed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "RUN_STARTED": self.run_started,
            "STOP_REASON": self.stop_reason,
            "OWNER_GO_CONSUMED": self.owner_go_consumed,
            "counters": self.counters.to_dict(),
            "evidence": self.evidence,
            "blockers": list(self.blockers),
            "state_machine": self.state_machine,
            "SHADOW_AUTHORIZED": False,
            "SHADOW_RUNNING": False,
            "AUTO_RESTART": False,
        }


@dataclass
class OperationalRunHooksV1:
    tick_source: ObservationTickSourceV1 | None = None
    productive_step: ProductiveCycleStepFnV1 | None = None
    clock_mono: Callable[[], float] = field(default_factory=time.monotonic)
    clock_wall: Callable[[], float] = field(default_factory=time.time)
    sleep_fn: Callable[[float], None] = field(default_factory=lambda: time.sleep)
    poll_interval_seconds: float = 1.0
    stop_flag: Callable[[], bool] = field(default_factory=lambda: lambda: False)
    kill_switch: Callable[[], bool] = field(default_factory=lambda: lambda: False)
    allow_real_network: bool = False


def _extract_auth_tokens(authorization_path: Path) -> tuple[str, str]:
    import json

    payload = json.loads(Path(authorization_path).read_text(encoding="utf-8"))
    obs = str(payload.get("OBSERVATION_TOKEN") or payload.get("observation_token") or "")
    act = str(payload.get("ACTIVATION_TOKEN") or payload.get("activation_token") or "")
    return obs, act


def _build_default_tick_source(
    *,
    allow_real_network: bool,
    repo_root: Path,
) -> ObservationTickSourceV1 | None:
    if not allow_real_network:
        return None
    if str(os.environ.get(REAL_NETWORK_ENV) or "0") != "1":
        return None
    _ = repo_root
    transport = EeaPublicMdTransportV1()
    return PublicEeaObservationTickSourceV1(transport=transport, venue_mapping=None)


def run_paper_shadow_bounded_operational_run_v1(
    *,
    contract: PaperShadowRunContractV1,
    repo_root: Path,
    authorization_path: Path,
    go_validation: OwnerGoValidationResultV1 | None = None,
    hooks: OperationalRunHooksV1 | None = None,
) -> OperationalRunResultV1:
    """Execute bounded operational loop. Never consumes Owner-GO artifacts on disk."""
    hooks = hooks or OperationalRunHooksV1()
    sm = RunStateMachineV1()
    blockers: list[str] = []

    sm.begin_preflight()
    fixpoint = evaluate_fixpoint_self_check_v1(
        repo_root=repo_root,
        expected_fixpoint_sha=contract.fixpoint_sha,
        expected_tree_sha=contract.fixpoint_tree,
        settings_digest=contract.settings_digest,
    )
    if not fixpoint.ok:
        sm.fail()
        return OperationalRunResultV1(
            ok=False,
            run_started=False,
            stop_reason="FIXPOINT_SELF_CHECK_FAILED",
            counters=BoundedRunCountersV1(),
            evidence={},
            blockers=tuple(fixpoint.blockers),
            state_machine=sm.to_dict(),
        )

    sm.complete_preflight_ready()

    if go_validation is None:
        obs_tok, act_tok = _extract_auth_tokens(authorization_path)
        go_validation = validate_owner_go_authorization_v1(
            contract=contract,
            authorization_path=authorization_path,
            observation_token=obs_tok or None,
            activation_token=act_tok or None,
        )
    if not go_validation.ok:
        sm.fail()
        return OperationalRunResultV1(
            ok=False,
            run_started=False,
            stop_reason="AUTHORIZATION_FAIL_CLOSED",
            counters=BoundedRunCountersV1(),
            evidence={},
            blockers=tuple(go_validation.blockers),
            state_machine=sm.to_dict(),
        )

    sm.authorize()

    allow_net = (
        hooks.allow_real_network
        or str(os.environ.get("PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK") or "0") == "1"
    )
    tick_source = hooks.tick_source
    public_source: PublicEeaObservationTickSourceV1 | None = None
    if tick_source is None:
        built = _build_default_tick_source(allow_real_network=allow_net, repo_root=repo_root)
        if built is None:
            sm.fail()
            return OperationalRunResultV1(
                ok=False,
                run_started=False,
                stop_reason="TICK_SOURCE_UNAVAILABLE",
                counters=BoundedRunCountersV1(),
                evidence={},
                blockers=("PUBLIC_MD_TICK_SOURCE_REQUIRES_REAL_NETWORK_ENV_OR_INJECTION",),
                state_machine=sm.to_dict(),
            )
        tick_source = built
        if isinstance(built, PublicEeaObservationTickSourceV1):
            public_source = built

    productive_step = hooks.productive_step or default_productive_cycle_step_v1
    session_id = f"paper-shadow-{contract.run_id}"
    bridge_state = HardenedBridgeSessionStateV2(instrument_id=CANONICAL_INSTRUMENT_ID)
    shadow_session, shadow_portfolio, shadow_ledger = default_shadow_session_bundle_v1(
        instrument_id="ETH-USD_UM_XPERP-TEST",
        state_root=None,
    )
    obs_tok, act_tok = _extract_auth_tokens(authorization_path)

    evidence = RunEvidenceAccumulatorV1(
        run_id=contract.run_id,
        fixpoint_sha=contract.fixpoint_sha,
        fixpoint_tree=contract.fixpoint_tree,
        settings_digest=contract.settings_digest,
        authorization_binding={
            "authorization_path": str(Path(authorization_path).resolve()),
            "OWNER_GO_CONSUMED": False,
        },
    )
    counters = BoundedRunCountersV1()
    stop_reason = ""
    sm.start_running()
    run_started = True
    start_mono = hooks.clock_mono()
    start_wall = hooks.clock_wall()
    evidence.start_wall_unix = start_wall
    productive_cycle_index = 0

    try:
        while True:
            if hooks.kill_switch():
                stop_reason = "KILL_SWITCH_FAIL_CLOSED"
                sm.begin_stopping()
                sm.abort()
                break
            if hooks.stop_flag():
                stop_reason = "EXTERNAL_STOP_FLAG"
                sm.begin_stopping()
                sm.complete()
                break

            drift = evaluate_fixpoint_self_check_v1(
                repo_root=repo_root,
                expected_fixpoint_sha=contract.fixpoint_sha,
                expected_tree_sha=contract.fixpoint_tree,
                settings_digest=contract.settings_digest,
            )
            if not drift.ok:
                stop_reason = "FIXPOINT_MISMATCH_FAIL_CLOSED"
                sm.begin_stopping()
                sm.abort()
                blockers.extend(drift.blockers)
                break

            elapsed = hooks.clock_mono() - start_mono
            counters.elapsed_seconds = elapsed
            bound = check_operational_bounds_v1(contract=contract, counters=counters)
            if bound.stop:
                stop_reason = bound.reason
                sm.begin_stopping()
                sm.complete()
                break

            fetch = tick_source.next_tick(
                wall_now_unix=hooks.clock_wall(),
                mono_now=hooks.clock_mono(),
                sequence=counters.observation_count + 1,
            )
            if fetch.fatal:
                stop_reason = fetch.reason or "OBSERVATION_FATAL"
                sm.begin_stopping()
                sm.abort()
                break
            if not fetch.ok or fetch.tick is None:
                hooks.sleep_fn(hooks.poll_interval_seconds)
                continue

            counters.observation_count += 1
            evidence.observation_count = counters.observation_count

            productive_cycle_index += 1
            step = productive_step(
                bridge_state,
                fetch.tick,
                fetch.reference_price,
                hooks.clock_wall(),
                session_id,
                productive_cycle_index,
            )
            if step.productive_cycle_ran:
                counters.cycle_count += 1
                evidence.cycle_count = counters.cycle_count
            evidence.record_productive_cycle(bridge_cycle=step.bridge_cycle)

            if step.fail_fatal:
                stop_reason = "PRODUCTIVE_CYCLE_FATAL"
                sm.begin_stopping()
                sm.abort()
                break

            if step.pre_external_event is not None:
                evidence.record_pre_external()
                route = route_pre_external_to_shadow_v1(
                    event=step.pre_external_event,
                    operator_go_token=act_tok,
                    operator_observation_go_token=obs_tok,
                    session=shadow_session,
                    portfolio=shadow_portfolio,
                    ledger=shadow_ledger,
                    max_open_positions=contract.max_simulated_open_position_count,
                    open_simulated_positions=counters.open_simulated_positions,
                )
                if route.ok:
                    counters.simulated_execution_count += 1
                    counters.open_simulated_positions = min(
                        counters.open_simulated_positions + 1,
                        contract.max_simulated_open_position_count,
                    )
                    evidence.simulated_execution_count = counters.simulated_execution_count
                    evidence.record_shadow(
                        sample=route.to_dict(),
                        reconcile_ok=bool(route.reconcile and route.reconcile.get("ok")),
                    )
                elif route.fail_reason == "MAX_SIMULATED_OPEN_POSITION_COUNT":
                    evidence.duplicate_prevented_count += 1
                elif route.event_substitution_count > 0:
                    stop_reason = "EVENT_SUBSTITUTION_FAIL_CLOSED"
                    sm.begin_stopping()
                    sm.abort()
                    break

            bound = check_operational_bounds_v1(contract=contract, counters=counters)
            if bound.stop:
                stop_reason = bound.reason
                sm.begin_stopping()
                sm.complete()
                break

            hooks.sleep_fn(hooks.poll_interval_seconds)
    finally:
        if public_source is not None:
            public_source.close()

    if not stop_reason and sm.state.value == "RUNNING":
        stop_reason = "LOOP_EXIT_UNEXPECTED"
        sm.begin_stopping()
        sm.abort()

    evidence_payload = evidence.finalize(
        stop_reason=stop_reason,
        elapsed=counters.elapsed_seconds,
        end_wall=hooks.clock_wall(),
    )
    ok = stop_reason in {
        "NORMAL_DURATION_COMPLETE",
        "MAX_OBSERVATION_BOUND",
        "MAX_CYCLE_BOUND",
        "MAX_SIMULATED_EXECUTION_BOUND",
        "EXTERNAL_STOP_FLAG",
    } or (run_started and stop_reason.startswith("KILL_SWITCH"))

    return OperationalRunResultV1(
        ok=ok,
        run_started=run_started,
        stop_reason=stop_reason,
        counters=counters,
        evidence=evidence_payload,
        blockers=tuple(blockers),
        state_machine=sm.to_dict(),
        owner_go_consumed=False,
    )
