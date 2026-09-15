"""TODAY declaration governed-binding contract v2.

Versions the §11.2.1.BS Today contract so Owner authorizes one
system-bound candidate without guessing venue/identity/precision/time.
Fresh GET pair is INITIAL_STOCK_ACQUISITION_EVIDENCE, not source
authority. Candidate is not ratification and not the stock anchor.
KIND_SET stays EMPTY_FAIL_CLOSED. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

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
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
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
    EQUITY_UNIT_SETTLEMENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BS_PACK_RELPATH,
    INSTRUMENT_ACCOUNT_LEVEL,
    TODAY_SOURCE_KIND,
    evaluate_today_initial_stock_source_kind_boundary_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT_V1"
EXPECTED_ORIGIN_MAIN_SHA = "956ce6ee5238181d75a8ae74713cea8cb8f8db93"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/"
    "full_core_live_equity_stock_today_declaration_governed_binding_contract_wp1/"
    "2026-09-14T174507Z"
)
CLAIMS_FILE = "claims.json"
SCHEMA_CLASS = "TODAY_DECLARATION_GOVERNED_BINDING_CONTRACT_V1"
PARENT_TODAY_SCHEMA_CLASS = "TODAY_INITIAL_STOCK_SOURCE_KIND_V1"
CONTRACT_VERSION = "v2"
AUTHORITY_EFFECT = "NONE"
TODAY_SOURCE_TYPE = "SYSTEM_BOUND_GOVERNED_ACQUISITION_PAIR"
ECONOMIC_MEANING = "ABSOLUTE_SETTLEMENT_CURRENCY_ACCOUNT_EQUITY_FOR_OPTION_D_PRIOR"
ACCOUNT_IDENTITY_BINDING = "GOVERNED_BINDING"
SETTLEMENT_CURRENCY_BINDING = "GOVERNED_BINDING"
EQUITY_UNIT = EQUITY_UNIT_SETTLEMENT
EQUITY_PRECISION_SEMANTIC = "LEXICAL_DECIMAL_SCALE_OF_EXACT_BOUND_EQUITY_VALUE_STRING"
AS_OF_TIME_SEMANTIC = "GOVERNED_ACQUISITION_OBSERVATION_TIME"
EQUITY_VALUE_FIELD = "eq"
FORBIDDEN_EQUITY_FIELDS: frozenset[str] = frozenset(
    {"totalEq", "eqUsd", "cashBal", "availEq", "adjEq", "pnl", "upl", "uplRatio"}
)
EXPECTED_ACCOUNT_MODE = "2"
EXPECTED_POS_MODE = "net_mode"
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
AUTHORIZED_ENDPOINTS: tuple[str, ...] = (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_BALANCE,
)
FORBIDDEN_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/asset/transfer",
    "/api/v5/account/set-position-mode",
    "/api/v5/account/set-leverage",
)
MAX_NETWORK_REQUEST_COUNT = 2
DEFAULT_MAX_RETRIES = 0
DEFAULT_TIMEOUT_SECONDS = 10.0
CANDIDATE_ID_PREFIX = "GOVERNED_TODAY_CANDIDATE_"
CANDIDATE_PRESENT_UNRATIFIED = "PRESENT_UNRATIFIED"
RATIFICATION_NOT_RATIFIED = "NOT_RATIFIED"
SOURCE_KIND_DEFINED_NOT_MEMBER = "DEFINED_NOT_KIND_SET_MEMBER"
RUNNING_EQUITY_BLOCKED = "BLOCKED_NO_RATIFIED_ANCHOR"
VENUE_EQ_RECONCILIATION_UNBOUND = "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "TODAY_INITIAL_STOCK_OWNER_RATIFICATION_REQUIRED"
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION_V1"
RAW_CONFIG_BODY_FILE = "raw_account_config_response_body.json"
RAW_BALANCE_BODY_FILE = "raw_account_balance_response_body.json"
RAW_CONFIG_CAPTURE_FILE = "raw_http_capture_config_v1.json"
RAW_BALANCE_CAPTURE_FILE = "raw_http_capture_balance_v1.json"
CANDIDATE_FILE = "system_bound_today_initial_stock_candidate_v1.json"
JOIN_FILE = "fail_closed_d4_join_v1.json"
CONTRACT_FILE = "today_declaration_governed_binding_contract_v1.json"
_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_LEXICAL_DECIMAL = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class TodayDeclarationGovernedBindingContractError(ValueError):
    """Fail-closed today governed-binding contract violation."""


@dataclass(frozen=True)
class AccountConfigJoinFactsV1:
    uid: str
    settle_ccy: str
    acct_lv: str
    pos_mode: str


@dataclass(frozen=True)
class SettlementEqRowV1:
    ccy: str
    eq: str
    account_utime_raw: str
    row_utime_raw: str
    matching_row_count: str


@dataclass(frozen=True)
class AcquisitionCaptureV1:
    endpoint: str
    request_utc: str
    response_utc: str
    http_status: str
    body_bytes: bytes
    sha256: str


@dataclass(frozen=True)
class SystemBoundTodayCandidateV1:
    declaration_id: str
    payload: dict[str, str]
    candidate_status: str
    ratification_status: str
    initial_stock_anchor_status: str
    live_equity_stock_kind_set: str
    venue_eq_source_authority: str
    owner_ratification_required: str


@dataclass(frozen=True)
class TodayDeclarationGovernedBindingResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    contract_version: str
    target_stock_semantic: str
    account_identity_binding: str
    settlement_currency_binding: str
    equity_value: str
    equity_unit: str
    equity_precision: str
    equity_precision_semantic: str
    as_of_time: str
    as_of_time_semantic: str
    config_uid_d4_match: str
    config_settle_ccy_d4_match: str
    matching_balance_row_count: str
    raw_config_evidence_sha256: str
    raw_balance_evidence_sha256: str
    venue_account_utime_raw: str
    venue_settlement_row_utime_raw: str
    candidate_status: str
    ratification_status: str
    initial_stock_anchor_status: str
    live_equity_stock_kind_set: str
    venue_eq_source_authority: str
    venue_get_count: str
    venue_post_count: str
    owner_ratification_required: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str
    evidence_manifest: str


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _folder_from_as_of(as_of: str) -> str:
    return as_of.replace(":", "")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _persist_raw_bytes(*, path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(body)
    tmp.replace(path)


def _require_json_string(*, row: Mapping[str, Any], field: str) -> str:
    if field not in row:
        raise TodayDeclarationGovernedBindingContractError(f"FIELD_MISSING:{field}")
    raw = row.get(field)
    if isinstance(raw, bool) or isinstance(raw, (int, float)):
        raise TodayDeclarationGovernedBindingContractError(f"NUMERIC_COERCION_FORBIDDEN:{field}")
    if not isinstance(raw, str):
        raise TodayDeclarationGovernedBindingContractError(
            f"FIELD_NOT_STRING:{field}:{type(raw).__name__}"
        )
    if raw == "":
        raise TodayDeclarationGovernedBindingContractError(f"FIELD_EMPTY:{field}")
    return raw


def lexical_decimal_scale_of_exact_equity_value_string_v1(value: str) -> str:
    if not isinstance(value, str):
        raise TodayDeclarationGovernedBindingContractError(
            f"EQUITY_VALUE_NOT_STRING:{type(value).__name__}"
        )
    if _LEXICAL_DECIMAL.fullmatch(value) is None:
        raise TodayDeclarationGovernedBindingContractError("EQUITY_VALUE_MALFORMED")
    if "." not in value:
        return "0"
    return str(len(value.split(".", 1)[1]))


def semantic_candidate_digest_v1(payload: Mapping[str, str]) -> str:
    stripped = {key: value for key, value in payload.items() if key != "provenance_digest"}
    return _sha256_bytes(_canonical_json(stripped).encode("utf-8"))


def derive_declaration_id_v1(bound_fields: Mapping[str, str]) -> str:
    if "declaration_id" in bound_fields or "provenance_digest" in bound_fields:
        raise TodayDeclarationGovernedBindingContractError(
            "DECLARATION_ID_INPUT_MUST_EXCLUDE_ID_AND_DIGEST"
        )
    digest = _sha256_bytes(_canonical_json(bound_fields).encode("utf-8"))
    declaration_id = f"{CANDIDATE_ID_PREFIX}{digest[:16]}"
    if declaration_id.startswith("FIXTURE"):
        raise TodayDeclarationGovernedBindingContractError("DECLARATION_ID_FIXTURE_FORBIDDEN")
    return declaration_id


def extract_account_config_join_facts_v1(
    payload: Mapping[str, Any],
) -> AccountConfigJoinFactsV1:
    if not isinstance(payload, Mapping):
        raise TodayDeclarationGovernedBindingContractError("CONFIG_PAYLOAD_NOT_OBJECT")
    code = payload.get("code")
    if not isinstance(code, str) or code != "0":
        raise TodayDeclarationGovernedBindingContractError("CONFIG_VENUE_CODE_NOT_ZERO")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], Mapping):
        raise TodayDeclarationGovernedBindingContractError("CONFIG_DATA_NOT_SINGLE_OBJECT")
    row = data[0]
    return AccountConfigJoinFactsV1(
        uid=_require_json_string(row=row, field="uid"),
        settle_ccy=_require_json_string(row=row, field="settleCcy"),
        acct_lv=_require_json_string(row=row, field="acctLv"),
        pos_mode=_require_json_string(row=row, field="posMode"),
    )


def extract_settlement_eq_row_v1(
    *,
    payload: Mapping[str, Any],
    settlement_currency: str,
) -> SettlementEqRowV1:
    if not isinstance(payload, Mapping):
        raise TodayDeclarationGovernedBindingContractError("BALANCE_PAYLOAD_NOT_OBJECT")
    code = payload.get("code")
    if not isinstance(code, str) or code != "0":
        raise TodayDeclarationGovernedBindingContractError("BALANCE_VENUE_CODE_NOT_ZERO")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], Mapping):
        raise TodayDeclarationGovernedBindingContractError("BALANCE_DATA_NOT_SINGLE_OBJECT")
    account = data[0]
    account_utime = _require_json_string(row=account, field="uTime")
    details = account.get("details")
    if not isinstance(details, list):
        raise TodayDeclarationGovernedBindingContractError("BALANCE_DETAILS_NOT_LIST")
    matches: list[Mapping[str, Any]] = []
    for item in details:
        if not isinstance(item, Mapping):
            raise TodayDeclarationGovernedBindingContractError("BALANCE_DETAIL_ROW_NOT_OBJECT")
        ccy_raw = item.get("ccy")
        if isinstance(ccy_raw, bool) or isinstance(ccy_raw, (int, float)):
            raise TodayDeclarationGovernedBindingContractError("NUMERIC_COERCION_FORBIDDEN:ccy")
        if isinstance(ccy_raw, str) and ccy_raw == settlement_currency:
            matches.append(item)
    if len(matches) != 1:
        raise TodayDeclarationGovernedBindingContractError(
            f"MATCHING_BALANCE_ROW_COUNT_NOT_ONE:{len(matches)}"
        )
    row = matches[0]
    eq = _require_json_string(row=row, field=EQUITY_VALUE_FIELD)
    for forbidden in FORBIDDEN_EQUITY_FIELDS:
        if forbidden == EQUITY_VALUE_FIELD:
            raise TodayDeclarationGovernedBindingContractError("EQUITY_FIELD_COLLAPSED")
    lexical_decimal_scale_of_exact_equity_value_string_v1(eq)
    return SettlementEqRowV1(
        ccy=_require_json_string(row=row, field="ccy"),
        eq=eq,
        account_utime_raw=account_utime,
        row_utime_raw=_require_json_string(row=row, field="uTime"),
        matching_row_count="1",
    )


def join_fresh_acquisition_to_d4_v1(
    *,
    config: AccountConfigJoinFactsV1,
    d4_bound_account_identity: str,
    d4_settlement_currency: str,
    expected_account_mode: str = EXPECTED_ACCOUNT_MODE,
    expected_pos_mode: str = EXPECTED_POS_MODE,
) -> None:
    if config.uid != d4_bound_account_identity:
        raise TodayDeclarationGovernedBindingContractError("CONFIG_UID_D4_MISMATCH")
    if config.settle_ccy != d4_settlement_currency:
        raise TodayDeclarationGovernedBindingContractError("CONFIG_SETTLE_CCY_D4_MISMATCH")
    if config.acct_lv != expected_account_mode:
        raise TodayDeclarationGovernedBindingContractError("CONFIG_ACCTLV_MISMATCH")
    if config.pos_mode != expected_pos_mode:
        raise TodayDeclarationGovernedBindingContractError("CONFIG_POSMODE_MISMATCH")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise TodayDeclarationGovernedBindingContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise TodayDeclarationGovernedBindingContractError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise TodayDeclarationGovernedBindingContractError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise TodayDeclarationGovernedBindingContractError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise TodayDeclarationGovernedBindingContractError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise TodayDeclarationGovernedBindingContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise TodayDeclarationGovernedBindingContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise TodayDeclarationGovernedBindingContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise TodayDeclarationGovernedBindingContractError("C17_CREATED_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise TodayDeclarationGovernedBindingContractError("BN_KIND_SET_NOT_EMPTY")
    if EQUITY_UNIT != "SETTLEMENT_CURRENCY_UNITS":
        raise TodayDeclarationGovernedBindingContractError("EQUITY_UNIT_DRIFT")
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


def build_system_bound_today_candidate_v1(
    *,
    account_identity: str,
    settlement_currency: str,
    equity_value: str,
    as_of_time: str,
    venue_account_utime_raw: str,
    venue_settlement_row_utime_raw: str,
    raw_config_sha256: str,
    raw_balance_sha256: str,
    config_request_utc: str,
    balance_request_utc: str,
) -> SystemBoundTodayCandidateV1:
    _assert_standing_pins()
    if as_of_time != balance_request_utc:
        raise TodayDeclarationGovernedBindingContractError("AS_OF_TIME_NOT_BALANCE_REQUEST_UTC")
    if _ISO_Z.fullmatch(as_of_time) is None:
        raise TodayDeclarationGovernedBindingContractError("AS_OF_TIME_NOT_ISO_Z")
    if as_of_time == venue_account_utime_raw or as_of_time == venue_settlement_row_utime_raw:
        raise TodayDeclarationGovernedBindingContractError("REQUEST_UTC_COLLAPSED_INTO_VENUE_UTIME")
    if equity_value in FORBIDDEN_EQUITY_FIELDS:
        raise TodayDeclarationGovernedBindingContractError("EQUITY_VALUE_IS_FIELD_NAME")
    precision = lexical_decimal_scale_of_exact_equity_value_string_v1(equity_value)
    bound_fields = {
        "source_kind": TODAY_SOURCE_KIND,
        "source_type": TODAY_SOURCE_TYPE,
        "economic_meaning": ECONOMIC_MEANING,
        "account_identity": account_identity,
        "account_identity_binding": ACCOUNT_IDENTITY_BINDING,
        "instrument_identity": INSTRUMENT_ACCOUNT_LEVEL,
        "settlement_currency": settlement_currency,
        "settlement_currency_binding": SETTLEMENT_CURRENCY_BINDING,
        "equity_value": equity_value,
        "equity_value_field": EQUITY_VALUE_FIELD,
        "equity_unit": EQUITY_UNIT,
        "equity_precision": precision,
        "equity_precision_semantic": EQUITY_PRECISION_SEMANTIC,
        "as_of_time": as_of_time,
        "as_of_time_semantic": AS_OF_TIME_SEMANTIC,
        "validity_window_start": as_of_time,
        "validity_window_end": as_of_time,
        "ratification_status": RATIFICATION_NOT_RATIFIED,
        "venue_eq_source_authority": FALSE_TOKEN,
        "initial_stock_anchor_status": STATUS_ABSENT,
        "live_equity_stock_kind_set": KIND_SET_EMPTY,
        "venue_account_utime_raw": venue_account_utime_raw,
        "venue_settlement_row_utime_raw": venue_settlement_row_utime_raw,
        "acquisition_config_request_utc": config_request_utc,
        "acquisition_balance_request_utc": balance_request_utc,
        "raw_config_sha256": raw_config_sha256,
        "raw_balance_sha256": raw_balance_sha256,
    }
    declaration_id = derive_declaration_id_v1(bound_fields)
    payload = dict(bound_fields)
    payload["declaration_id"] = declaration_id
    payload["provenance_digest"] = semantic_candidate_digest_v1(payload)
    if payload["declaration_id"].startswith("FIXTURE"):
        raise TodayDeclarationGovernedBindingContractError("DECLARATION_ID_FIXTURE_FORBIDDEN")
    if payload["equity_unit"] == payload["settlement_currency"]:
        raise TodayDeclarationGovernedBindingContractError("EQUITY_UNIT_COLLAPSED_INTO_CURRENCY")
    if payload["equity_precision_semantic"] != EQUITY_PRECISION_SEMANTIC:
        raise TodayDeclarationGovernedBindingContractError("PRECISION_SEMANTIC_DRIFT")
    members = ratified_live_equity_stock_kind_set_v1(evaluate_today_live_equity_stock_kind_set_v1())
    if members:
        raise TodayDeclarationGovernedBindingContractError("KIND_SET_NOT_EMPTY")
    return SystemBoundTodayCandidateV1(
        declaration_id=declaration_id,
        payload=payload,
        candidate_status=CANDIDATE_PRESENT_UNRATIFIED,
        ratification_status=RATIFICATION_NOT_RATIFIED,
        initial_stock_anchor_status=STATUS_ABSENT,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        venue_eq_source_authority=FALSE_TOKEN,
        owner_ratification_required=TRUE_TOKEN,
    )


def _open_transport_v1(
    *,
    vault_file: Path | str | None,
    transport: LiveCanaryTransportV1 | None,
) -> tuple[LiveCanaryTransportV1, Any, bool]:
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise TodayDeclarationGovernedBindingContractError("HOST_MISMATCH")
    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise TodayDeclarationGovernedBindingContractError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise TodayDeclarationGovernedBindingContractError("PRODUCTIVE_WIRE_DISABLED")
    handle = None
    if productive:
        backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
            credential_class=REQUIRED_CREDENTIAL_CLASS,
        )
    if transport is None:
        raise TodayDeclarationGovernedBindingContractError("TRANSPORT_ABSENT")
    return transport, handle, productive


def _one_authorized_get_v1(
    *,
    client: LiveCanaryHttpClientV1,
    handle: Any,
    endpoint: str,
) -> AcquisitionCaptureV1:
    if endpoint not in AUTHORIZED_ENDPOINTS:
        raise TodayDeclarationGovernedBindingContractError(f"UNAUTHORIZED_GET_SURFACE:{endpoint}")
    if endpoint in FORBIDDEN_ENDPOINTS:
        raise TodayDeclarationGovernedBindingContractError("MUTATION_ENDPOINT_FORBIDDEN")
    url = f"{REUSED_REST_BASE}{endpoint}"
    parsed = urlparse(url)
    if parsed.path != endpoint or parsed.query:
        raise TodayDeclarationGovernedBindingContractError("SIGNED_REQUEST_TARGET_MISMATCH")
    if parsed.hostname != AUTHORIZED_HOST:
        raise TodayDeclarationGovernedBindingContractError("HOST_MISMATCH")
    auth_headers: dict[str, str] = {}
    try:
        if handle is not None:
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        request_utc = _utc_now_z()
        try:
            response = client.get(endpoint=endpoint, headers=auth_headers or None)
        except LiveCanaryHttpError as exc:
            raise TodayDeclarationGovernedBindingContractError(
                f"ACQUISITION_GET_FAILED:{endpoint}:{exc}"
            ) from exc
        response_utc = _utc_now_z()
        if response.method != "GET":
            raise TodayDeclarationGovernedBindingContractError("NON_GET_RESPONSE")
        if bool(response.redirect_followed):
            raise TodayDeclarationGovernedBindingContractError("REDIRECT_FOLLOWED")
        body = bytes(response.body_bytes)
        return AcquisitionCaptureV1(
            endpoint=endpoint,
            request_utc=request_utc,
            response_utc=response_utc,
            http_status=str(int(response.status_code)),
            body_bytes=body,
            sha256=_sha256_bytes(body),
        )
    finally:
        auth_headers.clear()


def _assert_get_counters_v1(*, client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 2:
        raise TodayDeclarationGovernedBindingContractError("GET_COUNT_NOT_TWO")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 2:
        raise TodayDeclarationGovernedBindingContractError("REQUEST_COUNT_NOT_TWO")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise TodayDeclarationGovernedBindingContractError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise TodayDeclarationGovernedBindingContractError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise TodayDeclarationGovernedBindingContractError("ORDER_REQUEST_DETECTED")
    if list(client.counters.endpoints_used) != list(AUTHORIZED_ENDPOINTS):
        raise TodayDeclarationGovernedBindingContractError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET", "GET"]:
        raise TodayDeclarationGovernedBindingContractError("NON_GET_METHOD_DETECTED")
    return counters


def _capture_envelope(*, capture: AcquisitionCaptureV1, layer_name: str) -> dict[str, str]:
    return {
        "layer": "RAW_PRIMARY_EVIDENCE",
        "epistemic_class": "INITIAL_STOCK_ACQUISITION_EVIDENCE",
        "reconstruction_source_authority": FALSE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "interpretation_status": "JOIN_REQUIRED_BEFORE_CANDIDATE",
        "method": "GET",
        "endpoint": capture.endpoint,
        "host": AUTHORIZED_HOST,
        "query": "",
        "request_utc": capture.request_utc,
        "response_utc": capture.response_utc,
        "http_status": capture.http_status,
        "payload_sha256": capture.sha256,
        "body_byte_len": str(len(capture.body_bytes)),
        "secrets_or_signatures_persisted": FALSE_TOKEN,
        "request_utc_equals_venue_utime_claimed": FALSE_TOKEN,
        "epoch_normalized": FALSE_TOKEN,
        "surface_name": layer_name,
    }


def execute_live_equity_stock_today_declaration_governed_binding_contract_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    evidence_root: Path,
    sealed_bs_pack: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    genesis_store_root: Path | str | None = None,
) -> TodayDeclarationGovernedBindingResultV1:
    if owner_go != OWNER_GO:
        raise TodayDeclarationGovernedBindingContractError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise TodayDeclarationGovernedBindingContractError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    if verify_manifest_sha256_v1(store_root=sealed_bs_pack) != 0:
        raise TodayDeclarationGovernedBindingContractError("BS_MANIFEST_VERIFY_FAILED")
    bs_boundary = evaluate_today_initial_stock_source_kind_boundary_v1(repo_root=repo_root)
    if bs_boundary.live_equity_stock_kind_set != KIND_SET_EMPTY:
        raise TodayDeclarationGovernedBindingContractError("BS_KIND_SET_NOT_EMPTY")
    if bs_boundary.venue_eq_source_authority != FALSE_TOKEN:
        raise TodayDeclarationGovernedBindingContractError("BS_VENUE_EQ_SOURCE_AUTHORITY_DRIFT")
    if bs_boundary.initial_stock_anchor_status != STATUS_ABSENT:
        raise TodayDeclarationGovernedBindingContractError("BS_ANCHOR_NOT_ABSENT")
    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo_root)
    )
    if genesis_root is None:
        raise TodayDeclarationGovernedBindingContractError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    opened_transport, handle, _productive = _open_transport_v1(
        vault_file=vault_file, transport=transport
    )
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=opened_transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    try:
        config_cap = _one_authorized_get_v1(
            client=client, handle=handle, endpoint=ENDPOINT_ACCOUNT_CONFIG
        )
        balance_cap = _one_authorized_get_v1(
            client=client, handle=handle, endpoint=ENDPOINT_ACCOUNT_BALANCE
        )
        _assert_get_counters_v1(client=client)
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    persist_as_of = balance_cap.request_utc
    store = Path(evidence_root) / _folder_from_as_of(persist_as_of)
    store.mkdir(parents=True, exist_ok=True)
    _persist_raw_bytes(path=store / RAW_CONFIG_BODY_FILE, body=config_cap.body_bytes)
    _persist_raw_bytes(path=store / RAW_BALANCE_BODY_FILE, body=balance_cap.body_bytes)
    _persist_json(
        path=store / RAW_CONFIG_CAPTURE_FILE,
        payload=_capture_envelope(capture=config_cap, layer_name="ACCOUNT_CONFIG"),
    )
    _persist_json(
        path=store / RAW_BALANCE_CAPTURE_FILE,
        payload=_capture_envelope(capture=balance_cap, layer_name="ACCOUNT_BALANCE"),
    )
    if config_cap.http_status != "200" or balance_cap.http_status != "200":
        raise TodayDeclarationGovernedBindingContractError("HTTP_STATUS_NOT_200")
    try:
        config_payload = parse_json_object_v1(config_cap.body_bytes)
        balance_payload = parse_json_object_v1(balance_cap.body_bytes)
    except LiveCanaryHttpError as exc:
        raise TodayDeclarationGovernedBindingContractError(
            f"ACQUISITION_RESPONSE_NOT_JSON_OBJECT:{exc}"
        ) from exc
    config_facts = extract_account_config_join_facts_v1(config_payload)
    join_fresh_acquisition_to_d4_v1(
        config=config_facts,
        d4_bound_account_identity=d4.bound_account_identity,
        d4_settlement_currency=d4.settlement_currency,
    )
    if config_facts.settle_ccy != d4.settlement_currency:
        raise TodayDeclarationGovernedBindingContractError("CONFIG_SETTLE_CCY_D4_MISMATCH")
    eq_row = extract_settlement_eq_row_v1(
        payload=balance_payload,
        settlement_currency=config_facts.settle_ccy,
    )
    if eq_row.ccy != d4.settlement_currency:
        raise TodayDeclarationGovernedBindingContractError("BALANCE_CCY_D4_MISMATCH")
    candidate = build_system_bound_today_candidate_v1(
        account_identity=d4.bound_account_identity,
        settlement_currency=d4.settlement_currency,
        equity_value=eq_row.eq,
        as_of_time=balance_cap.request_utc,
        venue_account_utime_raw=eq_row.account_utime_raw,
        venue_settlement_row_utime_raw=eq_row.row_utime_raw,
        raw_config_sha256=config_cap.sha256,
        raw_balance_sha256=balance_cap.sha256,
        config_request_utc=config_cap.request_utc,
        balance_request_utc=balance_cap.request_utc,
    )
    _persist_json(path=store / CANDIDATE_FILE, payload=candidate.payload)
    _persist_json(
        path=store / JOIN_FILE,
        payload={
            "config_uid": config_facts.uid,
            "d4_bound_account_identity": d4.bound_account_identity,
            "config_uid_d4_match": TRUE_TOKEN,
            "config_settle_ccy": config_facts.settle_ccy,
            "d4_settlement_currency": d4.settlement_currency,
            "config_settle_ccy_d4_match": TRUE_TOKEN,
            "config_acct_lv": config_facts.acct_lv,
            "expected_account_mode": EXPECTED_ACCOUNT_MODE,
            "config_pos_mode": config_facts.pos_mode,
            "expected_pos_mode": EXPECTED_POS_MODE,
            "matching_balance_row_count": eq_row.matching_row_count,
            "equity_value_field": EQUITY_VALUE_FIELD,
            "forbidden_equity_fields": ",".join(sorted(FORBIDDEN_EQUITY_FIELDS)),
            "request_utc_equals_venue_utime_claimed": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / CONTRACT_FILE,
        payload={
            "schema_class": SCHEMA_CLASS,
            "parent_today_schema_class": PARENT_TODAY_SCHEMA_CLASS,
            "contract_version": CONTRACT_VERSION,
            "source_kind": TODAY_SOURCE_KIND,
            "source_type": TODAY_SOURCE_TYPE,
            "economic_meaning": ECONOMIC_MEANING,
            "account_identity_binding": ACCOUNT_IDENTITY_BINDING,
            "settlement_currency_binding": SETTLEMENT_CURRENCY_BINDING,
            "equity_unit": EQUITY_UNIT,
            "equity_precision_semantic": EQUITY_PRECISION_SEMANTIC,
            "as_of_time_semantic": AS_OF_TIME_SEMANTIC,
            "candidate_is_not_ratification": TRUE_TOKEN,
            "candidate_is_not_anchor": TRUE_TOKEN,
            "venue_eq_source_authority": FALSE_TOKEN,
            "owner_ratification_required": TRUE_TOKEN,
            "kind_set": KIND_SET_EMPTY,
        },
    )
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": persist_as_of,
        "SEALED_BS_PACK": CANONICAL_BS_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "BS_CONTRACT_REUSED": TRUE_TOKEN,
        "BN_CONTRACT_REUSED": TRUE_TOKEN,
        "NEW_CANONICAL_DEFINITION": TRUE_TOKEN,
        "NEW_CANONICAL_SEMANTICS": TRUE_TOKEN,
        "LEGACY_SEMANTICS_RECONSTRUCTED": FALSE_TOKEN,
        "KINDS_INVENTED_THIS_GO": FALSE_TOKEN,
        "INVENTED_IDENTITIES": FALSE_TOKEN,
        "INVENTED_VALUES": FALSE_TOKEN,
        "TODAY_INITIAL_STOCK_SOURCE_KIND": TODAY_SOURCE_KIND,
        "TODAY_SOURCE_TYPE": TODAY_SOURCE_TYPE,
        "ECONOMIC_MEANING": ECONOMIC_MEANING,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "PARENT_TODAY_SCHEMA_CLASS": PARENT_TODAY_SCHEMA_CLASS,
        "ACCOUNT_IDENTITY_BINDING": ACCOUNT_IDENTITY_BINDING,
        "SETTLEMENT_CURRENCY_BINDING": SETTLEMENT_CURRENCY_BINDING,
        "EQUITY_UNIT": EQUITY_UNIT,
        "EQUITY_PRECISION_SEMANTIC": EQUITY_PRECISION_SEMANTIC,
        "AS_OF_TIME_SEMANTIC": AS_OF_TIME_SEMANTIC,
        "EQUITY_VALUE_FIELD": EQUITY_VALUE_FIELD,
        "CANDIDATE_STATUS": candidate.candidate_status,
        "RATIFICATION_STATUS": RATIFICATION_NOT_RATIFIED,
        "OWNER_RATIFICATION_REQUIRED": TRUE_TOKEN,
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
        "VENUE_GET_COUNT": "2",
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
        "CONFIG_UID_D4_MATCH": TRUE_TOKEN,
        "CONFIG_SETTLE_CCY_D4_MATCH": TRUE_TOKEN,
        "MATCHING_BALANCE_ROW_COUNT": eq_row.matching_row_count,
        "RAW_CONFIG_EVIDENCE_SHA256": config_cap.sha256,
        "RAW_BALANCE_EVIDENCE_SHA256": balance_cap.sha256,
        "VENUE_ACCOUNT_UTIME_RAW": eq_row.account_utime_raw,
        "VENUE_SETTLEMENT_ROW_UTIME_RAW": eq_row.row_utime_raw,
        "AS_OF_TIME": balance_cap.request_utc,
        "DECLARATION_ID": candidate.declaration_id,
        "GATE_A_ID": GATE_A_ID,
        "GATE_B_ID": GATE_B_ID,
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bs_pack": CANONICAL_BS_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
            "raw_epistemic_class": "INITIAL_STOCK_ACQUISITION_EVIDENCE",
            "derived_epistemic_class": "SYSTEM_BOUND_UNRATIFIED_CANDIDATE",
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "venue_eq_as_source": "FORBIDDEN",
            "checkpoint_mints_equity": "FORBIDDEN",
            "float_coercion": "FORBIDDEN",
            "totalEq_as_stock": "FORBIDDEN",
            "eqUsd_as_stock": "FORBIDDEN",
            "self_ratify": "FORBIDDEN",
            "candidate_is_not_anchor": TRUE_TOKEN,
            "candidate_is_not_ratification": TRUE_TOKEN,
            "empty_live_kind_set": KIND_SET_EMPTY,
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "venue_get_count": "2",
            "venue_post_count": "0",
            "request_utc_equals_venue_utime_claimed": FALSE_TOKEN,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    if not _SHA256_HEX.match(candidate.payload["provenance_digest"]):
        raise TodayDeclarationGovernedBindingContractError("PROVENANCE_DIGEST_NOT_SHA256")
    return TodayDeclarationGovernedBindingResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        contract_version=CONTRACT_VERSION,
        target_stock_semantic=ECONOMIC_MEANING,
        account_identity_binding=ACCOUNT_IDENTITY_BINDING,
        settlement_currency_binding=SETTLEMENT_CURRENCY_BINDING,
        equity_value=eq_row.eq,
        equity_unit=EQUITY_UNIT,
        equity_precision=candidate.payload["equity_precision"],
        equity_precision_semantic=EQUITY_PRECISION_SEMANTIC,
        as_of_time=balance_cap.request_utc,
        as_of_time_semantic=AS_OF_TIME_SEMANTIC,
        config_uid_d4_match=TRUE_TOKEN,
        config_settle_ccy_d4_match=TRUE_TOKEN,
        matching_balance_row_count=eq_row.matching_row_count,
        raw_config_evidence_sha256=config_cap.sha256,
        raw_balance_evidence_sha256=balance_cap.sha256,
        venue_account_utime_raw=eq_row.account_utime_raw,
        venue_settlement_row_utime_raw=eq_row.row_utime_raw,
        candidate_status=candidate.candidate_status,
        ratification_status=RATIFICATION_NOT_RATIFIED,
        initial_stock_anchor_status=STATUS_ABSENT,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        venue_eq_source_authority=FALSE_TOKEN,
        venue_get_count="2",
        venue_post_count="0",
        owner_ratification_required=TRUE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "CANONICAL_PACK_RELPATH",
    "CONTRACT_VERSION",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "ECONOMIC_MEANING",
    "EQUITY_PRECISION_SEMANTIC",
    "EQUITY_UNIT",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "TODAY_SOURCE_TYPE",
    "TodayDeclarationGovernedBindingContractError",
    "build_system_bound_today_candidate_v1",
    "derive_declaration_id_v1",
    "execute_live_equity_stock_today_declaration_governed_binding_contract_v1",
    "extract_account_config_join_facts_v1",
    "extract_settlement_eq_row_v1",
    "join_fresh_acquisition_to_d4_v1",
    "lexical_decimal_scale_of_exact_equity_value_string_v1",
    "semantic_candidate_digest_v1",
]
