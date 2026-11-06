"""P24 execution model v2 config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


PriceRule = Literal["worst", "mid", "close"]
TouchMode = Literal["touch", "through"]
RoundingMode = Literal["none", "floor", "ceil"]


@dataclass(frozen=True)
class PartialFillsV2Config:
    max_fill_ratio_per_bar: float = 1.0
    min_fill_qty: float = 0.0
    volume_cap_ratio: float = 1.0
    price_rule: PriceRule = "worst"
    touch_mode: TouchMode = "touch"
    rounding: RoundingMode = "none"
    qty_step: Optional[float] = None
    allow_partial_on_trigger_bar: bool = True

    def validate(self) -> None:
        if not (0.0 < self.max_fill_ratio_per_bar <= 1.0):
            raise ValueError("max_fill_ratio_per_bar must be in (0,1].")
        if self.min_fill_qty < 0.0:
            raise ValueError("min_fill_qty must be >= 0.")
        if not (0.0 < self.volume_cap_ratio <= 1.0):
            raise ValueError("volume_cap_ratio must be in (0,1].")
        if self.rounding != "none":
            if self.qty_step is None or self.qty_step <= 0:
                raise ValueError("qty_step must be > 0 when rounding != 'none'.")


@dataclass(frozen=True)
class ExecutionModelV2Config:
    fee_rate: float = 0.0
    slippage_bps: float = 0.0
    partial_fills_v2: PartialFillsV2Config = PartialFillsV2Config()

    @staticmethod
    def from_dict(d: dict) -> "ExecutionModelV2Config":
        pf = d.get("partial_fills_v2", {}) or {}
        pf_cfg = PartialFillsV2Config(
            max_fill_ratio_per_bar=float(pf.get("max_fill_ratio_per_bar", 1.0)),
            min_fill_qty=float(pf.get("min_fill_qty", 0.0)),
            volume_cap_ratio=float(pf.get("volume_cap_ratio", 1.0)),
            price_rule=pf.get("price_rule", "worst"),
            touch_mode=pf.get("touch_mode", "touch"),
            rounding=pf.get("rounding", "none"),
            qty_step=(None if pf.get("qty_step", None) is None else float(pf.get("qty_step"))),
            allow_partial_on_trigger_bar=bool(pf.get("allow_partial_on_trigger_bar", True)),
        )
        pf_cfg.validate()
        cfg = ExecutionModelV2Config(
            fee_rate=float(d.get("fee_rate", 0.0)),
            slippage_bps=float(d.get("slippage_bps", 0.0)),
            partial_fills_v2=pf_cfg,
        )
        if cfg.fee_rate < 0:
            raise ValueError("fee_rate must be >= 0.")
        if cfg.slippage_bps < 0:
            raise ValueError("slippage_bps must be >= 0.")
        return cfg
