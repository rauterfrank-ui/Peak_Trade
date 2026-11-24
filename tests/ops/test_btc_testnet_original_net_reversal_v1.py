"""Original Core L10 and actual Demo read code, with HTTP replaced at the socket."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlsplit
import json
import pytest
from tests.ops.test_btc_demo_entry_submit_v1 import entry_send as entry_send
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)

from scripts.ops.inspect_btc_demo_account_v1 import reversal_pretrade_reader
from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_net_reversal_pretrade_v1 import BtcDemoNetReversalPretradeV1
from tests.ops.test_btc_testnet_original_execution_receipt_v1 import (
    original_testnet_entry as original_testnet_entry,
    demo_entry as demo_entry,
)
from tests.ops.test_btc_testnet_original_occupied_core_v1 import inputs
from tests.ops.test_inspect_btc_demo_account_v1 import Response
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def reversal_inputs(world, monkeypatch, fault=None):
    pairs, kw = inputs(world, monkeypatch, adverse=True)
    calls = []

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return world["now"] if tz is None else world["now"].astimezone(tz)

    monkeypatch.setattr(demo, "datetime", Clock)

    class Opener:
        def open(self, request, timeout):
            assert request.get_method() == "GET" and request.data is None
            assert request.get_header("X-simulated-trading") == "1"
            path = urlsplit(request.full_url).path
            calls.append(request.selector)
            if path == "/api/v5/public/instruments":
                rows = [
                    dict(
                        world["payloads"]["instruments"]["data"][0], settleCcy="USD", quoteCcy="USD"
                    )
                ]
            elif path == "/api/v5/account/max-size":
                rows = [dict(instId=world["bound"].venue_native_id, maxBuy="1000", maxSell="1000")]
                if fault == "limit":
                    rows[0].update(maxBuy="0.0004", maxSell="0.0004")
            else:
                keys = [
                    key
                    for key, (p, q) in demo.BTC_DEMO_PRETRADE_QUERIES_V1.items()
                    if request.selector == p + ("?" + demo.urlencode(q) if q else "")
                ]
                assert len(keys) == 1
                key = keys[0]
                rows = deepcopy(world["payloads"][key]["data"])
                if key == "book":
                    mark = Decimal(str(kw["mark_px"]))
                    rows[0].update(
                        ts=str(int(world["now"].timestamp() * 1000)),
                        asks=[
                            [str(mark + Decimal("0.1")), "0.0002"],
                            [str(mark + Decimal("0.2")), "100"],
                        ],
                        bids=[
                            [str(mark - Decimal("0.1")), "0.0002"],
                            [str(mark - Decimal("0.2")), "100"],
                        ],
                    )
                    if fault == "depth":
                        for side in ("asks", "bids"):
                            rows[0][side][0][1] = "0.0001"
                            rows[0][side][1][1] = "0.0002"
                if key == "fees" and fault == "fee":
                    for group in rows[0]["feeGroup"]:
                        group["taker"] = "-0.1"
                if key == "funding":
                    rows[0]["ts"] = str(int(world["now"].timestamp() * 1000))
                if key == "positions":
                    rows = deepcopy(world["context"].occupancy_payloads["POSITIONS"]["data"])
                    if fault == "position":
                        rows[0]["pos"] = str(Decimal(rows[0]["pos"]) * 2)
            return Response(request.full_url, rows)

    monkeypatch.setattr(demo, "build_opener", lambda *_: Opener())
    reader = reversal_pretrade_reader("fixture-key", "fixture-secret", "fixture-phrase")
    provider = BtcDemoNetReversalPretradeV1(
        reader, world["bound"], world["host"].account, world["host"].clock, world["movement_input"]
    )
    old = kw["live_29p_injected_by_lane"]["LANE_3"]
    kw["live_29p_injected_by_lane"] = {
        "LANE_3": replace(old, testnet_reversal_pretrade_provider=provider)
    }
    return pairs, kw, calls


def test_original_l10_prepares_cost_bound_demo_net_order_without_submit(
    original_testnet_entry, monkeypatch
):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    )
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
    )

    world = original_testnet_entry
    pairs, kw, calls = reversal_inputs(world, monkeypatch)
    before = world["host"].owner.local_commitment_readback_v1().commitments
    result = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kw)["LANE_3"]
    governed = result.governed_cycle_result
    plan = governed.position_management_reversal
    assert plan is not None, governed.first_genuine_blocker
    assert plan.episode.episode_id == world["episode"].identity.episode_id
    assert plan.current_contracts * plan.target_contracts < 0
    assert plan.slot_capital_basis_usdc == 25
    assert len(calls) == 11
    assert governed.post_count == 0 and not governed.permit_created
    assert world["host"].owner.local_commitment_readback_v1().commitments == before
    scope = read_occupied_scope_mark_snapshot_v1(world["demo"].cursor_root)
    assert scope["mark"]["pending_reversal_episode_id"] == plan.episode.episode_id
    from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
        DirectDoublePlayReversalV1,
    )

    assert DirectDoublePlayReversalV1.from_dict_v1(plan.to_dict_v1()) == plan
    record = json.loads(plan.financial_receipt_json)
    assert Decimal(record["net_order_cost"]["order_cost"]["quantity"]) == abs(
        plan.current_contracts
    ) + abs(plan.target_contracts)
    assert Decimal(record["net_order_cost"]["order_cost"]["fee_usdc"]) > 0
    assert record["sizing"]["native_initial_margin_binding"] is not None
    from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
        capture_n1_venue_quantity_limits_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.entry_execution_cost_v1 import (
        FreshPretradeGetTransportResultV1,
    )

    acquisition = json.loads(
        record["sizing"]["entry_cost_binding"]["observation"]["acquisition_decision_id"]
    )
    with pytest.raises(ValueError, match="SOURCE_NOT_TRUSTED"):
        capture_n1_venue_quantity_limits_v1(
            results={
                "instruments": FreshPretradeGetTransportResultV1(
                    **record["original_sources"]["quantity_public"]
                ),
                "max_size": FreshPretradeGetTransportResultV1(
                    **record["original_sources"]["quantity_private"]
                ),
            },
            acquisition_decision_id=record["sizing"]["entry_cost_binding"]["observation"][
                "acquisition_decision_id"
            ],
            account_identity=record["account"],
            bound_instrument=world["bound"],
            decision_epoch=plan.decision_epoch,
            cycle_id=acquisition["cycle_id"],
        )
    for fault in ("quote", "body", "fee", "missing"):
        altered = plan.to_dict_v1()
        financial = deepcopy(record)
        if fault == "quote":
            altered["quote_to_usdc"] = "2"
        elif fault == "body":
            financial["original_bodies"]["book"] = "00"
        elif fault == "fee":
            financial["net_order_cost"]["order_cost"]["fee_usdc"] = "0"
        else:
            financial = {}
        if fault != "quote":
            altered["financial_receipt_json"] = json.dumps(financial)
        with pytest.raises((ValueError, KeyError)):
            DirectDoublePlayReversalV1.from_dict_v1(altered)


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("depth", "DEPTH_INSUFFICIENT"),
        ("limit", "VENUE_QUANTITY_EXCEEDS_MAX"),
        ("fee", "MOVEMENT"),
        ("position", "POSITION_MISMATCH"),
    ],
)
def test_cost_or_position_gap_blocks_original_demo_net_order(
    original_testnet_entry, monkeypatch, fault, reason
):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    )

    world = original_testnet_entry
    pairs, kw, calls = reversal_inputs(world, monkeypatch, fault=fault)
    before = world["host"].owner.local_commitment_readback_v1().commitments
    governed = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kw)[
        "LANE_3"
    ].governed_cycle_result
    assert governed.position_management_reversal is None
    assert reason in governed.first_genuine_blocker, governed.first_genuine_blocker
    assert len(calls) == 11
    assert governed.post_count == 0 and not governed.permit_created
    assert world["host"].owner.local_commitment_readback_v1().commitments == before
