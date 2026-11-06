"""NEW_CANONICAL_DEFINITION of bootstrap INITIAL_STOCK_ANCHOR provenance.

Defines the fail-closed acquisition seam for the first OPTION_D prior stock.
Does not invent a live source kind. Does not reconstruct historical UNKNOWN.
Does not promote venue eq, checkpoint, flow, available, placement, or P01.
Today no forensic bootstrap proof is present. AUTHORITY_EFFECT=NONE.

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
    FACT_IDS,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    DAG_PIN,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_checkpoint_stock_value_contract_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BO_PACK_RELPATH,
    CHECKPOINT_MINTS_EQUITY as BO_CHECKPOINT_MINTS_EQUITY,
    DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BO_LIVE_BLOCKER,
    INITIAL_STOCK_ANCHOR_STATUS as BO_INITIAL_STOCK_ANCHOR_STATUS,
    NEXT_OWNER_GO_REQUIRED as BO_NEXT_OWNER_GO,
    OWNER_GO as BO_OWNER_GO,
    VENUE_EQ_SOURCE_AUTHORITY as BO_VENUE_EQ_SOURCE_AUTHORITY,
    evaluate_today_authoritative_derivation_boundary_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BN_PACK_RELPATH,
    CANDIDATE_C17,
    CANDIDATE_CLASSIFIED_EVENT_STREAM,
    CANDIDATE_GOVERNED_CHECKPOINT,
    CANDIDATE_P01,
    CANDIDATE_U04,
    CANDIDATE_U05,
    CANDIDATE_U06,
    CANDIDATE_VENUE_EQ,
    LAYER_ADJUDICATED,
    LAYER_CANONICAL,
    LAYER_FORENSIC,
    LAYER_HISTORICAL,
    LAYER_HYPOTHESIS,
    LAYER_OPEN,
    LIVE_EQUITY_STOCK_KIND_SET,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
    ROLE_AVAILABLE_CAPITAL_ONLY,
    ROLE_NON_SOURCE,
    ROLE_OTHER_DOMAIN,
    ROLE_PLACEMENT_CAPACITY_ONLY,
    ROLE_RECONCILIATION_TARGET_ONLY,
    ROLE_RISK_CAPITAL_REDUCTION_ONLY,
    ROLE_UNRESOLVED,
    evaluate_today_live_equity_stock_kind_set_v1,
    ratified_live_equity_stock_kind_set_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE_V1"
EXPECTED_ORIGIN_MAIN_SHA = "72d227d60efaf4245089582e466b035e7794207b"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_bootstrap_stock_provenance_wp1/2026-09-14T140000Z"
)
CLAIMS_FILE = "claims.json"
SCHEMA_CLASS = "BOOTSTRAP_STOCK_PROVENANCE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
ADMISSIBLE_SOURCE_CLASS = "OWNER_SUPPLIED_FORENSIC_BOOTSTRAP_STOCK"
EQUITY_UNIT_SETTLEMENT = "SETTLEMENT_CURRENCY_UNITS"
VALIDATION_VALID = "VALID"
VALIDATION_REJECTED = "REJECTED"
STATUS_ABSENT = "ABSENT"
STATUS_MISSING = "MISSING"
STATUS_SEAM_DEFINED_PROOF_ABSENT = "SEAM_DEFINED_PROOF_ABSENT"
STATUS_ACQUIRED_FORENSIC_PROOF = "ACQUIRED_FORENSIC_PROOF"
STATUS_STOCK_ONLY_NO_FLOW = "STOCK_ONLY_NO_FLOW"
DOUBLE_COUNT_GUARD = "STOCK_AND_FLOW_MAY_NOT_BOTH_COUNT"
EMBEDDING_RULE = "UNPROVEN_EMBEDDING_OR_LIABILITY_FAIL_CLOSED"
EMBEDDING_EXPLICIT_PROVEN = "EXPLICIT_PROVEN"
LIABILITY_EXPLICIT_PROVEN = "EXPLICIT_PROVEN"
SOURCE_KIND_STATUS = NONE_TOKEN
BOOTSTRAP_PROVENANCE_FINDING = "NO_PROVABLE_INITIAL_STOCK_ANCHOR"
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "BOOTSTRAP_STOCK_EXTERNAL_FORENSIC_PROOF_ABSENT"
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION_V1"
CANDIDATE_D4_GENESIS = "D4_GENESIS_ACCOUNT_CONFIG"
CANDIDATE_D5_OBSERVATION = "D5_CHECKPOINT_OBSERVATION"
CANDIDATE_OPTION_D = DERIVATION_OPTION_D_PRIOR_PLUS_STREAM
CANDIDATE_LEGACY_RELABEL = "LEGACY_RELABEL"
CANDIDATE_OWNER_SUPPLIED = ADMISSIBLE_SOURCE_CLASS

REQUIRED_FIELDS: tuple[str, ...] = (
    "anchor_id",
    "source_class",
    "account_identity",
    "settlement_currency",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "as_of_time",
    "sequence_identity",
    "provenance_ref",
    "provenance_digest",
    "input_digest",
    "semantic_digest",
    "embedding_status",
    "liability_status",
    "event_stream_boundary",
    "replay_boundary",
    "double_count_status",
    "acquisition_status",
    "validation_status",
    "reason_code",
)
SCALAR_INPUT_FIELDS: tuple[str, ...] = (
    "anchor_id",
    "source_class",
    "account_identity",
    "settlement_currency",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "as_of_time",
    "sequence_identity",
    "provenance_ref",
    "provenance_digest",
    "embedding_status",
    "liability_status",
    "event_stream_boundary",
    "replay_boundary",
    "double_count_status",
    "acquisition_status",
)

REASON_CLAIMED_CHECKPOINT_MINT = "CLAIMED_CHECKPOINT_MINT_FORBIDDEN"
REASON_CLAIMED_VENUE_EQ_SOURCE = "CLAIMED_VENUE_EQ_SOURCE_FORBIDDEN"
REASON_CLAIMED_FLOW_AS_STOCK = "CLAIMED_FLOW_AS_STOCK_FORBIDDEN"
REASON_CLAIMED_AVAILABLE_CAPITAL = "CLAIMED_AVAILABLE_CAPITAL_FORBIDDEN"
REASON_CLAIMED_PLACEMENT_CAPACITY = "CLAIMED_PLACEMENT_CAPACITY_FORBIDDEN"
REASON_CLAIMED_P01_AS_STOCK = "CLAIMED_P01_AS_STOCK_FORBIDDEN"
REASON_CIRCULAR_OPTION_D = "OPTION_D_CANNOT_BOOTSTRAP_ITSELF"
REASON_NOT_EQUITY_STOCK = "CANDIDATE_NOT_EQUITY_STOCK"
REASON_HISTORICAL_UNKNOWN = "HISTORICAL_UNKNOWN_NOT_BOOTSTRAP"
REASON_C17_NOT_CREATED = "C17_NOT_CREATED"
REASON_LEGACY_RELABEL = "LEGACY_RELABEL_FORBIDDEN"
REASON_MISSING_FIELD = "MISSING_FIELD"
REASON_MALFORMED_FIELD = "MALFORMED_FIELD"
REASON_CONTRADICTORY_FIELD = "CONTRADICTORY_FIELD"
REASON_ACCOUNT_SCOPE_MISMATCH = "ACCOUNT_SCOPE_MISMATCH"
REASON_CURRENCY_SCOPE_MISMATCH = "CURRENCY_SCOPE_MISMATCH"
REASON_SEQUENCE_TIME_AMBIGUOUS = "SEQUENCE_TIME_AMBIGUOUS"
REASON_SOURCE_PROVENANCE_MISSING = "SOURCE_PROVENANCE_MISSING"
REASON_SOURCE_PROVENANCE_MALFORMED = "SOURCE_PROVENANCE_MALFORMED"
REASON_DOUBLE_COUNT_STOCK_AND_FLOW = "DOUBLE_COUNT_STOCK_AND_FLOW"
REASON_EMBEDDING_UNRESOLVED = "EMBEDDING_UNRESOLVED"
REASON_LIABILITY_UNRESOLVED = "LIABILITY_UNRESOLVED"
REASON_KIND_MEMBERSHIP_UNRATIFIED = "KIND_MEMBERSHIP_UNRATIFIED"
REASON_EXTERNAL_PROOF_ABSENT = "EXTERNAL_FORENSIC_PROOF_ABSENT"
REASON_REPLAY_NONDETERMINISTIC = "REPLAY_NONDETERMINISTIC"
REASON_VALID = "VALID_BOOTSTRAP_STOCK_PROVENANCE"

REASON_PRECEDENCE: tuple[str, ...] = (
    REASON_CLAIMED_CHECKPOINT_MINT,
    REASON_CLAIMED_VENUE_EQ_SOURCE,
    REASON_CLAIMED_FLOW_AS_STOCK,
    REASON_CLAIMED_AVAILABLE_CAPITAL,
    REASON_CLAIMED_PLACEMENT_CAPACITY,
    REASON_CLAIMED_P01_AS_STOCK,
    REASON_CIRCULAR_OPTION_D,
    REASON_LEGACY_RELABEL,
    REASON_C17_NOT_CREATED,
    REASON_HISTORICAL_UNKNOWN,
    REASON_NOT_EQUITY_STOCK,
    REASON_MISSING_FIELD,
    REASON_MALFORMED_FIELD,
    REASON_CONTRADICTORY_FIELD,
    REASON_ACCOUNT_SCOPE_MISMATCH,
    REASON_CURRENCY_SCOPE_MISMATCH,
    REASON_SEQUENCE_TIME_AMBIGUOUS,
    REASON_SOURCE_PROVENANCE_MISSING,
    REASON_SOURCE_PROVENANCE_MALFORMED,
    REASON_DOUBLE_COUNT_STOCK_AND_FLOW,
    REASON_EMBEDDING_UNRESOLVED,
    REASON_LIABILITY_UNRESOLVED,
    REASON_KIND_MEMBERSHIP_UNRATIFIED,
    REASON_EXTERNAL_PROOF_ABSENT,
    REASON_REPLAY_NONDETERMINISTIC,
    REASON_VALID,
)

ALLOWED_CLAIMED_PROOFS: frozenset[str] = frozenset(
    {
        "NEW_CANONICAL_DEFINITION_BOOTSTRAP_PROVENANCE",
        "TODAY_BOOTSTRAP_REJECTED_FAIL_CLOSED",
        "FIXTURE_VALID_BOOTSTRAP_ONLY",
        "ACQUISITION_SEAM_DEFINED",
    }
)
FORBIDDEN_SOURCE_CLASSES: frozenset[str] = frozenset(
    {
        CANDIDATE_VENUE_EQ,
        "eq",
        CANDIDATE_GOVERNED_CHECKPOINT,
        "CHECKPOINT",
        "CHECKPOINT_MINT",
        CANDIDATE_CLASSIFIED_EVENT_STREAM,
        "FLOW",
        "DELTA",
        CANDIDATE_U04,
        "AVAILABLE_CAPITAL",
        CANDIDATE_U06,
        "PLACEMENT_CAPACITY",
        CANDIDATE_P01,
        "P01_RISK_CAPITAL",
        CANDIDATE_OPTION_D,
        CANDIDATE_LEGACY_RELABEL,
        "UNKNOWN",
        "UNCLASSIFIED",
        "UNPROVEN",
        "MISSING",
        NONE_TOKEN,
        STATUS_ABSENT,
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


class BootstrapStockProvenanceContractError(ValueError):
    """Fail-closed bootstrap stock provenance contract violation."""


@dataclass(frozen=True)
class BootstrapStockProvenanceRecordV1:
    anchor_id: str
    source_class: str
    account_identity: str
    settlement_currency: str
    equity_value: str
    equity_unit: str
    equity_precision: str
    as_of_time: str
    sequence_identity: str
    provenance_ref: str
    provenance_digest: str
    input_digest: str
    semantic_digest: str
    embedding_status: str
    liability_status: str
    event_stream_boundary: str
    replay_boundary: str
    double_count_status: str
    acquisition_status: str
    validation_status: str
    reason_code: str
    reason_precedence_index: str
    failures: tuple[str, ...]


@dataclass(frozen=True)
class BootstrapProvenanceCandidateRecordV1:
    candidate_id: str
    source_role: str
    layer: str
    input_status: str
    member: str
    reason_code: str
    reason_precedence_index: str


@dataclass(frozen=True)
class BootstrapStockProvenanceBoundaryV1:
    bootstrap_provenance_finding: str
    admissible_source_class: str
    admissible_source_present: str
    acquisition_seam_status: str
    initial_stock_anchor_status: str
    source_kind_status: str
    live_equity_stock_kind_set: str
    live_equity_stock_kind_set_resolved: str
    new_stock_kind_candidate: str
    membership_owner_ratification_required: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    new_canonical_definition: str
    legacy_semantics_reconstructed: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str


@dataclass(frozen=True)
class BootstrapStockProvenanceContractResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    bootstrap_provenance_finding: str
    acquisition_seam_status: str
    initial_stock_anchor_status: str
    source_kind_status: str
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
        raise BootstrapStockProvenanceContractError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise BootstrapStockProvenanceContractError(f"{field}_DRIFT:{actual}")


def _sha256_text(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise BootstrapStockProvenanceContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise BootstrapStockProvenanceContractError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise BootstrapStockProvenanceContractError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise BootstrapStockProvenanceContractError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise BootstrapStockProvenanceContractError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise BootstrapStockProvenanceContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise BootstrapStockProvenanceContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise BootstrapStockProvenanceContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise BootstrapStockProvenanceContractError("C17_CREATED_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise BootstrapStockProvenanceContractError("BN_KIND_SET_NOT_EMPTY")
    if BO_NEXT_OWNER_GO != OWNER_GO:
        raise BootstrapStockProvenanceContractError("BO_NEXT_OWNER_GO_DRIFT")
    if BO_LIVE_BLOCKER != "BOOTSTRAP_STOCK_PROVENANCE_ABSENT":
        raise BootstrapStockProvenanceContractError("BO_LIVE_BLOCKER_DRIFT")
    if BO_INITIAL_STOCK_ANCHOR_STATUS != STATUS_ABSENT:
        raise BootstrapStockProvenanceContractError("BO_INITIAL_STOCK_ANCHOR_NOT_ABSENT")
    if BO_CHECKPOINT_MINTS_EQUITY != FALSE_TOKEN:
        raise BootstrapStockProvenanceContractError("BO_CHECKPOINT_MINTS_EQUITY_DRIFT")
    if BO_VENUE_EQ_SOURCE_AUTHORITY != FALSE_TOKEN:
        raise BootstrapStockProvenanceContractError("BO_VENUE_EQ_SOURCE_AUTHORITY_DRIFT")
    if BO_OWNER_GO != "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT_V1":
        raise BootstrapStockProvenanceContractError("BO_OWNER_GO_DRIFT")
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


def reject_claimed_bootstrap_authority_mutation_v1(
    *,
    claimed_proof: str,
    anchor_id: str,
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
        "BOOTSTRAP_FROM_CHECKPOINT",
        "BOOTSTRAP_FROM_FLOW",
        "RELABEL_LEGACY_AS_STOCK",
        "RESTORE_LEGACY_EQUITY_LOGIC",
        "NORMALIZE_UNKNOWN_TO_INCLUDE",
        "NORMALIZE_UNKNOWN_TO_EXCLUDE",
        "PATH_C_UNKNOWN_CLOSEOUT",
        "MINT_INITIAL_STOCK",
    }
    if claimed_proof in forbidden:
        raise BootstrapStockProvenanceContractError(f"BOOTSTRAP_CANNOT_{claimed_proof}:{anchor_id}")
    if claimed_proof not in ALLOWED_CLAIMED_PROOFS:
        raise BootstrapStockProvenanceContractError(
            f"BOOTSTRAP_PROOF_UNKNOWN:{claimed_proof}:{anchor_id}"
        )


def reason_precedence_index_v1(reason_code: str) -> int:
    try:
        return REASON_PRECEDENCE.index(reason_code)
    except ValueError as exc:
        raise BootstrapStockProvenanceContractError(
            f"REASON_CODE_NOT_IN_PRECEDENCE:{reason_code}"
        ) from exc


def _field_as_str(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, str):
        return None
    return raw


def _digest_inputs(*, fields: Mapping[str, str]) -> dict[str, str]:
    return {key: fields.get(key, "") for key in SCALAR_INPUT_FIELDS}


def _evaluate_bootstrap_anchor_once_v1(
    payload: Mapping[str, Any],
    *,
    expected_account_identity: str | None = None,
    expected_settlement_currency: str | None = None,
    claimed_proof: str = "FIXTURE_VALID_BOOTSTRAP_ONLY",
) -> BootstrapStockProvenanceRecordV1:
    _assert_standing_pins()
    reject_claimed_bootstrap_authority_mutation_v1(
        claimed_proof=claimed_proof,
        anchor_id=str(payload.get("anchor_id") or "UNKNOWN"),
    )
    reasons: list[str] = []
    failures: list[str] = []
    fields: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        raw = payload.get(name, None)
        if name in {"validation_status", "reason_code"}:
            continue
        text = _field_as_str(raw)
        if raw is None:
            reasons.append(REASON_MISSING_FIELD)
            failures.append(f"MISSING:{name}")
            fields[name] = ""
        elif text is None:
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append(f"MALFORMED:{name}")
            fields[name] = ""
        else:
            fields[name] = text

    source = fields.get("source_class", "")
    if source in {
        CANDIDATE_VENUE_EQ,
        "eq",
    }:
        reasons.append(REASON_CLAIMED_VENUE_EQ_SOURCE)
    elif source in {CANDIDATE_GOVERNED_CHECKPOINT, "CHECKPOINT", "CHECKPOINT_MINT"}:
        reasons.append(REASON_CLAIMED_CHECKPOINT_MINT)
    elif source in {CANDIDATE_CLASSIFIED_EVENT_STREAM, "FLOW", "DELTA"}:
        reasons.append(REASON_CLAIMED_FLOW_AS_STOCK)
        reasons.append(REASON_DOUBLE_COUNT_STOCK_AND_FLOW)
    elif source in {CANDIDATE_U04, "AVAILABLE_CAPITAL"}:
        reasons.append(REASON_CLAIMED_AVAILABLE_CAPITAL)
    elif source in {CANDIDATE_U06, "PLACEMENT_CAPACITY"}:
        reasons.append(REASON_CLAIMED_PLACEMENT_CAPACITY)
    elif source in {CANDIDATE_P01, "P01_RISK_CAPITAL"}:
        reasons.append(REASON_CLAIMED_P01_AS_STOCK)
    elif source == CANDIDATE_OPTION_D:
        reasons.append(REASON_CIRCULAR_OPTION_D)
    elif source == CANDIDATE_LEGACY_RELABEL:
        reasons.append(REASON_LEGACY_RELABEL)
    elif source == CANDIDATE_C17:
        reasons.append(REASON_C17_NOT_CREATED)
    elif source in FACT_IDS or source == CANDIDATE_U05:
        reasons.append(REASON_HISTORICAL_UNKNOWN)
    elif source in {CANDIDATE_D4_GENESIS, CANDIDATE_D5_OBSERVATION}:
        reasons.append(REASON_NOT_EQUITY_STOCK)
    elif source in _UNKNOWN_TOKENS:
        reasons.append(REASON_SOURCE_PROVENANCE_MISSING)
    elif source and source != ADMISSIBLE_SOURCE_CLASS:
        if source in FORBIDDEN_SOURCE_CLASSES:
            reasons.append(REASON_SOURCE_PROVENANCE_MALFORMED)
        else:
            reasons.append(REASON_SOURCE_PROVENANCE_MALFORMED)
            failures.append("SOURCE_CLASS_NOT_ADMISSIBLE")

    as_of = fields.get("as_of_time", "")
    sequence = fields.get("sequence_identity", "")
    replay_boundary = fields.get("replay_boundary", "")
    event_boundary = fields.get("event_stream_boundary", "")
    if as_of and not _ISO_Z.match(as_of):
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:as_of_time")
    if sequence in _UNKNOWN_TOKENS:
        reasons.append(REASON_SEQUENCE_TIME_AMBIGUOUS)
        failures.append("SEQUENCE_IDENTITY_AMBIGUOUS")
    if as_of in _UNKNOWN_TOKENS:
        reasons.append(REASON_SEQUENCE_TIME_AMBIGUOUS)
        failures.append("AS_OF_TIME_AMBIGUOUS")
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

    double_count = fields.get("double_count_status", "")
    if double_count and double_count != STATUS_STOCK_ONLY_NO_FLOW:
        reasons.append(REASON_DOUBLE_COUNT_STOCK_AND_FLOW)
        failures.append("DOUBLE_COUNT_STATUS_NOT_STOCK_ONLY")

    acquisition = fields.get("acquisition_status", "")
    if source == ADMISSIBLE_SOURCE_CLASS and acquisition != STATUS_ACQUIRED_FORENSIC_PROOF:
        reasons.append(REASON_EXTERNAL_PROOF_ABSENT)
        failures.append("ADMISSIBLE_CLASS_WITHOUT_ACQUIRED_PROOF")
    if claimed_proof == "FIXTURE_VALID_BOOTSTRAP_ONLY" and source == ADMISSIBLE_SOURCE_CLASS:
        members = ratified_live_equity_stock_kind_set_v1(
            evaluate_today_live_equity_stock_kind_set_v1()
        )
        if members:
            reasons.append(REASON_KIND_MEMBERSHIP_UNRATIFIED)
            failures.append("KIND_SET_MEMBER_WOULD_BE_INVENTED")

    provenance_digest = fields.get("provenance_digest", "")
    declared_input = fields.get("input_digest", "")
    declared_semantic = fields.get("semantic_digest", "")
    if provenance_digest and not _SHA256_HEX.match(provenance_digest):
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:provenance_digest")
    computed_input = _sha256_text(_digest_inputs(fields=fields))
    if declared_input:
        if not _SHA256_HEX.match(declared_input):
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:input_digest")
        elif declared_input != computed_input:
            reasons.append(REASON_REPLAY_NONDETERMINISTIC)
            failures.append("INPUT_DIGEST_MISMATCH")
    canonical_for_semantic = _digest_inputs(fields=fields)
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
    return BootstrapStockProvenanceRecordV1(
        anchor_id=fields.get("anchor_id", ""),
        source_class=source,
        account_identity=account,
        settlement_currency=currency,
        equity_value=equity_value,
        equity_unit=unit,
        equity_precision=precision,
        as_of_time=as_of,
        sequence_identity=sequence,
        provenance_ref=fields.get("provenance_ref", ""),
        provenance_digest=provenance_digest,
        input_digest=declared_input or computed_input,
        semantic_digest=declared_semantic or computed_semantic,
        embedding_status=embedding,
        liability_status=liability,
        event_stream_boundary=event_boundary,
        replay_boundary=replay_boundary,
        double_count_status=double_count,
        acquisition_status=acquisition,
        validation_status=validation_status,
        reason_code=reason_code,
        reason_precedence_index=str(reason_precedence_index_v1(reason_code)),
        failures=tuple(failures),
    )


def evaluate_bootstrap_stock_provenance_v1(
    payload: Mapping[str, Any],
    *,
    expected_account_identity: str | None = None,
    expected_settlement_currency: str | None = None,
    claimed_proof: str = "FIXTURE_VALID_BOOTSTRAP_ONLY",
) -> BootstrapStockProvenanceRecordV1:
    first = _evaluate_bootstrap_anchor_once_v1(
        payload,
        expected_account_identity=expected_account_identity,
        expected_settlement_currency=expected_settlement_currency,
        claimed_proof=claimed_proof,
    )
    second = _evaluate_bootstrap_anchor_once_v1(
        payload,
        expected_account_identity=expected_account_identity,
        expected_settlement_currency=expected_settlement_currency,
        claimed_proof=claimed_proof,
    )
    if first != second:
        raise BootstrapStockProvenanceContractError("BOOTSTRAP_EVALUATION_NOT_DETERMINISTIC")
    return first


def _candidate_record(
    *,
    candidate_id: str,
    source_role: str,
    layer: str,
    input_status: str,
    reason_code: str,
) -> BootstrapProvenanceCandidateRecordV1:
    return BootstrapProvenanceCandidateRecordV1(
        candidate_id=candidate_id,
        source_role=source_role,
        layer=layer,
        input_status=input_status,
        member=FALSE_TOKEN,
        reason_code=reason_code,
        reason_precedence_index=str(reason_precedence_index_v1(reason_code)),
    )


def evaluate_today_bootstrap_provenance_candidates_v1() -> tuple[
    BootstrapProvenanceCandidateRecordV1, ...
]:
    _assert_standing_pins()
    records = (
        _candidate_record(
            candidate_id=CANDIDATE_VENUE_EQ,
            source_role=ROLE_RECONCILIATION_TARGET_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_VENUE_EQ_SOURCE,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_GOVERNED_CHECKPOINT,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_CHECKPOINT_MINT,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_CLASSIFIED_EVENT_STREAM,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_FLOW_AS_STOCK,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_U04,
            source_role=ROLE_AVAILABLE_CAPITAL_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_AVAILABLE_CAPITAL,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_U06,
            source_role=ROLE_PLACEMENT_CAPACITY_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_PLACEMENT_CAPACITY,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_P01,
            source_role=ROLE_RISK_CAPITAL_REDUCTION_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_P01_AS_STOCK,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_OPTION_D,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_CIRCULAR",
            reason_code=REASON_CIRCULAR_OPTION_D,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_LEGACY_RELABEL,
            source_role=ROLE_OTHER_DOMAIN,
            layer=LAYER_HYPOTHESIS,
            input_status="FORBIDDEN",
            reason_code=REASON_LEGACY_RELABEL,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_C17,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="ABSENT",
            reason_code=REASON_C17_NOT_CREATED,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_D4_GENESIS,
            source_role=ROLE_OTHER_DOMAIN,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_NOT_STOCK",
            reason_code=REASON_NOT_EQUITY_STOCK,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_D5_OBSERVATION,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_NOT_STOCK",
            reason_code=REASON_NOT_EQUITY_STOCK,
        ),
        *_tuple_historical_unknowns(),
        _candidate_record(
            candidate_id=CANDIDATE_OWNER_SUPPLIED,
            source_role=ROLE_UNRESOLVED,
            layer=LAYER_FORENSIC,
            input_status=STATUS_MISSING,
            reason_code=REASON_EXTERNAL_PROOF_ABSENT,
        ),
    )
    replay = (
        _candidate_record(
            candidate_id=CANDIDATE_VENUE_EQ,
            source_role=ROLE_RECONCILIATION_TARGET_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_VENUE_EQ_SOURCE,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_GOVERNED_CHECKPOINT,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_CHECKPOINT_MINT,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_CLASSIFIED_EVENT_STREAM,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_FLOW_AS_STOCK,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_U04,
            source_role=ROLE_AVAILABLE_CAPITAL_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_AVAILABLE_CAPITAL,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_U06,
            source_role=ROLE_PLACEMENT_CAPACITY_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_PLACEMENT_CAPACITY,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_P01,
            source_role=ROLE_RISK_CAPITAL_REDUCTION_ONLY,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_FORBIDDEN",
            reason_code=REASON_CLAIMED_P01_AS_STOCK,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_OPTION_D,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_CIRCULAR",
            reason_code=REASON_CIRCULAR_OPTION_D,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_LEGACY_RELABEL,
            source_role=ROLE_OTHER_DOMAIN,
            layer=LAYER_HYPOTHESIS,
            input_status="FORBIDDEN",
            reason_code=REASON_LEGACY_RELABEL,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_C17,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="ABSENT",
            reason_code=REASON_C17_NOT_CREATED,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_D4_GENESIS,
            source_role=ROLE_OTHER_DOMAIN,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_NOT_STOCK",
            reason_code=REASON_NOT_EQUITY_STOCK,
        ),
        _candidate_record(
            candidate_id=CANDIDATE_D5_OBSERVATION,
            source_role=ROLE_NON_SOURCE,
            layer=LAYER_CANONICAL,
            input_status="PRESENT_NOT_STOCK",
            reason_code=REASON_NOT_EQUITY_STOCK,
        ),
        *_tuple_historical_unknowns(),
        _candidate_record(
            candidate_id=CANDIDATE_OWNER_SUPPLIED,
            source_role=ROLE_UNRESOLVED,
            layer=LAYER_FORENSIC,
            input_status=STATUS_MISSING,
            reason_code=REASON_EXTERNAL_PROOF_ABSENT,
        ),
    )
    if records != replay:
        raise BootstrapStockProvenanceContractError("CANDIDATE_REPLAY_NOT_DETERMINISTIC")
    if any(item.member != FALSE_TOKEN for item in records):
        raise BootstrapStockProvenanceContractError("KIND_INVENTED_OR_UNPROVEN_MEMBER")
    return records


def _tuple_historical_unknowns() -> tuple[BootstrapProvenanceCandidateRecordV1, ...]:
    return tuple(
        _candidate_record(
            candidate_id=fact_id,
            source_role=ROLE_UNRESOLVED,
            layer=LAYER_HISTORICAL,
            input_status="UNRESOLVED",
            reason_code=REASON_HISTORICAL_UNKNOWN,
        )
        for fact_id in FACT_IDS
    )


def evaluate_today_bootstrap_stock_provenance_boundary_v1() -> BootstrapStockProvenanceBoundaryV1:
    _assert_standing_pins()
    kind_records = evaluate_today_live_equity_stock_kind_set_v1()
    members = ratified_live_equity_stock_kind_set_v1(kind_records)
    if members:
        raise BootstrapStockProvenanceContractError(
            f"KIND_INVENTED_OR_UNPROVEN_MEMBER:{','.join(members)}"
        )
    bo_boundary = evaluate_today_authoritative_derivation_boundary_v1()
    if bo_boundary.prior_stock_anchor_status != STATUS_ABSENT:
        raise BootstrapStockProvenanceContractError("BO_PRIOR_STOCK_NOT_ABSENT")
    candidates = evaluate_today_bootstrap_provenance_candidates_v1()
    owner_supplied = next(
        item for item in candidates if item.candidate_id == CANDIDATE_OWNER_SUPPLIED
    )
    if owner_supplied.reason_code != REASON_EXTERNAL_PROOF_ABSENT:
        raise BootstrapStockProvenanceContractError("OWNER_SUPPLIED_NOT_ABSENT")
    if any(item.layer == LAYER_ADJUDICATED and item.member == TRUE_TOKEN for item in candidates):
        raise BootstrapStockProvenanceContractError("ADJUDICATED_MEMBER_FORBIDDEN")
    if any(item.layer == LAYER_OPEN and item.member == TRUE_TOKEN for item in candidates):
        raise BootstrapStockProvenanceContractError("OPEN_MEMBER_FORBIDDEN")
    first = BootstrapStockProvenanceBoundaryV1(
        bootstrap_provenance_finding=BOOTSTRAP_PROVENANCE_FINDING,
        admissible_source_class=ADMISSIBLE_SOURCE_CLASS,
        admissible_source_present=FALSE_TOKEN,
        acquisition_seam_status=STATUS_SEAM_DEFINED_PROOF_ABSENT,
        initial_stock_anchor_status=STATUS_ABSENT,
        source_kind_status=SOURCE_KIND_STATUS,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        live_equity_stock_kind_set_resolved=FALSE_TOKEN,
        new_stock_kind_candidate=NONE_TOKEN,
        membership_owner_ratification_required=FALSE_TOKEN,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        new_canonical_definition=TRUE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    second = BootstrapStockProvenanceBoundaryV1(
        bootstrap_provenance_finding=BOOTSTRAP_PROVENANCE_FINDING,
        admissible_source_class=ADMISSIBLE_SOURCE_CLASS,
        admissible_source_present=FALSE_TOKEN,
        acquisition_seam_status=STATUS_SEAM_DEFINED_PROOF_ABSENT,
        initial_stock_anchor_status=STATUS_ABSENT,
        source_kind_status=SOURCE_KIND_STATUS,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        live_equity_stock_kind_set_resolved=FALSE_TOKEN,
        new_stock_kind_candidate=NONE_TOKEN,
        membership_owner_ratification_required=FALSE_TOKEN,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        new_canonical_definition=TRUE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    if first != second:
        raise BootstrapStockProvenanceContractError("BOOTSTRAP_BOUNDARY_NOT_DETERMINISTIC")
    return first


def join_bootstrap_provenance_to_d6_diagnostics_v1(
    *,
    existing: Mapping[str, Any],
    boundary: BootstrapStockProvenanceBoundaryV1,
) -> dict[str, Any]:
    attached = dict(existing)
    additions = {
        "BOOTSTRAP_PROVENANCE_CONTRACT_DEFINED": TRUE_TOKEN,
        "BOOTSTRAP_PROVENANCE_SCHEMA_CLASS": SCHEMA_CLASS,
        "BOOTSTRAP_PROVENANCE_FINDING": boundary.bootstrap_provenance_finding,
        "ADMISSIBLE_BOOTSTRAP_SOURCE_CLASS": boundary.admissible_source_class,
        "ADMISSIBLE_SOURCE_PRESENT": boundary.admissible_source_present,
        "ACQUISITION_SEAM_STATUS": boundary.acquisition_seam_status,
        "INITIAL_STOCK_ANCHOR_STATUS": boundary.initial_stock_anchor_status,
        "SOURCE_KIND_STATUS": boundary.source_kind_status,
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
            raise BootstrapStockProvenanceContractError(f"DIAGNOSTIC_AUTHORITY_COLLISION:{key}")
        attached[key] = value
    return attached


def execute_live_equity_stock_bootstrap_stock_provenance_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bo_pack: Path,
    evidence_root: Path,
    persist_as_of: str,
) -> BootstrapStockProvenanceContractResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise BootstrapStockProvenanceContractError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise BootstrapStockProvenanceContractError("ORIGIN_MAIN_SHA_MISMATCH")
    bo_pack = Path(sealed_bo_pack)
    try:
        manifest_rc = verify_manifest_sha256_v1(store_root=bo_pack)
    except Exception as exc:
        raise BootstrapStockProvenanceContractError("BO_MANIFEST_VERIFY_FAILED") from exc
    if manifest_rc != 0:
        raise BootstrapStockProvenanceContractError("BO_MANIFEST_VERIFY_FAILED")
    claims_path = bo_pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise BootstrapStockProvenanceContractError("BO_CLAIMS_MISSING")
    try:
        bo_claims = _load_json_object(path=claims_path)
    except json.JSONDecodeError as exc:
        raise BootstrapStockProvenanceContractError("BO_CLAIMS_MALFORMED") from exc
    _require_token(field="KIND_SET", payload=bo_claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="LIVE_EQUITY_STOCK_KIND_SET", payload=bo_claims, expected=KIND_SET_EMPTY)
    _require_token(field="GATE_A_EXECUTED", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bo_claims, expected="0")
    _require_token(field="VENUE_POST_COUNT", payload=bo_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="KINDS_INVENTED_THIS_GO", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="NEW_CANONICAL_DEFINITION", payload=bo_claims, expected=TRUE_TOKEN)
    _require_token(field="LEGACY_SEMANTICS_RECONSTRUCTED", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="CHECKPOINT_MINTS_EQUITY", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=bo_claims, expected=FALSE_TOKEN)
    _require_token(field="INITIAL_STOCK_ANCHOR_STATUS", payload=bo_claims, expected=STATUS_ABSENT)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=bo_claims, expected=OWNER_GO)
    _require_token(
        field="EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
        payload=bo_claims,
        expected=BO_LIVE_BLOCKER,
    )
    _require_token(field="F12_DECISION", payload=bo_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F13_DECISION", payload=bo_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_KIND_DECISION", payload=bo_claims, expected=DECISION_REMAIN_UNKNOWN)
    reject_claimed_bootstrap_authority_mutation_v1(
        claimed_proof="NEW_CANONICAL_DEFINITION_BOOTSTRAP_PROVENANCE",
        anchor_id=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    )
    reject_claimed_bootstrap_authority_mutation_v1(
        claimed_proof="TODAY_BOOTSTRAP_REJECTED_FAIL_CLOSED",
        anchor_id="TODAY_PRODUCTIVE_BOOTSTRAP",
    )
    reject_claimed_bootstrap_authority_mutation_v1(
        claimed_proof="ACQUISITION_SEAM_DEFINED",
        anchor_id=ADMISSIBLE_SOURCE_CLASS,
    )
    boundary = evaluate_today_bootstrap_stock_provenance_boundary_v1()
    candidates = evaluate_today_bootstrap_provenance_candidates_v1()
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
    diagnostics = join_bootstrap_provenance_to_d6_diagnostics_v1(
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
        "SEALED_BO_PACK": CANONICAL_BO_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "BO_CONTRACT_REUSED": TRUE_TOKEN,
        "BN_CONTRACT_REUSED": TRUE_TOKEN,
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
        "BOOTSTRAP_PROVENANCE_CONTRACT_DEFINED": TRUE_TOKEN,
        "BOOTSTRAP_PROVENANCE_SCHEMA_CLASS": SCHEMA_CLASS,
        "BOOTSTRAP_PROVENANCE_FINDING": boundary.bootstrap_provenance_finding,
        "ADMISSIBLE_BOOTSTRAP_SOURCE_CLASS": boundary.admissible_source_class,
        "ADMISSIBLE_SOURCE_PRESENT": boundary.admissible_source_present,
        "ACQUISITION_SEAM_STATUS": boundary.acquisition_seam_status,
        "INITIAL_STOCK_ANCHOR_STATUS": boundary.initial_stock_anchor_status,
        "SOURCE_KIND_STATUS": boundary.source_kind_status,
        "AUTHORITATIVE_DERIVATION_METHOD": DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
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
        "BO_LIVE_BLOCKER_CONSUMED": BO_LIVE_BLOCKER,
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
        "BO_MANIFEST_VERIFY_RC": "0",
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "bootstrap_provenance_contract_v1.json",
        payload={
            "schema_class": SCHEMA_CLASS,
            "contract_version": CONTRACT_VERSION,
            "required_fields": list(REQUIRED_FIELDS),
            "reason_precedence": list(REASON_PRECEDENCE),
            "admissible_source_class": ADMISSIBLE_SOURCE_CLASS,
            "checkpoint_mints_equity": FALSE_TOKEN,
            "venue_eq_source_authority": FALSE_TOKEN,
            "new_canonical_definition": TRUE_TOKEN,
            "legacy_semantics_reconstructed": FALSE_TOKEN,
            "option_d_cannot_bootstrap_itself": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=store / "bootstrap_provenance_boundary_v1.json",
        payload={
            "bootstrap_provenance_finding": boundary.bootstrap_provenance_finding,
            "admissible_source_class": boundary.admissible_source_class,
            "admissible_source_present": boundary.admissible_source_present,
            "acquisition_seam_status": boundary.acquisition_seam_status,
            "initial_stock_anchor_status": boundary.initial_stock_anchor_status,
            "source_kind_status": boundary.source_kind_status,
            "new_stock_kind_candidate": boundary.new_stock_kind_candidate,
            "membership_owner_ratification_required": (
                boundary.membership_owner_ratification_required
            ),
            "earliest_live_critical_path_blocker": boundary.earliest_live_critical_path_blocker,
            "next_owner_go_required": boundary.next_owner_go_required,
        },
    )
    _persist_json(
        path=store / "candidate_census_v1.json",
        payload={
            "candidates": [
                {
                    "candidate_id": item.candidate_id,
                    "source_role": item.source_role,
                    "layer": item.layer,
                    "input_status": item.input_status,
                    "member": item.member,
                    "reason_code": item.reason_code,
                    "reason_precedence_index": item.reason_precedence_index,
                }
                for item in candidates
            ]
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
            "option_d_self_bootstrap": "FORBIDDEN",
            "invent_live_source_kind": "FORBIDDEN",
            "reconstruct_historical_unknown": "FORBIDDEN",
            "empty_live_kind_set": KIND_SET_EMPTY,
            "double_count_guard": DOUBLE_COUNT_GUARD,
            "embedding_rule": EMBEDDING_RULE,
            "initial_stock_anchor": STATUS_ABSENT,
            "acquisition_seam_status": STATUS_SEAM_DEFINED_PROOF_ABSENT,
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
            "parent_bo_pack": CANONICAL_BO_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return BootstrapStockProvenanceContractResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        bootstrap_provenance_finding=boundary.bootstrap_provenance_finding,
        acquisition_seam_status=boundary.acquisition_seam_status,
        initial_stock_anchor_status=boundary.initial_stock_anchor_status,
        source_kind_status=boundary.source_kind_status,
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


def fixture_valid_bootstrap_stock_payload_v1() -> dict[str, Any]:
    fields = {
        "anchor_id": "FIXTURE_BOOTSTRAP_ANCHOR_001",
        "source_class": ADMISSIBLE_SOURCE_CLASS,
        "account_identity": "FIXTURE_BOUND_ACCOUNT",
        "settlement_currency": "USDT",
        "equity_value": "100.00",
        "equity_unit": EQUITY_UNIT_SETTLEMENT,
        "equity_precision": "2",
        "as_of_time": "2026-09-14T14:00:00Z",
        "sequence_identity": "SEQ_BOOTSTRAP_FIXTURE_001",
        "provenance_ref": "OWNER_SUPPLIED_FORENSIC_REF_FIXTURE",
        "provenance_digest": "c" * 64,
        "embedding_status": EMBEDDING_EXPLICIT_PROVEN,
        "liability_status": LIABILITY_EXPLICIT_PROVEN,
        "event_stream_boundary": "EVENT_BOUNDARY_BOOTSTRAP_FIXTURE_001",
        "replay_boundary": "2026-09-14T14:00:00Z",
        "double_count_status": STATUS_STOCK_ONLY_NO_FLOW,
        "acquisition_status": STATUS_ACQUIRED_FORENSIC_PROOF,
    }
    input_digest = _sha256_text(_digest_inputs(fields=fields))
    semantic_payload = _digest_inputs(fields=fields)
    semantic_payload["input_digest"] = input_digest
    return {
        **fields,
        "input_digest": input_digest,
        "semantic_digest": _sha256_text(semantic_payload),
        "validation_status": VALIDATION_VALID,
        "reason_code": REASON_VALID,
    }


__all__ = [
    "ADMISSIBLE_SOURCE_CLASS",
    "BOOTSTRAP_PROVENANCE_FINDING",
    "CANONICAL_PACK_RELPATH",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "REASON_PRECEDENCE",
    "REQUIRED_FIELDS",
    "SCHEMA_CLASS",
    "BootstrapStockProvenanceBoundaryV1",
    "BootstrapStockProvenanceContractError",
    "BootstrapStockProvenanceContractResultV1",
    "BootstrapStockProvenanceRecordV1",
    "evaluate_bootstrap_stock_provenance_v1",
    "evaluate_today_bootstrap_provenance_candidates_v1",
    "evaluate_today_bootstrap_stock_provenance_boundary_v1",
    "execute_live_equity_stock_bootstrap_stock_provenance_v1",
    "fixture_valid_bootstrap_stock_payload_v1",
    "reason_precedence_index_v1",
    "reject_claimed_bootstrap_authority_mutation_v1",
]
