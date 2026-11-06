"""NEW_CANONICAL_DEFINITION of checkpoint-bound EQUITY_STOCK_VALUE_V1.

Typed fail-closed contract that binds an already-derived stock value to a
governed checkpoint. The checkpoint attests; it does not mint equity.
Does not reconstruct historical F12/F13/U05/F16/F17/F18. Does not promote
venue eq to source. Empty KIND_SET remains EMPTY_FAIL_CLOSED. Does not GET.
Does not POST. Does not execute GATE_A or GATE_B. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    RATIFIED_SOURCE_KIND_SET,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    FALSE_TOKEN,
    KIND_SET_EMPTY,
    NONE_TOKEN,
    TRUE_TOKEN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
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
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    CHECKPOINT_KIND,
    EQUITY_MINT_STATUS_NOT_MINTED,
    OBSERVATION_VS_AUTHORITY_CLASS,
    RUNNING_EQUITY_VALUE_STATE_ABSENT,
    EquityStockCheckpointContractV1,
    assert_checkpoint_cannot_mint_equity_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CURRENTLY_DECISION_CAPABLE,
    EARLIEST_REMAINING_D6_BLOCKER as HISTORICAL_D6_BLOCKER,
    GATE_A_ID,
    GATE_B_ID,
    KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY as HISTORICAL_KIND_SET_BLOCKED_BY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BN_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BN_LIVE_BLOCKER,
    LIVE_EQUITY_STOCK_KIND_SET,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
    NEXT_OWNER_GO_REQUIRED as BN_NEXT_OWNER_GO,
    ROLE_NON_SOURCE,
    ROLE_RECONCILIATION_TARGET_ONLY,
    evaluate_today_live_equity_stock_kind_set_v1,
    ratified_live_equity_stock_kind_set_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT_V1"
EXPECTED_ORIGIN_MAIN_SHA = "1cd2d28828d7b818d7c075c91675ff935eb35926"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_checkpoint_stock_value_contract_wp1/"
    "2026-09-14T120000Z"
)
CLAIMS_FILE = "claims.json"
SCHEMA_CLASS = "EQUITY_STOCK_VALUE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
BINDING_CLASS = "CHECKPOINT_ATTESTS_EXISTING_STOCK_VALUE"
DERIVATION_OPTION_D_PRIOR_PLUS_STREAM = "OPTION_D_PRIOR_STOCK_PLUS_CLASSIFIED_EVENT_STREAM"
DERIVATION_VERSION = "v1"
EQUITY_UNIT_SETTLEMENT = "SETTLEMENT_CURRENCY_UNITS"
VALIDATION_VALID = "VALID"
VALIDATION_REJECTED = "REJECTED"
STATUS_ABSENT = "ABSENT"
STATUS_NON_SOURCE_NO_BOUND_STOCK = "NON_SOURCE_NO_BOUND_STOCK"
STATUS_FLOW_NOT_STOCK = "FLOW_NOT_STOCK"
STATUS_DETERMINISTIC_FAIL_CLOSED = "DETERMINISTIC_FAIL_CLOSED"
DOUBLE_COUNT_GUARD = "STOCK_AND_FLOW_MAY_NOT_BOTH_COUNT"
EMBEDDING_RULE = "UNPROVEN_EMBEDDING_OR_LIABILITY_FAIL_CLOSED"
EMBEDDING_EXPLICIT_PROVEN = "EXPLICIT_PROVEN"
LIABILITY_EXPLICIT_PROVEN = "EXPLICIT_PROVEN"
COMPONENT_PRIOR_GOVERNED_STOCK = "PRIOR_GOVERNED_STOCK"
COMPONENT_CLASSIFIED_EVENT_STREAM = "CLASSIFIED_EVENT_STREAM"
COMPONENT_VENUE_EQ = "VENUE_EQ"
COMPONENT_AVAILABLE_CAPITAL = "AVAILABLE_CAPITAL"
COMPONENT_PLACEMENT_CAPACITY = "PLACEMENT_CAPACITY"
COMPONENT_P01 = "P01_RISK_CAPITAL"
COMPONENT_UNCLASSIFIED_FLOW = "UNCLASSIFIED_FLOW"
COMPONENT_FLOW = "EQUITY_FLOW"
FORBIDDEN_INCLUDED_STOCK_COMPONENTS: frozenset[str] = frozenset(
    {
        COMPONENT_CLASSIFIED_EVENT_STREAM,
        COMPONENT_VENUE_EQ,
        COMPONENT_AVAILABLE_CAPITAL,
        COMPONENT_PLACEMENT_CAPACITY,
        COMPONENT_P01,
        COMPONENT_UNCLASSIFIED_FLOW,
        COMPONENT_FLOW,
        "eq",
        "DELTA",
        "CHECKPOINT_MINT",
    }
)
REQUIRED_EXCLUDED_COMPONENTS: frozenset[str] = frozenset(
    {
        COMPONENT_VENUE_EQ,
        COMPONENT_AVAILABLE_CAPITAL,
        COMPONENT_PLACEMENT_CAPACITY,
        COMPONENT_P01,
        COMPONENT_UNCLASSIFIED_FLOW,
        COMPONENT_FLOW,
    }
)
ALLOWED_SOURCE_PROVENANCE: frozenset[str] = frozenset({DERIVATION_OPTION_D_PRIOR_PLUS_STREAM})
FORBIDDEN_SOURCE_PROVENANCE: frozenset[str] = frozenset(
    {
        "VENUE_EQ",
        "eq",
        "CHECKPOINT",
        "CHECKPOINT_MINT",
        "FLOW",
        "DELTA",
        "AVAILABLE_CAPITAL",
        "PLACEMENT_CAPACITY",
        "P01",
        "P01_RISK_CAPITAL",
        "LEGACY_RELABEL",
        "UNKNOWN",
        "UNCLASSIFIED",
        "UNPROVEN",
        "MISSING",
        NONE_TOKEN,
        STATUS_ABSENT,
    }
)
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "BOOTSTRAP_STOCK_PROVENANCE_ABSENT"
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE_V1"
AUTHORITATIVE_DERIVATION_DEFINED = TRUE_TOKEN
CHECKPOINT_MINTS_EQUITY = FALSE_TOKEN
VENUE_EQ_SOURCE_AUTHORITY = FALSE_TOKEN
INITIAL_STOCK_ANCHOR_STATUS = STATUS_ABSENT

REQUIRED_FIELDS: tuple[str, ...] = (
    "stock_value_id",
    "account_identity",
    "settlement_currency",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "as_of_time",
    "sequence_identity",
    "checkpoint_id",
    "checkpoint_ref",
    "source_provenance",
    "derivation_method",
    "derivation_version",
    "included_components",
    "excluded_components",
    "embedding_status",
    "liability_status",
    "event_stream_boundary",
    "replay_boundary",
    "prior_checkpoint_id",
    "semantic_digest",
    "input_digest",
    "validation_status",
    "reason_code",
)
SCALAR_INPUT_FIELDS: tuple[str, ...] = (
    "stock_value_id",
    "account_identity",
    "settlement_currency",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "as_of_time",
    "sequence_identity",
    "checkpoint_id",
    "checkpoint_ref",
    "source_provenance",
    "derivation_method",
    "derivation_version",
    "embedding_status",
    "liability_status",
    "event_stream_boundary",
    "replay_boundary",
    "prior_checkpoint_id",
    "semantic_digest",
    "input_digest",
)

REASON_CLAIMED_CHECKPOINT_MINT = "CLAIMED_CHECKPOINT_MINT_FORBIDDEN"
REASON_CLAIMED_VENUE_EQ_SOURCE = "CLAIMED_VENUE_EQ_SOURCE_FORBIDDEN"
REASON_CLAIMED_FLOW_AS_STOCK = "CLAIMED_FLOW_AS_STOCK_FORBIDDEN"
REASON_CLAIMED_AVAILABLE_CAPITAL = "CLAIMED_AVAILABLE_CAPITAL_FORBIDDEN"
REASON_CLAIMED_PLACEMENT_CAPACITY = "CLAIMED_PLACEMENT_CAPACITY_FORBIDDEN"
REASON_CLAIMED_P01_AS_STOCK = "CLAIMED_P01_AS_STOCK_FORBIDDEN"
REASON_MISSING_FIELD = "MISSING_FIELD"
REASON_MALFORMED_FIELD = "MALFORMED_FIELD"
REASON_CONTRADICTORY_FIELD = "CONTRADICTORY_FIELD"
REASON_ACCOUNT_SCOPE_MISMATCH = "ACCOUNT_SCOPE_MISMATCH"
REASON_CURRENCY_SCOPE_MISMATCH = "CURRENCY_SCOPE_MISMATCH"
REASON_SEQUENCE_TIME_AMBIGUOUS = "SEQUENCE_TIME_AMBIGUOUS"
REASON_SOURCE_PROVENANCE_MISSING = "SOURCE_PROVENANCE_MISSING"
REASON_SOURCE_PROVENANCE_MALFORMED = "SOURCE_PROVENANCE_MALFORMED"
REASON_SOURCE_PROVENANCE_CONTRADICTORY = "SOURCE_PROVENANCE_CONTRADICTORY"
REASON_DOUBLE_COUNT_STOCK_AND_FLOW = "DOUBLE_COUNT_STOCK_AND_FLOW"
REASON_EMBEDDING_UNRESOLVED = "EMBEDDING_UNRESOLVED"
REASON_LIABILITY_UNRESOLVED = "LIABILITY_UNRESOLVED"
REASON_PRIOR_CHECKPOINT_REQUIRED_MISSING = "PRIOR_CHECKPOINT_REQUIRED_MISSING"
REASON_INITIAL_STOCK_ANCHOR_ABSENT = "INITIAL_STOCK_ANCHOR_ABSENT"
REASON_REPLAY_NONDETERMINISTIC = "REPLAY_NONDETERMINISTIC"
REASON_CHECKPOINT_CANNOT_MINT = "CHECKPOINT_CANNOT_MINT_EQUITY"
REASON_KIND_MEMBERSHIP_UNRATIFIED = "KIND_MEMBERSHIP_UNRATIFIED"
REASON_VALID = "VALID_EQUITY_STOCK_VALUE"

REASON_PRECEDENCE: tuple[str, ...] = (
    REASON_CLAIMED_CHECKPOINT_MINT,
    REASON_CLAIMED_VENUE_EQ_SOURCE,
    REASON_CLAIMED_FLOW_AS_STOCK,
    REASON_CLAIMED_AVAILABLE_CAPITAL,
    REASON_CLAIMED_PLACEMENT_CAPACITY,
    REASON_CLAIMED_P01_AS_STOCK,
    REASON_MISSING_FIELD,
    REASON_MALFORMED_FIELD,
    REASON_CONTRADICTORY_FIELD,
    REASON_ACCOUNT_SCOPE_MISMATCH,
    REASON_CURRENCY_SCOPE_MISMATCH,
    REASON_SEQUENCE_TIME_AMBIGUOUS,
    REASON_SOURCE_PROVENANCE_MISSING,
    REASON_SOURCE_PROVENANCE_MALFORMED,
    REASON_SOURCE_PROVENANCE_CONTRADICTORY,
    REASON_DOUBLE_COUNT_STOCK_AND_FLOW,
    REASON_EMBEDDING_UNRESOLVED,
    REASON_LIABILITY_UNRESOLVED,
    REASON_PRIOR_CHECKPOINT_REQUIRED_MISSING,
    REASON_INITIAL_STOCK_ANCHOR_ABSENT,
    REASON_REPLAY_NONDETERMINISTIC,
    REASON_CHECKPOINT_CANNOT_MINT,
    REASON_KIND_MEMBERSHIP_UNRATIFIED,
    REASON_VALID,
)

ALLOWED_CLAIMED_PROOFS: frozenset[str] = frozenset(
    {
        "NEW_CANONICAL_DEFINITION_STOCK_VALUE_CONTRACT",
        "TODAY_DERIVATION_REJECTED_FAIL_CLOSED",
        "FIXTURE_VALID_STOCK_VALUE_ONLY",
        "CHECKPOINT_ATTEST_EXISTING_STOCK",
    }
)

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_DECIMAL = re.compile(r"^-?\d+(?:\.\d+)?$")
_PRECISION = re.compile(r"^(?:0|[1-9]\d*)$")
_UNKNOWN_TOKENS: frozenset[str] = frozenset(
    {
        "UNKNOWN",
        "UNCLASSIFIED",
        "UNPROVEN",
        "MISSING",
        "DEFAULT",
        NONE_TOKEN,
        STATUS_ABSENT,
        "",
    }
)
_AMBIGUOUS_SEQUENCE_TOKENS: frozenset[str] = frozenset(
    {
        "UNKNOWN",
        "UNCLASSIFIED",
        "AMBIGUOUS",
        "UNORDERED",
        NONE_TOKEN,
        STATUS_ABSENT,
        "",
    }
)


class EquityStockCheckpointStockValueContractError(ValueError):
    """Fail-closed checkpoint stock-value contract violation."""


@dataclass(frozen=True)
class EquityStockValueRecordV1:
    stock_value_id: str
    account_identity: str
    settlement_currency: str
    equity_value: str
    equity_unit: str
    equity_precision: str
    as_of_time: str
    sequence_identity: str
    checkpoint_id: str
    checkpoint_ref: str
    source_provenance: str
    derivation_method: str
    derivation_version: str
    included_components: tuple[str, ...]
    excluded_components: tuple[str, ...]
    embedding_status: str
    liability_status: str
    event_stream_boundary: str
    replay_boundary: str
    prior_checkpoint_id: str
    semantic_digest: str
    input_digest: str
    validation_status: str
    reason_code: str
    reason_precedence_index: str
    failures: tuple[str, ...]


@dataclass(frozen=True)
class EquityStockCheckpointBindingV1:
    stock_value_id: str
    checkpoint_id: str
    checkpoint_ref: str
    binding_class: str
    checkpoint_mints_equity: str
    account_identity: str
    settlement_currency: str
    binding_digest: str
    validation_status: str
    reason_code: str


@dataclass(frozen=True)
class AuthoritativeDerivationBoundaryV1:
    derivation_method: str
    derivation_version: str
    prior_stock_anchor_status: str
    prior_checkpoint_status: str
    event_stream_boundary_status: str
    replay_determinism_status: str
    double_count_guards: str
    embedding_rules: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    live_equity_stock_kind_set: str
    live_equity_stock_kind_set_resolved: str
    new_stock_kind_candidate: str
    membership_owner_ratification_required: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str


@dataclass(frozen=True)
class EquityStockCheckpointStockValueContractResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    stock_value_contract_defined: str
    authoritative_derivation_defined: str
    initial_stock_anchor_status: str
    prior_checkpoint_status: str
    event_stream_boundary_status: str
    replay_determinism_status: str
    live_equity_stock_kind_set: str
    live_equity_stock_kind_set_resolved: str
    new_stock_kind_candidate: str
    membership_owner_ratification_required: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str
    venue_get_count: str
    venue_post_count: str
    gate_a_executed: str
    gate_b_executed: str
    checkpoint_mints_equity: str
    venue_eq_source_authority: str
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
        raise EquityStockCheckpointStockValueContractError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise EquityStockCheckpointStockValueContractError(f"{field}_DRIFT:{actual}")


def _sha256_text(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise EquityStockCheckpointStockValueContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise EquityStockCheckpointStockValueContractError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise EquityStockCheckpointStockValueContractError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise EquityStockCheckpointStockValueContractError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise EquityStockCheckpointStockValueContractError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise EquityStockCheckpointStockValueContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise EquityStockCheckpointStockValueContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise EquityStockCheckpointStockValueContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise EquityStockCheckpointStockValueContractError("BN_KIND_SET_NOT_EMPTY")
    if BN_NEXT_OWNER_GO != OWNER_GO:
        raise EquityStockCheckpointStockValueContractError("BN_NEXT_OWNER_GO_DRIFT")
    if BN_LIVE_BLOCKER != (
        "NO_ELIGIBLE_TODAY_LIVE_EQUITY_STOCK_SOURCE_KIND_AFTER_NEW_CANONICAL_DEFINITION"
    ):
        raise EquityStockCheckpointStockValueContractError("BN_LIVE_BLOCKER_DRIFT")
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


def reject_claimed_stock_value_authority_mutation_v1(
    *,
    claimed_proof: str,
    stock_value_id: str,
) -> None:
    forbidden = {
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "EXECUTE_GATE_B",
        "VENUE_GET",
        "VENUE_POST",
        "KIND_SET_RESOLVED_TRUE",
        "D6_FULLY_CLOSED",
        "D7_AUTHORIZED_TRUE",
        "MS2_AUTHORIZED_TRUE",
        "INVENT_LIVE_SOURCE_KIND",
        "RECONSTRUCT_HISTORICAL_UNKNOWN",
        "PROMOTE_EQ_TO_SOURCE",
        "PROMOTE_U04_TO_EQUITY_STOCK",
        "PROMOTE_P01_TO_EQUITY_STOCK",
        "CHECKPOINT_MINT_EQUITY",
        "BOOTSTRAP_FROM_VENUE_EQ",
        "RELABEL_LEGACY_AS_STOCK",
        "RESTORE_LEGACY_EQUITY_LOGIC",
        "NORMALIZE_UNKNOWN_TO_INCLUDE",
        "NORMALIZE_UNKNOWN_TO_EXCLUDE",
        "PATH_C_UNKNOWN_CLOSEOUT",
    }
    if claimed_proof in forbidden:
        raise EquityStockCheckpointStockValueContractError(
            f"STOCK_VALUE_CANNOT_{claimed_proof}:{stock_value_id}"
        )
    if claimed_proof not in ALLOWED_CLAIMED_PROOFS:
        raise EquityStockCheckpointStockValueContractError(
            f"STOCK_VALUE_PROOF_UNKNOWN:{claimed_proof}:{stock_value_id}"
        )


def reason_precedence_index_v1(reason_code: str) -> int:
    try:
        return REASON_PRECEDENCE.index(reason_code)
    except ValueError as exc:
        raise EquityStockCheckpointStockValueContractError(
            f"REASON_CODE_NOT_IN_PRECEDENCE:{reason_code}"
        ) from exc


def _field_as_str(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, str):
        return None
    return raw


def _split_components(raw: Any) -> tuple[str, ...] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        if raw == "":
            return ()
        parts = tuple(item for item in raw.split(",") if item != "")
        if any(item.strip() != item for item in parts):
            return None
        return parts
    if isinstance(raw, (list, tuple)):
        if any(not isinstance(item, str) or item.strip() != item or item == "" for item in raw):
            return None
        return tuple(raw)
    return None


def _digest_inputs(
    *,
    fields: Mapping[str, str],
    included: tuple[str, ...],
    excluded: tuple[str, ...],
) -> dict[str, str]:
    return {
        "stock_value_id": fields.get("stock_value_id", ""),
        "account_identity": fields.get("account_identity", ""),
        "settlement_currency": fields.get("settlement_currency", ""),
        "equity_value": fields.get("equity_value", ""),
        "equity_unit": fields.get("equity_unit", ""),
        "equity_precision": fields.get("equity_precision", ""),
        "as_of_time": fields.get("as_of_time", ""),
        "sequence_identity": fields.get("sequence_identity", ""),
        "checkpoint_id": fields.get("checkpoint_id", ""),
        "checkpoint_ref": fields.get("checkpoint_ref", ""),
        "source_provenance": fields.get("source_provenance", ""),
        "derivation_method": fields.get("derivation_method", ""),
        "derivation_version": fields.get("derivation_version", ""),
        "included_components": ",".join(included),
        "excluded_components": ",".join(excluded),
        "embedding_status": fields.get("embedding_status", ""),
        "liability_status": fields.get("liability_status", ""),
        "event_stream_boundary": fields.get("event_stream_boundary", ""),
        "replay_boundary": fields.get("replay_boundary", ""),
        "prior_checkpoint_id": fields.get("prior_checkpoint_id", ""),
    }


def compute_stock_value_input_digest_v1(payload: Mapping[str, Any]) -> str:
    fields = {field: _field_as_str(payload.get(field)) or "" for field in SCALAR_INPUT_FIELDS}
    included = _split_components(payload.get("included_components")) or ()
    excluded = _split_components(payload.get("excluded_components")) or ()
    return _sha256_text(_digest_inputs(fields=fields, included=included, excluded=excluded))


def compute_stock_value_semantic_digest_v1(payload: Mapping[str, Any]) -> str:
    fields = {field: _field_as_str(payload.get(field)) or "" for field in SCALAR_INPUT_FIELDS}
    included = _split_components(payload.get("included_components")) or ()
    excluded = _split_components(payload.get("excluded_components")) or ()
    canonical = _digest_inputs(fields=fields, included=included, excluded=excluded)
    canonical["input_digest"] = _sha256_text(canonical)
    return _sha256_text(canonical)


def _evaluate_equity_stock_value_once_v1(
    payload: Mapping[str, Any],
    *,
    expected_account_identity: str | None,
    expected_settlement_currency: str | None,
    claimed_proof: str,
) -> EquityStockValueRecordV1:
    _assert_standing_pins()
    stock_value_id = _field_as_str(payload.get("stock_value_id")) or "UNSET_STOCK_VALUE_ID"
    reject_claimed_stock_value_authority_mutation_v1(
        claimed_proof=claimed_proof
        if claimed_proof in ALLOWED_CLAIMED_PROOFS
        else "FIXTURE_VALID_STOCK_VALUE_ONLY",
        stock_value_id=stock_value_id,
    )
    reasons: list[str] = []
    failures: list[str] = []
    fields: dict[str, str] = {}
    for field in SCALAR_INPUT_FIELDS:
        raw = payload.get(field)
        text = _field_as_str(raw)
        if field not in payload or raw is None:
            reasons.append(REASON_MISSING_FIELD)
            failures.append(f"MISSING:{field}")
            fields[field] = ""
            continue
        if text is None:
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append(f"MALFORMED:{field}")
            fields[field] = ""
            continue
        if text.strip() != text or text == "":
            reasons.append(REASON_MISSING_FIELD)
            failures.append(f"MISSING:{field}")
            fields[field] = text
            continue
        fields[field] = text

    included = _split_components(payload.get("included_components"))
    excluded = _split_components(payload.get("excluded_components"))
    if "included_components" not in payload or payload.get("included_components") is None:
        reasons.append(REASON_MISSING_FIELD)
        failures.append("MISSING:included_components")
        included = ()
    elif included is None:
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:included_components")
        included = ()
    if "excluded_components" not in payload or payload.get("excluded_components") is None:
        reasons.append(REASON_MISSING_FIELD)
        failures.append("MISSING:excluded_components")
        excluded = ()
    elif excluded is None:
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:excluded_components")
        excluded = ()
    included_set = set(included)
    excluded_set = set(excluded)
    if included_set & excluded_set:
        reasons.append(REASON_CONTRADICTORY_FIELD)
        failures.append("INCLUDED_EXCLUDED_OVERLAP")

    source = fields.get("source_provenance", "")
    method = fields.get("derivation_method", "")
    if source in FORBIDDEN_SOURCE_PROVENANCE or method in FORBIDDEN_SOURCE_PROVENANCE:
        if source in {"VENUE_EQ", "eq"} or method in {"VENUE_EQ", "eq"}:
            reasons.append(REASON_CLAIMED_VENUE_EQ_SOURCE)
        elif source in {"FLOW", "DELTA"} or method in {"FLOW", "DELTA"}:
            reasons.append(REASON_CLAIMED_FLOW_AS_STOCK)
        elif source == "PLACEMENT_CAPACITY" or method == "PLACEMENT_CAPACITY":
            reasons.append(REASON_CLAIMED_PLACEMENT_CAPACITY)
        elif source == "AVAILABLE_CAPITAL" or method == "AVAILABLE_CAPITAL":
            reasons.append(REASON_CLAIMED_AVAILABLE_CAPITAL)
        elif source in {"P01", "P01_RISK_CAPITAL"} or method in {"P01", "P01_RISK_CAPITAL"}:
            reasons.append(REASON_CLAIMED_P01_AS_STOCK)
        elif source in {"CHECKPOINT", "CHECKPOINT_MINT"} or method in {
            "CHECKPOINT",
            "CHECKPOINT_MINT",
        }:
            reasons.append(REASON_CLAIMED_CHECKPOINT_MINT)
        elif source in _UNKNOWN_TOKENS:
            reasons.append(REASON_SOURCE_PROVENANCE_MISSING)
        else:
            reasons.append(REASON_SOURCE_PROVENANCE_MALFORMED)
    elif source != "" and source not in ALLOWED_SOURCE_PROVENANCE:
        reasons.append(REASON_SOURCE_PROVENANCE_MALFORMED)
        failures.append("SOURCE_PROVENANCE_NOT_AUTHORITATIVE")
    if method and method != DERIVATION_OPTION_D_PRIOR_PLUS_STREAM:
        if method not in FORBIDDEN_SOURCE_PROVENANCE:
            reasons.append(REASON_SOURCE_PROVENANCE_CONTRADICTORY)
            failures.append("DERIVATION_METHOD_NOT_OPTION_D")
    if (
        source
        and method
        and source != method
        and source in ALLOWED_SOURCE_PROVENANCE
        and method == DERIVATION_OPTION_D_PRIOR_PLUS_STREAM
    ):
        reasons.append(REASON_SOURCE_PROVENANCE_CONTRADICTORY)
        failures.append("SOURCE_PROVENANCE_METHOD_MISMATCH")
    if fields.get("derivation_version") and fields["derivation_version"] != DERIVATION_VERSION:
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:derivation_version")

    if included_set & FORBIDDEN_INCLUDED_STOCK_COMPONENTS:
        if included_set & {COMPONENT_VENUE_EQ, "eq"}:
            reasons.append(REASON_CLAIMED_VENUE_EQ_SOURCE)
        if included_set & {COMPONENT_FLOW, COMPONENT_CLASSIFIED_EVENT_STREAM, "DELTA"}:
            reasons.append(REASON_CLAIMED_FLOW_AS_STOCK)
            reasons.append(REASON_DOUBLE_COUNT_STOCK_AND_FLOW)
        if COMPONENT_AVAILABLE_CAPITAL in included_set:
            reasons.append(REASON_CLAIMED_AVAILABLE_CAPITAL)
        if COMPONENT_PLACEMENT_CAPACITY in included_set:
            reasons.append(REASON_CLAIMED_PLACEMENT_CAPACITY)
        if COMPONENT_P01 in included_set:
            reasons.append(REASON_CLAIMED_P01_AS_STOCK)
        if "CHECKPOINT_MINT" in included_set:
            reasons.append(REASON_CLAIMED_CHECKPOINT_MINT)
    if included and COMPONENT_PRIOR_GOVERNED_STOCK not in included_set:
        reasons.append(REASON_INITIAL_STOCK_ANCHOR_ABSENT)
        failures.append("INCLUDED_MISSING_PRIOR_GOVERNED_STOCK")
    if excluded and not REQUIRED_EXCLUDED_COMPONENTS.issubset(excluded_set):
        reasons.append(REASON_DOUBLE_COUNT_STOCK_AND_FLOW)
        failures.append("REQUIRED_EXCLUSIONS_INCOMPLETE")

    as_of = fields.get("as_of_time", "")
    sequence = fields.get("sequence_identity", "")
    if as_of and not _ISO_Z.match(as_of):
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:as_of_time")
    if sequence in _AMBIGUOUS_SEQUENCE_TOKENS:
        reasons.append(REASON_SEQUENCE_TIME_AMBIGUOUS)
        failures.append("SEQUENCE_IDENTITY_AMBIGUOUS")
    if as_of in _UNKNOWN_TOKENS:
        reasons.append(REASON_SEQUENCE_TIME_AMBIGUOUS)
        failures.append("AS_OF_TIME_AMBIGUOUS")
    replay_boundary = fields.get("replay_boundary", "")
    event_boundary = fields.get("event_stream_boundary", "")
    if replay_boundary in _UNKNOWN_TOKENS:
        reasons.append(REASON_SEQUENCE_TIME_AMBIGUOUS)
        failures.append("REPLAY_BOUNDARY_AMBIGUOUS")
    if event_boundary in _UNKNOWN_TOKENS:
        reasons.append(REASON_SEQUENCE_TIME_AMBIGUOUS)
        failures.append("EVENT_STREAM_BOUNDARY_AMBIGUOUS")
    if (
        as_of
        and replay_boundary
        and _ISO_Z.match(as_of)
        and _ISO_Z.match(replay_boundary)
        and as_of != replay_boundary
    ):
        reasons.append(REASON_SEQUENCE_TIME_AMBIGUOUS)
        failures.append("AS_OF_REPLAY_BOUNDARY_MISMATCH")
    if sequence and event_boundary and sequence == event_boundary:
        reasons.append(REASON_DOUBLE_COUNT_STOCK_AND_FLOW)
        failures.append("SEQUENCE_EQUALS_EVENT_STREAM_BOUNDARY")

    unit = fields.get("equity_unit", "")
    precision = fields.get("equity_precision", "")
    equity_value = fields.get("equity_value", "")
    if unit and unit != EQUITY_UNIT_SETTLEMENT:
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:equity_unit")
    if precision and not _PRECISION.match(precision):
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:equity_precision")
    if equity_value:
        if not _DECIMAL.match(equity_value):
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:equity_value")
        else:
            try:
                parsed = Decimal(equity_value)
            except InvalidOperation:
                reasons.append(REASON_MALFORMED_FIELD)
                failures.append("MALFORMED:equity_value")
            else:
                exponent = parsed.as_tuple().exponent
                if isinstance(exponent, int) and precision and _PRECISION.match(precision):
                    if exponent < -int(precision):
                        reasons.append(REASON_MALFORMED_FIELD)
                        failures.append("EQUITY_VALUE_EXCEEDS_PRECISION")

    account = fields.get("account_identity", "")
    currency = fields.get("settlement_currency", "")
    if account in _UNKNOWN_TOKENS:
        reasons.append(REASON_ACCOUNT_SCOPE_MISMATCH)
        failures.append("ACCOUNT_IDENTITY_UNKNOWN")
    if currency in _UNKNOWN_TOKENS:
        reasons.append(REASON_CURRENCY_SCOPE_MISMATCH)
        failures.append("SETTLEMENT_CURRENCY_UNKNOWN")
    if expected_account_identity is not None and account and account != expected_account_identity:
        reasons.append(REASON_ACCOUNT_SCOPE_MISMATCH)
        failures.append("ACCOUNT_IDENTITY_MISMATCH")
    if (
        expected_settlement_currency is not None
        and currency
        and currency != expected_settlement_currency
    ):
        reasons.append(REASON_CURRENCY_SCOPE_MISMATCH)
        failures.append("SETTLEMENT_CURRENCY_MISMATCH")

    embedding = fields.get("embedding_status", "")
    liability = fields.get("liability_status", "")
    if embedding != EMBEDDING_EXPLICIT_PROVEN:
        reasons.append(REASON_EMBEDDING_UNRESOLVED)
        failures.append("EMBEDDING_NOT_EXPLICIT_PROVEN")
    if liability != LIABILITY_EXPLICIT_PROVEN:
        reasons.append(REASON_LIABILITY_UNRESOLVED)
        failures.append("LIABILITY_NOT_EXPLICIT_PROVEN")

    prior = fields.get("prior_checkpoint_id", "")
    checkpoint_id = fields.get("checkpoint_id", "")
    checkpoint_ref = fields.get("checkpoint_ref", "")
    if method == DERIVATION_OPTION_D_PRIOR_PLUS_STREAM:
        if prior in _UNKNOWN_TOKENS:
            reasons.append(REASON_PRIOR_CHECKPOINT_REQUIRED_MISSING)
            reasons.append(REASON_INITIAL_STOCK_ANCHOR_ABSENT)
            failures.append("PRIOR_CHECKPOINT_REQUIRED_MISSING")
        elif prior and prior == checkpoint_id:
            reasons.append(REASON_CONTRADICTORY_FIELD)
            failures.append("PRIOR_EQUALS_CURRENT_CHECKPOINT")
    if checkpoint_id in _UNKNOWN_TOKENS or checkpoint_ref in _UNKNOWN_TOKENS:
        reasons.append(REASON_CHECKPOINT_CANNOT_MINT)
        failures.append("CHECKPOINT_REF_UNKNOWN")

    declared_input = fields.get("input_digest", "")
    declared_semantic = fields.get("semantic_digest", "")
    computed_input = _sha256_text(
        _digest_inputs(fields=fields, included=included, excluded=excluded)
    )
    if declared_input:
        if not _SHA256_HEX.match(declared_input):
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:input_digest")
        elif declared_input != computed_input:
            reasons.append(REASON_REPLAY_NONDETERMINISTIC)
            failures.append("INPUT_DIGEST_MISMATCH")
    canonical_for_semantic = _digest_inputs(fields=fields, included=included, excluded=excluded)
    canonical_for_semantic["input_digest"] = computed_input
    computed_semantic = _sha256_text(canonical_for_semantic)
    if declared_semantic:
        if not _SHA256_HEX.match(declared_semantic):
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:semantic_digest")
        elif declared_semantic != computed_semantic:
            reasons.append(REASON_REPLAY_NONDETERMINISTIC)
            failures.append("SEMANTIC_DIGEST_MISMATCH")

    unique_reasons = list(dict.fromkeys(reasons))
    if not unique_reasons:
        reason_code = REASON_VALID
        validation_status = VALIDATION_VALID
    else:
        reason_code = min(unique_reasons, key=reason_precedence_index_v1)
        validation_status = VALIDATION_REJECTED
    return EquityStockValueRecordV1(
        stock_value_id=fields.get("stock_value_id", "") or stock_value_id,
        account_identity=account,
        settlement_currency=currency,
        equity_value=equity_value,
        equity_unit=unit,
        equity_precision=precision,
        as_of_time=as_of,
        sequence_identity=sequence,
        checkpoint_id=checkpoint_id,
        checkpoint_ref=checkpoint_ref,
        source_provenance=source,
        derivation_method=method,
        derivation_version=fields.get("derivation_version", ""),
        included_components=included,
        excluded_components=excluded,
        embedding_status=embedding,
        liability_status=liability,
        event_stream_boundary=event_boundary,
        replay_boundary=replay_boundary,
        prior_checkpoint_id=prior,
        semantic_digest=declared_semantic or computed_semantic,
        input_digest=declared_input or computed_input,
        validation_status=validation_status,
        reason_code=reason_code,
        reason_precedence_index=str(reason_precedence_index_v1(reason_code)),
        failures=tuple(failures),
    )


def evaluate_equity_stock_value_v1(
    payload: Mapping[str, Any],
    *,
    expected_account_identity: str | None = None,
    expected_settlement_currency: str | None = None,
    claimed_proof: str = "FIXTURE_VALID_STOCK_VALUE_ONLY",
) -> EquityStockValueRecordV1:
    first = _evaluate_equity_stock_value_once_v1(
        payload,
        expected_account_identity=expected_account_identity,
        expected_settlement_currency=expected_settlement_currency,
        claimed_proof=claimed_proof,
    )
    second = _evaluate_equity_stock_value_once_v1(
        payload,
        expected_account_identity=expected_account_identity,
        expected_settlement_currency=expected_settlement_currency,
        claimed_proof=claimed_proof,
    )
    if first != second:
        raise EquityStockCheckpointStockValueContractError(
            "STOCK_VALUE_EVALUATION_NOT_DETERMINISTIC"
        )
    return first


def bind_equity_stock_value_to_checkpoint_v1(
    *,
    stock: EquityStockValueRecordV1,
    checkpoint: EquityStockCheckpointContractV1,
    claimed_proof: str = "CHECKPOINT_ATTEST_EXISTING_STOCK",
) -> EquityStockCheckpointBindingV1:
    _assert_standing_pins()
    reject_claimed_stock_value_authority_mutation_v1(
        claimed_proof=claimed_proof,
        stock_value_id=stock.stock_value_id,
    )
    assert_checkpoint_cannot_mint_equity_v1(
        equity_mint_status=checkpoint.equity_mint_status,
        running_equity_value_state=checkpoint.running_equity_value_state,
        claimed_equity_stock_value=checkpoint.claimed_equity_stock_value,
        observation_vs_authority_class=checkpoint.observation_vs_authority_class,
    )
    reasons: list[str] = []
    if stock.validation_status != VALIDATION_VALID:
        reasons.append(stock.reason_code)
    if checkpoint.checkpoint_kind != CHECKPOINT_KIND:
        reasons.append(REASON_CHECKPOINT_CANNOT_MINT)
    if checkpoint.checkpoint_id != stock.checkpoint_id:
        reasons.append(REASON_CONTRADICTORY_FIELD)
    if checkpoint.bound_account_identity_ref != stock.account_identity:
        reasons.append(REASON_ACCOUNT_SCOPE_MISMATCH)
    if checkpoint.claimed_equity_stock_value != STATUS_ABSENT:
        reasons.append(REASON_CLAIMED_CHECKPOINT_MINT)
    if checkpoint.equity_mint_status != EQUITY_MINT_STATUS_NOT_MINTED:
        reasons.append(REASON_CHECKPOINT_CANNOT_MINT)
    unique_reasons = list(dict.fromkeys(reasons))
    if unique_reasons:
        reason_code = min(unique_reasons, key=reason_precedence_index_v1)
        validation_status = VALIDATION_REJECTED
    else:
        reason_code = REASON_VALID
        validation_status = VALIDATION_VALID
    binding_payload = {
        "stock_value_id": stock.stock_value_id,
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_ref": stock.checkpoint_ref,
        "binding_class": BINDING_CLASS,
        "checkpoint_mints_equity": FALSE_TOKEN,
        "account_identity": stock.account_identity,
        "settlement_currency": stock.settlement_currency,
        "stock_semantic_digest": stock.semantic_digest,
        "checkpoint_provenance_digest": checkpoint.provenance_digest,
    }
    return EquityStockCheckpointBindingV1(
        stock_value_id=stock.stock_value_id,
        checkpoint_id=checkpoint.checkpoint_id,
        checkpoint_ref=stock.checkpoint_ref,
        binding_class=BINDING_CLASS,
        checkpoint_mints_equity=FALSE_TOKEN,
        account_identity=stock.account_identity,
        settlement_currency=stock.settlement_currency,
        binding_digest=_sha256_text(binding_payload),
        validation_status=validation_status,
        reason_code=reason_code,
    )


def evaluate_today_authoritative_derivation_boundary_v1() -> AuthoritativeDerivationBoundaryV1:
    _assert_standing_pins()
    records = evaluate_today_live_equity_stock_kind_set_v1()
    members = ratified_live_equity_stock_kind_set_v1(records)
    replay = evaluate_today_live_equity_stock_kind_set_v1()
    if records != replay:
        raise EquityStockCheckpointStockValueContractError("KIND_SET_REPLAY_NOT_DETERMINISTIC")
    if members:
        raise EquityStockCheckpointStockValueContractError(
            f"KIND_INVENTED_OR_UNPROVEN_MEMBER:{','.join(members)}"
        )
    first = AuthoritativeDerivationBoundaryV1(
        derivation_method=DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        derivation_version=DERIVATION_VERSION,
        prior_stock_anchor_status=STATUS_ABSENT,
        prior_checkpoint_status=STATUS_NON_SOURCE_NO_BOUND_STOCK,
        event_stream_boundary_status=STATUS_FLOW_NOT_STOCK,
        replay_determinism_status=STATUS_DETERMINISTIC_FAIL_CLOSED,
        double_count_guards=DOUBLE_COUNT_GUARD,
        embedding_rules=EMBEDDING_RULE,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        live_equity_stock_kind_set_resolved=FALSE_TOKEN,
        new_stock_kind_candidate=NONE_TOKEN,
        membership_owner_ratification_required=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    second = AuthoritativeDerivationBoundaryV1(
        derivation_method=DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        derivation_version=DERIVATION_VERSION,
        prior_stock_anchor_status=STATUS_ABSENT,
        prior_checkpoint_status=STATUS_NON_SOURCE_NO_BOUND_STOCK,
        event_stream_boundary_status=STATUS_FLOW_NOT_STOCK,
        replay_determinism_status=STATUS_DETERMINISTIC_FAIL_CLOSED,
        double_count_guards=DOUBLE_COUNT_GUARD,
        embedding_rules=EMBEDDING_RULE,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        live_equity_stock_kind_set_resolved=FALSE_TOKEN,
        new_stock_kind_candidate=NONE_TOKEN,
        membership_owner_ratification_required=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    if first != second:
        raise EquityStockCheckpointStockValueContractError("DERIVATION_BOUNDARY_NOT_DETERMINISTIC")
    return first


def join_stock_value_contract_to_d6_diagnostics_v1(
    *,
    existing: Mapping[str, Any],
    boundary: AuthoritativeDerivationBoundaryV1,
) -> dict[str, Any]:
    attached = dict(existing)
    additions = {
        "STOCK_VALUE_CONTRACT_DEFINED": TRUE_TOKEN,
        "STOCK_VALUE_SCHEMA_CLASS": SCHEMA_CLASS,
        "AUTHORITATIVE_DERIVATION_DEFINED": TRUE_TOKEN,
        "AUTHORITATIVE_DERIVATION_METHOD": boundary.derivation_method,
        "INITIAL_STOCK_ANCHOR_STATUS": boundary.prior_stock_anchor_status,
        "PRIOR_CHECKPOINT_STATUS": boundary.prior_checkpoint_status,
        "EVENT_STREAM_BOUNDARY_STATUS": boundary.event_stream_boundary_status,
        "REPLAY_DETERMINISM_STATUS": boundary.replay_determinism_status,
        "DOUBLE_COUNT_GUARDS": boundary.double_count_guards,
        "EMBEDDING_RULES": boundary.embedding_rules,
        "CHECKPOINT_MINTS_EQUITY": boundary.checkpoint_mints_equity,
        "VENUE_EQ_SOURCE_AUTHORITY": boundary.venue_eq_source_authority,
        "LIVE_EQUITY_STOCK_KIND_SET": boundary.live_equity_stock_kind_set,
        "LIVE_EQUITY_STOCK_KIND_SET_RESOLVED": boundary.live_equity_stock_kind_set_resolved,
        "NEW_STOCK_KIND_CANDIDATE": boundary.new_stock_kind_candidate,
        "MEMBERSHIP_OWNER_RATIFICATION_REQUIRED": (boundary.membership_owner_ratification_required),
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": boundary.earliest_live_critical_path_blocker,
        "NEXT_OWNER_GO_REQUIRED": boundary.next_owner_go_required,
        "GOVERNED_CHECKPOINT_ROLE": ROLE_NON_SOURCE,
        "VENUE_EQ_ROLE": ROLE_RECONCILIATION_TARGET_ONLY,
        "NEW_CANONICAL_DEFINITION": TRUE_TOKEN,
        "LEGACY_SEMANTICS_RECONSTRUCTED": FALSE_TOKEN,
        "VENUE_POST_COUNT": "0",
    }
    for key, value in additions.items():
        if key in attached and attached[key] != value:
            raise EquityStockCheckpointStockValueContractError(
                f"DIAGNOSTIC_AUTHORITY_COLLISION:{key}"
            )
        attached[key] = value
    return attached


def execute_live_equity_stock_checkpoint_stock_value_contract_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bn_pack: Path,
    evidence_root: Path,
    persist_as_of: str,
) -> EquityStockCheckpointStockValueContractResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise EquityStockCheckpointStockValueContractError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise EquityStockCheckpointStockValueContractError("ORIGIN_MAIN_SHA_MISMATCH")
    bn_pack = Path(sealed_bn_pack)
    try:
        manifest_rc = verify_manifest_sha256_v1(store_root=bn_pack)
    except Exception as exc:
        raise EquityStockCheckpointStockValueContractError("BN_MANIFEST_VERIFY_FAILED") from exc
    if manifest_rc != 0:
        raise EquityStockCheckpointStockValueContractError("BN_MANIFEST_VERIFY_FAILED")
    claims_path = bn_pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise EquityStockCheckpointStockValueContractError("BN_CLAIMS_MISSING")
    try:
        bn_claims = _load_json_object(path=claims_path)
    except json.JSONDecodeError as exc:
        raise EquityStockCheckpointStockValueContractError("BN_CLAIMS_MALFORMED") from exc
    _require_token(field="KIND_SET", payload=bn_claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=bn_claims, expected=FALSE_TOKEN)
    _require_token(field="LIVE_EQUITY_STOCK_KIND_SET", payload=bn_claims, expected=KIND_SET_EMPTY)
    _require_token(field="GATE_A_EXECUTED", payload=bn_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bn_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bn_claims, expected="0")
    _require_token(field="VENUE_POST_COUNT", payload=bn_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bn_claims, expected=FALSE_TOKEN)
    _require_token(field="KINDS_INVENTED_THIS_GO", payload=bn_claims, expected=FALSE_TOKEN)
    _require_token(field="NEW_CANONICAL_DEFINITION", payload=bn_claims, expected=TRUE_TOKEN)
    _require_token(field="LEGACY_SEMANTICS_RECONSTRUCTED", payload=bn_claims, expected=FALSE_TOKEN)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=bn_claims, expected=OWNER_GO)
    _require_token(field="F12_DECISION", payload=bn_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F13_DECISION", payload=bn_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_KIND_DECISION", payload=bn_claims, expected=DECISION_REMAIN_UNKNOWN)
    reject_claimed_stock_value_authority_mutation_v1(
        claimed_proof="NEW_CANONICAL_DEFINITION_STOCK_VALUE_CONTRACT",
        stock_value_id=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    )
    reject_claimed_stock_value_authority_mutation_v1(
        claimed_proof="TODAY_DERIVATION_REJECTED_FAIL_CLOSED",
        stock_value_id="TODAY_PRODUCTIVE_STOCK",
    )
    boundary = evaluate_today_authoritative_derivation_boundary_v1()
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
    diagnostics = join_stock_value_contract_to_d6_diagnostics_v1(
        existing=standing,
        boundary=boundary,
    )
    folder = _folder_from_as_of(persist_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": persist_as_of,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "BN_CONTRACT_REUSED": TRUE_TOKEN,
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
        "CHECKPOINT_MINTS_EQUITY": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "STOCK_VALUE_CONTRACT_DEFINED": TRUE_TOKEN,
        "STOCK_VALUE_SCHEMA_CLASS": SCHEMA_CLASS,
        "AUTHORITATIVE_DERIVATION_DEFINED": TRUE_TOKEN,
        "AUTHORITATIVE_DERIVATION_METHOD": boundary.derivation_method,
        "INITIAL_STOCK_ANCHOR_STATUS": boundary.prior_stock_anchor_status,
        "PRIOR_CHECKPOINT_STATUS": boundary.prior_checkpoint_status,
        "EVENT_STREAM_BOUNDARY_STATUS": boundary.event_stream_boundary_status,
        "REPLAY_DETERMINISM_STATUS": boundary.replay_determinism_status,
        "DOUBLE_COUNT_GUARDS": boundary.double_count_guards,
        "EMBEDDING_RULES": boundary.embedding_rules,
        "HISTORICAL_UNKNOWN_ON_CRITICAL_PATH": FALSE_TOKEN,
        "HISTORICAL_UNKNOWN_CHANGED": FALSE_TOKEN,
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        "LIVE_EQUITY_STOCK_KIND_SET": KIND_SET_EMPTY,
        "LIVE_EQUITY_STOCK_KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_MEMBERS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        "BN_LIVE_BLOCKER_CONSUMED": BN_LIVE_BLOCKER,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "NEW_STOCK_KIND_CANDIDATE": NONE_TOKEN,
        "MEMBERSHIP_OWNER_RATIFICATION_REQUIRED": FALSE_TOKEN,
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
        "GOVERNED_CHECKPOINT_ROLE": ROLE_NON_SOURCE,
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
        "BN_MANIFEST_VERIFY_RC": "0",
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "stock_value_contract_v1.json",
        payload={
            "schema_class": SCHEMA_CLASS,
            "contract_version": CONTRACT_VERSION,
            "required_fields": list(REQUIRED_FIELDS),
            "reason_precedence": list(REASON_PRECEDENCE),
            "authoritative_derivation_method": DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
            "checkpoint_mints_equity": FALSE_TOKEN,
            "venue_eq_source_authority": FALSE_TOKEN,
            "new_canonical_definition": TRUE_TOKEN,
            "legacy_semantics_reconstructed": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "authoritative_derivation_boundary_v1.json",
        payload={
            "derivation_method": boundary.derivation_method,
            "derivation_version": boundary.derivation_version,
            "prior_stock_anchor_status": boundary.prior_stock_anchor_status,
            "prior_checkpoint_status": boundary.prior_checkpoint_status,
            "event_stream_boundary_status": boundary.event_stream_boundary_status,
            "replay_determinism_status": boundary.replay_determinism_status,
            "double_count_guards": boundary.double_count_guards,
            "embedding_rules": boundary.embedding_rules,
            "venue_eq_source_authority": boundary.venue_eq_source_authority,
            "checkpoint_mints_equity": boundary.checkpoint_mints_equity,
            "new_stock_kind_candidate": boundary.new_stock_kind_candidate,
            "membership_owner_ratification_required": (
                boundary.membership_owner_ratification_required
            ),
            "earliest_live_critical_path_blocker": boundary.earliest_live_critical_path_blocker,
            "next_owner_go_required": boundary.next_owner_go_required,
        },
    )
    _persist_json(path=store / "d6_diagnostics_v1.json", payload=diagnostics)
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "checkpoint_mints_equity": "FORBIDDEN",
            "venue_eq_as_source": "FORBIDDEN",
            "flow_as_stock": "FORBIDDEN",
            "available_capital_as_stock": "FORBIDDEN",
            "placement_capacity_as_stock": "FORBIDDEN",
            "p01_as_stock": "FORBIDDEN",
            "invent_live_source_kind": "FORBIDDEN",
            "reconstruct_historical_unknown": "FORBIDDEN",
            "empty_live_kind_set": KIND_SET_EMPTY,
            "double_count_guard": DOUBLE_COUNT_GUARD,
            "embedding_rule": EMBEDDING_RULE,
            "initial_stock_anchor": STATUS_ABSENT,
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
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return EquityStockCheckpointStockValueContractResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        stock_value_contract_defined=TRUE_TOKEN,
        authoritative_derivation_defined=TRUE_TOKEN,
        initial_stock_anchor_status=boundary.prior_stock_anchor_status,
        prior_checkpoint_status=boundary.prior_checkpoint_status,
        event_stream_boundary_status=boundary.event_stream_boundary_status,
        replay_determinism_status=boundary.replay_determinism_status,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        live_equity_stock_kind_set_resolved=FALSE_TOKEN,
        new_stock_kind_candidate=NONE_TOKEN,
        membership_owner_ratification_required=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        venue_get_count="0",
        venue_post_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        venue_eq_source_authority=FALSE_TOKEN,
        kinds_invented_this_go=FALSE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )


def fixture_valid_stock_value_payload_v1() -> dict[str, Any]:
    included = (COMPONENT_PRIOR_GOVERNED_STOCK,)
    excluded = tuple(sorted(REQUIRED_EXCLUDED_COMPONENTS))
    fields = {
        "stock_value_id": "FIXTURE_STOCK_VALUE_001",
        "account_identity": "FIXTURE_BOUND_ACCOUNT",
        "settlement_currency": "USDT",
        "equity_value": "100.00",
        "equity_unit": EQUITY_UNIT_SETTLEMENT,
        "equity_precision": "2",
        "as_of_time": "2026-09-14T12:00:00Z",
        "sequence_identity": "SEQ_FIXTURE_001",
        "checkpoint_id": "CKPT_FIXTURE_001",
        "checkpoint_ref": "CKPT_REF_FIXTURE_001",
        "source_provenance": DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        "derivation_method": DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        "derivation_version": DERIVATION_VERSION,
        "embedding_status": EMBEDDING_EXPLICIT_PROVEN,
        "liability_status": LIABILITY_EXPLICIT_PROVEN,
        "event_stream_boundary": "EVENT_BOUNDARY_FIXTURE_001",
        "replay_boundary": "2026-09-14T12:00:00Z",
        "prior_checkpoint_id": "CKPT_FIXTURE_PRIOR",
        "semantic_digest": "",
        "input_digest": "",
    }
    input_digest = _sha256_text(_digest_inputs(fields=fields, included=included, excluded=excluded))
    semantic_payload = _digest_inputs(fields=fields, included=included, excluded=excluded)
    semantic_payload["input_digest"] = input_digest
    payload = {
        **fields,
        "included_components": list(included),
        "excluded_components": list(excluded),
        "input_digest": input_digest,
        "semantic_digest": _sha256_text(semantic_payload),
        "validation_status": VALIDATION_VALID,
        "reason_code": REASON_VALID,
    }
    return payload


__all__ = [
    "AUTHORITATIVE_DERIVATION_DEFINED",
    "BINDING_CLASS",
    "CANONICAL_PACK_RELPATH",
    "CHECKPOINT_MINTS_EQUITY",
    "DERIVATION_OPTION_D_PRIOR_PLUS_STREAM",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "AuthoritativeDerivationBoundaryV1",
    "EquityStockCheckpointBindingV1",
    "EquityStockCheckpointStockValueContractError",
    "EquityStockCheckpointStockValueContractResultV1",
    "EquityStockValueRecordV1",
    "INITIAL_STOCK_ANCHOR_STATUS",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "REASON_PRECEDENCE",
    "REQUIRED_FIELDS",
    "SCHEMA_CLASS",
    "VENUE_EQ_SOURCE_AUTHORITY",
    "bind_equity_stock_value_to_checkpoint_v1",
    "compute_stock_value_input_digest_v1",
    "compute_stock_value_semantic_digest_v1",
    "evaluate_equity_stock_value_v1",
    "evaluate_today_authoritative_derivation_boundary_v1",
    "execute_live_equity_stock_checkpoint_stock_value_contract_v1",
    "fixture_valid_stock_value_payload_v1",
    "join_stock_value_contract_to_d6_diagnostics_v1",
    "reason_precedence_index_v1",
    "reject_claimed_stock_value_authority_mutation_v1",
]
