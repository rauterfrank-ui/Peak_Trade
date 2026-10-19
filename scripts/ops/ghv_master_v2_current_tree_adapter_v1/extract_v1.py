"""One-hop CALLS extraction from explicit git blobs. No graph engine. AUTHORITY=NONE."""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import edge_semantics_flags
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.constants_v1 import (
    ANCHORS,
    AUTHORITY,
    AUTHORIZATION_NOT_AUTHORIZED,
    COVERAGE_STATUS,
    CURRENT_ORIGIN_MAIN_SHA,
    CURRENT_ORIGIN_MAIN_TREE,
    EDGE_TYPE,
    EXECUTION_AUTHORITY,
    EXISTENCE_EXISTS,
    EXTERNAL_POST_COUNT,
    FOREIGN_SEMANTICS,
    HOP_LIMIT,
    MEMBERSHIP_START_ANCHOR,
    MEMBERSHIP_UNKNOWN,
    OWNER_LOCK_MUTATED,
    PACKAGE_ID,
    PRODUCTIVE_IMPORTS,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCOPE_ID,
    STATUS_NOT_PROVEN,
    TRADING_AUTHORITY,
    WIRING_WIRED,
)
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.dynamic_bindings_v1 import (
    scan_literal_import_module_bindings_v1,
)
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.ghv_projection_v1 import (
    ghv_native_id,
    project_adapter_edges_v1,
    traverse_projected_graph_v1,
)
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.tree_reader_v1 import (
    PinRejected,
    TreeBlobReader,
    assert_commit_matches_tree,
    require_explicit_oid,
)

_BUILTIN_NAMES = frozenset(dir(builtins))
_STDLIB_ROOTS = frozenset(sys.stdlib_module_names) | frozenset(sys.builtin_module_names)
_NESTED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


@dataclass(frozen=True)
class _Binding:
    local_name: str
    module: str
    symbol: str | None
    import_lineno: int
    blob_path: str | None
    non_repository: bool
    ambiguous: bool


@dataclass
class _EdgeAcc:
    source_path: str
    source_symbol: str
    source_anchor_id: str
    source_blob_sha: str
    target_path: str | None
    target_symbol: str
    target_module: str | None
    existence: str
    membership: str
    import_lines: set[int]
    call_lines: set[int]

    def key(self) -> tuple[str, str, str, str, str]:
        return (
            self.source_path,
            self.source_symbol,
            self.target_path or "",
            self.target_symbol,
            self.target_module or "",
        )


def _calls_flags() -> dict[str, Any]:
    flags = dict(edge_semantics_flags(EDGE_TYPE))
    if flags.get("edge_type") != EDGE_TYPE or flags.get("trading_authority_implied") is not False:
        raise PinRejected("AUTHORITY_ESCALATION_REJECTED")
    return flags


def _module_candidates(module: str) -> list[str]:
    dotted = module.replace(".", "/") + ".py"
    init = module.replace(".", "/") + "/__init__.py"
    if module.startswith("src."):
        return [dotted, init]
    return [f"src/{dotted}", dotted, f"src/{init}", init]


def _is_stdlib(module: str) -> bool:
    root = module.split(".", 1)[0]
    return root in _STDLIB_ROOTS


def _resolve_module_blob(
    reader: TreeBlobReader, modules: list[str]
) -> tuple[str | None, bool, bool]:
    """Return blob path, ambiguous, non_repository."""
    found: set[str] = set()
    saw_repository_name = False
    for module in modules:
        paths = [path for path in _module_candidates(module) if reader.exists(path)]
        if paths:
            found.update(paths)
            saw_repository_name = True
        elif not _is_stdlib(module):
            saw_repository_name = True
    if len(found) == 1:
        return next(iter(found)), False, False
    if len(found) > 1:
        return None, True, False
    return None, False, not saw_repository_name


def _relative_modules(file_path: str, level: int, module: str | None) -> list[str]:
    parts = file_path.split("/")
    package = parts[:-1]
    interpretations = [package]
    if package and package[0] == "src":
        interpretations.append(package[1:])
    modules: list[str] = []
    for pkg in interpretations:
        if level <= 0 or level - 1 > len(pkg):
            continue
        base = pkg[: len(pkg) - (level - 1)]
        if module:
            full = ".".join([*base, *module.split(".")])
        else:
            full = ".".join(base)
        if full:
            modules.append(full)
    return list(dict.fromkeys(modules))


def _bindings_from_import(
    node: ast.Import | ast.ImportFrom,
    *,
    file_path: str,
    reader: TreeBlobReader,
) -> list[_Binding]:
    bindings: list[_Binding] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            local = alias.asname or alias.name.split(".", 1)[0]
            blob, ambiguous, non_repo = _resolve_module_blob(reader, [alias.name])
            bindings.append(
                _Binding(
                    local_name=local,
                    module=alias.name,
                    symbol=None,
                    import_lineno=node.lineno,
                    blob_path=blob,
                    non_repository=non_repo,
                    ambiguous=ambiguous,
                )
            )
        return bindings

    if any(alias.name == "*" for alias in node.names):
        return bindings
    if node.level:
        modules = _relative_modules(file_path, node.level, node.module)
    elif node.module:
        modules = [node.module]
    else:
        return bindings
    blob, ambiguous, non_repo = _resolve_module_blob(reader, modules)
    module_name = modules[0] if modules else ""
    for alias in node.names:
        if node.module is None and node.level:
            sub_modules = _relative_modules(file_path, node.level, alias.name)
            sub_blob, sub_ambiguous, sub_non_repo = _resolve_module_blob(reader, sub_modules)
            bindings.append(
                _Binding(
                    local_name=alias.asname or alias.name,
                    module=sub_modules[0] if sub_modules else alias.name,
                    symbol=None,
                    import_lineno=node.lineno,
                    blob_path=sub_blob,
                    non_repository=sub_non_repo,
                    ambiguous=sub_ambiguous,
                )
            )
            continue
        bindings.append(
            _Binding(
                local_name=alias.asname or alias.name,
                module=module_name,
                symbol=alias.name,
                import_lineno=node.lineno,
                blob_path=blob,
                non_repository=non_repo,
                ambiguous=ambiguous,
            )
        )
    return bindings


def _bind_map(bindings: list[_Binding]) -> dict[str, _Binding]:
    mapped: dict[str, _Binding] = {}
    duplicates: set[str] = set()
    for binding in bindings:
        if binding.local_name in mapped:
            duplicates.add(binding.local_name)
        mapped[binding.local_name] = binding
    for name in duplicates:
        del mapped[name]
    return mapped


def _target_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for element in node.elts:
            names.update(_target_names(element))
        return names
    return set()


def _assigned_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = {arg.arg for arg in [*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs]}
    if func.args.vararg is not None:
        names.add(func.args.vararg.arg)
    if func.args.kwarg is not None:
        names.add(func.args.kwarg.arg)

    def walk(node: ast.AST) -> None:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return
        if isinstance(node, ast.Assign):
            for target in node.targets:
                names.update(_target_names(target))
        elif isinstance(node, ast.AnnAssign):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.AugAssign):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.NamedExpr):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.For):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.ExceptHandler) and isinstance(node.name, str):
            names.add(node.name)
        elif isinstance(node, ast.With):
            for item in node.items:
                if item.optional_vars is not None:
                    names.update(_target_names(item.optional_vars))
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _NESTED):
                continue
            walk(child)

    for stmt in func.body:
        if isinstance(stmt, _NESTED):
            continue
        walk(stmt)
    return names


def _module_symbols(tree: ast.AST) -> set[str]:
    symbols: set[str] = set()
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
    return symbols


def _iter_nodes(func: ast.FunctionDef | ast.AsyncFunctionDef, kind: type[ast.AST]) -> list[ast.AST]:
    found: list[ast.AST] = []

    def walk(node: ast.AST) -> None:
        if isinstance(node, kind):
            found.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _NESTED):
                continue
            walk(child)

    for stmt in func.body:
        if isinstance(stmt, _NESTED):
            continue
        walk(stmt)
    return found


def _find_anchor_function(tree: ast.AST, symbol: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    matches = [
        node
        for node in (tree.body if isinstance(tree, ast.Module) else [])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol
    ]
    if len(matches) != 1:
        raise PinRejected(f"ANCHOR_SYMBOL_ABSENT:{symbol}")
    return matches[0]


def _parsed_symbols(
    reader: TreeBlobReader, path: str, cache: dict[str, set[str] | None]
) -> set[str] | None:
    if path in cache:
        return cache[path]
    text = reader.text(path)
    if text is None:
        cache[path] = None
        return None
    try:
        parsed = ast.parse(text)
    except SyntaxError:
        cache[path] = None
        return None
    symbols = _module_symbols(parsed)
    cache[path] = symbols
    return symbols


def _membership(path: str | None, symbol: str, anchors: set[tuple[str, str]]) -> str:
    if path is not None and (path, symbol) in anchors:
        return MEMBERSHIP_START_ANCHOR
    return MEMBERSHIP_UNKNOWN


def _add_edge(
    edges: dict[tuple[str, str, str, str, str], _EdgeAcc],
    *,
    source_path: str,
    source_symbol: str,
    source_anchor_id: str,
    source_blob_sha: str,
    target_path: str | None,
    target_symbol: str,
    target_module: str | None,
    existence: str,
    membership: str,
    import_lineno: int | None,
    call_lineno: int,
) -> None:
    acc = _EdgeAcc(
        source_path=source_path,
        source_symbol=source_symbol,
        source_anchor_id=source_anchor_id,
        source_blob_sha=source_blob_sha,
        target_path=target_path,
        target_symbol=target_symbol,
        target_module=target_module,
        existence=existence,
        membership=membership,
        import_lines=set() if import_lineno is None else {import_lineno},
        call_lines={call_lineno},
    )
    current = edges.get(acc.key())
    if current is None:
        edges[acc.key()] = acc
        return
    current.call_lines.add(call_lineno)
    current.import_lines.update(acc.import_lines)
    if current.existence != existence:
        current.existence = STATUS_NOT_PROVEN


def _lookup_binding(
    name: str,
    *,
    local_bindings: dict[str, _Binding],
    module_bindings: dict[str, _Binding],
) -> _Binding | None:
    if name in local_bindings:
        return local_bindings[name]
    return module_bindings.get(name)


def _dynamic_binding_report(
    *,
    scan_inputs: list[dict[str, Any]],
    reader: TreeBlobReader,
    baseline_edges: list[dict[str, Any]],
    commit_sha: str,
    tree_sha: str,
    flags: dict[str, Any],
    anchor_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    dynamic_edges: dict[tuple[str, str, str, str, str], _EdgeAcc] = {}
    call_kinds: dict[tuple[str, str, str, str, str], set[str]] = {}
    for item in scan_inputs:
        scan = scan_literal_import_module_bindings_v1(
            func=item["func"],
            file_path=item["path"],
            source_symbol=item["symbol"],
            source_anchor_id=item["anchor_id"],
            source_blob_sha=item["blob_sha"],
            lookup_binding=lambda name, item=item: _lookup_binding(
                name,
                local_bindings=item["local_bindings"],
                module_bindings=item["module_bindings"],
            ),
            shadowed=item["shadowed"],
            reader=reader,
            resolve_module_blob=_resolve_module_blob,
        )
        candidates.extend(scan["candidates"])
        unresolved.extend(scan["unresolved"])
        for fact in scan["resolved_calls"]:
            if (fact["source_path"], fact["source_symbol"]) not in anchor_keys:
                raise PinRejected("HOP_LIMIT_EXCEEDED")
            _add_edge(
                dynamic_edges,
                source_path=fact["source_path"],
                source_symbol=fact["source_symbol"],
                source_anchor_id=fact["source_anchor_id"],
                source_blob_sha=fact["source_blob_sha"],
                target_path=fact["target_path"],
                target_symbol=fact["target_symbol"],
                target_module=fact["target_module"],
                existence=fact["existence"],
                membership=_membership(fact["target_path"], fact["target_symbol"], anchor_keys),
                import_lineno=fact["import_lineno"],
                call_lineno=fact["call_lineno"],
            )
            key = (
                fact["source_path"],
                fact["source_symbol"],
                fact["target_path"] or "",
                fact["target_symbol"],
                fact["target_module"] or "",
            )
            call_kinds.setdefault(key, set()).add(fact["call_kind"])
    dynamic_records = []
    for key, acc in sorted(dynamic_edges.items(), key=lambda item: item[0]):
        record = _edge_record(acc, commit_sha=commit_sha, tree_sha=tree_sha, flags=flags)
        kinds = call_kinds.get(key, set())
        record["binding_resolution"] = "LITERAL_IMPORT_MODULE"
        record["call_kind"] = next(iter(kinds)) if len(kinds) == 1 else "MIXED"
        if record["activity"] == "ACTIVE" or record["authorization"] == "AUTHORIZED":
            raise PinRejected("STATUS_UPGRADE_REJECTED")
        if record["trading_authority_implied"] is not False:
            raise PinRejected("AUTHORITY_ESCALATION_REJECTED")
        dynamic_records.append(record)
    baseline_index: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for edge in baseline_edges:
        baseline_index.setdefault((edge["file"], edge["symbol"], edge["target_symbol"]), []).append(
            edge
        )
    new_edges: list[dict[str, Any]] = []
    resolved_baseline: list[dict[str, Any]] = []
    for record in dynamic_records:
        matches = baseline_index.get(
            (record["file"], record["symbol"], record["target_symbol"]), []
        )
        if not matches:
            new_edges.append(record)
            continue
        if len(matches) == 1 and not matches[0].get("target_file"):
            resolved_baseline.append(record)
            continue
        unresolved.append(
            {
                "status": "UNRESOLVED_DYNAMIC_BINDING",
                "reason": "DUPLICATE_BASELINE_EDGE",
                "source_file": record["file"],
                "source_symbol": record["symbol"],
                "source_line": record["call_lines"][0],
                "local_name": None,
                "module_literal": record["target_module"],
                "target_symbol": record["target_symbol"],
            }
        )
    unresolved.sort(
        key=lambda item: (
            item["source_file"],
            item["source_line"],
            item["reason"],
            item["target_symbol"] or "",
        )
    )
    new_digest = hashlib.sha256(
        json.dumps(new_edges, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    overlays = {
        (record["file"], record["symbol"], record["target_symbol"]): {
            "target_file": record["target_file"]
        }
        for record in resolved_baseline
    }
    return {
        "dynamic_binding_candidates": candidates,
        "resolved_dynamic_call_edges": new_edges,
        "resolved_baseline_unresolved_edges": resolved_baseline,
        "unresolved_dynamic_bindings": unresolved,
        "new_resolved_call_edge_digest_sha256": new_digest,
        "target_overlays": overlays,
    }


def _depth_one_traversal(
    projection: dict[str, Any], anchors: tuple[dict[str, Any], ...]
) -> dict[str, Any]:
    node_ids = {node["source_native_id"] for node in projection["nodes"]}
    report: dict[str, Any] = {
        "max_depth": 1,
        "runtime_reachability": "NOT_PROVEN",
        "activity": "NOT_PROVEN",
        "forward": {},
        "reverse": {},
    }
    for spec in anchors:
        origin = ghv_native_id(path=spec["path"], symbol=spec["symbol"])
        for direction, bucket_name in (("FORWARD", "forward"), ("REVERSE", "reverse")):
            if origin not in node_ids:
                report[bucket_name][spec["anchor_id"]] = {
                    "status": "ORIGIN_ABSENT",
                    "origin_native_id": origin,
                    "reachable_native_ids": [],
                    "activity": "NOT_PROVEN",
                    "runtime_reachability": "NOT_PROVEN",
                }
                continue
            result = traverse_projected_graph_v1(
                nodes=projection["nodes"],
                edges=projection["edges"],
                origin_native_id=origin,
                direction=direction,
                max_depth=1,
            )
            report[bucket_name][spec["anchor_id"]] = {
                "status": "TRAVERSED",
                "origin_native_id": origin,
                "reachable_native_ids": list(result.reachable_native_ids),
                "activity": "NOT_PROVEN",
                "runtime_reachability": "NOT_PROVEN",
            }
    return report


def extract_bounded_anchor_edges_v1(
    *,
    repo_root: Path,
    commit_sha: str,
    tree_sha: str,
) -> dict[str, Any]:
    require_explicit_oid(commit_sha)
    require_explicit_oid(tree_sha)
    assert_commit_matches_tree(repo_root=repo_root, commit_sha=commit_sha, tree_sha=tree_sha)
    flags = _calls_flags()
    reader = TreeBlobReader(repo_root=repo_root, tree_sha=tree_sha)
    anchor_keys = {(item["path"], item["symbol"]) for item in ANCHORS}
    symbol_cache: dict[str, set[str] | None] = {}
    edges: dict[tuple[str, str, str, str, str], _EdgeAcc] = {}
    omitted = {"builtin": 0, "non_repository": 0, "unresolved_attribute": 0, "unresolved_form": 0}
    anchor_records: list[dict[str, Any]] = []
    scan_inputs: list[dict[str, Any]] = []

    for spec in ANCHORS:
        path = spec["path"]
        symbol = spec["symbol"]
        text = reader.text(path)
        if text is None:
            raise PinRejected(f"ANCHOR_BLOB_ABSENT:{path}")
        try:
            parsed = ast.parse(text)
        except SyntaxError as exc:
            raise PinRejected(f"ANCHOR_SYNTAX:{path}") from exc
        func = _find_anchor_function(parsed, symbol)
        blob_sha = reader.blob_sha(path)
        if blob_sha is None:
            raise PinRejected(f"ANCHOR_BLOB_ABSENT:{path}")
        anchor_records.append(
            {
                "record_kind": "ANCHOR",
                "anchor_id": spec["anchor_id"],
                "current_sha": commit_sha,
                "current_tree": tree_sha,
                "file": path,
                "symbol": symbol,
                "edge_type": None,
                "evidence_ref": f"git:{tree_sha}:{path}#L{func.lineno}",
                "source_blob_sha": blob_sha,
                "coverage": COVERAGE_STATUS,
                "uncertainty": "ANCHOR_DEFINITION_ONLY",
                "existence": EXISTENCE_EXISTS,
                "wiring": STATUS_NOT_PROVEN,
                "reachability": STATUS_NOT_PROVEN,
                "activity": STATUS_NOT_PROVEN,
                "authorization": AUTHORIZATION_NOT_AUTHORIZED,
                "membership": MEMBERSHIP_START_ANCHOR,
                "foreign_semantics": FOREIGN_SEMANTICS,
                "location_fact": spec["location_fact"],
                "universe_membership": "NOT_CLAIMED",
            }
        )
        module_bindings = _bind_map(
            [
                binding
                for node in parsed.body
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for binding in _bindings_from_import(node, file_path=path, reader=reader)
            ]
        )
        local_bindings = _bind_map(
            [
                binding
                for node in _iter_nodes(func, ast.Import) + _iter_nodes(func, ast.ImportFrom)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for binding in _bindings_from_import(node, file_path=path, reader=reader)
            ]
        )
        shadowed = _assigned_names(func)
        same_file = _module_symbols(parsed)

        for call in _iter_nodes(func, ast.Call):
            if not isinstance(call, ast.Call):
                continue
            resolved = _resolve_call(
                call,
                file_path=path,
                local_bindings=local_bindings,
                module_bindings=module_bindings,
                shadowed=shadowed,
                same_file=same_file,
                omitted=omitted,
            )
            if resolved is None:
                continue
            target_path = resolved["target_path"]
            target_symbol = resolved["target_symbol"]
            existence = STATUS_NOT_PROVEN
            if target_path is not None:
                symbols = _parsed_symbols(reader, target_path, symbol_cache)
                if symbols is not None and target_symbol in symbols:
                    existence = EXISTENCE_EXISTS
            elif resolved["same_file"]:
                existence = EXISTENCE_EXISTS
                target_path = path
            _add_edge(
                edges,
                source_path=path,
                source_symbol=symbol,
                source_anchor_id=spec["anchor_id"],
                source_blob_sha=blob_sha,
                target_path=target_path,
                target_symbol=target_symbol,
                target_module=resolved["target_module"],
                existence=existence,
                membership=_membership(target_path, target_symbol, anchor_keys),
                import_lineno=resolved["import_lineno"],
                call_lineno=call.lineno,
            )
        scan_inputs.append(
            {
                "func": func,
                "path": path,
                "symbol": symbol,
                "anchor_id": spec["anchor_id"],
                "blob_sha": blob_sha,
                "module_bindings": module_bindings,
                "local_bindings": local_bindings,
                "shadowed": shadowed,
            }
        )

    edge_records = [
        _edge_record(acc, commit_sha=commit_sha, tree_sha=tree_sha, flags=flags)
        for _, acc in sorted(edges.items(), key=lambda item: item[0])
    ]
    for record in edge_records:
        if record["activity"] == "ACTIVE" or record["authorization"] == "AUTHORIZED":
            raise PinRejected("STATUS_UPGRADE_REJECTED")
        if record["edge_type"] != EDGE_TYPE:
            raise PinRejected("UNEXPECTED_EDGE_TYPE")
        if (record["file"], record["symbol"]) not in anchor_keys:
            raise PinRejected("HOP_LIMIT_EXCEEDED")
    digest = hashlib.sha256(
        json.dumps(edge_records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    dynamic = _dynamic_binding_report(
        scan_inputs=scan_inputs,
        reader=reader,
        baseline_edges=edge_records,
        commit_sha=commit_sha,
        tree_sha=tree_sha,
        flags=flags,
        anchor_keys=anchor_keys,
    )
    projection = project_adapter_edges_v1(
        [*edge_records, *dynamic["resolved_dynamic_call_edges"]],
        target_overlays=dynamic["target_overlays"],
    )
    depth_one = _depth_one_traversal(projection, ANCHORS)
    return {
        "package_id": PACKAGE_ID,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "external_post_count": EXTERNAL_POST_COUNT,
        "productive_imports": PRODUCTIVE_IMPORTS,
        "owner_lock_mutated": OWNER_LOCK_MUTATED,
        "census_decision_flow_remap": False,
        "graph_engine_created": False,
        "ghosv_invoked": False,
        "causal_graph_consulted": False,
        "hop_limit": HOP_LIMIT,
        "expansion": "EACH_START_ANCHOR_ONE_HOP",
        "current_sha": commit_sha,
        "current_tree": tree_sha,
        "anchors": anchor_records,
        "edges": edge_records,
        "edge_digest_sha256": digest,
        "baseline_edge_count": len(edge_records),
        "baseline_edge_digest_sha256": digest,
        "dynamic_binding_candidates": dynamic["dynamic_binding_candidates"],
        "resolved_dynamic_call_edges": dynamic["resolved_dynamic_call_edges"],
        "resolved_baseline_unresolved_edges": dynamic["resolved_baseline_unresolved_edges"],
        "unresolved_dynamic_bindings": dynamic["unresolved_dynamic_bindings"],
        "new_resolved_call_edge_count": len(dynamic["resolved_dynamic_call_edges"]),
        "new_resolved_call_edge_digest_sha256": dynamic["new_resolved_call_edge_digest_sha256"],
        "ghv_projection": projection,
        "ghv_depth_1": depth_one,
        "coverage": {
            "scope_id": SCOPE_ID,
            "status": COVERAGE_STATUS,
            "universe_coverage": "NOT_CLAIMED",
            "hop_limit": HOP_LIMIT,
            "omitted_calls": omitted,
            "uncertainty": [
                "ACTIVITY_NOT_PROVEN",
                "AUTHORIZATION_NOT_AUTHORIZED",
                "LITERAL_IMPORT_MODULE_BINDINGS_REPORTED_SEPARATELY",
                "FULL_UNIVERSE_BOUNDARY_NOT_CLAIMED",
                "NON_REPOSITORY_AND_UNTYPED_ATTRIBUTE_CALLS_OMITTED",
                "REACHABILITY_NOT_PROVEN",
                "TRANSITIVE_HOPS_NOT_TAKEN",
            ],
        },
    }


def _resolve_call(
    call: ast.Call,
    *,
    file_path: str,
    local_bindings: dict[str, _Binding],
    module_bindings: dict[str, _Binding],
    shadowed: set[str],
    same_file: set[str],
    omitted: dict[str, int],
) -> dict[str, Any] | None:
    func = call.func
    if isinstance(func, ast.Name):
        return _resolve_name(
            func.id,
            file_path=file_path,
            local_bindings=local_bindings,
            module_bindings=module_bindings,
            shadowed=shadowed,
            same_file=same_file,
            omitted=omitted,
        )
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return _resolve_attribute(
            func.value.id,
            func.attr,
            local_bindings=local_bindings,
            module_bindings=module_bindings,
            shadowed=shadowed,
            omitted=omitted,
        )
    omitted["unresolved_form"] += 1
    return None


def _lookup(
    name: str,
    *,
    local_bindings: dict[str, _Binding],
    module_bindings: dict[str, _Binding],
) -> _Binding | None:
    if name in local_bindings:
        return local_bindings[name]
    return module_bindings.get(name)


def _resolve_name(
    name: str,
    *,
    file_path: str,
    local_bindings: dict[str, _Binding],
    module_bindings: dict[str, _Binding],
    shadowed: set[str],
    same_file: set[str],
    omitted: dict[str, int],
) -> dict[str, Any] | None:
    if name in shadowed:
        return _unresolved(name)
    binding = _lookup(name, local_bindings=local_bindings, module_bindings=module_bindings)
    if binding is not None:
        if binding.non_repository:
            omitted["non_repository"] += 1
            return None
        if binding.ambiguous or binding.symbol is None:
            return _unresolved(name)
        return {
            "target_path": binding.blob_path,
            "target_symbol": binding.symbol,
            "target_module": binding.module,
            "import_lineno": binding.import_lineno,
            "same_file": False,
        }
    if name in same_file:
        return {
            "target_path": file_path,
            "target_symbol": name,
            "target_module": None,
            "import_lineno": None,
            "same_file": True,
        }
    if name in _BUILTIN_NAMES:
        omitted["builtin"] += 1
        return None
    return _unresolved(name)


def _resolve_attribute(
    name: str,
    attr: str,
    *,
    local_bindings: dict[str, _Binding],
    module_bindings: dict[str, _Binding],
    shadowed: set[str],
    omitted: dict[str, int],
) -> dict[str, Any] | None:
    if name in shadowed:
        omitted["unresolved_attribute"] += 1
        return None
    binding = _lookup(name, local_bindings=local_bindings, module_bindings=module_bindings)
    if binding is None or binding.symbol is not None or binding.ambiguous:
        omitted["unresolved_attribute"] += 1
        return None
    if binding.non_repository:
        omitted["non_repository"] += 1
        return None
    return {
        "target_path": binding.blob_path,
        "target_symbol": attr,
        "target_module": binding.module,
        "import_lineno": binding.import_lineno,
        "same_file": False,
    }


def _unresolved(name: str) -> dict[str, Any]:
    return {
        "target_path": None,
        "target_symbol": name,
        "target_module": None,
        "import_lineno": None,
        "same_file": False,
    }


def _edge_record(
    acc: _EdgeAcc,
    *,
    commit_sha: str,
    tree_sha: str,
    flags: dict[str, Any],
) -> dict[str, Any]:
    call_lines = sorted(acc.call_lines)
    import_lines = sorted(acc.import_lines)
    evidence = f"git:{tree_sha}:{acc.source_path}#L{','.join(str(line) for line in call_lines)}"
    return {
        "record_kind": "EDGE",
        "anchor_id": acc.source_anchor_id,
        "current_sha": commit_sha,
        "current_tree": tree_sha,
        "file": acc.source_path,
        "symbol": acc.source_symbol,
        "edge_type": EDGE_TYPE,
        "evidence_ref": evidence,
        "import_evidence_lines": import_lines,
        "call_lines": call_lines,
        "source_blob_sha": acc.source_blob_sha,
        "target_file": acc.target_path,
        "target_symbol": acc.target_symbol,
        "target_module": acc.target_module,
        "coverage": COVERAGE_STATUS,
        "uncertainty": "ONE_HOP_STATIC_CALL_ONLY",
        "existence": acc.existence,
        "wiring": WIRING_WIRED,
        "reachability": STATUS_NOT_PROVEN,
        "activity": STATUS_NOT_PROVEN,
        "authorization": AUTHORIZATION_NOT_AUTHORIZED,
        "membership": acc.membership,
        "foreign_semantics": FOREIGN_SEMANTICS,
        "universe_membership": "NOT_CLAIMED",
        "ghv_edge_flags": flags,
        "trading_authority_implied": False,
    }


def run_ghv_master_v2_current_tree_adapter_v1(
    *,
    repo_root: Path,
    commit_sha: str,
    tree_sha: str,
) -> dict[str, Any]:
    require_explicit_oid(commit_sha)
    require_explicit_oid(tree_sha)
    if commit_sha != CURRENT_ORIGIN_MAIN_SHA or tree_sha != CURRENT_ORIGIN_MAIN_TREE:
        raise PinRejected("CURRENT_PIN_MISMATCH")
    return extract_bounded_anchor_edges_v1(
        repo_root=repo_root,
        commit_sha=commit_sha,
        tree_sha=tree_sha,
    )
