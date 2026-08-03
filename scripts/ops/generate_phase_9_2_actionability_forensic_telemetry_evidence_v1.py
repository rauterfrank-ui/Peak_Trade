#!/usr/bin/env python3
"""Generate durable Phase 9.2 actionability forensic telemetry evidence (offline)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git_sha(repo: Path) -> str:
    out = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo),
        text=True,
    ).strip()
    return out


def main() -> int:
    repo = _repo_root()
    sys.path.insert(0, str(repo / "src"))
    sys.path.insert(0, str(repo))

    from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (  # noqa: E402
        EVIDENCE_DIRNAME,
    )
    from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.evidence_bundle_v1 import (  # noqa: E402
        materialize_actionability_evidence_bundle_v1,
        verify_manifest_v1,
    )
    from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.offline_replay_harness_v1 import (  # noqa: E402
        run_offline_actionability_campaign_v1,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=repo / "docs" / "evidence" / EVIDENCE_DIRNAME,
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=repo / ".runtime" / "phase_9_2_actionability_forensic_telemetry_offline",
    )
    args = parser.parse_args()

    repository_sha = _git_sha(repo)
    campaign = run_offline_actionability_campaign_v1(
        repository_sha=repository_sha,
        work_root=args.work_root,
    )
    materialized = materialize_actionability_evidence_bundle_v1(
        evidence_root=args.evidence_root,
        campaign=campaign,
    )
    rc = verify_manifest_v1(args.evidence_root)
    payload = {
        "repository_sha": repository_sha,
        "evidence_root": str(args.evidence_root),
        "manifest_verify_rc": rc,
        "verifier_ok": bool((campaign.get("verifier") or {}).get("ok")),
        "bottleneck": campaign.get("bottleneck"),
        "counters": campaign.get("counters"),
        "materialized": {
            "file_count": materialized.get("file_count"),
            "manifest_path": materialized.get("manifest_path"),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if rc == 0 and payload["verifier_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
