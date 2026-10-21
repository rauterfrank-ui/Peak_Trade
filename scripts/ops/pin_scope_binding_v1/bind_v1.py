"""Caller-supplied pin and scope binding. AUTHORITY=NONE.

Compares caller values with the checkout's embedded census and landscape
pins and with the git tree of the authoritative commit. Historical pins stay
historical. A caller who labels them CURRENT is rejected.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    CENSUS_CURRENCY_FIELD,
    CENSUS_EMBEDDED_PIN_KEY,
    CENSUS_PIN_FIELD,
    CENSUS_RELATIVE_PATH,
    COVERAGE_PROOF,
    CURRENCY_ABSENT,
    CURRENCY_CURRENT,
    CURRENCY_HISTORICAL,
    DOMAIN_EVIDENCE_COMMIT_FIELD,
    DOMAIN_EVIDENCE_TREE_FIELD,
    EXECUTION_AUTHORITY,
    GRAPH_ABSENT_PIN,
    GRAPH_CURRENCY_FIELD,
    GRAPH_PIN_FIELD,
    GUARDIAN_IDENTITY,
    INTEGRATED_GRAPH_NAME,
    LANDSCAPE_COMMIT_FIELD,
    LANDSCAPE_CURRENCY_FIELD,
    LANDSCAPE_EMBEDDED_COMMIT_KEY,
    LANDSCAPE_EMBEDDED_TREE_KEY,
    LANDSCAPE_RELATIVE_PATH,
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
    STATUS_FORGED_PROVENANCE,
    STATUS_INVALID_PROVENANCE,
    STATUS_INVALID_SCOPE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_CONFLICT,
    STATUS_SCOPE_EMPTY,
    TRADING_AUTHORITY,
)
from scripts.ops.pin_scope_binding_v1.legacy_v1 import (
    LEGACY_SCOPE_FIELDS,
    bind_legacy_pin_and_scope_v1,
)

_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CENSUS_FIELDS = (CENSUS_PIN_FIELD, CENSUS_CURRENCY_FIELD)
_LANDSCAPE_FIELDS = (
    LANDSCAPE_COMMIT_FIELD,
    LANDSCAPE_TREE_FIELD,
    LANDSCAPE_CURRENCY_FIELD,
)
_GRAPH_FIELDS = (GRAPH_PIN_FIELD, GRAPH_CURRENCY_FIELD)
_DOMAIN_FIELDS = (DOMAIN_EVIDENCE_COMMIT_FIELD, DOMAIN_EVIDENCE_TREE_FIELD)
_ROLE_FIELDS = {
    "census": _CENSUS_FIELDS,
    "landscape": _LANDSCAPE_FIELDS,
    "graph": _GRAPH_FIELDS,
    "domain_evidence": _DOMAIN_FIELDS,
}


def bind_pin_and_scope_v1(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
    scope: Mapping[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Bind a declared pin and a scope, or return one fail-closed status.

    Legacy manifests keep the three-field contract. Five-class domain evidence
    uses the current embedded-pin contract. Mixed contracts fail closed.
    """
    if _is_legacy_contract(provenance, scope):
        return bind_legacy_pin_and_scope_v1(
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            provenance=provenance,
            scope=scope,
        )
    root = _REPO_ROOT if repo_root is None else repo_root
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
        provenance=provenance,
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

    object_reason = _git_tree_reason(
        root,
        authoritative_commit_sha,
        authoritative_tree_sha,
    )
    if object_reason is not None:
        status = (
            STATUS_PIN_MISMATCH if object_reason == "tree_object" else STATUS_INVALID_PROVENANCE
        )
        return _result(
            status,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            mismatches=["tree"] if object_reason == "tree_object" else [],
            reasons=[] if object_reason == "tree_object" else [object_reason],
        )

    forged, stale_sources, embedded = _embedded_provenance(
        root,
        provenance=provenance,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
    )
    if forged:
        return _result(
            STATUS_FORGED_PROVENANCE,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            stale_sources=stale_sources,
            reasons=forged,
            embedded_pins=embedded,
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
            embedded_pins=embedded,
            stale_sources=stale_sources,
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
            parsed=parsed,
            conflicts=conflicts,
            embedded_pins=embedded,
            stale_sources=stale_sources,
        )

    if all(not parsed[field] for field in SCOPE_FIELDS):
        return _result(
            STATUS_SCOPE_EMPTY,
            authoritative_commit_sha=authoritative_commit_sha,
            authoritative_tree_sha=authoritative_tree_sha,
            declared_commit_sha=declared_commit_sha,
            declared_tree_sha=declared_tree_sha,
            parsed=parsed,
            embedded_pins=embedded,
            stale_sources=stale_sources,
            coverage_gap=True,
        )

    return _result(
        STATUS_ACCEPTED,
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        parsed=parsed,
        embedded_pins=embedded,
        stale_sources=stale_sources,
        coverage_gap=bool(parsed["unresolved"]),
    )


def _is_legacy_contract(provenance: Any, scope: Any) -> bool:
    """True only for the old manifest shape, never for domain evidence."""
    if not isinstance(provenance, Mapping) or not isinstance(scope, Mapping):
        return False
    if "domain_evidence" in provenance:
        return False
    for body in provenance.values():
        if isinstance(body, Mapping) and "currency" in body:
            return False
    scope_keys = set(scope)
    if scope_keys & set(SCOPE_FIELDS):
        return False
    return bool(scope_keys & set(LEGACY_SCOPE_FIELDS))


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
                continue
            value = body[field]
            if field in {CENSUS_CURRENCY_FIELD, LANDSCAPE_CURRENCY_FIELD, GRAPH_CURRENCY_FIELD}:
                _collect_currency(reasons, f"{role}.{field}", role, value)
            else:
                _collect_sha(reasons, f"{role}.{field}", value)
    return reasons


def _collect_currency(reasons: list[str], label: str, role: str, value: Any) -> None:
    allowed = {CURRENCY_HISTORICAL, CURRENCY_CURRENT}
    if role == "graph":
        allowed = {CURRENCY_ABSENT}
    if not isinstance(value, str) or value not in allowed:
        reasons.append(f"{label}_invalid")


def _collect_sha(reasons: list[str], label: str, value: Any) -> None:
    if not isinstance(value, str) or _SHA40.fullmatch(value) is None:
        reasons.append(f"{label}_malformed")


def _pin_mismatches(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
) -> list[str]:
    mismatches: list[str] = []
    if declared_commit_sha != authoritative_commit_sha:
        mismatches.append("commit")
    if declared_tree_sha != authoritative_tree_sha:
        mismatches.append("tree")
    domain = provenance["domain_evidence"]
    if domain[DOMAIN_EVIDENCE_COMMIT_FIELD] != authoritative_commit_sha:
        mismatches.append("domain_evidence_commit")
    if domain[DOMAIN_EVIDENCE_TREE_FIELD] != authoritative_tree_sha:
        mismatches.append("domain_evidence_tree")
    return mismatches


def _git_tree_reason(repo_root: Path, commit_sha: str, tree_sha: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", f"{commit_sha}^{{tree}}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "git_tree_unresolved"
    if completed.returncode != 0:
        return "git_commit_unresolved"
    actual = completed.stdout.strip()
    if actual != tree_sha:
        return "tree_object"
    return None


def _embedded_provenance(
    repo_root: Path,
    *,
    provenance: Mapping[str, Any],
    declared_commit_sha: str,
    declared_tree_sha: str,
) -> tuple[list[str], list[str], dict[str, str]]:
    forged: list[str] = []
    stale: list[str] = []
    census_path = repo_root / CENSUS_RELATIVE_PATH
    landscape_path = repo_root / LANDSCAPE_RELATIVE_PATH
    census_doc = _read_json(census_path)
    landscape_doc = _read_json(landscape_path)
    if census_doc is None:
        forged.append("census_artifact_unreadable")
        census_pin = ""
    else:
        census_pin = str(census_doc.get(CENSUS_EMBEDDED_PIN_KEY) or "")
    if landscape_doc is None:
        forged.append("landscape_artifact_unreadable")
        landscape_commit = ""
        landscape_tree = ""
    else:
        landscape_commit = str(landscape_doc.get(LANDSCAPE_EMBEDDED_COMMIT_KEY) or "")
        landscape_tree = str(landscape_doc.get(LANDSCAPE_EMBEDDED_TREE_KEY) or "")

    census = provenance["census"]
    claimed_census = str(census[CENSUS_PIN_FIELD])
    census_currency = str(census[CENSUS_CURRENCY_FIELD])
    if claimed_census != census_pin:
        forged.append("census_pin_not_embedded")
    elif census_currency == CURRENCY_CURRENT and census_pin != declared_commit_sha:
        forged.append("census_currency_forged_current")
    elif census_currency == CURRENCY_HISTORICAL and census_pin == declared_commit_sha:
        forged.append("census_historical_label_matches_current")
    elif census_pin != declared_commit_sha:
        stale.append("census")

    landscape = provenance["landscape"]
    claimed_commit = str(landscape[LANDSCAPE_COMMIT_FIELD])
    claimed_tree = str(landscape[LANDSCAPE_TREE_FIELD])
    landscape_currency = str(landscape[LANDSCAPE_CURRENCY_FIELD])
    if claimed_commit != landscape_commit or claimed_tree != landscape_tree:
        forged.append("landscape_pin_not_embedded")
    elif landscape_currency == CURRENCY_CURRENT and (
        landscape_commit != declared_commit_sha or landscape_tree != declared_tree_sha
    ):
        forged.append("landscape_currency_forged_current")
    elif landscape_commit != declared_commit_sha or landscape_tree != declared_tree_sha:
        stale.append("landscape_commit")
        stale.append("landscape_tree")

    graph = provenance["graph"]
    graph_present = _integrated_graph_present(repo_root)
    if graph_present:
        forged.append("graph_absent_claim_while_artifact_exists")
    if str(graph[GRAPH_PIN_FIELD]) != GRAPH_ABSENT_PIN:
        forged.append("graph_pin_not_absent_sentinel")
    if str(graph[GRAPH_CURRENCY_FIELD]) != CURRENCY_ABSENT:
        forged.append("graph_currency_not_absent")
    elif not graph_present:
        stale.append("graph")

    embedded = {
        "census": census_pin,
        "landscape_commit": landscape_commit,
        "landscape_tree": landscape_tree,
        "graph": CURRENCY_ABSENT,
    }
    return forged, stale, embedded


def _read_json(path: Path) -> Mapping[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return payload


def _integrated_graph_present(repo_root: Path) -> bool:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", f"*{INTEGRATED_GRAPH_NAME}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return True
    if completed.returncode != 0:
        return True
    return bool(completed.stdout.strip())


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
    fields = list(SCOPE_FIELDS)
    for index, left in enumerate(fields):
        for right in fields[index + 1 :]:
            overlap = sorted(set(parsed[left]) & set(parsed[right]))
            for node in overlap:
                conflicts.append({"node": node, "sets": [left, right]})
    return conflicts


def _scope_coverage_gap(status: str, parsed: Mapping[str, list[str]]) -> bool:
    if status in {STATUS_SCOPE_EMPTY, STATUS_SCOPE_CONFLICT}:
        return True
    if status != STATUS_ACCEPTED:
        return False
    return not parsed["domain_functional_members"] or bool(parsed["unresolved"])


def _result(
    status: str,
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    parsed: Mapping[str, list[str]] | None = None,
    mismatches: list[str] | None = None,
    stale_sources: list[str] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
    reasons: list[str] | None = None,
    embedded_pins: Mapping[str, str] | None = None,
    coverage_gap: bool = False,
) -> dict[str, Any]:
    body = {field: list((parsed or {}).get(field) or []) for field in SCOPE_FIELDS}
    scope_coverage_gap = _scope_coverage_gap(status, body)
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
        **body,
        "in_scope_nodes": (
            body["domain_functional_members"]
            + body["external_interfaces_under_observation"]
            + body["external_references_only"]
        ),
        "mismatches": list(mismatches or []),
        "stale_sources": list(stale_sources or []),
        "conflicts": list(conflicts or []),
        "embedded_pins": dict(embedded_pins or {}),
        "reasons": list(reasons or []),
    }
