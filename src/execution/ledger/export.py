from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .models import (
    FillEvent,
    LedgerEntry as Slice2LedgerEntry,
    LedgerSnapshot,
    MarkEvent,
    ValuationSnapshot,
)


def export_valuation_snapshot_json(snapshot: ValuationSnapshot) -> str:
    """
    Stable JSON export for a ValuationSnapshot.

    Contract:
    - sort_keys=True
    - stable separators
    - snapshot is expected to already contain quantized Decimal strings
    """
    return json.dumps(snapshot.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def export_mapping(obj: Mapping[str, Any]) -> str:
    """
    Stable JSON export for already-normalized mappings.
    """
    return json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# =============================================================================
# EXEC_SLICE2 canonical export (FIFO engine)
# =============================================================================


def _decimal_to_str(v: Any) -> Any:
    from decimal import Decimal

    if isinstance(v, Decimal):
        return str(v)
    return v


def _canonicalize_obj(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        # sort keys at dump-time; here we just recursively canonicalize values
        return {str(k): _canonicalize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_canonicalize_obj(v) for v in obj]
    if isinstance(obj, tuple):
        return [_canonicalize_obj(v) for v in obj]
    return _decimal_to_str(obj)


def to_canonical_dict(snapshot: LedgerSnapshot) -> dict:
    """
    Deterministic, JSON-serializable dict representation.

    Ordering rules:
    - positions: sorted by instrument
    - lots: sorted by (ts_utc, seq)
    """
    acct = snapshot.account

    positions_out: list[dict] = []
    for inst in sorted(acct.positions.keys()):
        pos = acct.positions[inst]
        lots_sorted = sorted(pos.lots, key=lambda l: (l.ts_utc, l.seq))
        positions_out.append(
            {
                "instrument": inst,
                "qty_signed": str(pos.qty_signed),
                "avg_price": None if pos.avg_price is None else str(pos.avg_price),
                "last_mark_price": None
                if pos.last_mark_price is None
                else str(pos.last_mark_price),
                "lots": [
                    {
                        "qty_signed": str(l.qty_signed),
                        "price": str(l.price),
                        "ts_utc": l.ts_utc,
                        "seq": int(l.seq),
                    }
                    for l in lots_sorted
                ],
            }
        )

    out = {
        "ts_utc_last": snapshot.ts_utc_last,
        "seq_last": int(snapshot.seq_last),
        "base_ccy": str(getattr(snapshot, "base_ccy", "") or getattr(acct, "base_ccy", "") or ""),
        "account": {
            "cash_by_ccy": {k: str(acct.cash_by_ccy[k]) for k in sorted(acct.cash_by_ccy.keys())},
            "realized_pnl_by_ccy": {
                k: str(acct.realized_pnl_by_ccy[k]) for k in sorted(acct.realized_pnl_by_ccy.keys())
            },
            "fees_by_ccy": {k: str(acct.fees_by_ccy[k]) for k in sorted(acct.fees_by_ccy.keys())},
            "positions": positions_out,
        },
        "unrealized_pnl_by_ccy": {
            k: str(snapshot.unrealized_pnl_by_ccy[k])
            for k in sorted(snapshot.unrealized_pnl_by_ccy.keys())
        },
        "equity_by_ccy": {k: str(snapshot.equity_by_ccy[k]) for k in sorted(snapshot.equity_by_ccy.keys())},
        "hash_inputs": _canonicalize_obj(snapshot.hash_inputs) if snapshot.hash_inputs is not None else None,
    }
    return out


def dumps_canonical_json(snapshot: LedgerSnapshot) -> bytes:
    """
    Canonical JSON bytes (UTF-8), suitable for stable hashing.
    """
    dct = to_canonical_dict(snapshot)
    s = json.dumps(dct, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def export_snapshot(path: str | Path, snapshot: LedgerSnapshot) -> None:
    p = Path(path)
    p.write_bytes(dumps_canonical_json(snapshot))


def _event_to_dict(ev: FillEvent | MarkEvent) -> dict:
    if isinstance(ev, FillEvent):
        return {
            "event_type": "FILL",
            "ts_utc": ev.ts_utc,
            "seq": int(ev.seq),
            "instrument": ev.instrument,
            "side": ev.side,
            "qty": str(ev.qty),
            "price": str(ev.price),
            "fee": str(ev.fee),
            "fee_ccy": ev.fee_ccy,
            "trade_id": ev.trade_id,
        }
    return {
        "event_type": "MARK",
        "ts_utc": ev.ts_utc,
        "seq": int(ev.seq),
        "instrument": ev.instrument,
        "price": str(ev.price),
    }


def export_events_jsonl(path: str | Path, events: Sequence[FillEvent | MarkEvent]) -> None:
    p = Path(path)
    lines = []
    for ev in events:
        obj = _event_to_dict(ev)
        lines.append(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def export_ledger_jsonl(path: str | Path, entries: Sequence[Slice2LedgerEntry]) -> None:
    p = Path(path)
    lines = []
    for e in entries:
        obj = {
            "ts_utc": e.ts_utc,
            "seq": int(e.seq),
            "kind": e.kind,
            "instrument": e.instrument,
            "fields": _canonicalize_obj(e.fields),
        }
        lines.append(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
