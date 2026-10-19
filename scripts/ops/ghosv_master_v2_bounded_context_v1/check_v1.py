"""Bounded Master V2 domain checker. No graph engine. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
from typing import Any

from scripts.ops.ghosv_master_v2_bounded_context_v1.constants_v1 import (
    AUTHORITY,
    CATALOG_VERSION,
    CONTRACT_DOCUMENT_PROVENANCE,
    CONTRACT_ID,
    CURRENT_CODE_PIN,
    CURRENT_TREE_PIN,
    CYCLE_SYMBOL,
    DECISION_OWNER_SYMBOL,
    EXECUTION_AUTHORITY,
    FORBIDDEN_AGGREGATE_KEYS,
    FULL_UNIVERSE_BOUNDARY_RATIFIED,
    GRAPH_ENGINE,
    GUARDIAN_IDENTITY,
    LIVE_GATE,
    NOT_TESTED_REQUIREMENTS,
    OWNER_SUBSTITUTE,
    PILOT_BASELINE_EDGE_COUNT,
    PILOT_BASELINE_EDGE_DIGEST,
    PILOT_MAX_DEPTH,
    PILOT_PROJECTED_EDGE_COUNT,
    PILOT_PROJECTED_NODE_COUNT,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCHEMA_ID,
    SCHEMA_VERSION,
    TRADING_AUTHORITY,
)
from scripts.ops.ghosv_master_v2_bounded_context_v1.findings_v1 import (
    canonical_sha256,
    make_finding_v1,
    sort_findings_v1,
)

_HEX = frozenset("0123456789abcdef")
_AUTHORITY_FIELDS = (
    "authority",
    "trading_authority",
    "safety_authority",
    "execution_authority",
)
_COLLAPSE_VALUES = frozenset({"RUNTIME_REACHABLE", "ACTIVE", "AUTHORIZED"})


def _hex40(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in _HEX for ch in value)


def _contract_reference_token(contract_reference: dict[str, Any]) -> str:
    return (
        f"{contract_reference.get('contract_id')}:{contract_reference.get('contract_text_sha256')}"
    )


def _contains_forbidden_key(value: Any, depth: int = 0) -> bool:
    if depth > 6:
        return False
    if isinstance(value, dict):
        if FORBIDDEN_AGGREGATE_KEYS.intersection(value):
            return True
        return any(_contains_forbidden_key(item, depth + 1) for item in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item, depth + 1) for item in value)
    return False


def _claims(adapter_report: dict[str, Any]) -> list[dict[str, Any]]:
    claims = adapter_report.get("submitted_claims", [])
    if claims is None:
        return []
    if not isinstance(claims, list):
        return []
    return [claim for claim in claims if isinstance(claim, dict)]


def _edge_type(edge: dict[str, Any]) -> str | None:
    if isinstance(edge.get("edge_type"), str):
        return edge["edge_type"]
    typed = edge.get("typed_edge")
    if isinstance(typed, dict) and isinstance(typed.get("edge_type"), str):
        return typed["edge_type"]
    return None


def _owner_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for edge in edges:
        if _edge_type(edge) != "CALLS":
            continue
        source = edge.get("symbol") or edge.get("source_symbol")
        if source == CYCLE_SYMBOL and edge.get("target_symbol") == DECISION_OWNER_SYMBOL:
            found.append(edge)
    return found


def _source_reference(edge: dict[str, Any]) -> str:
    source_file = edge.get("file") or edge.get("source_file") or ""
    target_file = edge.get("target_file") or ""
    lines = edge.get("call_lines") or []
    line = f"#L{lines[0]}" if lines else ""
    return (
        f"{source_file}::{edge.get('symbol') or edge.get('source_symbol')}"
        f"{line}->{target_file}::{edge.get('target_symbol')}"
    )


def _pilot_bound(
    adapter_report: dict[str, Any], baseline_digest: str, projection: dict[str, Any]
) -> bool:
    nodes = projection.get("nodes")
    edges = projection.get("edges")
    baseline_edges = adapter_report.get("edges")
    return (
        baseline_digest == PILOT_BASELINE_EDGE_DIGEST
        and adapter_report.get("baseline_edge_count") == PILOT_BASELINE_EDGE_COUNT
        and isinstance(baseline_edges, list)
        and len(baseline_edges) == PILOT_BASELINE_EDGE_COUNT
        and projection.get("edge_count") == PILOT_PROJECTED_EDGE_COUNT
        and isinstance(edges, list)
        and len(edges) == PILOT_PROJECTED_EDGE_COUNT
        and projection.get("node_count") == PILOT_PROJECTED_NODE_COUNT
        and isinstance(nodes, list)
        and len(nodes) == PILOT_PROJECTED_NODE_COUNT
    )


def _result(
    *,
    current_sha: str,
    current_tree: str,
    contract_text_sha256: str | None,
    baseline_digest: str | None,
    projection_digest: str | None,
    findings: list[dict[str, Any]],
    reaction: str | None,
    reaction_detail: str | None,
) -> dict[str, Any]:
    reproof_payload = {
        "schema_version": SCHEMA_VERSION,
        "current_sha": current_sha,
        "current_tree": current_tree,
        "contract_id": CONTRACT_ID,
        "contract_text_sha256": contract_text_sha256,
        "baseline_digest": baseline_digest,
        "projection_digest": projection_digest,
        "catalog_version": CATALOG_VERSION,
    }
    reproof_key = None
    if all(value not in (None, "") for value in reproof_payload.values()):
        reproof_key = canonical_sha256(reproof_payload)
    return {
        "contract_id": CONTRACT_ID,
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "catalog_version": CATALOG_VERSION,
        "domain": "MASTER_V2",
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_identity": GUARDIAN_IDENTITY,
        "graph_engine": GRAPH_ENGINE,
        "live_gate": LIVE_GATE,
        "owner_substitute": OWNER_SUBSTITUTE,
        "full_universe_boundary_ratified": FULL_UNIVERSE_BOUNDARY_RATIFIED,
        "execution_ghosv": "NOT_APPLICABLE",
        "execution_ghosv_invoked": False,
        "current_causal_graph": "NOT_MATERIALIZED",
        "causal_graph_consulted": False,
        "active": "NOT_PROVEN",
        "universe_membership": "NOT_CLAIMED",
        "reaction": reaction,
        "reaction_detail": reaction_detail,
        "reproof_key": reproof_key,
        "findings": sort_findings_v1(findings),
    }


def _rejection(
    *,
    reaction: str,
    reaction_detail: str | None,
    current_sha: str,
    current_tree: str,
    contract_reference: str,
    authority_effect: str = "NOT_ASSESSED",
    contract_text_sha256: str | None = None,
    baseline_digest: str | None = None,
    projection_digest: str | None = None,
) -> dict[str, Any]:
    finding = make_finding_v1(
        requirement_id="INPUT-POLICY",
        finding_type=reaction,
        current_sha=current_sha or "",
        current_tree=current_tree or "",
        source_reference=f"INPUT:{reaction}",
        contract_reference=contract_reference,
        check_id=f"INPUT-{reaction}",
        evidence_status="NOT_PROVEN",
        coverage_status="NOT_TESTED",
        uncertainty=reaction_detail or reaction,
        authority_effect=authority_effect,
        safety_effect="CLAIM_REJECTED" if authority_effect == "CLAIM_REJECTED" else "EFFECT_UNREAD",
        capital_effect="EFFECT_UNREAD",
        boundary_classification="UNKNOWN_MEMBERSHIP",
        foreign_finding_reference=None,
        conflict_status="NONE",
        owner_go_required=True,
    )
    return _result(
        current_sha=current_sha or "",
        current_tree=current_tree or "",
        contract_text_sha256=contract_text_sha256,
        baseline_digest=baseline_digest,
        projection_digest=projection_digest,
        findings=[finding],
        reaction=reaction,
        reaction_detail=reaction_detail,
    )


def _not_tested_findings(
    *,
    current_sha: str,
    current_tree: str,
    contract_reference: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for requirement_id in NOT_TESTED_REQUIREMENTS:
        findings.append(
            make_finding_v1(
                requirement_id=requirement_id,
                finding_type="NOT_TESTED",
                current_sha=current_sha,
                current_tree=current_tree,
                source_reference=f"CATALOG:{requirement_id}",
                contract_reference=contract_reference,
                check_id=f"{requirement_id}-NOT-TESTED",
                evidence_status="NOT_TESTED",
                coverage_status="NOT_TESTED",
                uncertainty="DOMAIN_CHECK_NOT_IN_BOUNDED_SLICE",
                authority_effect="NOT_ASSESSED",
                safety_effect="EFFECT_UNREAD",
                capital_effect="EFFECT_UNREAD",
                boundary_classification="UNKNOWN_MEMBERSHIP",
                foreign_finding_reference=None,
                conflict_status="NONE",
                owner_go_required=True,
            )
        )
    return findings


def run_ghosv_master_v2_bounded_context_v1(
    *,
    current_sha: str | None,
    current_tree: str | None,
    adapter_report: dict[str, Any] | None,
    contract_reference: dict[str, Any] | None,
    owner_rules: dict[str, Any] | None,
    runtime_evidence: dict[str, Any] | None = None,
    foreign_findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    token = "ABSENT"
    if isinstance(contract_reference, dict):
        token = _contract_reference_token(contract_reference)
    sha = current_sha or ""
    tree = current_tree or ""
    if (
        not isinstance(current_sha, str)
        or not isinstance(current_tree, str)
        or not isinstance(adapter_report, dict)
        or not isinstance(contract_reference, dict)
        or not isinstance(owner_rules, dict)
    ):
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="REQUIRED_INPUT_ABSENT",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
        )
    required_report = ("current_sha", "current_tree", "edges", "baseline_edge_digest_sha256")
    required_contract = (
        "contract_id",
        "contract_text",
        "contract_text_sha256",
        "document_provenance",
        "current_code_pin",
    )
    required_rules = (
        "owner_lock",
        "authority",
        "trading_authority",
        "safety_authority",
        "execution_authority",
    )
    if (
        any(adapter_report.get(key) in (None, "") for key in required_report)
        or any(contract_reference.get(key) in (None, "") for key in required_contract)
        or any(owner_rules.get(key) in (None, "") for key in required_rules)
        or not isinstance(adapter_report.get("edges"), list)
    ):
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="REQUIRED_FIELD_ABSENT",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
        )
    if not _hex40(current_sha) or not _hex40(current_tree):
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="OBJECT_ID_MALFORMED",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
        )
    text = contract_reference.get("contract_text")
    supplied_hash = contract_reference.get("contract_text_sha256")
    text_hash = (
        hashlib.sha256(text.encode("utf-8")).hexdigest() if isinstance(text, str) and text else None
    )
    if not isinstance(text, str) or not text or text_hash != supplied_hash:
        return _rejection(
            reaction="CONTRACT_TEXT_NOT_VERIFIED",
            reaction_detail="CONTRACT_TEXT_HASH_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=supplied_hash if isinstance(supplied_hash, str) else None,
        )
    if (
        contract_reference.get("document_provenance") == contract_reference.get("current_code_pin")
        or contract_reference.get("document_provenance") != CONTRACT_DOCUMENT_PROVENANCE
        or contract_reference.get("current_code_pin") != CURRENT_CODE_PIN
        or contract_reference.get("contract_id") != CONTRACT_ID
    ):
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="CONTRACT_PROVENANCE_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
        )
    if current_sha != CURRENT_CODE_PIN or adapter_report.get("current_sha") != current_sha:
        return _rejection(
            reaction="SHA_MISMATCH",
            reaction_detail="CURRENT_SHA_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
        )
    if current_tree != CURRENT_TREE_PIN or adapter_report.get("current_tree") != current_tree:
        return _rejection(
            reaction="TREE_MISMATCH",
            reaction_detail="CURRENT_TREE_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
        )
    baseline_edges = adapter_report["edges"]
    baseline_digest = canonical_sha256(baseline_edges)
    if adapter_report.get("baseline_edge_digest_sha256") != baseline_digest:
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="BASELINE_DIGEST_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
        )
    if adapter_report.get("baseline_edge_count") != len(baseline_edges):
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="BASELINE_COUNT_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
        )
    projection = adapter_report.get("ghv_projection")
    if not isinstance(projection, dict) or not isinstance(projection.get("edges"), list):
        return _rejection(
            reaction="REQUIRED_TOOL_ABSENT",
            reaction_detail="GHV_PROJECTION_ABSENT",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
        )
    projected_edges = projection["edges"]
    projected_nodes = projection.get("nodes")
    projection_digest = canonical_sha256(
        {
            "edges": projected_edges,
            "nodes": projected_nodes if isinstance(projected_nodes, list) else [],
        }
    )
    if projection.get("projection_digest_sha256") not in (None, projection_digest):
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="PROJECTION_DIGEST_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if projection.get("edge_count") != len(projected_edges) or (
        isinstance(projected_nodes, list)
        and projection.get("node_count") not in (None, len(projected_nodes))
    ):
        return _rejection(
            reaction="PROVENANCE_ABSENT",
            reaction_detail="PROJECTION_COUNT_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if owner_rules.get("write_requested") is True:
        return _rejection(
            reaction="WRITE_REJECTED",
            reaction_detail="WRITE_NOT_PERFORMED",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if owner_rules.get("post_requested") is True:
        return _rejection(
            reaction="POST_REJECTED",
            reaction_detail="POST_NOT_PERFORMED",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if owner_rules.get("productive_import_requested") is True:
        return _rejection(
            reaction="PRODUCTIVE_IMPORT_REJECTED",
            reaction_detail="PRODUCTIVE_IMPORT_NOT_PERFORMED",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if (
        _contains_forbidden_key(adapter_report)
        or _contains_forbidden_key(owner_rules)
        or _contains_forbidden_key(contract_reference)
    ):
        return _rejection(
            reaction="OVERALL_PASS_FORBIDDEN",
            reaction_detail="AGGREGATE_PASS_KEY_PRESENT",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if any(owner_rules.get(field) != "NONE" for field in _AUTHORITY_FIELDS):
        return _rejection(
            reaction="AUTHORITY_CLAIM_REJECTED",
            reaction_detail="AUTHORITY_GRANT_REJECTED",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            authority_effect="CLAIM_REJECTED",
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if (
        owner_rules.get("owner_lock") != "LEVEL_3"
        or owner_rules.get("lock_mutation_requested") is True
    ):
        return _rejection(
            reaction="OWNER_LOCK_VIOLATION",
            reaction_detail="LOCK_LEVEL_3_HOLDS",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    requested_depth = projection.get("max_depth_enforced")
    if requested_depth != PILOT_MAX_DEPTH or adapter_report.get("requested_depth") not in (
        None,
        PILOT_MAX_DEPTH,
    ):
        return _rejection(
            reaction="DEPTH_NOT_AUTHORIZED",
            reaction_detail="PILOT_DEPTH_EXCEEDED",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    claims = _claims(adapter_report)
    capture_sha = (
        None if not isinstance(runtime_evidence, dict) else runtime_evidence.get("capture_sha")
    )
    writer = None if not isinstance(runtime_evidence, dict) else runtime_evidence.get("writer")
    for claim in claims:
        claim_type = claim.get("type")
        if claim_type == "ACTIVE" and capture_sha != current_sha:
            return _rejection(
                reaction="ACTIVE_WITHOUT_CAPTURE",
                reaction_detail="ACTIVE_NOT_PROVEN",
                current_sha=sha,
                current_tree=tree,
                contract_reference=token,
                contract_text_sha256=text_hash,
                baseline_digest=baseline_digest,
                projection_digest=projection_digest,
            )
        if claim_type == "GRAPH_NEIGHBORHOOD_IS" and claim.get("value") in _COLLAPSE_VALUES:
            return _rejection(
                reaction="RUNTIME_STAGE_COLLAPSE",
                reaction_detail="GRAPH_NEIGHBORHOOD_IS_NOT_RUNTIME",
                current_sha=sha,
                current_tree=tree,
                contract_reference=token,
                authority_effect="CLAIM_REJECTED",
                contract_text_sha256=text_hash,
                baseline_digest=baseline_digest,
                projection_digest=projection_digest,
            )
        if claim_type == "PERSISTS" and not writer:
            return _rejection(
                reaction="PERSISTENCE_EVIDENCE_ABSENT",
                reaction_detail="WRITER_ABSENT",
                current_sha=sha,
                current_tree=tree,
                contract_reference=token,
                contract_text_sha256=text_hash,
                baseline_digest=baseline_digest,
                projection_digest=projection_digest,
            )
        if claim_type == "MEMBERSHIP":
            return _rejection(
                reaction="UNKNOWN_MEMBERSHIP",
                reaction_detail="MEMBERSHIP_NOT_DERIVED",
                current_sha=sha,
                current_tree=tree,
                contract_reference=token,
                contract_text_sha256=text_hash,
                baseline_digest=baseline_digest,
                projection_digest=projection_digest,
            )
        if claim_type == "RESOLVED_DYNAMIC_EDGE":
            unresolved = adapter_report.get("unresolved_dynamic_bindings") or []
            if unresolved:
                return _rejection(
                    reaction="UNRESOLVED_DYNAMIC_BINDING",
                    reaction_detail="DYNAMIC_BINDING_NOT_PROMOTED",
                    current_sha=sha,
                    current_tree=tree,
                    contract_reference=token,
                    contract_text_sha256=text_hash,
                    baseline_digest=baseline_digest,
                    projection_digest=projection_digest,
                )
    matches = _owner_edges(baseline_edges)
    if len(matches) != 1:
        return _rejection(
            reaction="DECISION_OWNER_MISMATCH",
            reaction_detail="DIRECT_CALL_ABSENT_OR_AMBIGUOUS",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    owner_edge = matches[0]
    if (
        owner_edge.get("current_sha") != current_sha
        or owner_edge.get("current_tree") != current_tree
    ):
        return _rejection(
            reaction="DECISION_OWNER_MISMATCH",
            reaction_detail="EDGE_PROVENANCE_MISMATCH",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    if (
        projection.get("trading_authority_implied") is not False
        or projection.get("graph_neighborhood_is_runtime_reachability") is not False
    ):
        return _rejection(
            reaction="RUNTIME_STAGE_COLLAPSE",
            reaction_detail="PROJECTION_AUTHORITY_OR_REACHABILITY_FLAG",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            authority_effect="CLAIM_REJECTED",
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    pilot = _pilot_bound(adapter_report, baseline_digest, projection)
    owner_status = "PROVEN" if pilot else "PARTIAL"
    graph_status = "PROVEN" if pilot else "PARTIAL"
    uncertainty_owner = (
        "DIRECT_CALL_ONLY;NOT_EXCLUSIVE_OWNER;ACTIVE_NOT_PROVEN;UNIVERSE_NOT_CLAIMED"
        if pilot
        else "DIRECT_CALL_ONLY;PILOT_DIGEST_NOT_BOUND;ACTIVE_NOT_PROVEN;UNIVERSE_NOT_CLAIMED"
    )
    uncertainty_graph = (
        "MAX_DEPTH_1_IS_PILOT_LIMIT;GRAPH_NEIGHBORHOOD_IS_NOT_RUNTIME"
        if pilot
        else "MAX_DEPTH_1_IS_PILOT_LIMIT;PILOT_COUNT_NOT_BOUND;GRAPH_NEIGHBORHOOD_IS_NOT_RUNTIME"
    )
    findings = [
        make_finding_v1(
            requirement_id="MV2-01",
            finding_type="DECLARED_DECISION_OWNER_WIRED",
            current_sha=sha,
            current_tree=tree,
            source_reference=_source_reference(owner_edge),
            contract_reference=token,
            check_id="MV2-01-DECISION-OWNER",
            evidence_status=owner_status,
            coverage_status="PARTIAL",
            uncertainty=uncertainty_owner,
            authority_effect="NONE",
            safety_effect="NOT_INTERPRETED",
            capital_effect="NOT_INTERPRETED",
            boundary_classification="UNKNOWN_MEMBERSHIP",
            foreign_finding_reference=None,
            conflict_status="NONE",
            owner_go_required=False,
        ),
        make_finding_v1(
            requirement_id="MV2-09",
            finding_type="GRAPH_NEIGHBORHOOD_NOT_RUNTIME",
            current_sha=sha,
            current_tree=tree,
            source_reference="GHV_PROJECTION:max_depth=1",
            contract_reference=token,
            check_id="MV2-09-GRAPH-NEIGHBORHOOD",
            evidence_status=graph_status,
            coverage_status="PARTIAL",
            uncertainty=uncertainty_graph,
            authority_effect="NONE",
            safety_effect="NOT_INTERPRETED",
            capital_effect="NOT_INTERPRETED",
            boundary_classification="UNKNOWN_MEMBERSHIP",
            foreign_finding_reference=None,
            conflict_status="NONE",
            owner_go_required=False,
        ),
        make_finding_v1(
            requirement_id="MV2-10",
            finding_type="NO_OVERALL_PASS",
            current_sha=sha,
            current_tree=tree,
            source_reference="OUTPUT:AGGREGATE_PASS_ABSENT",
            contract_reference=token,
            check_id="MV2-10-NO-OVERALL-PASS",
            evidence_status="PROVEN",
            coverage_status="PARTIAL",
            uncertainty="NO_AGGREGATE_STATUS",
            authority_effect="NONE",
            safety_effect="NOT_INTERPRETED",
            capital_effect="NOT_INTERPRETED",
            boundary_classification="UNKNOWN_MEMBERSHIP",
            foreign_finding_reference=None,
            conflict_status="NONE",
            owner_go_required=False,
        ),
        *_not_tested_findings(current_sha=sha, current_tree=tree, contract_reference=token),
    ]
    reaction = None
    reaction_detail = None
    supplied_foreign = foreign_findings or []
    topics: dict[str, str] = {}
    conflict_reference = None
    for foreign in supplied_foreign:
        if not isinstance(foreign, dict):
            continue
        topic = foreign.get("topic")
        text_value = foreign.get("text")
        if isinstance(topic, str) and isinstance(text_value, str):
            previous = topics.get(topic)
            if previous is not None and previous != text_value:
                conflict_reference = canonical_sha256(foreign)
                reaction = "CONFLICT_OPEN"
                reaction_detail = "FOREIGN_FINDINGS_CONTRADICT"
            topics[topic] = text_value
        conflicts_with = foreign.get("conflicts_with")
        if isinstance(conflicts_with, str):
            conflict_reference = canonical_sha256(foreign)
            reaction = "CONFLICT_OPEN"
            reaction_detail = "FOREIGN_FINDING_CONTRADICTS_LOCAL"
            for finding in findings:
                if finding["requirement_id"] == conflicts_with:
                    finding["conflict_status"] = "CONFLICT_OPEN"
                    finding["foreign_finding_reference"] = conflict_reference
    if reaction == "CONFLICT_OPEN":
        findings.append(
            make_finding_v1(
                requirement_id="INPUT-POLICY",
                finding_type="CONFLICT_OPEN",
                current_sha=sha,
                current_tree=tree,
                source_reference="FOREIGN:CONTRADICTION",
                contract_reference=token,
                check_id="INPUT-CONFLICT-OPEN",
                evidence_status="UNRESOLVED",
                coverage_status="PARTIAL",
                uncertainty="FOREIGN_TEXT_RETAINED",
                authority_effect="NOT_ASSESSED",
                safety_effect="NOT_INTERPRETED",
                capital_effect="NOT_INTERPRETED",
                boundary_classification="SEMANTIC_UNRESOLVED",
                foreign_finding_reference=conflict_reference,
                conflict_status="CONFLICT_OPEN",
                owner_go_required=True,
            )
        )
    result = _result(
        current_sha=sha,
        current_tree=tree,
        contract_text_sha256=text_hash,
        baseline_digest=baseline_digest,
        projection_digest=projection_digest,
        findings=findings,
        reaction=reaction,
        reaction_detail=reaction_detail,
    )
    if _contains_forbidden_key(result):
        return _rejection(
            reaction="OVERALL_PASS_FORBIDDEN",
            reaction_detail="OUTPUT_AGGREGATE_PASS",
            current_sha=sha,
            current_tree=tree,
            contract_reference=token,
            contract_text_sha256=text_hash,
            baseline_digest=baseline_digest,
            projection_digest=projection_digest,
        )
    return result


def assess_reproof_v1(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    previous_ids = [item["finding_id"] for item in previous.get("findings", [])]
    current_ids = [item["finding_id"] for item in current.get("findings", [])]
    if previous.get("reproof_key") != current.get("reproof_key"):
        reaction = "REPROOF_DELTA"
    elif previous_ids != current_ids:
        reaction = "TOOL_NONDETERMINISM"
    else:
        reaction = "REPROOF_MATCH"
    return {
        "reaction": reaction,
        "previous_retained": True,
        "previous_finding_ids": previous_ids,
    }
