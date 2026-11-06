"""Static fail-closed contract: Master V2 Dynamic Scope owner boundary v0.

Package C Slice C1 (INV-045) formalises Dynamic Scope envelope owner, authority, and
import boundaries. Inventories existing production modules via AST/read-only analysis.
Declares ``double_play_state.py`` as the sole canonical Dynamic Scope pure-model
candidate while offline replay, dashboard display, composition, and handoff paths
retain bounded consumer or value-transport scope only.

Cross-references existing docs-static guards without duplicating them:
``tests/ops/test_master_v2_dynamic_scope_envelope_contract_static_v0.py``.

Non-authorizing. No runtime, network, testnet execution, hot-path wiring, or formula
duplication. C2 / INV-046 state-switch owner formalisation is explicitly out of scope.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final, Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_MARKER = "DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_V0=true"
AUTHORITY_LIFT = False
C2_STATE_SWITCH_OUT_OF_SCOPE = True
REPAIR_AUTHORITY_OUT_OF_SCOPE = True

CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE = "src/trading/master_v2/double_play_state.py"
DSE_SPEC_OWNER = "docs/ops/specs/FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
DSE_STATIC_TEST_CROSS_REFERENCE = (
    "tests/ops/test_master_v2_dynamic_scope_envelope_contract_static_v0.py"
)
DSE_CROSSLINK_ANTI_DRIFT_REFERENCE = (
    "tests/ops/test_futures_dynamic_scope_envelope_contract_static_crosslink_contract_v0.py"
)

OwnerRole = Literal[
    "DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE",
    "OFFLINE_REPLAY_CONSUMER",
    "SURVIVAL_LIMITS_ADJACENT",
    "SCOPE_ENVELOPE_TRANSPORT",
    "SCOPE_ENVELOPE_VALIDATION",
    "DISPLAY_CONSUMER",
    "COMPOSITION_CONSUMER",
    "DSE_VOCABULARY_OWNER",
    "SCOPE_CAPITAL_DISTINCTION",
]

_BINDING_ROLES: Final[frozenset[str]] = frozenset(
    {
        "MASTER_V2_DYNAMIC_SCOPE_BINDING",
        "COMPLETION_DYNAMIC_SCOPE_BINDING",
        "ADAPTER_DYNAMIC_SCOPE_BINDING",
    }
)

_VALID_OWNER_ROLES: Final[frozenset[str]] = frozenset(
    {
        "DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE",
        "OFFLINE_REPLAY_CONSUMER",
        "SURVIVAL_LIMITS_ADJACENT",
        "SCOPE_ENVELOPE_TRANSPORT",
        "SCOPE_ENVELOPE_VALIDATION",
        "DISPLAY_CONSUMER",
        "COMPOSITION_CONSUMER",
        "DSE_VOCABULARY_OWNER",
        "SCOPE_CAPITAL_DISTINCTION",
    }
)

_CANONICAL_PURE_MODEL_SYMBOLS: Final[tuple[str, ...]] = (
    "DynamicScopeRules",
    "ScopeEvent",
    "RuntimeScopeState",
    "StaticHardLimits",
    "RuntimeEnvelope",
    "SideState",
    "TransitionDecision",
    "ActiveSide",
    "update_dynamic_boundaries",
    "transition_state",
    "envelope_valid",
    "rules_valid",
)

_FORBIDDEN_PARALLEL_PURE_MODEL_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "DynamicScopeRules",
        "RuntimeScopeState",
        "RuntimeEnvelope",
    }
)

_FORBIDDEN_DYNAMIC_SCOPE_FORMULA_NAMES: Final[frozenset[str]] = frozenset(
    {
        "update_dynamic_boundaries",
        "transition_state",
        "envelope_valid",
        "rules_valid",
        "clamp_band_width",
    }
)

_FORBIDDEN_OPERATIVE_DYNAMIC_SCOPE_CLAIM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "DYNAMIC_SCOPE_OPERATIVE_SSOT",
        "LIVE_AUTHORIZATION_GRANTED",
        "DYNAMIC_SCOPE_REPAIR_AUTHORITY",
        "REPAIR_AUTHORITY_GRANTED",
        "AUTOMATIC_SCOPE_REPAIR_ENABLED",
        "OPERATIVE_DYNAMIC_SCOPE_SSOT",
        "DYNAMIC_SCOPE_HOT_PATH_WIRED",
        "KILLSWITCH_SUBSTITUTED_BY_DYNAMIC_SCOPE",
        "EVIDENCE_AS_DYNAMIC_SCOPE_PERMISSION",
        "DASHBOARD_AS_DYNAMIC_SCOPE_PERMISSION",
    }
)

_FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS: Final[tuple[str, ...]] = (
    "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V1",
    "CANONICAL_DYNAMIC_SCOPE_ENVELOPE_V1",
)

_DSE_STATIC_MACHINE_MARKERS: Final[tuple[str, ...]] = (
    "MARKER: STATIC_HARD_LIMITS_NEVER_WIDENED_BY_DYNAMIC_RULES",
    "MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_ENVELOPE",
    "MARKER: DYNAMIC_SCOPE_TRAIL_NOT_KILLSWITCH",
    "MARKER: STATE_SWITCH_CONSUMES_CONFIRMED_SCOPE_EVENTS_ONLY",
    "MARKER: ENVELOPE_COMPLIANCE_NOT_LIVE_AUTHORIZATION",
    "MARKER: CANDIDATE_VS_CONFIRMED_SCOPE_EVENTS_DISTINCT",
)

_MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS: Final[tuple[Path, ...]] = (
    REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py",
    REPO_ROOT / "src" / "ops" / "offline_master_v2_replay_six_node_validation_graph_binding_v0.py",
    REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
)

_FORBIDDEN_PARALLEL_DYNAMIC_SCOPE_IMPORT_FRAGMENTS: Final[tuple[str, ...]] = (
    "canonical_dynamic_scope",
    "dynamic_scope_envelope_contract_v1",
    "futures_dynamic_scope_envelope_contract_v1",
)


class DynamicScopeOwnerRecord(TypedDict):
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


class DynamicScopeOwnerDesignSpecV0(TypedDict):
    package_slice: str
    inventory_id: str
    pure_model_candidate_path: str
    dse_spec_owner: str
    dse_static_test_cross_reference: str
    c2_state_switch_out_of_scope: bool
    repair_authority_out_of_scope: bool


DYNAMIC_SCOPE_OWNER_DESIGN_SPEC_V0: DynamicScopeOwnerDesignSpecV0 = {
    "package_slice": "PACKAGE_C_SLICE_C1",
    "inventory_id": "INV-045",
    "pure_model_candidate_path": CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE,
    "dse_spec_owner": DSE_SPEC_OWNER,
    "dse_static_test_cross_reference": DSE_STATIC_TEST_CROSS_REFERENCE,
    "c2_state_switch_out_of_scope": True,
    "repair_authority_out_of_scope": True,
}

DYNAMIC_SCOPE_OWNER_REGISTRY: tuple[DynamicScopeOwnerRecord, ...] = (
    {
        "path": CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE,
        "role": "DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": False,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": True,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": (
            "Pure Dynamic Scope model: ScopeEvent, boundaries, transition_state, envelope rules"
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
        "responsibility_scope": "Offline replay consumer — must not become operative runtime SSOT",
        "surface_symbols": (
            "DynamicScopeRules",
            "ScopeEvent",
            "SideState",
            "transition_state",
            "update_dynamic_boundaries",
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
        "responsibility_scope": "Arithmetic survival limits adjacent to Double Play — not Dynamic Scope SSOT",
        "surface_symbols": ("SurvivalEnvelopeDecision", "evaluate_survival_envelope"),
    },
    {
        "path": "src/trading/master_v2/decision_packet_v1.py",
        "role": "SCOPE_ENVELOPE_TRANSPORT",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "scope_envelope handoff is value-transport only — no pure-model import",
        "surface_symbols": ("ScopeCapitalEnvelopeHandoffV1", "scope_envelope"),
    },
    {
        "path": "src/trading/master_v2/input_adapter_v1.py",
        "role": "SCOPE_ENVELOPE_VALIDATION",
        "master_v2_relevant": True,
        "completion_adapter_relevant": True,
        "local_scope_only": True,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Boolean scope_envelope guard only — no Dynamic Scope authority",
        "surface_symbols": ("scope_envelope",),
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
        "responsibility_scope": "Composition consumes SideState/TransitionDecision — not scope SSOT",
        "surface_symbols": ("SideState", "TransitionDecision"),
    },
    {
        "path": DSE_SPEC_OWNER,
        "role": "DSE_VOCABULARY_OWNER",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Canonical docs-only Dynamic Scope Envelope vocabulary owner",
        "surface_symbols": (),
    },
    {
        "path": "docs/ops/specs/MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md",
        "role": "SCOPE_CAPITAL_DISTINCTION",
        "master_v2_relevant": True,
        "completion_adapter_relevant": False,
        "local_scope_only": False,
        "repair_authority": False,
        "operative_ssot": False,
        "canonical_candidate": False,
        "authority_lift": False,
        "live_authorization": False,
        "responsibility_scope": "Scope/capital distinction crosslink — distinct upstream layer",
        "surface_symbols": (),
    },
)


def _registry_by_path(path: str) -> DynamicScopeOwnerRecord:
    for record in DYNAMIC_SCOPE_OWNER_REGISTRY:
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


def _imports_parallel_dynamic_scope_owner(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = (alias.name or "").lower()
                if any(
                    fragment in name
                    for fragment in _FORBIDDEN_PARALLEL_DYNAMIC_SCOPE_IMPORT_FRAGMENTS
                ):
                    violations.append(f"import {alias.name}")
                if "double_play_state" not in name and "dynamic_scope" in name:
                    violations.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            if any(
                fragment in mod for fragment in _FORBIDDEN_PARALLEL_DYNAMIC_SCOPE_IMPORT_FRAGMENTS
            ):
                violations.append(f"from {node.module} import ...")
            if "double_play_state" not in mod and "dynamic_scope" in mod:
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


def test_dynamic_scope_owner_inventory_complete_and_roles_unique() -> None:
    paths = [record["path"] for record in DYNAMIC_SCOPE_OWNER_REGISTRY]
    assert len(paths) == len(set(paths)), "duplicate owner paths in registry"
    roles = [record["role"] for record in DYNAMIC_SCOPE_OWNER_REGISTRY]
    assert all(role in _VALID_OWNER_ROLES for role in roles)
    assert all(role not in _BINDING_ROLES for role in roles)
    for record in DYNAMIC_SCOPE_OWNER_REGISTRY:
        owner_path = REPO_ROOT / record["path"]
        assert owner_path.is_file(), record["path"]
        assert record["responsibility_scope"].strip(), record["path"]
        assert isinstance(record["surface_symbols"], tuple)

    assert DYNAMIC_SCOPE_OWNER_DESIGN_SPEC_V0["inventory_id"] == "INV-045"
    assert DYNAMIC_SCOPE_OWNER_DESIGN_SPEC_V0["pure_model_candidate_path"] == (
        CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE
    )
    assert (REPO_ROOT / DSE_STATIC_TEST_CROSS_REFERENCE).is_file()
    assert (REPO_ROOT / DSE_CROSSLINK_ANTI_DRIFT_REFERENCE).is_file()

    candidate = _registry_by_path(CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE)
    _production_symbols_exist(candidate["path"], candidate["surface_symbols"])


def test_exactly_one_dynamic_scope_pure_model_candidate() -> None:
    candidates = [
        record["path"]
        for record in DYNAMIC_SCOPE_OWNER_REGISTRY
        if record["role"] == "DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE"
    ]
    assert candidates == [CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE]
    candidate = _registry_by_path(CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE)
    assert candidate["canonical_candidate"] is True
    assert candidate["authority_lift"] is False
    assert candidate["live_authorization"] is False
    assert candidate["repair_authority"] is False

    non_candidates = [
        record for record in DYNAMIC_SCOPE_OWNER_REGISTRY if not record["canonical_candidate"]
    ]
    assert all(record["operative_ssot"] is False for record in non_candidates)
    assert all(record["authority_lift"] is False for record in DYNAMIC_SCOPE_OWNER_REGISTRY)

    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "src").glob("**/*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == CANONICAL_DYNAMIC_SCOPE_PURE_MODEL_CANDIDATE:
            continue
        parallel = _FORBIDDEN_PARALLEL_PURE_MODEL_CLASSES & _class_names_in_module(path)
        if parallel:
            offenders.append(f"{rel}: {sorted(parallel)}")
    assert not offenders, (
        f"parallel Dynamic Scope pure-model classes outside candidate: {offenders}"
    )


def test_local_consumers_remain_bounded_not_operative_ssot() -> None:
    offline = _registry_by_path("src/trading/master_v2/offline_double_play_scenario_replay_v0.py")
    assert offline["local_scope_only"] is True
    assert offline["operative_ssot"] is False
    offline_tree = ast.parse((REPO_ROOT / offline["path"]).read_text(encoding="utf-8"))
    assert _imports_double_play_state(offline_tree), (
        "offline replay must consume canonical pure model"
    )

    transport = _registry_by_path("src/trading/master_v2/decision_packet_v1.py")
    validation = _registry_by_path("src/trading/master_v2/input_adapter_v1.py")
    for record in (transport, validation):
        assert record["local_scope_only"] is True
        assert record["operative_ssot"] is False
        tree = ast.parse((REPO_ROOT / record["path"]).read_text(encoding="utf-8"))
        assert not _imports_double_play_state(tree), (
            f"{record['path']}: handoff paths must not import pure-model SSOT"
        )

    display = _registry_by_path("src/trading/master_v2/double_play_dashboard_display.py")
    composition = _registry_by_path("src/trading/master_v2/double_play_composition.py")
    for record in (display, composition):
        assert record["local_scope_only"] is True
        assert record["authority_lift"] is False
        imports = _module_import_targets(REPO_ROOT / record["path"])
        assert any(mod.endswith("double_play_state") for mod in imports), record["path"]


def test_master_v2_completion_adapter_paths_import_no_parallel_dynamic_scope_owner() -> None:
    seen: set[Path] = set()
    for path in _MASTER_V2_COMPLETION_ADAPTER_BINDING_PATHS:
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        bad = _imports_parallel_dynamic_scope_owner(tree)
        assert not bad, (
            f"{path.relative_to(REPO_ROOT)}: forbidden parallel Dynamic Scope import: {bad}"
        )

    for fragment in _FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS:
        assert not list((REPO_ROOT / "docs" / "ops" / "specs").glob(f"*{fragment}*"))


def test_contract_crosslinks_dse_static_markers_without_redefinition() -> None:
    dse_spec = (REPO_ROOT / DSE_SPEC_OWNER).read_text(encoding="utf-8")
    for marker in _DSE_STATIC_MACHINE_MARKERS:
        assert marker in dse_spec, f"missing canonical DSE marker: {marker}"

    static_test = (REPO_ROOT / DSE_STATIC_TEST_CROSS_REFERENCE).read_text(encoding="utf-8")
    for marker in _DSE_STATIC_MACHINE_MARKERS:
        assert marker in static_test, f"DSE static test must bind marker: {marker}"

    crosslink = (REPO_ROOT / DSE_CROSSLINK_ANTI_DRIFT_REFERENCE).read_text(encoding="utf-8")
    for fragment in _FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS:
        assert fragment in crosslink, (
            f"anti-drift guard must reference forbidden fragment: {fragment}"
        )


def test_contract_defines_no_dynamic_scope_formulas_and_is_non_authorizing() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    }
    assert defined.isdisjoint(_FORBIDDEN_DYNAMIC_SCOPE_FORMULA_NAMES)

    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert AUTHORITY_LIFT is False
    assert C2_STATE_SWITCH_OUT_OF_SCOPE is True
    assert REPAIR_AUTHORITY_OUT_OF_SCOPE is True
    assert DYNAMIC_SCOPE_OWNER_DESIGN_SPEC_V0["c2_state_switch_out_of_scope"] is True


def test_forbidden_authority_and_repair_claim_keys_absent() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for key in _FORBIDDEN_OPERATIVE_DYNAMIC_SCOPE_CLAIM_KEYS:
        assert f"{key}=true" not in text
    for record in DYNAMIC_SCOPE_OWNER_REGISTRY:
        assert record["repair_authority"] is False, record["path"]
        assert record["authority_lift"] is False, record["path"]
        assert record["live_authorization"] is False, record["path"]
