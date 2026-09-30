"""Offline inject harness for N=1 standing PRE_EXTERNAL runtime supervisor (WP-01)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.governance.current_productive_activation_policy_v1 import (
    RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    GovernedF1M9ThresholdConsumerWiringRequestV1,
    run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    ScriptedContinuousObservationSourceV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
    TRANSPORT_SCOPE_OFFLINE_INJECT,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorConfigV1,
    StandingSupervisorRunResultV1,
    run_n1_standing_pre_external_supervisor_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
)
from tests.governance.test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    _bound_context,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_productive_c1_event_ts_unix_v1,
    strong_uptrend_closes_v1,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _continuous_auth,
    _cursor_floor_or_zero,
    _lane_g17,
    _observation_from_closes,
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _bound_lane_1,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _FakeClock,
)
from tests.ops.test_okx_eea_private_account_state_runtime_v1 import _fixture_rest
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _valid_estimate,
)

# Owner-GO decision pins this baseline; descendant SHAs fail immutable-surface drift check.
OWNER_GO_BASELINE_SHA = "7a3597e61966749a9e30d06f3514e23a9179fb9e"
BASE_TS = 1_757_631_540_000


def public_rest_empty(_path: str, _query: dict[str, str]) -> dict[str, Any]:
    return {"code": "0", "data": []}


def seed_public_marks(store_root: Path, *, n: int = MINIMUM_FINALIZED_PT1M_MARKS) -> None:
    paths = default_store_paths_v1(store_root)
    for i in range(n):
        append_fact_v1(
            paths,
            {
                "fact_kind": "FinalizedPt1mMarkFactV1",
                "interval_start_ms": BASE_TS + i * PT1M_STEP_MS,
                "mark_px": str(100 + i),
                "confirm": "1",
                "captured_at": "2026-09-26T00:00:00Z",
                "instrument": {"venue_native_id": "ETH-USDT-SWAP"},
            },
        )


def f1_m9_evaluator_factory(*, repo_root: Path, ledger_root: Path):
    apply_rev = ledger_root / "apply_rev.jsonl"
    threshold_rev = ledger_root / "threshold_rev.jsonl"
    initialize_empty_revocation_ledger_v1(apply_rev)
    initialize_empty_threshold_revocation_ledger_v1(threshold_rev)
    continuation = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
        GovernedF1M9ThresholdConsumerWiringRequestV1(
            apply_ledger_paths=F1M9ProductiveApplyLedgerPathsV1(
                apply_ledger_path=ledger_root / "apply.jsonl",
                revocation_ledger_path=apply_rev,
            ),
            threshold_ledger_paths=F1M9ThresholdValueAuthorizationLedgerPathsV1(
                threshold_ledger_path=ledger_root / "threshold.jsonl",
                threshold_revocation_ledger_path=threshold_rev,
            ),
            repo_root=repo_root,
        )
    )
    assert continuation.bound_seam_record is not None
    ctx, elig = _bound_context(_valid_estimate())

    def _eval(_cycle_index: int):
        return evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
            market_context=ctx,
            eligibility=elig,
            governed_seam_record=continuation.bound_seam_record,
            require_governed_seam=True,
            runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
            repo_root=repo_root,
        )

    return _eval


def bootstrap_lane(*, session_root: Path, repo_root: Path) -> tuple[Any, Any, Any, str]:
    bound = _bound_lane_1()
    native_id = str(bound.venue_native_id)
    lane_state = session_root / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_state, bound=bound)
    g17 = _lane_g17(pairs)
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    obs_boot = _observation_from_closes(closes=path[:14], event_ts=t0 - 60.0)
    bootstrap_s8_lane_via_s7_compose_v1(
        composed_pairs=pairs,
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        g17_producers=g17,
        candles_payload=obs_boot.candles_payload,
        mark_price_payload=obs_boot.mark_price_payload,
        venue_native_id=native_id,
        index_tickers_payload=obs_boot.index_tickers_payload,
    )
    return bound, g17, pairs, native_id


def supervisor_config_from_roots(
    *,
    public_store: Path,
    private_store: Path,
    lane_state: Path,
    evidence_root: Path,
    lock_root: Path | None = None,
) -> StandingSupervisorConfigV1:
    return StandingSupervisorConfigV1(
        public_store_root=public_store,
        private_store_root=private_store,
        lane_state_root=lane_state,
        evidence_root=evidence_root,
        lock_root=lock_root,
        transport_scope=TRANSPORT_SCOPE_OFFLINE_INJECT,
    )


def run_offline_inject_supervisor_session_v1(
    *,
    repo_root: Path,
    session_root: Path,
    origin_main_sha: str = OWNER_GO_BASELINE_SHA,
    max_cycles: int = 2,
    skip_owner_go_validation: bool = False,
) -> StandingSupervisorRunResultV1:
    public_store = session_root / "public_store"
    private_store = session_root / "private_store"
    session_root.mkdir(parents=True, exist_ok=True)
    seed_public_marks(public_store)
    bound, g17, pairs, native_id = bootstrap_lane(session_root=session_root, repo_root=repo_root)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    path = strong_uptrend_closes_v1()
    auth = _continuous_auth(native_id=native_id, max_cycles=max_cycles)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=max_cycles,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=0.001 if max_cycles > 1 else auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=30.0 if max_cycles > 1 else auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    if max_cycles >= 2:
        obs = ScriptedContinuousObservationSourceV1(
            [
                _observation_from_closes(closes=path[:16], event_ts=t0),
                None,
                _observation_from_closes(closes=path[:18], event_ts=t1),
            ]
        )
    else:
        obs = ScriptedContinuousObservationSourceV1(
            [_observation_from_closes(closes=path[:16], event_ts=t0)]
        )
    cfg = supervisor_config_from_roots(
        public_store=public_store,
        private_store=private_store,
        lane_state=session_root / "lane_state",
        evidence_root=session_root / "evidence",
        lock_root=session_root / "lock",
    )
    ledger_root = session_root / "f1_m9_ledgers"
    return run_n1_standing_pre_external_supervisor_v1(
        config=cfg,
        origin_main_sha=origin_main_sha,
        bound=bound,
        authorization=auth,
        observation_source=obs,
        g17_producers=g17,
        f1_m9_cycle_evaluator=f1_m9_evaluator_factory(repo_root=repo_root, ledger_root=ledger_root),
        repo_root=repo_root,
        public_rest_fetch=public_rest_empty,
        private_rest_fetch=_fixture_rest,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
        skip_owner_go_validation=skip_owner_go_validation,
    )
