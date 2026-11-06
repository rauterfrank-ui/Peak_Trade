"""D6 source-mapping and classified event-stream acquisition.

Re-evaluates sealed S1-S6 plus #6452 source-role mapping against existing
D6/Class-C/algebra/census authority. Does not invent EQUITY_STOCK source
kinds. Does not treat eq as source authority. Does not GET or POST.
Does not authorize MS2 or D7. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    CANONICAL_S6_PACK_RELPATH,
    RATIFIED_SOURCE_KIND_SET,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    UNKNOWN_EMBEDDING_FACTS,
    UNKNOWN_NECESSARY_CLASS_REMAINS,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    reject_include_exclude_from_unknown_embedding_v1,
)

OWNER_GO = "OWNER_GO_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_AND_COMPLETE_EVENT_STREAM_ACQUISITION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "1dc7a601ca8403a658d242452abf984c21bdfb99"
CANONICAL_MAPPING_PACK_RELPATH = (
    "evidence/ops/full_core_d6_account_equity_source_mapping_ratification_v1/2026-09-13T192000Z"
)
ACQUISITION_STORE_RELPATH = (
    "evidence/ops/full_core_d6_source_mapping_and_complete_event_stream_acquisition_v1"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
RETENTION_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
EARLIEST_REMAINING_D6_BLOCKER = "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY = "F12_F13_F16_F17_F18_UNKNOWN"
COMPLETE_STREAM_ACQUISITION_STATUS = "FAIL_CLOSED_KIND_SET_AND_RETENTION_ORDERING_SEAM_UNPROVEN"
S2_BALANCE_FILE = "s2_account_balance_observation_v1.json"
S4_BILLS_FILE = "s4_account_bills_observation_v1.json"
S4_ARCHIVE_FILE = "s4_account_bills_archive_observation_v1.json"
S4_OVERLAP_FILE = "s4_bills_pair_overlap_v1.json"
MAPPING_CLAIMS_FILE = "claims.json"
U05_RAW_FIELDS: tuple[str, ...] = (
    "liab",
    "crossLiab",
    "isoLiab",
    "borrowFroz",
)
REQUIRED_OBSERVATION_FILES: tuple[str, ...] = (
    S2_BALANCE_FILE,
    S4_BILLS_FILE,
    S4_ARCHIVE_FILE,
    S4_OVERLAP_FILE,
)


class AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(ValueError):
    """Fail-closed D6 acquisition violation."""


@dataclass(frozen=True)
class AccountEquitySourceMappingAndCompleteEventStreamAcquisitionResultV1:
    genesis_id: str
    genesis_as_of: str
    acquisition_as_of: str
    store_root: str
    ratified_source_kinds: str
    kind_set: str
    kind_set_resolved: str
    mapping_persisted: str
    raw_eq_source_authority: str
    u05_kind_decision: str
    u06_kind_decision: str
    residual_kind_decision: str
    f12_f13_f16_f17_f18_status: str
    retention_coverage_status: str
    ordering_completeness_status: str
    authorized_productive_event_source_seam: str
    complete_classified_event_stream_proven: str
    earliest_remaining_d6_blocker: str
    earliest_unresolved_full_core_dependency: str
    new_network_get_count: str
    network_post_performed: str
    ms2_authorized: str
    d6_fully_closed: str
    d7_authorized: str
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
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            f"JSON_NOT_OBJECT:{path.name}"
        )
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            f"{field}_DRIFT:{actual}"
        )


def _raw_token(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, bool):
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "FORENSIC_BOOL_TOKEN_FORBIDDEN"
        )
    if isinstance(raw, (int, float)):
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "FORENSIC_NUMERIC_NORMALIZATION_FORBIDDEN"
        )
    if not isinstance(raw, str):
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "FORENSIC_TOKEN_NOT_STRING"
        )
    return raw


def reject_observed_value_as_kind_absence_or_embedding_decision_v1(
    *,
    claimed_proof: str,
    fact_id: str,
) -> None:
    if claimed_proof in {
        "KIND_ABSENCE",
        "ZERO_EVENTS",
        "INCLUDE",
        "EXCLUDE",
        "F12_TRUE",
        "F13_TRUE",
        "F16_TRUE",
        "F17_TRUE",
        "F18_TRUE",
        "EMPTY_MEANS_UNEMBEDDED",
        "ZERO_MEANS_EMBEDDED",
        "FEE_ZERO_MEANS_EMBEDDED",
    }:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            f"FORENSIC_VALUE_CANNOT_{claimed_proof}:{fact_id}"
        )
    if claimed_proof != "NO_UNIQUE_EMBEDDING_OR_KIND_DECISION":
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            f"FORENSIC_PROOF_UNKNOWN:{claimed_proof}"
        )
    if fact_id not in UNKNOWN_EMBEDDING_FACTS and fact_id != "KIND_ABSENCE":
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            f"FORENSIC_FACT_NOT_IN_UNKNOWN_SET:{fact_id}"
        )


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "SOURCE_KIND_SET_MUST_REMAIN_EMPTY"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if UNKNOWN_NECESSARY_CLASS_REMAINS is not True:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "UNKNOWN_NECESSARY_CLASS_MUST_REMAIN"
        )
    if MS2_AUTHORIZED is not False:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "MS2_AUTHORIZED_NOT_FALSE"
        )
    if D6_FULLY_CLOSED is not False:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "D6_FULLY_CLOSED_NOT_FALSE"
        )
    if D7_AUTHORIZED is not False:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "D7_AUTHORIZED_NOT_FALSE"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED_NOT_FALSE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "PRODUCTIVE_EVENT_SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )


def _unique_sorted_tokens(values: list[str]) -> str:
    return ",".join(sorted(set(values)))


def _extract_forensic_balance(*, observation: Path) -> dict[str, Any]:
    payload = _load_json_object(path=observation / S2_BALANCE_FILE)
    embedding = payload.get("reconciliation_or_embedding_fields")
    if not isinstance(embedding, list):
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "S2_EMBEDDING_FIELDS_NOT_LIST"
        )
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError("S2_ROWS_MISSING")
    account_borrow = _raw_token(rows[0].get("borrowFroz"))
    details: list[dict[str, str]] = []
    for item in embedding:
        if not isinstance(item, dict):
            raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
                "S2_EMBEDDING_ITEM_NOT_OBJECT"
            )
        details.append(
            {
                "ccy": _raw_token(item.get("ccy")),
                "eq": _raw_token(item.get("eq")),
                "cashBal": _raw_token(item.get("cashBal")),
                "liab": _raw_token(item.get("liab")),
                "crossLiab": _raw_token(item.get("crossLiab")),
                "isoLiab": _raw_token(item.get("isoLiab")),
                "interest": _raw_token(item.get("interest")),
                "upl": _raw_token(item.get("upl")),
                "uplLiab": _raw_token(item.get("uplLiab")),
                "uTime": _raw_token(item.get("uTime")),
            }
        )
    return {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "interpretation_status": "FORBIDDEN",
        "account_borrowFroz": account_borrow,
        "details": details,
        "empty_or_zero_or_blank_does_not_prove_kind_absence": TRUE_TOKEN,
        "eq_remains_reconciliation_target_only": TRUE_TOKEN,
    }


def _extract_forensic_bills(*, observation: Path) -> dict[str, Any]:
    live = _load_json_object(path=observation / S4_BILLS_FILE)
    archive = _load_json_object(path=observation / S4_ARCHIVE_FILE)
    overlap = _load_json_object(path=observation / S4_OVERLAP_FILE)
    live_rows = live.get("rows")
    archive_rows = archive.get("rows")
    if not isinstance(live_rows, list) or not isinstance(archive_rows, list):
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError("S4_ROWS_NOT_LIST")
    live_fees = [_raw_token(row.get("fee")) for row in live_rows if isinstance(row, dict)]
    archive_fees = [_raw_token(row.get("fee")) for row in archive_rows if isinstance(row, dict)]
    live_types = [
        f"{_raw_token(row.get('type'))}/{_raw_token(row.get('subType'))}"
        for row in live_rows
        if isinstance(row, dict)
    ]
    archive_types = [
        f"{_raw_token(row.get('type'))}/{_raw_token(row.get('subType'))}"
        for row in archive_rows
        if isinstance(row, dict)
    ]
    _require_token(
        field="retention_coverage_status",
        payload=overlap,
        expected=RETENTION_FAIL_CLOSED,
    )
    _require_token(
        field="ordering_completeness_status",
        payload=overlap,
        expected=ORDERING_FAIL_CLOSED,
    )
    _require_token(
        field="empty_result_proves_zero_events",
        payload=overlap,
        expected=FALSE_TOKEN,
    )
    _require_token(
        field="pagination_exhaustion_proves_completeness",
        payload=overlap,
        expected=FALSE_TOKEN,
    )
    return {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "interpretation_status": "FORBIDDEN",
        "live_row_count": str(len(live_rows)),
        "archive_row_count": str(len(archive_rows)),
        "overlap_count": str(overlap.get("overlap_count") or ""),
        "bills_archive_overlap_status": str(overlap.get("bills_archive_overlap_status") or ""),
        "live_unique_fee_tokens": _unique_sorted_tokens(live_fees),
        "archive_unique_fee_tokens": _unique_sorted_tokens(archive_fees),
        "live_unique_type_subtype_tokens": _unique_sorted_tokens(live_types),
        "archive_unique_type_subtype_tokens": _unique_sorted_tokens(archive_types),
        "venue_type_tokens_are_not_ratified_kinds": TRUE_TOKEN,
        "fee_token_does_not_decide_f16_f17_f18": TRUE_TOKEN,
        "partial_overlap_does_not_prove_retention": TRUE_TOKEN,
        "observed_ts_does_not_prove_ordering_completeness": TRUE_TOKEN,
        "retention_coverage_status": RETENTION_FAIL_CLOSED,
        "ordering_completeness_status": ORDERING_FAIL_CLOSED,
    }


def execute_account_equity_source_mapping_and_complete_event_stream_acquisition_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_observation_pack: Path | str,
    sealed_s6_pack: Path | str,
    sealed_mapping_pack: Path | str,
    evidence_root: Path | str,
    acquisition_as_of: str,
) -> AccountEquitySourceMappingAndCompleteEventStreamAcquisitionResultV1:
    if owner_go != OWNER_GO:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "ORIGIN_MAIN_SHA_MISMATCH"
        )
    _assert_standing_pins()
    observation = Path(sealed_observation_pack)
    s6_pack = Path(sealed_s6_pack)
    mapping = Path(sealed_mapping_pack)
    observation_rc = verify_manifest_sha256_v1(store_root=observation)
    s6_rc = verify_manifest_sha256_v1(store_root=s6_pack)
    mapping_rc = verify_manifest_sha256_v1(store_root=mapping)
    if observation_rc != 0 or s6_rc != 0 or mapping_rc != 0:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            "MANIFEST_VERIFY_NOT_ZERO"
        )
    missing = [name for name in REQUIRED_OBSERVATION_FILES if not (observation / name).is_file()]
    if missing:
        raise AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError(
            f"OBSERVATION_FILE_MISSING:{missing[0]}"
        )
    mapping_claims = _load_json_object(path=mapping / MAPPING_CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=mapping_claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="GENESIS_AS_OF", payload=mapping_claims, expected=EXPECTED_GENESIS_AS_OF)
    _require_token(field="MAPPING_PERSISTED", payload=mapping_claims, expected=TRUE_TOKEN)
    _require_token(field="RATIFIED_SOURCE_KINDS", payload=mapping_claims, expected=NONE_TOKEN)
    _require_token(field="KIND_SET_RESOLVED", payload=mapping_claims, expected=FALSE_TOKEN)
    _require_token(field="RAW_EQ_SOURCE_AUTHORITY", payload=mapping_claims, expected=FALSE_TOKEN)
    _require_token(
        field="U05_KIND_DECISION", payload=mapping_claims, expected=DECISION_REMAIN_UNKNOWN
    )
    _require_token(
        field="U06_KIND_DECISION", payload=mapping_claims, expected=DECISION_REMAIN_UNKNOWN
    )
    _require_token(
        field="RESIDUAL_KIND_DECISION",
        payload=mapping_claims,
        expected=DECISION_REMAIN_UNKNOWN,
    )
    _require_token(field="MS2_AUTHORIZED", payload=mapping_claims, expected=FALSE_TOKEN)
    _require_token(field="D6_FULLY_CLOSED", payload=mapping_claims, expected=FALSE_TOKEN)
    _require_token(field="D7_AUTHORIZED", payload=mapping_claims, expected=FALSE_TOKEN)
    for fact_id in UNKNOWN_EMBEDDING_FACTS:
        reject_include_exclude_from_unknown_embedding_v1(
            decision=DECISION_REMAIN_UNKNOWN,
            fact_id=fact_id,
        )
        reject_observed_value_as_kind_absence_or_embedding_decision_v1(
            claimed_proof="NO_UNIQUE_EMBEDDING_OR_KIND_DECISION",
            fact_id=fact_id,
        )
    reject_observed_value_as_kind_absence_or_embedding_decision_v1(
        claimed_proof="NO_UNIQUE_EMBEDDING_OR_KIND_DECISION",
        fact_id="KIND_ABSENCE",
    )
    forensic_balance = _extract_forensic_balance(observation=observation)
    forensic_bills = _extract_forensic_bills(observation=observation)
    ranked = [
        {
            "rank": "1",
            "blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "members": ",".join(NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES),
            "blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "role": "EARLIEST_REMAINING_D6_BLOCKER",
            "include_exclude_from_unknown": "FORBIDDEN",
        },
        {
            "rank": "2",
            "blocker": "NO_RATIFIED_EQUITY_STOCK_SOURCE_KIND",
            "role": "CONSEQUENCE_OF_UNRESOLVED_KIND_SET",
            "blocked_by": EARLIEST_REMAINING_D6_BLOCKER,
        },
        {
            "rank": "3",
            "blocker": "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_ABSENT",
            "role": "DOWNSTREAM_OF_KIND_SET_AND_MS2_AND_BILLS_NONCANONICAL",
            "blocked_by": "KIND_SET_UNRESOLVED,MS2_UNAUTHORIZED,ACCOUNT_BILLS_CURRENT_NONCANONICAL",
        },
        {
            "rank": "4",
            "blocker": "RETENTION_COVERAGE_FAIL_CLOSED_NOT_PROVEN",
            "role": "INDEPENDENT_COMPLETENESS_NOT_EARLIEST_SOURCE_KIND_BLOCKER",
            "blocked_by": "PARTIAL_BILL_ID_OVERLAP_DOES_NOT_PROVE_RETENTION",
        },
        {
            "rank": "5",
            "blocker": "ORDERING_COMPLETENESS_FAIL_CLOSED_NOT_PROVEN",
            "role": "INDEPENDENT_COMPLETENESS_NOT_EARLIEST_SOURCE_KIND_BLOCKER",
            "blocked_by": "OBSERVED_TS_AND_BILLID_DO_NOT_PROVE_STREAM_ORDERING_COMPLETENESS",
        },
    ]
    remaining = (
        f"{EARLIEST_REMAINING_D6_BLOCKER},"
        f"{KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY},"
        "NO_RATIFIED_EQUITY_STOCK_SOURCE_KIND,"
        "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_ABSENT,"
        "RETENTION_COVERAGE_FAIL_CLOSED_NOT_PROVEN,"
        "ORDERING_COMPLETENESS_FAIL_CLOSED_NOT_PROVEN"
    )
    pack_root = Path(evidence_root) / _folder_from_as_of(acquisition_as_of)
    pack_root.mkdir(parents=True, exist_ok=True)
    result_claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "ACQUISITION_AS_OF": acquisition_as_of,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "NEW_NETWORK_GET_COUNT": "0",
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED": FALSE_TOKEN,
        "SEALED_OBSERVATION_PACK": CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
        "SEALED_S6_PACK": CANONICAL_S6_PACK_RELPATH,
        "SEALED_MAPPING_PACK": CANONICAL_MAPPING_PACK_RELPATH,
        "OBSERVATION_MANIFEST_VERIFY_RC": str(observation_rc),
        "S6_MANIFEST_VERIFY_RC": str(s6_rc),
        "MAPPING_MANIFEST_VERIFY_RC": str(mapping_rc),
        "MANIFESTS_VERIFY": TRUE_TOKEN,
        "RATIFIED_SOURCE_KINDS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "MAPPING_PERSISTED": TRUE_TOKEN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "U05_KIND_DECISION": U05_KIND_DECISION,
        "U06_KIND_DECISION": U06_KIND_DECISION,
        "RESIDUAL_KIND_DECISION": RESIDUAL_KIND_DECISION,
        "HYPOTHESIS_ONLY": ",".join(HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES),
        "F12_STATUS": "UNKNOWN",
        "F13_STATUS": "UNKNOWN",
        "F16_STATUS": "UNKNOWN",
        "F17_STATUS": "UNKNOWN",
        "F18_STATUS": "UNKNOWN",
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
        "RETENTION_COVERAGE_STATUS": RETENTION_FAIL_CLOSED,
        "ORDERING_COMPLETENESS_STATUS": ORDERING_FAIL_CLOSED,
        "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM": FALSE_TOKEN,
        "COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN": FALSE_TOKEN,
        "COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION_STATUS": COMPLETE_STREAM_ACQUISITION_STATUS,
        "EARLIEST_REMAINING_D6_BLOCKER": EARLIEST_REMAINING_D6_BLOCKER,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": (
            "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
        ),
        "EARLIEST_OPTION_D_DEPENDENCY": "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION",
        "REMAINING_D6_BLOCKERS": remaining,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "MS2_EXECUTED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "ATLAS_AUTHORITY": "NONE",
        "AUTHORITY_EFFECT": "NONE",
        "U05_RAW_FIELDS": ",".join(U05_RAW_FIELDS),
    }
    _persist_json(path=pack_root / "claims.json", payload=result_claims)
    _persist_json(
        path=pack_root / "forensic_balance_raw_v1.json",
        payload=forensic_balance,
    )
    _persist_json(
        path=pack_root / "forensic_bills_raw_v1.json",
        payload=forensic_bills,
    )
    _persist_json(
        path=pack_root / "ranked_remaining_d6_blockers_v1.json",
        payload={
            "earliest_remaining_d6_blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "kind_set_include_exclude_blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "narrower_than_be_bag": TRUE_TOKEN,
            "records": ranked,
        },
    )
    _persist_json(
        path=pack_root / "fail_closed_guards_v1.json",
        payload={
            "include_exclude_from_unknown": "FORBIDDEN",
            "observed_value_as_kind_absence": "FORBIDDEN",
            "raw_eq_source_authority": FALSE_TOKEN,
            "new_network_get": "FORBIDDEN",
            "ms2_authorized": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "classified_kind_set": KIND_SET_EMPTY,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=pack_root)
    return AccountEquitySourceMappingAndCompleteEventStreamAcquisitionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        acquisition_as_of=acquisition_as_of,
        store_root=str(pack_root),
        ratified_source_kinds=NONE_TOKEN,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        mapping_persisted=TRUE_TOKEN,
        raw_eq_source_authority=FALSE_TOKEN,
        u05_kind_decision=U05_KIND_DECISION,
        u06_kind_decision=U06_KIND_DECISION,
        residual_kind_decision=RESIDUAL_KIND_DECISION,
        f12_f13_f16_f17_f18_status="UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN",
        retention_coverage_status=RETENTION_FAIL_CLOSED,
        ordering_completeness_status=ORDERING_FAIL_CLOSED,
        authorized_productive_event_source_seam=FALSE_TOKEN,
        complete_classified_event_stream_proven=FALSE_TOKEN,
        earliest_remaining_d6_blocker=EARLIEST_REMAINING_D6_BLOCKER,
        earliest_unresolved_full_core_dependency=(
            "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
        ),
        new_network_get_count="0",
        network_post_performed=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )
