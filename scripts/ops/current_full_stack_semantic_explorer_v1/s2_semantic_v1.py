"""Slice 2. Semantic relations that the AST and resolved symbols support."""

from __future__ import annotations

from typing import Any

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetTrackerV1
from scripts.ops.current_full_stack_semantic_explorer_v1.evidence_v1 import append_claim_v1


def _closed_reason(tracker: BudgetTrackerV1) -> str:
    if tracker.time_closed:
        return "TIME_BUDGET"
    return "NODE_BUDGET"


def _ref(path: str, lineno: int) -> str:
    return f"{path}:{lineno}"


def _symbol(path: str, qualname: str) -> str:
    return f"{path}::{qualname}"


def _resolve_module(dotted: str, module_index: dict[str, str]) -> str | None:
    if dotted in module_index:
        return module_index[dotted]
    init_key = f"{dotted}.__init__" if dotted else ""
    if init_key and init_key in module_index:
        return module_index[init_key]
    return None


def _relative_dotted(path: str, level: int, module: str | None) -> str:
    parts = path.split("/")[:-1]
    drop = max(level - 1, 0)
    if drop:
        parts = parts[:-drop] if drop <= len(parts) else []
    if module:
        parts.extend(module.split("."))
    return ".".join(parts)


def _aliases(
    path: str,
    parsed: dict[str, Any],
    module_index: dict[str, str],
    functions: dict[str, str],
) -> dict[str, str]:
    found: dict[str, str] = {}
    for item in parsed["imports"]:
        level = int(item["level"])
        module = item["module"]
        for name, alias in item["names"]:
            local = alias or name
            if module is None and level == 0:
                resolved = _resolve_module(name, module_index)
                if resolved:
                    found[alias or name.split(".")[0]] = resolved
                continue
            dotted = _relative_dotted(path, level, module) if level else str(module)
            resolved = _resolve_module(dotted, module_index)
            if resolved is None:
                continue
            symbol = _symbol(resolved, name)
            found[local] = symbol if symbol in functions else resolved
    return found


def extract_semantic_v1(
    census: dict[str, Any],
    tracker: BudgetTrackerV1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    commit_sha = str(census["commit_sha"])
    modules: dict[str, Any] = census["modules"]
    module_index: dict[str, str] = census["module_index"]
    functions = {
        _symbol(path, item["qualname"]): path
        for path, parsed in modules.items()
        for item in parsed["functions"]
    }
    claims: list[dict[str, Any]] = []
    done: list[str] = []
    partial: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    ordered = sorted(modules)
    for index, path in enumerate(ordered):
        if tracker.node_closed or tracker.time_closed:
            reason = _closed_reason(tracker)
            skipped.extend({"path": item, "stop_reason": reason} for item in ordered[index:])
            break
        snap = tracker.snapshot()
        mark = len(claims)
        parsed = modules[path]
        alias_map = _aliases(path, parsed, module_index, functions)
        _resolved_imports(commit_sha, path, parsed, module_index, claims, tracker)
        local = {item["qualname"]: _symbol(path, item["qualname"]) for item in parsed["functions"]}
        for item in parsed["functions"]:
            subject = _symbol(path, item["qualname"])
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="semantic",
                subject=subject,
                predicate="HAS_SIGNATURE",
                object_=",".join(item["args"]),
                evidence_refs=[_ref(path, item["lineno"])],
                evidence_class="STATIC",
                status="PROVEN",
            )
            if item["returns"] is None:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=subject,
                    predicate="RETURNS",
                    object_="",
                    evidence_refs=[_ref(path, item["lineno"])],
                    evidence_class="STATIC",
                    status="UNPROVEN",
                    unknowns=["NO_ANNOTATION"],
                )
            else:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=subject,
                    predicate="RETURNS",
                    object_=str(item["returns"]),
                    evidence_refs=[_ref(path, item["lineno"])],
                    evidence_class="STATIC",
                    status="PROVEN",
                )
            _calls(commit_sha, path, subject, item, local, alias_map, functions, claims, tracker)
            for raised in item["raises"]:
                known = raised["name"] is not None
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=subject,
                    predicate="RAISES",
                    object_=raised["name"] or "",
                    evidence_refs=[_ref(path, raised["lineno"])],
                    evidence_class="STATIC",
                    status="PROVEN" if known else "UNPROVEN",
                    unknowns=[] if known else ["UNRESOLVED_EXCEPTION"],
                )
            for site in item["persists"]:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=subject,
                    predicate="PERSISTS",
                    object_=site["callee"],
                    evidence_refs=[_ref(path, site["lineno"])],
                    evidence_class="STATIC",
                    status="PROVEN",
                    unknowns=["NOT_RUNTIME_OBSERVED"],
                )
            for site in item["external"]:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=subject,
                    predicate="EXTERNAL_EFFECT_SITE",
                    object_=site["callee"],
                    evidence_refs=[_ref(path, site["lineno"])],
                    evidence_class="STATIC",
                    status="PROVEN",
                    unknowns=["NOT_RUNTIME_OBSERVED"],
                )
            for access in item["reads"]:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=subject,
                    predicate="READS_STATE",
                    object_=access["name"],
                    evidence_refs=[_ref(path, access["lineno"])],
                    evidence_class="STATIC",
                    status="PROVEN",
                )
            for access in item["writes"]:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=subject,
                    predicate="WRITES_STATE",
                    object_=access["name"],
                    evidence_refs=[_ref(path, access["lineno"])],
                    evidence_class="STATIC",
                    status="PROVEN",
                )
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="semantic",
                subject=subject,
                predicate="FUNCTION_MEANING",
                object_="",
                evidence_refs=[_ref(path, item["lineno"])],
                evidence_class="STATIC",
                status="UNPROVEN",
                unknowns=["NO_AGREED_MEANING"],
            )
        if tracker.node_closed or tracker.time_closed:
            reason = _closed_reason(tracker)
            tracker.restore(snap)
            del claims[mark:]
            partial.append({"path": path, "stop_reason": reason})
            skipped.extend({"path": item, "stop_reason": reason} for item in ordered[index + 1 :])
            break
        done.append(path)
    return claims, {"done": done, "partial": partial, "skipped": skipped}


def _calls(
    commit_sha: str,
    path: str,
    subject: str,
    item: dict[str, Any],
    local: dict[str, str],
    alias_map: dict[str, str],
    functions: dict[str, str],
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> None:
    for call in item["calls"]:
        if call["kind"] != "plain":
            continue
        target = _direct_target(path, call, local, alias_map, functions)
        ref = _ref(path, call["lineno"])
        if target is None:
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="semantic",
                subject=subject,
                predicate="DYNAMIC_TARGET",
                object_="",
                evidence_refs=[ref],
                evidence_class="STATIC",
                status="UNPROVEN",
                unknowns=["UNRESOLVED_TARGET"],
            )
            continue
        args = call["args"]
        append_claim_v1(
            claims,
            tracker,
            commit_sha=commit_sha,
            scope="semantic",
            subject=subject,
            predicate="CALLS",
            object_=target,
            evidence_refs=[ref],
            evidence_class="STATIC",
            status="PROVEN",
        )
        if args is None:
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="semantic",
                subject=subject,
                predicate="DATA_FLOW",
                object_=target,
                evidence_refs=[ref],
                evidence_class="STATIC",
                status="UNPROVEN",
                unknowns=["UNRESOLVED_ARGUMENTS"],
            )
        else:
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="semantic",
                subject=subject,
                predicate="DATA_FLOW",
                object_=f"{target}({','.join(args)})",
                evidence_refs=[ref],
                evidence_class="STATIC",
                status="PROVEN",
            )


def _resolved_imports(
    commit_sha: str,
    path: str,
    parsed: dict[str, Any],
    module_index: dict[str, str],
    claims: list[dict[str, Any]],
    tracker: BudgetTrackerV1,
) -> None:
    for item in parsed["imports"]:
        level = int(item["level"])
        module = item["module"]
        ref = _ref(path, int(item["lineno"]))
        if module is None and level == 0:
            targets = [name for name, _alias in item["names"]]
        else:
            dotted = _relative_dotted(path, level, module) if level else str(module)
            targets = [dotted]
        for target in targets:
            resolved = _resolve_module(target, module_index)
            if resolved is None:
                append_claim_v1(
                    claims,
                    tracker,
                    commit_sha=commit_sha,
                    scope="semantic",
                    subject=path,
                    predicate="IMPORT_TARGET",
                    object_=target,
                    evidence_refs=[ref],
                    evidence_class="STATIC",
                    status="UNPROVEN",
                    unknowns=["UNRESOLVED_TARGET"],
                )
                continue
            append_claim_v1(
                claims,
                tracker,
                commit_sha=commit_sha,
                scope="semantic",
                subject=path,
                predicate="IMPORT_TARGET",
                object_=resolved,
                evidence_refs=[ref],
                evidence_class="STATIC",
                status="PROVEN",
            )


def _direct_target(
    path: str,
    call: dict[str, Any],
    local: dict[str, str],
    alias_map: dict[str, str],
    functions: dict[str, str],
) -> str | None:
    del path
    root = call["root"]
    attr = call["attr"]
    if not root:
        return None
    if attr is None:
        if root in local:
            return local[root]
        aliased = alias_map.get(root)
        if aliased in functions:
            return aliased
        return None
    base = alias_map.get(root)
    if not isinstance(base, str):
        return None
    module_path = base.split("::", 1)[0]
    candidate = f"{module_path}::{attr}"
    if candidate in functions:
        return candidate
    return None
