"""
Extract reconciliation snapshots from SafetyGuard / pipeline ``context`` (Runbook-B).

Callers attach optional pre/post state under ``context["recon"]`` when
``PEAK_RECON_ENABLED=1`` so ``run_recon_if_enabled`` compares real expected vs observed
instead of placeholder null snapshots.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.ops.recon.models import BalanceSnapshot, PositionSnapshot


def _parse_balance(obj: Any) -> Optional[BalanceSnapshot]:
    if obj is None:
        return None
    if isinstance(obj, BalanceSnapshot):
        return obj
    if isinstance(obj, dict):
        epoch = int(obj.get("epoch", 0))
        balances = obj.get("balances")
        if balances is None or not isinstance(balances, dict):
            return None
        return BalanceSnapshot(
            epoch=epoch, balances={str(k): float(v) for k, v in balances.items()}
        )
    return None


def _parse_position(obj: Any) -> Optional[PositionSnapshot]:
    if obj is None:
        return None
    if isinstance(obj, PositionSnapshot):
        return obj
    if isinstance(obj, dict):
        epoch = int(obj.get("epoch", 0))
        positions = obj.get("positions")
        if positions is None or not isinstance(positions, dict):
            return None
        return PositionSnapshot(
            epoch=epoch, positions={str(k): float(v) for k, v in positions.items()}
        )
    return None


def recon_snapshots_from_context(
    context: Optional[Dict[str, Any]],
) -> Tuple[
    Optional[BalanceSnapshot],
    Optional[BalanceSnapshot],
    Optional[PositionSnapshot],
    Optional[PositionSnapshot],
]:
    """
    Read optional snapshots from ``context["recon"]``.

    Supported keys:

    - ``expected_balances``, ``observed_balances``: ``BalanceSnapshot`` or
      ``{"epoch": int, "balances": {asset: float}}``
    - ``expected_positions``, ``observed_positions``: ``PositionSnapshot`` or
      ``{"epoch": int, "positions": {symbol: float}}``

    Missing or invalid entries yield ``None`` for that slot; ``run_recon_if_enabled``
    then falls back to the configured ``ReconProvider`` (typically empty null snapshots).
    """
    if not context or not isinstance(context, dict):
        return (None, None, None, None)
    block = context.get("recon")
    if not isinstance(block, dict):
        return (None, None, None, None)
    return (
        _parse_balance(block.get("expected_balances")),
        _parse_balance(block.get("observed_balances")),
        _parse_position(block.get("expected_positions")),
        _parse_position(block.get("observed_positions")),
    )


def normalize_pipeline_context_for_recon(
    context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Shallow copy of ``context`` for SafetyGuard / risk with Runbook-B recon wiring.

    If ``recon`` is absent and ``recon_pipeline`` is a dict, set ``recon`` to that
    value so callers can attach pipeline-level snapshots without colliding with an
    explicit ``recon`` key.
    """
    if not context or not isinstance(context, dict):
        return {}
    out = dict(context)
    if "recon" not in out and isinstance(out.get("recon_pipeline"), dict):
        out["recon"] = out["recon_pipeline"]
    return out
