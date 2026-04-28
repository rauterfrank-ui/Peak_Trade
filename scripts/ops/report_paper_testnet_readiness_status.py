"""Emit a read-only Paper/Testnet readiness status report.

This CLI is intentionally conservative: unless explicit evidence flags are
provided, the report remains BLOCKED. It does not read or mutate paper/testnet
artifacts, registries, out/ops data, execution state, or live state.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Literal


CONTRACT = "paper_testnet_readiness_status_v0"

Status = Literal["BLOCKED", "READY_FOR_REVIEW", "REVIEW_ONLY"]

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


def build_status(
    *,
    paper_evidence_present: bool,
    paper_robustness_present: bool,
    paper_stress_present: bool,
    testnet_evidence_present: bool,
    testnet_robustness_present: bool,
    testnet_stress_present: bool,
    external_review_decision_present: bool,
) -> dict[str, Any]:
    blockers: list[str] = []
    missing_or_open_items: list[str] = []

    if not paper_evidence_present:
        blockers.append("paper.evidence_missing")
        missing_or_open_items.append("paper.evidence_missing")
    if not paper_robustness_present:
        blockers.append("paper.robustness_missing")
        missing_or_open_items.append("paper.robustness_missing")
    if not paper_stress_present:
        blockers.append("paper.stress_missing")
        missing_or_open_items.append("paper.stress_missing")

    if not testnet_evidence_present:
        blockers.append("testnet.evidence_missing")
        missing_or_open_items.append("testnet.evidence_missing")
    if not testnet_robustness_present:
        blockers.append("testnet.robustness_missing")
        missing_or_open_items.append("testnet.robustness_missing")
    if not testnet_stress_present:
        blockers.append("testnet.stress_missing")
        missing_or_open_items.append("testnet.stress_missing")

    if blockers:
        status: Status = "BLOCKED"
    elif not external_review_decision_present:
        status = "READY_FOR_REVIEW"
    else:
        status = "REVIEW_ONLY"

    return {
        "contract": CONTRACT,
        "non_authorizing": True,
        "status": status,
        "paper": {
            "evidence_present": paper_evidence_present,
            "robustness_present": paper_robustness_present,
            "stress_present": paper_stress_present,
        },
        "testnet": {
            "evidence_present": testnet_evidence_present,
            "robustness_present": testnet_robustness_present,
            "stress_present": testnet_stress_present,
        },
        "blockers": sorted(set(blockers)),
        "missing_or_open_items": sorted(set(missing_or_open_items)),
        "external_review_decision_present": external_review_decision_present,
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit read-only Paper/Testnet readiness status JSON."
    )
    parser.add_argument("--json", action="store_true", required=True, help="Emit JSON to stdout.")
    parser.add_argument("--paper-evidence-present", action="store_true")
    parser.add_argument("--paper-robustness-present", action="store_true")
    parser.add_argument("--paper-stress-present", action="store_true")
    parser.add_argument("--testnet-evidence-present", action="store_true")
    parser.add_argument("--testnet-robustness-present", action="store_true")
    parser.add_argument("--testnet-stress-present", action="store_true")
    parser.add_argument("--external-review-decision-present", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_status(
        paper_evidence_present=args.paper_evidence_present,
        paper_robustness_present=args.paper_robustness_present,
        paper_stress_present=args.paper_stress_present,
        testnet_evidence_present=args.testnet_evidence_present,
        testnet_robustness_present=args.testnet_robustness_present,
        testnet_stress_present=args.testnet_stress_present,
        external_review_decision_present=args.external_review_decision_present,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
