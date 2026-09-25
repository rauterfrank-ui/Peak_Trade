#!/usr/bin/env python3
"""
P5B — Evidence Pack Validator CLI

Validates manifest structure and verifies file SHA256 checksums.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.aiops.p5b.validate import EvidencePackValidationError, validate_pack


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to evidence pack manifest.json",
    )
    args = ap.parse_args()

    mp = Path(args.manifest).expanduser().resolve()
    if not mp.is_file():
        raise FileNotFoundError(mp)

    try:
        validate_pack(mp)
    except EvidencePackValidationError as e:
        print(f"VALIDATION_FAIL: {e}")
        return 2

    print("VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
