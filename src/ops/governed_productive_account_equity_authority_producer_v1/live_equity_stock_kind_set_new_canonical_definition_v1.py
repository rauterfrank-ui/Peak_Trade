"""NEW_CANONICAL_DEFINITION of live EQUITY_STOCK KIND_SET membership.

Defines eligibility, source-role matrix, and a deterministic membership
evaluator for today's OPTION_D running-account-equity architecture. Does not
reconstruct historical F12/F13/U05/F16/F17/F18. Does not invent a source
kind. Empty KIND_SET remains EMPTY_FAIL_CLOSED until a today-candidate
satisfies every eligibility criterion. Does not GET. Does not POST.
Does not execute GATE_A or GATE_B. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    RATIFIED_SOURCE_KIND_SET,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    FACT_F12,
    FACT_F13,
    FACT_F16,
    FACT_F17,
    FACT_F18,
    FACT_IDS,
    FACT_U05,
    FALSE_TOKEN,
    KIND_SET_EMPTY,
    NONE_TOKEN,
    TRUE_TOKEN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
    CHECKPOINT_CAN_MINT_EQUITY,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EQ_RECONCILIATION_TARGET_ONLY,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    U06_PLACEMENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    CHECKPOINT_KIND,
    OBSERVATION_VS_AUTHORITY_CLASS,
    assert_checkpoint_cannot_mint_equity_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CURRENTLY_DECISION_CAPABLE,
    EARLIEST_REMAINING_D6_BLOCKER as HISTORICAL_D6_BLOCKER,
    GATE_A_ID,
    GATE_B_ID,
    KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY as HISTORICAL_KIND_SET_BLOCKED_BY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.fresh_eq_reconciliation_target_contract_v1 import (
    VENUE_FIELD_NAME,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_critical_path_next_blocker_bounded_wp1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BM_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BM_LIVE_BLOCKER,
    LIVE_CRITICAL_KIND_SET_IDENTITY,
    NEXT_OWNER_GO_REQUIRED as BM_NEXT_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "8ea65432709458ad1a91cc5f63818296294aa543"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_kind_set_new_canonical_definition_wp1/"
    "2026-09-14T100000Z"
)
CLAIMS_FILE = "claims.json"
NEW_CANONICAL_DEFINITION_ID = LIVE_CRITICAL_KIND_SET_IDENTITY
LIVE_EQUITY_STOCK_KIND_SET_IDENTITY = NEW_CANONICAL_DEFINITION_ID
LIVE_EQUITY_STOCK_KIND_SET = KIND_SET_EMPTY
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = (
    "NO_ELIGIBLE_TODAY_LIVE_EQUITY_STOCK_SOURCE_KIND_AFTER_NEW_CANONICAL_DEFINITION"
)
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT_V1"

ROLE_EQUITY_STOCK_SOURCE = "EQUITY_STOCK_SOURCE"
ROLE_EQUITY_FLOW_SOURCE = "EQUITY_FLOW_SOURCE"
ROLE_RECONCILIATION_TARGET_ONLY = "RECONCILIATION_TARGET_ONLY"
ROLE_AVAILABLE_CAPITAL_ONLY = "AVAILABLE_CAPITAL_ONLY"
ROLE_PLACEMENT_CAPACITY_ONLY = "PLACEMENT_CAPACITY_ONLY"
ROLE_RISK_CAPITAL_REDUCTION_ONLY = "RISK_CAPITAL_REDUCTION_ONLY"
ROLE_NON_SOURCE = "NON_SOURCE"
ROLE_OTHER_DOMAIN = "OTHER_DOMAIN"
ROLE_UNRESOLVED = "UNRESOLVED"
SOURCE_ROLES: tuple[str, ...] = (
    ROLE_EQUITY_STOCK_SOURCE,
    ROLE_EQUITY_FLOW_SOURCE,
    ROLE_RECONCILIATION_TARGET_ONLY,
    ROLE_AVAILABLE_CAPITAL_ONLY,
    ROLE_PLACEMENT_CAPACITY_ONLY,
    ROLE_RISK_CAPITAL_REDUCTION_ONLY,
    ROLE_NON_SOURCE,
    ROLE_OTHER_DOMAIN,
    ROLE_UNRESOLVED,
)

LAYER_CANONICAL = "CANONICAL_AUTHORITY"
LAYER_FORENSIC = "FORENSIC_RAW_EVIDENCE"
LAYER_ADJUDICATED = "ADJUDICATED_CONCLUSION"
LAYER_HISTORICAL = "HISTORICAL_INTERMEDIATE"
LAYER_NAVIGATION = "NAVIGATION_ONLY"
LAYER_INTERPRETATION = "INTERPRETATION"
LAYER_HYPOTHESIS = "HYPOTHESIS"
LAYER_OPEN = "OPEN_OR_CONTRADICTORY"

INPUT_PRESENT = "PRESENT"
INPUT_MISSING = "MISSING"
INPUT_MALFORMED = "MALFORMED"
INPUT_CONTRADICTORY = "CONTRADICTORY"

ELIGIBILITY_CRITERIA: tuple[str, ...] = (
    "ABSOLUTE_ACCOUNT_EQUITY_STATE_AT_CHECKPOINT",
    "UNIQUE_ACCOUNT_CURRENCY_SCOPE_IDENTITY",
    "DETERMINISTIC_TIME_SEQUENCE_IDENTITY",
    "OPTION_D_START_CHECKPOINT_CAPABLE",
    "NOT_DELTA_OR_FLOW",
    "NOT_VENUE_RECONCILIATION_WITNESS",
    "NOT_AVAILABLE_PLACEMENT_OR_RISK_CAPITAL",
    "NO_DOUBLE_COUNT_WITH_CLASSIFIED_EVENT_STREAM",
    "EMBEDDING_AND_LIABILITY_RULES_EXPLICIT",
    "SCHEMA_MISSING_MALFORMED_CONTRADICTORY_FAIL_CLOSED",
)

REASON_CLAIMED_INCLUDE_FORBIDDEN = "CLAIMED_INCLUDE_FORBIDDEN"
REASON_CLAIMED_EXCLUDE_FORBIDDEN = "CLAIMED_EXCLUDE_FORBIDDEN"
REASON_MISSING_INPUT = "MISSING_INPUT"
REASON_MALFORMED_INPUT = "MALFORMED_INPUT"
REASON_CONTRADICTORY_INPUT = "CONTRADICTORY_INPUT"
REASON_HISTORICAL_UNKNOWN = "HISTORICAL_UNKNOWN_NOT_NEW_CANONICAL_MEMBER"
REASON_RECONCILIATION_TARGET = "RATIFIED_RECONCILIATION_TARGET_ONLY"
REASON_AVAILABLE_CAPITAL = "RATIFIED_AVAILABLE_CAPITAL_ONLY"
REASON_PLACEMENT_CAPACITY = "RATIFIED_PLACEMENT_CAPACITY_ONLY"
REASON_RISK_CAPITAL_REDUCTION = "RATIFIED_RISK_CAPITAL_REDUCTION_ONLY"
REASON_NON_SOURCE = "RATIFIED_NON_SOURCE"
REASON_OTHER_DOMAIN = "RATIFIED_OTHER_DOMAIN"
REASON_DELTA_OR_FLOW = "IS_DELTA_OR_FLOW"
REASON_CHECKPOINT_CANNOT_MINT = "CHECKPOINT_CANNOT_MINT_EQUITY"
REASON_EMBEDDING_UNPROVEN = "EMBEDDING_UNPROVEN"
REASON_IDENTITY_UNPROVEN = "IDENTITY_UNPROVEN"
REASON_TIME_SEQUENCE_UNPROVEN = "TIME_SEQUENCE_UNPROVEN"
REASON_DOUBLE_COUNT_UNPROVEN = "DOUBLE_COUNT_UNPROVEN"
REASON_ABSOLUTE_STOCK_ABSENT = "ABSOLUTE_STOCK_VALUE_ABSENT"
REASON_OPTION_D_START_INCAPABLE = "OPTION_D_START_INCAPABLE"
REASON_UNKNOWN_UNRATIFIED = "UNKNOWN_UNRATIFIED"
REASON_ELIGIBLE = "ELIGIBLE_EQUITY_STOCK_SOURCE"

REASON_PRECEDENCE: tuple[str, ...] = (
    REASON_CLAIMED_INCLUDE_FORBIDDEN,
    REASON_CLAIMED_EXCLUDE_FORBIDDEN,
    REASON_MISSING_INPUT,
    REASON_MALFORMED_INPUT,
    REASON_CONTRADICTORY_INPUT,
    REASON_HISTORICAL_UNKNOWN,
    REASON_RECONCILIATION_TARGET,
    REASON_AVAILABLE_CAPITAL,
    REASON_PLACEMENT_CAPACITY,
    REASON_RISK_CAPITAL_REDUCTION,
    REASON_DELTA_OR_FLOW,
    REASON_CHECKPOINT_CANNOT_MINT,
    REASON_EMBEDDING_UNPROVEN,
    REASON_IDENTITY_UNPROVEN,
    REASON_TIME_SEQUENCE_UNPROVEN,
    REASON_DOUBLE_COUNT_UNPROVEN,
    REASON_ABSOLUTE_STOCK_ABSENT,
    REASON_OPTION_D_START_INCAPABLE,
    REASON_NON_SOURCE,
    REASON_OTHER_DOMAIN,
    REASON_UNKNOWN_UNRATIFIED,
    REASON_ELIGIBLE,
)

CANDIDATE_VENUE_EQ = "VENUE_EQ"
CANDIDATE_U04 = "U04"
CANDIDATE_U05 = "U05"
CANDIDATE_U06 = "U06"
CANDIDATE_P01 = "P01"
CANDIDATE_GOVERNED_CHECKPOINT = "GOVERNED_CHECKPOINT"
CANDIDATE_CLASSIFIED_EVENT_STREAM = "CLASSIFIED_EVENT_STREAM"
CANDIDATE_C17 = "C17"
HISTORICAL_CANDIDATE_IDS: tuple[str, ...] = FACT_IDS


class LiveEquityStockKindSetDefinitionError(ValueError):
    """Fail-closed live EQUITY_STOCK KIND_SET definition violation."""


@dataclass(frozen=True)
class LiveEquityStockKindCandidateV1:
    candidate_id: str
    source_role: str
    layer: str
    input_status: str
    claimed_proof: str
    is_historical_unknown: bool
    is_delta_or_flow: bool
    is_reconciliation_witness: bool
    is_available_capital: bool
    is_placement_capacity: bool
    is_risk_capital_reduction: bool
    is_checkpoint_non_minting: bool
    embedding_proven: bool
    identity_proven: bool
    time_sequence_proven: bool
    double_count_proven_safe: bool
    absolute_stock_value_present: bool
    option_d_start_capable: bool
    authority_ref: str


@dataclass(frozen=True)
class LiveEquityStockMembershipRecordV1:
    candidate_id: str
    source_role: str
    layer: str
    member: str
    reason_code: str
    reason_precedence_index: str
    eligibility_failures: tuple[str, ...]


@dataclass(frozen=True)
class LiveEquityStockKindSetDefinitionV1:
    definition_class: str
    definition_id: str
    live_equity_stock_kind_set: str
    live_equity_stock_kind_set_resolved: str
    kind_set_members: tuple[str, ...]
    kind_set_rejected_candidates: tuple[str, ...]
    legacy_semantics_reconstructed: str
    new_canonical_definition: str
    kinds_invented_this_go: str


@dataclass(frozen=True)
class LiveEquityStockKindSetDefinitionResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    live_equity_stock_kind_set: str
    live_equity_stock_kind_set_resolved: str
    kind_set_members: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str
    venue_get_count: str
    venue_post_count: str
    gate_a_executed: str
    gate_b_executed: str
    kinds_invented_this_go: str
    legacy_semantics_reconstructed: str
    d6_fully_closed: str
    d7_authorized: str
    ms2_authorized: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _folder_from_as_of(as_of: str) -> str:
    return as_of.replace(":", "")


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveEquityStockKindSetDefinitionError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise LiveEquityStockKindSetDefinitionError(f"{field}_DRIFT:{actual}")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise LiveEquityStockKindSetDefinitionError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise LiveEquityStockKindSetDefinitionError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise LiveEquityStockKindSetDefinitionError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise LiveEquityStockKindSetDefinitionError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise LiveEquityStockKindSetDefinitionError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise LiveEquityStockKindSetDefinitionError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise LiveEquityStockKindSetDefinitionError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not True and CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise LiveEquityStockKindSetDefinitionError("CHECKPOINT_CAN_MINT_EQUITY_NOT_BOOL")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise LiveEquityStockKindSetDefinitionError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise LiveEquityStockKindSetDefinitionError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise LiveEquityStockKindSetDefinitionError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if BM_NEXT_OWNER_GO != OWNER_GO:
        raise LiveEquityStockKindSetDefinitionError("BM_NEXT_OWNER_GO_DRIFT")
    if BM_LIVE_BLOCKER != "NO_OWNER_RATIFIED_NEW_CANONICAL_LIVE_EQUITY_STOCK_SOURCE_KIND":
        raise LiveEquityStockKindSetDefinitionError("BM_LIVE_BLOCKER_DRIFT")
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )
    assert_checkpoint_cannot_mint_equity_v1(
        equity_mint_status="NOT_MINTED",
        running_equity_value_state="ABSENT",
        claimed_equity_stock_value="ABSENT",
        observation_vs_authority_class=OBSERVATION_VS_AUTHORITY_CLASS,
    )


def reject_claimed_live_kind_set_authority_mutation_v1(
    *,
    claimed_proof: str,
    candidate_id: str,
) -> None:
    forbidden = {
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "EXECUTE_GATE_B",
        "HOPE_BALANCE_GET",
        "VENUE_POST",
        "KIND_SET_RESOLVED_TRUE",
        "D6_FULLY_CLOSED",
        "D7_AUTHORIZED_TRUE",
        "MS2_AUTHORIZED_TRUE",
        "INVENT_LIVE_SOURCE_KIND",
        "RECONSTRUCT_HISTORICAL_UNKNOWN",
        "PROMOTE_HISTORICAL_UNKNOWN_TO_LIVE_KIND",
        "PROMOTE_EQ_TO_SOURCE",
        "PROMOTE_U04_TO_EQUITY_STOCK",
        "PROMOTE_P01_TO_EQUITY_STOCK",
        "RESTORE_LEGACY_EQUITY_LOGIC",
        "NORMALIZE_UNKNOWN_TO_INCLUDE",
        "NORMALIZE_UNKNOWN_TO_EXCLUDE",
        "PATH_C_UNKNOWN_CLOSEOUT",
    }
    if claimed_proof in forbidden:
        raise LiveEquityStockKindSetDefinitionError(
            f"LIVE_KIND_SET_CANNOT_{claimed_proof}:{candidate_id}"
        )
    if claimed_proof not in {
        "NEW_CANONICAL_DEFINITION_EMPTY_FAIL_CLOSED",
        "HISTORICAL_UNKNOWN_NOT_LIVE_KIND_SET_MEMBER",
        "TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
        "ELIGIBILITY_EVALUATOR_ONLY",
    }:
        raise LiveEquityStockKindSetDefinitionError(
            f"LIVE_KIND_SET_PROOF_UNKNOWN:{claimed_proof}:{candidate_id}"
        )


def reason_precedence_index_v1(reason_code: str) -> int:
    try:
        return REASON_PRECEDENCE.index(reason_code)
    except ValueError as exc:
        raise LiveEquityStockKindSetDefinitionError(
            f"REASON_CODE_NOT_IN_PRECEDENCE:{reason_code}"
        ) from exc


def _eligibility_failures(
    candidate: LiveEquityStockKindCandidateV1,
) -> tuple[str, ...]:
    failures: list[str] = []
    if candidate.input_status != INPUT_PRESENT:
        failures.append("SCHEMA_MISSING_MALFORMED_CONTRADICTORY_FAIL_CLOSED")
    if not candidate.absolute_stock_value_present:
        failures.append("ABSOLUTE_ACCOUNT_EQUITY_STATE_AT_CHECKPOINT")
    if not candidate.identity_proven:
        failures.append("UNIQUE_ACCOUNT_CURRENCY_SCOPE_IDENTITY")
    if not candidate.time_sequence_proven:
        failures.append("DETERMINISTIC_TIME_SEQUENCE_IDENTITY")
    if not candidate.option_d_start_capable:
        failures.append("OPTION_D_START_CHECKPOINT_CAPABLE")
    if candidate.is_delta_or_flow:
        failures.append("NOT_DELTA_OR_FLOW")
    if candidate.is_reconciliation_witness:
        failures.append("NOT_VENUE_RECONCILIATION_WITNESS")
    if (
        candidate.is_available_capital
        or candidate.is_placement_capacity
        or candidate.is_risk_capital_reduction
    ):
        failures.append("NOT_AVAILABLE_PLACEMENT_OR_RISK_CAPITAL")
    if not candidate.double_count_proven_safe:
        failures.append("NO_DOUBLE_COUNT_WITH_CLASSIFIED_EVENT_STREAM")
    if not candidate.embedding_proven:
        failures.append("EMBEDDING_AND_LIABILITY_RULES_EXPLICIT")
    return tuple(failures)


def evaluate_live_equity_stock_kind_membership_v1(
    candidate: LiveEquityStockKindCandidateV1,
) -> LiveEquityStockMembershipRecordV1:
    _assert_standing_pins()
    if candidate.source_role not in SOURCE_ROLES:
        raise LiveEquityStockKindSetDefinitionError(
            f"SOURCE_ROLE_UNKNOWN:{candidate.candidate_id}:{candidate.source_role}"
        )
    reject_claimed_live_kind_set_authority_mutation_v1(
        claimed_proof=candidate.claimed_proof
        if candidate.claimed_proof
        in {
            "NEW_CANONICAL_DEFINITION_EMPTY_FAIL_CLOSED",
            "HISTORICAL_UNKNOWN_NOT_LIVE_KIND_SET_MEMBER",
            "TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            "ELIGIBILITY_EVALUATOR_ONLY",
        }
        else "ELIGIBILITY_EVALUATOR_ONLY",
        candidate_id=candidate.candidate_id,
    )
    reasons: list[str] = []
    if candidate.claimed_proof == DECISION_INCLUDE:
        reasons.append(REASON_CLAIMED_INCLUDE_FORBIDDEN)
    if candidate.claimed_proof == DECISION_EXCLUDE:
        reasons.append(REASON_CLAIMED_EXCLUDE_FORBIDDEN)
    if candidate.input_status == INPUT_MISSING:
        reasons.append(REASON_MISSING_INPUT)
    if candidate.input_status == INPUT_MALFORMED:
        reasons.append(REASON_MALFORMED_INPUT)
    if candidate.input_status == INPUT_CONTRADICTORY:
        reasons.append(REASON_CONTRADICTORY_INPUT)
    if candidate.is_historical_unknown:
        reasons.append(REASON_HISTORICAL_UNKNOWN)
    if candidate.is_reconciliation_witness:
        reasons.append(REASON_RECONCILIATION_TARGET)
    if candidate.is_available_capital:
        reasons.append(REASON_AVAILABLE_CAPITAL)
    if candidate.is_placement_capacity:
        reasons.append(REASON_PLACEMENT_CAPACITY)
    if candidate.is_risk_capital_reduction:
        reasons.append(REASON_RISK_CAPITAL_REDUCTION)
    if candidate.is_delta_or_flow:
        reasons.append(REASON_DELTA_OR_FLOW)
    if candidate.is_checkpoint_non_minting:
        reasons.append(REASON_CHECKPOINT_CANNOT_MINT)
    if not candidate.embedding_proven:
        reasons.append(REASON_EMBEDDING_UNPROVEN)
    if not candidate.identity_proven:
        reasons.append(REASON_IDENTITY_UNPROVEN)
    if not candidate.time_sequence_proven:
        reasons.append(REASON_TIME_SEQUENCE_UNPROVEN)
    if not candidate.double_count_proven_safe:
        reasons.append(REASON_DOUBLE_COUNT_UNPROVEN)
    if not candidate.absolute_stock_value_present:
        reasons.append(REASON_ABSOLUTE_STOCK_ABSENT)
    if not candidate.option_d_start_capable:
        reasons.append(REASON_OPTION_D_START_INCAPABLE)
    if candidate.source_role == ROLE_NON_SOURCE:
        reasons.append(REASON_NON_SOURCE)
    if candidate.source_role == ROLE_OTHER_DOMAIN:
        reasons.append(REASON_OTHER_DOMAIN)
    failures = _eligibility_failures(candidate)
    eligible = (
        not reasons
        and not failures
        and candidate.source_role == ROLE_EQUITY_STOCK_SOURCE
        and candidate.input_status == INPUT_PRESENT
    )
    if eligible:
        reason_code = REASON_ELIGIBLE
    elif reasons:
        reason_code = min(reasons, key=reason_precedence_index_v1)
    else:
        reason_code = REASON_UNKNOWN_UNRATIFIED
    return LiveEquityStockMembershipRecordV1(
        candidate_id=candidate.candidate_id,
        source_role=candidate.source_role,
        layer=candidate.layer,
        member=TRUE_TOKEN if reason_code == REASON_ELIGIBLE else FALSE_TOKEN,
        reason_code=reason_code,
        reason_precedence_index=str(reason_precedence_index_v1(reason_code)),
        eligibility_failures=failures,
    )


def build_today_live_equity_stock_candidates_v1() -> tuple[LiveEquityStockKindCandidateV1, ...]:
    _assert_standing_pins()
    historical = tuple(
        LiveEquityStockKindCandidateV1(
            candidate_id=fact_id,
            source_role=ROLE_UNRESOLVED,
            layer=LAYER_ADJUDICATED,
            input_status=INPUT_PRESENT,
            claimed_proof="HISTORICAL_UNKNOWN_NOT_LIVE_KIND_SET_MEMBER",
            is_historical_unknown=True,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref=f"BJ_REMAIN_UNKNOWN;{fact_id}",
        )
        for fact_id in HISTORICAL_CANDIDATE_IDS
    )
    today = (
        LiveEquityStockKindCandidateV1(
            candidate_id=CANDIDATE_VENUE_EQ,
            source_role=ROLE_RECONCILIATION_TARGET_ONLY,
            layer=LAYER_CANONICAL,
            input_status=INPUT_PRESENT,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=True,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref=f"{VENUE_FIELD_NAME};EQ_RECONCILIATION_TARGET_ONLY",
        ),
        LiveEquityStockKindCandidateV1(
            candidate_id=CANDIDATE_U04,
            source_role=ROLE_AVAILABLE_CAPITAL_ONLY,
            layer=LAYER_CANONICAL,
            input_status=INPUT_PRESENT,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=True,
            is_placement_capacity=True,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref=f"U04;{U04_PLACEMENT}",
        ),
        LiveEquityStockKindCandidateV1(
            candidate_id=CANDIDATE_U06,
            source_role=ROLE_UNRESOLVED,
            layer=LAYER_ADJUDICATED,
            input_status=INPUT_PRESENT,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN,
            is_delta_or_flow=False,
            is_reconciliation_witness=True,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref=f"U06;{U06_PLACEMENT};{U06_KIND_DECISION}",
        ),
        LiveEquityStockKindCandidateV1(
            candidate_id=CANDIDATE_P01,
            source_role=ROLE_RISK_CAPITAL_REDUCTION_ONLY,
            layer=LAYER_CANONICAL,
            input_status=INPUT_PRESENT,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=True,
            is_checkpoint_non_minting=False,
            embedding_proven=True,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref="P01;GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION",
        ),
        LiveEquityStockKindCandidateV1(
            candidate_id=CANDIDATE_GOVERNED_CHECKPOINT,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status=INPUT_PRESENT,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=True,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref=f"{CHECKPOINT_KIND};{OBSERVATION_VS_AUTHORITY_CLASS}",
        ),
        LiveEquityStockKindCandidateV1(
            candidate_id=CANDIDATE_CLASSIFIED_EVENT_STREAM,
            source_role=ROLE_EQUITY_FLOW_SOURCE,
            layer=LAYER_CANONICAL,
            input_status=INPUT_PRESENT,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=False,
            is_delta_or_flow=True,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref="EVENT_STREAM_CANNOT_MUTATE_EQUITY_STOCK",
        ),
        LiveEquityStockKindCandidateV1(
            candidate_id=CANDIDATE_C17,
            source_role=ROLE_UNRESOLVED,
            layer=LAYER_CANONICAL,
            input_status=INPUT_PRESENT,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=False,
            option_d_start_capable=False,
            authority_ref=f"C17_FROZEN={C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN}",
        ),
    )
    return (*historical, *today)


def evaluate_today_live_equity_stock_kind_set_v1() -> tuple[LiveEquityStockMembershipRecordV1, ...]:
    records = tuple(
        evaluate_live_equity_stock_kind_membership_v1(candidate)
        for candidate in build_today_live_equity_stock_candidates_v1()
    )
    ordered = tuple(sorted(records, key=lambda item: item.candidate_id))
    replay = tuple(
        evaluate_live_equity_stock_kind_membership_v1(candidate)
        for candidate in sorted(
            build_today_live_equity_stock_candidates_v1(),
            key=lambda item: item.candidate_id,
        )
    )
    replay_ids = tuple((item.candidate_id, item.reason_code, item.member) for item in replay)
    ordered_ids = tuple((item.candidate_id, item.reason_code, item.member) for item in ordered)
    if replay_ids != ordered_ids:
        raise LiveEquityStockKindSetDefinitionError("MEMBERSHIP_EVALUATION_NOT_DETERMINISTIC")
    return ordered


def ratified_live_equity_stock_kind_set_v1(
    records: Sequence[LiveEquityStockMembershipRecordV1] | None = None,
) -> tuple[str, ...]:
    evaluated = records if records is not None else evaluate_today_live_equity_stock_kind_set_v1()
    members = tuple(item.candidate_id for item in evaluated if item.member == TRUE_TOKEN)
    if members:
        raise LiveEquityStockKindSetDefinitionError(
            f"KIND_INVENTED_OR_UNPROVEN_MEMBER:{','.join(members)}"
        )
    return members


def build_live_equity_stock_kind_set_definition_v1() -> LiveEquityStockKindSetDefinitionV1:
    records = evaluate_today_live_equity_stock_kind_set_v1()
    members = ratified_live_equity_stock_kind_set_v1(records)
    rejected = tuple(item.candidate_id for item in records if item.member != TRUE_TOKEN)
    kind_set = KIND_SET_EMPTY if not members else ",".join(members)
    if kind_set != LIVE_EQUITY_STOCK_KIND_SET:
        raise LiveEquityStockKindSetDefinitionError("LIVE_KIND_SET_DRIFT")
    return LiveEquityStockKindSetDefinitionV1(
        definition_class="NEW_CANONICAL_DEFINITION",
        definition_id=LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        live_equity_stock_kind_set=kind_set,
        live_equity_stock_kind_set_resolved=FALSE_TOKEN,
        kind_set_members=members,
        kind_set_rejected_candidates=rejected,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        new_canonical_definition=TRUE_TOKEN,
        kinds_invented_this_go=FALSE_TOKEN,
    )


def join_live_kind_set_definition_to_d6_diagnostics_v1(
    *,
    existing: Mapping[str, Any],
    definition: LiveEquityStockKindSetDefinitionV1,
    records: Sequence[LiveEquityStockMembershipRecordV1],
) -> dict[str, Any]:
    attached = dict(existing)
    additions = {
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": definition.definition_id,
        "LIVE_EQUITY_STOCK_KIND_SET": definition.live_equity_stock_kind_set,
        "LIVE_EQUITY_STOCK_KIND_SET_RESOLVED": definition.live_equity_stock_kind_set_resolved,
        "LIVE_CRITICAL_DEFINITION_CLASS": definition.definition_class,
        "NEW_CANONICAL_DEFINITION": definition.new_canonical_definition,
        "LEGACY_SEMANTICS_RECONSTRUCTED": definition.legacy_semantics_reconstructed,
        "KIND_SET_MEMBER_COUNT": str(len(definition.kind_set_members)),
        "KIND_SET_REJECTED_CANDIDATE_COUNT": str(len(definition.kind_set_rejected_candidates)),
        "MEMBERSHIP_RECORD_COUNT": str(len(records)),
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "KINDS_INVENTED_THIS_GO": definition.kinds_invented_this_go,
        "VENUE_POST_COUNT": "0",
        "VENUE_EQ_ROLE": ROLE_RECONCILIATION_TARGET_ONLY,
        "U04_ROLE": ROLE_AVAILABLE_CAPITAL_ONLY,
        "U05_ROLE": ROLE_UNRESOLVED,
        "U06_ROLE": ROLE_UNRESOLVED,
        "P01_ROLE": ROLE_RISK_CAPITAL_REDUCTION_ONLY,
    }
    for key, value in additions.items():
        if key in attached and attached[key] != value:
            raise LiveEquityStockKindSetDefinitionError(f"DIAGNOSTIC_AUTHORITY_COLLISION:{key}")
        attached[key] = value
    return attached


def execute_live_equity_stock_kind_set_new_canonical_definition_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bm_pack: Path,
    evidence_root: Path,
    persist_as_of: str,
) -> LiveEquityStockKindSetDefinitionResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise LiveEquityStockKindSetDefinitionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise LiveEquityStockKindSetDefinitionError("ORIGIN_MAIN_SHA_MISMATCH")
    bm_pack = Path(sealed_bm_pack)
    try:
        manifest_rc = verify_manifest_sha256_v1(store_root=bm_pack)
    except Exception as exc:
        raise LiveEquityStockKindSetDefinitionError("BM_MANIFEST_VERIFY_FAILED") from exc
    if manifest_rc != 0:
        raise LiveEquityStockKindSetDefinitionError("BM_MANIFEST_VERIFY_FAILED")
    claims_path = bm_pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise LiveEquityStockKindSetDefinitionError("BM_CLAIMS_MISSING")
    try:
        bm_claims = _load_json_object(path=claims_path)
    except json.JSONDecodeError as exc:
        raise LiveEquityStockKindSetDefinitionError("BM_CLAIMS_MALFORMED") from exc
    _require_token(field="KIND_SET", payload=bm_claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=bm_claims, expected=FALSE_TOKEN)
    _require_token(field="LIVE_CRITICAL_KIND_SET", payload=bm_claims, expected=KIND_SET_EMPTY)
    _require_token(field="GATE_A_EXECUTED", payload=bm_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bm_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bm_claims, expected="0")
    _require_token(field="VENUE_POST_COUNT", payload=bm_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bm_claims, expected=FALSE_TOKEN)
    _require_token(field="KINDS_INVENTED_THIS_GO", payload=bm_claims, expected=FALSE_TOKEN)
    _require_token(
        field="HISTORICAL_UNKNOWN_ON_CRITICAL_PATH",
        payload=bm_claims,
        expected=FALSE_TOKEN,
    )
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=bm_claims, expected=OWNER_GO)
    _require_token(field="F12_DECISION", payload=bm_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F13_DECISION", payload=bm_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_KIND_DECISION", payload=bm_claims, expected=DECISION_REMAIN_UNKNOWN)
    reject_claimed_live_kind_set_authority_mutation_v1(
        claimed_proof="NEW_CANONICAL_DEFINITION_EMPTY_FAIL_CLOSED",
        candidate_id=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    )
    reject_claimed_live_kind_set_authority_mutation_v1(
        claimed_proof="HISTORICAL_UNKNOWN_NOT_LIVE_KIND_SET_MEMBER",
        candidate_id=FACT_F12,
    )
    records = evaluate_today_live_equity_stock_kind_set_v1()
    definition = build_live_equity_stock_kind_set_definition_v1()
    standing = {
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "GATE_A_ID": GATE_A_ID,
        "GATE_B_ID": GATE_B_ID,
    }
    diagnostics = join_live_kind_set_definition_to_d6_diagnostics_v1(
        existing=standing,
        definition=definition,
        records=records,
    )
    folder = _folder_from_as_of(persist_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": "NONE",
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": persist_as_of,
        "SEALED_BM_PACK": CANONICAL_BM_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "BM_CONTRACT_REUSED": TRUE_TOKEN,
        "VENUE_GET_COUNT": "0",
        "VENUE_POST_COUNT": "0",
        "POST_COUNT": "0",
        "GATE_A_EXECUTED": FALSE_TOKEN,
        "GATE_B_EXECUTED": FALSE_TOKEN,
        "UNKNOWN_SEMANTICS_INVENTED": FALSE_TOKEN,
        "KINDS_INVENTED_THIS_GO": FALSE_TOKEN,
        "LEGACY_SEMANTICS_RECONSTRUCTED": FALSE_TOKEN,
        "NEW_CANONICAL_DEFINITION": TRUE_TOKEN,
        "HISTORICAL_UNKNOWN_ON_CRITICAL_PATH": FALSE_TOKEN,
        "HISTORICAL_UNKNOWN_CHANGED": FALSE_TOKEN,
        "LIVE_CRITICAL_DEFINITION_CLASS": definition.definition_class,
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": definition.definition_id,
        "LIVE_EQUITY_STOCK_KIND_SET": definition.live_equity_stock_kind_set,
        "LIVE_EQUITY_STOCK_KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_MEMBERS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        "BM_LIVE_BLOCKER_CONSUMED": BM_LIVE_BLOCKER,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "F12_STATUS": "UNRESOLVED",
        "F13_STATUS": "UNRESOLVED",
        "U05_STATUS": "UNRESOLVED",
        "F16_STATUS": "UNRESOLVED",
        "F17_STATUS": "UNRESOLVED",
        "F18_STATUS": "UNRESOLVED",
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "VENUE_EQ_ROLE": ROLE_RECONCILIATION_TARGET_ONLY,
        "U04_ROLE": ROLE_AVAILABLE_CAPITAL_ONLY,
        "U05_ROLE": ROLE_UNRESOLVED,
        "U06_ROLE": ROLE_UNRESOLVED,
        "P01_ROLE": ROLE_RISK_CAPITAL_REDUCTION_ONLY,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "BULL_BEAR_STATE_SWITCH_UNCHANGED": TRUE_TOKEN,
        "TOP20_RANKING_UNIVERSE_UNCHANGED": TRUE_TOKEN,
        "TOP20_SELECTION_BINDINGS_UNCHANGED": TRUE_TOKEN,
        "SELF_LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_AUTONOMY_UNCHANGED": TRUE_TOKEN,
        "STEP_29P_UNCHANGED": TRUE_TOKEN,
        "BM_MANIFEST_VERIFY_RC": "0",
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "membership_v1.json",
        payload={
            item.candidate_id: {
                "source_role": item.source_role,
                "layer": item.layer,
                "member": item.member,
                "reason_code": item.reason_code,
                "reason_precedence_index": item.reason_precedence_index,
                "eligibility_failures": list(item.eligibility_failures),
            }
            for item in records
        },
    )
    _persist_json(
        path=store / "kind_set_definition_v1.json",
        payload={
            "definition_class": definition.definition_class,
            "definition_id": definition.definition_id,
            "live_equity_stock_kind_set": definition.live_equity_stock_kind_set,
            "live_equity_stock_kind_set_resolved": definition.live_equity_stock_kind_set_resolved,
            "kind_set_members": list(definition.kind_set_members),
            "kind_set_rejected_candidates": list(definition.kind_set_rejected_candidates),
            "eligibility_criteria": list(ELIGIBILITY_CRITERIA),
            "reason_precedence": list(REASON_PRECEDENCE),
            "legacy_semantics_reconstructed": definition.legacy_semantics_reconstructed,
            "new_canonical_definition": definition.new_canonical_definition,
            "kinds_invented_this_go": definition.kinds_invented_this_go,
        },
    )
    _persist_json(
        path=store / "source_role_matrix_v1.json",
        payload={
            CANDIDATE_VENUE_EQ: ROLE_RECONCILIATION_TARGET_ONLY,
            CANDIDATE_U04: ROLE_AVAILABLE_CAPITAL_ONLY,
            CANDIDATE_U05: ROLE_UNRESOLVED,
            CANDIDATE_U06: ROLE_UNRESOLVED,
            CANDIDATE_P01: ROLE_RISK_CAPITAL_REDUCTION_ONLY,
            CANDIDATE_GOVERNED_CHECKPOINT: ROLE_NON_SOURCE,
            CANDIDATE_CLASSIFIED_EVENT_STREAM: ROLE_EQUITY_FLOW_SOURCE,
            CANDIDATE_C17: ROLE_UNRESOLVED,
            FACT_F12: ROLE_UNRESOLVED,
            FACT_F13: ROLE_UNRESOLVED,
            FACT_U05: ROLE_UNRESOLVED,
            FACT_F16: ROLE_UNRESOLVED,
            FACT_F17: ROLE_UNRESOLVED,
            FACT_F18: ROLE_UNRESOLVED,
        },
    )
    _persist_json(path=store / "d6_diagnostics_v1.json", payload=diagnostics)
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "reconstruct_historical_unknown": "FORBIDDEN",
            "invent_live_source_kind": "FORBIDDEN",
            "promote_eq_to_source": "FORBIDDEN",
            "empty_live_kind_set": KIND_SET_EMPTY,
            "double_count_guard": "STOCK_AND_FLOW_MAY_NOT_BOTH_COUNT",
            "embedding_rule": "UNPROVEN_EMBEDDING_IS_NOT_STOCK_MEMBERSHIP",
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "venue_get_count": "0",
            "venue_post_count": "0",
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bm_pack": CANONICAL_BM_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return LiveEquityStockKindSetDefinitionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        live_equity_stock_kind_set=definition.live_equity_stock_kind_set,
        live_equity_stock_kind_set_resolved=FALSE_TOKEN,
        kind_set_members=NONE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        venue_get_count="0",
        venue_post_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
        kinds_invented_this_go=FALSE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "CANDIDATE_C17",
    "CANDIDATE_CLASSIFIED_EVENT_STREAM",
    "CANDIDATE_GOVERNED_CHECKPOINT",
    "CANDIDATE_P01",
    "CANDIDATE_U04",
    "CANDIDATE_U05",
    "CANDIDATE_U06",
    "CANDIDATE_VENUE_EQ",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "ELIGIBILITY_CRITERIA",
    "LIVE_EQUITY_STOCK_KIND_SET",
    "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY",
    "LiveEquityStockKindCandidateV1",
    "LiveEquityStockKindSetDefinitionError",
    "LiveEquityStockKindSetDefinitionResultV1",
    "LiveEquityStockKindSetDefinitionV1",
    "LiveEquityStockMembershipRecordV1",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "REASON_PRECEDENCE",
    "ROLE_AVAILABLE_CAPITAL_ONLY",
    "ROLE_EQUITY_FLOW_SOURCE",
    "ROLE_EQUITY_STOCK_SOURCE",
    "ROLE_NON_SOURCE",
    "ROLE_OTHER_DOMAIN",
    "ROLE_PLACEMENT_CAPACITY_ONLY",
    "ROLE_RECONCILIATION_TARGET_ONLY",
    "ROLE_RISK_CAPITAL_REDUCTION_ONLY",
    "ROLE_UNRESOLVED",
    "build_live_equity_stock_kind_set_definition_v1",
    "build_today_live_equity_stock_candidates_v1",
    "evaluate_live_equity_stock_kind_membership_v1",
    "evaluate_today_live_equity_stock_kind_set_v1",
    "execute_live_equity_stock_kind_set_new_canonical_definition_v1",
    "join_live_kind_set_definition_to_d6_diagnostics_v1",
    "ratified_live_equity_stock_kind_set_v1",
    "reason_precedence_index_v1",
    "reject_claimed_live_kind_set_authority_mutation_v1",
]
