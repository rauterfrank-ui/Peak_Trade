"""The two flat ranked Shadow swaps consume a genuine decision and native sized amount."""

from dataclasses import replace
from decimal import Decimal as D
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


class RecordedQuotes:
    def __init__(self, instrument, now):
        self.venue_instrument_id = instrument.venue_native_inst_id
        self.base = instrument.base_currency
        self.tick = D(instrument.tick_size)
        self.now = now
        self.fx_requests = 0
        self.after_fx = lambda: None

    def get_json(self, path, query):
        row = dict(instId=query["instId"], instType="SWAP", ts=str(int(self.now * 1000)))
        if row["instId"] == "USDC-USDT":
            row.update(idxPx="1.04")
            self.fx_requests += 1
            self.after_fx()
        elif path.endswith("/books"):
            row.update(
                bids=[[str(self.mark - self.tick), "100000"]],
                asks=[[str(self.mark + self.tick), "100000"]],
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
    root, config, assignment, inventory, *, short, start, price, fault=None, move=None
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
        replace(state.portfolio.model.params, linear_futures_collateral=True)
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
    transport = RecordedQuotes(i, start)
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
    for j in range(8):
        transport.now = start + j * 0.2
        transport.mark = price + (-1 if short else 1) * j * move
        if fault == "hold":
            transport.mark = price
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
            purchase = cycles[-1].get("ranked_shadow_first_purchase")
            if purchase and fault:
                break
    return cycles, state, transport.fx_requests


@pytest.mark.parametrize("scope", RANKED_SWAP_SCOPES, ids=lambda s: s.native_id)
@pytest.mark.parametrize("short", [False, True], ids=["long", "short"])
@pytest.mark.parametrize(
    "fault",
    [None, "selection", "stale", "hold", "ten", "below_minimum", "zero", "before_selection"],
)
def test_ranked_analytical_first_purchase(tmp_path, monkeypatch, scope, short, fault):
    row = dict(
        _perp(scope.native_id, base=scope.base, ct_val="2"),
        maxMktSz="1000",
        lotSz="0.1",
        minSz="0.2",
    )
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
    cycle["ranked_shadow_first_purchase"]["entry"]["nominal_usdc"] = "0.01"
    assert not verify_ranked_first_purchase_v1(cycle)
