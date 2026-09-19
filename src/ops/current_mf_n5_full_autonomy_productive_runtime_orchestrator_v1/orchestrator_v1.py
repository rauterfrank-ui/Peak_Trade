"""Productive Full-Autonomy N=5 runtime orchestrator — compose-only.

Consumes finished ranking handoff inputs, runs the existing N=5 join chain,
invokes sequential governed cycles with the shared portfolio budget owner,
and rolls up PRE_EXTERNAL readiness. Does not decide trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.bind_join_v1 import (
    bind_occupied_lane_cap24_n1_instruments_v1,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.ingest_join_v1 import (
    admit_occupied_lane_bound_instruments_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.handoff_join_v1 import (
    compose_occupied_lane_mv2_dp_handoff_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.readiness_join_v1 import (
    OccupiedLaneN1HostJoinReadinessProjectionV1,
    compose_occupied_lane_n1_host_join_readiness_v1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.constants_v1 import (
    AUTONOMY_TRADING_DECISION_AUTHORITY,
    EXECUTION_SCHEDULE,
    EXTERNAL_EFFECT_AUTHORIZED,
    FAILURE_AUTHORITY,
    FAILURE_CARDINALITY,
    FAILURE_EXTERNAL_EFFECT,
    FAILURE_FORBIDDEN_KWARG,
    FAILURE_LANE_ISOLATION,
    FAILURE_TERMINAL,
    FORBIDDEN_COMPOSE_KWARGS,
    FULL_AUTONOMY_TRADING_DECISION_AUTHORITY,
    HOST_JOIN,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    OWNER,
    POST_ALLOWED,
    TERMINAL_BOUNDARY_FAIL_CLOSED,
    TERMINAL_BOUNDARY_PRE_EXTERNAL,
)
from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1.completion_join_v1 import (
    OccupiedLaneRuntimeN5CompletionResultV1,
    run_occupied_lane_runtime_n5_completion_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    MAX_LANE_COUNT,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneTopologyV1,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.produce_join_v1 import (
    produce_occupied_lane_cap23_n1_selections_v1,
)
from src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1 import (
    consume_recovered_isolated_lane_topology_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_COMPLETED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    MembershipContextArtifactV1,
    build_membership_context_artifact_v1,
    validate_membership_context_artifact_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)

_SUCCESS_DISPOSITIONS = frozenset(
    {
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        DISPOSITION_HOLD,
        DISPOSITION_COMPLETED,
    }
)


class ProductiveFullAutonomyN5RuntimeOrchestratorError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class ProductiveFullAutonomyCap24BindContextV1:
    ranking_state_root: Path
    universe_state_root: Path
    reconciliation_state_root: Path
    observed_portfolio: PortfolioTruthSnapshotV1
    mark_price_by_native_id: Mapping[str, Any]
    session_id: str
    now_unix: float


@dataclass(frozen=True)
class ProductiveFullAutonomyN5LaneRollupV1:
    lane_id: str
    disposition: str
    post_count: int
    permit_created: bool
    external_effect_count: int
    cursor_store_root: str
    lock_root: str
    evidence_root: str


@dataclass(frozen=True)
class ProductiveFullAutonomyN5RuntimeOrchestratorResultV1:
    terminal_boundary: str
    target_cardinality: int
    occupied_lane_ids: tuple[str, ...]
    lane_rollups: tuple[ProductiveFullAutonomyN5LaneRollupV1, ...]
    readiness_projections: dict[str, OccupiedLaneN1HostJoinReadinessProjectionV1]
    completion_result: OccupiedLaneRuntimeN5CompletionResultV1 | None
    portfolio_active_sum: Decimal
    portfolio_admitted: bool
    external_effect_authorized: bool
    post_allowed: bool
    execution_schedule: str


def _fail(code: str, detail: str = "") -> NoReturn:
    raise ProductiveFullAutonomyN5RuntimeOrchestratorError(code, detail)


def _assert_orchestrator_authority() -> None:
    if (
        AUTONOMY_TRADING_DECISION_AUTHORITY
        or FULL_AUTONOMY_TRADING_DECISION_AUTHORITY
        or JOIN_RANKING_AUTHORITY
        or JOIN_SELECTION_AUTHORITY
        or JOIN_CAP23_SELECTION_AUTHORITY
        or JOIN_CAP24_BINDING_AUTHORITY
        or JOIN_TRADING_AUTHORITY
        or JOIN_EXECUTION_AUTHORITY
        or JOIN_FULL_AUTONOMY_HOST_AUTHORITY
        or MF_PRODUCTIVE_JOIN
        or HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or N_GT_1_ENABLED
        or EXTERNAL_EFFECT_AUTHORIZED
        or POST_ALLOWED
        or int(MAX_POSITIONS_EFFECTIVE) != 1
    ):
        _fail(FAILURE_AUTHORITY, OWNER)


def _select_target_lanes(
    composed: Mapping[str, tuple[Any, BoundInstrumentV1]],
    *,
    target_cardinality: int,
) -> dict[str, tuple[Any, BoundInstrumentV1]]:
    selected: dict[str, tuple[Any, BoundInstrumentV1]] = {}
    for lane_id in LANE_IDS:
        if len(selected) >= target_cardinality:
            break
        pair = composed.get(lane_id)
        if pair is not None:
            selected[lane_id] = pair
    if len(selected) != target_cardinality:
        _fail(
            FAILURE_CARDINALITY,
            f"wanted={target_cardinality} got={len(selected)}",
        )
    return selected


def _assert_lane_root_isolation(rollups: tuple[ProductiveFullAutonomyN5LaneRollupV1, ...]) -> None:
    seen: dict[str, str] = {}
    for rollup in rollups:
        for role, root in (
            ("cursor", rollup.cursor_store_root),
            ("lock", rollup.lock_root),
            ("evidence", rollup.evidence_root),
        ):
            prior = seen.get(root)
            if prior is not None:
                _fail(FAILURE_LANE_ISOLATION, f"{prior},{rollup.lane_id}:{role}")
            seen[root] = f"{rollup.lane_id}:{role}"


def _rollup_from_readiness(
    projections: Mapping[str, OccupiedLaneN1HostJoinReadinessProjectionV1],
) -> tuple[ProductiveFullAutonomyN5LaneRollupV1, ...]:
    rollups: list[ProductiveFullAutonomyN5LaneRollupV1] = []
    for lane_id in LANE_IDS:
        projection = projections.get(lane_id)
        if projection is None:
            continue
        record = projection.n1_consumer_result
        cycle = record.governed_cycle_result
        if int(cycle.post_count) != 0 or cycle.permit_created is not False:
            _fail(FAILURE_EXTERNAL_EFFECT, lane_id)
        if int(cycle.external_effect_count) != 0:
            _fail(FAILURE_EXTERNAL_EFFECT, lane_id)
        rollups.append(
            ProductiveFullAutonomyN5LaneRollupV1(
                lane_id=lane_id,
                disposition=str(cycle.disposition),
                post_count=int(cycle.post_count),
                permit_created=bool(cycle.permit_created),
                external_effect_count=int(cycle.external_effect_count),
                cursor_store_root=str(record.cursor_store_root),
                lock_root=str(record.lock_root),
                evidence_root=str(record.evidence_root),
            )
        )
    return tuple(rollups)


def run_productive_full_autonomy_n5_runtime_orchestrator_v1(
    *,
    membership: MembershipContextArtifactV1,
    ranking_snapshot: Mapping[str, Any],
    topology_state_root_base: Path | str,
    lane_assignment_writer: DurableLaneAssignmentSingleWriterV1,
    cap24_bind: ProductiveFullAutonomyCap24BindContextV1,
    repository_sha: str,
    producer_observed_at_unix: float,
    origin_main_sha: str,
    target_cardinality: int,
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
    include_host_completion_rollup: bool = False,
    **cycle_kwargs: Any,
) -> ProductiveFullAutonomyN5RuntimeOrchestratorResultV1:
    """Compose ranking→topology→Cap23/24→ingest→handoff→readiness (+ optional completion)."""
    _assert_orchestrator_authority()
    forbidden = sorted(set(cycle_kwargs) & FORBIDDEN_COMPOSE_KWARGS)
    if forbidden:
        _fail(FAILURE_FORBIDDEN_KWARG, ",".join(forbidden))
    target = int(target_cardinality)
    if target < 1 or target > int(MAX_LANE_COUNT):
        _fail(FAILURE_CARDINALITY, str(target))
    if not str(origin_main_sha or "").strip():
        _fail(FAILURE_AUTHORITY, "origin_main_sha")
    validate_membership_context_artifact_v1(membership)

    selections: dict[str, SingleSelectedFutureSelectionV1] = (
        produce_occupied_lane_cap23_n1_selections_v1(
            membership=membership,
            ranking_snapshot=ranking_snapshot,
            topology_state_root_base=topology_state_root_base,
            writer=lane_assignment_writer,
            repository_sha=repository_sha,
            producer_observed_at_unix=producer_observed_at_unix,
        )
    )
    topology_membership = membership
    if membership.bootstrap:
        topology_membership = build_membership_context_artifact_v1(
            ordered_instrument_ids=membership.ordered_instrument_ids,
            cap22_provenance=membership.cap22_provenance,
            bootstrap=False,
            prior_membership_reference=membership.instance_id,
        )
    topology: IsolatedLaneTopologyV1 = consume_recovered_isolated_lane_topology_v1(
        membership=topology_membership,
        ranking_snapshot=ranking_snapshot,
        topology_state_root_base=topology_state_root_base,
        writer=lane_assignment_writer,
    )
    bound_by_lane = bind_occupied_lane_cap24_n1_instruments_v1(
        selections=selections,
        topology_state_root_base=topology_state_root_base,
        ranking_state_root=cap24_bind.ranking_state_root,
        universe_state_root=cap24_bind.universe_state_root,
        reconciliation_state_root=cap24_bind.reconciliation_state_root,
        observed_portfolio=cap24_bind.observed_portfolio,
        mark_price_by_native_id=cap24_bind.mark_price_by_native_id,
        repository_sha=repository_sha,
        session_id=cap24_bind.session_id,
        now_unix=cap24_bind.now_unix,
    )
    admitted = admit_occupied_lane_bound_instruments_v1(bound_by_lane)
    composed = compose_occupied_lane_mv2_dp_handoff_v1(admitted, topology)
    selected_pairs = _select_target_lanes(composed, target_cardinality=target)

    owner = (
        portfolio_budget_owner
        if portfolio_budget_owner is not None
        else PortfolioCapitalReservationBudgetOwnerV1()
    )
    readiness_kwargs = dict(cycle_kwargs)
    readiness_kwargs["origin_main_sha"] = origin_main_sha
    readiness = compose_occupied_lane_n1_host_join_readiness_v1(
        selected_pairs,
        portfolio_budget_owner=owner,
        **readiness_kwargs,
    )
    rollups = _rollup_from_readiness(readiness)
    _assert_lane_root_isolation(rollups)

    terminal = TERMINAL_BOUNDARY_PRE_EXTERNAL
    for rollup in rollups:
        if rollup.disposition not in _SUCCESS_DISPOSITIONS:
            terminal = TERMINAL_BOUNDARY_FAIL_CLOSED
        if rollup.disposition == DISPOSITION_FAIL_CLOSED:
            _fail(FAILURE_TERMINAL, rollup.lane_id)

    completion: OccupiedLaneRuntimeN5CompletionResultV1 | None = None
    if include_host_completion_rollup:
        completion = run_occupied_lane_runtime_n5_completion_v1(
            selected_pairs,
            target_cardinality=target,
            origin_main_sha=origin_main_sha,
            **{k: v for k, v in cycle_kwargs.items() if k not in FORBIDDEN_COMPOSE_KWARGS},
        )
        if int(completion.post_count) != 0 or completion.permit_created:
            _fail(FAILURE_EXTERNAL_EFFECT, OWNER)

    budget = owner.budget_state_v1()
    return ProductiveFullAutonomyN5RuntimeOrchestratorResultV1(
        terminal_boundary=terminal,
        target_cardinality=target,
        occupied_lane_ids=tuple(sorted(readiness)),
        lane_rollups=rollups,
        readiness_projections=dict(readiness),
        completion_result=completion,
        portfolio_active_sum=budget.active_reservation_sum,
        portfolio_admitted=budget.admitted,
        external_effect_authorized=False,
        post_allowed=False,
        execution_schedule=EXECUTION_SCHEDULE,
    )
