# src/execution_simple/builder.py
"""
Execution Pipeline Builder - Config Integration.

Builds ExecutionPipeline from TOML config.
"""

from __future__ import annotations

from typing import Any

from .adapters import SimulatedBrokerAdapter
from .gates import LotSizeGate, MinNotionalGate, PriceSanityGate, ResearchOnlyGate
from .pipeline import ExecutionPipeline
from .types import ExecutionMode


def build_execution_pipeline_from_config(cfg: Any) -> ExecutionPipeline:
    """
    Build ExecutionPipeline from config.

    Expected config structure:

    [execution]
    mode = "paper"              # "backtest" | "paper" | "live"
    slippage_bps = 2.0          # only for simulated
    fee_bps = 0.0               # optional
    min_notional = 10.0
    lot_size = 0.0001
    min_qty = 0.0001

    [execution.gates]
    block_research_in_live = true

    Args:
        cfg: Config object with .get() method

    Returns:
        ExecutionPipeline instance

    Raises:
        ValueError: If config is invalid
    """
    # Get execution config with defaults
    mode_str = cfg.get("execution.mode", "paper")
    slippage_bps = float(cfg.get("execution.slippage_bps", 2.0))
    fee_bps = float(cfg.get("execution.fee_bps", 0.0))
    min_notional = float(cfg.get("execution.min_notional", 10.0))
    lot_size = float(cfg.get("execution.lot_size", 0.0001))
    min_qty = float(cfg.get("execution.min_qty", 0.0001))

    # Gate config
    block_research_in_live = bool(cfg.get("execution.gates.block_research_in_live", True))

    # Validate mode
    try:
        mode = ExecutionMode(mode_str)
    except ValueError:
        valid_modes = [m.value for m in ExecutionMode]
        raise ValueError(
            f"Invalid execution mode: '{mode_str}'. Must be one of: {', '.join(valid_modes)}"
        )

    # Build gates in order:
    # 1. PriceSanity - validate price first
    # 2. ResearchOnly - block research in LIVE
    # 3. LotSize - round quantity to lot size
    # 4. MinNotional - check minimum order size after rounding
    gates = [
        PriceSanityGate(),
        ResearchOnlyGate(block_research_in_live=block_research_in_live),
        LotSizeGate(lot_size=lot_size, min_qty=min_qty),
        MinNotionalGate(min_notional=min_notional),
    ]

    # Build adapter (only for paper/backtest)
    adapter = None
    if mode in (ExecutionMode.PAPER, ExecutionMode.BACKTEST):
        adapter = SimulatedBrokerAdapter(
            slippage_bps=slippage_bps,
            fee_bps=fee_bps,
        )

    # Build pipeline
    pipeline = ExecutionPipeline(gates=gates, adapter=adapter)

    return pipeline
