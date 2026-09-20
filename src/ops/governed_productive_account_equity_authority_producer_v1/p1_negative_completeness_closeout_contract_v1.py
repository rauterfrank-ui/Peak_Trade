"""P1 negative / completeness closeout contract (offline evaluator only).

Defines P1 positive vs negative vs does-not-apply vs unknown semantics and
evaluates sealed interest-accrued observations fail-closed. Does not GET.
Does not mint liability absence from empty rows alone. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    EMPTY_ROWS_PROVE_KIND_ABSENCE,
    EMPTY_ROWS_PROVE_ZERO_EVENTS,
    PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
    RAW_EQ_SOURCE_AUTHORITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)

SCHEMA_CLASS = "P1_NEGATIVE_COMPLETENESS_CLOSEOUT_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
WP_ID = "FULL_CORE_U05_P1_NEGATIVE_COMPLETENESS_CLOSEOUT_CONTRACT_TO_FIRST_HARD_BLOCKER_V1"

TRUE_TOKEN = "true"
FALSE_TOKEN = "false"

P1_CLOSEOUT_PROVEN_NEGATIVE = "PROVEN_NEGATIVE"
P1_CLOSEOUT_DOES_NOT_APPLY = "DOES_NOT_APPLY"
P1_CLOSEOUT_UNKNOWN = "UNKNOWN"
P1_CLOSEOUT_CONFLICTED = "CONFLICTED"

P1_STATUS_PROVEN = "PROVEN"
P1_STATUS_PROVEN_FALSE = "PROVEN_FALSE"
P1_STATUS_DOES_NOT_APPLY = "DOES_NOT_APPLY"
P1_STATUS_UNKNOWN = "UNKNOWN"

ZERO_ROWS_ALONE_MAY_PROVE_NEGATIVE = False

P1_SEMANTIC_DOMAIN = "INDEPENDENT_QUALIFYING_LIABILITY_EVENT_EXISTENCE_FOR_U05_P1_SLOT"
P1_APPLICABILITY_DOMAIN = (
    "FUTURES_MODE_BOUND_PRODUCTIVE_ACCOUNT_INDEPENDENT_LIABILITY_EVENT_HISTORY"
    "_SURFACE_INTEREST_ACCRUED_TYPE2_NOT_SPOT_ONLY_INCAPABLE_SURFACES"
)

P1_POSITIVE_SEMANTICS = (
    "AT_LEAST_ONE_CB_QUALIFYING_INDEPENDENT_LIABILITY_EVENT_ROW_ON_BOUND_P1_SURFACE"
)
P1_NEGATIVE_SEMANTICS = "GOVERNED_OBSERVATION_DOMAIN_COMPLETE_AND_ZERO_QUALIFYING_LIABILITY_EVENTS"
P1_DOES_NOT_APPLY_SEMANTICS = (
    "EXPLICIT_APPLICABILITY_PREDICATE_PROVES_ACCOUNT_OR_SURFACE_OUTSIDE_P1_DOMAIN"
)
P1_UNKNOWN_SEMANTICS = "NONE_OF_POSITIVE_NEGATIVE_OR_DOES_NOT_APPLY_INDEPENDENTLY_PROVEN"

REQUIREMENT_ACCOUNT_IDENTITY = "ACCOUNT_IDENTITY_COMPLETE"
REQUIREMENT_ACCOUNT_MODE = "ACCOUNT_MODE_COMPLETE"
REQUIREMENT_VENUE = "VENUE_COMPLETE"
REQUIREMENT_CURRENCY_DOMAIN = "CURRENCY_DOMAIN_COMPLETE"
REQUIREMENT_LIABILITY_EVENT_CLASS = "LIABILITY_EVENT_CLASS_COMPLETE"
REQUIREMENT_TIME_DOMAIN = "TIME_DOMAIN_COMPLETE"
REQUIREMENT_SURFACE_COVERAGE = "SURFACE_COVERAGE_COMPLETE"
REQUIREMENT_PAGINATION = "PAGINATION_COMPLETE"
REQUIREMENT_EVENT_ORDERING = "EVENT_ORDERING_COMPLETE"
REQUIREMENT_OBSERVATION_FRESHNESS = "OBSERVATION_FRESHNESS_COMPLETE"
REQUIREMENT_RESTART_DURABILITY = "RESTART_DURABILITY_COMPLETE"
REQUIREMENT_INDEPENDENCE_BALANCE = "INDEPENDENCE_FROM_BALANCE_SNAPSHOT"
REQUIREMENT_INDEPENDENCE_RAW_EQ = "INDEPENDENCE_FROM_RAW_EQ"
REQUIREMENT_PROVENANCE = "PROVENANCE_COMPLETE"

COMPLETENESS_REQUIREMENT_ORDER: tuple[str, ...] = (
    REQUIREMENT_ACCOUNT_IDENTITY,
    REQUIREMENT_ACCOUNT_MODE,
    REQUIREMENT_VENUE,
    REQUIREMENT_CURRENCY_DOMAIN,
    REQUIREMENT_LIABILITY_EVENT_CLASS,
    REQUIREMENT_TIME_DOMAIN,
    REQUIREMENT_SURFACE_COVERAGE,
    REQUIREMENT_PAGINATION,
    REQUIREMENT_EVENT_ORDERING,
    REQUIREMENT_OBSERVATION_FRESHNESS,
    REQUIREMENT_RESTART_DURABILITY,
    REQUIREMENT_INDEPENDENCE_BALANCE,
    REQUIREMENT_INDEPENDENCE_RAW_EQ,
    REQUIREMENT_PROVENANCE,
)

CANONICAL_CD_PACK = (
    "evidence/ops/full_core_u05_primary_proof_bound_interest_accrued_get_acquisition_v1/"
    "2026-09-15T010500Z"
)
CANONICAL_USDC_P1_PACK = (
    "evidence/ops/full_core_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1/"
    "2026-09-20T233000Z"
)
CANONICAL_U01_PACK = (
    "evidence/ops/full_core_current_productive_u01_account_mode_semantic_ratification_v1/"
    "20260915T113345Z"
)
EXPECTED_D4_IDENTITY_DIGEST = "00c354f2d247f5a64e33efb31f8be155b8557e847868335ccb15cd4f7ca9d7c4"


class P1NegativeCompletenessCloseoutError(ValueError):
    """Fail-closed P1 negative completeness contract violation."""


@dataclass(frozen=True)
class P1NegativeCompletenessInputV1:
    qualifying_event_count: int
    nonqualifying_event_count: int
    cd_row_count: int
    usdc_scoped_row_count: int
    account_identity_bound: bool
    account_mode_futures_ratified: bool
    venue_binding_complete: bool
    currency_domain_complete: bool
    liability_event_class_complete: bool
    time_domain_complete: bool
    surface_coverage_complete: bool
    pagination_complete: bool
    event_ordering_complete: bool
    observation_freshness_complete: bool
    restart_durability_complete: bool
    independence_from_balance_snapshot: bool
    independence_from_raw_eq: bool
    provenance_complete: bool
    applicability_account_spot_only: bool
    applicability_surface_futures_incapable: bool
    applicability_reason: str = ""


@dataclass(frozen=True)
class CompletenessRequirementRowV1:
    requirement: str
    required: bool
    proof_source: str
    status: str
    evidence: str
    missing_proof: str
    causal_blocker: str


@dataclass(frozen=True)
class P1NegativeCompletenessEvaluationV1:
    closeout_decision: str
    p1_status_after: str
    negative_evaluation: str
    does_not_apply_evaluation: str
    qualifying_event_count: int
    requirement_matrix: tuple[CompletenessRequirementRowV1, ...]
    minimal_missing_completeness_set: tuple[str, ...]
    first_missing_completeness_predicate: str
    first_missing_fact_origin: str
    evidence_class_required: str
    network_required: bool
    new_producer_required: bool
    zero_rows_alone_used: bool
    conflict_reason: str


def _requirement_specs_v1() -> dict[str, tuple[str, str]]:
    return {
        REQUIREMENT_ACCOUNT_IDENTITY: (
            "D4 bound account identity digest matches sealed P1 surface binding",
            "sealed_p1_surface_binding_v1+d4_genesis_binding",
        ),
        REQUIREMENT_ACCOUNT_MODE: (
            "FUTURES_MODE ratified for bound productive account (U01)",
            "sealed_u01_ratification+ p1_surface_binding",
        ),
        REQUIREMENT_VENUE: (
            "Venue/rest host binding complete for executed observations",
            "sealed_cd+usdc_claims+surface_binding",
        ),
        REQUIREMENT_CURRENCY_DOMAIN: (
            "Applicable loan-currency observation domain complete for negative closure",
            "explicit_currency_domain_completeness_witness_not_empty_rows",
        ),
        REQUIREMENT_LIABILITY_EVENT_CLASS: (
            "Ratified liability event taxonomy covers observed query class",
            "ratified_classified_kind_set+interest_accrued_type2_binding",
        ),
        REQUIREMENT_TIME_DOMAIN: (
            "Venue past-year (or bound window) traversal complete",
            "time_domain_exhaustion_witness_not_single_page_default",
        ),
        REQUIREMENT_SURFACE_COVERAGE: (
            "Documented FUTURES-compatible P1 liability event surfaces exhausted",
            "futures_p1_surface_discovery_v1",
        ),
        REQUIREMENT_PAGINATION: (
            "Pagination/cursor traversal complete for bound queries",
            "pagination_exhaustion_witness_per_d6_rules",
        ),
        REQUIREMENT_EVENT_ORDERING: (
            "Event ordering/tie ambiguity fail-closed preconditions met",
            "ordering_completeness_witness",
        ),
        REQUIREMENT_OBSERVATION_FRESHNESS: (
            "D5/checkpoint observation window freshness complete",
            "d5_checkpoint_window_binding_witness",
        ),
        REQUIREMENT_RESTART_DURABILITY: (
            "Restart/durability preconditions for observation completeness",
            "restart_durability_witness",
        ),
        REQUIREMENT_INDEPENDENCE_BALANCE: (
            "P1 evidence surface independent of balance snapshot authority",
            "cc_primary_proof_role+surface_binding",
        ),
        REQUIREMENT_INDEPENDENCE_RAW_EQ: (
            "P1 closeout independent of raw venue eq authority",
            "bj_by_raw_eq_non_authority_laws",
        ),
        REQUIREMENT_PROVENANCE: (
            "End-to-end provenance complete for full governed observation domain",
            "sealed_raw_chain+domain_completeness_witness",
        ),
    }


def _flag_for_requirement_v1(requirement: str, payload: P1NegativeCompletenessInputV1) -> bool:
    mapping = {
        REQUIREMENT_ACCOUNT_IDENTITY: payload.account_identity_bound,
        REQUIREMENT_ACCOUNT_MODE: payload.account_mode_futures_ratified,
        REQUIREMENT_VENUE: payload.venue_binding_complete,
        REQUIREMENT_CURRENCY_DOMAIN: payload.currency_domain_complete,
        REQUIREMENT_LIABILITY_EVENT_CLASS: payload.liability_event_class_complete,
        REQUIREMENT_TIME_DOMAIN: payload.time_domain_complete,
        REQUIREMENT_SURFACE_COVERAGE: payload.surface_coverage_complete,
        REQUIREMENT_PAGINATION: payload.pagination_complete,
        REQUIREMENT_EVENT_ORDERING: payload.event_ordering_complete,
        REQUIREMENT_OBSERVATION_FRESHNESS: payload.observation_freshness_complete,
        REQUIREMENT_RESTART_DURABILITY: payload.restart_durability_complete,
        REQUIREMENT_INDEPENDENCE_BALANCE: payload.independence_from_balance_snapshot,
        REQUIREMENT_INDEPENDENCE_RAW_EQ: payload.independence_from_raw_eq,
        REQUIREMENT_PROVENANCE: payload.provenance_complete,
    }
    return bool(mapping[requirement])


def _build_requirement_matrix_v1(
    payload: P1NegativeCompletenessInputV1,
) -> tuple[CompletenessRequirementRowV1, ...]:
    specs = _requirement_specs_v1()
    rows: list[CompletenessRequirementRowV1] = []
    for requirement in COMPLETENESS_REQUIREMENT_ORDER:
        spec_text, proof_source = specs[requirement]
        proven = _flag_for_requirement_v1(requirement, payload)
        if proven:
            status = "PROVEN"
            missing = ""
            blocker = ""
            evidence = spec_text
        else:
            status = "UNKNOWN"
            missing = f"{requirement}_NOT_INDEPENDENTLY_PROVEN"
            blocker = requirement
            evidence = (
                f"{spec_text}; sealed_cd_row_count={payload.cd_row_count}; "
                f"usdc_row_count={payload.usdc_scoped_row_count}"
            )
        rows.append(
            CompletenessRequirementRowV1(
                requirement=requirement,
                required=True,
                proof_source=proof_source,
                status=status,
                evidence=evidence,
                missing_proof=missing,
                causal_blocker=blocker,
            )
        )
    return tuple(rows)


def _missing_set_v1(matrix: Sequence[CompletenessRequirementRowV1]) -> tuple[str, ...]:
    return tuple(row.requirement for row in matrix if row.status != "PROVEN")


def _fact_origin_for_missing_v1(requirement: str) -> str:
    origins = {
        REQUIREMENT_CURRENCY_DOMAIN: "EXPLICIT_CURRENCY_DOMAIN_COMPLETENESS_WITNESS",
        REQUIREMENT_LIABILITY_EVENT_CLASS: "RATIFIED_CLASSIFIED_KIND_SET_RESOLUTION",
        REQUIREMENT_TIME_DOMAIN: "TIME_WINDOW_TRAVERSAL_EXHAUSTION_WITNESS",
        REQUIREMENT_PAGINATION: "PAGINATION_EXHAUSTION_WITNESS",
        REQUIREMENT_EVENT_ORDERING: "EVENT_ORDERING_COMPLETENESS_WITNESS",
        REQUIREMENT_OBSERVATION_FRESHNESS: "D5_OBSERVATION_WINDOW_FRESHNESS_WITNESS",
        REQUIREMENT_RESTART_DURABILITY: "RESTART_DURABILITY_WITNESS",
        REQUIREMENT_PROVENANCE: "FULL_DOMAIN_PROVENANCE_WITNESS",
    }
    return origins.get(requirement, "UNSUPPORTED_REQUIREMENT")


def _evidence_class_for_missing_v1(requirement: str) -> str:
    classes = {
        REQUIREMENT_CURRENCY_DOMAIN: "P1_CURRENCY_DOMAIN_COMPLETENESS_WITNESS_V1",
        REQUIREMENT_LIABILITY_EVENT_CLASS: "RATIFIED_LIABILITY_EVENT_TAXONOMY_WITNESS_V1",
        REQUIREMENT_TIME_DOMAIN: "P1_TIME_DOMAIN_EXHAUSTION_WITNESS_V1",
        REQUIREMENT_PAGINATION: "P1_PAGINATION_EXHAUSTION_WITNESS_V1",
        REQUIREMENT_EVENT_ORDERING: "P1_EVENT_ORDERING_WITNESS_V1",
        REQUIREMENT_OBSERVATION_FRESHNESS: "D5_CHECKPOINT_FRESHNESS_WITNESS_V1",
        REQUIREMENT_RESTART_DURABILITY: "OBSERVATION_RESTART_DURABILITY_WITNESS_V1",
        REQUIREMENT_PROVENANCE: "P1_FULL_DOMAIN_PROVENANCE_WITNESS_V1",
    }
    return classes.get(requirement, "UNKNOWN_EVIDENCE_CLASS")


def evaluate_p1_negative_completeness_v1(
    payload: P1NegativeCompletenessInputV1,
) -> P1NegativeCompletenessEvaluationV1:
    if payload.qualifying_event_count < 0 or payload.nonqualifying_event_count < 0:
        raise P1NegativeCompletenessCloseoutError("NEGATIVE_EVENT_COUNT")
    matrix = _build_requirement_matrix_v1(payload)
    missing = _missing_set_v1(matrix)
    first_missing = missing[0] if missing else ""

    does_not_apply = P1_CLOSEOUT_UNKNOWN
    if payload.applicability_account_spot_only or payload.applicability_surface_futures_incapable:
        if payload.applicability_reason:
            does_not_apply = P1_CLOSEOUT_DOES_NOT_APPLY
        else:
            does_not_apply = P1_CLOSEOUT_UNKNOWN

    if payload.qualifying_event_count > 0:
        return P1NegativeCompletenessEvaluationV1(
            closeout_decision=P1_CLOSEOUT_CONFLICTED,
            p1_status_after=P1_STATUS_UNKNOWN,
            negative_evaluation=P1_CLOSEOUT_CONFLICTED,
            does_not_apply_evaluation=does_not_apply,
            qualifying_event_count=payload.qualifying_event_count,
            requirement_matrix=matrix,
            minimal_missing_completeness_set=missing,
            first_missing_completeness_predicate=first_missing,
            first_missing_fact_origin=_fact_origin_for_missing_v1(first_missing)
            if first_missing
            else "",
            evidence_class_required=_evidence_class_for_missing_v1(first_missing)
            if first_missing
            else "",
            network_required=False,
            new_producer_required=False,
            zero_rows_alone_used=False,
            conflict_reason="QUALIFYING_EVENT_COUNT_GT_ZERO_BLOCKS_NEGATIVE_CLOSEOUT",
        )

    if does_not_apply == P1_CLOSEOUT_DOES_NOT_APPLY:
        return P1NegativeCompletenessEvaluationV1(
            closeout_decision=P1_CLOSEOUT_DOES_NOT_APPLY,
            p1_status_after=P1_STATUS_DOES_NOT_APPLY,
            negative_evaluation=P1_CLOSEOUT_UNKNOWN,
            does_not_apply_evaluation=P1_CLOSEOUT_DOES_NOT_APPLY,
            qualifying_event_count=0,
            requirement_matrix=matrix,
            minimal_missing_completeness_set=missing,
            first_missing_completeness_predicate=first_missing,
            first_missing_fact_origin=_fact_origin_for_missing_v1(first_missing)
            if first_missing
            else "",
            evidence_class_required=_evidence_class_for_missing_v1(first_missing)
            if first_missing
            else "",
            network_required=False,
            new_producer_required=False,
            zero_rows_alone_used=False,
            conflict_reason="",
        )

    all_proven = not missing
    zero_rows_alone = (
        payload.cd_row_count == 0
        and payload.usdc_scoped_row_count == 0
        and payload.qualifying_event_count == 0
    )
    if all_proven and payload.qualifying_event_count == 0:
        closeout = P1_CLOSEOUT_PROVEN_NEGATIVE
        return P1NegativeCompletenessEvaluationV1(
            closeout_decision=closeout,
            p1_status_after=P1_STATUS_PROVEN_FALSE,
            negative_evaluation=closeout,
            does_not_apply_evaluation=P1_CLOSEOUT_UNKNOWN,
            qualifying_event_count=0,
            requirement_matrix=matrix,
            minimal_missing_completeness_set=missing,
            first_missing_completeness_predicate=first_missing,
            first_missing_fact_origin=_fact_origin_for_missing_v1(first_missing)
            if first_missing
            else "",
            evidence_class_required=_evidence_class_for_missing_v1(first_missing)
            if first_missing
            else "",
            network_required=False,
            new_producer_required=False,
            zero_rows_alone_used=zero_rows_alone,
            conflict_reason="",
        )

    return P1NegativeCompletenessEvaluationV1(
        closeout_decision=P1_CLOSEOUT_UNKNOWN,
        p1_status_after=P1_STATUS_UNKNOWN,
        negative_evaluation=P1_CLOSEOUT_UNKNOWN,
        does_not_apply_evaluation=does_not_apply,
        qualifying_event_count=0,
        requirement_matrix=matrix,
        minimal_missing_completeness_set=missing,
        first_missing_completeness_predicate=first_missing,
        first_missing_fact_origin=_fact_origin_for_missing_v1(first_missing),
        evidence_class_required=_evidence_class_for_missing_v1(first_missing),
        network_required=first_missing != "",
        new_producer_required=False,
        zero_rows_alone_used=zero_rows_alone and not all_proven,
        conflict_reason="",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_bool_token(value: object) -> bool:
    return str(value or "").lower() == TRUE_TOKEN


def load_sealed_interest_accrued_p1_input_v1(
    *, repo_root: Path | str
) -> P1NegativeCompletenessInputV1:
    root = Path(repo_root)
    cd = _read_json(root / CANONICAL_CD_PACK / "claims.json")
    usdc = _read_json(root / CANONICAL_USDC_P1_PACK / "claims.json")
    reopen = _read_json(
        root / CANONICAL_USDC_P1_PACK / "interest_accrued_reopen_adjudication_v1.json"
    )
    discovery = _read_json(root / CANONICAL_USDC_P1_PACK / "futures_p1_surface_discovery_v1.json")
    binding = _read_json(root / CANONICAL_USDC_P1_PACK / "p1_surface_binding_v1.json")
    offline = _read_json(root / CANONICAL_USDC_P1_PACK / "p1_offline_qualification_v1.json")
    u01 = _read_json(root / CANONICAL_U01_PACK / "claims.json")

    qualifying = int(str(offline.get("qualifying_p1_count", "0")))
    nonqualifying = int(str(offline.get("nonqualifying_p1_count", "0")))
    cd_rows = int(str(cd.get("QUALIFYING_LIABILITY_ROWS", cd.get("ROW_COUNT", "0"))))
    usdc_rows = int(str(usdc.get("ROW_COUNT", "0")))

    identity_digest = str(binding.get("ACCOUNT_IDENTITY_DIGEST", ""))
    account_identity_bound = identity_digest == EXPECTED_D4_IDENTITY_DIGEST
    account_mode_futures = (
        str(binding.get("ACCOUNT_MODE", "")) == "FUTURES_MODE"
        and str(u01.get("U01_CANONICAL_SEMANTIC_TOKEN", "")) == "FUTURES_MODE"
    )
    venue_complete = (
        str(binding.get("VENUE", "")) == "OKX"
        and str(cd.get("VENUE_CODE", "")) == "0"
        and str(usdc.get("VENUE_CODE", "")) == "0"
        and str(cd.get("HTTP_STATUS", "")) == "200"
        and str(usdc.get("HTTP_STATUS", "")) == "200"
    )

    pagination_complete = _as_bool_token(reopen.get("CD_EXHAUSTION_PROVEN"))
    time_domain_complete = pagination_complete and not _as_bool_token(
        reopen.get("CD_CURSOR_USED", FALSE_TOKEN)
    )

    surface_coverage_complete = True
    for record in discovery.get("records", []):
        if not isinstance(record, dict):
            continue
        if str(record.get("STATUS", "")) == "CAPABLE_WITH_BOUNDED_BINDING":
            consumed = str(record.get("PREVIOUSLY_CONSUMED", ""))
            if "CD_UNSCOPED" not in consumed or "P1_USDC_SCOPE_NEW" not in consumed:
                surface_coverage_complete = False
                break

    currency_domain_complete = False
    liability_event_class_complete = (
        bool(RATIFIED_CLASSIFIED_KIND_SET) and RATIFIED_CLASSIFIED_KIND_SET_RESOLVED
    )

    independence_balance = str(usdc.get("P1_EVENT_SURFACE_ROLE", "")) == (
        "INDEPENDENT_LIABILITY_EVENT_EVIDENCE_ONLY"
    )
    independence_raw_eq = (
        not RAW_EQ_SOURCE_AUTHORITY
        and str(cd.get("VENUE_EQ_SOURCE_AUTHORITY", TRUE_TOKEN)) == FALSE_TOKEN
        and str(usdc.get("RAW_EQ_SOURCE_AUTHORITY", TRUE_TOKEN)) == FALSE_TOKEN
    )
    provenance_complete = (
        _as_bool_token(cd.get("RAW_EVIDENCE_PERSISTED"))
        and _as_bool_token(usdc.get("RAW_EVIDENCE_PERSISTED"))
        and bool(str(cd.get("RAW_EVIDENCE_SHA256", "")))
        and bool(str(usdc.get("RAW_EVIDENCE_SHA256", "")))
        and currency_domain_complete
        and time_domain_complete
        and pagination_complete
    )

    return P1NegativeCompletenessInputV1(
        qualifying_event_count=qualifying,
        nonqualifying_event_count=nonqualifying,
        cd_row_count=cd_rows,
        usdc_scoped_row_count=usdc_rows,
        account_identity_bound=account_identity_bound,
        account_mode_futures_ratified=account_mode_futures,
        venue_binding_complete=venue_complete,
        currency_domain_complete=currency_domain_complete,
        liability_event_class_complete=liability_event_class_complete,
        time_domain_complete=time_domain_complete,
        surface_coverage_complete=surface_coverage_complete,
        pagination_complete=pagination_complete,
        event_ordering_complete=False,
        observation_freshness_complete=False,
        restart_durability_complete=False,
        independence_from_balance_snapshot=independence_balance,
        independence_from_raw_eq=independence_raw_eq,
        provenance_complete=provenance_complete,
        applicability_account_spot_only=False,
        applicability_surface_futures_incapable=False,
        applicability_reason="",
    )


def evaluate_sealed_interest_accrued_p1_closeout_v1(
    *, repo_root: Path | str
) -> P1NegativeCompletenessEvaluationV1:
    payload = load_sealed_interest_accrued_p1_input_v1(repo_root=repo_root)
    return evaluate_p1_negative_completeness_v1(payload)


def ratified_absence_laws_v1() -> dict[str, bool]:
    return {
        "EMPTY_ROWS_PROVE_ZERO_EVENTS": EMPTY_ROWS_PROVE_ZERO_EVENTS,
        "EMPTY_ROWS_PROVE_KIND_ABSENCE": EMPTY_ROWS_PROVE_KIND_ABSENCE,
        "PAGINATION_EXHAUSTION_PROVES_COMPLETENESS": PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
        "ZERO_ROWS_ALONE_MAY_PROVE_NEGATIVE": ZERO_ROWS_ALONE_MAY_PROVE_NEGATIVE,
    }


def evaluation_to_mapping_v1(
    evaluation: P1NegativeCompletenessEvaluationV1,
) -> dict[str, Any]:
    return {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "WP_ID": WP_ID,
        "P1_CLOSEOUT_DECISION": evaluation.closeout_decision,
        "P1_STATUS_AFTER": evaluation.p1_status_after,
        "P1_NEGATIVE_EVALUATION": evaluation.negative_evaluation,
        "P1_DOES_NOT_APPLY_EVALUATION": evaluation.does_not_apply_evaluation,
        "MINIMAL_MISSING_COMPLETENESS_SET": list(evaluation.minimal_missing_completeness_set),
        "FIRST_MISSING_COMPLETENESS_PREDICATE": evaluation.first_missing_completeness_predicate,
        "FIRST_MISSING_FACT_ORIGIN": evaluation.first_missing_fact_origin,
        "EVIDENCE_CLASS_REQUIRED": evaluation.evidence_class_required,
        "NETWORK_REQUIRED": evaluation.network_required,
        "NEW_PRODUCER_REQUIRED": evaluation.new_producer_required,
        "ZERO_ROWS_ALONE_USED": evaluation.zero_rows_alone_used,
        "REQUIREMENT_MATRIX": [
            {
                "REQUIREMENT": row.requirement,
                "REQUIRED": row.required,
                "EVIDENCE": row.evidence,
                "STATUS": row.status,
                "MISSING_PROOF": row.missing_proof,
                "CAUSAL_BLOCKER": row.causal_blocker,
                "PROOF_SOURCE": row.proof_source,
            }
            for row in evaluation.requirement_matrix
        ],
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "COMPLETENESS_REQUIREMENT_ORDER",
    "CONTRACT_VERSION",
    "P1NegativeCompletenessCloseoutError",
    "P1NegativeCompletenessEvaluationV1",
    "P1NegativeCompletenessInputV1",
    "P1_APPLICABILITY_DOMAIN",
    "P1_CLOSEOUT_CONFLICTED",
    "P1_CLOSEOUT_DOES_NOT_APPLY",
    "P1_CLOSEOUT_PROVEN_NEGATIVE",
    "P1_CLOSEOUT_UNKNOWN",
    "P1_DOES_NOT_APPLY_SEMANTICS",
    "P1_NEGATIVE_SEMANTICS",
    "P1_POSITIVE_SEMANTICS",
    "P1_SEMANTIC_DOMAIN",
    "P1_STATUS_UNKNOWN",
    "P1_UNKNOWN_SEMANTICS",
    "SCHEMA_CLASS",
    "ZERO_ROWS_ALONE_MAY_PROVE_NEGATIVE",
    "evaluate_p1_negative_completeness_v1",
    "evaluate_sealed_interest_accrued_p1_closeout_v1",
    "evaluation_to_mapping_v1",
    "load_sealed_interest_accrued_p1_input_v1",
    "ratified_absence_laws_v1",
]
