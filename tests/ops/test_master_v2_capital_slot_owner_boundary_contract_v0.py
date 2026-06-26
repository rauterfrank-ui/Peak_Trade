"""Static fail-closed contract: Master V2 Capital Slot owner boundary v0.

Package D Slice D1 (INV-007) formalises Capital Slot ratchet/release owner, authority, and
import boundaries. Inventories existing production modules via AST/read-only analysis.
Declares ``double_play_capital_slot.py`` as the sole canonical Capital Slot pure-model
candidate while offline replay, dashboard display, composition, and lifecycle integration
paths retain bounded consumer or adjacent-reference scope only.

Cross-references existing docs-static guards without duplicating them:
``tests/ops/test_bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py``.

Non-authorizing. No runtime, network, testnet execution, hot-path wiring, or formula
duplication. Operative reallocation-pool authority is explicitly out of scope.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_V0=true"
AUTHORITY_LIFT = False
REALLOCATION_POOL_OUT_OF_SCOPE = True

CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE = "src/trading/master_v2/double_play_capital_slot.py"
CSR_SPEC_OWNER = "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md"
LIFECYCLE_CROSS_REFERENCE = "tests/ops/test_bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py"
C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE = (
    "tests/ops/test_master_v2_dynamic_scope_owner_boundary_contract_v0.py"
)
C2_PREDECESSOR_BOUNDARY_CROSS_REFERENCE = (
    "tests/ops/test_master_v2_state_switch_owner_boundary_contract_v0.py"
)

OwnerRole = Literal[
    "CAPITAL_SLOT_PURE_MODEL_CANDIDATE",
    "OFFLINE_REPLAY_CONSUMER",
    "DISPLAY_CONSUMER",
    "DISPLAY_JSON_CONSUMER",
    "COMPOSITION_CONSUMER",
    "LIFECYCLE_INTEGRATION_REFERENCE",
    "CSR_VOCABULARY_OWNER",
    "C1_PREDECESSOR_BOUNDARY",
    "C2_PREDECESSOR_BOUNDARY",
]

_BINDING_ROLES: Final[frozenset[str]] = frozenset(
    {
        "MASTER_V2_CAPITAL_SLOT_BINDING",
        "COMPLETION_CAPITAL_SLOT_BINDING",
        "ADAPTER_CAPITAL_SLOT_BINDING",
    }
)

_VALID_OWNER_ROLES: Final[frozenset[str]] = frozenset(
    {
        "CAPITAL_SLOT_PURE_MODEL_CANDIDATE",
        "OFFLINE_REPLAY_CONSUMER",
        "DISPLAY_CONSUMER",
        "DISPLAY_JSON_CONSUMER",
        "COMPOSITION_CONSUMER",
        "LIFECYCLE_INTEGRATION_REFERENCE",
        "CSR_VOCABULARY_OWNER",
        "C1_PREDECESSOR_BOUNDARY",
        "C2_PREDECESSOR_BOUNDARY",
    }
)

_CANONICAL_PURE_MODEL_SYMBOLS: Final[tuple[str, ...]] = (
    "CapitalSlotStatus",
    "CapitalSlotReleaseReason",
    "CapitalSlotBlockReason",
    "CapitalSlotConfig",
    "CapitalSlotState",
    "CapitalSlotRatchetDecision",
    "CapitalSlotReleaseDecision",
    "calculate_ratchet_target",
    "cashflow_split_valid",
    "apply_loss_following_base",
    "evaluate_capital_slot_ratchet",
    "evaluate_capital_slot_release",
)

_FORBIDDEN_PARALLEL_PURE_MODEL_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "CapitalSlotConfig",
        "CapitalSlotState",
        "CapitalSlotRatchetDecision",
        "CapitalSlotReleaseDecision",
    }
)

_FORBIDDEN_CAPITAL_SLOT_FORMULA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "calculate_ratchet_target",
        "cashflow_split_valid",
        "apply_loss_following_base",
        "evaluate_capital_slot_ratchet",
        "evaluate_capital_slot_release",
    }
)

_FORBIDDEN_OPERATIVE_CAPITAL_SLOT_CLAIM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "CAPITAL_SLOT_OPERATIVE_SSOT",
        "LIVE_AUTHORIZATION_GRANTED",
        "OPERATIVE_RATCHET_APPLIED",
        "OPERATIVE_RESERVE_MOVEMENT_EXECUTED",
        "OPERATIVE_CAPITAL_REALLOCATION_EXECUTED",
        "OPERATIVE_SLOT_RELEASE_EXECUTED",
        "RATCHET_REPAIR_AUTHORITY",
        "KILLSWITCH_SUBSTITUTED_BY_CAPITAL_SLOT",
        "EVIDENCE_AS_CAPITAL_SLOT_PERMISSION",
        "DASHBOARD_AS_CAPITAL_SLOT_PERMISSION",
    }
)

_FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS: Final[tuple[str, ...]] = (
    "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V1",
    "CANONICAL_CAPITAL_SLOT_V1",
)

_CSR_STATIC_MACHINE_MARKERS: Final[tuple[str, ...]] = (
    "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0",
    "fail-closed interpretation for missing governance or evidence",
    "Released capital is not authorized to open a new position",
    "This file grants no live authorization.",
    "reallocation boundary (capital returns to pool; does not auto-trade)",
    "BOUNDED_FUTURES_TESTNET_CAPITAL_SLOT_RATCHET_RELEASE_LIFECYCLE_INTEGRATION_GUARD_V0=true",
    "DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION",
)

_MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS: Final[tuple[Path, ...]] = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py",
    REPO_ROOT / "src" / "ops" / "offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
)

_FORBIDDEN_PARALLEL_CAPITAL_SLOT_IMPORT_FRAGMENTS: Final[tuple[str, ...]] = (
    "canonical_capital_slot",
    "capital_slot_owner_contract_v1",
    "double_play_capital_slot_contract_v1",
)


class CapitalSlotOwnerRecord(TypedDict):
    path: str
    role: OwnerRole
    master_v2_relevant: bool
    completion_adapter_relevant: bool
    local_scope_only: bool
    reallocation_pool_authority: bool
    operative_ssot: bool
    canonical_candidate: bool
    authority_lift: bool
    live_authorization: bool
    responsibility_scope: str
    surface_symbols: tuple[str, ...]


class CapitalSlotOwnerDesignSpecV0(TypedDict):
    package_slice: str
    inventory_id: str
    pure_model_candidate_path: str
    csr_spec_owner: str
    lifecycle_cross_reference: str
    c1_predecessor_cross_reference: str
    c2_predecessor_cross_reference: str
    reallocation_pool_out_of_scope: bool


CAPITAL_SLOT_OWNER_DESIGN_SPEC_V0: CapitalSlotOwnerDesignSpecV0 = {
    "package_slice": "PACKAGE_D_SLICE_D1",
    "inventory_id": "INV-007",
    "pure_model_candidate_path": CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE,
    "csr_spec_owner": CSR_SPEC_OWNER,
    "lifecycle_cross_reference": LIFECYCLE_CROSS_REFERENCE,
    "c1_predecessor_cross_reference": C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE,
    "c2_predecessor_cross_reference": C2_PREDECESSOR_BOUNDARY_CROSS_REFERENCE,
    "reallocation_pool_out_of_scope": True,
}

CAPITAL_SLOT_OWNER_REGISTRY: tuple[CapitalSlotOwnerRecord, ...] = (
    {
        "path": CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE,
        "role": "CAPITAL_SLOT_PURE_MODEL_CANDIDATE",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": False,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": True,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": (
            "Pure Capital Slot model: ratchet, release, loss-following base, slot config/state"
        ),
        "surface_symbols": _CANONICAL_PURE_MODEL_SYMBOLS,
    },
    {
        "path": "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        "role": "OFFLINE_REPLAY_CONSUMER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": True,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Offline replay consumer — must not become operative Capital Slot SSOT",
        "surface_symbols": (
            "CapitalSlotConfig",
            "CapitalSlotState",
            "evaluate_capital_slot_ratchet",
            "evaluate_capital_slot_release",
        ),
    },
    {
        "path": "src/trading/master_v2/double_play_dashboard_display.py",
        "role": "DISPLAY_CONSUMER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Display-only ratchet/release decision consumer — no authority",
        "surface_symbols": (
            "CapitalSlotRatchetDecision",
            "CapitalSlotReleaseDecision",
        ),
    },
    {
        "path": "src/webui/double_play_dashboard_display_json_route_v0.py",
        "role": "DISPLAY_JSON_CONSUMER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Read-only JSON route fixture consumer — no capital slot authority",
        "surface_symbols": (
            "CapitalSlotConfig",
            "CapitalSlotState",
            "evaluate_capital_slot_ratchet",
            "evaluate_capital_slot_release",
        ),
    },
    {
        "path": "src/trading/master_v2/double_play_composition.py",
        "role": "COMPOSITION_CONSUMER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Composition consumes ratchet/release decisions — not slot SSOT",
        "surface_symbols": (
            "CapitalSlotRatchetDecision",
            "CapitalSlotReleaseDecision",
        ),
    },
    {
        "path": (
            "src/ops/bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py"
        ),
        "role": "LIFECYCLE_INTEGRATION_REFERENCE",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": True,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": (
            "Static lifecycle integration reference — not operative Capital Slot SSOT"
        ),
        "surface_symbols": (),
    },
    {
        "path": CSR_SPEC_OWNER,
        "role": "CSR_VOCABULARY_OWNER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Canonical docs-only Capital Slot ratchet/release vocabulary owner",
        "surface_symbols": (),
    },
    {
        "path": C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE,
        "role": "C1_PREDECESSOR_BOUNDARY",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "C1 Dynamic Scope owner boundary — predecessor crosslink only",
        "surface_symbols": (),
    },
    {
        "path": C2_PREDECESSOR_BOUNDARY_CROSS_REFERENCE,
        "role": "C2_PREDECESSOR_BOUNDARY",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "reallocation_pool_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "C2 State Switch owner boundary — predecessor crosslink only",
        "surface_symbols": (),
    },
)


def _registry_by_path(path: str) -> CapitalSlotOwnerRecord:
    for record in CAPITAL_SLOT_OWNER_REGISTRY:
        if record["path"] == path:
            return record
    raise KeyError(f"missing registry record for owner path: {path}")


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


def _imports_parallel_capital_slot_owner(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = (alias.name or "").lower()
                if any(
                    fragment in name
                    for fragment in _FORBIDDEN_PARALLEL_CAPITAL_SLOT_IMPORT_FRAGMENTS
                ):
                    violations.append(f"import {alias.name}")
                if "double_play_capital_slot" not in name and "capital_slot" in name:
                    violations.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            if any(
                fragment in mod for fragment in _FORBIDDEN_PARALLEL_CAPITAL_SLOT_IMPORT_FRAGMENTS
            ):
                violations.append(f"from {node.module} import ...")
            if "double_play_capital_slot" not in mod and "capital_slot" in mod:
                violations.append(f"from {node.module} import ...")
    return sorted(set(violations))


def _imports_double_play_capital_slot(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name.endswith("double_play_capital_slot"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.endswith("double_play_capital_slot"):
                return True
    return False


def _class_names_in_module(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _production_symbols_exist(owner_path: str, symbols: tuple[str, ...]) -> None:
    if not symbols:
        return
    source_path = REPO_ROOT / owner_path
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    defined_classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for symbol in symbols:
        assert symbol in defined_functions or symbol in defined_classes, (
            f"{owner_path}: missing production symbol reference {symbol}"
        )


def test_capital_slot_owner_inventory_complete_and_roles_unique() -> None:
    paths = [record["path"] for record in CAPITAL_SLOT_OWNER_REGISTRY]
    assert len(paths) == len(set(paths)), "duplicate owner paths in registry"
    roles = [record["role"] for record in CAPITAL_SLOT_OWNER_REGISTRY]
    assert all(role in _VALID_OWNER_ROLES for role in roles)
    assert all(role not in _BINDING_ROLES for role in roles)
    for record in CAPITAL_SLOT_OWNER_REGISTRY:
        owner_path = REPO_ROOT / record["path"]
        assert owner_path.is_file(), record["path"]
        assert record["responsibility_scope"].strip(), record["path"]
        assert isinstance(record["surface_symbols"], tuple)

    assert CAPITAL_SLOT_OWNER_DESIGN_SPEC_V0["inventory_id"] == "INV-007"
    assert CAPITAL_SLOT_OWNER_DESIGN_SPEC_V0["pure_model_candidate_path"] == (
        CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE
    )
    assert (REPO_ROOT / LIFECYCLE_CROSS_REFERENCE).is_file()
    assert (REPO_ROOT / C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE).is_file()
    assert (REPO_ROOT / C2_PREDECESSOR_BOUNDARY_CROSS_REFERENCE).is_file()

    candidate = _registry_by_path(CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE)
    _production_symbols_exist(candidate["path"], candidate["surface_symbols"])
    candidate_text = (REPO_ROOT / candidate["path"]).read_text(encoding="utf-8")
    assert "DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION" in candidate_text


def test_exactly_one_capital_slot_pure_model_candidate() -> None:
    candidates = [
        record["path"]
        for record in CAPITAL_SLOT_OWNER_REGISTRY
        if record["role"] == "CAPITAL_SLOT_PURE_MODEL_CANDIDATE"
    ]
    assert candidates == [CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE]
    candidate = _registry_by_path(CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE)
    assert candidate["canonical_candidate"] is True
    assert candidate["authority_lift"] is False
    assert candidate["live_authorization"] is False
    assert candidate["reallocation_pool_authority"] is False

    non_candidates = [
        record for record in CAPITAL_SLOT_OWNER_REGISTRY if not record["canonical_candidate"]
    ]
    assert all(record["operative_ssot"] is False for record in non_candidates)
    assert all(record["authority_lift"] is False for record in CAPITAL_SLOT_OWNER_REGISTRY)

    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "src").glob("**/*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == CANONICAL_CAPITAL_SLOT_PURE_MODEL_CANDIDATE:
            continue
        parallel = _FORBIDDEN_PARALLEL_PURE_MODEL_CLASSES & _class_names_in_module(path)
        if parallel:
            offenders.append(f"{rel}: {sorted(parallel)}")
    assert not offenders, f"parallel Capital Slot pure-model classes outside candidate: {offenders}"


def test_local_consumers_remain_bounded_not_operative_ssot() -> None:
    offline = _registry_by_path("src/trading/master_v2/offline_double_play_scenario_replay_v0.py")
    assert offline["local_scope_only"] is True
    assert offline["operative_ssot"] is False
    offline_tree = ast.parse((REPO_ROOT / offline["path"]).read_text(encoding="utf-8"))
    assert _imports_double_play_capital_slot(offline_tree), (
        "offline replay must consume canonical pure model"
    )

    display = _registry_by_path("src/trading/master_v2/double_play_dashboard_display.py")
    composition = _registry_by_path("src/trading/master_v2/double_play_composition.py")
    display_json = _registry_by_path("src/webui/double_play_dashboard_display_json_route_v0.py")
    lifecycle = _registry_by_path(
        "src/ops/bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py"
    )
    for record in (display, composition, display_json, lifecycle):
        assert record["local_scope_only"] is True
        assert record["authority_lift"] is False
        assert record["reallocation_pool_authority"] is False
        if record["path"].endswith(".py") and "tests/" not in record["path"]:
            imports = _module_import_targets(REPO_ROOT / record["path"])
            assert any(mod.endswith("double_play_capital_slot") for mod in imports), record["path"]


def test_master_v2_completion_adapter_paths_import_no_parallel_capital_slot_owner() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_parallel_capital_slot_owner(tree)
        assert not bad, (
            f"{path.relative_to(REPO_ROOT)}: forbidden parallel Capital Slot import: {bad}"
        )

    for fragment in _FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS:
        assert not list((REPO_ROOT / "docs" / "ops" / "specs").glob(f"*{fragment}*"))


def test_contract_crosslinks_csr_static_markers_without_redefinition() -> None:
    csr_spec = (REPO_ROOT / CSR_SPEC_OWNER).read_text(encoding="utf-8")
    for marker in _CSR_STATIC_MACHINE_MARKERS:
        assert marker in csr_spec or marker in (REPO_ROOT / LIFECYCLE_CROSS_REFERENCE).read_text(
            encoding="utf-8"
        ), f"missing canonical CSR marker: {marker}"

    lifecycle_test = (REPO_ROOT / LIFECYCLE_CROSS_REFERENCE).read_text(encoding="utf-8")
    assert (
        "BOUNDED_FUTURES_TESTNET_CAPITAL_SLOT_RATCHET_RELEASE_LIFECYCLE_INTEGRATION_GUARD_V0=true"
        in lifecycle_test
    )
    assert "DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION" in lifecycle_test

    c1_boundary = (REPO_ROOT / C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE).read_text(encoding="utf-8")
    assert "INV-045" in c1_boundary
    assert "DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_V0=true" in c1_boundary

    c2_boundary = (REPO_ROOT / C2_PREDECESSOR_BOUNDARY_CROSS_REFERENCE).read_text(encoding="utf-8")
    assert "INV-046" in c2_boundary
    assert "STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_V0=true" in c2_boundary

    for fragment in _FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS:
        assert not list((REPO_ROOT / "docs" / "ops" / "specs").glob(f"*{fragment}*"))


def test_contract_defines_no_capital_slot_formulas_and_is_non_authorizing() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    assert defined.isdisjoint(_FORBIDDEN_CAPITAL_SLOT_FORMULA_NAMES)

    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
    assert REALLOCATION_POOL_OUT_OF_SCOPE is True
    assert CAPITAL_SLOT_OWNER_DESIGN_SPEC_V0["reallocation_pool_out_of_scope"] is True


def test_forbidden_authority_and_ratchet_claim_keys_absent() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for key in _FORBIDDEN_OPERATIVE_CAPITAL_SLOT_CLAIM_KEYS:
        assert f"{key}=true" not in text
    for record in CAPITAL_SLOT_OWNER_REGISTRY:
        assert record["reallocation_pool_authority"] is False, record["path"]
        assert record["authority_lift"] is False, record["path"]
        assert record["live_authorization"] is False, record["path"]
