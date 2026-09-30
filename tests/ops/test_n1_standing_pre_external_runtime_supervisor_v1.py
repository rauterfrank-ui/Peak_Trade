"""CURRENT-WP-01: standing N=1 PRE_EXTERNAL runtime supervisor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

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
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
    DISPOSITION_MAX_CYCLES,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    ScriptedContinuousObservationSourceV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.errors_v1 import (
    StandingSupervisorError,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.evidence_v1 import (
    write_standing_supervisor_closure_evidence_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorConfigV1,
    assert_supervisor_authority_boundary_v1,
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
    NATIVE_ID,
    _bound_lane_1,
    _continuous_auth,
    _cursor_floor_or_zero,
    _observation_from_closes,
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
)
from tests.ops.test_okx_eea_private_account_state_runtime_v1 import _fixture_rest
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _lane_g17,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    C1_A,
    _FakeClock,
    _obs,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _valid_estimate,
)

REPO = Path(__file__).resolve().parents[2]
# Owner-GO decision pins this baseline; descendant SHAs fail immutable-surface drift check.
OWNER_GO_BASELINE_SHA = "7a3597e61966749a9e30d06f3514e23a9179fb9e"
BASE_TS = 1_757_631_540_000


def _seed_public_marks(store_root: Path, *, n: int = MINIMUM_FINALIZED_PT1M_MARKS) -> None:
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


def _public_rest_empty(_path: str, _query: dict[str, str]) -> dict[str, Any]:
    return {"code": "0", "data": []}


def _f1_m9_evaluator_factory(tmp_path: Path):
    apply_rev = tmp_path / "apply_rev.jsonl"
    threshold_rev = tmp_path / "threshold_rev.jsonl"
    initialize_empty_revocation_ledger_v1(apply_rev)
    initialize_empty_threshold_revocation_ledger_v1(threshold_rev)
    continuation = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
        GovernedF1M9ThresholdConsumerWiringRequestV1(
            apply_ledger_paths=F1M9ProductiveApplyLedgerPathsV1(
                apply_ledger_path=tmp_path / "apply.jsonl",
                revocation_ledger_path=apply_rev,
            ),
            threshold_ledger_paths=F1M9ThresholdValueAuthorizationLedgerPathsV1(
                threshold_ledger_path=tmp_path / "threshold.jsonl",
                threshold_revocation_ledger_path=threshold_rev,
            ),
            repo_root=REPO,
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
            repo_root=REPO,
        )

    return _eval


def _bootstrap_lane(tmp_path: Path) -> tuple[Any, Any, Any, str]:
    bound = _bound_lane_1()
    native_id = str(bound.venue_native_id)
    lane_state = tmp_path / "lane_state"
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


def _supervisor_config(tmp_path: Path) -> StandingSupervisorConfigV1:
    return StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public_store",
        private_store_root=tmp_path / "private_store",
        lane_state_root=tmp_path / "lane_state",
        evidence_root=tmp_path / "evidence",
        lock_root=tmp_path / "lock",
    )


def test_authority_boundary_and_pins() -> None:
    assert_supervisor_authority_boundary_v1()
    assert CONTINUOUS_RUN_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_t_plus_01_supervisor_single_cycle(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    obs = ScriptedContinuousObservationSourceV1(
        [_observation_from_closes(closes=path[:16], event_ts=t0)]
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=obs,
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
        public_ws_messages=[],
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result.ok is True
    assert result.trace.governed_cycle_count >= 1
    assert result.trace.accepted_c1_count == result.trace.governed_cycle_count
    assert result.trace.post_count == 0
    assert result.owner_go_consumed is True
    assert result.trace.recovery_completed is True
    assert result.trace.public_supply_refreshed is True
    assert result.trace.public_marks_count >= MINIMUM_FINALIZED_PT1M_MARKS


def test_t_plus_02_two_distinct_c1_epochs(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    path = strong_uptrend_closes_v1()
    auth = _continuous_auth(native_id=native_id, max_cycles=2)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=2,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=0.001,
        max_wait_for_next_c1_seconds=30.0,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    obs = ScriptedContinuousObservationSourceV1(
        [
            _observation_from_closes(closes=path[:16], event_ts=t0),
            None,
            _observation_from_closes(closes=path[:18], event_ts=t1),
        ]
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=obs,
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result.trace.governed_cycle_count == 2
    assert result.trace.accepted_c1_count == 2
    assert result.policy_result is not None
    assert result.policy_result.orchestrator_result.disposition == DISPOSITION_MAX_CYCLES


def test_t_plus_03_terminal_dispositions_safe(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor) if floor else 0.0,
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    obs = ScriptedContinuousObservationSourceV1(
        [_observation_from_closes(closes=path[:16], event_ts=t0)]
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=obs,
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
    )
    disp = result.trace.terminal_disposition
    assert disp in {
        DISPOSITION_MAX_CYCLES,
        "DISPOSITION_HOLD",
        "DISPOSITION_HOLD_CONTINUE",
        "DISPOSITION_PRE_EXTERNAL_EFFECT",
        "DISPOSITION_FAIL_CLOSED",
    }


def test_t_plus_04_post_flags_false(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=ScriptedContinuousObservationSourceV1(
            [_observation_from_closes(closes=path[:16], event_ts=t0)]
        ),
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
    )
    assert result.policy_result is not None
    assert result.policy_result.post_allowed is False
    assert result.policy_result.external_effect_authorized is False
    assert result.trace.post_count == 0


def test_t_plus_06_recovery_before_continuous_on_restart_flag(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    cfg = _supervisor_config(tmp_path)
    cfg = StandingSupervisorConfigV1(
        public_store_root=cfg.public_store_root,
        private_store_root=cfg.private_store_root,
        lane_state_root=cfg.lane_state_root,
        evidence_root=cfg.evidence_root,
        lock_root=cfg.lock_root,
        simulate_restart_before_continuous=True,
    )
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=cfg,
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=ScriptedContinuousObservationSourceV1(
            [_observation_from_closes(closes=path[:16], event_ts=t0)]
        ),
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
    )
    assert result.trace.extra.get("recovery_restart_before_continuous") is True


def test_t_minus_01_missing_owner_go_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1."
        "validate_bounded_continuous_run_owner_go_decision_v1",
        lambda **_: (False, ("OWNER_GO_DECISION_MISSING",)),
    )
    bound, g17, _, native_id = _bootstrap_lane(tmp_path)
    with pytest.raises(StandingSupervisorError, match="OWNER_GO_VALIDATION_DENIED"):
        run_n1_standing_pre_external_supervisor_v1(
            config=_supervisor_config(tmp_path),
            origin_main_sha=OWNER_GO_BASELINE_SHA,
            bound=bound,
            authorization=_continuous_auth(native_id=native_id),
            observation_source=ScriptedContinuousObservationSourceV1([_obs(C1_A)]),
            g17_producers=g17,
            f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
            repo_root=REPO,
            public_rest_fetch=_public_rest_empty,
            private_rest_fetch=_fixture_rest,
        )


def test_t_minus_03_stale_equal_c1_no_second_cycle(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    path = strong_uptrend_closes_v1()
    auth = _continuous_auth(native_id=native_id, max_cycles=2)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=2,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=0.001,
        max_wait_for_next_c1_seconds=5.0,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    dup = _observation_from_closes(closes=path[:16], event_ts=t0)
    obs = ScriptedContinuousObservationSourceV1([dup, None, dup])
    result = run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=obs,
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result.trace.governed_cycle_count == 1


def test_t_minus_04_hard_cap_max_cycles(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    t2 = t1 + 60.0
    path = strong_uptrend_closes_v1()
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=0.001,
        max_wait_for_next_c1_seconds=30.0,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    obs = ScriptedContinuousObservationSourceV1(
        [
            _observation_from_closes(closes=path[:16], event_ts=t0),
            None,
            _observation_from_closes(closes=path[:18], event_ts=t1),
            None,
            _observation_from_closes(closes=path[:20], event_ts=t2),
        ]
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=obs,
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result.trace.governed_cycle_count == 1


def test_t_minus_02_kill_switch_file_present_run_stays_no_post(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    ks = tmp_path / "kill.json"
    ks.write_text(json.dumps({"state": "KILLED"}), encoding="utf-8")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    cfg = _supervisor_config(tmp_path)
    cfg = StandingSupervisorConfigV1(
        public_store_root=cfg.public_store_root,
        private_store_root=cfg.private_store_root,
        lane_state_root=cfg.lane_state_root,
        evidence_root=cfg.evidence_root,
        lock_root=cfg.lock_root,
        kill_switch_state_path=str(ks),
    )
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=cfg,
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=ScriptedContinuousObservationSourceV1(
            [_observation_from_closes(closes=path[:16], event_ts=t0)]
        ),
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
    )
    assert result.trace.post_count == 0


def test_evidence_writer_after_successful_run(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    result = run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=ScriptedContinuousObservationSourceV1(
            [_observation_from_closes(closes=path[:16], event_ts=t0)]
        ),
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
    )
    ev_path = write_standing_supervisor_closure_evidence_v1(
        repo_root=REPO,
        tested_code_sha=OWNER_GO_BASELINE_SHA,
        baseline_sha=OWNER_GO_BASELINE_SHA,
        trace=result.trace,
        ok=result.ok,
        owner_go_consumed=result.owner_go_consumed,
        authority_invariants_ok=result.authority_invariants_ok,
        transport_scope="offline_inject",
        launcher_invoked_supervisor=False,
        post_allowed=False,
        external_effect_authorized=False,
        real_venue_post_allowed=False,
        continuous_admission_granted=result.trace.continuous_admission_granted,
    )
    assert ev_path.is_file()
    payload = json.loads(ev_path.read_text(encoding="utf-8"))
    assert payload["POST_COUNT"] == 0
    assert payload["ok"] is True
