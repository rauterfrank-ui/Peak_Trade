"""Static fail-closed contract: reconciliation Decimal/float owner boundary v0.

Inventories existing reconciliation owners and their declared responsibility boundaries.
Proves ``src/execution/reconciliation.py`` is the precision-relevant execution reconciliation
candidate (Decimal, absolute and relative tolerances) while ``src/ops/recon/reconcile.py``
retains a local ops/drift/observation scope (float, absolute tolerance only). Master V2,
completion, and adapter paths must not import either owner as operative reconciliation SSOT.

Non-authorizing. No runtime, network, testnet execution, owner consolidation, kernel wiring,
or formula duplication.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_V0=true"
AUTHORITY_LIFT = False

CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE = "src/execution/reconciliation.py"
OPS_RECONCILIATION_FLOAT_OBSERVATION_OWNER = "src/ops/recon/reconcile.py"
FUTURE_RECONCILIATION_CONSOLIDATION_MUST_BE_EXPLICIT = True

OwnerRole = Literal[
    "EXECUTION_RECONCILIATION_DECIMAL_CANDIDATE",
    "OPS_RECONCILIATION_FLOAT_OBSERVATION",
    "POSITION_LEDGER_SOURCE",
    "FILL_SOURCE",
    "VALUE_TRANSPORT_ONLY",
]

_BINDING_ROLES: Final[frozenset[str]] = frozenset(
    {
        "MASTER_V2_RECONCILIATION_BINDING",
        "COMPLETION_RECONCILIATION_BINDING",
        "ADAPTER_RECONCILIATION_BINDING",
    }
)

_VALID_OWNER_ROLES: Final[frozenset[str]] = frozenset(
    {
        "EXECUTION_RECONCILIATION_DECIMAL_CANDIDATE",
        "OPS_RECONCILIATION_FLOAT_OBSERVATION",
        "POSITION_LEDGER_SOURCE",
        "FILL_SOURCE",
        "VALUE_TRANSPORT_ONLY",
    }
)


class ReconciliationOwnerRecord(TypedDict):
    path: str
    role: OwnerRole
    number_type: str
    input_units: str
    output_units: str
    sign_convention: str
    absolute_tolerance: bool
    relative_tolerance: bool
    quantization_strategy: str
    fail_closed: bool
    master_v2_relevant: bool
    completion_adapter_relevant: bool
    local_scope_only: bool


RECONCILIATION_OWNER_REGISTRY: tuple[ReconciliationOwnerRecord, ...] = (
    {
        "path": CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE,
        "role": "EXECUTION_RECONCILIATION_DECIMAL_CANDIDATE",
        "number_type": "Decimal",
        "input_units": "quantity:Decimal units; price:Decimal; cash:Decimal",
        "output_units": "ReconDiff with Decimal string details",
        "sign_convention": "signed quantity delta via abs(internal-external)",
        "absolute_tolerance": True,
        "relative_tolerance": True,
        "quantization_strategy": "Decimal max(abs, pct*reference)",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
    },
    {
        "path": OPS_RECONCILIATION_FLOAT_OBSERVATION_OWNER,
        "role": "OPS_RECONCILIATION_FLOAT_OBSERVATION",
        "number_type": "float",
        "input_units": "balance/position snapshots as float dict values",
        "output_units": "DriftReport string observations",
        "sign_convention": "signed float expected/observed via abs(e-o)",
        "absolute_tolerance": True,
        "relative_tolerance": False,
        "quantization_strategy": "none; native float comparison",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
    {
        "path": "src/execution/position_ledger.py",
        "role": "POSITION_LEDGER_SOURCE",
        "number_type": "Decimal",
        "input_units": "fill/order ledger events",
        "output_units": "Position.quantity Decimal",
        "sign_convention": "signed position quantity",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "ledger-owned",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
    {
        "path": "src/execution/order_ledger.py",
        "role": "FILL_SOURCE",
        "number_type": "mixed",
        "input_units": "order/fill events",
        "output_units": "order ledger records",
        "sign_convention": "order-side signed quantity",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "ledger-owned",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
    },
)

_OPERATIVE_RECONCILIATION_MODULES: Final[tuple[str, ...]] = (
    "src.execution.reconciliation",
    "src.ops.recon.reconcile",
)

_OPERATIVE_RECONCILIATION_SUBMODULES: Final[tuple[str, ...]] = (
    "reconciliation",
    "reconcile",
)

_MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS: Final[tuple[Path, ...]] = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py",
    REPO_ROOT / "src" / "ops" / "offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("*.py")),
    *sorted((REPO_ROOT / "src" / "trading" / "master_v2").glob("**/*.py")),
)

_FORBIDDEN_RECONCILIATION_FORMULA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "_reconcile_positions",
        "_reconcile_cash",
        "_determine_position_severity",
        "_create_mock_external_snapshot",
    }
)

_FORBIDDEN_OPERATIVE_RECONCILIATION_CLAIM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "RECONCILIATION_ARITHMETIC_PROVEN",
        "OPERATIVE_RECONCILIATION_EVIDENCE",
        "POSITION_RECONCILIATION_PROVEN",
        "FILL_RECONCILIATION_PROVEN",
        "RECONCILIATION_SSOT_BOUND",
        "RECONCILIATION_OWNER_CONSOLIDATED",
    }
)


def _imports_operative_reconciliation_owner(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                for full_mod in _OPERATIVE_RECONCILIATION_MODULES:
                    if name == full_mod or name.endswith(full_mod.split(".")[-1]):
                        violations.append(f"import {name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod is None:
                continue
            for full_mod in _OPERATIVE_RECONCILIATION_MODULES:
                if mod == full_mod or mod.endswith(full_mod.split(".")[-1]):
                    violations.append(f"from {mod} import ...")
            for sub in _OPERATIVE_RECONCILIATION_SUBMODULES:
                if mod == sub or mod.endswith(f".{sub}") or mod.endswith(sub):
                    violations.append(f"from {mod} import ...")
            if mod == "src.execution":
                for alias in node.names:
                    if alias.name == "reconciliation":
                        violations.append("from src.execution import reconciliation")
            if mod == "src.ops.recon":
                for alias in node.names:
                    if alias.name == "reconcile":
                        violations.append("from src.ops.recon import reconcile")
    return sorted(set(violations))


def _execution_reconciliation_tolerance_fields() -> tuple[str, ...]:
    src = REPO_ROOT / CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fields: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ReconciliationEngine":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and isinstance(
                                    target.value, ast.Name
                                ):
                                    if target.value.id == "self":
                                        fields.append(target.attr)
    return tuple(sorted(set(fields)))


def _ops_reconciliation_tolerance_fields() -> tuple[str, ...]:
    src = REPO_ROOT / OPS_RECONCILIATION_FLOAT_OBSERVATION_OWNER
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fields: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ReconTolerances":
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
    return tuple(sorted(set(fields)))


def test_reconciliation_owner_inventory_complete_and_roles_unique() -> None:
    paths = [record["path"] for record in RECONCILIATION_OWNER_REGISTRY]
    assert len(paths) == len(set(paths)), "duplicate owner paths in registry"
    roles = [record["role"] for record in RECONCILIATION_OWNER_REGISTRY]
    assert all(role in _VALID_OWNER_ROLES for role in roles)
    assert all(role not in _BINDING_ROLES for role in roles)
    for record in RECONCILIATION_OWNER_REGISTRY:
        owner_path = REPO_ROOT / record["path"]
        assert owner_path.is_file(), record["path"]


def test_exactly_one_execution_decimal_reconciliation_candidate() -> None:
    candidates = [
        record["path"]
        for record in RECONCILIATION_OWNER_REGISTRY
        if record["role"] == "EXECUTION_RECONCILIATION_DECIMAL_CANDIDATE"
    ]
    assert candidates == [CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE]
    candidate = next(
        record
        for record in RECONCILIATION_OWNER_REGISTRY
        if record["role"] == "EXECUTION_RECONCILIATION_DECIMAL_CANDIDATE"
    )
    assert candidate["number_type"] == "Decimal"
    assert candidate["absolute_tolerance"] is True
    assert candidate["relative_tolerance"] is True
    assert FUTURE_RECONCILIATION_CONSOLIDATION_MUST_BE_EXPLICIT is True


def test_ops_float_reconciliation_owner_remains_locally_bounded() -> None:
    ops_owner = next(
        record
        for record in RECONCILIATION_OWNER_REGISTRY
        if record["role"] == "OPS_RECONCILIATION_FLOAT_OBSERVATION"
    )
    assert ops_owner["path"] == OPS_RECONCILIATION_FLOAT_OBSERVATION_OWNER
    assert ops_owner["local_scope_only"] is True
    assert ops_owner["master_v2_relevant"] is False
    assert ops_owner["completion_adapter_relevant"] is False
    assert ops_owner["number_type"] == "float"
    assert ops_owner["relative_tolerance"] is False


def test_decimal_float_boundary_explicit_not_interchangeable() -> None:
    execution = next(
        record
        for record in RECONCILIATION_OWNER_REGISTRY
        if record["role"] == "EXECUTION_RECONCILIATION_DECIMAL_CANDIDATE"
    )
    ops = next(
        record
        for record in RECONCILIATION_OWNER_REGISTRY
        if record["role"] == "OPS_RECONCILIATION_FLOAT_OBSERVATION"
    )
    assert execution["number_type"] != ops["number_type"]
    assert execution["input_units"] != ops["input_units"]
    assert execution["output_units"] != ops["output_units"]

    execution_tree = ast.parse(
        (REPO_ROOT / CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE).read_text(encoding="utf-8")
    )
    execution_import_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(execution_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    execution_import_from_roots = {
        node.module.split(".")[0]
        for node in ast.walk(execution_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "decimal" in execution_import_roots | execution_import_from_roots

    ops_src = (REPO_ROOT / OPS_RECONCILIATION_FLOAT_OBSERVATION_OWNER).read_text(encoding="utf-8")
    assert "float(" in ops_src
    assert "Decimal" not in ops_src


def test_absolute_and_relative_tolerance_semantics_not_interchangeable() -> None:
    execution_fields = _execution_reconciliation_tolerance_fields()
    assert "quantity_tolerance_abs" in execution_fields
    assert "quantity_tolerance_pct" in execution_fields
    assert "price_tolerance_pct" in execution_fields

    ops_fields = _ops_reconciliation_tolerance_fields()
    assert ops_fields == ("balance_abs", "position_abs")
    assert not any("pct" in field or "rel" in field or "percent" in field for field in ops_fields)

    execution = next(
        record
        for record in RECONCILIATION_OWNER_REGISTRY
        if record["role"] == "EXECUTION_RECONCILIATION_DECIMAL_CANDIDATE"
    )
    ops = next(
        record
        for record in RECONCILIATION_OWNER_REGISTRY
        if record["role"] == "OPS_RECONCILIATION_FLOAT_OBSERVATION"
    )
    assert execution["absolute_tolerance"] and execution["relative_tolerance"]
    assert ops["absolute_tolerance"] and not ops["relative_tolerance"]
    assert execution["quantization_strategy"] != ops["quantization_strategy"]


def test_master_v2_completion_adapter_paths_import_no_operative_reconciliation_owner() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_operative_reconciliation_owner(tree)
        assert not bad, f"{path.relative_to(REPO_ROOT)}: forbidden reconciliation import: {bad}"
    text = Path(__file__).read_text(encoding="utf-8")
    for key in _FORBIDDEN_OPERATIVE_RECONCILIATION_CLAIM_KEYS:
        assert f"{key}=true" not in text


def test_contract_defines_no_reconciliation_formulas_and_is_non_authorizing() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    assert defined.isdisjoint(_FORBIDDEN_RECONCILIATION_FORMULA_NAMES)
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
