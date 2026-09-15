"""Pin U05 embedding identity as durable UNKNOWN and close the witness branch.

Consumes Owner-GO PATH_B. Does not GET. Does not POST. Does not INCLUDE
or EXCLUDE U05. Does not invent PATH_C closeout. Does not acquire a
witness. Durable UNKNOWN is not false, excluded, zero, or absent.
AUTHORITY_EFFECT=NONE.

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
    CLASS_U06,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_RESOLVED_STATUS,
    P01_U05_OVERLAP_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CD_PACK_RELPATH,
)

OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_CHOOSE_PATH_A_SPEC_PERSIST_OR_PATH_B_DURABLE_UNKNOWN_"
    "AFTER_NO_ACQUIRABLE_EMBEDDING_WITNESS_SOURCE_V1"
)
SELECTED_PATH = "PATH_B"
EXPECTED_ORIGIN_MAIN_SHA = "d3dbac35af5c9cfc3bc1a4087aeecc66950c58c6"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_u05_durable_unknown_embedding_identity_pin_v1/2026-09-15T014000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T01:40:00Z"
SCHEMA_CLASS = "U05_DURABLE_UNKNOWN_EMBEDDING_IDENTITY_PIN_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
PRIMARY_PROOF_STATUS = "WITNESS_BRANCH_CLOSED_EMBEDDING_IDENTITY_DURABLE_UNKNOWN_U05_REMAIN_UNKNOWN"
DECISION_BASIS = (
    "NO_ACQUIRABLE_REAL_WORLD_EMBEDDING_WITNESS_SOURCE_PATH_B_PIN_DURABLE_UNKNOWN_IS_NOT_EXCLUDE"
)
BLOCKER_ID = "U05_EMBEDDING_WITNESS_BRANCH_CLOSED_DURABLE_UNKNOWN_U06_PRIMARY_PROOF_NOT_ACQUIRED"
ARCHITECTURE_BLOCKER = (
    "U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_PRIMARY_PROOF_NOT_ACQUIRED"
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_FOR_FORENSIC_ACQUISITION_OF_U06_PAIRED_FEE_EVENT_AND_"
    "ONCE_ONLY_EQUITY_STOCK_EFFECT_PRIMARY_PROOF_V1"
)
NEXT_ACTION = "STOP_AWAIT_OWNER_GO_FOR_U06_PRIMARY_PROOF_ACQUISITION"
NEXT_PRODUCTIVE_NODE = CLASS_U06
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class U05DurableUnknownEmbeddingIdentityPinError(ValueError):
    """Fail-closed U05 durable-unknown embedding pin violation."""


@dataclass(frozen=True)
class U05DurableUnknownEmbeddingIdentityPinResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    selected_path: str
    non_algebraic_embedding_identity: str
    u05_decision_after: str
    further_u05_witness_acquisition: str
    witness_branch_closed: str
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
        raise U05DurableUnknownEmbeddingIdentityPinError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise U05DurableUnknownEmbeddingIdentityPinError(f"{field}_DRIFT:{actual}")


def _assert_standing_pins() -> None:
    if WIRE_SEND_PERMITTED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05DurableUnknownEmbeddingIdentityPinError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05DurableUnknownEmbeddingIdentityPinError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise U05DurableUnknownEmbeddingIdentityPinError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise U05DurableUnknownEmbeddingIdentityPinError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("COMPLETE_STREAM_MUST_REMAIN_UNPROVEN")
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if MS2_AUTHORIZED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise U05DurableUnknownEmbeddingIdentityPinError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise U05DurableUnknownEmbeddingIdentityPinError("BILLS_MUST_REMAIN_NONCANONICAL")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise U05DurableUnknownEmbeddingIdentityPinError("DAG_PIN_DRIFT")
    if P01_U05_OVERLAP_STATE != "UNRESOLVED":
        raise U05DurableUnknownEmbeddingIdentityPinError("P01_U05_OVERLAP_STATE_DRIFT")
    if P01_U05_OVERLAP_RESOLVED_STATUS != FALSE_TOKEN:
        raise U05DurableUnknownEmbeddingIdentityPinError("P01_U05_OVERLAP_MUST_REMAIN_UNRESOLVED")


def _assert_parent_cd_pack(*, sealed_cd_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_cd_pack) != 0:
        raise U05DurableUnknownEmbeddingIdentityPinError("CD_MANIFEST_VERIFY_NOT_ZERO")
    claims = _load_json_object(path=sealed_cd_pack / CLAIMS_FILE)
    _require_token(field="ACTUAL_GET_COUNT", payload=claims, expected="1")
    _require_token(field="RETRY_COUNT", payload=claims, expected="0")
    _require_token(field="POST_COUNT", payload=claims, expected="0")
    _require_token(field="OWNER_GO_STATUS", payload=claims, expected="CONSUMED")
    _require_token(field="NON_ALGEBRAIC_EMBEDDING_IDENTITY", payload=claims, expected="UNKNOWN")
    _require_token(field="U05_DECISION_AFTER", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="INDEPENDENT_LIABILITY_EVENT_PROVEN", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=claims, expected=FALSE_TOKEN)


def _reject_include_exclude(*, claimed: str) -> None:
    if claimed in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE, "FALSE", "true", "0", "absent"}:
        raise U05DurableUnknownEmbeddingIdentityPinError(
            f"DURABLE_UNKNOWN_CANNOT_BE_NORMALIZED:{claimed}"
        )


def build_downstream_dependency_tree_v1() -> dict[str, Any]:
    records = (
        {
            "node_id": "NON_ALGEBRAIC_EMBEDDING_IDENTITY",
            "classification": "ALREADY_CLOSED",
            "status": DURABLE_UNKNOWN_TOKEN,
            "reason": "PATH_B_PIN_NO_ACQUIRABLE_WITNESS_SOURCE",
        },
        {
            "node_id": "U05_KIND",
            "classification": "BLOCKED_BY_U05",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "INCLUDE_EXCLUDE_FORBIDDEN_WITHOUT_PRIMARY_PROOF",
        },
        {
            "node_id": "P01_U05_OVERLAP",
            "classification": "BLOCKED_BY_U05",
            "status": "UNRESOLVED",
            "reason": "OVERLAP_NOT_DISPROVEN_AND_NEW_P01_SEMANTICS_FORBIDDEN",
        },
        {
            "node_id": "F12_F13",
            "classification": "BLOCKED_BY_U05",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "EMBEDDING_AND_EQUITY_STOCK_EFFECT_REMAIN_UNKNOWN",
        },
        {
            "node_id": "ACCOUNT_EQUITY_SOURCE_MAPPING",
            "classification": "BLOCKED_BY_U05",
            "status": "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
            "reason": "U05_REMAINS_NAMED_UNRATIFIED_NECESSARY_CLASS",
        },
        {
            "node_id": "RESIDUAL",
            "classification": "BLOCKED_BY_U05",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "EXHAUSTIVENESS_CANNOT_CLOSE_WHILE_U05_AND_U06_REMAIN_UNKNOWN",
        },
        {
            "node_id": "D6_KIND_SET",
            "classification": "BLOCKED_BY_U05",
            "status": KIND_SET_EMPTY,
            "reason": "NAMED_REMAINING_UNKNOWNS_U05_U06_RESIDUAL",
        },
        {
            "node_id": "MS2",
            "classification": "BLOCKED_BY_U05",
            "status": "NOT_AUTHORIZED",
            "reason": "MS1_KIND_SET_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "D7",
            "classification": "BLOCKED_BY_U05",
            "status": "NOT_AUTHORIZED",
            "reason": "D6_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "D12_SIZING",
            "classification": "BLOCKED_BY_U05",
            "status": "NOT_BUILT",
            "reason": "MAPPING_AND_KIND_SET_UNRESOLVED",
        },
        {
            "node_id": "U06_KIND",
            "classification": "CAN_PROGRESS_WITH_U05_DURABLE_UNKNOWN",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "SEPARATE_EVIDENCE_CLASS_REQUIRES_NEW_AUTHORITY",
        },
        {
            "node_id": "U06_PRIMARY_PROOF_ACQUISITION",
            "classification": "REQUIRES_NEW_AUTHORITY",
            "status": "NOT_ACQUIRED",
            "reason": "PATH_B_DOES_NOT_AUTHORIZE_U06_GET_OR_ACQUISITION",
        },
        {
            "node_id": "INTEREST_ACCRUED_GET",
            "classification": "ALREADY_CLOSED",
            "status": "CONSUMED_COUNT_1",
            "reason": "RETRY_FORBIDDEN",
        },
    )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "selected_path": SELECTED_PATH,
        "witness_branch_closed": TRUE_TOKEN,
        "further_u05_witness_acquisition": "STOPPED",
        "path_c_closeout": FALSE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_productive_classification": "REQUIRES_NEW_AUTHORITY",
        "standing_full_core_dag_pin": DAG_PIN,
        "records": list(records),
    }


def execute_u05_durable_unknown_embedding_identity_pin_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_cd_pack: Path | str | None = None,
    persist_as_of: str | None = None,
    selected_path: str = SELECTED_PATH,
) -> U05DurableUnknownEmbeddingIdentityPinResultV1:
    if owner_go != OWNER_GO:
        raise U05DurableUnknownEmbeddingIdentityPinError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise U05DurableUnknownEmbeddingIdentityPinError("ORIGIN_MAIN_SHA_MISMATCH")
    if selected_path != SELECTED_PATH:
        raise U05DurableUnknownEmbeddingIdentityPinError("SELECTED_PATH_NOT_PATH_B")
    _assert_standing_pins()
    _reject_include_exclude(claimed=DURABLE_UNKNOWN_TOKEN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cd_pack = (
        Path(sealed_cd_pack) if sealed_cd_pack is not None else repo / CANONICAL_CD_PACK_RELPATH
    )
    _assert_parent_cd_pack(sealed_cd_pack=cd_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    tree = build_downstream_dependency_tree_v1()
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
        "PARENT_CD_PACK": CANONICAL_CD_PACK_RELPATH,
        "NO_ACQUIRABLE_REAL_WORLD_EMBEDDING_WITNESS_SOURCE": TRUE_TOKEN,
        "PREVIOUS_OWNER_SUPPLY_ASSUMPTION": "NOT_OPERATIONALIZED",
        "NON_ALGEBRAIC_EMBEDDING_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_FALSE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_ZERO_OR_ABSENT": TRUE_TOKEN,
        "U05_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U05_DECISION_BASIS": DECISION_BASIS,
        "U05_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "FURTHER_U05_EMBEDDING_WITNESS_ACQUISITION": "STOPPED",
        "WITNESS_BRANCH_CLOSED": TRUE_TOKEN,
        "PATH_C_CLOSEOUT": FALSE_TOKEN,
        "U06_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING": DAG_PIN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "INTEREST_ACCRUED_GET_COUNT_REMAINS": "1",
        "RETRY_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": "NOT_ATTEMPTED",
        "GET_ALONE_MAY_INCLUDE": FALSE_TOKEN,
        "GET_ALONE_MAY_EXCLUDE": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
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
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "selected_path": SELECTED_PATH,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cd_pack": CANONICAL_CD_PACK_RELPATH,
        "reconstruction_source_authority": FALSE_TOKEN,
        "witness_acquisition_authorized": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    current_proof = {
        "layer": "ADJUDICATED_CONCLUSION",
        "non_algebraic_embedding_identity": DURABLE_UNKNOWN_TOKEN,
        "u05_decision_after": DECISION_REMAIN_UNKNOWN,
        "u06_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "residual_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "include_from_unknown": "FORBIDDEN",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_IN_BASE_PROOF",
        "path_c_closeout": FALSE_TOKEN,
        "further_u05_witness_acquisition": "STOPPED",
        "venue_eq_source_authority": FALSE_TOKEN,
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "no_acquirable_real_world_embedding_witness_source": TRUE_TOKEN,
        "previous_owner_supply_assumption": "NOT_OPERATIONALIZED",
        "path_c_closeout": FALSE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=tree)
    _persist_json(path=store / "current_proof_evaluation_v1.json", payload=current_proof)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise U05DurableUnknownEmbeddingIdentityPinError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise U05DurableUnknownEmbeddingIdentityPinError("MANIFEST_VERIFY_NOT_ZERO")
    return U05DurableUnknownEmbeddingIdentityPinResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        selected_path=SELECTED_PATH,
        non_algebraic_embedding_identity=DURABLE_UNKNOWN_TOKEN,
        u05_decision_after=DECISION_REMAIN_UNKNOWN,
        further_u05_witness_acquisition="STOPPED",
        witness_branch_closed=TRUE_TOKEN,
        next_productive_node=NEXT_PRODUCTIVE_NODE,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


__all__ = (
    "OWNER_GO",
    "SELECTED_PATH",
    "execute_u05_durable_unknown_embedding_identity_pin_v1",
)
