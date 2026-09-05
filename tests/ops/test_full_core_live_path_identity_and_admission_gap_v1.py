"""Path identity and Full-Core live-admission gap DAG. Offline. No network."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.canary_isolation_v1 import (
    refuse_canary_plan_as_full_core_e2e_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE,
    CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E,
    CANARY_VENUE_PROOF_PATH_ROLE,
    CURRENT_LIVE_CORE_PATH_PROVEN,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
    G12_IS_NOT_FULL_CORE_E2E,
    LIVE_ARMED,
    LIVE_ENABLED,
    PATH_KIND,
    PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY,
    SECTION_11_13_5_NEXT_POINTER_DOMAIN,
    SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E,
    SECTION_11_14_NEXT_POINTER_DOMAIN,
    SECTION_11_14_POST_IS_NOT_STEP_29Q,
    STANDING_LIVE_AUTHORIZATION,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE,
    LIVE_ADMISSION_GAP_NODES,
    MAX_SAFE_REPO_INTERNAL_NEXT_SLICE,
    gap_node_v1,
    live_admission_gap_dag_v1,
)
from src.ops.full_core_live_path_composition_root_v1.overclaim_guards_v1 import (
    prove_package_does_not_import_wire_surfaces_v1,
)
from src.ops.full_core_live_path_composition_root_v1.path_identity_v1 import (
    bound_path_identity_v1,
    refuse_competing_productive_live_next_pointer_v1,
    refuse_historical_evidence_as_full_core_e2e_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_SIDE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP_V1.md"
REQUIRED_GAP_COMPONENTS = (
    "LIVE_ACCOUNT_BOUND",
    "FRESH_GET_PER_PRETRADE_DECISION",
    "PRIVATE_AUTH_PREFLIGHT",
    "MAX_AVAILABLE",
    "AVAILABLE_MARGIN",
    "PRICE_BAND",
    "LEVERAGE",
    "POS_MODE",
    "MARGIN_MODE",
    "INSTRUMENT_STATE",
    "ACCOUNT_MODE",
    "DURABLE_FILEGATE_RUNTIME_JOIN",
    "ExecutionAdmissionDecisionV1",
    "LiveExecutionPort",
    "OWNER_ONE_SHOT_EXECUTION_PERMIT",
    "LIVE_ENABLED",
    "LIVE_ARMED",
    "WIRE_SEND_PERMITTED",
)


def _section_11_2_1_i(text: str) -> str:
    start = text.index("11.2.1.I FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP")
    return text[start : text.index("## 11.3 Autonomy state model", start)]


def test_standing_identity_and_gates_remain_fail_closed() -> None:
    identity = bound_path_identity_v1()
    assert FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH == PATH_KIND == "FULL_CORE_LIVE_PATH"
    assert identity["FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH"] == "FULL_CORE_LIVE_PATH"
    assert identity["CANARY_VENUE_PROOF_PATH_ROLE"] == "HISTORICAL_AND_SCOPED_VENUE_PROOF"
    assert identity["CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E"] is False
    assert identity["CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY"] is False
    assert identity["FULL_CORE_SYSTEM_E2E_PROVEN"] is False
    assert identity["CURRENT_LIVE_CORE_PATH_PROVEN"] is False
    assert identity["STANDING_LIVE_AUTHORIZATION"] is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert STANDING_LIVE_AUTHORIZATION is False
    assert FULL_CORE_SYSTEM_E2E_PROVEN is False
    assert CURRENT_LIVE_CORE_PATH_PROVEN is False


def test_canary_and_section_11_14_are_not_productive_live_next_pointers() -> None:
    canary = refuse_competing_productive_live_next_pointer_v1("SECTION_11_13_5")
    ladder = refuse_competing_productive_live_next_pointer_v1("SECTION_11_14")
    full_core = refuse_competing_productive_live_next_pointer_v1("SECTION_11_2_1")
    assert canary["refused_as_productive_live_next_pointer"] is True
    assert ladder["refused_as_productive_live_next_pointer"] is True
    assert full_core["claimed_is_productive_live_authority"] is True
    assert full_core["refused_as_productive_live_next_pointer"] is False
    assert PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY == "SECTION_11_2_1"
    assert SECTION_11_13_5_NEXT_POINTER_DOMAIN == "SCOPED_CANARY_VENUE_PROOF_EVIDENCE_ONLY"
    assert SECTION_11_14_NEXT_POINTER_DOMAIN == (
        "HISTORICAL_CANARY_LIFECYCLE_EVIDENCE_LADDER_NOT_FULL_CORE_E2E"
    )


def test_historical_canary_and_g12_facts_are_not_full_core_e2e() -> None:
    verdict = refuse_historical_evidence_as_full_core_e2e_v1(
        {
            "LIVE_SUBMIT_ACK_OBSERVED": True,
            "LIVE_ACCOUNTING_RECONSTRUCTED": True,
            "G12": "OPEN",
            "canary_post": True,
        }
    )
    assert verdict["admissible_as_full_core_e2e"] is False
    assert SECTION_11_14_POST_IS_NOT_STEP_29Q is True
    assert SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E is True
    assert G12_IS_NOT_FULL_CORE_E2E is True
    assert CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE is True
    assert CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E is False
    canary_plan = refuse_canary_plan_as_full_core_e2e_v1(
        {"instrument_id": DEFAULT_INSTRUMENT_ID, "side": DEFAULT_SIDE}
    )
    assert canary_plan["admissible_as_full_core_e2e"] is False
    assert canary_plan["CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY"] is False
    assert canary_plan["CANARY_VENUE_PROOF_PATH_ROLE"] == CANARY_VENUE_PROOF_PATH_ROLE


def test_gap_dag_adjudicates_required_components_and_earliest_repo_internal_slice() -> None:
    dag = live_admission_gap_dag_v1()
    present = {node.component_id for node in LIVE_ADMISSION_GAP_NODES}
    for component in REQUIRED_GAP_COMPONENTS:
        assert component in present
        node = gap_node_v1(component)
        assert node.wiring_authorized is False
    filegate = gap_node_v1("DURABLE_FILEGATE_RUNTIME_JOIN")
    assert filegate.repo_internal_solvable is True
    assert filegate.fresh_external_evidence_required is False
    assert filegate.productive_account_access_required is False
    assert filegate.standing_live_gates_would_change is False
    assert filegate.implementation_status == "NOT_JOINED_UNKNOWN_BLOCKED"
    assert dag["EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY"] == (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == ("DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED")
    assert dag["MAX_SAFE_REPO_INTERNAL_NEXT_SLICE"] == MAX_SAFE_REPO_INTERNAL_NEXT_SLICE
    assert FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE is False
    assert dag["CANARY_29Q_CONSUMER_WIRING_AUTHORIZED"] is False
    reusable = set(dag["REUSABLE_MECHANISM_ONLY_COMPONENTS"])
    assert "MAX_AVAILABLE" in reusable
    assert "PRIVATE_AUTH_PREFLIGHT" in reusable
    live_enabled = gap_node_v1("LIVE_ENABLED")
    assert live_enabled.standing_live_gates_would_change is True
    assert live_enabled.repo_internal_solvable is False
    port = gap_node_v1("LiveExecutionPort")
    assert port.implementation_status == "CONSTRUCTION_FORBIDDEN"
    assert CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY is False


def test_package_still_does_not_import_wire_surfaces() -> None:
    proof = prove_package_does_not_import_wire_surfaces_v1()
    assert proof["ok"] is True
    assert proof["STANDING_LIVE_AUTHORIZATION"] is False
    assert proof["CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY"] is False


def test_runbook_and_spec_bind_path_identity_without_rewriting_11_14_facts() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    section = _section_11_2_1_i(runbook)
    assert "FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH=FULL_CORE_LIVE_PATH" in section
    assert "CANARY_VENUE_PROOF_PATH_ROLE=HISTORICAL_AND_SCOPED_VENUE_PROOF" in section
    assert "CANARY_VENUE_PROOF_PATH_IS_FULL_CORE_E2E=false" in section
    assert "CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY=false" in section
    assert "FULL_CORE_SYSTEM_E2E_PROVEN=false" in section
    assert "CURRENT_LIVE_CORE_PATH_PROVEN=false" in section
    assert "STANDING_LIVE_AUTHORIZATION=false" in section
    assert "SECTION_11_14_POST_IS_NOT_STEP_29Q=true" in section
    assert "SECTION_11_14_ACCOUNTING_IS_NOT_FULL_CORE_E2E=true" in section
    assert "G12_IS_NOT_FULL_CORE_E2E=true" in section
    assert "CANARY_SUBMIT_EVIDENCE_IS_NOT_FULL_CORE_SUBMIT_EVIDENCE=true" in section
    assert (
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED"
        in section
    )
    assert "GET_PERFORMED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "LIVE_ENABLED=false" in section
    assert "docs_token: DOCS_TOKEN_FULL_CORE_LIVE_PATH_IDENTITY_AND_ADMISSION_GAP_V1" in spec
    assert "CANARY_29Q_CONSUMER_WIRING_AUTHORIZED=false" in spec
    census = runbook[
        runbook.index("11.14 LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS") : runbook.index(
            "## 11.15 Full-autonomy observability and audit trail"
        )
    ]
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in census
    assert "LIVE_RESTART_RECONSTRUCTED=false" in census
    assert "LIVE_SUBMIT_ACK_OBSERVED=true" in census
    assert "BOUND_ORDID=3893505043080286208" in census
