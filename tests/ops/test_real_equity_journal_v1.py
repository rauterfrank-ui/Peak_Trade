"""Exact private original-response capture and offline replay, injected HTTP."""

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import stat
from unittest.mock import patch
from urllib.parse import urlsplit

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_journal_v1 import (
    PrivateEquityJournalV1,
    RealEquityJournalError,
    collect_real_equity_journal_v1,
    load_real_equity_journal_v1,
    collect_equity_funding_supplement_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    open_k1_account_observation_source_v1,
)
from tests.ops.test_k1_account_observation_source_v1 import ACCOUNT, wire
from tests.ops.test_current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    _FakeKeychainBackend,
)


def balance_row(ccy="USDC", cash="10", eq="10", upl="0"):
    return dict(
        ccy=ccy,
        cashBal=cash,
        eq=eq,
        upl=upl,
        isoEq="0",
        isoUpl="0",
        liab="",
        interest="",
        spotIsoBal="0",
        stgyEq="0",
        smtSyncEq="0",
        spotCopyTradingEq="0",
        uTime="1000000",
    )


class EquityOpener:
    def __init__(self, *, account=ACCOUNT, broken_cursor=False, funding_pages=None):
        self.account = account
        self.requests = []
        self.broken_cursor = broken_cursor
        self.funding_pages = deepcopy(funding_pages)

    @contextmanager
    def open(self, req, timeout):
        assert req.get_method() == "GET"
        assert req.has_header("Ok-access-sign")
        url = urlsplit(req.full_url)
        self.requests.append(req.full_url)
        if url.path.endswith("/config"):
            rows = [dict(uid=self.account, acctLv="2", posMode="net_mode", autoLoan=False)]
        elif url.path.endswith("/balance"):
            rows = [dict(details=[balance_row()], totalEq="10", isoEq="0", uTime="1000000")]
        elif url.path.endswith("/bills-archive"):
            rows = (
                []
                if "after=" in url.query and not self.broken_cursor
                else [
                    dict(
                        billId="5",
                        ts="1000",
                        ccy="USDC",
                        type="1",
                        subType="11",
                        bal="10",
                        balChg="10",
                    )
                ]
            )
        elif url.path.endswith("/bills-history") and self.funding_pages is not None:
            rows = self.funding_pages.pop(0)
        else:
            rows = []
        body = json.dumps({"code": "0", "data": rows}, separators=(",", ":")).encode()

        class Response:
            status = 200
            url = req.full_url

            def read(self):
                return body

        yield Response()


def acquire(tmp_path, opener=None):
    opener = opener or EquityOpener()
    journal = PrivateEquityJournalV1(
        tmp_path / "journal", expected_account_identity=ACCOUNT, source_commit="injected-http-test"
    )
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="injected-journal",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            manifest = collect_real_equity_journal_v1(source, journal)
            assert source.transport._transport.raw_response_sink_v1 is None
    return journal, manifest, opener


def test_actual_k1_signer_to_private_original_body_capture_and_offline_reload(tmp_path):
    journal, manifest, opener = acquire(tmp_path)
    assert len(opener.requests) == len(manifest["entries"]) == 10
    assert stat.S_IMODE(journal.root.stat().st_mode) == 0o700
    digest = sha256((journal.root / "manifest.json").read_bytes()).hexdigest()
    with patch.object(
        wire, "build_opener", side_effect=AssertionError("offline replay must not GET")
    ):
        loaded, records = load_real_equity_journal_v1(journal.root, expected_manifest_sha256=digest)
    assert loaded["account_identity"] == ACCOUNT
    assert records["archive_1"]["rows"] == []
    assert records["recent_0"]["rows"] == []
    assert loaded["orders_or_transfers"] == 0 and loaded["authority_effect"] == "NONE"
    for path in journal.root.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert "Ok-access-sign" not in path.read_text()
        assert "secret_key" not in path.read_text()


def test_wrong_account_stops_after_one_read_and_seals_failure(tmp_path):
    opener = EquityOpener(account="other")
    with pytest.raises(RealEquityJournalError, match="ACCOUNT_MISMATCH"):
        acquire(tmp_path, opener)
    assert len(opener.requests) == 1
    manifest = json.loads((tmp_path / "journal/manifest.json").read_text())
    assert manifest["status"] == "FAILED"


def test_cursor_failure_keeps_original_failure_evidence(tmp_path):
    with pytest.raises(RealEquityJournalError, match="CURSOR_NOT_PROGRESSING"):
        acquire(tmp_path, EquityOpener(broken_cursor=True))
    manifest = json.loads((tmp_path / "journal/manifest.json").read_text())
    assert manifest["status"] == "FAILED" and len(manifest["entries"]) == 5


def test_existing_target_is_never_overwritten_and_public_parent_is_rejected(tmp_path):
    journal, _, _ = acquire(tmp_path)
    with pytest.raises(FileExistsError):
        PrivateEquityJournalV1(
            journal.root, expected_account_identity=ACCOUNT, source_commit="test"
        )
    parent = tmp_path / "public"
    parent.mkdir(mode=0o755)
    with pytest.raises(RealEquityJournalError, match="PARENT_NOT_PRIVATE"):
        PrivateEquityJournalV1(
            parent / "journal", expected_account_identity=ACCOUNT, source_commit="test"
        )


def test_tampered_original_record_and_unbound_manifest_are_rejected(tmp_path):
    journal, _, _ = acquire(tmp_path)
    digest = sha256((journal.root / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(RealEquityJournalError, match="MANIFEST_HASH_MISMATCH"):
        load_real_equity_journal_v1(journal.root, expected_manifest_sha256="a" * 64)
    path = journal.root / "response_000.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(RealEquityJournalError, match="RECORD_HASH_MISMATCH"):
        load_real_equity_journal_v1(journal.root, expected_manifest_sha256=digest)


def test_funding_supplement_records_native_taxonomy_and_empty_history(tmp_path):
    journal = PrivateEquityJournalV1(
        tmp_path / "funding", expected_account_identity=ACCOUNT, source_commit="injected-http-test"
    )
    opener = EquityOpener()
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="injected-funding",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            manifest = collect_equity_funding_supplement_v1(source, journal, pace=lambda _: None)
    assert len(opener.requests) == 6
    assert manifest["labels"]["bill_taxonomy"] == 2
    assert manifest["labels"]["funding_history_0"] == 3
    assert manifest["status"] == "ACQUIRED"


@pytest.mark.parametrize("full_page", [False, True])
def test_funding_uses_timestamp_cursor_and_denies_a_full_tied_boundary(tmp_path, full_page):
    rows = [
        dict(billId=str(500 + n), ts="1789407907000", ccy="EUR", type="1", balChg="1", bal="1")
        for n in range(100 if full_page else 1)
    ]
    opener = EquityOpener(funding_pages=[rows, []])
    journal = PrivateEquityJournalV1(
        tmp_path / "funding", expected_account_identity=ACCOUNT, source_commit="injected-http-test"
    )
    waits = []
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="timestamp",
            max_request_count=10,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            if full_page:
                with pytest.raises(
                    RealEquityJournalError, match="TIMESTAMP_PAGE_BOUNDARY_AMBIGUOUS"
                ):
                    collect_equity_funding_supplement_v1(source, journal, pace=waits.append)
                assert journal.sealed and len(opener.requests) == 4
            else:
                collect_equity_funding_supplement_v1(source, journal, pace=waits.append)
                assert "after=1789407907000" in opener.requests[4]
                assert waits == [1.1]
