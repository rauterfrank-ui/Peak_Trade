"""D6 classified event-kind set and event-source seam census.

Forensic inventory plus fail-closed adjudication. Does not invent
classified kinds. Does not ratify an empty set as zero necessary
events. An event-kind source-seam binding is not Equity Source
Authority, not RAW_EQ_SOURCE_AUTHORITY, and not MAPPING_PROVEN.
No venue GET. Not reconstruction. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractError,
    assert_same_bound_account_identity_v1,
    require_bound_account_identity_ref_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED,
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    EVENT_KIND_SOURCE_BINDING_IS_NOT_EQUITY_SOURCE_AUTHORITY,
    EVENT_KIND_SOURCE_BINDING_IS_NOT_MAPPING_PROVEN,
    EVENT_KIND_SOURCE_BINDING_IS_NOT_RAW_EQ_SOURCE_AUTHORITY,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    GAP_DETECTION_FAIL_CLOSED,
    IDEMPOTENCY_REPLAY_IDENTITY_PROVEN,
    KIND_SET_RESOLVED,
    ORDERING_PROVEN,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_COVERAGE_COMPLETE,
    SOURCE_SELECTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    CLASSIFICATION_STATUS_UNCLASSIFIED,
    CLASSIFICATION_STATUS_UNKNOWN,
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_v1 import (
    C01_C16_IDS,
)

SCHEMA_CLASS = "CLASSIFIED_EVENT_KIND_SET_AND_SOURCE_SEAM_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
LAYER_CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
LAYER_FORENSIC_RAW = "FORENSIC_RAW"
LAYER_ADJUDICATED = "ADJUDICATED"
LAYER_HISTORICAL = "HISTORICAL_INTERMEDIATE"
LAYER_NAVIGATION = "NAVIGATION"
LAYER_HYPOTHESIS = "INTERPRETATION_HYPOTHESIS_UNKNOWN"
DISPOSITION_EXCLUDED = "EXCLUDED_FROM_CLASSIFIED_KIND_SET"
DISPOSITION_UNKNOWN = "UNKNOWN_UNCLASSIFIED_FAIL_CLOSED"
DISPOSITION_NOT_EVENT_KIND = "NOT_AN_EVENT_KIND"
DISPOSITION_NOT_EQUITY_STOCK = "NOT_EQUITY_STOCK_AFFECTING"
DISPOSITION_C01_C16_FORBIDDEN = "C01_C16_NOT_EVENT_TAXONOMY"
DISPOSITION_SEAM_NOT_AUTHORIZED = "NOT_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM"
BINDING_STATUS_FAIL_CLOSED = "FAIL_CLOSED_UNBOUND"
EQUITY_VALUE_STATE_ABSENT = "ABSENT"
EQUITY_MUTATION_NOT_MUTATED = "NOT_MUTATED"
RATIFIED_CLASSIFIED_EVENT_KIND_SET_TOKEN = "EMPTY_FAIL_CLOSED"
MISSING_KIND_SET_AND_SOURCE_SEAM = (
    "RATIFIED_CLASSIFIED_EVENT_KIND_SET_AND_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM"
)
_FAIL_CLOSED_KIND_TOKENS: Tuple[str, ...] = (
    CLASSIFICATION_STATUS_UNKNOWN,
    CLASSIFICATION_STATUS_UNCLASSIFIED,
    "MISSING",
    "UNSPECIFIED",
    "UNPROVEN",
)
_FORBIDDEN_EQUITY_CLAIM_MARKERS: Tuple[str, ...] = (
    "equity_stock",
    "running_account_equity",
    "available_for_sizing",
    "reconstructed_equity",
    "totaleq",
    "availeq",
    "adjeq",
    "availbal",
    "cashbal",
)
_SILENT_ZERO_MARKERS: Tuple[str, ...] = (
    "0",
    "0.0",
    "zero",
    "no-op",
    "noop",
    "ignore",
    "omit",
)


class ClassifiedEventKindSetAndSourceSeamContractError(ValueError):
    """Fail-closed classified kind-set / source-seam contract violation."""


@dataclass(frozen=True)
class EventKindCensusFindingV1:
    finding_id: str
    layer: str
    candidate_id: str
    semantic_identity: str
    equity_stock_affecting_status: str
    authoritative_producer: str
    required_provenance: str
    bound_account_identity_semantics: str
    ordering_requirement: str
    duplicate_idempotency_replay_semantics: str
    inclusion_exclusion_rationale: str
    disposition: str
    evidence_refs: str


@dataclass(frozen=True)
class EventSourceSeamCensusFindingV1:
    finding_id: str
    layer: str
    seam_id: str
    existing_authority: str
    bound_account_identity_status: str
    event_identity_provenance: str
    range_cursor_ordering_semantics: str
    gap_duplicate_detection: str
    replay_idempotency: str
    complete_acquisition_possible: str
    disposition: str
    evidence_refs: str


@dataclass(frozen=True)
class ClassifiedEventKindSetAdjudicationV1:
    census_id: str
    ratified_classified_event_kind_set: str
    kind_set_resolved: str
    included_classified_kinds: str
    excluded_candidate_ids: str
    unknown_necessary_class_remains: str
    absence_is_not_zero_events: str
    event_kind_inclusion_exclusion_proven: str
    authorized_productive_event_source_seam_present: str
    source_coverage_complete: str
    ordering_proven: str
    gap_detection_fail_closed: str
    idempotency_replay_identity_proven: str
    d6_completeness_preconditions_proven: str
    complete_event_stream_proven: str
    event_kind_source_seam_selected: str
    raw_eq_source_authority: str
    source_selected: str
    mapping_proven: str
    c17_created: str
    reconstruction_engine_created: str
    reconstructed_equity_created: str
    missing_completeness_dependency: str
    authority_effect: str
    provenance_digest: str


@dataclass(frozen=True)
class ClassifiedEventKindSourceBindingAttemptV1:
    binding_id: str
    event_kind: str
    source_seam_id: str
    bound_account_identity_ref: str
    bound_account_identity_digest: str
    binding_status: str
    event_kind_source_seam_selected: str
    equity_stock_mutation_status: str
    claimed_equity_stock_value: str
    raw_eq_source_authority: str
    source_selected: str
    mapping_proven: str
    authority_effect: str
    provenance_digest: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_kind_set_and_source_seam_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise ClassifiedEventKindSetAndSourceSeamContractError(f"KIND_SET_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise ClassifiedEventKindSetAndSourceSeamContractError(f"KIND_SET_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise ClassifiedEventKindSetAndSourceSeamContractError(f"KIND_SET_FIELD_MISSING:{field}")
    return text


def _assert_shared_pins() -> None:
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise ClassifiedEventKindSetAndSourceSeamContractError("KIND_SET_AUTHORITY_OWNER_MUTATED")
    if KIND_SET_RESOLVED is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "TAXONOMY_KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "CLASSIFIED_KIND_SET_MUST_REMAIN_EMPTY_FAIL_CLOSED"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_NOT_ABSENT"
        )
    if SOURCE_COVERAGE_COMPLETE is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError("SOURCE_COVERAGE_COMPLETE_NOT_FALSE")
    if ORDERING_PROVEN is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError("ORDERING_PROVEN_NOT_FALSE")
    if GAP_DETECTION_FAIL_CLOSED is not True:
        raise ClassifiedEventKindSetAndSourceSeamContractError("GAP_DETECTION_FAIL_CLOSED_NOT_TRUE")
    if IDEMPOTENCY_REPLAY_IDENTITY_PROVEN is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "IDEMPOTENCY_REPLAY_IDENTITY_PROVEN_NOT_FALSE"
        )
    if D6_COMPLETENESS_PRECONDITIONS_PROVEN is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "D6_COMPLETENESS_PRECONDITIONS_PROVEN_NOT_FALSE"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "COMPLETE_EVENT_STREAM_PROVEN_NOT_FALSE"
        )
    if EVENT_KIND_SOURCE_SEAM_SELECTED is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_SEAM_SELECTED_NOT_FALSE"
        )
    if EVENT_KIND_SOURCE_BINDING_IS_NOT_EQUITY_SOURCE_AUTHORITY is not True:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_BINDING_COLLIDED_WITH_EQUITY_SOURCE_AUTHORITY"
        )
    if EVENT_KIND_SOURCE_BINDING_IS_NOT_RAW_EQ_SOURCE_AUTHORITY is not True:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_BINDING_COLLIDED_WITH_RAW_EQ_SOURCE_AUTHORITY"
        )
    if EVENT_KIND_SOURCE_BINDING_IS_NOT_MAPPING_PROVEN is not True:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_BINDING_COLLIDED_WITH_MAPPING_PROVEN"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if SOURCE_SELECTED is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError("SOURCE_SELECTED_NOT_FALSE")
    if CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is True:
        raise ClassifiedEventKindSetAndSourceSeamContractError("MAPPING_CLOSURE_CONSUMED_REEXECUTE_FORBIDDEN")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError("MAPPING_PROVEN_NOT_FALSE")
    if C17_CREATED is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError("C17_CREATED_NOT_FALSE")
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE"
        )
    if len(C01_C16_IDS) != 16:
        raise ClassifiedEventKindSetAndSourceSeamContractError("C01_C16_IDENTITY_DRIFT")


def _kind_finding(
    *,
    finding_id: str,
    layer: str,
    candidate_id: str,
    semantic_identity: str,
    equity_stock_affecting_status: str,
    authoritative_producer: str,
    required_provenance: str,
    bound_account_identity_semantics: str,
    ordering_requirement: str,
    duplicate_idempotency_replay_semantics: str,
    inclusion_exclusion_rationale: str,
    disposition: str,
    evidence_refs: str,
) -> EventKindCensusFindingV1:
    return EventKindCensusFindingV1(
        finding_id=finding_id,
        layer=layer,
        candidate_id=candidate_id,
        semantic_identity=semantic_identity,
        equity_stock_affecting_status=equity_stock_affecting_status,
        authoritative_producer=authoritative_producer,
        required_provenance=required_provenance,
        bound_account_identity_semantics=bound_account_identity_semantics,
        ordering_requirement=ordering_requirement,
        duplicate_idempotency_replay_semantics=duplicate_idempotency_replay_semantics,
        inclusion_exclusion_rationale=inclusion_exclusion_rationale,
        disposition=disposition,
        evidence_refs=evidence_refs,
    )


def _seam_finding(
    *,
    finding_id: str,
    layer: str,
    seam_id: str,
    existing_authority: str,
    bound_account_identity_status: str,
    event_identity_provenance: str,
    range_cursor_ordering_semantics: str,
    gap_duplicate_detection: str,
    replay_idempotency: str,
    complete_acquisition_possible: str,
    disposition: str,
    evidence_refs: str,
) -> EventSourceSeamCensusFindingV1:
    return EventSourceSeamCensusFindingV1(
        finding_id=finding_id,
        layer=layer,
        seam_id=seam_id,
        existing_authority=existing_authority,
        bound_account_identity_status=bound_account_identity_status,
        event_identity_provenance=event_identity_provenance,
        range_cursor_ordering_semantics=range_cursor_ordering_semantics,
        gap_duplicate_detection=gap_duplicate_detection,
        replay_idempotency=replay_idempotency,
        complete_acquisition_possible=complete_acquisition_possible,
        disposition=disposition,
        evidence_refs=evidence_refs,
    )


def build_forensic_event_kind_census_findings_v1() -> Tuple[EventKindCensusFindingV1, ...]:
    _assert_shared_pins()
    runbook = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
    taxonomy = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "equity_affecting_event_taxonomy_contract_v1.py"
    )
    algebra = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "reconstruction_algebra_contract_v1.py"
    )
    census = (
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "source_candidate_census_v1.py"
    )
    return (
        _kind_finding(
            finding_id="EK01_UNKNOWN_REPRESENTABLE",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="UNKNOWN",
            semantic_identity="TAXONOMY_UNKNOWN_STATUS_AND_CLASS",
            equity_stock_affecting_status="RECONSTRUCTION_INVALID_NOT_CLASSIFIED",
            authoritative_producer="ops.governed_productive_account_equity_authority_producer_v1",
            required_provenance="event_digest+bound_account_identity_ref",
            bound_account_identity_semantics="D4_REFERENCE_BINDING_REQUIRED",
            ordering_requirement="PRESENT_BUT_NOT_RECONSTRUCTION_VALID",
            duplicate_idempotency_replay_semantics="FAIL_CLOSED_NOT_ZERO",
            inclusion_exclusion_rationale="UNKNOWN remains representable and must not map to zero/no-op",
            disposition=DISPOSITION_UNKNOWN,
            evidence_refs=f"{runbook}#11.2.1.AR;{taxonomy}",
        ),
        _kind_finding(
            finding_id="EK02_UNCLASSIFIED_REPRESENTABLE",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="UNCLASSIFIED",
            semantic_identity="TAXONOMY_UNCLASSIFIED_STATUS_AND_CLASS",
            equity_stock_affecting_status="RECONSTRUCTION_INVALID_NOT_CLASSIFIED",
            authoritative_producer="ops.governed_productive_account_equity_authority_producer_v1",
            required_provenance="event_digest+bound_account_identity_ref",
            bound_account_identity_semantics="D4_REFERENCE_BINDING_REQUIRED",
            ordering_requirement="PRESENT_BUT_NOT_RECONSTRUCTION_VALID",
            duplicate_idempotency_replay_semantics="FAIL_CLOSED_NOT_ZERO",
            inclusion_exclusion_rationale="UNCLASSIFIED remains representable and must not map to zero/no-op",
            disposition=DISPOSITION_UNKNOWN,
            evidence_refs=f"{runbook}#11.2.1.AR;{taxonomy}",
        ),
        _kind_finding(
            finding_id="EK03_UNRATIFIED_FILL_TOKEN",
            layer=LAYER_FORENSIC_RAW,
            candidate_id="FILL",
            semantic_identity="TEST_ONLY_UNRATIFIED_CLASSIFIED_TOKEN",
            equity_stock_affecting_status="UNPROVEN_AS_EQUITY_STOCK_CLASSIFIED_KIND",
            authoritative_producer="NONE_FOR_D6_EQUITY_STOCK",
            required_provenance="UNPROVEN",
            bound_account_identity_semantics="NOT_A_RATIFIED_KIND",
            ordering_requirement="UNPROVEN",
            duplicate_idempotency_replay_semantics="UNPROVEN",
            inclusion_exclusion_rationale="FILL appears only as an unratified test token; CLASSIFIED_KIND_NOT_RATIFIED",
            disposition=DISPOSITION_EXCLUDED,
            evidence_refs=(
                f"tests/ops/test_full_core_d6_classified_event_stream_acquisition_v1.py;{taxonomy}"
            ),
        ),
        _kind_finding(
            finding_id="EK04_ALGEBRA_U02_REALIZED_PNL",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="U02_REALIZED_PNL",
            semantic_identity="RECONSTRUCTION_ALGEBRA_TERM_NOT_EVENT_KIND",
            equity_stock_affecting_status="EMBEDDED_IN_AVAILABLE_FOR_SIZING_BASE_NOT_EVENT_CLASS",
            authoritative_producer="NONE_AS_EVENT_KIND",
            required_provenance="NOT_AN_EVENT_KIND",
            bound_account_identity_semantics="NOT_APPLICABLE_AS_EVENT_KIND",
            ordering_requirement="NOT_AN_EVENT_KIND",
            duplicate_idempotency_replay_semantics="NOT_AN_EVENT_KIND",
            inclusion_exclusion_rationale="Algebra term is not a classified EQUITY_STOCK event kind",
            disposition=DISPOSITION_NOT_EVENT_KIND,
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
        ),
        _kind_finding(
            finding_id="EK05_ALGEBRA_U03_UNREALIZED_MTM",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="U03_UNREALIZED_PNL_MTM",
            semantic_identity="RECONSTRUCTION_ALGEBRA_TERM_NOT_EVENT_KIND",
            equity_stock_affecting_status="EMBEDDED_IN_AVAILABLE_FOR_SIZING_BASE_NOT_EVENT_CLASS",
            authoritative_producer="NONE_AS_EVENT_KIND",
            required_provenance="NOT_AN_EVENT_KIND",
            bound_account_identity_semantics="NOT_APPLICABLE_AS_EVENT_KIND",
            ordering_requirement="NOT_AN_EVENT_KIND",
            duplicate_idempotency_replay_semantics="NOT_AN_EVENT_KIND",
            inclusion_exclusion_rationale="MTM algebra term is not a classified EQUITY_STOCK event kind",
            disposition=DISPOSITION_NOT_EVENT_KIND,
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
        ),
        _kind_finding(
            finding_id="EK06_ALGEBRA_U04_PENDING_ORDER",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="U04_PENDING_ORDER_RESERVATION",
            semantic_identity="AVAILABLE_FOR_SIZING_OR_RISK_SIZING_NOT_EQUITY_STOCK",
            equity_stock_affecting_status="EXPLICITLY_NOT_EQUITY_STOCK",
            authoritative_producer="NONE_AS_EQUITY_STOCK_EVENT_KIND",
            required_provenance="NOT_EQUITY_STOCK",
            bound_account_identity_semantics="NOT_APPLICABLE_AS_EQUITY_STOCK_EVENT",
            ordering_requirement="NOT_EQUITY_STOCK_EVENT",
            duplicate_idempotency_replay_semantics="NOT_EQUITY_STOCK_EVENT",
            inclusion_exclusion_rationale="U04 belongs to AVAILABLE_FOR_SIZING / RISK-SIZING, not EQUITY_STOCK",
            disposition=DISPOSITION_NOT_EQUITY_STOCK,
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
        ),
        _kind_finding(
            finding_id="EK07_ALGEBRA_U05_LIABILITY",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="U05_LIABILITY",
            semantic_identity="CONDITIONAL_EQUITY_STOCK_IF_GENUINE_BORROW_NOT_EMBEDDED",
            equity_stock_affecting_status="UNRESOLVED_CONDITIONAL_NOT_RATIFIED_KIND",
            authoritative_producer="NONE_AS_CLASSIFIED_EVENT_KIND",
            required_provenance="UNPROVEN",
            bound_account_identity_semantics="UNPROVEN_AS_EVENT_KIND",
            ordering_requirement="UNPROVEN",
            duplicate_idempotency_replay_semantics="UNPROVEN",
            inclusion_exclusion_rationale="U05 placement is not a ratified classified event kind; inclusion remains unresolved",
            disposition=DISPOSITION_UNKNOWN,
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
        ),
        _kind_finding(
            finding_id="EK08_ALGEBRA_U06_FEE",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="U06_FEE",
            semantic_identity="EVENT_OR_RECONCILIATION_DIMENSION_NOT_BLIND_SUBTRACTION",
            equity_stock_affecting_status="PLACEMENT_IS_NOT_KIND_RATIFICATION",
            authoritative_producer="NONE_AS_CLASSIFIED_EVENT_KIND",
            required_provenance="UNPROVEN",
            bound_account_identity_semantics="UNPROVEN_AS_EVENT_KIND",
            ordering_requirement="UNPROVEN",
            duplicate_idempotency_replay_semantics="UNPROVEN",
            inclusion_exclusion_rationale="U06_PLACEMENT does not ratify a classified FEE event kind",
            disposition=DISPOSITION_UNKNOWN,
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
        ),
        _kind_finding(
            finding_id="EK09_P01_REDUCTION",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="P01_GOVERNED_RISK_CAPITAL_REDUCTION",
            semantic_identity="AFTER_EQUITY_RISK_CAPITAL_REDUCTION_NOT_IN_SOURCE",
            equity_stock_affecting_status="EXPLICITLY_NOT_EQUITY_SOURCE_OR_EVENT_KIND",
            authoritative_producer="NONE_AS_EQUITY_STOCK_EVENT_KIND",
            required_provenance="NOT_EQUITY_SOURCE",
            bound_account_identity_semantics="NOT_APPLICABLE_AS_EQUITY_STOCK_EVENT",
            ordering_requirement="NOT_EQUITY_STOCK_EVENT",
            duplicate_idempotency_replay_semantics="NOT_EQUITY_STOCK_EVENT",
            inclusion_exclusion_rationale="P01 is never an equity source and is not a classified EQUITY_STOCK event kind",
            disposition=DISPOSITION_NOT_EQUITY_STOCK,
            evidence_refs=f"{runbook}#11.2.1.AR;{algebra}",
        ),
        _kind_finding(
            finding_id="EK10_C01_C16_NOT_TAXONOMY",
            layer=LAYER_CANONICAL_AUTHORITY,
            candidate_id="C01_THROUGH_C16",
            semantic_identity="REJECTED_EQUITY_SOURCE_CANDIDATES_NOT_EVENT_KINDS",
            equity_stock_affecting_status="FORBIDDEN_AS_EVENT_TAXONOMY",
            authoritative_producer="NONE_FOR_29P_EQUITY_AUTHORITY",
            required_provenance="C01_C16_REJECTION_STILL_BINDING",
            bound_account_identity_semantics="NOT_EVENT_KIND_IDENTITY",
            ordering_requirement="NOT_EVENT_KIND",
            duplicate_idempotency_replay_semantics="NOT_EVENT_KIND",
            inclusion_exclusion_rationale="C01-C16 must not be reused as classified event taxonomy",
            disposition=DISPOSITION_C01_C16_FORBIDDEN,
            evidence_refs=f"{runbook}#11.2.1.S;{census}",
        ),
        _kind_finding(
            finding_id="EK11_EXECUTION_LEDGER_FILL_MARK",
            layer=LAYER_FORENSIC_RAW,
            candidate_id="EXECUTION_LEDGER_FILL_OR_MARK",
            semantic_identity="INTERNAL_EXECUTION_LEDGER_EVENT_NOT_D6_KIND",
            equity_stock_affecting_status="UNPROVEN_AND_C10_C11_C16_CLASS_RISK",
            authoritative_producer="src.execution.ledger.engine",
            required_provenance="NOT_D6_EQUITY_STOCK_AUTHORITY",
            bound_account_identity_semantics="NOT_D4_EQUITY_STOCK_EVENT_IDENTITY",
            ordering_requirement="LEDGER_LOCAL_NOT_D6_STREAM",
            duplicate_idempotency_replay_semantics="LEDGER_LOCAL_NOT_D6_STREAM",
            inclusion_exclusion_rationale="Execution-ledger FILL/MARK is not a ratified D6 EQUITY_STOCK classified kind",
            disposition=DISPOSITION_EXCLUDED,
            evidence_refs="src/execution/ledger/engine.py;src/execution/ledger/export.py",
        ),
        _kind_finding(
            finding_id="EK12_NECESSARY_CLASS_REMAINS_UNKNOWN",
            layer=LAYER_HYPOTHESIS,
            candidate_id="UNKNOWN_NECESSARY_EQUITY_STOCK_EVENT_CLASS",
            semantic_identity="NO_CANONICALLY_PROVEN_COMPLETE_NECESSARY_KIND_SET",
            equity_stock_affecting_status="UNKNOWN_FAIL_CLOSED",
            authoritative_producer="NONE",
            required_provenance="UNPROVEN",
            bound_account_identity_semantics="UNPROVEN",
            ordering_requirement="UNPROVEN",
            duplicate_idempotency_replay_semantics="UNPROVEN",
            inclusion_exclusion_rationale="Necessary EQUITY_STOCK-affecting classes remain unknown; empty set is not zero necessary kinds",
            disposition=DISPOSITION_UNKNOWN,
            evidence_refs=f"{runbook}#11.2.1.AU;{taxonomy}",
        ),
    )


def build_forensic_event_source_seam_census_findings_v1() -> Tuple[
    EventSourceSeamCensusFindingV1, ...
]:
    _assert_shared_pins()
    runbook = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
    return (
        _seam_finding(
            finding_id="ES01_TAXONOMY_SCHEMA",
            layer=LAYER_CANONICAL_AUTHORITY,
            seam_id="EQUITY_AFFECTING_EVENT_TAXONOMY_CONTRACT_V1",
            existing_authority="TYPED_SCHEMA_NOT_PRODUCER",
            bound_account_identity_status="SCHEMA_REQUIRES_D4_REF",
            event_identity_provenance="SCHEMA_ONLY",
            range_cursor_ordering_semantics="ORDERING_KEY_SCHEMA_ONLY",
            gap_duplicate_detection="FAIL_CLOSED_SCHEMA_ONLY",
            replay_idempotency="SCHEMA_ONLY",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_SEAM_NOT_AUTHORIZED,
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/"
                "equity_affecting_event_taxonomy_contract_v1.py"
            ),
        ),
        _seam_finding(
            finding_id="ES02_D6_TYPED_ACQUISITION",
            layer=LAYER_CANONICAL_AUTHORITY,
            seam_id="CLASSIFIED_EVENT_STREAM_ACQUISITION_CONTRACT_V1",
            existing_authority="TYPED_OFFLINE_ACQUISITION_NOT_PRODUCTIVE_GET",
            bound_account_identity_status="D4_REFERENCE_REQUIRED",
            event_identity_provenance="TYPED_OFFLINE_MEMBERS_ONLY",
            range_cursor_ordering_semantics="UNPROVEN",
            gap_duplicate_detection="FAIL_CLOSED_WITHOUT_SOURCE_PROOF",
            replay_idempotency="REPLAY_IDENTITY_SCHEMA_NOT_SOURCE_PROOF",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_SEAM_NOT_AUTHORIZED,
            evidence_refs=f"{runbook}#11.2.1.AU",
        ),
        _seam_finding(
            finding_id="ES03_OKX_ACCOUNT_BILLS",
            layer=LAYER_FORENSIC_RAW,
            seam_id="GET_/api/v5/account/bills",
            existing_authority="ATLAS_CURRENT_NONCANONICAL_AUTHORITY_NONE",
            bound_account_identity_status="NOT_D4_BOUND_FOR_D6",
            event_identity_provenance="UNPROVEN_AS_D6_EVENT_IDENTITY",
            range_cursor_ordering_semantics="UNPROVEN_FOR_D6",
            gap_duplicate_detection="UNPROVEN_FOR_D6",
            replay_idempotency="UNPROVEN_FOR_D6",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_SEAM_NOT_AUTHORIZED,
            evidence_refs=(
                "docs/system_atlas/venue/okx/endpoints.yaml;"
                "src/ops/section_11_13_5_p08_read_only_closure_v1/census_v1.py;"
                f"{runbook}#11.2.1.AU"
            ),
        ),
        _seam_finding(
            finding_id="ES04_OKX_TRADE_FILLS",
            layer=LAYER_FORENSIC_RAW,
            seam_id="GET_/api/v5/trade/fills",
            existing_authority="LIVE_HANDOFF_CANARY_FILL_EVIDENCE_NOT_D6",
            bound_account_identity_status="LIVE_SUBMIT_IDENTITY_NOT_D4_EQUITY_STOCK",
            event_identity_provenance="FILL_EVIDENCE_NOT_CLASSIFIED_EQUITY_STOCK_EVENT",
            range_cursor_ordering_semantics="ORDER_SCOPED_NOT_D6_STREAM",
            gap_duplicate_detection="NOT_D6_STREAM",
            replay_idempotency="NOT_D6_STREAM",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_SEAM_NOT_AUTHORIZED,
            evidence_refs=(
                f"{runbook}#11.2.1.AU;"
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "fill_observed_gets_v1.py"
            ),
        ),
        _seam_finding(
            finding_id="ES05_FRESH_PRETRADE_GET",
            layer=LAYER_CANONICAL_AUTHORITY,
            seam_id="FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1",
            existing_authority="TYPED_ADMISSION_EVIDENCE_NOT_D6_EVENT_SOURCE",
            bound_account_identity_status="NOT_D6_EVENT_IDENTITY",
            event_identity_provenance="NOT_EVENT_STREAM",
            range_cursor_ordering_semantics="NOT_EVENT_STREAM",
            gap_duplicate_detection="NOT_EVENT_STREAM",
            replay_idempotency="NOT_EVENT_STREAM",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_SEAM_NOT_AUTHORIZED,
            evidence_refs=f"{runbook}#11.2.1.AT;{runbook}#11.2.1.AU",
        ),
        _seam_finding(
            finding_id="ES06_C01_ACCOUNT_BALANCE",
            layer=LAYER_CANONICAL_AUTHORITY,
            seam_id="C01_Q_GET_PACK_DETAILS_AVAILEQ",
            existing_authority="REJECTED_C01_NOT_EVENT_SOURCE",
            bound_account_identity_status="NOT_D6_EVENT_IDENTITY",
            event_identity_provenance="BALANCE_OBSERVATION_NOT_EVENT",
            range_cursor_ordering_semantics="NOT_EVENT_STREAM",
            gap_duplicate_detection="NOT_EVENT_STREAM",
            replay_idempotency="NOT_EVENT_STREAM",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_C01_C16_FORBIDDEN,
            evidence_refs=f"{runbook}#11.2.1.S",
        ),
        _seam_finding(
            finding_id="ES07_C07_FUNDING_BALANCE",
            layer=LAYER_CANONICAL_AUTHORITY,
            seam_id="C07_FUNDING_ACCOUNT_BALANCE_OBSERVATION",
            existing_authority="REJECTED_C07_NOT_EVENT_SOURCE",
            bound_account_identity_status="NOT_D6_EVENT_IDENTITY",
            event_identity_provenance="FUNDING_BALANCE_NOT_EVENT",
            range_cursor_ordering_semantics="NOT_EVENT_STREAM",
            gap_duplicate_detection="NOT_EVENT_STREAM",
            replay_idempotency="NOT_EVENT_STREAM",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_C01_C16_FORBIDDEN,
            evidence_refs=(
                "src/ops/governed_productive_account_equity_authority_producer_v1/"
                "source_candidate_census_v1.py"
            ),
        ),
        _seam_finding(
            finding_id="ES08_C10_LEDGER_SNAPSHOT",
            layer=LAYER_CANONICAL_AUTHORITY,
            seam_id="C10_LEDGER_SNAPSHOT_EQUITY_BY_CCY",
            existing_authority="REJECTED_C10_NOT_EVENT_SOURCE",
            bound_account_identity_status="NOT_D6_EVENT_IDENTITY",
            event_identity_provenance="SNAPSHOT_NOT_EVENT_STREAM",
            range_cursor_ordering_semantics="SNAPSHOT_NOT_STREAM",
            gap_duplicate_detection="SNAPSHOT_NOT_STREAM",
            replay_idempotency="SNAPSHOT_NOT_STREAM",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_C01_C16_FORBIDDEN,
            evidence_refs=f"{runbook}#11.2.1.AU",
        ),
        _seam_finding(
            finding_id="ES09_CREDENTIAL_ENV_DEFAULT",
            layer=LAYER_CANONICAL_AUTHORITY,
            seam_id="CREDENTIAL_ENV_OR_IMPLICIT_DEFAULT_SOURCE",
            existing_authority="FORBIDDEN",
            bound_account_identity_status="FORBIDDEN_PROVENANCE",
            event_identity_provenance="FORBIDDEN",
            range_cursor_ordering_semantics="FORBIDDEN",
            gap_duplicate_detection="FAIL_CLOSED",
            replay_idempotency="FORBIDDEN",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_SEAM_NOT_AUTHORIZED,
            evidence_refs=f"{runbook}#11.2.1.AS;{runbook}#11.2.1.AU",
        ),
        _seam_finding(
            finding_id="ES10_EXECUTION_LEDGER",
            layer=LAYER_FORENSIC_RAW,
            seam_id="src.execution.ledger",
            existing_authority="INTERNAL_LEDGER_NOT_D6_EVENT_SOURCE",
            bound_account_identity_status="NOT_D4_EQUITY_STOCK_EVENT_IDENTITY",
            event_identity_provenance="LEDGER_LOCAL",
            range_cursor_ordering_semantics="LEDGER_LOCAL",
            gap_duplicate_detection="LEDGER_LOCAL",
            replay_idempotency="LEDGER_LOCAL",
            complete_acquisition_possible="false",
            disposition=DISPOSITION_SEAM_NOT_AUTHORIZED,
            evidence_refs="src/execution/ledger/engine.py",
        ),
    )


def build_classified_event_kind_set_adjudication_v1(
    *,
    census_id: str,
) -> ClassifiedEventKindSetAdjudicationV1:
    _assert_shared_pins()
    census = _require_non_empty_str(field="census_id", raw=census_id)
    kind_findings = build_forensic_event_kind_census_findings_v1()
    seam_findings = build_forensic_event_source_seam_census_findings_v1()
    excluded = ",".join(finding.candidate_id for finding in kind_findings)
    unknown_remains = any(finding.disposition == DISPOSITION_UNKNOWN for finding in kind_findings)
    authorized_seams = tuple(
        finding.seam_id
        for finding in seam_findings
        if finding.disposition != DISPOSITION_SEAM_NOT_AUTHORIZED
        and finding.disposition != DISPOSITION_C01_C16_FORBIDDEN
    )
    if unknown_remains is not True:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "UNKNOWN_NECESSARY_CLASS_MUST_REMAIN"
        )
    if authorized_seams:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    payload = {
        "census_id": census,
        "ratified_classified_event_kind_set": RATIFIED_CLASSIFIED_EVENT_KIND_SET_TOKEN,
        "kind_set_resolved": FALSE_TOKEN,
        "included_classified_kinds": "NONE_RATIFIED",
        "excluded_candidate_ids": excluded,
        "unknown_necessary_class_remains": TRUE_TOKEN,
        "absence_is_not_zero_events": TRUE_TOKEN,
        "event_kind_inclusion_exclusion_proven": TRUE_TOKEN,
        "authorized_productive_event_source_seam_present": FALSE_TOKEN,
        "source_coverage_complete": FALSE_TOKEN,
        "ordering_proven": FALSE_TOKEN,
        "gap_detection_fail_closed": TRUE_TOKEN,
        "idempotency_replay_identity_proven": FALSE_TOKEN,
        "d6_completeness_preconditions_proven": FALSE_TOKEN,
        "complete_event_stream_proven": FALSE_TOKEN,
        "event_kind_source_seam_selected": FALSE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "source_selected": FALSE_TOKEN,
        "mapping_proven": FALSE_TOKEN,
        "c17_created": FALSE_TOKEN,
        "reconstruction_engine_created": FALSE_TOKEN,
        "reconstructed_equity_created": FALSE_TOKEN,
        "missing_completeness_dependency": MISSING_KIND_SET_AND_SOURCE_SEAM,
        "authority_effect": AUTHORITY_EFFECT,
    }
    if payload["included_classified_kinds"] != "NONE_RATIFIED":
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "INCLUDED_CLASSIFIED_KINDS_MUST_REMAIN_NONE_RATIFIED"
        )
    digest = compute_kind_set_and_source_seam_digest_v1(payload)
    return ClassifiedEventKindSetAdjudicationV1(**payload, provenance_digest=digest)


def bind_classified_event_kind_to_authorized_source_seam_v1(
    *,
    binding_id: str,
    event_kind: str,
    source_seam_id: str,
    expected_bound_account_identity_ref: str,
    expected_bound_account_identity_digest: str,
    bound_account_identity_ref: str,
    bound_account_identity_digest: str,
    claimed_equity_stock_value: str = EQUITY_VALUE_STATE_ABSENT,
    equity_stock_mutation_status: str = EQUITY_MUTATION_NOT_MUTATED,
) -> ClassifiedEventKindSourceBindingAttemptV1:
    _assert_shared_pins()
    bind_id = _require_non_empty_str(field="binding_id", raw=binding_id)
    kind = _require_non_empty_str(field="event_kind", raw=event_kind)
    seam = _require_non_empty_str(field="source_seam_id", raw=source_seam_id)
    claimed = _require_non_empty_str(
        field="claimed_equity_stock_value", raw=claimed_equity_stock_value
    )
    mutation = _require_non_empty_str(
        field="equity_stock_mutation_status", raw=equity_stock_mutation_status
    )
    left_ref, left_digest = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=expected_bound_account_identity_ref,
        bound_account_identity_digest=expected_bound_account_identity_digest,
    )
    right_ref, right_digest = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=bound_account_identity_ref,
        bound_account_identity_digest=bound_account_identity_digest,
    )
    try:
        assert_same_bound_account_identity_v1(
            left_ref=left_ref,
            left_digest=left_digest,
            right_ref=right_ref,
            right_digest=right_digest,
        )
    except BoundAccountIdentityContractError as exc:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_IDENTITY_MISMATCH_CROSS_ACCOUNT"
        ) from exc
    if mutation != EQUITY_MUTATION_NOT_MUTATED:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_BINDING_CANNOT_MUTATE_EQUITY_STOCK"
        )
    if claimed.strip().lower() in _SILENT_ZERO_MARKERS:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_ABSENCE_IS_NOT_ZERO"
        )
    lowered = claimed.lower()
    if any(marker in lowered for marker in _FORBIDDEN_EQUITY_CLAIM_MARKERS):
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_BINDING_CANNOT_MINT_OR_OVERWRITE_EQUITY"
        )
    if claimed != EQUITY_VALUE_STATE_ABSENT:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_BINDING_CANNOT_MINT_OR_OVERWRITE_EQUITY"
        )
    if kind in _FAIL_CLOSED_KIND_TOKENS:
        raise ClassifiedEventKindSetAndSourceSeamContractError(f"EVENT_KIND_{kind}_FAIL_CLOSED")
    if seam in ("MISSING", "AMBIGUOUS", "PARTIAL", "UNSPECIFIED", "UNPROVEN"):
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            f"EVENT_KIND_SOURCE_{seam}_FAIL_CLOSED"
        )
    if kind not in RATIFIED_CLASSIFIED_KIND_SET or KIND_SET_RESOLVED is not True:
        raise ClassifiedEventKindSetAndSourceSeamContractError("CLASSIFIED_KIND_NOT_RATIFIED")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not True:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_MISSING_OR_UNAUTHORIZED_FAIL_CLOSED"
        )
    payload = {
        "binding_id": bind_id,
        "event_kind": kind,
        "source_seam_id": seam,
        "bound_account_identity_ref": right_ref,
        "bound_account_identity_digest": right_digest,
        "binding_status": BINDING_STATUS_FAIL_CLOSED,
        "event_kind_source_seam_selected": FALSE_TOKEN,
        "equity_stock_mutation_status": mutation,
        "claimed_equity_stock_value": claimed,
        "raw_eq_source_authority": FALSE_TOKEN,
        "source_selected": FALSE_TOKEN,
        "mapping_proven": FALSE_TOKEN,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = compute_kind_set_and_source_seam_digest_v1(payload)
    return ClassifiedEventKindSourceBindingAttemptV1(**payload, provenance_digest=digest)


def adjudicate_event_source_range_order_and_duplicate_v1(
    *,
    gap_detected: str,
    ordering_proven: str,
    duplicate_detected: str,
) -> None:
    _assert_shared_pins()
    gap = _require_non_empty_str(field="gap_detected", raw=gap_detected)
    ordering = _require_non_empty_str(field="ordering_proven", raw=ordering_proven)
    duplicate = _require_non_empty_str(field="duplicate_detected", raw=duplicate_detected)
    if gap in ("GAP", "MISSING"):
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_RANGE_GAP_FAIL_CLOSED"
        )
    if ordering in (TRUE_TOKEN, "true", "PROVEN"):
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_ORDERING_NOT_PROVEN"
        )
    if duplicate in (TRUE_TOKEN, "true", "DUPLICATE"):
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_DUPLICATE_FAIL_CLOSED"
        )
    if ordering != FALSE_TOKEN:
        raise ClassifiedEventKindSetAndSourceSeamContractError(
            "EVENT_KIND_SOURCE_ORDER_AMBIGUITY_FAIL_CLOSED"
        )
