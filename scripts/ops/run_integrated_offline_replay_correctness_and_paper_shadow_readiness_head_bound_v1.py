#!/usr/bin/env python3
"""Run HEAD-bound integrated correctness proof and shadow-readiness adjudication."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.adjudication_v1 import (  # noqa: E402
    evaluate_integrated_paper_shadow_shadow_readiness_head_bound_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.economic_evidence_bundle_v1 import (  # noqa: E402
    produce_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.proof_v1 import (  # noqa: E402
    default_canonical_evidence_dir_for_head_v1,
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1,
    resolve_repository_head_sha_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HEAD-bound shadow readiness offline runner")
    parser.add_argument(
        "--produce-evidence",
        action="store_true",
        help="Write canonical evidence under evidence/ops/ (offline only).",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    head = resolve_repository_head_sha_v1(repo_root=_REPO_ROOT)
    correctness_dir = _REPO_ROOT / default_canonical_evidence_dir_for_head_v1(head_sha=head)
    bundle_dir = _REPO_ROOT / (
        f"evidence/ops/integrated_paper_shadow_economic_evidence_bundle_head_bound_v1/{head}"
    )

    proof_result = None
    bundle_result = None
    if args.produce_evidence:
        proof_result = produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
            repo_root=_REPO_ROOT,
            work_root=correctness_dir,
            expected_head_sha=head,
        )
        if not proof_result.ok:
            payload = {"ok": False, "stage": "correctness_proof", "blockers": proof_result.blockers}
            print(json.dumps(payload, sort_keys=True, indent=2))
            return 1
        bundle_result = produce_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
            repo_root=_REPO_ROOT,
            bundle_root=bundle_dir,
            correctness_evidence_root=correctness_dir,
        )
        if not bundle_result.verified:
            payload = {"ok": False, "stage": "economic_bundle", "blockers": bundle_result.blockers}
            print(json.dumps(payload, sort_keys=True, indent=2))
            return 1

    adjudication = evaluate_integrated_paper_shadow_shadow_readiness_head_bound_v1(
        repo_root=_REPO_ROOT,
    )
    payload = {
        "ok": adjudication.SHADOW_READINESS == "READY",
        "adjudication": adjudication.to_dict(),
        "repository_head_sha": head,
        "correctness_evidence_dir": str(correctness_dir.relative_to(_REPO_ROOT)),
        "economic_bundle_dir": str(bundle_dir.relative_to(_REPO_ROOT)),
    }
    if proof_result is not None:
        payload["proof"] = proof_result.to_dict()
    if bundle_result is not None:
        payload["bundle"] = bundle_result.to_dict()
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        for key, value in adjudication.to_dict().items():
            print(f"{key}={value}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
