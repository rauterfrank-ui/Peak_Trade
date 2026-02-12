from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional
import json


def _stable_json_dumps(obj: Any) -> str:
    # Deterministic: sorted keys, no whitespace, UTF-8, disallow NaN/Inf.
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


@dataclass(frozen=True)
class NormalizedEvent:
    """
    Minimal contract (Runbook A2):
      event_id: stable unique id (string)
      ts_ms: event timestamp in milliseconds since epoch (int)
      source: origin descriptor (e.g. "binance.ws", "kraken.rest", "shadow.sim")
      kind: event kind (e.g. "trade", "orderbook_snapshot", "balance_update")
      scope: namespace-like routing key (e.g. "market.BTCUSDT", "account.main")
      tags: small list of labels (e.g. ["shadow", "testnet"])
      sensitivity: "public"|"internal"|"restricted"
      payload: JSON-serializable mapping
    """

    event_id: str
    ts_ms: int
    source: str
    kind: str
    scope: str
    tags: List[str] = field(default_factory=list)
    sensitivity: str = "internal"
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_json_line(self) -> str:
        d: Dict[str, Any] = {
            "event_id": self.event_id,
            "ts_ms": self.ts_ms,
            "source": self.source,
            "kind": self.kind,
            "scope": self.scope,
            "tags": list(self.tags),
            "sensitivity": self.sensitivity,
            "payload": self.payload,
        }
        return _stable_json_dumps(d) + "\n"

    @staticmethod
    def from_json_line(line: str) -> "NormalizedEvent":
        obj = json.loads(line)
        return NormalizedEvent(
            event_id=obj["event_id"],
            ts_ms=int(obj["ts_ms"]),
            source=obj["source"],
            kind=obj["kind"],
            scope=obj["scope"],
            tags=list(obj.get("tags", [])),
            sensitivity=obj.get("sensitivity", "internal"),
            payload=obj.get("payload", {}),
        )
