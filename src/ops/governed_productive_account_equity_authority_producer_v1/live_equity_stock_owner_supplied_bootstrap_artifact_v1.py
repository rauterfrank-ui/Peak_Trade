"""Owner-supplied forensic bootstrap artifact ingest and fail-closed boundary.

Reuses the sealed BQ BOOTSTRAP_STOCK_ACQUISITION_V1 contract. Ingests raw
bytes without rewriting them. Produces a candidate only after complete
positive validation. Candidate is not an anchor. This GO cannot ratify.
KIND_SET stays empty without a proven and ratified source. Reconstruction,
checkpoint, event-stream, and venue-eq bindings remain unbound until a
ratified anchor exists. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_acquisition_v1 import (
    ADMISSIBLE_SOURCE_CLASS,
    ARTIFACT_FILENAME,
    CANONICAL_INPUT_SURFACE_RELPATH,
    CANONICAL_PACK_RELPATH as CANONICAL_BQ_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BQ_LIVE_BLOCKER,
    NEXT_OWNER_GO_REQUIRED as BQ_NEXT_OWNER_GO,
    OWNER_GO as BQ_OWNER_GO,
    REASON_ARTIFACT_CLASS_FORBIDDEN,
    REASON_CLAIMED_CHECKPOINT_MINT,
    REASON_CLAIMED_FLOW_AS_STOCK,
    REASON_CLAIMED_VENUE_EQ_SOURCE,
    REASON_CONTRADICTORY_FIELD,
    REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED,
    REASON_MALFORMED_FIELD,
    REASON_MISSING_FIELD,
    REASON_PRECEDENCE as BQ_REASON_PRECEDENCE,
    REASON_RATIFICATION_FORBIDDEN,
    REASON_RAW_EVIDENCE_DIGEST_MISMATCH,
    REASON_SOURCE_TYPE_FORBIDDEN,
    REASON_STOCK_PAYLOAD_REJECTED,
    REASON_VALID_CANDIDATE,
    REASON_VENUE_READ_NOT_BOOTSTRAP,
    SCHEMA_CLASS as BQ_SCHEMA_CLASS,
    SOURCE_TYPE_OWNER_FILE,
    VALIDATION_NOT_ACQUIRED,
    evaluate_bootstrap_stock_acquisition_v1,
    evaluate_today_bootstrap_stock_acquisition_boundary_v1,
    fixture_valid_acquisition_candidate_payload_v1,
    reject_claimed_acquisition_authority_mutation_v1,
    scan_owner_supplied_bootstrap_artifact_surface_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_provenance_v1 import (
    BOOTSTRAP_PROVENANCE_FINDING,
    CANONICAL_PACK_RELPATH as CANONICAL_BP_PACK_RELPATH,
    STATUS_ABSENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.fresh_eq_reconciliation_target_contract_v1 import (
    STATUS_UNKNOWN as EQ_RECONCILIATION_STATUS_UNKNOWN,
    TOLERANCE_POLICY_EXACT,
    evaluate_fresh_eq_reconciliation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_checkpoint_stock_value_contract_v1 import (
    DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
    STATUS_FLOW_NOT_STOCK,
    STATUS_NON_SOURCE_NO_BOUND_STOCK,
    evaluate_today_authoritative_derivation_boundary_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BN_PACK_RELPATH,
    LIVE_EQUITY_STOCK_KIND_SET,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
    ROLE_AVAILABLE_CAPITAL_ONLY,
    ROLE_NON_SOURCE,
    ROLE_RECONCILIATION_TARGET_ONLY,
    ROLE_RISK_CAPITAL_REDUCTION_ONLY,
    evaluate_today_live_equity_stock_kind_set_v1,
    ratified_live_equity_stock_kind_set_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_V1"
EXPECTED_ORIGIN_MAIN_SHA = "46cdb84d8ac91846840c5b8589c83c60ae79d164"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_owner_supplied_bootstrap_artifact_wp1/"
    "2026-09-14T170000Z"
)
CLAIMS_FILE = "claims.json"
SCHEMA_CLASS = "OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_INGEST_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
EPISTEMIC_RAW = "RAW_FORENSIC_EVIDENCE"
EPISTEMIC_DERIVED = "ADJUDICATED_CONCLUSION"
VALIDATION_VALID = "VALID"
VALIDATION_INVALID = "INVALID"
VALIDATION_INCOMPLETE = "INCOMPLETE"
VALIDATION_CONTRADICTORY = "CONTRADICTORY"
CANDIDATE_ABSENT = "ABSENT"
CANDIDATE_PRESENT_UNRATIFIED = "PRESENT_UNRATIFIED"
RATIFICATION_NOT_RATIFIED = "NOT_RATIFIED"
RATIFICATION_AUTHORITY_ABSENT = "RATIFICATION_AUTHORITY_ABSENT"
SOURCE_KIND_NONE = NONE_TOKEN
RUNNING_EQUITY_BLOCKED = "BLOCKED_NO_RATIFIED_ANCHOR"
VENUE_EQ_RECONCILIATION_UNBOUND = "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
AVAILABLE_FOR_SIZING_AFTER_EQUITY = "AFTER_EQUITY_SEPARATE"
INSTRUMENT_ACCOUNT_LEVEL = "ACCOUNT_LEVEL"
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "EXTERNAL_FORENSIC_ARTIFACT_REQUIRED"
NEXT_OWNER_GO_REQUIRED = (
    "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_SUPPLY_V1"
)
INGEST_CAPABILITY_DEFINED = "INGEST_VALIDATION_CANDIDATE_RATIFICATION_BOUNDARY_DEFINED"

REASON_JSON_MALFORMED = "JSON_MALFORMED"
REASON_MULTIPLE_ARTIFACTS = "MULTIPLE_ARTIFACTS_CONTRADICTORY"
REASON_IMPLICIT_NORMALIZATION_FORBIDDEN = "IMPLICIT_NORMALIZATION_FORBIDDEN"
REASON_ACCOUNT_BINDING_MISMATCH = "ACCOUNT_BINDING_MISMATCH"
REASON_INSTRUMENT_BINDING_MISMATCH = "INSTRUMENT_BINDING_MISMATCH"
REASON_TIME_BINDING_MISMATCH = "TIME_BINDING_MISMATCH"
REASON_UNKNOWN_SOURCE_KIND = "UNKNOWN_SOURCE_KIND"
REASON_UNKNOWN_BINDING_TOKEN = "UNKNOWN_BINDING_TOKEN_FORBIDDEN"
REASON_BINDING_EXPECTATION_ABSENT = "BINDING_EXPECTATION_ABSENT"
REASON_RATIFICATION_AUTHORITY_ABSENT = "RATIFICATION_AUTHORITY_ABSENT"
REASON_CANDIDATE_IS_NOT_ANCHOR = "CANDIDATE_IS_NOT_ANCHOR"
REASON_KIND_SET_EMPTY_WITHOUT_PROVEN_SOURCE = "KIND_SET_EMPTY_WITHOUT_PROVEN_SOURCE"
REASON_RECONSTRUCTION_BLOCKED = "RECONSTRUCTION_BLOCKED_NO_RATIFIED_ANCHOR"
REASON_VENUE_EQ_CANNOT_BE_SOURCE = "VENUE_EQ_CANNOT_BE_SOURCE"
REASON_CHECKPOINT_CANNOT_MINT = "CHECKPOINT_CANNOT_MINT_EQUITY"

REASON_PRECEDENCE: tuple[str, ...] = BQ_REASON_PRECEDENCE[:-1] + (
    REASON_JSON_MALFORMED,
    REASON_MULTIPLE_ARTIFACTS,
    REASON_IMPLICIT_NORMALIZATION_FORBIDDEN,
    REASON_UNKNOWN_SOURCE_KIND,
    REASON_UNKNOWN_BINDING_TOKEN,
    REASON_ACCOUNT_BINDING_MISMATCH,
    REASON_INSTRUMENT_BINDING_MISMATCH,
    REASON_TIME_BINDING_MISMATCH,
    REASON_BINDING_EXPECTATION_ABSENT,
    REASON_RATIFICATION_AUTHORITY_ABSENT,
    REASON_CANDIDATE_IS_NOT_ANCHOR,
    REASON_KIND_SET_EMPTY_WITHOUT_PROVEN_SOURCE,
    REASON_RECONSTRUCTION_BLOCKED,
    REASON_VENUE_EQ_CANNOT_BE_SOURCE,
    REASON_CHECKPOINT_CANNOT_MINT,
    REASON_VALID_CANDIDATE,
)

INCOMPLETE_REASONS: frozenset[str] = frozenset(
    {
        REASON_MISSING_FIELD,
        REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED,
        REASON_BINDING_EXPECTATION_ABSENT,
    }
)
CONTRADICTORY_REASONS: frozenset[str] = frozenset(
    {
        REASON_CONTRADICTORY_FIELD,
        REASON_RAW_EVIDENCE_DIGEST_MISMATCH,
        REASON_MULTIPLE_ARTIFACTS,
        REASON_ACCOUNT_BINDING_MISMATCH,
        REASON_INSTRUMENT_BINDING_MISMATCH,
        REASON_TIME_BINDING_MISMATCH,
    }
)
INVALID_REASONS: frozenset[str] = frozenset(
    {
        REASON_MALFORMED_FIELD,
        REASON_JSON_MALFORMED,
        REASON_ARTIFACT_CLASS_FORBIDDEN,
        REASON_SOURCE_TYPE_FORBIDDEN,
        REASON_CLAIMED_CHECKPOINT_MINT,
        REASON_CLAIMED_VENUE_EQ_SOURCE,
        REASON_CLAIMED_FLOW_AS_STOCK,
        REASON_VENUE_READ_NOT_BOOTSTRAP,
        REASON_RATIFICATION_FORBIDDEN,
        REASON_IMPLICIT_NORMALIZATION_FORBIDDEN,
        REASON_UNKNOWN_SOURCE_KIND,
        REASON_UNKNOWN_BINDING_TOKEN,
        REASON_VENUE_EQ_CANNOT_BE_SOURCE,
        REASON_CHECKPOINT_CANNOT_MINT,
        REASON_STOCK_PAYLOAD_REJECTED,
    }
)

ALLOWED_CLAIMED_PROOFS: frozenset[str] = frozenset(
    {
        "NEW_CANONICAL_DEFINITION_OWNER_SUPPLIED_ARTIFACT_INGEST",
        "TODAY_ARTIFACT_ABSENT_FAIL_CLOSED",
        "FIXTURE_VALID_CANDIDATE_NOT_ANCHOR",
        "INGEST_CAPABILITY_DEFINED",
        "RATIFICATION_BOUNDARY_DEFINED_NOT_PERFORMED",
        "RECONSTRUCTION_BINDING_DEFINED_UNBOUND",
    }
)
_UNKNOWN_TOKENS: frozenset[str] = frozenset(
    {
        "UNKNOWN",
        "UNCLASSIFIED",
        "UNPROVEN",
        "MISSING",
        "DEFAULT",
        "UNSPECIFIED",
        NONE_TOKEN,
        STATUS_ABSENT,
        "",
    }
)
_NUMERIC_JSON_TYPES = (int, float)
BINDING_FIELDS: tuple[str, ...] = (
    "account_identity",
    "instrument_identity",
    "as_of_time",
    "settlement_currency",
)


class OwnerSuppliedBootstrapArtifactContractError(ValueError):
    """Fail-closed owner-supplied bootstrap artifact contract violation."""


@dataclass(frozen=True)
class ArtifactBindingsV1:
    account_identity: str
    instrument_identity: str
    as_of_time: str
    settlement_currency: str


@dataclass(frozen=True)
class RawIngestRecordV1:
    surface_relpath: str
    surface_status: str
    artifact_present: str
    artifact_path: str
    artifact_count: str
    raw_bytes_preserved: str
    artifact_sha256: str
    parse_status: str
    epistemic_class: str
    overlay_source_digest: str


@dataclass(frozen=True)
class CandidateValidationRecordV1:
    validation_status: str
    bq_candidate_validation_status: str
    reason_code: str
    failures: tuple[str, ...]
    artifact_sha256: str
    provenance_status: str
    source_class: str
    source_type: str
    account_identity: str
    instrument_identity: str
    as_of_time: str
    initial_stock_candidate_status: str
    initial_stock_anchor_status: str
    ratification_status: str
    source_kind_status: str
    live_equity_stock_kind_set: str
    overlay_source_digest: str


@dataclass(frozen=True)
class RatificationBoundaryV1:
    ratification_status: str
    ratification_authority: str
    candidate_promoted_to_anchor: str
    kind_set_membership_granted: str
    next_owner_go_required: str


@dataclass(frozen=True)
class ReconstructionBindingV1:
    checkpoint_status: str
    event_stream_binding_status: str
    running_equity_reconstruction_status: str
    venue_eq_reconciliation_status: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    available_for_sizing_status: str
    risk_capital_status: str
    derivation_method: str


@dataclass(frozen=True)
class OwnerSuppliedArtifactBoundaryV1:
    ingest_capability_status: str
    forensic_artifact_present: str
    raw_evidence_preserved: str
    artifact_sha256: str
    provenance_status: str
    candidate_validation_status: str
    initial_stock_candidate_status: str
    initial_stock_anchor_status: str
    source_kind_status: str
    live_equity_stock_kind_set: str
    ratification_status: str
    checkpoint_status: str
    event_stream_binding_status: str
    running_equity_reconstruction_status: str
    venue_eq_reconciliation_status: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str


@dataclass(frozen=True)
class OwnerSuppliedArtifactContractResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    forensic_artifact_present: str
    raw_evidence_preserved: str
    artifact_sha256: str
    provenance_status: str
    candidate_validation_status: str
    initial_stock_candidate_status: str
    initial_stock_anchor_status: str
    source_kind_status: str
    live_equity_stock_kind_set: str
    ratification_status: str
    checkpoint_status: str
    event_stream_binding_status: str
    running_equity_reconstruction_status: str
    venue_eq_reconciliation_status: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    kinds_invented_this_go: str
    legacy_semantics_reconstructed: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str
    venue_get_count: str
    venue_post_count: str
    gate_a_executed: str
    gate_b_executed: str
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
        raise OwnerSuppliedBootstrapArtifactContractError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise OwnerSuppliedBootstrapArtifactContractError(f"{field}_DRIFT:{actual}")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_text(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise OwnerSuppliedBootstrapArtifactContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise OwnerSuppliedBootstrapArtifactContractError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise OwnerSuppliedBootstrapArtifactContractError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise OwnerSuppliedBootstrapArtifactContractError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise OwnerSuppliedBootstrapArtifactContractError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise OwnerSuppliedBootstrapArtifactContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise OwnerSuppliedBootstrapArtifactContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise OwnerSuppliedBootstrapArtifactContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise OwnerSuppliedBootstrapArtifactContractError("C17_CREATED_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise OwnerSuppliedBootstrapArtifactContractError("BN_KIND_SET_NOT_EMPTY")
    if BQ_SCHEMA_CLASS != "BOOTSTRAP_STOCK_ACQUISITION_V1":
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_SCHEMA_DRIFT")
    if BQ_NEXT_OWNER_GO != OWNER_GO:
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_NEXT_OWNER_GO_DRIFT")
    if BQ_LIVE_BLOCKER != EARLIEST_LIVE_CRITICAL_PATH_BLOCKER:
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_LIVE_BLOCKER_DRIFT")
    if BQ_OWNER_GO != "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION_V1":
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_OWNER_GO_DRIFT")
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )
    reject_claimed_acquisition_authority_mutation_v1(
        claimed_proof="ACQUISITION_CAPABILITY_DEFINED",
        artifact_id=ADMISSIBLE_SOURCE_CLASS,
    )
    assert_checkpoint_cannot_mint_equity_v1(
        equity_mint_status=EQUITY_MINT_STATUS_NOT_MINTED,
        running_equity_value_state=RUNNING_EQUITY_VALUE_STATE_ABSENT,
        claimed_equity_stock_value=STATUS_ABSENT,
        observation_vs_authority_class=OBSERVATION_VS_AUTHORITY_CLASS,
    )


def reject_claimed_artifact_authority_mutation_v1(*, claimed_proof: str, artifact_id: str) -> None:
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
        "CHECKPOINT_MINT_EQUITY",
        "BOOTSTRAP_FROM_VENUE_EQ",
        "BOOTSTRAP_FROM_CHECKPOINT",
        "BOOTSTRAP_FROM_FLOW",
        "RELABEL_LEGACY_AS_STOCK",
        "MINT_INITIAL_STOCK",
        "RATIFY_KIND_MEMBERSHIP",
        "PROMOTE_CANDIDATE_TO_ANCHOR",
        "VENUE_GET_AS_BOOTSTRAP",
        "INTERPRET_MISSING_AS_ZERO",
        "INVENT_OWNER_ARTIFACT",
        "NORMALIZE_UNKNOWN_TOKEN",
        "COALESCE_MISSING_FIELD",
    }
    if claimed_proof in forbidden:
        raise OwnerSuppliedBootstrapArtifactContractError(
            f"ARTIFACT_INGEST_CANNOT_{claimed_proof}:{artifact_id}"
        )
    if claimed_proof not in ALLOWED_CLAIMED_PROOFS:
        raise OwnerSuppliedBootstrapArtifactContractError(
            f"ARTIFACT_PROOF_UNKNOWN:{claimed_proof}:{artifact_id}"
        )


def reason_precedence_index_v1(reason_code: str) -> int:
    try:
        return REASON_PRECEDENCE.index(reason_code)
    except ValueError as exc:
        raise OwnerSuppliedBootstrapArtifactContractError(
            f"REASON_CODE_NOT_IN_PRECEDENCE:{reason_code}"
        ) from exc


def classify_validation_status_v1(reason_code: str) -> str:
    if reason_code == REASON_VALID_CANDIDATE:
        return VALIDATION_VALID
    if reason_code in CONTRADICTORY_REASONS:
        return VALIDATION_CONTRADICTORY
    if reason_code in INCOMPLETE_REASONS:
        return VALIDATION_INCOMPLETE
    if reason_code in INVALID_REASONS:
        return VALIDATION_INVALID
    raise OwnerSuppliedBootstrapArtifactContractError(f"VALIDATION_STATUS_UNMAPPED:{reason_code}")


def _inner_raw_bytes(payload: Mapping[str, Any], *, companion_raw: bytes | None) -> bytes | None:
    raw_evidence = payload.get("raw_evidence")
    if isinstance(raw_evidence, str):
        return raw_evidence.encode("utf-8")
    if raw_evidence is not None:
        return None
    if companion_raw is not None:
        return companion_raw
    return None


def detect_forbidden_implicit_normalization_v1(payload: Mapping[str, Any]) -> tuple[str, ...]:
    failures: list[str] = []
    for name in (
        "equity_value",
        "equity_precision",
        "account_identity",
        "instrument_identity",
        "as_of_time",
        "artifact_id",
        "raw_evidence_digest",
    ):
        raw = payload.get(name, None)
        if isinstance(raw, bool) or isinstance(raw, _NUMERIC_JSON_TYPES):
            failures.append(f"IMPLICIT_COERCE_FORBIDDEN:{name}")
        if isinstance(raw, str) and raw in _UNKNOWN_TOKENS and name in BINDING_FIELDS:
            failures.append(f"UNKNOWN_TOKEN_UNNORMALIZED:{name}")
    return tuple(failures)


def parse_owner_supplied_artifact_json_v1(
    raw_bytes: bytes,
) -> tuple[dict[str, Any] | None, str, tuple[str, ...]]:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None, VALIDATION_INVALID, ("JSON_NOT_UTF8",)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, VALIDATION_INVALID, ("JSON_MALFORMED",)
    if not isinstance(payload, dict):
        return None, VALIDATION_INVALID, ("JSON_NOT_OBJECT",)
    return payload, "PARSED_OVERLAY_ONLY", ()


def ingest_owner_supplied_bootstrap_artifact_v1(
    *,
    repo_root: Path,
    surface_relpath: str = CANONICAL_INPUT_SURFACE_RELPATH,
) -> RawIngestRecordV1:
    _assert_standing_pins()
    scan = scan_owner_supplied_bootstrap_artifact_surface_v1(
        repo_root=repo_root,
        surface_relpath=surface_relpath,
    )
    if scan.artifact_present != TRUE_TOKEN:
        return RawIngestRecordV1(
            surface_relpath=scan.surface_relpath,
            surface_status=scan.surface_status,
            artifact_present=FALSE_TOKEN,
            artifact_path="",
            artifact_count=scan.artifact_count,
            raw_bytes_preserved=TRUE_TOKEN,
            artifact_sha256="",
            parse_status=VALIDATION_INCOMPLETE,
            epistemic_class=EPISTEMIC_RAW,
            overlay_source_digest="",
        )
    surface = Path(repo_root) / surface_relpath
    artifacts = sorted(
        path for path in surface.iterdir() if path.is_file() and path.name.endswith(".json")
    )
    first = artifacts[0]
    raw_bytes = first.read_bytes()
    overlay_digest = _sha256_bytes(raw_bytes)
    parse_status = "PARSED_OVERLAY_ONLY"
    parsed, overlay_status, failures = parse_owner_supplied_artifact_json_v1(raw_bytes)
    if parsed is None:
        parse_status = VALIDATION_INVALID
    elif failures:
        parse_status = overlay_status
    return RawIngestRecordV1(
        surface_relpath=scan.surface_relpath,
        surface_status=scan.surface_status,
        artifact_present=TRUE_TOKEN,
        artifact_path=str(first.relative_to(repo_root)),
        artifact_count=str(len(artifacts)),
        raw_bytes_preserved=TRUE_TOKEN,
        artifact_sha256=overlay_digest,
        parse_status=parse_status,
        epistemic_class=EPISTEMIC_RAW,
        overlay_source_digest=overlay_digest,
    )


def _evaluate_candidate_once_v1(
    *,
    repo_root: Path,
    surface_relpath: str,
    expected_bindings: ArtifactBindingsV1 | None,
    claimed_proof: str,
) -> CandidateValidationRecordV1:
    _assert_standing_pins()
    reject_claimed_artifact_authority_mutation_v1(
        claimed_proof=claimed_proof,
        artifact_id="OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT",
    )
    ingest = ingest_owner_supplied_bootstrap_artifact_v1(
        repo_root=repo_root,
        surface_relpath=surface_relpath,
    )
    reasons: list[str] = []
    failures: list[str] = []
    if ingest.artifact_present != TRUE_TOKEN:
        reasons.append(REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED)
        failures.append("RAW_OWNER_ARTIFACT_ABSENT")
        reason_code = min(reasons, key=reason_precedence_index_v1)
        return CandidateValidationRecordV1(
            validation_status=classify_validation_status_v1(reason_code),
            bq_candidate_validation_status=VALIDATION_NOT_ACQUIRED,
            reason_code=reason_code,
            failures=tuple(failures),
            artifact_sha256="",
            provenance_status=STATUS_ABSENT,
            source_class=NONE_TOKEN,
            source_type=NONE_TOKEN,
            account_identity="",
            instrument_identity="",
            as_of_time="",
            initial_stock_candidate_status=CANDIDATE_ABSENT,
            initial_stock_anchor_status=STATUS_ABSENT,
            ratification_status=RATIFICATION_NOT_RATIFIED,
            source_kind_status=SOURCE_KIND_NONE,
            live_equity_stock_kind_set=KIND_SET_EMPTY,
            overlay_source_digest="",
        )
    if ingest.artifact_count not in {"1"}:
        reasons.append(REASON_MULTIPLE_ARTIFACTS)
        failures.append("MULTIPLE_JSON_ARTIFACTS")
    artifact_path = Path(repo_root) / ingest.artifact_path
    file_bytes = artifact_path.read_bytes()
    if _sha256_bytes(file_bytes) != ingest.artifact_sha256:
        reasons.append(REASON_RAW_EVIDENCE_DIGEST_MISMATCH)
        failures.append("INGEST_SHA256_DRIFT")
    parsed, parse_status, parse_failures = parse_owner_supplied_artifact_json_v1(file_bytes)
    if parsed is None:
        reasons.append(REASON_JSON_MALFORMED)
        failures.extend(parse_failures)
        reason_code = min(list(dict.fromkeys(reasons)), key=reason_precedence_index_v1)
        return CandidateValidationRecordV1(
            validation_status=classify_validation_status_v1(reason_code),
            bq_candidate_validation_status=VALIDATION_NOT_ACQUIRED,
            reason_code=reason_code,
            failures=tuple(dict.fromkeys(failures)),
            artifact_sha256=ingest.artifact_sha256,
            provenance_status="DIGEST_ONLY_PARSE_FAILED",
            source_class=NONE_TOKEN,
            source_type=NONE_TOKEN,
            account_identity="",
            instrument_identity="",
            as_of_time="",
            initial_stock_candidate_status=CANDIDATE_ABSENT,
            initial_stock_anchor_status=STATUS_ABSENT,
            ratification_status=RATIFICATION_NOT_RATIFIED,
            source_kind_status=SOURCE_KIND_NONE,
            live_equity_stock_kind_set=KIND_SET_EMPTY,
            overlay_source_digest=ingest.overlay_source_digest,
        )
    del parse_status
    norm_failures = detect_forbidden_implicit_normalization_v1(parsed)
    if any(item.startswith("IMPLICIT_COERCE_FORBIDDEN:") for item in norm_failures):
        reasons.append(REASON_IMPLICIT_NORMALIZATION_FORBIDDEN)
        failures.extend(norm_failures)
    if any(item.startswith("UNKNOWN_TOKEN_UNNORMALIZED:") for item in norm_failures):
        reasons.append(REASON_UNKNOWN_BINDING_TOKEN)
        failures.extend(norm_failures)
    companion = None
    companion_path = artifact_path.with_suffix(artifact_path.suffix + ".raw")
    if companion_path.is_file():
        companion = companion_path.read_bytes()
    inner_raw = _inner_raw_bytes(parsed, companion_raw=companion)
    acquisition = evaluate_bootstrap_stock_acquisition_v1(
        parsed,
        claimed_proof="FIXTURE_VALID_ACQUISITION_CANDIDATE_ONLY",
        raw_bytes=inner_raw,
    )
    if acquisition.reason_code != REASON_VALID_CANDIDATE:
        reasons.append(acquisition.reason_code)
        failures.extend(acquisition.failures)
    source_type = str(parsed.get("source_type") or "")
    artifact_class = str(parsed.get("artifact_class") or "")
    if source_type and source_type not in {SOURCE_TYPE_OWNER_FILE, ""}:
        if source_type in {"VENUE_EQ", "eq", "VENUE_GET", "CHECKPOINT", "FLOW"}:
            reasons.append(REASON_UNKNOWN_SOURCE_KIND)
            failures.append(f"UNKNOWN_OR_FORBIDDEN_SOURCE:{source_type}")
        elif source_type != SOURCE_TYPE_OWNER_FILE:
            reasons.append(REASON_UNKNOWN_SOURCE_KIND)
            failures.append(f"UNKNOWN_SOURCE_KIND:{source_type}")
    if artifact_class and artifact_class not in {ADMISSIBLE_SOURCE_CLASS, ""}:
        if artifact_class not in {
            "VENUE_EQ",
            "eq",
            "CHECKPOINT",
            "CHECKPOINT_MINT",
            "FLOW",
            "DELTA",
            "CLASSIFIED_EVENT_STREAM",
        }:
            reasons.append(REASON_UNKNOWN_SOURCE_KIND)
            failures.append(f"UNKNOWN_ARTIFACT_CLASS:{artifact_class}")
    account = str(parsed.get("account_identity") or "")
    instrument = parsed.get("instrument_identity", INSTRUMENT_ACCOUNT_LEVEL)
    instrument_text = instrument if isinstance(instrument, str) else ""
    as_of = str(parsed.get("as_of_time") or "")
    currency = str(parsed.get("settlement_currency") or "")
    if expected_bindings is None:
        reasons.append(REASON_BINDING_EXPECTATION_ABSENT)
        failures.append("EXPECTED_BINDINGS_NOT_SUPPLIED")
    else:
        if account != expected_bindings.account_identity:
            reasons.append(REASON_ACCOUNT_BINDING_MISMATCH)
            failures.append("ACCOUNT_IDENTITY_MISMATCH")
        if instrument_text != expected_bindings.instrument_identity:
            reasons.append(REASON_INSTRUMENT_BINDING_MISMATCH)
            failures.append("INSTRUMENT_IDENTITY_MISMATCH")
        if as_of != expected_bindings.as_of_time:
            reasons.append(REASON_TIME_BINDING_MISMATCH)
            failures.append("AS_OF_TIME_MISMATCH")
        if currency and currency != expected_bindings.settlement_currency:
            reasons.append(REASON_ACCOUNT_BINDING_MISMATCH)
            failures.append("SETTLEMENT_CURRENCY_MISMATCH")
    unique_reasons = list(dict.fromkeys(reasons))
    if not unique_reasons:
        reason_code = REASON_VALID_CANDIDATE
        candidate_status = CANDIDATE_PRESENT_UNRATIFIED
    else:
        reason_code = min(unique_reasons, key=reason_precedence_index_v1)
        candidate_status = CANDIDATE_ABSENT
    members = ratified_live_equity_stock_kind_set_v1(evaluate_today_live_equity_stock_kind_set_v1())
    if members:
        raise OwnerSuppliedBootstrapArtifactContractError(
            f"KIND_INVENTED_OR_UNPROVEN_MEMBER:{','.join(members)}"
        )
    return CandidateValidationRecordV1(
        validation_status=classify_validation_status_v1(reason_code),
        bq_candidate_validation_status=acquisition.candidate_validation_status,
        reason_code=reason_code,
        failures=tuple(dict.fromkeys(failures)),
        artifact_sha256=ingest.artifact_sha256,
        provenance_status="RAW_DIGEST_BOUND" if inner_raw is not None else STATUS_ABSENT,
        source_class=artifact_class or NONE_TOKEN,
        source_type=source_type or NONE_TOKEN,
        account_identity=account,
        instrument_identity=instrument_text or NONE_TOKEN,
        as_of_time=as_of,
        initial_stock_candidate_status=candidate_status,
        initial_stock_anchor_status=STATUS_ABSENT,
        ratification_status=RATIFICATION_NOT_RATIFIED,
        source_kind_status=SOURCE_KIND_NONE,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        overlay_source_digest=ingest.overlay_source_digest,
    )


def evaluate_owner_supplied_bootstrap_candidate_v1(
    *,
    repo_root: Path,
    surface_relpath: str = CANONICAL_INPUT_SURFACE_RELPATH,
    expected_bindings: ArtifactBindingsV1 | None = None,
    claimed_proof: str = "FIXTURE_VALID_CANDIDATE_NOT_ANCHOR",
) -> CandidateValidationRecordV1:
    first = _evaluate_candidate_once_v1(
        repo_root=repo_root,
        surface_relpath=surface_relpath,
        expected_bindings=expected_bindings,
        claimed_proof=claimed_proof,
    )
    second = _evaluate_candidate_once_v1(
        repo_root=repo_root,
        surface_relpath=surface_relpath,
        expected_bindings=expected_bindings,
        claimed_proof=claimed_proof,
    )
    if first != second:
        raise OwnerSuppliedBootstrapArtifactContractError("CANDIDATE_EVALUATION_NOT_DETERMINISTIC")
    return first


def evaluate_ratification_boundary_v1(
    candidate: CandidateValidationRecordV1,
) -> RatificationBoundaryV1:
    _assert_standing_pins()
    reject_claimed_artifact_authority_mutation_v1(
        claimed_proof="RATIFICATION_BOUNDARY_DEFINED_NOT_PERFORMED",
        artifact_id=candidate.artifact_sha256 or "NO_CANDIDATE",
    )
    if candidate.initial_stock_anchor_status != STATUS_ABSENT:
        raise OwnerSuppliedBootstrapArtifactContractError("CANDIDATE_PROMOTED_TO_ANCHOR")
    if candidate.ratification_status != RATIFICATION_NOT_RATIFIED:
        raise OwnerSuppliedBootstrapArtifactContractError("INGEST_CLAIMED_RATIFICATION")
    first = RatificationBoundaryV1(
        ratification_status=RATIFICATION_AUTHORITY_ABSENT,
        ratification_authority=NONE_TOKEN,
        candidate_promoted_to_anchor=FALSE_TOKEN,
        kind_set_membership_granted=FALSE_TOKEN,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    second = RatificationBoundaryV1(
        ratification_status=RATIFICATION_AUTHORITY_ABSENT,
        ratification_authority=NONE_TOKEN,
        candidate_promoted_to_anchor=FALSE_TOKEN,
        kind_set_membership_granted=FALSE_TOKEN,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    if first != second:
        raise OwnerSuppliedBootstrapArtifactContractError("RATIFICATION_BOUNDARY_NOT_DETERMINISTIC")
    return first


def derive_kind_set_from_proven_source_v1(
    candidate: CandidateValidationRecordV1,
    ratification: RatificationBoundaryV1,
) -> str:
    _assert_standing_pins()
    if ratification.ratification_status != "RATIFIED":
        return KIND_SET_EMPTY
    if candidate.source_class != ADMISSIBLE_SOURCE_CLASS:
        return KIND_SET_EMPTY
    if candidate.validation_status != VALIDATION_VALID:
        return KIND_SET_EMPTY
    raise OwnerSuppliedBootstrapArtifactContractError("KIND_SET_CANNOT_BE_MINTED_BY_THIS_GO")


def bind_option_d_reconstruction_v1(
    candidate: CandidateValidationRecordV1,
    ratification: RatificationBoundaryV1,
) -> ReconstructionBindingV1:
    _assert_standing_pins()
    reject_claimed_artifact_authority_mutation_v1(
        claimed_proof="RECONSTRUCTION_BINDING_DEFINED_UNBOUND",
        artifact_id=candidate.artifact_sha256 or "NO_CANDIDATE",
    )
    if ratification.candidate_promoted_to_anchor == TRUE_TOKEN:
        raise OwnerSuppliedBootstrapArtifactContractError(
            "RECONSTRUCTION_REQUIRES_SEPARATE_RATIFICATION"
        )
    if candidate.initial_stock_anchor_status != STATUS_ABSENT:
        raise OwnerSuppliedBootstrapArtifactContractError("ANCHOR_PRESENT_WITHOUT_RATIFICATION_GO")
    derivation = evaluate_today_authoritative_derivation_boundary_v1()
    if derivation.derivation_method != DERIVATION_OPTION_D_PRIOR_PLUS_STREAM:
        raise OwnerSuppliedBootstrapArtifactContractError("BO_DERIVATION_METHOD_DRIFT")
    if derivation.prior_stock_anchor_status != STATUS_ABSENT:
        raise OwnerSuppliedBootstrapArtifactContractError("BO_PRIOR_STOCK_NOT_ABSENT")
    if derivation.prior_checkpoint_status != STATUS_NON_SOURCE_NO_BOUND_STOCK:
        raise OwnerSuppliedBootstrapArtifactContractError("BO_CHECKPOINT_NOT_NON_SOURCE")
    if derivation.event_stream_boundary_status != STATUS_FLOW_NOT_STOCK:
        raise OwnerSuppliedBootstrapArtifactContractError("BO_EVENT_STREAM_NOT_FLOW")
    if derivation.checkpoint_mints_equity != FALSE_TOKEN:
        raise OwnerSuppliedBootstrapArtifactContractError("BO_CHECKPOINT_MINTS_EQUITY")
    if derivation.venue_eq_source_authority != FALSE_TOKEN:
        raise OwnerSuppliedBootstrapArtifactContractError("BO_VENUE_EQ_SOURCE_AUTHORITY")
    eq_status = evaluate_fresh_eq_reconciliation_v1(
        reconstructed_equity_value_state=STATUS_ABSENT,
        reconstructed_equity_value=STATUS_ABSENT,
        venue_eq_value_state=STATUS_ABSENT,
        venue_eq_value=STATUS_ABSENT,
        tolerance_policy=TOLERANCE_POLICY_EXACT,
    )
    if eq_status != EQ_RECONCILIATION_STATUS_UNKNOWN:
        raise OwnerSuppliedBootstrapArtifactContractError(
            f"VENUE_EQ_RECONCILIATION_NOT_UNBOUND:{eq_status}"
        )
    first = ReconstructionBindingV1(
        checkpoint_status=derivation.prior_checkpoint_status,
        event_stream_binding_status=derivation.event_stream_boundary_status,
        running_equity_reconstruction_status=RUNNING_EQUITY_BLOCKED,
        venue_eq_reconciliation_status=VENUE_EQ_RECONCILIATION_UNBOUND,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        available_for_sizing_status=AVAILABLE_FOR_SIZING_AFTER_EQUITY,
        risk_capital_status=ROLE_RISK_CAPITAL_REDUCTION_ONLY,
        derivation_method=derivation.derivation_method,
    )
    second = ReconstructionBindingV1(
        checkpoint_status=derivation.prior_checkpoint_status,
        event_stream_binding_status=derivation.event_stream_boundary_status,
        running_equity_reconstruction_status=RUNNING_EQUITY_BLOCKED,
        venue_eq_reconciliation_status=VENUE_EQ_RECONCILIATION_UNBOUND,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        available_for_sizing_status=AVAILABLE_FOR_SIZING_AFTER_EQUITY,
        risk_capital_status=ROLE_RISK_CAPITAL_REDUCTION_ONLY,
        derivation_method=derivation.derivation_method,
    )
    if first != second:
        raise OwnerSuppliedBootstrapArtifactContractError(
            "RECONSTRUCTION_BINDING_NOT_DETERMINISTIC"
        )
    if DIMENSION_EQUITY_STOCK == DIMENSION_AVAILABLE_FOR_SIZING:
        raise OwnerSuppliedBootstrapArtifactContractError("SIZING_COLLAPSED_INTO_EQUITY")
    if DIMENSION_P01_RISK_CAPITAL_REDUCTION == DIMENSION_EQUITY_STOCK:
        raise OwnerSuppliedBootstrapArtifactContractError("P01_COLLAPSED_INTO_EQUITY")
    return first


def evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1(
    *,
    repo_root: Path,
) -> OwnerSuppliedArtifactBoundaryV1:
    _assert_standing_pins()
    bq_boundary = evaluate_today_bootstrap_stock_acquisition_boundary_v1(repo_root=repo_root)
    if bq_boundary.initial_stock_anchor_status != STATUS_ABSENT:
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_INITIAL_STOCK_NOT_ABSENT")
    if bq_boundary.ratification_performed != FALSE_TOKEN:
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_RATIFICATION_NOT_FALSE")
    candidate = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=repo_root,
        claimed_proof="TODAY_ARTIFACT_ABSENT_FAIL_CLOSED",
        expected_bindings=None,
    )
    ratification = evaluate_ratification_boundary_v1(candidate)
    reconstruction = bind_option_d_reconstruction_v1(candidate, ratification)
    kind_set = derive_kind_set_from_proven_source_v1(candidate, ratification)
    first = OwnerSuppliedArtifactBoundaryV1(
        ingest_capability_status=INGEST_CAPABILITY_DEFINED,
        forensic_artifact_present=FALSE_TOKEN
        if candidate.reason_code == REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED
        else TRUE_TOKEN,
        raw_evidence_preserved=TRUE_TOKEN,
        artifact_sha256=candidate.artifact_sha256,
        provenance_status=candidate.provenance_status,
        candidate_validation_status=candidate.validation_status,
        initial_stock_candidate_status=candidate.initial_stock_candidate_status,
        initial_stock_anchor_status=STATUS_ABSENT,
        source_kind_status=candidate.source_kind_status,
        live_equity_stock_kind_set=kind_set,
        ratification_status=ratification.ratification_status,
        checkpoint_status=reconstruction.checkpoint_status,
        event_stream_binding_status=reconstruction.event_stream_binding_status,
        running_equity_reconstruction_status=reconstruction.running_equity_reconstruction_status,
        venue_eq_reconciliation_status=reconstruction.venue_eq_reconciliation_status,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    second = OwnerSuppliedArtifactBoundaryV1(
        ingest_capability_status=INGEST_CAPABILITY_DEFINED,
        forensic_artifact_present=FALSE_TOKEN
        if candidate.reason_code == REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED
        else TRUE_TOKEN,
        raw_evidence_preserved=TRUE_TOKEN,
        artifact_sha256=candidate.artifact_sha256,
        provenance_status=candidate.provenance_status,
        candidate_validation_status=candidate.validation_status,
        initial_stock_candidate_status=candidate.initial_stock_candidate_status,
        initial_stock_anchor_status=STATUS_ABSENT,
        source_kind_status=candidate.source_kind_status,
        live_equity_stock_kind_set=kind_set,
        ratification_status=ratification.ratification_status,
        checkpoint_status=reconstruction.checkpoint_status,
        event_stream_binding_status=reconstruction.event_stream_binding_status,
        running_equity_reconstruction_status=reconstruction.running_equity_reconstruction_status,
        venue_eq_reconciliation_status=reconstruction.venue_eq_reconciliation_status,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    if first != second:
        raise OwnerSuppliedBootstrapArtifactContractError("TODAY_BOUNDARY_NOT_DETERMINISTIC")
    return first


def execute_live_equity_stock_owner_supplied_bootstrap_artifact_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bq_pack: Path,
    repo_root: Path,
    evidence_root: Path,
    persist_as_of: str,
) -> OwnerSuppliedArtifactContractResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise OwnerSuppliedBootstrapArtifactContractError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise OwnerSuppliedBootstrapArtifactContractError("ORIGIN_MAIN_SHA_MISMATCH")
    bq_pack = Path(sealed_bq_pack)
    try:
        manifest_rc = verify_manifest_sha256_v1(store_root=bq_pack)
    except Exception as exc:
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_MANIFEST_VERIFY_FAILED") from exc
    if manifest_rc != 0:
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_MANIFEST_VERIFY_FAILED")
    claims_path = bq_pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_CLAIMS_MISSING")
    try:
        bq_claims = _load_json_object(path=claims_path)
    except json.JSONDecodeError as exc:
        raise OwnerSuppliedBootstrapArtifactContractError("BQ_CLAIMS_MALFORMED") from exc
    _require_token(field="KIND_SET", payload=bq_claims, expected=KIND_SET_EMPTY)
    _require_token(field="LIVE_EQUITY_STOCK_KIND_SET", payload=bq_claims, expected=KIND_SET_EMPTY)
    _require_token(field="GATE_A_EXECUTED", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bq_claims, expected="0")
    _require_token(field="VENUE_POST_COUNT", payload=bq_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="KINDS_INVENTED_THIS_GO", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="CHECKPOINT_MINTS_EQUITY", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="INITIAL_STOCK_ANCHOR_STATUS", payload=bq_claims, expected=STATUS_ABSENT)
    _require_token(field="RATIFICATION_PERFORMED", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="FORENSIC_ARTIFACT_PRESENT", payload=bq_claims, expected=FALSE_TOKEN)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=bq_claims, expected=OWNER_GO)
    _require_token(
        field="EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
        payload=bq_claims,
        expected=BQ_LIVE_BLOCKER,
    )
    _require_token(field="F12_DECISION", payload=bq_claims, expected=DECISION_REMAIN_UNKNOWN)
    reject_claimed_artifact_authority_mutation_v1(
        claimed_proof="NEW_CANONICAL_DEFINITION_OWNER_SUPPLIED_ARTIFACT_INGEST",
        artifact_id=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    )
    reject_claimed_artifact_authority_mutation_v1(
        claimed_proof="TODAY_ARTIFACT_ABSENT_FAIL_CLOSED",
        artifact_id="TODAY_PRODUCTIVE_INGEST",
    )
    reject_claimed_artifact_authority_mutation_v1(
        claimed_proof="INGEST_CAPABILITY_DEFINED",
        artifact_id=ADMISSIBLE_SOURCE_CLASS,
    )
    ingest = ingest_owner_supplied_bootstrap_artifact_v1(repo_root=repo_root)
    boundary = evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1(repo_root=repo_root)
    candidate = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=repo_root,
        claimed_proof="TODAY_ARTIFACT_ABSENT_FAIL_CLOSED",
        expected_bindings=None,
    )
    ratification = evaluate_ratification_boundary_v1(candidate)
    reconstruction = bind_option_d_reconstruction_v1(candidate, ratification)
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
        "SEALED_BQ_PACK": CANONICAL_BQ_PACK_RELPATH,
        "SEALED_BP_PACK": CANONICAL_BP_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "BQ_CONTRACT_REUSED": TRUE_TOKEN,
        "BP_CONTRACT_REUSED": TRUE_TOKEN,
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
        "ACQUISITION_CONTRACT_REUSED": TRUE_TOKEN,
        "INGEST_CAPABILITY_STATUS": boundary.ingest_capability_status,
        "BOOTSTRAP_PROVENANCE_FINDING": BOOTSTRAP_PROVENANCE_FINDING,
        "ADMISSIBLE_BOOTSTRAP_SOURCE_CLASS": ADMISSIBLE_SOURCE_CLASS,
        "FORENSIC_ARTIFACT_PRESENT": boundary.forensic_artifact_present,
        "FORENSIC_ARTIFACT_CLASS": ingest.epistemic_class
        if ingest.artifact_present == TRUE_TOKEN
        else NONE_TOKEN,
        "RAW_EVIDENCE_PRESERVED": boundary.raw_evidence_preserved,
        "ARTIFACT_SHA256": boundary.artifact_sha256 or NONE_TOKEN,
        "PROVENANCE_STATUS": boundary.provenance_status,
        "CANDIDATE_VALIDATION_STATUS": boundary.candidate_validation_status,
        "INITIAL_STOCK_CANDIDATE_STATUS": boundary.initial_stock_candidate_status,
        "INITIAL_STOCK_ANCHOR_STATUS": boundary.initial_stock_anchor_status,
        "SOURCE_KIND_STATUS": boundary.source_kind_status,
        "RATIFICATION_STATUS": boundary.ratification_status,
        "RATIFICATION_PERFORMED": FALSE_TOKEN,
        "CHECKPOINT_STATUS": boundary.checkpoint_status,
        "EVENT_STREAM_BINDING_STATUS": boundary.event_stream_binding_status,
        "RUNNING_EQUITY_RECONSTRUCTION_STATUS": boundary.running_equity_reconstruction_status,
        "VENUE_EQ_RECONCILIATION_STATUS": boundary.venue_eq_reconciliation_status,
        "AVAILABLE_FOR_SIZING_STATUS": reconstruction.available_for_sizing_status,
        "RISK_CAPITAL_STATUS": reconstruction.risk_capital_status,
        "AUTHORITATIVE_DERIVATION_METHOD": DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        "LIVE_EQUITY_STOCK_KIND_SET_IDENTITY": LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
        "LIVE_EQUITY_STOCK_KIND_SET": KIND_SET_EMPTY,
        "LIVE_EQUITY_STOCK_KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_MEMBERS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        "BQ_LIVE_BLOCKER_CONSUMED": BQ_LIVE_BLOCKER,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "NEW_STOCK_KIND_CANDIDATE": NONE_TOKEN,
        "MEMBERSHIP_OWNER_RATIFICATION_REQUIRED": FALSE_TOKEN,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "VENUE_EQ_ROLE": ROLE_RECONCILIATION_TARGET_ONLY,
        "GOVERNED_CHECKPOINT_ROLE": ROLE_NON_SOURCE,
        "U04_ROLE": ROLE_AVAILABLE_CAPITAL_ONLY,
        "P01_ROLE": ROLE_RISK_CAPITAL_REDUCTION_ONLY,
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
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "BQ_MANIFEST_VERIFY_RC": "0",
        "EPISTEMIC_RAW_CLASS": EPISTEMIC_RAW,
        "EPISTEMIC_DERIVED_CLASS": EPISTEMIC_DERIVED,
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "ingest_result_v1.json",
        payload={
            "schema_class": SCHEMA_CLASS,
            "contract_version": CONTRACT_VERSION,
            "bq_schema_class": BQ_SCHEMA_CLASS,
            "surface_relpath": ingest.surface_relpath,
            "surface_status": ingest.surface_status,
            "artifact_present": ingest.artifact_present,
            "artifact_path": ingest.artifact_path,
            "artifact_count": ingest.artifact_count,
            "raw_bytes_preserved": ingest.raw_bytes_preserved,
            "artifact_sha256": ingest.artifact_sha256 or NONE_TOKEN,
            "parse_status": ingest.parse_status,
            "epistemic_class": ingest.epistemic_class,
            "expected_artifact_filename": ARTIFACT_FILENAME,
        },
    )
    _persist_json(
        path=store / "candidate_boundary_v1.json",
        payload={
            "validation_status": candidate.validation_status,
            "bq_candidate_validation_status": candidate.bq_candidate_validation_status,
            "reason_code": candidate.reason_code,
            "failures": list(candidate.failures),
            "initial_stock_candidate_status": candidate.initial_stock_candidate_status,
            "initial_stock_anchor_status": candidate.initial_stock_anchor_status,
            "ratification_status": candidate.ratification_status,
            "source_kind_status": candidate.source_kind_status,
            "live_equity_stock_kind_set": candidate.live_equity_stock_kind_set,
        },
    )
    _persist_json(
        path=store / "ratification_boundary_v1.json",
        payload={
            "ratification_status": ratification.ratification_status,
            "ratification_authority": ratification.ratification_authority,
            "candidate_promoted_to_anchor": ratification.candidate_promoted_to_anchor,
            "kind_set_membership_granted": ratification.kind_set_membership_granted,
            "next_owner_go_required": ratification.next_owner_go_required,
        },
    )
    _persist_json(
        path=store / "reconstruction_binding_v1.json",
        payload={
            "checkpoint_status": reconstruction.checkpoint_status,
            "event_stream_binding_status": reconstruction.event_stream_binding_status,
            "running_equity_reconstruction_status": (
                reconstruction.running_equity_reconstruction_status
            ),
            "venue_eq_reconciliation_status": reconstruction.venue_eq_reconciliation_status,
            "venue_eq_source_authority": reconstruction.venue_eq_source_authority,
            "checkpoint_mints_equity": reconstruction.checkpoint_mints_equity,
            "available_for_sizing_status": reconstruction.available_for_sizing_status,
            "risk_capital_status": reconstruction.risk_capital_status,
            "derivation_method": reconstruction.derivation_method,
        },
    )
    _persist_json(
        path=store / "d6_diagnostics_v1.json",
        payload={
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
            "FORENSIC_ARTIFACT_PRESENT": boundary.forensic_artifact_present,
            "CANDIDATE_VALIDATION_STATUS": boundary.candidate_validation_status,
            "INITIAL_STOCK_CANDIDATE_STATUS": boundary.initial_stock_candidate_status,
            "INITIAL_STOCK_ANCHOR_STATUS": boundary.initial_stock_anchor_status,
            "RATIFICATION_STATUS": boundary.ratification_status,
            "LIVE_EQUITY_STOCK_KIND_SET": KIND_SET_EMPTY,
            "CHECKPOINT_MINTS_EQUITY": FALSE_TOKEN,
            "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
            "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": boundary.earliest_live_critical_path_blocker,
            "NEXT_OWNER_GO_REQUIRED": boundary.next_owner_go_required,
            "NEW_CANONICAL_DEFINITION": TRUE_TOKEN,
            "LEGACY_SEMANTICS_RECONSTRUCTED": FALSE_TOKEN,
            "VENUE_POST_COUNT": "0",
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "checkpoint_mints_equity": "FORBIDDEN",
            "venue_eq_as_source": "FORBIDDEN",
            "venue_get_as_bootstrap": "FORBIDDEN",
            "flow_as_stock": "FORBIDDEN",
            "ingest_self_ratify": "FORBIDDEN",
            "candidate_is_not_anchor": TRUE_TOKEN,
            "empty_live_kind_set": KIND_SET_EMPTY,
            "initial_stock_anchor": STATUS_ABSENT,
            "implicit_normalization": "FORBIDDEN",
            "unknown_token_rewrite": "FORBIDDEN",
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
            "parent_bq_pack": CANONICAL_BQ_PACK_RELPATH,
            "parent_bp_pack": CANONICAL_BP_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
            "input_surface": CANONICAL_INPUT_SURFACE_RELPATH,
            "raw_epistemic_class": EPISTEMIC_RAW,
            "derived_epistemic_class": EPISTEMIC_DERIVED,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return OwnerSuppliedArtifactContractResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        forensic_artifact_present=boundary.forensic_artifact_present,
        raw_evidence_preserved=boundary.raw_evidence_preserved,
        artifact_sha256=boundary.artifact_sha256 or NONE_TOKEN,
        provenance_status=boundary.provenance_status,
        candidate_validation_status=boundary.candidate_validation_status,
        initial_stock_candidate_status=boundary.initial_stock_candidate_status,
        initial_stock_anchor_status=boundary.initial_stock_anchor_status,
        source_kind_status=boundary.source_kind_status,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        ratification_status=boundary.ratification_status,
        checkpoint_status=boundary.checkpoint_status,
        event_stream_binding_status=boundary.event_stream_binding_status,
        running_equity_reconstruction_status=boundary.running_equity_reconstruction_status,
        venue_eq_reconciliation_status=boundary.venue_eq_reconciliation_status,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        kinds_invented_this_go=FALSE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        venue_get_count="0",
        venue_post_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )


def fixture_owner_supplied_artifact_file_payload_v1() -> tuple[dict[str, Any], bytes, bytes]:
    envelope, inner_raw = fixture_valid_acquisition_candidate_payload_v1()
    payload = dict(envelope)
    payload["instrument_identity"] = INSTRUMENT_ACCOUNT_LEVEL
    payload["raw_evidence"] = inner_raw.decode("utf-8")
    file_bytes = _canonical_json(payload).encode("utf-8")
    return payload, file_bytes, inner_raw


def fixture_expected_bindings_v1() -> ArtifactBindingsV1:
    payload, _inner = fixture_valid_acquisition_candidate_payload_v1()
    return ArtifactBindingsV1(
        account_identity=str(payload["account_identity"]),
        instrument_identity=INSTRUMENT_ACCOUNT_LEVEL,
        as_of_time=str(payload["as_of_time"]),
        settlement_currency=str(payload["settlement_currency"]),
    )


__all__ = [
    "ADMISSIBLE_SOURCE_CLASS",
    "ARTIFACT_FILENAME",
    "CANONICAL_INPUT_SURFACE_RELPATH",
    "CANONICAL_PACK_RELPATH",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "REASON_PRECEDENCE",
    "SCHEMA_CLASS",
    "VALIDATION_CONTRADICTORY",
    "VALIDATION_INCOMPLETE",
    "VALIDATION_INVALID",
    "VALIDATION_VALID",
    "ArtifactBindingsV1",
    "CandidateValidationRecordV1",
    "OwnerSuppliedArtifactBoundaryV1",
    "OwnerSuppliedArtifactContractResultV1",
    "OwnerSuppliedBootstrapArtifactContractError",
    "RawIngestRecordV1",
    "RatificationBoundaryV1",
    "ReconstructionBindingV1",
    "bind_option_d_reconstruction_v1",
    "classify_validation_status_v1",
    "derive_kind_set_from_proven_source_v1",
    "detect_forbidden_implicit_normalization_v1",
    "evaluate_owner_supplied_bootstrap_candidate_v1",
    "evaluate_ratification_boundary_v1",
    "evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1",
    "execute_live_equity_stock_owner_supplied_bootstrap_artifact_v1",
    "fixture_expected_bindings_v1",
    "fixture_owner_supplied_artifact_file_payload_v1",
    "ingest_owner_supplied_bootstrap_artifact_v1",
    "parse_owner_supplied_artifact_json_v1",
    "reason_precedence_index_v1",
    "reject_claimed_artifact_authority_mutation_v1",
]
