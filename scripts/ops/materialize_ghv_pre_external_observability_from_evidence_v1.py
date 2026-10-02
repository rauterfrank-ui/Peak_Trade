#!/usr/bin/env python3
"""Offline PR7014/7015 observability materialization from captured Product evidence.

Does not invoke Product, network I/O, or trading authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_SNAPSHOT_DIR = "ghv_pre_external_continuation_snapshot_v1"
FLIGHT_RECORD = "ghv_pre_external_runtime_flight_record_v1.jsonl"


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize GHV whole-cycle + Canary artifacts from captured evidence"
    )
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        default=None,
        help="Continuation snapshot dir (default: <evidence-root>/ghv_pre_external_continuation_snapshot_v1)",
    )
    parser.add_argument(
        "--skip-continuation-harness",
        action="store_true",
        help="Only materialize flight-record-derived bundles (no compose/venue-plan replay)",
    )
    args = parser.parse_args()
    evidence_root = Path(args.evidence_root).resolve()
    if not (evidence_root / FLIGHT_RECORD).is_file():
        print(json.dumps({"status": "FAIL", "blocker": "MISSING_FLIGHT_RECORD"}))
        return 2

    snapshot_root = (
        Path(args.snapshot_root).resolve()
        if args.snapshot_root is not None
        else evidence_root / DEFAULT_SNAPSHOT_DIR
    )

    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_continuation_harness_v1 import (
        run_ghv_pre_external_continuation_harness_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_system_wide_canary_surface_discovery_v1 import (
        build_system_wide_canary_bundle_v1,
        persist_system_wide_canary_artifacts_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_whole_cycle_causal_observability_v1 import (
        build_whole_cycle_observability_v1,
        persist_whole_cycle_observability_artifacts_v1,
    )

    harness_report = None
    if not args.skip_continuation_harness:
        if not snapshot_root.is_dir():
            print(
                json.dumps(
                    {
                        "status": "FAIL",
                        "blocker": "MISSING_CONTINUATION_SNAPSHOT",
                        "snapshot_root": str(snapshot_root),
                    }
                )
            )
            return 2
        harness_report = run_ghv_pre_external_continuation_harness_v1(
            snapshot_root=snapshot_root,
            output_dir=evidence_root,
        )
        (evidence_root / "ghv_pre_external_offline_continuation_harness_report_v1.json").write_text(
            json.dumps(harness_report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        wc_only = build_whole_cycle_observability_v1(
            evidence_root=evidence_root,
            harness_report=None,
        )
        persist_whole_cycle_observability_artifacts_v1(
            evidence_root=evidence_root,
            bundle=wc_only,
        )
        canary_only = build_system_wide_canary_bundle_v1(
            evidence_root=evidence_root,
            harness_report=None,
        )
        persist_system_wide_canary_artifacts_v1(
            evidence_root=evidence_root,
            bundle=canary_only,
        )

    out = {
        "status": "PASS",
        "evidence_root": str(evidence_root),
        "snapshot_root": str(snapshot_root),
        "continuation_harness_executed": harness_report is not None,
        "evidence_domain": "OFFLINE_CONTINUATION"
        if harness_report
        else "FLIGHT_RECORD_DERIVED_ONLY",
        "ROOT_BLOCKERS": (harness_report or {}).get("ROOT_BLOCKERS", []),
    }
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
