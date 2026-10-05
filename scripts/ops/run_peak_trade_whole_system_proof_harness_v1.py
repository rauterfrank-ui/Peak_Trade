#!/usr/bin/env python3
"""Run Peak_Trade Whole-System Proof Harness V1 (AUTHORITY=NONE)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ops.peak_trade_whole_system_proof_harness_v1.constants_v1 import (  # noqa: E402
    DEFAULT_OPERATION_SPEC_REL,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.harness_v1 import (  # noqa: E402
    run_whole_system_proof_harness_v1,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Whole-System Proof Harness V1")
    parser.add_argument(
        "--operation-spec",
        default=DEFAULT_OPERATION_SPEC_REL,
        help="Relative path to operation JSON spec",
    )
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="Skip writing evidence/ research artifacts",
    )
    args = parser.parse_args()
    out = run_whole_system_proof_harness_v1(
        REPO_ROOT,
        operation_spec_rel=args.operation_spec,
        write_evidence=not args.no_evidence,
    )
    if out.get("BLOCKED"):
        print(f"BLOCKED: {out.get('REASON')}")
        return 2
    r = out.get("readiness", {})
    print(f"WHOLE_SYSTEM_PROOF_HARNESS_READY={r.get('WHOLE_SYSTEM_PROOF_HARNESS_READY')}")
    print(f"CURRENT_READY={r.get('CURRENT_READY')}")
    if out.get("evidence_dir"):
        print(f"EVIDENCE_DIR={out['evidence_dir']}")
    return 0 if r.get("WHOLE_SYSTEM_PROOF_HARNESS_READY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
