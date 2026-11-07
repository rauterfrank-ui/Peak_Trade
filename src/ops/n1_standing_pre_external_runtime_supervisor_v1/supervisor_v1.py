"""Standing N=1 PRE_EXTERNAL runtime supervisor — orchestration only."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
    validate_bounded_continuous_run_owner_go_decision_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    ContinuousObservationSourceV1,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_STALL,
    DISPOSITION_CANCELLED,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    mint_continuous_run_id_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    PersistentNaturalEnterConvergenceError,
    run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
    PRETRADE_DECISION_ID_SUPERVISOR_TICK,
    SUPERVISOR_ZERO_ECONOMIC_AUTHORITY,
    TRANSPORT_SCOPE_OFFLINE_INJECT,
    TRANSPORT_SCOPE_SCOPED_READONLY_GET,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.errors_v1 import (
    StandingSupervisorError,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.trace_v1 import (
    StandingSupervisorTraceV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.wp02_insertion_v1 import (
    Wp02HookV1,
    Wp02InsertionContextV1,
    noop_wp02_hook_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_real_md_cap22_n1_chain_v1 import (
    run_public_runtime_ws_normalization_cycle_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    PublicRuntimeEconomicMdPublicSourceV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.unified_recovery_orchestration_v1 import (
    UnifiedRecoveryOrchestrationResultV1,
    execute_unified_recovery_orchestration_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.governance.current_continuous_run_runtime_binding_v1 import (
    PolicyGovernedContinuousRunResultV1,
)


from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_notice_v1 import (
    record_runtime_notice_v1,
)


def _record_supervisor_outcome_v1(run):
    @wraps(run)
    def observed(**kwargs):
        config = kwargs["config"]
        # An unsafe evidence path is not a safe place for a fault notice.
        # Validate root ownership before the wrapper can write any notice.
        budget_owner_root_for_config_v1(config)
        try:
            result = run(**kwargs)
        except Exception as exc:
            try:
                record_runtime_notice_v1(
                    evidence_root=config.evidence_root,
                    component="STANDING_N1_SUPERVISOR",
                    run_id="",
                    reason_code=getattr(exc, "reason_code", "SUPERVISOR_FAILURE"),
                    action="Inspect the failing owner, reconcile durable state and verify authorization before a new run. Do not clear safety locks.",
                    owner_action_required=True,
                    notification_kind="FAULT",
                    extra={
                        "exception_type": type(exc).__name__,
                        "automatic_restart_allowed": False,
                    },
                )
            except OSError:
                pass  # local notice writer logs failure; preserve original exception
            raise
        terminal = result.policy_result.orchestrator_result if result.policy_result else None
        record_runtime_notice_v1(
            evidence_root=config.evidence_root,
            component="STANDING_N1_SUPERVISOR",
            run_id=result.run_id,
            reason_code=terminal.reason_code if terminal else "SUPERVISOR_NO_RUNTIME_RESULT",
            action=terminal.next_required_owner_decision
            if terminal
            else "Inspect missing runtime result before a new authorized run.",
            owner_action_required=terminal is None or terminal.disposition != DISPOSITION_CANCELLED,
            extra={
                "disposition": result.trace.terminal_disposition,
                "ok": result.ok,
                "automatic_restart_allowed": False,
            },
        )
        return result

    return observed


@dataclass(frozen=True)
class StandingSupervisorConfigV1:
    public_store_root: Path
    private_store_root: Path
    lane_state_root: Path
    evidence_root: Path
    lock_root: Path | None = None
    cap24_productivity_root: Path | None = None
    expected_account_identity: str | None = None
    venue_native_id: str = "ETH-USDT-SWAP"
    canonical_instrument_id: str = "inst-eth-usdt-perp"
    kill_switch_state_path: str | None = None
    transport_scope: str = TRANSPORT_SCOPE_OFFLINE_INJECT
    require_pretrade_collection: bool = False
    simulate_restart_before_continuous: bool = False
    wp02_productive_default_enabled: bool = True
    wp02_universe_source_payload: Mapping[str, Any] | None = None
    wp02_universe_mark_price_payload: Mapping[str, Any] | None = None
    wp02_universe_source_event_time: str = "1700000000000"
    wp02_state_root: Path | None = None
    wp02_topology_state_root_base: Path | None = None


def budget_owner_root_for_config_v1(config: StandingSupervisorConfigV1) -> Path:
    """Resolve one private owner, disjoint from run/lane/public roots; no writes."""
    paths = {
        name: Path(getattr(config, name))
        for name in ("private_store_root", "evidence_root", "lane_state_root", "public_store_root")
    }
    if any(not p.is_absolute() for p in paths.values()):
        raise StandingSupervisorError("BUDGET_OWNER_ABSOLUTE_ROOTS_REQUIRED")
    root = (paths["private_store_root"] / "portfolio_budget_host_v1").resolve()
    for name in ("evidence_root", "lane_state_root", "public_store_root"):
        other = paths[name].resolve()
        if root == other or root.is_relative_to(other) or other.is_relative_to(root):
            raise StandingSupervisorError("BUDGET_OWNER_ROOT_OVERLAP", name)
    return root


@dataclass(frozen=True)
class StandingSupervisorRunResultV1:
    ok: bool
    run_id: str
    trace: StandingSupervisorTraceV1
    recovery: UnifiedRecoveryOrchestrationResultV1
    policy_result: PolicyGovernedContinuousRunResultV1 | None
    owner_go_consumed: bool
    authority_invariants_ok: bool


def assert_supervisor_authority_boundary_v1() -> None:
    proof = prove_hard_facts_authority_invariants_v1()
    if not proof.ok or not proof.authority_matrix.get("supervisor_zero_economic_authority"):
        raise StandingSupervisorError("SUPERVISOR_AUTHORITY_BOUNDARY_VIOLATION")
    if not SUPERVISOR_ZERO_ECONOMIC_AUTHORITY:
        raise StandingSupervisorError("SUPERVISOR_ZERO_ECONOMIC_AUTHORITY_FALSE")
    if POST_ALLOWED or EXTERNAL_EFFECT_AUTHORIZED or REAL_VENUE_POST_ALLOWED:
        raise StandingSupervisorError("EXTERNAL_EFFECT_PIN_VIOLATION")


def _run_unified_recovery_v1(
    *,
    config: StandingSupervisorConfigV1,
    public_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    private_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
) -> UnifiedRecoveryOrchestrationResultV1:
    return execute_unified_recovery_orchestration_v1(
        public_store_root=config.public_store_root,
        private_store_root=config.private_store_root,
        public_rest_fetch=public_rest_fetch,
        private_rest_fetch=private_rest_fetch,
        venue_native_id=config.venue_native_id,
        kill_switch_state_path=config.kill_switch_state_path,
        unresolved_venue_order=False,
    )


def _refresh_public_supply_v1(
    *,
    config: StandingSupervisorConfigV1,
    ws_messages: list[Mapping[str, Any]],
    public_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
) -> int:
    config.public_store_root.mkdir(parents=True, exist_ok=True)
    run_public_runtime_ws_normalization_cycle_v1(
        store_root=config.public_store_root,
        venue_native_id=config.venue_native_id,
        canonical_instrument_id=config.canonical_instrument_id,
        ws_messages=ws_messages,
        rest_fetch_json=public_rest_fetch,
    )
    adapter = PublicRuntimeEconomicMdPublicSourceV1(store_root=config.public_store_root)
    bundle = adapter.collect_instrument_raw_input_v1(venue_native_id=config.venue_native_id)
    return len(bundle.marks)


def _refresh_pretrade_truth_v1(
    *,
    bound: BoundInstrumentV1,
    transport: FullCoreFreshPretradeGetTransportV1 | None,
    require_collection: bool,
) -> str:
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=PRETRADE_DECISION_ID_SUPERVISOR_TICK,
        instrument_id=str(bound.instrument_id),
        td_mode="cross",
        transport=transport,
        require_collection=require_collection,
    )
    return str(evidence.pretrade_freshness_status)


@_record_supervisor_outcome_v1
def run_n1_standing_pre_external_supervisor_v1(
    *,
    config: StandingSupervisorConfigV1,
    origin_main_sha: str,
    bound: BoundInstrumentV1,
    authorization: CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    observation_source: ContinuousObservationSourceV1,
    g17_producers: Mapping[str, object],
    f1_m9_cycle_evaluator: Callable[[int], Any],
    repo_root: Path | None = None,
    public_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    private_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    public_ws_messages: list[Mapping[str, Any]] | None = None,
    pretrade_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    wp02_hook: Wp02HookV1 | None = None,
    time_fn: Callable[[], float] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    skip_owner_go_validation: bool = False,
    cancel_requested: Callable[[], bool] | None = None,
    post_close_startup_recovery: Any | None = None,
) -> StandingSupervisorRunResultV1:
    """Single standing supervisor session: recovery → supply → pretrade → continuous PRE_EXTERNAL run."""

    root = repo_root or Path(__file__).resolve().parents[3]
    assert_supervisor_authority_boundary_v1()

    if not skip_owner_go_validation:
        ok_go, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
            repo_root=root,
            baseline_origin_main_sha=origin_main_sha,
        )
        if not ok_go:
            raise StandingSupervisorError("OWNER_GO_VALIDATION_DENIED", ",".join(reasons))

    auth_proof = prove_hard_facts_authority_invariants_v1()
    if not auth_proof.ok:
        raise StandingSupervisorError("HARD_FACTS_AUTHORITY_INVARIANTS_FAIL")
    if (
        not isinstance(config.expected_account_identity, str)
        or not config.expected_account_identity
        or config.expected_account_identity != config.expected_account_identity.strip()
    ):
        raise StandingSupervisorError("BUDGET_OWNER_EXPECTED_ACCOUNT_REQUIRED")

    run_id = mint_continuous_run_id_v1(authorization)
    trace = StandingSupervisorTraceV1(
        run_id=run_id,
        tick_index=0,
        bound_instrument_id=str(bound.instrument_id),
        venue_native_id=config.venue_native_id,
    )

    if config.transport_scope == TRANSPORT_SCOPE_SCOPED_READONLY_GET:
        from datetime import datetime, timezone
        from .startup_binding_v1 import acquire_account_bound_n1_startup_v1

        if config.cap24_productivity_root is None or not config.expected_account_identity:
            raise StandingSupervisorError("N1_START_ACCOUNT_AND_SELECTION_ROOT_REQUIRED")
        if (
            config.venue_native_id != bound.venue_native_id
            or config.canonical_instrument_id != bound.instrument_id
        ):
            raise StandingSupervisorError("N1_START_CONFIG_INSTRUMENT_MISMATCH")
        startup = acquire_account_bound_n1_startup_v1(
            productivity_root=config.cap24_productivity_root,
            repository_sha=origin_main_sha,
            binding_epoch=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            expected_account_identity=config.expected_account_identity,
            session_id=run_id,
            private_rest_fetch=private_rest_fetch,
            expected_bound=bound,
        )
        bound = startup.handoff.bound_instrument
        trace.extra["startup_account_bound"] = True
        trace.extra["startup_selection_id"] = startup.handoff.selection_id

    recovery = _run_unified_recovery_v1(
        config=config,
        public_rest_fetch=public_rest_fetch,
        private_rest_fetch=private_rest_fetch,
    )
    if not recovery.ok:
        raise StandingSupervisorError(
            "UNIFIED_RECOVERY_FAIL_CLOSED",
            recovery.fail_closed_reason,
        )
    trace.observation_recovery_completed = True
    trace.recovery_completed = recovery.runtime_owner_recovery_complete
    trace.recovery_steps = list(recovery.steps_completed)
    trace.extra["recovery_evidence_scope"] = recovery.evidence_scope
    trace.extra["pending_runtime_recovery_steps"] = list(recovery.pending_runtime_steps)

    if config.simulate_restart_before_continuous:
        recovery_restart = _run_unified_recovery_v1(
            config=config,
            public_rest_fetch=public_rest_fetch,
            private_rest_fetch=private_rest_fetch,
        )
        if not recovery_restart.ok:
            raise StandingSupervisorError(
                "UNIFIED_RECOVERY_RESTART_FAIL_CLOSED",
                recovery_restart.fail_closed_reason,
            )
        trace.extra["recovery_restart_before_continuous"] = True

    owner_go_consumed = False
    policy_result: PolicyGovernedContinuousRunResultV1 | None = None
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1

    budget_host = PortfolioBudgetHostV1(
        root=budget_owner_root_for_config_v1(config),
        private_rest_fetch=private_rest_fetch,
        repository_sha=origin_main_sha,
        session_id=str(config.evidence_root.name),
        expected_account_identity=config.expected_account_identity,
        durable_mode="recover",
        reconciliation_transport=pretrade_transport,
        retry_interval_seconds=authorization.wait_interval_seconds,
        **({"retry_sleep": sleep_fn} if sleep_fn is not None else {}),
    )
    try:
        if post_close_startup_recovery is not None:
            from .startup_binding_v1 import recover_post_close_before_runtime_v1

            trace.extra["post_close_startup_recovery"] = recover_post_close_before_runtime_v1(
                post_close_startup_recovery,
                current_bound=bound,
                current_topology_root=config.lane_state_root,
                budget_host=budget_host,
            )
        ws_msgs = public_ws_messages if public_ws_messages is not None else []
        mark_count = _refresh_public_supply_v1(
            config=config,
            ws_messages=ws_msgs,
            public_rest_fetch=public_rest_fetch,
        )
        trace.public_supply_refreshed = True
        trace.public_marks_count = mark_count

        wp02_chain_error: type[Exception] | None = None
        if wp02_hook is not None:
            hook = wp02_hook
        elif config.wp02_productive_default_enabled:
            from src.ops.current_wp02_default_productive_universe_handoff_v1.errors_v1 import (
                Wp02ProductiveDefaultChainError,
            )
            from src.ops.current_wp02_default_productive_universe_handoff_v1.wp02_hook_v1 import (
                Wp02HookBindingV1,
                build_default_wp02_hook_v1,
            )

            wp02_chain_error = Wp02ProductiveDefaultChainError
            if (
                config.wp02_universe_source_payload is None
                or config.wp02_universe_mark_price_payload is None
            ):
                raise StandingSupervisorError("WP02_UNIVERSE_INJECT_REQUIRED")
            wp02_state = config.wp02_state_root or (config.lane_state_root / "wp02_runtime")
            topo_base = config.wp02_topology_state_root_base or (
                config.lane_state_root / "topology"
            )
            binding = Wp02HookBindingV1(
                wp02_state_root=wp02_state,
                topology_state_root_base=topo_base,
                repository_sha=origin_main_sha,
                universe_source_payload=config.wp02_universe_source_payload,
                universe_mark_price_payload=config.wp02_universe_mark_price_payload,
                source_event_time=config.wp02_universe_source_event_time,
            )
            hook = build_default_wp02_hook_v1(binding)
        else:
            hook = noop_wp02_hook_v1
        wp02_result_sink: dict[str, Any] = {}
        try:
            hook(
                Wp02InsertionContextV1(
                    public_store_root=config.public_store_root,
                    venue_native_id=config.venue_native_id,
                    canonical_instrument_id=config.canonical_instrument_id,
                    economic_md_mark_count=mark_count,
                    tick_index=trace.tick_index,
                    wp02_result_sink=wp02_result_sink,
                )
            )
        except Exception as exc:
            if wp02_chain_error is not None and isinstance(exc, wp02_chain_error):
                raise StandingSupervisorError(getattr(exc, "code", "WP02_FAIL"), str(exc)) from exc
            raise
        trace.wp02_hook_invoked = True
        chain_result = wp02_result_sink.get("chain_result")
        if chain_result is not None:
            trace.wp02_cap21_refresh_invoked = bool(chain_result.cap21_refresh_invoked)
            trace.wp02_hard_facts_handoff_invoked = bool(chain_result.hard_facts_handoff_invoked)
            trace.wp02_membership_persisted = bool(chain_result.membership_persisted)
            trace.extra["wp02_ranking_snapshot_id"] = str(
                (chain_result.ranking_snapshot or {}).get("ranking_snapshot_id") or ""
            )
            trace.extra["wp02"] = {"chain_result": chain_result}

        trace.pretrade_freshness_status = _refresh_pretrade_truth_v1(
            bound=bound,
            transport=pretrade_transport,
            require_collection=config.require_pretrade_collection,
        )
        trace.pretrade_truth_refreshed = True

        policy_result = run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
            authorization=authorization,
            origin_main_sha=origin_main_sha,
            lane_state_root=config.lane_state_root,
            bound=bound,
            g17_producers=g17_producers,
            observation_source=observation_source,
            evidence_root=config.evidence_root,
            f1_m9_cycle_evaluator=f1_m9_cycle_evaluator,
            repo_root=root,
            lock_root=config.lock_root,
            time_fn=time_fn,
            sleep_fn=sleep_fn,
            fresh_pretrade_get_transport=pretrade_transport,
            cap24_productivity_root=config.cap24_productivity_root,
            portfolio_budget_host=budget_host,
            cancel_requested=cancel_requested,
        )
        owner_go_consumed = (
            config.evidence_root / "bounded_continuous_run_owner_go_consume_v1.json"
        ).is_file()
    except PersistentNaturalEnterConvergenceError as exc:
        raise StandingSupervisorError(exc.reason_code, exc.detail) from exc
    finally:
        budget_state = (
            budget_host.owner.budget_state_v1() if budget_host.owner is not None else None
        )
        trace.extra["portfolio_budget_host"] = {
            "durable_root": str(budget_host.root),
            "owner_opened": budget_host.owner is not None,
            "active_reservation_sum": str(budget_host.owner.active_sum_v1())
            if budget_host.owner is not None
            else "UNKNOWN",
            "recovery_required_before_close": budget_state.recovery_required
            if budget_state is not None
            else True,
            "transport_retry_count": budget_host.transport_retry_count,
            "venue_fill_integrated": False,
        }
        budget_host.close()

    orch = policy_result.orchestrator_result
    trace.governed_cycle_count = int(orch.cycles_completed)
    trace.accepted_c1_count = int(orch.accepted_c1_count)
    trace.terminal_disposition = str(orch.disposition)
    trace.post_count = int(orch.post_count)
    trace.continuous_admission_granted = all(
        item.continuous_admission_granted for item in policy_result.iteration_evidence
    )
    if policy_result.iteration_evidence:
        trace.continuous_admission_reasons = policy_result.iteration_evidence[0].reason_codes

    if trace.post_count != 0:
        raise StandingSupervisorError("POST_COUNT_NONZERO", str(trace.post_count))
    if policy_result.post_allowed or policy_result.external_effect_authorized:
        raise StandingSupervisorError("POLICY_RESULT_EXTERNAL_EFFECT_LEAK")

    if trace.accepted_c1_count != trace.governed_cycle_count:
        raise StandingSupervisorError(
            "C1_CYCLE_COUNT_MISMATCH",
            f"{trace.accepted_c1_count}!={trace.governed_cycle_count}",
        )

    ok = (
        trace.observation_recovery_completed
        and trace.public_supply_refreshed
        and trace.pretrade_truth_refreshed
        and owner_go_consumed
        and trace.post_count == 0
        and trace.terminal_disposition
        not in {DISPOSITION_FAIL_CLOSED, DISPOSITION_STALL, DISPOSITION_CANCELLED}
    )
    return StandingSupervisorRunResultV1(
        ok=ok,
        run_id=run_id,
        trace=trace,
        recovery=recovery,
        policy_result=policy_result,
        owner_go_consumed=owner_go_consumed,
        authority_invariants_ok=auth_proof.ok,
    )


__all__ = [
    "StandingSupervisorConfigV1",
    "StandingSupervisorRunResultV1",
    "assert_supervisor_authority_boundary_v1",
    "run_n1_standing_pre_external_supervisor_v1",
]
