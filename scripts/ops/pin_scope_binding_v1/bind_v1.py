"""Caller-supplied pin and scope binding. AUTHORITY=NONE.

The function compares values the caller supplies. It does not read git, census,
landscape, or graph artifacts, and it does not add scope nodes.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    CENSUS_PIN_FIELD,
    COVERAGE_PROOF,
    EXECUTION_AUTHORITY,
    GRAPH_PIN_FIELD,
    GUARDIAN_IDENTITY,
    LANDSCAPE_COMMIT_FIELD,
    LANDSCAPE_TREE_FIELD,
    LIVE_GATE,
    NETWORK_ACCESS,
    PROVENANCE_ROLES,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SCOPE_FIELDS,
    STATUS_ACCEPTED,
    STATUS_INPUT_SOURCE_STALE,
    STATUS_INVALID_PROVENANCE,
    STATUS_INVALID_SCOPE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_CONFLICT,
    STATUS_SCOPE_EMPTY,
    TRADING_AUTHORITY,
)

_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_ROLE_FIELDS = {
    "census": (CENSUS_PIN_FIELD,),
    "landscape": (LANDSCAPE_COMMIT_FIELD, LANDSCAPE_TREE_FIELD),
    "graph": (GRAPH_PIN_FIELD,),
}


def bind_pin_and_scope_v1(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
    scope: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind a declared pin and a caller scope, or return one fail-closed status."""
    provenance_reasons = _provenance_reasons(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        provenance=provenance,
    )
    if provenance_reasons:
        return _result(
            STATUS_INVALID_PROVENANCE,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            reasons=provenance_reasons,
        )

    mismatches = _pin_mismatches(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
    )
    if mismatches:
        return _result(
            STATUS_PIN_MISMATCH,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            mismatches=mismatches,
        )

    stale_sources = _stale_sources(
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        provenance=provenance,
    )
    if stale_sources:
        return _result(
            STATUS_INPUT_SOURCE_STALE,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            stale_sources=stale_sources,
        )

    scope_reasons, parsed = _parse_scope(scope)
    if scope_reasons:
        return _result(
            STATUS_INVALID_SCOPE,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            reasons=scope_reasons,
        )
    assert parsed is not None

    conflicts = _scope_conflicts(parsed)
    if conflicts:
        return _result(
            STATUS_SCOPE_CONFLICT,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            allowed_nodes=parsed["allowed_nodes"],
            exclusions=parsed["exclusions"],
            unassigned=parsed["unassigned"],
            conflicts=conflicts,
        )

    if not parsed["allowed_nodes"] and not parsed["exclusions"] and not parsed["unassigned"]:
        return _result(
            STATUS_SCOPE_EMPTY,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            allowed_nodes=[],
            exclusions=[],
            unassigned=[],
            coverage_gap=True,
        )

    return _result(
        STATUS_ACCEPTED,
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        allowed_nodes=parsed["allowed_nodes"],
        exclusions=parsed["exclusions"],
        unassigned=parsed["unassigned"],
        coverage_gap=bool(parsed["unassigned"]),
    )


def _provenance_reasons(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    _collect_sha(reasons, "authoritative_commit_sha", authoritative_commit_sha)
    _collect_sha(reasons, "authoritative_tree_sha", authoritative_tree_sha)
    _collect_sha(reasons, "declared_commit_sha", declared_commit_sha)
    _collect_sha(reasons, "declared_tree_sha", declared_tree_sha)
    if not isinstance(provenance, Mapping):
        reasons.append("provenance_not_object")
        return reasons
    extra = sorted(set(provenance) - set(PROVENANCE_ROLES))
    reasons.extend(f"provenance_extra:{role}" for role in extra)
    missing = [role for role in PROVENANCE_ROLES if role not in provenance]
    reasons.extend(f"provenance_missing:{role}" for role in missing)
    for role in PROVENANCE_ROLES:
        if role not in provenance:
            continue
        body = provenance[role]
        if not isinstance(body, Mapping):
            reasons.append(f"{role}_not_object")
            continue
        expected = _ROLE_FIELDS[role]
        reasons.extend(f"{role}_extra:{field}" for field in sorted(set(body) - set(expected)))
        for field in expected:
            if field not in body:
                reasons.append(f"{role}_missing:{field}")
            else:
                _collect_sha(reasons, f"{role}.{field}", body[field])
    return reasons


def _collect_sha(reasons: list[str], label: str, value: Any) -> None:
    if not isinstance(value, str) or _SHA40.fullmatch(value) is None:
        reasons.append(f"{label}_malformed")


def _pin_mismatches(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
) -> list[str]:
    mismatches: list[str] = []
    if declared_commit_sha != authoritative_commit_sha:
        mismatches.append("commit")
    if declared_tree_sha != authoritative_tree_sha:
        mismatches.append("tree")
    return mismatches


def _stale_sources(
    *,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
) -> list[str]:
    stale: list[str] = []
    census = provenance["census"]
    landscape = provenance["landscape"]
    graph = provenance["graph"]
    if census[CENSUS_PIN_FIELD] != declared_commit_sha:
        stale.append("census")
    if landscape[LANDSCAPE_COMMIT_FIELD] != declared_commit_sha:
        stale.append("landscape_commit")
    if landscape[LANDSCAPE_TREE_FIELD] != declared_tree_sha:
        stale.append("landscape_tree")
    if graph[GRAPH_PIN_FIELD] != declared_commit_sha:
        stale.append("graph")
    return stale


def _parse_scope(
    scope: Mapping[str, Any],
) -> tuple[list[str], dict[str, list[str]] | None]:
    reasons: list[str] = []
    if not isinstance(scope, Mapping):
        return ["scope_not_object"], None
    reasons.extend(f"scope_extra:{field}" for field in sorted(set(scope) - set(SCOPE_FIELDS)))
    parsed: dict[str, list[str]] = {}
    for field in SCOPE_FIELDS:
        if field not in scope:
            reasons.append(f"scope_missing:{field}")
            continue
        value = scope[field]
        if not isinstance(value, list):
            reasons.append(f"{field}_not_list")
            continue
        nodes: list[str] = []
        seen: set[str] = set()
        for index, node in enumerate(value):
            if not isinstance(node, str) or node.strip() == "":
                reasons.append(f"{field}[{index}]_malformed")
                continue
            if node in seen:
                reasons.append(f"{field}_duplicate:{node}")
                continue
            seen.add(node)
            nodes.append(node)
        parsed[field] = nodes
    if reasons:
        return reasons, None
    return [], parsed


def _scope_conflicts(parsed: Mapping[str, list[str]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    pairs = (
        ("allowed_nodes", "exclusions"),
        ("allowed_nodes", "unassigned"),
        ("exclusions", "unassigned"),
    )
    for left, right in pairs:
        overlap = sorted(set(parsed[left]) & set(parsed[right]))
        for node in overlap:
            conflicts.append({"node": node, "sets": [left, right]})
    return conflicts


def _scope_coverage_gap(status: str, allowed_nodes: list[str], unassigned: list[str]) -> bool:
    """Scope gaps come only from the checked scope, not from graph or findings."""
    if status in {STATUS_SCOPE_EMPTY, STATUS_SCOPE_CONFLICT}:
        return True
    if status != STATUS_ACCEPTED:
        return False
    return not allowed_nodes or bool(unassigned)


def _result(
    status: str,
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    allowed_nodes: list[str] | None = None,
    exclusions: list[str] | None = None,
    unassigned: list[str] | None = None,
    mismatches: list[str] | None = None,
    stale_sources: list[str] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
    reasons: list[str] | None = None,
    coverage_gap: bool = False,
) -> dict[str, Any]:
    allowed = list(allowed_nodes or [])
    open_nodes = list(unassigned or [])
    scope_coverage_gap = _scope_coverage_gap(status, allowed, open_nodes)
    graph_coverage_gap = False
    observation_coverage_gap = False
    coverage_gap = (
        bool(coverage_gap) or scope_coverage_gap or graph_coverage_gap or observation_coverage_gap
    )
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_identity": GUARDIAN_IDENTITY,
        "live_gate": LIVE_GATE,
        "network_access": NETWORK_ACCESS,
        "implicit_scope_expansion": False,
        "scope_coverage_gap": scope_coverage_gap,
        "graph_coverage_gap": graph_coverage_gap,
        "observation_coverage_gap": observation_coverage_gap,
        "coverage_gap": coverage_gap,
        "coverage_proof": COVERAGE_PROOF,
        "authoritative_commit_sha": authoritative_commit_sha,
        "authoritative_tree_sha": authoritative_tree_sha,
        "declared_commit_sha": declared_commit_sha,
        "declared_tree_sha": declared_tree_sha,
        "allowed_nodes": list(allowed_nodes or []),
        "exclusions": list(exclusions or []),
        "unassigned": list(unassigned or []),
        "mismatches": list(mismatches or []),
        "stale_sources": list(stale_sources or []),
        "conflicts": list(conflicts or []),
        "reasons": list(reasons or []),
    }
