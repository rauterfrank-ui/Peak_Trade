"""D6 classified kind-set and event-source seam fail-closed census."""

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
    C01_C16_REJECTION_STILL_BINDING,
    C17_CREATED,
    C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
    CHECKPOINT_CAN_MINT_EQUITY,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    EARLIEST_D6_COMPLETENESS_DEPENDENCY,
    EARLIEST_OPTION_D_DEPENDENCY,
    EVENT_ACQUISITION_CREATED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    GAP_DETECTION_FAIL_CLOSED,
    GOVERNED_PRODUCER_CREATED,
    IDEMPOTENCY_REPLAY_IDENTITY_PROVEN,
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    ORDERING_PROVEN,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_COVERAGE_COMPLETE,
    SOURCE_SELECTED,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_C01_C16_FORBIDDEN,
    DISPOSITION_UNKNOWN,
    MISSING_KIND_SET_AND_SOURCE_SEAM,
    RATIFIED_CLASSIFIED_EVENT_KIND_SET_TOKEN,
    ClassifiedEventKindSetAndSourceSeamContractError,
    adjudicate_event_source_range_order_and_duplicate_v1,
    bind_classified_event_kind_to_authorized_source_seam_v1,
    build_classified_event_kind_set_adjudication_v1,
    build_forensic_event_kind_census_findings_v1,
    build_forensic_event_source_seam_census_findings_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C01_C16_NOT_ELEVATED,
    C01_C16_REVIVAL_ALLOWED,
    EVENT_KIND_SOURCE_BINDING_IS_NOT_EQUITY_SOURCE_AUTHORITY,
    EVENT_KIND_SOURCE_BINDING_IS_NOT_MAPPING_PROVEN,
    EVENT_KIND_SOURCE_BINDING_IS_NOT_RAW_EQ_SOURCE_AUTHORITY,
    KIND_SET_CENSUS_CREATED,
    OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM_V1.md"
)
AU_HEADING = "11.2.1.AU FULL_CORE_D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
AV_HEADING = "11.2.1.AV FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM"
AW_HEADING = "11.2.1.AW FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT"
_DIGEST = "a" * 64
_DIGEST_B = "b" * 64
_NEW_CONTRACT_FILES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "classified_event_kind_set_and_source_seam_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "classified_event_stream_acquisition_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_affecting_event_taxonomy_contract_v1.py",
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)
_BINDING_KW = {
    "binding_id": "BIND_KIND_SEAM_A",
    "event_kind": "FILL",
    "source_seam_id": "GET_/api/v5/account/bills",
}


def _identity(*, identity_id: str, account: str) -> BoundAccountIdentityContractV1:
    return build_bound_account_identity_contract_v1(
        identity_id=identity_id,
        bound_account_identity=account,
        bound_venue_identity="SYNTHETIC_VENUE_OKX",
        bound_td_mode="cross",
        settlement_currency="USDC",
    )


def _identity_kwargs(identity: BoundAccountIdentityContractV1) -> dict[str, str]:
    return {
        "bound_account_identity_ref": identity.identity_id,
        "bound_account_identity_digest": identity.identity_digest,
        "expected_bound_account_identity_ref": identity.identity_id,
        "expected_bound_account_identity_digest": identity.identity_digest,
    }


def _av_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    av_start = runbook.index(AV_HEADING)
    return runbook[av_start : runbook.index(AW_HEADING, av_start)]


def test_exact_kind_membership_and_inclusion_exclusion_boundaries() -> None:
    adjudication = build_classified_event_kind_set_adjudication_v1(census_id="KIND_SET_CENSUS_A")
    findings = build_forensic_event_kind_census_findings_v1()
    candidate_ids = {finding.candidate_id for finding in findings}
    assert RATIFIED_CLASSIFIED_KIND_SET == ()
    assert RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is False
    assert KIND_SET_RESOLVED is False
    assert adjudication.ratified_classified_event_kind_set == (
        RATIFIED_CLASSIFIED_EVENT_KIND_SET_TOKEN
    )
    assert adjudication.kind_set_resolved == "false"
    assert adjudication.included_classified_kinds == "NONE_RATIFIED"
    assert "FILL" in candidate_ids
    assert "UNKNOWN" in candidate_ids
    assert "UNCLASSIFIED" in candidate_ids
    assert "U04_PENDING_ORDER_RESERVATION" in candidate_ids
    assert "C01_THROUGH_C16" in candidate_ids
    assert "FILL" not in RATIFIED_CLASSIFIED_KIND_SET
    assert "U04_PENDING_ORDER_RESERVATION" not in RATIFIED_CLASSIFIED_KIND_SET
    assert any(finding.disposition == DISPOSITION_UNKNOWN for finding in findings)
    assert any(finding.disposition == DISPOSITION_C01_C16_FORBIDDEN for finding in findings)
    assert adjudication.event_kind_inclusion_exclusion_proven == "true"
    assert adjudication.unknown_necessary_class_remains == "true"
    assert adjudication.absence_is_not_zero_events == "true"


def test_unknown_unclassified_and_unratified_kind_fail_closed() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    kwargs = {**_BINDING_KW, **_identity_kwargs(identity)}
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as unknown_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{**kwargs, "event_kind": "UNKNOWN"}
        )
    assert "EVENT_KIND_UNKNOWN_FAIL_CLOSED" in str(unknown_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as unclassified_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{**kwargs, "event_kind": "UNCLASSIFIED"}
        )
    assert "EVENT_KIND_UNCLASSIFIED_FAIL_CLOSED" in str(unclassified_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as fill_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(**kwargs)
    assert "CLASSIFIED_KIND_NOT_RATIFIED" in str(fill_err.value)


def test_missing_ambiguous_source_and_account_mismatch_fail_closed() -> None:
    identity_a = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    identity_b = _identity(identity_id="SYNTHETIC_ACCOUNT_B", account="SYNTHETIC_ACCOUNT_B")
    kwargs = {**_BINDING_KW, **_identity_kwargs(identity_a)}
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as missing_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{**kwargs, "source_seam_id": "MISSING"}
        )
    assert "EVENT_KIND_SOURCE_MISSING_FAIL_CLOSED" in str(missing_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as ambiguous_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{**kwargs, "source_seam_id": "AMBIGUOUS"}
        )
    assert "EVENT_KIND_SOURCE_AMBIGUOUS_FAIL_CLOSED" in str(ambiguous_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as partial_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{**kwargs, "source_seam_id": "PARTIAL"}
        )
    assert "EVENT_KIND_SOURCE_PARTIAL_FAIL_CLOSED" in str(partial_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as mismatch_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            binding_id="BIND_KIND_SEAM_MIX",
            event_kind="FILL",
            source_seam_id="GET_/api/v5/account/bills",
            expected_bound_account_identity_ref=identity_a.identity_id,
            expected_bound_account_identity_digest=identity_a.identity_digest,
            bound_account_identity_ref=identity_b.identity_id,
            bound_account_identity_digest=identity_b.identity_digest,
        )
    assert "EVENT_KIND_SOURCE_IDENTITY_MISMATCH_CROSS_ACCOUNT" in str(mismatch_err.value)
    seams = build_forensic_event_source_seam_census_findings_v1()
    assert all(
        finding.complete_acquisition_possible == "false"
        and finding.disposition
        in (DISPOSITION_C01_C16_FORBIDDEN, "NOT_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM")
        for finding in seams
    )
    assert AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is False
    assert SOURCE_COVERAGE_COMPLETE is False


def test_range_gap_duplicate_order_and_absence_not_zero() -> None:
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as gap_err:
        adjudicate_event_source_range_order_and_duplicate_v1(
            gap_detected="GAP",
            ordering_proven="false",
            duplicate_detected="false",
        )
    assert "EVENT_KIND_SOURCE_RANGE_GAP_FAIL_CLOSED" in str(gap_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as order_err:
        adjudicate_event_source_range_order_and_duplicate_v1(
            gap_detected="UNKNOWN",
            ordering_proven="true",
            duplicate_detected="false",
        )
    assert "EVENT_KIND_SOURCE_ORDERING_NOT_PROVEN" in str(order_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as dup_err:
        adjudicate_event_source_range_order_and_duplicate_v1(
            gap_detected="UNKNOWN",
            ordering_proven="false",
            duplicate_detected="DUPLICATE",
        )
    assert "EVENT_KIND_SOURCE_DUPLICATE_FAIL_CLOSED" in str(dup_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as amb_err:
        adjudicate_event_source_range_order_and_duplicate_v1(
            gap_detected="UNKNOWN",
            ordering_proven="UNPROVEN",
            duplicate_detected="false",
        )
    assert "EVENT_KIND_SOURCE_ORDER_AMBIGUITY_FAIL_CLOSED" in str(amb_err.value)
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as zero_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{
                **_BINDING_KW,
                **_identity_kwargs(identity),
                "claimed_equity_stock_value": "0",
            }
        )
    assert "EVENT_KIND_SOURCE_ABSENCE_IS_NOT_ZERO" in str(zero_err.value)
    adjudication = build_classified_event_kind_set_adjudication_v1(
        census_id="KIND_SET_CENSUS_ABSENCE"
    )
    assert adjudication.absence_is_not_zero_events == "true"
    assert adjudication.complete_event_stream_proven == "false"
    assert COMPLETE_EVENT_STREAM_PROVEN is False


def test_source_binding_cannot_mint_or_overwrite_equity() -> None:
    identity = _identity(identity_id="SYNTHETIC_ACCOUNT_A", account="SYNTHETIC_ACCOUNT_A")
    kwargs = {**_BINDING_KW, **_identity_kwargs(identity)}
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as mint_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{**kwargs, "claimed_equity_stock_value": "100.00"}
        )
    assert "EVENT_KIND_SOURCE_BINDING_CANNOT_MINT_OR_OVERWRITE_EQUITY" in str(mint_err.value)
    with pytest.raises(ClassifiedEventKindSetAndSourceSeamContractError) as mutate_err:
        bind_classified_event_kind_to_authorized_source_seam_v1(
            **{**kwargs, "equity_stock_mutation_status": "MUTATED"}
        )
    assert "EVENT_KIND_SOURCE_BINDING_CANNOT_MUTATE_EQUITY_STOCK" in str(mutate_err.value)


def test_d4_d5_d6_prerequisites_and_existing_owner_unchanged() -> None:
    dag = live_admission_gap_dag_v1()
    adjudication = build_classified_event_kind_set_adjudication_v1(census_id="KIND_SET_CENSUS_PINS")
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    assert EVENT_ACQUISITION_CREATED is True
    assert COMPLETE_EVENT_STREAM_PROVEN is False
    assert KIND_SET_CENSUS_CREATED is True
    assert KIND_SET_RESOLVED is False
    assert AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is False
    assert SOURCE_COVERAGE_COMPLETE is False
    assert ORDERING_PROVEN is False
    assert GAP_DETECTION_FAIL_CLOSED is True
    assert IDEMPOTENCY_REPLAY_IDENTITY_PROVEN is False
    assert D6_COMPLETENESS_PRECONDITIONS_PROVEN is False
    assert EVENT_KIND_SOURCE_SEAM_SELECTED is False
    assert EVENT_KIND_SOURCE_BINDING_IS_NOT_EQUITY_SOURCE_AUTHORITY is True
    assert EVENT_KIND_SOURCE_BINDING_IS_NOT_RAW_EQ_SOURCE_AUTHORITY is True
    assert EVENT_KIND_SOURCE_BINDING_IS_NOT_MAPPING_PROVEN is True
    assert SOURCE_SELECTED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert MAPPING_PROVEN is False
    assert C17_CREATED is False
    assert C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN is True
    assert C01_C16_REJECTION_STILL_BINDING is True
    assert C01_C16_REVIVAL_ALLOWED is False
    assert C01_C16_NOT_ELEVATED is True
    assert len(C01_C16_IDS) == 16
    assert RECONSTRUCTION_ENGINE_CREATED is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert CHECKPOINT_CAN_MINT_EQUITY is False
    assert EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert adjudication.event_kind_source_seam_selected == "false"
    assert adjudication.source_selected == "false"
    assert adjudication.raw_eq_source_authority == "false"
    assert adjudication.mapping_proven == "false"
    assert adjudication.c17_created == "false"
    assert adjudication.reconstruction_engine_created == "false"
    assert adjudication.reconstructed_equity_created == "false"
    assert adjudication.missing_completeness_dependency == MISSING_KIND_SET_AND_SOURCE_SEAM
    assert dag["KIND_SET_RESOLVED"] is False
    assert dag["AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT"] is False
    assert dag["D6_COMPLETENESS_PRECONDITIONS_PROVEN"] is False
    assert dag["COMPLETE_EVENT_STREAM_PROVEN"] is False
    assert dag["EVENT_KIND_SOURCE_SEAM_SELECTED"] is False
    assert dag["SOURCE_SELECTED"] is False
    assert dag["RAW_EQ_SOURCE_AUTHORITY"] is False
    assert dag["MAPPING_PROVEN"] is False
    assert dag["C17_CREATED"] is False
    assert dag["RECONSTRUCTION_ENGINE_CREATED"] is False
    assert dag["EARLIEST_OPTION_D_DEPENDENCY"] == (
        "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    )
    assert EARLIEST_OPTION_D_DEPENDENCY == "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
    assert EARLIEST_D6_COMPLETENESS_DEPENDENCY == (
        "RATIFIED_CLASSIFIED_EVENT_KIND_SET_AND_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM"
    )
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


def test_runbook_av_consumes_owner_go_without_rewriting_au_or_protected_surfaces() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    av_section = _av_section()
    au_start = runbook.index(AU_HEADING)
    au_section = runbook[au_start : runbook.index(AV_HEADING, au_start)]
    assert "THIS_SLICE=11.2.1.AU" in au_section
    assert "THIS_SLICE=11.2.1.AV" not in au_section
    assert (
        "OWNER_GO=OWNER_GO_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM_WORKPACKAGE_V1"
        in av_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in av_section
    assert "THIS_SLICE=11.2.1.AV.FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM" in (
        av_section
    )
    assert "KIND_SET_RESOLVED=false" in av_section
    assert "RATIFIED_CLASSIFIED_EVENT_KIND_SET=EMPTY_FAIL_CLOSED" in av_section
    assert "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT=false" in av_section
    assert "SOURCE_COVERAGE_COMPLETE=false" in av_section
    assert "ORDERING_PROVEN=false" in av_section
    assert "GAP_DETECTION_FAIL_CLOSED=true" in av_section
    assert "IDEMPOTENCY_REPLAY_IDENTITY_PROVEN=false" in av_section
    assert "D6_COMPLETENESS_PRECONDITIONS_PROVEN=false" in av_section
    assert "COMPLETE_EVENT_STREAM_PROVEN=false" in av_section
    assert "EVENT_KIND_SOURCE_SEAM_SELECTED=false" in av_section
    assert "EVENT_KIND_SOURCE_BINDING_IS_NOT_EQUITY_SOURCE_AUTHORITY=true" in av_section
    assert "NETWORK_GET_PERFORMED=false" in av_section
    assert "NETWORK_POST_PERFORMED=false" in av_section
    assert "NEW_TRANSPORT_CREATED=false" in av_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in av_section
    assert "SOURCE_SELECTED=false" in av_section
    assert "MAPPING_PROVEN=false" in av_section
    assert "C17_CREATED=false" in av_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in av_section
    assert "RECONSTRUCTED_EQUITY_CREATED=false" in av_section
    assert "EXISTING_AUTHORITY_OWNER_UNCHANGED=true" in av_section
    assert (
        "ACCOUNT_EQUITY_AUTHORITY_OWNER="
        "ops.governed_productive_account_equity_authority_producer_v1" in av_section
    )
    assert "LIVE_ENABLED=false" in av_section
    assert "MASTER_V2_UNCHANGED=true" in av_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in av_section
    assert "BULL_BEAR_STATE_SWITCH_UNCHANGED=true" in av_section
    assert "TOP20_RANKING_UNIVERSE_UNCHANGED=true" in av_section
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in av_section
    assert (
        "EARLIEST_OPTION_D_DEPENDENCY=D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION" in av_section
    )
    assert (
        "EARLIEST_D6_COMPLETENESS_DEPENDENCY="
        "RATIFIED_CLASSIFIED_EVENT_KIND_SET_AND_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM"
        in av_section
    )
    assert "KIND_SET_RESOLVED=false" in spec
    assert "COMPLETE_EVENT_STREAM_PROVEN=false" in spec
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in spec
    assert "DOCS_TOKEN_FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM_V1.md" in mot
    assert "§11.2.1.AV FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM" in mot
