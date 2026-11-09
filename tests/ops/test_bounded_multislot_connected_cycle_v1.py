"""Synthetic per-instrument ports, original N1/Core and one durable budget owner."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as n1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_n1_venue_quantity_limit_admission_v1 as limits,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    _lane_pair_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1 as prepare,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import provenance_for_bound_v1
from tests.ops.test_bounded_multislot_entry_budget_v1 import policy
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    _bound,
    _injected,
    _balance_payload,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _market_kwargs,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    create_position_episode_from_simulated_accounting_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _contract
from tests.ops.test_simulated_accounting_entry_source_v1 import _args
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_aligned_g17_dk_producer_v1,
)
from tests.ops.test_current_mf_n5_instrument_runtime_identity_closure_v1 import _positions_payload
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lifecycle_v1 import (
    rotation_decision_for_lane_v1,
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def ports(bound, epoch, cycle, *, denied=False):
    base = _injected(payload=_balance_payload(avail_eq="1000.00"))
    instruments = json.loads(json.dumps(base.instruments_payload))
    row = next(r for r in instruments["data"] if r["instId"] == "ETH-USDT-SWAP")
    row.update(
        instId=bound.venue_native_id,
        baseCcy=bound.venue_native_id.split("-")[0],
        ctValCcy=bound.venue_native_id.split("-")[0],
        maxMktSz="10000",
        maxLmtSz="10000",
    )
    acquisition = canonical(dict(decision_epoch=epoch, cycle_id=cycle))
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def source(endpoint, payload):
        body = canonical(payload)
        return limits.VenueQuantitySourceV1(
            endpoint, now, acquisition, hashlib.sha256(body.encode()).hexdigest(), body
        )

    observation = limits.N1VenueQuantityLimitsObservationV1(
        account_identity=base.expected_account_identity,
        bound_instrument_json=canonical(bound.to_dict()),
        decision_epoch=epoch,
        cycle_id=cycle,
        acquisition_decision_id=acquisition,
        public_source=source(
            f"/api/v5/public/instruments?instId={bound.venue_native_id}&instType=SWAP", instruments
        ),
        private_source=source(
            f"/api/v5/account/max-size?instId={bound.venue_native_id}&tdMode=cross",
            {
                "code": "0",
                "data": [
                    {
                        "instId": bound.venue_native_id,
                        "maxBuy": "0" if denied else "10000",
                        "maxSell": "10000",
                    }
                ],
            },
        ),
    )
    observation = replace(observation, integrity_digest=observation.digest_v1())
    return replace(
        base, observed_at=epoch, instruments_payload=instruments, venue_quantity_limits=observation
    )


def connected(tmp_path, count, *, denied_lane=None):
    pairs, seeds, provenance, payloads = {}, {}, {}, {}
    for i, symbol in enumerate(["ETH", "SOL", "ADA", "LINK", "APT"][:count], 1):
        lane = f"LANE_{i}"
        bound = replace(
            _bound(),
            instrument_id="synthetic-" + symbol,
            venue_native_id=f"{symbol}-USDT-SWAP",
            selection_id="selected-" + lane,
        )
        parent = tmp_path / lane
        arm, closes, mark, event, g17 = prepare(
            bound=bound, g17_typed_vol_producer=None, lane_state_root=parent, lane_id=lane
        )
        pairs[lane] = _lane_pair_v1(lane_state_root=parent, bound=bound, lane_id=lane)
        seeds[lane] = (arm, g17)
        provenance[lane] = provenance_for_bound_v1(bound=bound, mark_px=mark, index_px=mark * 0.995)
        rows = [
            [
                str(int((event - (len(closes) - 1 - j) * 60) * 1000)),
                str(p),
                str(p),
                str(p),
                str(p),
                "10",
                "100",
                "USDT",
                "1",
            ]
            for j, p in enumerate(closes)
        ]
        payloads[lane] = dict(code="0", instId=bound.venue_native_id, data=rows)
    kwargs = _market_kwargs(cycle_id_prefix="connected")
    kwargs.pop("canonical_price_provenance")
    epoch = datetime.fromtimestamp(event + 1, timezone.utc).isoformat().replace("+00:00", "Z")
    kwargs.update(
        observed_unix=event + 1,
        last_finalized_event_ts_unix=event,
        finalized_closes=closes,
        mark_px=mark,
        index_px=mark * 0.995,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        candles_payload=None,
        candles_payload_by_lane=payloads,
        canonical_price_provenance_by_lane=provenance,
        g17_typed_vol_producers={lane: s[1] for lane, s in seeds.items()},
        live_29p_injected_by_lane={
            lane: ports(bound, epoch, "connected:" + lane, denied=lane == denied_lane)
            for lane, (_, bound) in pairs.items()
        },
    )
    account = next(iter(kwargs["live_29p_injected_by_lane"].values())).expected_account_identity
    host = PortfolioBudgetHostV1(
        root=tmp_path / "budget",
        private_rest_fetch=_fetch(uid=account),
        repository_sha="bounded-synthetic-proof",
        session_id="bounded-synthetic-proof",
        expected_account_identity=account,
        durable_mode="create",
        clock=lambda: event + 1,
        execution_environment="INTERNAL_SIMULATED_EXECUTION",
        entry_budget_policy=policy(),
    )
    context = host.observe_v1({lane: bound for lane, (_, bound) in pairs.items()})
    kwargs.update(portfolio_budget_owner=host.owner, host_budget_recovery=context)
    return pairs, seeds, kwargs, host


@pytest.mark.parametrize("count", [2, 5])
def test_connected_original_slots_have_distinct_plans_and_one_budget(tmp_path, count):
    pairs, seeds, kwargs, host = connected(tmp_path, count)
    try:
        results = n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        for lane, result in results.items():
            cycle = result.governed_cycle_result
            assert cycle.disposition == "PRE_EXTERNAL_EFFECT", (lane, cycle.first_real_blocker)
            assert cycle.final_order_envelope.instrument_id == pairs[lane][1].venue_native_id
            assert cycle.final_order_envelope.side == "buy"
            assert cycle.extra["PORTFOLIO_RESERVATION_ID"]
            assert 0 < host.owner.active_slot_sum_v1(lane) <= 25
            assert cycle.post_count == 0 and not cycle.permit_created
            assert result.s7_invocation.cycle_result.replay is not None
        assert (
            len(
                {
                    r.governed_cycle_result.extra["PORTFOLIO_RESERVATION_ID"]
                    for r in results.values()
                }
            )
            == count
        )
        assert host.owner.stored_reservation_count_v1() == count
        assert host.owner.active_sum_v1() == sum(
            host.owner.active_slot_sum_v1(lane) for lane in pairs
        )
        assert host.owner.active_sum_v1() <= count * 25
    finally:
        host.close()


@pytest.mark.parametrize("count", [2, 5])
def test_original_entry_fills_continue_occupied_core_and_time_exit(tmp_path, count):
    pairs, seeds, kwargs, host = connected(tmp_path, count)
    try:
        entries = n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        scope = PositionEpisodeScopeV1(
            host.expected_account_identity, "INTERNAL_SIMULATED_EXECUTION"
        )
        episodes, sessions = {}, {}
        opened = kwargs["last_finalized_event_ts_unix"] + 1
        for lane, result in entries.items():
            order = result.governed_cycle_result.final_order_envelope
            assert order is not None
            session = ProductiveFuturesAccountingSessionV1(
                contract=_contract(order.instrument_id, contract_size="0.01", min_qty="1")
            )
            fill = build_simulated_fill_v1(
                fill_id="original-plan:" + order.envelope_digest,
                instrument_id=order.instrument_id,
                side=order.side.upper(),
                quantity=order.quantity,
                mark_price=str(kwargs["mark_px"]),
                contract=session.contract,
                event_time_unix=opened,
            )
            session.apply_fill(fill)
            bound = pairs[lane][1]
            identity = bind_simulated_accounting_episode_identity_v1(
                identity=PositionEpisodeIdentityV1(
                    lane,
                    bound.instrument_id,
                    bound.venue_native_id,
                    "pending-opening",
                    "long",
                    scope,
                ),
                opening_fill=fill,
            )
            episodes[lane] = create_position_episode_from_simulated_accounting_v1(
                **_args(tmp_path / "episodes" / lane, identity), session=session, fills=(fill,)
            )
            sessions[lane] = session
        held = host.owner.active_sum_v1()
        for step, delta in enumerate((60, 120, 3660), 1):
            event = opened + delta
            next_kwargs = dict(kwargs)
            payloads, g17 = {}, {}
            for lane, (_, bound) in pairs.items():
                old = kwargs["candles_payload_by_lane"][lane]
                closes = tuple(float(row[4]) for row in old["data"])
                rows = [
                    [
                        str(int((event - (len(closes) - 1 - j) * 60) * 1000)),
                        str(p),
                        str(p),
                        str(p),
                        str(p),
                        "10",
                        "100",
                        "USDT",
                        "1",
                    ]
                    for j, p in enumerate(closes)
                ]
                payloads[lane] = dict(code="0", instId=bound.venue_native_id, data=rows)
                g17[lane] = governed_c1_aligned_g17_dk_producer_v1(
                    bound=bound,
                    anchor_event_ts_unix=event,
                    evidence_store_root=tmp_path / "g17-progress" / str(step) / lane,
                    mark_closes=closes,
                )
            portfolio = PortfolioTruthSnapshotV1(
                positions=tuple(
                    PositionTruthV1.from_signed(
                        instrument_id=pairs[lane][1].instrument_id,
                        signed_quantity=session.position.qty,
                    )
                    for lane, session in sessions.items()
                ),
                event_time_unix=event,
                wall_time_unix=event,
                source_id="analytical_execution_state",
            )
            next_kwargs.update(
                cycle_id_prefix=f"occupied-{step}",
                observed_unix=event + 1,
                last_finalized_event_ts_unix=event,
                candles_payload_by_lane=payloads,
                g17_typed_vol_producers=g17,
                observed_portfolio=portfolio,
                occupancy_payloads=_positions_payload(
                    *[
                        (pairs[lane][1].venue_native_id, "net", session.position.qty)
                        for lane, session in sessions.items()
                    ]
                ),
                position_episode_bindings=episodes,
                position_episode_scope=scope,
            )
            progress = n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **next_kwargs)
            for lane, result in progress.items():
                assert result.s7_invocation is not None, (
                    result.governed_cycle_result.first_genuine_blocker
                )
                assert result.s7_invocation.cycle_result.replay is not None
                assert result.s7_invocation.cycle_result.decision_outcome not in {
                    "enter_long",
                    "enter_short",
                }
                assert result.governed_cycle_result.post_count == 0
                if delta == 3660:
                    assert result.position_management_close_intent is not None, (
                        result.governed_cycle_result.first_real_blocker
                    )
                    close = result.position_management_close_intent
                    assert close.reduce_only is True
                    assert (
                        result.position_management_quantity_handoff.open_quantity
                        == sessions[lane].position.qty
                    )
                    assert (
                        result.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
                        == "time_exit"
                    )
            assert host.owner.active_sum_v1() == held
            assert host.owner.stored_reservation_count_v1() == count
        # A local close intent is not a reconciled venue/account transition.
        assert not rotation_decision_for_lane_v1(
            venue_flat=True, reconciled=False, lane_health_allows_replacement=True
        ).allowed
        assert host.owner.active_sum_v1() == held
        ledgers = list((tmp_path).rglob("governed_cycle_orchestrator_ledger_v1.json"))
        assert len(ledgers) == count * 4
        with pytest.raises(ValueError, match="CYCLE_AUTHORIZATION_REPLAY"):
            n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **next_kwargs)
    finally:
        host.close()


def test_instrument_local_quantity_denial_does_not_borrow_or_stop_other_slots(tmp_path):
    pairs, _, kwargs, host = connected(tmp_path, 5, denied_lane="LANE_2")
    try:
        results = n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        assert results["LANE_2"].governed_cycle_result.final_order_envelope is None
        assert host.owner.active_slot_sum_v1("LANE_2") == 0
        for lane in set(pairs) - {"LANE_2"}:
            assert results[lane].governed_cycle_result.final_order_envelope is not None
            assert host.owner.active_slot_sum_v1(lane) > 0
        assert host.owner.budget_state_v1().admitted
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["dual", "missing", "foreign", "type"])
def test_lane_financial_inputs_refuse_ambiguity_before_core(tmp_path, fault):
    kwargs = _market_kwargs(cycle_id_prefix="invalid-ports")
    kwargs["live_29p_injected_by_lane"] = {}
    if fault == "dual":
        kwargs["live_29p_injected"] = _injected()
    if fault == "foreign":
        kwargs["live_29p_injected_by_lane"] = {"LANE_6": _injected()}
    if fault == "type":
        kwargs["live_29p_injected_by_lane"] = {"LANE_1": object()}
    with pytest.raises(ValueError, match="live_29p"):
        n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1({"LANE_1": None}, **kwargs)
