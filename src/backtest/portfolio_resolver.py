"""
Portfolio config resolution (single source of truth).

This module provides a shared resolver for:
- CLI (`scripts/run_registry_portfolio_backtest.py`)
- Engine (`src/backtest/engine.py`)

It supports optional TOML profile subtables:
  [portfolio]               # base
  [portfolio.aggressive]    # profile overrides
  [portfolio.aggressive.weights]  # nested dict overrides (merged)
"""

from typing import Any, Dict, Mapping


def resolve_portfolio_cfg(cfg: Mapping[str, Any], portfolio_name: str) -> Dict[str, Any]:
    """
    Return effective portfolio config (base + optional profile).

    Behavior:
    - If no profile exists for `portfolio_name`, returns a shallow copy of `[portfolio]`.
    - If profile exists (`[portfolio.<name>]`), returns base + profile merged:
      - shallow merge for top-level keys
      - dict-merge for nested dicts (e.g., `weights`)
    """
    portfolio_all = cfg.get("portfolio", {}) or {}
    if not isinstance(portfolio_all, dict):
        return {}

    profile = portfolio_all.get(portfolio_name)
    if not (portfolio_name and isinstance(profile, dict)):
        return dict(portfolio_all)

    merged: Dict[str, Any] = dict(portfolio_all)
    for k, v in profile.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v

    return merged
