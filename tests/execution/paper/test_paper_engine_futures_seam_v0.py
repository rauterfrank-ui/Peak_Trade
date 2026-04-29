"""Characterization tests: PaperExecutionEngine (WP1B) vs pure Futures Paper Accounting v0.

Non-authorizing: documents current import/runtime boundaries only — no wiring, no source edits.
See MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0 (WP1B spot-sim vs offline futures kernel).
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_PAPER_PKG = Path(__file__).resolve().parents[3] / "src" / "execution" / "paper"
_FUTURES_ACCOUNTING_SRC = _PAPER_PKG / "futures_accounting.py"
_ENGINE_SRC = _PAPER_PKG / "engine.py"
_FUTURES_TYPE_NAMES = frozenset(
    {
        "FuturesInstrumentSpec",
        "FuturesMarginSpec",
        "FuturesSide",
        "FuturesPosition",
        "LiquidationProximityV0",
    }
)


def _paper_py_modules_except_futures_accounting() -> list[Path]:
    return sorted(p for p in _PAPER_PKG.glob("*.py") if p.name != "futures_accounting.py")


def _imports_futures_accounting_submodule(tree: ast.AST) -> list[str]:
    """Return human-readable violations if this AST imports the futures_accounting submodule."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "futures_accounting" or name.endswith(".futures_accounting"):
                    violations.append(f"import {name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod is not None and (
                mod == "futures_accounting"
                or mod.endswith(".futures_accounting")
                or mod == "src.execution.paper.futures_accounting"
            ):
                violations.append(f"from {mod} import ...")
            if mod == "src.execution.paper":
                for a in node.names:
                    if a.name == "futures_accounting":
                        violations.append("from src.execution.paper import futures_accounting")
            if mod is None:
                for a in node.names:
                    if a.name == "futures_accounting":
                        violations.append("relative import of futures_accounting")
    return violations


def test_paper_package_modules_do_not_import_futures_accounting_kernel() -> None:
    """WP1B-related paper modules must not bind to the offline futures accounting kernel."""

    for path in _paper_py_modules_except_futures_accounting():
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        bad = _imports_futures_accounting_submodule(tree)
        assert not bad, f"{path.name}: forbidden import of futures accounting: {bad}"


def test_futures_accounting_kernel_imports_remain_stdlib_only() -> None:
    """Pure kernel: no paper engine/broker/journal, no authority or I/O stacks."""

    allowed_roots = frozenset({"__future__", "dataclasses", "decimal", "enum", "typing"})
    text = _FUTURES_ACCOUNTING_SRC.read_text(encoding="utf-8")
    tree = ast.parse(text)
    banned_substrings = (
        "master_v2",
        "ccxt",
        "requests",
        "urllib",
        "socket",
        "paper.engine",
        "paper.broker",
        "paper.journal",
        "PaperExecutionEngine",
        "PaperBroker",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name or ""
                assert mod.split(".")[0] not in ("src", "execution"), mod
                for b in banned_substrings:
                    assert b not in mod, mod
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None, "relative imports not expected in futures_accounting"
            mod = node.module
            root = mod.split(".")[0]
            assert root in allowed_roots, f"unexpected import root {root!r} from {mod}"
            for b in banned_substrings:
                assert b not in mod, mod


def test_paper_execution_engine_source_has_no_futures_accounting_type_references() -> None:
    """PaperExecutionEngine implementation is spot-path typed; no futures DTO symbols."""

    text = _ENGINE_SRC.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in _FUTURES_TYPE_NAMES:
            pytest.fail(f"{_ENGINE_SRC.name}: unexpected Name reference {node.id!r}")
        if isinstance(node, ast.Attribute) and node.attr in _FUTURES_TYPE_NAMES:
            pytest.fail(f"{_ENGINE_SRC.name}: unexpected Attribute {node.attr!r}")


def test_import_engine_and_futures_accounting_modules_without_coupling() -> None:
    """Both surfaces may be loaded in one process; no cross-import between these packages' code."""

    acc = importlib.import_module("src.execution.paper.futures_accounting")
    eng = importlib.import_module("src.execution.paper.engine")
    assert acc is not eng
    assert hasattr(acc, "FuturesInstrumentSpec")
    assert hasattr(eng, "PaperExecutionEngine")


def test_futures_accounting_and_engine_package_exports_characterization() -> None:
    """Smoke: public symbols exist; paper package __init__ stays futures-accounting-free."""

    acc = importlib.import_module("src.execution.paper.futures_accounting")
    assert callable(getattr(acc, "notional_value", None))
    pkg = importlib.import_module("src.execution.paper")
    public = set(getattr(pkg, "__all__", ()))
    assert "FuturesInstrumentSpec" not in public
    assert "PaperExecutionEngine" in public
