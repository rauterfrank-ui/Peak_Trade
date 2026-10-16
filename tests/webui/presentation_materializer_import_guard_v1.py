"""AST import guards for presentation archive materializers (WP-R1 extraction).

Guards enforce:
- no productive Ops → WebUI imports (``src.webui.*`` / ``webui.*``)
- no forbidden domain roots (trading, backtest, …) per test
- no forbidden direct call names (KillSwitch, compose_*, …)

``src.ops.*`` imports are allowed (including workflow archive projections).
"""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_WEBUI_MODULE_PREFIXES: tuple[str, ...] = (
    "src.webui.",
    "webui.",
)


def absolute_import_module_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                modules.append(node.module)
    return modules


def assert_import_modules_allowed(
    modules: list[str],
    *,
    forbidden_roots: frozenset[str] | None = None,
    forbidden_module_prefixes: tuple[str, ...] = FORBIDDEN_WEBUI_MODULE_PREFIXES,
    forbidden_module_substrings: tuple[str, ...] = (),
) -> None:
    roots = forbidden_roots or frozenset()
    for mod in modules:
        for prefix in forbidden_module_prefixes:
            bare = prefix.rstrip(".")
            if mod == bare or mod.startswith(prefix):
                raise AssertionError(f"forbidden webui import: {mod}")
        root = mod.split(".", 1)[0]
        if root in roots:
            raise AssertionError(f"forbidden import root {root!r}: {mod}")
        for sub in forbidden_module_substrings:
            if sub in mod:
                raise AssertionError(f"forbidden import substring {sub!r}: {mod}")


def assert_forbidden_direct_calls_absent(path: Path, forbidden_call_names: frozenset[str]) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in forbidden_call_names:
                raise AssertionError(f"forbidden call: {node.func.id}")


def assert_presentation_materializer_import_guard_v1(
    path: Path,
    *,
    forbidden_call_names: frozenset[str],
    forbidden_roots: frozenset[str] | None = None,
    forbidden_module_substrings: tuple[str, ...] = (),
) -> None:
    modules = absolute_import_module_names(path)
    assert_import_modules_allowed(
        modules,
        forbidden_roots=forbidden_roots,
        forbidden_module_substrings=forbidden_module_substrings,
    )
    assert_forbidden_direct_calls_absent(path, forbidden_call_names)
