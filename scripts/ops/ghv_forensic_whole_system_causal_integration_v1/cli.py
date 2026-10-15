#!/usr/bin/env python3
"""Offline CLI for WP2-A causal integration (AUTHORITY=NONE)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _ensure_repo_on_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def main() -> int:
    _ensure_repo_on_path()
    parser = argparse.ArgumentParser(description="GHV WP2-A offline causal integration")
    parser.add_argument("--wp1-output-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Default: /tmp/ghv_wp2a_integration_<utc>",
    )
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--stage-mapping", type=Path, default=None)
    parser.add_argument(
        "--runtime-context-json",
        type=Path,
        default=None,
        help="JSON with run_id, continuous_run_id, evidence_contract_id",
    )
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path(f"/tmp/ghv_wp2a_integration_{ts}")

    from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.integrate_v1 import (
        run_causal_integration_v1,
    )
    from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.load_wp1_v1 import (
        load_wp1_artifacts_v1,
    )
    from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.runtime_evidence_v1 import (
        RuntimeEvidenceRequestV1,
    )

    bundle, _ = load_wp1_artifacts_v1(wp1_output_dir=args.wp1_output_dir)
    runtime_req = None
    if args.evidence_root is not None:
        if args.stage_mapping is None or args.runtime_context_json is None:
            print(
                json.dumps(
                    {
                        "status": "FAIL",
                        "failure_semantic": "INPUT_VALIDATION_FAILURE",
                        "error": "evidence_requires_stage_mapping_and_runtime_context",
                    }
                )
            )
            return 2
        ctx = json.loads(args.runtime_context_json.read_text(encoding="utf-8"))
        code_rev = str(
            (bundle.composed.get("code_snapshot") or {}).get("git_head") if bundle else ""
        )
        runtime_req = RuntimeEvidenceRequestV1(
            evidence_root=args.evidence_root,
            stage_mapping_path=args.stage_mapping,
            runtime_context=ctx,
            code_revision=code_rev,
            snapshot_id=str(bundle.snapshot_id if bundle else ""),
        )

    result = run_causal_integration_v1(
        wp1_output_dir=args.wp1_output_dir,
        output_dir=output_dir,
        runtime_evidence=runtime_req,
    )
    print(
        json.dumps(
            {
                "status": "PASS" if result.ok else "FAIL",
                "failure_semantic": result.failure_semantic,
                "errors": result.errors,
                "output_dir": str(output_dir),
                "manifest": result.manifest,
            },
            sort_keys=True,
        )
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
