"""Only in-memory venue frames and a temporary evidence file; no endpoint is contacted."""

import json
import zlib
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from scripts.ops import up_paper_ws_depth_v1 as cli
from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    PaperBookV1,
    PaperLiquidityPolicyV1,
    PaperLiquiditySnapshotV1,
)
from src.ops.bounded_peaktrade_system_composition_v1.up_paper_depth_case_v1 import ReversalWindow
from src.ops.bounded_peaktrade_system_composition_v1.up_paper_depth_replay_v1 import (
    MS,
    compare_recording,
)

NATIVE = cli.UP_PAPER_SLOT.native_id
CHANNELS = {ch: dict(channel=ch, instId=NATIVE) for ch in ("mark-price", "books")}
PLAN = dict(
    schema="up_paper_joint_depth.v1",
    identity=dict(native_id=NATIVE, session="fixture", mode="PAPER"),
    subscriptions=list(CHANNELS.values()),
    endpoint="offline-fixture",
)
START = 100000


def mark(offset, px="100", **fields):
    row = dict(instId=NATIVE, instType="FUTURES", ts=str(START + offset), markPx=px)
    return dict(arg=CHANNELS["mark-price"], data=[dict(row, **fields)])


def book(offset, seq, prev, *, bids=None, asks=None, checksum=None):
    snapshot = prev == -1
    row = dict(
        seqId=seq,
        prevSeqId=prev,
        ts=str(START + offset),
        bids=([["99.9", "10"]] if snapshot else []) if bids is None else bids,
        asks=([["100.1", "10"]] if snapshot else []) if asks is None else asks,
    )
    if checksum is not None:
        row["checksum"] = checksum
    return dict(arg=CHANNELS["books"], action="snapshot" if snapshot else "update", data=[row])


ACK = [
    (1, dict(event="subscribe", arg=CHANNELS["mark-price"])),
    (2, dict(event="subscribe", arg=CHANNELS["books"])),
]


def window(*, start=0, end=1000, qty="6", side="BUY"):
    base = PaperLiquiditySnapshotV1(
        D(1),
        D(1000),
        D(1),
        D("0.01"),
        D(10),
        D(100),
        PaperBookV1((), ()),
        0,
        D(10**7),
        PaperLiquidityPolicyV1(D(25), D(50), D(".1"), 30),
        {"adv": "fixture"},
    )
    return ReversalWindow(
        "decision", D(qty), side, START, (START + start) * MS, (START + end) * MS, base, {}
    )


class FakeSocket:
    def __init__(self, events):
        self.events = iter(events)
        self.now = START * MS
        self.closed = False

    def settimeout(self, timeout):
        self.timeout = timeout

    def getstatus(self):
        return 101

    def send(self, raw):
        assert json.loads(raw) == {"op": "subscribe", "args": list(CHANNELS.values())}

    def recv(self):
        next_frame = next(self.events, None)
        if next_frame is None:
            self.now += round(self.timeout * 10**9)
            raise TimeoutError
        offset, msg = next_frame
        self.now = (START + offset) * MS
        if isinstance(msg, Exception):
            raise msg
        return json.dumps(msg)

    def close(self):
        self.closed = True


def recording(tmp_path, monkeypatch, events, seconds=1, *, failure=None):
    ws = FakeSocket(events)
    clock = SimpleNamespace(
        time_ns=lambda: ws.now, monotonic_ns=lambda: ws.now, monotonic=lambda: ws.now / 10**9
    )
    monkeypatch.setattr(cli, "time", clock)
    path = tmp_path / "capture.jsonl"

    def record():
        cli.record(PLAN, path, seconds, connect=lambda *a, **kw: ws, timeout_error=TimeoutError)

    if failure:
        with pytest.raises(failure):
            record()
    else:
        record()
    assert ws.closed
    return path


@pytest.mark.parametrize("side", ["BUY", "SELL"])
def test_deep_tick_rounded_vwap_and_raw_receipt_order(tmp_path, monkeypatch, side):
    asks = [[str(D("100.01") + D(".01") * i), "1"] for i in range(6)]
    bids = [[str(D("99.99") - D(".01") * i), "1"] for i in range(6)]
    path = recording(
        tmp_path, monkeypatch, ACK + [(10, book(8, 3, -1, bids=bids, asks=asks)), (35, mark(12))]
    )
    report = compare_recording(path, PLAN, window(side=side))
    first = report["first_observed_liquidity_pass"]
    assert first["known_at_ns"] == (START + 35) * MS
    assert first["mark_minus_book_ms"] == 4 and first["book_frame"] == 3
    assert first["liquidity"]["open_price_quote"] == ("100.04" if side == "BUY" else "99.96")
    assert report["unassessable_intervals"][-1]["until_ns"] == first["known_at_ns"]
    assert json.loads(path.read_text().splitlines()[3])["raw"] == json.dumps(
        book(8, 3, -1, bids=bids, asks=asks)
    )


def test_missing_delta_invalidates_intervening_mark_then_recovers_only_from_snapshot(
    tmp_path, monkeypatch
):
    events = ACK + [
        (5, book(5, 10, -1)),
        (9, mark(8)),
        (20, book(18, 99, 11)),
        (30, book(30, 104, 99)),
        (40, book(40, 2, -1)),
        (43, mark(42)),
    ]
    report = compare_recording(recording(tmp_path, monkeypatch, events), PLAN, window())
    assert report["first_observed_liquidity_pass"]["known_at_ns"] == (START + 43) * MS
    assert any(
        "sequence break" in gap["reason"] and gap["from_ns"] <= (START + 9) * MS
        for gap in report["unassessable_intervals"]
    )


def test_delta_size_deletion_sequence_jump_and_checksum(tmp_path, monkeypatch):
    checksum = zlib.crc32(b"99.9:10:100.1:10")
    events = ACK + [
        (10, mark(10)),
        (20, book(20, 400, -1, asks=[["102", "10"]])),
        (21, book(21, 409, 400, asks=[["102", "0"], ["100.1", "10"]], checksum=checksum)),
        (22, book(22, 409, 409, checksum=checksum)),
    ]
    report = compare_recording(recording(tmp_path, monkeypatch, events), PLAN, window())
    first = report["first_observed_liquidity_pass"]
    assert first["book_seq_id"] == 409 and first["checksum"] == "verified"
    assert report["assessment_counts"] == {
        "evaluated": 2,
        "ZKP_PAPER_SPREAD_LIMIT": 1,
        "ZKP_PAPER_SLIPPAGE_LIMIT": 1,
        "liquidity_pass": 1,
    }


@pytest.mark.parametrize(
    "invalid, reason",
    [
        (book(12, 2, 1, checksum=41), "checksum"),
        (book(12, 2, 1, bids=[["102", "1"]]), "CROSSED"),
        (book(12, 1, 1, bids=[["99.9", "1"]]), "sequence"),
        (book(12, 0, 1), "sequence"),
        (book(9, 2, 1), "regressing"),
        (book(16, 2, 1), "future"),
        (book(12, 2, 1, asks=[["100.005", "1"]]), "grid"),
    ],
)
def test_invalid_book_fails_closed(tmp_path, monkeypatch, invalid, reason):
    events = ACK + [(10, book(10, 1, -1)), (15, invalid), (18, mark(18))]
    report = compare_recording(recording(tmp_path, monkeypatch, events), PLAN, window())
    assert report["first_observed_liquidity_pass"] is None
    assert any(reason in gap["reason"] for gap in report["unassessable_intervals"])


def test_missing_mark_stale_book_duplicate_cannot_extend_freshness(tmp_path, monkeypatch):
    events = ACK + [
        (10, book(10, 6, -1)),
        (4500, book(4500, 6, 6)),
        (5100, mark(5050)),
        (5200, book(5190, 9, 6, bids=[["99.9", "12"]])),
    ]
    report = compare_recording(recording(tmp_path, monkeypatch, events, 6), PLAN, window(end=6000))
    assert report["first_observed_liquidity_pass"]["book_frame"] == 6
    assert any(g["reason"] == "books freshness expired" for g in report["unassessable_intervals"])


def test_missing_depth_and_price_limits_are_distinct(tmp_path, monkeypatch):
    path = recording(
        tmp_path, monkeypatch, ACK + [(6, mark(6)), (7, book(7, 1, -1, bids=[["99.9", "1"]]))]
    )
    result = compare_recording(path, PLAN, window())
    assert result["assessment_counts"] == {
        "evaluated": 1,
        "ZKP_PAPER_EXECUTABLE_DEPTH_INSUFFICIENT": 1,
    }
    assert result["first_observed_liquidity_pass"] is None


def test_bad_ack_or_wrong_instrument_cannot_be_joined(tmp_path, monkeypatch):
    events = [ACK[0], (3, book(3, 1, -1)), (5, ACK[1][1])]
    report = compare_recording(recording(tmp_path, monkeypatch, events), PLAN, window())
    assert report["recording"]["protocol_error"] == "unconfirmed or interrupted subscription"
    with pytest.raises(ValueError, match="binding"):
        compare_recording(
            tmp_path / "capture.jsonl",
            dict(PLAN, identity=dict(PLAN["identity"], mode="TESTNET")),
            window(),
        )


def test_start_window_carry_in_and_exclusive_end(tmp_path, monkeypatch):
    path = recording(tmp_path, monkeypatch, ACK + [(10, mark(10)), (20, book(20, 1, -1))])
    result = compare_recording(path, PLAN, window(start=40))
    assert result["first_observed_liquidity_pass"]["known_at_ns"] == (START + 40) * MS
    assert compare_recording(path, PLAN, window(end=20))["first_observed_liquidity_pass"] is None
    late = compare_recording(path, PLAN, window(start=1100, end=1200))
    assert late["unassessable_intervals"] == [
        dict(from_ns=(START + 1100) * MS, until_ns=(START + 1200) * MS, reason="outside recording")
    ]


def test_disconnect_and_corruption(tmp_path, monkeypatch):
    path = recording(
        tmp_path, monkeypatch, ACK + [(15, ConnectionError("lost"))], failure=ConnectionError
    )
    result = compare_recording(path, PLAN, window())
    assert (
        result["recording"]["end_status"] == "lost"
        and result["first_observed_liquidity_pass"] is None
    )
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        cli.record(
            PLAN, path, 1, connect=lambda *_: pytest.fail("opened"), timeout_error=TimeoutError
        )
    path.write_bytes(original.replace(b'"frame": 2', b'"frame": 3'))
    with pytest.raises(ValueError, match="unordered"):
        compare_recording(path, PLAN, window())
    path.write_bytes(original.replace(b"subscribe", b"corrupted"))
    with pytest.raises(ValueError, match="digest"):
        compare_recording(path, PLAN, window())
    path.write_bytes(original[: original.rindex(b'{"kind": "end"')])
    with pytest.raises(ValueError, match="incomplete recording"):
        compare_recording(path, PLAN, window())


@pytest.mark.parametrize(
    "mode,native", [("TESTNET", NATIVE), ("SHADOW", "UP-USDT-SWAP"), ("PAPER_EXCHANGE", "BTC-USD")]
)
def test_only_up_paper_binding_allowed(tmp_path, mode, native):
    path = tmp_path / "slot.json"
    path.write_text(
        json.dumps(
            dict(
                surface=mode,
                canonical_instrument_id=cli.UP_PAPER_SLOT.instrument_id,
                native_instrument_id=native,
            )
        )
    )
    with pytest.raises(ValueError, match="UP dated future"):
        cli.preparation(SimpleNamespace(slot_config=path))


@pytest.mark.parametrize(
    "wrong", [mark(20, instId="UP-USDT-SWAP"), mark(25), mark(20, instType="SWAP")]
)
def test_unusable_mark_cannot_reuse_an_older_price(tmp_path, monkeypatch, wrong):
    events = ACK + [(10, mark(10)), (21, wrong), (23, book(23, 1, -1)), (26, mark(26))]
    result = compare_recording(recording(tmp_path, monkeypatch, events), PLAN, window())
    assert result["first_observed_liquidity_pass"]["mark_frame"] == 6


def test_late_correction_at_same_exchange_time_applies_only_on_receipt(tmp_path, monkeypatch):
    events = ACK + [(10, book(10, 1, -1)), (20, mark(20, "99")), (80, mark(20, "100"))]
    result = compare_recording(recording(tmp_path, monkeypatch, events), PLAN, window())
    first = result["first_observed_liquidity_pass"]
    assert (first["known_at_ns"], first["mark_event_ms"]) == ((START + 80) * MS, START + 20)
    assert result["assessment_counts"]["ZKP_PAPER_SLIPPAGE_LIMIT"] == 1


def test_usd_adv_and_rest_top_50_depth_constraints(tmp_path, monkeypatch):
    from dataclasses import replace

    levels = [[str(D("100.01") + D(".01") * i), "1"] for i in range(51)]
    path = recording(
        tmp_path,
        monkeypatch,
        ACK + [(10, mark(10)), (12, book(12, 1, -1, asks=levels, bids=[["99.9", "100"]]))],
    )
    assert (
        compare_recording(path, PLAN, window(qty="51"))["assessment_counts"][
            "ZKP_PAPER_EXECUTABLE_DEPTH_INSUFFICIENT"
        ]
        == 1
    )
    base = window()
    limited = replace(base, liquidity=replace(base.liquidity, adv_quote=D("100")))
    result = compare_recording(path, PLAN, limited)
    assert result["assessment_counts"]["ZKP_PAPER_ADV_PARTICIPATION_LIMIT"] == 1


def test_missing_channel_and_unrecorded_tail_cannot_prove_a_pass(tmp_path, monkeypatch):
    path = recording(tmp_path, monkeypatch, ACK + [(5, mark(5))])
    result = compare_recording(path, PLAN, window(end=2000))
    assert result["first_observed_liquidity_pass"] is None
    assert result["unassessable_intervals"][-2]["reason"] == "awaiting books data"
    assert result["unassessable_intervals"][-1]["reason"] == "outside recording"
    path.write_bytes(path.read_bytes().replace(b"duration_elapsed", b"disconnected"))
    with pytest.raises(ValueError, match="digest"):
        compare_recording(path, PLAN, window())


def test_prepare_uses_entry_binding_and_retains_n5_occupancy(tmp_path, monkeypatch):
    from scripts.ops import run_zkp_lane1_paper_v1 as driver

    slot = cli.UP_PAPER_SLOT
    config = dict(
        surface="PAPER_EXCHANGE",
        session_id="fixture",
        native_instrument_id=slot.native_id,
        canonical_instrument_id=slot.instrument_id,
        paper_cap24={"root": str(tmp_path)},
        paper_entry_admission={},
    )
    path = tmp_path / "slot.json"
    path.write_text(json.dumps(config))
    prior = SimpleNamespace(
        selection=SimpleNamespace(integrity_digest="original", repository_sha="rev")
    )
    checks = []
    entry = SimpleNamespace(
        selection=SimpleNamespace(integrity_digest="renewed"), require_binding_v1=checks.append
    )
    monkeypatch.setattr(cli, "read_ranked_paper_slot_v1", lambda config: (prior, slot))
    monkeypatch.setattr(cli, "read_paper_entry_admission_v1", lambda config, original: entry)
    monkeypatch.setattr(driver, "_read_cap24_binding", lambda root, entry_repository_sha: "bound")
    monkeypatch.setattr(
        driver, "_verify_renewed_paper_cap24", lambda *args: checks.append(args[2:])
    )
    result = cli.preparation(SimpleNamespace(slot_config=path))
    assert checks == ["bound", (prior, entry, "bound")]
    assert result["identity"]["binding_digest"] == "renewed"
    assert result["identity"]["occupancy_digest"] == "original"
    assert result["subscriptions"] == list(CHANNELS.values())


def test_record_deadline_preserves_nanosecond_remainder(tmp_path, monkeypatch):
    ws = FakeSocket([])
    ws.now = 1795429871234567890
    clock = SimpleNamespace(time_ns=lambda: ws.now, monotonic_ns=lambda: ws.now)
    monkeypatch.setattr(cli, "time", clock)
    path = tmp_path / "deadline.jsonl"
    cli.record(PLAN, path, 1, connect=lambda *args, **kwargs: ws)
    header, footer = map(json.loads, path.read_text().splitlines())
    assert footer["status"] == "duration_elapsed"
    assert footer["received_mono_ns"] == header["received_mono_ns"] + 10**9
