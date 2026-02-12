from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "p4c.capsule.v0"


@dataclass(frozen=True)
class P4CCapsule:
    """
    Minimal input capsule for L2 Market Outlook (P4C).

    Keep this tiny and versioned. Extend only via additive fields + defaults.
    """

    schema_version: str = SCHEMA_VERSION

    # Example inputs (to be aligned with runbook P4C_SECTION):
    asof_utc: str = ""  # ISO8601 Z
    universe: Optional[List[str]] = None  # tickers/symbols
    features: Optional[Dict[str, Any]] = None  # normalized features snapshot
    context: Optional[Dict[str, Any]] = None  # optional metadata (env, pipeline stage, etc.)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Normalize Nones
        if d["universe"] is None:
            d["universe"] = []
        if d["features"] is None:
            d["features"] = {}
        if d["context"] is None:
            d["context"] = {}
        return d
