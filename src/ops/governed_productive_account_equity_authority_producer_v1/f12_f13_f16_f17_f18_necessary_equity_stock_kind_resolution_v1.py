"""D6 F12/F13/F16/F17/F18 necessary EQUITY_STOCK kind resolution.

Adjudicates sealed embedding facts against sealed S1-S6, #6452 mapping,
and #6453 acquisition evidence. Does not GET or POST. Does not treat
empty, zero, blank, or unpaired fee tokens as kind absence or embedding
proof. Does not ratify EQUITY_STOCK source kinds. Does not authorize MS2
or D7. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_and_complete_event_stream_acquisition_v1 import (
    CANONICAL_MAPPING_PACK_RELPATH,
    reject_observed_value_as_kind_absence_or_embedding_decision_v1,
)
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

OWNER_GO = "OWNER_GO_D6_F12_F13_F16_F17_F18_NECESSARY_EQUITY_STOCK_KIND_RESOLUTION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "9e4b3297abd724639250a028f52892fa7ada6ba2"
CANONICAL_ACQUISITION_PACK_RELPATH = (
    "evidence/ops/full_core_d6_source_mapping_and_complete_event_stream_acquisition_v1/"
    "2026-09-13T194000Z"
)
RESOLUTION_STORE_RELPATH = (
    "evidence/ops/full_core_d6_f12_f13_f16_f17_f18_necessary_equity_stock_kind_resolution_v1"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATUS_UNKNOWN = "UNKNOWN"
RETENTION_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
F12_F13_MISSING_EVIDENCE = "NONZERO_LIABILITY_STOCK_PRIMARY_OBSERVATION_OR_RATIFIED_EQ_IDENTITY"
F16_F17_F18_MISSING_EVIDENCE = (
    "PAIRED_FEE_EVENT_AND_EQUITY_STOCK_OBSERVATION_OR_RATIFIED_EQ_IDENTITY"
)
EARLIEST_REMAINING_D6_BLOCKER = (
    "F12_F13_RESOLUTION_REQUIRES_NONZERO_LIABILITY_STOCK_PRIMARY_EVIDENCE_OR_RATIFIED_EQ_IDENTITY"
)
KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY = (
    "F12_F13_MISSING_NONZERO_LIABILITY_STOCK_PRIMARY_EVIDENCE_OR_RATIFIED_EQ_IDENTITY"
)
F16_F17_F18_BLOCKER = "F16_F17_F18_RESOLUTION_REQUIRES_PAIRED_FEE_EVENT_AND_EQUITY_STOCK_OBSERVATION_OR_RATIFIED_EQ_IDENTITY"
NAMED_KIND_SET_BLOCKER = "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
SURFACE_BALANCE = "GET_/api/v5/account/balance"
SURFACE_BILLS = "GET_/api/v5/account/bills"
SURFACE_BILLS_ARCHIVE = "GET_/api/v5/account/bills-archive"
CLAIMS_FILE = "claims.json"
FORENSIC_BALANCE_FILE = "forensic_balance_raw_v1.json"
FORENSIC_BILLS_FILE = "forensic_bills_raw_v1.json"


class F12F13F16F17F18NecessaryEquityStockKindResolutionError(ValueError):
    """Fail-closed F12-F18 kind-resolution violation."""


@dataclass(frozen=True)
class F12F13F16F17F18NecessaryEquityStockKindResolutionResultV1:
    genesis_id: str
    genesis_as_of: str
    resolution_as_of: str
    store_root: str
    f12_decision: str
    f13_decision: str
    f16_decision: str
    f17_decision: str
    f18_decision: str
    f12_f13_f16_f17_f18_status: str
    ratified_source_kinds: str
    kind_set: str
    kind_set_resolved: str
    u05_kind_decision: str
    u06_kind_decision: str
    residual_kind_decision: str
    raw_eq_source_authority: str
    retention_coverage_status: str
    ordering_completeness_status: str
    authorized_productive_event_source_seam: str
    complete_classified_event_stream_proven: str
    earliest_remaining_d6_blocker: str
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
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(f"{field}_DRIFT:{actual}")


def reject_claimed_f12_f13_f16_f17_f18_proof_without_primary_evidence_v1(
    *,
    claimed_proof: str,
    fact_id: str,
) -> None:
    if claimed_proof in {
        "INCLUDE_AS_NECESSARY_EQUITY_STOCK_KIND",
        "EXCLUDE_AS_NON_SOURCE_OR_OTHER_DOMAIN",
        "F12_TRUE",
        "F13_TRUE",
        "F16_TRUE",
        "F17_TRUE",
        "F18_TRUE",
        "F12_FALSE",
        "F13_FALSE",
        "F16_TRUE_FROM_FEE_ZERO",
        "F17_TRUE_FROM_FEE_FIELD_PRESENCE",
        "F18_TRUE_FROM_RECONCILIATION_GUESS",
        "EMPTY_LIAB_MEANS_F12_FALSE",
        "ZERO_LIAB_MEANS_F13_TRUE",
        "ALGEBRAIC_EQ_IDENTITY",
    }:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            f"F12_F18_CANNOT_{claimed_proof}:{fact_id}"
        )
    if claimed_proof != "REMAIN_UNKNOWN_MISSING_PRIMARY_EVIDENCE":
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            f"F12_F18_PROOF_UNKNOWN:{claimed_proof}"
        )
    if fact_id not in UNKNOWN_EMBEDDING_FACTS:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            f"F12_F18_FACT_NOT_IN_UNKNOWN_SET:{fact_id}"
        )


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "SOURCE_KIND_SET_MUST_REMAIN_EMPTY"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if UNKNOWN_NECESSARY_CLASS_REMAINS is not True:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "UNKNOWN_NECESSARY_CLASS_MUST_REMAIN"
        )
    if MS2_AUTHORIZED is not False:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED_NOT_FALSE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError(
            "PRODUCTIVE_EVENT_SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )


def _adjudicate_facts() -> list[dict[str, str]]:
    records = [
        {
            "fact_id": "F12_LIABILITY_AFFECTS_EQUITY_STOCK",
            "decision": DECISION_REMAIN_UNKNOWN,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "missing_evidence": F12_F13_MISSING_EVIDENCE,
            "selected_observation_surface": SURFACE_BALANCE,
            "new_get_authorized": FALSE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "empty_or_zero_or_blank_does_not_decide": TRUE_TOKEN,
            "layer": "ADJUDICATED_CONCLUSION",
        },
        {
            "fact_id": "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
            "decision": DECISION_REMAIN_UNKNOWN,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "missing_evidence": ("RATIFIED_EQ_IDENTITY_OR_PAIRED_LIABILITY_AND_EQ_OBSERVATION"),
            "selected_observation_surface": SURFACE_BALANCE,
            "new_get_authorized": FALSE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "empty_or_zero_or_blank_does_not_decide": TRUE_TOKEN,
            "layer": "ADJUDICATED_CONCLUSION",
        },
        {
            "fact_id": "F16_FEE_ALREADY_EMBEDDED_IN_EQ",
            "decision": DECISION_REMAIN_UNKNOWN,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "missing_evidence": F16_F17_F18_MISSING_EVIDENCE,
            "selected_observation_surface": f"{SURFACE_BILLS},{SURFACE_BILLS_ARCHIVE},{SURFACE_BALANCE}",
            "new_get_authorized": FALSE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "live_fee_zero_or_archive_nonzero_does_not_decide": TRUE_TOKEN,
            "layer": "ADJUDICATED_CONCLUSION",
        },
        {
            "fact_id": "F17_FEE_SEPARATE_ACCOUNT_DELTA",
            "decision": DECISION_REMAIN_UNKNOWN,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "missing_evidence": F16_F17_F18_MISSING_EVIDENCE,
            "selected_observation_surface": f"{SURFACE_BILLS},{SURFACE_BILLS_ARCHIVE},{SURFACE_BALANCE}",
            "new_get_authorized": FALSE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "fee_field_presence_is_not_kind_ratification": TRUE_TOKEN,
            "layer": "ADJUDICATED_CONCLUSION",
        },
        {
            "fact_id": "F18_FEE_RECONCILIATION_ONLY",
            "decision": DECISION_REMAIN_UNKNOWN,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "missing_evidence": F16_F17_F18_MISSING_EVIDENCE,
            "selected_observation_surface": f"{SURFACE_BILLS},{SURFACE_BILLS_ARCHIVE},{SURFACE_BALANCE}",
            "new_get_authorized": FALSE_TOKEN,
            "ratified_eq_identity_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "unpaired_archive_fee_does_not_decide": TRUE_TOKEN,
            "layer": "ADJUDICATED_CONCLUSION",
        },
    ]
    if tuple(record["fact_id"] for record in records) != UNKNOWN_EMBEDDING_FACTS:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("EMBEDDING_FACT_SET_DRIFT")
    for record in records:
        fact_id = record["fact_id"]
        reject_include_exclude_from_unknown_embedding_v1(
            decision=DECISION_REMAIN_UNKNOWN,
            fact_id=fact_id,
        )
        reject_observed_value_as_kind_absence_or_embedding_decision_v1(
            claimed_proof="NO_UNIQUE_EMBEDDING_OR_KIND_DECISION",
            fact_id=fact_id,
        )
        reject_claimed_f12_f13_f16_f17_f18_proof_without_primary_evidence_v1(
            claimed_proof="REMAIN_UNKNOWN_MISSING_PRIMARY_EVIDENCE",
            fact_id=fact_id,
        )
    return records


def _missing_primary_evidence(*, acquisition: Path) -> dict[str, Any]:
    balance = _load_json_object(path=acquisition / FORENSIC_BALANCE_FILE)
    bills = _load_json_object(path=acquisition / FORENSIC_BILLS_FILE)
    _require_token(field="interpretation_status", payload=balance, expected="FORBIDDEN")
    _require_token(
        field="empty_or_zero_or_blank_does_not_prove_kind_absence",
        payload=balance,
        expected=TRUE_TOKEN,
    )
    _require_token(
        field="eq_remains_reconciliation_target_only", payload=balance, expected=TRUE_TOKEN
    )
    _require_token(field="interpretation_status", payload=bills, expected="FORBIDDEN")
    _require_token(
        field="fee_token_does_not_decide_f16_f17_f18", payload=bills, expected=TRUE_TOKEN
    )
    _require_token(
        field="venue_type_tokens_are_not_ratified_kinds",
        payload=bills,
        expected=TRUE_TOKEN,
    )
    return {
        "layer": "MISSING_PRIMARY_EVIDENCE",
        "new_get_authorized": FALSE_TOKEN,
        "new_get_performed": FALSE_TOKEN,
        "ratified_eq_identity_present": FALSE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "algebraic_inference": "FORBIDDEN",
        "records": [
            {
                "covers_facts": "F12_LIABILITY_AFFECTS_EQUITY_STOCK,F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
                "missing_evidence": F12_F13_MISSING_EVIDENCE,
                "selected_observation_surface_already_present": SURFACE_BALANCE,
                "sealed_s2_liability_tokens_do_not_decide": TRUE_TOKEN,
                "new_get_authorized": FALSE_TOKEN,
            },
            {
                "covers_facts": (
                    "F16_FEE_ALREADY_EMBEDDED_IN_EQ,"
                    "F17_FEE_SEPARATE_ACCOUNT_DELTA,"
                    "F18_FEE_RECONCILIATION_ONLY"
                ),
                "missing_evidence": F16_F17_F18_MISSING_EVIDENCE,
                "selected_observation_surface_already_present": (
                    f"{SURFACE_BILLS},{SURFACE_BILLS_ARCHIVE},{SURFACE_BALANCE}"
                ),
                "live_fee_zero_and_archive_nonzero_unpaired_do_not_decide": TRUE_TOKEN,
                "new_get_authorized": FALSE_TOKEN,
            },
        ],
        "forensic_balance_layer": str(balance.get("layer") or ""),
        "forensic_bills_layer": str(bills.get("layer") or ""),
    }


def execute_f12_f13_f16_f17_f18_necessary_equity_stock_kind_resolution_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_observation_pack: Path | str,
    sealed_s6_pack: Path | str,
    sealed_mapping_pack: Path | str,
    sealed_acquisition_pack: Path | str,
    evidence_root: Path | str,
    resolution_as_of: str,
) -> F12F13F16F17F18NecessaryEquityStockKindResolutionResultV1:
    if owner_go != OWNER_GO:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    observation = Path(sealed_observation_pack)
    s6_pack = Path(sealed_s6_pack)
    mapping = Path(sealed_mapping_pack)
    acquisition = Path(sealed_acquisition_pack)
    observation_rc = verify_manifest_sha256_v1(store_root=observation)
    s6_rc = verify_manifest_sha256_v1(store_root=s6_pack)
    mapping_rc = verify_manifest_sha256_v1(store_root=mapping)
    acquisition_rc = verify_manifest_sha256_v1(store_root=acquisition)
    if observation_rc != 0 or s6_rc != 0 or mapping_rc != 0 or acquisition_rc != 0:
        raise F12F13F16F17F18NecessaryEquityStockKindResolutionError("MANIFEST_VERIFY_NOT_ZERO")
    mapping_claims = _load_json_object(path=mapping / CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=mapping_claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="GENESIS_AS_OF", payload=mapping_claims, expected=EXPECTED_GENESIS_AS_OF)
    _require_token(field="MAPPING_PERSISTED", payload=mapping_claims, expected=TRUE_TOKEN)
    _require_token(field="RATIFIED_SOURCE_KINDS", payload=mapping_claims, expected=NONE_TOKEN)
    _require_token(field="KIND_SET_RESOLVED", payload=mapping_claims, expected=FALSE_TOKEN)
    _require_token(field="RAW_EQ_SOURCE_AUTHORITY", payload=mapping_claims, expected=FALSE_TOKEN)
    acquisition_claims = _load_json_object(path=acquisition / CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=acquisition_claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="F12_STATUS", payload=acquisition_claims, expected=STATUS_UNKNOWN)
    _require_token(field="F13_STATUS", payload=acquisition_claims, expected=STATUS_UNKNOWN)
    _require_token(field="F16_STATUS", payload=acquisition_claims, expected=STATUS_UNKNOWN)
    _require_token(field="F17_STATUS", payload=acquisition_claims, expected=STATUS_UNKNOWN)
    _require_token(field="F18_STATUS", payload=acquisition_claims, expected=STATUS_UNKNOWN)
    _require_token(field="NEW_NETWORK_GET_COUNT", payload=acquisition_claims, expected="0")
    facts = _adjudicate_facts()
    missing = _missing_primary_evidence(acquisition=acquisition)
    ranked = [
        {
            "rank": "1",
            "blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "covers_facts": "F12_LIABILITY_AFFECTS_EQUITY_STOCK,F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
            "blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "role": "EARLIEST_REMAINING_D6_BLOCKER",
            "new_get_authorized": FALSE_TOKEN,
            "include_exclude_from_unknown": "FORBIDDEN",
        },
        {
            "rank": "2",
            "blocker": F16_F17_F18_BLOCKER,
            "covers_facts": (
                "F16_FEE_ALREADY_EMBEDDED_IN_EQ,"
                "F17_FEE_SEPARATE_ACCOUNT_DELTA,"
                "F18_FEE_RECONCILIATION_ONLY"
            ),
            "blocked_by": F16_F17_F18_MISSING_EVIDENCE,
            "role": "NEXT_EMBEDDING_FACT_BLOCKER_AFTER_F12_F13",
            "new_get_authorized": FALSE_TOKEN,
        },
        {
            "rank": "3",
            "blocker": NAMED_KIND_SET_BLOCKER,
            "members": ",".join(NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES),
            "blocked_by": (
                f"{EARLIEST_REMAINING_D6_BLOCKER},{F16_F17_F18_BLOCKER},"
                "RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS"
            ),
            "role": "CONSEQUENCE_OF_UNRESOLVED_F12_F18_AND_RESIDUAL",
        },
        {
            "rank": "4",
            "blocker": "NO_RATIFIED_EQUITY_STOCK_SOURCE_KIND",
            "role": "CONSEQUENCE_OF_UNRESOLVED_KIND_SET",
            "blocked_by": NAMED_KIND_SET_BLOCKER,
        },
        {
            "rank": "5",
            "blocker": "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_ABSENT",
            "role": "DOWNSTREAM_OF_KIND_SET_AND_MS2_AND_BILLS_NONCANONICAL",
            "blocked_by": "KIND_SET_UNRESOLVED,MS2_UNAUTHORIZED,ACCOUNT_BILLS_CURRENT_NONCANONICAL",
        },
        {
            "rank": "6",
            "blocker": "RETENTION_COVERAGE_FAIL_CLOSED_NOT_PROVEN",
            "role": "INDEPENDENT_COMPLETENESS_NOT_EARLIEST_SOURCE_KIND_BLOCKER",
            "blocked_by": "PARTIAL_BILL_ID_OVERLAP_DOES_NOT_PROVE_RETENTION",
        },
        {
            "rank": "7",
            "blocker": "ORDERING_COMPLETENESS_FAIL_CLOSED_NOT_PROVEN",
            "role": "INDEPENDENT_COMPLETENESS_NOT_EARLIEST_SOURCE_KIND_BLOCKER",
            "blocked_by": "OBSERVED_TS_AND_BILLID_DO_NOT_PROVE_STREAM_ORDERING_COMPLETENESS",
        },
    ]
    folder = _folder_from_as_of(resolution_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": "NONE",
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "RESOLUTION_AS_OF": resolution_as_of,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "SEALED_OBSERVATION_PACK": CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
        "SEALED_S6_PACK": CANONICAL_S6_PACK_RELPATH,
        "SEALED_MAPPING_PACK": CANONICAL_MAPPING_PACK_RELPATH,
        "SEALED_ACQUISITION_PACK": CANONICAL_ACQUISITION_PACK_RELPATH,
        "OBSERVATION_MANIFEST_VERIFY_RC": str(observation_rc),
        "S6_MANIFEST_VERIFY_RC": str(s6_rc),
        "MAPPING_MANIFEST_VERIFY_RC": str(mapping_rc),
        "ACQUISITION_MANIFEST_VERIFY_RC": str(acquisition_rc),
        "MANIFESTS_VERIFY": TRUE_TOKEN,
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "F12_STATUS": STATUS_UNKNOWN,
        "F13_STATUS": STATUS_UNKNOWN,
        "F16_STATUS": STATUS_UNKNOWN,
        "F17_STATUS": STATUS_UNKNOWN,
        "F18_STATUS": STATUS_UNKNOWN,
        "F12_F13_F16_F17_F18_STATUS": STATUS_UNKNOWN,
        "F12_MISSING_EVIDENCE": F12_F13_MISSING_EVIDENCE,
        "F13_MISSING_EVIDENCE": "RATIFIED_EQ_IDENTITY_OR_PAIRED_LIABILITY_AND_EQ_OBSERVATION",
        "F16_MISSING_EVIDENCE": F16_F17_F18_MISSING_EVIDENCE,
        "F17_MISSING_EVIDENCE": F16_F17_F18_MISSING_EVIDENCE,
        "F18_MISSING_EVIDENCE": F16_F17_F18_MISSING_EVIDENCE,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": EARLIEST_REMAINING_D6_BLOCKER,
        "NARROWER_THAN_BF_BAG": TRUE_TOKEN,
        "RATIFIED_SOURCE_KINDS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "MAPPING_PERSISTED": TRUE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U06_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RETENTION_COVERAGE_STATUS": RETENTION_FAIL_CLOSED,
        "ORDERING_COMPLETENESS_STATUS": ORDERING_FAIL_CLOSED,
        "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM": FALSE_TOKEN,
        "COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "MS2_EXECUTED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "NEW_NETWORK_GET_COUNT": "0",
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED": FALSE_TOKEN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": (
            "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
        ),
        "EARLIEST_OPTION_D_DEPENDENCY": "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION",
        "EARLIEST_D6_KIND_SET_DEPENDENCY": NAMED_KIND_SET_BLOCKER,
        "C01_REHABILITATION_FORBIDDEN": TRUE_TOKEN,
        "EXISTING_NON_SOURCE_AND_OTHER_DOMAIN_UNCHANGED": TRUE_TOKEN,
    }
    _persist_json(path=store / "embedding_fact_adjudication_v1.json", payload={"facts": facts})
    _persist_json(path=store / "missing_primary_evidence_v1.json", payload=missing)
    _persist_json(
        path=store / "ranked_remaining_d6_blockers_v1.json",
        payload={
            "earliest_remaining_d6_blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "kind_set_include_exclude_blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "narrower_than_bf_bag": TRUE_TOKEN,
            "records": ranked,
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "include_exclude_from_unknown": "FORBIDDEN",
            "algebraic_inference": "FORBIDDEN",
            "new_network_get": "FORBIDDEN",
            "observed_value_as_kind_absence": "FORBIDDEN",
            "raw_eq_source_authority": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "classified_kind_set": KIND_SET_EMPTY,
        },
    )
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    manifest = persist_manifest_sha256_v1(store_root=store)
    return F12F13F16F17F18NecessaryEquityStockKindResolutionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        resolution_as_of=resolution_as_of,
        store_root=str(store),
        f12_decision=DECISION_REMAIN_UNKNOWN,
        f13_decision=DECISION_REMAIN_UNKNOWN,
        f16_decision=DECISION_REMAIN_UNKNOWN,
        f17_decision=DECISION_REMAIN_UNKNOWN,
        f18_decision=DECISION_REMAIN_UNKNOWN,
        f12_f13_f16_f17_f18_status=STATUS_UNKNOWN,
        ratified_source_kinds=NONE_TOKEN,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        u05_kind_decision=DECISION_REMAIN_UNKNOWN,
        u06_kind_decision=DECISION_REMAIN_UNKNOWN,
        residual_kind_decision=DECISION_REMAIN_UNKNOWN,
        raw_eq_source_authority=FALSE_TOKEN,
        retention_coverage_status=RETENTION_FAIL_CLOSED,
        ordering_completeness_status=ORDERING_FAIL_CLOSED,
        authorized_productive_event_source_seam=FALSE_TOKEN,
        complete_classified_event_stream_proven=FALSE_TOKEN,
        earliest_remaining_d6_blocker=EARLIEST_REMAINING_D6_BLOCKER,
        new_network_get_count="0",
        network_post_performed=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )
