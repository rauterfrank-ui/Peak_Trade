"""Today initial-stock KIND_SET membership V1.

Binds exactly the already defined source kind
OWNER_DECLARED_TODAY_INITIAL_EQUITY_STOCK as the sole member of
LIVE_EQUITY_STOCK_KIND_SET. Membership references Candidate ->
Ratification -> Anchor by digest. Does not rewrite BT/BU/BV packs.
Does not invent a kind. Venue eq remains non-source.
Candidate != Ratification != Anchor != KIND_SET Membership.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    EARLIEST_OPTION_D_DEPENDENCY,
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
    INPUT_PRESENT,
    LAYER_CANONICAL,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
    ROLE_EQUITY_STOCK_SOURCE,
    ROLE_RISK_CAPITAL_REDUCTION_ONLY,
    LiveEquityStockKindCandidateV1,
    evaluate_live_equity_stock_kind_membership_v1,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    ANCHOR_FILE,
    AUTHORIZED_ANCHOR_ID,
    AUTHORIZED_CANDIDATE_FILE_SHA256,
    AUTHORIZED_RATIFICATION_DIGEST,
    CANONICAL_PACK_RELPATH as CANONICAL_BV_PACK_RELPATH,
    STATUS_PRESENT,
    TodayInitialStockAnchorError,
    anchor_digest_v1,
    assert_authorized_identity_binding_v1,
    assert_authorized_today_ratification_v1,
    load_sealed_candidate_identity_v1,
    load_sealed_today_ratification_v1,
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
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BS_PACK_RELPATH,
    SOURCE_KIND_DEFINED_NOT_MEMBER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    Package1S6MappingClassificationError,
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_V1"
EXPECTED_ORIGIN_MAIN_SHA = "6ed70553db02d0fe1ca7567e02169e1fbde038a4"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_today_initial_stock_kind_set_membership_wp1/"
    "2026-09-14T212500Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-14T21:25:00Z"
SCHEMA_CLASS = "TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
OWNER_AUTHORITY_CLASS = "OWNER_GOVERNED_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP"
MEMBERSHIP_DECISION = "BIND_EXACT_DEFINED_TODAY_INITIAL_STOCK_KIND_AS_SOLE_LIVE_KIND_SET_MEMBER"
AUTHORIZED_ANCHOR_DIGEST = "2035e5ea02d049fdd0185efbee87de5331020e168e2e166e3ec547b98a4574de"
AUTHORIZED_MEMBERSHIP_ID = "GOVERNED_TODAY_INITIAL_STOCK_KIND_SET_MEMBERSHIP_5d6c32292e0cb733"
SOURCE_KIND_DEFINED_MEMBER = "DEFINED_KIND_SET_MEMBER"
MEMBERSHIP_STATUS_PRESENT = STATUS_PRESENT
MEMBERSHIP_STATUS_UNRATIFIED = "UNRATIFIED"
MEMBERSHIP_OWNER_RATIFICATION_REQUIRED_AFTER = FALSE_TOKEN
RUNNING_EQUITY_BLOCKED = "BLOCKED_D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
VENUE_EQ_RECONCILIATION_UNBOUND = "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = EARLIEST_OPTION_D_DEPENDENCY
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_OPTION_D_RUNNING_EQUITY_RECONSTRUCTION_V1"
MEMBERSHIP_FILE = "today_initial_stock_kind_set_membership_v1.json"
LINEAGE_FILE = "candidate_ratification_anchor_membership_lineage_v1.json"
KIND_IDENTITY_FILE = "exact_kind_identity_v1.json"
KIND_SET_BEFORE_AFTER_FILE = "kind_set_membership_before_after_v1.json"
EXCLUSIVITY_FILE = "kind_set_exclusivity_guard_v1.json"
SOURCE_AUTHORITY_FILE = "source_authority_separation_v1.json"
FORBIDDEN_VENUE_SOURCE_FIELDS: tuple[str, ...] = (
    "eq",
    "totalEq",
    "availEq",
    "adjEq",
    "availBal",
    "cashBal",
)
FORBIDDEN_KIND_ALIASES: frozenset[str] = frozenset(
    {
        "TODAY_INITIAL_STOCK",
        "TODAY_INITIAL_EQUITY_STOCK",
        "OWNER_DECLARED_TODAY_INITIAL_EQUITY",
        "OWNER_DECLARED_INITIAL_EQUITY_STOCK",
        "INITIAL_STOCK",
        "OPTION_D_PRIOR",
        "VENUE_EQ",
        "eq",
    }
)
REQUIRED_ANCHOR_STRING_FIELDS: tuple[str, ...] = (
    "schema_class",
    "contract_version",
    "owner_go",
    "declaration_id",
    "candidate_digest",
    "ratification_digest",
    "anchor_id",
    "anchor_digest",
    "ratification_status",
    "initial_stock_anchor_status",
    "live_equity_stock_kind_set",
    "kind_set_members",
    "membership_owner_ratification_required",
    "venue_eq_source_authority",
    "economic_meaning",
    "equity_value",
    "equity_unit",
    "settlement_currency",
    "as_of_time",
    "as_of_time_semantic",
    "source_kind",
    "source_type",
)


class TodayInitialStockKindSetMembershipError(ValueError):
    """Fail-closed today initial-stock KIND_SET membership violation."""


@dataclass(frozen=True)
class TodayInitialStockKindSetMembershipResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    declaration_id: str
    candidate_digest: str
    ratification_digest: str
    anchor_id: str
    anchor_digest: str
    membership_id: str
    membership_digest: str
    source_kind_id: str
    source_kind_status: str
    membership_status: str
    live_equity_stock_kind_set: str
    kind_set_members: str
    membership_owner_ratification_required: str
    venue_eq_source_authority: str
    venue_get_count_added: str
    venue_post_count: str
    candidate_ratification_anchor_membership_lineage_valid: str
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
        raise TodayInitialStockKindSetMembershipError(absent_reason)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TodayInitialStockKindSetMembershipError(malformed_reason) from exc
    if not isinstance(payload, dict):
        raise TodayInitialStockKindSetMembershipError(malformed_reason)
    typed: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TodayInitialStockKindSetMembershipError(malformed_reason)
        if isinstance(value, bool) or isinstance(value, (int, float)):
            raise TodayInitialStockKindSetMembershipError(f"NUMERIC_COERCION_FORBIDDEN:{key}")
        if not isinstance(value, str):
            raise TodayInitialStockKindSetMembershipError(f"{malformed_reason}:{key}")
        typed[key] = value
    return typed


def membership_digest_v1(payload: Mapping[str, str]) -> str:
    stripped = {key: value for key, value in payload.items() if key != "membership_digest"}
    return _sha256_bytes(_canonical_json(stripped).encode("utf-8"))


def _assert_lexical_equity(*, equity_value: str, equity_precision: str) -> None:
    if equity_value != AUTHORIZED_EQUITY_VALUE:
        raise TodayInitialStockKindSetMembershipError("EQUITY_VALUE_MISMATCH")
    if equity_precision != AUTHORIZED_EQUITY_PRECISION:
        raise TodayInitialStockKindSetMembershipError("EQUITY_PRECISION_MISMATCH")
    if "." not in equity_value:
        raise TodayInitialStockKindSetMembershipError("EQUITY_LEXICAL_SCALE_MISMATCH")
    whole, frac = equity_value.split(".", 1)
    if whole != "2" or not frac.isdigit() or len(frac) != int(AUTHORIZED_EQUITY_PRECISION):
        raise TodayInitialStockKindSetMembershipError("EQUITY_LEXICAL_SCALE_MISMATCH")
    if any(marker in equity_value.lower() for marker in ("e", "+", " ")):
        raise TodayInitialStockKindSetMembershipError("EQUITY_VALUE_NOT_LEXICAL_DECIMAL")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise TodayInitialStockKindSetMembershipError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise TodayInitialStockKindSetMembershipError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise TodayInitialStockKindSetMembershipError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise TodayInitialStockKindSetMembershipError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise TodayInitialStockKindSetMembershipError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise TodayInitialStockKindSetMembershipError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise TodayInitialStockKindSetMembershipError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise TodayInitialStockKindSetMembershipError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise TodayInitialStockKindSetMembershipError("C17_CREATED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise TodayInitialStockKindSetMembershipError("WIRE_SEND_PERMITTED_NOT_FALSE")
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
    bn_members = ratified_live_equity_stock_kind_set_v1(
        evaluate_today_live_equity_stock_kind_set_v1()
    )
    if bn_members:
        raise TodayInitialStockKindSetMembershipError(
            f"EXTRA_KIND_SET_MEMBER:{','.join(bn_members)}"
        )


def _assert_no_venue_source_fields(payload: Mapping[str, str]) -> None:
    for field in FORBIDDEN_VENUE_SOURCE_FIELDS:
        if field in payload:
            raise TodayInitialStockKindSetMembershipError(
                f"VENUE_FIELD_AS_SOURCE_FORBIDDEN:{field}"
            )
        for value in payload.values():
            if value == field:
                raise TodayInitialStockKindSetMembershipError(
                    f"VENUE_EQ_SOURCE_AUTHORITY_DRIFT:{field}"
                )


def assert_defined_today_kind_identity_v1(kind: str) -> str:
    if kind in FORBIDDEN_KIND_ALIASES:
        raise TodayInitialStockKindSetMembershipError("KIND_ALIAS_OR_SUBSTITUTION")
    if kind != TODAY_SOURCE_KIND:
        raise TodayInitialStockKindSetMembershipError("UNKNOWN_OR_ALIAS_STOCK_KIND")
    return kind


def assert_exclusive_today_kind_set_members_v1(members: Sequence[str] | str) -> tuple[str, ...]:
    if isinstance(members, str):
        if members in {NONE_TOKEN, KIND_SET_EMPTY, ""}:
            parsed: tuple[str, ...] = ()
        else:
            parsed = tuple(item for item in members.split(",") if item)
    else:
        parsed = tuple(members)
    extras = tuple(item for item in parsed if item != TODAY_SOURCE_KIND)
    if extras:
        raise TodayInitialStockKindSetMembershipError(f"EXTRA_KIND_SET_MEMBER:{','.join(extras)}")
    if parsed != (TODAY_SOURCE_KIND,):
        raise TodayInitialStockKindSetMembershipError("UNKNOWN_OR_ALIAS_STOCK_KIND")
    return parsed


def evaluate_authorized_today_kind_membership_v1() -> str:
    record = evaluate_live_equity_stock_kind_membership_v1(
        LiveEquityStockKindCandidateV1(
            candidate_id=TODAY_SOURCE_KIND,
            source_role=ROLE_EQUITY_STOCK_SOURCE,
            layer=LAYER_CANONICAL,
            input_status=INPUT_PRESENT,
            claimed_proof="ELIGIBILITY_EVALUATOR_ONLY",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=False,
            embedding_proven=True,
            identity_proven=True,
            time_sequence_proven=True,
            double_count_proven_safe=True,
            absolute_stock_value_present=True,
            option_d_start_capable=True,
            authority_ref=f"{AUTHORIZED_ANCHOR_ID};{TODAY_SOURCE_KIND}",
        )
    )
    if record.member != TRUE_TOKEN:
        raise TodayInitialStockKindSetMembershipError(
            f"TODAY_KIND_NOT_ELIGIBLE:{record.reason_code}"
        )
    return record.candidate_id


def load_sealed_today_anchor_v1(*, store_root: Path) -> dict[str, str]:
    typed = _load_string_object(
        path=Path(store_root) / ANCHOR_FILE,
        absent_reason="ANCHOR_ABSENT",
        malformed_reason="ANCHOR_MALFORMED",
    )
    for field in REQUIRED_ANCHOR_STRING_FIELDS:
        if field not in typed or typed[field] == "":
            raise TodayInitialStockKindSetMembershipError(f"ANCHOR_MALFORMED:MISSING:{field}")
    return typed


def assert_authorized_today_anchor_v1(anchor: Mapping[str, str]) -> str:
    if anchor["declaration_id"].startswith("FIXTURE"):
        raise TodayInitialStockKindSetMembershipError(REASON_FIXTURE_CANNOT_PROMOTE)
    recomputed = anchor_digest_v1(anchor)
    if anchor["anchor_digest"] != recomputed:
        raise TodayInitialStockKindSetMembershipError("ANCHOR_DIGEST_MISMATCH")
    if anchor["declaration_id"] != AUTHORIZED_DECLARATION_ID:
        raise TodayInitialStockKindSetMembershipError("DECLARATION_ID_MISMATCH")
    if anchor["candidate_digest"] != AUTHORIZED_PROVENANCE_DIGEST:
        raise TodayInitialStockKindSetMembershipError("CANDIDATE_DIGEST_MISMATCH")
    if anchor["ratification_digest"] != AUTHORIZED_RATIFICATION_DIGEST:
        raise TodayInitialStockKindSetMembershipError("RATIFICATION_DIGEST_MISMATCH")
    if anchor["anchor_id"] != AUTHORIZED_ANCHOR_ID:
        raise TodayInitialStockKindSetMembershipError("ANCHOR_ID_MISMATCH")
    if anchor["ratification_status"] != RATIFICATION_RATIFIED:
        raise TodayInitialStockKindSetMembershipError("RATIFICATION_NOT_RATIFIED")
    if anchor["initial_stock_anchor_status"] != STATUS_PRESENT:
        raise TodayInitialStockKindSetMembershipError("ANCHOR_NOT_PRESENT")
    if anchor["equity_value"] != AUTHORIZED_EQUITY_VALUE:
        raise TodayInitialStockKindSetMembershipError("EQUITY_VALUE_MISMATCH")
    if anchor["equity_unit"] != EQUITY_UNIT:
        raise TodayInitialStockKindSetMembershipError("EQUITY_UNIT_MISMATCH")
    if anchor["settlement_currency"] != AUTHORIZED_SETTLEMENT_CURRENCY:
        raise TodayInitialStockKindSetMembershipError("SETTLEMENT_CURRENCY_MISMATCH")
    if anchor["as_of_time"] != AUTHORIZED_AS_OF_TIME:
        raise TodayInitialStockKindSetMembershipError("AS_OF_TIME_MISMATCH")
    if anchor["as_of_time_semantic"] != AS_OF_TIME_SEMANTIC:
        raise TodayInitialStockKindSetMembershipError("AS_OF_TIME_SEMANTIC_DRIFT")
    if anchor["economic_meaning"] != ECONOMIC_MEANING:
        raise TodayInitialStockKindSetMembershipError("ECONOMIC_MEANING_MISMATCH")
    assert_defined_today_kind_identity_v1(anchor["source_kind"])
    if anchor["source_type"] != TODAY_SOURCE_TYPE:
        raise TodayInitialStockKindSetMembershipError("SOURCE_TYPE_MISMATCH")
    if anchor["live_equity_stock_kind_set"] != KIND_SET_EMPTY:
        raise TodayInitialStockKindSetMembershipError("SEALED_ANCHOR_KIND_SET_NOT_EMPTY")
    if anchor["kind_set_members"] not in {NONE_TOKEN, "", KIND_SET_EMPTY}:
        raise TodayInitialStockKindSetMembershipError("SEALED_ANCHOR_KIND_SET_NOT_EMPTY")
    if anchor["membership_owner_ratification_required"] != TRUE_TOKEN:
        raise TodayInitialStockKindSetMembershipError("SEALED_ANCHOR_MEMBERSHIP_ALREADY_BOUND")
    if anchor["venue_eq_source_authority"] != FALSE_TOKEN:
        raise TodayInitialStockKindSetMembershipError("VENUE_EQ_SOURCE_AUTHORITY_DRIFT")
    _assert_no_venue_source_fields(anchor)
    _assert_lexical_equity(
        equity_value=anchor["equity_value"],
        equity_precision=AUTHORIZED_EQUITY_PRECISION,
    )
    if recomputed != AUTHORIZED_ANCHOR_DIGEST:
        raise TodayInitialStockKindSetMembershipError("ANCHOR_SUBSTITUTION")
    return recomputed


def execute_live_equity_stock_today_initial_stock_kind_set_membership_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    repo_root: Path,
    evidence_root: Path,
    sealed_bv_pack: Path,
    sealed_bu_pack: Path,
    sealed_bt_pack: Path,
    persist_as_of: str = CANONICAL_PERSIST_AS_OF,
) -> TodayInitialStockKindSetMembershipResultV1:
    if owner_go != OWNER_GO:
        raise TodayInitialStockKindSetMembershipError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise TodayInitialStockKindSetMembershipError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    sealed_bv = Path(sealed_bv_pack)
    sealed_bu = Path(sealed_bu_pack)
    sealed_bt = Path(sealed_bt_pack)
    try:
        if verify_manifest_sha256_v1(store_root=sealed_bv) != 0:
            raise TodayInitialStockKindSetMembershipError("BV_MANIFEST_VERIFY_FAILED")
        if verify_manifest_sha256_v1(store_root=sealed_bu) != 0:
            raise TodayInitialStockKindSetMembershipError("BU_MANIFEST_VERIFY_FAILED")
        if verify_manifest_sha256_v1(store_root=sealed_bt) != 0:
            raise TodayInitialStockKindSetMembershipError("BT_MANIFEST_VERIFY_FAILED")
    except Package1S6MappingClassificationError as exc:
        raise TodayInitialStockKindSetMembershipError("MANIFEST_VERIFY_FAILED") from exc
    try:
        ratification = load_sealed_today_ratification_v1(store_root=sealed_bu)
        identity = load_sealed_candidate_identity_v1(store_root=sealed_bu)
        candidate = load_sealed_today_candidate_v1(store_root=sealed_bt)
        candidate_digest = assert_authorized_today_candidate_v1(candidate)
        ratification_digest = assert_authorized_today_ratification_v1(ratification)
        assert_authorized_identity_binding_v1(identity)
    except TodayInitialStockAnchorError as exc:
        raise TodayInitialStockKindSetMembershipError(str(exc)) from exc
    except TodayInitialStockRatificationError as exc:
        raise TodayInitialStockKindSetMembershipError(str(exc)) from exc
    anchor = load_sealed_today_anchor_v1(store_root=sealed_bv)
    anchor_digest = assert_authorized_today_anchor_v1(anchor)
    assert_defined_today_kind_identity_v1(identity["source_kind"])
    if candidate_digest != identity["candidate_digest"]:
        raise TodayInitialStockKindSetMembershipError("CANDIDATE_SUBSTITUTION")
    if candidate_digest != ratification["candidate_digest"]:
        raise TodayInitialStockKindSetMembershipError("CANDIDATE_SUBSTITUTION")
    if candidate_digest != anchor["candidate_digest"]:
        raise TodayInitialStockKindSetMembershipError("CANDIDATE_SUBSTITUTION")
    if identity["declaration_id"] != ratification["declaration_id"]:
        raise TodayInitialStockKindSetMembershipError("CANDIDATE_SUBSTITUTION")
    if identity["declaration_id"] != anchor["declaration_id"]:
        raise TodayInitialStockKindSetMembershipError("CANDIDATE_SUBSTITUTION")
    if identity["equity_value"] != ratification["equity_value"]:
        raise TodayInitialStockKindSetMembershipError("EQUITY_VALUE_MISMATCH")
    if identity["equity_value"] != anchor["equity_value"]:
        raise TodayInitialStockKindSetMembershipError("EQUITY_VALUE_MISMATCH")
    if ratification_digest != anchor["ratification_digest"]:
        raise TodayInitialStockKindSetMembershipError("RATIFICATION_DIGEST_MISMATCH")
    candidate_bytes_sha256 = _sha256_bytes((sealed_bt / CANDIDATE_FILE).read_bytes())
    if candidate_bytes_sha256 != AUTHORIZED_CANDIDATE_FILE_SHA256:
        raise TodayInitialStockKindSetMembershipError("CANDIDATE_SUBSTITUTION")
    bound_kind = evaluate_authorized_today_kind_membership_v1()
    members = assert_exclusive_today_kind_set_members_v1((bound_kind,))
    store = Path(evidence_root) / _folder_from_as_of(persist_as_of)
    if store.exists() and any(store.iterdir()):
        raise TodayInitialStockKindSetMembershipError("MEMBERSHIP_STORE_ALREADY_PRESENT")
    store.mkdir(parents=True, exist_ok=True)
    membership = {
        "schema_class": SCHEMA_CLASS,
        "contract_version": CONTRACT_VERSION,
        "owner_go": OWNER_GO,
        "owner_authority_class": OWNER_AUTHORITY_CLASS,
        "membership_decision": MEMBERSHIP_DECISION,
        "membership_id": AUTHORIZED_MEMBERSHIP_ID,
        "declaration_id": AUTHORIZED_DECLARATION_ID,
        "candidate_digest": candidate_digest,
        "candidate_file_sha256": candidate_bytes_sha256,
        "ratification_digest": ratification_digest,
        "anchor_id": AUTHORIZED_ANCHOR_ID,
        "anchor_digest": anchor_digest,
        "sealed_bt_pack": CANONICAL_BT_PACK_RELPATH,
        "sealed_bu_pack": CANONICAL_BU_PACK_RELPATH,
        "sealed_bv_pack": CANONICAL_BV_PACK_RELPATH,
        "candidate_status": CANDIDATE_PRESENT,
        "ratification_status": RATIFICATION_RATIFIED,
        "initial_stock_anchor_status": STATUS_PRESENT,
        "membership_status": MEMBERSHIP_STATUS_PRESENT,
        "source_kind": TODAY_SOURCE_KIND,
        "source_kind_status": SOURCE_KIND_DEFINED_MEMBER,
        "live_equity_stock_kind_set": TODAY_SOURCE_KIND,
        "live_equity_stock_kind_set_identity": LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        "live_equity_stock_kind_set_resolved": TRUE_TOKEN,
        "kind_set_members": TODAY_SOURCE_KIND,
        "membership_owner_ratification_required": MEMBERSHIP_OWNER_RATIFICATION_REQUIRED_AFTER,
        "venue_eq_source_authority": FALSE_TOKEN,
        "reconstruction_source_authority": FALSE_TOKEN,
        "candidate_is_not_membership": TRUE_TOKEN,
        "ratification_is_not_membership": TRUE_TOKEN,
        "anchor_is_not_kind_set_membership": TRUE_TOKEN,
        "persist_as_of": persist_as_of,
        "economic_meaning": ECONOMIC_MEANING,
        "equity_value": AUTHORIZED_EQUITY_VALUE,
        "equity_unit": EQUITY_UNIT,
        "settlement_currency": AUTHORIZED_SETTLEMENT_CURRENCY,
        "equity_precision": AUTHORIZED_EQUITY_PRECISION,
        "equity_precision_semantic": EQUITY_PRECISION_SEMANTIC,
        "as_of_time": AUTHORIZED_AS_OF_TIME,
        "as_of_time_semantic": AS_OF_TIME_SEMANTIC,
        "source_type": TODAY_SOURCE_TYPE,
        "equity_copied_without_provenance": FALSE_TOKEN,
    }
    membership["membership_digest"] = membership_digest_v1(membership)
    lineage = {
        "candidate_id": AUTHORIZED_DECLARATION_ID,
        "candidate_digest": candidate_digest,
        "ratification_digest": ratification_digest,
        "anchor_id": AUTHORIZED_ANCHOR_ID,
        "anchor_digest": anchor_digest,
        "membership_id": AUTHORIZED_MEMBERSHIP_ID,
        "membership_digest": membership["membership_digest"],
        "source_kind": TODAY_SOURCE_KIND,
        "lineage": "CANDIDATE->RATIFICATION->ANCHOR->MEMBERSHIP",
        "lineage_valid": TRUE_TOKEN,
        "sealed_bt_pack": CANONICAL_BT_PACK_RELPATH,
        "sealed_bu_pack": CANONICAL_BU_PACK_RELPATH,
        "sealed_bv_pack": CANONICAL_BV_PACK_RELPATH,
        "candidate_rewritten": FALSE_TOKEN,
        "ratification_rewritten": FALSE_TOKEN,
        "anchor_rewritten": FALSE_TOKEN,
    }
    kind_identity = {
        "source_kind": TODAY_SOURCE_KIND,
        "source_kind_status_before": SOURCE_KIND_DEFINED_NOT_MEMBER,
        "source_kind_status_after": SOURCE_KIND_DEFINED_MEMBER,
        "alias_normalization": FALSE_TOKEN,
        "kind_invented": FALSE_TOKEN,
        "anchor_id": AUTHORIZED_ANCHOR_ID,
        "membership_id": AUTHORIZED_MEMBERSHIP_ID,
    }
    before_after = {
        "live_equity_stock_kind_set_before": KIND_SET_EMPTY,
        "kind_set_members_before": NONE_TOKEN,
        "membership_status_before": MEMBERSHIP_STATUS_UNRATIFIED,
        "membership_owner_ratification_required_before": TRUE_TOKEN,
        "live_equity_stock_kind_set_after": TODAY_SOURCE_KIND,
        "kind_set_members_after": TODAY_SOURCE_KIND,
        "membership_status_after": MEMBERSHIP_STATUS_PRESENT,
        "membership_owner_ratification_required_after": MEMBERSHIP_OWNER_RATIFICATION_REQUIRED_AFTER,
        "additional_members": NONE_TOKEN,
    }
    exclusivity = {
        "authorized_member": TODAY_SOURCE_KIND,
        "bound_members": ",".join(members),
        "bn_evaluator_members": NONE_TOKEN,
        "extra_member_forbidden": TRUE_TOKEN,
        "alias_forbidden": TRUE_TOKEN,
        "historical_unknown_not_member": TRUE_TOKEN,
        "venue_eq_not_member": TRUE_TOKEN,
    }
    source_authority = {
        "venue_eq_role": "RECONCILIATION_TARGET_ONLY",
        "venue_eq_source_authority": FALSE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "checkpoint_mints_equity": FALSE_TOKEN,
        "candidate_role": "INITIAL_STOCK_ACQUISITION_EVIDENCE",
        "ratification_role": "OWNER_RATIFIED_TODAY_INITIAL_STOCK",
        "anchor_role": "OPTION_D_PRIOR_STOCK_IDENTITY",
        "membership_role": "SOLE_LIVE_EQUITY_STOCK_KIND_SET_MEMBER",
        "reconstruction_engine_created": FALSE_TOKEN,
        "kind_set_membership_bound": TRUE_TOKEN,
        "available_for_sizing_separate": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
    }
    _persist_json(path=store / MEMBERSHIP_FILE, payload=membership)
    _persist_json(path=store / LINEAGE_FILE, payload=lineage)
    _persist_json(path=store / KIND_IDENTITY_FILE, payload=kind_identity)
    _persist_json(path=store / KIND_SET_BEFORE_AFTER_FILE, payload=before_after)
    _persist_json(path=store / EXCLUSIVITY_FILE, payload=exclusivity)
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
        "SEALED_BV_PACK": CANONICAL_BV_PACK_RELPATH,
        "SEALED_BS_PACK": CANONICAL_BS_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "BT_CONTRACT_REUSED": TRUE_TOKEN,
        "BU_CONTRACT_REUSED": TRUE_TOKEN,
        "BV_CONTRACT_REUSED": TRUE_TOKEN,
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
        "MEMBERSHIP_DECISION": MEMBERSHIP_DECISION,
        "MEMBERSHIP_ID": AUTHORIZED_MEMBERSHIP_ID,
        "MEMBERSHIP_DIGEST": membership["membership_digest"],
        "ANCHOR_ID": AUTHORIZED_ANCHOR_ID,
        "ANCHOR_DIGEST": anchor_digest,
        "DECLARATION_ID": AUTHORIZED_DECLARATION_ID,
        "CANDIDATE_DIGEST": candidate_digest,
        "RATIFICATION_DIGEST": ratification_digest,
        "CANDIDATE_STATUS": CANDIDATE_PRESENT,
        "RATIFICATION_STATUS": RATIFICATION_RATIFIED,
        "INITIAL_STOCK_ANCHOR_STATUS": STATUS_PRESENT,
        "MEMBERSHIP_STATUS": MEMBERSHIP_STATUS_PRESENT,
        "SOURCE_KIND_ID": TODAY_SOURCE_KIND,
        "SOURCE_KIND_STATUS": SOURCE_KIND_DEFINED_MEMBER,
        "LIVE_EQUITY_STOCK_KIND_SET": TODAY_SOURCE_KIND,
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        "LIVE_EQUITY_STOCK_KIND_SET_RESOLVED": TRUE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_MEMBERS": TODAY_SOURCE_KIND,
        "MEMBERSHIP_OWNER_RATIFICATION_REQUIRED": MEMBERSHIP_OWNER_RATIFICATION_REQUIRED_AFTER,
        "ANCHOR_IS_NOT_KIND_SET_MEMBERSHIP": TRUE_TOKEN,
        "CANDIDATE_RATIFICATION_ANCHOR_MEMBERSHIP_LINEAGE_VALID": TRUE_TOKEN,
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
        "CANDIDATE_SUBSTITUTION_GUARD": "EXACT_AUTHORIZED_RATIFIED_ANCHOR_IDENTITY_ONLY",
        "BT_CANDIDATE_REWRITTEN": FALSE_TOKEN,
        "BU_RATIFICATION_REWRITTEN": FALSE_TOKEN,
        "BV_ANCHOR_REWRITTEN": FALSE_TOKEN,
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bt_pack": CANONICAL_BT_PACK_RELPATH,
            "parent_bu_pack": CANONICAL_BU_PACK_RELPATH,
            "parent_bv_pack": CANONICAL_BV_PACK_RELPATH,
            "parent_bs_pack": CANONICAL_BS_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
            "raw_epistemic_class": "OWNER_RATIFIED_TODAY_INITIAL_STOCK_ANCHOR",
            "derived_epistemic_class": "LIVE_EQUITY_STOCK_KIND_SET_SINGLE_MEMBER",
            "reconstruction_source_authority": FALSE_TOKEN,
            "candidate_digest": candidate_digest,
            "ratification_digest": ratification_digest,
            "anchor_digest": anchor_digest,
            "membership_digest": membership["membership_digest"],
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "venue_eq_as_source": "FORBIDDEN",
            "checkpoint_mints_equity": "FORBIDDEN",
            "candidate_rewrite": "FORBIDDEN",
            "ratification_rewrite": "FORBIDDEN",
            "anchor_rewrite": "FORBIDDEN",
            "candidate_substitution": "FORBIDDEN",
            "ratification_substitution": "FORBIDDEN",
            "anchor_substitution": "FORBIDDEN",
            "latest_candidate": "FORBIDDEN",
            "fixture_promote": "FORBIDDEN",
            "unknown_or_extra_stock_kind": "FORBIDDEN",
            "kind_alias_or_substitution": "FORBIDDEN",
            "extra_kind_set_member": "FORBIDDEN",
            "equity_float_coercion": "FORBIDDEN",
            "self_membership_without_owner_go": "FORBIDDEN",
            "fresh_get": "FORBIDDEN",
            "venue_post": "FORBIDDEN",
            "live_equity_stock_kind_set": TODAY_SOURCE_KIND,
            "kind_set_members": TODAY_SOURCE_KIND,
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
        raise TodayInitialStockKindSetMembershipError("BT_CANDIDATE_REWRITTEN")
    if (sealed_bu / RATIFICATION_FILE).read_bytes() != (
        repo / CANONICAL_BU_PACK_RELPATH / RATIFICATION_FILE
    ).read_bytes() and sealed_bu.resolve() == (repo / CANONICAL_BU_PACK_RELPATH).resolve():
        raise TodayInitialStockKindSetMembershipError("BU_RATIFICATION_REWRITTEN")
    if (sealed_bv / ANCHOR_FILE).read_bytes() != (
        repo / CANONICAL_BV_PACK_RELPATH / ANCHOR_FILE
    ).read_bytes() and sealed_bv.resolve() == (repo / CANONICAL_BV_PACK_RELPATH).resolve():
        raise TodayInitialStockKindSetMembershipError("BV_ANCHOR_REWRITTEN")
    return TodayInitialStockKindSetMembershipResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        declaration_id=AUTHORIZED_DECLARATION_ID,
        candidate_digest=candidate_digest,
        ratification_digest=ratification_digest,
        anchor_id=AUTHORIZED_ANCHOR_ID,
        anchor_digest=anchor_digest,
        membership_id=AUTHORIZED_MEMBERSHIP_ID,
        membership_digest=membership["membership_digest"],
        source_kind_id=TODAY_SOURCE_KIND,
        source_kind_status=SOURCE_KIND_DEFINED_MEMBER,
        membership_status=MEMBERSHIP_STATUS_PRESENT,
        live_equity_stock_kind_set=TODAY_SOURCE_KIND,
        kind_set_members=TODAY_SOURCE_KIND,
        membership_owner_ratification_required=MEMBERSHIP_OWNER_RATIFICATION_REQUIRED_AFTER,
        venue_eq_source_authority=FALSE_TOKEN,
        venue_get_count_added="0",
        venue_post_count="0",
        candidate_ratification_anchor_membership_lineage_valid=TRUE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "AUTHORIZED_MEMBERSHIP_ID",
    "CANONICAL_PACK_RELPATH",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "MEMBERSHIP_STATUS_PRESENT",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "SOURCE_KIND_DEFINED_MEMBER",
    "TodayInitialStockKindSetMembershipError",
    "assert_defined_today_kind_identity_v1",
    "assert_exclusive_today_kind_set_members_v1",
    "execute_live_equity_stock_today_initial_stock_kind_set_membership_v1",
    "membership_digest_v1",
]
