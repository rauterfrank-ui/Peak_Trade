"""Run S1–S5 for one declared commit. The tool performs no external effects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import (
    BudgetTrackerV1,
    BudgetV1,
    slice_status_v1,
)
from scripts.ops.current_full_stack_semantic_explorer_v1.cache_v1 import (
    fingerprint_v1,
    load_run_cache_v1,
    store_run_cache_v1,
)
from scripts.ops.current_full_stack_semantic_explorer_v1.constants_v1 import (
    AUTHORITY_PREDICATES,
    EXTERNAL_EFFECTS_PERFORMED,
    SCHEMA_ID,
    TOOL_AUTHORITY,
)
from scripts.ops.current_full_stack_semantic_explorer_v1.git_objects_v1 import (
    list_entries_v1,
    resolve_commit_v1,
)
from scripts.ops.current_full_stack_semantic_explorer_v1.s1_physical_v1 import discover_physical_v1
from scripts.ops.current_full_stack_semantic_explorer_v1.s2_semantic_v1 import extract_semantic_v1
from scripts.ops.current_full_stack_semantic_explorer_v1.s3_causal_v1 import reconstruct_causal_v1
from scripts.ops.current_full_stack_semantic_explorer_v1.s4_runtime_v1 import correlate_runtime_v1
from scripts.ops.current_full_stack_semantic_explorer_v1.s5_layers_v1 import discover_layers_v1


def _sorted_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(claims, key=lambda item: str(item["claim_id"]))


def _audit(claims: list[dict[str, Any]]) -> bool:
    for claim in claims:
        if claim["status"] == "PROVEN" and claim["predicate"] == "DYNAMIC_TARGET":
            return False
        if claim["status"] == "PROVEN" and claim["predicate"] == "FUNCTIONAL_LAYER":
            return False
        if claim["status"] != "PROVEN" or claim["predicate"] not in AUTHORITY_PREDICATES:
            continue
        refs = claim["evidence_refs"]
        has_code = any(".py:" in ref for ref in refs)
        has_contract = any(ref.endswith(".json") for ref in refs)
        if not (has_code and has_contract):
            return False
    return True


def _slice(slice_id: str, status: str, claims: list[dict[str, Any]]) -> dict[str, Any]:
    return {"slice_id": slice_id, "status": status, "claims": _sorted_claims(claims)}


def _run_status(slices: list[dict[str, Any]]) -> str:
    statuses = {item["status"] for item in slices}
    if "FAIL" in statuses:
        return "FAIL"
    if "INCOMPLETE" in statuses:
        return "INCOMPLETE"
    return "PASS"


def run_explorer_v1(
    repo: Path | str,
    commit: str,
    *,
    capture_path: Path | str | None = None,
    cache_dir: Path | str | None = None,
    budget: BudgetV1 | None = None,
    path_prefixes: Sequence[str] | None = None,
) -> dict[str, Any]:
    root = Path(repo)
    active_budget = budget or BudgetV1()
    tracker = BudgetTrackerV1(active_budget)
    prefixes = None if path_prefixes is None else tuple(path_prefixes)
    selection_mode = "FULL_CENSUS" if prefixes is None else "BOUNDED_SLICE"
    commit_sha = resolve_commit_v1(root, commit)
    entries = list_entries_v1(root, commit_sha, prefixes)
    capture = None if capture_path is None else Path(capture_path)
    capture_bytes = capture.read_bytes() if capture is not None and capture.is_file() else None
    cache = None if cache_dir is None else Path(cache_dir)
    fingerprint = fingerprint_v1(
        commit_sha,
        entries,
        active_budget,
        capture_bytes,
        selection_mode=selection_mode,
    )
    cached = load_run_cache_v1(cache, fingerprint)
    if cached is not None:
        return cached

    census, s1_claims = discover_physical_v1(root, commit_sha, tracker, entries, cache_dir=cache)
    s1_status = slice_status_v1(tracker)
    s2_claims = extract_semantic_v1(census, tracker)
    s2_status = slice_status_v1(tracker)
    prior = [*s1_claims, *s2_claims]
    s3_claims = reconstruct_causal_v1(census, prior, tracker)
    s3_status = slice_status_v1(tracker)
    s4_claims, _raw = correlate_runtime_v1(commit_sha, prior, capture, tracker)
    s4_status = slice_status_v1(tracker)
    s5_claims = discover_layers_v1(commit_sha, [*prior, *s3_claims], tracker)
    s5_status = slice_status_v1(tracker)
    all_claims = [*s1_claims, *s2_claims, *s3_claims, *s4_claims, *s5_claims]
    if not _audit(all_claims):
        s3_status = "FAIL"
    slices = [
        _slice("S1", s1_status, s1_claims),
        _slice("S2", s2_status, s2_claims),
        _slice("S3", s3_status, s3_claims),
        _slice("S4", s4_status, s4_claims),
        _slice("S5", s5_status, s5_claims),
    ]
    run = {
        "schema": SCHEMA_ID,
        "tool_authority": TOOL_AUTHORITY,
        "commit_sha": commit_sha,
        "selection_mode": selection_mode,
        "paths_indexed": len(entries),
        "paths_read": tracker.files,
        "run_status": _run_status(slices),
        "external_effects": EXTERNAL_EFFECTS_PERFORMED,
        "slices": slices,
    }
    store_run_cache_v1(cache, fingerprint, run)
    return run


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Offline CURRENT semantic explorer")
    parser.add_argument("repo")
    parser.add_argument("commit")
    parser.add_argument("--capture")
    parser.add_argument("--cache-dir")
    parser.add_argument("--max-files", type=int, default=40)
    parser.add_argument("--path-prefix", action="append", default=None)
    args = parser.parse_args()
    result = run_explorer_v1(
        args.repo,
        args.commit,
        capture_path=args.capture,
        cache_dir=args.cache_dir,
        budget=BudgetV1(max_files=args.max_files),
        path_prefixes=args.path_prefix,
    )
    print(json.dumps({"run_status": result["run_status"], "commit_sha": result["commit_sha"]}))


if __name__ == "__main__":
    main()
