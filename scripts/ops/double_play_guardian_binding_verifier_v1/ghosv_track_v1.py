"""Read-only checks for MV2-04, MV2-05, MV2-06 and MV2-08. AUTHORITY=NONE."""

from __future__ import annotations

import ast
from typing import Any, Mapping

SCHEMA_ID = "DOUBLE_PLAY_GHOSV_BINDING_VERIFIER_V1"
TOOL_IDENTITY = "DOUBLE_PLAY_GHOSV"
DOMAIN = "DOUBLE_PLAY"
EXPECTED_BASELINE_SHA = "97c8c954204c15f9af5a48995b889ce3fb223c64"
EXPECTED_BASELINE_TREE = "898ede79de7e527db3632b8a3b32daf8b9b098b8"
EXISTING_GHOSV_CODE_PIN = "7628005ae495c115ff341d32fa932b7f4642f456"
LOCK_TOKEN = "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3"
INTERNAL_AREA_TOKEN = "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA=true"
SEPARATE_UNIVERSE_TOKEN = "DOUBLE_PLAY_SEPARATE_UNIVERSE=false"
REQUIREMENT_IDS = ("MV2-04", "MV2-05", "MV2-06", "MV2-08")
STATE_IMPORTS = ("transition_state", "update_dynamic_boundaries")
INSPECTED_ENFORCEMENT_MODULE = (
    "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py"
)
FORBIDDEN_OUTPUT_KEYS = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized"}
)


def verify_double_play_ghosv_v1(
    *,
    current_sha: str,
    current_tree: str,
    ghosv_contract_text: str | None,
    decision_path_text: str | None,
    hardening_source: str | None,
    ghosv_constants_source: str | None,
    persistence_constants_source: str | None,
    replay_source: str | None,
    policy_source: str | None,
    host_binding_source: str | None,
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

    texts = (
        ghosv_contract_text,
        decision_path_text,
        hardening_source,
        ghosv_constants_source,
        persistence_constants_source,
        replay_source,
        policy_source,
        host_binding_source,
    )
    if any(not isinstance(text, str) or not text for text in texts):
        reasons.append("MISSING_REQUIRED_EVIDENCE")

    not_tested = _not_tested(ghosv_constants_source)
    if not_tested is None:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    pin = _constant(ghosv_constants_source, "CURRENT_CODE_PIN")
    if not isinstance(pin, str):
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    if claim_map.get("treat_older_pin_as_current") is True:
        reasons.append("OLDER_PIN_TREATED_AS_CURRENT")

    contract = ghosv_contract_text or ""
    decision = decision_path_text or ""
    findings = [
        _mv2_04(decision, replay_source, claim_map, reasons),
        _mv2_05(contract, decision, hardening_source, claim_map, reasons),
        _mv2_06(replay_source, policy_source, claim_map, reasons),
        _mv2_08(persistence_constants_source, host_binding_source, claim_map, reasons),
    ]
    for row in findings:
        row["EXISTING_CHECKER_STATUS"] = (
            "NOT_TESTED" if not_tested and row["REQUIREMENT_ID"] in not_tested else "UNKNOWN"
        )
        row["DOMAIN"] = DOMAIN

    unique = tuple(dict.fromkeys(reasons))
    report: dict[str, Any] = {
        "SCHEMA_ID": SCHEMA_ID,
        "TOOL_IDENTITY": TOOL_IDENTITY,
        "DOMAIN": DOMAIN,
        "AUTHORITY": "NONE",
        "TRADING_AUTHORITY": "NONE",
        "SAFETY_AUTHORITY": "NONE",
        "EXECUTION_AUTHORITY": "NONE",
        "GHOSV_READY": False,
        "VERIFICATION_STATUS": "REJECTED" if unique else "REPORTED",
        "REJECTION_REASONS": list(unique),
        "EXISTING_CHECKER_EXECUTED": False,
        "KNOWN_OLDER_GHOSV_CODE_PIN": EXISTING_GHOSV_CODE_PIN,
        "OBSERVED_GHOSV_CODE_PIN": pin if isinstance(pin, str) else None,
        "GHOSV_PIN_IS_CURRENT_BASELINE": pin == EXPECTED_BASELINE_SHA,
        "FINDINGS": findings,
    }
    _assert_no_forbidden_keys(report)
    return report


def _mv2_04(
    decision: str,
    replay_source: str | None,
    claims: Mapping[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    flags = INTERNAL_AREA_TOKEN in decision and SEPARATE_UNIVERSE_TOKEN in decision
    imports = _state_imports(replay_source)
    violation = (
        claims.get("separate_universe_claimed") is True
        or claims.get("decision_authority_claimed") is True
    )
    if violation:
        reasons.append("DYNAMIC_SCOPE_ROLE_VIOLATION")
    if violation:
        status = "VIOLATION"
    elif flags and imports:
        status = "INTERNAL_ROLE_OBSERVED"
    else:
        status = "MISSING"
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    return {
        "REQUIREMENT_ID": "MV2-04",
        "OBSERVATION_STATUS": status,
        "EVIDENCE_STATUS": "NOT_PROVEN" if violation or not flags else "PARTIAL",
        "REACTION": "DYNAMIC_SCOPE_ROLE_VIOLATION" if violation else None,
        "STATE_IMPORTS_OBSERVED": imports,
        "DECISION_AUTHORITY_GRANTED": False,
        "AUTHORITY": "NONE",
    }


def _mv2_05(
    contract: str,
    decision: str,
    hardening_source: str | None,
    claims: Mapping[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    tokens = bool(contract and decision and LOCK_TOKEN in contract and LOCK_TOKEN in decision)
    enforced = _lock_assigned(hardening_source)
    violation = (
        claims.get("lock_mutation_requested") is True
        or claims.get("tool_run_claimed_as_owner_go") is True
        or (contract and decision and not tokens)
    )
    if violation:
        reasons.append("OWNER_LOCK_VIOLATION")
    if not tokens and not violation:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    return {
        "REQUIREMENT_ID": "MV2-05",
        "OBSERVATION_STATUS": "VIOLATION" if violation else "LOCK_TEXT_OBSERVED",
        "EVIDENCE_STATUS": "PARTIAL" if tokens and not violation else "NOT_PROVEN",
        "REACTION": "OWNER_LOCK_VIOLATION" if violation else None,
        "LOCK_TOKENS_OBSERVED": tokens,
        "PYTHON_ENFORCEMENT": "TOKEN_MATCH" if enforced else "ENFORCEMENT_ABSENT",
        "ENFORCEMENT_SCOPE": INSPECTED_ENFORCEMENT_MODULE,
        "REPOSITORY_WIDE_ENFORCEMENT": "NOT_ASSESSED",
        "TOOL_RUN_IS_OWNER_GO": False,
        "AUTHORITY": "NONE",
    }


def _mv2_06(
    replay_source: str | None,
    policy_source: str | None,
    claims: Mapping[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    call_present = _calls_name(replay_source, "evaluate_double_play_entry_exit_policy_v0")
    default_none = _authority_default_none(policy_source)
    if claims.get("effect_pass_requested") is True:
        reasons.append("EFFECT_PASS_BLOCKED")
    if not call_present or not default_none:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    return {
        "REQUIREMENT_ID": "MV2-06",
        "OBSERVATION_STATUS": "CALL_SITE_OBSERVED" if call_present else "MISSING",
        "EVIDENCE_STATUS": "NOT_PROVEN",
        "REACTION": None,
        "ENTRY_EXIT_EFFECT": "NOT_PROVEN",
        "EFFECT_PASS": False,
        "AUTHORITY_EFFECT_DEFAULT": "NONE" if default_none else "UNKNOWN",
        "CALL_PRESENCE_IS_NOT_REACHABILITY": True,
        "AUTHORITY": "NONE",
    }


def _mv2_08(
    persistence_source: str | None,
    host_source: str | None,
    claims: Mapping[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    persisted = _constant(persistence_source, "DYNAMIC_SCOPE_STATE_PERSISTED")
    activated = _constant(persistence_source, "RUNTIME_ACTIVATED")
    call_present = _calls_name(host_source, "persist_dynamic_scope_state_atomic_v1")
    conditional = _persist_condition(host_source)
    if claims.get("persists_claimed") is True or claims.get("writer_proven_from_constants") is True:
        reasons.append("PERSISTENCE_EVIDENCE_ABSENT")
    if claims.get("writer_refutation_requested") is True:
        reasons.append("WRITER_REFUTATION_BLOCKED")
    if persisted is None or activated is None or not call_present:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    return {
        "REQUIREMENT_ID": "MV2-08",
        "OBSERVATION_STATUS": "WRITER_CALL_CONDITIONAL" if call_present else "MISSING",
        "EVIDENCE_STATUS": "NOT_PROVEN",
        "REACTION": (
            "PERSISTENCE_EVIDENCE_ABSENT"
            if claims.get("persists_claimed") is True
            or claims.get("writer_proven_from_constants") is True
            else None
        ),
        "DYNAMIC_SCOPE_STATE_PERSISTED": persisted,
        "BINDER_RUNTIME_ACTIVATED": activated,
        "WRITER_CALL_PRESENT": call_present,
        "WRITER_CONDITION": conditional,
        "PRODUCTIVE_WRITER": "NOT_PROVEN",
        "RUNTIME_ACTIVATED_IS_WRITER_ABSENCE_PROOF": False,
        "CONSTANT_IS_WRITER_PROOF": False,
        "AUTHORITY": "NONE",
    }


def _state_imports(source: str | None) -> bool:
    if not source:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if node.module.split(".")[-1] != "double_play_state":
            continue
        names = {alias.name for alias in node.names}
        if set(STATE_IMPORTS).issubset(names):
            return True
    return False


def _lock_assigned(source: str | None) -> bool:
    value = _constant(source, "DOUBLE_PLAY_FULL_OWNER_LOCK")
    return value == "LEVEL_3"


def _calls_name(source: str | None, name: str) -> bool:
    if not source:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _callee(node) == name:
            return True
    return False


def _persist_condition(source: str | None) -> str | None:
    if not source:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    parents = _parents(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _callee(node) == "persist_dynamic_scope_state_atomic_v1":
            return _condition(node, parents)
    return None


def _authority_default_none(source: str | None) -> bool:
    if not source:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    constants: dict[str, Any] = {}
    for node in tree.body:
        target, value = _assignment(node)
        if target is None or value is None:
            continue
        try:
            constants[target] = ast.literal_eval(value)
        except (ValueError, TypeError):
            continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id != "authority_effect" or node.value is None:
            continue
        if isinstance(node.value, ast.Constant):
            return node.value.value == "NONE"
        if isinstance(node.value, ast.Name):
            return constants.get(node.value.id) == "NONE"
    return False


def _not_tested(source: str | None) -> tuple[str, ...] | None:
    raw = _constant(source, "NOT_TESTED_REQUIREMENTS")
    if not isinstance(raw, tuple) or any(item not in raw for item in REQUIREMENT_IDS):
        return None
    return raw


def _constant(source: str | None, name: str) -> Any:
    if not source:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        target, value = _assignment(node)
        if target == name and value is not None:
            return ast.literal_eval(value)
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


def _callee(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _condition(call: ast.Call, parents: Mapping[ast.AST, ast.AST]) -> str:
    parts: list[str] = []
    current: ast.AST | None = call
    seen: set[int] = set()
    while current in parents:
        parent = parents[current]
        if isinstance(parent, ast.If) and id(parent) not in seen:
            branch = _branch(parent, call, parents)
            if branch == "body":
                parts.append(ast.unparse(parent.test))
            elif branch == "orelse":
                parts.append(_negate(parent.test))
            seen.add(id(parent))
        current = parent
    parts.reverse()
    return " and ".join(parts) if parts else "DIRECT"


def _branch(
    if_node: ast.If,
    target: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
) -> str | None:
    current: ast.AST | None = target
    while current is not None and current is not if_node:
        if current in if_node.body:
            return "body"
        if current in if_node.orelse:
            return "orelse"
        current = parents.get(current)
    return None


def _negate(test: ast.expr) -> str:
    if (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
    ):
        left = ast.unparse(test.left)
        if isinstance(test.ops[0], ast.IsNot):
            return f"{left} is None"
        if isinstance(test.ops[0], ast.Is):
            return f"{left} is not None"
    return f"not ({ast.unparse(test)})"


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


def _assert_no_forbidden_keys(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            _assert_no_forbidden_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_forbidden_keys(item)
