"""D6 scoped read-only observation-boundary contract persist."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EARLIEST_D6_KIND_SET_DEPENDENCY,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    OBSERVATION_BOUNDARY_CONTRACT_CREATED,
    OBSERVATION_BOUNDARY_CONTRACT_STATUS,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESIDUAL_KIND_DECISION,
    SOURCE_SELECTED,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_ATLAS_AUTHORITY,
    ACCOUNT_COMPOSITION_OBSERVATION_DEFINED,
    EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED,
    FEE_EMBEDDING_OBSERVATION_DEFINED,
    LIABILITY_OBSERVATION_DEFINED,
    OBSERVATION_IS_NOT_COMPLETENESS_UNLESS_RANGE_ORDERING_PROVENANCE_PROVEN,
    OBSERVATION_IS_NOT_D7_AUTHORIZATION,
    OBSERVATION_IS_NOT_KIND_RATIFICATION,
    OBSERVATION_IS_NOT_MS2_RELEASE,
    OBSERVATION_IS_NOT_RAW_EQ_SOURCE_AUTHORITY,
    OBSERVATION_IS_NOT_SOURCE_AUTHORITY,
    OWNER,
    PATH_A_ARCHIVE_OR_REPO_SEARCH,
    PATH_B_SCOPED_READ_ONLY_OBSERVATION,
    PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    CANDIDATE_RESIDUAL,
    CANDIDATE_U05,
    CANDIDATE_U06,
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.scoped_read_only_observation_boundary_contract_v1 import (
    ATLAS_AUTHORITY_NONE,
    BOUNDARY_STATUS_DEFINED_NOT_EXECUTED,
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    OBS_ACCOUNT_COMPOSITION,
    OBS_EXOGENOUS_COVERAGE,
    OBS_FEE_EMBEDDING,
    OBS_LIABILITY,
    PATH_B_SELECTED_BUT_BLOCKED,
    SELECTION_NONE,
    SURFACE_CLASS_CANDIDATE,
    ScopedReadOnlyObservationBoundaryContractError,
    build_observation_candidate_surface_records_v1,
    build_observation_domain_records_v1,
    build_scoped_read_only_observation_boundary_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_V1.md"
AX_HEADING = "11.2.1.AX FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST"
AY_HEADING = "11.2.1.AY FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY"
AZ_HEADING = "11.2.1.AZ FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES"
_NEW_CONTRACT_FILE = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "scoped_read_only_observation_boundary_contract_v1.py"
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)
_REQUIRED_DOMAIN_FIELDS = (
    "observation_id",
    "question_answered",
    "required_fields",
    "required_account_binding",
    "required_time_range",
    "required_provenance",
    "required_freshness",
    "required_ordering",
    "required_idempotency_or_replay_identity",
    "success_criterion",
    "fail_closed_criterion",
    "what_it_can_prove",
    "what_it_cannot_prove",
    "which_unknown_it_can_resolve",
    "include_decision_preconditions",
    "exclude_decision_preconditions",
)


def _ax_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ax_start = runbook.index(AX_HEADING)
    return runbook[ax_start : runbook.index(AY_HEADING, ax_start)]


def _ay_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ay_start = runbook.index(AY_HEADING)
    return runbook[ay_start : runbook.index(AZ_HEADING, ay_start)]


def test_four_observation_domains_are_defined_and_kinds_remain_unknown() -> None:
    persist = build_scoped_read_only_observation_boundary_contract_v1(
        persist_id="OBSERVATION_BOUNDARY_A"
    )
    domains = {record.observation_id: record for record in build_observation_domain_records_v1()}
    assert tuple(domains) == (
        OBS_ACCOUNT_COMPOSITION,
        OBS_LIABILITY,
        OBS_FEE_EMBEDDING,
        OBS_EXOGENOUS_COVERAGE,
    )
    for record in domains.values():
        for field_name in _REQUIRED_DOMAIN_FIELDS:
            value = getattr(record, field_name)
            assert isinstance(value, str) and value.strip() == value and value != ""
    assert domains[OBS_LIABILITY].which_unknown_it_can_resolve == CANDIDATE_U05
    assert domains[OBS_FEE_EMBEDDING].which_unknown_it_can_resolve == CANDIDATE_U06
    assert domains[OBS_EXOGENOUS_COVERAGE].which_unknown_it_can_resolve == (CANDIDATE_RESIDUAL)
    assert "not source authority" in domains[OBS_ACCOUNT_COMPOSITION].what_it_cannot_prove
    assert "rehabilitate C01" in domains[OBS_ACCOUNT_COMPOSITION].what_it_cannot_prove
    assert "empty rows without coverage cannot EXCLUDE" in (
        domains[OBS_LIABILITY].exclude_decision_preconditions
    )
    assert "NON_VENUE_EVIDENCE" in domains[OBS_FEE_EMBEDDING].what_it_cannot_prove
    assert "global zero" in domains[OBS_EXOGENOUS_COVERAGE].what_it_cannot_prove
    assert RATIFIED_CLASSIFIED_KIND_SET == ()
    assert RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is False
    assert persist.u05_kind_decision == DECISION_REMAIN_UNKNOWN
    assert persist.u06_kind_decision == DECISION_REMAIN_UNKNOWN
    assert persist.residual_kind_decision == DECISION_REMAIN_UNKNOWN
    assert persist.ratified_classified_event_kind_set == "EMPTY_FAIL_CLOSED"
    assert persist.kind_set_resolved == "false"
    assert persist.ms1_kind_set_fully_closed == "false"
    assert persist.ms2_authorized == "false"
    assert persist.d6_fully_closed == "false"
    assert persist.d7_authorized == "false"
    assert persist.observation_executed == "false"
    assert persist.observation_execution_authorized == "false"
    assert persist.path_b == PATH_B_SELECTED_BUT_BLOCKED
    assert persist.path_a == "REJECT"
    assert persist.path_c == "REJECT"


def test_observation_boundary_does_not_select_surfaces_or_authorize_get() -> None:
    persist = build_scoped_read_only_observation_boundary_contract_v1(
        persist_id="OBSERVATION_BOUNDARY_PINS"
    )
    surfaces = {
        record.surface_id: record for record in build_observation_candidate_surface_records_v1()
    }
    dag = live_admission_gap_dag_v1()
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    assert OBSERVATION_BOUNDARY_CONTRACT_CREATED is True
    assert OBSERVATION_BOUNDARY_CONTRACT_STATUS == BOUNDARY_STATUS_DEFINED_NOT_EXECUTED
    assert OBSERVATION_EXECUTED is False
    assert OBSERVATION_EXECUTION_AUTHORIZED is False
    assert OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is False
    assert ACCOUNT_COMPOSITION_OBSERVATION_DEFINED is True
    assert LIABILITY_OBSERVATION_DEFINED is True
    assert FEE_EMBEDDING_OBSERVATION_DEFINED is True
    assert EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED is True
    assert OBSERVATION_IS_NOT_SOURCE_AUTHORITY is True
    assert OBSERVATION_IS_NOT_KIND_RATIFICATION is True
    assert OBSERVATION_IS_NOT_MS2_RELEASE is True
    assert OBSERVATION_IS_NOT_D7_AUTHORIZATION is True
    assert OBSERVATION_IS_NOT_RAW_EQ_SOURCE_AUTHORITY is True
    assert OBSERVATION_IS_NOT_COMPLETENESS_UNLESS_RANGE_ORDERING_PROVENANCE_PROVEN is True
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert KIND_SET_RESOLVED is False
    assert MS1_KIND_SET_FULLY_CLOSED is False
    assert MS2_AUTHORIZED is False
    assert D6_FULLY_CLOSED is False
    assert D7_AUTHORIZED is False
    assert PATH_A_ARCHIVE_OR_REPO_SEARCH == "REJECT"
    assert PATH_B_SCOPED_READ_ONLY_OBSERVATION == PATH_B_SELECTED_BUT_BLOCKED
    assert PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT == "REJECT"
    assert ACCOUNT_BILLS_ATLAS_AUTHORITY == ATLAS_AUTHORITY_NONE
    assert persist.candidate_surface_selection == SELECTION_NONE
    assert persist.account_bills_atlas_authority == ATLAS_AUTHORITY_NONE
    bills = surfaces[CANDIDATE_SURFACE_ACCOUNT_BILLS]
    assert bills.classification == SURFACE_CLASS_CANDIDATE
    assert bills.current_status == "CURRENT_NONCANONICAL"
    assert bills.atlas_authority == ATLAS_AUTHORITY_NONE
    assert bills.selected == "false"
    assert all(record.selected == "false" for record in surfaces.values())
    assert AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is False
    assert EVENT_KIND_SOURCE_SEAM_SELECTED is False
    assert SOURCE_SELECTED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert COMPLETE_EVENT_STREAM_PROVEN is False
    assert D6_COMPLETENESS_PRECONDITIONS_PROVEN is False
    assert C17_CREATED is False
    assert RECONSTRUCTION_ENGINE_CREATED is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert EARLIEST_D6_KIND_SET_DEPENDENCY == (
        "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert dag["OBSERVATION_EXECUTED"] is False
    assert dag["OBSERVATION_NETWORK_GET_AUTHORIZED"] is False
    assert dag["D6_FULLY_CLOSED"] is False
    assert dag["D7_AUTHORIZED"] is False
    assert dag["U05_KIND_DECISION"] == DECISION_REMAIN_UNKNOWN
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    with pytest.raises(ScopedReadOnlyObservationBoundaryContractError):
        build_scoped_read_only_observation_boundary_contract_v1(persist_id=" ")
    text = (REPO_ROOT / _NEW_CONTRACT_FILE).read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in _FORBIDDEN_ENGINE_MARKERS:
        assert marker not in lowered
    assert "def reconstruct_equity_stock" not in text
    assert persist.authority_effect == "NONE"


def test_runbook_ay_consumes_owner_go_without_rewriting_ax_or_executing_observation() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ax_section = _ax_section()
    ay_section = _ay_section()
    assert "THIS_SLICE=11.2.1.AX" in ax_section
    assert "THIS_SLICE=11.2.1.AY" not in ax_section
    assert "THIS_SLICE=11.2.1.AZ" not in ay_section
    assert "OWNER_GO=OWNER_GO_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_CONTRACT_V1" in ay_section
    assert "OWNER_GO_STATUS=CONSUMED" in ay_section
    assert "THIS_SLICE=11.2.1.AY.FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY" in ay_section
    assert "OBSERVATION_EXECUTED=false" in ay_section
    assert "OBSERVATION_EXECUTION_AUTHORIZED=false" in ay_section
    assert "NETWORK_GET_PERFORMED=false" in ay_section
    assert "NETWORK_POST_PERFORMED=false" in ay_section
    assert "ACCOUNT_COMPOSITION_OBSERVATION_DEFINED=true" in ay_section
    assert "LIABILITY_OBSERVATION_DEFINED=true" in ay_section
    assert "FEE_EMBEDDING_OBSERVATION_DEFINED=true" in ay_section
    assert "EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED=true" in ay_section
    assert "OBSERVATION_IS_NOT_SOURCE_AUTHORITY=true" in ay_section
    assert "OBSERVATION_IS_NOT_KIND_RATIFICATION=true" in ay_section
    assert "OBSERVATION_IS_NOT_MS2_RELEASE=true" in ay_section
    assert "OBSERVATION_IS_NOT_D7_AUTHORIZATION=true" in ay_section
    assert "OBSERVATION_IS_NOT_RAW_EQ_SOURCE_AUTHORITY=true" in ay_section
    assert (
        "OBSERVATION_IS_NOT_COMPLETENESS_UNLESS_RANGE_ORDERING_PROVENANCE_PROVEN=true" in ay_section
    )
    assert "U05_KIND_DECISION=REMAIN_UNKNOWN" in ay_section
    assert "U06_KIND_DECISION=REMAIN_UNKNOWN" in ay_section
    assert "RESIDUAL_KIND_DECISION=REMAIN_UNKNOWN" in ay_section
    assert "KIND_SET_RESOLVED=false" in ay_section
    assert "MS1_KIND_SET_FULLY_CLOSED=false" in ay_section
    assert "MS2_AUTHORIZED=false" in ay_section
    assert "D6_FULLY_CLOSED=false" in ay_section
    assert "D7_AUTHORIZED=false" in ay_section
    assert "PATH_A=REJECT" in ay_section
    assert "PATH_B=SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION" in ay_section
    assert "PATH_C=REJECT" in ay_section
    assert "CANDIDATE_SURFACE_SELECTION=NONE_SELECTED" in ay_section
    assert "ATLAS_AUTHORITY=NONE" in ay_section
    assert "C17_CREATED=false" in ay_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in ay_section
    assert "LIVE_ENABLED=false" in ay_section
    assert "MASTER_V2_UNCHANGED=true" in ay_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in ay_section
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in ay_section
    assert (
        "MAX_SAFE_REPO_INTERNAL_NEXT_SLICE="
        "D6_REMAINS_BLOCKED_ON_SEPARATELY_AUTHORIZED_SCOPED_READ_ONLY_OBSERVATION_EXECUTION"
        in ay_section
    )
    assert "KIND_SET_RESOLVED=false" in spec
    assert "MS2_AUTHORIZED=false" in spec
    assert "OBSERVATION_EXECUTED=false" in spec
    assert "DOCS_TOKEN_FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_V1.md" in mot
    assert "§11.2.1.AY FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY" in mot
