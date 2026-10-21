"""AST facts for one Python blob. Names are not meanings."""

from __future__ import annotations

import ast
from typing import Any

from scripts.ops.current_full_stack_semantic_explorer_v1.constants_v1 import (
    AUTHORITY_FIELDS,
    EXTERNAL_ATTRS,
    EXTERNAL_ROOTS,
    PERSIST_CALLS,
)


def _annotation(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _arg_text(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    return None


def _call_parts(node: ast.AST) -> tuple[str | None, str | None]:
    if isinstance(node, ast.Name):
        return node.id, None
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return node.value.id, node.attr
    return None, None


def _is_external(root: str | None, attr: str | None) -> bool:
    return root in EXTERNAL_ROOTS and (attr is None or attr in EXTERNAL_ATTRS)


def _is_persist(root: str | None, attr: str | None) -> bool:
    if attr is None and root in PERSIST_CALLS:
        return True
    return attr in PERSIST_CALLS


def parse_module_v1(source: str) -> dict[str, Any]:
    tree = ast.parse(source)
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    authority: dict[str, dict[str, Any]] = {}
    exports: list[str] = []
    entrypoint: int | None = None
    function_meaning: dict[str, Any] | None = None

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.names: list[str] = []
            self.current: list[dict[str, Any]] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            qualname = ".".join([*self.names, node.name])
            classes.append({"qualname": qualname, "lineno": node.lineno})
            self.names.append(node.name)
            self.generic_visit(node)
            self.names.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._function(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._function(node)

        def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            qualname = ".".join([*self.names, node.name])
            record: dict[str, Any] = {
                "qualname": qualname,
                "lineno": node.lineno,
                "args": [arg.arg for arg in node.args.args],
                "returns": _annotation(node.returns),
                "calls": [],
                "raises": [],
                "persists": [],
                "external": [],
                "reads": [],
                "writes": [],
            }
            functions.append(record)
            self.names.append(node.name)
            self.current.append(record)
            self.generic_visit(node)
            self.current.pop()
            self.names.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if self.current:
                owner = self.current[-1]
                root, attr = _call_parts(node.func)
                rendered = [_arg_text(item) for item in node.args]
                args = None if any(item is None for item in rendered) else rendered
                if _is_persist(root, attr):
                    kind = "persist"
                    owner["persists"].append({"callee": attr or root or "", "lineno": node.lineno})
                elif _is_external(root, attr):
                    kind = "external"
                    callee = f"{root}.{attr}" if root and attr else (root or attr or "")
                    owner["external"].append({"callee": callee, "lineno": node.lineno})
                else:
                    kind = "plain"
                owner["calls"].append(
                    {"kind": kind, "root": root, "attr": attr, "lineno": node.lineno, "args": args}
                )
            self.generic_visit(node)

        def visit_Raise(self, node: ast.Raise) -> None:
            if self.current:
                name = None
                if isinstance(node.exc, ast.Name):
                    name = node.exc.id
                elif isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                    name = node.exc.func.id
                self.current[-1]["raises"].append({"name": name, "lineno": node.lineno})
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            if self.current and isinstance(node.value, ast.Name) and node.value.id == "self":
                if isinstance(node.ctx, ast.Load):
                    self.current[-1]["reads"].append({"name": node.attr, "lineno": node.lineno})
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            self._assign(node.targets, node.value, node.lineno)
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            self._assign([node.target], node.value, node.lineno)
            self.generic_visit(node)

        def _assign(self, targets: list[ast.expr], value: ast.AST | None, lineno: int) -> None:
            nonlocal function_meaning
            for target in targets:
                if (
                    self.current
                    and isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    self.current[-1]["writes"].append({"name": target.attr, "lineno": lineno})
                if self.names or not isinstance(target, ast.Name):
                    continue
                if (
                    target.id == "__all__"
                    and isinstance(value, ast.List)
                    and all(
                        isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        for elt in value.elts
                    )
                ):
                    exports.extend(
                        str(elt.value) for elt in value.elts if isinstance(elt, ast.Constant)
                    )
                    continue
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    continue
                field = next(
                    (key for key, predicate in AUTHORITY_FIELDS.items() if predicate == target.id),
                    None,
                )
                if field is not None:
                    authority[field] = {"value": value.value, "lineno": lineno}
                if target.id == "FUNCTION_MEANING":
                    function_meaning = {"value": value.value, "lineno": lineno}

        def visit_If(self, node: ast.If) -> None:
            nonlocal entrypoint
            test = node.test
            if (
                not self.names
                and isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"
            ):
                entrypoint = node.lineno
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            imports.append(
                {
                    "lineno": node.lineno,
                    "level": 0,
                    "module": None,
                    "names": [[alias.name, alias.asname] for alias in node.names],
                }
            )

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            imports.append(
                {
                    "lineno": node.lineno,
                    "level": node.level or 0,
                    "module": node.module,
                    "names": [[alias.name, alias.asname] for alias in node.names],
                }
            )

    Visitor().visit(tree)
    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "authority": authority,
        "exports": exports,
        "entrypoint": entrypoint,
        "function_meaning": function_meaning,
    }
