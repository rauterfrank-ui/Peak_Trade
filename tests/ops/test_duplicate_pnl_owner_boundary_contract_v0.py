"""Static fail-closed contract: duplicate PnL owner boundaries v0.

Package A Slice A1 (INV-021) formalises futures PnL ownership and import boundaries.

Inventories existing PnL/accounting owners and their declared responsibility boundaries.
Declares ``futures_accounting.py`` as the sole canonical futures PnL kernel candidate while
``position_ledger.py`` and ``ledger/pnl.py`` retain only local ledger/accounting scope and
must not be interpreted as alternative Master-V2 futures PnL kernels. Master V2 / completion /
adapter paths must not import alternative PnL owners as operative arithmetic SSOT.

Kernel wiring, decimal/float seam binding, and equity-identity proof are explicitly outside
A1 (deferred to separate GO / A2 INV-048). Cross-reference only:
``tests/ops/test_master_v2_arithmetic_kernel_seam_fail_closed_contract_v0.py``.

Non-authorizing. No runtime, network, testnet execution, kernel wiring, or formula duplication.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_V0=true"
AUTHORITY_LIFT = False
A2_ARITHMETIC_OUT_OF_SCOPE = True
KERNEL_WIRING_OUT_OF_SCOPE = True
EQUITY_IDENTITY_PROOF_OUT_OF_SCOPE = True

CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE = "src/execution/paper/futures_accounting.py"
FUTURE_KERNEL_WIRING_MUST_BE_EXPLICIT = True

INV021_TRIPLE_OWNER_PATHS: Final[tuple[str, ...]] = (
    "src/execution/paper/futures_accounting.py",
    "src/execution/position_ledger.py",
    "src/execution/ledger/pnl.py",
)

INV021_PARALLEL_LOCAL_PNL_OWNER_PATHS: Final[tuple[str, ...]] = (
    "src/execution/position_ledger.py",
    "src/execution/ledger/pnl.py",
)

SEAM_CONTRACT_CROSS_REFERENCE = (
    "tests/ops/test_master_v2_arithmetic_kernel_seam_fail_closed_contract_v0.py"
)

OwnerCategory = Literal[
    "FUTURES_ACCOUNTING_KERNEL_CANDIDATE",
    "EXECUTION_LEDGER_LOCAL_ACCOUNTING",
    "PAPER_BROKER_LOCAL_SIMULATION",
    "LEGACY_OR_AUXILIARY_PNL_OWNER",
    "VALUE_TRANSPORT_ONLY",
]

ImportDirection = Literal["FORBIDDEN", "ALLOWED_FUTURE_EXPLICIT_GO"]

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
    responsibility_scope: str
    forbidden_as_master_v2_pnl_kernel: bool
    equity_identity_scope: str
    pnl_surface_symbols: tuple[str, ...]


class ImportDirectionRule(TypedDict):
    source_path: str
    target_module: str
    direction: ImportDirection
    boundary: str


class PnlOwnerDesignSpecV0(TypedDict):
    package_slice: str
    inventory_id: str
    kernel_candidate_path: str
    future_kernel_wiring_must_be_explicit: bool
    parallel_local_owner_paths: tuple[str, ...]
    seam_contract_cross_reference: str
    a2_arithmetic_out_of_scope: bool
    kernel_wiring_out_of_scope: bool
    equity_identity_proof_out_of_scope: bool


PNL_OWNER_DESIGN_SPEC_V0: PnlOwnerDesignSpecV0 = {
    "package_slice": "PACKAGE_A_SLICE_A1",
    "inventory_id": "INV-021",
    "kernel_candidate_path": CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE,
    "future_kernel_wiring_must_be_explicit": True,
    "parallel_local_owner_paths": INV021_PARALLEL_LOCAL_PNL_OWNER_PATHS,
    "seam_contract_cross_reference": SEAM_CONTRACT_CROSS_REFERENCE,
    "a2_arithmetic_out_of_scope": True,
    "kernel_wiring_out_of_scope": True,
    "equity_identity_proof_out_of_scope": True,
}

IMPORT_DIRECTION_RULES_V0: tuple[ImportDirectionRule, ...] = (
    {
        "source_path": "src/trading/master_v2/",
        "target_module": "src.execution.position_ledger",
        "direction": "FORBIDDEN",
        "boundary": "Master V2 must not import position_ledger as operative PnL SSOT",
    },
    {
        "source_path": "src/trading/master_v2/",
        "target_module": "src.execution.ledger.pnl",
        "direction": "FORBIDDEN",
        "boundary": "Master V2 must not import ledger.pnl as operative PnL SSOT",
    },
    {
        "source_path": "src/trading/master_v2/",
        "target_module": "src.execution.paper.broker",
        "direction": "FORBIDDEN",
        "boundary": "Master V2 must not import paper.broker as operative PnL SSOT",
    },
    {
        "source_path": "src/ops/bounded_master_v2_testnet_completion_path_wiring_v0.py",
        "target_module": "src.execution.position_ledger",
        "direction": "FORBIDDEN",
        "boundary": "Completion wiring must not import position_ledger as operative PnL SSOT",
    },
    {
        "source_path": "src/ops/bounded_master_v2_testnet_completion_path_wiring_v0.py",
        "target_module": "src.execution.ledger.pnl",
        "direction": "FORBIDDEN",
        "boundary": "Completion wiring must not import ledger.pnl as operative PnL SSOT",
    },
    {
        "source_path": "src/execution/position_ledger.py",
        "target_module": "src.execution.paper.futures_accounting",
        "direction": "FORBIDDEN",
        "boundary": "position_ledger must not delegate operative SSOT to futures_accounting",
    },
    {
        "source_path": "src/execution/ledger/pnl.py",
        "target_module": "src.execution.paper.futures_accounting",
        "direction": "FORBIDDEN",
        "boundary": "ledger.pnl must not delegate operative SSOT to futures_accounting",
    },
    {
        "source_path": "src/execution/paper/futures_accounting.py",
        "target_module": "src.execution.position_ledger",
        "direction": "FORBIDDEN",
        "boundary": "futures_accounting kernel must remain pure/offline without ledger imports",
    },
    {
        "source_path": "src/execution/paper/futures_accounting.py",
        "target_module": "src.execution.ledger.pnl",
        "direction": "FORBIDDEN",
        "boundary": "futures_accounting kernel must remain pure/offline without ledger imports",
    },
    {
        "source_path": "src/trading/master_v2/",
        "target_module": "src.execution.paper.futures_accounting",
        "direction": "ALLOWED_FUTURE_EXPLICIT_GO",
        "boundary": "Future kernel wiring only via separate explicit GO — not authorized by A1",
    },
)

PNL_OWNER_REGISTRY: tuple[PnlOwnerRecord, ...] = (
    {
        "path": "src/execution/paper/futures_accounting.py",
        "category": "FUTURES_ACCOUNTING_KERNEL_CANDIDATE",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": False,
        "responsibility_scope": (
            "Futures unrealized/realized PnL, notional, margin estimates, funding placeholder"
        ),
        "forbidden_as_master_v2_pnl_kernel": False,
        "equity_identity_scope": (
            "Snapshot bundles realized+unrealized+fees+funding; full identity proof deferred to A2"
        ),
        "pnl_surface_symbols": (
            "unrealized_pnl",
            "realize_pnl_on_close",
            "notional_value",
            "apply_fee_on_notional",
            "funding_payment_quote",
            "build_futures_paper_accounting_snapshot_v0",
        ),
    },
    {
        "path": "src/execution/position_ledger.py",
        "category": "EXECUTION_LEDGER_LOCAL_ACCOUNTING",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "responsibility_scope": (
            "Spot-oriented execution ledger — cash, fills, per-symbol positions only"
        ),
        "forbidden_as_master_v2_pnl_kernel": True,
        "equity_identity_scope": (
            "Local ledger only: equity = cash + total_unrealized_pnl(mark_prices)"
        ),
        "pnl_surface_symbols": (
            "Position.unrealized_pnl",
            "get_total_realized_pnl",
            "get_total_unrealized_pnl",
            "get_equity",
        ),
    },
    {
        "path": "src/execution/ledger/pnl.py",
        "category": "LEGACY_OR_AUXILIARY_PNL_OWNER",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "responsibility_scope": (
            "FIFO ledger unrealized aggregation with QuantizationPolicy — auxiliary only"
        ),
        "forbidden_as_master_v2_pnl_kernel": True,
        "equity_identity_scope": "Aggregated unrealized only — no global equity SSOT claim",
        "pnl_surface_symbols": (
            "unrealized_pnl_for_position",
            "total_unrealized_pnl",
        ),
    },
    {
        "path": "src/execution/paper/broker.py",
        "category": "PAPER_BROKER_LOCAL_SIMULATION",
        "number_type": "Decimal",
        "computes_formulas": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "responsibility_scope": "Paper broker local simulation accounting",
        "forbidden_as_master_v2_pnl_kernel": True,
        "equity_identity_scope": "Broker-local simulation only — not futures kernel SSOT",
        "pnl_surface_symbols": (),
    },
    {
        "path": "src/ops/recon/reconcile.py",
        "category": "LEGACY_OR_AUXILIARY_PNL_OWNER",
        "number_type": "float",
        "computes_formulas": False,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "responsibility_scope": "Float reconciliation compare — value transport only",
        "forbidden_as_master_v2_pnl_kernel": True,
        "equity_identity_scope": "Compare-only — no operative equity SSOT",
        "pnl_surface_symbols": (),
    },
    {
        "path": "src/execution/reconciliation.py",
        "category": "LEGACY_OR_AUXILIARY_PNL_OWNER",
        "number_type": "Decimal",
        "computes_formulas": False,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "responsibility_scope": "Decimal reconciliation compare — value transport only",
        "forbidden_as_master_v2_pnl_kernel": True,
        "equity_identity_scope": "Compare-only — no operative equity SSOT",
        "pnl_surface_symbols": (),
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

_KERNEL_PURITY_FORBIDDEN_IMPORTS: Final[tuple[str, ...]] = (
    "src.execution.position_ledger",
    "src.execution.ledger.pnl",
    "src.execution.paper.broker",
    "position_ledger",
    "ledger.pnl",
)


def _registry_by_path(path: str) -> PnlOwnerRecord:
    for record in PNL_OWNER_REGISTRY:
        if record["path"] == path:
            return record
    raise KeyError(f"missing registry record for owner path: {path}")


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


def _imports_module(tree: ast.AST, target_modules: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                for target in target_modules:
                    if name == target or name.endswith(f".{target.split('.')[-1]}"):
                        violations.append(f"import {name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod is None:
                continue
            for target in target_modules:
                if mod == target or mod.endswith(target):
                    violations.append(f"from {mod} import ...")
    return sorted(set(violations))


def _production_symbols_exist(owner_path: str, symbols: tuple[str, ...]) -> None:
    source_path = REPO_ROOT / owner_path
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    defined_classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for symbol in symbols:
        if "." in symbol:
            class_name, method_name = symbol.split(".", 1)
            class_nodes = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef) and node.name == class_name
            ]
            assert class_nodes, f"{owner_path}: missing class {class_name}"
            method_names = {
                child.name
                for class_node in class_nodes
                for child in class_node.body
                if isinstance(child, ast.FunctionDef)
            }
            assert method_name in method_names, f"{owner_path}: missing method {symbol}"
            continue
        assert symbol in defined_functions or symbol in defined_classes, (
            f"{owner_path}: missing production symbol reference {symbol}"
        )


def test_pnl_owner_inventory_complete_and_roles_unique() -> None:
    paths = [record["path"] for record in PNL_OWNER_REGISTRY]
    assert len(paths) == len(set(paths)), "duplicate owner paths in registry"
    categories = [record["category"] for record in PNL_OWNER_REGISTRY]
    assert all(category in _VALID_OWNER_CATEGORIES for category in categories)
    assert all(category not in _BINDING_CATEGORIES for category in categories)
    for record in PNL_OWNER_REGISTRY:
        owner_path = REPO_ROOT / record["path"]
        assert owner_path.is_file(), record["path"]
        assert record["responsibility_scope"].strip(), record["path"]
        assert record["equity_identity_scope"].strip(), record["path"]
        assert isinstance(record["pnl_surface_symbols"], tuple)

    inv021_records = [_registry_by_path(path) for path in INV021_TRIPLE_OWNER_PATHS]
    assert {record["path"] for record in inv021_records} == set(INV021_TRIPLE_OWNER_PATHS)
    for record in inv021_records:
        assert record["pnl_surface_symbols"], record["path"]
        _production_symbols_exist(record["path"], record["pnl_surface_symbols"])

    assert PNL_OWNER_DESIGN_SPEC_V0["inventory_id"] == "INV-021"
    assert PNL_OWNER_DESIGN_SPEC_V0["kernel_candidate_path"] == (
        CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE
    )
    assert PNL_OWNER_DESIGN_SPEC_V0["parallel_local_owner_paths"] == (
        INV021_PARALLEL_LOCAL_PNL_OWNER_PATHS
    )

    covered_local_paths = {
        rule["source_path"]
        for rule in IMPORT_DIRECTION_RULES_V0
        if rule["direction"] == "FORBIDDEN"
        and rule["target_module"] == "src.execution.paper.futures_accounting"
        and rule["source_path"].endswith(".py")
    }
    assert covered_local_paths == set(INV021_PARALLEL_LOCAL_PNL_OWNER_PATHS)

    kernel_rule_targets = {
        rule["target_module"]
        for rule in IMPORT_DIRECTION_RULES_V0
        if rule["source_path"].startswith("src/trading/master_v2/")
        and rule["direction"] == "FORBIDDEN"
    }
    assert "src.execution.position_ledger" in kernel_rule_targets
    assert "src.execution.ledger.pnl" in kernel_rule_targets


def test_exactly_one_futures_arithmetic_kernel_candidate() -> None:
    kernel_candidates = [
        record["path"]
        for record in PNL_OWNER_REGISTRY
        if record["category"] == "FUTURES_ACCOUNTING_KERNEL_CANDIDATE"
    ]
    assert kernel_candidates == [CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE]
    assert FUTURE_KERNEL_WIRING_MUST_BE_EXPLICIT is True
    assert (
        PNL_OWNER_DESIGN_SPEC_V0["kernel_candidate_path"]
        == CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE
    )
    assert (REPO_ROOT / SEAM_CONTRACT_CROSS_REFERENCE).is_file()

    non_kernel_records = [
        record
        for record in PNL_OWNER_REGISTRY
        if record["category"] != "FUTURES_ACCOUNTING_KERNEL_CANDIDATE"
    ]
    assert all(record["forbidden_as_master_v2_pnl_kernel"] for record in non_kernel_records)

    kernel = _registry_by_path(CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE)
    assert kernel["forbidden_as_master_v2_pnl_kernel"] is False
    assert kernel["local_scope_only"] is False
    assert kernel["master_v2_relevant"] is True

    future_go_rules = [
        rule
        for rule in IMPORT_DIRECTION_RULES_V0
        if rule["direction"] == "ALLOWED_FUTURE_EXPLICIT_GO"
    ]
    assert len(future_go_rules) == 1
    assert future_go_rules[0]["target_module"] == "src.execution.paper.futures_accounting"


def test_local_pnl_owners_retain_local_scope_not_global_ssot() -> None:
    local_owners = [record for record in PNL_OWNER_REGISTRY if record["local_scope_only"]]
    assert len(local_owners) >= 4
    for record in local_owners:
        assert record["category"] != "FUTURES_ACCOUNTING_KERNEL_CANDIDATE"
        assert record["master_v2_relevant"] is False
        assert record["completion_adapter_relevant"] is False
        assert record["forbidden_as_master_v2_pnl_kernel"] is True

    kernel = _registry_by_path(CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE)
    assert kernel["number_type"] == "Decimal"
    assert kernel["computes_formulas"] is True

    for path in INV021_PARALLEL_LOCAL_PNL_OWNER_PATHS:
        record = _registry_by_path(path)
        assert record["local_scope_only"] is True
        assert record["forbidden_as_master_v2_pnl_kernel"] is True
        assert record["equity_identity_scope"] != kernel["equity_identity_scope"]
        tree = ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))
        bad = _imports_module(
            tree, ("src.execution.paper.futures_accounting", "futures_accounting")
        )
        assert not bad, f"{path}: parallel owner must not import futures_accounting kernel: {bad}"


def test_master_v2_and_completion_adapter_paths_import_no_alternative_pnl_owner() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_AND_COMPLETION_ADAPTER_BINDING_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_alternative_pnl_owner(tree)
        assert not bad, f"{path.relative_to(REPO_ROOT)}: forbidden PnL owner import: {bad}"

    kernel_tree = ast.parse(
        (REPO_ROOT / CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE).read_text(encoding="utf-8")
    )
    kernel_bad = _imports_module(kernel_tree, _KERNEL_PURITY_FORBIDDEN_IMPORTS)
    assert not kernel_bad, (
        f"{CANONICAL_FUTURES_ARITHMETIC_KERNEL_CANDIDATE}: "
        f"kernel must remain pure/offline without ledger imports: {kernel_bad}"
    )


def test_contract_defines_no_pnl_fee_funding_formulas() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    assert defined.isdisjoint(_FORBIDDEN_FORMULA_NAMES)

    referenced_symbols = {
        symbol
        for record in PNL_OWNER_REGISTRY
        for symbol in record["pnl_surface_symbols"]
        if "." not in symbol
    }
    assert referenced_symbols, (
        "registry must reference production PnL symbols without redefining them"
    )
    assert not (referenced_symbols & defined), (
        "contract must reference production symbols only — not redefine PnL formulas"
    )


def test_contract_is_non_authorizing() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
    assert A2_ARITHMETIC_OUT_OF_SCOPE is True
    assert KERNEL_WIRING_OUT_OF_SCOPE is True
    assert EQUITY_IDENTITY_PROOF_OUT_OF_SCOPE is True
    assert PNL_OWNER_DESIGN_SPEC_V0["a2_arithmetic_out_of_scope"] is True
    assert PNL_OWNER_DESIGN_SPEC_V0["kernel_wiring_out_of_scope"] is True
    assert PNL_OWNER_DESIGN_SPEC_V0["equity_identity_proof_out_of_scope"] is True
    assert PNL_OWNER_DESIGN_SPEC_V0["future_kernel_wiring_must_be_explicit"] is True
