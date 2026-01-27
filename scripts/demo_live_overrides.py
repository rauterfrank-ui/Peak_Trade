#!/usr/bin/env python3
"""
Demo / Debug tool for live overrides config layering.

Shows the effective config values before/after applying:
  config/live_overrides/auto.toml
via `load_config_with_live_overrides()`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.peak_config import (
    AUTO_LIVE_OVERRIDES_PATH,
    PeakConfig,
    _load_live_auto_overrides,
    load_config,
    load_config_with_live_overrides,
)


def _format(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.6g}"
    return repr(v)


def _parse_keys(keys: Optional[str]) -> Optional[List[str]]:
    if not keys:
        return None
    parts = [p.strip() for p in keys.split(",")]
    return [p for p in parts if p]


def _diff_keys(base: PeakConfig, eff: PeakConfig, keys: List[str]) -> List[str]:
    lines: List[str] = []
    for k in keys:
        before = base.get(k, "<missing>")
        after = eff.get(k, "<missing>")
        marker = "CHANGED" if before != after else "same"
        lines.append(f"- {k}: {marker}  { _format(before) } -> { _format(after) }")
    return lines


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Demo live overrides config layering.")
    p.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.toml"),
        help="Base config path (TOML).",
    )
    p.add_argument(
        "--overrides",
        type=Path,
        default=AUTO_LIVE_OVERRIDES_PATH,
        help="Overrides TOML path (default: config/live_overrides/auto.toml).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Force-apply overrides even in non-live environments (tests/debug only).",
    )
    p.add_argument(
        "--keys",
        type=str,
        default="",
        help="Comma-separated dotted keys to show (defaults to keys found in overrides).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    base = load_config(args.config)
    eff = load_config_with_live_overrides(
        args.config,
        auto_overrides_path=args.overrides,
        force_apply_overrides=args.force,
    )

    overrides: Dict[str, Any] = _load_live_auto_overrides(args.overrides)
    keys = _parse_keys(args.keys) or sorted(overrides.keys())

    print("## Live Overrides Demo")
    print(f"- base config: {args.config}")
    print(f"- overrides:   {args.overrides}  ({len(overrides)} key(s) found)")
    print(f"- force:       {args.force}")
    print("")

    if not keys:
        print("No override keys found; nothing to diff.")
        return

    print("## Diff (by key)")
    for line in _diff_keys(base, eff, keys):
        print(line)


if __name__ == "__main__":
    main()
