"""Read-only H1 evidence-scope observer. AUTHORITY=NONE.

Calls the existing Phase-A pin, manifest, GHV, and GHOSV functions.
Does not import an H1 implementation, does not call the causal integrator,
and does not rewrite historical census, landscape, or graph pins.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.generic_ghosv_kernel_v1.observe_v1 import run_generic_ghosv_v1
from scripts.ops.guardian_domain_scope_manifest_v1.validate_v1 import (
    validate_guardian_domain_scope_manifest_v1,
)
from scripts.ops.h1_evidence_scope_observation_v1.constants_v1 import (
    ABSENCE_CATEGORY,
    AUTHORITY,
    CAUSAL_INTEGRATOR_INVOKED,
    CENSUS_RELATIVE,
    COVERAGE_PROOF,
    CURRENT_CENSUS_PROVEN,
    DOMAIN_VERIFICATION,
    EXECUTION_AUTHORITY,
    FORBIDDEN_FINDING_CATEGORIES,
    FORBIDDEN_OUTPUT_KEYS,
    GRAPH_CURRENT_FLAG_ADOPTED,
    GRAPH_RELATIVES,
    GUARDIAN_IDENTITY,
    H1_MEMBERSHIP_COMPLETE,
    H1_PATH_BY_NODE,
    H1_SCOPE_NODES,
    HISTORICAL_PINS_REWRITTEN,
    LANDSCAPE_RELATIVE,
    MANIFEST_ID,
    NETWORK_ACCESS,
    POST_EXECUTED,
    PRESENCE_CATEGORY,
    PRIVATE_GET_EXECUTED,
    PROVEN_CURRENT,
    REPOSITORY_EVIDENCE_WRITE,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCHEMA_ID,
    SCHEMA_VERSION,
    STATE_WRITE_EXECUTED,
    TOOL_SLOTS,
    TRADING_AUTHORITY,
    UNASSIGNED_FINDING_STATUS,
)
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import STATUS_ACCEPTED
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import run_scoped_ghv_v1

_SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def observe_h1_evidence_scope_v1(
    *,
    repository_root: Path,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe the two H1 path identities through the Phase-A chain."""
    root = repository_root.resolve()
    recorded = _read_recorded_provenance(root)
    pins_match_authoritative = _pins_match(
        recorded["pin_integrity"],
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
    )
    recorded["pin_integrity"]["census_pin_is_current"] = (
        recorded["pin_integrity"]["census_pin"] == authoritative_commit_sha
    )
    recorded["pin_integrity"]["landscape_commit_is_current"] = (
        recorded["pin_integrity"]["landscape_commit_pin"] == authoritative_commit_sha
    )
    recorded["pin_integrity"]["landscape_tree_is_current"] = (
        recorded["pin_integrity"]["landscape_tree_pin"] == authoritative_tree_sha
    )
    recorded["pin_integrity"]["graph_pin_is_current"] = (
        recorded["pin_integrity"]["graph_pin"] == authoritative_commit_sha
    )
    recorded["pins_match_authoritative"] = pins_match_authoritative
    if pins_match_authoritative:
        admissible_nodes, admissible_candidates = _admissible_nodes(recorded["census_objects"])
    else:
        admissible_nodes, admissible_candidates = [], []
    recorded["admissible_nodes"] = admissible_nodes
    recorded["admissible_candidates"] = admissible_candidates
    reasons = list(recorded["reasons"])
    payload, selection_reasons = _select_provenance(
        recorded_payload=recorded["payload"],
        supplied=provenance,
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
    )
    reasons.extend(selection_reasons)
    scope = _scope(recorded["admissible_nodes"])
    findings, evidence_refs = _findings(recorded)

    binding = bind_pin_and_scope_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=authoritative_commit_sha,
        declared_tree_sha=authoritative_tree_sha,
        provenance=payload,
        scope=scope,
    )
    manifest = validate_guardian_domain_scope_manifest_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        manifest={
            "manifest_id": MANIFEST_ID,
            "declared_commit_sha": authoritative_commit_sha,
            "declared_tree_sha": authoritative_tree_sha,
            "provenance": payload,
            "scope": scope,
            "tool_slots": dict(TOOL_SLOTS),
        },
    )
    scoped_ghv = run_scoped_ghv_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=authoritative_commit_sha,
        declared_tree_sha=authoritative_tree_sha,
        provenance=payload,
        scope=scope,
        candidate_nodes=list(recorded["admissible_candidates"]),
        candidate_edges=[],
    )
    ghosv = run_generic_ghosv_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=authoritative_commit_sha,
        declared_tree_sha=authoritative_tree_sha,
        provenance=payload,
        scope=scope,
        findings=findings,
        evidence_refs=evidence_refs,
    )
    proven_graph_nodes = _proven_graph_nodes(
        scoped_ghv.get("evaluated_nodes"),
        recorded["admissible_nodes"],
    )
    if binding.get("status") == STATUS_ACCEPTED and not pins_match_authoritative:
        reasons.append("accepted_read_is_not_current_census")
        proven_graph_nodes = []
    coverage_gap = _coverage_gap(
        binding=binding,
        scoped_ghv=scoped_ghv,
        ghosv=ghosv,
        unassigned=scope["unassigned"],
        pins_match_authoritative=pins_match_authoritative,
        proven_graph_nodes=proven_graph_nodes,
    )
    result = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": binding.get("status"),
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_identity": GUARDIAN_IDENTITY,
        "network_access": NETWORK_ACCESS,
        "repository_evidence_write": REPOSITORY_EVIDENCE_WRITE,
        "private_get_executed": PRIVATE_GET_EXECUTED,
        "post_executed": POST_EXECUTED,
        "state_write_executed": STATE_WRITE_EXECUTED,
        "causal_integrator_invoked": CAUSAL_INTEGRATOR_INVOKED,
        "domain_verification": DOMAIN_VERIFICATION,
        "current_census_proven": CURRENT_CENSUS_PROVEN,
        "h1_membership_complete": H1_MEMBERSHIP_COMPLETE,
        "historical_pins_rewritten": HISTORICAL_PINS_REWRITTEN,
        "coverage_gap": coverage_gap,
        "coverage_proof": COVERAGE_PROOF,
        "fail_closed": binding.get("status") != STATUS_ACCEPTED or coverage_gap,
        "reasons": _unique(reasons),
        "pin_integrity": recorded["pin_integrity"],
        "h1_paths": recorded["h1_paths"],
        "scope": scope,
        "admissible_nodes": list(recorded["admissible_nodes"]),
        "proven_graph_nodes": proven_graph_nodes,
        "evaluated_nodes": list(scoped_ghv.get("evaluated_nodes") or []),
        "manifest_slots": dict(manifest.get("tool_slots") or {}),
        "submitted_findings": findings,
        "pin_binding": binding,
        "manifest": manifest,
        "scoped_ghv": scoped_ghv,
        "ghosv": ghosv,
    }
    _assert_no_forbidden_keys(result)
    _assert_finding_categories(findings)
    return result


def _select_provenance(
    *,
    recorded_payload: Mapping[str, Any],
    supplied: Mapping[str, Any] | None,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
) -> tuple[dict[str, Any], list[str]]:
    """Keep recorded pins. A supplied current-shaped payload is not adopted."""
    if supplied is None:
        return dict(recorded_payload), []
    if not isinstance(supplied, Mapping):
        return {"census": {}, "landscape": {}, "graph": {}}, ["provenance_missing"]
    if _same_provenance(supplied, recorded_payload):
        return dict(recorded_payload), []
    if _matches_authoritative(
        supplied,
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
    ):
        return dict(recorded_payload), ["artificial_current_provenance_rejected"]
    if _missing_or_malformed(supplied):
        return _copy_provenance(supplied), ["provenance_missing"]
    return _copy_provenance(supplied), ["provenance_contradiction"]


def _read_recorded_provenance(root: Path) -> dict[str, Any]:
    reasons: list[str] = []
    census_document, census_reason = _read_json(root, CENSUS_RELATIVE)
    landscape_document, landscape_reason = _read_json(root, LANDSCAPE_RELATIVE)
    if census_reason:
        reasons.append(f"census_{census_reason}")
    if landscape_reason:
        reasons.append(f"landscape_{landscape_reason}")

    census_pin = _field(census_document, "source_baseline_head")
    landscape_commit = _field(landscape_document, "evidence_baseline_sha")
    landscape_tree = _field(landscape_document, "evidence_baseline_tree_sha")
    graph_pins: list[str | None] = []
    graph_census_revisions: list[str | None] = []
    graph_flags: list[bool | None] = []
    for relative in GRAPH_RELATIVES:
        document, reason = _read_json(root, relative)
        if reason:
            reasons.append(f"graph_{reason}:{relative}")
            graph_pins.append(None)
            graph_census_revisions.append(None)
            graph_flags.append(None)
            continue
        snapshot = document.get("code_snapshot") if isinstance(document, Mapping) else None
        snapshot = snapshot if isinstance(snapshot, Mapping) else {}
        graph_pins.append(_field(snapshot, "git_head"))
        graph_census_revisions.append(_field(snapshot, "census_revision"))
        flag = document.get("CURRENT_GRAPH_VERIFIED") if isinstance(document, Mapping) else None
        graph_flags.append(flag if isinstance(flag, bool) else None)

    present_pins = [pin for pin in graph_pins if isinstance(pin, str)]
    if len(graph_pins) != len(GRAPH_RELATIVES) or any(pin is None for pin in graph_pins):
        graph_pin = None
        reasons.append("graph_pin_missing")
    elif len(set(present_pins)) != 1:
        graph_pin = None
        reasons.append("graph_pin_conflict")
    else:
        graph_pin = present_pins[0]

    census_objects: list[dict[str, Any]] = []
    raw_objects = (
        census_document.get("census_objects") if isinstance(census_document, Mapping) else None
    )
    if isinstance(raw_objects, list):
        census_objects = [item for item in raw_objects if isinstance(item, dict)]
    h1_paths = {
        node: {
            "path": H1_PATH_BY_NODE[node],
            "path_present": _path_present(root, H1_PATH_BY_NODE[node]),
            "imported": False,
        }
        for node in H1_SCOPE_NODES
    }
    internal_conflict = bool(
        _is_sha(census_pin)
        and any(_is_sha(revision) and revision != census_pin for revision in graph_census_revisions)
    )
    if internal_conflict:
        reasons.append("census_pin_disagrees_with_graph_census_revision")
    payload = {
        "census": _role("pin", census_pin),
        "landscape": _landscape_role(landscape_commit, landscape_tree),
        "graph": _role("pin", graph_pin),
    }
    pin_integrity = {
        "census_pin": census_pin,
        "landscape_commit_pin": landscape_commit,
        "landscape_tree_pin": landscape_tree,
        "graph_pin": graph_pin,
        "graph_pins_observed": list(graph_pins),
        "graph_embedded_census_revisions": list(graph_census_revisions),
        "graph_current_flags_observed": list(graph_flags),
        "graph_current_flag_adopted": GRAPH_CURRENT_FLAG_ADOPTED,
        "internal_pin_conflict": internal_conflict,
        "historical_pins_rewritten": HISTORICAL_PINS_REWRITTEN,
    }
    return {
        "payload": payload,
        "reasons": reasons,
        "pin_integrity": pin_integrity,
        "h1_paths": h1_paths,
        "census_objects": census_objects,
        "census_objects_examined": len(census_objects),
    }


def _pins_match(
    integrity: Mapping[str, Any],
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
) -> bool:
    """Historical role pins do not become current by agreeing with each other."""
    if integrity.get("internal_pin_conflict") is True:
        return False
    return (
        integrity.get("census_pin") == authoritative_commit_sha
        and integrity.get("landscape_commit_pin") == authoritative_commit_sha
        and integrity.get("landscape_tree_pin") == authoritative_tree_sha
        and integrity.get("graph_pin") == authoritative_commit_sha
    )


def _admissible_nodes(
    census_objects: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Include a node only when its census object id is already PROVEN_CURRENT."""
    nodes: list[str] = []
    candidates: list[dict[str, Any]] = []
    for node in H1_SCOPE_NODES:
        matched = _matching_proven_object(census_objects, node, H1_PATH_BY_NODE[node])
        if matched is None:
            continue
        if str(matched.get("object_id") or "") != node:
            continue
        nodes.append(node)
        candidates.append(dict(matched))
    return nodes, candidates


def _matching_proven_object(
    census_objects: list[dict[str, Any]],
    node: str,
    path: str,
) -> dict[str, Any] | None:
    for obj in census_objects:
        if obj.get("epistemic_status") != PROVEN_CURRENT:
            continue
        if obj.get("current_status") != PROVEN_CURRENT:
            continue
        object_id = str(obj.get("object_id") or "")
        name = str(obj.get("name") or "")
        raw_paths = obj.get("paths")
        paths = [str(item) for item in raw_paths] if isinstance(raw_paths, list) else []
        if object_id == node or name == node or path in paths:
            return obj
    return None


def _scope(admissible_nodes: list[str]) -> dict[str, list[str]]:
    allowed = [node for node in H1_SCOPE_NODES if node in admissible_nodes]
    return {
        "allowed_nodes": allowed,
        "exclusions": [],
        "unassigned": [node for node in H1_SCOPE_NODES if node not in allowed],
    }


def _findings(recorded: Mapping[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    findings: list[dict[str, str]] = []
    refs: list[str] = []
    paths = recorded["h1_paths"]
    for node in H1_SCOPE_NODES:
        path_info = paths[node]
        relative = str(path_info["path"])
        if path_info["path_present"]:
            findings.append(
                _finding(
                    finding_id=f"{node.lower()}-path-presence",
                    category=PRESENCE_CATEGORY,
                    observed_state="PATH_PRESENT_MEMBERSHIP_NOT_PROVEN",
                    evidence_ref=relative,
                    affected_scope=node,
                )
            )
            refs.append(relative)
        findings.append(
            _finding(
                finding_id=f"{node.lower()}-proven-current-absent",
                category=ABSENCE_CATEGORY,
                observed_state="PROVEN_CURRENT_CENSUS_OBJECT_ABSENT",
                evidence_ref=CENSUS_RELATIVE,
                affected_scope=node,
            )
        )
    refs.append(CENSUS_RELATIVE)
    return findings, _unique(refs)


def _finding(
    *,
    finding_id: str,
    category: str,
    observed_state: str,
    evidence_ref: str,
    affected_scope: str,
) -> dict[str, str]:
    if category in FORBIDDEN_FINDING_CATEGORIES:
        raise RuntimeError("forbidden_finding_category")
    return {
        "finding_id": finding_id,
        "category": category,
        "observed_state": observed_state,
        "evidence_ref": evidence_ref,
        "affected_scope": affected_scope,
        "status": UNASSIGNED_FINDING_STATUS,
    }


def _proven_graph_nodes(evaluated: Any, admissible_nodes: list[str]) -> list[str]:
    if not isinstance(evaluated, list):
        return []
    allowed = set(admissible_nodes)
    return [str(node) for node in evaluated if str(node) in allowed]


def _coverage_gap(
    *,
    binding: Mapping[str, Any],
    scoped_ghv: Mapping[str, Any],
    ghosv: Mapping[str, Any],
    unassigned: list[str],
    pins_match_authoritative: bool,
    proven_graph_nodes: list[str],
) -> bool:
    if binding.get("status") != STATUS_ACCEPTED:
        return True
    if not pins_match_authoritative or unassigned or not proven_graph_nodes:
        return True
    return bool(scoped_ghv.get("coverage_gap") or ghosv.get("coverage_gap"))


def _read_json(root: Path, relative: str) -> tuple[Mapping[str, Any] | None, str | None]:
    path = _inside(root, relative)
    if path is None:
        return None, "path_rejected"
    if not path.is_file():
        return None, "missing"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "unreadable"
    if not isinstance(document, dict):
        return None, "not_object"
    return document, None


def _path_present(root: Path, relative: str) -> bool:
    path = _inside(root, relative)
    return path is not None and path.is_dir()


def _inside(root: Path, relative: str) -> Path | None:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def _field(document: Mapping[str, Any] | None, key: str) -> str | None:
    if not isinstance(document, Mapping):
        return None
    value = document.get(key)
    if isinstance(value, str):
        return value
    return None


def _role(field: str, value: str | None) -> dict[str, str]:
    if value is None:
        return {}
    return {field: value}


def _landscape_role(commit_pin: str | None, tree_pin: str | None) -> dict[str, str]:
    body: dict[str, str] = {}
    if commit_pin is not None:
        body["commit_pin"] = commit_pin
    if tree_pin is not None:
        body["tree_pin"] = tree_pin
    return body


def _matches_authoritative(
    provenance: Mapping[str, Any],
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
) -> bool:
    census = provenance.get("census")
    landscape = provenance.get("landscape")
    graph = provenance.get("graph")
    if not isinstance(census, Mapping) or not isinstance(landscape, Mapping):
        return False
    if not isinstance(graph, Mapping):
        return False
    return (
        census.get("pin") == authoritative_commit_sha
        and landscape.get("commit_pin") == authoritative_commit_sha
        and landscape.get("tree_pin") == authoritative_tree_sha
        and graph.get("pin") == authoritative_commit_sha
    )


def _missing_or_malformed(provenance: Mapping[str, Any]) -> bool:
    for role in ("census", "landscape", "graph"):
        body = provenance.get(role)
        if not isinstance(body, Mapping):
            return True
    census_pin = provenance["census"].get("pin")
    landscape = provenance["landscape"]
    graph_pin = provenance["graph"].get("pin")
    values = (
        census_pin,
        landscape.get("commit_pin"),
        landscape.get("tree_pin"),
        graph_pin,
    )
    return any(not _is_sha(value) for value in values)


def _same_provenance(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _copy_provenance(left) == _copy_provenance(right)


def _copy_provenance(provenance: Mapping[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for role, body in provenance.items():
        copied[str(role)] = dict(body) if isinstance(body, Mapping) else body
    return copied


def _is_sha(value: Any) -> bool:
    return isinstance(value, str) and _SHA40.fullmatch(value) is not None


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _assert_finding_categories(findings: list[dict[str, str]]) -> None:
    for finding in findings:
        if finding["category"] in FORBIDDEN_FINDING_CATEGORIES:
            raise RuntimeError("forbidden_finding_category")


def _assert_no_forbidden_keys(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            _assert_no_forbidden_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_forbidden_keys(item)
