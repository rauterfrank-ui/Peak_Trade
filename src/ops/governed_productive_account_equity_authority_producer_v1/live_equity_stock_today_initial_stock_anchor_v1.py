"""Today initial-stock Anchor V1.

Binds exactly the already Owner-ratified sealed candidate as the
OPTION_D Today Initial Stock Anchor. Does not re-acquire equity, does
not rewrite BT/BU evidence, does not mutate KIND_SET, and does not
promote venue eq to reconstruction source authority.
Candidate != Ratification != Anchor. AUTHORITY_EFFECT=NONE.

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
    TODAY_SOURCE_TYPE,
    semantic_candidate_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_ratification_v1 import (
    AUTHORIZED_AS_OF_TIME,
    AUTHORIZED_DECLARATION_ID,
    AUTHORIZED_EQUITY_PRECISION,
    AUTHORIZED_EQUITY_VALUE,
    AUTHORIZED_PROVENANCE_DIGEST,
    AUTHORIZED_SETTLEMENT_CURRENCY,
    CANONICAL_PACK_RELPATH as CANONICAL_BU_PACK_RELPATH,
    CANDIDATE_PRESENT,
    IDENTITY_FILE,
    RATIFICATION_FILE,
    RATIFICATION_RATIFIED,
    REASON_FIXTURE_CANNOT_PROMOTE,
    TODAY_SOURCE_KIND,
    TodayInitialStockRatificationError,
    assert_authorized_today_candidate_v1,
    load_sealed_today_candidate_v1,
    ratification_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BS_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    Package1S6MappingClassificationError,
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_ANCHOR_V1"
EXPECTED_ORIGIN_MAIN_SHA = "85451214c94d345b5209ed7dedf0139edd22d4a2"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_today_initial_stock_anchor_wp1/2026-09-14T205500Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-14T20:55:00Z"
SCHEMA_CLASS = "TODAY_INITIAL_STOCK_ANCHOR_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
OWNER_AUTHORITY_CLASS = "OWNER_GOVERNED_TODAY_INITIAL_STOCK_ANCHOR"
ANCHOR_DECISION = "BIND_EXACT_RATIFIED_CANDIDATE_AS_OPTION_D_TODAY_INITIAL_STOCK_ANCHOR"
AUTHORIZED_RATIFICATION_DIGEST = "dcc7cd67b7e57052f42ba30252ca1c01121df3ab7795f5173449bdcd4f5685bb"
AUTHORIZED_CANDIDATE_FILE_SHA256 = (
    "b4216f1343b608135f363aafd0ab4e3aaea80b4185b57cce01d03154ec970a1c"
)
AUTHORIZED_ANCHOR_ID = "GOVERNED_TODAY_INITIAL_STOCK_ANCHOR_5d6c32292e0cb733"
STATUS_PRESENT = "PRESENT"
RUNNING_EQUITY_BLOCKED = "BLOCKED_KIND_SET_MEMBERSHIP_UNRATIFIED"
VENUE_EQ_RECONCILIATION_UNBOUND = "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_REQUIRED"
NEXT_OWNER_GO_REQUIRED = (
    "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_V1"
)
MEMBERSHIP_OWNER_RATIFICATION_REQUIRED = TRUE_TOKEN
ANCHOR_FILE = "today_initial_stock_anchor_v1.json"
LINEAGE_FILE = "candidate_ratification_anchor_lineage_v1.json"
STOCK_BINDING_FILE = "exact_stock_semantic_binding_v1.json"
SOURCE_AUTHORITY_FILE = "source_authority_separation_v1.json"
FORBIDDEN_VENUE_SOURCE_FIELDS: tuple[str, ...] = (
    "eq",
    "totalEq",
    "availEq",
    "adjEq",
    "availBal",
    "cashBal",
)
REQUIRED_RATIFICATION_STRING_FIELDS: tuple[str, ...] = (
    "schema_class",
    "contract_version",
    "owner_go",
    "declaration_id",
    "candidate_digest",
    "ratification_digest",
    "ratification_status",
    "initial_stock_anchor_status",
    "live_equity_stock_kind_set",
    "venue_eq_source_authority",
    "economic_meaning",
    "equity_value",
    "equity_unit",
    "settlement_currency",
    "as_of_time",
    "as_of_time_semantic",
)
REQUIRED_IDENTITY_STRING_FIELDS: tuple[str, ...] = (
    "declaration_id",
    "candidate_digest",
    "candidate_file_sha256",
    "equity_value",
    "equity_unit",
    "settlement_currency",
    "equity_precision",
    "equity_precision_semantic",
    "as_of_time",
    "as_of_time_semantic",
    "economic_meaning",
    "source_kind",
    "source_type",
)


class TodayInitialStockAnchorError(ValueError):
    """Fail-closed today initial-stock anchor violation."""


@dataclass(frozen=True)
class TodayInitialStockAnchorResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    declaration_id: str
    candidate_digest: str
    ratification_digest: str
    anchor_id: str
    anchor_digest: str
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


def _load_string_object(*, path: Path, absent_reason: str, malformed_reason: str) -> dict[str, str]:
    if not path.is_file():
        raise TodayInitialStockAnchorError(absent_reason)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TodayInitialStockAnchorError(malformed_reason) from exc
    if not isinstance(payload, dict):
        raise TodayInitialStockAnchorError(malformed_reason)
    typed: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TodayInitialStockAnchorError(malformed_reason)
        if isinstance(value, bool) or isinstance(value, (int, float)):
            raise TodayInitialStockAnchorError(f"NUMERIC_COERCION_FORBIDDEN:{key}")
        if not isinstance(value, str):
            raise TodayInitialStockAnchorError(f"{malformed_reason}:{key}")
        typed[key] = value
    return typed


def anchor_digest_v1(payload: Mapping[str, str]) -> str:
    stripped = {key: value for key, value in payload.items() if key != "anchor_digest"}
    return _sha256_bytes(_canonical_json(stripped).encode("utf-8"))


def _assert_lexical_equity(*, equity_value: str, equity_precision: str) -> None:
    if equity_value != AUTHORIZED_EQUITY_VALUE:
        raise TodayInitialStockAnchorError("EQUITY_VALUE_MISMATCH")
    if equity_precision != AUTHORIZED_EQUITY_PRECISION:
        raise TodayInitialStockAnchorError("EQUITY_PRECISION_MISMATCH")
    if "." not in equity_value:
        raise TodayInitialStockAnchorError("EQUITY_LEXICAL_SCALE_MISMATCH")
    whole, frac = equity_value.split(".", 1)
    if whole != "2" or not frac.isdigit() or len(frac) != int(AUTHORIZED_EQUITY_PRECISION):
        raise TodayInitialStockAnchorError("EQUITY_LEXICAL_SCALE_MISMATCH")
    if any(marker in equity_value.lower() for marker in ("e", "+", " ")):
        raise TodayInitialStockAnchorError("EQUITY_VALUE_NOT_LEXICAL_DECIMAL")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise TodayInitialStockAnchorError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise TodayInitialStockAnchorError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise TodayInitialStockAnchorError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise TodayInitialStockAnchorError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise TodayInitialStockAnchorError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise TodayInitialStockAnchorError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise TodayInitialStockAnchorError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise TodayInitialStockAnchorError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise TodayInitialStockAnchorError("C17_CREATED_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise TodayInitialStockAnchorError("BN_KIND_SET_NOT_EMPTY")
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
        raise TodayInitialStockAnchorError("KIND_SET_NOT_EMPTY")


def _assert_no_venue_source_fields(payload: Mapping[str, str]) -> None:
    for field in FORBIDDEN_VENUE_SOURCE_FIELDS:
        if field in payload:
            raise TodayInitialStockAnchorError(f"VENUE_FIELD_AS_SOURCE_FORBIDDEN:{field}")
        for value in payload.values():
            if value == field:
                raise TodayInitialStockAnchorError(f"VENUE_EQ_SOURCE_AUTHORITY_DRIFT:{field}")


def _assert_no_extra_kind_semantics(payload: Mapping[str, str]) -> None:
    kind_set = payload.get("live_equity_stock_kind_set", payload.get("kind_set", KIND_SET_EMPTY))
    if kind_set != KIND_SET_EMPTY:
        raise TodayInitialStockAnchorError("UNKNOWN_OR_EXTRA_STOCK_KIND_SEMANTIC")
    members = payload.get("kind_set_members", payload.get("KIND_SET_MEMBERS", NONE_TOKEN))
    if members not in {NONE_TOKEN, "", KIND_SET_EMPTY}:
        raise TodayInitialStockAnchorError("UNKNOWN_OR_EXTRA_STOCK_KIND_SEMANTIC")


def load_sealed_today_ratification_v1(*, store_root: Path) -> dict[str, str]:
    typed = _load_string_object(
        path=Path(store_root) / RATIFICATION_FILE,
        absent_reason="RATIFICATION_ABSENT",
        malformed_reason="RATIFICATION_MALFORMED",
    )
    for field in REQUIRED_RATIFICATION_STRING_FIELDS:
        if field not in typed or typed[field] == "":
            raise TodayInitialStockAnchorError(f"RATIFICATION_MALFORMED:MISSING:{field}")
    return typed


def load_sealed_candidate_identity_v1(*, store_root: Path) -> dict[str, str]:
    typed = _load_string_object(
        path=Path(store_root) / IDENTITY_FILE,
        absent_reason="RATIFICATION_IDENTITY_ABSENT",
        malformed_reason="RATIFICATION_IDENTITY_MALFORMED",
    )
    for field in REQUIRED_IDENTITY_STRING_FIELDS:
        if field not in typed or typed[field] == "":
            raise TodayInitialStockAnchorError(f"RATIFICATION_IDENTITY_MALFORMED:MISSING:{field}")
    return typed


def assert_authorized_today_ratification_v1(ratification: Mapping[str, str]) -> str:
    if ratification["declaration_id"].startswith("FIXTURE"):
        raise TodayInitialStockAnchorError(REASON_FIXTURE_CANNOT_PROMOTE)
    recomputed = ratification_digest_v1(ratification)
    if ratification["ratification_digest"] != recomputed:
        raise TodayInitialStockAnchorError("RATIFICATION_DIGEST_MISMATCH")
    if "ratification_id" in ratification and ratification["ratification_id"] != recomputed:
        raise TodayInitialStockAnchorError("RATIFICATION_ID_MISMATCH")
    if ratification["declaration_id"] != AUTHORIZED_DECLARATION_ID:
        raise TodayInitialStockAnchorError("DECLARATION_ID_MISMATCH")
    if ratification["candidate_digest"] != AUTHORIZED_PROVENANCE_DIGEST:
        raise TodayInitialStockAnchorError("CANDIDATE_DIGEST_MISMATCH")
    if ratification["ratification_status"] != RATIFICATION_RATIFIED:
        raise TodayInitialStockAnchorError("RATIFICATION_NOT_RATIFIED")
    if ratification["equity_value"] != AUTHORIZED_EQUITY_VALUE:
        raise TodayInitialStockAnchorError("EQUITY_VALUE_MISMATCH")
    if ratification["equity_unit"] != EQUITY_UNIT:
        raise TodayInitialStockAnchorError("EQUITY_UNIT_MISMATCH")
    if ratification["settlement_currency"] != AUTHORIZED_SETTLEMENT_CURRENCY:
        raise TodayInitialStockAnchorError("SETTLEMENT_CURRENCY_MISMATCH")
    if ratification["as_of_time"] != AUTHORIZED_AS_OF_TIME:
        raise TodayInitialStockAnchorError("AS_OF_TIME_MISMATCH")
    if ratification["as_of_time_semantic"] != AS_OF_TIME_SEMANTIC:
        raise TodayInitialStockAnchorError("AS_OF_TIME_SEMANTIC_DRIFT")
    if ratification["economic_meaning"] != ECONOMIC_MEANING:
        raise TodayInitialStockAnchorError("ECONOMIC_MEANING_MISMATCH")
    if ratification["initial_stock_anchor_status"] != STATUS_ABSENT:
        raise TodayInitialStockAnchorError("SEALED_RATIFICATION_ANCHOR_NOT_ABSENT")
    if ratification["live_equity_stock_kind_set"] != KIND_SET_EMPTY:
        raise TodayInitialStockAnchorError("UNKNOWN_OR_EXTRA_STOCK_KIND_SEMANTIC")
    if ratification["venue_eq_source_authority"] != FALSE_TOKEN:
        raise TodayInitialStockAnchorError("VENUE_EQ_SOURCE_AUTHORITY_DRIFT")
    if ratification.get("reconstruction_source_authority", FALSE_TOKEN) != FALSE_TOKEN:
        raise TodayInitialStockAnchorError("RECONSTRUCTION_SOURCE_AUTHORITY_DRIFT")
    if ratification["equity_unit"] == ratification["settlement_currency"]:
        raise TodayInitialStockAnchorError("EQUITY_UNIT_COLLAPSED_INTO_CURRENCY")
    _assert_no_venue_source_fields(ratification)
    _assert_no_extra_kind_semantics(ratification)
    _assert_lexical_equity(
        equity_value=ratification["equity_value"],
        equity_precision=AUTHORIZED_EQUITY_PRECISION,
    )
    if recomputed != AUTHORIZED_RATIFICATION_DIGEST:
        raise TodayInitialStockAnchorError("RATIFICATION_SUBSTITUTION")
    return recomputed


def assert_authorized_identity_binding_v1(identity: Mapping[str, str]) -> None:
    if identity["declaration_id"] != AUTHORIZED_DECLARATION_ID:
        raise TodayInitialStockAnchorError("DECLARATION_ID_MISMATCH")
    if identity["candidate_digest"] != AUTHORIZED_PROVENANCE_DIGEST:
        raise TodayInitialStockAnchorError("CANDIDATE_DIGEST_MISMATCH")
    if identity["candidate_file_sha256"] != AUTHORIZED_CANDIDATE_FILE_SHA256:
        raise TodayInitialStockAnchorError("CANDIDATE_FILE_SHA256_MISMATCH")
    if identity["equity_value"] != AUTHORIZED_EQUITY_VALUE:
        raise TodayInitialStockAnchorError("EQUITY_VALUE_MISMATCH")
    if identity["equity_unit"] != EQUITY_UNIT:
        raise TodayInitialStockAnchorError("EQUITY_UNIT_MISMATCH")
    if identity["settlement_currency"] != AUTHORIZED_SETTLEMENT_CURRENCY:
        raise TodayInitialStockAnchorError("SETTLEMENT_CURRENCY_MISMATCH")
    if identity["equity_precision"] != AUTHORIZED_EQUITY_PRECISION:
        raise TodayInitialStockAnchorError("EQUITY_PRECISION_MISMATCH")
    if identity["equity_precision_semantic"] != EQUITY_PRECISION_SEMANTIC:
        raise TodayInitialStockAnchorError("EQUITY_PRECISION_SEMANTIC_DRIFT")
    if identity["as_of_time"] != AUTHORIZED_AS_OF_TIME:
        raise TodayInitialStockAnchorError("AS_OF_TIME_MISMATCH")
    if identity["as_of_time_semantic"] != AS_OF_TIME_SEMANTIC:
        raise TodayInitialStockAnchorError("AS_OF_TIME_SEMANTIC_DRIFT")
    if identity["economic_meaning"] != ECONOMIC_MEANING:
        raise TodayInitialStockAnchorError("ECONOMIC_MEANING_MISMATCH")
    if identity["source_kind"] != TODAY_SOURCE_KIND:
        raise TodayInitialStockAnchorError("SOURCE_KIND_MISMATCH")
    if identity["source_type"] != TODAY_SOURCE_TYPE:
        raise TodayInitialStockAnchorError("SOURCE_TYPE_MISMATCH")
    _assert_lexical_equity(
        equity_value=identity["equity_value"],
        equity_precision=identity["equity_precision"],
    )
    _assert_no_venue_source_fields(identity)
    _assert_no_extra_kind_semantics(identity)


def execute_live_equity_stock_today_initial_stock_anchor_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    evidence_root: Path,
    sealed_bu_pack: Path,
    sealed_bt_pack: Path,
    persist_as_of: str = CANONICAL_PERSIST_AS_OF,
) -> TodayInitialStockAnchorResultV1:
    if owner_go != OWNER_GO:
        raise TodayInitialStockAnchorError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise TodayInitialStockAnchorError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    sealed_bu = Path(sealed_bu_pack)
    sealed_bt = Path(sealed_bt_pack)
    try:
        if verify_manifest_sha256_v1(store_root=sealed_bu) != 0:
            raise TodayInitialStockAnchorError("BU_MANIFEST_VERIFY_FAILED")
        if verify_manifest_sha256_v1(store_root=sealed_bt) != 0:
            raise TodayInitialStockAnchorError("BT_MANIFEST_VERIFY_FAILED")
    except Package1S6MappingClassificationError as exc:
        raise TodayInitialStockAnchorError("MANIFEST_VERIFY_FAILED") from exc
    ratification = load_sealed_today_ratification_v1(store_root=sealed_bu)
    identity = load_sealed_candidate_identity_v1(store_root=sealed_bu)
    try:
        candidate = load_sealed_today_candidate_v1(store_root=sealed_bt)
        candidate_digest = assert_authorized_today_candidate_v1(candidate)
    except TodayInitialStockRatificationError as exc:
        raise TodayInitialStockAnchorError(str(exc)) from exc
    ratification_digest = assert_authorized_today_ratification_v1(ratification)
    assert_authorized_identity_binding_v1(identity)
    if candidate_digest != identity["candidate_digest"]:
        raise TodayInitialStockAnchorError("CANDIDATE_SUBSTITUTION")
    if candidate_digest != ratification["candidate_digest"]:
        raise TodayInitialStockAnchorError("CANDIDATE_SUBSTITUTION")
    if identity["declaration_id"] != ratification["declaration_id"]:
        raise TodayInitialStockAnchorError("CANDIDATE_SUBSTITUTION")
    if identity["equity_value"] != ratification["equity_value"]:
        raise TodayInitialStockAnchorError("EQUITY_VALUE_MISMATCH")
    candidate_bytes_sha256 = _sha256_bytes((sealed_bt / CANDIDATE_FILE).read_bytes())
    if candidate_bytes_sha256 != AUTHORIZED_CANDIDATE_FILE_SHA256:
        raise TodayInitialStockAnchorError("CANDIDATE_SUBSTITUTION")
    store = Path(evidence_root) / _folder_from_as_of(persist_as_of)
    if store.exists() and any(store.iterdir()):
        raise TodayInitialStockAnchorError("ANCHOR_STORE_ALREADY_PRESENT")
    store.mkdir(parents=True, exist_ok=True)
    anchor = {
        "schema_class": SCHEMA_CLASS,
        "contract_version": CONTRACT_VERSION,
        "owner_go": OWNER_GO,
        "owner_authority_class": OWNER_AUTHORITY_CLASS,
        "anchor_decision": ANCHOR_DECISION,
        "anchor_id": AUTHORIZED_ANCHOR_ID,
        "declaration_id": AUTHORIZED_DECLARATION_ID,
        "candidate_digest": candidate_digest,
        "candidate_file_sha256": candidate_bytes_sha256,
        "ratification_digest": ratification_digest,
        "sealed_bt_pack": CANONICAL_BT_PACK_RELPATH,
        "sealed_bu_pack": CANONICAL_BU_PACK_RELPATH,
        "candidate_status": CANDIDATE_PRESENT,
        "ratification_status": RATIFICATION_RATIFIED,
        "initial_stock_anchor_status": STATUS_PRESENT,
        "live_equity_stock_kind_set": KIND_SET_EMPTY,
        "kind_set_members": NONE_TOKEN,
        "membership_owner_ratification_required": MEMBERSHIP_OWNER_RATIFICATION_REQUIRED,
        "venue_eq_source_authority": FALSE_TOKEN,
        "reconstruction_source_authority": FALSE_TOKEN,
        "reconstruction_prior_bound": TRUE_TOKEN,
        "candidate_is_not_anchor": TRUE_TOKEN,
        "ratification_is_not_anchor": TRUE_TOKEN,
        "anchor_is_not_kind_set_membership": TRUE_TOKEN,
        "persist_as_of": persist_as_of,
        "economic_meaning": ratification["economic_meaning"],
        "equity_value": ratification["equity_value"],
        "equity_unit": ratification["equity_unit"],
        "settlement_currency": ratification["settlement_currency"],
        "equity_precision": identity["equity_precision"],
        "equity_precision_semantic": identity["equity_precision_semantic"],
        "as_of_time": ratification["as_of_time"],
        "as_of_time_semantic": ratification["as_of_time_semantic"],
        "source_kind": identity["source_kind"],
        "source_type": identity["source_type"],
        "equity_copied_without_provenance": FALSE_TOKEN,
    }
    anchor["anchor_digest"] = anchor_digest_v1(anchor)
    lineage = {
        "candidate_id": AUTHORIZED_DECLARATION_ID,
        "candidate_digest": candidate_digest,
        "ratification_digest": ratification_digest,
        "anchor_id": AUTHORIZED_ANCHOR_ID,
        "anchor_digest": anchor["anchor_digest"],
        "lineage": "CANDIDATE->RATIFICATION->ANCHOR",
        "lineage_valid": TRUE_TOKEN,
        "sealed_bt_pack": CANONICAL_BT_PACK_RELPATH,
        "sealed_bu_pack": CANONICAL_BU_PACK_RELPATH,
        "candidate_rewritten": FALSE_TOKEN,
        "ratification_rewritten": FALSE_TOKEN,
    }
    stock_binding = {
        "anchor_id": AUTHORIZED_ANCHOR_ID,
        "declaration_id": AUTHORIZED_DECLARATION_ID,
        "candidate_digest": candidate_digest,
        "ratification_digest": ratification_digest,
        "target_stock_semantic": ECONOMIC_MEANING,
        "equity_value_exact_string": AUTHORIZED_EQUITY_VALUE,
        "equity_unit": EQUITY_UNIT,
        "settlement_currency": AUTHORIZED_SETTLEMENT_CURRENCY,
        "equity_lexical_scale": AUTHORIZED_EQUITY_PRECISION,
        "equity_precision_semantic": EQUITY_PRECISION_SEMANTIC,
        "as_of_time": AUTHORIZED_AS_OF_TIME,
        "as_of_time_semantic": AS_OF_TIME_SEMANTIC,
        "source_kind": TODAY_SOURCE_KIND,
        "float_used": FALSE_TOKEN,
        "value_authority": "SEALED_OWNER_RATIFICATION_IDENTITY",
    }
    source_authority = {
        "venue_eq_role": "RECONCILIATION_TARGET_ONLY",
        "venue_eq_source_authority": FALSE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "checkpoint_mints_equity": FALSE_TOKEN,
        "candidate_role": "INITIAL_STOCK_ACQUISITION_EVIDENCE",
        "ratification_role": "OWNER_RATIFIED_TODAY_INITIAL_STOCK",
        "anchor_role": "OPTION_D_PRIOR_STOCK_IDENTITY",
        "reconstruction_engine_created": FALSE_TOKEN,
        "kind_set_membership_bound": FALSE_TOKEN,
        "available_for_sizing_separate": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
    }
    _persist_json(path=store / ANCHOR_FILE, payload=anchor)
    _persist_json(path=store / LINEAGE_FILE, payload=lineage)
    _persist_json(path=store / STOCK_BINDING_FILE, payload=stock_binding)
    _persist_json(path=store / SOURCE_AUTHORITY_FILE, payload=source_authority)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": persist_as_of,
        "SEALED_BT_PACK": CANONICAL_BT_PACK_RELPATH,
        "SEALED_BU_PACK": CANONICAL_BU_PACK_RELPATH,
        "SEALED_BS_PACK": CANONICAL_BS_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "BT_CONTRACT_REUSED": TRUE_TOKEN,
        "BU_CONTRACT_REUSED": TRUE_TOKEN,
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
        "ANCHOR_DECISION": ANCHOR_DECISION,
        "ANCHOR_ID": AUTHORIZED_ANCHOR_ID,
        "DECLARATION_ID": AUTHORIZED_DECLARATION_ID,
        "CANDIDATE_DIGEST": candidate_digest,
        "RATIFICATION_DIGEST": ratification_digest,
        "ANCHOR_DIGEST": anchor["anchor_digest"],
        "CANDIDATE_STATUS": CANDIDATE_PRESENT,
        "RATIFICATION_STATUS": RATIFICATION_RATIFIED,
        "INITIAL_STOCK_ANCHOR_STATUS": STATUS_PRESENT,
        "LIVE_EQUITY_STOCK_KIND_SET": KIND_SET_EMPTY,
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_MEMBERS": NONE_TOKEN,
        "MEMBERSHIP_OWNER_RATIFICATION_REQUIRED": MEMBERSHIP_OWNER_RATIFICATION_REQUIRED,
        "ANCHOR_IS_NOT_KIND_SET_MEMBERSHIP": TRUE_TOKEN,
        "CANDIDATE_RATIFICATION_ANCHOR_LINEAGE_VALID": TRUE_TOKEN,
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
        "TARGET_STOCK_SEMANTIC": ECONOMIC_MEANING,
        "EQUITY_VALUE": AUTHORIZED_EQUITY_VALUE,
        "EQUITY_UNIT": EQUITY_UNIT,
        "SETTLEMENT_CURRENCY": AUTHORIZED_SETTLEMENT_CURRENCY,
        "EQUITY_LEXICAL_SCALE": AUTHORIZED_EQUITY_PRECISION,
        "AS_OF_TIME": AUTHORIZED_AS_OF_TIME,
        "AS_OF_TIME_SEMANTIC": AS_OF_TIME_SEMANTIC,
        "GATE_A_ID": GATE_A_ID,
        "GATE_B_ID": GATE_B_ID,
        "CANDIDATE_SUBSTITUTION_GUARD": "EXACT_AUTHORIZED_RATIFIED_IDENTITY_ONLY",
        "BT_CANDIDATE_REWRITTEN": FALSE_TOKEN,
        "BU_RATIFICATION_REWRITTEN": FALSE_TOKEN,
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bt_pack": CANONICAL_BT_PACK_RELPATH,
            "parent_bu_pack": CANONICAL_BU_PACK_RELPATH,
            "parent_bs_pack": CANONICAL_BS_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
            "raw_epistemic_class": "OWNER_RATIFIED_TODAY_INITIAL_STOCK",
            "derived_epistemic_class": "OPTION_D_TODAY_INITIAL_STOCK_ANCHOR",
            "reconstruction_source_authority": FALSE_TOKEN,
            "candidate_digest": candidate_digest,
            "ratification_digest": ratification_digest,
            "anchor_digest": anchor["anchor_digest"],
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "venue_eq_as_source": "FORBIDDEN",
            "checkpoint_mints_equity": "FORBIDDEN",
            "candidate_rewrite": "FORBIDDEN",
            "ratification_rewrite": "FORBIDDEN",
            "candidate_substitution": "FORBIDDEN",
            "ratification_substitution": "FORBIDDEN",
            "latest_candidate": "FORBIDDEN",
            "fixture_promote": "FORBIDDEN",
            "kind_set_mutation": "FORBIDDEN",
            "unknown_or_extra_stock_kind": "FORBIDDEN",
            "equity_float_coercion": "FORBIDDEN",
            "self_anchor_without_owner_go": "FORBIDDEN",
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
    repo = Path(repo_root)
    if (sealed_bt / CANDIDATE_FILE).read_bytes() != (
        repo / CANONICAL_BT_PACK_RELPATH / CANDIDATE_FILE
    ).read_bytes() and sealed_bt.resolve() == (repo / CANONICAL_BT_PACK_RELPATH).resolve():
        raise TodayInitialStockAnchorError("BT_CANDIDATE_REWRITTEN")
    if (sealed_bu / RATIFICATION_FILE).read_bytes() != (
        repo / CANONICAL_BU_PACK_RELPATH / RATIFICATION_FILE
    ).read_bytes() and sealed_bu.resolve() == (repo / CANONICAL_BU_PACK_RELPATH).resolve():
        raise TodayInitialStockAnchorError("BU_RATIFICATION_REWRITTEN")
    return TodayInitialStockAnchorResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        declaration_id=AUTHORIZED_DECLARATION_ID,
        candidate_digest=candidate_digest,
        ratification_digest=ratification_digest,
        anchor_id=AUTHORIZED_ANCHOR_ID,
        anchor_digest=anchor["anchor_digest"],
        candidate_status=CANDIDATE_PRESENT,
        ratification_status=RATIFICATION_RATIFIED,
        initial_stock_anchor_status=STATUS_PRESENT,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        venue_eq_source_authority=FALSE_TOKEN,
        venue_get_count_added="0",
        venue_post_count="0",
        owner_authority_bound=OWNER_AUTHORITY_CLASS,
        candidate_substitution_guard="EXACT_AUTHORIZED_RATIFIED_IDENTITY_ONLY",
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "AUTHORIZED_ANCHOR_ID",
    "AUTHORIZED_RATIFICATION_DIGEST",
    "CANONICAL_PACK_RELPATH",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "STATUS_PRESENT",
    "TodayInitialStockAnchorError",
    "anchor_digest_v1",
    "assert_authorized_today_ratification_v1",
    "execute_live_equity_stock_today_initial_stock_anchor_v1",
    "load_sealed_today_ratification_v1",
]
