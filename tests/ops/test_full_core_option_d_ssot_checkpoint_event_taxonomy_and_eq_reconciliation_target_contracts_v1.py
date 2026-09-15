"""OPTION_D SSOT, checkpoint, event taxonomy, and eq-target contracts."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    C01_C16_REJECTION_STILL_BINDING,
    C17_CREATED,
    C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
    CHECKPOINT_CAN_MINT_EQUITY,
    CHECKPOINT_CONTRACT_SCHEMA_PRESENT,
    DIMENSION_AVAILABLE_FOR_SIZING,
    DIMENSION_EQUITY_STOCK,
    DIMENSION_MARGIN_REQUIREMENTS,
    DIMENSION_P01_RISK_CAPITAL_REDUCTION,
    DIMENSION_SPLIT_PERSISTED,
    EARLIEST_OPTION_D_DEPENDENCY,
    EQ_RECONCILIATION_TARGET_ONLY,
    EVENT_ACQUISITION_CREATED,
    EVENT_TAXONOMY_SCHEMA_PRESENT,
    GOVERNED_PRODUCER_CREATED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_BOUNDARY_CURRENTLY_OPEN,
    MAPPING_PROVEN,
    OPTION_D_SELECTED,
    OPTION_D_SSOT_PERSISTED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESTART_PROVEN,
    SOURCE_SELECTED,
    UNCLASSIFIED_EVENT_FAIL_CLOSED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractV1,
    build_bound_account_identity_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    BOUND_ACCOUNT_IDENTITY_PROVEN,
    C01_C16_NOT_ELEVATED,
    C01_C16_REVIVAL_ALLOWED,
    OPTION_A_REJECTED_AS_LONG_TERM_TARGET,
    OPTION_B_FORBIDDEN,
    OPTION_C_FAIL_CLOSED_FALLBACK_ONLY,
    OWNER,
    P01_PLACEMENT,
    U04_PLACEMENT,
    U05_PLACEMENT,
    U06_PLACEMENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    CLASSIFICATION_STATUS_CLASSIFIED,
    CLASSIFICATION_STATUS_UNCLASSIFIED,
    CLASSIFICATION_STATUS_UNKNOWN,
    EquityAffectingEventTaxonomyContractError,
    RATIFIED_CLASSIFIED_KIND_SET,
    build_equity_affecting_event_taxonomy_record_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    EquityStockCheckpointContractError,
    build_equity_stock_checkpoint_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.fresh_eq_reconciliation_target_contract_v1 import (
    FreshEqReconciliationTargetContractError,
    STATUS_MISMATCH,
    STATUS_UNKNOWN,
    TOLERANCE_POLICY_UNSPECIFIED,
    build_fresh_eq_reconciliation_target_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.option_d_ssot_architecture_contract_v1 import (
    FORBIDDEN_SOURCE_FIELDS,
    OptionDSSOTArchitectureContractError,
    assert_dimension_split_v1,
    build_option_d_ssot_architecture_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_OPTION_D_SSOT_CHECKPOINT_EVENT_TAXONOMY_AND_EQ_RECONCILIATION_TARGET_CONTRACTS_V1.md"
)
AQ_HEADING = "11.2.1.AQ FULL_CORE_EQUITY_RECOVERY_PR1_GOVERNANCE_REOPEN_AND_CANDIDATE_CENSUS"
AR_HEADING = (
    "11.2.1.AR FULL_CORE_OPTION_D_SSOT_CHECKPOINT_EVENT_TAXONOMY_"
    "AND_EQ_RECONCILIATION_TARGET_CONTRACTS"
)
AS_HEADING = "11.2.1.AS FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT"
_DIGEST = hashlib.sha256(b"option-d-ssot-synthetic").hexdigest()
_DIGEST_B = hashlib.sha256(b"option-d-ssot-synthetic-b").hexdigest()
_NEW_CONTRACT_FILES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "option_d_ssot_architecture_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_stock_checkpoint_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_affecting_event_taxonomy_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "fresh_eq_reconciliation_target_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "bound_account_identity_contract_v1.py",
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)


def _synthetic_identity() -> BoundAccountIdentityContractV1:
    return build_bound_account_identity_contract_v1(
        identity_id="SYNTHETIC_ACCOUNT_A",
        bound_account_identity="SYNTHETIC_ACCOUNT_A",
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )


def _identity_kwargs() -> dict[str, str]:
    identity = _synthetic_identity()
    return {
        "bound_account_identity_ref": identity.identity_id,
        "bound_account_identity_digest": identity.identity_digest,
    }


def _ar_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ar_start = runbook.index(AR_HEADING)
    return runbook[ar_start : runbook.index(AS_HEADING, ar_start)]


def test_option_d_and_dimension_split_pins() -> None:
    contract = build_option_d_ssot_architecture_contract_v1(
        architecture_contract_id="OPTION_D_SSOT_ARCHITECTURE_CONTRACT_V1"
    )
    assert OPTION_D_SELECTED is True
    assert OPTION_D_SSOT_PERSISTED is True
    assert OPTION_A_REJECTED_AS_LONG_TERM_TARGET is True
    assert OPTION_B_FORBIDDEN is True
    assert OPTION_C_FAIL_CLOSED_FALLBACK_ONLY is True
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_RECONCILIATION_TARGET_ONLY is True
    assert DIMENSION_SPLIT_PERSISTED is True
    assert contract.equity_stock_dimension_id == DIMENSION_EQUITY_STOCK
    assert contract.available_for_sizing_dimension_id == DIMENSION_AVAILABLE_FOR_SIZING
    assert contract.margin_requirements_dimension_id == DIMENSION_MARGIN_REQUIREMENTS
    assert contract.p01_dimension_id == DIMENSION_P01_RISK_CAPITAL_REDUCTION
    assert U04_PLACEMENT == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert U05_PLACEMENT == "EQUITY_STOCK_ONLY_IF_BORROW_LIAB_NOT_ALREADY_EMBEDDED"
    assert U06_PLACEMENT == "EVENT_OR_RECONCILIATION_NOT_BLIND_SUBTRACTION"
    assert P01_PLACEMENT == "AFTER_EQUITY_RISK_CAPITAL_REDUCTION_NOT_IN_SOURCE"
    assert_dimension_split_v1(
        equity_stock_dimension_id=DIMENSION_EQUITY_STOCK,
        available_for_sizing_dimension_id=DIMENSION_AVAILABLE_FOR_SIZING,
        margin_requirements_dimension_id=DIMENSION_MARGIN_REQUIREMENTS,
        p01_dimension_id=DIMENSION_P01_RISK_CAPITAL_REDUCTION,
    )
    with pytest.raises(OptionDSSOTArchitectureContractError):
        assert_dimension_split_v1(
            equity_stock_dimension_id=DIMENSION_EQUITY_STOCK,
            available_for_sizing_dimension_id=DIMENSION_EQUITY_STOCK,
            margin_requirements_dimension_id=DIMENSION_MARGIN_REQUIREMENTS,
            p01_dimension_id=DIMENSION_P01_RISK_CAPITAL_REDUCTION,
        )


def test_c01_c16_remain_fenced_and_c17_not_created() -> None:
    assert C01_C16_REJECTION_STILL_BINDING is True
    assert C01_C16_REVIVAL_ALLOWED is False
    assert C01_C16_NOT_ELEVATED is True
    assert C17_CREATED is False
    assert C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN is True
    assert len(C01_C16_IDS) == 16
    assert "eq" in FORBIDDEN_SOURCE_FIELDS
    assert "availEq" in FORBIDDEN_SOURCE_FIELDS


def test_existing_authority_owner_unchanged() -> None:
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    contract = build_option_d_ssot_architecture_contract_v1(
        architecture_contract_id="OPTION_D_OWNER_PIN"
    )
    assert contract.authority_owner == ACCOUNT_EQUITY_AUTHORITY_OWNER


def test_checkpoint_cannot_mint_equity() -> None:
    assert CHECKPOINT_CAN_MINT_EQUITY is False
    assert CHECKPOINT_CONTRACT_SCHEMA_PRESENT is True
    checkpoint = build_equity_stock_checkpoint_contract_v1(
        checkpoint_id="CKPT_SYNTHETIC_TEST_ONLY",
        schema_digest=_DIGEST,
        input_set_digest=_DIGEST_B,
        checkpoint_version="v1",
        **_identity_kwargs(),
    )
    assert checkpoint.equity_mint_status == "NOT_MINTED"
    assert checkpoint.running_equity_value_state == "ABSENT"
    assert checkpoint.claimed_equity_stock_value == "ABSENT"
    assert checkpoint.observation_vs_authority_class == "NON_AUTHORITATIVE_ANCHOR"
    with pytest.raises(EquityStockCheckpointContractError) as err:
        build_equity_stock_checkpoint_contract_v1(
            checkpoint_id="CKPT_SYNTHETIC_TEST_ONLY",
            schema_digest=_DIGEST,
            input_set_digest=_DIGEST_B,
            checkpoint_version="v1",
            claimed_equity_stock_value="100.00",
            **_identity_kwargs(),
        )
    assert "CHECKPOINT_CANNOT_MINT_EQUITY" in str(err.value)
    with pytest.raises(EquityStockCheckpointContractError):
        build_equity_stock_checkpoint_contract_v1(
            checkpoint_id="CKPT_SYNTHETIC_TEST_ONLY",
            schema_digest="not-a-digest",
            input_set_digest=_DIGEST_B,
            checkpoint_version="v1",
            **_identity_kwargs(),
        )


def test_unclassified_and_unknown_events_fail_closed() -> None:
    assert EVENT_TAXONOMY_SCHEMA_PRESENT is True
    assert UNCLASSIFIED_EVENT_FAIL_CLOSED is True
    assert RATIFIED_CLASSIFIED_KIND_SET == ()
    unknown = build_equity_affecting_event_taxonomy_record_v1(
        event_record_id="EVT_UNKNOWN_TEST_ONLY",
        classification_status=CLASSIFICATION_STATUS_UNKNOWN,
        event_semantic_class=CLASSIFICATION_STATUS_UNKNOWN,
        ordering_key="1",
        event_digest=_DIGEST,
        mapped_numeric_effect="FORBIDDEN_NOT_ZERO",
        **_identity_kwargs(),
    )
    assert unknown.reconstruction_eligibility == "INVALID_FAIL_CLOSED"
    assert unknown.execution_eligibility == "INVALID_FAIL_CLOSED"
    unclassified = build_equity_affecting_event_taxonomy_record_v1(
        event_record_id="EVT_UNCLASSIFIED_TEST_ONLY",
        classification_status=CLASSIFICATION_STATUS_UNCLASSIFIED,
        event_semantic_class=CLASSIFICATION_STATUS_UNCLASSIFIED,
        ordering_key="2",
        event_digest=_DIGEST_B,
        mapped_numeric_effect="FORBIDDEN_NOT_ZERO",
        **_identity_kwargs(),
    )
    assert unclassified.reconstruction_eligibility == "INVALID_FAIL_CLOSED"
    with pytest.raises(EquityAffectingEventTaxonomyContractError) as zero_err:
        build_equity_affecting_event_taxonomy_record_v1(
            event_record_id="EVT_UNKNOWN_ZERO",
            classification_status=CLASSIFICATION_STATUS_UNKNOWN,
            event_semantic_class=CLASSIFICATION_STATUS_UNKNOWN,
            ordering_key="3",
            event_digest=_DIGEST,
            mapped_numeric_effect="0",
            **_identity_kwargs(),
        )
    assert "UNCLASSIFIED_EVENT_CANNOT_MAP_TO_ZERO_OR_NOOP" in str(zero_err.value)
    with pytest.raises(EquityAffectingEventTaxonomyContractError) as ignore_err:
        build_equity_affecting_event_taxonomy_record_v1(
            event_record_id="EVT_UNCLASSIFIED_IGNORE",
            classification_status=CLASSIFICATION_STATUS_UNCLASSIFIED,
            event_semantic_class=CLASSIFICATION_STATUS_UNCLASSIFIED,
            ordering_key="4",
            event_digest=_DIGEST,
            mapped_numeric_effect="ignore",
            **_identity_kwargs(),
        )
    assert "UNCLASSIFIED_EVENT_CANNOT_MAP_TO_ZERO_OR_NOOP" in str(ignore_err.value)
    with pytest.raises(EquityAffectingEventTaxonomyContractError) as classified_err:
        build_equity_affecting_event_taxonomy_record_v1(
            event_record_id="EVT_CLASSIFIED_UNRATIFIED",
            classification_status=CLASSIFICATION_STATUS_CLASSIFIED,
            event_semantic_class="FILL",
            ordering_key="5",
            event_digest=_DIGEST,
            mapped_numeric_effect="FORBIDDEN_NOT_ZERO",
            **_identity_kwargs(),
        )
    assert "CLASSIFIED_KIND_NOT_RATIFIED" in str(classified_err.value)


def test_fresh_eq_is_target_only_and_mismatch_cannot_mint_sample() -> None:
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_RECONCILIATION_TARGET_ONLY is True
    match = build_fresh_eq_reconciliation_target_contract_v1(
        reconciliation_record_id="EQ_RECON_MATCH",
        reconstructed_equity_fact_id="RECON_FACT_A",
        reconstructed_equity_provenance_digest=_DIGEST,
        reconstructed_equity_value_state="PRESENT",
        reconstructed_equity_value="12.50",
        venue_eq_fact_id="VENUE_EQ_FACT_A",
        venue_eq_provenance_digest=_DIGEST_B,
        venue_eq_value_state="PRESENT",
        venue_eq_value="12.50",
        **_identity_kwargs(),
    )
    assert match.reconciliation_status == "MATCH"
    assert match.governed_sample_valid == "false"
    assert match.eq_promoted_to_source == "false"
    assert match.reconstructed_stock_overwritten == "false"
    assert match.reconstructed_fact_retained == "true"
    assert match.venue_eq_fact_retained == "true"
    mismatch = build_fresh_eq_reconciliation_target_contract_v1(
        reconciliation_record_id="EQ_RECON_MISMATCH",
        reconstructed_equity_fact_id="RECON_FACT_B",
        reconstructed_equity_provenance_digest=_DIGEST,
        reconstructed_equity_value_state="PRESENT",
        reconstructed_equity_value="12.50",
        venue_eq_fact_id="VENUE_EQ_FACT_B",
        venue_eq_provenance_digest=_DIGEST_B,
        venue_eq_value_state="PRESENT",
        venue_eq_value="9.00",
        **_identity_kwargs(),
    )
    assert mismatch.reconciliation_status == STATUS_MISMATCH
    assert mismatch.governed_sample_valid == "false"
    assert mismatch.reconstructed_equity_value == "12.50"
    assert mismatch.venue_eq_value == "9.00"
    unknown = build_fresh_eq_reconciliation_target_contract_v1(
        reconciliation_record_id="EQ_RECON_UNKNOWN",
        reconstructed_equity_fact_id="RECON_FACT_C",
        reconstructed_equity_provenance_digest=_DIGEST,
        reconstructed_equity_value_state="UNKNOWN",
        reconstructed_equity_value="UNKNOWN",
        venue_eq_fact_id="VENUE_EQ_FACT_C",
        venue_eq_provenance_digest=_DIGEST_B,
        venue_eq_value_state="PRESENT",
        venue_eq_value="12.50",
        **_identity_kwargs(),
    )
    assert unknown.reconciliation_status == STATUS_UNKNOWN
    assert unknown.governed_sample_valid == "false"
    with pytest.raises(FreshEqReconciliationTargetContractError):
        build_fresh_eq_reconciliation_target_contract_v1(
            reconciliation_record_id="EQ_RECON_TOLERANCE",
            reconstructed_equity_fact_id="RECON_FACT_D",
            reconstructed_equity_provenance_digest=_DIGEST,
            reconstructed_equity_value_state="PRESENT",
            reconstructed_equity_value="12.50",
            venue_eq_fact_id="VENUE_EQ_FACT_D",
            venue_eq_provenance_digest=_DIGEST_B,
            venue_eq_value_state="PRESENT",
            venue_eq_value="12.50",
            tolerance_policy=TOLERANCE_POLICY_UNSPECIFIED,
            **_identity_kwargs(),
        )
    with pytest.raises(FreshEqReconciliationTargetContractError):
        build_fresh_eq_reconciliation_target_contract_v1(
            reconciliation_record_id="EQ_RECON_SHARED_ID",
            reconstructed_equity_fact_id="SAME_FACT",
            reconstructed_equity_provenance_digest=_DIGEST,
            reconstructed_equity_value_state="PRESENT",
            reconstructed_equity_value="12.50",
            venue_eq_fact_id="SAME_FACT",
            venue_eq_provenance_digest=_DIGEST_B,
            venue_eq_value_state="PRESENT",
            venue_eq_value="12.50",
            **_identity_kwargs(),
        )


def test_no_event_acquisition_reconstruction_engine_restart_or_live() -> None:
    dag = live_admission_gap_dag_v1()
    assert EVENT_ACQUISITION_CREATED is True
    assert RECONSTRUCTION_ENGINE_CREATED is False
    assert RESTART_PROVEN is False
    assert BOUND_ACCOUNT_IDENTITY_PROVEN is True
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert MAPPING_BOUNDARY_CURRENTLY_OPEN is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert dag["EVENT_ACQUISITION_CREATED"] is True
    assert dag["RECONSTRUCTION_ENGINE_CREATED"] is False
    assert dag["RESTART_PROVEN"] is False
    assert dag["RAW_EQ_SOURCE_AUTHORITY"] is False
    assert dag["EQ_RECONCILIATION_TARGET_ONLY"] is True
    assert dag["C17_CREATED"] is False
    assert dag["BOUND_ACCOUNT_IDENTITY_PROVEN"] is True
    assert dag["EARLIEST_OPTION_D_DEPENDENCY"] == (
        "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    )
    assert EARLIEST_OPTION_D_DEPENDENCY == "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    for relative in _NEW_CONTRACT_FILES:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in _FORBIDDEN_ENGINE_MARKERS:
            assert marker not in lowered
        assert "def reconstruct_equity_stock" not in text
        assert "def acquire_events" not in text


def test_runbook_ar_consumes_owner_go_without_rewriting_aq_or_protected_surfaces() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ar_section = _ar_section()
    aq_start = runbook.index(AQ_HEADING)
    aq_section = runbook[aq_start : runbook.index(AR_HEADING, aq_start)]
    assert "THIS_SLICE=11.2.1.AQ" in aq_section
    assert "THIS_SLICE=11.2.1.AR" not in aq_section
    assert "OWNER_GO=OWNER_GO_OPTION_D_FIRST_IMPLEMENTATION_WORKPACKAGE_V1" in ar_section
    assert "OWNER_GO_STATUS=CONSUMED" in ar_section
    assert "SELECTED_OPTION=OPTION_D" in ar_section
    assert "OPTION_D_SSOT_PERSISTED=true" in ar_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in ar_section
    assert "EQ_RECONCILIATION_TARGET_ONLY=true" in ar_section
    assert "CHECKPOINT_CAN_MINT_EQUITY=false" in ar_section
    assert "UNCLASSIFIED_EVENT_FAIL_CLOSED=true" in ar_section
    assert "DIMENSION_SPLIT_PERSISTED=true" in ar_section
    assert "C01_C16_REJECTION_STILL_BINDING=true" in ar_section
    assert "C17_CREATED=false" in ar_section
    assert "MAPPING_PROVEN=false" in ar_section
    assert "EVENT_ACQUISITION_CREATED=false" in ar_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in ar_section
    assert "RESTART_PROVEN=false" in ar_section
    assert "EXISTING_AUTHORITY_OWNER_UNCHANGED=true" in ar_section
    assert (
        "ACCOUNT_EQUITY_AUTHORITY_OWNER="
        "ops.governed_productive_account_equity_authority_producer_v1" in ar_section
    )
    assert "LIVE_ENABLED=false" in ar_section
    assert "LIVE_ARMED=false" in ar_section
    assert "WIRE_SEND_PERMITTED=false" in ar_section
    assert "MASTER_V2_UNCHANGED=true" in ar_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in ar_section
    assert "BULL_BEAR_STATE_SWITCH_UNCHANGED=true" in ar_section
    assert "TOP20_RANKING_UNIVERSE_UNCHANGED=true" in ar_section
    assert "SELF_LEARNING_UNCHANGED=true" in ar_section
    assert "FULL_CORE_AUTONOMY_UNCHANGED=true" in ar_section
    assert "PROTECTED_SURFACES_UNCHANGED=true" in ar_section
    assert "CORE_LOGIC_CHANGE=false" in ar_section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in ar_section
    assert "EARLIEST_OPTION_D_DEPENDENCY=D4_BOUND_ACCOUNT_IDENTITY" in ar_section
    assert (
        "DOCS_TOKEN_FULL_CORE_OPTION_D_SSOT_CHECKPOINT_EVENT_TAXONOMY_AND_EQ_RECONCILIATION_TARGET_CONTRACTS_V1"
        in spec
    )
    assert "THIS_SLICE=11.2.1.AQ" in aq_section
    assert "C17_CREATED=false" in aq_section
