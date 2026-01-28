from __future__ import annotations

import hashlib
from decimal import Decimal

from src.execution.ledger import FillEvent, FifoLedgerEngine, MarkEvent
from src.execution.ledger.export import dumps_canonical_json


def _events() -> list[object]:
    return [
        FillEvent(
            ts_utc="2026-01-01T00:00:00Z",
            seq=1,
            instrument="ABC/USD",
            side="BUY",
            qty=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0.10"),
            fee_ccy="USD",
        ),
        MarkEvent(
            ts_utc="2026-01-01T00:00:01Z",
            seq=2,
            instrument="ABC/USD",
            price=Decimal("101"),
        ),
        FillEvent(
            ts_utc="2026-01-01T00:00:02Z",
            seq=3,
            instrument="ABC/USD",
            side="BUY",
            qty=Decimal("1"),
            price=Decimal("110"),
            fee=Decimal("0.10"),
            fee_ccy="USD",
        ),
        MarkEvent(
            ts_utc="2026-01-01T00:00:03Z",
            seq=4,
            instrument="ABC/USD",
            price=Decimal("105"),
        ),
        FillEvent(
            ts_utc="2026-01-01T00:00:04Z",
            seq=5,
            instrument="ABC/USD",
            side="SELL",
            qty=Decimal("1.5"),
            price=Decimal("120"),
            fee=Decimal("0.10"),
            fee_ccy="USD",
        ),
        MarkEvent(
            ts_utc="2026-01-01T00:00:05Z",
            seq=6,
            instrument="ABC/USD",
            price=Decimal("115"),
        ),
    ]


def test_determinism_same_event_stream_produces_identical_snapshots_and_hashes():
    def run_once() -> tuple[list[bytes], bytes]:
        eng = FifoLedgerEngine(base_ccy="USD")
        eng.open_cash(amount=Decimal("10000"), ccy="USD")

        snaps: list[bytes] = []
        for ev in _events():
            eng.apply(ev)  # deterministic
            ts_utc = ev.ts_utc  # type: ignore[attr-defined]
            seq = ev.seq  # type: ignore[attr-defined]
            snap = eng.snapshot(ts_utc_last=ts_utc, seq_last=seq)
            snaps.append(dumps_canonical_json(snap))

        final_hash = hashlib.sha256(snaps[-1]).digest()
        return snaps, final_hash

    a_snaps, a_hash = run_once()
    b_snaps, b_hash = run_once()

    assert a_snaps == b_snaps
    assert a_hash == b_hash
