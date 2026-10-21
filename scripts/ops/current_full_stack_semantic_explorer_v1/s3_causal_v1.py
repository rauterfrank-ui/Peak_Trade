"""Slice 3. Chains and authority only where evidence agrees."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetTrackerV1
from scripts.ops.current_full_stack_semantic_explorer_v1.constants_v1 import AUTHORITY_FIELDS
from scripts.ops.current_full_stack_semantic_explorer_v1.evidence_v1 import (
    append_claim_v1,
    append_unbudgeted_claim_v1,
)


def _proven(claims: list[dict[str, Any]], predicate: str) -> list[dict[str, Any]]:
    return [
        claim for claim in claims if claim["predicate"] == predicate and claim["status"] == "PROVEN"
    ]


def _add_edge(
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
    **kwargs: Any,
) -> bool:
    if not tracker.allow_edge():
        reason = "TIME_BUDGET" if tracker.time_closed else "EDGE_BUDGET"
        blocked = dict(kwargs)
        blocked["status"] = "UNPROVEN"
        unknowns = list(blocked.get("unknowns", []))
        unknowns.extend([reason, "INCOMPLETE"])
        blocked["unknowns"] = unknowns
        append_unbudgeted_claim_v1(claims, **blocked)
        return False
    return append_claim_v1(claims, tracker, **kwargs)


def reconstruct_causal_v1(
    census: dict[str, Any],
    prior: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    commit_sha = str(census["commit_sha"])
    claims: list[dict[str, Any]] = []
    calls = [(claim["subject"], claim["object"]) for claim in _proven(prior, "CALLS")]
    imports = [(claim["subject"], claim["object"]) for claim in _proven(prior, "IMPORT_TARGET")]
    edge_stopped = False
    for source, target in sorted(set(calls + imports)):
        if not _add_edge(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="causal",
            subject=source,
            predicate="DEPENDS_ON",
            object_=target,
            evidence_refs=[claim_ref(prior, source, target)],
            evidence_class="STATIC",
            status="PROVEN",
        ):
            edge_stopped = True
            break
    depth_truncated = False
    if not edge_stopped:
        depth_truncated = _transitive(
            commit_sha, calls, tracker.budget.max_depth, claims, tracker, prior
        )
        _effect_chains(commit_sha, calls, prior, claims, tracker)
    if tracker.edge_closed:
        edge_stopped = True
    _authority(commit_sha, census, claims, tracker)
    return claims, {"depth_truncated": depth_truncated, "edge_stopped": edge_stopped}


def claim_ref(prior: list[dict[str, Any]], source: str, target: str) -> str:
    for claim in prior:
        if claim["subject"] == source and claim["object"] == target and claim["status"] == "PROVEN":
            refs = claim["evidence_refs"]
            if refs:
                return str(refs[0])
    return source


def _transitive(
    commit_sha: str,
    calls: list[tuple[str, str]],
    max_depth: int,
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
    prior: list[dict[str, Any]],
) -> bool:
    truncated = False
    succ: dict[str, list[str]] = defaultdict(list)
    for source, target in calls:
        succ[source].append(target)
    for source in succ:
        succ[source] = sorted(set(succ[source]))
    for origin in sorted(succ):
        queue: list[tuple[str, list[str]]] = [(origin, [origin])]
        seen = {origin}
        while queue:
            node, path = queue.pop(0)
            if len(path) - 1 >= max_depth:
                for nxt in succ.get(node, []):
                    if nxt in seen:
                        continue
                    seen.add(nxt)
                    append_unbudgeted_claim_v1(
                        claims,
                        commit_sha=commit_sha,
                        scope="causal",
                        subject=origin,
                        predicate="TRANSITIVE_DEPENDS_ON",
                        object_=nxt,
                        evidence_refs=[">".join([*path, nxt])],
                        evidence_class="STATIC",
                        status="UNPROVEN",
                        unknowns=["DEPTH_LIMIT", "INCOMPLETE"],
                    )
                    truncated = True
                continue
            for nxt in succ.get(node, []):
                if nxt in seen:
                    continue
                seen.add(nxt)
                extended = [*path, nxt]
                if len(extended) >= 3:
                    if not _add_edge(
                        claims,
                        tracker,
                        commit_sha=commit_sha,
                        scope="causal",
                        subject=origin,
                        predicate="TRANSITIVE_DEPENDS_ON",
                        object_=nxt,
                        evidence_refs=[">".join(extended)],
                        evidence_class="STATIC",
                        status="PROVEN",
                    ):
                        return truncated
                    if not _add_edge(
                        claims,
                        tracker,
                        commit_sha=commit_sha,
                        scope="causal",
                        subject=origin,
                        predicate="CONTROL_CHAIN",
                        object_=">".join(extended),
                        evidence_refs=[">".join(extended)],
                        evidence_class="STATIC",
                        status="PROVEN",
                    ):
                        return truncated
                queue.append((nxt, extended))
    return truncated


def _effect_chains(
    commit_sha: str,
    calls: list[tuple[str, str]],
    prior: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> None:
    writes = {claim["subject"]: claim["object"] for claim in _proven(prior, "WRITES_STATE")}
    persists = {claim["subject"]: claim["object"] for claim in _proven(prior, "PERSISTS")}
    effects = {
        claim["subject"]: claim["object"] for claim in _proven(prior, "EXTERNAL_EFFECT_SITE")
    }
    for source, target in sorted(set(calls)):
        if target in writes:
            _add_edge(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="causal",
                subject=source,
                predicate="STATE_CHAIN",
                object_=f"{target}:{writes[target]}",
                evidence_refs=[source, target],
                evidence_class="STATIC",
                status="PROVEN",
            )
        if target in persists:
            _add_edge(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="causal",
                subject=source,
                predicate="PERSISTENCE_CHAIN",
                object_=f"{target}:{persists[target]}",
                evidence_refs=[source, target],
                evidence_class="STATIC",
                status="PROVEN",
            )
        if target in effects:
            _add_edge(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="causal",
                subject=source,
                predicate="EXTERNAL_EFFECT_CHAIN",
                object_=f"{target}:{effects[target]}",
                evidence_refs=[source, target],
                evidence_class="STATIC",
                status="PROVEN",
                unknowns=["NOT_RUNTIME_OBSERVED"],
            )


def _authority(
    commit_sha: str,
    census: dict[str, Any],
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> None:
    by_subject: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for path, document in census["contracts"].items():
        subject = document.get("subject")
        if isinstance(subject, str):
            by_subject[subject].append((path, document))
    modules: dict[str, Any] = census["modules"]
    subjects = sorted(set(modules) | set(by_subject))
    for subject in subjects:
        code = modules.get(subject, {}).get("authority", {})
        documents = by_subject.get(subject, [])
        for field, predicate in AUTHORITY_FIELDS.items():
            code_item = code.get(field)
            contract_values = []
            contract_refs = []
            for path, document in documents:
                if field in document and isinstance(document[field], str):
                    contract_values.append(document[field])
                    contract_refs.append(path)
            agreed = len(set(contract_values)) == 1
            if (
                code_item
                and contract_values
                and agreed
                and code_item["value"] == contract_values[0]
            ):
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="authority",
                    subject=subject,
                    predicate=predicate,
                    object_=str(code_item["value"]),
                    evidence_refs=[f"{subject}:{code_item['lineno']}", *contract_refs],
                    evidence_class="CONTRACT",
                    status="PROVEN",
                )
                continue
            unknowns = []
            if code_item and not contract_values:
                unknowns.append("CODE_WITHOUT_CONTRACT")
            if contract_values and not code_item:
                unknowns.append("CONTRACT_WITHOUT_CODE")
            if (
                code_item
                and contract_values
                and (not agreed or code_item["value"] != contract_values[0])
            ):
                unknowns.append("CONTRADICTION")
            if not unknowns:
                continue
            refs = []
            if code_item:
                refs.append(f"{subject}:{code_item['lineno']}")
            refs.extend(contract_refs)
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="authority",
                subject=subject,
                predicate=predicate,
                object_=str(code_item["value"]) if code_item else str(contract_values[0]),
                evidence_refs=refs,
                evidence_class="CONTRACT" if contract_refs else "STATIC",
                status="UNPROVEN",
                unknowns=unknowns,
            )
