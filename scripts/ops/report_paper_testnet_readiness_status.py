"""Emit a read-only Paper/Testnet readiness status report.

This CLI is intentionally conservative: unless explicit evidence flags are
provided, the report remains BLOCKED. It does not read or mutate paper/testnet
artifacts, registries, out/ops data, execution state, or live state.

Optional ``--paper-runtime-evidence-review`` ingests a bounded scheduler
Paper-runtime **review or closeout** artifact only; it is necessary-but-not-
sufficient for Paper layer readiness and never authorizes Testnet or Live.

Optional ``--paper-robustness-evidence-review`` ingests a Paper robustness
**review or closeout** artifact only; it satisfies the robustness slice of
Paper readiness context and never authorizes Testnet or Live.

Optional ``--paper-stress-evidence-review`` ingests a Paper stress **review or
closeout** artifact only; it satisfies the stress slice of Paper readiness
context and never authorizes Testnet or Live.

Optional ``--testnet-prerequisites-review`` ingests a Testnet prerequisites
**review or inventory** artifact only; it records non-authorizing prerequisites
context and never enables Testnet or Live.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal

CONTRACT = "paper_testnet_readiness_status_v0"
PAPER_RUNTIME_EVIDENCE_SCHEMA = "peak_trade.paper_runtime_evidence_input.v0"
PAPER_ROBUSTNESS_EVIDENCE_SCHEMA = "peak_trade.paper_robustness_evidence_input.v0"
PAPER_STRESS_EVIDENCE_SCHEMA = "peak_trade.paper_stress_evidence_input.v0"
TESTNET_PREREQUISITES_EVIDENCE_SCHEMA = "peak_trade.testnet_prerequisites_evidence_input.v0"

CLOSEOUT_VERDICTS_ACCEPTED = frozenset(
    {
        "7200S_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS",
        "SIXTY_MIN_SCHEDULER_PAPER_RUNTIME_EVIDENCE_PASS",
    }
)

ROBUSTNESS_CLOSEOUT_VERDICTS_ACCEPTED = frozenset(
    {
        "PAPER_ROBUSTNESS_EVIDENCE_PASS",
        "ROBUSTNESS_EVIDENCE_PASS",
    }
)

STRESS_CLOSEOUT_VERDICTS_ACCEPTED = frozenset(
    {
        "PAPER_STRESS_EVIDENCE_PASS",
        "STRESS_EVIDENCE_PASS",
    }
)

TESTNET_PREREQUISITES_CLOSEOUT_VERDICTS_ACCEPTED = frozenset(
    {
        "TESTNET_PREREQUISITES_EVIDENCE_PASS",
        "TESTNET_PREREQUISITES_REVIEW_PASS",
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


def default_paper_robustness_evidence_v0() -> dict[str, Any]:
    return {
        "schema_version": PAPER_ROBUSTNESS_EVIDENCE_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "contributes_to": "paper_robustness_only",
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def default_paper_stress_evidence_v0() -> dict[str, Any]:
    return {
        "schema_version": PAPER_STRESS_EVIDENCE_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "contributes_to": "paper_stress_only",
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def default_testnet_prerequisites_evidence_v0() -> dict[str, Any]:
    return {
        "schema_version": TESTNET_PREREQUISITES_EVIDENCE_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "contributes_to": "testnet_prerequisites_only",
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


def _parse_robustness_review_json(text: str) -> str | None:
    """Accept PASS JSON only when explicitly tagged as paper robustness evidence."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("verdict") != "PASS":
        return None
    issues = data.get("issues")
    if issues is not None and issues != []:
        return None
    explicit = (
        data.get("evidence_kind") == "paper_robustness"
        or data.get("kind") == "paper_robustness"
        or data.get("paper_robustness_evidence") is True
    )
    if not explicit:
        return None
    return "PASS"


def _parse_robustness_closeout_markdown(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("VERDICT="):
            continue
        verdict = line.split("=", 1)[1].strip()
        if verdict in ROBUSTNESS_CLOSEOUT_VERDICTS_ACCEPTED:
            return verdict
    return None


def _parse_stress_review_json(text: str) -> str | None:
    """Accept PASS JSON only when explicitly tagged as paper stress evidence."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("verdict") != "PASS":
        return None
    issues = data.get("issues")
    if issues is not None and issues != []:
        return None
    explicit = (
        data.get("evidence_kind") == "paper_stress"
        or data.get("kind") == "paper_stress"
        or data.get("paper_stress_evidence") is True
    )
    if not explicit:
        return None
    return "PASS"


def _parse_stress_closeout_markdown(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("VERDICT="):
            continue
        verdict = line.split("=", 1)[1].strip()
        if verdict in STRESS_CLOSEOUT_VERDICTS_ACCEPTED:
            return verdict
    return None


def _parse_testnet_prerequisites_review_json(text: str) -> str | None:
    """Accept PASS JSON only when explicitly tagged as testnet prerequisites evidence."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("verdict") != "PASS":
        return None
    issues = data.get("issues")
    if issues is not None and issues != []:
        return None
    explicit = (
        data.get("evidence_kind") == "testnet_prerequisites"
        or data.get("kind") == "testnet_prerequisites"
        or data.get("testnet_prerequisites_evidence") is True
    )
    if not explicit:
        return None
    return "PASS"


def _parse_testnet_prerequisites_closeout_markdown(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("VERDICT="):
            continue
        verdict = line.split("=", 1)[1].strip()
        if verdict in TESTNET_PREREQUISITES_CLOSEOUT_VERDICTS_ACCEPTED:
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


def load_paper_robustness_evidence_review(path: Path) -> str | None:
    """Return verdict string if accepted; otherwise None."""
    text = path.read_text(encoding="utf-8", errors="replace")

    verdict_json = _parse_robustness_review_json(text)
    if verdict_json is not None:
        return verdict_json

    verdict_md = _parse_robustness_closeout_markdown(text)
    if verdict_md is not None:
        return verdict_md

    return None


def load_paper_stress_evidence_review(path: Path) -> str | None:
    """Return verdict string if accepted; otherwise None."""
    text = path.read_text(encoding="utf-8", errors="replace")

    verdict_json = _parse_stress_review_json(text)
    if verdict_json is not None:
        return verdict_json

    verdict_md = _parse_stress_closeout_markdown(text)
    if verdict_md is not None:
        return verdict_md

    return None


def load_testnet_prerequisites_review(path: Path) -> str | None:
    """Return verdict string if accepted; otherwise None."""
    text = path.read_text(encoding="utf-8", errors="replace")

    verdict_json = _parse_testnet_prerequisites_review_json(text)
    if verdict_json is not None:
        return verdict_json

    verdict_md = _parse_testnet_prerequisites_closeout_markdown(text)
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
    parser.add_argument(
        "--paper-robustness-evidence-review",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to JSON (verdict PASS, explicit paper_robustness tag) "
            "or Paper robustness success closeout markdown."
        ),
    )
    parser.add_argument(
        "--paper-stress-evidence-review",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to JSON (verdict PASS, explicit paper_stress tag) "
            "or Paper stress success closeout markdown."
        ),
    )
    parser.add_argument(
        "--testnet-prerequisites-review",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to JSON (verdict PASS, explicit testnet_prerequisites tag) "
            "or Testnet prerequisites success closeout markdown."
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
    robustness_path = (
        args.paper_robustness_evidence_review.expanduser().resolve()
        if args.paper_robustness_evidence_review is not None
        else None
    )
    stress_path = (
        args.paper_stress_evidence_review.expanduser().resolve()
        if args.paper_stress_evidence_review is not None
        else None
    )
    testnet_prereq_path = (
        args.testnet_prerequisites_review.expanduser().resolve()
        if args.testnet_prerequisites_review is not None
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

    robustness_v0 = default_paper_robustness_evidence_v0()
    robustness_accepted = False
    robustness_verdict: str | None = None

    if robustness_path is not None:
        robustness_v0["record_present"] = True
        robustness_v0["record_path"] = str(robustness_path)
        if not robustness_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--paper-robustness-evidence-review not a file: {robustness_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        rb_verdict = load_paper_robustness_evidence_review(robustness_path)
        if rb_verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "paper robustness evidence file is not a valid review JSON "
                "(verdict PASS, explicit paper_robustness marker, optional empty issues) "
                "or an accepted closeout markdown verdict line.",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        robustness_verdict = rb_verdict
        robustness_accepted = True
        robustness_v0["verdict"] = rb_verdict
        robustness_v0["accepted"] = True

    stress_v0 = default_paper_stress_evidence_v0()
    stress_accepted = False
    stress_verdict: str | None = None

    if stress_path is not None:
        stress_v0["record_present"] = True
        stress_v0["record_path"] = str(stress_path)
        if not stress_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--paper-stress-evidence-review not a file: {stress_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        st_verdict = load_paper_stress_evidence_review(stress_path)
        if st_verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "paper stress evidence file is not a valid review JSON "
                "(verdict PASS, explicit paper_stress marker, optional empty issues) "
                "or an accepted closeout markdown verdict line.",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        stress_verdict = st_verdict
        stress_accepted = True
        stress_v0["verdict"] = st_verdict
        stress_v0["accepted"] = True

    testnet_prereq_v0 = default_testnet_prerequisites_evidence_v0()
    testnet_prereq_accepted = False
    testnet_prereq_verdict: str | None = None

    if testnet_prereq_path is not None:
        testnet_prereq_v0["record_present"] = True
        testnet_prereq_v0["record_path"] = str(testnet_prereq_path)
        if not testnet_prereq_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--testnet-prerequisites-review not a file: {testnet_prereq_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        tp_verdict = load_testnet_prerequisites_review(testnet_prereq_path)
        if tp_verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "testnet prerequisites file is not a valid review JSON "
                "(verdict PASS, explicit testnet_prerequisites marker, optional empty issues) "
                "or an accepted closeout markdown verdict line.",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        testnet_prereq_verdict = tp_verdict
        testnet_prereq_accepted = True
        testnet_prereq_v0["verdict"] = tp_verdict
        testnet_prereq_v0["accepted"] = True

    effective_paper_evidence = bool(args.paper_evidence_present) or runtime_accepted
    effective_paper_robustness = bool(args.paper_robustness_present) or robustness_accepted
    effective_paper_stress = bool(args.paper_stress_present) or stress_accepted

    payload = build_status(
        paper_evidence_present=effective_paper_evidence,
        paper_robustness_present=effective_paper_robustness,
        paper_stress_present=effective_paper_stress,
        testnet_evidence_present=args.testnet_evidence_present,
        testnet_robustness_present=args.testnet_robustness_present,
        testnet_stress_present=args.testnet_stress_present,
        external_review_decision_present=args.external_review_decision_present,
    )
    payload["paper_runtime_evidence_v0"] = runtime_v0
    payload["paper_robustness_evidence_v0"] = robustness_v0
    payload["paper_stress_evidence_v0"] = stress_v0
    payload["testnet_prerequisites_evidence_v0"] = testnet_prereq_v0

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status={payload['status']}")
        print(f"paper_runtime_evidence_accepted={str(runtime_accepted).lower()}")
        print(f"paper_robustness_evidence_accepted={str(robustness_accepted).lower()}")
        print(f"paper_stress_evidence_accepted={str(stress_accepted).lower()}")
        print(f"testnet_prerequisites_evidence_accepted={str(testnet_prereq_accepted).lower()}")
        print("testnet_authorized=false")
        print("live_authorized=false")
        if review_path is not None and runtime_verdict is not None:
            print(f"paper_runtime_evidence_verdict={runtime_verdict}")
        if robustness_path is not None and robustness_verdict is not None:
            print(f"paper_robustness_evidence_verdict={robustness_verdict}")
        if stress_path is not None and stress_verdict is not None:
            print(f"paper_stress_evidence_verdict={stress_verdict}")
        if testnet_prereq_path is not None and testnet_prereq_verdict is not None:
            print(f"testnet_prerequisites_evidence_verdict={testnet_prereq_verdict}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
