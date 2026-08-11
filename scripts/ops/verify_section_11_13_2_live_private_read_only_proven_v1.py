#!/usr/bin/env python3
"""Verify §11.13.2 LIVE_PRIVATE_READ_ONLY evidence bundles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.ops.section_11_13_2_live_private_read_only_v1.verifier_v1 import (
    LivePrivateRoVerifierError,
    verify_live_private_read_only_evidence_v1,
    verify_or_raise_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify §11.13.2 evidence root")
    parser.add_argument("evidence_root", type=str)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.evidence_root)
    try:
        result = verify_live_private_read_only_evidence_v1(root)
    except LivePrivateRoVerifierError as exc:
        print(f"VERIFY_FAIL:{exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        print(f"MANIFEST_VERIFY_RC={result['MANIFEST_VERIFY_RC']}")
        print(f"LIVE_PRIVATE_READ_ONLY_PROVEN={result['LIVE_PRIVATE_READ_ONLY_PROVEN']}")
        print(f"LIVE_AUTHORIZED={result['LIVE_AUTHORIZED']}")
    return verify_or_raise_v1(root)


if __name__ == "__main__":
    raise SystemExit(main())
