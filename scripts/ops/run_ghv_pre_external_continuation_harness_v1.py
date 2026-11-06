#!/usr/bin/env python3
"""Offline GHV PRE_EXTERNAL continuation harness from flight-recorder snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _main() -> int:
    parser = argparse.ArgumentParser(description="GHV PRE_EXTERNAL offline continuation harness")
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        required=True,
        help="Path to ghv_pre_external_continuation_snapshot_v1 directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for ghv_pre_external_causal_blocker_report_v1.json",
    )
    args = parser.parse_args()
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_continuation_harness_v1 import (
        run_ghv_pre_external_continuation_harness_v1,
    )

    out = args.output_dir or args.snapshot_root
    report = run_ghv_pre_external_continuation_harness_v1(
        snapshot_root=args.snapshot_root,
        output_dir=out,
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
