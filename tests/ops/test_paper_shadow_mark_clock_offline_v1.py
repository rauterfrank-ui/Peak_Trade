"""Original Mark/book readback and rejected-capture retention; no network."""

from dataclasses import replace
from hashlib import sha256
import json
import socket

import pytest

from scripts.ops import run_zkp_lane1_paper_v1 as paper
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    bind_zkp_paper_market_v1,
    collect_zkp_paper_market_v1,
    zkp_public_queries_v1,
    XperpPaperSlotV1,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as transport_module,
)
from src.ops.instrument_card_stream_v1 import default_shadow_card_source_v1
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    _typed_cycle_market_time,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.market_data_price_basis_v2 import (
    build_explicit_mid_price_basis_v2,
)
from tests.ops.test_zkp_lane1_paper_opening_v1 import REPO, _observations


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("OFFLINE_ONLY")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)


@pytest.mark.parametrize("port", ["paper", "shadow"])
@pytest.mark.parametrize("fault", ["g17", "funding", "partial_transport"])
def test_rejected_capture_keeps_original_bytes_and_receipts(tmp_path, monkeypatch, port, fault):
    slot = paper.ZKP_PAPER_SLOT if port == "paper" else XperpPaperSlotV1("LANE_2", "SOPH", "310912")
    receipts, policy, observed = _observations(slot=slot)
    if fault == "g17":
        for row in receipts["mark-candles"].payload["data"]:
            row[0] = str(int(row[0]) - 60_000)
    elif fault == "funding":
        row = receipts["funding"].payload["data"][0]
        row["fundingTime"] = row["prevFundingTime"]
    by_endpoint = {receipt.endpoint: (name, receipt) for name, receipt in receipts.items()}
    originals = {}

    class RecordedTransport:
        def __init__(self, **kwargs):
            self.raw_response_sink_v1 = None
            self.count = 0

        def get(self, *, endpoint, auth_required, **kwargs):
            assert auth_required is False
            if fault == "partial_transport" and self.count == 3:
                raise OSError("RECORDED_TRANSPORT_INTERRUPTION")
            name, receipt = by_endpoint[endpoint]
            body = json.dumps(receipt.payload).encode()
            originals[name] = body
            receipt = replace(receipt, body_sha256=sha256(body).hexdigest())
            self.raw_response_sink_v1(result=receipt, body=body)
            self.count += 1
            return receipt

    monkeypatch.setattr(paper, "FullCoreProductiveReadOnlyGetTransportV1", RecordedTransport)
    monkeypatch.setattr(
        transport_module, "FullCoreProductiveReadOnlyGetTransportV1", RecordedTransport
    )
    if port == "paper":

        def collect(*args, **kwargs):
            return collect_zkp_paper_market_v1(*args, **kwargs, clock=lambda: observed)

        monkeypatch.setattr(paper, "collect_zkp_paper_market_v1", collect)

        def capture():
            return paper._capture(policy, label="recorded", output=tmp_path)

        output = tmp_path
    else:
        source = default_shadow_card_source_v1(repo=REPO, capture_root=tmp_path)

        def capture():
            return source(slot=slot, capture_id="recorded", clock=lambda: observed)

        output = tmp_path / sha256(b"recorded").hexdigest()
    with pytest.raises(
        (ValueError, OSError),
        match={
            "g17": "G17_AND_C1_CLOCK_MISMATCH",
            "funding": "FUNDING_CLOCK_OR_BOUNDS_INVALID",
            "partial_transport": "RECORDED_TRANSPORT_INTERRUPTION",
        }[fault],
    ):
        capture()
    stored = json.loads((output / "receipts.json").read_bytes())
    assert len(stored) == (
        3 if fault == "partial_transport" else len(zkp_public_queries_v1(policy.adv_days))
    )
    assert stored.keys() == originals.keys()
    for label, row in stored.items():
        assert "payload" not in row
        assert row["acquired_at_utc"] == receipts[label].acquired_at_utc
        assert row["endpoint"] == receipts[label].endpoint
        assert row["auth_header_sent"] is False
        assert (output / (label + ".json")).read_bytes() == originals[label]
        assert sha256(originals[label]).hexdigest() == row["body_sha256"]


@pytest.mark.parametrize("fault", ["old_c1", "old_g17", "funding_transition", "expired_funding"])
def test_clock_gates_keep_rejecting_unaligned_original_sources(fault):
    receipts, policy, observed = _observations()
    if fault in {"old_c1", "old_g17"}:
        key = "trade-candles" if fault == "old_c1" else "mark-candles"
        for row in receipts[key].payload["data"]:
            row[0] = str(int(row[0]) - 60_000)
        reason = "G17_AND_C1_CLOCK_MISMATCH"
    else:
        row = receipts["funding"].payload["data"][0]
        if fault == "funding_transition":
            row["prevFundingTime"] = row["fundingTime"]
        else:
            row["fundingTime"] = str(int((observed - 1) * 1000))
        reason = "FUNDING_CLOCK_OR_BOUNDS_INVALID"
    with pytest.raises(ValueError, match=reason):
        bind_zkp_paper_market_v1(receipts, policy=policy, observed_unix=observed)


@pytest.mark.parametrize(
    "fault", [None, "price", "bid", "last_label", "quote_future", "quote_nan", "quote_removed"]
)
def test_mark_and_execution_book_must_match_original_cycle(fault):
    mark = dict(
        event_ts_unix=100.0,
        mark_receive_ts_unix=100.1,
        receive_ts_unix=100.1,
        mid_price=0.0009249,
        mark_px=0.0009249,
        canonical_instrument_id="canonical",
        venue_instrument_id="native",
        mapping_digest="mapping",
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        price_basis_quote=dict(
            bid_px=0.0009239,
            ask_px=0.000926,
            endpoint="/api/v5/market/books",
            body_sha256="a" * 64,
            event_ts_unix=99.9,
            acquired_at_utc="1970-01-01T00:01:40Z",
        ),
    )
    basis = build_explicit_mid_price_basis_v2(
        mid_price=mark["mid_price"],
        event_ts_unix=100.0,
        receive_ts_unix=100.1,
        price_field="markPx",
        bid_px=0.0009239,
        ask_px=0.000926,
        quote_source="public_book",
    )
    cycle = dict(
        session_id="session",
        instrument_id="canonical",
        price_basis=basis.to_dict(),
        market_data_reference=basis.market_data_reference,
        shadow_decision_timing=dict(
            mark_event_ts_unix=100.0,
            mark_receive_ts_unix=100.1,
            decision_input_available_ts_unix=100.2,
            decision_cycle_ts_unix=100.3,
        ),
    )
    session = dict(
        session_id="session",
        canonical_instrument_id="canonical",
        venue_instrument_id="native",
        mapping_digest="mapping",
    )
    if fault == "price":
        cycle["price_basis"]["mid_price"] *= 2
    elif fault == "bid":
        mark["price_basis_quote"]["bid_px"] -= 0.0000001
    elif fault == "last_label":
        cycle["price_basis"]["price_field"] = "last"
    elif fault == "quote_future":
        mark["price_basis_quote"]["acquired_at_utc"] = "1970-01-01T00:01:41Z"
    elif fault == "quote_nan":
        mark["price_basis_quote"]["bid_px"] = float("nan")
    elif fault == "quote_removed":
        mark.pop("price_basis_quote")
    if fault is None:
        assert _typed_cycle_market_time(cycle, mark, session) == 100.3
    else:
        with pytest.raises(ValueError, match="DDO_MARKET_"):
            _typed_cycle_market_time(cycle, mark, session)
