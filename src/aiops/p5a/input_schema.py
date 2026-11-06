from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


SCHEMA_VERSION = "p5a.input.v0"


@dataclass(frozen=True)
class P5AInput:
    schema_version: str = SCHEMA_VERSION
    asof_utc: str = ""
    universe: List[str] = None
    p4c_outlook: Dict[str, Any] = None
    risk: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["universe"] is None:
            d["universe"] = []
        if d["p4c_outlook"] is None:
            d["p4c_outlook"] = {}
        if d["risk"] is None:
            d["risk"] = {}
        return d


def validate_input(obj: Dict[str, Any]) -> None:
    if not isinstance(obj, dict):
        raise TypeError("input must be dict")
    sv = obj.get("schema_version", "")
    if sv != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}, got {sv!r}")
    if not isinstance(obj.get("universe", []), list):
        raise TypeError("universe must be list")
    if not isinstance(obj.get("p4c_outlook", {}), dict):
        raise TypeError("p4c_outlook must be dict")
    if not isinstance(obj.get("risk", {}), dict):
        raise TypeError("risk must be dict")
