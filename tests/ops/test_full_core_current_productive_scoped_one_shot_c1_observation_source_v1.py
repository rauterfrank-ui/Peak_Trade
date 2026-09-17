"""MS01 authority persist and owner pins for scoped one-shot C1 observation source."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY as EG_AUTHORITY_BOUNDARY,
    JOIN_SEAM_ID as EG_JOIN_SEAM_ID,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    AUTONOMY_CAN_CHANGE_TRADING_LOGIC,
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    AUTONOMY_CAN_RESELECT_DOWNSTREAM,
    BOUNDED_POLL_AUTHORIZED,
    CADENCE_OWNER_AUTHORIZED,
    CONTINUOUS_RUNTIME_AUTHORIZED,
    DAEMON_AUTHORIZED,
    EG_AUTHORITY_BOUNDARY_UNCHANGED,
    JOIN_SEAM_ID,
    LIVE_GET_EXECUTED,
    MS01_IMPLEMENTATION_STATUS,
    MS02_AUTHORIZED,
    MS03_AUTHORIZED,
    MS04_AUTHORIZED,
    MS05_AUTHORIZED,
    OWNER_GO,
    OWNER_GO_SCOPE,
    PERFORM_GET_DEFAULT,
    PRODUCER_AUTHORITY,
    RUNTIME_CYCLE_AUTHORIZED,
    THIS_SLICE,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_CREATED,
    CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_CREATED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
OWNER_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_scoped_one_shot_c1_observation_source_v1.py"
)
EG_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1.py"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
)
EH_HEADING = "### 11.2.1.EH FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE"
FORBIDDEN_SOURCE_SNIPPETS = (
    "while True",
    "time.sleep",
    "extract_finalized_candle_closes_v1",
    "_evaluate_c1_gate_v1",
    "trigger_current_productive_next_c1_and_exactly_one_cycle_v1",
    "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1",
    "FullCoreProductiveReadOnlyGetTransportV1",
    "execute_network=True",
    'execute_network": True',
    "scheduler",
    "PRODUCTIVE_CONTINUOUS_C1_OBSERVATION_SOURCE_OR_BOUNDED_POLL_OWNER_ABSENT",
)


def test_ms01_created_flag_pins_and_docs() -> None:
    assert CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_CREATED is True
    assert (
        CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_CREATED
        is True
    )
    assert OWNER_GO == ("OWNER_GO_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_V1")
    assert OWNER_GO_SCOPE == "MS01_AUTHORITY_PERSIST_AND_OWNER_PINS_ONLY"
    assert PRODUCER_AUTHORITY == "ONE_SHOT_PUBLIC_1M_C1_OBSERVATION_ACQUISITION_ONLY"
    assert EG_AUTHORITY_BOUNDARY_UNCHANGED == (
        "NEXT_C1_TRIGGER_AND_SINGLE_CYCLE_ORCHESTRATION_ONLY"
    )
    assert EG_AUTHORITY_BOUNDARY == EG_AUTHORITY_BOUNDARY_UNCHANGED
    assert EG_JOIN_SEAM_ID == (
        "CURRENT_PRODUCTIVE_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_SEAM_V1"
    )
    assert MS01_IMPLEMENTATION_STATUS == "AUTHORITY_SCAFFOLD_ONLY"
    assert BOUNDED_POLL_AUTHORIZED is False
    assert DAEMON_AUTHORIZED is False
    assert CADENCE_OWNER_AUTHORIZED is False
    assert CONTINUOUS_RUNTIME_AUTHORIZED is False
    assert RUNTIME_CYCLE_AUTHORIZED is False
    assert PERFORM_GET_DEFAULT is False
    assert LIVE_GET_EXECUTED is False
    assert MS02_AUTHORIZED is False
    assert MS03_AUTHORIZED is False
    assert MS04_AUTHORIZED is False
    assert MS05_AUTHORIZED is False
    assert AUTONOMY_CAN_CHANGE_TRADING_LOGIC is False
    assert AUTONOMY_CAN_RESELECT_DOWNSTREAM is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert JOIN_SEAM_ID == ("CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_SEAM_V1")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert EH_HEADING in runbook
    assert THIS_SLICE in runbook
    assert "CURRENT_PHASE=11.2.1.DW.FULL_CORE_POST_SUBMIT_LIFECYCLE_ACTIVATION_AND_JOIN" in runbook
    assert "PRODUCTIVE_CONTINUOUS_C1_OBSERVATION_SOURCE_OR_BOUNDED_POLL_OWNER_ABSENT" not in runbook
    assert "FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE" in mot
    assert "docs_token:" in spec
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_V1"
    ) in spec
    assert JOIN_SEAM_ID in atlas
    for path in PROTECTED_ALGORITHM_FILES:
        assert (REPO_ROOT / path).is_file()


def test_ms01_source_guards_forbid_successor_and_runtime_surfaces() -> None:
    source = OWNER_MODULE.read_text(encoding="utf-8")
    for snippet in FORBIDDEN_SOURCE_SNIPPETS:
        assert snippet not in source
    assert "MS01 AUTHORITY/CONTRACT SCAFFOLD ONLY" in source
    assert "def acquire_" not in source
    assert "urllib" not in source
    assert "http.client" not in source
    eg_source = EG_MODULE.read_text(encoding="utf-8")
    assert "while True" not in eg_source
    assert "time.sleep" not in eg_source
    assert 'execute_network": True' not in eg_source
    assert "execute_network = True" not in eg_source
