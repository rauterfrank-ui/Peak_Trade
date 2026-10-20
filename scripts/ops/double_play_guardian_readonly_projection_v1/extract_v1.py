"""Read-only extractors. No guardian, graph, or trading execution."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


def read_text_v1(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def read_json_object_v1(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return payload


def extract_constant_assignments_v1(path: Path, names: frozenset[str]) -> dict[str, Any] | None:
    text = read_text_v1(path)
    if text is None:
        return None
    parsed = ast.parse(text)
    found: dict[str, Any] = {}
    for node in parsed.body:
        targets: list[ast.expr]
        value: ast.expr | None
        if isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        elif isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        else:
            continue
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in names:
                found[target.id] = ast.literal_eval(value)
    return found


def path_is_inside_v1(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
