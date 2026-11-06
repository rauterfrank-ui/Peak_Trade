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

Optional ``--testnet-prerequisites-checker-report`` ingests JSON emitted by
``check_testnet_prerequisites_readonly.py`` only (read from disk). The reporter
never runs the checker, never validates credentials, and never authorizes
Testnet or Live from this input.

Optional ``--testnet-evidence-review``, ``--testnet-robustness-evidence-review``,
and ``--testnet-stress-evidence-review`` ingest Testnet-layer **review or
closeout** artifacts only; they clear modeled Testnet readiness flags without
authorizing execution.

Optional ``--external-operator-testnet-gate-record`` ingests a non-runtime
**external operator** gate record (Markdown or JSON). It records review-gate
context only and does not authorize Testnet execution, Live, or order paths.
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
TESTNET_EVIDENCE_SCHEMA = "peak_trade.testnet_evidence_input.v0"
TESTNET_ROBUSTNESS_EVIDENCE_SCHEMA = "peak_trade.testnet_robustness_evidence_input.v0"
TESTNET_STRESS_EVIDENCE_SCHEMA = "peak_trade.testnet_stress_evidence_input.v0"
TESTNET_PREREQUISITE_CHECKER_REPORT_SCHEMA = "peak_trade.testnet_prerequisite_checker_report.v0"
TESTNET_PREREQUISITES_READONLY_CHECKER_SCHEMA = "peak_trade.testnet_prerequisites_readonly.v0"
EXTERNAL_OPERATOR_TESTNET_GATE_RECORD_SCHEMA = "peak_trade.external_operator_testnet_gate_record.v0"
AUTHORIZATION_BOUNDARY_V0_SCHEMA = "peak_trade.authorization_boundary.v0"

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

TESTNET_EVIDENCE_CLOSEOUT_VERDICTS_ACCEPTED = frozenset({"TESTNET_EVIDENCE_PASS"})
TESTNET_ROBUSTNESS_EVIDENCE_CLOSEOUT_VERDICTS_ACCEPTED = frozenset(
    {"TESTNET_ROBUSTNESS_EVIDENCE_PASS"}
)
TESTNET_STRESS_EVIDENCE_CLOSEOUT_VERDICTS_ACCEPTED = frozenset({"TESTNET_STRESS_EVIDENCE_PASS"})

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
EXTERNAL_OPERATOR_GATE_DOES_NOT_AUTHORIZE = [
    "testnet_execution",
    "live",
    "broker",
    "exchange",
    "order_submission",
]

MISSING_REVIEW_EXIT = 2


def build_authorization_boundary_v0() -> dict[str, Any]:
    """Static contract: evidence inputs and readiness status never authorize execution."""
    return {
        "schema_version": AUTHORIZATION_BOUNDARY_V0_SCHEMA,
        "non_authorizing_evidence_inputs": True,
        "evidence_inputs_do_not_authorize": list(DOES_NOT_AUTHORIZE),
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_exchange_order_paths_authorized": False,
        "order_submission_authorized": False,
        "authorization_requires_external_operator_gate": True,
        "readiness_status_is_not_execution_authority": True,
    }


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


def default_testnet_prerequisite_checker_report_v0() -> dict[str, Any]:
    return {
        "schema_version": TESTNET_PREREQUISITE_CHECKER_REPORT_SCHEMA,
        "record_path": None,
        "record_present": False,
        "accepted": False,
        "checker_status": None,
        "missing_count": None,
        "required_count": None,
        "non_authorizing": True,
        "contributes_to": "testnet_prerequisite_checker_context_only",
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def default_testnet_evidence_v0() -> dict[str, Any]:
    return {
        "schema_version": TESTNET_EVIDENCE_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "contributes_to": "testnet_evidence_only",
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def default_testnet_robustness_evidence_v0() -> dict[str, Any]:
    return {
        "schema_version": TESTNET_ROBUSTNESS_EVIDENCE_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "contributes_to": "testnet_robustness_only",
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def default_testnet_stress_evidence_v0() -> dict[str, Any]:
    return {
        "schema_version": TESTNET_STRESS_EVIDENCE_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "contributes_to": "testnet_stress_only",
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def default_external_operator_testnet_gate_record_v0() -> dict[str, Any]:
    return {
        "schema_version": EXTERNAL_OPERATOR_TESTNET_GATE_RECORD_SCHEMA,
        "record_path": None,
        "record_present": False,
        "verdict": None,
        "accepted": False,
        "non_authorizing": True,
        "non_execution_authority": True,
        "contributes_to": "external_operator_testnet_review_gate_only",
        "does_not_authorize": list(EXTERNAL_OPERATOR_GATE_DOES_NOT_AUTHORIZE),
    }


EXTERNAL_OPERATOR_GATE_MD_VERDICT = "EXTERNAL_OPERATOR_TESTNET_GATE_REVIEW_PASS"


def _parse_external_operator_gate_markdown(text: str) -> str | None:
    required = {
        "VERDICT": EXTERNAL_OPERATOR_GATE_MD_VERDICT,
        "OPERATOR_APPROVES_TESTNET_REVIEW_GATE": "yes",
        "NON_EXECUTION_AUTHORITY": "true",
        "TESTNET_EXECUTION_AUTHORIZED": "false",
        "LIVE_AUTHORIZED": "false",
    }
    found: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if "=" not in line or line.startswith("#"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        found[key] = val
    for k, exp in required.items():
        if found.get(k) != exp:
            return None
    return EXTERNAL_OPERATOR_GATE_MD_VERDICT


def _parse_external_operator_gate_json_dict(data: dict[str, Any]) -> str | None:
    if data.get("schema_version") != EXTERNAL_OPERATOR_TESTNET_GATE_RECORD_SCHEMA:
        return None
    if data.get("verdict") != "PASS":
        return None
    issues = data.get("issues")
    if issues is not None and issues != []:
        return None
    if data.get("operator_approves_testnet_review_gate") is not True:
        return None
    if data.get("non_execution_authority") is not True:
        return None
    if data.get("testnet_execution_authorized") is not False:
        return None
    if data.get("live_authorized") is not False:
        return None
    if data.get("broker_exchange_order_paths_authorized") is True:
        return None
    if data.get("order_submission_authorized") is True:
        return None
    return "PASS"


def _parse_external_operator_gate_json_text(text: str) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return _parse_external_operator_gate_json_dict(data)


def load_external_operator_testnet_gate_record(path: Path) -> str | None:
    """Return verdict string if gate record is valid; otherwise None."""
    text = path.read_text(encoding="utf-8", errors="replace")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        vj = _parse_external_operator_gate_json_text(text)
        if vj is not None:
            return vj
        return None
    return _parse_external_operator_gate_markdown(text)


def _checker_boundary_v0_is_valid(boundary: Any) -> bool:
    if not isinstance(boundary, dict):
        return False
    return (
        boundary.get("non_authorizing") is True
        and boundary.get("testnet_authorized") is False
        and boundary.get("live_authorized") is False
        and boundary.get("broker_exchange_order_paths_authorized") is False
        and boundary.get("order_submission_authorized") is False
        and boundary.get("checker_does_not_connect_to_exchange") is True
        and boundary.get("checker_does_not_validate_credentials") is True
    )


def _parse_testnet_prerequisite_checker_report_json(text: str) -> dict[str, Any] | None:
    """Parse and validate read-only checker JSON; return summary fields or None."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("schema_version") != TESTNET_PREREQUISITES_READONLY_CHECKER_SCHEMA:
        return None
    if not _checker_boundary_v0_is_valid(data.get("checker_boundary_v0")):
        return None
    status = data.get("status")
    if status not in ("BLOCKED", "READY_FOR_OPERATOR_REVIEW"):
        return None
    missing = data.get("missing")
    if missing is not None and not isinstance(missing, list):
        return None
    req_raw = data.get("required_key_count")
    if not isinstance(req_raw, int) or req_raw < 0:
        return None
    miss_raw = data.get("missing_count")
    if not isinstance(miss_raw, int) or miss_raw < 0:
        return None
    return {
        "checker_status": status,
        "missing_count": miss_raw,
        "required_count": req_raw,
    }


def load_testnet_prerequisite_checker_report(path: Path) -> dict[str, Any] | None:
    """Return summary dict if file is valid checker JSON; otherwise None."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return _parse_testnet_prerequisite_checker_report_json(text)


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


def _parse_testnet_evidence_review_json(text: str) -> str | None:
    """Accept PASS JSON only when explicitly tagged as testnet evidence."""
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
        data.get("evidence_kind") == "testnet_evidence"
        or data.get("kind") == "testnet_evidence"
        or data.get("testnet_evidence") is True
    )
    if not explicit:
        return None
    return "PASS"


def _parse_testnet_evidence_closeout_markdown(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("VERDICT="):
            continue
        verdict = line.split("=", 1)[1].strip()
        if verdict in TESTNET_EVIDENCE_CLOSEOUT_VERDICTS_ACCEPTED:
            return verdict
    return None


def _parse_testnet_robustness_review_json(text: str) -> str | None:
    """Accept PASS JSON only when explicitly tagged as testnet robustness."""
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
        data.get("evidence_kind") == "testnet_robustness"
        or data.get("kind") == "testnet_robustness"
        or data.get("testnet_robustness_evidence") is True
    )
    if not explicit:
        return None
    return "PASS"


def _parse_testnet_robustness_closeout_markdown(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("VERDICT="):
            continue
        verdict = line.split("=", 1)[1].strip()
        if verdict in TESTNET_ROBUSTNESS_EVIDENCE_CLOSEOUT_VERDICTS_ACCEPTED:
            return verdict
    return None


def _parse_testnet_stress_review_json(text: str) -> str | None:
    """Accept PASS JSON only when explicitly tagged as testnet stress."""
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
        data.get("evidence_kind") == "testnet_stress"
        or data.get("kind") == "testnet_stress"
        or data.get("testnet_stress_evidence") is True
    )
    if not explicit:
        return None
    return "PASS"


def _parse_testnet_stress_closeout_markdown(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("VERDICT="):
            continue
        verdict = line.split("=", 1)[1].strip()
        if verdict in TESTNET_STRESS_EVIDENCE_CLOSEOUT_VERDICTS_ACCEPTED:
            return verdict
    return None


def load_testnet_evidence_review(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    vj = _parse_testnet_evidence_review_json(text)
    if vj is not None:
        return vj
    vm = _parse_testnet_evidence_closeout_markdown(text)
    if vm is not None:
        return vm
    return None


def load_testnet_robustness_evidence_review(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    vj = _parse_testnet_robustness_review_json(text)
    if vj is not None:
        return vj
    vm = _parse_testnet_robustness_closeout_markdown(text)
    if vm is not None:
        return vm
    return None


def load_testnet_stress_evidence_review(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    vj = _parse_testnet_stress_review_json(text)
    if vj is not None:
        return vj
    vm = _parse_testnet_stress_closeout_markdown(text)
    if vm is not None:
        return vm
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
    parser.add_argument(
        "--testnet-prerequisites-checker-report",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to JSON emitted by check_testnet_prerequisites_readonly.py "
            f"({TESTNET_PREREQUISITES_READONLY_CHECKER_SCHEMA})."
        ),
    )
    parser.add_argument(
        "--testnet-evidence-review",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to JSON (verdict PASS, explicit testnet_evidence tag) "
            "or Testnet evidence success closeout markdown."
        ),
    )
    parser.add_argument(
        "--testnet-robustness-evidence-review",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to JSON (verdict PASS, explicit testnet_robustness tag) "
            "or Testnet robustness success closeout markdown."
        ),
    )
    parser.add_argument(
        "--testnet-stress-evidence-review",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to JSON (verdict PASS, explicit testnet_stress tag) "
            "or Testnet stress success closeout markdown."
        ),
    )
    parser.add_argument(
        "--external-operator-testnet-gate-record",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Optional path to external operator Testnet review gate record "
            f"(JSON {EXTERNAL_OPERATOR_TESTNET_GATE_RECORD_SCHEMA} or strict markdown)."
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
    checker_report_path = (
        args.testnet_prerequisites_checker_report.expanduser().resolve()
        if args.testnet_prerequisites_checker_report is not None
        else None
    )
    testnet_evidence_path = (
        args.testnet_evidence_review.expanduser().resolve()
        if args.testnet_evidence_review is not None
        else None
    )
    testnet_robustness_evidence_path = (
        args.testnet_robustness_evidence_review.expanduser().resolve()
        if args.testnet_robustness_evidence_review is not None
        else None
    )
    testnet_stress_evidence_path = (
        args.testnet_stress_evidence_review.expanduser().resolve()
        if args.testnet_stress_evidence_review is not None
        else None
    )
    external_operator_gate_path = (
        args.external_operator_testnet_gate_record.expanduser().resolve()
        if args.external_operator_testnet_gate_record is not None
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

    checker_report_v0 = default_testnet_prerequisite_checker_report_v0()
    checker_report_accepted = False
    checker_summary: dict[str, Any] | None = None

    if checker_report_path is not None:
        checker_report_v0["record_present"] = True
        checker_report_v0["record_path"] = str(checker_report_path)
        if not checker_report_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--testnet-prerequisites-checker-report not a file: {checker_report_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        checker_summary = load_testnet_prerequisite_checker_report(checker_report_path)
        if checker_summary is None:
            print(
                "report_paper_testnet_readiness_status: "
                "testnet prerequisites checker report is not valid read-only checker JSON "
                f"({TESTNET_PREREQUISITES_READONLY_CHECKER_SCHEMA}, checker_boundary_v0).",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        checker_report_accepted = True
        checker_report_v0["accepted"] = True
        checker_report_v0["checker_status"] = checker_summary["checker_status"]
        checker_report_v0["missing_count"] = checker_summary["missing_count"]
        checker_report_v0["required_count"] = checker_summary["required_count"]

    testnet_evidence_v0 = default_testnet_evidence_v0()
    testnet_evidence_accepted = False
    testnet_evidence_verdict: str | None = None

    if testnet_evidence_path is not None:
        testnet_evidence_v0["record_present"] = True
        testnet_evidence_v0["record_path"] = str(testnet_evidence_path)
        if not testnet_evidence_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--testnet-evidence-review not a file: {testnet_evidence_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        te_verdict = load_testnet_evidence_review(testnet_evidence_path)
        if te_verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "testnet evidence file is not a valid review JSON "
                "(verdict PASS, explicit testnet_evidence marker, optional empty issues) "
                "or an accepted closeout markdown verdict line.",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        testnet_evidence_verdict = te_verdict
        testnet_evidence_accepted = True
        testnet_evidence_v0["verdict"] = te_verdict
        testnet_evidence_v0["accepted"] = True

    testnet_robustness_evidence_v0 = default_testnet_robustness_evidence_v0()
    testnet_robustness_evidence_accepted = False
    testnet_robustness_evidence_verdict: str | None = None

    if testnet_robustness_evidence_path is not None:
        testnet_robustness_evidence_v0["record_present"] = True
        testnet_robustness_evidence_v0["record_path"] = str(testnet_robustness_evidence_path)
        if not testnet_robustness_evidence_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--testnet-robustness-evidence-review not a file: "
                f"{testnet_robustness_evidence_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        tr_verdict = load_testnet_robustness_evidence_review(testnet_robustness_evidence_path)
        if tr_verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "testnet robustness evidence file is not a valid review JSON "
                "(verdict PASS, explicit testnet_robustness marker, optional empty issues) "
                "or an accepted closeout markdown verdict line.",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        testnet_robustness_evidence_verdict = tr_verdict
        testnet_robustness_evidence_accepted = True
        testnet_robustness_evidence_v0["verdict"] = tr_verdict
        testnet_robustness_evidence_v0["accepted"] = True

    testnet_stress_evidence_v0 = default_testnet_stress_evidence_v0()
    testnet_stress_evidence_accepted = False
    testnet_stress_evidence_verdict: str | None = None

    if testnet_stress_evidence_path is not None:
        testnet_stress_evidence_v0["record_present"] = True
        testnet_stress_evidence_v0["record_path"] = str(testnet_stress_evidence_path)
        if not testnet_stress_evidence_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--testnet-stress-evidence-review not a file: {testnet_stress_evidence_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        ts_verdict = load_testnet_stress_evidence_review(testnet_stress_evidence_path)
        if ts_verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "testnet stress evidence file is not a valid review JSON "
                "(verdict PASS, explicit testnet_stress marker, optional empty issues) "
                "or an accepted closeout markdown verdict line.",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        testnet_stress_evidence_verdict = ts_verdict
        testnet_stress_evidence_accepted = True
        testnet_stress_evidence_v0["verdict"] = ts_verdict
        testnet_stress_evidence_v0["accepted"] = True

    external_operator_gate_v0 = default_external_operator_testnet_gate_record_v0()
    external_operator_gate_accepted = False
    external_operator_gate_verdict: str | None = None

    if external_operator_gate_path is not None:
        external_operator_gate_v0["record_present"] = True
        external_operator_gate_v0["record_path"] = str(external_operator_gate_path)
        if not external_operator_gate_path.is_file():
            print(
                "report_paper_testnet_readiness_status: "
                f"--external-operator-testnet-gate-record not a file: "
                f"{external_operator_gate_path}",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        og_verdict = load_external_operator_testnet_gate_record(external_operator_gate_path)
        if og_verdict is None:
            print(
                "report_paper_testnet_readiness_status: "
                "external operator Testnet gate record is not valid strict markdown or JSON "
                f"({EXTERNAL_OPERATOR_TESTNET_GATE_RECORD_SCHEMA}).",
                file=sys.stderr,
            )
            return MISSING_REVIEW_EXIT
        external_operator_gate_verdict = og_verdict
        external_operator_gate_accepted = True
        external_operator_gate_v0["verdict"] = og_verdict
        external_operator_gate_v0["accepted"] = True

    effective_paper_evidence = bool(args.paper_evidence_present) or runtime_accepted
    effective_paper_robustness = bool(args.paper_robustness_present) or robustness_accepted
    effective_paper_stress = bool(args.paper_stress_present) or stress_accepted
    effective_testnet_evidence = bool(args.testnet_evidence_present) or testnet_evidence_accepted
    effective_testnet_robustness = (
        bool(args.testnet_robustness_present) or testnet_robustness_evidence_accepted
    )
    effective_testnet_stress = bool(args.testnet_stress_present) or testnet_stress_evidence_accepted

    payload = build_status(
        paper_evidence_present=effective_paper_evidence,
        paper_robustness_present=effective_paper_robustness,
        paper_stress_present=effective_paper_stress,
        testnet_evidence_present=effective_testnet_evidence,
        testnet_robustness_present=effective_testnet_robustness,
        testnet_stress_present=effective_testnet_stress,
        external_review_decision_present=args.external_review_decision_present,
    )
    payload["paper_runtime_evidence_v0"] = runtime_v0
    payload["paper_robustness_evidence_v0"] = robustness_v0
    payload["paper_stress_evidence_v0"] = stress_v0
    payload["testnet_prerequisites_evidence_v0"] = testnet_prereq_v0
    payload["testnet_prerequisite_checker_report_v0"] = checker_report_v0
    payload["testnet_evidence_v0"] = testnet_evidence_v0
    payload["testnet_robustness_evidence_v0"] = testnet_robustness_evidence_v0
    payload["testnet_stress_evidence_v0"] = testnet_stress_evidence_v0
    payload["external_operator_testnet_gate_record_v0"] = external_operator_gate_v0
    payload["authorization_boundary_v0"] = build_authorization_boundary_v0()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status={payload['status']}")
        print(f"paper_runtime_evidence_accepted={str(runtime_accepted).lower()}")
        print(f"paper_robustness_evidence_accepted={str(robustness_accepted).lower()}")
        print(f"paper_stress_evidence_accepted={str(stress_accepted).lower()}")
        print(f"testnet_evidence_accepted={str(testnet_evidence_accepted).lower()}")
        print(
            "testnet_robustness_evidence_accepted="
            f"{str(testnet_robustness_evidence_accepted).lower()}"
        )
        print(f"testnet_stress_evidence_accepted={str(testnet_stress_evidence_accepted).lower()}")
        print(f"testnet_prerequisites_evidence_accepted={str(testnet_prereq_accepted).lower()}")
        print(
            f"testnet_prerequisite_checker_report_accepted={str(checker_report_accepted).lower()}"
        )
        print(
            "external_operator_testnet_gate_record_accepted="
            f"{str(external_operator_gate_accepted).lower()}"
        )
        print("testnet_authorized=false")
        print("live_authorized=false")
        if checker_report_accepted and checker_summary is not None:
            print(f"testnet_prerequisite_checker_status={checker_summary['checker_status']}")
            print(f"testnet_prerequisite_checker_missing_count={checker_summary['missing_count']}")
        if review_path is not None and runtime_verdict is not None:
            print(f"paper_runtime_evidence_verdict={runtime_verdict}")
        if robustness_path is not None and robustness_verdict is not None:
            print(f"paper_robustness_evidence_verdict={robustness_verdict}")
        if stress_path is not None and stress_verdict is not None:
            print(f"paper_stress_evidence_verdict={stress_verdict}")
        if testnet_evidence_path is not None and testnet_evidence_verdict is not None:
            print(f"testnet_evidence_verdict={testnet_evidence_verdict}")
        if (
            testnet_robustness_evidence_path is not None
            and testnet_robustness_evidence_verdict is not None
        ):
            print(f"testnet_robustness_evidence_verdict={testnet_robustness_evidence_verdict}")
        if testnet_stress_evidence_path is not None and testnet_stress_evidence_verdict is not None:
            print(f"testnet_stress_evidence_verdict={testnet_stress_evidence_verdict}")
        if testnet_prereq_path is not None and testnet_prereq_verdict is not None:
            print(f"testnet_prerequisites_evidence_verdict={testnet_prereq_verdict}")
        if external_operator_gate_path is not None and external_operator_gate_verdict is not None:
            print(f"external_operator_testnet_gate_record_verdict={external_operator_gate_verdict}")
        print(
            "external_operator_testnet_gate_non_execution_authority="
            f"{str(external_operator_gate_accepted).lower()}"
        )
        ab = payload["authorization_boundary_v0"]
        print(
            "authorization_boundary_non_authorizing_evidence_inputs="
            f"{str(ab['non_authorizing_evidence_inputs']).lower()}"
        )
        print(f"authorization_boundary_testnet_authorized={str(ab['testnet_authorized']).lower()}")
        print(
            "authorization_boundary_order_submission_authorized="
            f"{str(ab['order_submission_authorized']).lower()}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
