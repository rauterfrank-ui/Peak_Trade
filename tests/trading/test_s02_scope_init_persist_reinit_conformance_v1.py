"""S02 scope init / persist / reinit fail-closed conformance vectors.

BOUNDED_WORKPACKAGE=
MASTER_V2_DOUBLE_PLAY_BOUNDED_BEHAVIORAL_CONFORMANCE_VECTOR_SET_FROM_PROVEN_CELLS_ONLY_V1
SLICE=S02_SCOPE_INIT_PERSIST_REINIT
PRIMARY_OWNER=canonical_scope_initialization_v1
PERSISTENCE_LOAD_OWNER=ops.dynamic_scope_persistence_binding_v1

Additive behavioral assertions only. No trading-semantics mutation.
Initialization owner remains initialize_canonical_scope.
Cap-6.2 persistence is a durable carrier, not a decision owner.
Replay is a consumer, not the initialization owner.
FILEGATE / execution / Live / S03 trailing are out of this slice.

Epistemic:
- CANONICAL_AUTHORITY: initialize_canonical_scope; Cap-6.2 load/ensure
- FORENSIC_RAW_EVIDENCE: absent existing_scope=None init; persist/load
  snapshot identity; SCOPE_ALREADY_INITIALIZED preserves valid snapshot;
  assert_no_silent_reinitialization_v1 -> SILENT_REINITIALIZATION_BLOCKED
- ALREADY_ADJUDICATED: S02 vector set; RuntimeScopeState is not the init object
- Not claimed: non-SCOPE_VALID rebuild; SCOPE_CONTEXT_STALE vs Replay;
  classifier lifecycle vs snapshot lifecycle; trailing/ScopeEvent semantics

Path is tests/trading/ not tests/trading/master_v2/: the Economic Guard treats
tests/trading/master_v2/test_* as forbidden MASTER_V2 mutation surface.
Init fixtures are reused via import of the existing owner test helpers.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.dynamic_scope_persistence_binding_v1.authority_inventory_v1 import (
    inventory_dynamic_scope_binding_authority_surfaces_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    CANONICAL_SCOPE_SNAPSHOT_OWNER,
    DEFAULT_VENUE,
    PRODUCTIVE_DECISION_OWNER,
)
from src.ops.dynamic_scope_persistence_binding_v1.host_binding_v1 import (
    HostDynamicScopeBindingV1,
    dynamic_scope_config_digest_v1,
    ensure_host_dynamic_scope_binding_v1,
    stable_scope_session_id_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import CanonicalDynamicScopeStateV1
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    DynamicScopePersistenceError,
    assert_no_silent_reinitialization_v1,
    load_dynamic_scope_state_v1,
    persist_dynamic_scope_state_atomic_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.reason_codes_v1 import (
    DynamicScopeBindingFailureCodeV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.single_writer_v1 import (
    DynamicScopeStateSingleWriterV1,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeBlockReason,
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
    initialize_canonical_scope,
)

from tests.trading.master_v2.test_canonical_scope_initialization_v1 import (
    _context,
    _policy,
    _prerequisites,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_INIT_SOURCE = _REPO_ROOT / "src/trading/master_v2/canonical_scope_initialization_v1.py"
_REPLAY_SOURCE = _REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_PERSISTENCE_SOURCE = _REPO_ROOT / "src/ops/dynamic_scope_persistence_binding_v1/persistence_v1.py"
_HOST_BINDING_SOURCE = (
    _REPO_ROOT / "src/ops/dynamic_scope_persistence_binding_v1/host_binding_v1.py"
)
_COMPOSE_ORACLE = "compose_double_play_decision"
_REPOSITORY_SHA = "30fee92639cb4b9fac8d63f82e37f745873ce45f"


def _initialize_absent_prior():
    return initialize_canonical_scope(
        _context(),
        _policy(),
        _prerequisites(),
        existing_scope=None,
    )


def _persist_snapshot(
    state_root: Path,
    scope: CanonicalScopeSnapshotV1,
    *,
    repository_sha: str,
    config_digest: str,
) -> CanonicalDynamicScopeStateV1:
    session_id = stable_scope_session_id_v1(
        instrument_id=scope.instrument_id,
        venue=DEFAULT_VENUE,
        repository_sha=repository_sha,
        config_digest=config_digest,
    )
    state = CanonicalDynamicScopeStateV1(
        scope_session_id=session_id,
        instrument_id=scope.instrument_id,
        venue=DEFAULT_VENUE,
        existing_scope=scope,
        runtime_scope_state=None,
        runtime_scope_bound_instrument_id=scope.instrument_id,
        confirmation_session_id="",
        market_observation_epoch=None,
        last_market_event_time=None,
        last_accepted_observation_identity_digest=None,
        position_context={},
        scope_direction_state="",
        side_state="neutral_observe",
        host_trading_epoch=int(scope.initialized_at_trading_epoch),
        price_path_tail=(),
        repository_sha=repository_sha,
        config_digest=config_digest,
    )
    writer = DynamicScopeStateSingleWriterV1(
        state_root=state_root,
        session_id=session_id,
        instrument_id=scope.instrument_id,
    )
    writer.acquire()
    try:
        out = persist_dynamic_scope_state_atomic_v1(
            state_root=state_root,
            state=state,
            writer=writer,
        )
        persisted: CanonicalDynamicScopeStateV1 = out["state"]
        return persisted
    finally:
        writer.release()


def _imported_names(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
            names.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def _defined_function_names(tree: ast.AST) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _calls_named(tree: ast.AST, func_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == func_name:
                return True
            if isinstance(func, ast.Attribute) and func.attr == func_name:
                return True
    return False


def test_v_sc_01_absent_prior_initializes_canonical_snapshot() -> None:
    """V-SC-01: existing_scope=None initializes CanonicalScopeSnapshotV1."""
    result = _initialize_absent_prior()
    assert result.scope is not None
    assert isinstance(result.scope, CanonicalScopeSnapshotV1)
    assert result.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_VALID
    assert result.block_reasons == ()
    assert result.scope.lifecycle_state is CanonicalScopeLifecycleState.SCOPE_VALID
    assert result.scope.scope_id
    assert result.scope.semantic_digest
    assert len(result.scope.semantic_digest) == 64
    assert result.is_authority is False
    assert result.is_signal is False
    assert result.execution_eligible is False
    assert result.live_authorization is False
    assert result.order_effect is False
    assert result.runtime_effect is False
    assert result.scope_event_generated is False


def test_v_sc_02_persist_load_restores_existing_snapshot_identity(tmp_path: Path) -> None:
    """V-SC-02: Cap-6.2 persist/load restores snapshot identity; not None."""
    first = _initialize_absent_prior()
    assert first.scope is not None
    config_digest = dynamic_scope_config_digest_v1()
    _persist_snapshot(
        tmp_path,
        first.scope,
        repository_sha=_REPOSITORY_SHA,
        config_digest=config_digest,
    )

    loaded = load_dynamic_scope_state_v1(
        tmp_path,
        require_present=True,
        expected_repository_sha=_REPOSITORY_SHA,
        expected_config_digest=config_digest,
        expected_instrument_id=first.scope.instrument_id,
    )
    assert loaded is not None
    assert loaded.existing_scope is not None
    assert loaded.existing_scope.scope_id == first.scope.scope_id
    assert loaded.existing_scope.semantic_digest == first.scope.semantic_digest

    binding = HostDynamicScopeBindingV1()
    ensure_host_dynamic_scope_binding_v1(
        binding,
        instrument_id=first.scope.instrument_id,
        venue=DEFAULT_VENUE,
        repository_sha=_REPOSITORY_SHA,
        config_digest=config_digest,
        state_root=tmp_path,
    )
    assert binding.existing_scope is not None
    assert binding.existing_scope.scope_id == first.scope.scope_id
    assert binding.existing_scope.semantic_digest == first.scope.semantic_digest


def test_v_sc_03_valid_existing_scope_is_not_rebuilt() -> None:
    """V-SC-03 init layer: SCOPE_VALID snapshot is preserved, not rebuilt."""
    first = _initialize_absent_prior()
    assert first.scope is not None
    second = initialize_canonical_scope(
        _context(),
        _policy(),
        _prerequisites(),
        existing_scope=first.scope,
    )
    assert CanonicalScopeBlockReason.SCOPE_ALREADY_INITIALIZED in second.block_reasons
    assert second.scope is first.scope
    assert second.scope is not None
    assert second.scope.scope_id == first.scope.scope_id
    assert second.scope.semantic_digest == first.scope.semantic_digest


def test_v_sc_03_prior_commit_fresh_init_emits_silent_reinitialization_blocked(
    tmp_path: Path,
) -> None:
    """V-SC-03 persistence layer: exact unit guard after prior commit."""
    first = _initialize_absent_prior()
    assert first.scope is not None
    config_digest = dynamic_scope_config_digest_v1()
    _persist_snapshot(
        tmp_path,
        first.scope,
        repository_sha=_REPOSITORY_SHA,
        config_digest=config_digest,
    )
    with pytest.raises(DynamicScopePersistenceError) as excinfo:
        assert_no_silent_reinitialization_v1(
            state_root=tmp_path,
            loaded=None,
            initializing_fresh=True,
        )
    assert excinfo.value.code is DynamicScopeBindingFailureCodeV1.SILENT_REINITIALIZATION_BLOCKED


def test_v_neg_s02_persistence_and_replay_are_not_initialization_owners() -> None:
    """V-NEG: persistence is not trading-logic authority; Replay is not init owner."""
    inv = inventory_dynamic_scope_binding_authority_surfaces_v1()
    assert inv["serialization_adapter_has_decision_authority"] is False
    assert inv["parallel_master_v2_persistence_domain_created"] is False
    assert inv["parallel_double_play_persistence_domain_created"] is False
    assert inv["parallel_scope_domain_model_created"] is False
    assert inv["canonical_scope_snapshot_owner"] == CANONICAL_SCOPE_SNAPSHOT_OWNER
    assert inv["decision_authority"] == PRODUCTIVE_DECISION_OWNER
    assert CANONICAL_SCOPE_SNAPSHOT_OWNER.endswith("CanonicalScopeSnapshotV1")
    assert PRODUCTIVE_DECISION_OWNER.endswith("run_integrated_offline_trading_logic_replay_v1")
    assert inv["canonical_scope_snapshot_owner"] != inv["decision_authority"]

    init_tree = ast.parse(_INIT_SOURCE.read_text(encoding="utf-8"))
    replay_tree = ast.parse(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    persistence_tree = ast.parse(_PERSISTENCE_SOURCE.read_text(encoding="utf-8"))
    host_tree = ast.parse(_HOST_BINDING_SOURCE.read_text(encoding="utf-8"))

    assert "initialize_canonical_scope" in _defined_function_names(init_tree)
    assert "initialize_canonical_scope" not in _defined_function_names(replay_tree)
    assert "initialize_canonical_scope" not in _defined_function_names(persistence_tree)
    assert "initialize_canonical_scope" not in _defined_function_names(host_tree)

    replay_imports = _imported_names(replay_tree)
    assert any(
        name.endswith("canonical_scope_initialization_v1.initialize_canonical_scope")
        or name.endswith("canonical_scope_initialization_v1")
        for name in replay_imports
    )
    assert _calls_named(replay_tree, "initialize_canonical_scope") is True

    for tree in (init_tree, replay_tree, persistence_tree, host_tree):
        imported = _imported_names(tree)
        assert all(_COMPOSE_ORACLE not in name for name in imported)
        assert _calls_named(tree, _COMPOSE_ORACLE) is False
        assert all("src.execution" not in name for name in imported)
