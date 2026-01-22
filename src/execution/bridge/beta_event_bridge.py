from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Protocol, Sequence

from .artifact_sink import ArtifactSink
from .canonical_json import dumps_canonical, validate_no_floats
from .run_fingerprint import run_fingerprint


class BetaEventBridgeError(ValueError):
    pass


DEFAULT_EVENT_TYPE_RANK: dict[str, int] = {
    "Price": 0,
    "OrderIntent": 10,
    "OrderRequest": 20,
    "Order": 30,
    "Fill": 40,
    "Cancel": 50,
    "Reject": 60,
    "Adjustment": 70,
    "Fee": 80,
    "SnapshotMarker": 90,
}


def _type_rank(event_type: str, mapping: Mapping[str, int]) -> int:
    return int(mapping.get(event_type, 999))


def _assert_no_floats(x: Any, *, path: str = "$") -> None:
    # Keep a single source of truth for float rejection.
    try:
        validate_no_floats(x, path=path)
    except Exception as ex:  # noqa: BLE001
        raise BetaEventBridgeError(str(ex)) from ex


def _stable_hash_hex(obj: Mapping[str, Any]) -> str:
    return hashlib.sha256(dumps_canonical(dict(obj))).hexdigest()


def _derive_t(raw: Mapping[str, Any]) -> int:
    if "t" in raw:
        return int(raw["t"])
    if "ts_sim" in raw:
        return int(raw["ts_sim"])
    if "idx" in raw:
        return int(raw["idx"])
    raise BetaEventBridgeError("Missing logical time field 't' (or derivable 'ts_sim'/'idx')")


def _normalize_event(raw: Mapping[str, Any]) -> dict[str, Any]:
    event_type = raw.get("event_type")
    if event_type is None:
        raise BetaEventBridgeError("Missing event_type")
    event_type_s = str(event_type)
    t = _derive_t(raw)

    source = str(raw.get("source") or "beta")
    payload = raw.get("payload", {})
    if payload is None:
        payload = {}
    if not isinstance(payload, Mapping):
        raise BetaEventBridgeError("payload must be a dict-like mapping")
    payload_d = dict(payload)

    # Hard constraint: forbid floats anywhere.
    _assert_no_floats(payload_d, path="$.payload")

    seq = raw.get("seq", None)
    if seq is not None:
        seq = int(seq)

    out: dict[str, Any] = {
        "event_type": event_type_s,
        "t": int(t),
        "seq": seq,  # filled deterministically later if missing
        "source": source,
        "payload": payload_d,
    }
    _assert_no_floats(out)
    return out


def _initial_sort_key_for_seq(
    ev: Mapping[str, Any], *, type_rank: Mapping[str, int], original_index: int
) -> tuple:
    """
    Addendum rule for seq derivation:
    - stable sort by (t, rank, original_index)
    - assign seq as running counter in that sorted order
    """
    return (int(ev["t"]), _type_rank(str(ev["event_type"]), type_rank), int(original_index))


def _final_sort_key(ev: Mapping[str, Any], *, type_rank: Mapping[str, int]) -> tuple:
    return (
        int(ev["t"]),
        _type_rank(str(ev["event_type"]), type_rank),
        int(ev["seq"]),
        str(ev["event_id"]),
    )


def _compute_event_id(ev: Mapping[str, Any]) -> str:
    material = {
        "event_type": ev["event_type"],
        "t": ev["t"],
        "seq": ev["seq"],
        "source": ev["source"],
        "payload": ev["payload"],
    }
    return _stable_hash_hex(material)


def _jsonl_lines(events: Sequence[Mapping[str, Any]]) -> bytes:
    parts: list[bytes] = []
    for ev in events:
        parts.append(dumps_canonical(dict(ev)) + b"\n")
    return b"".join(parts)


class LedgerEngineLike(Protocol):
    def apply(self, event: Mapping[str, Any]) -> dict[str, Any]:  # pragma: no cover
        ...

    def get_state(self) -> dict[str, Any]:  # pragma: no cover
        ...


@dataclass(frozen=True)
class BetaEventBridgeConfig:
    emit_equity_curve: bool = False
    equity_snapshot_every_n_events: Optional[int] = None
    type_rank: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_EVENT_TYPE_RANK))

    def to_dict(self) -> dict[str, Any]:
        return {
            "emit_equity_curve": bool(self.emit_equity_curve),
            "equity_snapshot_every_n_events": self.equity_snapshot_every_n_events,
            "type_rank": dict(self.type_rank),
        }


@dataclass(frozen=True)
class BridgeResult:
    run_fingerprint: str
    counts: dict[str, int]
    artifact_relpaths: dict[str, str]


class BetaEventBridge:
    def __init__(
        self,
        ledger_engine: LedgerEngineLike,
        *,
        prices_manifest_or_ref: Optional[Mapping[str, Any]] = None,
        config: Optional[BetaEventBridgeConfig] = None,
    ):
        self.ledger_engine = ledger_engine
        self.prices_manifest_or_ref = prices_manifest_or_ref or {}
        self.config = config or BetaEventBridgeConfig()

    def run(self, beta_events: Iterable[Mapping[str, Any]], *, sink: ArtifactSink) -> BridgeResult:
        # 1) normalize + validate (capture original_index for seq derivation)
        normalized_with_idx: list[tuple[int, dict[str, Any]]] = []
        for idx, raw in enumerate(beta_events):
            normalized_with_idx.append((idx, _normalize_event(raw)))
        normalized_count = len(normalized_with_idx)

        # 2) stable sort for seq derivation: (t, rank, original_index)
        seq_ordered = sorted(
            normalized_with_idx,
            key=lambda pair: _initial_sort_key_for_seq(
                pair[1], type_rank=self.config.type_rank, original_index=pair[0]
            ),
        )

        # 2b) assign/validate seq as running counter starting at 0 in that order
        with_seq: list[dict[str, Any]] = []
        for seq, (_orig_idx, ev) in enumerate(seq_ordered):
            if ev.get("seq") is not None and int(ev["seq"]) != int(seq):
                raise BetaEventBridgeError("Provided seq does not match derived deterministic seq")
            with_seq.append({**ev, "seq": int(seq)})

        # 3) compute event_id deterministically (over event_type,t,seq,source,payload)
        with_ids: list[dict[str, Any]] = [
            {**ev, "event_id": _compute_event_id(ev)} for ev in with_seq
        ]

        # 4) final sort + dedup (t, rank, seq, event_id)
        final_sorted = sorted(
            with_ids, key=lambda ev: _final_sort_key(ev, type_rank=self.config.type_rank)
        )
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        dup_count = 0
        for ev in final_sorted:
            eid = str(ev["event_id"])
            if eid in seen:
                dup_count += 1
                continue
            seen.add(eid)
            deduped.append(ev)

        # 5) emit normalized_beta_events.jsonl (canonical)
        normalized_jsonl = _jsonl_lines(deduped)

        # 5b) compute run fingerprint (depends on normalized events bytes + prices ref + config)
        fp = run_fingerprint(
            normalized_events_jsonl_bytes=normalized_jsonl,
            prices_manifest_or_ref=self.prices_manifest_or_ref,
            bridge_config=self.config.to_dict(),
        )

        artifact_relpaths = {
            "normalized_beta_events.jsonl": f"out/{fp}/normalized_beta_events.jsonl",
            "ledger_applied_events.jsonl": f"out/{fp}/ledger_applied_events.jsonl",
            "ledger_final_state.json": f"out/{fp}/ledger_final_state.json",
        }
        if self.config.emit_equity_curve:
            artifact_relpaths["equity_curve.jsonl"] = f"out/{fp}/equity_curve.jsonl"

        sink.write_bytes(artifact_relpaths["normalized_beta_events.jsonl"], normalized_jsonl)

        # 6) apply to ledger_engine in sorted order
        applied_rows: list[dict[str, Any]] = []
        equity_rows: list[dict[str, Any]] = []

        for idx, ev in enumerate(deduped):
            applied = self.ledger_engine.apply(ev)

            applied_rows.append(
                {
                    "event_id": str(ev["event_id"]),
                    "t": int(ev["t"]),
                    "seq": int(ev["seq"]),
                    "event_type": str(ev["event_type"]),
                    "applied": bool(applied.get("applied", False)),
                }
            )

            if self.config.emit_equity_curve:
                every = self.config.equity_snapshot_every_n_events
                should_emit = every is None or every <= 0 or ((idx + 1) % every == 0)
                if should_emit:
                    st = self.ledger_engine.get_state()
                    equity_rows.append(
                        {
                            "t": int(ev["t"]),
                            "cash_int": int(st["cash_int"]),
                            "equity_int": int(st["equity_int"]),
                            "realized_pnl_int": int(st["realized_pnl_int"]),
                            "unrealized_pnl_int": int(st["unrealized_pnl_int"]),
                            "fees_paid_int": int(st["fees_paid_int"]),
                            "positions": dict(st["positions"]),
                        }
                    )

        sink.write_bytes(
            artifact_relpaths["ledger_applied_events.jsonl"],
            _jsonl_lines(applied_rows),
        )

        # 8) emit ledger_final_state.json
        sink.write_bytes(
            artifact_relpaths["ledger_final_state.json"],
            dumps_canonical(self.ledger_engine.get_state()),
        )

        # 9) optional equity_curve.jsonl
        if self.config.emit_equity_curve:
            sink.write_bytes(artifact_relpaths["equity_curve.jsonl"], _jsonl_lines(equity_rows))

        return BridgeResult(
            run_fingerprint=fp,
            counts={
                "input_events": normalized_count,
                "normalized_events": normalized_count,
                "deduped_events": len(deduped),
                "duplicates_dropped": int(dup_count),
                "applied_events": len(deduped),
            },
            artifact_relpaths=artifact_relpaths,
        )
