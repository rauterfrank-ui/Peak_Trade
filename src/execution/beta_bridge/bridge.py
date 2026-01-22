from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from src.execution.ledger import LedgerEngine

from .canonical import canonical_json_bytes, canonical_jsonl_bytes
from .schema import BetaEventSchemaError, dedupe_by_event_id, sort_key_beta_exec_v1
from .sink import DeterministicArtifactSink


@dataclass(frozen=True)
class BetaBridgeConfig:
    quote_currency: str
    # Optional: opening cash booked before replay (deterministic, explicit).
    opening_cash: Optional[str] = None

    # Equity curve behavior.
    emit_equity_curve: bool = False


@dataclass(frozen=True)
class BetaBridgeArtifacts:
    """
    Relative paths (within sink.output_dir) for stable artifacts.
    """

    normalized_beta_events_jsonl: str = "normalized_beta_events.jsonl"
    ledger_applied_events_jsonl: str = "ledger_applied_events.jsonl"
    ledger_final_state_json: str = "ledger_final_state.json"
    equity_curve_jsonl: str = "equity_curve.jsonl"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for i, line in enumerate(raw):
        line_s = line.strip()
        if not line_s:
            continue
        try:
            obj = json.loads(line_s)
        except Exception as ex:  # noqa: BLE001
            raise ValueError(f"Invalid JSONL at line {i + 1}") from ex
        if not isinstance(obj, Mapping):
            raise ValueError(f"JSONL line {i + 1} must be an object")
        out.append(dict(obj))
    return out


def _final_state_export(
    engine: LedgerEngine, *, applied_event_ids_in_order: Sequence[str]
) -> Dict[str, Any]:
    st = engine.state
    accounts_sorted = [
        {"account": k, "balance": str(st.accounts[k])} for k in sorted(st.accounts.keys())
    ]
    positions_sorted = [st.positions[s].to_dict() for s in sorted(st.positions.keys())]
    journal_list = [je.to_dict() for je in st.journal]
    return {
        "quote_currency": st.quote_currency,
        "last_ts_sim": st.last_ts_sim,
        "applied_event_ids": list(applied_event_ids_in_order),
        "accounts": accounts_sorted,
        "positions": positions_sorted,
        "journal": journal_list,
    }


class BetaEventBridge:
    """
    Deterministic bridge: beta_events -> LedgerEngine + stable artifacts.
    """

    def __init__(self, *, config: BetaBridgeConfig):
        self.config = config

    def run(
        self,
        *,
        events: Optional[Iterable[Mapping[str, Any]]] = None,
        events_jsonl_path: Optional[Path] = None,
        sink: DeterministicArtifactSink,
        artifacts: BetaBridgeArtifacts = BetaBridgeArtifacts(),
        # Prices: deterministic mark prices used for optional equity curve.
        # Mapping: ts_sim -> {symbol: Decimal}
        mark_prices_by_ts: Optional[Mapping[int, Mapping[str, Any]]] = None,
        # Metadata must be deterministic and must not contain absolute paths / wall-clock.
        snapshot_meta: Optional[Mapping[str, Any]] = None,
    ) -> BetaBridgeArtifacts:
        if (events is None) == (events_jsonl_path is None):
            raise ValueError("Pass exactly one of events or events_jsonl_path")

        raw_events: list[Mapping[str, Any]]
        if events_jsonl_path is not None:
            raw_events = _read_jsonl(Path(events_jsonl_path))
        else:
            raw_events = list(events or [])

        # Normalize + validate + dedupe
        normalized = dedupe_by_event_id(raw_events)

        # Deterministic sort
        normalized_sorted = sorted(normalized, key=sort_key_beta_exec_v1)

        # Emit canonical normalized events JSONL
        sink.write_bytes(
            relpath=artifacts.normalized_beta_events_jsonl,
            data=canonical_jsonl_bytes(normalized_sorted),
        )

        # Replay into LedgerEngine
        eng = LedgerEngine(quote_currency=self.config.quote_currency)
        if self.config.opening_cash is not None:
            eng.open_cash(amount=Decimal(self.config.opening_cash))

        applied_rows: list[dict[str, Any]] = []
        equity_rows: list[dict[str, Any]] = []
        applied_event_ids: list[str] = []

        meta_clean = dict(snapshot_meta or {})

        for ev in normalized_sorted:
            # Replay-safe: LedgerEngine enforces idempotency via event_id.
            eng.apply(ev)
            applied_event_ids.append(str(ev["event_id"]))

            applied_rows.append(
                {
                    "event_id": str(ev["event_id"]),
                    "ts_sim": int(ev["ts_sim"]),
                    "event_type": str(ev["event_type"]),
                    "symbol": str(ev["symbol"]),
                    "ledger_effective": bool(ev["event_type"] == "FILL"),
                }
            )

            if self.config.emit_equity_curve:
                ts = int(ev["ts_sim"])
                mp_raw = (mark_prices_by_ts or {}).get(ts, {})
                mp: Dict[str, Decimal] = {}
                for k in sorted(mp_raw.keys()):
                    v = mp_raw[k]
                    if isinstance(v, float):
                        raise BetaEventSchemaError(
                            "float forbidden in mark_prices_by_ts (pass str/int/Decimal)"
                        )
                    mp[str(k)] = Decimal(str(v)) if not isinstance(v, Decimal) else v

                snap = eng.snapshot(ts_sim=ts, mark_prices=mp, meta=meta_clean)
                equity_rows.append(
                    {
                        "ts_sim": snap.ts_sim,
                        "equity": str(snap.equity),
                        "cash": str(snap.cash),
                        "realized_pnl": str(snap.realized_pnl),
                        "unrealized_pnl": str(snap.unrealized_pnl),
                    }
                )

        sink.write_bytes(
            relpath=artifacts.ledger_applied_events_jsonl, data=canonical_jsonl_bytes(applied_rows)
        )

        final_state = _final_state_export(eng, applied_event_ids_in_order=applied_event_ids)
        sink.write_bytes(
            relpath=artifacts.ledger_final_state_json, data=canonical_json_bytes(final_state)
        )

        if self.config.emit_equity_curve:
            sink.write_bytes(
                relpath=artifacts.equity_curve_jsonl, data=canonical_jsonl_bytes(equity_rows)
            )

        return artifacts
