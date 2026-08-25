"""AST inventory of named forensic guards. Definition is not protection."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    DEAD_UNWIRED_GUARD_BASELINE,
)

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parents[2]


def _iter_python_files() -> list[Path]:
    return sorted(path for path in _PACKAGE_DIR.rglob("*.py") if path.suffix == ".py")


def inventory_named_guards(
    names: tuple[str, ...] = DEAD_UNWIRED_GUARD_BASELINE,
) -> dict[str, dict[str, Any]]:
    defined: dict[str, str] = {}
    called: dict[str, list[str]] = {name: [] for name in names}
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = str(path.relative_to(_REPO_ROOT))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in names:
                defined[node.name] = f"{rel}:{node.lineno}"
            if isinstance(node, ast.Call):
                func = node.func
                ident = None
                if isinstance(func, ast.Name):
                    ident = func.id
                elif isinstance(func, ast.Attribute):
                    ident = func.attr
                if ident in names:
                    called[ident].append(f"{rel}:{node.lineno}")
    inventory: dict[str, dict[str, Any]] = {}
    for name in names:
        sites = sorted(set(called[name]))
        inventory[name] = {
            "DEFINED": name in defined,
            "DEFINED_AT": defined.get(name),
            "CALLED": bool(sites),
            "CALL_SITES": sites,
            "REACHABLE": bool(sites),
            "COVERED_BY_ACTIVE_EQUIVALENT": bool(sites),
            "TESTED": False,
        }
    return inventory
