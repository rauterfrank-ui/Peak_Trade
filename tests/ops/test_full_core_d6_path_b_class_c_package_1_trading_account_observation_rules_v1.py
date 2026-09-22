"""D6 PATH_B CLASS_C PACKAGE_1 trading-account observation rules persist."""

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
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    PROVENANCE_EXPLICIT_TYPED_BINDING,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_ATLAS_AUTHORITY,
    BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01,
    BALANCE_RULE_PERSISTED,
    C01_REHABILITATION_FORBIDDEN,
    CANDIDATE_SURFACE_SELECTION,
    D4_RULE_PERSISTED,
    EMBEDDING_OPTION,
    EMBEDDING_RULE_PERSISTED,
    EMPTY_COVERAGE_RULE_PERSISTED,
    EMPTY_ROWS_PROVE_KIND_ABSENCE,
    EMPTY_ROWS_PROVE_ZERO_EVENTS,
    EQ_ROLE,
    EXECUTION_READY,
    OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT,
    OWNER,
    PACKAGE_1_AUTHORITY_EFFECT,
    PACKAGE_1_PERSISTED,
    PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
    PATH_A_ARCHIVE_OR_REPO_SEARCH,
    PATH_B_CLASS_C_PACKAGE_1_SELECTED,
    PATH_B_PREAUTHORIZATION_READY,
    PATH_B_SCOPED_READ_ONLY_OBSERVATION,
    PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT,
    SELECTED_OBSERVATION_SURFACES,
    UNKNOWN_EMBEDDING_FACTS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    ATLAS_AUTHORITY_NONE,
    EMBEDDING_FACTS_REMAIN_UNKNOWN,
    EMBEDDING_OPTION_A,
    FORBIDDEN_BALANCE_AUTHORITY_USES,
    SURFACE_ACCOUNT_BALANCE,
    SURFACE_ACCOUNT_BILLS,
    SURFACE_ACCOUNT_BILLS_ARCHIVE,
    SURFACE_ACCOUNT_CONFIG,
    SURFACE_ACCOUNT_SUBTYPES,
    PathBClassCPackage1TradingAccountObservationRulesContractError,
    assert_balance_observation_cannot_become_authority_v1,
    assert_empty_rows_are_not_zero_or_kind_absence_v1,
    build_path_b_class_c_package_1_trading_account_observation_rules_v1,
    build_selected_observation_surface_records_v1,
    build_unknown_embedding_fact_records_v1,
    corroborate_d4_identity_from_account_config_observation_v1,
    reject_include_exclude_from_unknown_embedding_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_V1.md"
)
AY_HEADING = "11.2.1.AY FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY"
AZ_HEADING = "11.2.1.AZ FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES"
BA_HEADING = "11.2.1.BA FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT"
_NEW_CONTRACT_FILE = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "path_b_class_c_package_1_trading_account_observation_rules_contract_v1.py"
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)
_FORBIDDEN_AUTHORITY_FLAGS = (
    "ATLAS_AUTHORITY_UPLIFTED",
    "KIND_SET_RESOLVED",
    "MS2_AUTHORIZED",
    "C01_REHABILITATED",
    "D7_AUTHORIZED",
    "LIVE_AUTHORIZED",
    "CANARY_AUTHORIZED",
)


def _ay_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ay_start = runbook.index(AY_HEADING)
    return runbook[ay_start : runbook.index(AZ_HEADING, ay_start)]


def _az_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    az_start = runbook.index(AZ_HEADING)
    return runbook[az_start : runbook.index(BA_HEADING, az_start)]


def test_package_1_persists_selected_surfaces_and_semantic_laws() -> None:
    persist = build_path_b_class_c_package_1_trading_account_observation_rules_v1(
        persist_id="PACKAGE_1_RULES_A"
    )
    surfaces = {
        record.surface_id: record for record in build_selected_observation_surface_records_v1()
    }
    facts = {record.fact_id: record for record in build_unknown_embedding_fact_records_v1()}
    assert SELECTED_OBSERVATION_SURFACES == (
        SURFACE_ACCOUNT_CONFIG,
        SURFACE_ACCOUNT_BALANCE,
        SURFACE_ACCOUNT_BILLS,
        SURFACE_ACCOUNT_BILLS_ARCHIVE,
        SURFACE_ACCOUNT_SUBTYPES,
    )
    assert persist.selected_observation_surfaces == ",".join(SELECTED_OBSERVATION_SURFACES)
    assert persist.d4_rule_persisted == "true"
    assert persist.balance_rule_persisted == "true"
    assert persist.empty_coverage_rule_persisted == "true"
    assert persist.embedding_rule_persisted == "true"
    assert persist.path_b_preauthorization_ready == "true"
    assert persist.execution_ready == "false"
    assert persist.observation_executed == "false"
    assert persist.authority_effect == "NONE"
    assert persist.candidate_surface_selection == "NONE_SELECTED"
    assert persist.account_bills_atlas_authority == ATLAS_AUTHORITY_NONE
    assert persist.eq_role == "RECONCILIATION_OR_EMBEDDING_TARGET_ONLY"
    assert persist.embedding_option == EMBEDDING_OPTION_A
    assert tuple(surfaces) == SELECTED_OBSERVATION_SURFACES
    assert all(record.selected == "true" for record in surfaces.values())
    assert all(record.atlas_authority == ATLAS_AUTHORITY_NONE for record in surfaces.values())
    assert all(record.authority_effect == "NONE" for record in surfaces.values())
    assert all(record.observation_executed == "false" for record in surfaces.values())
    assert tuple(facts) == EMBEDDING_FACTS_REMAIN_UNKNOWN
    assert all(record.status == "UNKNOWN" for record in facts.values())
    assert all(record.include_from_unknown == "false" for record in facts.values())
    assert all(record.exclude_from_unknown == "false" for record in facts.values())
    assert all(record.algebraic_inference_allowed == "false" for record in facts.values())


def test_package_1_forbidden_authority_effects_remain_false() -> None:
    persist = build_path_b_class_c_package_1_trading_account_observation_rules_v1(
        persist_id="PACKAGE_1_PINS"
    )
    dag = live_admission_gap_dag_v1()
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    assert PACKAGE_1_PERSISTED is True
    assert PATH_B_CLASS_C_PACKAGE_1_SELECTED is True
    assert PATH_B_PREAUTHORIZATION_READY is True
    assert EXECUTION_READY is False
    assert PACKAGE_1_AUTHORITY_EFFECT == "NONE"
    assert D4_RULE_PERSISTED is True
    assert BALANCE_RULE_PERSISTED is True
    assert EMPTY_COVERAGE_RULE_PERSISTED is True
    assert EMBEDDING_RULE_PERSISTED is True
    assert OBSERVATION_EXECUTED is False
    assert OBSERVATION_EXECUTION_AUTHORIZED is False
    assert OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert CANDIDATE_SURFACE_SELECTION == "NONE_SELECTED"
    assert ACCOUNT_BILLS_ATLAS_AUTHORITY == ATLAS_AUTHORITY_NONE
    assert PATH_A_ARCHIVE_OR_REPO_SEARCH == "REJECT"
    assert PATH_B_SCOPED_READ_ONLY_OBSERVATION == "SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION"
    assert PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT == "REJECT"
    assert C01_REHABILITATION_FORBIDDEN is True
    assert BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01 is True
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_ROLE == "RECONCILIATION_OR_EMBEDDING_TARGET_ONLY"
    assert OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT == "NONE"
    assert EMPTY_ROWS_PROVE_ZERO_EVENTS is False
    assert EMPTY_ROWS_PROVE_KIND_ABSENCE is False
    assert PAGINATION_EXHAUSTION_PROVES_COMPLETENESS is False
    assert EMBEDDING_OPTION == EMBEDDING_OPTION_A
    assert UNKNOWN_EMBEDDING_FACTS == EMBEDDING_FACTS_REMAIN_UNKNOWN
    assert KIND_SET_RESOLVED is False
    assert MS1_KIND_SET_FULLY_CLOSED is False
    assert MS2_AUTHORIZED is False
    assert D6_FULLY_CLOSED is False
    assert D7_AUTHORIZED is False
    assert AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is False
    assert EVENT_KIND_SOURCE_SEAM_SELECTED is False
    assert SOURCE_SELECTED is False
    assert COMPLETE_EVENT_STREAM_PROVEN is False
    assert D6_COMPLETENESS_PRECONDITIONS_PROVEN is False
    assert C17_CREATED is False
    assert RECONSTRUCTION_ENGINE_CREATED is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert persist.kind_set_resolved == "false"
    assert persist.ms2_authorized == "false"
    assert persist.d6_fully_closed == "false"
    assert persist.d7_authorized == "false"
    assert persist.c01_rehabilitation_forbidden == "true"
    assert persist.raw_eq_source_authority == "false"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert dag["PACKAGE_1_PERSISTED"] is True
    assert dag["PATH_B_PREAUTHORIZATION_READY"] is True
    assert dag["EXECUTION_READY"] is False
    assert dag["OBSERVATION_EXECUTED"] is False
    assert dag["MS2_AUTHORIZED"] is False
    assert dag["D7_AUTHORIZED"] is False
    assert dag["KIND_SET_RESOLVED"] is False
    assert dag["CANDIDATE_SURFACE_SELECTION"] == "NONE_SELECTED"
    assert dag["ACCOUNT_BILLS_ATLAS_AUTHORITY"] == ATLAS_AUTHORITY_NONE
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    with pytest.raises(PathBClassCPackage1TradingAccountObservationRulesContractError):
        build_path_b_class_c_package_1_trading_account_observation_rules_v1(persist_id=" ")
    text = (REPO_ROOT / _NEW_CONTRACT_FILE).read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in _FORBIDDEN_ENGINE_MARKERS:
        assert marker not in lowered
    assert "def reconstruct_equity_stock" not in text
    for flag in _FORBIDDEN_AUTHORITY_FLAGS:
        assert f"{flag}=true" not in text


def test_package_1_fail_closed_laws_reject_forbidden_authority_uses() -> None:
    corroborated = corroborate_d4_identity_from_account_config_observation_v1(
        bound_account_identity="acct-bound-1",
        bound_settlement_currency="USDC",
        observed_uid="acct-bound-1",
        observed_main_uid="main-bound-1",
        observed_settle_ccy="USDC",
        observed_account_mode="cash",
        identity_provenance_class=PROVENANCE_EXPLICIT_TYPED_BINDING,
    )
    assert corroborated == "D4_RUNTIME_EVIDENCE_CORROBORATED_IDENTITY_NOT_MINTED"
    with pytest.raises(PathBClassCPackage1TradingAccountObservationRulesContractError) as minted:
        corroborate_d4_identity_from_account_config_observation_v1(
            bound_account_identity="acct-bound-1",
            bound_settlement_currency="USDC",
            observed_uid="acct-bound-1",
            observed_main_uid="main-bound-1",
            observed_settle_ccy="USDC",
            observed_account_mode="cash",
            identity_provenance_class="CREDENTIAL",
        )
    assert "D4_OBSERVATION_PROVENANCE_FORBIDDEN" in str(minted.value)
    with pytest.raises(PathBClassCPackage1TradingAccountObservationRulesContractError) as mismatch:
        corroborate_d4_identity_from_account_config_observation_v1(
            bound_account_identity="acct-bound-1",
            bound_settlement_currency="USDC",
            observed_uid="other-uid",
            observed_main_uid="main-bound-1",
            observed_settle_ccy="USDC",
            observed_account_mode="cash",
            identity_provenance_class=PROVENANCE_EXPLICIT_TYPED_BINDING,
        )
    assert "D4_OBSERVATION_MISMATCH_FAIL_CLOSED" in str(mismatch.value)
    for claimed_use in FORBIDDEN_BALANCE_AUTHORITY_USES:
        with pytest.raises(PathBClassCPackage1TradingAccountObservationRulesContractError) as bal:
            assert_balance_observation_cannot_become_authority_v1(claimed_use=claimed_use)
        assert "BALANCE_OBSERVATION_FORBIDDEN_AUTHORITY_USE" in str(bal.value)
    for claimed_proof in ("ZERO_EVENTS", "KIND_ABSENCE", "COMPLETENESS"):
        with pytest.raises(PathBClassCPackage1TradingAccountObservationRulesContractError) as empty:
            assert_empty_rows_are_not_zero_or_kind_absence_v1(claimed_proof=claimed_proof)
        assert "EMPTY_COVERAGE_FORBIDDEN_PROOF" in str(empty.value)
    assert_empty_rows_are_not_zero_or_kind_absence_v1(
        claimed_proof="NO_ROWS_OBSERVED_WITHIN_EXECUTED_QUERY"
    )
    for fact_id in EMBEDDING_FACTS_REMAIN_UNKNOWN:
        reject_include_exclude_from_unknown_embedding_v1(
            decision=DECISION_REMAIN_UNKNOWN, fact_id=fact_id
        )
        for decision in ("INCLUDE", "EXCLUDE"):
            with pytest.raises(
                PathBClassCPackage1TradingAccountObservationRulesContractError
            ) as embed:
                reject_include_exclude_from_unknown_embedding_v1(decision=decision, fact_id=fact_id)
            assert f"EMBEDDING_UNKNOWN_CANNOT_{decision}" in str(embed.value)


def test_runbook_az_consumes_owner_selection_without_rewriting_ay_or_executing() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ay_section = _ay_section()
    az_section = _az_section()
    assert "THIS_SLICE=11.2.1.AY" in ay_section
    assert "THIS_SLICE=11.2.1.AZ" not in ay_section
    assert (
        "OWNER_SELECTION=OWNER_SELECT_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_V1"
        in az_section
    )
    assert "OWNER_SELECTION_STATUS=CONSUMED" in az_section
    assert (
        "THIS_SLICE=11.2.1.AZ.FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES"
        in (az_section)
    )
    assert "THIS_SLICE=11.2.1.BA" not in az_section
    assert "PACKAGE_1_PERSISTED=true" in az_section
    assert "PATH_B_PREAUTHORIZATION_READY=true" in az_section
    assert "EXECUTION_READY=false" in az_section
    assert "OBSERVATION_EXECUTED=false" in az_section
    assert "OBSERVATION_EXECUTION_AUTHORIZED=false" in az_section
    assert "NETWORK_GET_PERFORMED=false" in az_section
    assert "NETWORK_POST_PERFORMED=false" in az_section
    assert "D4_RULE_PERSISTED=true" in az_section
    assert "BALANCE_RULE_PERSISTED=true" in az_section
    assert "EMPTY_COVERAGE_RULE_PERSISTED=true" in az_section
    assert "EMBEDDING_RULE_PERSISTED=true" in az_section
    assert "BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01=true" in az_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in az_section
    assert "EQ_ROLE=RECONCILIATION_OR_EMBEDDING_TARGET_ONLY" in az_section
    assert "EMPTY_ROWS_PROVE_ZERO_EVENTS=false" in az_section
    assert "EMPTY_ROWS_PROVE_KIND_ABSENCE=false" in az_section
    assert "PAGINATION_EXHAUSTION_PROVES_COMPLETENESS=false" in az_section
    assert "EMBEDDING_OPTION=E_OPTION_A_FAIL_CLOSED_UNKNOWN_ALLOWED" in az_section
    assert "KIND_SET_RESOLVED=false" in az_section
    assert "MS2_AUTHORIZED=false" in az_section
    assert "D6_FULLY_CLOSED=false" in az_section
    assert "D7_AUTHORIZED=false" in az_section
    assert "C01_REHABILITATION_FORBIDDEN=true" in az_section
    assert "CANDIDATE_SURFACE_SELECTION=NONE_SELECTED" in az_section
    assert "ATLAS_AUTHORITY=NONE" in az_section
    assert "PATH_B=SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION" in az_section
    assert "C17_CREATED=false" in az_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in az_section
    assert "LIVE_ENABLED=false" in az_section
    assert "MASTER_V2_UNCHANGED=true" in az_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in az_section
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in az_section
    assert (
        "MAX_SAFE_REPO_INTERNAL_NEXT_SLICE="
        "PATH_B_CLASS_C_PACKAGE_1_PERSISTED_OBSERVATION_EXECUTION_STILL_REQUIRES_OWNER_GO"
        in az_section
    )
    assert "GET_/api/v5/account/config" in az_section
    assert "GET_/api/v5/account/balance" in az_section
    assert "GET_/api/v5/account/bills" in az_section
    assert "GET_/api/v5/account/bills-archive" in az_section
    assert "GET_/api/v5/account/subtypes" in az_section
    assert "F12_LIABILITY_AFFECTS_EQUITY_STOCK" in az_section
    assert "F18_FEE_RECONCILIATION_ONLY" in az_section
    assert "PATH_B=SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION" in ay_section
    assert "CANDIDATE_SURFACE_SELECTION=NONE_SELECTED" in ay_section
    assert "KIND_SET_RESOLVED=false" in spec
    assert "MS2_AUTHORIZED=false" in spec
    assert "OBSERVATION_EXECUTED=false" in spec
    assert "PATH_B_PREAUTHORIZATION_READY=true" in spec
    assert "EXECUTION_READY=false" in spec
    assert (
        "DOCS_TOKEN_FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_V1"
        in spec
    )
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_V1.md" in mot
    assert (
        "§11.2.1.AZ FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES" in mot
    )
