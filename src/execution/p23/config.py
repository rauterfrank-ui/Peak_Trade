"""
P23 Execution Model Config Schema.

Config-driven defaults for fees, slippage, and stop behavior.
Deterministic: no randomness, same config → same behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class ExecutionModelP23Config:
    """
    P23 execution model configuration.

    Attributes:
        enabled: Whether P23 execution model is active.
        maker_bps: Maker fee in basis points.
        taker_bps: Taker fee in basis points.
        slippage_bps: Slippage in basis points.
        stop_market_enabled: Whether stop-market orders are supported.
    """

    enabled: bool = True
    maker_bps: int = 5
    taker_bps: int = 10
    slippage_bps: int = 5
    stop_market_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dict for serialization."""
        return {
            "enabled": self.enabled,
            "maker_bps": self.maker_bps,
            "taker_bps": self.taker_bps,
            "slippage_bps": self.slippage_bps,
            "stop_market_enabled": self.stop_market_enabled,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any] | None) -> ExecutionModelP23Config:
        """Build config from dict (e.g. YAML). Supports flat and nested structure."""
        if d is None:
            return cls()
        fees = d.get("fees") or {}
        slippage = d.get("slippage") or {}
        stops = d.get("stops") or {}
        return cls(
            enabled=d.get("enabled", True),
            maker_bps=int(fees.get("maker_bps", d.get("maker_bps", 5))),
            taker_bps=int(fees.get("taker_bps", d.get("taker_bps", 10))),
            slippage_bps=int(slippage.get("bps", d.get("slippage_bps", 5))),
            stop_market_enabled=bool(
                stops.get("stop_market_enabled", d.get("stop_market_enabled", True))
            ),
        )
