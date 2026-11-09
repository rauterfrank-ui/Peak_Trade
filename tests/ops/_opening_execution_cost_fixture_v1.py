"""Explicit simulated GETs injected at the actual current N1 financial seam."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import hashlib
import json

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as invoke,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost


def attach_costs(kwargs, *, taker="-0.0005", fault=None):
    injected = kwargs["injected"]
    bound = kwargs["bound_instrument"]
    epoch = kwargs["decision_epoch"]
    cycle = kwargs["portfolio_slot"].cycle_id
    stamp = str(int(datetime.fromisoformat(epoch.replace("Z", "+00:00")).timestamp() * 1000))
    instruments = deepcopy(injected.instruments_payload)
    native = bound.venue_native_id
    row = next(r for r in instruments["data"] if r["instId"] == native)
    family = "-".join(native.split("-")[:2])
    row.update(instFamily=family, groupId="explicit-fixture-group", ctMult="1")
    index = deepcopy(injected.index_tickers_payload)
    if index is not None:
        for r in index["data"]:
            r["ts"] = stamp
    acquisition = cost.canonical(dict(decision_epoch=epoch, cycle_id=cycle))
    mark = Decimal(str(kwargs["replay"].intermediate.market_context.mark_price))
    account = injected.expected_account_identity

    def source(endpoint, payload, private=False):
        return FreshPretradeGetTransportResultV1(
            True,
            "GET",
            endpoint,
            200,
            payload,
            private,
            "EXPLICIT_SYNTHETIC_COST_SOURCE",
            False,
            False,
            "",
            hashlib.sha256(cost.canonical(payload).encode()).hexdigest(),
            pretrade_decision_id=acquisition,
            acquired_at_utc=epoch,
        )

    sources = {
        "account": source("/api/v5/account/config", dict(code="0", data=[dict(uid=account)]), True),
        "instruments": source(
            f"/api/v5/public/instruments?instType={row['instType']}&instId={native}", instruments
        ),
        "fees": source(
            f"/api/v5/account/trade-fee?instType={row['instType']}&instFamily={family}",
            dict(
                code="0",
                data=[
                    dict(
                        instType=row["instType"],
                        ts=stamp,
                        feeGroup=[dict(groupId=row["groupId"], maker="0.0002", taker=taker)],
                    )
                ],
            ),
            True,
        ),
        "book": source(
            f"/api/v5/market/books?instId={native}&sz=20",
            dict(
                code="0",
                data=[
                    dict(
                        ts=stamp,
                        bids=[[str(mark - Decimal("0.01")), "100000", "0", "1"]],
                        asks=[[str(mark + Decimal("0.01")), "100000", "0", "1"]],
                    )
                ],
            ),
        ),
    }
    if fault == "missing-book":
        sources["book"] = replace(sources["book"], payload=dict(code="0", data=[]))
    elif fault == "wrong-group":
        sources["fees"].payload["data"][0]["feeGroup"][0]["groupId"] = "foreign"
    elif fault == "top-level-fees":
        r = sources["fees"].payload["data"][0]
        r.pop("feeGroup")
        r.update(taker="-0.0001", takerU="-0.0001", takerUSDC="-0.0001")
    elif fault == "wrong-family":
        sources["fees"] = replace(
            sources["fees"],
            endpoint=f"/api/v5/account/trade-fee?instType={row['instType']}&instFamily=FOREIGN-USDT",
        )
    elif fault == "wrong-account":
        sources["account"].payload["data"][0]["uid"] = "foreign-account"
    elif fault == "no-auth":
        sources["fees"] = replace(sources["fees"], auth_header_sent=False)
    elif fault == "reused-get":
        sources["fees"] = replace(sources["fees"], historical_reuse=True)
    elif fault == "foreign-acquisition":
        sources["book"] = replace(sources["book"], pretrade_decision_id="foreign")
    elif fault in {"future-book", "stale-book"}:
        sources["book"].payload["data"][0]["ts"] = str(
            int(stamp) + (1000 if fault == "future-book" else -60000)
        )
    elif fault == "insufficient-depth":
        for key in ("bids", "asks"):
            sources["book"].payload["data"][0][key][0][1] = "0.00000001"
    elif fault == "crossed-book":
        sources["book"].payload["data"][0]["bids"][0][0] = str(mark + 1)

    class ExplicitPort:
        calls = []

        def get(self, *, endpoint, auth_required, pretrade_decision_id, get_cache_policy):
            self.calls.append(endpoint)
            assert pretrade_decision_id == acquisition
            matches = [r for r in sources.values() if r.endpoint == endpoint]
            if not matches and fault == "wrong-family" and "/account/trade-fee?" in endpoint:
                return sources["fees"]
            assert len(matches) == 1
            result = matches[0]
            if fault != "no-auth":
                assert result.auth_header_sent == auth_required
            return result

    port = ExplicitPort()
    # A malformed transport response remains an explicit injected response;
    # the collector requests the original correct grammar in every case.
    observation = cost.collect_entry_execution_cost_observation_v1(
        transport=port,
        account_identity=account,
        bound_instrument=bound,
        inst_type=row["instType"],
        decision_epoch=epoch,
        cycle_id=cycle,
    )
    assert len(port.calls) == 4
    kwargs["injected"] = replace(
        injected,
        instruments_payload=instruments,
        index_tickers_payload=index,
        opening_cost_observation=observation,
    )
    return observation


def install_cost_probe(monkeypatch, *, taker="-0.0005", fault=None):
    original = invoke.join_current_productive_enter_live_29p_before_venue_plan_v1
    captures, clock = [], [""]
    monkeypatch.setattr(cost, "utc_now_iso_v1", lambda: clock[0])

    def observe(**kwargs):
        clock[0] = kwargs["decision_epoch"]
        attach_costs(kwargs, taker=taker, fault=fault)
        result = original(**kwargs)
        captures.append((kwargs, result, kwargs["portfolio_budget_owner"].risk_snapshot_v1()))
        return result

    monkeypatch.setattr(
        invoke, "join_current_productive_enter_live_29p_before_venue_plan_v1", observe
    )
    return captures, clock
