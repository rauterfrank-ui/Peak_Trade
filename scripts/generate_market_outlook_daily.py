#!/usr/bin/env python3
"""Retired MarketSentinel v0 entrypoint; the producer was removed in PR #6579."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Retired MarketSentinel v0 entrypoint. No market outlook is generated.",
    )
    # Accept the original flags so existing invocations report retirement.
    parser.add_argument("--config-path")
    parser.add_argument("--out-dir")
    parser.add_argument("--data-dir")
    parser.add_argument("--skip-llm", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.parse_args(argv)
    print("MARKET_SENTINEL_V0_RETIRED: no market outlook was generated.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
