"""Occupied-lane governed-cycle N=1 consumer: S8 roots → invoke, NON-V5 EG, S7 T2.

Harness join only. Does not flip MF_PRODUCTIVE_JOIN or 1_UNJOINED.
Does not bind Cap61, join a host, call V5, or POST.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Mapping, NoReturn, Sequence

if TYPE_CHECKING:
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        AuthenticatedEntryEpisodeRequestV1,
        HostBudgetRecoveryContextV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import (
        SlotCloseAccountingSourceV1,
    )
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeBindingV1,
        PositionEpisodeScopeV1,
    )

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    PerLaneGovernedIngressV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
    PositionManagementExecutionHandoffV1,
    PositionManagementQuantityHandoffV1,
    bind_position_management_quantity_handoff_v1,
    compose_position_management_full_close_intent_v1,
    occupied_l10_close_from_binding_v1,
)
from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentV1,
    canonical_order_intent_to_semantic_dict,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    CURSOR_FILENAME,
    CURSOR_OWNER_CHANGE_REQUIRED,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EG_V5_USED,
    FAILURE_AUTHORITY,
    FAILURE_IDENTITY_MISMATCH,
    FAILURE_INJECTED_C1_REQUIRED,
    FAILURE_NATIVE_ID_MISSING,
    FAILURE_OCCUPANCY,
    FAILURE_ORIGIN_MAIN_SHA,
    FAILURE_PAIR_TYPE,
    FAILURE_S8_ROOTS_MISSING,
    FAILURE_UNKNOWN_LANE_ID,
    FAILURE_V5_DISPATCH,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    GLOBAL_N1_CURSOR_REJECTED,
    GOVERNED_CYCLE_INVOKED,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_IMPLEMENTED,
    JOIN_MAPPING_AUTHORITY,
    JOIN_MEMBERSHIP_AUTHORITY,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MAY_BIND_CAP61_STATE_ROOT,
    MAY_INVOKE_GOVERNED_CYCLE,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    OCCUPIED_LANES_ONLY,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    S8_CONSUMED,
    T2_S7_USED,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    UNIQUE_MUTABLE_ROOTS_ENFORCED,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError,
    OccupiedLaneMv2DpDecisionStateConsumerInvocationV1,
    bind_occupied_lane_governed_cycle_store_roots_v1,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
    CurrentProductiveEnterLive29PPortfolioSlotContextV1,
    DECISION_ENTER,
    POSITION_MANAGEMENT_HANDOFF_REQUIRED,
    STATUS_PASS,
    current_productive_decision_class_v1,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    EG_OWNER_GO,
    GET_OWNER_GO,
    RUNTIME_OWNER_GO,
    T2_RUNTIME_OWNER_GO,
    CurrentProductiveGovernedCycleAuthorizationV1,
    CurrentProductiveGovernedCycleResultV1,
    run_current_productive_governed_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    OCCUPANCY_OWNER_GO,
    CurrentProductiveGovernedNextC1OrchestrationError,
    cursor_last_accepted_c1_venue_event_time_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.compose_v1 import (
    InstrumentRuntimeIdentityClosureError,
    compose_per_lane_n5_identity_closure_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.reconciliation_admission_v1 import (
    build_master_v2_reconciliation_admission_for_lane_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lane_generation_v1 import (
    LaneGenerationError,
    assert_cursor_matches_identity_or_absent_v1,
    ensure_lane_generation_safe_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

_FALSE = "false"
_TRUE = "true"


class FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class OccupiedLaneGovernedCycleN1ConsumerResultV1:
    lane_id: str
    bound_instrument: BoundInstrumentV1
    native_id: str
    cursor_store_root: str
    lock_root: str
    evidence_root: str
    bootstrap_used: bool
    s7_invocation: OccupiedLaneMv2DpDecisionStateConsumerInvocationV1 | None
    governed_cycle_result: CurrentProductiveGovernedCycleResultV1
    eg_v5_used: bool
    t2_s7_used: bool
    cap61_state_root_bound: bool
    position_management_quantity_handoff: PositionManagementQuantityHandoffV1 | None = None
    position_management_close_intent: CanonicalOrderIntentV1 | None = None
    slot_loss_protection_status: str = "NOT_APPLICABLE"
    slot_loss_protection_reason_codes: tuple[str, ...] = ()


def _fail(code: str, detail: str = "") -> NoReturn:
    raise FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        not JOIN_IMPLEMENTED
        or not S8_CONSUMED
        or not GOVERNED_CYCLE_INVOKED
        or not MAY_INVOKE_GOVERNED_CYCLE
        or not T2_S7_USED
        or EG_V5_USED
        or not OCCUPIED_LANES_ONLY
        or not UNIQUE_MUTABLE_ROOTS_ENFORCED
        or not GLOBAL_N1_CURSOR_REJECTED
        or JOIN_SELECTION_AUTHORITY
        or JOIN_CAP23_SELECTION_AUTHORITY
        or JOIN_CAP24_BINDING_AUTHORITY
        or JOIN_TRADING_AUTHORITY
        or JOIN_RUNTIME_ACTIVATION_AUTHORITY
        or JOIN_EXECUTION_AUTHORITY
        or JOIN_RANKING_AUTHORITY
        or JOIN_MEMBERSHIP_AUTHORITY
        or JOIN_MAPPING_AUTHORITY
        or JOIN_PERSISTENCE_AUTHORITY
        or JOIN_FULL_AUTONOMY_HOST_AUTHORITY
        or HOST_JOIN
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or FULL_AUTONOMY_HOST_CHANGE_REQUIRED
        or CURSOR_OWNER_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
        or THIS_SLICE_MAY_REINVOKE_CAP23
        or THIS_SLICE_MAY_REINVOKE_CAP24
        or MAY_BIND_CAP61_STATE_ROOT
        or not UNIVERSE_ISOLATION_ENFORCED
    ):
        _fail(FAILURE_AUTHORITY, OWNER)
    if (
        CROSS_UNIVERSE_SELECTION
        or CROSS_UNIVERSE_PIN
        or CROSS_UNIVERSE_REPLACEMENT
        or CROSS_UNIVERSE_FALLBACK
        or CROSS_UNIVERSE_CANDIDATE_BORROWING
        or CROSS_UNIVERSE_RERANKING
        or MULTI_UNIVERSE_MERGE
        or INSTRUMENT_ID_ALONE_SUFFICIENT
    ):
        _fail(FAILURE_AUTHORITY, "constant_violation")


def _iso_utc(unix: float) -> str:
    return datetime.fromtimestamp(float(unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def non_v5_eg_dispatch_v1(**kwargs: Any) -> SimpleNamespace:
    """EG dispatch that must never call V5 or Cap21-24."""
    if EG_V5_USED:
        _fail(FAILURE_V5_DISPATCH, OWNER)
    forbidden = (
        "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1",
        "_run_cap21_to_cap24_v1",
    )
    for name in forbidden:
        if name in kwargs:
            _fail(FAILURE_V5_DISPATCH, name)
    return SimpleNamespace(permit_created=_FALSE, post_count="0")


def _occupancy_absent() -> dict[str, object]:
    return {
        "POSITIONS": {"code": "0", "data": []},
        "PENDING": {"code": "0", "data": []},
        "CONFIG": {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
    }


def _cursor_floor_or_zero(cursor_store_root: Path) -> float:
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(cursor_store_root)
    if not isinstance(loaded, Mapping):
        return 0.0
    try:
        return float(cursor_last_accepted_c1_venue_event_time_v1(loaded))
    except CurrentProductiveGovernedNextC1OrchestrationError:
        return 0.0


def _align_lane_s7_closes_to_injected_c1_v1(
    lane_s7: Mapping[str, Any],
    candles_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Align S7 MV2 inputs to injected governed-cycle C1 (closes + cap61 floor)."""
    aligned = dict(lane_s7)
    extracted, last_ts = extract_finalized_candle_closes_v1(candles_payload)
    if extracted:
        aligned["finalized_closes"] = extracted
    if last_ts is None:
        return aligned
    candle_last = float(last_ts)
    aligned["last_finalized_event_ts_unix"] = candle_last - 60.0
    if getattr(lane_s7.get("canonical_price_provenance"), "mark_clock_json", "null") == "null":
        aligned["observed_unix"] = max(float(lane_s7["observed_unix"]), candle_last + 0.001)
    return aligned


def _align_lane_s7_bootstrap_to_injected_c1_v1(
    lane_s7: Mapping[str, Any],
    candles_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind MV2 cold-start cap61 floor strictly below injected governed-cycle C1."""
    return _align_lane_s7_closes_to_injected_c1_v1(lane_s7, candles_payload)


def _s7_kwargs(
    *,
    cycle_id_prefix: str,
    observed_unix: float,
    mark_px: float,
    index_px: float,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    finalized_closes: Sequence[float],
    last_finalized_event_ts_unix: float,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    g17_typed_vol_producers: Mapping[str, object] | None,
    canonical_price_provenance: object,
) -> dict[str, Any]:
    return {
        "cycle_id_prefix": cycle_id_prefix,
        "observed_unix": observed_unix,
        "mark_px": mark_px,
        "index_px": index_px,
        "canonical_price_provenance": canonical_price_provenance,
        "bid_px": bid_px,
        "ask_px": ask_px,
        "volume": volume,
        "open_interest": open_interest,
        "funding_rate": funding_rate,
        "finalized_closes": finalized_closes,
        "last_finalized_event_ts_unix": last_finalized_event_ts_unix,
        "venue_flat": venue_flat,
        "existing_position_side": existing_position_side,
        "g17_typed_vol_producers": g17_typed_vol_producers,
    }


def _finalize_portfolio_reservation_after_enter_join_v1(
    owner: PortfolioCapitalReservationBudgetOwnerV1 | None,
    *,
    reservation_id: str,
    enter_status: str,
    venue_plan_pass: bool,
    venue_quantity_admission_denied: bool = False,
) -> None:
    if owner is None or not str(reservation_id or "").strip():
        return
    if enter_status == STATUS_PASS and venue_plan_pass:
        owner.commit_internal_pre_external_effect_v1(str(reservation_id))
        return
    if venue_quantity_admission_denied:
        owner.release_sizing_or_admission_deny_v1(str(reservation_id))
        return
    owner.release_plan_failure_v1(str(reservation_id))


def _occupied_scope_close_binding_v1(
    *, lane_identity, episode, cursor_root: Path
) -> dict[str, Any]:
    from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
        require_current_cursor_continuity_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        current_productive_cursor_digest_v1,
    )

    identity = episode.identity
    if (
        not episode.binding.has_open_position
        or episode.binding.alpha_blocked
        or episode.binding.existing_position_side != identity.position_side
    ):
        raise ValueError("OCCUPIED_SCOPE_CLOSE_EPISODE_MISMATCH")
    exit_state = load_exit_policy_state_v1(
        Path(episode.binding.state_root),
        expected_repository_sha=episode.binding.repository_sha,
        expected_config_digest=episode.binding.config_digest,
        expected_instrument_id=identity.instrument_id,
    )
    if exit_state.to_dict() != episode.binding.to_canonical_state().to_dict():
        raise ValueError("OCCUPIED_SCOPE_CLOSE_EPISODE_READBACK_MISMATCH")
    cursor = load_current_productive_sidestate_confirmation_cursor_v1(cursor_root)
    if cursor is None or episode.binding.current_cursor_publication is None:
        raise ValueError("OCCUPIED_SCOPE_CLOSE_PROOF_UNAVAILABLE")
    require_current_cursor_continuity_v1(episode=episode, incoming=cursor, store_root=cursor_root)
    return _scope_switch_close_binding_v1(
        lane_identity=lane_identity,
        identity=identity,
        cursor_root=cursor_root,
        exit_state_digest=exit_state.digest(),
        cursor_digest=current_productive_cursor_digest_v1(cursor),
        entry_source_ref=(
            episode.entry_source_ref
            if identity.account_scope.execution_environment == "LIVE"
            else None
        ),
    )


def _scope_switch_close_binding_v1(
    *,
    lane_identity,
    identity,
    cursor_root: Path,
    exit_state_digest: str,
    cursor_digest: str,
    entry_source_ref: str | None = None,
) -> dict[str, Any]:
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
        restore_layered_core_episode_v1,
    )

    identity.validate_v1()
    if (
        identity.account_scope.execution_environment not in {"INTERNAL_SIMULATED_EXECUTION", "LIVE"}
        or identity.lane_id != lane_identity.lane_id
        or identity.instrument_id != lane_identity.canonical_instrument_id
        or identity.venue_native_id != lane_identity.venue_native_id
    ):
        raise ValueError("OCCUPIED_SCOPE_CLOSE_EPISODE_MISMATCH")
    scope = read_occupied_scope_mark_snapshot_v1(cursor_root)
    snapshot = restore_layered_core_episode_v1(
        cursor_root, expected_instrument_id=identity.instrument_id
    )
    expected_regimes = {"long": ("bull", "bear"), "short": ("bear", "bull")}
    if (
        scope is None
        or scope["mark"]["pending_close_episode_id"] != identity.episode_id
        or scope["mark"].get("switch_condition_met") is not True
        or scope["snapshot"]["snapshot_id"] != snapshot.snapshot_id
        or (scope["mark"].get("regime_pre"), snapshot.regime.value)
        != expected_regimes[identity.position_side]
    ):
        raise ValueError("OCCUPIED_SCOPE_CLOSE_PROOF_UNAVAILABLE")
    return {
        "lane_instrument": lane_identity.to_manifest_dict(),
        "position_episode": asdict(identity),
        "exit_state_digest": exit_state_digest,
        "cursor_digest": cursor_digest,
        "scope_digest": scope["digest"],
        "scope_seal_id": scope["mark"]["seal_id"],
        "cycle_id": scope["mark"]["cycle_id"],
        **({"entry_source_ref": entry_source_ref} if entry_source_ref is not None else {}),
    }


def _occupied_attempt_root_v1(
    evidence_root: str | Path, *, prefix: str, authenticated: bool
) -> Path:
    attempt_dir = "authenticated_mark_attempts_v1" if authenticated else "bounded_slot_attempts_v1"
    return Path(evidence_root) / attempt_dir / hashlib.sha256(prefix.encode()).hexdigest()


def recover_occupied_scope_close_for_reconciliation_v1(
    *,
    lane_id: str,
    lane_pair: tuple[IsolatedLaneSlotV1, BoundInstrumentV1],
    expected_scope: PositionEpisodeScopeV1,
    episode: PositionEpisodeBindingV1 | None = None,
    sealed_accounting_source: SlotCloseAccountingSourceV1 | None = None,
    authenticated_entry: AuthenticatedEntryEpisodeRequestV1 | None = None,
    host_budget_recovery: HostBudgetRecoveryContextV1 | None = None,
) -> PositionManagementExecutionHandoffV1:
    """Read the exact close for its authenticated position or sealed simulated episode."""
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
        OccupiedLaneRuntimeInstrumentIdentityV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        occupied_scope_mark_cycle_lock_v1,
        read_retained_occupied_scope_close_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
        restore_retained_position_management_close_v1,
    )

    from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import (
        SlotCloseAccountingSourceV1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
        inspect_sealed_simulated_episode_v1,
    )

    if (
        sum(
            source is not None
            for source in (episode, sealed_accounting_source, authenticated_entry)
        )
        != 1
    ):
        raise ValueError("OCCUPIED_SCOPE_CLOSE_EXACTLY_ONE_EPISODE_SOURCE_REQUIRED")
    if authenticated_entry is not None:
        from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
            AuthenticatedEntryEpisodeRequestV1,
            HostBudgetRecoveryContextV1,
        )

        if (
            type(authenticated_entry) is not AuthenticatedEntryEpisodeRequestV1
            or type(host_budget_recovery) is not HostBudgetRecoveryContextV1
            or expected_scope.execution_environment != "LIVE"
            or expected_scope.account_identity != host_budget_recovery.account
            or host_budget_recovery.host.bindings != {lane_id: lane_pair[1]}
        ):
            raise ValueError("OCCUPIED_SCOPE_CLOSE_AUTHENTICATED_HOST_REQUIRED")
        config_rows = host_budget_recovery.occupancy_payloads.get("CONFIG", {}).get("data", [])
        if len(config_rows) != 1 or config_rows[0].get("posMode") != "net_mode":
            raise ValueError("FULL_CLOSE_NET_POSITION_MODE_REQUIRED")
        episode = host_budget_recovery.bind_current_authenticated_entry_episode_v1(
            lane_id=lane_id,
            proof_root=authenticated_entry.proof_root,
            proof=authenticated_entry.proof,
            config_digest=_occupied_scope_exit_config_digest_v1(),
            recover_only=True,
        )
    elif (
        host_budget_recovery is not None
        or expected_scope.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
    ):
        raise ValueError("OCCUPIED_SCOPE_CLOSE_SIMULATED_RECOVERY_REQUIRED")
    if sealed_accounting_source is not None:
        if type(sealed_accounting_source) is not SlotCloseAccountingSourceV1:
            raise ValueError("OCCUPIED_SCOPE_CLOSE_SEALED_ACCOUNTING_SOURCE_INVALID")
        identity = sealed_accounting_source.identity_v1()
    else:
        identity = episode.identity
    if identity.account_scope != expected_scope:
        raise ValueError("OCCUPIED_SCOPE_CLOSE_ACCOUNT_SCOPE_MISMATCH")
    cursor, lock_root, evidence_root = bind_occupied_lane_governed_cycle_store_roots_v1(
        {lane_id: lane_pair}
    )[lane_id]
    lane_identity = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id=lane_id, bound=lane_pair[1]
    )
    cursor_root = Path(cursor)

    def read_binding():
        if sealed_accounting_source is None:
            return (
                _occupied_scope_close_binding_v1(
                    lane_identity=lane_identity, episode=episode, cursor_root=cursor_root
                ),
                None,
            )
        sealed = inspect_sealed_simulated_episode_v1(
            identity=identity,
            state_root=Path(sealed_accounting_source.state_root),
            repository_sha=sealed_accounting_source.repository_sha,
            config_digest=sealed_accounting_source.config_digest,
            expected_initial_source_ref=sealed_accounting_source.initial_source_ref,
            expected_current_cursor_root=cursor_root,
        )
        if sealed["bound_instrument"] != lane_pair[1].to_dict():
            raise ValueError("OCCUPIED_SCOPE_CLOSE_FLAT_INSTRUMENT_BINDING_MISMATCH")
        return (
            _scope_switch_close_binding_v1(
                lane_identity=lane_identity,
                identity=identity,
                cursor_root=cursor_root,
                exit_state_digest=sealed["prior_exit_state_digest"],
                cursor_digest=sealed["prior_cursor_digest"],
            ),
            sealed["source_payload"]["fills"][-1],
        )

    binding, closing_fill = read_binding()
    suffix = f":{lane_id}:{lane_id}"
    cycle_id = binding["cycle_id"]
    if not isinstance(cycle_id, str) or not cycle_id.endswith(suffix):
        raise ValueError("OCCUPIED_SCOPE_CLOSE_CYCLE_ID_INVALID")
    prefix = cycle_id.removesuffix(suffix)
    if not prefix:
        raise ValueError("OCCUPIED_SCOPE_CLOSE_CYCLE_ID_INVALID")
    attempt_root = _occupied_attempt_root_v1(
        evidence_root, prefix=prefix, authenticated=authenticated_entry is not None
    )

    def read_completed_close(current, fill):
        if current != binding or fill != closing_fill:
            raise ValueError("OCCUPIED_SCOPE_CLOSE_PROOF_CHANGED")
        retained = read_retained_occupied_scope_close_v1(attempt_root)
        handoff = restore_retained_position_management_close_v1(retained, expected_binding=current)
        quantity = handoff.source.quantity_handoff
        if (
            handoff.source.close_quantity_decision.binding_ref
            != hashlib.sha256(
                json.dumps(lane_identity.to_manifest_dict(), sort_keys=True).encode()
            ).hexdigest()
            or quantity.lane_id != lane_id
            or quantity.instrument_id != lane_identity.canonical_instrument_id
            or quantity.venue_native_id != lane_identity.venue_native_id
            or quantity.instrument_epoch != lane_identity.lane_identity.instrument_epoch
            or quantity.position_side != identity.position_side
        ):
            raise ValueError("OCCUPIED_SCOPE_CLOSE_HANDOFF_IDENTITY_MISMATCH")
        if authenticated_entry is not None:
            positions = tuple(
                position
                for position in host_budget_recovery.observed.positions
                if position.instrument_id == identity.instrument_id
            )
            if (
                len(positions) != 1
                or positions[0].side != identity.position_side.upper()
                or abs(positions[0].signed_quantity) != Decimal(handoff.envelope.quantity)
            ):
                raise ValueError("OCCUPIED_SCOPE_CLOSE_CURRENT_POSITION_MISMATCH")
        if fill is not None:
            envelope = handoff.envelope
            if (
                fill["fill_id"] != "original-close:" + envelope.envelope_digest
                or fill["instrument_id"] != envelope.instrument_id
                or fill["side"].lower() != envelope.side
                or Decimal(fill["quantity"]) != Decimal(envelope.quantity)
                or fill["reduce_only"] is not True
            ):
                raise ValueError("OCCUPIED_SCOPE_CLOSE_SEALED_FILL_MISMATCH")
        return handoff

    def verify_completed_close():
        try:
            read_completed_close(*read_binding())
        except ValueError:
            return False
        return True

    # Refuse incomplete/foreign records before attempting stale lock recovery.
    read_completed_close(binding, closing_fill)
    lock = occupied_scope_mark_cycle_lock_v1(
        lock_root=Path(lock_root),
        evidence_root=attempt_root,
        native_id=lane_identity.venue_native_id,
        verify_completed_close=verify_completed_close,
    )
    lock.acquire()
    try:
        return read_completed_close(*read_binding())
    finally:
        lock.release()


def _occupied_scope_exit_config_digest_v1() -> str:
    from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
        FROZEN_PROFIT_PROTECTION_DISTANCE,
    )
    from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
        layer_c_derived_exit_policy_adverse_config_digest_v1,
    )

    return layer_c_derived_exit_policy_adverse_config_digest_v1(
        profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
    )


def _t2_from_s7(
    *,
    lane_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    native_id: str,
    lane_id: str,
    s7_base: Mapping[str, Any],
    live_29p_injected: CurrentProductiveEnterLive29PInjectedGetV1 | None,
    candles_payload: Mapping[str, Any],
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
    common_epoch_decision_epoch: str | None = None,
    position_management_only: bool = False,
    position_management_ingress: PerLaneGovernedIngressV1 | None = None,
    position_management_config_payload: Mapping[str, Any] | None = None,
    host_budget_recovery: HostBudgetRecoveryContextV1 | None = None,
    offline_observation_clock_unix: float | None = None,
) -> Any:
    def _dispatch(**kwargs: Any) -> SimpleNamespace:
        bound_epoch = str(common_epoch_decision_epoch or "").strip()
        epoch = bound_epoch if bound_epoch else _iso_utc(float(s7_base["observed_unix"]))
        observation = kwargs.get("observation")
        last_finalized_ts = float(s7_base["last_finalized_event_ts_unix"])
        accepted_c1_ts = s7_base.get("accepted_c1_venue_event_time_unix")
        if accepted_c1_ts is not None:
            accepted_c1_ts = float(accepted_c1_ts)
        closes = tuple(s7_base["finalized_closes"])
        if observation is not None:
            obs_c1_ts = float(getattr(observation, "venue_event_time", 0) or 0)
            if obs_c1_ts > 0:
                accepted_c1_ts = obs_c1_ts
            payload = getattr(observation, "payload", None)
            extracted, last_ts = extract_finalized_candle_closes_v1(
                payload if payload is not None else candles_payload
            )
            if extracted:
                closes = extracted
        compose_s7_base = {
            key: value
            for key, value in s7_base.items()
            if key not in {"cycle_evidence_root", "accepted_c1_venue_event_time_unix"}
        }
        eg_incoming_cursor = kwargs.get("incoming_cursor")
        if position_management_only and s7_base.get("position_episode_bindings") is not None:
            # Exit continuity consumes the exact last committed Core cursor.
            # S7 still publishes its negative Entry marker before evaluation
            # and CAS-publishes the actual result against that marker.
            eg_incoming_cursor = load_current_productive_sidestate_confirmation_cursor_v1(
                Path(lane_pairs[lane_id][0].lane_state_root)
            )
        if s7_base.get("occupied_scope_mark"):
            from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
                NakedLayeredCoreDurableStateError,
            )
            from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
                require_new_occupied_scope_mark_v1,
            )

            mark = s7_base["canonical_price_provenance"]
            episode = s7_base["position_episode_bindings"][lane_id]
            try:
                require_new_occupied_scope_mark_v1(
                    Path(lane_pairs[lane_id][0].lane_state_root),
                    event_unix=mark.require_current_mark_clock_v1(
                        observed_unix=float(s7_base["observed_unix"])
                    ),
                    price=float(s7_base["mark_px"]),
                    episode_id=episode.identity.episode_id,
                )
            except NakedLayeredCoreDurableStateError as exc:
                _fail(FAILURE_AUTHORITY, str(exc))
        try:
            composed = compose_occupied_lane_mv2_dp_durable_cycle_v1(
                lane_pairs,
                **{
                    **compose_s7_base,
                    "finalized_closes": closes,
                    "last_finalized_event_ts_unix": last_finalized_ts,
                    "accepted_c1_venue_event_time_unix": accepted_c1_ts,
                    "incoming_cursor_override": eg_incoming_cursor,
                    "observed_unix": (
                        offline_observation_clock_unix
                        if offline_observation_clock_unix is not None
                        else datetime.now(timezone.utc).timestamp()
                        if getattr(
                            s7_base.get("canonical_price_provenance"), "mark_clock_json", "null"
                        )
                        != "null"
                        else float(s7_base["observed_unix"])
                        if s7_base.get("rotation_exit_requests") is not None
                        else float(accepted_c1_ts) + 1.0
                        if accepted_c1_ts is not None
                        else last_finalized_ts + 1.0
                    ),
                },
            )
        except Exception as exc:
            # A failed Core cycle may precede its durable negative cursor write.
            # Fence this original host owner before returning the failure, so
            # retained plans cannot keep using its old positive admission. Close
            # retains all durable holds; no cursor, release or submit evidence
            # is fabricated. A new owner still needs original recovery.
            if portfolio_budget_owner is not None:
                try:
                    portfolio_budget_owner.close()
                except Exception as close_error:
                    # close() disarms before closing its writer lease. Keep the
                    # original Core failure and expose failed cleanup as cause.
                    raise exc from close_error
            if isinstance(exc, FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError):
                _fail(exc.failure_code, exc.detail)
            raise
        if len(composed) != 1:
            _fail(FAILURE_OCCUPANCY, ",".join(sorted(composed)))
        invocation = next(iter(composed.values()))
        bound = invocation.bound_instrument
        if str(bound.venue_native_id or "").strip() != native_id:
            _fail(FAILURE_IDENTITY_MISMATCH, native_id)
        replay = invocation.cycle_result.replay
        if position_management_only:
            if replay is None or not replay.replay_pass:
                _fail(FAILURE_AUTHORITY, "position_management_replay_failed")
            outcome = invocation.cycle_result.decision_outcome
            if outcome in {"enter_long", "enter_short"}:
                _fail(FAILURE_AUTHORITY, "position_management_entry_forbidden")
            action_pending = outcome in {"reduce", "exit"}
            quantity_handoff = None
            close_intent = None
            close_quantity_decision = None
            close_execution_handoff = None
            occupied_scope_close_binding = None
            close_plan_reasons = ()
            if action_pending:
                if position_management_ingress is None:
                    _fail(FAILURE_AUTHORITY, "position_management_ingress_required")
                metadata = None
                if (
                    live_29p_injected is not None
                    and live_29p_injected.instruments_payload is not None
                ):
                    metadata = (
                        produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
                            venue_native_id=native_id,
                            bound_instrument_id=bound.instrument_id,
                            instruments_payload=live_29p_injected.instruments_payload,
                            observed_at_as_of=live_29p_injected.observed_at,
                        )
                    )
                quantity_args = dict(
                    identity=position_management_ingress.identity,
                    position=position_management_ingress.position,
                    reconciliation_admitted=position_management_ingress.reconciliation.admitted,
                    replay=replay,
                    metadata=metadata,
                )
                if outcome == "exit":
                    close_handoff = compose_position_management_full_close_intent_v1(
                        **quantity_args
                    )
                    quantity_handoff = close_handoff.quantity_handoff
                    close_intent = close_handoff.canonical_intent
                    close_quantity_decision = close_handoff.close_quantity_decision
                    config_rows = (position_management_config_payload or {}).get("data", [])
                    net_mode = len(config_rows) == 1 and config_rows[0].get("posMode") == "net_mode"
                    if close_intent is not None and not net_mode:
                        close_plan_reasons = ("FULL_CLOSE_NET_POSITION_MODE_REQUIRED",)
                    if close_intent is not None and net_mode:
                        status, close_plan_reasons, plan = (
                            try_bind_current_productive_venue_plan_v1(
                                replay=replay,
                                bound_instrument=bound,
                                session_id=str(s7_base["cycle_id_prefix"]),
                                run_id=f"{s7_base['cycle_id_prefix']}:{next(iter(composed))}",
                                composed_epoch=epoch,
                                execution_mode=(
                                    s7_base["position_episode_scope"].execution_environment
                                    if s7_base.get("position_episode_scope") is not None
                                    else "LIVE"
                                ),
                                full_close_handoff=close_handoff,
                            )
                        )
                        if status is CompositionStatusV1.PASS and plan is not None:
                            l10_close = None
                            policy = replay.intermediate.entry_exit_decision
                            if (
                                s7_base.get("occupied_scope_mark")
                                and policy.exit_class.value == "strategy_invalidation_exit"
                                and any(
                                    reason.startswith("l10_scope_switch_exit:")
                                    for reason in policy.reason_codes
                                )
                            ):
                                occupied_scope_close_binding = _occupied_scope_close_binding_v1(
                                    lane_identity=position_management_ingress.identity,
                                    episode=s7_base["position_episode_bindings"][lane_id],
                                    cursor_root=Path(lane_pairs[lane_id][0].lane_state_root),
                                )
                                l10_close = occupied_l10_close_from_binding_v1(
                                    occupied_scope_close_binding
                                )
                                if (
                                    "l10_scope_switch_exit:" + l10_close.scope_seal_id
                                ) not in policy.reason_codes:
                                    _fail(FAILURE_AUTHORITY, "occupied_scope_close_seal_mismatch")
                            envelope = bind_final_order_envelope_from_venue_plan_v1(
                                plan,
                                admission_ref=(
                                    l10_close.admission_ref_v1()
                                    if l10_close is not None
                                    else f"{s7_base['cycle_id_prefix']}:position-management"
                                ),
                                provenance_ref=close_intent.semantic_digest,
                                creation_epoch=epoch,
                            )
                            close_execution_handoff = PositionManagementExecutionHandoffV1(
                                source=close_handoff, envelope=envelope, l10_close=l10_close
                            )
                else:
                    quantity_handoff = bind_position_management_quantity_handoff_v1(**quantity_args)
                    # Missing metadata or a rejected quantity binding precedes
                    # the still-unbound reduction rule. Preserve that owner's
                    # actual reason instead of relabelling every failure.
                    if quantity_handoff.status in {
                        "POSITION_QUANTITY_BOUND",
                        "BOUND_TO_CANONICAL_INTENT",
                    }:
                        quantity_handoff = replace(
                            quantity_handoff,
                            status="REDUCE_RISK_RULE_REQUIRED",
                            requested_quantity=None,
                            canonical_intent_ref="",
                            reason_codes=("REDUCE_RISK_RULE_REQUIRED",),
                        )
            _dispatch.last_position_management_quantity_handoff = quantity_handoff
            _dispatch.last_position_management_close_intent = close_intent
            _dispatch.last_invocation = invocation
            return SimpleNamespace(
                runtime_cycle_count="1",
                decision_result=(
                    "POSITION_MANAGEMENT_VENUE_PLAN_BOUND"
                    if close_execution_handoff is not None
                    else "POSITION_MANAGEMENT_ACTION_PENDING"
                    if action_pending
                    else "POSITION_MANAGEMENT_EVALUATED"
                ),
                decision_execution_eligible=_FALSE,
                master_v2_decision=outcome,
                venue_plan_status="BOUND" if close_execution_handoff else "NOT_REQUESTED",
                final_envelope_id=(envelope.envelope_id if close_execution_handoff else ""),
                final_envelope_digest=(envelope.envelope_digest if close_execution_handoff else ""),
                final_order_envelope=(envelope if close_execution_handoff else None),
                position_management_execution_handoff=close_execution_handoff,
                occupied_scope_close_binding=occupied_scope_close_binding,
                canonical_order_intent=close_intent if close_execution_handoff else None,
                permit_created=_FALSE,
                post_count="0",
                first_real_blocker=(
                    ""
                    if close_execution_handoff
                    else close_plan_reasons[0]
                    if close_plan_reasons
                    else quantity_handoff.reason_codes[0]
                    if quantity_handoff is not None and quantity_handoff.reason_codes
                    else POSITION_MANAGEMENT_HANDOFF_REQUIRED
                    if action_pending
                    else ""
                ),
                s7_invocation=invocation,
                position_management_quantity_handoff=(
                    None if quantity_handoff is None else quantity_handoff.to_dict()
                ),
                position_management_canonical_close_intent=(
                    None
                    if close_intent is None
                    else {
                        **canonical_order_intent_to_semantic_dict(close_intent),
                        "semantic_digest": close_intent.semantic_digest,
                    }
                ),
                position_management_close_quantity_assessment=(
                    None if close_quantity_decision is None else close_quantity_decision.to_dict()
                ),
            )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
            maybe_apply_synthetic_enter_forensic_overlay_v1,
            read_cycle_index_from_s5_evidence_root_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
            append_flight_record_stage_v1,
            persist_continuation_snapshot_v1,
        )

        flight_parent = "gen_s7_mv2_output"
        flight_parent = (
            append_flight_record_stage_v1(
                stage="S7_MV2_FINAL_OUTPUT",
                producer_symbol="compose_occupied_lane_mv2_dp_durable_cycle_v1",
                consumer_symbol="maybe_apply_synthetic_enter_forensic_overlay_v1",
                parent_generation_id=flight_parent,
                replay=replay,
            )
            or flight_parent
        )

        cycle_evidence_root = Path(str(s7_base.get("cycle_evidence_root") or ""))
        cycle_index = read_cycle_index_from_s5_evidence_root_v1(cycle_evidence_root)
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            replay,
            cycle_index=cycle_index,
            cycle_evidence_root=cycle_evidence_root if str(cycle_evidence_root) else None,
        )
        replay = overlay.replay
        if overlay.applied:
            flight_parent = (
                append_flight_record_stage_v1(
                    stage="SYNTHETIC_OVERLAY_OUTPUT",
                    producer_symbol="maybe_apply_synthetic_enter_forensic_overlay_v1",
                    consumer_symbol="join_current_productive_enter_live_29p_before_venue_plan_v1",
                    parent_generation_id=flight_parent,
                    replay=replay,
                    extra={
                        "natural_outcome_before_overlay": overlay.natural_outcome_before,
                        "synthetic_side": overlay.synthetic_side,
                    },
                )
                or flight_parent
            )
        if overlay.applied:
            evidence = getattr(replay, "evidence", None)
            raw_outcome = getattr(evidence, "decision_outcome", "") if evidence is not None else ""
            consumed_outcome = str(getattr(raw_outcome, "value", raw_outcome) or "").strip().lower()
            invocation = replace(
                invocation,
                cycle_result=replace(
                    invocation.cycle_result,
                    replay=replay,
                    decision_outcome=consumed_outcome,
                ),
            )
        portfolio_slot = None
        if portfolio_budget_owner is not None:
            evidence = getattr(replay, "evidence", None)
            decision_id = str(getattr(evidence, "decision_id", "") or "").strip()
            if not decision_id:
                _fail(FAILURE_AUTHORITY, "portfolio_decision_id")
            portfolio_slot = CurrentProductiveEnterLive29PPortfolioSlotContextV1(
                slot_id=lane_id,
                decision_id=decision_id,
                cycle_id=str(s7_base["cycle_id_prefix"]),
            )
        live_29p = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=replay,
            bound_instrument=bound,
            injected=live_29p_injected,
            decision_epoch=epoch,
            portfolio_budget_owner=portfolio_budget_owner,
            portfolio_slot=portfolio_slot,
            cycle_index=cycle_index,
            host_budget_recovery=host_budget_recovery,
        )
        live_29p_gen = (
            append_flight_record_stage_v1(
                stage="LIVE_29P_JOIN_OUTPUT",
                producer_symbol="join_current_productive_enter_live_29p_before_venue_plan_v1",
                consumer_symbol="try_bind_current_productive_venue_plan_v1",
                parent_generation_id=flight_parent,
                replay=live_29p.replay,
                extra={
                    "live_29p_status": str(live_29p.status),
                    "live_29p_first_blocker": str(live_29p.first_blocker or ""),
                    "sizing_outcome": str(live_29p.sizing_outcome),
                },
            )
            or flight_parent
        )
        if live_29p.replay is not None:
            persist_continuation_snapshot_v1(
                parent_generation_id=live_29p_gen,
                post_live_29p_replay=live_29p.replay,
                bound_instrument=bound,
                composed_epoch=epoch,
                session_id=str(s7_base["cycle_id_prefix"]),
                run_id_suffix=f"{s7_base['cycle_id_prefix']}:{next(iter(composed))}",
                synthetic_overlay_applied=bool(overlay.applied),
                live_29p_status=str(live_29p.status or ""),
                live_29p_first_blocker=str(live_29p.first_blocker or ""),
                venue_plan_input_generation_id=live_29p_gen,
            )
        # Classify from the post-overlay replay at the LIVE-29P join seam, not a stale
        # pre-overlay cycle_result snapshot or a rebound artifact that may lag overlay.
        decision_class = current_productive_decision_class_v1(replay)
        master_decision = str(
            getattr(getattr(replay, "evidence", None), "decision_outcome", "") or ""
        )
        if decision_class == DECISION_ENTER:
            if str(live_29p.status or "") != STATUS_PASS:
                result = SimpleNamespace(
                    runtime_cycle_count="1",
                    decision_result="OBSERVE_HOLD",
                    decision_execution_eligible=_FALSE,
                    master_v2_decision=master_decision or "enter",
                    venue_plan_status="DENY",
                    final_envelope_id="",
                    final_envelope_digest="",
                    permit_created=_FALSE,
                    post_count="0",
                    first_real_blocker=str(live_29p.first_blocker or "LIVE_29P_NOT_PASS"),
                    s7_invocation=invocation,
                )
                _dispatch.last_invocation = invocation  # type: ignore[attr-defined]
                return result
            venue_plan_replay = live_29p.replay
            if overlay.applied and venue_plan_replay is not None:
                from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
                    is_forensic_synthetic_enter_outcome_v1,
                    reapply_forensic_synthetic_safety_reprojection_on_replay_v1,
                )

                if is_forensic_synthetic_enter_outcome_v1(venue_plan_replay):
                    venue_plan_replay = reapply_forensic_synthetic_safety_reprojection_on_replay_v1(
                        venue_plan_replay,
                        parent_generation_id=live_29p_gen,
                    )
            append_flight_record_stage_v1(
                stage="VENUE_PLAN_INPUT",
                producer_symbol="reapply_forensic_synthetic_safety_reprojection_on_replay_v1",
                consumer_symbol="try_bind_current_productive_venue_plan_v1",
                parent_generation_id=live_29p_gen,
                replay=venue_plan_replay,
                extra={"venue_plan_input_generation_id": live_29p_gen},
            )
            status, _reasons, plan = try_bind_current_productive_venue_plan_v1(
                replay=venue_plan_replay,
                bound_instrument=bound,
                session_id=str(s7_base["cycle_id_prefix"]),
                run_id=f"{s7_base['cycle_id_prefix']}:{next(iter(composed))}",
                composed_epoch=epoch,
                execution_mode="LIVE",
            )
            venue_plan_pass = status is CompositionStatusV1.PASS and plan is not None
            quantity_assessment = None
            if venue_plan_pass:
                from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
                    assess_n1_final_plan_venue_quantity_v1,
                )

                quantity_assessment = assess_n1_final_plan_venue_quantity_v1(
                    observation=getattr(live_29p_injected, "venue_quantity_limits", None),
                    plan=plan,
                    bound_instrument=bound,
                    account_identity=str(
                        getattr(live_29p_injected, "expected_account_identity", "") or ""
                    ),
                    decision_epoch=epoch,
                    cycle_id=str(s7_base["cycle_id_prefix"]),
                )
                venue_plan_pass = quantity_assessment.allowed
            from src.ops.full_core_live_path_composition_root_v1.current_productive_forensic_executable_quantity_override_v1 import (
                active_forensic_executable_quantity_override_session_v1,
                refresh_forensic_executable_quantity_run_outcome_v1,
            )

            fq_session = active_forensic_executable_quantity_override_session_v1()
            if fq_session is not None:
                sizing_state = live_29p.replay.intermediate.capital_risk_sizing_decision
                policy_out = ""
                if sizing_state is not None:
                    policy_out = str(getattr(sizing_state.outcome, "value", sizing_state.outcome))
                refresh_forensic_executable_quantity_run_outcome_v1(
                    session=fq_session,
                    policy_outcome_after_override=policy_out,
                    venue_plan_status_after_override=str(status.value),
                    pre_external_reached=False,
                    post_count=0,
                    external_effect_count=0,
                )
            _finalize_portfolio_reservation_after_enter_join_v1(
                portfolio_budget_owner,
                reservation_id=live_29p.portfolio_reservation_id,
                enter_status=live_29p.status,
                venue_plan_pass=venue_plan_pass,
                venue_quantity_admission_denied=(
                    quantity_assessment is not None and not quantity_assessment.allowed
                ),
            )
            if venue_plan_pass:
                admission_ref = f"{s7_base['cycle_id_prefix']}:admission"
                if (
                    portfolio_budget_owner is not None
                    and portfolio_budget_owner.budget_state_v1().durable_state_enabled
                ):
                    admission_ref += f":portfolio-reservation:{live_29p.portfolio_reservation_id}"
                envelope = bind_final_order_envelope_from_venue_plan_v1(
                    plan,
                    admission_ref=admission_ref,
                    provenance_ref=f"{s7_base['cycle_id_prefix']}:provenance",
                    creation_epoch=epoch,
                )
                execution_plan_context = None
                if (
                    portfolio_budget_owner is not None
                    and portfolio_budget_owner.budget_state_v1().durable_state_enabled
                ):
                    portfolio_budget_owner.bind_execution_plan_v1(
                        live_29p.portfolio_reservation_id,
                        envelope,
                        canonical_intent=venue_plan_replay.intermediate.canonical_order_intent,
                        venue_plan=plan,
                        core_parent=venue_plan_replay.evidence,
                        core_cursor_root=Path(lane_pairs[lane_id][0].lane_state_root),
                        entry_frame_required=True,
                    )
                    execution_plan_context = portfolio_budget_owner.execution_plan_context_v1(
                        live_29p.portfolio_reservation_id, envelope
                    )
                result = SimpleNamespace(
                    runtime_cycle_count="1",
                    decision_result="EXECUTABLE_VENUE_PLAN_BOUND",
                    portfolio_reservation_id=live_29p.portfolio_reservation_id,
                    decision_execution_eligible=_TRUE,
                    master_v2_decision=master_decision or "enter",
                    venue_plan_status="BOUND",
                    final_envelope_id=str(envelope.envelope_id),
                    final_envelope_digest=str(envelope.envelope_digest),
                    final_order_envelope=envelope,
                    canonical_order_intent=venue_plan_replay.intermediate.canonical_order_intent,
                    execution_plan_context=execution_plan_context,
                    venue_quantity_limit_assessment=quantity_assessment.to_dict(),
                    permit_created=_FALSE,
                    post_count="0",
                    first_real_blocker="",
                    s7_invocation=invocation,
                )
                _dispatch.last_invocation = invocation  # type: ignore[attr-defined]
                return result
            result = SimpleNamespace(
                runtime_cycle_count="1",
                decision_result="OBSERVE_HOLD",
                portfolio_reservation_id=live_29p.portfolio_reservation_id,
                decision_execution_eligible=_FALSE,
                master_v2_decision=master_decision or "enter",
                venue_plan_status="DENY",
                final_envelope_id="",
                final_envelope_digest="",
                permit_created=_FALSE,
                post_count="0",
                first_real_blocker=(
                    quantity_assessment.reason_codes[0]
                    if quantity_assessment is not None
                    else "VENUE_PLAN_NOT_PASS"
                ),
                venue_quantity_limit_assessment=(
                    quantity_assessment.to_dict() if quantity_assessment is not None else None
                ),
                s7_invocation=invocation,
            )
            _dispatch.last_invocation = invocation  # type: ignore[attr-defined]
            return result
        result = SimpleNamespace(
            runtime_cycle_count="1",
            decision_result="OBSERVE_HOLD",
            decision_execution_eligible=_FALSE,
            master_v2_decision=master_decision or "observe",
            venue_plan_status="DENY",
            final_envelope_id="",
            final_envelope_digest="",
            permit_created=_FALSE,
            post_count="0",
            first_real_blocker="HOLD",
            s7_invocation=invocation,
        )
        _dispatch.last_invocation = invocation  # type: ignore[attr-defined]
        return result

    _dispatch.last_invocation = None  # type: ignore[attr-defined]
    _dispatch.last_position_management_quantity_handoff = None
    _dispatch.last_position_management_close_intent = None
    return _dispatch


def invoke_occupied_lane_governed_cycle_n1_consumer_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    *,
    origin_main_sha: str,
    cycle_id_prefix: str,
    observed_unix: float,
    mark_px: float,
    index_px: float,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    finalized_closes: Sequence[float],
    last_finalized_event_ts_unix: float,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    candles_payload: Mapping[str, Any] | None,
    candles_payload_by_lane: Mapping[str, Mapping[str, Any]] | None = None,
    observed_portfolio: PortfolioTruthSnapshotV1 | None = None,
    occupancy_payloads: Mapping[str, Any] | None = None,
    live_29p_injected: CurrentProductiveEnterLive29PInjectedGetV1 | None = None,
    live_29p_injected_by_lane: Mapping[str, CurrentProductiveEnterLive29PInjectedGetV1]
    | None = None,
    g17_typed_vol_producers: Mapping[str, object] | None = None,
    canonical_price_provenance: object | None = None,
    canonical_price_provenance_by_lane: Mapping[str, object] | None = None,
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
    host_budget_recovery: HostBudgetRecoveryContextV1 | None = None,
    position_episode_bindings: Mapping[str, PositionEpisodeBindingV1] | None = None,
    position_episode_scope: PositionEpisodeScopeV1 | None = None,
    rotation_exit_requests: Mapping[str, object] | None = None,
    common_epoch_decision_epoch: str | None = None,
    offline_governed_attempt: object | None = None,
    occupied_scope_mark_lane_id: str | None = None,
    authenticated_entry: AuthenticatedEntryEpisodeRequestV1 | None = None,
) -> dict[str, OccupiedLaneGovernedCycleN1ConsumerResultV1]:
    """Consume S8 roots and invoke the governed cycle once per occupied lane.

    EG is NON-V5. T2 is S7 compose of the already-bound instrument. Cap61
    remains unbound. Missing cursor bootstraps via S7 or follows existing
    fail-closed load semantics.
    """
    _assert_non_authority()
    from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
        BoundedSlotEntryBudgetV1,
    )

    bounded_slots = isinstance(
        portfolio_budget_owner.entry_budget_policy_v1()
        if portfolio_budget_owner is not None
        else None,
        BoundedSlotEntryBudgetV1,
    )
    if occupied_scope_mark_lane_id is not None and (
        occupied_scope_mark_lane_id not in composed_pairs
        or (
            authenticated_entry is None and (not bounded_slots or position_episode_bindings is None)
        )
        or rotation_exit_requests is not None
    ):
        _fail(FAILURE_AUTHORITY, "occupied_scope_mark_requires_bound_offline_lane")
    authenticated_admission = None
    if authenticated_entry is not None:
        from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
            AuthenticatedEntryEpisodeRequestV1,
            HostBudgetRecoveryContextV1,
        )
        from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
            POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
            build_productive_master_v2_reconciliation_admission_from_gate_v1,
        )
        from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
            run_productive_reconciliation_startup_gate_v1,
        )

        if (
            type(authenticated_entry) is not AuthenticatedEntryEpisodeRequestV1
            or type(host_budget_recovery) is not HostBudgetRecoveryContextV1
            or occupied_scope_mark_lane_id is None
            or len(composed_pairs) != 1
            or bounded_slots
            or offline_governed_attempt is not None
            or position_episode_bindings is not None
            or position_episode_scope is not None
            or observed_portfolio is not None
            or occupancy_payloads is not None
        ):
            _fail(FAILURE_AUTHORITY, "authenticated_scope_mark_requires_original_n1_host")
        host = host_budget_recovery.host
        pair = composed_pairs[occupied_scope_mark_lane_id]
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or not isinstance(pair[1], BoundInstrumentV1)
        ):
            _fail(FAILURE_PAIR_TYPE, occupied_scope_mark_lane_id)
        bound = pair[1]
        if (
            host.closed
            or host.owner is None
            or host.owner is not portfolio_budget_owner
            or host.execution_environment != "LIVE"
            or host.bindings != {occupied_scope_mark_lane_id: bound}
            or not 0
            <= host.clock() - observed_unix
            <= POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS / 1000
        ):
            _fail(FAILURE_AUTHORITY, "authenticated_scope_mark_requires_original_n1_host")
        observed_portfolio = host_budget_recovery.observed
        occupancy_payloads = host_budget_recovery.occupancy_payloads
        config_rows = occupancy_payloads.get("CONFIG", {}).get("data", [])
        if len(config_rows) != 1 or config_rows[0].get("posMode") != "net_mode":
            _fail(FAILURE_AUTHORITY, "FULL_CLOSE_NET_POSITION_MODE_REQUIRED")
        close_input = (
            live_29p_injected_by_lane.get(occupied_scope_mark_lane_id)
            if live_29p_injected_by_lane is not None
            else live_29p_injected
        )
        if (
            not isinstance(close_input, CurrentProductiveEnterLive29PInjectedGetV1)
            or close_input.instruments_payload is None
            or not produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
                venue_native_id=bound.venue_native_id,
                bound_instrument_id=bound.instrument_id,
                instruments_payload=close_input.instruments_payload,
                observed_at_as_of=close_input.observed_at,
            ).produced
        ):
            _fail(FAILURE_AUTHORITY, "authenticated_scope_mark_close_metadata_required")
        try:
            episode = host_budget_recovery.bind_current_authenticated_entry_episode_v1(
                lane_id=occupied_scope_mark_lane_id,
                proof_root=authenticated_entry.proof_root,
                proof=authenticated_entry.proof,
                config_digest=_occupied_scope_exit_config_digest_v1(),
            )
            gate = run_productive_reconciliation_startup_gate_v1(
                state_root=host.root / "reconciliation",
                observed=observed_portfolio,
                session_id=host.session_id,
                repository_sha=host.repository_sha,
                now_unix=host.clock(),
                require_persisted_present=True,
            )
            authenticated_admission = (
                build_productive_master_v2_reconciliation_admission_from_gate_v1(
                    gate=gate,
                    session_id=host.session_id,
                    repository_sha=host.repository_sha,
                    bound_instrument_id=bound.instrument_id,
                )
            )
            authenticated_admission.validate_for_productive_master_v2_entry_v1(
                instrument_id=bound.instrument_id
            )
        except (OSError, ValueError) as exc:
            _fail(FAILURE_AUTHORITY, str(exc))
        position_episode_bindings = {occupied_scope_mark_lane_id: episode}
        position_episode_scope = episode.identity.account_scope
    if bounded_slots:
        from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
            HostBudgetRecoveryContextV1,
        )

        if (
            not isinstance(host_budget_recovery, HostBudgetRecoveryContextV1)
            or host_budget_recovery.host.closed
            or host_budget_recovery.host.owner is not portfolio_budget_owner
            or host_budget_recovery.host.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            or offline_governed_attempt is not None
            or live_29p_injected_by_lane is None
        ):
            _fail(FAILURE_AUTHORITY, "bounded_slots_original_simulated_host_required")
    if live_29p_injected_by_lane is not None:
        if live_29p_injected is not None:
            _fail(FAILURE_AUTHORITY, "dual_live_29p_inputs_forbidden")
        if set(live_29p_injected_by_lane) != set(composed_pairs):
            _fail(FAILURE_AUTHORITY, "live_29p_lane_set_mismatch")
        if any(
            not isinstance(value, CurrentProductiveEnterLive29PInjectedGetV1)
            for value in live_29p_injected_by_lane.values()
        ):
            _fail(FAILURE_AUTHORITY, "live_29p_lane_input_type")
    if position_episode_bindings is not None:
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            PositionEpisodeScopeV1,
        )

        if host_budget_recovery is not None:
            if (
                host_budget_recovery.host.closed
                or host_budget_recovery.host.owner is not portfolio_budget_owner
            ):
                _fail(FAILURE_AUTHORITY, "position_episode_budget_host_unbound")
            host_scope = PositionEpisodeScopeV1(
                host_budget_recovery.account, host_budget_recovery.host.execution_environment
            )
            if position_episode_scope is None:
                position_episode_scope = host_scope
            elif position_episode_scope != host_scope:
                _fail(FAILURE_AUTHORITY, "position_episode_host_account_scope_mismatch")
        if not isinstance(position_episode_scope, PositionEpisodeScopeV1):
            _fail(FAILURE_AUTHORITY, "position_episode_account_scope_required")
        position_episode_scope.validate_v1()
    if not str(origin_main_sha or "").strip():
        _fail(FAILURE_ORIGIN_MAIN_SHA, OWNER)
    if candles_payload is None and candles_payload_by_lane is None:
        _fail(FAILURE_INJECTED_C1_REQUIRED, OWNER)
    if canonical_price_provenance_by_lane is not None and canonical_price_provenance is not None:
        _fail(FAILURE_AUTHORITY, "dual_canonical_price_provenance_forbidden")
    if canonical_price_provenance_by_lane is None and canonical_price_provenance is None:
        _fail(FAILURE_AUTHORITY, "canonical_price_provenance")
    prefix = str(cycle_id_prefix or "").strip()
    if not prefix:
        _fail(FAILURE_AUTHORITY, "cycle_id_prefix")
    unknown = sorted(set(composed_pairs) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))
    if position_episode_bindings is not None and set(position_episode_bindings) - set(
        composed_pairs
    ):
        _fail(FAILURE_AUTHORITY, "foreign_position_episode_lane")
    for lane_id, pair in composed_pairs.items():
        if not isinstance(pair, tuple) or len(pair) != 2:
            _fail(FAILURE_PAIR_TYPE, lane_id)
        slot, bound = pair
        if not isinstance(slot, IsolatedLaneSlotV1) or not isinstance(bound, BoundInstrumentV1):
            _fail(FAILURE_PAIR_TYPE, lane_id)
        if slot.occupancy != OCCUPANCY_OCCUPIED:
            _fail(FAILURE_OCCUPANCY, lane_id)
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(composed_pairs)
    if bounded_slots or authenticated_entry is not None:
        # Keep the original cursor and exclusion lock; each attempt owns its ledger.
        addressed = {
            lane: (
                cursor,
                lock,
                str(
                    _occupied_attempt_root_v1(
                        evidence, prefix=prefix, authenticated=not bounded_slots
                    )
                ),
            )
            for lane, (cursor, lock, evidence) in addressed.items()
        }
    if offline_governed_attempt is not None:
        from src.ops.bounded_peaktrade_system_composition_v1.governed_attempt_v1 import (
            OfflineGovernedAttemptV1,
        )

        if not isinstance(offline_governed_attempt, OfflineGovernedAttemptV1):
            _fail(FAILURE_AUTHORITY, "offline_governed_attempt_invalid")
        addressed = offline_governed_attempt.bind_roots_v1(
            addressed,
            prefix=prefix,
            scope=position_episode_scope,
            episodes=position_episode_bindings,
            origin_main_sha=origin_main_sha,
            observed_unix=observed_unix,
            last_finalized_event_ts_unix=last_finalized_event_ts_unix,
        )
    occupancy = dict(occupancy_payloads) if occupancy_payloads is not None else _occupancy_absent()
    try:
        per_lane_ingress, _ownership = compose_per_lane_n5_identity_closure_v1(
            composed_pairs,
            candles_payload=candles_payload,
            candles_payload_by_lane=candles_payload_by_lane,
            occupancy_payloads=occupancy,
            observed_portfolio=observed_portfolio,
            venue_flat=venue_flat,
            existing_position_side=existing_position_side,
            last_finalized_event_ts_unix=last_finalized_event_ts_unix,
            finalized_closes=tuple(finalized_closes),
            isolate_known_lane_positions=bounded_slots,
        )
    except InstrumentRuntimeIdentityClosureError as exc:
        if bounded_slots:
            try:
                portfolio_budget_owner.close()
            except Exception as cleanup_error:
                raise exc from cleanup_error
        _fail(exc.failure_code, exc.detail)
    if position_episode_bindings is not None:
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            PositionEpisodeBindingV1,
        )

        # Reject an incompatible episode before consuming a governed-cycle token.
        for lane_id, ingress in per_lane_ingress.items():
            if occupied_scope_mark_lane_id is not None and lane_id != occupied_scope_mark_lane_id:
                continue
            episode = position_episode_bindings.get(lane_id)
            if episode is None:
                if not ingress.position.venue_flat:
                    _fail(FAILURE_AUTHORITY, "position_episode_missing:" + lane_id)
                continue
            if not isinstance(episode, PositionEpisodeBindingV1):
                _fail(FAILURE_AUTHORITY, "position_episode_binding_invalid:" + lane_id)
            try:
                episode_event_unix = float(ingress.last_finalized_event_ts_unix)
                if lane_id == occupied_scope_mark_lane_id:
                    mark = (
                        canonical_price_provenance_by_lane.get(lane_id)
                        if canonical_price_provenance_by_lane is not None
                        else canonical_price_provenance
                    )
                    episode_event_unix = mark.require_current_mark_clock_v1(
                        observed_unix=observed_unix
                    )
                episode.prepare_for_cycle_v1(
                    instrument_id=str(composed_pairs[lane_id][1].instrument_id),
                    venue_native_id=str(composed_pairs[lane_id][1].venue_native_id),
                    position_side=str(ingress.position.existing_position_side.value),
                    venue_flat=ingress.position.venue_flat,
                    event_time=episode_event_unix,
                    lane_id=lane_id,
                    expected_scope=position_episode_scope,
                )
                from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
                    require_simulated_accounting_quantity_v1,
                )

                require_simulated_accounting_quantity_v1(
                    episode=episode,
                    observation=ingress.position.quantity_observation,
                )
                from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
                    require_current_cursor_continuity_v1,
                )
                from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
                    load_current_productive_sidestate_confirmation_cursor_v1,
                )

                cursor_root = Path(composed_pairs[lane_id][0].lane_state_root)
                require_current_cursor_continuity_v1(
                    episode=episode,
                    incoming=load_current_productive_sidestate_confirmation_cursor_v1(cursor_root),
                    store_root=cursor_root,
                )
            except (AttributeError, ValueError) as exc:
                _fail(FAILURE_AUTHORITY, str(exc))
    base_mark_px = mark_px
    base_index_px = index_px
    base_provenance: object | None = canonical_price_provenance
    if canonical_price_provenance_by_lane is not None:
        first_lane = next(iter(composed_pairs))
        base_provenance = canonical_price_provenance_by_lane.get(first_lane)
        if base_provenance is None:
            _fail(FAILURE_AUTHORITY, f"canonical_price_provenance_by_lane:{first_lane}")
        base_mark_px = float(getattr(base_provenance, "mark_px", mark_px))
        base_index_px = float(getattr(base_provenance, "index_px", index_px))
    if base_provenance is None:
        _fail(FAILURE_AUTHORITY, "canonical_price_provenance")
    s7_base = _s7_kwargs(
        cycle_id_prefix=prefix,
        observed_unix=observed_unix,
        mark_px=base_mark_px,
        index_px=base_index_px,
        bid_px=bid_px,
        ask_px=ask_px,
        volume=volume,
        open_interest=open_interest,
        funding_rate=funding_rate,
        finalized_closes=finalized_closes,
        last_finalized_event_ts_unix=last_finalized_event_ts_unix,
        venue_flat=venue_flat,
        existing_position_side=existing_position_side,
        g17_typed_vol_producers=g17_typed_vol_producers,
        canonical_price_provenance=base_provenance,
    )
    results: dict[str, OccupiedLaneGovernedCycleN1ConsumerResultV1] = {}
    lane_order = list(LANE_IDS)
    if rotation_exit_requests is not None or (
        bounded_slots
        and portfolio_budget_owner.entry_budget_policy_v1().enforce_open_slot_loss_protection
    ):
        lane_order.sort(
            key=lambda lane: (
                per_lane_ingress[lane].position.venue_flat if lane in per_lane_ingress else True,
                LANE_IDS.index(lane),
            )
        )
    for lane_id in lane_order:
        if occupied_scope_mark_lane_id is not None and lane_id != occupied_scope_mark_lane_id:
            continue
        pair = composed_pairs.get(lane_id)
        if pair is None:
            continue
        roots = addressed.get(lane_id)
        if roots is None:
            _fail(FAILURE_S8_ROOTS_MISSING, lane_id)
        cursor_store_root, lock_root, evidence_root = roots
        _slot, bound = pair
        lane_29p = (
            live_29p_injected_by_lane[lane_id]
            if live_29p_injected_by_lane is not None
            else live_29p_injected
        )
        native_id = str(bound.venue_native_id or "").strip()
        if not native_id:
            _fail(FAILURE_NATIVE_ID_MISSING, lane_id)
        lane_pairs = {lane_id: pair}
        ingress = per_lane_ingress[lane_id]
        try:
            ensure_lane_generation_safe_v1(
                lane_state_root=Path(cursor_store_root),
                identity=ingress.identity,
            )
            assert_cursor_matches_identity_or_absent_v1(
                cursor_store_root=Path(cursor_store_root),
                identity=ingress.identity,
            )
        except LaneGenerationError as exc:
            _fail(exc.failure_code, exc.detail)
        lane_s7 = dict(s7_base)
        if rotation_exit_requests is not None:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_rotation_close_v1 import (
                bind_rotation_close_slot_scope_v1,
            )

            request = rotation_exit_requests.get(lane_id)
            try:
                request = bind_rotation_close_slot_scope_v1(
                    request,
                    bindings=(
                        host_budget_recovery.host.bindings
                        if host_budget_recovery is not None
                        else {l: b for l, (_, b) in composed_pairs.items()}
                    ),
                )
            except (ValueError, TypeError, KeyError, AttributeError):
                # An invalid new rotation source cannot suppress other exits.
                request = None
            lane_s7["rotation_exit_requests"] = {} if request is None else {lane_id: request}
        lane_s7["finalized_closes"] = ingress.finalized_closes
        lane_s7["last_finalized_event_ts_unix"] = ingress.last_finalized_event_ts_unix
        lane_s7["venue_flat"] = ingress.position.venue_flat
        lane_s7["existing_position_side"] = ingress.position.existing_position_side
        if position_episode_bindings is not None:
            episode = position_episode_bindings.get(lane_id)
            if episode is None and not ingress.position.venue_flat:
                _fail(FAILURE_AUTHORITY, "position_episode_missing:" + lane_id)
            lane_s7["position_episode_bindings"] = {} if episode is None else {lane_id: episode}
            lane_s7["position_episode_scope"] = position_episode_scope
        lane_s7["master_v2_reconciliation_admission"] = (
            authenticated_admission
            or build_master_v2_reconciliation_admission_for_lane_v1(
                identity=ingress.identity,
                per_lane=ingress.reconciliation,
                session_id=prefix,
                repository_sha=str(origin_main_sha),
                portfolio=observed_portfolio,
            )
        )
        lane_candles = dict(ingress.candles_payload)
        lane_occupancy = occupancy
        if bounded_slots:
            positions = occupancy.get("POSITIONS", {})
            lane_occupancy = {
                **occupancy,
                "POSITIONS": {
                    **positions,
                    "data": [
                        row
                        for row in positions.get("data", [])
                        if str(row.get("instId") or "").strip() == native_id
                    ],
                },
            }
        if canonical_price_provenance_by_lane is not None:
            lane_prov = canonical_price_provenance_by_lane.get(lane_id)
            if lane_prov is None:
                _fail(FAILURE_AUTHORITY, f"canonical_price_provenance_by_lane:{lane_id}")
            lane_s7["canonical_price_provenance"] = lane_prov
            lane_s7["mark_px"] = float(getattr(lane_prov, "mark_px", lane_s7["mark_px"]))
            lane_s7["index_px"] = float(getattr(lane_prov, "index_px", lane_s7["index_px"]))
        occupied_mark_event = None
        if lane_id == occupied_scope_mark_lane_id:
            if ingress.position.venue_flat or lane_id not in position_episode_bindings:
                _fail(FAILURE_AUTHORITY, "occupied_scope_mark_position_required")
            try:
                occupied_mark_event = lane_s7[
                    "canonical_price_provenance"
                ].require_current_mark_clock_v1(observed_unix=observed_unix)
            except (AttributeError, ValueError) as exc:
                _fail(FAILURE_AUTHORITY, str(exc))
            lane_s7["occupied_scope_mark"] = True
        loss_protection_status = "NOT_APPLICABLE"
        loss_protection_reasons = ()
        if (
            bounded_slots
            and portfolio_budget_owner.entry_budget_policy_v1().enforce_open_slot_loss_protection
            and not ingress.position.venue_flat
        ):
            from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
                PortfolioCapitalBudgetError,
            )
            from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
                MonetaryNormalizationError,
            )

            episode = (
                None
                if position_episode_bindings is None
                else position_episode_bindings.get(lane_id)
            )
            try:
                loss_request = portfolio_budget_owner.observe_open_slot_loss_v1(
                    slot_id=lane_id,
                    episode=episode,
                    observation=None if lane_29p is None else lane_29p.open_slot_loss_observation,
                    mark_px=lane_s7["mark_px"],
                    observed_unix=observed_unix,
                )
                loss_protection_status = "OBSERVED_PROTECTION_ONLY"
            except PortfolioCapitalBudgetError:
                raise
            except (
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
                ArithmeticError,
                MonetaryNormalizationError,
            ) as exc:
                # Missing valuation cannot invent a loss or suppress an
                # original exit; an already durable close trigger survives.
                loss_request = portfolio_budget_owner.pending_open_slot_loss_exit_v1(lane_id)
                loss_protection_status = "UNPROVEN_ORIGINAL_EXITS_RETAINED"
                loss_protection_reasons = (str(exc),)
            lane_s7["slot_loss_exit_requests"] = (
                {} if loss_request is None else {lane_id: loss_request}
            )
        if g17_typed_vol_producers is not None:
            if lane_id not in g17_typed_vol_producers:
                _fail(FAILURE_S8_ROOTS_MISSING, f"g17:{lane_id}")
            lane_s7["g17_typed_vol_producers"] = {lane_id: g17_typed_vol_producers[lane_id]}
        cursor_path = Path(cursor_store_root) / CURSOR_FILENAME
        bootstrap_used = False
        if not cursor_path.is_file():
            if occupied_mark_event is not None:
                _fail(FAILURE_AUTHORITY, "occupied_scope_mark_cursor_required")
            lane_s7 = _align_lane_s7_closes_to_injected_c1_v1(
                lane_s7,
                lane_candles,
            )
            compose_occupied_lane_mv2_dp_durable_cycle_v1(lane_pairs, **lane_s7)
            bootstrap_used = True
        expected_floor = _cursor_floor_or_zero(Path(cursor_store_root))
        t2_dispatch = _t2_from_s7(
            lane_pairs=lane_pairs,
            native_id=native_id,
            lane_id=lane_id,
            s7_base={**lane_s7, "cycle_id_prefix": f"{prefix}:{lane_id}"},
            live_29p_injected=lane_29p,
            candles_payload=lane_candles,
            portfolio_budget_owner=portfolio_budget_owner,
            common_epoch_decision_epoch=common_epoch_decision_epoch,
            host_budget_recovery=host_budget_recovery,
            position_management_only=not ingress.position.venue_flat,
            position_management_ingress=ingress,
            position_management_config_payload=(occupancy_payloads or {}).get("CONFIG"),
            offline_observation_clock_unix=(
                observed_unix
                if offline_governed_attempt is not None
                or (occupied_mark_event is not None and authenticated_entry is None)
                else None
            ),
        )
        from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_binding_v1 import (
            FullCoreCapitalGuardHandoffContextV1,
            bind_full_core_capital_guard_handoff_context_v1,
            extract_instrument_contract_metadata_v1,
            reset_full_core_capital_guard_handoff_context_v1,
        )

        handoff_meta = None
        if lane_29p is not None and lane_29p.instruments_payload is not None:
            try:
                handoff_meta = extract_instrument_contract_metadata_v1(
                    lane_29p.instruments_payload,
                    instrument_id=str(bound.venue_native_id or native_id),
                )
            except Exception:
                handoff_meta = None
        handoff_ctx_reset = bind_full_core_capital_guard_handoff_context_v1(
            FullCoreCapitalGuardHandoffContextV1(
                bound_instrument=bound,
                canonical_decision_id=str(common_epoch_decision_epoch or ""),
                account_identity=str(
                    getattr(lane_29p, "expected_account_identity", "")
                    or "REUSED_BINDING_ACCOUNT_SCOPE"
                ),
                environment="PRODUCTIVE_READ_ONLY",
                origin_main_sha=str(origin_main_sha),
                instrument_metadata=handoff_meta,
                reference_mark_px=str(lane_s7.get("mark_px") or ""),
            )
        )
        try:
            cycle_result = run_current_productive_governed_cycle_v1(
                authorization=CurrentProductiveGovernedCycleAuthorizationV1(
                    cycle_owner_go=RUNTIME_OWNER_GO,
                    get_owner_go=GET_OWNER_GO,
                    eg_owner_go=EG_OWNER_GO,
                    occupancy_owner_go=OCCUPANCY_OWNER_GO,
                    t2_owner_go=T2_RUNTIME_OWNER_GO,
                    native_id=native_id,
                    bar="1m",
                    expected_cursor_floor=expected_floor,
                ),
                origin_main_sha=origin_main_sha,
                cursor_store_root=Path(cursor_store_root),
                lock_root=Path(lock_root),
                evidence_root=Path(evidence_root),
                candles_payload=lane_candles,
                occupancy_payloads=lane_occupancy,
                execute_network=False,
                perform_get=False,
                eg_cycle_dispatch=non_v5_eg_dispatch_v1,
                t2_cycle_dispatch=t2_dispatch,
                position_management_cycle_dispatch=(
                    t2_dispatch if not ingress.position.venue_flat else None
                ),
                occupied_scope_mark_event_unix=occupied_mark_event,
            )
        finally:
            reset_full_core_capital_guard_handoff_context_v1(handoff_ctx_reset)
        s7_invocation = getattr(t2_dispatch, "last_invocation", None)
        if cycle_result.disposition in {
            DISPOSITION_PRE_EXTERNAL_EFFECT,
            DISPOSITION_HOLD,
            "COMPLETED",
        }:
            if s7_invocation is None:
                _fail(FAILURE_AUTHORITY, "t2_s7_missing")
            if str(s7_invocation.bound_instrument.venue_native_id or "").strip() != native_id:
                _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
            if s7_invocation.cap61_state_root_bound is not False:
                _fail(FAILURE_AUTHORITY, "cap61_bound")
        if int(cycle_result.post_count) != 0 or cycle_result.permit_created is not False:
            _fail(FAILURE_AUTHORITY, "external_effect")
        results[lane_id] = OccupiedLaneGovernedCycleN1ConsumerResultV1(
            lane_id=lane_id,
            bound_instrument=bound,
            native_id=native_id,
            cursor_store_root=cursor_store_root,
            lock_root=lock_root,
            evidence_root=evidence_root,
            bootstrap_used=bootstrap_used,
            s7_invocation=s7_invocation,
            governed_cycle_result=cycle_result,
            eg_v5_used=False,
            t2_s7_used=True,
            cap61_state_root_bound=False,
            position_management_quantity_handoff=getattr(
                t2_dispatch, "last_position_management_quantity_handoff", None
            ),
            position_management_close_intent=getattr(
                t2_dispatch, "last_position_management_close_intent", None
            ),
            slot_loss_protection_status=loss_protection_status,
            slot_loss_protection_reason_codes=loss_protection_reasons,
        )
    return results
