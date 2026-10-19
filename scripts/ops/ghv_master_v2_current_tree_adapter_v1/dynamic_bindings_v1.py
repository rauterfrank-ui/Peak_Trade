"""Static recognition of literal importlib.import_module bindings.

The import is not executed. Only a unique literal, a unique local name,
and one uniquely defined target symbol can become a call fact.
"""

from __future__ import annotations

import ast
from typing import Any, Callable

from scripts.ops.ghv_master_v2_current_tree_adapter_v1.tree_reader_v1 import TreeBlobReader

_NESTED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
ResolveModule = Callable[[TreeBlobReader, list[str]], tuple[str | None, bool, bool]]


def _assignment_counts(func: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, int]:
    counts: dict[str, int] = {}

    def add(names: set[str]) -> None:
        for name in names:
            counts[name] = counts.get(name, 0) + 1

    def names_of(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Name):
            return {node.id}
        if isinstance(node, (ast.Tuple, ast.List)):
            found: set[str] = set()
            for element in node.elts:
                found.update(names_of(element))
            return found
        return set()

    add({arg.arg for arg in [*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs]})
    if func.args.vararg is not None:
        add({func.args.vararg.arg})
    if func.args.kwarg is not None:
        add({func.args.kwarg.arg})

    def walk(node: ast.AST) -> None:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return
        if isinstance(node, ast.Assign):
            for target in node.targets:
                add(names_of(target))
        elif isinstance(node, ast.AnnAssign):
            add(names_of(node.target))
        elif isinstance(node, ast.AugAssign):
            add(names_of(node.target))
        elif isinstance(node, ast.NamedExpr):
            add(names_of(node.target))
        elif isinstance(node, ast.For):
            add(names_of(node.target))
        elif isinstance(node, ast.ExceptHandler) and isinstance(node.name, str):
            add({node.name})
        elif isinstance(node, ast.With):
            for item in node.items:
                if item.optional_vars is not None:
                    add(names_of(item.optional_vars))
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _NESTED):
                continue
            walk(child)

    for stmt in func.body:
        if isinstance(stmt, _NESTED):
            continue
        walk(stmt)
    return counts


def _collect(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[list[ast.Assign], list[ast.Call]]:
    assigns: list[ast.Assign] = []
    calls: list[ast.Call] = []

    def walk(node: ast.AST) -> None:
        if isinstance(node, ast.Assign):
            assigns.append(node)
        if isinstance(node, ast.Call):
            calls.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _NESTED):
                continue
            walk(child)

    for stmt in func.body:
        if isinstance(stmt, _NESTED):
            continue
        walk(stmt)
    return assigns, calls


def _importlib_state(name: str, lookup: Callable[[str], Any], shadowed: set[str]) -> str:
    binding = lookup(name)
    matches = (
        binding is not None
        and getattr(binding, "module", None) == "importlib"
        and getattr(binding, "symbol", None) is None
        and getattr(binding, "non_repository", False) is True
        and getattr(binding, "ambiguous", False) is False
    )
    if name in shadowed:
        return "unresolved" if matches or name == "importlib" else "no"
    if matches:
        return "ok"
    return "unresolved" if name == "importlib" else "no"


def _is_import_module_call(call: ast.Call) -> str | None:
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "import_module":
        return None
    if not isinstance(func.value, ast.Name):
        return None
    return func.value.id


def _module_literal(call: ast.Call) -> tuple[str | None, str | None]:
    if any(keyword.arg is None for keyword in call.keywords):
        return None, "COMPUTED_MODULE_NAME"
    named = {keyword.arg: keyword.value for keyword in call.keywords}
    if len(call.args) == 1 and not named:
        value = call.args[0]
    elif not call.args and set(named) == {"name"}:
        value = named["name"]
    else:
        return None, "COMPUTED_MODULE_NAME"
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        literal = value.value
        if literal and not literal.startswith("."):
            return literal, None
    return None, "COMPUTED_MODULE_NAME"


def _symbol_counts(reader: TreeBlobReader, path: str) -> dict[str, int] | None:
    text = reader.text(path)
    if text is None:
        return None
    try:
        parsed = ast.parse(text)
    except SyntaxError:
        return None
    counts: dict[str, int] = {}
    for node in parsed.body if isinstance(parsed, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            counts[node.name] = counts.get(node.name, 0) + 1
    return counts


def _unresolved(
    *,
    file_path: str,
    source_symbol: str,
    reason: str,
    line: int,
    local_name: str | None = None,
    module_literal: str | None = None,
    target_symbol: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "UNRESOLVED_DYNAMIC_BINDING",
        "reason": reason,
        "source_file": file_path,
        "source_symbol": source_symbol,
        "source_line": line,
        "local_name": local_name,
        "module_literal": module_literal,
        "target_symbol": target_symbol,
    }


def scan_literal_import_module_bindings_v1(
    *,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    file_path: str,
    source_symbol: str,
    source_anchor_id: str,
    source_blob_sha: str,
    lookup_binding: Callable[[str], Any],
    shadowed: set[str],
    reader: TreeBlobReader,
    resolve_module_blob: ResolveModule,
) -> dict[str, list[dict[str, Any]]]:
    assigns, calls = _collect(func)
    counts = _assignment_counts(func)
    consumed_binding_calls: set[int] = set()
    candidates: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    modules: dict[str, dict[str, Any]] = {}
    failed_modules: dict[str, dict[str, Any]] = {}

    for call in calls:
        receiver = _is_import_module_call(call)
        if receiver is None:
            continue
        state = _importlib_state(receiver, lookup_binding, shadowed)
        if state == "no":
            continue
        literal, literal_reason = _module_literal(call)
        owner = None
        for assign in assigns:
            if (
                assign.value is call
                and len(assign.targets) == 1
                and isinstance(assign.targets[0], ast.Name)
            ):
                owner = assign.targets[0].id
                break
        if owner is not None:
            consumed_binding_calls.add(id(call))
        if state != "ok" or literal is None or owner is None or counts.get(owner) != 1:
            reason = literal_reason or "RECEIVER_NOT_IMPORTLIB"
            if state == "ok" and literal is not None and (owner is None or counts.get(owner) != 1):
                reason = "BINDING_NOT_UNIQUE"
            if owner is not None and (counts.get(owner) != 1 or literal is None or state != "ok"):
                failed_modules[owner] = {"reason": reason, "module_literal": literal}
            unresolved.append(
                _unresolved(
                    file_path=file_path,
                    source_symbol=source_symbol,
                    reason=reason,
                    line=call.lineno,
                    local_name=owner,
                    module_literal=literal,
                )
            )
            continue
        blob_path, ambiguous, non_repository = resolve_module_blob(reader, [literal])
        if ambiguous or non_repository or blob_path is None:
            reason = "MODULE_AMBIGUOUS" if ambiguous else "MODULE_NOT_IN_TREE"
            unresolved.append(
                _unresolved(
                    file_path=file_path,
                    source_symbol=source_symbol,
                    reason=reason,
                    line=call.lineno,
                    local_name=owner,
                    module_literal=literal,
                )
            )
            if owner is not None and counts.get(owner) == 1:
                failed_modules[owner] = {"reason": reason, "module_literal": literal}
            candidates.append(
                {
                    "local_name": owner,
                    "call_lineno": call.lineno,
                    "module_literal": literal,
                    "status": "UNRESOLVED",
                    "reason": reason,
                    "blob_path": None,
                    "source_file": file_path,
                    "source_symbol": source_symbol,
                }
            )
            continue
        binding = {
            "local_name": owner,
            "call_lineno": call.lineno,
            "module_literal": literal,
            "blob_path": blob_path,
            "source_anchor_id": source_anchor_id,
            "source_blob_sha": source_blob_sha,
        }
        modules[owner] = binding
        candidates.append(
            {
                "local_name": owner,
                "call_lineno": call.lineno,
                "module_literal": literal,
                "status": "MODULE_RESOLVED",
                "reason": None,
                "blob_path": blob_path,
                "source_file": file_path,
                "source_symbol": source_symbol,
            }
        )

    aliases: dict[str, tuple[dict[str, Any], str]] = {}
    ambiguous_aliases: set[str] = set()
    for assign in assigns:
        if len(assign.targets) != 1 or not isinstance(assign.targets[0], ast.Name):
            continue
        alias = assign.targets[0].id
        value = assign.value
        if not isinstance(value, ast.Attribute) or not isinstance(value.value, ast.Name):
            continue
        module_binding = modules.get(value.value.id)
        if module_binding is None:
            continue
        if counts.get(alias) != 1:
            ambiguous_aliases.add(alias)
            continue
        aliases[alias] = (module_binding, value.attr)

    resolved_calls: list[dict[str, Any]] = []

    def resolve_call(
        module_binding: dict[str, Any], target_symbol: str, call: ast.Call, kind: str
    ) -> None:
        counts_in_module = _symbol_counts(reader, module_binding["blob_path"])
        count = None if counts_in_module is None else counts_in_module.get(target_symbol, 0)
        if count != 1:
            reason = "SYMBOL_NOT_UNIQUE" if count and count > 1 else "SYMBOL_ABSENT"
            if counts_in_module is None:
                reason = "MODULE_NOT_IN_TREE"
            unresolved.append(
                _unresolved(
                    file_path=file_path,
                    source_symbol=source_symbol,
                    reason=reason,
                    line=call.lineno,
                    local_name=module_binding["local_name"],
                    module_literal=module_binding["module_literal"],
                    target_symbol=target_symbol,
                )
            )
            return
        resolved_calls.append(
            {
                "source_path": file_path,
                "source_symbol": source_symbol,
                "source_anchor_id": module_binding["source_anchor_id"],
                "source_blob_sha": module_binding["source_blob_sha"],
                "target_path": module_binding["blob_path"],
                "target_symbol": target_symbol,
                "target_module": module_binding["module_literal"],
                "import_lineno": module_binding["call_lineno"],
                "call_lineno": call.lineno,
                "existence": "EXISTS",
                "call_kind": kind,
            }
        )

    for call in calls:
        if id(call) in consumed_binding_calls:
            continue
        func_node = call.func
        if isinstance(func_node, ast.Attribute) and isinstance(func_node.value, ast.Name):
            failed = failed_modules.get(func_node.value.id)
            if failed is not None:
                unresolved.append(
                    _unresolved(
                        file_path=file_path,
                        source_symbol=source_symbol,
                        reason=str(failed["reason"]),
                        line=call.lineno,
                        local_name=func_node.value.id,
                        module_literal=failed["module_literal"],
                        target_symbol=func_node.attr,
                    )
                )
                continue
            module_binding = modules.get(func_node.value.id)
            if module_binding is not None:
                resolve_call(module_binding, func_node.attr, call, "ATTRIBUTE_CALL")
                continue
        if isinstance(func_node, ast.Name) and func_node.id in ambiguous_aliases:
            unresolved.append(
                _unresolved(
                    file_path=file_path,
                    source_symbol=source_symbol,
                    reason="BINDING_NOT_UNIQUE",
                    line=call.lineno,
                    local_name=func_node.id,
                )
            )
            continue
        if isinstance(func_node, ast.Name) and func_node.id in aliases:
            module_binding, target_symbol = aliases[func_node.id]
            resolve_call(module_binding, target_symbol, call, "ALIAS_CALL")

    candidates.sort(key=lambda item: (item["source_file"], item["call_lineno"], item["local_name"]))
    unresolved.sort(
        key=lambda item: (
            item["source_file"],
            item["source_line"],
            item["reason"],
            item["target_symbol"] or "",
        )
    )
    return {
        "candidates": candidates,
        "resolved_calls": resolved_calls,
        "unresolved": unresolved,
    }
