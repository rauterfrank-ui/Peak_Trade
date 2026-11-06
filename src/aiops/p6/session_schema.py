from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


SCHEMA_VERSION = "p6.shadow_session.v0"


@dataclass(frozen=True)
class ShadowSessionSummary:
    schema_version: str = SCHEMA_VERSION
    run_id: str = ""
    asof_utc: str = ""
    scenario: str | None = None
    profile: str | None = None
    expected_decision: str | None = None
    expected_regime: str | None = None
    expected_fills: List[Any] | None = None
    expected_positions: Dict[str, float] | None = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    no_trade: bool = False
    notes: List[str] = field(default_factory=list)
    p7_outputs: Dict[str, Any] = field(default_factory=dict)
    p7_account_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for key in (
            "scenario",
            "profile",
            "expected_decision",
            "expected_regime",
            "expected_fills",
            "expected_positions",
        ):
            if d.get(key) is None:
                d.pop(key, None)
        d["notes"] = sorted(set([str(x) for x in d["notes"]]))
        return d
