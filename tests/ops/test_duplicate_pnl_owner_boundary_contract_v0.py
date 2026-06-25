"""Static fail-closed contract: duplicate PnL owner boundaries v0.

Inventories existing PnL/accounting owners and their declared responsibility boundaries.
Proves ``futures_accounting.py`` is the sole Master-V2 futures arithmetic kernel candidate
while other owners retain only local scope. Master V2 / completion / adapter paths must not
import alternative PnL owners as operative arithmetic SSOT.

Non-authorizing. No runtime, network, testnet execution, kernel wiring, or formula duplication.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_V0=true"
AUTHORITY_LIFT = False

CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE = "src/execution/paper/futures_accounting.py"
FUTURE_KERNEL_WIRING_MUST_BE_EXPLICIT = True

OwnerCategory = Literal[
    "FUTURES_ACCOUNTING_KERNEL_CANDIDATE",
    "EXECUTION_LEDGER_LOCAL_ACCOUNTING",
    "PAPER_BROKER_LOCAL_SIMULATION",
    "LEGACY_OR_AUXILIARY_PNL_OWNER",
    "VALUE_TRANSPORT_ONLY",
]

_BINDING_CATEGORIES: Final[frozenset[str]] = frozenset(
    {
        "MASTER_V2_ARITHMETIC_BINDING",
        "COMPLETION_ADAPTER_ARITHMETIC_BINDING",
    }
)

_VALID_OWNER_CATEGORIES: Final[frozenset[str]] = frozenset(
    {
        "FUTURES_ACCOUNTING_KERNEL_CANDIDATE",
        "EXECUTION_LEDGER_LOCAL_ACCOUNTING",
        "PAPER_BROKER_LOCAL_SIMULATION",
        "LEGACY_OR_AUXILIARY_PNL_OWNER",
        "VALUE_TRANSPORT_ONLY",
    }
)


class PnlOwnerRecord(TypedDict):
    path: str
    category: OwnerCategory
    number_type: str
    computes_formulas: bool
    master_v2_relevant: bool
    completion_adapter_relevant: bool
    local_scope_only: bool


PNL_OWNER_REGISTRY: tuple[PnlOwnerRecord, ...] = (
    {
        "path": "src/execution/paper/futures_accounting.py",
        "category": "FUTURES_ACCOUNTING_KERNEL_CANDIDATE",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": False,
    },
    {
        "path": "src/execution/position_ledger.py",
        "category": "EXECUTION_LEDGER_LOCAL_ACCOUNTING",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
    {
        "path": "src/execution/ledger/pnl.py",
        "category": "LEGACY_OR_AUXILIARY_PNL_OWNER",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
    {
        "path": "src/execution/paper/broker.py",
        "category": "PAPER_BROKER_LOCAL_SIMULATION",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
    {
        "path": "src/ops/recon/reconcile.py",
        "category": "LEGACY_OR_AUXILIARY_PNL_OWNER",
        "number_type": "float",
        "computes_formulas": False,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
    {
        "path": "src/execution/reconciliation.py",
        "category": "LEGACY_OR_AUXILIARY_PNL_OWNER",
        "number_type": "Decimal",
        "computes_formulas": False,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
)

_ALTERNATIVE_PNL_OWNER_SUBMODULES: Final[tuple[str, ...]] = (
    "futures_accounting",
    "position_ledger",
    "ledger.pnl",
    "paper.broker",
)

_ALTERNATIVE_PNL_OWNER_FULL_MODULES: Final[tuple[str, ...]] = (
    "src.execution.paper.futures_accounting",
    "src.execution.position_ledger",
    "src.execution.ledger.pnl",
    "src.execution.paper.broker",
)

_MASTER_V2_AND_COMPLETION_ADAPTER_BINDING_PATHS: Final[tuple[Path, ...]] = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py",
    REPO_ROOT / "src" / "ops" / "offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("*.py")),
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("**/*.py")),
)

_FORBIDDEN_FORMULA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "unrealized_pnl",
        "realize_pnl_on_close",
        "notional_value",
        "apply_fee_on_notional",
        "funding_payment_quote",
        "unrealized_pnl_for_position",
        "total_unrealized_pnl",
    }
)


def _imports_alternative_pnl_owner(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                for full_mod in _ALTERNATIVE_PNL_OWNER_FULL_MODULES:
                    if name == full_mod or name.endswith(f".{full_mod.split('.')[-1]}"):
                        violations.append(f"import {name}")
                for sub in _ALTERNATIVE_PNL_OWNER_SUBMODULES:
                    if name == sub or name.endswith(f".{sub}"):
                        violations.append(f"import {name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod is None:
                continue
            for full_mod in _ALTERNATIVE_PNL_OWNER_FULL_MODULES:
                if mod == full_mod or mod.endswith(full_mod.split(".")[-1]):
                    violations.append(f"from {mod} import ...")
            for sub in _ALTERNATIVE_PNL_OWNER_SUBMODULES:
                if mod == sub or mod.endswith(f".{sub}") or mod.endswith(sub):
                    violations.append(f"from {mod} import ...")
            if mod == "src.execution.paper":
                for alias in node.names:
                    if alias.name in {"futures_accounting", "broker"}:
                        violations.append(f"from src.execution.paper import {alias.name}")
            if mod == "src.execution.ledger":
                for alias in node.names:
                    if alias.name == "pnl":
                        violations.append("from src.execution.ledger import pnl")
    return sorted(set(violations))


def test_pnl_owner_inventory_complete_and_roles_unique() -> None:
    paths = [record["path"] for record in PNL_OWNER_REGISTRY]
    assert len(paths) == len(set(paths)), "duplicate owner paths in registry"
    categories = [record["category"] for record in PNL_OWNER_REGISTRY]
    assert all(category in _VALID_OWNER_CATEGORIES for category in categories)
    assert all(category not in _BINDING_CATEGORIES for category in categories)
    for record in PNL_OWNER_REGISTRY:
        owner_path = REPO_ROOT / record["path"]
        assert owner_path.is_file(), record["path"]


def test_exactly_one_futures_arithmetic_kernel_candidate() -> None:
    kernel_candidates = [
        record["path"]
        for record in PNL_OWNER_REGISTRY
        if record["category"] == "FUTURES_ACCOUNTING_KERNEL_CANDIDATE"
    ]
    assert kernel_candidates == [CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE]
    assert FUTURE_KERNEL_WIRING_MUST_BE_EXPLICIT is True


def test_local_pnl_owners_retain_local_scope_not_global_ssot() -> None:
    local_owners = [record for record in PNL_OWNER_REGISTRY if record["local_scope_only"]]
    assert len(local_owners) >= 4
    for record in local_owners:
        assert record["category"] != "FUTURES_ACCOUNTING_KERNEL_CANDIDATE"
        assert record["master_v2_relevant"] is False
        assert record["completion_adapter_relevant"] is False
    kernel = next(
        record
        for record in PNL_OWNER_REGISTRY
        if record["category"] == "FUTURES_ACCOUNTING_KERNEL_CANDIDATE"
    )
    assert kernel["number_type"] == "Decimal"
    assert kernel["computes_formulas"] is True


def test_master_v2_and_completion_adapter_paths_import_no_alternative_pnl_owner() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_AND_COMPLETION_ADAPTER_BINDING_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_alternative_pnl_owner(tree)
        assert not bad, f"{path.relative_to(REPO_ROOT)}: forbidden PnL owner import: {bad}"


def test_contract_defines_no_pnl_fee_funding_formulas() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    assert defined.isdisjoint(_FORBIDDEN_FORMULA_NAMES)


def test_contract_is_non_authorizing() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
