"""Slice 4. Offline correlation against an existing capture. No runners."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetTrackerV1
from scripts.ops.current_full_stack_semantic_explorer_v1.evidence_v1 import (
    append_claim_v1,
    append_unbudgeted_claim_v1,
)


def correlate_runtime_v1(
    commit_sha: str,
    static_claims: list[dict[str, Any]],
    capture_path: Path | None,
    tracker: BudgetTrackerV1,
) -> tuple[list[dict[str, Any]], bytes | None]:
    claims: list[dict[str, Any]] = []
    if capture_path is None:
        append_unbudgeted_claim_v1(
            claims,
            commit_sha=commit_sha,
            scope="runtime",
            subject=commit_sha,
            predicate="RUNTIME_CAPTURE",
            object_="",
            evidence_refs=[],
            evidence_class="RUNTIME_OBSERVED",
            status="UNPROVEN",
            unknowns=["CAPTURE_NOT_SUPPLIED"],
        )
        return claims, None
    if not capture_path.is_file():
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=commit_sha,
            predicate="RUNTIME_CAPTURE",
            object_=str(capture_path),
            evidence_refs=[str(capture_path)],
            evidence_class="RUNTIME_OBSERVED",
            status="UNPROVEN",
            unknowns=["CAPTURE_ABSENT"],
        )
        return claims, None
    raw = capture_path.read_bytes()
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=commit_sha,
            predicate="RUNTIME_CAPTURE",
            object_=str(capture_path),
            evidence_refs=[str(capture_path)],
            evidence_class="RUNTIME_OBSERVED",
            status="UNPROVEN",
            unknowns=["CAPTURE_UNREADABLE"],
        )
        return claims, raw
    if not isinstance(document, dict):
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=commit_sha,
            predicate="RUNTIME_CAPTURE",
            object_=str(capture_path),
            evidence_refs=[str(capture_path)],
            evidence_class="RUNTIME_OBSERVED",
            status="UNPROVEN",
            unknowns=["PROVENANCE_INCOMPLETE"],
        )
        return claims, raw
    identity = document.get("identity")
    provenance = document.get("provenance")
    captured_sha = document.get("commit_sha")
    if (
        not isinstance(identity, str)
        or not isinstance(provenance, str)
        or not isinstance(captured_sha, str)
    ):
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=commit_sha,
            predicate="RUNTIME_CAPTURE",
            object_=str(capture_path),
            evidence_refs=[str(capture_path)],
            evidence_class="RUNTIME_OBSERVED",
            status="UNPROVEN",
            unknowns=["PROVENANCE_INCOMPLETE"],
        )
        return claims, raw
    if captured_sha != commit_sha:
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=identity,
            predicate="RUNTIME_CAPTURE",
            object_=captured_sha,
            evidence_refs=[str(capture_path)],
            evidence_class="RUNTIME_OBSERVED",
            status="UNPROVEN",
            unknowns=["REVISION_MISMATCH"],
        )
        return claims, raw
    observations = document.get("observations")
    if not isinstance(observations, list):
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=identity,
            predicate="RUNTIME_CAPTURE",
            object_=provenance,
            evidence_refs=[str(capture_path)],
            evidence_class="RUNTIME_OBSERVED",
            status="UNPROVEN",
            unknowns=["PROVENANCE_INCOMPLETE"],
        )
        return claims, raw
    static_index = {
        (claim["subject"], claim["predicate"], claim["object"]): claim["claim_id"]
        for claim in static_claims
        if claim["status"] == "PROVEN" and claim["evidence_class"] == "STATIC"
    }
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            continue
        subject = observation.get("subject")
        predicate = observation.get("predicate")
        object_ = observation.get("object")
        evidence_ref = observation.get("evidence_ref")
        if not all(isinstance(item, str) for item in (subject, predicate, object_, evidence_ref)):
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="runtime",
                subject=identity,
                predicate="RUNTIME_OBSERVES",
                object_=str(index),
                evidence_refs=[str(capture_path)],
                evidence_class="RUNTIME_OBSERVED",
                status="UNPROVEN",
                unknowns=["PROVENANCE_INCOMPLETE"],
            )
            continue
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=str(subject),
            predicate="RUNTIME_OBSERVES",
            object_=f"{predicate}:{object_}",
            evidence_refs=[str(evidence_ref)],
            evidence_class="RUNTIME_OBSERVED",
            status="PROVEN",
        )
        static_id = static_index.get((subject, predicate, object_))
        if static_id is None:
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="runtime",
                subject=str(subject),
                predicate="CORRELATES",
                object_=f"{predicate}:{object_}",
                evidence_refs=[str(evidence_ref)],
                evidence_class="RUNTIME_OBSERVED",
                status="UNPROVEN",
                unknowns=["NO_STATIC_COUNTERPART"],
            )
            continue
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="runtime",
            subject=str(subject),
            predicate="CORRELATES",
            object_=str(static_id),
            evidence_refs=[str(evidence_ref), str(static_id)],
            evidence_class="RUNTIME_OBSERVED",
            status="PROVEN",
            unknowns=["STATIC_NOT_UPGRADED"],
        )
    return claims, raw
