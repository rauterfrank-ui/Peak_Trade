"""Slice 1. Physical census of one commit, read from Git objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetTrackerV1
from scripts.ops.current_full_stack_semantic_explorer_v1.cache_v1 import (
    load_parse_cache_v1,
    store_parse_cache_v1,
)
from scripts.ops.current_full_stack_semantic_explorer_v1.constants_v1 import MAX_BLOB_BYTES
from scripts.ops.current_full_stack_semantic_explorer_v1.evidence_v1 import append_claim_v1
from scripts.ops.current_full_stack_semantic_explorer_v1.git_objects_v1 import (
    GitEntryV1,
    read_blob_v1,
)
from scripts.ops.current_full_stack_semantic_explorer_v1.parse_v1 import parse_module_v1


def _ref(path: str, lineno: int | None = None) -> str:
    if lineno is None:
        return path
    return f"{path}:{lineno}"


def _dotted(path: str) -> str:
    if path.endswith("/__init__.py"):
        return path[: -len("/__init__.py")].replace("/", ".")
    if path.endswith(".py"):
        return path[: -len(".py")].replace("/", ".")
    return path.replace("/", ".")


def discover_physical_v1(
    repo: Path,
    commit_sha: str,
    tracker: BudgetTrackerV1,
    entries: list[GitEntryV1],
    *,
    cache_dir: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    modules: dict[str, Any] = {}
    contracts: dict[str, Any] = {}
    module_index: dict[str, str] = {}
    admitted: list[str] = []
    partial: list[dict[str, str]] = []
    not_started: list[dict[str, str]] = []

    for index, entry in enumerate(entries):
        if tracker.time_closed or tracker.node_closed:
            not_started.extend(_pending(entries[index:]))
            break
        snap = tracker.snapshot()
        mark = len(claims)
        module_keys = set(modules)
        contract_keys = set(contracts)
        index_keys = set(module_index)
        if not tracker.allow_file():
            not_started.extend(_pending(entries[index:]))
            break
        if not append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=entry.path,
            predicate="FILE",
            object_=entry.mode,
            evidence_refs=[f"git:{entry.object_sha}"],
            evidence_class="STATIC",
            status="PROVEN",
        ):
            break_file = True
        else:
            break_file = False
        if break_file or tracker.node_closed or tracker.time_closed:
            reason = _fresh_reason(snap, tracker)
            tracker.restore(snap)
            _drop_new(modules, module_keys)
            _drop_new(contracts, contract_keys)
            _drop_new(module_index, index_keys)
            del claims[mark:]
            partial.append(
                {"path": entry.path, "blob_sha": entry.object_sha, "stop_reason": reason}
            )
            not_started.extend(_pending(entries[index + 1 :]))
            break
        handled = False
        if entry.object_type == "commit" or entry.mode == "160000":
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="physical",
                subject=entry.path,
                predicate="REPOSITORY_BOUNDARY",
                object_=entry.object_sha,
                evidence_refs=[f"git:{entry.object_sha}"],
                evidence_class="STATIC",
                status="PROVEN",
                unknowns=["NOT_TRAVERSED"],
            )
            handled = True
        elif entry.object_type != "blob":
            handled = True
        else:
            blob = read_blob_v1(repo, entry.object_sha)
            if len(blob) > MAX_BLOB_BYTES:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="physical",
                    subject=entry.path,
                    predicate="PARSED",
                    object_="",
                    evidence_refs=[f"git:{entry.object_sha}"],
                    evidence_class="STATIC",
                    status="UNPROVEN",
                    unknowns=["BLOB_TOO_LARGE"],
                )
                handled = True
            elif entry.path.endswith(".json"):
                _take_contract(commit_sha, entry, blob, contracts, claims, tracker)
                handled = True
            elif not entry.path.endswith(".py"):
                handled = True
            else:
                parsed = _parse_python(entry, blob, cache_dir, claims, tracker, commit_sha)
                if parsed is not None:
                    modules[entry.path] = parsed
                    module_index[_dotted(entry.path)] = entry.path
                    _emit_structure(commit_sha, entry.path, parsed, claims, tracker)
                handled = True
        if not handled or tracker.node_closed or tracker.time_closed:
            reason = _fresh_reason(snap, tracker)
            tracker.restore(snap)
            _drop_new(modules, module_keys)
            _drop_new(contracts, contract_keys)
            _drop_new(module_index, index_keys)
            del claims[mark:]
            partial.append(
                {"path": entry.path, "blob_sha": entry.object_sha, "stop_reason": reason}
            )
            not_started.extend(_pending(entries[index + 1 :]))
            break
        admitted.append(entry.path)

    census = {
        "commit_sha": commit_sha,
        "modules": modules,
        "contracts": contracts,
        "module_index": module_index,
    }
    return census, claims, {"admitted": admitted, "partial": partial, "not_started": not_started}


def _pending(entries: list[GitEntryV1]) -> list[dict[str, str]]:
    return [{"path": entry.path, "blob_sha": entry.object_sha} for entry in entries]


def _drop_new(mapping: dict[str, Any], before: set[str]) -> None:
    for key in list(mapping):
        if key not in before:
            del mapping[key]


def _fresh_reason(snap: Any, tracker: BudgetTrackerV1) -> str:
    previous = set(snap.stop_reasons)
    for reason in tracker.stop_reasons:
        if reason not in previous:
            return reason
    if tracker.time_closed:
        return "TIME_BUDGET"
    if tracker.node_closed:
        return "NODE_BUDGET"
    return "NODE_BUDGET"


def _parse_python(
    entry: GitEntryV1,
    blob: bytes,
    cache_dir: Path | None,
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
    commit_sha: str,
) -> dict[str, Any] | None:
    cached = load_parse_cache_v1(cache_dir, entry.object_sha)
    if cached is not None:
        return cached
    try:
        source = blob.decode("utf-8")
        parsed = parse_module_v1(source)
    except (UnicodeDecodeError, SyntaxError):
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=entry.path,
            predicate="PARSED",
            object_="",
            evidence_refs=[f"git:{entry.object_sha}"],
            evidence_class="STATIC",
            status="UNPROVEN",
            unknowns=["PARSE_FAILED"],
        )
        return None
    store_parse_cache_v1(cache_dir, entry.object_sha, parsed)
    return parsed


def _take_contract(
    commit_sha: str,
    entry: GitEntryV1,
    blob: bytes,
    contracts: dict[str, Any],
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> None:
    try:
        loaded = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=entry.path,
            predicate="CONTRACT_FILE",
            object_="",
            evidence_refs=[entry.path],
            evidence_class="CONTRACT",
            status="UNPROVEN",
            unknowns=["CONTRACT_UNREADABLE"],
        )
        return
    if isinstance(loaded, dict) and isinstance(loaded.get("subject"), str):
        contracts[entry.path] = loaded


def _emit_structure(
    commit_sha: str,
    path: str,
    parsed: dict[str, Any],
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> None:
    append_claim_v1(
        claims,
        tracker,
        commit_sha=commit_sha,
        scope="physical",
        subject=path,
        predicate="MODULE",
        object_=_dotted(path),
        evidence_refs=[path],
        evidence_class="STATIC",
        status="PROVEN",
    )
    for item in parsed["classes"]:
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=f"{path}::{item['qualname']}",
            predicate="DEFINES",
            object_="class",
            evidence_refs=[_ref(path, item["lineno"])],
            evidence_class="STATIC",
            status="PROVEN",
        )
    for item in parsed["functions"]:
        kind = "method" if "." in item["qualname"] else "function"
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=f"{path}::{item['qualname']}",
            predicate="DEFINES",
            object_=kind,
            evidence_refs=[_ref(path, item["lineno"])],
            evidence_class="STATIC",
            status="PROVEN",
        )
    for item in parsed["imports"]:
        module_name = item["module"] or ""
        names = ",".join(name for name, _alias in item["names"])
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=path,
            predicate="IMPORTS",
            object_=f"{module_name}:{names}",
            evidence_refs=[_ref(path, item["lineno"])],
            evidence_class="STATIC",
            status="PROVEN" if module_name or names else "UNPROVEN",
            unknowns=[] if module_name or names else ["UNRESOLVED_TARGET"],
        )
    for name in parsed["exports"]:
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=path,
            predicate="EXPORTS",
            object_=name,
            evidence_refs=[path],
            evidence_class="STATIC",
            status="PROVEN",
        )
    if parsed["entrypoint"] is not None:
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="physical",
            subject=path,
            predicate="ENTRYPOINT",
            object_="__main__",
            evidence_refs=[_ref(path, parsed["entrypoint"])],
            evidence_class="STATIC",
            status="PROVEN",
        )
