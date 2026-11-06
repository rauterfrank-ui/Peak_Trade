"""Bounded factual equity reconstruction within the existing equity owner.

Distinct from AVAILABLE_FOR_SIZING: no U04, P01, reservations or capital mint.
Native cash postings are counted once. Display residuals stay explicit; a
binary64 rendering match is a diagnostic, never a tolerance/authority grant.
Current valuation supports flat Futures-mode accounts only, fail closed otherwise.
"""

from datetime import datetime, timezone
from decimal import Decimal, localcontext
from hashlib import sha256
import math
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

from src.ops.okx_eea_private_account_state_runtime_v1.bills_observation_v1 import (
    _amount,
    _integer,
    audit_bill_pages_v1,
    canonical_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_journal_v1 import (
    RealEquityJournalError,
    unique_json_v1,
)


class RealEquityReplayError(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise RealEquityReplayError(reason)


def amount_v1(value):
    return _amount(value, "equity_term")


def text_decimal_v1(value):
    return format(value, "f")


def compare_native_display_v1(exact, observed):
    """Keep exact residual; separately test a named, deterministic rendering.

    No epsilon and no changed ledger value. Venue documentation does not promise
    binary64 formatting. A match is an observed representation explanation only.
    """
    observed = amount_v1(observed)
    rendered = float(exact)
    _require(math.isfinite(rendered), "EQUITY_DISPLAY_OVERFLOW")
    return {
        "exact_decimal": text_decimal_v1(exact),
        "observed_decimal": text_decimal_v1(observed),
        "exact_equal": exact == observed,
        "observed_minus_exact": text_decimal_v1(observed - exact),
        "binary64_shortest_rendering_matches": Decimal(repr(rendered)) == observed,
        "rounding_authority_assumed": False,
    }


def load_historical_opening_v1(repo_root, *, expected_account_identity):
    from scripts.ops.verify_historical_accounting_sources_v1 import verify_historical_sources_v1
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
        semantic_candidate_digest_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_ratification_v1 import (
        ratification_digest_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
        anchor_digest_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_kind_set_membership_v1 import (
        membership_digest_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
        verify_manifest_sha256_v1,
    )

    root = Path(repo_root)
    historical = verify_historical_sources_v1(root)
    names = historical["sources_sha256"]
    suffixes = [
        "system_bound_today_initial_stock_candidate_v1.json",
        "today_initial_stock_owner_ratification_v1.json",
        "today_initial_stock_anchor_v1.json",
        "today_initial_stock_kind_set_membership_v1.json",
    ]
    docs = []
    sources = {}
    for suffix, fn, field in zip(
        suffixes,
        [
            semantic_candidate_digest_v1,
            ratification_digest_v1,
            anchor_digest_v1,
            membership_digest_v1,
        ],
        ["provenance_digest", "ratification_digest", "anchor_digest", "membership_digest"],
    ):
        name = next(n for n in names if n.endswith(suffix))
        path = root / name
        _require(
            verify_manifest_sha256_v1(store_root=path.parent) == 0,
            "OPENING_SEALED_PACK_MANIFEST_INVALID",
        )
        doc = unique_json_v1(path.read_bytes())
        _require(fn(doc) == doc[field], "OPENING_SEMANTIC_DIGEST_INVALID")
        sources[name] = sha256(path.read_bytes()).hexdigest()
        docs.append(doc)
    candidate = docs[0]
    _require(candidate["account_identity"] == expected_account_identity, "OPENING_ACCOUNT_MISMATCH")
    base = (root / next(n for n in names if n.endswith(suffixes[0]))).parent
    bodies = {}
    for stem in ("balance", "config"):
        path = base / f"raw_account_{stem}_response_body.json"
        data = path.read_bytes()
        _require(
            sha256(data).hexdigest() == candidate[f"raw_{stem}_sha256"], "OPENING_RAW_HASH_MISMATCH"
        )
        sources[str(path.relative_to(root))] = sha256(data).hexdigest()
        payload = unique_json_v1(data)
        _require(payload["code"] == "0" and len(payload["data"]) == 1, "OPENING_RAW_SCHEMA_INVALID")
        bodies[stem] = payload["data"][0]
    _require(bodies["config"].get("uid") == expected_account_identity, "OPENING_ACCOUNT_MISMATCH")
    details = {r["ccy"]: r for r in bodies["balance"]["details"]}
    _require(len(details) == len(bodies["balance"]["details"]), "OPENING_DUPLICATE_CURRENCY")
    _require(
        details[candidate["settlement_currency"]]["eq"] == candidate["equity_value"],
        "OPENING_RATIFIED_VALUE_NOT_RAW_BOUND",
    )
    return {
        "candidate": candidate,
        "config": bodies["config"],
        "balance": bodies["balance"],
        "source_hashes": sources,
        "historical_anchor_validated": True,
    }


def _config(record, account):
    rows = record["rows"]
    _require(len(rows) == 1 and rows[0].get("uid") == account, "REPLAY_ACCOUNT_MISMATCH")
    row = rows[0]
    _require(
        row.get("acctLv") == "2"
        and row.get("posMode") == "net_mode"
        and row.get("autoLoan") is False,
        "REPLAY_ACCOUNT_MODE_UNSUPPORTED",
    )
    return {k: row[k] for k in ("uid", "acctLv", "posMode", "autoLoan")}


def _balance(record):
    rows = record["rows"]
    _require(
        len(rows) == 1 and isinstance(rows[0].get("details"), list), "REPLAY_BALANCE_SCOPE_INVALID"
    )
    top = rows[0]
    _require(amount_v1(top.get("isoEq")) == 0, "REPLAY_ISOLATED_EQUITY_UNSUPPORTED")
    result = {}
    for row in top["details"]:
        ccy = row.get("ccy")
        _require(
            isinstance(ccy, str)
            and bool(re.fullmatch(r"[A-Z0-9]{1,20}", ccy))
            and ccy not in result,
            "REPLAY_CURRENCY_SCOPE_INVALID",
        )
        for key in (
            "cashBal",
            "eq",
            "upl",
            "isoEq",
            "isoUpl",
            "spotIsoBal",
            "stgyEq",
            "smtSyncEq",
            "spotCopyTradingEq",
        ):
            amount_v1(row.get(key))
        for key in ("isoEq", "isoUpl", "spotIsoBal", "stgyEq", "smtSyncEq", "spotCopyTradingEq"):
            _require(amount_v1(row[key]) == 0, "REPLAY_NON_CASH_EQUITY_UNSUPPORTED")
        # These fields are inapplicable for the expressly required Futures mode.
        # Present nonzero data is a contradiction, not a subtract-again term.
        for key in ("liab", "interest"):
            _require(
                key in row and (row[key] == "" or amount_v1(row[key]) == 0),
                "REPLAY_LIABILITY_OR_INTEREST_UNSUPPORTED",
            )
        result[ccy] = row
    return top, result


def _check_record_scopes(records, funding=False):
    expected = (
        {
            "config_before": "/api/v5/account/config",
            "config_after": "/api/v5/account/config",
            "funding_before": "/api/v5/asset/balances",
            "funding_after": "/api/v5/asset/balances",
            "bill_taxonomy": "/api/v5/account/subtypes",
        }
        if funding
        else {
            "config_before": "/api/v5/account/config",
            "config_after": "/api/v5/account/config",
            "balance_before": "/api/v5/account/balance",
            "balance_after": "/api/v5/account/balance",
            "positions_before": "/api/v5/account/positions",
            "positions_after": "/api/v5/account/positions",
            "funding_balance": "/api/v5/asset/balances",
        }
    )
    _require(set(expected) <= set(records), "REPLAY_REQUIRED_RECORD_MISSING")
    for label, path in expected.items():
        _require(records[label]["endpoint"] == path, "REPLAY_ENDPOINT_SCOPE_MISMATCH")
    extra = set(records) - set(expected)
    patterns = (r"funding_history_[0-3]",) if funding else (r"archive_[0-1]", r"recent_0")
    _require(
        all(any(re.fullmatch(p, label) for p in patterns) for label in extra),
        "REPLAY_UNEXPECTED_RECORD_LABEL",
    )
    order = (
        ["config_before", "funding_before", "bill_taxonomy"]
        + sorted(extra, key=lambda s: int(s.rsplit("_", 1)[1]))
        + ["funding_after", "config_after"]
        if funding
        else ["config_before", "balance_before", "positions_before"]
        + sorted(
            (k for k in extra if k.startswith("archive_")), key=lambda s: int(s.rsplit("_", 1)[1])
        )
        + sorted(k for k in extra if k.startswith("recent_"))
        + ["funding_balance", "positions_after", "balance_after", "config_after"]
    )
    _require(
        [records[k]["index"] for k in order] == list(range(len(records))),
        "REPLAY_ACQUISITION_ORDER_INVALID",
    )


def _bill_rows(records, prefix, path, *, funding=False):
    page_records = [(k, v) for k, v in records.items() if k.startswith(prefix + "_")]
    page_records.sort(key=lambda kv: int(kv[0].rsplit("_", 1)[1]))
    _require(bool(page_records), "REPLAY_BILL_PAGES_MISSING")
    rows = []
    cursor = None
    for index, (label, record) in enumerate(page_records):
        _require(label == f"{prefix}_{index}", "REPLAY_BILL_PAGE_GAP")
        parsed = urlsplit(record["endpoint"])
        params = parse_qs(parsed.query, keep_blank_values=True)
        expected = {"limit": ["100"]}
        if cursor is not None:
            expected["after"] = [str(cursor)]
        _require(
            parsed.path == path
            and not parsed.netloc
            and not parsed.fragment
            and params == expected,
            "REPLAY_BILL_REQUEST_SCOPE_INVALID",
        )
        page = record["rows"]
        _require(len(page) <= 100, "REPLAY_BILL_PAGE_OVERSIZED")
        if not page:
            _require(index == len(page_records) - 1, "REPLAY_PAGE_AFTER_EXHAUSTION")
            break
        ids = [_integer(r.get("billId"), "billId") for r in page]
        ts = [_integer(r.get("ts"), "ts") for r in page]
        values = ts if funding else ids
        _require(
            all(a >= b if funding else a > b for a, b in zip(values, values[1:])),
            "REPLAY_BILL_PAGE_ORDER_INVALID",
        )
        _require(cursor is None or all(v < cursor for v in values), "REPLAY_CURSOR_NOT_PROGRESSING")
        if funding:
            _require(len(page) < 100, "REPLAY_FUNDING_TIMESTAMP_BOUNDARY_AMBIGUOUS")
        rows.extend(page)
        cursor = values[-1]
    _require(not page_records[-1][1]["rows"], "REPLAY_PAGINATION_NOT_EXHAUSTED")
    return rows


TRADE_KINDS = {
    ("1", "11"): "INTERNAL_TRANSFER_IN",
    ("1", "12"): "INTERNAL_TRANSFER_OUT",
    ("2", "1"): "FUTURES_EXECUTION",
    ("2", "2"): "FUTURES_EXECUTION",
    ("8", "173"): "FUNDING_EXPENSE",
    ("8", "174"): "FUNDING_INCOME",
    ("27", "318"): "CONVERT_IN",
    ("27", "319"): "CONVERT_OUT",
    ("30", "320"): "SIMPLE_BUY",
    ("30", "321"): "SIMPLE_SELL",
}


def classify_trading_rows_v1(rows, taxonomy):
    native = {}
    for item in taxonomy:
        for sub in item.get("subTypeDetails", []):
            key = (item["type"], sub["subType"])
            _require(key not in native, "REPLAY_TAXONOMY_DUPLICATE")
            native[key] = sub.get("subTypeDesc")
    pairs = {}
    classified = []
    for row in rows:
        kind = (row["type"], row["subType"])
        _require(kind in TRADE_KINDS and bool(native.get(kind)), "REPLAY_UNKNOWN_ECONOMIC_KIND")
        delta = amount_v1(row["balChg"])
        _require(amount_v1(row.get("interest")) == 0, "REPLAY_UNMODELLED_INTEREST")
        if kind[0] == "1":
            incoming = kind[1] == "11"
            _require(
                row.get("from") == ("6" if incoming else "18")
                and row.get("to") == ("18" if incoming else "6"),
                "REPLAY_UNBOUND_INTERNAL_TRANSFER_SCOPE",
            )
            _require(
                delta == amount_v1(row.get("sz")) * (1 if incoming else -1)
                and (delta > 0 if incoming else delta < 0),
                "REPLAY_TRANSFER_AMOUNT_INVALID",
            )
            _require(
                row.get("fee") in ("", "0") and row.get("pnl") in ("", "0"),
                "REPLAY_TRANSFER_EXTRA_TERMS_UNSUPPORTED",
            )
        else:
            fee = amount_v1(row.get("fee"))
            pnl = amount_v1(row.get("pnl"))
            if kind[0] in {"2", "8"}:
                _require(
                    row.get("instType") in {"SWAP", "FUTURES"}
                    and row.get("mgnMode") == "cross"
                    and bool(row.get("instId")),
                    "REPLAY_EXECUTION_PRODUCT_UNSUPPORTED",
                )
                _require(delta == pnl + fee, "REPLAY_NET_POSTING_COMPONENT_MISMATCH")
                if kind[0] == "2":
                    _require(
                        bool(row.get("ordId")) and row.get("tradeId") not in (None, "", "0"),
                        "REPLAY_FILL_IDENTITY_MISSING",
                    )
                else:
                    _require(
                        (delta <= 0 if kind[1] == "173" else delta >= 0),
                        "REPLAY_FUNDING_SIGN_INVALID",
                    )
            else:
                _require(fee == 0 and pnl == 0, "REPLAY_CONVERSION_EXTRA_TERMS_UNSUPPORTED")
                _require(amount_v1(row.get("px")) > 0, "REPLAY_CONVERSION_PRICE_INVALID")
                _require(row.get("tradeId") not in (None, "", "0"), "REPLAY_CONVERSION_ID_MISSING")
                positive = kind[1] in {"318", "320"}
                _require(
                    delta == amount_v1(row.get("sz")) * (1 if positive else -1)
                    and (delta > 0 if positive else delta < 0),
                    "REPLAY_CONVERSION_AMOUNT_INVALID",
                )
                pair_key = (kind[0], row["tradeId"], row["ts"], row.get("instId"))
                pairs.setdefault(pair_key, []).append(row)
        classified.append(
            {**row, "economic_class": TRADE_KINDS[kind], "native_type_description": native[kind]}
        )
    for key, pair in pairs.items():
        _require(
            len(pair) == 2 and len({r["ccy"] for r in pair}) == 2,
            "REPLAY_CONVERSION_COUNTERPART_MISSING",
        )
        _require(
            {r["subType"] for r in pair} == ({"318", "319"} if key[0] == "27" else {"320", "321"}),
            "REPLAY_CONVERSION_COUNTERPART_INVALID",
        )
        _require(
            set(key[3].split("-")) == {r["ccy"] for r in pair}
            and len({r.get("px") for r in pair}) == 1,
            "REPLAY_CONVERSION_PAIR_IDENTITY_INVALID",
        )
    return classified


def _funding_balances(rows):
    values = {}
    for row in rows:
        ccy = row.get("ccy")
        _require(isinstance(ccy, str) and ccy not in values, "REPLAY_FUNDING_CURRENCY_INVALID")
        bal = amount_v1(row.get("bal"))
        avail = amount_v1(row.get("availBal"))
        frozen = amount_v1(row.get("frozenBal"))
        _require(bal == avail + frozen, "REPLAY_FUNDING_BALANCE_PARTITION_MISMATCH")
        values[ccy] = bal
    return values


def reconcile_real_equity_window_v1(opening, trading_manifest, trading, funding_manifest, funding):
    """Replay the observed window, preserving all exact residuals and blockers."""
    with localcontext() as context:
        context.prec = 120
        return _reconcile(opening, trading_manifest, trading, funding_manifest, funding)


def _reconcile(opening, tm, trading, fm, funding):
    _require(
        opening.get("historical_anchor_validated") is True, "REPLAY_VALIDATED_OPENING_REQUIRED"
    )
    account = opening["candidate"]["account_identity"]
    _require(tm["account_identity"] == fm["account_identity"] == account, "REPLAY_ACCOUNT_MISMATCH")
    _check_record_scopes(trading)
    _check_record_scopes(funding, funding=True)
    configs = [
        _config(records[label], account)
        for records in (trading, funding)
        for label in ("config_before", "config_after")
    ]
    _require(all(c == configs[0] for c in configs), "REPLAY_ACCOUNT_MODE_CHANGED")
    _config({"rows": [opening["config"]]}, account)
    _, opening_details = _balance({"rows": [opening["balance"]]})
    for label in ("positions_before", "positions_after"):
        _require(trading[label]["rows"] == [], "REPLAY_OPEN_POSITION_VALUATION_UNSUPPORTED")
    top_before, before = _balance(trading["balance_before"])
    top_after, after = _balance(trading["balance_after"])
    _require(
        all(
            "uid" not in top or top["uid"] == account
            for top in (top_before, top_after, opening["balance"])
        ),
        "REPLAY_BALANCE_ACCOUNT_MISMATCH",
    )
    fields = (
        "cashBal",
        "eq",
        "upl",
        "isoEq",
        "isoUpl",
        "liab",
        "interest",
        "spotIsoBal",
        "stgyEq",
        "smtSyncEq",
        "spotCopyTradingEq",
    )
    _require(
        set(before) == set(after)
        and all(all(before[c][f] == after[c][f] for f in fields) for c in before),
        "REPLAY_BALANCE_CHANGED_DURING_ACQUISITION",
    )
    _require(all(amount_v1(r["upl"]) == 0 for r in after.values()), "REPLAY_NON_FLAT_UPL")
    _require(
        all(amount_v1(r["eq"]) == amount_v1(r["cashBal"]) for r in after.values()),
        "REPLAY_NON_CASH_END_EQUITY",
    )
    archive = _bill_rows(trading, "archive", "/api/v5/account/bills-archive")
    recent = _bill_rows(trading, "recent", "/api/v5/account/bills")
    binding = canonical_digest_v1({"account_identity": account, "venue_host": "eea.okx.com"})
    audit = audit_bill_pages_v1(
        [
            dict(
                account_binding_digest=binding,
                endpoint_path="/api/v5/account/bills-archive",
                rows=archive,
            ),
            dict(
                account_binding_digest=binding, endpoint_path="/api/v5/account/bills", rows=recent
            ),
        ],
        account_binding_digest=binding,
    )
    _require(audit["observed_chain_consistent"], "REPLAY_BILL_BALANCE_CHAIN_BREAK")
    unique = {r["billId"]: r for r in archive + recent}
    rows = sorted(unique.values(), key=lambda r: int(r["billId"]))
    cutoff = _integer(opening["balance"]["uTime"], "opening_uTime")
    completed = int(datetime.fromisoformat(tm["completed_at"]).timestamp() * 1000)
    _require(
        0 <= completed - cutoff < 89 * 86400000,
        "REPLAY_OPENING_OUTSIDE_CONSERVATIVE_ARCHIVE_RETENTION",
    )
    _require(
        bool(rows) and min(int(r["ts"]) for r in rows) <= cutoff,
        "REPLAY_NO_PRE_OPENING_BILL_WITNESS",
    )
    _require(all(int(r["ts"]) <= completed for r in rows), "REPLAY_FUTURE_DATED_BILL")
    old = opening_details
    active = [r for r in rows if int(r["ts"]) > cutoff]
    classified = classify_trading_rows_v1(active, funding["bill_taxonomy"]["rows"])
    result = []
    all_residuals = []
    exact = True
    for ccy in sorted(set(old) | set(after) | {r["ccy"] for r in rows}):
        previous = [r for r in rows if r["ccy"] == ccy and int(r["ts"]) <= cutoff]
        current = [r for r in classified if r["ccy"] == ccy]
        if ccy in old:
            _require(
                bool(previous) and previous[-1]["ts"] == old[ccy]["uTime"],
                "REPLAY_OPENING_BILL_TIMESTAMP_NOT_BOUND",
            )
            start = amount_v1(previous[-1]["bal"])
            start_display = compare_native_display_v1(start, old[ccy]["cashBal"])
            _require(
                start_display["exact_equal"]
                or start_display["binary64_shortest_rendering_matches"],
                "REPLAY_OPENING_CASH_UNEXPLAINED",
            )
        else:
            # Specific full-account balance contract: zero cash and zero eq
            # currencies are omitted. Never a default for a missing numeric field.
            _require(not previous and bool(current), "REPLAY_OPENING_CURRENCY_UNBOUND")
            _require(
                amount_v1(current[0]["bal"]) == amount_v1(current[0]["balChg"]),
                "REPLAY_NEW_CURRENCY_NONZERO_PREDECESSOR",
            )
            start = Decimal("0")
            start_display = None
        cash = start
        buckets = {}
        for row in current:
            cash += amount_v1(row["balChg"])
            _require(cash == amount_v1(row["bal"]), "REPLAY_FORWARD_BALANCE_MISMATCH")
            buckets[row["economic_class"]] = buckets.get(
                row["economic_class"], Decimal("0")
            ) + amount_v1(row["balChg"])
        if ccy not in after:
            _require(cash == 0, "REPLAY_MISSING_NONZERO_END_CURRENCY")
            closing_display = None
        else:
            closing_display = compare_native_display_v1(cash, after[ccy]["cashBal"])
            _require(
                closing_display["exact_equal"]
                or closing_display["binary64_shortest_rendering_matches"],
                "REPLAY_END_CASH_UNEXPLAINED",
            )
        for comparison in (start_display, closing_display):
            if comparison and not comparison["exact_equal"]:
                exact = False
                all_residuals.append({"currency": ccy, **comparison})
        result.append(
            {
                "currency": ccy,
                "opening_exact_cash": text_decimal_v1(start),
                "opening_published_cash_comparison": start_display,
                "cash_posting_count": len(current),
                "signed_cash_by_class": {k: text_decimal_v1(v) for k, v in sorted(buckets.items())},
                "reconstructed_end_cash_and_flat_equity": text_decimal_v1(cash),
                "end_published_equity_comparison": closing_display,
                "currency_omission_is_documented_zero_row_case": ccy not in old or ccy not in after,
            }
        )
    settlement = opening["candidate"]["settlement_currency"]
    initial_cash = next(
        amount_v1(r["opening_exact_cash"]) for r in result if r["currency"] == settlement
    )
    initial_upl = amount_v1(old[settlement]["upl"])
    initial_comparison = compare_native_display_v1(
        initial_cash + initial_upl, opening["candidate"]["equity_value"]
    )
    _require(
        initial_comparison["exact_equal"]
        or initial_comparison["binary64_shortest_rendering_matches"],
        "REPLAY_OPENING_RATIFIED_EQUITY_UNEXPLAINED",
    )
    funding_result = reconcile_funding_window_v1(
        cutoff, classified, funding, trading["funding_balance"]["rows"]
    )
    _require(
        funding_result["all_counterparty_flow_reconstructions_exact"],
        "REPLAY_FUNDING_COUNTERPART_CASH_UNEXPLAINED",
    )
    all_exact = (
        exact
        and initial_comparison["exact_equal"]
        and funding_result["exact_decimal_snapshot_match"]
    )
    return {
        "schema": "peaktrade.real_equity_window_reconciliation.v1",
        "input_data_digest": canonical_digest_v1(
            {"opening": opening, "trading_manifest": tm, "funding_manifest": fm}
        ),
        "historical_source_hashes": opening.get("source_hashes", {}),
        "opening_as_of": opening["candidate"]["as_of_time"],
        "opening_raw_balance_time_ms": cutoff,
        "observed_at": tm["completed_at"],
        "historical_anchor_and_current_account_joined": True,
        "archive_and_recent_endpoint_pagination_exhausted": True,
        "retention_window_checked_under_89_days": True,
        "all_observed_window_trading_rows_classified": True,
        "window_trading_posting_count": len(classified),
        "current_positions_flat_observed_twice": True,
        "initial_equity_display_comparison": initial_comparison,
        "initial_upl_replaced_not_double_counted": text_decimal_v1(initial_upl),
        "trading_currencies": result,
        "funding": funding_result,
        "presentation_residuals": all_residuals,
        "exact_decimal_equality_to_all_snapshot_fields": all_exact,
        "status": (
            "OBSERVED_WINDOW_EXACT_NATIVE_RECONCILIATION"
            if all_exact
            else "OBSERVED_WINDOW_EXPLAINED_WITH_EXPLICIT_PRESENTATION_RESIDUALS"
        ),
        "universal_D6_completeness_promoted": False,
        "venue_binary64_formatting_contract_proven": False,
        "economic_adjustment_or_tolerance_added": False,
        "available_for_sizing_produced": False,
        "capital_admitted": False,
        "authority_effect": "NONE",
        "blocking_for_exact_authoritative_equity_source": (
            [] if all_exact else ["VENUE_NUMERIC_REPRESENTATION_CONTRACT_UNPROVEN"]
        ),
        "future_open_position_valuation_supported": False,
    }


def reconcile_funding_window_v1(cutoff, trading_rows, records, original_snapshot):
    before = _funding_balances(records["funding_before"]["rows"])
    after = _funding_balances(records["funding_after"]["rows"])
    _require(
        before == after == _funding_balances(original_snapshot), "REPLAY_FUNDING_SNAPSHOT_CHANGED"
    )
    rows = _bill_rows(records, "funding_history", "/api/v5/asset/bills-history", funding=True)
    unique = {}
    for row in rows:
        bid = _integer(row.get("billId"), "funding_billId")
        _require(bid not in unique or unique[bid] == row, "REPLAY_FUNDING_BILL_ID_CONFLICT")
        amount_v1(row.get("bal"))
        amount_v1(row.get("balChg"))
        unique[bid] = row
    ordered = sorted(unique.values(), key=lambda r: (int(r["ts"]), int(r["billId"])))
    active = [r for r in ordered if int(r["ts"]) > cutoff]
    _require(all(r["type"] in {"1", "130", "131"} for r in active), "REPLAY_UNKNOWN_FUNDING_KIND")
    counterpart_count = 0
    counterpart_diffs = []
    matched = set()
    counterpart_deltas = {}
    for row in [r for r in active if r["type"] in {"130", "131"}]:
        incoming_trading = row["type"] == "131"
        candidates = [
            r
            for r in trading_rows
            if r["type"] == "1"
            and r["subType"] == ("11" if incoming_trading else "12")
            and r["ccy"] == row["ccy"]
            and abs(int(r["ts"]) - int(row["ts"])) < 1000
        ]
        _require(
            len(candidates) == 1 and candidates[0]["billId"] not in matched,
            "REPLAY_INTERNAL_TRANSFER_COUNTERPART_AMBIGUOUS",
        )
        candidate = candidates[0]
        matched.add(candidate["billId"])
        counterpart_deltas[row["billId"]] = -amount_v1(candidate["balChg"])
        comparison = compare_native_display_v1(-amount_v1(candidate["balChg"]), row["balChg"])
        _require(
            comparison["exact_equal"] or comparison["binary64_shortest_rendering_matches"],
            "REPLAY_INTERNAL_TRANSFER_AMOUNT_MISMATCH",
        )
        counterpart_count += 1
        if not comparison["exact_equal"]:
            counterpart_diffs.append({"currency": row["ccy"], **comparison})
    _require(
        len(matched) == sum(r["type"] == "1" for r in trading_rows),
        "REPLAY_UNMATCHED_TRADING_TRANSFER",
    )
    results = []
    exact = True
    for ccy in sorted(set(after) | {r["ccy"] for r in active}):
        previous = [r for r in ordered if r["ccy"] == ccy and int(r["ts"]) <= cutoff]
        current = [r for r in active if r["ccy"] == ccy]
        if previous:
            initial = amount_v1(previous[-1]["bal"])
        else:
            _require(
                bool(current)
                and current[0]["type"] == "1"
                and amount_v1(current[0]["bal"]) == amount_v1(current[0]["balChg"]),
                "REPLAY_FUNDING_OPENING_UNBOUND",
            )
            initial = Decimal("0")
        cash = initial
        bilateral_cash = initial
        breaks = []
        for row in current:
            delta = amount_v1(row["balChg"])
            _require(
                (delta > 0 if row["type"] in {"1", "130"} else delta < 0),
                "REPLAY_FUNDING_EVENT_SIGN_INVALID",
            )
            computed = cash + delta
            published = amount_v1(row["bal"])
            bilateral_cash += (
                counterpart_deltas[row["billId"]] if row["type"] in {"130", "131"} else delta
            )
            comparison = compare_native_display_v1(bilateral_cash, row["bal"])
            _require(
                comparison["exact_equal"] or comparison["binary64_shortest_rendering_matches"],
                "REPLAY_FUNDING_INTERMEDIATE_BALANCE_UNEXPLAINED",
            )
            residual = published - computed
            if residual:
                # Do not adjust the ledger or invent a rounding tolerance.
                breaks.append(
                    {"bill_id": row["billId"], "observed_minus_computed": text_decimal_v1(residual)}
                )
            cash = computed
        target = after.get(ccy)
        _require(target is not None or cash == 0, "REPLAY_FUNDING_END_CURRENCY_MISSING")
        residual = (target - cash) if target is not None else Decimal("0")
        if residual:
            exact = False
        results.append(
            {
                "currency": ccy,
                "opening_reported_cash": text_decimal_v1(initial),
                "cash_posting_count": len(current),
                "replayed_from_reported_postings": text_decimal_v1(cash),
                "current_observed_balance": text_decimal_v1(target) if target is not None else "0",
                "observed_minus_replayed": text_decimal_v1(residual),
                "counterparty_flow_reconstruction": text_decimal_v1(bilateral_cash),
                "counterparty_flow_matches_observed_exactly": bilateral_cash
                == (target if target is not None else Decimal("0")),
                "internal_transfer_representation_residuals": breaks,
            }
        )
    return {
        "currency_balances": results,
        "observed_window_posting_count": len(active),
        "unique_internal_transfer_counterparts": counterpart_count,
        "counterpart_representation_comparisons": counterpart_diffs,
        "exact_decimal_snapshot_match": exact,
        "all_counterparty_flow_reconstructions_exact": all(
            r["counterparty_flow_matches_observed_exactly"] for r in results
        ),
        "historical_pre_window_unknown_kinds_not_adopted": sorted(
            {r["type"] for r in ordered if int(r["ts"]) <= cutoff} - {"1", "130", "131"}
        ),
        "scope": "FUNDING_ACCOUNT_SEPARATE_FROM_TRADING_EQUITY",
    }
