from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .canonical import iter_jsonl
from .contract import MissingRequiredFileError


@dataclass(frozen=True)
class ReplayBundle:
    root: Path
    manifest: Dict[str, Any]

    def path(self, relpath: str) -> Path:
        return self.root / relpath

    def inputs_config(self) -> Optional[Dict[str, Any]]:
        p = self.root / "inputs" / "config_snapshot.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def execution_events(self) -> Iterable[Dict[str, Any]]:
        yield from iter_jsonl(self.root / "events" / "execution_events.jsonl")

    def expected_fills(self) -> Optional[Iterable[Dict[str, Any]]]:
        p = self.root / "outputs" / "expected_fills.jsonl"
        if not p.exists():
            return None
        return iter_jsonl(p)

    def expected_positions(self) -> Optional[Dict[str, Any]]:
        p = self.root / "outputs" / "expected_positions.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def market_data_refs(self) -> Optional[object]:
        """
        Optional market data references.

        Preferred location:
        - events/market_data_refs.json

        Fallback:
        - manifest.data_refs.market_data_refs
        """
        p = self.root / "events" / "market_data_refs.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        data_refs = self.manifest.get("data_refs")
        if isinstance(data_refs, dict) and "market_data_refs" in data_refs:
            return data_refs.get("market_data_refs")
        return None

    def ledger_fifo_snapshot(self) -> Optional[Dict[str, Any]]:
        p = self.root / "ledger" / "ledger_fifo_snapshot.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def ledger_fifo_entries(self) -> Optional[Iterable[Dict[str, Any]]]:
        p = self.root / "ledger" / "ledger_fifo_entries.jsonl"
        if not p.exists():
            return None
        return iter_jsonl(p)


def load_replay_pack(bundle_path: str | Path) -> ReplayBundle:
    root = Path(bundle_path)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise MissingRequiredFileError("manifest.json missing in bundle root")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return ReplayBundle(root=root, manifest=manifest)
