"""Today initial-stock Owner ratification.

Ratifies exactly one already sealed system-bound candidate. Does not
re-acquire equity, rewrite BT evidence, mint an anchor, or mutate
KIND_SET. Venue eq remains acquisition evidence, not reconstruction
source authority. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
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
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    RATIFIED_SOURCE_KIND_SET,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    FALSE_TOKEN,
    KIND_SET_EMPTY,
    NONE_TOKEN,
    TRUE_TOKEN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    C17_CREATED,
    CHECKPOINT_CAN_MINT_EQUITY,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EQ_RECONCILIATION_TARGET_ONLY,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    EQUITY_MINT_STATUS_NOT_MINTED,
    OBSERVATION_VS_AUTHORITY_CLASS,
    RUNNING_EQUITY_VALUE_STATE_ABSENT,
    assert_checkpoint_cannot_mint_equity_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CURRENTLY_DECISION_CAPABLE,
    EARLIEST_REMAINING_D6_BLOCKER as HISTORICAL_D6_BLOCKER,
    GATE_A_ID,
    GATE_B_ID,
    KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY as HISTORICAL_KIND_SET_BLOCKED_BY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_provenance_v1 import (
    STATUS_ABSENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_checkpoint_stock_value_contract_v1 import (
    STATUS_FLOW_NOT_STOCK,
    STATUS_NON_SOURCE_NO_BOUND_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BN_PACK_RELPATH,
    LIVE_EQUITY_STOCK_KIND_SET,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
    ROLE_RISK_CAPITAL_REDUCTION_ONLY,
    evaluate_today_live_equity_stock_kind_set_v1,
    ratified_live_equity_stock_kind_set_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_declaration_governed_binding_contract_v1 import (
    AS_OF_TIME_SEMANTIC,
    CANONICAL_PACK_RELPATH as CANONICAL_BT_PACK_RELPATH,
    CANDIDATE_FILE,
    ECONOMIC_MEANING,
    EQUITY_PRECISION_SEMANTIC,
    EQUITY_UNIT,
    RATIFICATION_NOT_RATIFIED,
    TODAY_SOURCE_TYPE,
    semantic_candidate_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BS_PACK_RELPATH,
    REASON_FIXTURE_CANNOT_PROMOTE,
    TODAY_SOURCE_KIND,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    Package1S6MappingClassificationError,
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "745708de030ae1887fb6c338c36eb680c981dc0f"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_today_initial_stock_ratification_wp1/"
    "2026-09-14T182100Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-14T18:21:00Z"
SCHEMA_CLASS = "TODAY_INITIAL_STOCK_OWNER_RATIFICATION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
OWNER_AUTHORITY_CLASS = "OWNER_GOVERNED_TODAY_INITIAL_STOCK_RATIFICATION"
RATIFICATION_DECISION = "RATIFY_THIS_PROVEN_SYSTEM_BOUND_CANDIDATE_AS_OPTION_D_TODAY_INITIAL_STOCK"
AUTHORIZED_DECLARATION_ID = "GOVERNED_TODAY_CANDIDATE_5d6c32292e0cb733"
AUTHORIZED_PROVENANCE_DIGEST = "2a7e0a570b1e497e0d7582bf4b8c1977f3d971214d8d3c7418e818fb3c5eee51"
AUTHORIZED_EQUITY_VALUE = "2.290727894593913"
AUTHORIZED_EQUITY_PRECISION = "15"
AUTHORIZED_SETTLEMENT_CURRENCY = "USDC"
AUTHORIZED_AS_OF_TIME = "2026-09-14T17:45:07Z"
AUTHORIZED_RAW_CONFIG_SHA256 = "36876f8378c2029823643ac2caf6b2fd24525b7d41afa0a32b6abef46c72d5fb"
AUTHORIZED_RAW_BALANCE_SHA256 = "1cc6264fc2f8e422cde89bb3b5f4a36d449182a7cd48ccb7007e2bec8055768c"
CANDIDATE_PRESENT = "PRESENT"
RATIFICATION_RATIFIED = "RATIFIED"
RUNNING_EQUITY_BLOCKED = "BLOCKED_NO_RATIFIED_ANCHOR"
VENUE_EQ_RECONCILIATION_UNBOUND = "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "TODAY_INITIAL_STOCK_ANCHOR_REQUIRED"
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_ANCHOR_V1"
RATIFICATION_FILE = "today_initial_stock_owner_ratification_v1.json"
IDENTITY_FILE = "authorized_candidate_identity_binding_v1.json"
REQUIRED_CANDIDATE_STRING_FIELDS: tuple[str, ...] = (
    "declaration_id",
    "provenance_digest",
    "source_kind",
    "source_type",
    "economic_meaning",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "equity_precision_semantic",
    "settlement_currency",
    "as_of_time",
    "as_of_time_semantic",
    "validity_window_start",
    "validity_window_end",
    "ratification_status",
    "initial_stock_anchor_status",
    "live_equity_stock_kind_set",
    "venue_eq_source_authority",
    "raw_config_sha256",
    "raw_balance_sha256",
)


class TodayInitialStockRatificationError(ValueError):
    """Fail-closed today initial-stock ratification violation."""


@dataclass(frozen=True)
class TodayInitialStockRatificationResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    declaration_id: str
    candidate_digest: str
    ratification_digest: str
    candidate_status: str
    ratification_status: str
    initial_stock_anchor_status: str
    live_equity_stock_kind_set: str
    venue_eq_source_authority: str
    venue_get_count_added: str
    venue_post_count: str
    owner_authority_bound: str
    candidate_substitution_guard: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _folder_from_as_of(as_of: str) -> str:
    return as_of.replace(":", "")


def ratification_digest_v1(payload: Mapping[str, str]) -> str:
    stripped = {key: value for key, value in payload.items() if key != "ratification_digest"}
    return _sha256_bytes(_canonical_json(stripped).encode("utf-8"))


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise TodayInitialStockRatificationError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise TodayInitialStockRatificationError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise TodayInitialStockRatificationError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise TodayInitialStockRatificationError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise TodayInitialStockRatificationError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise TodayInitialStockRatificationError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise TodayInitialStockRatificationError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise TodayInitialStockRatificationError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise TodayInitialStockRatificationError("C17_CREATED_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise TodayInitialStockRatificationError("BN_KIND_SET_NOT_EMPTY")
    if WIRE_SEND_PERMITTED is not False:
        raise TodayInitialStockRatificationError("WIRE_SEND_PERMITTED_NOT_FALSE")
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )
    assert_checkpoint_cannot_mint_equity_v1(
        equity_mint_status=EQUITY_MINT_STATUS_NOT_MINTED,
        running_equity_value_state=RUNNING_EQUITY_VALUE_STATE_ABSENT,
        claimed_equity_stock_value=STATUS_ABSENT,
        observation_vs_authority_class=OBSERVATION_VS_AUTHORITY_CLASS,
    )
    members = ratified_live_equity_stock_kind_set_v1(evaluate_today_live_equity_stock_kind_set_v1())
    if members:
        raise TodayInitialStockRatificationError("KIND_SET_NOT_EMPTY")


def load_sealed_today_candidate_v1(*, store_root: Path) -> dict[str, str]:
    path = Path(store_root) / CANDIDATE_FILE
    if not path.is_file():
        raise TodayInitialStockRatificationError("CANDIDATE_ABSENT")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TodayInitialStockRatificationError("CANDIDATE_MALFORMED") from exc
    if not isinstance(payload, dict):
        raise TodayInitialStockRatificationError("CANDIDATE_MALFORMED")
    typed: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TodayInitialStockRatificationError("CANDIDATE_MALFORMED")
        if isinstance(value, bool) or isinstance(value, (int, float)):
            raise TodayInitialStockRatificationError(f"NUMERIC_COERCION_FORBIDDEN:{key}")
        if not isinstance(value, str):
            raise TodayInitialStockRatificationError(f"CANDIDATE_MALFORMED:{key}")
        typed[key] = value
    for field in REQUIRED_CANDIDATE_STRING_FIELDS:
        if field not in typed or typed[field] == "":
            raise TodayInitialStockRatificationError(f"CANDIDATE_MALFORMED:MISSING:{field}")
    return typed


def assert_authorized_today_candidate_v1(candidate: Mapping[str, str]) -> str:
    declaration_id = candidate["declaration_id"]
    if declaration_id.startswith("FIXTURE"):
        raise TodayInitialStockRatificationError(REASON_FIXTURE_CANNOT_PROMOTE)
    recomputed = semantic_candidate_digest_v1(candidate)
    if candidate["provenance_digest"] != recomputed:
        raise TodayInitialStockRatificationError("CANDIDATE_DIGEST_MISMATCH")
    if declaration_id != AUTHORIZED_DECLARATION_ID:
        raise TodayInitialStockRatificationError("DECLARATION_ID_MISMATCH")
    if candidate["equity_value"] != AUTHORIZED_EQUITY_VALUE:
        raise TodayInitialStockRatificationError("EQUITY_VALUE_MISMATCH")
    if candidate["as_of_time"] != AUTHORIZED_AS_OF_TIME:
        raise TodayInitialStockRatificationError("AS_OF_TIME_MISMATCH")
    if recomputed != AUTHORIZED_PROVENANCE_DIGEST:
        raise TodayInitialStockRatificationError("CANDIDATE_SUBSTITUTION")
    if candidate["equity_unit"] != EQUITY_UNIT:
        raise TodayInitialStockRatificationError("EQUITY_UNIT_MISMATCH")
    if candidate["settlement_currency"] != AUTHORIZED_SETTLEMENT_CURRENCY:
        raise TodayInitialStockRatificationError("SETTLEMENT_CURRENCY_MISMATCH")
    if candidate["equity_precision"] != AUTHORIZED_EQUITY_PRECISION:
        raise TodayInitialStockRatificationError("EQUITY_PRECISION_MISMATCH")
    if candidate["equity_precision_semantic"] != EQUITY_PRECISION_SEMANTIC:
        raise TodayInitialStockRatificationError("EQUITY_PRECISION_SEMANTIC_DRIFT")
    if candidate["as_of_time_semantic"] != AS_OF_TIME_SEMANTIC:
        raise TodayInitialStockRatificationError("AS_OF_TIME_SEMANTIC_DRIFT")
    if candidate["validity_window_start"] != AUTHORIZED_AS_OF_TIME:
        raise TodayInitialStockRatificationError("VALIDITY_WINDOW_START_MISMATCH")
    if candidate["validity_window_end"] != AUTHORIZED_AS_OF_TIME:
        raise TodayInitialStockRatificationError("VALIDITY_WINDOW_END_MISMATCH")
    if candidate["economic_meaning"] != ECONOMIC_MEANING:
        raise TodayInitialStockRatificationError("ECONOMIC_MEANING_MISMATCH")
    if candidate["source_kind"] != TODAY_SOURCE_KIND:
        raise TodayInitialStockRatificationError("SOURCE_KIND_MISMATCH")
    if candidate["source_type"] != TODAY_SOURCE_TYPE:
        raise TodayInitialStockRatificationError("SOURCE_TYPE_MISMATCH")
    if candidate["ratification_status"] != RATIFICATION_NOT_RATIFIED:
        raise TodayInitialStockRatificationError("SEALED_CANDIDATE_RATIFICATION_STATUS_DRIFT")
    if candidate["initial_stock_anchor_status"] != STATUS_ABSENT:
        raise TodayInitialStockRatificationError("ANCHOR_NOT_ABSENT")
    if candidate["live_equity_stock_kind_set"] != KIND_SET_EMPTY:
        raise TodayInitialStockRatificationError("KIND_SET_NOT_EMPTY")
    if candidate["venue_eq_source_authority"] != FALSE_TOKEN:
        raise TodayInitialStockRatificationError("VENUE_EQ_SOURCE_AUTHORITY_DRIFT")
    if candidate["raw_config_sha256"] != AUTHORIZED_RAW_CONFIG_SHA256:
        raise TodayInitialStockRatificationError("RAW_CONFIG_SHA256_MISMATCH")
    if candidate["raw_balance_sha256"] != AUTHORIZED_RAW_BALANCE_SHA256:
        raise TodayInitialStockRatificationError("RAW_BALANCE_SHA256_MISMATCH")
    if candidate["equity_unit"] == candidate["settlement_currency"]:
        raise TodayInitialStockRatificationError("EQUITY_UNIT_COLLAPSED_INTO_CURRENCY")
    return recomputed


def execute_live_equity_stock_today_initial_stock_ratification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    evidence_root: Path,
    sealed_bt_pack: Path,
    persist_as_of: str = CANONICAL_PERSIST_AS_OF,
) -> TodayInitialStockRatificationResultV1:
    if owner_go != OWNER_GO:
        raise TodayInitialStockRatificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise TodayInitialStockRatificationError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    sealed = Path(sealed_bt_pack)
    try:
        if verify_manifest_sha256_v1(store_root=sealed) != 0:
            raise TodayInitialStockRatificationError("BT_MANIFEST_VERIFY_FAILED")
    except Package1S6MappingClassificationError as exc:
        raise TodayInitialStockRatificationError("BT_MANIFEST_VERIFY_FAILED") from exc
    candidate = load_sealed_today_candidate_v1(store_root=sealed)
    candidate_digest = assert_authorized_today_candidate_v1(candidate)
    candidate_bytes_sha256 = _sha256_bytes((sealed / CANDIDATE_FILE).read_bytes())
    store = Path(evidence_root) / _folder_from_as_of(persist_as_of)
    if store.exists() and any(store.iterdir()):
        raise TodayInitialStockRatificationError("RATIFICATION_STORE_ALREADY_PRESENT")
    store.mkdir(parents=True, exist_ok=True)
    identity = {
        "declaration_id": candidate["declaration_id"],
        "candidate_digest": candidate_digest,
        "candidate_file_sha256": candidate_bytes_sha256,
        "sealed_bt_pack": CANONICAL_BT_PACK_RELPATH,
        "equity_value": candidate["equity_value"],
        "equity_unit": candidate["equity_unit"],
        "settlement_currency": candidate["settlement_currency"],
        "equity_precision": candidate["equity_precision"],
        "equity_precision_semantic": candidate["equity_precision_semantic"],
        "as_of_time": candidate["as_of_time"],
        "as_of_time_semantic": candidate["as_of_time_semantic"],
        "validity_window_start": candidate["validity_window_start"],
        "validity_window_end": candidate["validity_window_end"],
        "economic_meaning": candidate["economic_meaning"],
        "source_kind": candidate["source_kind"],
        "source_type": candidate["source_type"],
        "raw_config_sha256": candidate["raw_config_sha256"],
        "raw_balance_sha256": candidate["raw_balance_sha256"],
        "sealed_candidate_ratification_status": candidate["ratification_status"],
        "candidate_rewritten": FALSE_TOKEN,
    }
    ratification = {
        "schema_class": SCHEMA_CLASS,
        "contract_version": CONTRACT_VERSION,
        "owner_go": OWNER_GO,
        "owner_authority_class": OWNER_AUTHORITY_CLASS,
        "ratification_decision": RATIFICATION_DECISION,
        "declaration_id": AUTHORIZED_DECLARATION_ID,
        "candidate_digest": candidate_digest,
        "candidate_file_sha256": candidate_bytes_sha256,
        "sealed_bt_pack": CANONICAL_BT_PACK_RELPATH,
        "candidate_status": CANDIDATE_PRESENT,
        "ratification_status": RATIFICATION_RATIFIED,
        "initial_stock_anchor_status": STATUS_ABSENT,
        "live_equity_stock_kind_set": KIND_SET_EMPTY,
        "venue_eq_source_authority": FALSE_TOKEN,
        "reconstruction_source_authority": FALSE_TOKEN,
        "owner_ratification": TRUE_TOKEN,
        "initial_stock_acquisition_evidence": FALSE_TOKEN,
        "venue_reconciliation_target": FALSE_TOKEN,
        "candidate_is_not_anchor": TRUE_TOKEN,
        "ratification_is_not_anchor": TRUE_TOKEN,
        "persist_as_of": persist_as_of,
        "candidate_as_of_time_unchanged": TRUE_TOKEN,
        "economic_meaning": candidate["economic_meaning"],
        "equity_value": candidate["equity_value"],
        "equity_unit": candidate["equity_unit"],
        "settlement_currency": candidate["settlement_currency"],
        "as_of_time": candidate["as_of_time"],
        "as_of_time_semantic": candidate["as_of_time_semantic"],
    }
    ratification["ratification_digest"] = ratification_digest_v1(ratification)
    _persist_json(path=store / IDENTITY_FILE, payload=identity)
    _persist_json(path=store / RATIFICATION_FILE, payload=ratification)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": persist_as_of,
        "SEALED_BT_PACK": CANONICAL_BT_PACK_RELPATH,
        "SEALED_BS_PACK": CANONICAL_BS_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "BT_CONTRACT_REUSED": TRUE_TOKEN,
        "BS_CONTRACT_REUSED": TRUE_TOKEN,
        "BN_CONTRACT_REUSED": TRUE_TOKEN,
        "NEW_CANONICAL_DEFINITION": FALSE_TOKEN,
        "NEW_CANONICAL_SEMANTICS": FALSE_TOKEN,
        "LEGACY_SEMANTICS_RECONSTRUCTED": FALSE_TOKEN,
        "KINDS_INVENTED_THIS_GO": FALSE_TOKEN,
        "INVENTED_IDENTITIES": FALSE_TOKEN,
        "INVENTED_VALUES": FALSE_TOKEN,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER_AUTHORITY_CLASS": OWNER_AUTHORITY_CLASS,
        "RATIFICATION_DECISION": RATIFICATION_DECISION,
        "DECLARATION_ID": AUTHORIZED_DECLARATION_ID,
        "CANDIDATE_DIGEST": candidate_digest,
        "CANDIDATE_STATUS": CANDIDATE_PRESENT,
        "RATIFICATION_STATUS": RATIFICATION_RATIFIED,
        "OWNER_RATIFICATION_REQUIRED": FALSE_TOKEN,
        "INITIAL_STOCK_ANCHOR_STATUS": STATUS_ABSENT,
        "LIVE_EQUITY_STOCK_KIND_SET": KIND_SET_EMPTY,
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "CHECKPOINT_STATUS": STATUS_NON_SOURCE_NO_BOUND_STOCK,
        "EVENT_STREAM_BINDING_STATUS": STATUS_FLOW_NOT_STOCK,
        "RUNNING_EQUITY_RECONSTRUCTION_STATUS": RUNNING_EQUITY_BLOCKED,
        "VENUE_EQ_RECONCILIATION_STATUS": VENUE_EQ_RECONCILIATION_UNBOUND,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "CHECKPOINT_MINTS_EQUITY": FALSE_TOKEN,
        "P01_ROLE": ROLE_RISK_CAPITAL_REDUCTION_ONLY,
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "VENUE_GET_COUNT": "0",
        "VENUE_GET_COUNT_ADDED": "0",
        "VENUE_POST_COUNT": "0",
        "POST_COUNT": "0",
        "GATE_A_EXECUTED": FALSE_TOKEN,
        "GATE_B_EXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "BULL_BEAR_STATE_SWITCH_UNCHANGED": TRUE_TOKEN,
        "SELF_LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_AUTONOMY_UNCHANGED": TRUE_TOKEN,
        "TOP20_RANKING_UNIVERSE_UNCHANGED": TRUE_TOKEN,
        "TOP20_SELECTION_BINDINGS_UNCHANGED": TRUE_TOKEN,
        "STEP_29P_UNCHANGED": TRUE_TOKEN,
        "EQUITY_VALUE": AUTHORIZED_EQUITY_VALUE,
        "EQUITY_UNIT": EQUITY_UNIT,
        "SETTLEMENT_CURRENCY": AUTHORIZED_SETTLEMENT_CURRENCY,
        "AS_OF_TIME": AUTHORIZED_AS_OF_TIME,
        "AS_OF_TIME_SEMANTIC": AS_OF_TIME_SEMANTIC,
        "GATE_A_ID": GATE_A_ID,
        "GATE_B_ID": GATE_B_ID,
        "CANDIDATE_SUBSTITUTION_GUARD": "EXACT_AUTHORIZED_IDENTITY_ONLY",
        "BT_CANDIDATE_REWRITTEN": FALSE_TOKEN,
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bt_pack": CANONICAL_BT_PACK_RELPATH,
            "parent_bs_pack": CANONICAL_BS_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
            "raw_epistemic_class": "INITIAL_STOCK_ACQUISITION_EVIDENCE",
            "derived_epistemic_class": "OWNER_RATIFIED_TODAY_INITIAL_STOCK",
            "reconstruction_source_authority": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "venue_eq_as_source": "FORBIDDEN",
            "checkpoint_mints_equity": "FORBIDDEN",
            "candidate_rewrite": "FORBIDDEN",
            "candidate_substitution": "FORBIDDEN",
            "latest_candidate": "FORBIDDEN",
            "fixture_promote": "FORBIDDEN",
            "anchor_mint": "FORBIDDEN",
            "kind_set_mutation": "FORBIDDEN",
            "self_ratify_without_owner_go": "FORBIDDEN",
            "fresh_get": "FORBIDDEN",
            "venue_post": "FORBIDDEN",
            "empty_live_kind_set": KIND_SET_EMPTY,
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "venue_get_count_added": "0",
            "venue_post_count": "0",
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    if (sealed / CANDIDATE_FILE).read_bytes() != (
        Path(repo_root) / CANONICAL_BT_PACK_RELPATH / CANDIDATE_FILE
    ).read_bytes() and sealed.resolve() == (Path(repo_root) / CANONICAL_BT_PACK_RELPATH).resolve():
        raise TodayInitialStockRatificationError("BT_CANDIDATE_REWRITTEN")
    return TodayInitialStockRatificationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        declaration_id=AUTHORIZED_DECLARATION_ID,
        candidate_digest=candidate_digest,
        ratification_digest=ratification["ratification_digest"],
        candidate_status=CANDIDATE_PRESENT,
        ratification_status=RATIFICATION_RATIFIED,
        initial_stock_anchor_status=STATUS_ABSENT,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        venue_eq_source_authority=FALSE_TOKEN,
        venue_get_count_added="0",
        venue_post_count="0",
        owner_authority_bound=OWNER_AUTHORITY_CLASS,
        candidate_substitution_guard="EXACT_AUTHORIZED_IDENTITY_ONLY",
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "AUTHORIZED_DECLARATION_ID",
    "AUTHORIZED_PROVENANCE_DIGEST",
    "CANONICAL_PACK_RELPATH",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "REASON_FIXTURE_CANNOT_PROMOTE",
    "TodayInitialStockRatificationError",
    "assert_authorized_today_candidate_v1",
    "execute_live_equity_stock_today_initial_stock_ratification_v1",
    "load_sealed_today_candidate_v1",
    "ratification_digest_v1",
]
