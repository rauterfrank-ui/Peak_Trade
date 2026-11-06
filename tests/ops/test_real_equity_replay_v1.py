"""Independent synthetic cash postings, transfers and adversarial replay."""

from copy import deepcopy
from decimal import Decimal, localcontext

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_replay_v1 import (
    RealEquityReplayError,
    compare_native_display_v1,
    reconcile_real_equity_window_v1,
)
from tests.ops.test_real_equity_journal_v1 import ACCOUNT, balance_row

CUTOFF = 1789407907317


def bill(bid, offset, ccy, delta, bal, kind, **extra):
    return dict(
        billId=str(bid),
        ts=str(CUTOFF + offset),
        ccy=ccy,
        balChg=delta,
        bal=bal,
        type=kind[0],
        subType=kind[1],
        interest="0",
        fee="0",
        pnl="0",
        **extra,
    )


def fixture():
    initial_usdc = balance_row(cash="10", eq="9", upl="-1")
    initial_usdc["uTime"] = str(CUTOFF - 2000)
    initial_eur = balance_row(ccy="EUR", cash="0.5", eq="0.5")
    initial_eur["uTime"] = str(CUTOFF - 1000)
    opening = dict(
        candidate=dict(
            account_identity=ACCOUNT,
            settlement_currency="USDC",
            equity_value="9",
            as_of_time="2026-09-14T17:45:07Z",
        ),
        config=dict(acctLv="2", uid=ACCOUNT, posMode="net_mode", autoLoan=False),
        historical_anchor_validated=True,
        balance=dict(uTime=str(CUTOFF), isoEq="0", details=[initial_usdc, initial_eur]),
    )
    rows = [
        bill(100, -2000, "USDC", "10", "10", ("1", "11")),
        bill(101, -1000, "EUR", "0.5", "0.5", ("1", "11")),
        bill(
            102,
            1000,
            "USDC",
            "-0.1",
            "9.9",
            ("8", "173"),
            instType="FUTURES",
            mgnMode="cross",
            instId="SUI-X",
        ),
    ]
    rows[-1]["pnl"] = "-0.1"
    rows.append(
        bill(
            103,
            2000,
            "USDC",
            "-1.01",
            "8.89",
            ("2", "2"),
            instType="FUTURES",
            mgnMode="cross",
            instId="SUI-X",
            ordId="o1",
            tradeId="t1",
        )
    )
    rows[-1].update(pnl="-1", fee="-0.01")
    rows.append(
        bill(104, 3000, "EUR", "2", "2.5", ("1", "11"), sz="2", **{"from": "6", "to": "18"})
    )
    rows += [
        bill(
            105,
            4000,
            "USDC",
            "2.25",
            "11.14",
            ("30", "320"),
            sz="2.25",
            instId="USDC-EUR",
            tradeId="s1",
            px="0.8888",
        ),
        bill(
            106,
            4000,
            "EUR",
            "-2",
            "0.5",
            ("30", "321"),
            sz="2",
            instId="USDC-EUR",
            tradeId="s1",
            px="0.8888",
        ),
        bill(
            107, 5000, "BTC", "0.001", "0.001", ("1", "11"), sz="0.001", **{"from": "6", "to": "18"}
        ),
        bill(
            108,
            6000,
            "BTC",
            "-0.001",
            "0",
            ("27", "319"),
            sz="0.001",
            instId="BTC-USDC",
            tradeId="c1",
            px="50000",
        ),
        bill(
            109,
            6000,
            "USDC",
            "50",
            "61.14",
            ("27", "318"),
            sz="50",
            instId="BTC-USDC",
            tradeId="c1",
            px="50000",
        ),
    ]
    configs = [dict(uid=ACCOUNT, acctLv="2", posMode="net_mode", autoLoan=False)]
    top = [
        dict(
            details=[
                balance_row(cash="61.14", eq="61.14"),
                balance_row(ccy="EUR", cash="0.5", eq="0.5"),
            ],
            isoEq="0",
            totalEq="61.64",
        )
    ]
    funding_balances = [dict(ccy="EUR", bal="3", availBal="3", frozenBal="0")]
    specs = [
        ("config_before", "/api/v5/account/config", configs),
        ("balance_before", "/api/v5/account/balance", top),
        ("positions_before", "/api/v5/account/positions", []),
        ("archive_0", "/api/v5/account/bills-archive?limit=100", list(reversed(rows))),
        ("archive_1", "/api/v5/account/bills-archive?limit=100&after=100", []),
        ("recent_0", "/api/v5/account/bills?limit=100", []),
        ("funding_balance", "/api/v5/asset/balances", funding_balances),
        ("positions_after", "/api/v5/account/positions", []),
        ("balance_after", "/api/v5/account/balance", top),
        ("config_after", "/api/v5/account/config", configs),
    ]
    trading = {
        name: dict(index=i, endpoint=path, rows=deepcopy(values))
        for i, (name, path, values) in enumerate(specs)
    }
    types = {}
    for row in rows:
        types.setdefault(row["type"], set()).add(row["subType"])
    taxonomy = [
        dict(
            type=t,
            subTypeDetails=[
                dict(subType=s, subTypeDesc="observed test label") for s in sorted(subs)
            ],
        )
        for t, subs in types.items()
    ]
    frows = [
        dict(billId="200", ts=str(CUTOFF - 1000), ccy="EUR", type="1", balChg="5", bal="5"),
        dict(billId="201", ts=str(CUTOFF + 3000), ccy="EUR", type="131", balChg="-2", bal="3"),
        dict(billId="202", ts=str(CUTOFF + 4500), ccy="BTC", type="1", balChg="0.001", bal="0.001"),
        dict(billId="203", ts=str(CUTOFF + 5000), ccy="BTC", type="131", balChg="-0.001", bal="0"),
    ]
    fspecs = [
        ("config_before", "/api/v5/account/config", configs),
        ("funding_before", "/api/v5/asset/balances", funding_balances),
        ("bill_taxonomy", "/api/v5/account/subtypes", taxonomy),
        ("funding_history_0", "/api/v5/asset/bills-history?limit=100", list(reversed(frows))),
        (
            "funding_history_1",
            "/api/v5/asset/bills-history?limit=100&after=" + str(CUTOFF - 1000),
            [],
        ),
        ("funding_after", "/api/v5/asset/balances", funding_balances),
        ("config_after", "/api/v5/account/config", configs),
    ]
    funding = {
        name: dict(index=i, endpoint=path, rows=deepcopy(values))
        for i, (name, path, values) in enumerate(fspecs)
    }
    tm = dict(account_identity=ACCOUNT, completed_at="2026-11-03T22:02:20+00:00")
    return opening, tm, trading, deepcopy(tm), funding


def test_forward_ledger_matches_without_double_counting_pnl_fees_or_old_upl():
    r = reconcile_real_equity_window_v1(*fixture())
    usdc = next(c for c in r["trading_currencies"] if c["currency"] == "USDC")
    assert usdc["reconstructed_end_cash_and_flat_equity"] == "61.14"
    assert usdc["signed_cash_by_class"] == {
        "CONVERT_IN": "50",
        "FUNDING_EXPENSE": "-0.1",
        "FUTURES_EXECUTION": "-1.01",
        "SIMPLE_BUY": "2.25",
    }
    assert r["initial_upl_replaced_not_double_counted"] == "-1"
    assert r["window_trading_posting_count"] == 8
    assert r["funding"]["observed_window_posting_count"] == 3
    assert r["exact_decimal_equality_to_all_snapshot_fields"]
    assert r["blocking_for_exact_authoritative_equity_source"] == []
    assert not r["available_for_sizing_produced"] and not r["capital_admitted"]


def test_native_precision_difference_is_not_rounded_away_or_called_exact():
    with localcontext() as ctx:
        ctx.prec = 120
        comparison = compare_native_display_v1(Decimal("725.4691081539303132"), "725.4691081539303")
        assert comparison["observed_minus_exact"] == "-0.0000000000000132"
        assert comparison["binary64_shortest_rendering_matches"]
        assert not comparison["exact_equal"] and not comparison["rounding_authority_assumed"]


@pytest.mark.parametrize(
    "change,reason",
    [
        ("missing_funding", "CHAIN_BREAK"),
        ("unknown", "UNKNOWN_ECONOMIC_KIND"),
        ("missing_conversion_leg", "COUNTERPART_MISSING"),
        ("fee", "COMPONENT_MISMATCH"),
        ("open_position", "OPEN_POSITION_VALUATION_UNSUPPORTED"),
        ("wrong_account", "ACCOUNT_MISMATCH"),
        ("no_terminal", "PAGINATION_NOT_EXHAUSTED"),
        ("filtered", "REQUEST_SCOPE_INVALID"),
        ("liability", "LIABILITY_OR_INTEREST_UNSUPPORTED"),
        ("stale_retention", "RETENTION"),
        ("changed_snapshot", "CHANGED_DURING_ACQUISITION"),
        ("funding_gap", "UNMATCHED_TRADING_TRANSFER"),
        ("funding_unknown", "UNKNOWN_FUNDING_KIND"),
        ("funding_money_gap", "COUNTERPART_CASH_UNEXPLAINED"),
        ("missing_amount", "BILL_DECIMAL_INVALID"),
        ("no_taxonomy", "UNKNOWN_ECONOMIC_KIND"),
        ("wrong_capture_order", "ACQUISITION_ORDER_INVALID"),
        ("wrong_balance_account", "BALANCE_ACCOUNT_MISMATCH"),
        ("funding_intermediate_gap", "FUNDING_INTERMEDIATE_BALANCE_UNEXPLAINED"),
        ("unknown_conversion_price", "BILL_DECIMAL_INVALID"),
    ],
)
def test_economic_or_provenance_gaps_fail_closed(change, reason):
    o, tm, t, fm, f = fixture()
    rows = t["archive_0"]["rows"]
    if change == "missing_funding":
        rows[:] = [r for r in rows if r["billId"] != "102"]
    elif change == "unknown":
        next(r for r in rows if r["billId"] == "103")["type"] = "999"
    elif change == "missing_conversion_leg":
        rows[:] = [r for r in rows if r["billId"] != "108"]
    elif change == "fee":
        next(r for r in rows if r["billId"] == "103")["fee"] = "0"
    elif change == "open_position":
        t["positions_after"]["rows"] = [{"pos": "1"}]
    elif change == "wrong_account":
        fm["account_identity"] = "other"
    elif change == "no_terminal":
        older = deepcopy(rows[-1])
        older["billId"] = "99"
        t["archive_1"]["rows"] = [older]
    elif change == "filtered":
        t["archive_0"]["endpoint"] += "&ccy=USDC"
    elif change == "liability":
        for label in ("balance_before", "balance_after"):
            t[label]["rows"][0]["details"][0]["liab"] = "1"
    elif change == "stale_retention":
        tm["completed_at"] = "2027-02-03T22:00:00+00:00"
    elif change == "changed_snapshot":
        t["balance_after"]["rows"][0]["details"][0]["cashBal"] = "61.15"
    elif change == "funding_gap":
        f["funding_history_0"]["rows"] = [
            r for r in f["funding_history_0"]["rows"] if r["billId"] != "201"
        ]
    elif change == "funding_unknown":
        f["funding_history_0"]["rows"][0]["type"] = "999"
    elif change == "funding_money_gap":
        for records, label in ((t, "funding_balance"), (f, "funding_before"), (f, "funding_after")):
            records[label]["rows"][0].update(bal="3.01", availBal="3.01")
    elif change == "missing_amount":
        rows[0]["balChg"] = ""
    elif change == "no_taxonomy":
        f["bill_taxonomy"]["rows"] = []
    elif change == "wrong_capture_order":
        t["balance_before"]["index"] = 8
    elif change == "wrong_balance_account":
        t["balance_after"]["rows"][0]["uid"] = "other"
    elif change == "funding_intermediate_gap":
        next(r for r in f["funding_history_0"]["rows"] if r["billId"] == "201")["bal"] = "3.01"
    elif change == "unknown_conversion_price":
        next(r for r in rows if r["billId"] == "109")["px"] = ""
    with pytest.raises((ValueError, RealEquityReplayError), match=reason):
        reconcile_real_equity_window_v1(o, tm, t, fm, f)
