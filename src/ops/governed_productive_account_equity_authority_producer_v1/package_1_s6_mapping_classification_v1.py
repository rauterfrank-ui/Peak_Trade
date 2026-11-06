"""PACKAGE_1 S6 mapping/classification against sealed S1-S5 evidence.

Classifies observed rows against existing D6/Class-C contracts.
Does not mint D4 identity. Does not invent ratified kinds.
Does not execute GET/POST. Does not authorize MS2 or D7.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    RATIFIED_CLASSIFIED_EVENT_KIND_SET_TOKEN,
    build_forensic_event_kind_census_findings_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY,
    DIMENSION_MARGIN_REQUIREMENTS,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    RESIDUAL_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.fresh_eq_reconciliation_target_contract_v1 import (
    OBSERVATION_SEMANTIC_CLASS as EQ_RECONCILIATION_OBSERVATION_SEMANTIC,
    VENUE_FIELD_NAME as EQ_VENUE_FIELD_NAME,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.option_d_ssot_architecture_contract_v1 import (
    FORBIDDEN_SOURCE_FIELDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    U01_ACCOUNT_MODE_ROLE,
    VALUATION_NOTIONAL_PROHIBITED_AS_ADDEND,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    CLASSIFICATION_STATUS_UNCLASSIFIED,
    CLASSIFICATION_STATUS_UNKNOWN,
    RATIFIED_CLASSIFIED_KIND_SET,
    build_equity_affecting_event_taxonomy_record_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    CANDIDATE_RESIDUAL,
    CANDIDATE_U05,
    CANDIDATE_U06,
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    BALANCE_ALLOWED_OBSERVATION_FIELDS,
    EMBEDDING_FACTS_REMAIN_UNKNOWN,
    EQ_ROLE_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY,
    FORBIDDEN_BALANCE_AUTHORITY_USES,
    SURFACE_ACCOUNT_BALANCE,
    SURFACE_ACCOUNT_BILLS,
    SURFACE_ACCOUNT_BILLS_ARCHIVE,
    SURFACE_ACCOUNT_CONFIG,
    SURFACE_ACCOUNT_SUBTYPES,
    reject_include_exclude_from_unknown_embedding_v1,
)

OWNER_GO = "OWNER_GO_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "d98e3bf9d8560d4d54b5f421abe657c0f5348a3a"
CANONICAL_SEALED_OBSERVATION_PACK_RELPATH = (
    "evidence/ops/full_core_d6_path_b_package_1_observation_execution_v1/2026-09-13T182521Z"
)
PACKAGE_1_S6_MAPPING_STORE_RELPATH = (
    "evidence/ops/full_core_d6_path_b_package_1_s6_mapping_classification_v1"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NOT_MAPPED_FAIL_CLOSED = "NOT_MAPPED_FAIL_CLOSED"
MAPPING_COVERAGE_FAIL_CLOSED = "FAIL_CLOSED_NO_RATIFIED_KIND"
OBSERVED_KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
RETENTION_COVERAGE_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_COMPLETENESS_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
D4_CORROBORATED = "D4_RUNTIME_EVIDENCE_CORROBORATED_IDENTITY_NOT_MINTED"
STATUS_MAPPED_RATIFIED = "MAPPED_RATIFIED"
STATUS_OBSERVED_UNRATIFIED = "OBSERVED_UNRATIFIED"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
RATIFICATION_CONTRACT_SEMANTIC = "CONTRACT_SEMANTIC_RATIFIED"
RATIFICATION_REJECTION = "REJECTION_RATIFIED"
RATIFICATION_UNRATIFIED = "UNRATIFIED"
RATIFICATION_AMBIGUOUS = "AMBIGUOUS_UNRATIFIED"
TARGET_KIND_NONE = "NONE"
REDACTED_VALUE = "REDACTED_IDENTITY_OR_ACCOUNT_MEMBER"
REDACT_FIELD_NAMES = frozenset({"uid", "mainUid", "ip", "from", "to"})
C02_FORBIDDEN_SOURCE_FIELDS = frozenset(FORBIDDEN_SOURCE_FIELDS)
C01_AVAILEQ_FIELDS = frozenset({"availEq"})
P01_REJECTED_VENUE_FIELDS = frozenset(
    {
        "availEq",
        "totalEq",
        "eq",
        "adjEq",
        "availBal",
        "cashBal",
        "frozenBal",
        "isoEq",
        "ordFrozen",
        "upl",
    }
)
U05_EMBEDDING_FIELDS = frozenset({"liab", "crossLiab", "isoLiab", "borrowFroz"})
U06_FEE_FIELDS = frozenset({"fee"})
U03_UPL_FIELDS = frozenset({"upl", "uplLiab", "isoUpl", "spotUpl"})
U04_FROZEN_FIELDS = frozenset({"ordFroz", "ordFrozen"})
MARGIN_DIMENSION_FIELDS = frozenset({"imr", "mmr", "mgnRatio"})
NOTIONAL_FIELDS = frozenset(
    {
        "notionalUsd",
        "notionalUsdForBorrow",
        "notionalUsdForFutures",
        "notionalUsdForOption",
        "notionalUsdForSwap",
        "notionalLever",
    }
)
BILL_EVENT_IDENTITY_FIELDS = frozenset({"billId", "ts"})
BILL_KIND_TOKEN_FIELDS = frozenset({"type", "subType"})
INTEREST_FIELDS = frozenset({"interest"})
PNL_FIELDS = frozenset({"pnl", "totalPnl"})
D4_IDENTITY_FIELDS = frozenset({"uid", "mainUid"})
D4_SETTLEMENT_FIELDS = frozenset({"settleCcy", "settleCcyList"})
D4_ACCOUNT_MODE_FIELDS = frozenset({"posMode"})
CURRENCY_FIELDS = frozenset({"ccy"})
REQUIRED_SEALED_FILES: tuple[str, ...] = (
    "claims.json",
    "s1_account_config_observation_v1.json",
    "s2_account_balance_observation_v1.json",
    "s3_account_subtypes_observation_v1.json",
    "s4_account_bills_observation_v1.json",
    "s4_account_bills_archive_observation_v1.json",
    "s4_bills_pair_overlap_v1.json",
    "s5_raw_evidence_seal_v1.json",
)
BILL_SURFACES: tuple[str, ...] = (
    SURFACE_ACCOUNT_BILLS,
    SURFACE_ACCOUNT_BILLS_ARCHIVE,
)
SURFACE_FILE_BY_ID = {
    SURFACE_ACCOUNT_CONFIG: "s1_account_config_observation_v1.json",
    SURFACE_ACCOUNT_BALANCE: "s2_account_balance_observation_v1.json",
    SURFACE_ACCOUNT_SUBTYPES: "s3_account_subtypes_observation_v1.json",
    SURFACE_ACCOUNT_BILLS: "s4_account_bills_observation_v1.json",
    SURFACE_ACCOUNT_BILLS_ARCHIVE: "s4_account_bills_archive_observation_v1.json",
}


class Package1S6MappingClassificationError(ValueError):
    """Fail-closed PACKAGE_1 S6 mapping/classification violation."""


@dataclass(frozen=True)
class Package1S6MappingClassificationResultV1:
    genesis_id: str
    genesis_as_of: str
    mapping_as_of: str
    store_root: str
    sealed_input_pack: str
    sealed_input_only: str
    manifest_verify_rc: str
    s6_executed: str
    observed_kind_set: str
    kind_set_resolved: str
    unresolved_kinds_or_ambiguities: str
    mapping_persisted: str
    mapping_coverage_status: str
    classification_records_persisted: str
    classified_bill_row_count: str
    retention_coverage_status: str
    ordering_completeness_status: str
    d4_corroboration_result: str
    d4_identity_minted: str
    raw_eq_source_authority: str
    new_network_get_count: str
    network_post_performed: str
    ms2_authorized: str
    ms2_executed: str
    d6_fully_closed: str
    d7_authorized: str
    observed_relevant_field_count: str
    mapped_ratified_fields: str
    observed_unratified_fields: str
    ambiguous_fields: str
    not_applicable_fields: str
    ratification_candidates: str
    high_value_unratified_candidates: str
    kind_set_resolution_blockers: str
    evidence_manifest: str


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


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify_manifest_sha256_v1(*, store_root: Path | str) -> int:
    root = Path(store_root)
    manifest = root / "MANIFEST.sha256"
    if not manifest.is_file():
        raise Package1S6MappingClassificationError("MANIFEST_ABSENT")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual_names = {p.name for p in root.iterdir() if p.is_file() and p.name != "MANIFEST.sha256"}
    if set(expected) != actual_names:
        raise Package1S6MappingClassificationError("MANIFEST_FILESET_DRIFT")
    for name, digest in expected.items():
        actual = _sha256_bytes((root / name).read_bytes())
        if actual != digest:
            raise Package1S6MappingClassificationError(f"MANIFEST_DIGEST_MISMATCH:{name}")
    return 0


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Package1S6MappingClassificationError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _optional_str(row: Mapping[str, Any], field: str) -> str:
    raw = row.get(field)
    if raw is None or isinstance(raw, bool):
        return ""
    return str(raw).strip()


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise Package1S6MappingClassificationError(f"{field}_DRIFT:{actual}")


def _census_candidate_index() -> dict[str, str]:
    return {
        finding.candidate_id: finding.disposition
        for finding in build_forensic_event_kind_census_findings_v1()
    }


def _rows_from_observation(*, payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows")
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise Package1S6MappingClassificationError("OBSERVATION_ROWS_NOT_LIST")
    out: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            out.append(row)
    return out


def _classify_bill_row(
    *,
    surface_id: str,
    row: Mapping[str, Any],
    row_index: int,
    source_payload_digest: str,
    identity_digest: str,
    census_index: Mapping[str, str],
) -> dict[str, str]:
    bill_id = _optional_str(row, "billId")
    type_token = _optional_str(row, "type")
    subtype_token = _optional_str(row, "subType")
    ts = _optional_str(row, "ts")
    if bill_id:
        event_record_id = f"{surface_id}:{bill_id}"
        classification_status = CLASSIFICATION_STATUS_UNCLASSIFIED
        event_semantic_class = CLASSIFICATION_STATUS_UNCLASSIFIED
        identity_basis = "BILL_ID_PRESENT_NO_RATIFIED_KIND"
    else:
        event_record_id = f"{surface_id}:ROW_INDEX_{row_index}"
        classification_status = CLASSIFICATION_STATUS_UNKNOWN
        event_semantic_class = CLASSIFICATION_STATUS_UNKNOWN
        identity_basis = "BILL_ID_ABSENT_FAIL_CLOSED"
    ordering_key = ts if ts else f"ORDERING_KEY_ABSENT_FAIL_CLOSED:{event_record_id}"
    digest_payload = {
        "surface_id": surface_id,
        "billId": bill_id,
        "type": type_token,
        "subType": subtype_token,
        "ts": ts,
        "source_payload_digest": source_payload_digest,
        "row_index": str(row_index),
    }
    event_digest = _sha256_bytes(_canonical_json(digest_payload).encode("utf-8"))
    census_disposition = "NO_CENSUS_CANDIDATE_ID_MATCH"
    if type_token in census_index:
        census_disposition = census_index[type_token]
    if type_token in RATIFIED_CLASSIFIED_KIND_SET:
        raise Package1S6MappingClassificationError("VENUE_TYPE_MUST_NOT_BE_RATIFIED_KIND")
    record = build_equity_affecting_event_taxonomy_record_v1(
        event_record_id=event_record_id,
        classification_status=classification_status,
        event_semantic_class=event_semantic_class,
        ordering_key=ordering_key,
        event_digest=event_digest,
        mapped_numeric_effect=NOT_MAPPED_FAIL_CLOSED,
        bound_account_identity_ref=identity_digest,
        bound_account_identity_digest=identity_digest,
    )
    payload = {str(k): str(v) for k, v in asdict(record).items()}
    payload["source_surface_id"] = surface_id
    payload["observed_type_token"] = type_token
    payload["observed_subtype_token"] = subtype_token
    payload["observed_bill_id_present"] = TRUE_TOKEN if bill_id else FALSE_TOKEN
    payload["observed_ts_present"] = TRUE_TOKEN if ts else FALSE_TOKEN
    payload["forensic_fee_field_present"] = TRUE_TOKEN if _optional_str(row, "fee") else FALSE_TOKEN
    payload["forensic_interest_field_present"] = (
        TRUE_TOKEN if _optional_str(row, "interest") else FALSE_TOKEN
    )
    payload["forensic_pnl_field_present"] = TRUE_TOKEN if _optional_str(row, "pnl") else FALSE_TOKEN
    payload["census_candidate_match"] = census_disposition
    payload["identity_basis"] = identity_basis
    payload["kind_ratification"] = "FORBIDDEN_NO_RATIFIED_KIND"
    payload["u05_kind_decision"] = U05_KIND_DECISION
    payload["u06_kind_decision"] = U06_KIND_DECISION
    payload["source_payload_digest"] = source_payload_digest
    payload["contract_rule"] = (
        "equity_affecting_event_taxonomy_contract_v1:"
        "UNCLASSIFIED_OR_UNKNOWN_NOT_MAPPED_TO_ZERO;"
        "RATIFIED_CLASSIFIED_KIND_SET_EMPTY;"
        "bills_cannot_ratify_U05_U06"
    )
    return payload


def _classify_subtypes(*, payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = _rows_from_observation(payload=payload)
    catalog_types: list[str] = []
    for row in rows:
        token = _optional_str(row, "type")
        if token:
            catalog_types.append(token)
    unique_types = tuple(sorted(set(catalog_types)))
    return {
        "surface_id": SURFACE_ACCOUNT_SUBTYPES,
        "surface_class": "CATALOG_METADATA_NOT_EVENT_KIND",
        "row_count": str(payload.get("row_count") or len(rows)),
        "observed_catalog_type_count": str(len(unique_types)),
        "observed_catalog_type_tokens": ",".join(unique_types),
        "query_result_is_not_kind_completeness": TRUE_TOKEN,
        "kind_ratification": "FORBIDDEN",
        "empty_result_proves_zero_events": FALSE_TOKEN,
        "contract_rule": "EMPTY_ROWS_AND_QUERY_RESULT_ARE_NOT_KIND_ABSENCE",
    }


def _classify_balance(*, payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = _rows_from_observation(payload=payload)
    extra_keys: set[str] = set()
    allowed_present: set[str] = set()
    for row in rows:
        extra_keys.update(str(k) for k in row.keys())
        details = row.get("details")
        nested = details if isinstance(details, list) else []
        for item in nested:
            if isinstance(item, dict):
                extra_keys.update(str(k) for k in item.keys())
                for field in BALANCE_ALLOWED_OBSERVATION_FIELDS:
                    if _optional_str(item, field):
                        allowed_present.add(field)
    extra_keys.difference_update(BALANCE_ALLOWED_OBSERVATION_FIELDS)
    extra_keys.discard("details")
    extra_keys.discard("ccy")
    return {
        "surface_id": SURFACE_ACCOUNT_BALANCE,
        "eq_role": EQ_ROLE_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY,
        "raw_eq_source_authority": FALSE_TOKEN,
        "c01_rehabilitation": "FORBIDDEN",
        "allowed_observation_fields_present": ",".join(sorted(allowed_present)),
        "forensic_extra_keys_not_authority": ",".join(sorted(extra_keys)),
        "forbidden_authority_uses": ",".join(FORBIDDEN_BALANCE_AUTHORITY_USES),
        "kind_ratification": "FORBIDDEN",
        "contract_rule": "BALANCE_OBSERVATION_CANNOT_BECOME_AUTHORITY",
    }


def _classify_config(*, payload: Mapping[str, Any]) -> dict[str, Any]:
    minted = str(payload.get("d4_identity_minted") or "")
    if minted != FALSE_TOKEN:
        raise Package1S6MappingClassificationError("SEALED_S1_D4_IDENTITY_MINTED_NOT_FALSE")
    corroboration = str(payload.get("d4_corroboration_result") or "")
    if corroboration != D4_CORROBORATED:
        raise Package1S6MappingClassificationError("SEALED_S1_D4_CORROBORATION_DRIFT")
    if D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY is not True:
        raise Package1S6MappingClassificationError("D4_POST_GENESIS_MUST_NOT_MINT_PIN_DRIFT")
    return {
        "surface_id": SURFACE_ACCOUNT_CONFIG,
        "d4_corroboration_result": corroboration,
        "d4_identity_minted": FALSE_TOKEN,
        "identity_authority": "FORBIDDEN_CORROBORATION_ONLY",
        "kind_ratification": "FORBIDDEN",
        "contract_rule": "D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY",
    }


def _observed_type_and_class(raw: Any) -> tuple[str, str, str]:
    if raw is None:
        return "null", "EMPTY", ""
    if isinstance(raw, bool):
        return "bool", "PRESENT_BOOL", str(raw).lower()
    if isinstance(raw, list):
        return "list", "PRESENT_LIST", f"LIST_LEN_{len(raw)}"
    if isinstance(raw, dict):
        return "object", "PRESENT_OBJECT", "OBJECT"
    text = str(raw).strip()
    if text == "":
        return "string", "EMPTY", ""
    try:
        as_float = float(text)
    except ValueError:
        return "string", "PRESENT_STRING", text
    if as_float == 0.0:
        return "string", "PRESENT_ZERO", text
    return "string", "PRESENT_NONZERO", text


def _is_empty_observed(raw: Any) -> bool:
    return raw is None or raw == ""


def _union_row_fields(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for row in rows:
        for key, value in row.items():
            name = str(key)
            if name not in merged:
                merged[name] = value
                continue
            if _is_empty_observed(merged[name]) and not _is_empty_observed(value):
                merged[name] = value
    return merged


def _field_record(
    *,
    field_name: str,
    field_path: str,
    source_endpoint: str,
    raw: Any,
    existing_canonical_semantic: str,
    existing_canonical_contract: str,
    peak_trade_target_kind: str,
    classification_status: str,
    ratification_status: str,
    requires_ratification_workpackage: str,
    high_value_unratified_candidate: str,
    kind_set_resolution_blocker: str,
    contract_rule: str,
) -> dict[str, str]:
    observed_type, value_class, observed_value = _observed_type_and_class(raw)
    if field_name in REDACT_FIELD_NAMES:
        observed_value = REDACTED_VALUE
    return {
        "raw_venue_field": field_name,
        "field_path": field_path,
        "observed_value": observed_value,
        "observed_type": observed_type,
        "observed_value_class": value_class,
        "source_endpoint": source_endpoint,
        "existing_canonical_semantic": existing_canonical_semantic,
        "existing_canonical_contract": existing_canonical_contract,
        "peak_trade_target_kind": peak_trade_target_kind,
        "classification_status": classification_status,
        "ratification_status": ratification_status,
        "requires_ratification_workpackage": requires_ratification_workpackage,
        "high_value_unratified_candidate": high_value_unratified_candidate,
        "kind_set_resolution_blocker": kind_set_resolution_blocker,
        "observation_is_not_kind_ratification": TRUE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "contract_rule": contract_rule,
    }


def _classify_one_field(
    *, scope: str, field_name: str, raw: Any, source_endpoint: str
) -> dict[str, str]:
    path = f"{scope}.{field_name}"
    default_contract = (
        "NO_UNIQUE_D6_CLASS_C_FIELD_BINDING;observation_of_name_or_value_is_not_kind_ratification"
    )
    if field_name in D4_IDENTITY_FIELDS and scope == "config":
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic=D4_CORROBORATED,
            existing_canonical_contract=(
                "path_b_class_c_package_1_trading_account_observation_rules_contract_v1;"
                "d4_genesis_fresh_account_config_bootstrap_v1"
            ),
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_MAPPED_RATIFIED,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="D4_POST_GENESIS_OBSERVATION_MUST_NOT_MINT_IDENTITY",
        )
    if field_name in D4_SETTLEMENT_FIELDS and scope == "config":
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="SETTLEMENT_CURRENCY_RUNTIME_EVIDENCE_ONLY",
            existing_canonical_contract="d4_genesis_fresh_account_config_bootstrap_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_MAPPED_RATIFIED,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="D4_OBSERVED_FIELDS_ARE_RUNTIME_EVIDENCE_ONLY",
        )
    if field_name in D4_ACCOUNT_MODE_FIELDS and scope == "config":
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic=U01_ACCOUNT_MODE_ROLE,
            existing_canonical_contract="reconstruction_algebra_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_MAPPED_RATIFIED,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="U01_ACCOUNT_MODE_IS_ELIGIBILITY_CONTEXT_NOT_NUMERIC_EQUITY",
        )
    if scope == "subtypes":
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="CATALOG_METADATA_NOT_EVENT_KIND",
            existing_canonical_contract="path_b_class_c_package_1_trading_account_observation_rules_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_NOT_APPLICABLE,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="SUBTYPES_QUERY_RESULT_IS_NOT_KIND_COMPLETENESS",
        )
    if field_name == EQ_VENUE_FIELD_NAME and scope == "details":
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic=EQ_RECONCILIATION_OBSERVATION_SEMANTIC,
            existing_canonical_contract="fresh_eq_reconciliation_target_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_MAPPED_RATIFIED,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="EQ_IS_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY_NOT_SOURCE",
        )
    if field_name in C01_AVAILEQ_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="REJECTED_C01_AVAILABLE_MARGIN_NOT_29P_EQUITY",
            existing_canonical_contract="source_candidate_census_v1;source_candidate_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_NOT_APPLICABLE,
            ratification_status=RATIFICATION_REJECTION,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="C01_REHABILITATION_FORBIDDEN",
        )
    if field_name in C02_FORBIDDEN_SOURCE_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="REJECTED_C02_FORBIDDEN_RAW_VENUE_EQ_FIELD_NOT_SOURCE",
            existing_canonical_contract="option_d_ssot_architecture_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_NOT_APPLICABLE,
            ratification_status=RATIFICATION_REJECTION,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="FORBIDDEN_SOURCE_FIELDS_CANNOT_BECOME_EQUITY_SOURCE",
        )
    if field_name in U05_EMBEDDING_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED",
            existing_canonical_contract=(
                "reconstruction_algebra_contract_v1;"
                "path_b_class_c_package_1_trading_account_observation_rules_contract_v1"
            ),
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_AMBIGUOUS,
            ratification_status=RATIFICATION_AMBIGUOUS,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=TRUE_TOKEN,
            contract_rule="F12_F13_REMAIN_UNKNOWN;U05_KIND_DECISION=REMAIN_UNKNOWN",
        )
    if field_name in U06_FEE_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="U06_FEE_INCLUSION_UNRESOLVED",
            existing_canonical_contract=(
                "reconstruction_algebra_contract_v1;"
                "classified_event_kind_set_and_source_seam_contract_v1"
            ),
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_AMBIGUOUS,
            ratification_status=RATIFICATION_AMBIGUOUS,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=TRUE_TOKEN,
            contract_rule="F16_F17_F18_REMAIN_UNKNOWN;U06_KIND_DECISION=REMAIN_UNKNOWN",
        )
    if field_name in INTEREST_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="HYPOTHESIS_ONLY_INTEREST_NOT_RATIFIED_KIND",
            existing_canonical_contract="constants_v1.HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_AMBIGUOUS,
            ratification_status=RATIFICATION_AMBIGUOUS,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=TRUE_TOKEN,
            contract_rule="INTEREST_IS_HYPOTHESIS_ONLY;NO_INCLUDE_FROM_UNKNOWN",
        )
    if field_name in U03_UPL_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="U03_UNREALIZED_PNL_MTM_NOT_EVENT_KIND_FIELD_BINDING_UNPROVEN",
            existing_canonical_contract="classified_event_kind_set_and_source_seam_contract_v1;reconstruction_algebra_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_AMBIGUOUS,
            ratification_status=RATIFICATION_AMBIGUOUS,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="U03_IS_ALGEBRA_TERM_NOT_EVENT_KIND;NAME_IS_NOT_BINDING",
        )
    if field_name in U04_FROZEN_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED",
            existing_canonical_contract="reconstruction_algebra_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_AMBIGUOUS,
            ratification_status=RATIFICATION_AMBIGUOUS,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="U04_IS_NOT_EQUITY_STOCK_KIND;FIELD_BINDING_UNPROVEN",
        )
    if field_name in MARGIN_DIMENSION_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic=f"{DIMENSION_MARGIN_REQUIREMENTS}_DIMENSION_EXISTS_UNBOUND",
            existing_canonical_contract="option_d_ssot_architecture_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_AMBIGUOUS,
            ratification_status=RATIFICATION_AMBIGUOUS,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="MARGIN_REQUIREMENTS_DIMENSION_HAS_NO_ACCOUNT_BALANCE_FIELD_BINDING",
        )
    if field_name in NOTIONAL_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic=VALUATION_NOTIONAL_PROHIBITED_AS_ADDEND,
            existing_canonical_contract="reconstruction_algebra_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_NOT_APPLICABLE,
            ratification_status=RATIFICATION_REJECTION,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="NOTIONAL_PROHIBITED_AS_EQUITY_STOCK_ADDEND",
        )
    if field_name in BILL_KIND_TOKEN_FIELDS and scope in {"bills", "bills-archive"}:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="VENUE_TYPE_TOKEN_NOT_RATIFIED_CLASSIFIED_KIND",
            existing_canonical_contract="equity_affecting_event_taxonomy_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_OBSERVED_UNRATIFIED,
            ratification_status=RATIFICATION_UNRATIFIED,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=TRUE_TOKEN,
            contract_rule="RATIFIED_CLASSIFIED_KIND_SET_EMPTY;VENUE_TYPE_IS_NOT_KIND",
        )
    if field_name in BILL_EVENT_IDENTITY_FIELDS and scope in {"bills", "bills-archive"}:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="FORENSIC_EVENT_IDENTITY_OR_ORDERING_KEY",
            existing_canonical_contract="equity_affecting_event_taxonomy_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_MAPPED_RATIFIED,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="ORDERING_COMPLETENESS_REMAINS_FAIL_CLOSED_NOT_PROVEN",
        )
    if field_name in PNL_FIELDS and scope in {"bills", "bills-archive", "details"}:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="U02_REALIZED_PNL_NOT_EVENT_KIND_FIELD_BINDING_UNPROVEN",
            existing_canonical_contract="classified_event_kind_set_and_source_seam_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_AMBIGUOUS,
            ratification_status=RATIFICATION_AMBIGUOUS,
            requires_ratification_workpackage=TRUE_TOKEN,
            high_value_unratified_candidate=TRUE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="U02_IS_ALGEBRA_TERM_NOT_EVENT_KIND;NAME_IS_NOT_BINDING",
        )
    if field_name in CURRENCY_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="CURRENCY_DOMAIN_OBSERVATION_NOT_U08_CONVERSION_AUTHORITY",
            existing_canonical_contract="reconstruction_algebra_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_MAPPED_RATIFIED,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="U08_REQUIRES_USDC_NATIVE_OR_OWNER_RATIFIED_CONVERSION_CONTRACT",
        )
    if field_name in BALANCE_ALLOWED_OBSERVATION_FIELDS and scope in {"details", "account"}:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="ALLOWED_BALANCE_OBSERVATION_FIELD_AUTHORITY_NONE",
            existing_canonical_contract="path_b_class_c_package_1_trading_account_observation_rules_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_MAPPED_RATIFIED,
            ratification_status=RATIFICATION_CONTRACT_SEMANTIC,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="BALANCE_OBSERVATION_ALLOWED_FIELDS_HAVE_AUTHORITY_EFFECT_NONE",
        )
    if field_name in P01_REJECTED_VENUE_FIELDS:
        return _field_record(
            field_name=field_name,
            field_path=path,
            source_endpoint=source_endpoint,
            raw=raw,
            existing_canonical_semantic="REJECTED_VENUE_RAW_NOT_P01",
            existing_canonical_contract="p01_numeric_value_provenance_contract_v1",
            peak_trade_target_kind=TARGET_KIND_NONE,
            classification_status=STATUS_NOT_APPLICABLE,
            ratification_status=RATIFICATION_REJECTION,
            requires_ratification_workpackage=FALSE_TOKEN,
            high_value_unratified_candidate=FALSE_TOKEN,
            kind_set_resolution_blocker=FALSE_TOKEN,
            contract_rule="VENUE_RAW_FIELDS_ARE_NOT_P01",
        )
    hypothesis = ",".join(HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES)
    return _field_record(
        field_name=field_name,
        field_path=path,
        source_endpoint=source_endpoint,
        raw=raw,
        existing_canonical_semantic="NONE_NAMED",
        existing_canonical_contract="NONE_NAMED",
        peak_trade_target_kind=TARGET_KIND_NONE,
        classification_status=STATUS_OBSERVED_UNRATIFIED,
        ratification_status=RATIFICATION_UNRATIFIED,
        requires_ratification_workpackage=TRUE_TOKEN,
        high_value_unratified_candidate=FALSE_TOKEN,
        kind_set_resolution_blocker=FALSE_TOKEN,
        contract_rule=f"{default_contract};hypothesis_only_classes={hypothesis}",
    )


def _classify_observed_fields(
    *,
    surfaces: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    config_rows = _rows_from_observation(payload=surfaces[SURFACE_ACCOUNT_CONFIG])
    for name, raw in _union_row_fields(rows=config_rows).items():
        records.append(
            _classify_one_field(
                scope="config",
                field_name=name,
                raw=raw,
                source_endpoint=SURFACE_ACCOUNT_CONFIG,
            )
        )
    balance_rows = _rows_from_observation(payload=surfaces[SURFACE_ACCOUNT_BALANCE])
    account_fields = _union_row_fields(rows=balance_rows)
    details_rows: list[dict[str, Any]] = []
    for row in balance_rows:
        details = row.get("details")
        if isinstance(details, list):
            details_rows.extend(item for item in details if isinstance(item, dict))
    for name, raw in account_fields.items():
        if name == "details":
            continue
        records.append(
            _classify_one_field(
                scope="account",
                field_name=name,
                raw=raw,
                source_endpoint=SURFACE_ACCOUNT_BALANCE,
            )
        )
    for name, raw in _union_row_fields(rows=details_rows).items():
        records.append(
            _classify_one_field(
                scope="details",
                field_name=name,
                raw=raw,
                source_endpoint=SURFACE_ACCOUNT_BALANCE,
            )
        )
    subtype_rows = _rows_from_observation(payload=surfaces[SURFACE_ACCOUNT_SUBTYPES])
    for name, raw in _union_row_fields(rows=subtype_rows).items():
        records.append(
            _classify_one_field(
                scope="subtypes",
                field_name=name,
                raw=raw,
                source_endpoint=SURFACE_ACCOUNT_SUBTYPES,
            )
        )
    bills_rows = _rows_from_observation(payload=surfaces[SURFACE_ACCOUNT_BILLS])
    for name, raw in _union_row_fields(rows=bills_rows).items():
        records.append(
            _classify_one_field(
                scope="bills",
                field_name=name,
                raw=raw,
                source_endpoint=SURFACE_ACCOUNT_BILLS,
            )
        )
    archive_rows = _rows_from_observation(payload=surfaces[SURFACE_ACCOUNT_BILLS_ARCHIVE])
    for name, raw in _union_row_fields(rows=archive_rows).items():
        records.append(
            _classify_one_field(
                scope="bills-archive",
                field_name=name,
                raw=raw,
                source_endpoint=SURFACE_ACCOUNT_BILLS_ARCHIVE,
            )
        )
    return records


def _summarize_field_records(records: list[dict[str, str]]) -> dict[str, str]:
    grouped: dict[str, list[str]] = {
        STATUS_MAPPED_RATIFIED: [],
        STATUS_OBSERVED_UNRATIFIED: [],
        STATUS_AMBIGUOUS: [],
        STATUS_NOT_APPLICABLE: [],
    }
    ratification_candidates: list[str] = []
    high_value: list[str] = []
    blockers: list[str] = []
    for record in records:
        status = record["classification_status"]
        grouped.setdefault(status, []).append(record["field_path"])
        if record["requires_ratification_workpackage"] == TRUE_TOKEN:
            ratification_candidates.append(record["field_path"])
        if record["high_value_unratified_candidate"] == TRUE_TOKEN:
            high_value.append(record["field_path"])
        if record["kind_set_resolution_blocker"] == TRUE_TOKEN:
            blockers.append(record["field_path"])
    kind_set_blockers = [
        "RATIFIED_CLASSIFIED_KIND_SET_EMPTY",
        "U05_KIND_DECISION=REMAIN_UNKNOWN",
        "U06_KIND_DECISION=REMAIN_UNKNOWN",
        "RESIDUAL_KIND_DECISION=REMAIN_UNKNOWN",
        "F12_F13_F16_F17_F18_UNKNOWN",
        "RETENTION_COVERAGE_FAIL_CLOSED_NOT_PROVEN",
        "ORDERING_COMPLETENESS_FAIL_CLOSED_NOT_PROVEN",
        *blockers,
    ]
    return {
        "observed_relevant_field_count": str(len(records)),
        "mapped_ratified_fields": ",".join(grouped[STATUS_MAPPED_RATIFIED]),
        "observed_unratified_fields": ",".join(grouped[STATUS_OBSERVED_UNRATIFIED]),
        "ambiguous_fields": ",".join(grouped[STATUS_AMBIGUOUS]),
        "not_applicable_fields": ",".join(grouped[STATUS_NOT_APPLICABLE]),
        "ratification_candidates": ",".join(ratification_candidates),
        "high_value_unratified_candidates": ",".join(high_value),
        "kind_set_resolution_blockers": ",".join(kind_set_blockers),
    }


def execute_package_1_s6_mapping_classification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_observation_pack: Path | str,
    genesis_store_root: Path | str,
    evidence_root: Path | str,
    mapping_as_of: str | None = None,
) -> Package1S6MappingClassificationResultV1:
    if owner_go != OWNER_GO:
        raise Package1S6MappingClassificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise Package1S6MappingClassificationError("ORIGIN_MAIN_SHA_MISMATCH")
    if KIND_SET_RESOLVED is not False:
        raise Package1S6MappingClassificationError("STANDING_KIND_SET_RESOLVED_NOT_FALSE")
    if MS2_AUTHORIZED is not False:
        raise Package1S6MappingClassificationError("STANDING_MS2_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise Package1S6MappingClassificationError("STANDING_RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise Package1S6MappingClassificationError("RATIFIED_KIND_SET_MUST_REMAIN_EMPTY")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise Package1S6MappingClassificationError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise Package1S6MappingClassificationError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise Package1S6MappingClassificationError("RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    sealed = Path(sealed_observation_pack)
    genesis = Path(genesis_store_root)
    manifest_rc = verify_manifest_sha256_v1(store_root=sealed)
    verify_manifest_sha256_v1(store_root=genesis)
    missing = [name for name in REQUIRED_SEALED_FILES if not (sealed / name).is_file()]
    if missing:
        raise Package1S6MappingClassificationError(f"SEALED_INPUT_FILE_MISSING:{missing[0]}")
    claims = _load_json_object(path=sealed / "claims.json")
    _require_token(field="GENESIS_ID", payload=claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="GENESIS_AS_OF", payload=claims, expected=EXPECTED_GENESIS_AS_OF)
    _require_token(field="AUTHORIZED_GET_SURFACE_COUNT", payload=claims, expected="5")
    _require_token(field="UNAUTHORIZED_GET_SURFACE_COUNT", payload=claims, expected="0")
    _require_token(field="NETWORK_POST_PERFORMED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="D4_IDENTITY_MINTED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="RAW_EQ_SOURCE_AUTHORITY", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="S6_EXECUTED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="RAW_EVIDENCE_SEALED", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="D4_CORROBORATION_RESULT", payload=claims, expected=D4_CORROBORATED)
    _require_token(
        field="RETENTION_COVERAGE_STATUS",
        payload=claims,
        expected=RETENTION_COVERAGE_FAIL_CLOSED,
    )
    _require_token(
        field="ORDERING_COMPLETENESS_STATUS",
        payload=claims,
        expected=ORDERING_COMPLETENESS_FAIL_CLOSED,
    )
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis)
    if d4.identity_digest != str(claims.get("D4_IDENTITY_DIGEST") or ""):
        raise Package1S6MappingClassificationError("D4_IDENTITY_DIGEST_DRIFT")
    if d4.instance_digest != str(claims.get("D4_INSTANCE_DIGEST") or ""):
        raise Package1S6MappingClassificationError("D4_INSTANCE_DIGEST_DRIFT")
    surfaces = {
        surface_id: _load_json_object(path=sealed / filename)
        for surface_id, filename in SURFACE_FILE_BY_ID.items()
    }
    overlap = _load_json_object(path=sealed / "s4_bills_pair_overlap_v1.json")
    seal = _load_json_object(path=sealed / "s5_raw_evidence_seal_v1.json")
    if str(seal.get("network_post_performed") or "") != FALSE_TOKEN:
        raise Package1S6MappingClassificationError("SEALED_POST_NOT_FALSE")
    census_index = _census_candidate_index()
    classification_records: list[dict[str, str]] = []
    observed_type_tokens: set[str] = set()
    observed_subtype_tokens: set[str] = set()
    for surface_id in BILL_SURFACES:
        payload = surfaces[surface_id]
        source_digest = str(payload.get("payload_digest") or "")
        if not source_digest:
            raise Package1S6MappingClassificationError(f"SOURCE_PAYLOAD_DIGEST_ABSENT:{surface_id}")
        for index, row in enumerate(_rows_from_observation(payload=payload)):
            record = _classify_bill_row(
                surface_id=surface_id,
                row=row,
                row_index=index,
                source_payload_digest=source_digest,
                identity_digest=d4.identity_digest,
                census_index=census_index,
            )
            if record["observed_type_token"]:
                observed_type_tokens.add(record["observed_type_token"])
            if record["observed_subtype_token"]:
                observed_subtype_tokens.add(record["observed_subtype_token"])
            classification_records.append(record)
    embedding_facts = []
    for fact_id in EMBEDDING_FACTS_REMAIN_UNKNOWN:
        reject_include_exclude_from_unknown_embedding_v1(
            decision=DECISION_REMAIN_UNKNOWN,
            fact_id=fact_id,
        )
        embedding_facts.append(
            {
                "fact_id": fact_id,
                "status": "UNKNOWN",
                "decision": DECISION_REMAIN_UNKNOWN,
                "include_from_unknown": "FORBIDDEN",
                "exclude_from_unknown": "FORBIDDEN",
                "contract_rule": "reject_include_exclude_from_unknown_embedding_v1",
            }
        )
    subtypes_mapping = _classify_subtypes(payload=surfaces[SURFACE_ACCOUNT_SUBTYPES])
    balance_mapping = _classify_balance(payload=surfaces[SURFACE_ACCOUNT_BALANCE])
    config_mapping = _classify_config(payload=surfaces[SURFACE_ACCOUNT_CONFIG])
    field_records = _classify_observed_fields(surfaces=surfaces)
    field_summary = _summarize_field_records(field_records)
    unresolved = (
        f"{CANDIDATE_U05},{CANDIDATE_U06},{CANDIDATE_RESIDUAL},"
        "ALL_OBSERVED_VENUE_BILL_TYPE_TOKENS_UNCLASSIFIED,"
        "F12_LIABILITY_AFFECTS_EQUITY_STOCK,"
        "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ,"
        "F16_FEE_ALREADY_EMBEDDED_IN_EQ,"
        "F17_FEE_SEPARATE_ACCOUNT_DELTA,"
        "F18_FEE_RECONCILIATION_ONLY,"
        "SUBTYPES_CATALOG_NOT_KIND_COMPLETENESS,"
        "RETENTION_COVERAGE_NOT_PROVEN,"
        "ORDERING_COMPLETENESS_NOT_PROVEN"
    )
    as_of = mapping_as_of if mapping_as_of is not None else _utc_now_z()
    pack_root = Path(evidence_root) / _folder_from_as_of(as_of)
    pack_root.mkdir(parents=True, exist_ok=True)
    observed_types = ",".join(sorted(observed_type_tokens))
    observed_subtypes = ",".join(sorted(observed_subtype_tokens))
    input_digests = {
        name: _sha256_bytes((sealed / name).read_bytes()) for name in REQUIRED_SEALED_FILES
    }
    s6_claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "MAPPING_AS_OF": as_of,
        "SEALED_INPUT_PACK": str(sealed),
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "MANIFEST_VERIFY_RC": str(manifest_rc),
        "S6_EXECUTED": TRUE_TOKEN,
        "OBSERVED_KIND_SET": OBSERVED_KIND_SET_EMPTY,
        "OBSERVED_VENUE_TYPE_TOKEN_SET": observed_types,
        "OBSERVED_VENUE_SUBTYPE_TOKEN_SET": observed_subtypes,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "RATIFIED_CLASSIFIED_EVENT_KIND_SET": RATIFIED_CLASSIFIED_EVENT_KIND_SET_TOKEN,
        "UNRESOLVED_KINDS_OR_AMBIGUITIES": unresolved,
        "MAPPING_PERSISTED": FALSE_TOKEN,
        "MAPPING_COVERAGE_STATUS": MAPPING_COVERAGE_FAIL_CLOSED,
        "CLASSIFICATION_RECORDS_PERSISTED": TRUE_TOKEN,
        "CLASSIFIED_BILL_ROW_COUNT": str(len(classification_records)),
        "RETENTION_COVERAGE_STATUS": RETENTION_COVERAGE_FAIL_CLOSED,
        "ORDERING_COMPLETENESS_STATUS": ORDERING_COMPLETENESS_FAIL_CLOSED,
        "BILLS_ARCHIVE_OVERLAP_STATUS": str(overlap.get("bills_archive_overlap_status") or ""),
        "PARTIAL_OVERLAP_IS_NOT_RETENTION_COMPLETENESS": TRUE_TOKEN,
        "PARTIAL_OVERLAP_IS_NOT_ORDERING_COMPLETENESS": TRUE_TOKEN,
        "D4_CORROBORATION_RESULT": D4_CORROBORATED,
        "D4_IDENTITY_MINTED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "NEW_NETWORK_GET_COUNT": "0",
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "MS2_EXECUTED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "ATLAS_AUTHORITY": "NONE",
        "AUTHORITY_EFFECT": "NONE",
        "D4_IDENTITY_DIGEST": d4.identity_digest,
        "D4_INSTANCE_DIGEST": d4.instance_digest,
        "OBSERVED_RELEVANT_FIELD_COUNT": field_summary["observed_relevant_field_count"],
        "MAPPED_RATIFIED_FIELDS": field_summary["mapped_ratified_fields"],
        "OBSERVED_UNRATIFIED_FIELDS": field_summary["observed_unratified_fields"],
        "AMBIGUOUS_FIELDS": field_summary["ambiguous_fields"],
        "NOT_APPLICABLE_FIELDS": field_summary["not_applicable_fields"],
        "RATIFICATION_CANDIDATES": field_summary["ratification_candidates"],
        "HIGH_VALUE_UNRATIFIED_CANDIDATES": field_summary["high_value_unratified_candidates"],
        "KIND_SET_RESOLUTION_BLOCKERS": field_summary["kind_set_resolution_blockers"],
        "FIELD_SEMANTIC_TRACE_PERSISTED": TRUE_TOKEN,
    }
    _persist_json(path=pack_root / "claims.json", payload=s6_claims)
    _persist_json(
        path=pack_root / "s6_classification_records_v1.json",
        payload={
            "classification_records_persisted": TRUE_TOKEN,
            "classified_bill_row_count": str(len(classification_records)),
            "mapping_persisted": FALSE_TOKEN,
            "records": classification_records,
        },
    )
    _persist_json(
        path=pack_root / "s6_observed_type_inventory_v1.json",
        payload={
            "observed_kind_set": OBSERVED_KIND_SET_EMPTY,
            "observed_venue_type_token_set": observed_types,
            "observed_venue_subtype_token_set": observed_subtypes,
            "ratified_classified_event_kind_set": RATIFIED_CLASSIFIED_EVENT_KIND_SET_TOKEN,
            "kind_set_resolved": FALSE_TOKEN,
            "venue_type_tokens_are_not_ratified_kinds": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=pack_root / "s6_surface_mapping_v1.json",
        payload={
            "config": config_mapping,
            "balance": balance_mapping,
            "subtypes": subtypes_mapping,
            "bills": {
                "surface_id": SURFACE_ACCOUNT_BILLS,
                "atlas_authority": "NONE",
                "account_bills_remains_current_noncanonical": TRUE_TOKEN,
                "candidate_surface_selection": "NONE_SELECTED",
                "kind_ratification": "FORBIDDEN",
            },
            "bills_archive": {
                "surface_id": SURFACE_ACCOUNT_BILLS_ARCHIVE,
                "atlas_authority": "NONE",
                "kind_ratification": "FORBIDDEN",
            },
        },
    )
    _persist_json(
        path=pack_root / "s6_embedding_facts_v1.json",
        payload={"facts": embedding_facts, "include_exclude_from_unknown": "FORBIDDEN"},
    )
    _persist_json(
        path=pack_root / "s6_kind_set_adjudication_v1.json",
        payload={
            "observed_kind_set": OBSERVED_KIND_SET_EMPTY,
            "kind_set_resolved": FALSE_TOKEN,
            "u05_kind_decision": U05_KIND_DECISION,
            "u06_kind_decision": U06_KIND_DECISION,
            "residual_kind_decision": RESIDUAL_KIND_DECISION,
            "unresolved_kinds_or_ambiguities": unresolved,
            "mapping_coverage_status": MAPPING_COVERAGE_FAIL_CLOSED,
            "mapping_persisted": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=pack_root / "s6_observed_field_classification_v1.json",
        payload={
            "field_semantic_trace_persisted": TRUE_TOKEN,
            "mapping_persisted": FALSE_TOKEN,
            "raw_eq_source_authority": FALSE_TOKEN,
            "observation_is_not_kind_ratification": TRUE_TOKEN,
            "observed_relevant_field_count": field_summary["observed_relevant_field_count"],
            "mapped_ratified_fields": field_summary["mapped_ratified_fields"],
            "observed_unratified_fields": field_summary["observed_unratified_fields"],
            "ambiguous_fields": field_summary["ambiguous_fields"],
            "not_applicable_fields": field_summary["not_applicable_fields"],
            "ratification_candidates": field_summary["ratification_candidates"],
            "high_value_unratified_candidates": field_summary["high_value_unratified_candidates"],
            "kind_set_resolution_blockers": field_summary["kind_set_resolution_blockers"],
            "records": field_records,
        },
    )
    _persist_json(
        path=pack_root / "s6_input_provenance_v1.json",
        payload={
            "sealed_input_only": TRUE_TOKEN,
            "sealed_input_pack": str(sealed),
            "manifest_verify_rc": str(manifest_rc),
            "new_network_get_count": "0",
            "network_post_performed": FALSE_TOKEN,
            "input_file_sha256": input_digests,
            "observation_as_of": str(claims.get("OBSERVATION_AS_OF") or ""),
            "d4_identity_digest": d4.identity_digest,
            "d4_instance_digest": d4.instance_digest,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=pack_root)
    return Package1S6MappingClassificationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        mapping_as_of=as_of,
        store_root=str(pack_root),
        sealed_input_pack=str(sealed),
        sealed_input_only=TRUE_TOKEN,
        manifest_verify_rc=str(manifest_rc),
        s6_executed=TRUE_TOKEN,
        observed_kind_set=OBSERVED_KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        unresolved_kinds_or_ambiguities=unresolved,
        mapping_persisted=FALSE_TOKEN,
        mapping_coverage_status=MAPPING_COVERAGE_FAIL_CLOSED,
        classification_records_persisted=TRUE_TOKEN,
        classified_bill_row_count=str(len(classification_records)),
        retention_coverage_status=RETENTION_COVERAGE_FAIL_CLOSED,
        ordering_completeness_status=ORDERING_COMPLETENESS_FAIL_CLOSED,
        d4_corroboration_result=D4_CORROBORATED,
        d4_identity_minted=FALSE_TOKEN,
        raw_eq_source_authority=FALSE_TOKEN,
        new_network_get_count="0",
        network_post_performed=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        ms2_executed=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        observed_relevant_field_count=field_summary["observed_relevant_field_count"],
        mapped_ratified_fields=field_summary["mapped_ratified_fields"],
        observed_unratified_fields=field_summary["observed_unratified_fields"],
        ambiguous_fields=field_summary["ambiguous_fields"],
        not_applicable_fields=field_summary["not_applicable_fields"],
        ratification_candidates=field_summary["ratification_candidates"],
        high_value_unratified_candidates=field_summary["high_value_unratified_candidates"],
        kind_set_resolution_blockers=field_summary["kind_set_resolution_blockers"],
        evidence_manifest=str(manifest),
    )
