#!/usr/bin/env python3
"""Retired entrypoint. The historical CSV order, portfolio and health CLI was removed."""

import argparse
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_known_args(argv)
    print(
        "LIVE_OPS_RETIRED: requires the removed src.notifications and src.forward runtime.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
