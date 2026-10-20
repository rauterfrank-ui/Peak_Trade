"""Shared fail-closed checks for the three Execution guardian tracks. AUTHORITY=NONE."""

from __future__ import annotations

import ast
import json
import re
from typing import Any, Mapping

from scripts.ops.execution_guardian_binding_verifier_v1.constants_v1 import (
    BOUNDARY_CONTRACT_TOKENS,
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    FORBIDDEN_CONTRACT_TOKENS,
    FORBIDDEN_OUTPUT_KEYS,
    STALE_FOREIGN_SNAPSHOT_ID,
    frozen_registry_document_v1,
)

_CODE_PIN_RE = re.compile(r"CURRENT_CODE_PIN=([0-9a-f]{40})")
_TREE_PIN_RE = re.compile(r"CURRENT_TREE_PIN=([0-9a-f]{40})")

_AUTHORITY_FIELDS = (
    "authority",
    "trading_authority",
    "safety_authority",
    "execution_authority",
)


def authority_block_v1() -> dict[str, Any]:
    return {
        "AUTHORITY": "NONE",
        "GUARDIAN_AUTHORITY": "NONE",
        "TRADING_AUTHORITY": "NONE",
        "SAFETY_AUTHORITY": "NONE",
        "EXECUTION_AUTHORITY": "NONE",
        "POST_ALLOWED": False,
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "EXTERNAL_EFFECT_PERFORMED": False,
        "UNIVERSE_RATIFIED": False,
        "VERIFIER_EXECUTION_IS_OWNER_AUTHORIZATION": False,
        "DOUBLE_PLAY_FULL_OWNER_LOCK": "LEVEL_3",
        "DOUBLE_PLAY_MUTATED": False,
    }


def bind_baseline_v1(current_sha: str, current_tree: str, reasons: list[str]) -> None:
    if current_sha != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if current_tree != EXPECTED_BASELINE_TREE:
        reasons.append("BASELINE_TREE_MISMATCH")


def reject_claims_v1(claims: Mapping[str, Any], reasons: list[str]) -> None:
    if any(claims.get(name) not in (None, "NONE") for name in _AUTHORITY_FIELDS):
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")
    if claims.get("universe_ratification_requested") is True:
        reasons.append("UNAUTHORIZED_UNIVERSE_CLAIM")
    if claims.get("workflow_equals_guardian") is True:
        reasons.append("WORKFLOW_EQUALS_GUARDIAN_CLAIM")
    if claims.get("transitive_closure_proven") is True:
        reasons.append("TRANSITIVE_CLOSURE_NOT_EVIDENCED")
    if claims.get("open_task_resolved") is True:
        reasons.append("OPEN_TASK_RESOLUTION_BLOCKED")
    if claims.get("post_allowed") is True or claims.get("external_effect_authorized") is True:
        reasons.append("EXTERNAL_EFFECT_CLAIM")
    if claims.get("double_play_lock_mutation") is True:
        reasons.append("OWNER_LOCK_VIOLATION")
    if claims.get("traffic_green_is_release") is True:
        reasons.append("WORKFLOW_AMPEL_IS_NOT_RELEASE")
    if contains_forbidden_key_v1(claims):
        reasons.append("OVERALL_PASS_FORBIDDEN")


def registry_status_v1(registry: Mapping[str, Any] | None, reasons: list[str]) -> str:
    if not isinstance(registry, Mapping):
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        return "MISSING"
    expected = json.dumps(
        frozen_registry_document_v1(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    observed = json.dumps(registry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if observed != expected:
        reasons.append("REGISTRY_DRIFT")
        return "DRIFT"
    return "MATCH"


def contract_assessment_v1(
    contract_text: str | None,
    reasons: list[str],
) -> list[dict[str, str]]:
    if not isinstance(contract_text, str) or not contract_text.strip():
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        return [
            {"CHECK": check, "RESULT": "MISSING_REQUIRED_EVIDENCE"}
            for check, _token in BOUNDARY_CONTRACT_TOKENS
        ] + [{"CHECK": "PIN", "RESULT": "MISSING_REQUIRED_EVIDENCE"}]
    findings: list[dict[str, str]] = []
    mismatched = any(token in contract_text for token in FORBIDDEN_CONTRACT_TOKENS)
    for check, token in BOUNDARY_CONTRACT_TOKENS:
        if mismatched or token not in contract_text:
            findings.append({"CHECK": check, "RESULT": "CONTRACT_MISMATCH"})
        else:
            findings.append({"CHECK": check, "RESULT": "MATCH"})
    if any(row["RESULT"] == "CONTRACT_MISMATCH" for row in findings):
        reasons.append("CONTRACT_MISMATCH")
    findings.append({"CHECK": "PIN", "RESULT": _pin_result(contract_text, reasons)})
    return findings


def _pin_result(contract_text: str, reasons: list[str]) -> str:
    code_pin = _CODE_PIN_RE.search(contract_text)
    tree_pin = _TREE_PIN_RE.search(contract_text)
    if code_pin is None and tree_pin is None:
        return "NOT_ASSESSED"
    drifted = (code_pin is not None and code_pin.group(1) != EXPECTED_BASELINE_SHA) or (
        tree_pin is not None and tree_pin.group(1) != EXPECTED_BASELINE_TREE
    )
    if drifted:
        reasons.append("PIN_DRIFT")
        return "PIN_DRIFT"
    return "MATCH"


def lock_assignment_result_v1(source: str | None) -> str:
    if source is None:
        return "NOT_ASSESSED"
    if not source.strip():
        return "MISSING_REQUIRED_EVIDENCE"
    values = constant_assignments_v1(source, {"DOUBLE_PLAY_FULL_OWNER_LOCK"})
    if values is None:
        return "MISSING_REQUIRED_EVIDENCE"
    if values.get("DOUBLE_PLAY_FULL_OWNER_LOCK") == "LEVEL_3":
        return "MATCH"
    if "DOUBLE_PLAY_FULL_OWNER_LOCK" not in values:
        return "NOT_ASSESSED"
    return "CONTRACT_MISMATCH"


def bind_graph_artifact_v1(
    artifact: Mapping[str, Any] | None,
    reasons: list[str],
) -> dict[str, Any]:
    if not isinstance(artifact, Mapping):
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        return {
            "STATUS": "MISSING_REQUIRED_EVIDENCE",
            "SNAPSHOT_ID": None,
            "GIT_HEAD": None,
            "TREE": None,
            "SNAPSHOT_IS_CURRENT_MATERIALIZATION": False,
        }
    if artifact.get("authority") not in (None, "NONE"):
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")
    snapshot = artifact.get("snapshot_id")
    code = artifact.get("code_snapshot")
    code = code if isinstance(code, Mapping) else {}
    head = code.get("git_head")
    tree = code.get("tree")
    if not isinstance(snapshot, str) or not snapshot:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        status = "MISSING_REQUIRED_EVIDENCE"
    elif snapshot == STALE_FOREIGN_SNAPSHOT_ID:
        reasons.append("SNAPSHOT_ID_MISMATCH")
        status = "SNAPSHOT_ID_MISMATCH"
    else:
        status = "RECORDED_NOT_MATERIALIZED"
    if head != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if tree != EXPECTED_BASELINE_TREE:
        reasons.append("BASELINE_TREE_MISMATCH")
    return {
        "STATUS": status,
        "SNAPSHOT_ID": snapshot if isinstance(snapshot, str) else None,
        "GIT_HEAD": head if isinstance(head, str) else None,
        "TREE": tree if isinstance(tree, str) else None,
        "SNAPSHOT_IS_CURRENT_MATERIALIZATION": False,
    }


def symbol_line_v1(source: str, symbol: str) -> int | None:
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    for node in ast.walk(parsed):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                return node.lineno
        if isinstance(node, ast.Call) and _callee_name(node) == symbol:
            return node.lineno
    return None


def _callee_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def direction_class_v1(direction: str) -> str:
    if direction.startswith("INBOUND"):
        return "REVERSE"
    if direction.startswith("OUTBOUND") or direction.startswith("FORWARD"):
        return "FORWARD"
    return "NOT_TRAVERSABLE"


def constant_assignments_v1(source: str | None, names: set[str]) -> dict[str, Any] | None:
    if not isinstance(source, str) or not source:
        return None
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    found: dict[str, Any] = {}
    for node in parsed.body:
        target, value = _assignment(node)
        if target in names and value is not None:
            try:
                found[target] = ast.literal_eval(value)
            except (TypeError, ValueError):
                return None
    return found


def contains_forbidden_key_v1(payload: object) -> bool:
    if isinstance(payload, dict):
        return any(
            key in FORBIDDEN_OUTPUT_KEYS or contains_forbidden_key_v1(value)
            for key, value in payload.items()
        )
    if isinstance(payload, list):
        return any(contains_forbidden_key_v1(item) for item in payload)
    return False


def assert_no_forbidden_keys_v1(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            assert_no_forbidden_keys_v1(value)
    elif isinstance(payload, list):
        for item in payload:
            assert_no_forbidden_keys_v1(item)


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
