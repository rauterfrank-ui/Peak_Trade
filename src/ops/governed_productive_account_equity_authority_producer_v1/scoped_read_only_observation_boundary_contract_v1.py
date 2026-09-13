"""D6 scoped read-only observation-boundary contract.

Defines fail-closed observation domains only. Does not execute
observation. Does not authorize GET. Does not ratify kinds.
Does not release Mini-Slice 2 or D7. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_ATLAS_AUTHORITY,
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    ACCOUNT_COMPOSITION_OBSERVATION_DEFINED,
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C01_REHABILITATION_FORBIDDEN,
    C17_CREATED,
    CANDIDATE_SURFACE_SELECTION,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EARLIEST_D6_KIND_SET_DEPENDENCY,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED,
    FEE_EMBEDDING_OBSERVATION_DEFINED,
    KIND_SET_RESOLVED,
    LIABILITY_OBSERVATION_DEFINED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    OBSERVATION_BOUNDARY_CONTRACT_CREATED,
    OBSERVATION_BOUNDARY_CONTRACT_STATUS,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_IS_NOT_COMPLETENESS_UNLESS_RANGE_ORDERING_PROVENANCE_PROVEN,
    OBSERVATION_IS_NOT_D7_AUTHORIZATION,
    OBSERVATION_IS_NOT_KIND_RATIFICATION,
    OBSERVATION_IS_NOT_MS2_RELEASE,
    OBSERVATION_IS_NOT_RAW_EQ_SOURCE_AUTHORITY,
    OBSERVATION_IS_NOT_SOURCE_AUTHORITY,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    PAPER_SIMULATED_FEE_ACCOUNTING_IS_NON_VENUE_EVIDENCE,
    PATH_A_ARCHIVE_OR_REPO_SEARCH,
    PATH_B_SCOPED_READ_ONLY_OBSERVATION,
    PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESIDUAL_KIND_DECISION,
    SOURCE_SELECTED,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
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

SCHEMA_CLASS = "SCOPED_READ_ONLY_OBSERVATION_BOUNDARY_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
BOUNDARY_STATUS_DEFINED_NOT_EXECUTED = "DEFINED_NOT_EXECUTED_GET_UNAUTHORIZED"
PATH_A_REJECT = "REJECT"
PATH_B_SELECTED_BUT_BLOCKED = "SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION"
PATH_C_REJECT = "REJECT"
SURFACE_CLASS_CANDIDATE = "CANDIDATE_SURFACE"
SURFACE_CLASS_DATA_CLASS_ONLY = "REQUIRED_DATA_CLASS_ENDPOINT_NOT_SELECTED"
ATLAS_AUTHORITY_NONE = "NONE"
CURRENT_NONCANONICAL = "CURRENT_NONCANONICAL"
SELECTION_NONE = "NONE_SELECTED"

OBS_ACCOUNT_COMPOSITION = "OBS_D6_ACCOUNT_COMPOSITION_V1"
OBS_LIABILITY = "OBS_D6_LIABILITY_V1"
OBS_FEE_EMBEDDING = "OBS_D6_FEE_EMBEDDING_V1"
OBS_EXOGENOUS_COVERAGE = "OBS_D6_EXOGENOUS_EVENT_COVERAGE_V1"

DATA_CLASS_CHECKPOINT_EQ_COMPONENT_BREAKDOWN = "CHECKPOINT_EQ_COMPONENT_BREAKDOWN"
DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE = "BORROW_OR_ACCOUNT_LIABILITY_STATE"
DATA_CLASS_ACCRUED_OR_ALREADY_CHARGED_FEE_DELTA = "ACCRUED_OR_ALREADY_CHARGED_FEE_DELTA"
DATA_CLASS_EXOGENOUS_EQUITY_AFFECTING_ACCOUNT_EVENTS = "EXOGENOUS_EQUITY_AFFECTING_ACCOUNT_EVENTS"

CANDIDATE_SURFACE_ACCOUNT_BILLS = "GET_/api/v5/account/bills"
CANDIDATE_SURFACE_TRADE_FILLS = "GET_/api/v5/trade/fills"
CANDIDATE_SURFACE_ACCOUNT_BALANCE = "C01_Q_GET_PACK_DETAILS_AVAILEQ"

REQUIRED_ACCOUNT_BINDING = "D4_BOUND_ACCOUNT_IDENTITY_REFERENCE_AND_D5_CHECKPOINT_OBSERVATION"
REQUIRED_TIME_RANGE = (
    "EXPLICIT_CHECKPOINT_WINDOW_BOUND_TO_D5_AS_OF_ABSENCE_IN_ARBITRARY_"
    "SMALL_WINDOW_IS_NOT_GLOBAL_ZERO"
)
REQUIRED_PROVENANCE = (
    "VENUE_OR_AUTHORIZED_ACCOUNT_EVIDENCE_WITH_IDENTITY_DIGEST_NOT_PAPER_"
    "SIMULATED_AND_NOT_RAW_EQ_SOURCE_AUTHORITY"
)
REQUIRED_FRESHNESS = (
    "FRESHNESS_PROVEN_RELATIVE_TO_BOUND_CHECKPOINT_WINDOW_NOT_LIVE_NOW_UNLESS_SEPARATELY_AUTHORIZED"
)
REQUIRED_ORDERING = (
    "SOURCE_PROVEN_TOTAL_ORDER_OR_FAIL_CLOSED_UNPROVEN_ORDERING_CANNOT_"
    "SUPPORT_COMPLETENESS_OR_EXCLUDE"
)
REQUIRED_REPLAY_IDENTITY = (
    "STABLE_EVENT_OR_COMPONENT_IDENTITY_SUPPORTING_IDEMPOTENT_REPLAY_AND_DUPLICATE_DETECTION"
)

HYPOTHESIS_CLASSES_NOT_RATIFIED = "DEPOSIT,WITHDRAWAL,TRANSFER,FUNDING,INTEREST,LIQUIDATION,CONVERT"


class ScopedReadOnlyObservationBoundaryContractError(ValueError):
    """Fail-closed scoped read-only observation-boundary violation."""


@dataclass(frozen=True)
class ObservationDomainRecordV1:
    observation_id: str
    question_answered: str
    required_fields: str
    required_account_binding: str
    required_time_range: str
    required_provenance: str
    required_freshness: str
    required_ordering: str
    required_idempotency_or_replay_identity: str
    success_criterion: str
    fail_closed_criterion: str
    what_it_can_prove: str
    what_it_cannot_prove: str
    which_unknown_it_can_resolve: str
    include_decision_preconditions: str
    exclude_decision_preconditions: str


@dataclass(frozen=True)
class ObservationCandidateSurfaceRecordV1:
    surface_id: str
    classification: str
    atlas_authority: str
    current_status: str
    selected: str
    may_inform_data_class: str
    forbidden_use: str


@dataclass(frozen=True)
class ScopedReadOnlyObservationBoundaryContractV1:
    persist_id: str
    observation_boundary_contract_status: str
    observation_executed: str
    observation_execution_authorized: str
    observation_network_get_authorized: str
    event_acquisition_network_get_authorized: str
    account_composition_observation_defined: str
    liability_observation_defined: str
    fee_embedding_observation_defined: str
    exogenous_event_coverage_observation_defined: str
    observation_is_not_source_authority: str
    observation_is_not_kind_ratification: str
    observation_is_not_ms2_release: str
    observation_is_not_d7_authorization: str
    observation_is_not_raw_eq_source_authority: str
    observation_is_not_completeness_unless_range_ordering_provenance_proven: str
    u05_kind_decision: str
    u06_kind_decision: str
    residual_kind_decision: str
    ratified_classified_event_kind_set: str
    kind_set_resolved: str
    ms1_kind_set_fully_closed: str
    ms2_authorized: str
    d6_fully_closed: str
    d7_authorized: str
    path_a: str
    path_b: str
    path_c: str
    candidate_surface_selection: str
    account_bills_atlas_authority: str
    paper_simulated_fee_accounting_is_non_venue_evidence: str
    c01_rehabilitation_forbidden: str
    earliest_d6_kind_set_dependency: str
    authority_effect: str
    provenance_digest: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_observation_boundary_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise ScopedReadOnlyObservationBoundaryContractError(
            f"OBSERVATION_BOUNDARY_FIELD_MISSING:{field}"
        )
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise ScopedReadOnlyObservationBoundaryContractError(
            f"OBSERVATION_BOUNDARY_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise ScopedReadOnlyObservationBoundaryContractError(
            f"OBSERVATION_BOUNDARY_FIELD_MISSING:{field}"
        )
    return text


def _assert_shared_pins() -> None:
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_BOUNDARY_AUTHORITY_OWNER_MUTATED"
        )
    if OBSERVATION_BOUNDARY_CONTRACT_CREATED is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_BOUNDARY_CONTRACT_CREATED_NOT_TRUE"
        )
    if OBSERVATION_BOUNDARY_CONTRACT_STATUS != BOUNDARY_STATUS_DEFINED_NOT_EXECUTED:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_BOUNDARY_CONTRACT_STATUS_DRIFT"
        )
    if OBSERVATION_EXECUTED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_EXECUTED_MUST_REMAIN_FALSE"
        )
    if OBSERVATION_EXECUTION_AUTHORIZED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_NETWORK_GET_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if ACCOUNT_COMPOSITION_OBSERVATION_DEFINED is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "ACCOUNT_COMPOSITION_OBSERVATION_NOT_DEFINED"
        )
    if LIABILITY_OBSERVATION_DEFINED is not True:
        raise ScopedReadOnlyObservationBoundaryContractError("LIABILITY_OBSERVATION_NOT_DEFINED")
    if FEE_EMBEDDING_OBSERVATION_DEFINED is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "FEE_EMBEDDING_OBSERVATION_NOT_DEFINED"
        )
    if EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "EXOGENOUS_EVENT_COVERAGE_OBSERVATION_NOT_DEFINED"
        )
    if OBSERVATION_IS_NOT_SOURCE_AUTHORITY is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_MUST_NOT_BE_SOURCE_AUTHORITY"
        )
    if OBSERVATION_IS_NOT_KIND_RATIFICATION is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_MUST_NOT_BE_KIND_RATIFICATION"
        )
    if OBSERVATION_IS_NOT_MS2_RELEASE is not True:
        raise ScopedReadOnlyObservationBoundaryContractError("OBSERVATION_MUST_NOT_RELEASE_MS2")
    if OBSERVATION_IS_NOT_D7_AUTHORIZATION is not True:
        raise ScopedReadOnlyObservationBoundaryContractError("OBSERVATION_MUST_NOT_AUTHORIZE_D7")
    if OBSERVATION_IS_NOT_RAW_EQ_SOURCE_AUTHORITY is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_MUST_NOT_BE_RAW_EQ_SOURCE_AUTHORITY"
        )
    if OBSERVATION_IS_NOT_COMPLETENESS_UNLESS_RANGE_ORDERING_PROVENANCE_PROVEN is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "OBSERVATION_MUST_NOT_IMPLY_COMPLETENESS_WITHOUT_COVERAGE_PROOF"
        )
    if PAPER_SIMULATED_FEE_ACCOUNTING_IS_NON_VENUE_EVIDENCE is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "PAPER_SIMULATED_FEE_MUST_REMAIN_NON_VENUE"
        )
    if C01_REHABILITATION_FORBIDDEN is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "C01_REHABILITATION_MUST_REMAIN_FORBIDDEN"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "ACCOUNT_BILLS_MUST_REMAIN_CURRENT_NONCANONICAL"
        )
    if ACCOUNT_BILLS_ATLAS_AUTHORITY != ATLAS_AUTHORITY_NONE:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "ACCOUNT_BILLS_ATLAS_AUTHORITY_MUST_REMAIN_NONE"
        )
    if CANDIDATE_SURFACE_SELECTION != SELECTION_NONE:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "CANDIDATE_SURFACE_MUST_REMAIN_UNSELECTED"
        )
    if PATH_A_ARCHIVE_OR_REPO_SEARCH != PATH_A_REJECT:
        raise ScopedReadOnlyObservationBoundaryContractError("PATH_A_MUST_REMAIN_REJECT")
    if PATH_B_SCOPED_READ_ONLY_OBSERVATION != PATH_B_SELECTED_BUT_BLOCKED:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "PATH_B_MUST_REMAIN_SELECTED_BUT_BLOCKED"
        )
    if PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT != PATH_C_REJECT:
        raise ScopedReadOnlyObservationBoundaryContractError("PATH_C_MUST_REMAIN_REJECT")
    if KIND_SET_RESOLVED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("TAXONOMY_KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "CLASSIFIED_KIND_SET_MUST_REMAIN_EMPTY_FAIL_CLOSED"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ScopedReadOnlyObservationBoundaryContractError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ScopedReadOnlyObservationBoundaryContractError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if MS1_KIND_SET_FULLY_CLOSED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("MS1_KIND_SET_FULLY_CLOSED_NOT_FALSE")
    if MS2_AUTHORIZED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("D7_AUTHORIZED_NOT_FALSE")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_NOT_ABSENT"
        )
    if EVENT_KIND_SOURCE_SEAM_SELECTED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "EVENT_KIND_SOURCE_SEAM_SELECTED_NOT_FALSE"
        )
    if SOURCE_SELECTED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("SOURCE_SELECTED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "COMPLETE_EVENT_STREAM_PROVEN_NOT_FALSE"
        )
    if D6_COMPLETENESS_PRECONDITIONS_PROVEN is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "D6_COMPLETENESS_PRECONDITIONS_PROVEN_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError("C17_CREATED_NOT_FALSE")
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise ScopedReadOnlyObservationBoundaryContractError(
            "RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE"
        )
    if EARLIEST_D6_KIND_SET_DEPENDENCY != (
        "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
    ):
        raise ScopedReadOnlyObservationBoundaryContractError(
            "EARLIEST_D6_KIND_SET_DEPENDENCY_DRIFT"
        )


def build_observation_domain_records_v1() -> Tuple[ObservationDomainRecordV1, ...]:
    _assert_shared_pins()
    return (
        ObservationDomainRecordV1(
            observation_id=OBS_ACCOUNT_COMPOSITION,
            question_answered=("Which components are already contained in the bound checkpoint eq"),
            required_fields=(
                "bound_account_identity,checkpoint_as_of,eq_value,component_identity,"
                "component_value,component_inclusion_vector,component_provenance,"
                "source_revision_or_digest"
            ),
            required_account_binding=REQUIRED_ACCOUNT_BINDING,
            required_time_range=REQUIRED_TIME_RANGE,
            required_provenance=REQUIRED_PROVENANCE,
            required_freshness=REQUIRED_FRESHNESS,
            required_ordering=REQUIRED_ORDERING,
            required_idempotency_or_replay_identity=REQUIRED_REPLAY_IDENTITY,
            success_criterion=(
                "Component breakdown is bound to D4 identity and D5 checkpoint as_of "
                "with provenance sufficient to name included components"
            ),
            fail_closed_criterion=(
                "Missing binding, using eq as source authority, minting equity, "
                "rehabilitating C01, or deriving event taxonomy from the snapshot"
            ),
            what_it_can_prove=("Which named components are already inside the bound checkpoint eq"),
            what_it_cannot_prove=(
                "eq is not source authority; cannot mint EQUITY_STOCK; cannot "
                "rehabilitate C01; cannot ratify event kinds from a snapshot"
            ),
            which_unknown_it_can_resolve=(
                "EMBEDDING_PRECONDITION_FOR_U05_AND_U06_NOT_A_KIND_DECISION"
            ),
            include_decision_preconditions=(
                "Composition observation cannot INCLUDE a classified event kind"
            ),
            exclude_decision_preconditions=(
                "Composition observation cannot EXCLUDE a classified event kind"
            ),
        ),
        ObservationDomainRecordV1(
            observation_id=OBS_LIABILITY,
            question_answered=(
                "Does genuine borrow or account liability exist; if yes does it "
                "affect EQUITY_STOCK; is it already embedded in eq or checkpoint"
            ),
            required_fields=(
                "bound_account_identity,checkpoint_as_of,liability_identity,"
                "liability_exists,liability_value,affects_equity_stock,"
                "already_embedded_in_eq,provenance,source_revision_or_digest"
            ),
            required_account_binding=REQUIRED_ACCOUNT_BINDING,
            required_time_range=REQUIRED_TIME_RANGE,
            required_provenance=REQUIRED_PROVENANCE,
            required_freshness=REQUIRED_FRESHNESS,
            required_ordering=REQUIRED_ORDERING,
            required_idempotency_or_replay_identity=REQUIRED_REPLAY_IDENTITY,
            success_criterion=(
                "Bound-account liability presence, EQUITY_STOCK effect, and "
                "embedding status are each positively proven or fail-closed unknown"
            ),
            fail_closed_criterion=(
                "Empty rows without coverage provenance; treating snapshot embedding "
                "as kind ratification; P01 overlap used as U05 kind proof"
            ),
            what_it_can_prove=(
                "Whether a genuine borrow/liability exists in the defined window, "
                "whether it moves EQUITY_STOCK, and whether it is already in eq"
            ),
            what_it_cannot_prove=(
                "Cannot ratify U05 as a classified kind by itself; cannot globalize "
                "absence from a small window; cannot treat algebra placement as kind"
            ),
            which_unknown_it_can_resolve=CANDIDATE_U05,
            include_decision_preconditions=(
                "Genuine liability exists AND produces an EQUITY_STOCK delta not "
                "already embedded AND event identity/range/ordering/provenance are "
                "sufficient AND a later Owner-GO ratifies the kind"
            ),
            exclude_decision_preconditions=(
                "Coverage-proven that no genuine borrow/liability exists in the "
                "defined window OR liability is proven fully embedded with no "
                "remaining event delta; empty rows without coverage cannot EXCLUDE"
            ),
        ),
        ObservationDomainRecordV1(
            observation_id=OBS_FEE_EMBEDDING,
            question_answered=(
                "Are accrued or already-charged fees already in eq, a separate "
                "account delta, or only a reconciliation dimension"
            ),
            required_fields=(
                "bound_account_identity,checkpoint_as_of,fee_identity,fee_value,"
                "already_embedded_in_eq,separate_account_delta,reconciliation_only,"
                "venue_versus_paper,provenance,source_revision_or_digest"
            ),
            required_account_binding=REQUIRED_ACCOUNT_BINDING,
            required_time_range=REQUIRED_TIME_RANGE,
            required_provenance=REQUIRED_PROVENANCE,
            required_freshness=REQUIRED_FRESHNESS,
            required_ordering=REQUIRED_ORDERING,
            required_idempotency_or_replay_identity=REQUIRED_REPLAY_IDENTITY,
            success_criterion=(
                "Fee embedding class is proven as embedded-in-eq OR separate-delta "
                "OR reconciliation-only, with venue versus paper distinguished"
            ),
            fail_closed_criterion=(
                "Paper or simulated fee accounting used as venue evidence; blind "
                "subtraction; bills/fills treated as D6 authority; empty rows "
                "without coverage provenance treated as no fee class"
            ),
            what_it_can_prove=(
                "Whether venue accrued/already-charged fees sit inside eq, as a "
                "separate account delta, or only as a reconciliation dimension"
            ),
            what_it_cannot_prove=(
                "Cannot ratify U06 as a classified kind by itself; paper/simulated "
                "fee accounting remains NON_VENUE_EVIDENCE; cannot globalize absence"
            ),
            which_unknown_it_can_resolve=CANDIDATE_U06,
            include_decision_preconditions=(
                "Venue fee delta exists, is not already in eq, has identity and "
                "provenance, is an EQUITY_STOCK event not merely reconciliation, "
                "AND a later Owner-GO ratifies the kind"
            ),
            exclude_decision_preconditions=(
                "Fees proven fully embedded in eq with no remaining event class OR "
                "proven reconciliation-only with no event delta; paper accounting "
                "cannot EXCLUDE; empty window cannot EXCLUDE without coverage"
            ),
        ),
        ObservationDomainRecordV1(
            observation_id=OBS_EXOGENOUS_COVERAGE,
            question_answered=(
                "Whether equity-affecting exogenous account events can or must "
                "occur in the bound checkpoint window for deposit, withdrawal, "
                "transfer, funding, interest, liquidation, convert"
            ),
            required_fields=(
                "bound_account_identity,checkpoint_window_start,checkpoint_window_end,"
                "event_class,presence_or_absence,coverage_provenance,ordering_proven,"
                "completeness_claim_basis,source_revision_or_digest"
            ),
            required_account_binding=REQUIRED_ACCOUNT_BINDING,
            required_time_range=REQUIRED_TIME_RANGE,
            required_provenance=REQUIRED_PROVENANCE,
            required_freshness=REQUIRED_FRESHNESS,
            required_ordering=REQUIRED_ORDERING,
            required_idempotency_or_replay_identity=REQUIRED_REPLAY_IDENTITY,
            success_criterion=(
                "Positive presence or absence of each named hypothesis class is "
                "recorded inside an explicit window with stated coverage provenance"
            ),
            fail_closed_criterion=(
                "Ratifying any hypothesis class now; interpreting no rows as no "
                "possible event class; claiming completeness without range, "
                "ordering, and provenance proof; globalizing a small-window absence"
            ),
            what_it_can_prove=(
                "Presence or absence of named exogenous classes inside one defined "
                "checkpoint window, and whether that window's coverage is proven"
            ),
            what_it_cannot_prove=(
                "Cannot ratify deposit/withdrawal/transfer/funding/interest/"
                "liquidation/convert kinds; absence in a small window is not global "
                "zero; completeness requires explicit coverage provenance"
            ),
            which_unknown_it_can_resolve=CANDIDATE_RESIDUAL,
            include_decision_preconditions=(
                "Presence of an equity-affecting event of that class in a "
                "coverage-proven window PLUS a later Owner-GO for kind ratification; "
                "plausibility cannot INCLUDE"
            ),
            exclude_decision_preconditions=(
                "Coverage-proven complete inventory of the defined window with no "
                "unnamed remainder; one window cannot globalize NO_REMAINDER; empty "
                "rows are not global zero event classes"
            ),
        ),
    )


def build_observation_candidate_surface_records_v1() -> Tuple[
    ObservationCandidateSurfaceRecordV1, ...
]:
    _assert_shared_pins()
    return (
        ObservationCandidateSurfaceRecordV1(
            surface_id=DATA_CLASS_CHECKPOINT_EQ_COMPONENT_BREAKDOWN,
            classification=SURFACE_CLASS_DATA_CLASS_ONLY,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            current_status="REQUIRED_DATA_CLASS_NO_ENDPOINT_SELECTED",
            selected=FALSE_TOKEN,
            may_inform_data_class=DATA_CLASS_CHECKPOINT_EQ_COMPONENT_BREAKDOWN,
            forbidden_use="RAW_EQ_SOURCE_AUTHORITY_OR_C01_REHABILITATION_OR_KIND_RATIFICATION",
        ),
        ObservationCandidateSurfaceRecordV1(
            surface_id=DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
            classification=SURFACE_CLASS_DATA_CLASS_ONLY,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            current_status="REQUIRED_DATA_CLASS_NO_ENDPOINT_SELECTED",
            selected=FALSE_TOKEN,
            may_inform_data_class=DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
            forbidden_use="U05_KIND_RATIFICATION_OR_SOURCE_SEAM_SELECTION",
        ),
        ObservationCandidateSurfaceRecordV1(
            surface_id=DATA_CLASS_ACCRUED_OR_ALREADY_CHARGED_FEE_DELTA,
            classification=SURFACE_CLASS_DATA_CLASS_ONLY,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            current_status="REQUIRED_DATA_CLASS_NO_ENDPOINT_SELECTED",
            selected=FALSE_TOKEN,
            may_inform_data_class=DATA_CLASS_ACCRUED_OR_ALREADY_CHARGED_FEE_DELTA,
            forbidden_use="U06_KIND_RATIFICATION_OR_PAPER_FEE_AS_VENUE_EVIDENCE",
        ),
        ObservationCandidateSurfaceRecordV1(
            surface_id=DATA_CLASS_EXOGENOUS_EQUITY_AFFECTING_ACCOUNT_EVENTS,
            classification=SURFACE_CLASS_DATA_CLASS_ONLY,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            current_status="REQUIRED_DATA_CLASS_NO_ENDPOINT_SELECTED",
            selected=FALSE_TOKEN,
            may_inform_data_class=DATA_CLASS_EXOGENOUS_EQUITY_AFFECTING_ACCOUNT_EVENTS,
            forbidden_use="HYPOTHESIS_CLASS_RATIFICATION_OR_NO_ROWS_EQUALS_NO_CLASS",
        ),
        ObservationCandidateSurfaceRecordV1(
            surface_id=CANDIDATE_SURFACE_ACCOUNT_BILLS,
            classification=SURFACE_CLASS_CANDIDATE,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            current_status=CURRENT_NONCANONICAL,
            selected=FALSE_TOKEN,
            may_inform_data_class=(
                f"{DATA_CLASS_ACCRUED_OR_ALREADY_CHARGED_FEE_DELTA},"
                f"{DATA_CLASS_EXOGENOUS_EQUITY_AFFECTING_ACCOUNT_EVENTS}"
            ),
            forbidden_use="SOURCE_SEAM_SELECTION_OR_GET_AUTHORIZATION_OR_ATLAS_UPLIFT",
        ),
        ObservationCandidateSurfaceRecordV1(
            surface_id=CANDIDATE_SURFACE_TRADE_FILLS,
            classification=SURFACE_CLASS_CANDIDATE,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            current_status="LIVE_HANDOFF_CANARY_FILL_EVIDENCE_NOT_D6",
            selected=FALSE_TOKEN,
            may_inform_data_class=DATA_CLASS_ACCRUED_OR_ALREADY_CHARGED_FEE_DELTA,
            forbidden_use="D6_EVENT_SOURCE_AUTHORITY_OR_U06_KIND_RATIFICATION",
        ),
        ObservationCandidateSurfaceRecordV1(
            surface_id=CANDIDATE_SURFACE_ACCOUNT_BALANCE,
            classification=SURFACE_CLASS_CANDIDATE,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            current_status="REJECTED_C01_NOT_EQUITY_SOURCE",
            selected=FALSE_TOKEN,
            may_inform_data_class=DATA_CLASS_CHECKPOINT_EQ_COMPONENT_BREAKDOWN,
            forbidden_use="C01_REHABILITATION_OR_RAW_EQ_SOURCE_AUTHORITY_OR_EQUITY_MINT",
        ),
    )


def build_scoped_read_only_observation_boundary_contract_v1(
    *,
    persist_id: str,
) -> ScopedReadOnlyObservationBoundaryContractV1:
    _assert_shared_pins()
    persist = _require_non_empty_str(field="persist_id", raw=persist_id)
    domains = build_observation_domain_records_v1()
    surfaces = build_observation_candidate_surface_records_v1()
    if tuple(record.observation_id for record in domains) != (
        OBS_ACCOUNT_COMPOSITION,
        OBS_LIABILITY,
        OBS_FEE_EMBEDDING,
        OBS_EXOGENOUS_COVERAGE,
    ):
        raise ScopedReadOnlyObservationBoundaryContractError("OBSERVATION_DOMAIN_SET_DRIFT")
    if any(surface.selected != FALSE_TOKEN for surface in surfaces):
        raise ScopedReadOnlyObservationBoundaryContractError("CANDIDATE_SURFACE_SELECTED_FORBIDDEN")
    payload = {
        "persist_id": persist,
        "observation_boundary_contract_status": BOUNDARY_STATUS_DEFINED_NOT_EXECUTED,
        "observation_executed": FALSE_TOKEN,
        "observation_execution_authorized": FALSE_TOKEN,
        "observation_network_get_authorized": FALSE_TOKEN,
        "event_acquisition_network_get_authorized": FALSE_TOKEN,
        "account_composition_observation_defined": TRUE_TOKEN,
        "liability_observation_defined": TRUE_TOKEN,
        "fee_embedding_observation_defined": TRUE_TOKEN,
        "exogenous_event_coverage_observation_defined": TRUE_TOKEN,
        "observation_is_not_source_authority": TRUE_TOKEN,
        "observation_is_not_kind_ratification": TRUE_TOKEN,
        "observation_is_not_ms2_release": TRUE_TOKEN,
        "observation_is_not_d7_authorization": TRUE_TOKEN,
        "observation_is_not_raw_eq_source_authority": TRUE_TOKEN,
        "observation_is_not_completeness_unless_range_ordering_provenance_proven": (TRUE_TOKEN),
        "u05_kind_decision": DECISION_REMAIN_UNKNOWN,
        "u06_kind_decision": DECISION_REMAIN_UNKNOWN,
        "residual_kind_decision": DECISION_REMAIN_UNKNOWN,
        "ratified_classified_event_kind_set": "EMPTY_FAIL_CLOSED",
        "kind_set_resolved": FALSE_TOKEN,
        "ms1_kind_set_fully_closed": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "d6_fully_closed": FALSE_TOKEN,
        "d7_authorized": FALSE_TOKEN,
        "path_a": PATH_A_REJECT,
        "path_b": PATH_B_SELECTED_BUT_BLOCKED,
        "path_c": PATH_C_REJECT,
        "candidate_surface_selection": SELECTION_NONE,
        "account_bills_atlas_authority": ATLAS_AUTHORITY_NONE,
        "paper_simulated_fee_accounting_is_non_venue_evidence": TRUE_TOKEN,
        "c01_rehabilitation_forbidden": TRUE_TOKEN,
        "earliest_d6_kind_set_dependency": EARLIEST_D6_KIND_SET_DEPENDENCY,
        "authority_effect": AUTHORITY_EFFECT,
        "hypothesis_classes_not_ratified": HYPOTHESIS_CLASSES_NOT_RATIFIED,
    }
    return ScopedReadOnlyObservationBoundaryContractV1(
        persist_id=persist,
        observation_boundary_contract_status=payload["observation_boundary_contract_status"],
        observation_executed=payload["observation_executed"],
        observation_execution_authorized=payload["observation_execution_authorized"],
        observation_network_get_authorized=payload["observation_network_get_authorized"],
        event_acquisition_network_get_authorized=payload[
            "event_acquisition_network_get_authorized"
        ],
        account_composition_observation_defined=payload["account_composition_observation_defined"],
        liability_observation_defined=payload["liability_observation_defined"],
        fee_embedding_observation_defined=payload["fee_embedding_observation_defined"],
        exogenous_event_coverage_observation_defined=payload[
            "exogenous_event_coverage_observation_defined"
        ],
        observation_is_not_source_authority=payload["observation_is_not_source_authority"],
        observation_is_not_kind_ratification=payload["observation_is_not_kind_ratification"],
        observation_is_not_ms2_release=payload["observation_is_not_ms2_release"],
        observation_is_not_d7_authorization=payload["observation_is_not_d7_authorization"],
        observation_is_not_raw_eq_source_authority=payload[
            "observation_is_not_raw_eq_source_authority"
        ],
        observation_is_not_completeness_unless_range_ordering_provenance_proven=(
            payload["observation_is_not_completeness_unless_range_ordering_provenance_proven"]
        ),
        u05_kind_decision=payload["u05_kind_decision"],
        u06_kind_decision=payload["u06_kind_decision"],
        residual_kind_decision=payload["residual_kind_decision"],
        ratified_classified_event_kind_set=payload["ratified_classified_event_kind_set"],
        kind_set_resolved=payload["kind_set_resolved"],
        ms1_kind_set_fully_closed=payload["ms1_kind_set_fully_closed"],
        ms2_authorized=payload["ms2_authorized"],
        d6_fully_closed=payload["d6_fully_closed"],
        d7_authorized=payload["d7_authorized"],
        path_a=payload["path_a"],
        path_b=payload["path_b"],
        path_c=payload["path_c"],
        candidate_surface_selection=payload["candidate_surface_selection"],
        account_bills_atlas_authority=payload["account_bills_atlas_authority"],
        paper_simulated_fee_accounting_is_non_venue_evidence=payload[
            "paper_simulated_fee_accounting_is_non_venue_evidence"
        ],
        c01_rehabilitation_forbidden=payload["c01_rehabilitation_forbidden"],
        earliest_d6_kind_set_dependency=payload["earliest_d6_kind_set_dependency"],
        authority_effect=payload["authority_effect"],
        provenance_digest=compute_observation_boundary_digest_v1(payload),
    )
