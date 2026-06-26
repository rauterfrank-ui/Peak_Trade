"""Static fail-closed contract: Master V2 State-Switch owner boundary v0.

Package C Slice C2 (INV-046) formalises Bull/Bear side-state-switch owner, authority, and
import boundaries. Inventories existing production modules via AST/read-only analysis.
Declares ``double_play_state.py`` as the sole canonical State-Switch pure-model candidate
while offline replay, survival limits, dashboard display, and composition paths retain
bounded consumer or adjacent-reference scope only.

Cross-references existing docs-static guards without duplicating them:
``tests/ops/test_master_v2_state_switch_contract_static_v0.py``.

Non-authorizing. No runtime, network, testnet execution, hot-path wiring, or formula
duplication. Repair authority is explicitly out of scope.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_V0=true"
AUTHORITY_LIFT = False
REPAIR_AUTHORITY_OUT_OF_SCOPE = True

CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE = "src/trading/master_v2/double_play_state.py"
SS_SPEC_OWNER = "docs/ops/specs/FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md"
DSE_PREDECESSOR_SPEC = "docs/ops/specs/FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
SS_STATIC_TEST_CROSS_REFERENCE = "tests/ops/test_master_v2_state_switch_contract_static_v0.py"
C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE = (
    "tests/ops/test_master_v2_dynamic_scope_owner_boundary_contract_v0.py"
)

OwnerRole = Literal[
    "STATE_SWITCH_PURE_MODEL_CANDIDATE",
    "OFFLINE_REPLAY_CONSUMER",
    "SURVIVAL_LIMITS_ADJACENT",
    "DISPLAY_CONSUMER",
    "COMPOSITION_CONSUMER",
    "SS_VOCABULARY_OWNER",
    "DSE_PREDECESSOR_CROSSLINK",
    "C1_PREDECESSOR_BOUNDARY",
]

_BINDING_ROLES: Final[frozenset[str]] = frozenset(
    {
        "MASTER_V2_STATE_SWITCH_BINDING",
        "COMPLETION_STATE_SWITCH_BINDING",
        "ADAPTER_STATE_SWITCH_BINDING",
    }
)

_VALID_OWNER_ROLES: Final[frozenset[str]] = frozenset(
    {
        "STATE_SWITCH_PURE_MODEL_CANDIDATE",
        "OFFLINE_REPLAY_CONSUMER",
        "SURVIVAL_LIMITS_ADJACENT",
        "DISPLAY_CONSUMER",
        "COMPOSITION_CONSUMER",
        "SS_VOCABULARY_OWNER",
        "DSE_PREDECESSOR_CROSSLINK",
        "C1_PREDECESSOR_BOUNDARY",
    }
)

_CANONICAL_PURE_MODEL_SYMBOLS: Final[tuple[str, ...]] = (
    "SideState",
    "ActiveSide",
    "derive_active_side",
    "transition_state",
    "_both_active_invariant_ok",
)

_FORBIDDEN_PARALLEL_PURE_MODEL_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "SideState",
        "ActiveSide",
    }
)

_FORBIDDEN_STATE_SWITCH_FORMULA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "derive_active_side",
        "transition_state",
        "_both_active_invariant_ok",
    }
)

_FORBIDDEN_OPERATIVE_STATE_SWITCH_CLAIM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "STATE_SWITCH_OPERATIVE_SSOT",
        "LIVE_AUTHORIZATION_GRANTED",
        "STATE_SWITCH_REPAIR_AUTHORITY",
        "REPAIR_AUTHORITY_GRANTED",
        "AUTOMATIC_STATE_SWITCH_REPAIR_ENABLED",
        "OPERATIVE_STATE_SWITCH_SSOT",
        "STATE_SWITCH_HOT_PATH_WIRED",
        "KILLSWITCH_SUBSTITUTED_BY_STATE_SWITCH",
        "EVIDENCE_AS_STATE_SWITCH_PERMISSION",
        "DASHBOARD_AS_STATE_SWITCH_PERMISSION",
    }
)

_FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS: Final[tuple[str, ...]] = (
    "FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V1",
    "CANONICAL_STATE_SWITCH_V1",
)

_SS_STATIC_MACHINE_MARKERS: Final[tuple[str, ...]] = (
    "MARKER: FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0_EXISTS",
    "MARKER: STATE_SWITCH_CONTRACT_V0",
    "MARKER: STATE_SWITCH_IMPLEMENTED=false",
    "MARKER: DSE_PREDECESSOR_REQUIRED",
    "MARKER: CANDIDATE_EVENTS_DO_NOT_AUTHORIZE_SIDE_SWITCH",
    "MARKER: KILLSWITCH_SUPERIOR",
    "MARKER: STATE_SWITCH_NOT_KILLSWITCH_FLIP",
    "MARKER: AI_AUTHORITY=false",
    "MARKER: DASHBOARD_AUTHORITY=false",
    "MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_STATE_SWITCH",
)

_MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS: Final[tuple[Path, ...]] = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py",
    REPO_ROOT / "src" / "ops" / "offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
)

_FORBIDDEN_PARALLEL_STATE_SWITCH_IMPORT_FRAGMENTS: Final[tuple[str, ...]] = (
    "canonical_state_switch",
    "futures_double_play_state_switch_contract_v1",
    "state_switch_owner_contract_v1",
)


class StateSwitchOwnerRecord(TypedDict):
    path: str
    role: OwnerRole
    master_v2_relevant: bool
    completion_adapter_relevant: bool
    local_scope_only: bool
    repair_authority: bool
    operative_ssot: bool
    canonical_candidate: bool
    authority_lift: bool
    live_authorization: bool
    responsibility_scope: str
    surface_symbols: tuple[str, ...]


class StateSwitchOwnerDesignSpecV0(TypedDict):
    package_slice: str
    inventory_id: str
    pure_model_candidate_path: str
    ss_spec_owner: str
    ss_static_test_cross_reference: str
    c1_predecessor_cross_reference: str
    repair_authority_out_of_scope: bool


STATE_SWITCH_OWNER_DESIGN_SPEC_V0: StateSwitchOwnerDesignSpecV0 = {
    "package_slice": "PACKAGE_C_SLICE_C2",
    "inventory_id": "INV-046",
    "pure_model_candidate_path": CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE,
    "ss_spec_owner": SS_SPEC_OWNER,
    "ss_static_test_cross_reference": SS_STATIC_TEST_CROSS_REFERENCE,
    "c1_predecessor_cross_reference": C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE,
    "repair_authority_out_of_scope": True,
}

STATE_SWITCH_OWNER_REGISTRY: tuple[StateSwitchOwnerRecord, ...] = (
    {
        "path": CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE,
        "role": "STATE_SWITCH_PURE_MODEL_CANDIDATE",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": False,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": True,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": (
            "Pure State-Switch model: SideState, ActiveSide, derive_active_side, transition_state"
        ),
        "surface_symbols": _CANONICAL_PURE_MODEL_SYMBOLS,
    },
    {
        "path": "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        "role": "OFFLINE_REPLAY_CONSUMER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Offline replay consumer — must not become operative State-Switch SSOT",
        "surface_symbols": (
            "SideState",
            "ActiveSide",
            "derive_active_side",
            "transition_state",
        ),
    },
    {
        "path": "src/trading/master_v2/double_play_survival.py",
        "role": "SURVIVAL_LIMITS_ADJACENT",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": (
            "StateSwitchSurvivalLimits adjacent to Double Play — not State-Switch SSOT"
        ),
        "surface_symbols": ("StateSwitchSurvivalLimits", "evaluate_survival_envelope"),
    },
    {
        "path": "src/trading/master_v2/double_play_dashboard_display.py",
        "role": "DISPLAY_CONSUMER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Display-only TransitionDecision consumer — no authority",
        "surface_symbols": ("TransitionDecision",),
    },
    {
        "path": "src/trading/master_v2/double_play_composition.py",
        "role": "COMPOSITION_CONSUMER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Composition consumes SideState/TransitionDecision — not SS SSOT",
        "surface_symbols": ("SideState", "TransitionDecision"),
    },
    {
        "path": SS_SPEC_OWNER,
        "role": "SS_VOCABULARY_OWNER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Canonical docs-only State-Switch vocabulary owner",
        "surface_symbols": (),
    },
    {
        "path": DSE_PREDECESSOR_SPEC,
        "role": "DSE_PREDECESSOR_CROSSLINK",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": (
            "DSE predecessor — scope-event producer authority before State-Switch consumer"
        ),
        "surface_symbols": (),
    },
    {
        "path": C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE,
        "role": "C1_PREDECESSOR_BOUNDARY",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "C1 Dynamic Scope owner boundary — predecessor crosslink only",
        "surface_symbols": (),
    },
)


def _registry_by_path(path: str) -> StateSwitchOwnerRecord:
    for record in STATE_SWITCH_OWNER_REGISTRY:
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


def _imports_parallel_state_switch_owner(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = (alias.name or "").lower()
                if any(
                    fragment in name
                    for fragment in _FORBIDDEN_PARALLEL_STATE_SWITCH_IMPORT_FRAGMENTS
                ):
                    violations.append(f"import {alias.name}")
                if "double_play_state" not in name and "state_switch" in name:
                    violations.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            if any(
                fragment in mod for fragment in _FORBIDDEN_PARALLEL_STATE_SWITCH_IMPORT_FRAGMENTS
            ):
                violations.append(f"from {node.module} import ...")
            if "double_play_state" not in mod and "state_switch" in mod:
                violations.append(f"from {node.module} import ...")
    return sorted(set(violations))


def _imports_double_play_state(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name.endswith("double_play_state"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.endswith("double_play_state"):
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


def test_state_switch_owner_inventory_complete_and_roles_unique() -> None:
    paths = [record["path"] for record in STATE_SWITCH_OWNER_REGISTRY]
    assert len(paths) == len(set(paths)), "duplicate owner paths in registry"
    roles = [record["role"] for record in STATE_SWITCH_OWNER_REGISTRY]
    assert all(role in _VALID_OWNER_ROLES for role in roles)
    assert all(role not in _BINDING_ROLES for role in roles)
    for record in STATE_SWITCH_OWNER_REGISTRY:
        owner_path = REPO_ROOT / record["path"]
        assert owner_path.is_file(), record["path"]
        assert record["responsibility_scope"].strip(), record["path"]
        assert isinstance(record["surface_symbols"], tuple)

    assert STATE_SWITCH_OWNER_DESIGN_SPEC_V0["inventory_id"] == "INV-046"
    assert STATE_SWITCH_OWNER_DESIGN_SPEC_V0["pure_model_candidate_path"] == (
        CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE
    )
    assert (REPO_ROOT / SS_STATIC_TEST_CROSS_REFERENCE).is_file()
    assert (REPO_ROOT / C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE).is_file()

    candidate = _registry_by_path(CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE)
    _production_symbols_exist(candidate["path"], candidate["surface_symbols"])


def test_exactly_one_state_switch_pure_model_candidate() -> None:
    candidates = [
        record["path"]
        for record in STATE_SWITCH_OWNER_REGISTRY
        if record["role"] == "STATE_SWITCH_PURE_MODEL_CANDIDATE"
    ]
    assert candidates == [CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE]
    candidate = _registry_by_path(CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE)
    assert candidate["canonical_candidate"] is True
    assert candidate["authority_lift"] is False
    assert candidate["live_authorization"] is False
    assert candidate["repair_authority"] is False

    non_candidates = [
        record for record in STATE_SWITCH_OWNER_REGISTRY if not record["canonical_candidate"]
    ]
    assert all(record["operative_ssot"] is False for record in non_candidates)
    assert all(record["authority_lift"] is False for record in STATE_SWITCH_OWNER_REGISTRY)

    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "src").glob("**/*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == CANONICAL_STATE_SWITCH_PURE_MODEL_CANDIDATE:
            continue
        parallel = _FORBIDDEN_PARALLEL_PURE_MODEL_CLASSES & _class_names_in_module(path)
        if parallel:
            offenders.append(f"{rel}: {sorted(parallel)}")
    assert not offenders, f"parallel State-Switch pure-model classes outside candidate: {offenders}"


def test_local_consumers_remain_bounded_not_operative_ssot() -> None:
    offline = _registry_by_path("src/trading/master_v2/offline_double_play_scenario_replay_v0.py")
    assert offline["local_scope_only"] is True
    assert offline["operative_ssot"] is False
    offline_tree = ast.parse((REPO_ROOT / offline["path"]).read_text(encoding="utf-8"))
    assert _imports_double_play_state(offline_tree), (
        "offline replay must consume canonical pure model"
    )

    survival = _registry_by_path("src/trading/master_v2/double_play_survival.py")
    assert survival["local_scope_only"] is True
    assert survival["operative_ssot"] is False
    survival_tree = ast.parse((REPO_ROOT / survival["path"]).read_text(encoding="utf-8"))
    assert not _imports_double_play_state(survival_tree), (
        "survival limits must remain adjacent — not import pure-model SSOT"
    )

    display = _registry_by_path("src/trading/master_v2/double_play_dashboard_display.py")
    composition = _registry_by_path("src/trading/master_v2/double_play_composition.py")
    for record in (display, composition):
        assert record["local_scope_only"] is True
        assert record["authority_lift"] is False
        imports = _module_import_targets(REPO_ROOT / record["path"])
        assert any(mod.endswith("double_play_state") for mod in imports), record["path"]


def test_master_v2_completion_adapter_paths_import_no_parallel_state_switch_owner() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_parallel_state_switch_owner(tree)
        assert not bad, (
            f"{path.relative_to(REPO_ROOT)}: forbidden parallel State-Switch import: {bad}"
        )

    for fragment in _FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS:
        assert not list((REPO_ROOT / "docs" / "ops" / "specs").glob(f"*{fragment}*"))


def test_contract_crosslinks_ss_static_markers_without_redefinition() -> None:
    ss_spec = (REPO_ROOT / SS_SPEC_OWNER).read_text(encoding="utf-8")
    for marker in _SS_STATIC_MACHINE_MARKERS:
        assert marker in ss_spec, f"missing canonical SS marker: {marker}"

    static_test = (REPO_ROOT / SS_STATIC_TEST_CROSS_REFERENCE).read_text(encoding="utf-8")
    for marker in _SS_STATIC_MACHINE_MARKERS:
        assert marker in static_test, f"SS static test must bind marker: {marker}"

    c1_boundary = (REPO_ROOT / C1_PREDECESSOR_BOUNDARY_CROSS_REFERENCE).read_text(encoding="utf-8")
    assert "INV-045" in c1_boundary
    assert "DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_V0=true" in c1_boundary

    for fragment in _FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS:
        assert not list((REPO_ROOT / "docs" / "ops" / "specs").glob(f"*{fragment}*"))


def test_contract_defines_no_state_switch_formulas_and_is_non_authorizing() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    assert defined.isdisjoint(_FORBIDDEN_STATE_SWITCH_FORMULA_NAMES)

    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
    assert REPAIR_AUTHORITY_OUT_OF_SCOPE is True
    assert STATE_SWITCH_OWNER_DESIGN_SPEC_V0["repair_authority_out_of_scope"] is True


def test_forbidden_authority_and_side_switch_claim_keys_absent() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for key in _FORBIDDEN_OPERATIVE_STATE_SWITCH_CLAIM_KEYS:
        assert f"{key}=true" not in text
    for record in STATE_SWITCH_OWNER_REGISTRY:
        assert record["repair_authority"] is False, record["path"]
        assert record["authority_lift"] is False, record["path"]
        assert record["live_authorization"] is False, record["path"]
