#!/usr/bin/env python3
"""Retired entrypoint. The historical CSV Paper entrypoint was removed. It is separate from the Paper pilot."""

import argparse
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_known_args(argv)
    print(
        "PAPER_TRADE_FROM_ORDERS_RETIRED: requires the removed src.notifications runtime.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
