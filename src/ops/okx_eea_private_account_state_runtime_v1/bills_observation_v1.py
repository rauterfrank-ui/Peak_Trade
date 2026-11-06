"""Audit observed account bills, without classifying or minting equity.

The venue's signed balChg is already the posted account movement. Adding
pnl/fee/funding again would double count it. Arithmetic continuity is only
a diagnostic: offsetting missing events and events outside retention remain
undetectable. The first row's implied predecessor is never an opening anchor.
"""

from decimal import Decimal, localcontext
from hashlib import sha256
import json
import re


class BillsObservationError(ValueError):
    pass


def canonical_digest_v1(value):
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode()
    ).hexdigest()


def _integer(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,40}", value):
        raise BillsObservationError("BILL_INTEGER_INVALID:" + field)
    if int(value) <= 0:
        raise BillsObservationError("BILL_INTEGER_INVALID:" + field)
    return int(value)


def _amount(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]{1,40}(?:\.[0-9]{1,40})?", value):
        raise BillsObservationError("BILL_DECIMAL_INVALID:" + field)
    return Decimal(value)


def audit_bill_pages_v1(pages, *, account_binding_digest):
    """Exact per-currency continuity over observed rows, never completeness.

    Every page must carry the same independently supplied account binding.
    Historical binding digests identify historical scope, not today's account
    authorization. Full-row conflicts under the same native billId fail closed.
    """
    if not isinstance(account_binding_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", account_binding_digest
    ):
        raise BillsObservationError("BILL_ACCOUNT_BINDING_REQUIRED")
    if not isinstance(pages, (list, tuple)) or not pages:
        raise BillsObservationError("BILL_PAGES_REQUIRED")
    seen = {}
    duplicate_count = 0
    page_digests = []
    for page in pages:
        if (
            not isinstance(page, dict)
            or page.get("account_binding_digest") != account_binding_digest
        ):
            raise BillsObservationError("BILL_ACCOUNT_BINDING_MISMATCH")
        if page.get("endpoint_path") not in {
            "/api/v5/account/bills",
            "/api/v5/account/bills-archive",
        } or not isinstance(page.get("rows"), list):
            raise BillsObservationError("BILL_PAGE_SCHEMA_INVALID")
        page_digests.append(canonical_digest_v1(page))
        for row in page["rows"]:
            if not isinstance(row, dict):
                raise BillsObservationError("BILL_ROW_INVALID")
            bid = _integer(row.get("billId"), "billId")
            ts = _integer(row.get("ts"), "ts")
            ccy = row.get("ccy")
            if not isinstance(ccy, str) or not re.fullmatch(r"[A-Z0-9]{1,20}", ccy):
                raise BillsObservationError("BILL_CURRENCY_INVALID")
            for field in ("type", "subType"):
                _integer(row.get(field), field)
            bal = _amount(row.get("bal"), "bal")
            delta = _amount(row.get("balChg"), "balChg")
            digest = canonical_digest_v1(row)
            if bid in seen:
                if seen[bid]["digest"] != digest:
                    raise BillsObservationError("BILL_ID_CONFLICT")
                duplicate_count += 1
            else:
                seen[bid] = dict(
                    bid=bid,
                    ts=ts,
                    ccy=ccy,
                    bal=bal,
                    delta=delta,
                    digest=digest,
                    kind=(row["type"], row["subType"]),
                )
    ordered = sorted(seen.values(), key=lambda r: r["bid"])
    if any(a["ts"] > b["ts"] for a, b in zip(ordered, ordered[1:])):
        raise BillsObservationError("BILL_ID_TIME_ORDER_CONFLICT")
    currencies = []
    with localcontext() as context:
        context.prec = 100 + len(str(max(1, len(ordered))))
        for ccy in sorted({r["ccy"] for r in ordered}):
            rows = [r for r in ordered if r["ccy"] == ccy]
            breaks = sum(b["bal"] != a["bal"] + b["delta"] for a, b in zip(rows, rows[1:]))
            currencies.append(
                {
                    "currency": ccy,
                    "row_count": len(rows),
                    "first_event_ms": rows[0]["ts"],
                    "last_event_ms": rows[-1]["ts"],
                    "continuity_comparison_count": len(rows) - 1,
                    "continuity_break_count": breaks,
                    "observed_chain_consistent": breaks == 0,
                    "opening_balance_authorized": False,
                }
            )
    return {
        "schema": "peaktrade.account_bills_observation_audit.v1",
        "page_digests": page_digests,
        "account_binding_digest": account_binding_digest,
        "unique_bill_count": len(ordered),
        "identical_duplicate_count": duplicate_count,
        "observed_type_subtype_tokens": sorted({"/".join(r["kind"]) for r in ordered}),
        "currencies": currencies,
        "observed_chain_consistent": all(c["observed_chain_consistent"] for c in currencies),
        "empty_observation": not ordered,
        "empty_means_zero_events": False,
        "classified_event_stream_complete": False,
        "equity_reconstructed": False,
        "capital_admitted": False,
        "authority_effect": "NONE",
    }
