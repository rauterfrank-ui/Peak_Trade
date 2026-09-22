"""Parallel-decoupled tracks authority/interface/reconciliation contract v1.

Materializes OWNER_DECISION_1=C (PARALLEL_DECOUPLED_TRACKS) as a docs/contract
surface for RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING.

Does not select a source, mint sizing, create Option-D reconstruction
reconciliation (RECONCILIATION_CONTRACT_CREATED remains false), map
Source→Semantic, or authorize producers / GET / POST / Live.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    MAPPING_PROVEN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    GOVERNED_PRODUCER_CREATED,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    RECONCILIATION_CONTRACT_CREATED,
    SOURCE_SELECTED,
)

SCHEMA_CLASS = (
    "RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_"
    "AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1"
)
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"

OWNER_GO = (
    "OWNER_GO_FULL_CORE_RUNNING_ACCOUNT_EQUITY_PARALLEL_DECOUPLED_TRACKS_"
    "AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_V1"
)
OWNER_GO_STATUS = "CONSUMED"
OWNER_DECISION_1 = "C"
AUTHORITY_MODEL = "PARALLEL_DECOUPLED_TRACKS"
DIMENSION_ID = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"

EXPECTED_ORIGIN_MAIN_SHA = "be19ac91eefc40cece83d354a34061694211ecdd"

# Distinct from Option-D reconstruction↔eq RECONCILIATION_CONTRACT_CREATED.
PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED = True
OPTION_D_RECONSTRUCTION_RECONCILIATION_CONTRACT_CREATED = False

TRACK_CURRENT_VENUE_OBSERVATION = "CURRENT_VENUE_OBSERVATION_TRACK"
TRACK_OPTION_D_RECONSTRUCTION = "OPTION_D_RECONSTRUCTION_EQUITY_STOCK_TRACK"

OBSERVATION_IS_NOT_AUTHORITY = True
RECONSTRUCTION_OR_EQUITY_STOCK_AUTHORITY_IS_NOT_STEP_29P_SIZING_AUTHORITY = True
SILENT_EQUIVALENCE_OR_SUBSTITUTION_FORBIDDEN = True
RECONCILIATION_MAY_COMPARE_OR_DIAGNOSE = True
RECONCILIATION_MAY_NOT_MINT_AUTHORITY_BY_AGREEMENT = True
SOURCE_TO_SEMANTIC_MAPPING_AUTHORIZED_BY_THIS_WP = False
SIZING_MINT_AUTHORIZED_BY_THIS_WP = False
QUARANTINE_OR_PR_6714_USED_AS_AUTHORITY = False
QUARANTINE_OR_PR_6714_USED_AS_IMPLEMENTATION_SOURCE = False

# Risk-freeze / sizing-chain pins preserved (not package empty-slot identity).
ACCOUNT_EQUITY_AUTHORITY_OWNER = "UNRESOLVED"
ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED = False
SELECTED_SOURCE = "NONE"
AVAILABLE_FOR_SIZING_SOURCE_STATUS = "UNBOUND"

NEXT_OWNER_GO_REQUIRED = (
    "OWNER_GO_REQUIRED_TO_RATIFY_SOURCE_TO_SEMANTIC_MAPPING_OR_BIND_"
    "AVAILABLE_FOR_SIZING_PRODUCER_UNDER_PARALLEL_DECOUPLED_TRACKS_V1"
)
NEXT_UNRESOLVED_DEPENDENCY = "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"

FORBIDDEN_SILENT_SUBSTITUTES = (
    "availEq",
    "eq",
    "reconstructed_equity",
    "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING",
)

EPISTEMIC_LABELS = (
    "CANONICAL_AUTHORITY",
    "ADJUDICATED_OWNER_DECISION",
    "ADJUDICATED_FACT",
    "NAVIGATION",
    "INTERPRETATION",
    "HYPOTHESIS",
    "UNKNOWN",
)


class ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(ValueError):
    """Fail-closed contract construction / pin violation."""


@dataclass(frozen=True)
class RunningAccountEquityParallelDecoupledTracksAuthorityInterfaceReconciliationContractV1:
    contract_id: str
    contract_version: str
    schema_class: str
    owner_go: str
    owner_go_status: str
    owner_decision_1: str
    authority_model: str
    dimension_id: str
    authority_effect: str
    runtime_authorization_effect: str
    observation_is_not_authority: bool
    reconstruction_or_equity_stock_authority_is_not_step_29p_sizing_authority: bool
    silent_equivalence_or_substitution_forbidden: bool
    reconciliation_may_compare_or_diagnose: bool
    reconciliation_may_not_mint_authority_by_agreement: bool
    parallel_decoupled_tracks_contract_created: bool
    option_d_reconstruction_reconciliation_contract_created: bool
    source_to_semantic_mapping_authorized_by_this_wp: bool
    sizing_mint_authorized_by_this_wp: bool
    account_equity_authority_owner: str
    account_equity_authority_chain_closed: bool
    canonically_valid_account_equity_source_mapping: bool
    selected_source: str
    available_for_sizing_source_status: str
    legacy_reconstruction_required_for_live: bool
    source_selected: bool
    mapping_proven: bool
    mapped_to_running_account_equity_available_for_sizing: bool
    governed_producer_created: bool
    quarantine_or_pr_6714_used_as_authority: bool
    next_owner_go_required: str
    next_unresolved_dependency: str
    expected_origin_main_sha: str


def _require_preserved_pins_v1() -> None:
    if RECONCILIATION_CONTRACT_CREATED is not False:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "OPTION_D_RECONCILIATION_CONTRACT_CREATED_MUST_REMAIN_FALSE"
        )
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_MUST_REMAIN_FALSE"
        )
    if SOURCE_SELECTED is not False or CURRENT_PRODUCTIVE_SOURCE_SELECTED is not False:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "SOURCE_SELECTED_MUST_REMAIN_FALSE"
        )
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS != "UNBOUND":
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "AVAILABLE_FOR_SIZING_SOURCE_STATUS_MUST_REMAIN_UNBOUND"
        )
    if LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is not False:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE_MUST_REMAIN_FALSE"
        )
    if MAPPING_PROVEN is not False:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "MAPPING_PROVEN_MUST_REMAIN_FALSE"
        )
    if MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is not False:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING_MUST_REMAIN_FALSE"
        )
    if GOVERNED_PRODUCER_CREATED is not False:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "GOVERNED_PRODUCER_CREATED_MUST_REMAIN_FALSE"
        )


def build_running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1(
    *,
    contract_id: str,
) -> RunningAccountEquityParallelDecoupledTracksAuthorityInterfaceReconciliationContractV1:
    if not contract_id or not str(contract_id).strip():
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "CONTRACT_ID_REQUIRED"
        )
    _require_preserved_pins_v1()
    return RunningAccountEquityParallelDecoupledTracksAuthorityInterfaceReconciliationContractV1(
        contract_id=str(contract_id).strip(),
        contract_version=CONTRACT_VERSION,
        schema_class=SCHEMA_CLASS,
        owner_go=OWNER_GO,
        owner_go_status=OWNER_GO_STATUS,
        owner_decision_1=OWNER_DECISION_1,
        authority_model=AUTHORITY_MODEL,
        dimension_id=DIMENSION_ID,
        authority_effect=AUTHORITY_EFFECT,
        runtime_authorization_effect=RUNTIME_AUTHORIZATION_EFFECT,
        observation_is_not_authority=OBSERVATION_IS_NOT_AUTHORITY,
        reconstruction_or_equity_stock_authority_is_not_step_29p_sizing_authority=(
            RECONSTRUCTION_OR_EQUITY_STOCK_AUTHORITY_IS_NOT_STEP_29P_SIZING_AUTHORITY
        ),
        silent_equivalence_or_substitution_forbidden=(SILENT_EQUIVALENCE_OR_SUBSTITUTION_FORBIDDEN),
        reconciliation_may_compare_or_diagnose=RECONCILIATION_MAY_COMPARE_OR_DIAGNOSE,
        reconciliation_may_not_mint_authority_by_agreement=(
            RECONCILIATION_MAY_NOT_MINT_AUTHORITY_BY_AGREEMENT
        ),
        parallel_decoupled_tracks_contract_created=(
            PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED
        ),
        option_d_reconstruction_reconciliation_contract_created=(
            OPTION_D_RECONSTRUCTION_RECONCILIATION_CONTRACT_CREATED
        ),
        source_to_semantic_mapping_authorized_by_this_wp=(
            SOURCE_TO_SEMANTIC_MAPPING_AUTHORIZED_BY_THIS_WP
        ),
        sizing_mint_authorized_by_this_wp=SIZING_MINT_AUTHORIZED_BY_THIS_WP,
        account_equity_authority_owner=ACCOUNT_EQUITY_AUTHORITY_OWNER,
        account_equity_authority_chain_closed=ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED,
        canonically_valid_account_equity_source_mapping=(
            CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING
        ),
        selected_source=SELECTED_SOURCE,
        available_for_sizing_source_status=AVAILABLE_FOR_SIZING_SOURCE_STATUS,
        legacy_reconstruction_required_for_live=LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
        source_selected=SOURCE_SELECTED,
        mapping_proven=MAPPING_PROVEN,
        mapped_to_running_account_equity_available_for_sizing=(
            MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING
        ),
        governed_producer_created=GOVERNED_PRODUCER_CREATED,
        quarantine_or_pr_6714_used_as_authority=QUARANTINE_OR_PR_6714_USED_AS_AUTHORITY,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        next_unresolved_dependency=NEXT_UNRESOLVED_DEPENDENCY,
        expected_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )


def reject_silent_track_substitution_v1(*, claimed_equivalence: Mapping[str, str]) -> None:
    """Fail closed if any forbidden silent equivalence is asserted."""
    left = str(claimed_equivalence.get("left", "")).strip()
    right = str(claimed_equivalence.get("right", "")).strip()
    if not left or not right:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "CLAIMED_EQUIVALENCE_INCOMPLETE"
        )
    forbidden = set(FORBIDDEN_SILENT_SUBSTITUTES)
    if left in forbidden and right in forbidden and left != right:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "SILENT_EQUIVALENCE_OR_SUBSTITUTION_FORBIDDEN"
        )


def reject_authority_mint_by_reconciliation_agreement_v1(*, agreement: bool) -> None:
    if agreement is True:
        raise ParallelDecoupledTracksAuthorityInterfaceReconciliationContractError(
            "RECONCILIATION_MAY_NOT_MINT_AUTHORITY_BY_AGREEMENT"
        )
