"""Observe four catalog rows. AUTHORITY=NONE. Does not run the existing checker."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.double_play_ghosv_observation_adapter_v1.constants_v1 import (
    AUTHORITY,
    DECISION_PATH_RELATIVE,
    ENTRY_EXIT_SYMBOL,
    EXISTING_GHOSV_CODE_PIN,
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    FORBIDDEN_OUTPUT_KEYS,
    GHOSV_CONSTANTS_RELATIVE,
    GHOSV_CONTRACT_RELATIVE,
    INTERNAL_AREA_TOKEN,
    LOCK_TOKEN,
    NEGATIVE_CODES,
    PERSISTENCE_CONSTANTS_RELATIVE,
    REQUIREMENT_IDS,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SEPARATE_UNIVERSE_TOKEN,
    SHARED_MODULE_TOKEN,
)


@dataclass(frozen=True)
class ObservationRequestV1:
    separate_universe_claimed: bool = False
    decision_authority_claimed: bool = False
    replace_implies_persistence: bool = False
    lock_mutation_requested: bool = False
    tool_run_claimed_as_owner_go: bool = False
    effect_pass_requested: bool = False
    persists_claimed: bool = False
    writer_refutation_requested: bool = False
    authority: str = "NONE"


def observe_double_play_catalog_v1(
    *,
    repository_root: Path,
    current_sha: str,
    current_tree: str,
    request: ObservationRequestV1 | None = None,
) -> dict[str, Any]:
    ask = request or ObservationRequestV1()
    reasons: list[str] = []
    if current_sha != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if current_tree != EXPECTED_BASELINE_TREE:
        reasons.append("BASELINE_TREE_MISMATCH")
    if ask.authority != "NONE":
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")

    root = repository_root.resolve()
    contract = _read_inside(root, GHOSV_CONTRACT_RELATIVE)
    decision = _read_inside(root, DECISION_PATH_RELATIVE)
    constants = _constants(root)
    runtime_activated = _runtime_activated(root)
    if contract is None or decision is None or constants is None or runtime_activated is None:
        reasons.append("MISSING_REQUIRED_EVIDENCE")

    not_tested = _not_tested(constants)
    catalog_ready = contract is not None and _catalog_rows_present(contract)
    flags_ready = decision is not None and _role_flags(decision) and LOCK_TOKEN in decision
    pin = _pin(constants)
    if not_tested is None or not catalog_ready or not flags_ready or pin != EXISTING_GHOSV_CODE_PIN:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    if runtime_activated is False:
        binder_constant = False
    else:
        binder_constant = None
        reasons.append("MISSING_REQUIRED_EVIDENCE")

    findings = [
        _mv2_04(ask, contract, decision, reasons),
        _mv2_05(ask, decision, contract, reasons),
        _mv2_06(ask, contract, reasons),
        _mv2_08(ask, binder_constant, reasons),
    ]
    unique = tuple(dict.fromkeys(reasons))
    report: dict[str, Any] = {
        "SCHEMA_ID": SCHEMA_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "AUTHORITY": AUTHORITY,
        "TRADING_AUTHORITY": "NONE",
        "SAFETY_AUTHORITY": "NONE",
        "EXECUTION_AUTHORITY": "NONE",
        "BASELINE_SHA": EXPECTED_BASELINE_SHA,
        "BASELINE_TREE": EXPECTED_BASELINE_TREE,
        "PROJECTION_STATUS": "REJECTED" if unique else "OBSERVED",
        "REJECTION_REASONS": list(unique),
        "EXISTING_CHECKER_MUTATED": False,
        "EXISTING_GHOSV_CODE_PIN": pin,
        "GHOSV_PIN_IS_CURRENT_BASELINE": False,
        "POLICY_BODY_EXECUTED": False,
        "PERSISTENCE_BINDER_WRITTEN": False,
        "FINDINGS": findings,
    }
    _assert_no_forbidden_keys(report)
    return report


def _mv2_04(
    ask: ObservationRequestV1,
    contract: str | None,
    decision: str | None,
    reasons: list[str],
) -> dict[str, Any]:
    violation = (
        ask.separate_universe_claimed
        or ask.decision_authority_claimed
        or ask.replace_implies_persistence
    )
    if violation:
        reasons.append(NEGATIVE_CODES["MV2-04"])
    flags = bool(
        decision and contract and _role_flags(decision) and SHARED_MODULE_TOKEN in contract
    )
    if violation:
        observation = "VIOLATION"
    elif flags:
        observation = "INTERNAL_ROLE_FLAGS_OBSERVED"
    else:
        observation = "MISSING"
    return _finding(
        "MV2-04",
        observation=observation,
        evidence="NOT_PROVEN" if violation or not flags else "PARTIAL",
        reaction=NEGATIVE_CODES["MV2-04"] if violation else None,
        extra={
            "PERSISTENCE_INFERRED_FROM_REPLACE": False,
            "DECISION_AUTHORITY_GRANTED": False,
        },
    )


def _mv2_05(
    ask: ObservationRequestV1,
    decision: str | None,
    contract: str | None,
    reasons: list[str],
) -> dict[str, Any]:
    violation = ask.lock_mutation_requested or ask.tool_run_claimed_as_owner_go
    if violation:
        reasons.append(NEGATIVE_CODES["MV2-05"])
    lock_text = bool(decision and contract and LOCK_TOKEN in decision and LOCK_TOKEN in contract)
    if violation:
        observation = "VIOLATION"
    elif lock_text:
        observation = "LOCK_TEXT_OBSERVED"
    else:
        observation = "MISSING"
    return _finding(
        "MV2-05",
        observation=observation,
        evidence="NOT_PROVEN" if violation or not lock_text else "PARTIAL",
        reaction=NEGATIVE_CODES["MV2-05"] if violation else None,
        extra={
            "PYTHON_ENFORCEMENT": "NOT_CLAIMED",
            "TOOL_RUN_IS_OWNER_GO": False,
            "GATE_CREATED": False,
        },
    )


def _mv2_06(
    ask: ObservationRequestV1,
    contract: str | None,
    reasons: list[str],
) -> dict[str, Any]:
    if ask.effect_pass_requested:
        reasons.append("EFFECT_PASS_BLOCKED")
    symbol = bool(contract and ENTRY_EXIT_SYMBOL in contract)
    return _finding(
        "MV2-06",
        observation="EFFECT_BLOCKED",
        evidence="NOT_PROVEN",
        reaction=None,
        blocked=True,
        extra={
            "SYMBOL_MENTIONED_IN_CATALOG": symbol,
            "EFFECT_PASS": False,
            "POLICY_BODY_EXECUTED": False,
        },
    )


def _mv2_08(
    ask: ObservationRequestV1,
    binder_constant: bool | None,
    reasons: list[str],
) -> dict[str, Any]:
    if ask.persists_claimed:
        reasons.append(NEGATIVE_CODES["MV2-08"])
    if ask.writer_refutation_requested:
        reasons.append("WRITER_REFUTATION_BLOCKED")
    return _finding(
        "MV2-08",
        observation="WRITER_NOT_PROVEN",
        evidence="NOT_PROVEN",
        reaction=NEGATIVE_CODES["MV2-08"] if ask.persists_claimed else None,
        blocked=True,
        extra={
            "BINDER_RUNTIME_ACTIVATED": binder_constant,
            "PRODUCTIVE_WRITER_REFUTED": False,
            "WRITER_REFUTATION": "BLOCKED",
        },
    )


def _finding(
    requirement_id: str,
    *,
    observation: str,
    evidence: str,
    reaction: str | None,
    extra: dict[str, Any],
    blocked: bool = False,
) -> dict[str, Any]:
    row = {
        "REQUIREMENT_ID": requirement_id,
        "EXISTING_CHECKER_STATUS": "NOT_TESTED",
        "OBSERVATION_STATUS": observation,
        "EVIDENCE_STATUS": evidence,
        "REACTION": reaction,
        "BLOCKED": blocked,
        "AUTHORITY": "NONE",
    }
    row.update(extra)
    return row


def _catalog_rows_present(contract: str) -> bool:
    if any(requirement_id not in contract for requirement_id in REQUIREMENT_IDS):
        return False
    if NEGATIVE_CODES["MV2-04"] not in contract or NEGATIVE_CODES["MV2-05"] not in contract:
        return False
    return NEGATIVE_CODES["MV2-08"] in contract and "NOT_PROVEN" in contract


def _role_flags(decision: str) -> bool:
    return INTERNAL_AREA_TOKEN in decision and SEPARATE_UNIVERSE_TOKEN in decision


def _read_inside(root: Path, relative: str) -> str | None:
    path = root / relative
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _constants(root: Path) -> dict[str, Any] | None:
    path = root / GHOSV_CONSTANTS_RELATIVE
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    parsed = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, Any] = {}
    names = {"NOT_TESTED_REQUIREMENTS", "CURRENT_CODE_PIN"}
    for node in parsed.body:
        target, value = _assignment(node)
        if target in names and value is not None:
            found[target] = ast.literal_eval(value)
    return found


def _runtime_activated(root: Path) -> bool | None:
    path = root / PERSISTENCE_CONSTANTS_RELATIVE
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    parsed = ast.parse(path.read_text(encoding="utf-8"))
    for node in parsed.body:
        target, value = _assignment(node)
        if target == "RUNTIME_ACTIVATED" and value is not None:
            evaluated = ast.literal_eval(value)
            if isinstance(evaluated, bool):
                return evaluated
    return None


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


def _not_tested(constants: dict[str, Any] | None) -> tuple[str, ...] | None:
    if constants is None:
        return None
    raw = constants.get("NOT_TESTED_REQUIREMENTS")
    if not isinstance(raw, tuple) or not all(isinstance(item, str) for item in raw):
        return None
    if any(requirement_id not in raw for requirement_id in REQUIREMENT_IDS):
        return None
    return raw


def _pin(constants: dict[str, Any] | None) -> str | None:
    if constants is None:
        return None
    pin = constants.get("CURRENT_CODE_PIN")
    if isinstance(pin, str):
        return pin
    return None


def _assert_no_forbidden_keys(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            _assert_no_forbidden_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_forbidden_keys(item)
