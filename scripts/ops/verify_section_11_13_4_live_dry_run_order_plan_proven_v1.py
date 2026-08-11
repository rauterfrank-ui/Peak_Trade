#!/usr/bin/env python3
"""Verify sealed §11.13.4 LIVE_DRY_RUN_ORDER_PLAN evidence root."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.verifier_v1 import (  # noqa: E402
    LiveDryRunOrderPlanVerifierError,
    verify_live_dry_run_order_plan_evidence_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.evidence_v1 import (  # noqa: E402
    LiveDryRunOrderPlanEvidenceError,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_live_dry_run_order_plan_evidence_v1(args.evidence_root)
    except (LiveDryRunOrderPlanVerifierError, LiveDryRunOrderPlanEvidenceError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
