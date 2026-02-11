from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "p5a.trade_plan_advisory.v0"


@dataclass(frozen=True)
class TradePlanAdvisory:
    """
    Advisory-only trade plan (NO execution).
    Output of L3 integration step P5A.

    Keep versioned and deterministic. No secrets. No exchange side effects.
    """

    schema_version: str = SCHEMA_VERSION
    asof_utc: str = ""
    universe: Optional[List[str]] = None

    # High-level guidance (advisory)
    stance: str = "HOLD"  # e.g., HOLD / RISK_ON / RISK_OFF / NO_TRADE
    allocations: Optional[Dict[str, float]] = None  # symbol -> target weight (0..1)
    constraints: Optional[Dict[str, Any]] = None  # risk limits, max leverage, etc.
    rationale: Optional[List[str]] = None  # bullet reasons, stable ordering
    no_trade: bool = False
    no_trade_reasons: Optional[List[str]] = None

    # Evidence pointers (paths/hashes) — optional, filled by runner
    evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["universe"] is None:
            d["universe"] = []
        if d["allocations"] is None:
            d["allocations"] = {}
        if d["constraints"] is None:
            d["constraints"] = {}
        if d["rationale"] is None:
            d["rationale"] = []
        if d["no_trade_reasons"] is None:
            d["no_trade_reasons"] = []
        if d["evidence"] is None:
            d["evidence"] = {}
        d["rationale"] = sorted(set(str(x) for x in d["rationale"]))
        d["no_trade_reasons"] = sorted(set(str(x) for x in d["no_trade_reasons"]))
        return d
