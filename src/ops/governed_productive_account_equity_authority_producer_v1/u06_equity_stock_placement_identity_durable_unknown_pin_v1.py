"""Pin U06 equity-stock placement identity as durable UNKNOWN after NONE_BINDABLE.

Consumes Owner-GO PATH_B. Does not GET. Does not POST. Does not INCLUDE
or EXCLUDE U06. Does not invent PATH_C closeout. Does not Hope-GET.
Durable UNKNOWN is not INCLUDE, EXCLUDE, zero, no-fee, or absent.
NONE_BINDABLE is not zero/no-fee. Pairing and XOR remain required.
U06 remains once-only for already-accrued fees. AUTHORITY_EFFECT=NONE.

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
    CLASS_RESIDUAL,
    CLASS_U06,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    PROOF_OBJECT_U06,
    TARGET_U06,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CF_PACK_RELPATH,
    NEXT_OWNER_GO as CONSUMED_OWNER_GO,
    SELECTION_STATUS as PARENT_SELECTION_STATUS,
    build_proof_halves_v1,
    reject_hope_get_v1,
    reject_none_bindable_as_exclude_v1,
)

OWNER_GO = CONSUMED_OWNER_GO
SELECTED_PATH = "PATH_B"
EXPECTED_ORIGIN_MAIN_SHA = "433ce52062c69194d54c918a05ade762000e8176"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_u06_equity_stock_placement_identity_durable_"
    "unknown_pin_v1/2026-09-15T030000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T03:00:00Z"
SCHEMA_CLASS = "U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
PLACEMENT_XOR = "IN_BASE_XOR_EVENT_SEPARATE"
PRIMARY_PROOF_STATUS = "PLACEMENT_IDENTITY_BRANCH_CLOSED_DURABLE_UNKNOWN_U06_REMAIN_UNKNOWN"
DECISION_BASIS = (
    "NO_ACQUIRABLE_NON_EQ_VENUE_PLACEMENT_IDENTITY_PATH_B_PIN_"
    "DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE"
)
BLOCKER_ID = (
    "U06_PLACEMENT_IDENTITY_BRANCH_CLOSED_DURABLE_UNKNOWN_RESIDUAL_PRIMARY_PROOF_NOT_ACQUIRED"
)
ARCHITECTURE_BLOCKER = "RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_NOT_ACQUIRED"
NEXT_PRODUCTIVE_NODE = CLASS_RESIDUAL
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_FOR_FORENSIC_ACQUISITION_OF_"
    "RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_V1"
)
NEXT_ACTION = (
    "STOP_AWAIT_OWNER_GO_FOR_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_NO_GET"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_NORMALIZERS = frozenset(
    {
        OUTCOME_INCLUDE,
        OUTCOME_EXCLUDE,
        "INCLUDE",
        "EXCLUDE",
        "FALSE",
        "false",
        "true",
        "0",
        "zero",
        "absent",
        "NO_FEE",
        "NONE_BINDABLE_MEANS_NO_FEE",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class U06EquityStockPlacementIdentityDurableUnknownPinError(ValueError):
    """Fail-closed U06 durable-unknown placement-identity pin violation."""


@dataclass(frozen=True)
class U06EquityStockPlacementIdentityDurableUnknownPinResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    selected_path: str
    target_unknown: str
    placement_identity_status: str
    u06_decision_after: str
    further_u06_placement_acquisition: str
    placement_branch_closed: str
    next_productive_node: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
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
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(f"{field}_DRIFT:{actual}")


def reject_durable_unknown_as_include_or_exclude_v1(*, claimed: str) -> None:
    if claimed in _NORMALIZERS:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            f"DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE:{claimed}"
        )


def _assert_standing_pins() -> None:
    if WIRE_SEND_PERMITTED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if CANDIDATE_SURFACE_SELECTION != "NONE_SELECTED":
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "CANDIDATE_SURFACE_SELECTION_NOT_NONE"
        )
    if MS2_AUTHORIZED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "BILLS_MUST_REMAIN_NONCANONICAL"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("DAG_PIN_DRIFT")


def _assert_parent_cf_pack(*, sealed_cf_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_cf_pack) != 0:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("CF_MANIFEST_VERIFY_NOT_ZERO")
    claims = _load_json_object(path=sealed_cf_pack / CLAIMS_FILE)
    _require_token(field="OWNER_GO_STATUS", payload=claims, expected="CONSUMED")
    _require_token(
        field="CONCRETE_SURFACE_SELECTION_STATUS",
        payload=claims,
        expected=PARENT_SELECTION_STATUS,
    )
    _require_token(field="MAX_GET_COUNT", payload=claims, expected="0")
    _require_token(field="AUTHORIZED_GET_COUNT", payload=claims, expected="0")
    _require_token(field="ACTUAL_GET_COUNT", payload=claims, expected="0")
    _require_token(field="POST_COUNT", payload=claims, expected="0")
    _require_token(field="HOPE_GET_FORBIDDEN", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="U06_DECISION_AFTER", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="NONE_BINDABLE_IS_NOT_EXCLUDE", payload=claims, expected=TRUE_TOKEN)
    _require_token(
        field="PLACEMENT_PIN_IMPLEMENTED_THIS_SLICE", payload=claims, expected=FALSE_TOKEN
    )
    _require_token(field="PATH_C_CLOSEOUT", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="ACCOUNT_BILLS_CANONICALIZED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="BLOCKER_ID", payload=claims, expected=PARENT_BLOCKER_ID)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=OWNER_GO)
    _require_token(
        field="NEXT_PRODUCTIVE_NODE",
        payload=claims,
        expected="U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_V1",
    )


def build_downstream_dependency_tree_v1() -> dict[str, Any]:
    records = (
        {
            "node_id": "U06_EQUITY_STOCK_PLACEMENT_IDENTITY",
            "classification": "ALREADY_CLOSED",
            "status": DURABLE_UNKNOWN_TOKEN,
            "reason": "PATH_B_PIN_IN_BASE_XOR_EVENT_SEPARATE_NOT_PROVABLE_ON_CURRENT_NON_EQ_VENUE_SURFACES",
        },
        {
            "node_id": "U06_KIND",
            "classification": "BLOCKED_BY_U06",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "INCLUDE_EXCLUDE_FORBIDDEN_WITHOUT_PRIMARY_PROOF",
        },
        {
            "node_id": "U06_ONCE_ONLY_ACCRUED_FEE",
            "classification": "ALREADY_CLOSED_SEMANTIC",
            "status": "INTACT",
            "reason": "U06_COUNTS_ALREADY_ACCRUED_FEES_ONCE_FUTURE_FEES_ARE_P01_NOT_U06",
        },
        {
            "node_id": "P01_FUTURE_FEE_RESERVE",
            "classification": "OUTSIDE_U06",
            "status": "UNCHANGED",
            "reason": "FUTURE_FEES_REMAIN_P01_NOT_U06",
        },
        {
            "node_id": "U05_KIND",
            "classification": "UNCHANGED",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "U05_PATH_B_PIN_REMAINS_DURABLE_UNKNOWN",
        },
        {
            "node_id": "ACCOUNT_EQUITY_SOURCE_MAPPING",
            "classification": "BLOCKED_BY_U06",
            "status": "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
            "reason": "U06_REMAINS_NAMED_UNRATIFIED_NECESSARY_CLASS",
        },
        {
            "node_id": "D6_KIND_SET",
            "classification": "BLOCKED_BY_U06",
            "status": KIND_SET_EMPTY,
            "reason": "NAMED_REMAINING_UNKNOWNS_U05_U06_RESIDUAL",
        },
        {
            "node_id": "MS2",
            "classification": "BLOCKED_BY_U06",
            "status": "NOT_AUTHORIZED",
            "reason": "MS1_KIND_SET_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "D7",
            "classification": "BLOCKED_BY_U06",
            "status": "NOT_AUTHORIZED",
            "reason": "D6_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "RESIDUAL_KIND",
            "classification": "BLOCKED_FROM_EXCLUDE_WHILE_U05_AND_U06_REMAIN_UNKNOWN",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "EXHAUSTIVENESS_CANNOT_CLOSE_WHILE_U05_AND_U06_REMAIN_UNKNOWN",
        },
        {
            "node_id": "RESIDUAL_PRIMARY_PROOF_ACQUISITION",
            "classification": "CAN_PROGRESS_WITH_U06_DURABLE_UNKNOWN",
            "status": "NOT_ACQUIRED",
            "reason": "SEPARATE_EVIDENCE_CLASS_REQUIRES_NEW_AUTHORITY_NOT_GET",
        },
        {
            "node_id": "U06_SURFACE_BINDING",
            "classification": "ALREADY_CLOSED",
            "status": PARENT_SELECTION_STATUS,
            "reason": "PARENT_NONE_BINDABLE_GET_COUNT_0_CONSUMED",
        },
    )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "selected_path": SELECTED_PATH,
        "placement_branch_closed": TRUE_TOKEN,
        "further_u06_placement_acquisition": "STOPPED",
        "path_c_closeout": FALSE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_productive_classification": "REQUIRES_NEW_AUTHORITY",
        "standing_full_core_dag_pin": DAG_PIN,
        "records": list(records),
    }


def execute_u06_equity_stock_placement_identity_durable_unknown_pin_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_cf_pack: Path | str | None = None,
    persist_as_of: str | None = None,
    selected_path: str = SELECTED_PATH,
) -> U06EquityStockPlacementIdentityDurableUnknownPinResultV1:
    if owner_go != OWNER_GO:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("ORIGIN_MAIN_SHA_MISMATCH")
    if selected_path != SELECTED_PATH:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("SELECTED_PATH_NOT_PATH_B")
    _assert_standing_pins()
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    reject_none_bindable_as_exclude_v1(claimed=PARENT_SELECTION_STATUS)
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    law_outcome = evaluate_u06_primary_proof_v1(proof={})
    if law_outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("ABSENT_PROOF_MUST_NOT_DECIDE")
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError(
            "ABSENT_PROOF_MUST_BE_NONQUALIFYING"
        )
    reject_durable_unknown_as_include_or_exclude_v1(claimed=law_outcome.outcome)
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cf_pack = (
        Path(sealed_cf_pack) if sealed_cf_pack is not None else repo / CANONICAL_CF_PACK_RELPATH
    )
    _assert_parent_cf_pack(sealed_cf_pack=cf_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    tree = build_downstream_dependency_tree_v1()
    halves = build_proof_halves_v1()
    if halves["placement_xor"] != PLACEMENT_XOR:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("PLACEMENT_XOR_DRIFT")
    if halves["pairing_requirement"] != (
        "fee_event_and_equity_stock_effect_from_same_economic_cause"
    ):
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("PAIRING_REQUIREMENT_DRIFT")
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "SELECTED_PATH": SELECTED_PATH,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CF_PACK": CANONICAL_CF_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "TARGET_UNKNOWN": TARGET_U06,
        "U06_EVIDENCE_CLASS": CLASS_U06,
        "EXPECTED_PRIMARY_PROOF_OBJECT": PROOF_OBJECT_U06,
        "PARENT_CONCRETE_SURFACE_SELECTION_STATUS": PARENT_SELECTION_STATUS,
        "PARENT_BLOCKER_ID": PARENT_BLOCKER_ID,
        "NO_ACQUIRABLE_NON_EQ_VENUE_PLACEMENT_IDENTITY": TRUE_TOKEN,
        "PLACEMENT_IDENTITY_STATUS": DURABLE_UNKNOWN_TOKEN,
        "PLACEMENT_XOR": PLACEMENT_XOR,
        "PLACEMENT_XOR_NOT_PROVABLE_ON_CURRENT_NON_EQ_VENUE_SURFACES": TRUE_TOKEN,
        "PAIRING_REQUIREMENT_UNCHANGED": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_FALSE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_ZERO_OR_ABSENT": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "NONE_BINDABLE_IS_NOT_EXCLUDE": TRUE_TOKEN,
        "NONE_BINDABLE_IS_NOT_ZERO_OR_NO_FEE": TRUE_TOKEN,
        "NO_GET_REQUIRED": TRUE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "NO_ALGEBRAIC_UPLIFT": TRUE_TOKEN,
        "NO_FEE_TOKEN_UPLIFT": TRUE_TOKEN,
        "NO_RETROACTIVE_SEALED_EVIDENCE_UPLIFT": TRUE_TOKEN,
        "NO_HOPE_GET": TRUE_TOKEN,
        "U06_ONCE_ONLY_SEMANTICS_INTACT": TRUE_TOKEN,
        "FUTURE_FEES_ARE_P01_NOT_U06": TRUE_TOKEN,
        "U06_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U06_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U06_DECISION_BASIS": DECISION_BASIS,
        "U06_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "FURTHER_U06_PLACEMENT_ACQUISITION": "STOPPED",
        "PLACEMENT_BRANCH_CLOSED": TRUE_TOKEN,
        "PATH_C_CLOSEOUT": FALSE_TOKEN,
        "U05_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING": DAG_PIN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "MAX_GET_COUNT": "0",
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "RETRY_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": "NOT_ATTEMPTED",
        "GET_ALONE_MAY_INCLUDE": FALSE_TOKEN,
        "GET_ALONE_MAY_EXCLUDE": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ALGEBRAIC_EQ_IDENTITY_FORBIDDEN": TRUE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
    }
    lineage = {
        "layer": "HISTORICAL",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "selected_path": SELECTED_PATH,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cf_pack": CANONICAL_CF_PACK_RELPATH,
        "reconstruction_source_authority": FALSE_TOKEN,
        "witness_acquisition_authorized": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "algebraic_uplift_used": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "trading_authority_unchanged": TRUE_TOKEN,
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
    current_proof = {
        "layer": "ADJUDICATED_CONCLUSION",
        "target_unknown": TARGET_U06,
        "placement_identity_status": DURABLE_UNKNOWN_TOKEN,
        "u06_decision_after": DECISION_REMAIN_UNKNOWN,
        "u05_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "residual_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "include_from_unknown": "FORBIDDEN",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_IN_BASE_PROOF",
        "path_c_closeout": FALSE_TOKEN,
        "further_u06_placement_acquisition": "STOPPED",
        "venue_eq_source_authority": FALSE_TOKEN,
        "no_get_required": TRUE_TOKEN,
        "u06_once_only_semantics_intact": TRUE_TOKEN,
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "no_acquirable_non_eq_venue_placement_identity": TRUE_TOKEN,
        "placement_xor_not_provable_on_current_non_eq_venue_surfaces": TRUE_TOKEN,
        "path_c_closeout": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "algebraic_eq_identity_forbidden": TRUE_TOKEN,
        "fee_token_alone_is_not_primary_proof": TRUE_TOKEN,
        "durable_unknown_is_not_include": TRUE_TOKEN,
        "durable_unknown_is_not_exclude": TRUE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
    }
    once_only = {
        "layer": "CANONICAL_AUTHORITY",
        "u06_once_only_semantics_intact": TRUE_TOKEN,
        "accrued_fees_counted_once": TRUE_TOKEN,
        "future_fees_are_p01_not_u06": TRUE_TOKEN,
        "p01_reserve_outside_u06": TRUE_TOKEN,
        "double_count_forbidden": TRUE_TOKEN,
        "blind_subtraction_forbidden": TRUE_TOKEN,
    }
    historical = {
        "layer": "HISTORICAL",
        "package_1_bills_uplift_forbidden": TRUE_TOKEN,
        "section_11_14_live_fee_observed_is_not_d6_u06_authority": TRUE_TOKEN,
        "g12_flatten_fills_uplift_forbidden": TRUE_TOKEN,
        "pre_prior_nonzero_fees_cannot_include": TRUE_TOKEN,
        "post_prior_live_bills_fee_zero_nonqualifying": TRUE_TOKEN,
        "reinterpretation_forbidden": TRUE_TOKEN,
        "fee_token_uplift_forbidden": TRUE_TOKEN,
        "sealed_evidence_uplift_forbidden": TRUE_TOKEN,
    }
    layers = {
        "CANONICAL_AUTHORITY": (
            "architecture_blocker_v1.json,proof_halves_v1.json,once_only_semantics_v1.json"
        ),
        "FORENSIC_RAW_EVIDENCE": "NONE_NO_GET_NO_SECRET_RESOLUTION",
        "ADJUDICATED_CONCLUSION": (
            "current_proof_evaluation_v1.json,downstream_dependency_tree_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json,historical_fee_evidence_non_uplift_v1.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=tree)
    _persist_json(path=store / "proof_halves_v1.json", payload=halves)
    _persist_json(path=store / "current_proof_evaluation_v1.json", payload=current_proof)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "once_only_semantics_v1.json", payload=once_only)
    _persist_json(path=store / "historical_fee_evidence_non_uplift_v1.json", payload=historical)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise U06EquityStockPlacementIdentityDurableUnknownPinError("MANIFEST_VERIFY_NOT_ZERO")
    return U06EquityStockPlacementIdentityDurableUnknownPinResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        selected_path=SELECTED_PATH,
        target_unknown=TARGET_U06,
        placement_identity_status=DURABLE_UNKNOWN_TOKEN,
        u06_decision_after=DECISION_REMAIN_UNKNOWN,
        further_u06_placement_acquisition="STOPPED",
        placement_branch_closed=TRUE_TOKEN,
        next_productive_node=NEXT_PRODUCTIVE_NODE,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


__all__ = (
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
    "PARENT_BLOCKER_ID",
    "SELECTED_PATH",
    "U06EquityStockPlacementIdentityDurableUnknownPinError",
    "execute_u06_equity_stock_placement_identity_durable_unknown_pin_v1",
    "reject_durable_unknown_as_include_or_exclude_v1",
)
