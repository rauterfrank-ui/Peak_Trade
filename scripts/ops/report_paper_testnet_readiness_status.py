"""Emit a read-only Paper/Testnet readiness status report.

This CLI is intentionally conservative: unless explicit evidence flags are
provided, the report remains BLOCKED. It does not read or mutate paper/testnet
artifacts, registries, out/ops data, execution state, or live state.

Optional ``--paper-runtime-evidence-review`` ingests a bounded scheduler
Paper-runtime **review or closeout** artifact only; it is necessary-but-not-
sufficient for Paper layer readiness and never authorizes Testnet or Live.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal

CONTRACT = "paper_testnet_readiness_status_v0"
PAPER_RUNTIME_EVIDENCE_SCHEMA = "peak_trade.paper_runtime_evidence_input.v0"

CLOSEOUT_VERDICTS_ACCEPTED = frozenset(
    {
        "7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS",
        "SIXTY_MIN_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS",
    }
)

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

DOES_NOT_AUTHORIZE = ["testnet", "live", "broker", "exchange", "order_submission"]

MISSING_REVIEW_EXIT = 2


def default_paper_runtime_evidence_v0() -> dict[str, Any]:
    return {
        "schema_version": PAPER_RUNTIME_EVIDENCE_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "contributes_to": "paper_evidence_only",
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def _parse_review_json(text: str) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("verdict") != "PASS":
        return None
    issues = data.get("issues")
    if issues != []:
        return None
    return "PASS"


def _parse_closeout_markdown(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("VERDICT="):
            continue
        verdict = line.split("=", 1)[1].strip()
        if verdict in CLOSEOUT_VERDICTS_ACCEPTED:
            return verdict
    return None


def load_paper_runtime_evidence_review(path: Path) -> str | None:
    """Return verdict string if accepted; otherwise None."""
    text = path.read_text(encoding="utf-8", errors="replace")

    verdict_json = _parse_review_json(text)
    if verdict_json is not None:
        return verdict_json

    verdict_md = _parse_closeout_markdown(text)
    if verdict_md is not None:
        return verdict_md

    return None


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
        # Explicit non-authorization for consumers that expect these keys.
        "live_authorized": False,
        "testnet_authorized": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit read-only Paper/Testnet readiness status (JSON or human summary)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON to stdout.",
    )
    parser.add_argument("--paper-evidence-present", action="store_true")
    parser.add_argument("--paper-robustness-present", action="store_true")
    parser.add_argument("--paper-stress-present", action="store_true")
    parser.add_argument("--testnet-evidence-present", action="store_true")
    parser.add_argument("--testnet-robustness-present", action="store_true")
    parser.add_argument("--testnet-stress-present", action="store_true")
    parser.add_argument("--external-review-decision-present", action="store_true")
    parser.add_argument(
        "--paper-runtime-evidence-review",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to `review_scheduler_paper_runtime_evidence.py` JSON "
            "(verdict PASS, empty issues) or Paper-runtime success closeout markdown."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    review_path = (
        args.paper_runtime_evidence_review.expanduser().resolve()
        if args.paper_runtime_evidence_review is not None
        else None
    )

    runtime_v0 = default_paper_runtime_evidence_v0()
    runtime_accepted = False
    runtime_verdict: str | None = None

    if review_path is not None:
        runtime_v0["record_present"] = True
        runtime_v0["record_path"] = str(review_path)
        if not review_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--paper-runtime-evidence-review not a file: {review_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        verdict = load_paper_runtime_evidence_review(review_path)
        if verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "paper runtime evidence file is not a valid review JSON (PASS, empty issues) "
                "or an accepted closeout markdown verdict line.",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        runtime_verdict = verdict
        runtime_accepted = True
        runtime_v0["verdict"] = verdict
        runtime_v0["accepted"] = True

    effective_paper_evidence = bool(args.paper_evidence_present) or runtime_accepted

    payload = build_status(
        paper_evidence_present=effective_paper_evidence,
        paper_robustness_present=args.paper_robustness_present,
        paper_stress_present=args.paper_stress_present,
        testnet_evidence_present=args.testnet_evidence_present,
        testnet_robustness_present=args.testnet_robustness_present,
        testnet_stress_present=args.testnet_stress_present,
        external_review_decision_present=args.external_review_decision_present,
    )
    payload["paper_runtime_evidence_v0"] = runtime_v0

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status={payload['status']}")
        print(f"paper_runtime_evidence_accepted={str(runtime_accepted).lower()}")
        print("testnet_authorized=false")
        print("live_authorized=false")
        if review_path is not None and runtime_verdict is not None:
            print(f"paper_runtime_evidence_verdict={runtime_verdict}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
