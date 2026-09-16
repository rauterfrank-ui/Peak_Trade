"""Static contracts for BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2."""

from __future__ import annotations

import ast
from pathlib import Path

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED,
    PRODUCTIVE_HOST,
    SILENT_DYNAMIC_SCOPE_REINITIALIZATION,
)
from src.ops.derive_scope_event_distances_v1.constants_v1 import AUTHORITY_EFFECT
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CHOP_CAN_MUTATE_SIDE_STATE,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
)
from tests.ops.test_derive_scope_event_distances_v1 import (
    PRODUCTIVE_CONSUMER_ROOTS,
    REPO_ROOT,
    _imported_modules,
    _is_forbidden_import,
    _iter_python_files,
)

SPEC = REPO_ROOT / "docs/ops/specs/BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2.md"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
REPLAY = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
CURRENT_PRODUCTIVE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
)
CAP62_HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
HARDENING_V2 = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "hardening_cycle_bridge_v2.py"
)
TRANSITION = REPO_ROOT / "src/trading/master_v2/double_play_state.py"
ENTRY_EXIT = REPO_ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"


def _read(path: Path) -> str:
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_cc_a_contract_and_pointers_persist_without_authority_expansion() -> None:
    spec = _read(SPEC)
    runbook = _read(RUNBOOK)
    mot = _read(MOT)
    assert "DOCS_TOKEN_BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2" in spec
    assert "MODEL_C_BOUND=false" in spec
    assert "BLOCKED_CROSS_GO_CONSUMED=false" in spec
    assert "LIVE_OR_EXECUTION_AUTHORITY_TOUCHED=false" in spec
    assert "VENUE_SIDESTATE_MUTATION_AUTHORIZED=false" in spec
    assert "HARDENING_V2_DISPOSITION=PARKED_WITH_REASON" in spec
    assert "### 9.2.7 Bounded post-disentanglement" in runbook
    assert "MODEL_C_BOUND=false" in runbook
    assert "NEXT_OWNER_GO_CONSUMED=false" in runbook
    assert "BOUNDED_POST_DISENTANGLEMENT_DOUBLE_PLAY_CLEAN_CORE_REPAIR_V2.md" in mot
    assert "§9.2.7" in mot
    assert "MODEL_C_BOUND=true" not in spec
    assert "MODEL_C_BOUND=true" not in runbook


def test_cc_e_classification_only_no_venue_sidestate_mutation_in_wp() -> None:
    spec = _read(SPEC)
    host = _read(CURRENT_PRODUCTIVE)
    assert "VENUE_SIDESTATE_SEED_ADJUDICATION=OWNER_DECISION_REQUIRED" in spec
    assert "VENUE_SIDESTATE_MUTATION_PERFORMED=false" in spec
    assert "LEGITIMATE_RECON_RESTORE" in spec
    assert "COMPETING_SIDESTATE_WRITER" in spec
    assert "POSITION_CONTEXT_ONLY" in spec
    assert "if existing_position_side is ExistingPositionSide.LONG:" in host
    assert "side_state = SideState.LONG_ACTIVE" in host
    assert "elif existing_position_side is ExistingPositionSide.SHORT:" in host
    assert "side_state = SideState.SHORT_ACTIVE" in host


def test_cc_f_hardening_v2_remains_parked_without_runtime_repair() -> None:
    spec = _read(SPEC)
    hardening = _read(HARDENING_V2)
    assert "HARDENING_V2_DISPOSITION=PARKED_WITH_REASON" in spec
    assert "HARDENING_V2_RUNTIME_MUTATION_AUTHORIZED=false" in spec
    assert "existing_scope=None" in hardening
    assert PRODUCTIVE_HOST.endswith("decision_economics_cycle_bridge_v1.py")


def test_cc_g_model_c_remains_unbound_with_zero_productive_consumers() -> None:
    spec = _read(SPEC)
    replay = _read(REPLAY)
    assert "MODEL_C_BOUND=false" in spec
    assert "derive_scope_event_distances_v1" not in replay
    assert AUTHORITY_EFFECT == "NONE"
    hits: list[str] = []
    for root in PRODUCTIVE_CONSUMER_ROOTS:
        for path in _iter_python_files(REPO_ROOT / root):
            for module in _imported_modules(path):
                if _is_forbidden_import(module):
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{module}")
    assert hits == []
    replay_tree = ast.parse(replay, filename=str(REPLAY))
    imported: list[str] = []
    for node in ast.walk(replay_tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert not any("derive_scope_event_distances_v1" in name for name in imported)


def test_cc_d_cursor_owned_fields_pass_through_on_in_scope_hosts() -> None:
    current = _read(CURRENT_PRODUCTIVE)
    cap62 = _read(CAP62_HOST)
    assert "existing_scope=existing_scope," in current
    assert "runtime_scope_state=runtime_scope_state," in current
    assert "existing_scope=replay.intermediate.current_scope" in current
    assert "runtime_scope_state=replay.intermediate.runtime_scope_state_after" in current
    assert "existing_scope=state.dynamic_scope_binding.existing_scope" in cap62
    assert "runtime_scope_state=state.dynamic_scope_binding.runtime_scope_state" in cap62
    assert SILENT_DYNAMIC_SCOPE_REINITIALIZATION is False
    assert MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED is False


def test_cc_h_authority_invariants_remain() -> None:
    spec = _read(SPEC)
    entry = _read(ENTRY_EXIT)
    transition = _read(TRANSITION)
    replay = _read(REPLAY)
    current = _read(CURRENT_PRODUCTIVE)
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert LIVE_AUTHORIZED == "false"
    assert ORDERS_ENABLED == "false"
    assert CHOP_CAN_MUTATE_SIDE_STATE == "false"
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")
    assert "position_flip_allowed=False" in entry.replace(" ", "")
    assert "CAP65_PROFIT_PROTECTION_JOINED=false" in spec
    assert "KILL_SWITCH_ROLE=SAFETY_VETO_ONLY" in spec
    assert "MODEL_A" not in replay
    assert "price_vs_boundary" not in transition
    assert "OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1" in spec
    assert "BLOCKED_CROSS_GO_CONSUMED=false" in spec
    assert "dynamic_scope_rules=" not in current
