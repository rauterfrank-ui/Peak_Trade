"""The two flat ranked Shadow swaps consume a genuine decision and native sized amount."""

from dataclasses import replace
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from src.ops import ranked_shadow_entry_selection_v1 as selection
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_HOST,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    RANKED_SWAP_SCOPES,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.ranked_shadow_first_purchase_v1 import RankedShadowFirstPurchaseV1
from src.ops.ranked_slot_run_source_v1 import RankedRunSlotV1
from src.ops.ranked_swap_shadow_observation_v1 import collect_ranked_swap_observation_v1
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (
    run_hardened_wallclock_bridge_observation_cycle_v2,
)
from tests.ops.test_single_selected_future_runtime_binding_v1 import (
    _build_chain,
    _perp,
    OBSERVED_UNIX,
    REPO_SHA,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("short", [False, True], ids=["long-short", "short-long"])
@pytest.mark.parametrize("thin", [False, True], ids=["two-levels", "blocked-then-two-levels"])
def test_csop_close_to_flat_then_separately_confirmed_reentry(tmp_path, monkeypatch, short, thin):
    from copy import deepcopy
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.full_economic_reconstruction_verifier_v2 import (
        verify_full_economic_reconstruction_v2,
    )

    scope = next(scope for scope in RANKED_SWAP_SCOPES if scope.base == "CSOPSKHYNIX2L")
    row = dict(_perp(scope.native_id, base=scope.base, ct_val="1"), tickSz="0.001", maxMktSz="1000")
    config, assignment = ranked_config(tmp_path, monkeypatch, row, scope)
    depth = [(1, "2"), (3, "30")]
    steps = [(D(k) / 100, [(1, "1")] if thin and k <= 6 else depth) for k in range(1, 12)]
    cycles, state, _ = exercise_ranked_entry(
        tmp_path,
        config,
        assignment,
        row,
        short=short,
        start=OBSERVED_UNIX,
        price=D("1.838"),
        move=D("0.01"),
        initial_equity=D("10.40"),
        after_opening=steps,
    )
    opening, closing, reopening = [c for c in cycles if c["fill"]]
    first = opening["ranked_shadow_first_purchase"]
    exit_receipt = closing["ranked_shadow_exit"]
    again = reopening["ranked_shadow_first_purchase"]
    assert D(first["capacity"]["entry_limit_usdc"]) == 10
    assert closing["decision_outcome"] in {"reduce", "exit"}
    assert exit_receipt["opening_fill_id"] == opening["fill_id"]
    assert D(exit_receipt["position_after_contracts"]) == 0
    assert closing["cycle_index"] < reopening["cycle_index"]
    assert again["entry"]["previous_exit_fill_id"] == closing["fill_id"]
    assert again["confirmation"]["progress"]["distinct_confirmation_observation_count"] >= 2
    assert again["entry"]["direction"] == ("long" if short else "short")
    assert (
        again["entry"]["entry_action"] == "REENTRY" and D(again["entry"]["entry_limit_usdc"]) <= 10
    )
    assert closing["fill"]["side"] == reopening["fill"]["side"] != opening["fill"]["side"]
    for c in (closing, reopening):
        f = c["fill"]
        px, qty = D(f["fill_price"]), D(f["quantity_contracts"])
        mark = D(f["mark_price"])
        assert qty > 2
        # The two best contracts fill one tick away. The remainder fills three ticks away.
        ticks = ((2 + (qty - 2) * 3) / qty).to_integral_value(rounding=ROUND_CEILING)
        assert px == mark + (1 if short else -1) * ticks * D("0.001")
        assert D(f["fee"]) == px * qty * D("0.0002")
    blocked = [c for c in cycles if (c.get("ranked_shadow_exit") or {}).get("status") == "BLOCKED"]
    assert bool(blocked) == thin
    assert all(
        c["fill"] is None
        and c["ranked_shadow_exit"]["reason"] == "SHADOW_INSUFFICIENT_EXECUTABLE_DEPTH"
        for c in blocked
    )

    def check(ledger):
        return verify_full_economic_reconstruction_v2(
            cycle_ledger=ledger,
            fill_ledger=state.fill_ledger,
            final_portfolio_snapshot=state.portfolio.snapshot(),
            economic_metrics=state.portfolio.economic_metrics().to_dict(),
        )

    assert check(cycles).ok
    bad = deepcopy(cycles)
    bad[closing["cycle_index"] - 1]["ranked_shadow_exit"]["opening_fill_id"] = "other"
    assert not check(bad).ok


@pytest.mark.parametrize(
    "short, prices, total_fees, final_equity",
    [
        pytest.param(
            False,
            ("1.842", "1.819", "1.799", "1.823", "1.843"),
            "0.009126",
            "9.742354",
            id="long-short-long",
        ),
        pytest.param(
            True,
            ("1.840", "1.863", "1.883", "1.859", "1.839"),
            "0.009284",
            "9.772196",
            id="short-long-short",
        ),
    ],
)
def test_csop_slot4_two_switches_on_one_budget(
    tmp_path, monkeypatch, short, prices, total_fees, final_equity
):
    positions = (-5, 0, 5, 0, -5) if short else (5, 0, -5, 0, 5)
    check_csop_slot4_sequence(tmp_path, monkeypatch, positions, prices, total_fees, final_equity)


@pytest.mark.parametrize(
    "positions, prices, third_switch_fees, total_fees, final_equity",
    [
        pytest.param(
            (5, 0, -5, 0, 5, 0, -5),
            ("1.842", "1.819", "1.799", "1.823", "1.843", "1.797", "1.777"),
            "0.0035740",
            "0.0127000",
            "9.5287800",
            id="long-short-long-short",
        ),
        pytest.param(
            (-5, 0, 5, 0, -5, 0, 4),
            ("1.840", "1.863", "1.883", "1.859", "1.839", "1.885", "1.904"),
            "0.0034082",
            "0.0126922",
            "9.5097878",
            id="short-long-short-long",
        ),
    ],
)
def test_csop_slot4_three_switches_on_one_budget(
    tmp_path, monkeypatch, positions, prices, third_switch_fees, total_fees, final_equity
):
    _, filled = check_csop_slot4_sequence(
        tmp_path,
        monkeypatch,
        positions,
        prices,
        total_fees,
        final_equity,
        extra_steps=csop_switch_steps((-10, 20, 30, 40, 50, 60)),
    )
    close, reentry = filled[-2:]
    check_csop_switch_depth_and_fees(close, reentry, third_switch_fees)
    purchase = reentry["ranked_shadow_first_purchase"]
    available = D(close["portfolio_snapshot"]["state"]["cash"])
    mark = D(purchase["valuation"]["mark_usdt_per_base"])
    allowance = D(purchase["entry"]["cost_allowance_usdt"])
    cap = D(purchase["sizing"]["decision"]["pre_sizing_risk"]["capital_cap_quantity"])
    assert cap == abs(positions[-1])
    assert cap * mark + allowance <= available
    if positions[-1] == 4:
        # Five contracts at the mark would fit, but even the cost allowance for four
        # takes that five-contract amount over the remaining cash.
        assert 5 * mark < available < 5 * mark + allowance


@pytest.mark.parametrize(
    "positions, prices, fourth_switch_fees, total_fees, final_equity",
    [
        pytest.param(
            (5, 0, -5, 0, 5, 0, -5, 0, 4),
            ("1.842", "1.819", "1.799", "1.823", "1.843", "1.797", "1.777", "1.825", "1.844"),
            "0.0033002",
            "0.0160002",
            "9.2664798",
            id="long-short-long-short-long",
        ),
        pytest.param(
            (-5, 0, 5, 0, -5, 0, 4, 0, -5),
            ("1.840", "1.863", "1.883", "1.859", "1.839", "1.885", "1.904", "1.858", "1.837"),
            "0.0033234",
            "0.0160156",
            "9.3414644",
            id="short-long-short-long-short",
        ),
    ],
)
def test_csop_slot4_four_switches_across_minute_on_one_budget(
    tmp_path, monkeypatch, positions, prices, fourth_switch_fees, total_fees, final_equity
):
    # Both opening fills occur at second 58.420; follow-on observation 20 closes the minute.
    start = OBSERVED_UNIX + (58.02 if positions[0] < 0 else 57.82)
    cycles, filled = check_csop_slot4_sequence(
        tmp_path,
        monkeypatch,
        positions,
        prices,
        total_fees,
        final_equity,
        start=start,
        followup_interval=0.080,
        extra_steps=csop_switch_steps((-10, 20, 30, 40, 50, 60))
        + csop_switch_steps((70, 40, 30, 20, 10, 0)),
    )
    (rollover,) = [
        c
        for prev, c in zip(cycles, cycles[1:])
        if c["price_basis"]["event_ts_unix"] // 60 > prev["price_basis"]["event_ts_unix"] // 60
    ]
    assert rollover["cycle_index"] == filled[6]["cycle_index"] + 1 == filled[0]["cycle_index"] + 20
    assert rollover["canonical_volatility_typed_binding"]["producer_outcome"] == "PRODUCED"
    assert all(
        c["canonical_market_context_typed_estimate_present"]
        for c in cycles[rollover["cycle_index"] - 1 :]
    )
    check_csop_switch_depth_and_fees(*filled[-2:], fourth_switch_fees)


def csop_switch_steps(offsets_in_ticks):
    # Only one contract on the second and third observation; otherwise two at
    # the touch and the rest four ticks away.
    deep = [(1, "2"), (5, "30")]
    thin = [(1, "1")]
    return [
        (D("0.001") * ticks, thin if index in (2, 3) else deep)
        for index, ticks in enumerate(offsets_in_ticks, 1)
    ]


def check_csop_switch_depth_and_fees(close, reentry, expected_fees):
    purchase = reentry["ranked_shadow_first_purchase"]
    entry = purchase["entry"]
    for cycle, receipt in ((close, close["ranked_shadow_exit"]), (reentry, entry)):
        fill = cycle["fill"]
        quantity = D(fill["quantity_contracts"])
        buy = fill["side"] == "BUY"
        (book,) = json.loads(receipt["fill_book"]["body"])["data"]
        best, next_level = book["asks" if buy else "bids"][:2]
        best_price, best_size = D(best[0]), D(best[1])
        next_price, next_size = D(next_level[0]), D(next_level[1])
        assert best_size == 2 and 0 < quantity - best_size <= next_size
        assert next_price - best_price == (D("0.004") if buy else D("-0.004"))
        vwap = (best_size * best_price + (quantity - best_size) * next_price) / quantity
        rounded_price = vwap.quantize(D("0.001"), rounding=ROUND_CEILING if buy else ROUND_FLOOR)
        assert D(fill["fill_price"]) == rounded_price
    assert D(close["fill"]["fee"]) + D(reentry["fill"]["fee"]) == D(expected_fees)


def test_csop_slot4_finalized_minute_continues_g17_history(tmp_path, monkeypatch):
    scope = next(scope for scope in RANKED_SWAP_SCOPES if scope.base == "CSOPSKHYNIX2L")
    row = dict(_perp(scope.native_id, base=scope.base, ct_val="1"), tickSz="0.001")
    config, assignment = ranked_config(tmp_path, monkeypatch, row, scope)
    start = OBSERVED_UNIX + 59.2
    quotes = RecordedQuotes(assignment.instrument, start)
    cycles, state, _ = exercise_ranked_entry(
        tmp_path,
        config,
        assignment,
        row,
        short=False,
        start=start,
        price=D("1.808"),
        move=D("0.010"),
        after_opening=[(D("0.002"), [(1, "30")])] * 3,
        transport=quotes,
    )
    history = state.typed_volatility_cmc_binding_host.producer.history
    previous, added = history.records[-2:]
    (rollover,) = [
        i
        for i in range(1, len(cycles))
        if cycles[i]["price_basis"]["event_ts_unix"] // 60
        > cycles[i - 1]["price_basis"]["event_ts_unix"] // 60
    ]
    cycle = cycles[rollover]
    assert history.observation_count_prices == 62
    assert added.venue == previous.venue == "OKX"
    assert (added.canonical_instrument_id, added.venue_instrument_id) == (
        scope.canonical_id,
        scope.native_id,
    )
    assert added.event_time.unix_seconds == previous.event_time.unix_seconds + 60 == OBSERVED_UNIX
    assert added.mark_price == cycles[rollover - 1]["price_basis"]["mid_price"]
    assert added.receive_time == cycle["price_basis"]["receive_ts_unix"] >= OBSERVED_UNIX + 60
    assert cycle["canonical_volatility_typed_binding"]["producer_outcome"] == "PRODUCED"
    assert all(c["canonical_market_context_typed_estimate_present"] for c in cycles[rollover:])

    quotes.now += 60
    market = collect_ranked_swap_observation_v1(
        assignment, tmp_path / "mismatch", lambda: quotes.now, transport=quotes
    )
    tick = ObservationMarketTickV1(
        scope.canonical_id,
        "OKX",
        "FUTURES",
        len(cycles) + 1,
        quotes.now,
        quotes.now,
        0,
        market.mark,
    )
    for foreign, reason in (
        (replace(market, native_id="OTHER-SWAP"), "RANKED_MARK_INSTRUMENT_MISMATCH"),
        (replace(market, canonical_id="other"), "RANKED_MARK_INSTRUMENT_MISMATCH"),
        (replace(market, mark=market.mark + 1), "RANKED_MARK_OBSERVATION_BASIS_MISMATCH"),
    ):
        rejected = run_hardened_wallclock_bridge_observation_cycle_v2(
            bridge_state=state,
            ticks=[tick],
            reference_price=quotes.mark,
            wall_now_unix=quotes.now,
            session_id=state.session_id,
            price_field="markPx",
            ranked_swap_observation=foreign,
        )
        assert not rejected.ok and reason in rejected.md_blockers
    assert history.records[-1] == added


def check_csop_slot4_sequence(
    tmp_path,
    monkeypatch,
    positions,
    prices,
    total_fees,
    final_equity,
    *,
    extra_steps=(),
    start=OBSERVED_UNIX,
    followup_interval=0.2,
):
    from copy import deepcopy
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.full_economic_reconstruction_verifier_v2 import (
        verify_full_economic_reconstruction_v2,
    )

    scope = next(s for s in RANKED_SWAP_SCOPES if s.base == "CSOPSKHYNIX2L")
    row = dict(_perp(scope.native_id, base=scope.base, ct_val="1"), tickSz="0.001", maxMktSz="1000")
    config, assignment = ranked_config(tmp_path, monkeypatch, row, scope)
    fx = D("1.001148")  # USDT per USDC
    quotes = RecordedQuotes(assignment.instrument, start)
    quotes.usdt_per_usdc = str(fx)
    # Archived opening mark 1.838, best bid 1.840 and ask 1.842.
    quotes.book_mid_offset = D("0.003")
    offsets_in_ticks = [2, 10, 20, 30, 40, 50, 60, 50, 40, 30, 20, 10, 0]
    two_levels = [(1, "2"), (2, "30")]
    steps = [
        (ticks * D("0.001"), [(1, "1")] if observation in (9, 10) else two_levels)
        for observation, ticks in enumerate(offsets_in_ticks, 1)
    ]
    initial_cash = D(10) * fx
    cycles, state, _ = exercise_ranked_entry(
        tmp_path,
        config,
        assignment,
        row,
        short=positions[0] < 0,
        start=start,
        price=D("1.858") if positions[0] < 0 else D("1.808"),
        move=D("0.010"),
        initial_equity=initial_cash,
        after_opening=[*steps, *extra_steps],
        followup_interval=followup_interval,
        transport=quotes,
    )
    filled = [cycle for cycle in cycles if cycle["fill"]]
    assert len(filled) == len(positions)
    assert [c["fill"] for c in filled] == state.fill_ledger
    opening, final = filled[0], filled[-1]
    assert D(opening["ranked_shadow_first_purchase"]["capacity"]["slot_available_usdc"]) == 10
    assert opening["ranked_shadow_first_purchase"]["entry"]["entry_action"] == "FIRST_PURCHASE"
    assert final is cycles[-1]
    assert all(not c["forced_wiring"] and not c["orders_authorized"] for c in cycles)
    assert all(
        D(c["portfolio_snapshot"]["params"]["initial_equity"]) == initial_cash for c in cycles
    )

    # Carry cash through each close and charge every fee on the executed quantity.
    cash = initial_cash
    position = 0
    fees = D(0)
    entry_price = D(0)
    for c, expected_price, next_position in zip(filled, prices, positions, strict=True):
        fill = c["fill"]
        price = D(expected_price)
        assert D(fill["fill_price"]) == price
        quantity = abs(next_position - position)
        assert D(fill["quantity_contracts"]) == D(fill["quantity"]) == quantity
        assert fill["side"] == ("BUY" if next_position > position else "SELL")
        fee = price * quantity * D("0.0002")
        assert D(fill["fee"]) == fee
        if position == 0:
            purchase = c["ranked_shadow_first_purchase"]
            assert (purchase["lane_id"], purchase["entry"]["venue_native_id"]) == (
                "LANE_4",
                scope.native_id,
            )
            assert D(purchase["valuation"]["usdc_per_usdt"]) == 1 / fx
            assert D(purchase["entry"]["entry_limit_usdc"]) == cash * (1 / fx)
            assert quantity * price + fee <= cash
            entry_price = price
        else:
            cash += position * (price - entry_price)
        cash -= fee
        fees += fee
        position = next_position
        account = c["portfolio_snapshot"]["state"]
        assert D(account["cash"]) == cash
        assert D(account["positions"][scope.canonical_id]["quantity"]) == position
        assert D(account["cumulative_fees"]) == fees

    openings = filled[::2]
    closes = filled[1::2]
    blocked_exits = [
        c for c in cycles if (c.get("ranked_shadow_exit") or {}).get("status") == "BLOCKED"
    ]
    for prior, blocked, close in zip(openings[1:-1], blocked_exits, closes[1:], strict=True):
        assert prior["cycle_index"] < blocked["cycle_index"] < close["cycle_index"]
        assert blocked["ranked_shadow_exit"]["reason"] == "SHADOW_INSUFFICIENT_EXECUTABLE_DEPTH"
        assert blocked["fill"] is None and blocked["intended_action"]["intended_side"] == "HOLD"
        held = blocked["portfolio_snapshot"]["state"]
        booked = prior["portfolio_snapshot"]["state"]
        assert (
            held["positions"][scope.canonical_id]["quantity"]
            == booked["positions"][scope.canonical_id]["quantity"]
        )
        assert held["cash"] == booked["cash"]

    for prior, close, reentry in zip(openings[:-1], closes, openings[1:], strict=True):
        assert close["ranked_shadow_exit"]["opening_fill_id"] == prior["fill_id"]
        assert close["ranked_shadow_position_scope"]["anchor_after"] is None
        receipt = reentry["ranked_shadow_first_purchase"]
        assert receipt["entry"]["entry_action"] == "REENTRY"
        assert receipt["entry"]["previous_exit_fill_id"] == close["fill_id"]
        progress = receipt["confirmation"]["progress"]
        assert progress["candidate_started_at_epoch"]["value"] > close["trading_epoch"]
        assert progress["distinct_confirmation_observation_count"] >= 2

    assert fees == D(total_fees)
    assert D(state.portfolio.snapshot()["state"]["equity"]) == D(final_equity)

    def reconstruct(journal):
        return verify_full_economic_reconstruction_v2(
            cycle_ledger=journal,
            fill_ledger=state.fill_ledger,
            final_portfolio_snapshot=state.portfolio.snapshot(),
            economic_metrics=state.portfolio.economic_metrics().to_dict(),
        )

    proof = reconstruct(cycles)
    assert proof.ok, proof.blockers
    assert proof.reconstructed_fill_count == len(positions)

    # A genuine fill from the preceding switch must not validate the last switch.
    last_close = closes[-1]
    wrong_close = deepcopy(cycles)
    exit_receipt = wrong_close[last_close["cycle_index"] - 1]["ranked_shadow_exit"]
    exit_receipt["opening_fill_id"] = openings[-3]["fill_id"]
    assert (
        f"RANKED_SHADOW_EXIT_LINKAGE_BREAK_{last_close['cycle_index']}"
        in reconstruct(wrong_close).blockers
    )
    wrong_reentry = deepcopy(cycles)
    entry = wrong_reentry[-1]["ranked_shadow_first_purchase"]["entry"]
    entry["previous_exit_fill_id"] = closes[-2]["fill_id"]
    assert (
        f"RANKED_REENTRY_LINKAGE_BREAK_{final['cycle_index']}"
        in reconstruct(wrong_reentry).blockers
    )
    return cycles, filled


class RecordedQuotes:
    def __init__(self, instrument, now):
        self.venue_instrument_id = instrument.venue_native_inst_id
        self.base = instrument.base_currency
        self.tick = D(instrument.tick_size)
        self.book_mid_offset = D(0)
        self.usdt_per_usdc = "1.04"
        self.now = now
        self.fx_requests = 0
        self.after_fx = lambda: None
        self.depth = [(1, "100000")]
        self.other_book = False

    def get_json(self, path, query):
        row = dict(instId=query["instId"], instType="SWAP", ts=str(int(self.now * 1000)))
        if row["instId"] == "USDC-USDT":
            row.update(idxPx=self.usdt_per_usdc)
            self.fx_requests += 1
            self.after_fx()
        elif path.endswith("/books"):
            if self.other_book:
                row.pop("instId")
                query = dict(query, instId="OTHER-USDT-SWAP")
            mid = self.mark + self.book_mid_offset
            row.update(
                bids=[[str(mid - ticks * self.tick), size] for ticks, size in self.depth],
                asks=[[str(mid + ticks * self.tick), size] for ticks, size in self.depth],
            )
        else:
            row.update(
                markPx=str(self.mark),
                idxPx=str(self.mark),
                oi="1000",
                vol24h="150000",
                fundingRate="0.001",
                fundingTime=str(int((self.now + 3600) * 1000)),
                minFundingRate="-0.01",
                maxFundingRate="0.01",
            )
        payload = dict(code="0", data=[row])
        return SimpleNamespace(
            payload=payload,
            body=json.dumps(payload).encode(),
            status=200,
            path=path,
            url=f"https://{CANONICAL_HOST}{path}?{urlencode(query)}",
        )


def exercise_ranked_entry(
    root,
    config,
    assignment,
    inventory,
    *,
    short,
    start,
    price,
    fault=None,
    move=None,
    after_opening=(),
    followup_interval=0.2,
    initial_equity=None,
    transport=None,
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )
    from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
    )

    i = assignment.instrument
    sid = json.loads(config.read_text())["session_id"]
    state = HardenedBridgeSessionStateV2(
        session_id=sid,
        instrument_id=i.canonical_instrument_id,
        venue_instrument_id=i.venue_native_inst_id,
    )
    state.portfolio = state.portfolio.from_params(
        replace(
            state.portfolio.model.params,
            linear_futures_collateral=True,
            initial_equity=initial_equity
            if initial_equity is not None
            else state.portfolio.model.params.initial_equity,
        )
    )
    tick = D(i.tick_size)
    move = tick if move is None else move
    last_minute = int(start // 60) * 60 - 60
    bars = []
    for j in range(61):
        close = str(price + (j % 3) * move)
        bars.append([str((last_minute - (60 - j) * 60) * 1000), close, close, close, close, "1"])
    g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=root / "g17",
        bound_instrument=SimpleNamespace(
            instrument_id=i.canonical_instrument_id, venue_native_id=i.venue_native_inst_id
        ),
        mark_candles_payload=dict(code="0", data=bars[::-1]),
        receive_or_capture_timestamp=str(int(start * 1000)),
    )
    assert g17.estimate_present, g17
    state.typed_volatility_cmc_binding_host = (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1(producer=g17.producer)
    )
    if transport is None:
        transport = RecordedQuotes(i, start)
    if i.venue_native_inst_id == "CSOPSKHYNIX2L-USDT-SWAP":
        if fault == "ten":
            transport.depth = [(1, "0.5"), (4, "100000")]
        if fault == "thin":
            transport.depth = [(1, "0.1")]
        transport.other_book = fault == "other_book"
    policy = load_slot_entry_budget_v1(
        REPO / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )
    handoff = RankedShadowFirstPurchaseV1(
        config,
        assignment,
        dict(code="0", data=[inventory]),
        policy,
        root / "recon",
        transport,
        lambda: transport.now + 0.05,
    )
    if fault == "selection":

        def change():
            cfg = json.loads(config.read_text())
            cfg["session_id"] = "other"
            config.write_text(json.dumps(cfg))

        transport.after_fx = change
    if fault == "stale":
        transport.after_fx = lambda: setattr(transport, "now", transport.now + 300)
    cycles = []
    state.mid_prices = [float(price + (j % 3) * move) for j in range(12)]

    def observe(j):
        market = collect_ranked_swap_observation_v1(
            assignment, root / str(j), lambda: transport.now, transport=transport
        )
        event = ObservationMarketTickV1(
            i.canonical_instrument_id,
            "OKX",
            "FUTURES",
            j + 1,
            market.market_event_unix,
            transport.now,
            0.0,
            float(transport.mark),
        )
        out = run_hardened_wallclock_bridge_observation_cycle_v2(
            bridge_state=state,
            ticks=[event],
            reference_price=transport.mark,
            wall_now_unix=transport.now,
            session_id=sid,
            price_field="markPx",
            ranked_swap_observation=market,
            ranked_entry=handoff,
        )
        if out.bridge_cycle is not None:
            cycles.append(out.bridge_cycle)

    for j in range(8):
        transport.now = start + j * 0.2
        transport.mark = price + (-1 if short else 1) * j * move
        if fault == "hold":
            transport.mark = price
        observe(j)
        if cycles and cycles[-1].get("ranked_shadow_first_purchase") and (fault or after_opening):
            break
    opened_at = transport.mark
    opening_time = transport.now
    for k, (offset, depth) in enumerate(after_opening, start=j + 1):
        transport.now = opening_time + (k - j) * followup_interval
        transport.mark = opened_at + (offset if short else -offset)
        transport.depth = depth
        observe(k)
    return cycles, state, transport.fx_requests


def ranked_config(tmp_path, monkeypatch, row, scope):
    chain = _build_chain(tmp_path, [row])
    universe = load_and_validate_universe_snapshot_v1(
        chain["universe_root"], expected_repository_sha=REPO_SHA
    ).snapshot
    assignment = RankedRunSlotV1(
        scope.lane_id,
        chain["selection"],
        universe.instruments[0],
        universe.snapshot_id,
        "fixture-transition",
        chain["selection_root"],
    )
    monkeypatch.setattr(selection, "read_ranked_run_slot_v1", lambda config: assignment)
    config = tmp_path / "slot.json"
    config.write_text(
        json.dumps(
            dict(
                session_id="ranked-test",
                lane=scope.lane_id,
                surface="SHADOW",
                native_instrument_id=scope.native_id,
                canonical_instrument_id=scope.canonical_id,
                n5_source={k: str(chain[k]) for k in ("ranking_root", "universe_root")},
            )
        )
    )
    return config, assignment


@pytest.mark.parametrize("short", [False, True], ids=["long", "short"])
@pytest.mark.parametrize(
    "scope,fault",
    [
        pytest.param(scope, fault, id=f"{scope.native_id}-{fault}")
        for scope in RANKED_SWAP_SCOPES
        for fault in (
            None,
            "selection",
            "stale",
            "hold",
            "ten",
            "below_minimum",
            "zero",
            "before_selection",
            "thin",
            "other_book",
        )
        if fault not in {"thin", "other_book"} or scope.native_id == "CSOPSKHYNIX2L-USDT-SWAP"
    ],
)
def test_ranked_analytical_first_purchase(tmp_path, monkeypatch, scope, short, fault):
    row = dict(
        _perp(scope.native_id, base=scope.base, ct_val="2"),
        maxMktSz="1000",
        lotSz="0.1",
        minSz="0.2",
    )
    config, assignment = ranked_config(tmp_path, monkeypatch, row, scope)
    if fault in {"ten", "below_minimum", "zero"}:
        cfg = json.loads(config.read_bytes())
        cfg["shadow_entry_cost_limit_usdc"] = {"ten": "10", "below_minimum": "0.60", "zero": "0"}[
            fault
        ]
        config.write_text(json.dumps(cfg))
    cycles, state, requests = exercise_ranked_entry(
        tmp_path,
        config,
        assignment,
        row,
        short=short,
        start=OBSERVED_UNIX - 6 if fault == "before_selection" else OBSERVED_UNIX,
        price=D("2.00"),
        fault=fault,
    )
    purchases = [
        c["ranked_shadow_first_purchase"] for c in cycles if c.get("ranked_shadow_first_purchase")
    ]
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.full_economic_reconstruction_verifier_v2 import (
        verify_full_economic_reconstruction_v2,
    )

    proof = verify_full_economic_reconstruction_v2(
        cycle_ledger=cycles,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=state.portfolio.snapshot(),
        economic_metrics=state.portfolio.economic_metrics().to_dict(),
    )
    assert proof.ok, proof.blockers
    if fault == "hold":
        assert not requests and not state.fill_ledger and not state.ranked_confirmed_entry_budget
        return
    if fault == "before_selection":
        assert len(purchases) == 1
        assert purchases[0]["reason_codes"] == ["SHADOW_ENTRY_SELECTION_NOT_YET_OBSERVED"]
        assert (
            not requests and not state.fill_ledger and state.ranked_confirmed_entry_budget is None
        )
        return
    assert len(purchases) == requests == 1, [(p["status"], p["reason_codes"]) for p in purchases]
    purchase = purchases[0]
    if fault and fault != "ten":
        assert purchase["status"] == "BLOCKED" and purchase["reason_codes"]
        if fault == "thin":
            assert purchase["reason_codes"] == ["SHADOW_FIRST_PURCHASE_MINIMUM_LOT_NOT_ADMITTED"]
        if fault == "other_book":
            assert purchase["reason_codes"] == ["SHADOW_FIRST_PURCHASE_BOOK_SOURCE_MISMATCH"]
        assert not state.fill_ledger and state.ranked_confirmed_entry_budget is None
        return
    assert purchase["status"] == "FILLED", purchase["reason_codes"]
    assert len(state.fill_ledger) == 1
    fill = state.fill_ledger[0]
    entry = purchase["entry"]
    assert entry == state.ranked_confirmed_entry_budget
    assert entry["lane_id"] == scope.lane_id and entry["venue_native_id"] == scope.native_id
    assert entry["direction"] == ("short" if short else "long")
    assert entry["first_purchase_side"] == fill["side"] == ("SELL" if short else "BUY")
    assert D(fill["quantity_contracts"]) * 2 == D(fill["quantity"])
    assert (
        D(entry["nominal_usdc"])
        == D(entry["nominal_usdt"]) * D(purchase["valuation"]["usdc_per_usdt"])
        < 25
    )
    if fault == "ten":
        assert (
            D(entry["nominal_usdc"]) <= 10 and D(purchase["capacity"]["slot_available_usdc"]) == 25
        )
    assert purchase["budget"]["reserved_amount"] is None
    position = selection.observe_ranked_shadow_positions_v1(
        state, assignment, session_id=state.session_id, now=OBSERVED_UNIX + 2
    )
    assert position.positions[0].signed_quantity == (-1 if short else 1) * D(
        entry["quantity_contracts"]
    )
    from copy import deepcopy
    from src.ops.ranked_shadow_first_purchase_v1 import verify_ranked_first_purchase_v1

    cycle = deepcopy(next(c for c in cycles if c.get("fill")))
    if scope.native_id == "CSOPSKHYNIX2L-USDT-SWAP":
        mark = D(fill["mark_price"])
        tick = D(assignment.instrument.tick_size)
        count = D(fill["quantity_contracts"])
        ticks = D(1)
        if fault == "ten":
            assert count > D("0.5")
            ticks = (D("0.5") + (count - D("0.5")) * 4) / count
            assert 1 < ticks < 4
        expected = ((mark / tick) + (-ticks if short else ticks)).to_integral_value(
            rounding=ROUND_FLOOR if short else ROUND_CEILING
        ) * tick
        assert D(fill["fill_price"]) == D(entry["opening_book_usdt_per_base"]) == expected
        assert state.portfolio.model.state.positions[scope.canonical_id].avg_entry_price == expected
        notional = count * 2 * expected
        fee = notional * state.portfolio.model.params.fee_rate_bps / 10000
        assert D(fill["notional"]) == notional and D(fill["fee"]) == fee
        assert (
            (notional + fee) * D(purchase["valuation"]["usdc_per_usdt"])
            <= D(entry["entry_limit_usdc"])
            == 10
        )
        for key in ("fill_price", "fee_amount"):
            changed = deepcopy(cycle)
            changed["fill"][key] = "0"
            assert not verify_ranked_first_purchase_v1(changed)
        changed = deepcopy(cycle)
        changed["ranked_shadow_first_purchase"]["entry"]["fill_book"]["body"] += " "
        assert not verify_ranked_first_purchase_v1(changed)
        changed_ledger = [dict(fill, fee="0")]
        assert not verify_full_economic_reconstruction_v2(
            cycle_ledger=cycles,
            fill_ledger=changed_ledger,
            final_portfolio_snapshot=state.portfolio.snapshot(),
            economic_metrics=state.portfolio.economic_metrics().to_dict(),
        ).ok
    else:
        assert "fill_book" not in entry
        slip = state.portfolio.model.params.slippage_bps / 10000
        assert D(fill["fill_price"]) == D(fill["mark_price"]) * (1 - slip if short else 1 + slip)
    cycle["ranked_shadow_first_purchase"]["entry"]["nominal_usdc"] = "0.01"
    assert not verify_ranked_first_purchase_v1(cycle)
