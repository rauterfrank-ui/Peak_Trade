"""Slice 5. Technical call groups from proven calls. Functional layers stay unproven."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetTrackerV1
from scripts.ops.current_full_stack_semantic_explorer_v1.evidence_v1 import append_claim_v1


def _proven_pairs(claims: list[dict[str, Any]], predicate: str) -> list[tuple[str, str]]:
    return [
        (claim["subject"], claim["object"])
        for claim in claims
        if claim["predicate"] == predicate and claim["status"] == "PROVEN"
    ]


def _sccs(nodes: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    succ: dict[str, list[str]] = defaultdict(list)
    pred: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        succ[source].append(target)
        pred[target].append(source)
    for node in nodes:
        succ[node] = sorted(set(succ[node]))
        pred[node] = sorted(set(pred[node]))
    seen: set[str] = set()
    order: list[str] = []
    for start in nodes:
        if start in seen:
            continue
        stack: list[tuple[str, bool]] = [(start, False)]
        while stack:
            current, done = stack.pop()
            if done:
                order.append(current)
                continue
            if current in seen:
                continue
            seen.add(current)
            stack.append((current, True))
            for nxt in reversed(succ[current]):
                if nxt not in seen:
                    stack.append((nxt, False))
    seen.clear()
    components: list[list[str]] = []
    for start in reversed(order):
        if start in seen:
            continue
        stack_nodes = [start]
        group: list[str] = []
        while stack_nodes:
            current = stack_nodes.pop()
            if current in seen:
                continue
            seen.add(current)
            group.append(current)
            for nxt in pred[current]:
                if nxt not in seen:
                    stack_nodes.append(nxt)
        components.append(sorted(group))
    components.sort(key=lambda group: group[0])
    return components


def _group_id(members: list[str]) -> str:
    digest = hashlib.sha256("\n".join(members).encode("utf-8")).hexdigest()[:12]
    return f"call_group:{digest}"


def discover_layers_v1(
    commit_sha: str,
    prior: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    defined = [
        claim["subject"]
        for claim in prior
        if claim["predicate"] == "DEFINES" and claim["object"] in {"function", "method"}
    ]
    calls = _proven_pairs(prior, "CALLS")
    involved = sorted({node for edge in calls for node in edge})
    for subject in sorted(set(defined) - set(involved)):
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="layer",
            subject=subject,
            predicate="UNASSIGNED",
            object_="",
            evidence_refs=[subject],
            evidence_class="STATIC",
            status="UNPROVEN",
            unknowns=["NO_PROVEN_RELATIONSHIP"],
        )
    if not involved:
        return claims
    components = _sccs(involved, calls)
    owner = {member: _group_id(group) for group in components for member in group}
    signatures = {
        claim["subject"]: claim["object"]
        for claim in prior
        if claim["predicate"] == "HAS_SIGNATURE" and claim["status"] == "PROVEN"
    }
    returns = {claim["subject"]: claim for claim in prior if claim["predicate"] == "RETURNS"}
    incoming: dict[str, set[str]] = defaultdict(set)
    for source, target in calls:
        if owner.get(source) == owner.get(target):
            incoming[target].add(source)
    for group in components:
        group_id = _group_id(group)
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="functional_layer",
            subject=group_id,
            predicate="FUNCTIONAL_LAYER",
            object_="",
            evidence_refs=list(group),
            evidence_class="STATIC",
            status="UNPROVEN",
            unknowns=["NO_FUNCTIONAL_EVIDENCE"],
        )
        for member in group:
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="call_group",
                subject=group_id,
                predicate="CALL_GROUP_MEMBER",
                object_=member,
                evidence_refs=[member],
                evidence_class="STATIC",
                status="PROVEN",
                unknowns=["TECHNICAL_CALL_GROUP"],
            )
            if member not in incoming:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="call_group",
                    subject=group_id,
                    predicate="CALL_GROUP_INPUT",
                    object_=f"{member}:{signatures.get(member, '')}",
                    evidence_refs=[member],
                    evidence_class="STATIC",
                    status="PROVEN",
                    unknowns=["TECHNICAL_CALL_GROUP"],
                )
            returned = returns.get(member)
            if returned is None or returned["status"] != "PROVEN":
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="call_group",
                    subject=group_id,
                    predicate="CALL_GROUP_OUTPUT",
                    object_=member,
                    evidence_refs=[member],
                    evidence_class="STATIC",
                    status="UNPROVEN",
                    unknowns=["NO_RETURN_EVIDENCE", "TECHNICAL_CALL_GROUP"],
                )
            else:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="call_group",
                    subject=group_id,
                    predicate="CALL_GROUP_OUTPUT",
                    object_=f"{member}:{returned['object']}",
                    evidence_refs=[member],
                    evidence_class="STATIC",
                    status="PROVEN",
                    unknowns=["TECHNICAL_CALL_GROUP"],
                )
    seen_links: set[tuple[str, str]] = set()
    for source, target in calls:
        left = owner[source]
        right = owner[target]
        if left == right or (left, right) in seen_links:
            continue
        seen_links.add((left, right))
        if not tracker.allow_edge():
            break
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="call_group",
            subject=left,
            predicate="CALL_GROUP_LINK",
            object_=right,
            evidence_refs=[source, target],
            evidence_class="STATIC",
            status="PROVEN",
            unknowns=["TECHNICAL_CALL_GROUP"],
        )
    for claim in prior:
        if claim["status"] != "PROVEN":
            continue
        if claim["predicate"] not in {
            "READS_STATE",
            "WRITES_STATE",
            "PERSISTS",
            "EXTERNAL_EFFECT_SITE",
        }:
            continue
        group_id = owner.get(claim["subject"])
        if group_id is None:
            continue
        predicate = (
            "CALL_GROUP_STATE" if claim["predicate"].endswith("STATE") else "CALL_GROUP_EFFECT"
        )
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="call_group",
            subject=group_id,
            predicate=predicate,
            object_=f"{claim['subject']}:{claim['object']}",
            evidence_refs=list(claim["evidence_refs"]),
            evidence_class="STATIC",
            status="PROVEN",
            unknowns=[*claim["unknowns"], "TECHNICAL_CALL_GROUP"],
        )
    return claims
