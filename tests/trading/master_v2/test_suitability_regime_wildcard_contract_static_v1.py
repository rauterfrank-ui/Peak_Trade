# tests/trading/master_v2/test_suitability_regime_wildcard_contract_static_v1.py
"""Static contract: single-owner Suitability regime wildcard '*' semantics."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OWNER = REPO_ROOT / "src" / "trading" / "master_v2" / "suitability_binding_v1.py"
ADAPTER = REPO_ROOT / "src" / "strategies" / "suitability_registry_adapter_v1.py"


def _function_defs_named(path: Path, name: str) -> list[ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]


def test_single_owner_strategy_supports_regime_v1() -> None:
    owners = _function_defs_named(OWNER, "strategy_supports_regime_v1")
    assert len(owners) == 1
    src_root = REPO_ROOT / "src"
    duplicates: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        if path.resolve() == OWNER.resolve():
            continue
        if _function_defs_named(path, "strategy_supports_regime_v1"):
            duplicates.append(path.relative_to(REPO_ROOT).as_posix())
    assert duplicates == []


def test_wildcard_semantics_frozen_in_owner() -> None:
    source = OWNER.read_text(encoding="utf-8")
    assert '_REGIME_WILDCARD_TOKEN = "*"' in source
    assert "normalized in supported or _REGIME_WILDCARD_TOKEN in supported" in source
    assert "def strategy_supports_regime_v1(" in source
    assert "def regime_wildcard_matched_v1(" in source
    assert "def _strategy_supports_regime(" in source
    tree = ast.parse(source)
    helpers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_strategy_supports_regime"
    ]
    assert len(helpers) == 1
    helper_src = ast.get_source_segment(source, helpers[0])
    assert helper_src is not None
    assert "strategy_supports_regime_v1(" in helper_src
    assert "_REGIME_WILDCARD_TOKEN" not in helper_src


def test_adapter_does_not_reimplement_wildcard_match() -> None:
    source = ADAPTER.read_text(encoding="utf-8")
    assert "strategy_supports_regime_v1" not in source
    assert "normalized in supported or" not in source
    assert "_REGIME_WILDCARD_TOKEN" not in source
