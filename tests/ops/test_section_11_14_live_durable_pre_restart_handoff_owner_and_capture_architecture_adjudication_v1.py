"""Architecture adjudication tests for the first §11.14 Live handoff owner."""

from __future__ import annotations

from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    HOST_CRASH_DURABILITY,
)
from src.learning.mutation_critical_control_state_storage_v1.authority_v1 import (
    ADMISSION_TRUE,
    DEPENDENT_MUTATION_ALLOWED,
    PRODUCTIVE_HOST_BINDING,
    SUPERVISOR_ACTIVATED,
)
from src.learning.mutation_critical_control_state_storage_v1.crash_reproof_v1 import (
    POWER_LOSS_DURABILITY,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD,
    HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO,
    LIVE_RESTART_RECONSTRUCTED,
    SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_architecture_adjudication_execute_v1 import (
    execute_live_durable_pre_restart_handoff_owner_and_capture_architecture_adjudication_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_and_capture_architecture_adjudication_v1 import (
    FIRST_OWNER_PRODUCTIVELY_BOUND,
    IMPLEMENTATION_AUTHORIZED,
    PROPOSED_FIRST_OWNER_ADJUDICATION,
    PROPOSED_NEXT_SLICE,
    STEP_29P_HANDOFF_RELATION,
    bind_capture_seam_graph_census_v1,
    bind_durability_contract_adjudication_v1,
    bind_owner_and_capture_architecture_adjudication_v1,
    bind_owner_contract_adjudication_v1,
    bind_pos_semantics_adjudication_v1,
    bind_restart_admission_predicate_v1,
    bind_step_29p_handoff_relation_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_vacancy_contract_v1 import (
    PROPOSED_FIRST_OWNER_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_proposed_owner_is_eligible_and_not_bound() -> None:
    owner = bind_owner_contract_adjudication_v1()
    assert owner["SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"] == "NONE"
    assert owner["PROPOSED_FIRST_OWNER_ID"] == PROPOSED_FIRST_OWNER_ID
    assert owner["PROPOSED_FIRST_OWNER_ADJUDICATION"] == (
        "ELIGIBLE_AS_FIRST_LOGICAL_OWNER_ID_NOT_PRODUCTIVELY_BOUND"
    )
    assert owner["FIRST_OWNER_CONTRACT_DECLARED"] is True
    assert owner["FIRST_OWNER_PRODUCTIVELY_BOUND"] is False
    assert owner["NAME_OR_DECLARATION_IS_NOT_PRODUCTIVE_BIND"] is True
    assert owner["COMPETING_PRODUCTIVE_OWNER_COUNT"] == 0
    assert owner["STORAGE_OWNER_MINTED"] is False
    assert owner["WRITER_BOUND"] is False
    assert owner["READER_BOUND"] is False
    assert FIRST_OWNER_PRODUCTIVELY_BOUND is False
    assert PROPOSED_FIRST_OWNER_ADJUDICATION == owner["PROPOSED_FIRST_OWNER_ADJUDICATION"]


def test_pos_semantics_remain_unproven_with_zero_acceptable_producers() -> None:
    pos = bind_pos_semantics_adjudication_v1()
    assert pos["POS_SEMANTICS_STATUS"] == "UNPROVEN"
    assert pos["POS_CANONICAL_MEANING"] == "UNPROVEN"
    assert pos["POS_UNIT"] == "UNPROVEN"
    assert pos["POS_SIGN_SEMANTICS"] == "UNPROVEN"
    assert pos["POS_ACCEPTABLE_PRODUCER_COUNT"] == 0
    assert pos["POS_ACCEPTABLE_PRODUCERS"] == []
    assert pos["BOUND_POS_FIELD_PRESENT"] is False
    assert pos["BOUND_IDENTITY_HAS_FILL_SZ_NOT_POS"] is True
    assert pos["NO_UNIQUE_CANONICAL_MEANING_FROM_AUTHORITY"] is True
    assert len(pos["POS_REJECTED_PRODUCERS_WITH_REASON"]) >= 16


def test_no_acceptable_complete_capture_seam() -> None:
    seams = bind_capture_seam_graph_census_v1()
    assert seams["ACCEPTABLE_COMPLETE_SEAM_COUNT"] == 0
    assert seams["SEAM_CANDIDATE_COUNT"] == 16
    assert seams["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert seams["EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT"] == "NONE"
    assert seams["EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN"] is False
    assert seams["NO_MOMENT_HAS_ALL_FIVE_PEAK_TRADE_OWNED_CONTEMPORANEOUS_FIELDS"] is True
    for row in seams["seams"]:
        assert row["ACCEPTABLE"] in {"false", "unproven"}
        assert row["ACCEPTABLE"] != "true"
        assert "pos" in row["MISSING_FIELDS"]


def test_durability_remains_unproven_and_not_inherited() -> None:
    durability = bind_durability_contract_adjudication_v1()
    assert durability["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert durability["POWER_LOSS_DURABILITY"] == "UNPROVEN"
    assert durability["DURABILITY_PROVEN_EFFECTIVE"] is False
    assert durability["CURRENTLY_PROVEN_PRIMITIVES"] == []
    assert durability["A1_PROCESS_KILL_PROOF_IS_NOT_INHERITED"] is True
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"


def test_restart_admission_predicate_stays_false() -> None:
    admission = bind_restart_admission_predicate_v1()
    assert admission["RESTART_HANDOFF_ELIGIBLE"] is False
    assert admission["ADMISSION_TRUE"] is False
    assert admission["SUPERVISOR_ACTIVATED"] is False
    assert "pos_semantics_proven" in admission["false_required"]
    assert "owner_bound" in admission["false_required"]
    assert "capture_seam_bound" in admission["false_required"]
    assert ADMISSION_TRUE is False
    assert SUPERVISOR_ACTIVATED is False
    assert LIVE_RESTART_RECONSTRUCTED is False


def test_step_29p_is_orthogonal_to_this_handoff_owner() -> None:
    relation = bind_step_29p_handoff_relation_v1()
    assert relation["STEP_29P_HANDOFF_RELATION"] == (
        "ORTHOGONAL_TO_SECTION_11_14_LIVE_CANARY_HANDOFF"
    )
    assert relation["ORTHOGONAL_TO_THIS_FIELD"] is True
    assert relation["REQUIRED_FOR_HANDOFF_OWNER"] is False
    assert relation["REQUIRED_FOR_CAPTURE_SEAM"] is False
    assert relation["REQUIRED_FOR_WRITER"] is False
    assert relation["REQUIRED_FOR_READER"] is False
    assert relation["REQUIRED_FOR_RESTART_RECONSTRUCTION_OF_THIS_FIELD"] is False
    assert relation["FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD"] is False
    assert FULL_CORE_29P_REQUIRED_FOR_THIS_FIELD is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == ("STEP_29P_EQUITY_DIMENSION_BINDING_MISSING")
    assert STEP_29P_HANDOFF_RELATION == relation["STEP_29P_HANDOFF_RELATION"]


def test_architecture_execute_is_offline_and_does_not_authorize_implementation() -> None:
    result = (
        execute_live_durable_pre_restart_handoff_owner_and_capture_architecture_adjudication_v1(
            owner_go=HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            repo_root=REPO_ROOT,
            run_id="20260906T213200Z-test",
        )
    )
    summary = result["summary"]
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["ARCHITECTURE_ADJUDICATION_COMPLETE"] is True
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert summary["ADMISSION_TRUE"] is False
    assert summary["SUPERVISOR_ACTIVATED"] is False
    assert summary["SEQUENCE_AUTO_EXECUTED"] is False
    assert summary["POS_SEMANTICS"] == "UNPROVEN"
    assert summary["POS_ACCEPTABLE_PRODUCER_COUNT"] == 0
    assert summary["SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT"] == "NONE"
    assert summary["PROPOSED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE
    assert result["raw_exchanges"] == []
    assert HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO.endswith(
        "OWNER_AND_CAPTURE_ARCHITECTURE_ADJUDICATION_V1"
    )
    assert SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT == "NONE"
    assert IMPLEMENTATION_AUTHORIZED is False
    assert DEPENDENT_MUTATION_ALLOWED is False
    assert PRODUCTIVE_HOST_BINDING is False
    architecture = bind_owner_and_capture_architecture_adjudication_v1()
    assert architecture["ARCHITECTURE_ADJUDICATION_COMPLETE"] is True
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={"source_kind": "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF_CENSUS"}
    )
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
