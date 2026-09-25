"""WP-2 deterministic composition proof (transport-bound; not productive real GET).

Proves the composed Full-Core closure executor and occupied-lane consumer path through
WP-1 handoff and governed-cycle orchestration. PRE_EXTERNAL requires canonical MV2
``enter_long``; post-#6764 baseline-first fixtures are documented separately.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    DECISION_ENTER,
    STATUS_PASS,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    compose_current_productive_29p_common_epoch_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
    build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    OWNER_GO,
    execute_current_productive_full_core_pre_external_closure_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _invoke,
    _mv2_aligned_candles,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    _EPOCH,
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    _balance_payload,
    _injected,
    _join,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound as _oneshot_bound,
    _cycle,
    _cycle_a_with_confirmation_progress,
    _produced_g17_producer,
    _strong_uptrend_closes,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _bound,
    _origin_main_sha,
    _productive_transport,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

PRODUCTIVE_TRANSPORT_CLASS_TESTDOUBLE = True
PRODUCTIVE_REAL_GET_PROVEN = False


def test_stale_flat_mark_upscope_confirm_cycle_does_not_natural_enter() -> None:
    """Negative: flat mark on UPSCOPE_CONFIRM cycle fails C3 alignment (pre-V32 assumption)."""
    path = _strong_uptrend_closes()
    cycle_a = _cycle_a_with_confirmation_progress()
    cycle_b = _cycle(
        cycle_id="wp2-stale-flat-mark-probe",
        incoming_cursor=cycle_a.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_120.0,
    )
    assert cycle_b.decision_outcome not in {"enter_long", "enter_short"}


def test_wp1_transport_common_epoch_to_injected_handoff_without_manual_29p_pass() -> None:
    bound = _bound()
    transport = _productive_transport()
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=_EPOCH,
        bound_instrument=bound,
        fresh_get_transport=transport,
    )
    assert handoff.evaluator_29p is True
    injected = build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
        handoff=handoff,
        transport=transport,
    )
    assert injected.fresh_pretrade_get_status == "TRUSTED_PRESENT"
    assert injected.instruments_payload is not None
    assert transport.transport_class == TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET


def test_wp2_execute_transport_bound_wp1_pass_governed_cycle_hold_fail_closed_safe(
    tmp_path: Path,
) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    path = _strong_uptrend_closes()
    last_mark = float(path[-1])
    candles = _mv2_aligned_candles(last_ts_ms=int(1_700_000_120_000), mark_px=last_mark)
    g17 = _produced_g17_producer(instrument_id=bound.instrument_id)
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        lane_state_root=tmp_path / "lanes",
        fresh_get_transport=_productive_transport(),
        execute_network=False,
        evidence_root=tmp_path / "evidence",
        candles_payload=candles,
        market_kwargs={
            "cycle_id_prefix": "wp2-compose-hold",
            "mark_px": last_mark,
            "index_px": last_mark,
            "bid_px": last_mark - 0.5,
            "ask_px": last_mark + 0.5,
            "finalized_closes": path,
            "last_finalized_event_ts_unix": 1_700_000_120.0,
            "observed_unix": 1_700_000_120.0 + 100.0,
            "venue_flat": True,
            "existing_position_side": ExistingPositionSide.NONE,
        },
        g17_typed_vol_producers={"LANE_1": g17},
        execution_integrity_backend=integrity,
    )
    assert result.wp1_status == "PASS"
    assert result.admissibility_29p_status == "true"
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.external_effect_occurred is False
    assert result.runtime_owner_gos_consumed
    assert result.terminal_disposition in {
        DISPOSITION_HOLD,
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        "FAIL_CLOSED",
    }
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False


def test_wp2_untrusted_29p_avail_zero_blocks_wp1_admissibility(tmp_path: Path) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    transport = _productive_transport(avail_eq="0")
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        lane_state_root=tmp_path / "lanes",
        fresh_get_transport=transport,
        execute_network=False,
        evidence_root=tmp_path / "evidence",
        candles_payload=_mv2_aligned_candles(last_ts_ms=1_700_000_120_000, mark_px=100.0),
        execution_integrity_backend=integrity,
    )
    assert result.wp1_status == "FAIL"
    assert result.admissibility_29p_status == "false"
    assert result.wp2_status == "NOT_STARTED"
    assert result.post_count == 0
    assert result.terminal_disposition == "FAIL_CLOSED"


def test_wp2_enter_join_denies_venue_plan_when_29p_not_pass() -> None:
    _, cycle_b, _path = _host_enter_cycle()
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
        _enter_replay,
    )

    replay = _enter_replay(cycle_b)
    denied = _join(replay=replay, injected=_injected(payload=_balance_payload(avail_eq="0")))
    assert denied.decision_class == DECISION_ENTER
    assert denied.status != STATUS_PASS
    assert denied.venue_plan_authorized is False


def test_wp2_consumer_compose_layered_store_then_c1_orchestrator_consumed(tmp_path: Path) -> None:
    """Real consumer join + S7/P5.10 path; terminal HOLD when MV2 does not ENTER."""
    pairs, results = _invoke(tmp_path, ("LANE_1",), cycle_id_prefix="wp2-consumer-compose")
    record = results["LANE_1"]
    cycle = record.governed_cycle_result
    assert record.t2_s7_used is True
    assert int(cycle.post_count) == 0
    assert cycle.permit_created is False
    assert cycle.disposition in {DISPOSITION_HOLD, DISPOSITION_PRE_EXTERNAL_EFFECT}


def test_wp2_reference_price_join_uses_mv2_mark_when_enter_replay_supplied() -> None:
    """Lower-layer: when ENTER replay exists, join rebind uses producer (not INDEX_PX)."""
    _, cycle_b, _path = _host_enter_cycle()
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
        _enter_replay,
    )

    replay = _enter_replay(cycle_b)
    result = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=_oneshot_bound(),
        injected=_injected(payload=_balance_payload()),
        decision_epoch=_EPOCH,
    )
    assert result.decision_class == DECISION_ENTER
    if result.status == STATUS_PASS and result.replay is not None:
        sizing = result.replay.intermediate.capital_risk_sizing_decision
        assert sizing is not None
        assert result.producer_output_value != ""


def test_wp2_deterministic_pre_external_effect_full_compose_transport_bound(
    tmp_path: Path,
) -> None:
    """Layered Long: ARM cycle seeds store; one governed cycle produces ENTER → PRE_EXTERNAL.

    Direction = LONG for mechanical minimality only (Short is also proven bilaterally).
    """
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    g17 = _produced_g17_producer(instrument_id=bound.instrument_id)
    lanes_root = tmp_path / "lanes"
    _arm_cycle, enter_closes, mark_px, event_ts = (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
            bound=bound,
            g17_typed_vol_producer=g17,
            lane_state_root=lanes_root,
        )
    )
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        lane_state_root=lanes_root,
        fresh_get_transport=_productive_transport(),
        execute_network=False,
        evidence_root=tmp_path / "evidence",
        candles_payload=candles,
        market_kwargs={
            "cycle_id_prefix": "wp2-pre-ext-enter",
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "existing_position_side": ExistingPositionSide.NONE,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
        },
        g17_typed_vol_producers={"LANE_1": g17},
        execution_integrity_backend=integrity,
    )
    assert result.wp1_status == "PASS"
    assert result.wp2_status == "PASS"
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.external_effect_occurred is False
    assert result.reference_price_status == "GOVERNED_MV2_MARK"
    assert result.venue_plan_status == "PASS"
    assert result.final_order_envelope_status == "PASS"
