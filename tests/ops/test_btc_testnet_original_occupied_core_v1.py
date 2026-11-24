"""The authenticated Demo episode consumes its existing original Core cursor."""

from dataclasses import replace
from datetime import datetime, timedelta
import json

import pytest
from tests.ops.test_btc_demo_entry_submit_v1 import entry_send as entry_send
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)

from tests.ops.test_btc_testnet_original_execution_receipt_v1 import (
    original_testnet_entry as original_testnet_entry,
    demo_entry as demo_entry,
)
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def inputs(world, monkeypatch, *, adverse=False):
    from src.ops.btc_demo_entry_financial_inputs_v1 import build_btc_demo_capital_inputs_v1
    from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        restore_layered_core_episode_v1,
    )
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        IsolatedLaneSlotV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        AuthenticatedEntryEpisodeRequestV1,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_enter_live_29p_join_v1 as financial,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as original,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

    demo, host, now = world["demo"], world["host"], world["now"]
    bound = world["bound"]
    saved = world["saved"]
    rows = json.loads(saved["entry_cost_binding"]["observation"]["sources_json"])
    rows.update(json.loads(saved["native_initial_margin_binding"]["observation"]["sources_json"]))
    rows = {key: cost.FreshPretradeGetTransportResultV1(**value) for key, value in rows.items()}
    epoch = world["entry"].cycle.replay.intermediate.market_context.decision_time
    _, capital, _, _ = build_btc_demo_capital_inputs_v1(
        rows,
        account=host.account,
        epoch=epoch,
        now=now.isoformat(),
        config=world["payloads"]["account"]["data"][0],
    )
    world["context"].recover_v1(host.owner, capital)
    core = restore_layered_core_episode_v1(
        demo.cursor_root, expected_instrument_id=bound.instrument_id
    )
    direction = 1 if world["episode"].identity.position_side == "long" else -1
    mark = core.running_reference.reference_price_r_t + direction * core.scope.d_t * (
        -1.5 if adverse else 0.1
    )
    payload = dict(
        code="0",
        data=[
            dict(
                instId=bound.venue_native_id,
                markPx=str(mark),
                idxPx=str(mark),
                ts=str(int((now.timestamp() - 0.05) * 1000)),
            )
        ],
    )
    price = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=payload,
        venue_native_id=bound.venue_native_id,
        mark_acquired_at_utc=now.isoformat(),
    )
    candles = demo._offline_fixture_candles
    closes, c1 = extract_finalized_candle_closes_v1(candles)
    slot = IsolatedLaneSlotV1(
        "LANE_3",
        "OCCUPIED",
        bound.instrument_id,
        str(demo.cursor_root),
        bound.universe_snapshot_id,
        bound.ranking_snapshot_id,
        bound.ranking_integrity_digest,
    )
    instrument = world["payloads"]["instruments"]
    injected = financial.CurrentProductiveEnterLive29PInjectedGetV1(
        instruments_payload=instrument, observed_at=now.isoformat()
    )

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz is None else now.astimezone(tz)

    monkeypatch.setattr(original, "datetime", Clock)
    return {"LANE_3": (slot, bound)}, dict(
        origin_main_sha=demo.repository_sha,
        cycle_id_prefix="testnet-core-adverse" if adverse else "testnet-core-hold",
        observed_unix=now.timestamp(),
        mark_px=mark,
        index_px=mark,
        bid_px=mark - 0.1,
        ask_px=mark + 0.1,
        volume=100.0,
        open_interest=200.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=c1,
        venue_flat=False,
        existing_position_side=ExistingPositionSide(world["episode"].identity.position_side),
        candles_payload=candles,
        g17_typed_vol_producers={"LANE_3": demo.g17},
        canonical_price_provenance=price,
        portfolio_budget_owner=host.owner,
        host_budget_recovery=world["context"],
        authenticated_entry=AuthenticatedEntryEpisodeRequestV1(world["proof_root"], world["proof"]),
        occupied_scope_mark_lane_id="LANE_3",
        live_29p_injected_by_lane={"LANE_3": injected},
    )


def test_original_governed_consumer_continues_same_demo_scope_and_hold(
    original_testnet_entry, monkeypatch
):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    )
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
    )

    world = original_testnet_entry
    pairs, kw = inputs(world, monkeypatch)
    before = world["host"].owner.local_commitment_readback_v1().commitments
    result = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kw)["LANE_3"]
    governed = result.governed_cycle_result
    assert governed.post_count == 0 and not governed.permit_created
    retained = read_occupied_scope_mark_snapshot_v1(world["demo"].cursor_root)
    assert retained is not None, governed
    assert retained["mark"]["position_episode_id"] == world["episode"].identity.episode_id
    assert world["host"].owner.local_commitment_readback_v1().commitments == before
    assert governed.position_management_reversal is None
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        load_current_productive_sidestate_confirmation_cursor_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
        cursor_last_accepted_c1_venue_event_time_v1,
    )

    assert (
        cursor_last_accepted_c1_venue_event_time_v1(
            load_current_productive_sidestate_confirmation_cursor_v1(world["demo"].cursor_root)
        )
        == kw["last_finalized_event_ts_unix"]
    )
    allocation = world["host"].owner.risk_snapshot_v1()["state"]["slot_capital_allocation"]
    previous_mark = retained["mark"]["event_unix"]
    world["now"] += timedelta(seconds=0.25)
    world["host"].clock = world["now"].timestamp
    pairs, kw = inputs(world, monkeypatch)
    kw["cycle_id_prefix"] += "-next"
    again = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kw)["LANE_3"]
    assert again.governed_cycle_result.post_count == 0
    retained = read_occupied_scope_mark_snapshot_v1(world["demo"].cursor_root)
    assert retained["mark"]["event_unix"] > previous_mark
    assert retained["mark"]["position_episode_id"] == world["episode"].identity.episode_id
    assert world["host"].owner.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
    assert world["host"].owner.local_commitment_readback_v1().commitments == before


def test_observed_position_alone_cannot_acknowledge_entry_and_signed_proof_is_idempotent(
    original_testnet_entry,
):
    from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
        run_productive_reconciliation_startup_gate_v1,
    )

    world = original_testnet_entry
    host, ctx = world["host"], world["context"]
    args = dict(
        state_root=host.root / "reconciliation",
        observed=ctx.observed,
        session_id=host.session_id,
        repository_sha=host.repository_sha,
        now_unix=host.clock(),
        require_persisted_present=True,
    )
    denied = run_productive_reconciliation_startup_gate_v1(**args)
    assert not denied.alpha_enabled and denied.hard_stop
    before = host.owner.local_commitment_readback_v1().commitments
    accepted = run_productive_reconciliation_startup_gate_v1(
        **args, authenticated_testnet_entry=(ctx, world["proof"])
    )
    assert accepted.ok and accepted.alpha_enabled
    assert (
        accepted.evidence.applied_mutation["authenticated_testnet_entry_identity_digest"]
        == world["episode"].identity.episode_id
    )
    replay = run_productive_reconciliation_startup_gate_v1(
        **args, authenticated_testnet_entry=(ctx, world["proof"])
    )
    assert replay.ok and replay.evidence.applied_mutation == {}
    assert host.owner.local_commitment_readback_v1().commitments == before


@pytest.mark.parametrize("fault", ["proof", "quantity", "stale", "missing-proof-store"])
def test_wrong_testnet_fill_proof_cannot_advance_original_portfolio(original_testnet_entry, fault):
    from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
        run_productive_reconciliation_startup_gate_v1,
    )

    world = original_testnet_entry
    host, ctx, proof = world["host"], world["context"], world["proof"]
    observed = ctx.observed
    if fault == "proof":
        proof = replace(proof, identity_digest="f" * 64)
    elif fault == "quantity":
        observed = replace(
            observed,
            positions=(
                replace(
                    observed.positions[0], signed_quantity=observed.positions[0].signed_quantity * 2
                ),
            ),
        )
    elif fault == "stale":
        host.clock = lambda: world["now"].timestamp() + 6
    else:
        ctx.authenticated_reconciliation.proof_root = None
    portfolio = host.root / "reconciliation"
    before = {
        p.relative_to(portfolio): p.read_bytes()
        for p in portfolio.rglob("*")
        if p.is_file() and "lock" not in p.name
    }
    with pytest.raises((ValueError, OSError)):
        run_productive_reconciliation_startup_gate_v1(
            state_root=portfolio,
            observed=observed,
            session_id=host.session_id,
            repository_sha=host.repository_sha,
            now_unix=host.clock(),
            require_persisted_present=True,
            authenticated_testnet_entry=(ctx, proof),
        )
    after = {
        p.relative_to(portfolio): p.read_bytes()
        for p in portfolio.rglob("*")
        if p.is_file() and "lock" not in p.name
    }
    assert before == after
