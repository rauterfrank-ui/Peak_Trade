# src/research/new_listings/collectors/replay.py
"""
ReplayCollector – offline-first collector that reads JSON fixtures and emits RawEvents.

Reads from a directory of JSON files (e.g. out/research/new_listings/replay/*.json).
Each file is a list of event objects: {"source", "venue_type", "observed_at", "payload"}.
No network, no secrets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .base import CollectorContext, RawEvent


def _get_replay_config(cfg: Mapping[str, Any], default_dir: Path) -> dict[str, Any]:
    sources = cfg.get("sources") or {}
    replay_cfg = sources.get("replay") or {}
    dir_str = replay_cfg.get("dir")
    return {
        "dir": Path(dir_str) if dir_str else default_dir,
        "enabled": bool(replay_cfg.get("enabled", True)),
    }


class ReplayCollector:
    """Collector that reads JSON fixture files and yields RawEvents (offline)."""

    name = "replay"

    def __init__(self, config: Mapping[str, Any], replay_dir: Path | None = None) -> None:
        self._config = config
        default = replay_dir or Path("out/research/new_listings/replay")
        self._replay_config = _get_replay_config(config, default)

    def collect(self, ctx: CollectorContext) -> Sequence[RawEvent]:
        if not self._replay_config["enabled"]:
            return []
        dir_path = self._replay_config["dir"]
        if not dir_path.is_dir():
            return []

        events: list[RawEvent] = []
        for path in sorted(dir_path.glob("*.json")):
            try:
                raw = path.read_text(encoding="utf-8")
                data = json.loads(raw)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, list):
                continue
            for item in data:
                if not isinstance(item, dict):
                    continue
                source = item.get("source") or self.name
                venue_type = item.get("venue_type") or "replay"
                observed_at = item.get("observed_at") or ""
                payload = item.get("payload")
                if payload is None:
                    payload = dict(item)
                    payload.pop("source", None)
                    payload.pop("venue_type", None)
                    payload.pop("observed_at", None)
                if not isinstance(payload, dict):
                    payload = {"raw": payload}
                events.append(
                    RawEvent(
                        source=str(source),
                        venue_type=str(venue_type),
                        observed_at=str(observed_at),
                        payload=payload,
                    )
                )
        return events


__all__ = ["ReplayCollector", "_get_replay_config"]
