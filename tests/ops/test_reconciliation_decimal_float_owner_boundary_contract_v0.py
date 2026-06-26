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
    "RECON_ADAPTER",
    "RECON_HOOK",
    "RECON_CONTEXT",
    "RECON_MODELS",
    "HISTORICAL_PAPER_INVARIANT",
    "HISTORICAL_LIVE_MOCK",
    "EVIDENCE_AIOPS",
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
        "RECON_ADAPTER",
        "RECON_HOOK",
        "RECON_CONTEXT",
        "RECON_MODELS",
        "HISTORICAL_PAPER_INVARIANT",
        "HISTORICAL_LIVE_MOCK",
        "EVIDENCE_AIOPS",
    }
)

_HISTORICAL_AND_EVIDENCE_ROLES: Final[frozenset[str]] = frozenset(
    {
        "HISTORICAL_PAPER_INVARIANT",
        "HISTORICAL_LIVE_MOCK",
        "EVIDENCE_AIOPS",
    }
)

_SUPPORTING_OPS_RECON_PATHS: Final[tuple[str, ...]] = (
    "src/ops/recon/reconcile.py",
    "src/ops/recon/providers.py",
    "src/ops/recon/recon_hook.py",
    "src/ops/recon/context.py",
    "src/ops/recon/models.py",
)

_OPS_RECON_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "src.ops.recon",
        "src.ops.recon.reconcile",
        "src.ops.recon.providers",
        "src.ops.recon.recon_hook",
        "src.ops.recon.context",
        "src.ops.recon.models",
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
    repair_authority: bool
    operative_ssot: bool
    canonical_candidate: bool
    expected_state_role: str
    observed_state_role: str


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
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": True,
        "expected_state_role": "internal_ledger_snapshot",
        "observed_state_role": "external_snapshot_reference",
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
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "provider_expected_snapshot",
        "observed_state_role": "provider_observed_snapshot",
    },
    {
        "path": "src/ops/recon/providers.py",
        "role": "RECON_ADAPTER",
        "number_type": "float",
        "input_units": "adapter-provided balance/position snapshots",
        "output_units": "BalanceSnapshot/PositionSnapshot transport",
        "sign_convention": "provider-owned snapshot semantics",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "adapter-owned",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "expected_balance_position_snapshots",
        "observed_state_role": "observed_balance_position_snapshots",
    },
    {
        "path": "src/ops/recon/recon_hook.py",
        "role": "RECON_HOOK",
        "number_type": "float",
        "input_units": "ReconConfig and provider/snapshot inputs",
        "output_units": "DriftReport observation",
        "sign_convention": "hook compares expected vs observed only",
        "absolute_tolerance": True,
        "relative_tolerance": False,
        "quantization_strategy": "delegates to ops float reconcile",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "hook_expected_inputs",
        "observed_state_role": "hook_observed_inputs",
    },
    {
        "path": "src/ops/recon/context.py",
        "role": "RECON_CONTEXT",
        "number_type": "float",
        "input_units": "pipeline context recon payloads",
        "output_units": "BalanceSnapshot/PositionSnapshot extraction",
        "sign_convention": "context normalization only",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "context-owned",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "pipeline_context_expected",
        "observed_state_role": "pipeline_context_observed",
    },
    {
        "path": "src/ops/recon/models.py",
        "role": "RECON_MODELS",
        "number_type": "float",
        "input_units": "snapshot value transport",
        "output_units": "BalanceSnapshot/PositionSnapshot/DriftReport",
        "sign_convention": "value transport only",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "model-owned",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "value_transport_expected",
        "observed_state_role": "value_transport_observed",
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
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "internal_position_state",
        "observed_state_role": "not_applicable",
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
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "internal_order_fill_state",
        "observed_state_role": "not_applicable",
    },
    {
        "path": "src/sim/paper/reconcile.py",
        "role": "HISTORICAL_PAPER_INVARIANT",
        "number_type": "float",
        "input_units": "paper ledger rows",
        "output_units": "invariant verification only",
        "sign_convention": "paper simulation ledger",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "historical-local",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "paper_ledger_invariant",
        "observed_state_role": "not_applicable",
    },
    {
        "path": "src/execution/live/reconcile.py",
        "role": "HISTORICAL_LIVE_MOCK",
        "number_type": "float",
        "input_units": "local order intent vs broker mock snapshot",
        "output_units": "ReconcileReport descriptive mismatches",
        "sign_convention": "mock broker compare only",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "historical-local",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "local_order_intent",
        "observed_state_role": "broker_mock_snapshot",
    },
    {
        "path": "src/aiops/p7/reconciliation.py",
        "role": "EVIDENCE_AIOPS",
        "number_type": "mixed",
        "input_units": "artifact metrics vs spec expected",
        "output_units": "ReconciliationResult evidence issues",
        "sign_convention": "evidence-only validator",
        "absolute_tolerance": False,
        "relative_tolerance": False,
        "quantization_strategy": "evidence-owned",
        "fail_closed": True,
        "master_v2_relevant": False,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "expected_state_role": "spec_expected_metrics",
        "observed_state_role": "artifact_observed_metrics",
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
        "REPAIR_AUTHORITY_GRANTED",
        "AUTOMATIC_STATE_REPAIR_ENABLED",
        "RECONCILIATION_REPAIR_AUTHORITY_BOUND",
        "OPERATIVE_RECONCILIATION_SSOT",
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


def _module_import_targets(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
    return targets


def _class_names_in_module(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


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
    assert len(roles) == len(set(roles)), "duplicate owner roles in registry"
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
    assert candidate["canonical_candidate"] is True
    assert candidate["operative_ssot"] is False
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


def test_all_registry_records_declare_no_repair_authority() -> None:
    for record in RECONCILIATION_OWNER_REGISTRY:
        assert record["repair_authority"] is False, record["path"]
    assert all(not record["operative_ssot"] for record in RECONCILIATION_OWNER_REGISTRY)


def test_registry_supporting_and_historical_roles_present() -> None:
    roles = {record["role"] for record in RECONCILIATION_OWNER_REGISTRY}
    for required in (
        "RECON_ADAPTER",
        "RECON_HOOK",
        "RECON_CONTEXT",
        "RECON_MODELS",
        "HISTORICAL_PAPER_INVARIANT",
        "HISTORICAL_LIVE_MOCK",
        "EVIDENCE_AIOPS",
    ):
        assert required in roles
    for rel_path in _SUPPORTING_OPS_RECON_PATHS:
        assert rel_path in {record["path"] for record in RECONCILIATION_OWNER_REGISTRY}


def test_historical_and_evidence_owners_not_canonical_ssot() -> None:
    for record in RECONCILIATION_OWNER_REGISTRY:
        if record["role"] in _HISTORICAL_AND_EVIDENCE_ROLES:
            assert record["canonical_candidate"] is False
            assert record["operative_ssot"] is False
            assert record["repair_authority"] is False
    canonical_candidates = [
        record for record in RECONCILIATION_OWNER_REGISTRY if record["canonical_candidate"]
    ]
    assert len(canonical_candidates) == 1
    assert canonical_candidates[0]["path"] == CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE


def test_registry_expected_observed_state_roles_declared() -> None:
    for record in RECONCILIATION_OWNER_REGISTRY:
        assert record["expected_state_role"]
        assert record["observed_state_role"]
    adapter = next(
        record for record in RECONCILIATION_OWNER_REGISTRY if record["role"] == "RECON_ADAPTER"
    )
    assert adapter["expected_state_role"] != adapter["observed_state_role"]
    evidence = next(
        record for record in RECONCILIATION_OWNER_REGISTRY if record["role"] == "EVIDENCE_AIOPS"
    )
    assert evidence["expected_state_role"] == "spec_expected_metrics"
    assert evidence["observed_state_role"] == "artifact_observed_metrics"


def test_canonical_candidate_must_not_import_ops_recon_modules() -> None:
    imports = _module_import_targets(REPO_ROOT / CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE)
    forbidden = sorted(imports & _OPS_RECON_IMPORT_MODULES)
    assert not forbidden, f"canonical candidate reverse-imports ops recon: {forbidden}"


def test_supporting_ops_recon_must_not_import_execution_reconciliation() -> None:
    for rel_path in _SUPPORTING_OPS_RECON_PATHS:
        imports = _module_import_targets(REPO_ROOT / rel_path)
        assert "src.execution.reconciliation" not in imports, rel_path


def test_no_parallel_reconciliation_engine_class_outside_canonical_candidate() -> None:
    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "src").glob("**/*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == CANONICAL_EXECUTION_RECONCILIATION_CANDIDATE:
            continue
        if "ReconciliationEngine" in _class_names_in_module(path):
            offenders.append(rel)
    assert not offenders, f"parallel ReconciliationEngine outside canonical candidate: {offenders}"


def test_forbidden_authority_and_repair_claim_keys_absent() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for key in _FORBIDDEN_OPERATIVE_RECONCILIATION_CLAIM_KEYS:
        assert f"{key}=true" not in text
