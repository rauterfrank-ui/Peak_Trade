"""Persist the already-adjudicated U06 NONE_BINDABLE surface binding.

Consumes the Owner-GO named by §11.2.1.CE. Does not search new
candidates. Does not GET. Does not POST. Does not resolve secrets.
Does not INCLUDE or EXCLUDE U06. NONE_BINDABLE is not EXCLUDE, zero,
or no-fee. AUTHORITY_EFFECT=NONE.

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
    CLASS_U06,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    PROOF_OBJECT_U06,
    evaluate_u06_primary_proof_v1,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    SELECTED_BALANCE_SURFACE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.scoped_read_only_observation_boundary_contract_v1 import (
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    CANDIDATE_SURFACE_TRADE_FILLS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_durable_unknown_embedding_identity_pin_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CE_PACK_RELPATH,
    NEXT_OWNER_GO as CONSUMED_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1 import (
    CANDIDATE_SURFACE_BILLS_ARCHIVE,
)

OWNER_GO = CONSUMED_OWNER_GO
EXPECTED_ORIGIN_MAIN_SHA = "ed28786306ce17b69b224abde4c598ba86ddb545"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_u06_paired_fee_event_and_once_only_equity_stock_"
    "effect_primary_proof_surface_binding_v1/2026-09-15T021000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T02:10:00Z"
SCHEMA_CLASS = (
    "U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_PRIMARY_PROOF_SURFACE_BINDING_V1"
)
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
SELECTION_STATUS = "NONE_BINDABLE"
BINDING_STATUS = "NOT_BOUND"
PRIMARY_PROOF_STATUS = "NOT_ACQUIRED_NO_BINDABLE_CONCRETE_GET_SURFACE"
DECISION_BASIS = (
    "NO_CONCRETE_VENUE_SURFACE_CAN_PRODUCE_PAIRED_NON_EQ_EQUITY_STOCK_PLACEMENT_IDENTITY"
)
BLOCKER_ID = "U06_EQUITY_STOCK_PLACEMENT_IDENTITY_NOT_ACQUIRABLE_ON_CURRENT_VENUE_SURFACES"
ARCHITECTURE_BLOCKER = (
    "NO_REAL_OKX_EEA_SURFACE_CAN_PRODUCE_PAIRED_FEE_EVENT_AND_ONCE_ONLY_"
    "EQUITY_STOCK_EFFECT_V1_WITHOUT_EQ_OR_ALGEBRA"
)
NEXT_PRODUCTIVE_NODE = "U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_V1"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_PIN_U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_"
    "UNKNOWN_PATH_B_AFTER_NONE_BINDABLE_V1"
)
NEXT_ACTION = "STOP_AWAIT_OWNER_GO_FOR_U06_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_NO_GET"
SECRET_RESOLUTION_NOT_ATTEMPTED = "NOT_ATTEMPTED"
PLACEMENT_XOR = "IN_BASE_XOR_EVENT_SEPARATE"
CLAIMS_FILE = "claims.json"
CANDIDATE_SURFACE_ACCOUNT_TRADE_FEE = "GET_ACCOUNT_TRADE_FEE_RATE_SCHEDULE_NOT_CHARGED_FEE_EVENT"
CANDIDATE_SURFACE_PAIRED_FILLS_PLUS_BILLS = (
    f"{CANDIDATE_SURFACE_TRADE_FILLS}+{CANDIDATE_SURFACE_ACCOUNT_BILLS}"
)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXCLUDE_NORMALIZERS = frozenset(
    {
        OUTCOME_EXCLUDE,
        "EXCLUDE",
        "0",
        "zero",
        "absent",
        "NO_FEE",
        "FALSE",
        "false",
        "NONE_BINDABLE_MEANS_NO_FEE",
    }
)


class U06PrimaryProofSurfaceBindingError(ValueError):
    """Fail-closed U06 NONE_BINDABLE surface-binding violation."""


@dataclass(frozen=True)
class U06PrimaryProofSurfaceBindingResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    concrete_surface_selection_status: str
    concrete_surface_id: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    u06_decision_after: str
    blocker_id: str
    next_productive_node: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise U06PrimaryProofSurfaceBindingError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise U06PrimaryProofSurfaceBindingError(f"{field}_DRIFT:{actual}")


def reject_none_bindable_as_exclude_v1(*, claimed: str) -> None:
    if claimed in _EXCLUDE_NORMALIZERS or claimed == OUTCOME_INCLUDE:
        raise U06PrimaryProofSurfaceBindingError(
            f"NONE_BINDABLE_IS_NOT_EXCLUDE_OR_INCLUDE:{claimed}"
        )


def reject_hope_get_v1(*, authorized_get_count: str, actual_get_count: str) -> None:
    if authorized_get_count != "0" or actual_get_count != "0":
        raise U06PrimaryProofSurfaceBindingError("HOPE_GET_FORBIDDEN")


def _assert_standing_pins() -> None:
    if LIVE_ENABLED is not False:
        raise U06PrimaryProofSurfaceBindingError("LIVE_ENABLED_NOT_FALSE")
    if LIVE_ARMED is not False:
        raise U06PrimaryProofSurfaceBindingError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise U06PrimaryProofSurfaceBindingError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U06PrimaryProofSurfaceBindingError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U06PrimaryProofSurfaceBindingError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U06PrimaryProofSurfaceBindingError("RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if KIND_SET_RESOLVED is not False:
        raise U06PrimaryProofSurfaceBindingError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U06PrimaryProofSurfaceBindingError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U06PrimaryProofSurfaceBindingError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U06PrimaryProofSurfaceBindingError("COMPLETE_STREAM_MUST_REMAIN_UNPROVEN")
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U06PrimaryProofSurfaceBindingError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U06PrimaryProofSurfaceBindingError("OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED")
    if CANDIDATE_SURFACE_SELECTION != "NONE_SELECTED":
        raise U06PrimaryProofSurfaceBindingError("CANDIDATE_SURFACE_SELECTION_NOT_NONE")
    if MS2_AUTHORIZED is not False:
        raise U06PrimaryProofSurfaceBindingError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U06PrimaryProofSurfaceBindingError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U06PrimaryProofSurfaceBindingError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U06PrimaryProofSurfaceBindingError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U06PrimaryProofSurfaceBindingError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U06PrimaryProofSurfaceBindingError("BILLS_MUST_REMAIN_NONCANONICAL")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U06PrimaryProofSurfaceBindingError("DAG_PIN_DRIFT")


def _assert_parent_ce_pack(*, sealed_ce_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_ce_pack) != 0:
        raise U06PrimaryProofSurfaceBindingError("CE_MANIFEST_VERIFY_NOT_ZERO")
    claims = _load_json_object(path=sealed_ce_pack / CLAIMS_FILE)
    _require_token(field="OWNER_GO_STATUS", payload=claims, expected="CONSUMED")
    _require_token(field="WITNESS_BRANCH_CLOSED", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="PATH_C_CLOSEOUT", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="ACTUAL_GET_COUNT", payload=claims, expected="0")
    _require_token(field="POST_COUNT", payload=claims, expected="0")
    _require_token(field="U06_DECISION_UNCHANGED", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=OWNER_GO)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="ACCOUNT_BILLS_CANONICALIZED", payload=claims, expected=FALSE_TOKEN)


def build_proof_halves_v1() -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "evidence_class_id": CLASS_U06,
        "primary_proof_object": PROOF_OBJECT_U06,
        "event_half": (
            "unique_fee_event_id+event_digest+ordering_key+nonzero_fee_amount+"
            "currency_domain+event_after_prior_as_of+D4_identity"
        ),
        "equity_effect_half": (
            "pairing_equity_stock_observation_id+once_only_guard+"
            "placement_IN_BASE_xor_EVENT_SEPARATE+pairing_observation_is_not_raw_eq_source"
        ),
        "pairing_requirement": "fee_event_and_equity_stock_effect_from_same_economic_cause",
        "placement_xor": PLACEMENT_XOR,
        "event_separate_requires": "pairing_delta_matches_fee",
        "in_base_requires": "fee_coverage_complete",
        "semantic_normalization_forbidden": TRUE_TOKEN,
    }


def build_frozen_candidate_census_v1() -> dict[str, Any]:
    records = (
        {
            "candidate_id": "C01_EXISTING_PACKAGE1_LIVE_BILLS",
            "surface_id": CANDIDATE_SURFACE_ACCOUNT_BILLS,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "POST_PRIOR_ROWS_HAVE_FEE_ZERO;EMPTY_ZERO_ABSENT_FEE_NONQUALIFYING;"
                "PACKAGE_1_EXHAUSTED;NO_RETROACTIVE_UPLIFT"
            ),
        },
        {
            "candidate_id": "C02_EXISTING_PACKAGE1_BILLS_ARCHIVE",
            "surface_id": CANDIDATE_SURFACE_BILLS_ARCHIVE,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "PRE_PRIOR;SEALED_PACKAGE_1_BILLS_RETROACTIVE_UPLIFT_FORBIDDEN;"
                "BALCHG_IS_NOT_EQUITY_STOCK_PLACEMENT;TYPE_TOKENS_UNCLASSIFIED"
            ),
        },
        {
            "candidate_id": "C03_EXISTING_SECTION_1114_LIVE_FEE_FILLS",
            "surface_id": CANDIDATE_SURFACE_TRADE_FILLS,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "FEE_TOKEN_ALONE;NOT_D6;PRE_PRIOR;NO_AUTHORITY_REINTERPRETATION"
            ),
        },
        {
            "candidate_id": "C04_EXISTING_G12_FLATTEN_FILLS",
            "surface_id": CANDIDATE_SURFACE_TRADE_FILLS,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": "PRE_PRIOR;FEE_TOKEN_ALONE;NOT_U06_AUTHORITY",
        },
        {
            "candidate_id": "C05_NEW_GET_ACCOUNT_BILLS",
            "surface_id": CANDIDATE_SURFACE_ACCOUNT_BILLS,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "HOPE_GET;NO_INDEPENDENT_POST_PRIOR_TRADE_FEE;PLACEMENT_UNRESOLVABLE_WITHOUT_EQ"
            ),
        },
        {
            "candidate_id": "C06_NEW_GET_ACCOUNT_BILLS_ARCHIVE",
            "surface_id": CANDIDATE_SURFACE_BILLS_ARCHIVE,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": "REPEAT_OF_SEALED_PACK;PRE_PRIOR;HOPE_GET",
        },
        {
            "candidate_id": "C07_NEW_GET_TRADE_FILLS",
            "surface_id": CANDIDATE_SURFACE_TRADE_FILLS,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": "FEE_TOKEN_ALONE;NO_EQUITY_STOCK_ON_FILL;NOT_D6",
        },
        {
            "candidate_id": "C08_NEW_GET_ACCOUNT_TRADE_FEE",
            "surface_id": CANDIDATE_SURFACE_ACCOUNT_TRADE_FEE,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": "RATE_SCHEDULE_NOT_CHARGED_FEE_EVENT",
        },
        {
            "candidate_id": "C09_NEW_GET_ACCOUNT_BALANCE_AS_PAIRING_HALF",
            "surface_id": SELECTED_BALANCE_SURFACE,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "GATE_A_EXECUTED_NONQUALIFYING;VENUE_EQ_SOURCE_AUTHORITY_FORBIDDEN;"
                "PAIRING_CANNOT_BE_RAW_EQ"
            ),
        },
        {
            "candidate_id": "C10_NEW_PAIRED_FILLS_PLUS_BILLS_TWO_GETS",
            "surface_id": CANDIDATE_SURFACE_PAIRED_FILLS_PLUS_BILLS,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "SECOND_GET_ADDS_BALCHG_NOT_EQUITY_STOCK_PLACEMENT;"
                "IN_BASE_VS_SEPARATE_UNRESOLVABLE_WITHOUT_EQ_OR_ALGEBRA"
            ),
        },
    )
    if any(item["bindable"] == TRUE_TOKEN for item in records):
        raise U06PrimaryProofSurfaceBindingError("BINDABLE_SURFACE_MUST_NOT_EXIST")
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "census_kind": "FROZEN_PRIOR_ADJUDICATION_NOT_NEW_SEARCH",
        "candidate_count": str(len(records)),
        "selection_status": SELECTION_STATUS,
        "selected_surface_id": NONE_TOKEN,
        "selected_method": NONE_TOKEN,
        "selected_host": NONE_TOKEN,
        "selected_path": NONE_TOKEN,
        "selected_query": NONE_TOKEN,
        "u06_primary_proof_role_bound": FALSE_TOKEN,
        "second_get_required": FALSE_TOKEN,
        "why_second_get_required_if_true": (
            "NOT_APPLICABLE;A_SECOND_GET_CANNOT_CREATE_NON_EQ_EQUITY_STOCK_PLACEMENT_IDENTITY"
        ),
        "hope_get_forbidden": TRUE_TOKEN,
        "records": list(records),
    }


def execute_u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_ce_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> U06PrimaryProofSurfaceBindingResultV1:
    if owner_go != OWNER_GO:
        raise U06PrimaryProofSurfaceBindingError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U06PrimaryProofSurfaceBindingError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    ce_pack = (
        Path(sealed_ce_pack) if sealed_ce_pack is not None else repo / CANONICAL_CE_PACK_RELPATH
    )
    _assert_parent_ce_pack(sealed_ce_pack=ce_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise U06PrimaryProofSurfaceBindingError("FIELD_MISSING:persist_as_of")
    reject_none_bindable_as_exclude_v1(claimed=SELECTION_STATUS)
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    law_outcome = evaluate_u06_primary_proof_v1(proof={})
    if law_outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise U06PrimaryProofSurfaceBindingError("ABSENT_PROOF_MUST_NOT_DECIDE")
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise U06PrimaryProofSurfaceBindingError("ABSENT_PROOF_MUST_BE_NONQUALIFYING")
    reject_none_bindable_as_exclude_v1(claimed=law_outcome.outcome)
    reject_none_bindable_as_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    census = build_frozen_candidate_census_v1()
    halves = build_proof_halves_v1()
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "hope_get_forbidden": TRUE_TOKEN,
        "second_get_cannot_close_placement_gap": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "algebraic_eq_identity_forbidden": TRUE_TOKEN,
        "fee_token_alone_is_not_primary_proof": TRUE_TOKEN,
        "none_bindable_is_not_exclude": TRUE_TOKEN,
        "none_bindable_is_not_zero_or_no_fee": TRUE_TOKEN,
        "path_c_closeout": FALSE_TOKEN,
        "placement_pin_not_implemented_this_slice": TRUE_TOKEN,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_action": NEXT_ACTION,
    }
    surface = {
        "layer": "CANONICAL_AUTHORITY",
        "owner_go": OWNER_GO,
        "semantic_acquisition_surface": ACQUISITION_SURFACE,
        "expected_primary_proof_object": PROOF_OBJECT_U06,
        "concrete_surface_id": NONE_TOKEN,
        "http_method": NONE_TOKEN,
        "bound_endpoint": NONE_TOKEN,
        "primary_proof_role_bound": FALSE_TOKEN,
        "max_get_count": "0",
        "retry_allowed": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "surface_binding_status": BINDING_STATUS,
        "concrete_surface_selection_status": SELECTION_STATUS,
        "productive_acquisition_authorized": FALSE_TOKEN,
        "event_acquisition_network_get_authorized": FALSE_TOKEN,
        "account_bills_canonicalized": FALSE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "fail_closed_policy": "NO_SURFACE_NO_GET_NO_INCLUDE_NO_EXCLUDE",
        "blocker_id": BLOCKER_ID,
    }
    predicates = {
        "layer": "ADJUDICATED_CONCLUSION",
        "paired_fee_event_proven": FALSE_TOKEN,
        "once_only_equity_stock_effect_proven": FALSE_TOKEN,
        "placement_in_base_or_event_separate_proven": FALSE_TOKEN,
        "pairing_observation_is_not_raw_eq_source": TRUE_TOKEN,
        "pairing_uses_raw_eq": FALSE_TOKEN,
        "algebraic_eq_identity_used": FALSE_TOKEN,
        "fee_token_alone": TRUE_TOKEN,
        "event_after_prior_proven": FALSE_TOKEN,
        "fee_coverage_complete": FALSE_TOKEN,
        "absence_is_not_exclude": TRUE_TOKEN,
        "none_bindable_is_not_exclude": TRUE_TOKEN,
        "get_alone_may_include": FALSE_TOKEN,
        "get_alone_may_exclude": FALSE_TOKEN,
        "second_get_required": FALSE_TOKEN,
    }
    evaluation = {
        "layer": "ADJUDICATED_CONCLUSION",
        "current_primary_proof_present": FALSE_TOKEN,
        "law_outcome": law_outcome.outcome,
        "law_basis": law_outcome.basis,
        "u06_primary_proof_status": PRIMARY_PROOF_STATUS,
        "blocker_id": BLOCKER_ID,
        "u06_decision_after": DECISION_REMAIN_UNKNOWN,
        "u06_decision_basis": DECISION_BASIS,
        "include_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_PRIMARY_PROOF",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_IN_BASE_PROOF",
        "productive_acquisition_authorized": FALSE_TOKEN,
    }
    historical = {
        "layer": "HISTORICAL",
        "package_1_bills_uplift_forbidden": TRUE_TOKEN,
        "section_11_14_live_fee_observed_is_not_d6_u06_authority": TRUE_TOKEN,
        "g12_flatten_fills_uplift_forbidden": TRUE_TOKEN,
        "pre_prior_nonzero_fees_cannot_include": TRUE_TOKEN,
        "post_prior_live_bills_fee_zero_nonqualifying": TRUE_TOKEN,
        "reinterpretation_forbidden": TRUE_TOKEN,
    }
    none_bindable_guard = {
        "layer": "ADJUDICATED_CONCLUSION",
        "none_bindable_is_not_exclude": TRUE_TOKEN,
        "none_bindable_is_not_include": TRUE_TOKEN,
        "none_bindable_is_not_zero": TRUE_TOKEN,
        "none_bindable_is_not_absent_fee": TRUE_TOKEN,
        "u06_decision_after": DECISION_REMAIN_UNKNOWN,
        "remain_unknown_is_not_exclude": TRUE_TOKEN,
    }
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "WORKPACKAGE": SCHEMA_CLASS,
        "U06_EVIDENCE_CLASS": CLASS_U06,
        "EXPECTED_PRIMARY_PROOF_OBJECT": PROOF_OBJECT_U06,
        "AUTHORIZED_ACQUISITION_SURFACE": ACQUISITION_SURFACE,
        "CONCRETE_SURFACE_CANDIDATE_COUNT": census["candidate_count"],
        "CONCRETE_SURFACE_SELECTION_STATUS": SELECTION_STATUS,
        "CONCRETE_SURFACE_ID": NONE_TOKEN,
        "HTTP_METHOD": NONE_TOKEN,
        "BOUND_ENDPOINT": NONE_TOKEN,
        "PRIMARY_PROOF_ROLE_BOUND": FALSE_TOKEN,
        "MAX_GET_COUNT": "0",
        "RETRY_ALLOWED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "SURFACE_BINDING_STATUS": BINDING_STATUS,
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "RAW_EVIDENCE_STATUS": "NOT_ACQUIRED",
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "U06_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "U06_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U06_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U06_DECISION_BASIS": DECISION_BASIS,
        "NONE_BINDABLE_IS_NOT_EXCLUDE": TRUE_TOKEN,
        "U05_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "GET_ALONE_MAY_INCLUDE": FALSE_TOKEN,
        "GET_ALONE_MAY_EXCLUDE": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "SECOND_GET_REQUIRED": FALSE_TOKEN,
        "PLACEMENT_PIN_IMPLEMENTED_THIS_SLICE": FALSE_TOKEN,
        "PATH_C_CLOSEOUT": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "SECRETS_OR_SIGNATURES_PERSISTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
    }
    lineage = {
        "layer": "HISTORICAL",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_ce_pack": CANONICAL_CE_PACK_RELPATH,
        "reconstruction_source_authority": FALSE_TOKEN,
        "new_candidate_search_executed": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "u05_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    layers = {
        "CANONICAL_AUTHORITY": (
            "acquisition_surface_binding_v1.json,proof_halves_v1.json,architecture_blocker_v1.json"
        ),
        "FORENSIC_RAW_EVIDENCE": "NONE_NO_GET_NO_SECRET_RESOLUTION",
        "ADJUDICATED_CONCLUSION": (
            "candidate_surface_capability_adjudication_v1.json,"
            "predicate_adjudication_v1.json,current_proof_evaluation_v1.json,"
            "none_bindable_not_exclude_guard_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json,historical_fee_evidence_non_uplift_v1.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    _persist_json(path=root / CLAIMS_FILE, payload=claims)
    _persist_json(path=root / "acquisition_surface_binding_v1.json", payload=surface)
    _persist_json(path=root / "proof_halves_v1.json", payload=halves)
    _persist_json(
        path=root / "candidate_surface_capability_adjudication_v1.json",
        payload=census,
    )
    _persist_json(path=root / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=root / "predicate_adjudication_v1.json", payload=predicates)
    _persist_json(path=root / "current_proof_evaluation_v1.json", payload=evaluation)
    _persist_json(
        path=root / "none_bindable_not_exclude_guard_v1.json", payload=none_bindable_guard
    )
    _persist_json(path=root / "historical_fee_evidence_non_uplift_v1.json", payload=historical)
    _persist_json(path=root / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=root / "layers_v1.json", payload=layers)
    _persist_json(path=root / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=root)
    if verify_manifest_sha256_v1(store_root=root) != 0:
        raise U06PrimaryProofSurfaceBindingError("MANIFEST_VERIFY_NOT_ZERO")
    return U06PrimaryProofSurfaceBindingResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(root),
        concrete_surface_selection_status=SELECTION_STATUS,
        concrete_surface_id=NONE_TOKEN,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        u06_decision_after=DECISION_REMAIN_UNKNOWN,
        blocker_id=BLOCKER_ID,
        next_productive_node=NEXT_PRODUCTIVE_NODE,
        evidence_manifest=str(root / "MANIFEST.sha256"),
    )


__all__ = [
    "ARCHITECTURE_BLOCKER",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "DECISION_BASIS",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PRIMARY_PROOF_STATUS",
    "SELECTION_STATUS",
    "U06PrimaryProofSurfaceBindingError",
    "build_frozen_candidate_census_v1",
    "build_proof_halves_v1",
    "execute_u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1",
    "reject_hope_get_v1",
    "reject_none_bindable_as_exclude_v1",
]
