#!/usr/bin/env python3
"""CLI entrypoint: non-enforcing canonical volatility max-age research execution v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (  # noqa: E402
    run_max_age_parameter_research_execution_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Execute non-enforcing canonical volatility numeric max-age "
            "parameter research. Never selects or promotes a threshold."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Repository root (default: detected from script location)",
    )
    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=None,
        help="Optional path to research evidence ledger JSONL",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Optional output evidence root (defaults under docs/evidence/.../execution_id)",
    )
    parser.add_argument(
        "--repository-sha",
        type=str,
        default=None,
        help="Optional explicit repository SHA binding",
    )
    parser.add_argument(
        "--native-baseline-admission-json",
        type=Path,
        required=True,
        help="Path to D26 native baseline evidence JSON (required for D27 test-entry admission)",
    )
    parser.add_argument(
        "--proposal-review-json",
        type=Path,
        help="Read the original M9 ingress and its stored governance review before follow-up",
    )
    parser.add_argument(
        "--created-at-utc",
        help="Explicit UTC observation time for a proposal-review follow-up",
    )
    args = parser.parse_args(argv)

    native_baseline = json.loads(args.native_baseline_admission_json.read_text(encoding="utf-8"))
    if args.proposal_review_json is not None:
        from src.experiments.f1_m9_proposal_review_research_follow_up_v1 import (
            F1M9ProposalReviewResearchContextV1,
            run_f1_m9_proposal_review_research_follow_up_v1,
        )

        context_path = args.proposal_review_json.resolve()
        context = json.loads(context_path.read_bytes())
        result = run_f1_m9_proposal_review_research_follow_up_v1(
            context=F1M9ProposalReviewResearchContextV1(
                review_store=context_path.parent / context["review_store"],
                original_ingress=context["original_ingress"],
                review_policy_digest=context["review_policy_digest"],
                review_feedback_digest=context["review_feedback_digest"],
            ),
            repo_root=args.repo_root.resolve(),
            native_baseline_evidence_v1=native_baseline,
            ledger_path=None if args.ledger_path is None else args.ledger_path.resolve(),
            output_root=None if args.output_root is None else args.output_root.resolve(),
            repository_sha=args.repository_sha,
            created_at_utc=args.created_at_utc,
        )
        print(json.dumps(result, sort_keys=True, indent=2))
        research = result["research"]
        completed = result["action"] == "KEEP_ADMITTED_PROPOSAL" or (
            research is not None and research["status"] == "PASS"
        )
        return 0 if completed else 2
    if args.created_at_utc is not None:
        parser.error("--created-at-utc requires --proposal-review-json")
    result = run_max_age_parameter_research_execution_v1(
        repo_root=args.repo_root.resolve(),
        native_baseline_evidence_v1=native_baseline,
        ledger_path=None if args.ledger_path is None else args.ledger_path.resolve(),
        output_root=None if args.output_root is None else args.output_root.resolve(),
        repository_sha=args.repository_sha,
    )
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
