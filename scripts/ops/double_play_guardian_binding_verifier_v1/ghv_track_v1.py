"""Read-only Double Play GHV binding verifier. AUTHORITY=NONE."""

from __future__ import annotations

import ast
import re
from typing import Any, Mapping

SCHEMA_ID = "DOUBLE_PLAY_GHV_BINDING_VERIFIER_V1"
TOOL_IDENTITY = "DOUBLE_PLAY_GHV"
EXPECTED_BASELINE_SHA = "97c8c954204c15f9af5a48995b889ce3fb223c64"
EXPECTED_BASELINE_TREE = "898ede79de7e527db3632b8a3b32daf8b9b098b8"
INSPECTED_ENFORCEMENT_MODULE = (
    "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py"
)
HIERARCHY_OWNER = "OWNER > MASTER V2 > FULL AUTONOMOUS STACK"
HIERARCHY_DOUBLE_PLAY = "MASTER V2 > DOUBLE PLAY > DYNAMIC SCOPE"
OWNER_LOCK_MARK = "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3"
INTERNAL_AREA_MARK = "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA=true"
SEPARATE_UNIVERSE_MARK = "DOUBLE_PLAY_SEPARATE_UNIVERSE=false"
AUTHORITY_CONSTANT_NAMES = (
    "DOWNSTREAM_REDECISION_AUTHORITY",
    "LEARNING_TRADING_DECISION_AUTHORITY",
    "OPTIMIZATION_TRADING_DECISION_AUTHORITY",
    "META_LEARNING_TRADING_DECISION_AUTHORITY",
    "AUTONOMY_TRADING_DECISION_AUTHORITY",
    "EXECUTION_TRADING_DECISION_AUTHORITY",
)
FORBIDDEN_OUTPUT_KEYS = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized"}
)
_PROVENANCE_RE = re.compile(r"auf `([0-9a-f]{40})`")


def verify_double_play_ghv_v1(
    *,
    current_sha: str,
    current_tree: str,
    ghosv_contract_text: str | None,
    decision_path_text: str | None,
    hardening_source: str | None,
    ghosv_constants_source: str | None,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    claim_map = dict(claims or {})
    _reject_shared_claims(claim_map, reasons)
    if current_sha != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if current_tree != EXPECTED_BASELINE_TREE:
        reasons.append("BASELINE_TREE_MISMATCH")
    if _contains_forbidden_key(claim_map):
        reasons.append("OVERALL_PASS_FORBIDDEN")

    missing = (
        not ghosv_contract_text
        or not decision_path_text
        or not hardening_source
        or not ghosv_constants_source
    )
    if missing:
        reasons.append("MISSING_REQUIRED_EVIDENCE")

    contract = ghosv_contract_text or ""
    decision = decision_path_text or ""
    findings = [
        _hierarchy(contract, missing),
        _internal_role(decision, missing),
        _lock_tokens(contract, decision, missing),
        _authority(hardening_source, missing),
        _ghosv_pin(ghosv_constants_source, missing),
        _decision_provenance(decision, ghosv_constants_source, missing),
        _enforcement(hardening_source, missing),
    ]
    if any(row["RESULT"] == "UNKNOWN" for row in findings) and not missing:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    if _result(findings, "AUTHORITY_CONSTANTS") == "TOKEN_MISMATCH":
        reasons.append("AUTHORITY_DRIFT")
    if _result(findings, "LOCK_TOKEN") == "TOKEN_MISMATCH":
        reasons.append("LOCK_TOKEN_MISMATCH")
    if claim_map.get("treat_older_pin_as_current") is True:
        reasons.append("OLDER_PIN_TREATED_AS_CURRENT")
    if (
        claim_map.get("python_enforcement_claimed") is True
        and _result(findings, "PYTHON_LOCK_ENFORCEMENT") != "TOKEN_MATCH"
    ):
        reasons.append("UNSUPPORTED_ENFORCEMENT_CLAIM")

    report = _base_report(reasons, findings)
    _assert_no_forbidden_keys(report)
    return report


def _hierarchy(contract: str, missing: bool) -> dict[str, Any]:
    if missing or not contract:
        return _finding("HIERARCHY", "UNKNOWN")
    matched = HIERARCHY_OWNER in contract and HIERARCHY_DOUBLE_PLAY in contract
    return _finding("HIERARCHY", "TOKEN_MATCH" if matched else "TOKEN_MISMATCH")


def _internal_role(decision: str, missing: bool) -> dict[str, Any]:
    if missing or not decision:
        return _finding("INTERNAL_ROLE", "UNKNOWN")
    matched = INTERNAL_AREA_MARK in decision and SEPARATE_UNIVERSE_MARK in decision
    return _finding("INTERNAL_ROLE", "TOKEN_MATCH" if matched else "TOKEN_MISMATCH")


def _lock_tokens(contract: str, decision: str, missing: bool) -> dict[str, Any]:
    if missing or not contract or not decision:
        return _finding("LOCK_TOKEN", "UNKNOWN")
    matched = OWNER_LOCK_MARK in contract and OWNER_LOCK_MARK in decision
    return _finding("LOCK_TOKEN", "TOKEN_MATCH" if matched else "TOKEN_MISMATCH")


def _authority(source: str | None, missing: bool) -> dict[str, Any]:
    if missing or not source:
        return _finding("AUTHORITY_CONSTANTS", "UNKNOWN")
    try:
        values = _assignments(source, set(AUTHORITY_CONSTANT_NAMES))
    except SyntaxError:
        return _finding("AUTHORITY_CONSTANTS", "UNKNOWN")
    if any(name not in values for name in AUTHORITY_CONSTANT_NAMES):
        return _finding("AUTHORITY_CONSTANTS", "UNKNOWN")
    matched = all(values[name] == "NONE" for name in AUTHORITY_CONSTANT_NAMES)
    return _finding("AUTHORITY_CONSTANTS", "TOKEN_MATCH" if matched else "TOKEN_MISMATCH")


def _ghosv_pin(source: str | None, missing: bool) -> dict[str, Any]:
    if missing or not source:
        return _finding("GHOSV_CODE_PIN", "UNKNOWN")
    try:
        values = _assignments(source, {"CURRENT_CODE_PIN"})
    except SyntaxError:
        return _finding("GHOSV_CODE_PIN", "UNKNOWN")
    pin = values.get("CURRENT_CODE_PIN")
    if not isinstance(pin, str):
        return _finding("GHOSV_CODE_PIN", "UNKNOWN")
    result = "TOKEN_MATCH" if pin == EXPECTED_BASELINE_SHA else "PIN_DRIFT"
    return _finding("GHOSV_CODE_PIN", result, observed=pin, baseline=EXPECTED_BASELINE_SHA)


def _decision_provenance(decision: str, source: str | None, missing: bool) -> dict[str, Any]:
    if missing or not decision or not source:
        return _finding("DECISION_PATH_PROVENANCE", "UNKNOWN")
    match = _PROVENANCE_RE.search(decision)
    try:
        values = _assignments(source, {"CONTRACT_DOCUMENT_PROVENANCE"})
    except SyntaxError:
        return _finding("DECISION_PATH_PROVENANCE", "UNKNOWN")
    constant = values.get("CONTRACT_DOCUMENT_PROVENANCE")
    prose = match.group(1) if match else None
    if not isinstance(constant, str) or prose is None:
        return _finding("DECISION_PATH_PROVENANCE", "UNKNOWN")
    if constant != prose:
        return _finding(
            "DECISION_PATH_PROVENANCE",
            "TOKEN_MISMATCH",
            observed=constant,
            baseline=EXPECTED_BASELINE_SHA,
        )
    result = "TOKEN_MATCH" if constant == EXPECTED_BASELINE_SHA else "PIN_DRIFT"
    return _finding(
        "DECISION_PATH_PROVENANCE",
        result,
        observed=constant,
        baseline=EXPECTED_BASELINE_SHA,
    )


def _enforcement(source: str | None, missing: bool) -> dict[str, Any]:
    scope = {
        "ENFORCEMENT_SCOPE": INSPECTED_ENFORCEMENT_MODULE,
        "REPOSITORY_WIDE_ENFORCEMENT": "NOT_ASSESSED",
    }
    if missing or not source:
        return _finding("PYTHON_LOCK_ENFORCEMENT", "UNKNOWN", extra=scope)
    try:
        values = _assignments(source, {"DOUBLE_PLAY_FULL_OWNER_LOCK"})
    except SyntaxError:
        return _finding("PYTHON_LOCK_ENFORCEMENT", "UNKNOWN", extra=scope)
    if "DOUBLE_PLAY_FULL_OWNER_LOCK" not in values:
        return _finding("PYTHON_LOCK_ENFORCEMENT", "ENFORCEMENT_ABSENT", extra=scope)
    if values["DOUBLE_PLAY_FULL_OWNER_LOCK"] == "LEVEL_3":
        return _finding("PYTHON_LOCK_ENFORCEMENT", "TOKEN_MATCH", extra=scope)
    return _finding("PYTHON_LOCK_ENFORCEMENT", "TOKEN_MISMATCH", extra=scope)


def _assignments(source: str, names: set[str]) -> dict[str, Any]:
    parsed = ast.parse(source)
    found: dict[str, Any] = {}
    for node in parsed.body:
        target, value = _assignment(node)
        if target in names and value is not None:
            found[target] = ast.literal_eval(value)
    return found


def _assignment(node: ast.stmt) -> tuple[str | None, ast.expr | None]:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id, node.value
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0].id, node.value
    return None, None


def _finding(
    check: str,
    result: str,
    *,
    observed: str | None = None,
    baseline: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"CHECK": check, "RESULT": result}
    if observed is not None:
        row["OBSERVED"] = observed
    if baseline is not None:
        row["BASELINE"] = baseline
    if extra:
        row.update(extra)
    return row


def _result(findings: list[dict[str, Any]], check: str) -> str:
    for row in findings:
        if row["CHECK"] == check:
            return str(row["RESULT"])
    return "UNKNOWN"


def _reject_shared_claims(claims: Mapping[str, Any], reasons: list[str]) -> None:
    if any(claims.get(name) not in (None, "NONE") for name in ("authority", "trading_authority")):
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")
    if claims.get("dynamic_scope_separate_universe") is True:
        reasons.append("UNAUTHORIZED_UNIVERSE_CLAIM")


def _contains_forbidden_key(payload: object) -> bool:
    if isinstance(payload, dict):
        return any(
            key in FORBIDDEN_OUTPUT_KEYS or _contains_forbidden_key(value)
            for key, value in payload.items()
        )
    if isinstance(payload, list):
        return any(_contains_forbidden_key(item) for item in payload)
    return False


def _base_report(reasons: list[str], findings: list[dict[str, Any]]) -> dict[str, Any]:
    unique = tuple(dict.fromkeys(reasons))
    return {
        "SCHEMA_ID": SCHEMA_ID,
        "TOOL_IDENTITY": TOOL_IDENTITY,
        "AUTHORITY": "NONE",
        "TRADING_AUTHORITY": "NONE",
        "SAFETY_AUTHORITY": "NONE",
        "EXECUTION_AUTHORITY": "NONE",
        "GHV_READY": False,
        "VERIFICATION_STATUS": "REJECTED" if unique else "REPORTED",
        "REJECTION_REASONS": list(unique),
        "FINDINGS": findings,
        "CONTRACT_TEXT_IS_EXECUTABLE_PROTECTION": False,
        "VERIFIER_EXECUTION_IS_OWNER_AUTHORIZATION": False,
        "REPOSITORY_WIDE_ENFORCEMENT": "NOT_ASSESSED",
    }


def _assert_no_forbidden_keys(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            _assert_no_forbidden_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_forbidden_keys(item)
