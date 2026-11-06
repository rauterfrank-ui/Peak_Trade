"""Qualify and bind one new U05 event surface to the pre-acquisition boundary.

Consumes the Owner-GO that fulfills the §11.2.1.CB next-GO. Inspects a
bounded census of previously unadjudicated official EEA GET surfaces,
selects exactly one EVENT_SURFACE, and binds only a pre-acquisition
contract if all positive capability predicates pass. Does not GET.
Does not POST. Does not treat the surface as an embedding witness.
Does not use acctLv=2 as a standalone disqualifier. Empty/zero/absent
remain UNKNOWN. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    ACQUISITION_SURFACE,
    CLASS_U05,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    PROOF_OBJECT_U05,
    evaluate_u05_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CB_PACK_RELPATH,
    NEXT_OWNER_GO as PARENT_CB_NEXT_OWNER_GO,
    PRODUCER_ID,
    PRODUCER_STATUS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANDIDATE_SURFACE_SELECTION,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    SELECTED_BALANCE_SURFACE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    AUTHORIZED_ANCHOR_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_RESOLVED_STATUS,
    P01_U05_OVERLAP_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.scoped_read_only_observation_boundary_contract_v1 import (
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    CANDIDATE_SURFACE_TRADE_FILLS,
    DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1 import (
    CANDIDATE_SURFACE_BILLS_ARCHIVE,
)


def _fail_closed_credential_unavailable_v1(*_a, **_k):
    raise RuntimeError("CREDENTIAL_HANDLE_FAIL_CLOSED")


OWNER_GO = (
    "QUALIFY_AND_BIND_EXACTLY_ONE_NEW_INDEPENDENT_LIABILITY_EVENT_SURFACE_OR_"
    "NON_ALGEBRAIC_EMBEDDING_WITNESS_NOT_IN_PRIOR_FOUR_CANDIDATES_TO_"
    "ACQUISITION_BOUNDARY_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "6653fd920843179d14a88de66a1b3205cb6a9daf"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_u05_independent_liability_event_surface_or_"
    "embedding_witness_qualification_v1/2026-09-15T003000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T00:30:00Z"
SCHEMA_CLASS = "U05_INDEPENDENT_LIABILITY_EVENT_SURFACE_OR_EMBEDDING_WITNESS_QUALIFICATION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
UNKNOWN_TOKEN = "UNKNOWN"
SELECTED_SURFACE_ID = "GET_/api/v5/account/interest-accrued"
SELECTED_ENDPOINT_PATH = "/api/v5/account/interest-accrued"
HTTP_METHOD = "GET"
SELECTED_CANDIDATE_KIND = "EVENT_SURFACE"
BINDING_STATUS = "PRE_ACQUISITION_CONTRACT_BOUND"
PRIMARY_PROOF_ROLE = "INDEPENDENT_LIABILITY_EVENT_SURFACE_NOT_EMBEDDING_WITNESS"
PRIMARY_PROOF_STATUS = "NOT_ACQUIRED_EVENT_SURFACE_PRE_ACQUISITION_BOUND_EMBEDDING_WITNESS_UNBOUND"
DECISION_BASIS = "EVENT_SURFACE_PRE_ACQUISITION_BOUND_NO_GET_EXECUTED_EMBEDDING_WITNESS_UNBOUND"
BLOCKER_ID = (
    "INDEPENDENT_LIABILITY_EVENT_NOT_ACQUIRED_AND_NON_ALGEBRAIC_EMBEDDING_"
    "WITNESS_STILL_UNBOUND_AFTER_INTEREST_ACCRUED_PRE_ACQUISITION_BINDING"
)
ARCHITECTURE_BLOCKER = (
    "U05_STILL_REQUIRES_SEPARATELY_AUTHORIZED_ACQUISITION_AND_INDEPENDENT_"
    "NON_ALGEBRAIC_EMBEDDING_WITNESS"
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_EXECUTE_EXACTLY_ONE_BOUND_U05_PRIMARY_PROOF_GET_OR_WITNESS_ACQUISITION_V1"
)
NEXT_ACTION = "STOP_AWAIT_OWNER_MERGE_GO"
SECRET_RESOLUTION_NOT_ATTEMPTED = "NOT_ATTEMPTED_PRE_ACQUISITION_BOUNDARY_NO_GET"
VENUE_AUTHORITY_SOURCE = "https://my.okx.com/docs-v5/en/"
VENUE_REST_BASE = "https://eea.okx.com"
FUTURE_MAX_GET_COUNT = "1"
LOAN_TYPE_MARKET = "2"
PRIOR_FOUR_SURFACES: tuple[str, ...] = (
    SELECTED_BALANCE_SURFACE,
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    CANDIDATE_SURFACE_BILLS_ARCHIVE,
    CANDIDATE_SURFACE_TRADE_FILLS,
)
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
CLAIMS_FILE = "claims.json"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class U05IndependentLiabilityEventSurfaceQualificationError(ValueError):
    """Fail-closed U05 event-surface qualification violation."""


@dataclass(frozen=True)
class U05IndependentLiabilityEventSurfaceQualificationResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    selected_single_candidate_id: str
    selected_candidate_kind: str
    surface_or_witness_bindable: str
    binding_status: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    future_max_get_count_if_separately_authorized: str
    vault_available: str
    secret_resolution_status: str
    u05_primary_proof_status: str
    u05_decision_after: str
    u05_decision_basis: str
    productive_acquisition_executed: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None or isinstance(raw, bool) or not isinstance(raw, str):
        raise U05IndependentLiabilityEventSurfaceQualificationError(f"FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise U05IndependentLiabilityEventSurfaceQualificationError(f"FIELD_MISSING:{field}")
    return text


def _assert_no_secret_material(*, blob: str, label: str) -> None:
    lowered = blob.lower()
    for marker in SECRET_MARKERS:
        if marker in lowered:
            raise U05IndependentLiabilityEventSurfaceQualificationError(f"SECRET_MARKER_IN_{label}")


def _assert_standing_pins() -> None:
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U05IndependentLiabilityEventSurfaceQualificationError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if CANDIDATE_SURFACE_SELECTION != "NONE_SELECTED":
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "CANDIDATE_SURFACE_SELECTION_NOT_NONE"
        )
    if MS2_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "BILLS_MUST_REMAIN_NONCANONICAL"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U05IndependentLiabilityEventSurfaceQualificationError("DAG_PIN_DRIFT")
    if P01_U05_OVERLAP_STATE != "UNRESOLVED":
        raise U05IndependentLiabilityEventSurfaceQualificationError("P01_U05_OVERLAP_STATE_DRIFT")
    if P01_U05_OVERLAP_RESOLVED_STATUS != FALSE_TOKEN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "P01_U05_OVERLAP_MUST_REMAIN_UNRESOLVED"
        )


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise U05IndependentLiabilityEventSurfaceQualificationError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _assert_parent_cb_pack(*, sealed_cb_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_cb_pack) != 0:
        raise U05IndependentLiabilityEventSurfaceQualificationError("CB_MANIFEST_MISMATCH")
    claims = _load_json_object(path=sealed_cb_pack / CLAIMS_FILE)
    if claims.get("U05_DECISION_AFTER") != DECISION_REMAIN_UNKNOWN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "PARENT_CB_U05_NOT_REMAIN_UNKNOWN"
        )
    if claims.get("PRODUCTIVE_ACQUISITION_EXECUTED") != FALSE_TOKEN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "PARENT_CB_MUST_NOT_HAVE_ACQUIRED"
        )
    if claims.get("SURFACE_BINDING_STATUS") != "NOT_BOUND":
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "PARENT_CB_SURFACE_MUST_REMAIN_UNBOUND"
        )
    if claims.get("NEXT_OWNER_GO_REQUIRED") != PARENT_CB_NEXT_OWNER_GO:
        raise U05IndependentLiabilityEventSurfaceQualificationError("PARENT_CB_NEXT_OWNER_GO_DRIFT")
    if claims.get("PRODUCER_ID") != PRODUCER_ID:
        raise U05IndependentLiabilityEventSurfaceQualificationError("PARENT_CB_PRODUCER_ID_DRIFT")
    if claims.get("BORROW_OR_ACCOUNT_LIABILITY_STATE_PRODUCER_STATUS") != PRODUCER_STATUS:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "PARENT_CB_PRODUCER_STATUS_DRIFT"
        )


def _inspect_vault_presence(*, repo: Path, vault_file: Path | str | None) -> dict[str, str]:
    resolved = (
        Path(vault_file)
        if vault_file is not None
        else _fail_closed_credential_unavailable_v1(repo_root=repo)
    )
    presence = _fail_closed_credential_unavailable_v1(vault_file=resolved)
    if presence.get("VALUES_INCLUDED") is not False:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "SECRET_VALUES_MUST_NOT_BE_INCLUDED"
        )
    available = presence.get("available") is True
    reason = str(presence.get("reason") or NONE_TOKEN)
    payload = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "vault_file_present": TRUE_TOKEN if presence.get("VAULT_FILE_PRESENT") else FALSE_TOKEN,
        "secretref_uri_bound": TRUE_TOKEN if presence.get("SECRETREF_URI_BOUND") else FALSE_TOKEN,
        "credential_fields_complete": (
            TRUE_TOKEN if presence.get("CREDENTIAL_FIELDS_COMPLETE") else FALSE_TOKEN
        ),
        "values_included": FALSE_TOKEN,
        "available": TRUE_TOKEN if available else FALSE_TOKEN,
        "reason": reason,
        "secret_resolution_status": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "secrets_or_signatures_persisted": FALSE_TOKEN,
    }
    _assert_no_secret_material(blob=_canonical_json(payload), label="VAULT_PRESENCE")
    return payload


def build_prior_four_exclusion_v1() -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "prior_four_candidates_excluded": TRUE_TOKEN,
        "excluded_surface_ids": list(PRIOR_FOUR_SURFACES),
        "repackage_forbidden": TRUE_TOKEN,
        "alias_pagination_archive_relabel_forbidden": TRUE_TOKEN,
        "source_pack": CANONICAL_CB_PACK_RELPATH,
    }


def build_venue_specification_excerpts_v1() -> dict[str, Any]:
    return {
        "layer": "VENUE_SPECIFICATION",
        "venue_authority_source": VENUE_AUTHORITY_SOURCE,
        "venue_rest_base": VENUE_REST_BASE,
        "not_forum_not_sdk_not_snippet": TRUE_TOKEN,
        "records": [
            {
                "excerpt_id": "EEA_PRODUCTION_REST_BASE",
                "text": "REST: https://eea.okx.com",
            },
            {
                "excerpt_id": "ACCTLV_FUTURES_MODE",
                "text": "acctLv Account mode 1: Spot mode 2: Futures mode 3: Multi-currency margin 4: Portfolio margin",
            },
            {
                "excerpt_id": "INTEREST_ACCRUED_IDENTITY",
                "text": "Get interest accrued data. GET /api/v5/account/interest-accrued. Get the interest accrued data for the past year.",
            },
            {
                "excerpt_id": "INTEREST_ACCRUED_LOAN_TYPE",
                "text": "type Loan type 2: Market loans Default is 2. ccy Loan currency Only applicable to Market loans Only applicable to MARGIN.",
            },
            {
                "excerpt_id": "INTEREST_ACCRUED_FIELDS",
                "text": "ccy Loan currency. instId Instrument ID Only applicable to Market loans. mgnMode Margin mode cross isolated. interest Interest accrued. interestRate Hourly borrowing interest rate. liab Liability. totalLiab Total liability for current account. interestFreeLiab Interest-free liability for current account. ts Timestamp for interest accrued.",
            },
            {
                "excerpt_id": "MARGIN_ISOLATED_MAX_LOAN_FUTURES_MODE",
                "text": "Max loan of isolated MARGIN in Futures mode. Max loan of cross MARGIN in Futures mode. mgnCcy Applicable to isolated MARGIN and cross MARGIN in Futures mode.",
            },
            {
                "excerpt_id": "SET_LEVERAGE_MARGIN_FUTURES_MODE",
                "text": "Set leverage for MARGIN instruments under cross-margin trade mode and Futures mode account mode at pairs level.",
            },
            {
                "excerpt_id": "SPOT_BORROW_REPAY_HISTORY_SPOT_MODE_ONLY",
                "text": "Get borrow/repay history. Retrieve the borrow/repay history under Spot mode. GET /api/v5/account/spot-borrow-repay-history.",
            },
            {
                "excerpt_id": "INTEREST_LIMITS_STATE",
                "text": "Get borrow interest and limit. GET /api/v5/account/interest-limits. debt Current debt in USD. usedLmt Borrowed amount for current account.",
            },
            {
                "excerpt_id": "ENABLE_SPOT_BORROW_IS_SPOT_MODE",
                "text": "enableSpotBorrow Whether borrow is allowed or not in Spot mode true: Enabled false: Disabled",
            },
        ],
    }


def build_bounded_candidate_census_v1() -> dict[str, Any]:
    records = [
        {
            "surface_id": SELECTED_SURFACE_ID,
            "kind": "EVENT_SURFACE",
            "selected": TRUE_TOKEN,
            "http_method": HTTP_METHOD,
            "why_inspected": "OFFICIAL_EEA_HISTORICAL_INTEREST_AND_LIABILITY_FIELDS_WITH_TS",
            "not_selected_reason": NONE_TOKEN,
        },
        {
            "surface_id": "GET_/api/v5/account/spot-borrow-repay-history",
            "kind": "EVENT_SURFACE",
            "selected": FALSE_TOKEN,
            "http_method": HTTP_METHOD,
            "why_inspected": "EXPLICIT_BORROW_REPAY_EVENT_TYPES",
            "not_selected_reason": "OFFICIAL_EEA_TEXT_RESTRICTS_SURFACE_TO_SPOT_MODE",
        },
        {
            "surface_id": "GET_/api/v5/account/interest-limits",
            "kind": "EVENT_SURFACE",
            "selected": FALSE_TOKEN,
            "http_method": HTTP_METHOD,
            "why_inspected": "DOCUMENTED_DEBT_AND_INTEREST_FIELDS",
            "not_selected_reason": "STATE_OR_LIMIT_SNAPSHOT_NOT_STRONGEST_EVENT_RECORD_SURFACE",
        },
        {
            "surface_id": "GET_/api/v5/account/max-loan",
            "kind": "EVENT_SURFACE",
            "selected": FALSE_TOKEN,
            "http_method": HTTP_METHOD,
            "why_inspected": "DOCUMENTED_FUTURES_MODE_MARGIN_LOAN_CAPACITY",
            "not_selected_reason": "MAX_LOAN_CAPACITY_IS_NOT_LIABILITY_EVENT_OR_STATE_RECORD",
        },
        {
            "surface_id": "GET_/api/v5/account/max-withdrawal",
            "kind": "EMBEDDING_WITNESS",
            "selected": FALSE_TOKEN,
            "http_method": HTTP_METHOD,
            "why_inspected": "DISTINGUISHES_VALUES_INCLUDING_EXCLUDING_BORROWED_ASSETS",
            "not_selected_reason": "NOT_INDEPENDENT_LIABILITY_EVENT_AND_NOT_NON_ALGEBRAIC_EMBEDDING_WITNESS",
        },
    ]
    selected = [item for item in records if item["selected"] == TRUE_TOKEN]
    if len(selected) != 1:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "CENSUS_MUST_SELECT_EXACTLY_ONE"
        )
    if selected[0]["surface_id"] != SELECTED_SURFACE_ID:
        raise U05IndependentLiabilityEventSurfaceQualificationError("CENSUS_SELECTED_SURFACE_DRIFT")
    if any(item["surface_id"] in PRIOR_FOUR_SURFACES for item in records):
        raise U05IndependentLiabilityEventSurfaceQualificationError("PRIOR_FOUR_REOPENED")
    return {
        "layer": "CANONICAL_AUTHORITY",
        "candidate_census_count": str(len(records)),
        "selected_single_candidate_id": SELECTED_SURFACE_ID,
        "selected_candidate_kind": SELECTED_CANDIDATE_KIND,
        "why_this_single_candidate_selected": (
            "STRONGEST_PREVIOUSLY_UNADJUDICATED_EEA_GET_WITH_EXPLICIT_LIAB_INTEREST_TS_"
            "AND_NOT_SPOT_MODE_RESTRICTED"
        ),
        "prior_four_candidates_excluded": TRUE_TOKEN,
        "acctlv2_alone_is_not_a_disqualifier": TRUE_TOKEN,
        "embedding_witness_not_pursued": TRUE_TOKEN,
        "records": records,
    }


def evaluate_selected_event_surface_predicates_v1() -> dict[str, Any]:
    predicates = {
        "exact_surface_identity": TRUE_TOKEN,
        "read_only_proven": TRUE_TOKEN,
        "account_scope_capability": TRUE_TOKEN,
        "liability_identity_capability": TRUE_TOKEN,
        "time_event_identity_capability": TRUE_TOKEN,
        "currency_scope_capability": TRUE_TOKEN,
        "distinct_from_fees_fills_trades_transfers_balance_residuals": TRUE_TOKEN,
        "raw_evidence_separable_from_interpretation": TRUE_TOKEN,
        "compatible_with_existing_producer_without_redesign": TRUE_TOKEN,
        "equity_stock_effect_capability": FALSE_TOKEN,
        "independence_from_reconstruction_algebra": TRUE_TOKEN,
        "non_algebraic_embedding_capability": FALSE_TOKEN,
        "once_only_effect_capability": FALSE_TOKEN,
        "double_counting_safety_capability": TRUE_TOKEN,
    }
    reasons = {
        "exact_surface_identity": "OFFICIAL_EEA_DOCUMENTS_GET_/api/v5/account/interest-accrued",
        "read_only_proven": "OFFICIAL_EEA_HTTP_METHOD_IS_GET_NO_MUTATION_SEMANTICS",
        "account_scope_capability": (
            "EEA_TRADING_ACCOUNT_GET_DOCUMENTED_AND_MARGIN_MARKET_LOANS_DOCUMENTED_"
            "UNDER_FUTURES_MODE_SO_ACCTLV2_IS_NOT_A_DISQUALIFIER;AUTHENTICATED_D4_"
            "SESSION_SUPPLIES_ACCOUNT_IDENTITY;CURRENT_MARGIN_LOAN_PRESENCE_REMAINS_UNKNOWN"
        ),
        "liability_identity_capability": (
            "OFFICIAL_EEA_FIELDS_LIAB_LIABILITY_TOTALLIAB_INTEREST_ACCRUED_"
            "INTEREST_RATE_HOURLY_BORROWING"
        ),
        "time_event_identity_capability": "OFFICIAL_EEA_TS_IS_TIMESTAMP_FOR_INTEREST_ACCRUED",
        "currency_scope_capability": "OFFICIAL_EEA_CCY_IS_LOAN_CURRENCY",
        "distinct_from_fees_fills_trades_transfers_balance_residuals": (
            "DISTINCT_ENDPOINT_FROM_PRIOR_FOUR_AND_DOCUMENTED_AS_INTEREST_ACCRUED_"
            "LIABILITY_NOT_TRADE_FILL_FEE_TRANSFER_OR_GENERIC_BALANCE_SNAPSHOT"
        ),
        "raw_evidence_separable_from_interpretation": (
            "PRE_ACQUISITION_CONTRACT_REQUIRES_RAW_HTTP_BODY_PERSIST_SEPARATE_FROM_INTERPRETATION"
        ),
        "compatible_with_existing_producer_without_redesign": (
            f"EXISTING_{PRODUCER_ID}_ACCEPTS_RAW_SOURCE_INDEPENDENT_LIABILITY_EVENT_RECORD"
        ),
        "equity_stock_effect_capability": (
            "SURFACE_CAN_EVIDENCE_LIABILITY_OR_INTEREST_RECORDS_BUT_DOES_NOT_PROVE_"
            "EQUITY_STOCK_EFFECT_WITHOUT_SEPARATE_EMBEDDING_WITNESS"
        ),
        "independence_from_reconstruction_algebra": (
            "SURFACE_IS_VENUE_INTEREST_ACCRUED_RECORD_NOT_P01_OR_EQ_RESIDUAL_ALGEBRA"
        ),
        "non_algebraic_embedding_capability": (
            "SELECTED_AS_EVENT_SURFACE_NOT_EMBEDDING_WITNESS;LIAB_TOTALLIAB_VALUES_"
            "MUST_NOT_BE_USED_TO_INFER_P01_U05_OVERLAP_OR_EMBEDDING"
        ),
        "once_only_effect_capability": "ONCE_ONLY_EQUITY_STOCK_EFFECT_NOT_ESTABLISHED_BY_THIS_SURFACE_ALONE",
        "double_counting_safety_capability": (
            "CONTRACT_FORBIDS_COUNTING_BALANCE_SNAPSHOT_LIAB_AND_INTEREST_ACCRUED_LIAB_"
            "AS_THE_SAME_EVENT_AND_FORBIDS_ALGEBRAIC_EQ_IDENTITY"
        ),
    }
    required_for_bind = (
        "exact_surface_identity",
        "read_only_proven",
        "account_scope_capability",
        "liability_identity_capability",
        "time_event_identity_capability",
        "currency_scope_capability",
        "distinct_from_fees_fills_trades_transfers_balance_residuals",
        "raw_evidence_separable_from_interpretation",
        "compatible_with_existing_producer_without_redesign",
    )
    missing = [name for name in required_for_bind if predicates[name] != TRUE_TOKEN]
    if missing:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            f"REQUIRED_PREDICATE_NOT_PROVEN:{','.join(missing)}"
        )
    if predicates["non_algebraic_embedding_capability"] == TRUE_TOKEN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "EMBEDDING_WITNESS_CLAIM_FORBIDDEN_ON_EVENT_SURFACE"
        )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "selected_single_candidate_id": SELECTED_SURFACE_ID,
        "selected_candidate_kind": SELECTED_CANDIDATE_KIND,
        "venue_authority_source": VENUE_AUTHORITY_SOURCE,
        "venue_capability_proven": TRUE_TOKEN,
        "read_only_proven": TRUE_TOKEN,
        "acctlv2_alone_used_as_disqualifier": FALSE_TOKEN,
        "margin_under_futures_mode_documented": TRUE_TOKEN,
        "current_bound_account_margin_loan_presence": UNKNOWN_TOKEN,
        "surface_or_witness_bindable": TRUE_TOKEN,
        "predicates": predicates,
        "predicate_reasons": reasons,
        "required_bind_predicates": list(required_for_bind),
    }


def build_pre_acquisition_contract_v1(
    *, d4_identity_digest: str, d5_binding_id: str
) -> dict[str, Any]:
    account = _require_non_empty_str(field="d4_identity_digest", raw=d4_identity_digest)
    window = _require_non_empty_str(field="d5_binding_id", raw=d5_binding_id)
    return {
        "layer": "CANONICAL_AUTHORITY",
        "surface_id": SELECTED_SURFACE_ID,
        "http_method": HTTP_METHOD,
        "endpoint_path": SELECTED_ENDPOINT_PATH,
        "venue_host": "eea.okx.com",
        "venue_authority_source": VENUE_AUTHORITY_SOURCE,
        "account_scope": f"D4_BOUND_AUTHENTICATED_EEA_TRADING_ACCOUNT:{account}",
        "instrument_scope": "UNBOUND_INSTID_OPTIONAL_AND_ONLY_APPLICABLE_TO_MARKET_LOANS",
        "currency_scope": "PER_ROW_CCY_LOAN_CURRENCY_NOT_PREBOUND",
        "time_scope": (
            f"VENUE_DOCUMENTED_PAST_YEAR_INTEREST_ACCRUED_TS;D5_WINDOW={window};"
            "AFTER_BEFORE_NOT_AUTHORIZED_IN_THIS_CONTRACT"
        ),
        "expected_response_class": (
            "RAW_OKX_JSON_ARRAY_OF_INTEREST_ACCRUED_RECORDS_WITH_CCY_INTEREST_LIAB_TS"
        ),
        "loan_type": LOAN_TYPE_MARKET,
        "query_type": LOAN_TYPE_MARKET,
        "query_limit": "100",
        "future_max_get_count_if_separately_authorized": FUTURE_MAX_GET_COUNT,
        "retry_allowed": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "productive_acquisition_authorized": FALSE_TOKEN,
        "authorized_get_count": "0",
        "actual_get_count": "0",
        "post_count": "0",
        "raw_evidence_persistence_contract": (
            "PERSIST_RAW_HTTP_STATUS_VENUE_CODE_AND_BODY_SEPARATE_FROM_INTERPRETATION_"
            "BEFORE_ANY_PRODUCER_CLASSIFICATION"
        ),
        "eligibility_predicates": (
            "SEPARATE_CURRENT_OWNER_GO_REQUIRED;EXACT_SURFACE_ONLY;TYPE_2_MARKET_LOANS;"
            "NO_RETRY;NO_PAGINATION_GET;EMPTY_ZERO_ABSENT_REMAIN_UNKNOWN;"
            "NO_INCLUDE_OR_EXCLUDE_FROM_GET_ALONE;NO_EQ_SOURCE_AUTHORITY;"
            "NO_P01_U05_OVERLAP_INFERENCE_FROM_LIAB_OR_TOTALLIAB;"
            "DO_NOT_COUNT_BALANCE_SNAPSHOT_LIAB_AS_THE_SAME_EVENT;"
            "FEED_EXISTING_TYPED_PRODUCER_WITHOUT_AUTHORITY_REDESIGN"
        ),
        "acquisition_forbidden_in_this_workpackage": TRUE_TOKEN,
        "primary_proof_role_bound": PRIMARY_PROOF_ROLE,
        "embedding_witness_bound": FALSE_TOKEN,
        "surface_binding_status": BINDING_STATUS,
        "data_class": DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
        "producer_id": PRODUCER_ID,
    }


def execute_u05_independent_liability_event_surface_or_embedding_witness_qualification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    genesis_store_root: Path | str | None = None,
    sealed_cb_pack: Path | str | None = None,
    vault_file: Path | str | None = None,
    persist_as_of: str | None = None,
) -> U05IndependentLiabilityEventSurfaceQualificationResultV1:
    if owner_go != OWNER_GO:
        raise U05IndependentLiabilityEventSurfaceQualificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U05IndependentLiabilityEventSurfaceQualificationError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cb_pack = (
        Path(sealed_cb_pack) if sealed_cb_pack is not None else repo / CANONICAL_CB_PACK_RELPATH
    )
    _assert_parent_cb_pack(sealed_cb_pack=cb_pack)
    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise U05IndependentLiabilityEventSurfaceQualificationError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    _require_non_empty_str(field="persist_as_of", raw=as_of)
    vault_presence = _inspect_vault_presence(repo=repo, vault_file=vault_file)
    prior_four = build_prior_four_exclusion_v1()
    venue_spec = build_venue_specification_excerpts_v1()
    census = build_bounded_candidate_census_v1()
    adjudication = evaluate_selected_event_surface_predicates_v1()
    contract = build_pre_acquisition_contract_v1(
        d4_identity_digest=d4.identity_digest,
        d5_binding_id=d5.binding_id,
    )
    law_outcome = evaluate_u05_primary_proof_v1(proof={})
    if law_outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise U05IndependentLiabilityEventSurfaceQualificationError("ABSENT_PROOF_MUST_NOT_DECIDE")
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "ABSENT_PROOF_MUST_BE_NONQUALIFYING"
        )
    if contract["productive_acquisition_authorized"] != FALSE_TOKEN:
        raise U05IndependentLiabilityEventSurfaceQualificationError(
            "ACQUISITION_MUST_REMAIN_UNAUTHORIZED"
        )
    if contract["actual_get_count"] != "0" or contract["post_count"] != "0":
        raise U05IndependentLiabilityEventSurfaceQualificationError("GET_OR_POST_MUST_REMAIN_ZERO")
    predicates = {
        "layer": "ADJUDICATED_CONCLUSION",
        "independent_liability_event_proven": FALSE_TOKEN,
        "equity_stock_effect_proven": FALSE_TOKEN,
        "event_after_prior_proven": FALSE_TOKEN,
        "d4_d5_binding_present": TRUE_TOKEN,
        "d4_identity_digest": d4.identity_digest,
        "d5_binding_id": d5.binding_id,
        "prior_anchor_id_present": AUTHORIZED_ANCHOR_ID,
        "d4_d5_scope_identity_proven": FALSE_TOKEN,
        "non_algebraic_embedding_identity": UNKNOWN_TOKEN,
        "p01_u05_overlap_state": P01_U05_OVERLAP_STATE,
        "p01_u05_overlap_disproven": FALSE_TOKEN,
        "once_only_equity_stock_effect_proven": FALSE_TOKEN,
        "double_counting_guard_proven": TRUE_TOKEN,
        "absence_is_not_exclude": TRUE_TOKEN,
        "get_alone_may_include": FALSE_TOKEN,
        "get_alone_may_exclude": FALSE_TOKEN,
        "liab_totalLiab_must_not_prove_embedding": TRUE_TOKEN,
        "surface_or_witness_bindable": TRUE_TOKEN,
        "primary_proof_role_bound": PRIMARY_PROOF_ROLE,
        "embedding_witness_bound": FALSE_TOKEN,
    }
    evaluation = {
        "layer": "ADJUDICATED_CONCLUSION",
        "current_primary_proof_present": FALSE_TOKEN,
        "law_outcome": law_outcome.outcome,
        "law_basis": law_outcome.basis,
        "u05_primary_proof_status": PRIMARY_PROOF_STATUS,
        "blocker_id": BLOCKER_ID,
        "u05_decision_after": DECISION_REMAIN_UNKNOWN,
        "u05_decision_basis": DECISION_BASIS,
        "include_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_PRIMARY_PROOF",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_IN_BASE_PROOF",
        "productive_acquisition_authorized": FALSE_TOKEN,
        "concrete_surface_id": SELECTED_SURFACE_ID,
        "surface_capability_proven": TRUE_TOKEN,
        "surface_binding_status": BINDING_STATUS,
        "embedding_witness_id": NONE_TOKEN,
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "missing_positive_proof_component": (
            "SEPARATELY_AUTHORIZED_INTEREST_ACCRUED_GET_AND_INDEPENDENT_NON_ALGEBRAIC_EMBEDDING_WITNESS"
        ),
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
        "why_u05_remains_unknown": (
            "Event surface is bound only to the pre-acquisition boundary. No GET was "
            "executed. Independent liability events are therefore not proven. The "
            "selected surface is not an embedding witness. liab/totalLiab values must "
            "not infer P01/U05 overlap."
        ),
    }
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PARENT_CB_NEXT_OWNER_GO": PARENT_CB_NEXT_OWNER_GO,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "U05_EVIDENCE_CLASS": CLASS_U05,
        "AUTHORIZED_ACQUISITION_SURFACE": ACQUISITION_SURFACE,
        "EXPECTED_PRIMARY_PROOF_OBJECT": PROOF_OBJECT_U05,
        "CANDIDATE_CENSUS_COUNT": census["candidate_census_count"],
        "SELECTED_SINGLE_CANDIDATE_ID": SELECTED_SURFACE_ID,
        "SELECTED_CANDIDATE_KIND": SELECTED_CANDIDATE_KIND,
        "PRIOR_FOUR_CANDIDATES_EXCLUDED": TRUE_TOKEN,
        "EXACT_SURFACE_OR_WITNESS": SELECTED_SURFACE_ID,
        "HTTP_METHOD": HTTP_METHOD,
        "BOUND_ENDPOINT": SELECTED_ENDPOINT_PATH,
        "VENUE_AUTHORITY_SOURCE": VENUE_AUTHORITY_SOURCE,
        "VENUE_CAPABILITY_PROVEN": TRUE_TOKEN,
        "READ_ONLY_PROVEN": TRUE_TOKEN,
        "LIABILITY_IDENTITY_CAPABILITY": TRUE_TOKEN,
        "ACCOUNT_SCOPE_CAPABILITY": TRUE_TOKEN,
        "TIME_EVENT_IDENTITY_CAPABILITY": TRUE_TOKEN,
        "CURRENCY_SCOPE_CAPABILITY": TRUE_TOKEN,
        "EQUITY_STOCK_EFFECT_CAPABILITY": FALSE_TOKEN,
        "INDEPENDENCE_FROM_RECONSTRUCTION_ALGEBRA": TRUE_TOKEN,
        "NON_ALGEBRAIC_EMBEDDING_CAPABILITY": FALSE_TOKEN,
        "ONCE_ONLY_EFFECT_CAPABILITY": FALSE_TOKEN,
        "DOUBLE_COUNTING_SAFETY_CAPABILITY": TRUE_TOKEN,
        "SURFACE_OR_WITNESS_BINDABLE": TRUE_TOKEN,
        "SURFACE_BINDING_STATUS": BINDING_STATUS,
        "PRIMARY_PROOF_ROLE_BOUND": PRIMARY_PROOF_ROLE,
        "MAX_GET_COUNT": FUTURE_MAX_GET_COUNT,
        "FUTURE_MAX_GET_COUNT_IF_SEPARATELY_AUTHORIZED": FUTURE_MAX_GET_COUNT,
        "RETRY_ALLOWED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "ACQUISITION_AUTHORITY_AFTER_BINDING": "NOT_AUTHORIZED_SEPARATE_OWNER_GO_REQUIRED",
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "POST_COUNT": "0",
        "VAULT_AVAILABLE": vault_presence["available"],
        "SECRET_RESOLUTION_STATUS": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "RAW_EVIDENCE_STATUS": "NOT_ACQUIRED",
        "BORROW_OR_ACCOUNT_LIABILITY_STATE_PRODUCER_STATUS": PRODUCER_STATUS,
        "PRODUCER_ID": PRODUCER_ID,
        "INDEPENDENT_LIABILITY_EVENT_PROVEN": FALSE_TOKEN,
        "EQUITY_STOCK_EFFECT_PROVEN": FALSE_TOKEN,
        "NON_ALGEBRAIC_EMBEDDING_IDENTITY": UNKNOWN_TOKEN,
        "P01_U05_OVERLAP_DISPROVEN": FALSE_TOKEN,
        "ONCE_ONLY_EQUITY_STOCK_EFFECT_PROVEN": FALSE_TOKEN,
        "DOUBLE_COUNTING_GUARD_PROVEN": TRUE_TOKEN,
        "U05_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "U05_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_BASIS": DECISION_BASIS,
        "U06_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "SECRETS_OR_SIGNATURES_PERSISTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "ACCTLV2_ALONE_USED_AS_DISQUALIFIER": FALSE_TOKEN,
    }
    lineage = {
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cb_pack": CANONICAL_CB_PACK_RELPATH,
        "d4_identity_digest": d4.identity_digest,
        "d5_binding_id": d5.binding_id,
        "prior_anchor_id": AUTHORIZED_ANCHOR_ID,
        "reconstruction_source_authority": FALSE_TOKEN,
        "external_research_input_trusted": FALSE_TOKEN,
        "external_research_input_independently_verified": TRUE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "u06_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "p01_authority_unchanged": TRUE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
        "treasury_unchanged": TRUE_TOKEN,
        "live_gates_unchanged": TRUE_TOKEN,
        "venue_execution_authority_unchanged": TRUE_TOKEN,
    }
    layers = {
        "CANONICAL_AUTHORITY": (
            "pre_acquisition_contract_v1.json,candidate_census_v1.json,"
            "prior_four_exclusion_v1.json,architecture_blocker_v1.json"
        ),
        "VENUE_SPECIFICATION": "venue_specification_excerpts_v1.json",
        "FORENSIC_RAW_EVIDENCE": "vault_presence_v1.json",
        "ADJUDICATED_CONCLUSION": (
            "predicate_adjudication_v1.json,selected_surface_adjudication_v1.json,"
            "current_proof_evaluation_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=root / CLAIMS_FILE, payload=claims)
    _persist_json(path=root / "prior_four_exclusion_v1.json", payload=prior_four)
    _persist_json(path=root / "venue_specification_excerpts_v1.json", payload=venue_spec)
    _persist_json(path=root / "candidate_census_v1.json", payload=census)
    _persist_json(path=root / "selected_surface_adjudication_v1.json", payload=adjudication)
    _persist_json(path=root / "pre_acquisition_contract_v1.json", payload=contract)
    _persist_json(path=root / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=root / "predicate_adjudication_v1.json", payload=predicates)
    _persist_json(path=root / "current_proof_evaluation_v1.json", payload=evaluation)
    _persist_json(path=root / "vault_presence_v1.json", payload=vault_presence)
    _persist_json(path=root / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=root / "layers_v1.json", payload=layers)
    _persist_json(path=root / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=root)
    if verify_manifest_sha256_v1(store_root=root) != 0:
        raise U05IndependentLiabilityEventSurfaceQualificationError("MANIFEST_VERIFY_NOT_ZERO")
    return U05IndependentLiabilityEventSurfaceQualificationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=as_of,
        store_root=str(root),
        selected_single_candidate_id=SELECTED_SURFACE_ID,
        selected_candidate_kind=SELECTED_CANDIDATE_KIND,
        surface_or_witness_bindable=TRUE_TOKEN,
        binding_status=BINDING_STATUS,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        future_max_get_count_if_separately_authorized=FUTURE_MAX_GET_COUNT,
        vault_available=vault_presence["available"],
        secret_resolution_status=SECRET_RESOLUTION_NOT_ATTEMPTED,
        u05_primary_proof_status=PRIMARY_PROOF_STATUS,
        u05_decision_after=DECISION_REMAIN_UNKNOWN,
        u05_decision_basis=DECISION_BASIS,
        productive_acquisition_executed=FALSE_TOKEN,
        evidence_manifest=str(root / "MANIFEST.sha256"),
    )


__all__ = [
    "ARCHITECTURE_BLOCKER",
    "BINDING_STATUS",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "DECISION_BASIS",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "FUTURE_MAX_GET_COUNT",
    "HTTP_METHOD",
    "NEXT_OWNER_GO",
    "OWNER_GO",
    "PARENT_CB_NEXT_OWNER_GO",
    "PRIMARY_PROOF_ROLE",
    "PRIMARY_PROOF_STATUS",
    "PRIOR_FOUR_SURFACES",
    "SELECTED_CANDIDATE_KIND",
    "SELECTED_SURFACE_ID",
    "U05IndependentLiabilityEventSurfaceQualificationError",
    "U05IndependentLiabilityEventSurfaceQualificationResultV1",
    "build_bounded_candidate_census_v1",
    "build_pre_acquisition_contract_v1",
    "build_prior_four_exclusion_v1",
    "build_venue_specification_excerpts_v1",
    "evaluate_selected_event_surface_predicates_v1",
    "execute_u05_independent_liability_event_surface_or_embedding_witness_qualification_v1",
]
