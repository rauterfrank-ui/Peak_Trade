"""Fail-closed acquisition of OWNER_SUPPLIED_FORENSIC_BOOTSTRAP_STOCK.

Reuses the BP provenance seam. Acquisition does not mint an initial stock
anchor and does not ratify KIND_SET membership. Today no owner-supplied
forensic artifact is present. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_provenance_v1 import (
    ADMISSIBLE_SOURCE_CLASS,
    BOOTSTRAP_PROVENANCE_FINDING,
    CANONICAL_PACK_RELPATH as CANONICAL_BP_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BP_LIVE_BLOCKER,
    NEXT_OWNER_GO_REQUIRED as BP_NEXT_OWNER_GO,
    OWNER_GO as BP_OWNER_GO,
    STATUS_ABSENT,
    evaluate_bootstrap_stock_provenance_v1,
    evaluate_today_bootstrap_stock_provenance_boundary_v1,
    fixture_valid_bootstrap_stock_payload_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_checkpoint_stock_value_contract_v1 import (
    DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BN_PACK_RELPATH,
    LIVE_EQUITY_STOCK_KIND_SET,
    LIVE_EQUITY_STOCK_KIND_SET_IDENTITY,
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

OWNER_GO = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "5ee7f52293dc2fd36e5b431a07959737a949b323"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_equity_stock_bootstrap_stock_acquisition_wp1/2026-09-14T160000Z"
)
CANONICAL_INPUT_SURFACE_RELPATH = "evidence/ops/owner_supplied_forensic_bootstrap_stock_input_v1"
ARTIFACT_FILENAME = "owner_supplied_forensic_bootstrap_stock_v1.json"
CLAIMS_FILE = "claims.json"
SCHEMA_CLASS = "BOOTSTRAP_STOCK_ACQUISITION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
SOURCE_TYPE_OWNER_FILE = "OWNER_SUPPLIED_FORENSIC_FILE"
RATIFICATION_NOT_RATIFIED = "NOT_RATIFIED"
VALIDATION_VALID_CANDIDATE = "VALID_CANDIDATE_NOT_RATIFIED"
VALIDATION_REJECTED = "REJECTED"
VALIDATION_NOT_ACQUIRED = "NOT_ACQUIRED"
SURFACE_MISSING = "MISSING"
SURFACE_EMPTY = "EMPTY"
SURFACE_PRESENT = "PRESENT"
ACQUISITION_DEFINED_FAIL_CLOSED = "DEFINED_FAIL_CLOSED"
RAW_EVIDENCE_PRESERVED = TRUE_TOKEN
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = "EXTERNAL_FORENSIC_ARTIFACT_REQUIRED"
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_V1"

REQUIRED_FIELDS: tuple[str, ...] = (
    "artifact_id",
    "artifact_class",
    "raw_evidence_ref",
    "raw_evidence_digest",
    "source_identity",
    "source_type",
    "ratification_status",
    "account_identity",
    "settlement_currency",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "as_of_time",
    "sequence_identity",
    "event_stream_boundary",
    "replay_boundary",
    "embedding_status",
    "liability_status",
    "input_digest",
    "semantic_digest",
    "candidate_validation_status",
    "reason_code",
)
SCALAR_INPUT_FIELDS: tuple[str, ...] = (
    "artifact_id",
    "artifact_class",
    "raw_evidence_ref",
    "raw_evidence_digest",
    "source_identity",
    "source_type",
    "ratification_status",
    "account_identity",
    "settlement_currency",
    "equity_value",
    "equity_unit",
    "equity_precision",
    "as_of_time",
    "sequence_identity",
    "event_stream_boundary",
    "replay_boundary",
    "embedding_status",
    "liability_status",
)
STOCK_PAYLOAD_FIELDS: tuple[str, ...] = (
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

REASON_CLAIMED_CHECKPOINT_MINT = "CLAIMED_CHECKPOINT_MINT_FORBIDDEN"
REASON_CLAIMED_VENUE_EQ_SOURCE = "CLAIMED_VENUE_EQ_SOURCE_FORBIDDEN"
REASON_CLAIMED_FLOW_AS_STOCK = "CLAIMED_FLOW_AS_STOCK_FORBIDDEN"
REASON_VENUE_READ_NOT_BOOTSTRAP = "VENUE_READ_NOT_BOOTSTRAP_SOURCE"
REASON_RATIFICATION_FORBIDDEN = "ACQUISITION_CANNOT_RATIFY"
REASON_MISSING_FIELD = "MISSING_FIELD"
REASON_MALFORMED_FIELD = "MALFORMED_FIELD"
REASON_CONTRADICTORY_FIELD = "CONTRADICTORY_FIELD"
REASON_SOURCE_TYPE_FORBIDDEN = "SOURCE_TYPE_FORBIDDEN"
REASON_ARTIFACT_CLASS_FORBIDDEN = "ARTIFACT_CLASS_FORBIDDEN"
REASON_RAW_EVIDENCE_DIGEST_MISMATCH = "RAW_EVIDENCE_DIGEST_MISMATCH"
REASON_STOCK_PAYLOAD_REJECTED = "STOCK_PAYLOAD_REJECTED"
REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED = "EXTERNAL_FORENSIC_ARTIFACT_REQUIRED"
REASON_VALID_CANDIDATE = "VALID_ACQUISITION_CANDIDATE_NOT_RATIFIED"

REASON_PRECEDENCE: tuple[str, ...] = (
    REASON_CLAIMED_CHECKPOINT_MINT,
    REASON_CLAIMED_VENUE_EQ_SOURCE,
    REASON_CLAIMED_FLOW_AS_STOCK,
    REASON_VENUE_READ_NOT_BOOTSTRAP,
    REASON_RATIFICATION_FORBIDDEN,
    REASON_ARTIFACT_CLASS_FORBIDDEN,
    REASON_SOURCE_TYPE_FORBIDDEN,
    REASON_MISSING_FIELD,
    REASON_MALFORMED_FIELD,
    REASON_CONTRADICTORY_FIELD,
    REASON_RAW_EVIDENCE_DIGEST_MISMATCH,
    REASON_STOCK_PAYLOAD_REJECTED,
    REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED,
    REASON_VALID_CANDIDATE,
)

ALLOWED_CLAIMED_PROOFS: frozenset[str] = frozenset(
    {
        "NEW_CANONICAL_DEFINITION_BOOTSTRAP_ACQUISITION",
        "TODAY_ACQUISITION_REJECTED_FAIL_CLOSED",
        "FIXTURE_VALID_ACQUISITION_CANDIDATE_ONLY",
        "ACQUISITION_CAPABILITY_DEFINED",
    }
)
FORBIDDEN_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "VENUE_EQ",
        "VENUE_GET",
        "eq",
        "CHECKPOINT",
        "CHECKPOINT_MINT",
        "FLOW",
        "DELTA",
        "U04",
        "U06",
        "P01",
        "D4_GENESIS_ACCOUNT_CONFIG",
        "D5_CHECKPOINT_OBSERVATION",
        DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
        "INTERPRETATION",
        "HYPOTHESIS",
    }
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class BootstrapStockAcquisitionContractError(ValueError):
    """Fail-closed bootstrap stock acquisition contract violation."""


@dataclass(frozen=True)
class OwnerSuppliedArtifactSurfaceScanV1:
    surface_relpath: str
    surface_status: str
    artifact_present: str
    artifact_class: str
    artifact_count: str
    artifact_path: str


@dataclass(frozen=True)
class BootstrapStockAcquisitionRecordV1:
    artifact_id: str
    artifact_class: str
    raw_evidence_ref: str
    raw_evidence_digest: str
    source_identity: str
    source_type: str
    ratification_status: str
    candidate_validation_status: str
    stock_reason_code: str
    input_digest: str
    semantic_digest: str
    reason_code: str
    reason_precedence_index: str
    failures: tuple[str, ...]


@dataclass(frozen=True)
class BootstrapStockAcquisitionBoundaryV1:
    acquisition_contract_status: str
    forensic_artifact_present: str
    forensic_artifact_class: str
    raw_evidence_preserved: str
    candidate_validation_status: str
    initial_stock_anchor_status: str
    source_kind_status: str
    live_equity_stock_kind_set: str
    ratification_performed: str
    venue_eq_source_authority: str
    checkpoint_mints_equity: str
    new_canonical_definition: str
    legacy_semantics_reconstructed: str
    earliest_live_critical_path_blocker: str
    next_owner_go_required: str


@dataclass(frozen=True)
class BootstrapStockAcquisitionContractResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    acquisition_contract_status: str
    forensic_artifact_present: str
    forensic_artifact_class: str
    raw_evidence_preserved: str
    candidate_validation_status: str
    initial_stock_anchor_status: str
    source_kind_status: str
    live_equity_stock_kind_set: str
    ratification_performed: str
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
        raise BootstrapStockAcquisitionContractError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise BootstrapStockAcquisitionContractError(f"{field}_DRIFT:{actual}")


def _sha256_text(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise BootstrapStockAcquisitionContractError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise BootstrapStockAcquisitionContractError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise BootstrapStockAcquisitionContractError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise BootstrapStockAcquisitionContractError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise BootstrapStockAcquisitionContractError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise BootstrapStockAcquisitionContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise BootstrapStockAcquisitionContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if CHECKPOINT_CAN_MINT_EQUITY is not False:
        raise BootstrapStockAcquisitionContractError("CHECKPOINT_CAN_MINT_EQUITY_NOT_FALSE")
    if C17_CREATED is not False:
        raise BootstrapStockAcquisitionContractError("C17_CREATED_NOT_FALSE")
    if LIVE_EQUITY_STOCK_KIND_SET != KIND_SET_EMPTY:
        raise BootstrapStockAcquisitionContractError("BN_KIND_SET_NOT_EMPTY")
    if BP_NEXT_OWNER_GO != OWNER_GO:
        raise BootstrapStockAcquisitionContractError("BP_NEXT_OWNER_GO_DRIFT")
    if BP_LIVE_BLOCKER != "BOOTSTRAP_STOCK_EXTERNAL_FORENSIC_PROOF_ABSENT":
        raise BootstrapStockAcquisitionContractError("BP_LIVE_BLOCKER_DRIFT")
    if BP_OWNER_GO != "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE_V1":
        raise BootstrapStockAcquisitionContractError("BP_OWNER_GO_DRIFT")
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


def reject_claimed_acquisition_authority_mutation_v1(
    *,
    claimed_proof: str,
    artifact_id: str,
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
    }
    if claimed_proof in forbidden:
        raise BootstrapStockAcquisitionContractError(
            f"ACQUISITION_CANNOT_{claimed_proof}:{artifact_id}"
        )
    if claimed_proof not in ALLOWED_CLAIMED_PROOFS:
        raise BootstrapStockAcquisitionContractError(
            f"ACQUISITION_PROOF_UNKNOWN:{claimed_proof}:{artifact_id}"
        )


def reason_precedence_index_v1(reason_code: str) -> int:
    try:
        return REASON_PRECEDENCE.index(reason_code)
    except ValueError as exc:
        raise BootstrapStockAcquisitionContractError(
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


def scan_owner_supplied_bootstrap_artifact_surface_v1(
    *,
    repo_root: Path,
    surface_relpath: str = CANONICAL_INPUT_SURFACE_RELPATH,
) -> OwnerSuppliedArtifactSurfaceScanV1:
    _assert_standing_pins()
    surface = Path(repo_root) / surface_relpath
    if not surface.exists():
        return OwnerSuppliedArtifactSurfaceScanV1(
            surface_relpath=surface_relpath,
            surface_status=SURFACE_MISSING,
            artifact_present=FALSE_TOKEN,
            artifact_class=NONE_TOKEN,
            artifact_count="0",
            artifact_path="",
        )
    if not surface.is_dir():
        raise BootstrapStockAcquisitionContractError("INPUT_SURFACE_NOT_DIRECTORY")
    artifacts = sorted(
        path for path in surface.iterdir() if path.is_file() and path.name.endswith(".json")
    )
    if not artifacts:
        return OwnerSuppliedArtifactSurfaceScanV1(
            surface_relpath=surface_relpath,
            surface_status=SURFACE_EMPTY,
            artifact_present=FALSE_TOKEN,
            artifact_class=NONE_TOKEN,
            artifact_count="0",
            artifact_path="",
        )
    first = artifacts[0]
    return OwnerSuppliedArtifactSurfaceScanV1(
        surface_relpath=surface_relpath,
        surface_status=SURFACE_PRESENT,
        artifact_present=TRUE_TOKEN,
        artifact_class=ADMISSIBLE_SOURCE_CLASS,
        artifact_count=str(len(artifacts)),
        artifact_path=str(first.relative_to(repo_root)),
    )


def _stock_payload_from_acquisition(payload: Mapping[str, Any]) -> dict[str, Any]:
    nested = payload.get("stock_payload")
    if isinstance(nested, dict):
        return dict(nested)
    stock: dict[str, Any] = {}
    for name in STOCK_PAYLOAD_FIELDS:
        if name in payload:
            stock[name] = payload[name]
    if "anchor_id" not in stock and "artifact_id" in payload:
        stock["anchor_id"] = payload["artifact_id"]
    if "source_class" not in stock:
        stock["source_class"] = payload.get("artifact_class", "")
    if "provenance_ref" not in stock:
        stock["provenance_ref"] = payload.get("raw_evidence_ref", "")
    if "provenance_digest" not in stock:
        stock["provenance_digest"] = payload.get("raw_evidence_digest", "")
    return stock


def _evaluate_acquisition_once_v1(
    payload: Mapping[str, Any],
    *,
    claimed_proof: str,
    raw_bytes: bytes | None,
) -> BootstrapStockAcquisitionRecordV1:
    _assert_standing_pins()
    reject_claimed_acquisition_authority_mutation_v1(
        claimed_proof=claimed_proof,
        artifact_id=str(payload.get("artifact_id") or "UNKNOWN"),
    )
    reasons: list[str] = []
    failures: list[str] = []
    fields: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if name in {"candidate_validation_status", "reason_code"}:
            continue
        raw = payload.get(name, None)
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

    artifact_class = fields.get("artifact_class", "")
    source_type = fields.get("source_type", "")
    ratification = fields.get("ratification_status", "")
    if artifact_class in {"VENUE_EQ", "eq"}:
        reasons.append(REASON_CLAIMED_VENUE_EQ_SOURCE)
    elif artifact_class in {"CHECKPOINT", "CHECKPOINT_MINT"}:
        reasons.append(REASON_CLAIMED_CHECKPOINT_MINT)
    elif artifact_class in {"FLOW", "DELTA", "CLASSIFIED_EVENT_STREAM"}:
        reasons.append(REASON_CLAIMED_FLOW_AS_STOCK)
    elif artifact_class and artifact_class != ADMISSIBLE_SOURCE_CLASS:
        reasons.append(REASON_ARTIFACT_CLASS_FORBIDDEN)
        failures.append("ARTIFACT_CLASS_NOT_OWNER_SUPPLIED")
    if source_type in {"VENUE_GET", "VENUE_EQ", "eq"}:
        reasons.append(REASON_VENUE_READ_NOT_BOOTSTRAP)
    elif source_type in FORBIDDEN_SOURCE_TYPES:
        reasons.append(REASON_SOURCE_TYPE_FORBIDDEN)
        failures.append("SOURCE_TYPE_FORBIDDEN")
    elif source_type and source_type != SOURCE_TYPE_OWNER_FILE:
        reasons.append(REASON_SOURCE_TYPE_FORBIDDEN)
        failures.append("SOURCE_TYPE_NOT_OWNER_FILE")
    if ratification and ratification != RATIFICATION_NOT_RATIFIED:
        reasons.append(REASON_RATIFICATION_FORBIDDEN)
        failures.append("ACQUISITION_CLAIMED_RATIFICATION")

    declared_raw = fields.get("raw_evidence_digest", "")
    if declared_raw and not _SHA256_HEX.match(declared_raw):
        reasons.append(REASON_MALFORMED_FIELD)
        failures.append("MALFORMED:raw_evidence_digest")
    if raw_bytes is None:
        reasons.append(REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED)
        failures.append("RAW_BYTES_ABSENT")
    else:
        computed_raw = _sha256_bytes(raw_bytes)
        if declared_raw and declared_raw != computed_raw:
            reasons.append(REASON_RAW_EVIDENCE_DIGEST_MISMATCH)
            failures.append("RAW_BYTES_DIGEST_MISMATCH")

    stock_payload = _stock_payload_from_acquisition(payload)
    stock_reason = ""
    if stock_payload:
        stock = evaluate_bootstrap_stock_provenance_v1(
            stock_payload,
            claimed_proof="FIXTURE_VALID_BOOTSTRAP_ONLY",
        )
        stock_reason = stock.reason_code
        if stock.validation_status != "VALID":
            reasons.append(REASON_STOCK_PAYLOAD_REJECTED)
            failures.append(f"STOCK:{stock.reason_code}")

    declared_input = fields.get("input_digest", "")
    declared_semantic = fields.get("semantic_digest", "")
    computed_input = _sha256_text(_digest_inputs(fields=fields))
    if declared_input:
        if not _SHA256_HEX.match(declared_input):
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:input_digest")
        elif declared_input != computed_input:
            reasons.append(REASON_CONTRADICTORY_FIELD)
            failures.append("INPUT_DIGEST_MISMATCH")
    semantic_payload = _digest_inputs(fields=fields)
    semantic_payload["input_digest"] = computed_input
    computed_semantic = _sha256_text(semantic_payload)
    if declared_semantic:
        if not _SHA256_HEX.match(declared_semantic):
            reasons.append(REASON_MALFORMED_FIELD)
            failures.append("MALFORMED:semantic_digest")
        elif declared_semantic != computed_semantic:
            reasons.append(REASON_CONTRADICTORY_FIELD)
            failures.append("SEMANTIC_DIGEST_MISMATCH")

    unique_reasons = list(dict.fromkeys(reasons))
    if not unique_reasons:
        reason_code = REASON_VALID_CANDIDATE
        validation_status = VALIDATION_VALID_CANDIDATE
    else:
        reason_code = min(unique_reasons, key=reason_precedence_index_v1)
        validation_status = VALIDATION_REJECTED
    return BootstrapStockAcquisitionRecordV1(
        artifact_id=fields.get("artifact_id", ""),
        artifact_class=artifact_class,
        raw_evidence_ref=fields.get("raw_evidence_ref", ""),
        raw_evidence_digest=declared_raw,
        source_identity=fields.get("source_identity", ""),
        source_type=source_type,
        ratification_status=ratification,
        candidate_validation_status=validation_status,
        stock_reason_code=stock_reason,
        input_digest=declared_input or computed_input,
        semantic_digest=declared_semantic or computed_semantic,
        reason_code=reason_code,
        reason_precedence_index=str(reason_precedence_index_v1(reason_code)),
        failures=tuple(failures),
    )


def evaluate_bootstrap_stock_acquisition_v1(
    payload: Mapping[str, Any],
    *,
    claimed_proof: str = "FIXTURE_VALID_ACQUISITION_CANDIDATE_ONLY",
    raw_bytes: bytes | None = None,
) -> BootstrapStockAcquisitionRecordV1:
    first = _evaluate_acquisition_once_v1(payload, claimed_proof=claimed_proof, raw_bytes=raw_bytes)
    second = _evaluate_acquisition_once_v1(
        payload, claimed_proof=claimed_proof, raw_bytes=raw_bytes
    )
    if first != second:
        raise BootstrapStockAcquisitionContractError("ACQUISITION_EVALUATION_NOT_DETERMINISTIC")
    return first


def evaluate_today_bootstrap_stock_acquisition_boundary_v1(
    *,
    repo_root: Path,
) -> BootstrapStockAcquisitionBoundaryV1:
    _assert_standing_pins()
    members = ratified_live_equity_stock_kind_set_v1(evaluate_today_live_equity_stock_kind_set_v1())
    if members:
        raise BootstrapStockAcquisitionContractError(
            f"KIND_INVENTED_OR_UNPROVEN_MEMBER:{','.join(members)}"
        )
    bp_boundary = evaluate_today_bootstrap_stock_provenance_boundary_v1()
    if bp_boundary.initial_stock_anchor_status != STATUS_ABSENT:
        raise BootstrapStockAcquisitionContractError("BP_INITIAL_STOCK_NOT_ABSENT")
    scan = scan_owner_supplied_bootstrap_artifact_surface_v1(repo_root=repo_root)
    if scan.artifact_present != FALSE_TOKEN:
        raise BootstrapStockAcquisitionContractError("UNEXPECTED_OWNER_SUPPLIED_ARTIFACT")
    first = BootstrapStockAcquisitionBoundaryV1(
        acquisition_contract_status=ACQUISITION_DEFINED_FAIL_CLOSED,
        forensic_artifact_present=FALSE_TOKEN,
        forensic_artifact_class=NONE_TOKEN,
        raw_evidence_preserved=RAW_EVIDENCE_PRESERVED,
        candidate_validation_status=VALIDATION_NOT_ACQUIRED,
        initial_stock_anchor_status=STATUS_ABSENT,
        source_kind_status=NONE_TOKEN,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        ratification_performed=FALSE_TOKEN,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        new_canonical_definition=TRUE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    second = BootstrapStockAcquisitionBoundaryV1(
        acquisition_contract_status=ACQUISITION_DEFINED_FAIL_CLOSED,
        forensic_artifact_present=FALSE_TOKEN,
        forensic_artifact_class=NONE_TOKEN,
        raw_evidence_preserved=RAW_EVIDENCE_PRESERVED,
        candidate_validation_status=VALIDATION_NOT_ACQUIRED,
        initial_stock_anchor_status=STATUS_ABSENT,
        source_kind_status=NONE_TOKEN,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        ratification_performed=FALSE_TOKEN,
        venue_eq_source_authority=FALSE_TOKEN,
        checkpoint_mints_equity=FALSE_TOKEN,
        new_canonical_definition=TRUE_TOKEN,
        legacy_semantics_reconstructed=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
    )
    if first != second:
        raise BootstrapStockAcquisitionContractError("ACQUISITION_BOUNDARY_NOT_DETERMINISTIC")
    return first


def execute_live_equity_stock_bootstrap_stock_acquisition_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bp_pack: Path,
    repo_root: Path,
    evidence_root: Path,
    persist_as_of: str,
) -> BootstrapStockAcquisitionContractResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise BootstrapStockAcquisitionContractError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise BootstrapStockAcquisitionContractError("ORIGIN_MAIN_SHA_MISMATCH")
    bp_pack = Path(sealed_bp_pack)
    try:
        manifest_rc = verify_manifest_sha256_v1(store_root=bp_pack)
    except Exception as exc:
        raise BootstrapStockAcquisitionContractError("BP_MANIFEST_VERIFY_FAILED") from exc
    if manifest_rc != 0:
        raise BootstrapStockAcquisitionContractError("BP_MANIFEST_VERIFY_FAILED")
    claims_path = bp_pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise BootstrapStockAcquisitionContractError("BP_CLAIMS_MISSING")
    try:
        bp_claims = _load_json_object(path=claims_path)
    except json.JSONDecodeError as exc:
        raise BootstrapStockAcquisitionContractError("BP_CLAIMS_MALFORMED") from exc
    _require_token(field="KIND_SET", payload=bp_claims, expected=KIND_SET_EMPTY)
    _require_token(field="LIVE_EQUITY_STOCK_KIND_SET", payload=bp_claims, expected=KIND_SET_EMPTY)
    _require_token(field="GATE_A_EXECUTED", payload=bp_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bp_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bp_claims, expected="0")
    _require_token(field="VENUE_POST_COUNT", payload=bp_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bp_claims, expected=FALSE_TOKEN)
    _require_token(field="KINDS_INVENTED_THIS_GO", payload=bp_claims, expected=FALSE_TOKEN)
    _require_token(field="CHECKPOINT_MINTS_EQUITY", payload=bp_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=bp_claims, expected=FALSE_TOKEN)
    _require_token(field="INITIAL_STOCK_ANCHOR_STATUS", payload=bp_claims, expected=STATUS_ABSENT)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=bp_claims, expected=OWNER_GO)
    _require_token(
        field="EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
        payload=bp_claims,
        expected=BP_LIVE_BLOCKER,
    )
    _require_token(field="F12_DECISION", payload=bp_claims, expected=DECISION_REMAIN_UNKNOWN)
    reject_claimed_acquisition_authority_mutation_v1(
        claimed_proof="NEW_CANONICAL_DEFINITION_BOOTSTRAP_ACQUISITION",
        artifact_id=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    )
    reject_claimed_acquisition_authority_mutation_v1(
        claimed_proof="TODAY_ACQUISITION_REJECTED_FAIL_CLOSED",
        artifact_id="TODAY_PRODUCTIVE_ACQUISITION",
    )
    reject_claimed_acquisition_authority_mutation_v1(
        claimed_proof="ACQUISITION_CAPABILITY_DEFINED",
        artifact_id=ADMISSIBLE_SOURCE_CLASS,
    )
    scan = scan_owner_supplied_bootstrap_artifact_surface_v1(repo_root=repo_root)
    boundary = evaluate_today_bootstrap_stock_acquisition_boundary_v1(repo_root=repo_root)
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
        "SEALED_BP_PACK": CANONICAL_BP_PACK_RELPATH,
        "SEALED_BN_PACK": CANONICAL_BN_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
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
        "ACQUISITION_CONTRACT_DEFINED": TRUE_TOKEN,
        "ACQUISITION_CONTRACT_STATUS": boundary.acquisition_contract_status,
        "BOOTSTRAP_PROVENANCE_FINDING": BOOTSTRAP_PROVENANCE_FINDING,
        "ADMISSIBLE_BOOTSTRAP_SOURCE_CLASS": ADMISSIBLE_SOURCE_CLASS,
        "FORENSIC_ARTIFACT_PRESENT": boundary.forensic_artifact_present,
        "FORENSIC_ARTIFACT_CLASS": boundary.forensic_artifact_class,
        "RAW_EVIDENCE_PRESERVED": boundary.raw_evidence_preserved,
        "CANDIDATE_VALIDATION_STATUS": boundary.candidate_validation_status,
        "INITIAL_STOCK_ANCHOR_STATUS": boundary.initial_stock_anchor_status,
        "SOURCE_KIND_STATUS": boundary.source_kind_status,
        "RATIFICATION_PERFORMED": boundary.ratification_performed,
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
        "BP_LIVE_BLOCKER_CONSUMED": BP_LIVE_BLOCKER,
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
        "BP_MANIFEST_VERIFY_RC": "0",
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "acquisition_contract_v1.json",
        payload={
            "schema_class": SCHEMA_CLASS,
            "contract_version": CONTRACT_VERSION,
            "required_fields": list(REQUIRED_FIELDS),
            "reason_precedence": list(REASON_PRECEDENCE),
            "admissible_source_class": ADMISSIBLE_SOURCE_CLASS,
            "acquisition_cannot_ratify": TRUE_TOKEN,
            "checkpoint_mints_equity": FALSE_TOKEN,
            "venue_eq_source_authority": FALSE_TOKEN,
            "new_canonical_definition": TRUE_TOKEN,
            "legacy_semantics_reconstructed": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "acquisition_boundary_v1.json",
        payload={
            "acquisition_contract_status": boundary.acquisition_contract_status,
            "forensic_artifact_present": boundary.forensic_artifact_present,
            "forensic_artifact_class": boundary.forensic_artifact_class,
            "raw_evidence_preserved": boundary.raw_evidence_preserved,
            "candidate_validation_status": boundary.candidate_validation_status,
            "initial_stock_anchor_status": boundary.initial_stock_anchor_status,
            "source_kind_status": boundary.source_kind_status,
            "ratification_performed": boundary.ratification_performed,
            "earliest_live_critical_path_blocker": boundary.earliest_live_critical_path_blocker,
            "next_owner_go_required": boundary.next_owner_go_required,
        },
    )
    _persist_json(
        path=store / "input_surface_scan_v1.json",
        payload={
            "surface_relpath": scan.surface_relpath,
            "surface_status": scan.surface_status,
            "artifact_present": scan.artifact_present,
            "artifact_class": scan.artifact_class,
            "artifact_count": scan.artifact_count,
            "artifact_path": scan.artifact_path,
            "expected_artifact_filename": ARTIFACT_FILENAME,
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
            "ACQUISITION_CONTRACT_STATUS": boundary.acquisition_contract_status,
            "FORENSIC_ARTIFACT_PRESENT": boundary.forensic_artifact_present,
            "CANDIDATE_VALIDATION_STATUS": boundary.candidate_validation_status,
            "INITIAL_STOCK_ANCHOR_STATUS": boundary.initial_stock_anchor_status,
            "RATIFICATION_PERFORMED": boundary.ratification_performed,
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
            "acquisition_self_ratify": "FORBIDDEN",
            "candidate_is_not_kind_member": TRUE_TOKEN,
            "empty_live_kind_set": KIND_SET_EMPTY,
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
            "parent_bp_pack": CANONICAL_BP_PACK_RELPATH,
            "parent_bn_pack": CANONICAL_BN_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
            "input_surface": CANONICAL_INPUT_SURFACE_RELPATH,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return BootstrapStockAcquisitionContractResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        acquisition_contract_status=boundary.acquisition_contract_status,
        forensic_artifact_present=boundary.forensic_artifact_present,
        forensic_artifact_class=boundary.forensic_artifact_class,
        raw_evidence_preserved=boundary.raw_evidence_preserved,
        candidate_validation_status=boundary.candidate_validation_status,
        initial_stock_anchor_status=boundary.initial_stock_anchor_status,
        source_kind_status=boundary.source_kind_status,
        live_equity_stock_kind_set=KIND_SET_EMPTY,
        ratification_performed=FALSE_TOKEN,
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


def fixture_valid_acquisition_candidate_payload_v1() -> tuple[dict[str, Any], bytes]:
    stock = fixture_valid_bootstrap_stock_payload_v1()
    raw_bytes = _canonical_json(stock).encode("utf-8")
    fields = {
        "artifact_id": "FIXTURE_ACQUISITION_ARTIFACT_001",
        "artifact_class": ADMISSIBLE_SOURCE_CLASS,
        "raw_evidence_ref": "FIXTURE_OWNER_SUPPLIED_RAW_REF",
        "raw_evidence_digest": _sha256_bytes(raw_bytes),
        "source_identity": "FIXTURE_OWNER",
        "source_type": SOURCE_TYPE_OWNER_FILE,
        "ratification_status": RATIFICATION_NOT_RATIFIED,
        "account_identity": stock["account_identity"],
        "settlement_currency": stock["settlement_currency"],
        "equity_value": stock["equity_value"],
        "equity_unit": stock["equity_unit"],
        "equity_precision": stock["equity_precision"],
        "as_of_time": stock["as_of_time"],
        "sequence_identity": stock["sequence_identity"],
        "event_stream_boundary": stock["event_stream_boundary"],
        "replay_boundary": stock["replay_boundary"],
        "embedding_status": stock["embedding_status"],
        "liability_status": stock["liability_status"],
    }
    input_digest = _sha256_text(_digest_inputs(fields=fields))
    semantic_payload = _digest_inputs(fields=fields)
    semantic_payload["input_digest"] = input_digest
    payload = {
        **fields,
        "stock_payload": stock,
        "input_digest": input_digest,
        "semantic_digest": _sha256_text(semantic_payload),
        "candidate_validation_status": VALIDATION_VALID_CANDIDATE,
        "reason_code": REASON_VALID_CANDIDATE,
    }
    return payload, raw_bytes


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
    "REQUIRED_FIELDS",
    "SCHEMA_CLASS",
    "BootstrapStockAcquisitionBoundaryV1",
    "BootstrapStockAcquisitionContractError",
    "BootstrapStockAcquisitionContractResultV1",
    "BootstrapStockAcquisitionRecordV1",
    "evaluate_bootstrap_stock_acquisition_v1",
    "evaluate_today_bootstrap_stock_acquisition_boundary_v1",
    "execute_live_equity_stock_bootstrap_stock_acquisition_v1",
    "fixture_valid_acquisition_candidate_payload_v1",
    "reason_precedence_index_v1",
    "reject_claimed_acquisition_authority_mutation_v1",
    "scan_owner_supplied_bootstrap_artifact_surface_v1",
]
