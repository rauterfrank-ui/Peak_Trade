#!/usr/bin/env python3
"""Retired entrypoint. The historical CSV risk-check entrypoint was removed."""

import argparse
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_known_args(argv)
    print(
        "CHECK_LIVE_RISK_LIMITS_RETIRED: requires the removed src.notifications runtime.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
