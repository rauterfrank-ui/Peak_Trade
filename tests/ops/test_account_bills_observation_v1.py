"""Real historical replay and adversarial observed-bill / signed-GET checks."""

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest

from src.ops.okx_eea_private_account_state_runtime_v1.bills_observation_v1 import (
    BillsObservationError,
    audit_bill_pages_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    open_k1_account_observation_source_v1,
)
from tests.ops.test_k1_account_observation_source_v1 import ACCOUNT, InjectedOpener, wire
from tests.ops.test_current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    _FakeKeychainBackend,
)

BINDING = "a" * 64


def row(bid="1", ts="100", ccy="USDC", bal="10", delta="10"):
    return dict(
        billId=bid,
        ts=ts,
        ccy=ccy,
        bal=bal,
        balChg=delta,
        type="2",
        subType="1",
        fee="-999",
        pnl="999",
    )


def page(rows):
    return dict(
        account_binding_digest=BINDING, endpoint_path="/api/v5/account/bills-archive", rows=rows
    )


def audit(rows):
    return audit_bill_pages_v1([page(rows)], account_binding_digest=BINDING)


def test_signed_posted_change_counts_once_with_rebate_and_currency_partition():
    result = audit(
        [
            row(),
            row("2", "101", bal="9.75", delta="-0.25"),
            row("3", "102", ccy="EUR", bal="42", delta="42"),
            row("4", "103", bal="9.76", delta="0.01"),
        ]
    )
    assert result["observed_chain_consistent"]
    assert [c["row_count"] for c in result["currencies"]] == [1, 3]
    assert result["equity_reconstructed"] is False
    assert result["classified_event_stream_complete"] is False
    assert result["capital_admitted"] is False


def test_gap_is_detected_but_offsetting_missing_events_are_not_claimed_detectable():
    assert not audit([row(), row("3", "103", bal="8", delta="-1")])["observed_chain_consistent"]
    r = audit([row(), row("3", "103", bal="9", delta="-1")])
    assert r["observed_chain_consistent"]
    assert not r["classified_event_stream_complete"]


def test_overlap_deduplicates_only_identical_native_bill():
    result = audit_bill_pages_v1([page([row()]), page([row()])], account_binding_digest=BINDING)
    assert (result["unique_bill_count"], result["identical_duplicate_count"]) == (1, 1)
    changed = row()
    changed["fee"] = "0"
    with pytest.raises(BillsObservationError, match="BILL_ID_CONFLICT"):
        audit_bill_pages_v1([page([row()]), page([changed])], account_binding_digest=BINDING)


@pytest.mark.parametrize(
    "field,value",
    [
        ("balChg", ""),
        ("balChg", None),
        ("balChg", 0.1),
        ("bal", "NaN"),
        ("bal", "Infinity"),
        ("bal", "1e9"),
        ("billId", "1.0"),
        ("billId", "0"),
        ("ts", "-1"),
        ("ccy", ""),
        ("ccy", "usdc"),
        ("subType", ""),
    ],
)
def test_invalid_terms_are_not_zero(field, value):
    r = row()
    r[field] = value
    with pytest.raises(BillsObservationError):
        audit([r])


def test_mixed_accounts_and_time_order_conflict_fail_closed():
    p = page([row()])
    p["account_binding_digest"] = "b" * 64
    with pytest.raises(BillsObservationError, match="BINDING_MISMATCH"):
        audit_bill_pages_v1([p], account_binding_digest=BINDING)
    with pytest.raises(BillsObservationError, match="TIME_ORDER_CONFLICT"):
        audit([row(), row("2", "99")])


def test_precision_does_not_round_away_a_small_break():
    large = "9" * 40
    assert not audit([row(bal=large), row("2", "101", bal=large, delta="0." + "0" * 39 + "1")])[
        "observed_chain_consistent"
    ]


def test_empty_rows_prove_neither_zero_events_nor_an_opening_anchor():
    r = audit([])
    assert r["empty_observation"]
    assert not r["empty_means_zero_events"]
    assert not r["equity_reconstructed"]


def test_actual_historical_pages_have_36_unique_bills_and_22_overlapping_rows():
    root = Path(__file__).resolve().parents[2]
    base = (
        root
        / "evidence/ops/full_core_d6_path_b_package_1_observation_execution_v1/2026-09-13T182521Z"
    )
    pages = []
    for name in (
        "s4_account_bills_observation_v1.json",
        "s4_account_bills_archive_observation_v1.json",
    ):
        d = json.loads((base / name).read_text())
        binding = d["d4_identity_digest"]
        pages.append(
            dict(
                account_binding_digest=binding,
                endpoint_path=d["request_surface"].removeprefix("GET_"),
                rows=d["rows"],
            )
        )
    r = audit_bill_pages_v1(pages, account_binding_digest=binding)
    assert (r["unique_bill_count"], r["identical_duplicate_count"]) == (36, 22)
    assert [
        (c["currency"], c["row_count"], c["continuity_break_count"]) for c in r["currencies"]
    ] == [("EUR", 4, 0), ("USDC", 32, 0)]
    assert not r["classified_event_stream_complete"]


class BillsOpener(InjectedOpener):
    def __init__(self, pages):
        super().__init__()
        self.pages = deepcopy(pages)

    @contextmanager
    def open(self, req, timeout):
        if urlsplit(req.full_url).path != "/api/v5/account/bills-archive":
            with super().open(req, timeout) as response:
                yield response
            return
        assert req.get_method() == "GET" and req.has_header("Ok-access-sign")
        self.requests.append(req.full_url)
        assert self.pages
        payload = {"code": "0", "data": self.pages.pop(0)}

        class Response:
            status = 200
            url = req.full_url

            def read(self):
                return json.dumps(payload).encode()

        yield Response()


def run(pages, max_pages=6):
    opener = BillsOpener(pages)
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="injected-bills",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
            clock=lambda: 1000,
        ) as source:
            result = source.inspect_accounting_bills_v1(max_pages=max_pages)
    return result, opener.requests


def test_native_signed_get_paginates_after_oldest_id_through_empty_page():
    r, urls = run([[row("2", "101", bal="9", delta="-1"), row()], []])
    assert len(urls) == 3  # config + data + empty; no short-page assumption
    assert parse_qs(urlsplit(urls[-1]).query) == {"limit": ["100"], "after": ["1"]}
    assert r["endpoint_pagination_exhausted"]
    assert r["observed_chain_consistent"] and not r["equity_reconstructed"]
    assert "rows" not in r and "cashBal" not in json.dumps(r)


def test_page_budget_is_an_explicit_blocker():
    r, urls = run([[row()]], max_pages=1)
    assert len(urls) == 2
    assert not r["endpoint_pagination_exhausted"]
    assert "BILL_PAGE_BUDGET_EXHAUSTED" in r["blockers"]


def test_repeated_cursor_fails_without_retry():
    with pytest.raises(BillsObservationError, match="PAGINATION_NOT_PROGRESSING"):
        run([[row()], [row()]])


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v5/account/bills-archive?limit=100&ccy=USDC",
        "/api/v5/account/bills-archive?limit=100&after=-1",
        "/api/v5/account/bills-archive?limit=100&after=1&after=2",
        "/api/v5/account/bills-archive?limit=100&instType=SWAP",
    ],
)
def test_no_currency_or_instrument_filters_can_hide_obligations(endpoint):
    with patch.object(wire, "build_opener", return_value=BillsOpener([])):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="scope",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            with pytest.raises(ValueError, match="SCOPE_INVALID"):
                source.transport.get(endpoint=endpoint, auth_required=True)


def test_historical_trade_and_anchor_replay_and_tamper_guards(tmp_path):
    from scripts.ops.verify_historical_accounting_sources_v1 import verify_historical_sources_v1

    root = Path(__file__).resolve().parents[2]
    result = verify_historical_sources_v1(root)
    assert result["historical_trade_reproduced"]
    assert result["historical_anchor_cross_artifact_links_match"]
    assert not result["today_equity_reconstructed"]
    assert not result["account_identity_continuity_to_today_proven"]
    for name in result["sources_sha256"]:
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((root / name).read_bytes())
    raw_name = next(n for n in result["sources_sha256"] if n.endswith("GET_FILLS.raw.json"))
    raw_path = tmp_path / raw_name
    original = raw_path.read_text()
    raw = json.loads(original)
    raw["BODY_UTF8_EXACT"] += " "
    raw_path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="RAW_BODY_DIGEST_MISMATCH"):
        verify_historical_sources_v1(tmp_path)
    raw_path.write_text(original)
    anchor_name = next(
        n for n in result["sources_sha256"] if n.endswith("today_initial_stock_anchor_v1.json")
    )
    anchor_path = tmp_path / anchor_name
    anchor = json.loads(anchor_path.read_text())
    anchor["as_of_time"] = "2026-11-03T00:00:00Z"
    anchor_path.write_text(json.dumps(anchor))
    with pytest.raises(ValueError, match="ANCHOR_LINK_MISMATCH:as_of_time"):
        verify_historical_sources_v1(tmp_path)
