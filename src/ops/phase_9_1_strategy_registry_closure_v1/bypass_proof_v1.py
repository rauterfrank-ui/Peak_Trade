"""Negative proofs: strategies cannot bypass Master V2 / Double Play / Risk / Safety."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from src.ops.phase_9_1_strategy_registry_closure_v1.models_v1 import StrategyRegistryMatrixRowV1
from src.strategies.base import BaseStrategy

_FORBIDDEN_ATTRS = (
    "submit_order",
    "place_order",
    "create_order",
    "send_order",
    "execute_order",
    "apply_fill",
    "create_intent",
    "emit_intent",
)


def _strategy_source_paths(repo_root: Path) -> Tuple[Path, ...]:
    root = repo_root / "src" / "strategies"
    paths = []
    for path in sorted(root.rglob("*.py")):
        if path.name.startswith("__"):
            continue
        if path.name in {"diagnostics.py", "parameters.py"}:
            continue
        paths.append(path)
    return tuple(paths)


def prove_no_direct_order_fill_intent_in_strategy_modules(repo_root: Path) -> Dict[str, Any]:
    hits = []
    for path in _strategy_source_paths(repo_root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            hits.append({"path": str(path), "error": f"syntax:{exc}"})
            continue
        for node in ast.walk(tree):
            name = None
            if isinstance(node, ast.FunctionDef):
                name = node.name
            elif isinstance(node, ast.AsyncFunctionDef):
                name = node.name
            elif isinstance(node, ast.Attribute):
                name = node.attr
            if name in _FORBIDDEN_ATTRS:
                hits.append({"path": str(path.relative_to(repo_root)), "symbol": name})
    return {
        "DIRECT_ORDER_CAPABILITY_ABSENT": len(hits) == 0,
        "DIRECT_FILL_CAPABILITY_ABSENT": len(hits) == 0,
        "DIRECT_INTENT_BYPASS_ABSENT": len(hits) == 0,
        "hits": hits,
        "base_strategy_contract": "generate_signals_only",
        "base_strategy_has_generate_signals": hasattr(BaseStrategy, "generate_signals"),
    }


def prove_matrix_bypass_absent(rows: Iterable[StrategyRegistryMatrixRowV1]) -> Dict[str, Any]:
    rows = tuple(rows)
    return {
        "MASTER_V2_BYPASS_ABSENT": all(not r.MASTER_V2_BYPASS_REACHABLE for r in rows),
        "DOUBLE_PLAY_BYPASS_ABSENT": all(not r.DOUBLE_PLAY_BYPASS_REACHABLE for r in rows),
        "RISK_BYPASS_ABSENT": all(not r.RISK_BYPASS_REACHABLE for r in rows),
        "SAFETY_BYPASS_ABSENT": all(not r.SAFETY_BYPASS_REACHABLE for r in rows),
        "DIRECT_INTENT_BYPASS_ABSENT": all(not r.DIRECT_INTENT_REACHABLE for r in rows),
        "DIRECT_FILL_CAPABILITY_ABSENT": all(not r.DIRECT_FILL_REACHABLE for r in rows),
        "DIRECT_ORDER_CAPABILITY_ABSENT": all(not r.DIRECT_ORDER_REACHABLE for r in rows),
        "LEGACY_PARALLEL_AUTHORITY_ABSENT": all(
            not (r.TARGET_CLASSIFICATION == "LEGACY_DEAUTHORIZED" and r.RUNTIME_REACHABLE)
            for r in rows
        ),
        "row_count": len(rows),
    }


def prove_bypass_boundary_v1(
    *, repo_root: Path, rows: Tuple[StrategyRegistryMatrixRowV1, ...]
) -> Dict[str, Any]:
    module_proof = prove_no_direct_order_fill_intent_in_strategy_modules(repo_root)
    matrix_proof = prove_matrix_bypass_absent(rows)
    ok = all(
        bool(module_proof[k])
        for k in (
            "DIRECT_ORDER_CAPABILITY_ABSENT",
            "DIRECT_FILL_CAPABILITY_ABSENT",
            "DIRECT_INTENT_BYPASS_ABSENT",
        )
    ) and all(
        bool(matrix_proof[k])
        for k in (
            "MASTER_V2_BYPASS_ABSENT",
            "DOUBLE_PLAY_BYPASS_ABSENT",
            "RISK_BYPASS_ABSENT",
            "SAFETY_BYPASS_ABSENT",
            "LEGACY_PARALLEL_AUTHORITY_ABSENT",
        )
    )
    return {
        "ok": ok,
        "module_proof": module_proof,
        "matrix_proof": matrix_proof,
        **{k: matrix_proof[k] for k in matrix_proof if k.endswith("_ABSENT")},
        "DIRECT_ORDER_CAPABILITY_ABSENT": bool(module_proof["DIRECT_ORDER_CAPABILITY_ABSENT"]),
        "DIRECT_FILL_CAPABILITY_ABSENT": bool(module_proof["DIRECT_FILL_CAPABILITY_ABSENT"]),
        "DIRECT_INTENT_BYPASS_ABSENT": bool(module_proof["DIRECT_INTENT_BYPASS_ABSENT"]),
    }
