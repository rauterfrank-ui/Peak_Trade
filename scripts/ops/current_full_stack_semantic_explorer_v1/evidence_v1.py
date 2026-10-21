"""Canonical claim records. Identities depend only on claim content."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetTrackerV1
from scripts.ops.current_full_stack_semantic_explorer_v1.constants_v1 import (
    EVIDENCE_CLASSES,
    STATUSES,
)


def make_claim_v1(
    *,
    commit_sha: str,
    scope: str,
    subject: str,
    predicate: str,
    object_: str,
    evidence_refs: Sequence[str],
    evidence_class: str,
    status: str,
    unknowns: Sequence[str] = (),
) -> dict[str, Any]:
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError(f"EVIDENCE_CLASS_INVALID:{evidence_class}")
    if status not in STATUSES:
        raise ValueError(f"STATUS_INVALID:{status}")
    body: dict[str, Any] = {
        "commit_sha": commit_sha,
        "scope": scope,
        "subject": subject,
        "predicate": predicate,
        "object": object_,
        "evidence_refs": sorted(set(evidence_refs)),
        "evidence_class": evidence_class,
        "status": status,
        "unknowns": sorted(set(unknowns)),
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    body["claim_id"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return body


def append_unbudgeted_claim_v1(claims: list[dict[str, Any]], **kwargs: Any) -> None:
    """Record a mandatory unknown. A file budget must not drop it."""
    claims.append(make_claim_v1(**kwargs))


def append_claim_v1(
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
    **kwargs: Any,
) -> bool:
    if not tracker.allow_node():
        return False
    claims.append(make_claim_v1(**kwargs))
    return True


def claims_document_v1(claims: Sequence[Mapping[str, Any]]) -> str:
    ordered = sorted(claims, key=lambda item: str(item["claim_id"]))
    return json.dumps(list(ordered), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
