"""NEW_CANONICAL today initial-stock source kind.

Retires the historical forensic bootstrap-artifact supply path from the
productive critical path. Sealed BQ/BR packs remain immutable audit
evidence. Defines OWNER_DECLARED_TODAY_INITIAL_EQUITY_STOCK as a new
canonical source-kind taxonomy. Does not invent a declaration value.
Does not ratify. Candidate is not an anchor. KIND_SET stays empty until
a later ratification GO. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
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
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
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
    DIMENSION_AVAILABLE_FOR_SIZING,
    DIMENSION_EQUITY_STOCK,
    DIMENSION_P01_RISK_CAPITAL_REDUCTION,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.fresh_eq_reconciliation_target_contract_v1 import (
    STATUS_UNKNOWN as EQ_RECONCILIATION_STATUS_UNKNOWN,
    TOLERANCE_POLICY_EXACT,
    evaluate_fresh_eq_reconciliation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_provenance_v1 import (
    STATUS_ABSENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_checkpoint_stock_value_contract_v1 import (
    DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
    STATUS_FLOW_NOT_STOCK,
    STATUS_NON_SOURCE_NO_BOUND_STOCK,
    evaluate_today_authoritative_derivation_boundary_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BN_PACK_RELPATH,
    INPUT_MISSING,
    LAYER_CANONICAL,
    LIVE_EQUITY_STOCK_KIND_SET,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
    LiveEquityStockKindCandidateV1,
    ROLE_EQUITY_STOCK_SOURCE,
    ROLE_RISK_CAPITAL_REDUCTION_ONLY,
    evaluate_live_equity_stock_kind_membership_v1,
    evaluate_today_live_equity_stock_kind_set_v1,
    ratified_live_equity_stock_kind_set_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_owner_supplied_bootstrap_artifact_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BR_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BR_LIVE_BLOCKER,
    NEXT_OWNER_GO_REQUIRED as BR_NEXT_OWNER_GO,
    OWNER_GO as BR_OWNER_GO,
    detect_forbidden_implicit_normalization_v1,
    evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_NEW_CANONICAL_TODAY_INITIAL_STOCK_SOURCE_KIND_V1"
EXPECTED_ORIGIN_MAIN_SHA = "462464f45038886bb27cd08fc23bb4472e66db1d"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_today_initial_stock_source_kind_wp1/"
    "2026-09-14T184000Z"
)
CLAIMS_FILE = "claims.json"
SCHEMA_CLASS = "TODAY_INITIAL_STOCK_SOURCE_KIND_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
TODAY_SOURCE_KIND = "OWNER_DECLARED_TODAY_INITIAL_EQUITY_STOCK"
TODAY_SOURCE_TYPE = "OWNER_DECLARED_TODAY_FILE"
ECONOMIC_MEANING = "ABSOLUTE_ACCOUNT_EQUITY_STOCK_AT_DECLARED_AS_OF_FOR_OPTION_D_PRIOR"
DECLARATION_SURFACE_RELPATH = "evidence/ops/owner_supplied_today_initial_stock_declaration_v1"
DECLARATION_FILENAME = "owner_declared_today_initial_equity_stock_v1.json"
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
FORENSIC_PATH_PRODUCTIVE_STATUS = "RETIRED_FROM_PRODUCTIVE_CRITICAL_PATH"
FORENSIC_EVIDENCE_RETENTION_STATUS = "RETAINED_IMMUTABLE"
HISTORICAL_ARTIFACT_EXISTENCE_CLAIM = "NO_PROVABLE_ARTIFACT_WITHIN_AVAILABLE_LOCAL_SEARCH_SURFACES"
DISCOVERY_VERDICT = "EXHAUSTED_WITHIN_AVAILABLE_LOCAL_SEARCH_SURFACES"
OLD_EXTERNAL_ARTIFACT_DEPENDENCY_STATUS = "RETIRED_FROM_PRODUCTIVE_CRITICAL_PATH"
SURFACE_MISSING = "MISSING"
SURFACE_EMPTY = "EMPTY"
SURFACE_PRESENT = "PRESENT"
VALIDATION_VALID = "VALID"
VALIDATION_INVALID = "INVALID"
VALIDATION_INCOMPLETE = "INCOMPLETE"
VALIDATION_CONTRADICTORY = "CONTRADICTORY"
CANDIDATE_ABSENT = "ABSENT"
CANDIDATE_PRESENT_UNRATIFIED = "PRESENT_UNRATIFIED"
RATIFICATION_AUTHORITY_ABSENT = "RATIFICATION_AUTHORITY_ABSENT"
SOURCE_KIND_DEFINED_NOT_MEMBER = "DEFINED_NOT_KIND_SET_MEMBER"
RUNNING_EQUITY_BLOCKED = "BLOCKED_NO_RATIFIED_ANCHOR"
VENUE_EQ_RECONCILIATION_UNBOUND = "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
AVAILABLE_FOR_SIZING_AFTER_EQUITY = "AFTER_EQUITY_SEPARATE"
INSTRUMENT_ACCOUNT_LEVEL = "ACCOUNT_LEVEL"
EPISTEMIC_RAW_DECLARATION = "RAW_OWNER_TODAY_DECLARATION"
EPISTEMIC_DERIVED = "ADJUDICATED_CONCLUSION"
EPISTEMIC_CANONICAL = "CANONICAL_AUTHORITY"
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "OWNER_SUPPLIED_TODAY_INITIAL_STOCK_DECLARATION_REQUIRED"
NEXT_OWNER_GO_REQUIRED = (
    "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_DECLARATION_SUPPLY_V1"
)
NEXT_RATIFICATION_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_RATIFICATION_V1"
INGEST_CAPABILITY_DEFINED = "TODAY_SOURCE_KIND_CONTRACT_CANDIDATE_RATIFICATION_BOUNDARY_DEFINED"

REQUIRED_FIELDS: tuple[str, ...] = (
    "declaration_id",
    "source_kind",
    "economic_meaning",
    "account_identity",
    "instrument_identity",
    "settlement_currency",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "as_of_time",
    "validity_window_start",
    "validity_window_end",
    "provenance_digest",
    "ratification_status",
    "source_type",
)
BINDING_FIELDS: tuple[str, ...] = (
    "account_identity",
    "instrument_identity",
    "as_of_time",
    "settlement_currency",
)
_UNKNOWN_VALUES: frozenset[str] = frozenset(
    {
        "UNKNOWN",
        "UNCLASSIFIED",
        "UNPROVEN",
        "MISSING",
        "DEFAULT",
        "UNSPECIFIED",
        NONE_TOKEN,
    }
)
REASON_JSON_MALFORMED = "JSON_MALFORMED"
REASON_DECLARATION_ABSENT = "OWNER_SUPPLIED_TODAY_INITIAL_STOCK_DECLARATION_REQUIRED"
REASON_MULTIPLE_DECLARATIONS = "MULTIPLE_DECLARATIONS_CONTRADICTORY"
REASON_IMPLICIT_NORMALIZATION_FORBIDDEN = "IMPLICIT_NORMALIZATION_FORBIDDEN"
REASON_ACCOUNT_BINDING_MISMATCH = "ACCOUNT_BINDING_MISMATCH"
REASON_INSTRUMENT_BINDING_MISMATCH = "INSTRUMENT_BINDING_MISMATCH"
REASON_TIME_BINDING_MISMATCH = "TIME_BINDING_MISMATCH"
REASON_UNKNOWN_SOURCE_KIND = "UNKNOWN_SOURCE_KIND"
REASON_FORENSIC_PATH_NOT_PRODUCTIVE = "FORENSIC_BOOTSTRAP_PATH_NOT_PRODUCTIVE_AUTHORITY"
REASON_VENUE_EQ_CANNOT_BE_SOURCE = "VENUE_EQ_CANNOT_BE_SOURCE"
REASON_CHECKPOINT_CANNOT_MINT = "CHECKPOINT_CANNOT_MINT_EQUITY"
REASON_FIXTURE_CANNOT_PROMOTE = "FIXTURE_CANNOT_PROMOTE"
REASON_FLOW_NOT_STOCK = "FLOW_CANNOT_BE_SOURCE"
REASON_ESTIMATED_PNL = "ESTIMATED_PNL_CANNOT_BE_SOURCE"
REASON_PLAUSIBILITY = "PLAUSIBILITY_CANNOT_BE_SOURCE"
REASON_UNCLASSIFIED_EVENT = "UNCLASSIFIED_EVENT_CANNOT_BE_SOURCE"
REASON_UNKNOWN_SOURCE_TYPE = "UNKNOWN_SOURCE_TYPE"
REASON_MISSING_FIELD = "MISSING_FIELD"
REASON_MALFORMED_FIELD = "MALFORMED_FIELD"
REASON_CONTRADICTORY_FIELD = "CONTRADICTORY_FIELD"
REASON_DIGEST_MISMATCH = "PROVENANCE_DIGEST_MISMATCH"
REASON_RATIFICATION_FORBIDDEN = "DECLARATION_CLAIMED_RATIFICATION"
REASON_VALID_CANDIDATE = "VALID_TODAY_CANDIDATE_NOT_RATIFIED"
REASON_PRECEDENCE: tuple[str, ...] = (
    REASON_FORENSIC_PATH_NOT_PRODUCTIVE,
    REASON_VENUE_EQ_CANNOT_BE_SOURCE,
    REASON_CHECKPOINT_CANNOT_MINT,
    REASON_FIXTURE_CANNOT_PROMOTE,
    REASON_FLOW_NOT_STOCK,
    REASON_ESTIMATED_PNL,
    REASON_PLAUSIBILITY,
    REASON_UNCLASSIFIED_EVENT,
    REASON_JSON_MALFORMED,
    REASON_MULTIPLE_DECLARATIONS,
    REASON_IMPLICIT_NORMALIZATION_FORBIDDEN,
    REASON_UNKNOWN_SOURCE_KIND,
    REASON_UNKNOWN_SOURCE_TYPE,
    REASON_ACCOUNT_BINDING_MISMATCH,
    REASON_INSTRUMENT_BINDING_MISMATCH,
    REASON_TIME_BINDING_MISMATCH,
    REASON_MISSING_FIELD,
    REASON_MALFORMED_FIELD,
    REASON_CONTRADICTORY_FIELD,
    REASON_DIGEST_MISMATCH,
    REASON_RATIFICATION_FORBIDDEN,
    REASON_DECLARATION_ABSENT,
    REASON_VALID_CANDIDATE,
)
INCOMPLETE_REASONS: frozenset[str] = frozenset({REASON_DECLARATION_ABSENT, REASON_MISSING_FIELD})
CONTRADICTORY_REASONS: frozenset[str] = frozenset(
    {REASON_MULTIPLE_DECLARATIONS, REASON_CONTRADICTORY_FIELD, REASON_DIGEST_MISMATCH}
)


class TodayInitialStockSourceKindContractError(ValueError):
    """Fail-closed today initial-stock source-kind violation."""


@dataclass(frozen=True)
class TodayDeclarationScanV1:
    surface_relpath: str
    surface_status: str
    declaration_present: str
    declaration_count: str
    declaration_path: str


@dataclass(frozen=True)
class TodayDeclarationCandidateV1:
    validation_status: str
    reason_code: str
    failures: tuple[str, ...]
    declaration_sha256: str
    initial_stock_candidate_status: str
    initial_stock_anchor_status: str
    source_kind_status: str
    live_equity_stock_kind_set: str
    ratification_status: str
    membership_member: str


@dataclass(frozen=True)
class TodayInitialStockBoundaryV1:
    forensic_path_productive_status: str
    forensic_evidence_retention_status: str
    historical_artifact_existence_claim: str
    discovery_verdict: str
    old_external_artifact_dependency_status: str
    today_source_kind: str
    today_source_contract_status: str
    today_observation_status: str
    candidate_status: str
    ratification_status: str
    initial_stock_anchor_status: str
    live_equity_stock_kind_set: str
    checkpoint_status: str
    event_stream_binding_status: str
    running_equity_reconstruction_status: str
    venue_eq_reconciliation_status: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str


@dataclass(frozen=True)
class TodayInitialStockContractResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    forensic_path_productive_status: str
    today_observation_status: str
    candidate_status: str
    ratification_status: str
    initial_stock_anchor_status: str
    live_equity_stock_kind_set: str
    checkpoint_status: str
    event_stream_binding_status: str
    running_equity_reconstruction_status: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    kinds_invented_this_go: str
    legacy_semantics_reconstructed: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str
    venue_get_count: str
    venue_post_count: str
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
        raise TodayInitialStockSourceKindContractError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise TodayInitialStockSourceKindContractError(f"{field}_DRIFT:{actual}")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def semantic_declaration_digest_v1(payload: Mapping[str, Any]) -> str:
    stripped = {key: value for key, value in payload.items() if key != "provenance_digest"}
    return _sha256_bytes(_canonical_json(stripped).encode("utf-8"))


def reason_precedence_index_v1(reason_code: str) -> int:
    try:
        return REASON_PRECEDENCE.index(reason_code)
    except ValueError as exc:
        raise TodayInitialStockSourceKindContractError(
            f"REASON_CODE_NOT_IN_PRECEDENCE:{reason_code}"
        ) from exc


def classify_validation_status_v1(reason_code: str) -> str:
    if reason_code == REASON_VALID_CANDIDATE:
        return VALIDATION_VALID
    if reason_code in CONTRADICTORY_REASONS:
        return VALIDATION_CONTRADICTORY
    if reason_code in INCOMPLETE_REASONS:
        return VALIDATION_INCOMPLETE
    return VALIDATION_INVALID


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise TodayInitialStockSourceKindContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise TodayInitialStockSourceKindContractError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise TodayInitialStockSourceKindContractError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise TodayInitialStockSourceKindContractError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise TodayInitialStockSourceKindContractError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise TodayInitialStockSourceKindContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise TodayInitialStockSourceKindContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise TodayInitialStockSourceKindContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise TodayInitialStockSourceKindContractError("C17_CREATED_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise TodayInitialStockSourceKindContractError("BN_KIND_SET_NOT_EMPTY")
    if LIVE_ENABLED is not False:
        raise TodayInitialStockSourceKindContractError("LIVE_ENABLED_NOT_FALSE")
    if LIVE_ARMED is not False:
        raise TodayInitialStockSourceKindContractError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise TodayInitialStockSourceKindContractError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if BR_OWNER_GO != "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_V1":
        raise TodayInitialStockSourceKindContractError("BR_OWNER_GO_DRIFT")
    if BR_LIVE_BLOCKER != "EXTERNAL_FORENSIC_ARTIFACT_REQUIRED":
        raise TodayInitialStockSourceKindContractError("BR_HISTORICAL_BLOCKER_DRIFT")
    if BR_NEXT_OWNER_GO != (
        "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_SUPPLY_V1"
    ):
        raise TodayInitialStockSourceKindContractError("BR_HISTORICAL_NEXT_GO_DRIFT")
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
    reject_forensic_path_as_productive_authority_v1(
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
    )


def reject_forensic_path_as_productive_authority_v1(*, claimed_proof: str) -> None:
    forbidden = {
        "EXTERNAL_FORENSIC_ARTIFACT_REQUIRED_STILL_PRODUCTIVE",
        "PROMOTE_FORENSIC_ARTIFACT_TO_TODAY_SOURCE",
        "RESTORE_HISTORICAL_F12",
        "RESTORE_HISTORICAL_F13",
        "RESTORE_HISTORICAL_U05",
        "BOOTSTRAP_FROM_VENUE_EQ",
        "CHECKPOINT_MINT_EQUITY",
        "PROMOTE_FIXTURE",
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
    }
    if claimed_proof in forbidden:
        raise TodayInitialStockSourceKindContractError(
            f"FORENSIC_OR_LEGACY_CLAIM_FORBIDDEN:{claimed_proof}"
        )


def scan_today_declaration_surface_v1(
    *,
    repo_root: Path,
    surface_relpath: str = DECLARATION_SURFACE_RELPATH,
) -> TodayDeclarationScanV1:
    _assert_standing_pins()
    surface = Path(repo_root) / surface_relpath
    if not surface.exists():
        return TodayDeclarationScanV1(
            surface_relpath=surface_relpath,
            surface_status=SURFACE_MISSING,
            declaration_present=FALSE_TOKEN,
            declaration_count="0",
            declaration_path="",
        )
    if not surface.is_dir():
        raise TodayInitialStockSourceKindContractError("DECLARATION_SURFACE_NOT_DIRECTORY")
    artifacts = sorted(
        path for path in surface.iterdir() if path.is_file() and path.name.endswith(".json")
    )
    if not artifacts:
        return TodayDeclarationScanV1(
            surface_relpath=surface_relpath,
            surface_status=SURFACE_EMPTY,
            declaration_present=FALSE_TOKEN,
            declaration_count="0",
            declaration_path="",
        )
    return TodayDeclarationScanV1(
        surface_relpath=surface_relpath,
        surface_status=SURFACE_PRESENT,
        declaration_present=TRUE_TOKEN,
        declaration_count=str(len(artifacts)),
        declaration_path=str(artifacts[0].relative_to(repo_root)),
    )


def _membership_for_declaration(
    *,
    input_status: str,
    absolute_present: bool,
) -> str:
    record = evaluate_live_equity_stock_kind_membership_v1(
        LiveEquityStockKindCandidateV1(
            candidate_id=TODAY_SOURCE_KIND,
            source_role=ROLE_EQUITY_STOCK_SOURCE,
            layer=LAYER_CANONICAL,
            input_status=input_status,
            claimed_proof="TODAY_CANDIDATE_REJECTED_FAIL_CLOSED",
            is_historical_unknown=False,
            is_delta_or_flow=False,
            is_reconciliation_witness=False,
            is_available_capital=False,
            is_placement_capacity=False,
            is_risk_capital_reduction=False,
            is_checkpoint_non_minting=True,
            embedding_proven=False,
            identity_proven=False,
            time_sequence_proven=False,
            double_count_proven_safe=False,
            absolute_stock_value_present=absolute_present,
            option_d_start_capable=False,
            authority_ref=f"{TODAY_SOURCE_KIND};NEW_CANONICAL_UNRATIFIED",
        )
    )
    return record.member


def evaluate_today_declaration_candidate_v1(
    *,
    repo_root: Path,
    claimed_proof: str,
    expected_bindings: Mapping[str, str] | None = None,
) -> TodayDeclarationCandidateV1:
    _assert_standing_pins()
    reject_forensic_path_as_productive_authority_v1(claimed_proof=claimed_proof)
    scan = scan_today_declaration_surface_v1(repo_root=repo_root)
    reasons: list[str] = []
    failures: list[str] = []
    digest = ""
    if scan.declaration_present != TRUE_TOKEN:
        reasons.append(REASON_DECLARATION_ABSENT)
        failures.append("TODAY_DECLARATION_ABSENT")
        reason_code = min(reasons, key=reason_precedence_index_v1)
        member = _membership_for_declaration(input_status=INPUT_MISSING, absolute_present=False)
        return TodayDeclarationCandidateV1(
            validation_status=classify_validation_status_v1(reason_code),
            reason_code=reason_code,
            failures=tuple(failures),
            declaration_sha256=NONE_TOKEN,
            initial_stock_candidate_status=CANDIDATE_ABSENT,
            initial_stock_anchor_status=STATUS_ABSENT,
            source_kind_status=SOURCE_KIND_DEFINED_NOT_MEMBER,
            live_equity_stock_kind_set=KIND_SET_EMPTY,
            ratification_status=RATIFICATION_AUTHORITY_ABSENT,
            membership_member=member,
        )
    if scan.declaration_count != "1":
        reasons.append(REASON_MULTIPLE_DECLARATIONS)
        failures.append("MULTIPLE_DECLARATION_FILES")
    path = Path(repo_root) / scan.declaration_path
    raw_bytes = path.read_bytes()
    digest = _sha256_bytes(raw_bytes)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        reasons.append(REASON_JSON_MALFORMED)
        payload = None
    if payload is not None and not isinstance(payload, dict):
        reasons.append(REASON_JSON_MALFORMED)
        payload = None
    if isinstance(payload, dict):
        failures.extend(detect_forbidden_implicit_normalization_v1(payload))
        if any(item.startswith("IMPLICIT_COERCE_FORBIDDEN:") for item in failures):
            reasons.append(REASON_IMPLICIT_NORMALIZATION_FORBIDDEN)
        source_kind = str(payload.get("source_kind") or "")
        source_type = str(payload.get("source_type") or "")
        if source_kind in {"OWNER_SUPPLIED_FORENSIC_BOOTSTRAP_STOCK", "FORENSIC_BOOTSTRAP"}:
            reasons.append(REASON_FORENSIC_PATH_NOT_PRODUCTIVE)
        elif source_kind and source_kind != TODAY_SOURCE_KIND:
            reasons.append(REASON_UNKNOWN_SOURCE_KIND)
        if source_type in {"VENUE_EQ", "eq", "VENUE_GET"}:
            reasons.append(REASON_VENUE_EQ_CANNOT_BE_SOURCE)
        elif source_type in {"CHECKPOINT", "CHECKPOINT_MINT"}:
            reasons.append(REASON_CHECKPOINT_CANNOT_MINT)
        elif source_type in {"FLOW", "HISTORICAL_FLOW", "EVENT_STREAM"}:
            reasons.append(REASON_FLOW_NOT_STOCK)
        elif source_type in {"ESTIMATED_PNL", "PNL"}:
            reasons.append(REASON_ESTIMATED_PNL)
        elif source_type == "PLAUSIBILITY":
            reasons.append(REASON_PLAUSIBILITY)
        elif source_type in {"UNCLASSIFIED", "UNCLASSIFIED_EVENT"}:
            reasons.append(REASON_UNCLASSIFIED_EVENT)
        elif source_type and source_type != TODAY_SOURCE_TYPE:
            reasons.append(REASON_UNKNOWN_SOURCE_TYPE)
        if str(payload.get("declaration_id") or "").startswith("FIXTURE"):
            reasons.append(REASON_FIXTURE_CANNOT_PROMOTE)
        if str(payload.get("ratification_status") or "") not in {"", "NOT_RATIFIED"}:
            reasons.append(REASON_RATIFICATION_FORBIDDEN)
        declared_digest = str(payload.get("provenance_digest") or "")
        if declared_digest and not _SHA256_HEX.match(declared_digest):
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:provenance_digest")
        elif declared_digest and declared_digest != semantic_declaration_digest_v1(payload):
            reasons.append(REASON_DIGEST_MISMATCH)
        economic_meaning = str(payload.get("economic_meaning") or "")
        if economic_meaning and economic_meaning != ECONOMIC_MEANING:
            reasons.append(REASON_CONTRADICTORY_FIELD)
            failures.append("CONTRADICTORY:economic_meaning")
        instrument_identity = str(payload.get("instrument_identity") or "")
        if instrument_identity and instrument_identity != INSTRUMENT_ACCOUNT_LEVEL:
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:instrument_identity")
        as_of_time = str(payload.get("as_of_time") or "")
        window_start = str(payload.get("validity_window_start") or "")
        window_end = str(payload.get("validity_window_end") or "")
        if as_of_time and window_start and window_start != as_of_time:
            reasons.append(REASON_CONTRADICTORY_FIELD)
            failures.append("CONTRADICTORY:validity_window_start")
        if as_of_time and window_end and window_end != as_of_time:
            reasons.append(REASON_CONTRADICTORY_FIELD)
            failures.append("CONTRADICTORY:validity_window_end")
        for field in REQUIRED_FIELDS:
            raw_field = payload.get(field, None)
            if field not in payload or raw_field in ("", None):
                if field == "ratification_status" and raw_field == "":
                    continue
                reasons.append(REASON_MISSING_FIELD)
                failures.append(f"MISSING:{field}")
        if expected_bindings:
            if str(payload.get("account_identity") or "") != expected_bindings["account_identity"]:
                reasons.append(REASON_ACCOUNT_BINDING_MISMATCH)
            if (
                str(payload.get("instrument_identity") or "")
                != expected_bindings["instrument_identity"]
            ):
                reasons.append(REASON_INSTRUMENT_BINDING_MISMATCH)
            if str(payload.get("as_of_time") or "") != expected_bindings["as_of_time"]:
                reasons.append(REASON_TIME_BINDING_MISMATCH)
        for name in BINDING_FIELDS:
            raw = payload.get(name)
            if isinstance(raw, str) and raw in _UNKNOWN_VALUES:
                reasons.append(REASON_MALFORMED_FIELD)
                failures.append(f"UNKNOWN_VALUE:{name}")
    unique = list(dict.fromkeys(reasons))
    if not unique:
        reason_code = REASON_VALID_CANDIDATE
        candidate_status = CANDIDATE_PRESENT_UNRATIFIED
        member = _membership_for_declaration(input_status=INPUT_MISSING, absolute_present=True)
    else:
        reason_code = min(unique, key=reason_precedence_index_v1)
        candidate_status = CANDIDATE_ABSENT
        member = FALSE_TOKEN
    if reason_code == REASON_VALID_CANDIDATE:
        member = FALSE_TOKEN
    return TodayDeclarationCandidateV1(
        validation_status=classify_validation_status_v1(reason_code),
        reason_code=reason_code,
        failures=tuple(dict.fromkeys(failures)),
        declaration_sha256=digest or NONE_TOKEN,
        initial_stock_candidate_status=candidate_status,
        initial_stock_anchor_status=STATUS_ABSENT,
        source_kind_status=SOURCE_KIND_DEFINED_NOT_MEMBER,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        ratification_status=RATIFICATION_AUTHORITY_ABSENT,
        membership_member=member,
    )


def bind_today_reconstruction_unbound_v1() -> tuple[str, str, str, str]:
    _assert_standing_pins()
    derivation = evaluate_today_authoritative_derivation_boundary_v1()
    if derivation.derivation_method != DERIVATION_OPTION_D_PRIOR_PLUS_STREAM:
        raise TodayInitialStockSourceKindContractError("BO_DERIVATION_METHOD_DRIFT")
    if derivation.prior_checkpoint_status != STATUS_NON_SOURCE_NO_BOUND_STOCK:
        raise TodayInitialStockSourceKindContractError("BO_CHECKPOINT_NOT_NON_SOURCE")
    if derivation.event_stream_boundary_status != STATUS_FLOW_NOT_STOCK:
        raise TodayInitialStockSourceKindContractError("BO_EVENT_STREAM_NOT_FLOW")
    eq_status = evaluate_fresh_eq_reconciliation_v1(
        reconstructed_equity_value_state=STATUS_ABSENT,
        reconstructed_equity_value=STATUS_ABSENT,
        venue_eq_value_state=STATUS_ABSENT,
        venue_eq_value=STATUS_ABSENT,
        tolerance_policy=TOLERANCE_POLICY_EXACT,
    )
    if eq_status != EQ_RECONCILIATION_STATUS_UNKNOWN:
        raise TodayInitialStockSourceKindContractError(
            f"VENUE_EQ_RECONCILIATION_NOT_UNBOUND:{eq_status}"
        )
    if DIMENSION_EQUITY_STOCK == DIMENSION_AVAILABLE_FOR_SIZING:
        raise TodayInitialStockSourceKindContractError("SIZING_COLLAPSED_INTO_EQUITY")
    if DIMENSION_P01_RISK_CAPITAL_REDUCTION == DIMENSION_EQUITY_STOCK:
        raise TodayInitialStockSourceKindContractError("P01_COLLAPSED_INTO_EQUITY")
    return (
        derivation.prior_checkpoint_status,
        derivation.event_stream_boundary_status,
        RUNNING_EQUITY_BLOCKED,
        VENUE_EQ_RECONCILIATION_UNBOUND,
    )


def evaluate_today_initial_stock_source_kind_boundary_v1(
    *,
    repo_root: Path,
) -> TodayInitialStockBoundaryV1:
    _assert_standing_pins()
    br_boundary = evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1(repo_root=repo_root)
    if br_boundary.forensic_artifact_present != FALSE_TOKEN:
        raise TodayInitialStockSourceKindContractError("BR_FORENSIC_ARTIFACT_NOT_ABSENT")
    if br_boundary.initial_stock_anchor_status != STATUS_ABSENT:
        raise TodayInitialStockSourceKindContractError("BR_ANCHOR_NOT_ABSENT")
    bn_members = ratified_live_equity_stock_kind_set_v1(
        evaluate_today_live_equity_stock_kind_set_v1()
    )
    if bn_members:
        raise TodayInitialStockSourceKindContractError("BN_KIND_SET_NOT_EMPTY")
    candidate = evaluate_today_declaration_candidate_v1(
        repo_root=repo_root,
        claimed_proof="TODAY_SOURCE_KIND_DEFINED_DECLARATION_ABSENT_FAIL_CLOSED",
    )
    (
        checkpoint_status,
        event_status,
        reconstruction,
        venue_eq,
    ) = bind_today_reconstruction_unbound_v1()
    if candidate.initial_stock_candidate_status == CANDIDATE_PRESENT_UNRATIFIED:
        blocker = "TODAY_INITIAL_STOCK_RATIFICATION_AUTHORITY_ABSENT"
        next_go = NEXT_RATIFICATION_GO
        observation = "PRESENT_UNRATIFIED"
    else:
        blocker = EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
        next_go = NEXT_OWNER_GO_REQUIRED
        observation = "ABSENT"
    first = TodayInitialStockBoundaryV1(
        forensic_path_productive_status=FORENSIC_PATH_PRODUCTIVE_STATUS,
        forensic_evidence_retention_status=FORENSIC_EVIDENCE_RETENTION_STATUS,
        historical_artifact_existence_claim=HISTORICAL_ARTIFACT_EXISTENCE_CLAIM,
        discovery_verdict=DISCOVERY_VERDICT,
        old_external_artifact_dependency_status=OLD_EXTERNAL_ARTIFACT_DEPENDENCY_STATUS,
        today_source_kind=TODAY_SOURCE_KIND,
        today_source_contract_status=INGEST_CAPABILITY_DEFINED,
        today_observation_status=observation,
        candidate_status=candidate.initial_stock_candidate_status,
        ratification_status=RATIFICATION_AUTHORITY_ABSENT,
        initial_stock_anchor_status=STATUS_ABSENT,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        checkpoint_status=checkpoint_status,
        event_stream_binding_status=event_status,
        running_equity_reconstruction_status=reconstruction,
        venue_eq_reconciliation_status=venue_eq,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        earliest_live_critical_path_blocker=blocker,
        next_owner_go_required=next_go,
    )
    second = TodayInitialStockBoundaryV1(
        forensic_path_productive_status=FORENSIC_PATH_PRODUCTIVE_STATUS,
        forensic_evidence_retention_status=FORENSIC_EVIDENCE_RETENTION_STATUS,
        historical_artifact_existence_claim=HISTORICAL_ARTIFACT_EXISTENCE_CLAIM,
        discovery_verdict=DISCOVERY_VERDICT,
        old_external_artifact_dependency_status=OLD_EXTERNAL_ARTIFACT_DEPENDENCY_STATUS,
        today_source_kind=TODAY_SOURCE_KIND,
        today_source_contract_status=INGEST_CAPABILITY_DEFINED,
        today_observation_status=observation,
        candidate_status=candidate.initial_stock_candidate_status,
        ratification_status=RATIFICATION_AUTHORITY_ABSENT,
        initial_stock_anchor_status=STATUS_ABSENT,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        checkpoint_status=checkpoint_status,
        event_stream_binding_status=event_status,
        running_equity_reconstruction_status=reconstruction,
        venue_eq_reconciliation_status=venue_eq,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        earliest_live_critical_path_blocker=blocker,
        next_owner_go_required=next_go,
    )
    if first != second:
        raise TodayInitialStockSourceKindContractError("TODAY_BOUNDARY_NOT_DETERMINISTIC")
    return first


def execute_live_equity_stock_today_initial_stock_source_kind_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_br_pack: Path,
    repo_root: Path,
    evidence_root: Path,
    persist_as_of: str,
) -> TodayInitialStockContractResultV1:
    if owner_go != OWNER_GO:
        raise TodayInitialStockSourceKindContractError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise TodayInitialStockSourceKindContractError("ORIGIN_MAIN_SHA_MISMATCH")
    if verify_manifest_sha256_v1(store_root=sealed_br_pack) != 0:
        raise TodayInitialStockSourceKindContractError("BR_MANIFEST_VERIFY_FAILED")
    br_claims = _load_json_object(path=Path(sealed_br_pack) / CLAIMS_FILE)
    _require_token(field="FORENSIC_ARTIFACT_PRESENT", payload=br_claims, expected=FALSE_TOKEN)
    _require_token(field="INITIAL_STOCK_ANCHOR_STATUS", payload=br_claims, expected=STATUS_ABSENT)
    _require_token(field="LIVE_EQUITY_STOCK_KIND_SET", payload=br_claims, expected=KIND_SET_EMPTY)
    _require_token(
        field="EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
        payload=br_claims,
        expected=BR_LIVE_BLOCKER,
    )
    boundary = evaluate_today_initial_stock_source_kind_boundary_v1(repo_root=repo_root)
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
        "SEALED_BR_PACK": CANONICAL_BR_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "BR_CONTRACT_REUSED": TRUE_TOKEN,
        "BN_CONTRACT_REUSED": TRUE_TOKEN,
        "BO_CONTRACT_REUSED": TRUE_TOKEN,
        "NEW_CANONICAL_DEFINITION": TRUE_TOKEN,
        "NEW_CANONICAL_SEMANTICS": TRUE_TOKEN,
        "LEGACY_SEMANTICS_RECONSTRUCTED": FALSE_TOKEN,
        "KINDS_INVENTED_THIS_GO": FALSE_TOKEN,
        "INVENTED_IDENTITIES": FALSE_TOKEN,
        "INVENTED_VALUES": FALSE_TOKEN,
        "FORENSIC_PATH_PRODUCTIVE_STATUS": FORENSIC_PATH_PRODUCTIVE_STATUS,
        "FORENSIC_EVIDENCE_RETENTION_STATUS": FORENSIC_EVIDENCE_RETENTION_STATUS,
        "HISTORICAL_ARTIFACT_EXISTENCE_CLAIM": HISTORICAL_ARTIFACT_EXISTENCE_CLAIM,
        "DISCOVERY_VERDICT": DISCOVERY_VERDICT,
        "OLD_EXTERNAL_ARTIFACT_DEPENDENCY_STATUS": OLD_EXTERNAL_ARTIFACT_DEPENDENCY_STATUS,
        "TODAY_INITIAL_STOCK_SOURCE_KIND": TODAY_SOURCE_KIND,
        "TODAY_SOURCE_CONTRACT_STATUS": INGEST_CAPABILITY_DEFINED,
        "TODAY_OBSERVATION_STATUS": boundary.today_observation_status,
        "CANDIDATE_STATUS": boundary.candidate_status,
        "RATIFICATION_STATUS": boundary.ratification_status,
        "INITIAL_STOCK_ANCHOR_STATUS": STATUS_ABSENT,
        "LIVE_EQUITY_STOCK_KIND_SET": KIND_SET_EMPTY,
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        "CHECKPOINT_STATUS": boundary.checkpoint_status,
        "EVENT_STREAM_BINDING_STATUS": boundary.event_stream_binding_status,
        "RUNNING_EQUITY_RECONSTRUCTION_STATUS": boundary.running_equity_reconstruction_status,
        "VENUE_EQ_RECONCILIATION_STATUS": boundary.venue_eq_reconciliation_status,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "CHECKPOINT_MINTS_EQUITY": FALSE_TOKEN,
        "AUTHORITATIVE_DERIVATION_METHOD": DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        "AVAILABLE_FOR_SIZING_STATUS": AVAILABLE_FOR_SIZING_AFTER_EQUITY,
        "P01_ROLE": ROLE_RISK_CAPITAL_REDUCTION_ONLY,
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": boundary.earliest_live_critical_path_blocker,
        "NEXT_OWNER_GO_REQUIRED": boundary.next_owner_go_required,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "VENUE_GET_COUNT": "0",
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
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "DECLARATION_SURFACE": DECLARATION_SURFACE_RELPATH,
        "DECLARATION_FILENAME": DECLARATION_FILENAME,
        "GATE_A_ID": GATE_A_ID,
        "GATE_B_ID": GATE_B_ID,
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "forensic_path_retirement_v1.json",
        payload={
            "forensic_path_productive_status": FORENSIC_PATH_PRODUCTIVE_STATUS,
            "forensic_evidence_retention_status": FORENSIC_EVIDENCE_RETENTION_STATUS,
            "historical_artifact_existence_claim": HISTORICAL_ARTIFACT_EXISTENCE_CLAIM,
            "discovery_verdict": DISCOVERY_VERDICT,
            "old_external_artifact_dependency_status": OLD_EXTERNAL_ARTIFACT_DEPENDENCY_STATUS,
            "sealed_br_pack": CANONICAL_BR_PACK_RELPATH,
            "br_live_blocker_historical": BR_LIVE_BLOCKER,
            "br_next_owner_go_historical": BR_NEXT_OWNER_GO,
            "productive_next_owner_go": boundary.next_owner_go_required,
        },
    )
    _persist_json(
        path=store / "today_source_kind_contract_v1.json",
        payload={
            "schema_class": SCHEMA_CLASS,
            "source_kind": TODAY_SOURCE_KIND,
            "source_type": TODAY_SOURCE_TYPE,
            "economic_meaning": ECONOMIC_MEANING,
            "required_inputs": list(REQUIRED_FIELDS),
            "account_binding": "OWNER_DECLARED_ACCOUNT_IDENTITY",
            "instrument_identity": INSTRUMENT_ACCOUNT_LEVEL,
            "time_binding": "OWNER_DECLARED_AS_OF_POINT_IN_TIME",
            "observation_binding": "OWNER_DECLARED_TODAY_DECLARATION_FILE",
            "provenance": "SHA256_OF_DECLARATION_WITHOUT_PROVENANCE_DIGEST",
            "determinism": "SAME_INPUTS_SAME_CANDIDATE_DECISION",
            "validity_window": "POINT_IN_TIME_EQUAL_TO_AS_OF",
            "ratification_authority": NEXT_RATIFICATION_GO,
            "replay_behavior": "DETERMINISTIC_FAIL_CLOSED",
            "contradiction_behavior": "FAIL_CLOSED_NO_CANDIDATE",
            "missing_behavior": "FAIL_CLOSED_NO_CANDIDATE",
            "transition": (
                "EMPTY_FAIL_CLOSED->CANDIDATE_PRESENT_UNRATIFIED->"
                "RATIFIED_SOURCE_KIND->INITIAL_STOCK_ANCHOR"
            ),
            "invalidation": "BINDING_OR_DIGEST_OR_WINDOW_DRIFT_INVALIDATES_CANDIDATE",
            "reconciliation": "VENUE_EQ_WITNESS_ONLY_AFTER_RATIFIED_ANCHOR",
            "epistemic_raw": EPISTEMIC_RAW_DECLARATION,
            "epistemic_candidate": EPISTEMIC_DERIVED,
            "epistemic_ratified": EPISTEMIC_CANONICAL,
            "candidate_is_not_anchor": TRUE_TOKEN,
            "venue_eq_source_authority": FALSE_TOKEN,
            "checkpoint_mints_equity": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "today_observation_boundary_v1.json",
        payload={
            "today_observation_status": boundary.today_observation_status,
            "candidate_status": boundary.candidate_status,
            "ratification_status": boundary.ratification_status,
            "initial_stock_anchor_status": boundary.initial_stock_anchor_status,
            "live_equity_stock_kind_set": KIND_SET_EMPTY,
            "surface_relpath": DECLARATION_SURFACE_RELPATH,
            "expected_filename": DECLARATION_FILENAME,
        },
    )
    _persist_json(
        path=store / "reconstruction_binding_v1.json",
        payload={
            "checkpoint_status": boundary.checkpoint_status,
            "event_stream_binding_status": boundary.event_stream_binding_status,
            "running_equity_reconstruction_status": (boundary.running_equity_reconstruction_status),
            "venue_eq_reconciliation_status": boundary.venue_eq_reconciliation_status,
            "venue_eq_source_authority": FALSE_TOKEN,
            "checkpoint_mints_equity": FALSE_TOKEN,
            "available_for_sizing_status": AVAILABLE_FOR_SIZING_AFTER_EQUITY,
            "risk_capital_status": ROLE_RISK_CAPITAL_REDUCTION_ONLY,
            "derivation_method": DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "forensic_path_productive": "FORBIDDEN",
            "venue_eq_as_source": "FORBIDDEN",
            "checkpoint_mints_equity": "FORBIDDEN",
            "fixture_promote": "FORBIDDEN",
            "legacy_reconstruction": "FORBIDDEN",
            "invented_identities": "FORBIDDEN",
            "invented_values": "FORBIDDEN",
            "self_ratify": "FORBIDDEN",
            "candidate_is_not_anchor": TRUE_TOKEN,
            "empty_live_kind_set": KIND_SET_EMPTY,
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "venue_get_count": "0",
            "venue_post_count": "0",
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_br_pack": CANONICAL_BR_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
            "declaration_surface": DECLARATION_SURFACE_RELPATH,
            "raw_epistemic_class": EPISTEMIC_RAW_DECLARATION,
            "derived_epistemic_class": EPISTEMIC_DERIVED,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return TodayInitialStockContractResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        forensic_path_productive_status=FORENSIC_PATH_PRODUCTIVE_STATUS,
        today_observation_status=boundary.today_observation_status,
        candidate_status=boundary.candidate_status,
        ratification_status=boundary.ratification_status,
        initial_stock_anchor_status=STATUS_ABSENT,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        checkpoint_status=boundary.checkpoint_status,
        event_stream_binding_status=boundary.event_stream_binding_status,
        running_equity_reconstruction_status=boundary.running_equity_reconstruction_status,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        kinds_invented_this_go=FALSE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        earliest_live_critical_path_blocker=boundary.earliest_live_critical_path_blocker,
        next_owner_go_required=boundary.next_owner_go_required,
        venue_get_count="0",
        venue_post_count="0",
        evidence_manifest=str(manifest),
    )


def fixture_today_declaration_payload_v1() -> dict[str, Any]:
    return {
        "declaration_id": "OWNER_TODAY_DECLARATION_001",
        "source_kind": TODAY_SOURCE_KIND,
        "economic_meaning": ECONOMIC_MEANING,
        "account_identity": "BOUND_ACCOUNT_REF",
        "instrument_identity": INSTRUMENT_ACCOUNT_LEVEL,
        "settlement_currency": "USDC",
        "equity_value": "100.00",
        "equity_unit": "USDC",
        "equity_precision": "2",
        "as_of_time": "2026-09-14T18:40:00Z",
        "validity_window_start": "2026-09-14T18:40:00Z",
        "validity_window_end": "2026-09-14T18:40:00Z",
        "provenance_digest": "PENDING",
        "ratification_status": "NOT_RATIFIED",
        "source_type": TODAY_SOURCE_TYPE,
    }


__all__ = [
    "CANONICAL_PACK_RELPATH",
    "DECLARATION_FILENAME",
    "DECLARATION_SURFACE_RELPATH",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "FORENSIC_PATH_PRODUCTIVE_STATUS",
    "HISTORICAL_ARTIFACT_EXISTENCE_CLAIM",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "TODAY_SOURCE_KIND",
    "evaluate_today_declaration_candidate_v1",
    "evaluate_today_initial_stock_source_kind_boundary_v1",
    "execute_live_equity_stock_today_initial_stock_source_kind_v1",
    "fixture_today_declaration_payload_v1",
    "reject_forensic_path_as_productive_authority_v1",
    "scan_today_declaration_surface_v1",
    "semantic_declaration_digest_v1",
]
