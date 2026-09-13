"""D6 account-equity source-mapping ratification.

Adjudicates sealed S6 field traces against existing D6/Class-C/algebra
authority. Persists source-role mappings. Does not invent classified
EQUITY_STOCK kinds. Does not treat eq as source authority. Does not
prove retention or ordering. Does not authorize MS2 or D7.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    DIMENSION_MARGIN_REQUIREMENTS,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U05_PLACEMENT,
    U06_KIND_DECISION,
    U06_PLACEMENT,
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
    CANDIDATE_RESIDUAL,
    CANDIDATE_U05,
    CANDIDATE_U06,
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    BILL_EVENT_IDENTITY_FIELDS,
    BILL_KIND_TOKEN_FIELDS,
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    C01_AVAILEQ_FIELDS,
    C02_FORBIDDEN_SOURCE_FIELDS,
    CURRENCY_FIELDS,
    D4_ACCOUNT_MODE_FIELDS,
    D4_IDENTITY_FIELDS,
    D4_SETTLEMENT_FIELDS,
    INTEREST_FIELDS,
    MARGIN_DIMENSION_FIELDS,
    NOTIONAL_FIELDS,
    P01_REJECTED_VENUE_FIELDS,
    PNL_FIELDS,
    STATUS_AMBIGUOUS,
    STATUS_MAPPED_RATIFIED,
    STATUS_NOT_APPLICABLE,
    STATUS_OBSERVED_UNRATIFIED,
    U03_UPL_FIELDS,
    U04_FROZEN_FIELDS,
    U05_EMBEDDING_FIELDS,
    U06_FEE_FIELDS,
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    reject_include_exclude_from_unknown_embedding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EMBEDDED_CONDITIONAL,
    EMBEDDED_NOT_APPLICABLE,
    EMBEDDED_YES,
    INCLUSION_NOT_APPLICABLE,
    INCLUSION_UNRESOLVED,
    ROLE_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE,
    ROLE_EMBEDDED_NOT_SEPARATE,
    U04_PENDING_ORDER_RESERVATIONS,
    U05_LIABILITIES_BORROWINGS,
    U06_FEES,
)

OWNER_GO = "OWNER_GO_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION_WORKPACKAGE_V1"
EXPECTED_ORIGIN_MAIN_SHA = "6fceaa7c7623cd244b13a89db9c1dcbc2af7b3f6"
CANONICAL_S6_PACK_RELPATH = (
    "evidence/ops/full_core_d6_path_b_package_1_s6_mapping_classification_v1/2026-09-13T184000Z"
)
SOURCE_MAPPING_STORE_RELPATH = (
    "evidence/ops/full_core_d6_account_equity_source_mapping_ratification_v1"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
NOT_MAPPED_FAIL_CLOSED = "NOT_MAPPED_FAIL_CLOSED"
OBSERVED_KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
RETENTION_COVERAGE_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_COMPLETENESS_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
MAPPING_COVERAGE_PARTIAL = "PARTIAL_FAIL_CLOSED_NO_RATIFIED_SOURCE_KIND"
STATUS_RATIFIED_SOURCE_KIND = "RATIFIED_SOURCE_KIND"
STATUS_RATIFIED_NON_SOURCE = "RATIFIED_NON_SOURCE"
STATUS_RATIFIED_OTHER_DOMAIN = "RATIFIED_OTHER_DOMAIN"
STATUS_UNRESOLVED_AMBIGUOUS = "UNRESOLVED_AMBIGUOUS"
STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY = "UNRESOLVED_INSUFFICIENT_AUTHORITY"
STATUS_UNRESOLVED_INSUFFICIENT_EVIDENCE = "UNRESOLVED_INSUFFICIENT_EVIDENCE"
RATIFICATION_STATUSES = (
    STATUS_RATIFIED_SOURCE_KIND,
    STATUS_RATIFIED_NON_SOURCE,
    STATUS_RATIFIED_OTHER_DOMAIN,
    STATUS_UNRESOLVED_AMBIGUOUS,
    STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY,
    STATUS_UNRESOLVED_INSUFFICIENT_EVIDENCE,
)
RATIFIED_SOURCE_KIND_SET: tuple[str, ...] = ()
UNIT_UNPROVEN = "UNPROVEN_U08_NOT_CONVERSION_AUTHORITY"
IDENTITY_NONE = "NONE_FAIL_CLOSED"
ORDERING_NONE = "NONE_FAIL_CLOSED"
SIGN_NOT_APPLICABLE = "NOT_APPLICABLE"
S6_FIELD_FILE = "s6_observed_field_classification_v1.json"
S6_CLAIMS_FILE = "claims.json"
S6_EMBEDDING_FILE = "s6_embedding_facts_v1.json"
REQUIRED_S6_FILES: tuple[str, ...] = (
    "claims.json",
    "s6_classification_records_v1.json",
    "s6_embedding_facts_v1.json",
    "s6_kind_set_adjudication_v1.json",
    "s6_observed_field_classification_v1.json",
    "s6_input_provenance_v1.json",
)
RUNBOOK_AUTHORITY = (
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.BD;"
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.AW;"
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.AX;"
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.AR"
)
CENSUS_AUTHORITY = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "classified_event_kind_set_and_source_seam_contract_v1.py"
)
ALGEBRA_AUTHORITY = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "reconstruction_algebra_contract_v1.py"
)
EQ_TARGET_AUTHORITY = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "fresh_eq_reconciliation_target_contract_v1.py"
)
OPTION_D_AUTHORITY = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "option_d_ssot_architecture_contract_v1.py"
)
TAXONOMY_AUTHORITY = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_affecting_event_taxonomy_contract_v1.py"
)


class AccountEquitySourceMappingRatificationError(ValueError):
    """Fail-closed source-mapping ratification violation."""


@dataclass(frozen=True)
class AccountEquitySourceMappingRatificationResultV1:
    genesis_id: str
    genesis_as_of: str
    ratification_as_of: str
    store_root: str
    sealed_s6_pack: str
    sealed_observation_pack: str
    sealed_input_only: str
    manifests_verify: str
    ratification_candidate_count: str
    ratified_source_kinds: str
    ratified_non_source_fields: str
    ratified_other_domain_fields: str
    unresolved_fields: str
    u05_kind_decision: str
    u06_kind_decision: str
    residual_kind_decision: str
    f12_f13_f16_f17_f18_status: str
    kind_set: str
    kind_set_resolved: str
    source_mapping: str
    mapping_persisted: str
    mapping_coverage_status: str
    raw_eq_source_authority: str
    retention_coverage_status: str
    ordering_completeness_status: str
    complete_classified_event_stream_proven: str
    remaining_d6_blockers: str
    new_network_get_count: str
    network_post_performed: str
    ms2_authorized: str
    ms2_executed: str
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
        raise AccountEquitySourceMappingRatificationError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise AccountEquitySourceMappingRatificationError(f"{field}_DRIFT:{actual}")


def _s6_evidence_ref(*, s6_pack: Path, field_path: str) -> str:
    return f"{s6_pack.as_posix()}/{S6_FIELD_FILE}#{field_path}"


def reject_unratified_equity_stock_source_kind_v1(
    *,
    event_kind: str,
    mapped_numeric_effect: str,
) -> None:
    kind = event_kind.strip()
    if kind in RATIFIED_SOURCE_KIND_SET:
        return
    if kind not in {NONE_TOKEN, "", "UNCLASSIFIED", "UNKNOWN"}:
        raise AccountEquitySourceMappingRatificationError(
            f"UNRATIFIED_SOURCE_KIND_FORBIDDEN:{kind}"
        )
    if mapped_numeric_effect.strip() not in {NOT_MAPPED_FAIL_CLOSED, SIGN_NOT_APPLICABLE}:
        raise AccountEquitySourceMappingRatificationError(
            "UNRATIFIED_KIND_CANNOT_MAP_NUMERIC_EFFECT"
        )


def assert_eq_is_not_source_authority_v1(*, field_name: str, ratification_status: str) -> None:
    if field_name != "eq":
        return
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise AccountEquitySourceMappingRatificationError("RAW_EQ_SOURCE_AUTHORITY_PIN_DRIFT")
    if ratification_status == STATUS_RATIFIED_SOURCE_KIND:
        raise AccountEquitySourceMappingRatificationError("EQ_CANNOT_BE_RATIFIED_SOURCE_KIND")


def _base_record(
    *,
    s6: Mapping[str, str],
    s6_pack: Path,
    ratification_status: str,
    source_role: str,
    economic_semantic: str,
    embedding_status: str,
    event_kind: str,
    sign_rule: str,
    identity_dedup_key: str,
    ordering_key: str,
    unresolved_reason: str,
    existing_authority_ref: str,
) -> dict[str, str]:
    field_name = s6["raw_venue_field"]
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=event_kind,
        mapped_numeric_effect=NOT_MAPPED_FAIL_CLOSED,
    )
    assert_eq_is_not_source_authority_v1(
        field_name=field_name,
        ratification_status=ratification_status,
    )
    if ratification_status not in RATIFICATION_STATUSES:
        raise AccountEquitySourceMappingRatificationError(
            f"RATIFICATION_STATUS_UNKNOWN:{ratification_status}"
        )
    if ratification_status == STATUS_RATIFIED_SOURCE_KIND:
        raise AccountEquitySourceMappingRatificationError("NO_RATIFIED_SOURCE_KIND_AVAILABLE")
    return {
        "raw_field": field_name,
        "field_path": s6["field_path"],
        "source_endpoint": s6["source_endpoint"],
        "observed_evidence_ref": _s6_evidence_ref(s6_pack=s6_pack, field_path=s6["field_path"]),
        "existing_authority_ref": existing_authority_ref,
        "economic_semantic": economic_semantic,
        "embedding_status": embedding_status,
        "event_kind": event_kind,
        "sign_rule": sign_rule,
        "unit_currency_domain": UNIT_UNPROVEN,
        "identity_dedup_key": identity_dedup_key,
        "ordering_key": ordering_key,
        "source_role": source_role,
        "ratification_status": ratification_status,
        "unresolved_reason": unresolved_reason,
        "peak_trade_target_kind": NONE_TOKEN,
        "mapped_numeric_effect": NOT_MAPPED_FAIL_CLOSED,
        "s6_classification_status": s6["classification_status"],
        "observation_is_not_kind_ratification": TRUE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "kind_set_resolved": FALSE_TOKEN,
    }


def _identity_key_for(s6: Mapping[str, str]) -> str:
    field_name = s6["raw_venue_field"]
    if field_name in BILL_EVENT_IDENTITY_FIELDS and field_name == "billId":
        return "BILL_ID_FORENSIC_IDENTITY"
    if field_name in D4_IDENTITY_FIELDS:
        return "D4_UID_CORROBORATION_ONLY_NOT_MINTED"
    return IDENTITY_NONE


def _ordering_key_for(s6: Mapping[str, str]) -> str:
    field_name = s6["raw_venue_field"]
    if field_name in {"ts", "uTime"}:
        return "FORENSIC_TIMESTAMP_NOT_COMPLETENESS"
    if field_name in BILL_EVENT_IDENTITY_FIELDS and field_name == "ts":
        return "FORENSIC_TIMESTAMP_NOT_COMPLETENESS"
    return ORDERING_NONE


def _adjudicate_s6_record(*, s6: Mapping[str, str], s6_pack: Path) -> dict[str, str]:
    field_name = s6["raw_venue_field"]
    scope = s6["field_path"].split(".", 1)[0]
    s6_status = s6["classification_status"]
    s6_contract = s6["existing_canonical_contract"]
    identity = _identity_key_for(s6)
    ordering = _ordering_key_for(s6)

    if field_name == "eq" and scope == "details":
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="FRESH_EQ_RECONCILIATION_TARGET_NOT_SOURCE",
            economic_semantic="EQ_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{EQ_TARGET_AUTHORITY};{s6_contract}",
        )
    if field_name in C01_AVAILEQ_FIELDS or field_name in C02_FORBIDDEN_SOURCE_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="REJECTED_EQUITY_SOURCE_C01_C02",
            economic_semantic=s6["existing_canonical_semantic"],
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{OPTION_D_AUTHORITY};{s6_contract}",
        )
    if field_name in NOTIONAL_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="NOTIONAL_PROHIBITED_AS_EQUITY_STOCK_ADDEND",
            economic_semantic=s6["existing_canonical_semantic"],
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{ALGEBRA_AUTHORITY};{s6_contract}",
        )
    if scope == "subtypes":
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="CATALOG_METADATA_NOT_EVENT_KIND",
            economic_semantic="CATALOG_QUERY_RESULT_NOT_KIND_COMPLETENESS",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if field_name in D4_IDENTITY_FIELDS and scope == "config":
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="D4_IDENTITY_CORROBORATION_NOT_MINTED",
            economic_semantic="D4_RUNTIME_EVIDENCE_CORROBORATED_IDENTITY_NOT_MINTED",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if field_name in D4_SETTLEMENT_FIELDS and scope == "config":
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="SETTLEMENT_CURRENCY_RUNTIME_EVIDENCE",
            economic_semantic="SETTLEMENT_CURRENCY_RUNTIME_EVIDENCE_ONLY",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if field_name in D4_ACCOUNT_MODE_FIELDS and scope == "config":
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="U01_ELIGIBILITY_CONTEXT_NOT_NUMERIC_EQUITY",
            economic_semantic="U01_ACCOUNT_MODE_IS_ELIGIBILITY_CONTEXT_NOT_NUMERIC_EQUITY",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{ALGEBRA_AUTHORITY};{s6_contract}",
        )
    if field_name in CURRENCY_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="CURRENCY_DOMAIN_OBSERVATION_NOT_U08_AUTHORITY",
            economic_semantic="CURRENCY_DOMAIN_OBSERVATION_NOT_U08_CONVERSION_AUTHORITY",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{ALGEBRA_AUTHORITY};{s6_contract}",
        )
    if field_name in BILL_EVENT_IDENTITY_FIELDS and scope in {"bills", "bills-archive"}:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="FORENSIC_EVENT_IDENTITY_OR_ORDERING_KEY",
            economic_semantic="FORENSIC_EVENT_IDENTITY_OR_ORDERING_KEY",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{TAXONOMY_AUTHORITY};{s6_contract}",
        )
    if field_name in {"uTime"}:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="FORENSIC_TIMESTAMP_NOT_COMPLETENESS",
            economic_semantic="ALLOWED_BALANCE_OBSERVATION_FIELD_AUTHORITY_NONE",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if field_name in U05_EMBEDDING_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_UNRESOLVED_AMBIGUOUS,
            source_role="U05_LIABILITY_OBSERVATION_NOT_KIND",
            economic_semantic=(
                f"U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED;policy={U05_LIABILITIES_BORROWINGS};"
                f"placement={U05_PLACEMENT}"
            ),
            embedding_status=f"{EMBEDDED_CONDITIONAL};inclusion={INCLUSION_UNRESOLVED}",
            event_kind=NONE_TOKEN,
            sign_rule=ROLE_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason="F12_F13_UNKNOWN;U05_KIND_DECISION=REMAIN_UNKNOWN",
            existing_authority_ref=(
                f"{ALGEBRA_AUTHORITY};{CENSUS_AUTHORITY};{RUNBOOK_AUTHORITY};{s6_contract}"
            ),
        )
    if field_name in U06_FEE_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_UNRESOLVED_AMBIGUOUS,
            source_role="U06_FEE_OBSERVATION_NOT_KIND",
            economic_semantic=(
                f"U06_FEE_INCLUSION_UNRESOLVED;policy={U06_FEES};placement={U06_PLACEMENT}"
            ),
            embedding_status=(
                f"{EMBEDDED_CONDITIONAL};inclusion={INCLUSION_UNRESOLVED};"
                "base_or_event_or_reconciliation_unresolved"
            ),
            event_kind=NONE_TOKEN,
            sign_rule="CONDITIONAL_ONCE_IN_BASE_OR_SINGLE_SUBTRACTION",
            identity_dedup_key="BILL_ID_FORENSIC_IDENTITY_IF_PRESENT",
            ordering_key="FORENSIC_TIMESTAMP_NOT_COMPLETENESS",
            unresolved_reason="F16_F17_F18_UNKNOWN;U06_KIND_DECISION=REMAIN_UNKNOWN",
            existing_authority_ref=(
                f"{ALGEBRA_AUTHORITY};{CENSUS_AUTHORITY};{RUNBOOK_AUTHORITY};{s6_contract}"
            ),
        )
    if field_name in INTEREST_FIELDS:
        hypothesis = ",".join(HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES)
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY,
            source_role="HYPOTHESIS_ONLY_INTEREST_NOT_RATIFIED_KIND",
            economic_semantic="HYPOTHESIS_ONLY_INTEREST_NOT_RATIFIED_KIND",
            embedding_status=INCLUSION_UNRESOLVED,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=f"INTEREST_IS_HYPOTHESIS_ONLY;NO_INCLUDE_FROM_UNKNOWN;{hypothesis}",
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if field_name in U03_UPL_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="U03_ALGEBRA_TERM_NOT_EQUITY_STOCK_EVENT_KIND",
            economic_semantic="U03_UNREALIZED_PNL_MTM_EMBEDDED_NOT_SEPARATE_NOT_EVENT_KIND",
            embedding_status=f"{EMBEDDED_YES};role={ROLE_EMBEDDED_NOT_SEPARATE}",
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason="FIELD_BINDING_TO_U03_VALUE_UNPROVEN",
            existing_authority_ref=f"{CENSUS_AUTHORITY};{ALGEBRA_AUTHORITY};{s6_contract}",
        )
    if field_name in U04_FROZEN_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_OTHER_DOMAIN,
            source_role="U04_AVAILABLE_FOR_SIZING_OR_RISK_SIZING_OBSERVATION",
            economic_semantic=(
                f"U04_PENDING_ORDER_RESERVATION_NOT_EQUITY_STOCK;placement={U04_PLACEMENT};"
                f"policy={U04_PENDING_ORDER_RESERVATIONS}"
            ),
            embedding_status=f"{EMBEDDED_CONDITIONAL};inclusion={INCLUSION_UNRESOLVED}",
            event_kind=NONE_TOKEN,
            sign_rule=ROLE_CONDITIONAL_SUBTRACTIVE_IF_NOT_IN_BASE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason="U04_INCLUSION_UNRESOLVED;NOT_EQUITY_STOCK_KIND",
            existing_authority_ref=f"{CENSUS_AUTHORITY};{ALGEBRA_AUTHORITY};{s6_contract}",
        )
    if field_name in MARGIN_DIMENSION_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="MARGIN_REQUIREMENTS_DIMENSION_EXISTS_FIELD_BINDING_UNBOUND",
            economic_semantic=(
                f"{DIMENSION_MARGIN_REQUIREMENTS}_DIMENSION_EXISTS_UNBOUND;"
                "NOT_EQUITY_STOCK_SOURCE;NOT_EQUITY_STOCK_EVENT_KIND"
            ),
            embedding_status=INCLUSION_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason="MARGIN_REQUIREMENTS_ACCOUNT_BALANCE_FIELD_BINDING_UNBOUND",
            existing_authority_ref=f"{OPTION_D_AUTHORITY};{s6_contract}",
        )
    if field_name in PNL_FIELDS:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="U02_ALGEBRA_TERM_NOT_EQUITY_STOCK_EVENT_KIND",
            economic_semantic="U02_REALIZED_PNL_EMBEDDED_NOT_SEPARATE_NOT_EVENT_KIND",
            embedding_status=f"{EMBEDDED_YES};role={ROLE_EMBEDDED_NOT_SEPARATE}",
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=(
                "BILL_ID_FORENSIC_IDENTITY_IF_PRESENT"
                if scope in {"bills", "bills-archive"}
                else identity
            ),
            ordering_key=(
                "FORENSIC_TIMESTAMP_NOT_COMPLETENESS"
                if scope in {"bills", "bills-archive"}
                else ordering
            ),
            unresolved_reason="FIELD_BINDING_TO_U02_VALUE_UNPROVEN",
            existing_authority_ref=f"{CENSUS_AUTHORITY};{ALGEBRA_AUTHORITY};{s6_contract}",
        )
    if field_name in BILL_KIND_TOKEN_FIELDS and scope in {"bills", "bills-archive"}:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY,
            source_role="VENUE_TYPE_TOKEN_NOT_RATIFIED_CLASSIFIED_KIND",
            economic_semantic="VENUE_TYPE_TOKEN_NOT_RATIFIED_CLASSIFIED_KIND",
            embedding_status=INCLUSION_UNRESOLVED,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key="BILL_ID_FORENSIC_IDENTITY_IF_PRESENT",
            ordering_key="FORENSIC_TIMESTAMP_NOT_COMPLETENESS",
            unresolved_reason=(
                "RATIFIED_CLASSIFIED_KIND_SET_EMPTY;VENUE_TYPE_IS_NOT_KIND;"
                f"{CANDIDATE_RESIDUAL}=REMAIN_UNKNOWN"
            ),
            existing_authority_ref=f"{TAXONOMY_AUTHORITY};{CENSUS_AUTHORITY};{s6_contract}",
        )
    if field_name in P01_REJECTED_VENUE_FIELDS and s6_status == STATUS_NOT_APPLICABLE:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="REJECTED_VENUE_RAW_NOT_P01",
            economic_semantic="REJECTED_VENUE_RAW_NOT_P01",
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if s6_status == STATUS_MAPPED_RATIFIED:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="CONTRACT_SEMANTIC_RATIFIED_NOT_EQUITY_SOURCE",
            economic_semantic=s6["existing_canonical_semantic"],
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if s6_status == STATUS_NOT_APPLICABLE:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_RATIFIED_NON_SOURCE,
            source_role="NOT_APPLICABLE_NOT_EQUITY_SOURCE",
            economic_semantic=s6["existing_canonical_semantic"],
            embedding_status=EMBEDDED_NOT_APPLICABLE,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=NONE_TOKEN,
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    if s6_status in {STATUS_AMBIGUOUS, STATUS_OBSERVED_UNRATIFIED}:
        return _base_record(
            s6=s6,
            s6_pack=s6_pack,
            ratification_status=STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY,
            source_role="NO_UNIQUE_D6_CLASS_C_FIELD_BINDING",
            economic_semantic=s6["existing_canonical_semantic"],
            embedding_status=INCLUSION_UNRESOLVED,
            event_kind=NONE_TOKEN,
            sign_rule=SIGN_NOT_APPLICABLE,
            identity_dedup_key=identity,
            ordering_key=ordering,
            unresolved_reason=(
                "NO_UNIQUE_EXISTING_AUTHORITY_FOR_SOURCE_KIND;"
                "OBSERVATION_OF_NAME_OR_VALUE_IS_NOT_KIND_RATIFICATION"
            ),
            existing_authority_ref=f"{RUNBOOK_AUTHORITY};{s6_contract}",
        )
    raise AccountEquitySourceMappingRatificationError(
        f"S6_CLASSIFICATION_STATUS_UNHANDLED:{s6_status}:{s6['field_path']}"
    )


def _csv(values: list[str]) -> str:
    return ",".join(values)


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise AccountEquitySourceMappingRatificationError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise AccountEquitySourceMappingRatificationError("CLASSIFIED_KIND_SET_MUST_REMAIN_EMPTY")
    if RATIFIED_SOURCE_KIND_SET:
        raise AccountEquitySourceMappingRatificationError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquitySourceMappingRatificationError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquitySourceMappingRatificationError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise AccountEquitySourceMappingRatificationError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if UNKNOWN_NECESSARY_CLASS_REMAINS is not True:
        raise AccountEquitySourceMappingRatificationError("UNKNOWN_NECESSARY_CLASS_MUST_REMAIN")
    if MS2_AUTHORIZED is not False:
        raise AccountEquitySourceMappingRatificationError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise AccountEquitySourceMappingRatificationError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise AccountEquitySourceMappingRatificationError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise AccountEquitySourceMappingRatificationError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")


def execute_account_equity_source_mapping_ratification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_s6_pack: Path | str,
    sealed_observation_pack: Path | str,
    evidence_root: Path | str,
    ratification_as_of: str,
) -> AccountEquitySourceMappingRatificationResultV1:
    if owner_go != OWNER_GO:
        raise AccountEquitySourceMappingRatificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise AccountEquitySourceMappingRatificationError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    s6_pack = Path(sealed_s6_pack)
    observation = Path(sealed_observation_pack)
    s6_rc = verify_manifest_sha256_v1(store_root=s6_pack)
    observation_rc = verify_manifest_sha256_v1(store_root=observation)
    if s6_rc != 0 or observation_rc != 0:
        raise AccountEquitySourceMappingRatificationError("MANIFEST_VERIFY_NOT_ZERO")
    missing = [name for name in REQUIRED_S6_FILES if not (s6_pack / name).is_file()]
    if missing:
        raise AccountEquitySourceMappingRatificationError(f"S6_INPUT_FILE_MISSING:{missing[0]}")
    claims = _load_json_object(path=s6_pack / S6_CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="GENESIS_AS_OF", payload=claims, expected=EXPECTED_GENESIS_AS_OF)
    _require_token(field="S6_EXECUTED", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="SEALED_INPUT_ONLY", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="MAPPING_PERSISTED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="RAW_EQ_SOURCE_AUTHORITY", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="MS2_AUTHORIZED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="D6_FULLY_CLOSED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="D7_AUTHORIZED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="FIELD_SEMANTIC_TRACE_PERSISTED", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="NEW_NETWORK_GET_COUNT", payload=claims, expected="0")
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
    embedding = _load_json_object(path=s6_pack / S6_EMBEDDING_FILE)
    facts = embedding.get("facts")
    if not isinstance(facts, list):
        raise AccountEquitySourceMappingRatificationError("S6_EMBEDDING_FACTS_NOT_LIST")
    observed_fact_ids = [str(fact.get("fact_id") or "") for fact in facts if isinstance(fact, dict)]
    if tuple(observed_fact_ids) != UNKNOWN_EMBEDDING_FACTS:
        raise AccountEquitySourceMappingRatificationError("EMBEDDING_FACT_SET_DRIFT")
    for fact_id in UNKNOWN_EMBEDDING_FACTS:
        reject_include_exclude_from_unknown_embedding_v1(
            decision=DECISION_REMAIN_UNKNOWN,
            fact_id=fact_id,
        )
    fields = _load_json_object(path=s6_pack / S6_FIELD_FILE)
    raw_records = fields.get("records")
    if not isinstance(raw_records, list):
        raise AccountEquitySourceMappingRatificationError("S6_FIELD_RECORDS_NOT_LIST")
    candidate_csv = str(claims.get("RATIFICATION_CANDIDATES") or "")
    candidate_paths = [item for item in candidate_csv.split(",") if item]
    mapping_records: list[dict[str, str]] = []
    for raw in raw_records:
        if not isinstance(raw, dict):
            raise AccountEquitySourceMappingRatificationError("S6_FIELD_RECORD_NOT_OBJECT")
        record = {str(key): str(value) for key, value in raw.items()}
        mapping_records.append(_adjudicate_s6_record(s6=record, s6_pack=s6_pack))
    by_path = {record["field_path"]: record for record in mapping_records}
    missing_candidates = [path for path in candidate_paths if path not in by_path]
    if missing_candidates:
        raise AccountEquitySourceMappingRatificationError(
            f"RATIFICATION_CANDIDATE_MISSING:{missing_candidates[0]}"
        )
    source_kinds = [
        record["field_path"]
        for record in mapping_records
        if record["ratification_status"] == STATUS_RATIFIED_SOURCE_KIND
    ]
    if source_kinds:
        raise AccountEquitySourceMappingRatificationError("RATIFIED_SOURCE_KIND_MUST_REMAIN_EMPTY")
    non_source = [
        record["field_path"]
        for record in mapping_records
        if record["ratification_status"] == STATUS_RATIFIED_NON_SOURCE
    ]
    other_domain = [
        record["field_path"]
        for record in mapping_records
        if record["ratification_status"] == STATUS_RATIFIED_OTHER_DOMAIN
    ]
    unresolved = [
        record["field_path"]
        for record in mapping_records
        if record["ratification_status"]
        in {
            STATUS_UNRESOLVED_AMBIGUOUS,
            STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY,
            STATUS_UNRESOLVED_INSUFFICIENT_EVIDENCE,
        }
    ]
    remaining = (
        f"{CANDIDATE_U05},{CANDIDATE_U06},{CANDIDATE_RESIDUAL},"
        "F12_F13_F16_F17_F18_UNKNOWN,"
        "RETENTION_COVERAGE_FAIL_CLOSED_NOT_PROVEN,"
        "ORDERING_COMPLETENESS_FAIL_CLOSED_NOT_PROVEN,"
        "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_ABSENT,"
        "NO_RATIFIED_EQUITY_STOCK_SOURCE_KIND"
    )
    pack_root = Path(evidence_root) / _folder_from_as_of(ratification_as_of)
    pack_root.mkdir(parents=True, exist_ok=True)
    result_claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "RATIFICATION_AS_OF": ratification_as_of,
        "SEALED_S6_PACK": str(s6_pack),
        "SEALED_OBSERVATION_PACK": str(observation),
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "MANIFESTS_VERIFY": TRUE_TOKEN,
        "S6_MANIFEST_VERIFY_RC": str(s6_rc),
        "OBSERVATION_MANIFEST_VERIFY_RC": str(observation_rc),
        "RATIFICATION_CANDIDATE_COUNT": str(len(candidate_paths)),
        "RATIFIED_SOURCE_KINDS": NONE_TOKEN,
        "RATIFIED_NON_SOURCE_FIELDS": _csv(non_source),
        "RATIFIED_OTHER_DOMAIN_FIELDS": _csv(other_domain),
        "UNRESOLVED_FIELDS": _csv(unresolved),
        "U05_KIND_DECISION": U05_KIND_DECISION,
        "U06_KIND_DECISION": U06_KIND_DECISION,
        "RESIDUAL_KIND_DECISION": RESIDUAL_KIND_DECISION,
        "F12_STATUS": "UNKNOWN",
        "F13_STATUS": "UNKNOWN",
        "F16_STATUS": "UNKNOWN",
        "F17_STATUS": "UNKNOWN",
        "F18_STATUS": "UNKNOWN",
        "KIND_SET": OBSERVED_KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "SOURCE_MAPPING": MAPPING_COVERAGE_PARTIAL,
        "MAPPING_PERSISTED": TRUE_TOKEN,
        "MAPPING_COVERAGE_STATUS": MAPPING_COVERAGE_PARTIAL,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "RETENTION_COVERAGE_STATUS": RETENTION_COVERAGE_FAIL_CLOSED,
        "ORDERING_COMPLETENESS_STATUS": ORDERING_COMPLETENESS_FAIL_CLOSED,
        "COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN": FALSE_TOKEN,
        "REMAINING_D6_BLOCKERS": remaining,
        "NEW_NETWORK_GET_COUNT": "0",
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "MS2_EXECUTED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "ATLAS_AUTHORITY": "NONE",
        "AUTHORITY_EFFECT": "NONE",
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "OBSERVED_RELEVANT_FIELD_COUNT": str(len(mapping_records)),
    }
    _persist_json(path=pack_root / "claims.json", payload=result_claims)
    _persist_json(
        path=pack_root / "source_mapping_records_v1.json",
        payload={
            "mapping_persisted": TRUE_TOKEN,
            "ratified_source_kind_set": NONE_TOKEN,
            "kind_set_resolved": FALSE_TOKEN,
            "raw_eq_source_authority": FALSE_TOKEN,
            "record_count": str(len(mapping_records)),
            "records": mapping_records,
        },
    )
    _persist_json(
        path=pack_root / "kind_set_revaluation_v1.json",
        payload={
            "kind_set": OBSERVED_KIND_SET_EMPTY,
            "kind_set_resolved": FALSE_TOKEN,
            "ratified_source_kinds": NONE_TOKEN,
            "u05_kind_decision": U05_KIND_DECISION,
            "u06_kind_decision": U06_KIND_DECISION,
            "residual_kind_decision": RESIDUAL_KIND_DECISION,
            "unknown_necessary_class_remains": TRUE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
            "complete_classified_event_stream_proven": FALSE_TOKEN,
            "remaining_d6_blockers": remaining,
        },
    )
    _persist_json(
        path=pack_root / "embedding_facts_v1.json",
        payload={
            "facts": [
                {
                    "fact_id": fact_id,
                    "status": "UNKNOWN",
                    "decision": DECISION_REMAIN_UNKNOWN,
                    "include_from_unknown": "FORBIDDEN",
                    "exclude_from_unknown": "FORBIDDEN",
                }
                for fact_id in UNKNOWN_EMBEDDING_FACTS
            ],
            "include_exclude_from_unknown": "FORBIDDEN",
        },
    )
    _persist_json(
        path=pack_root / "fail_closed_guards_v1.json",
        payload={
            "unratified_source_kind_use": "FORBIDDEN",
            "raw_eq_source_authority": FALSE_TOKEN,
            "classified_kind_set": OBSERVED_KIND_SET_EMPTY,
            "retention_coverage_status": RETENTION_COVERAGE_FAIL_CLOSED,
            "ordering_completeness_status": ORDERING_COMPLETENESS_FAIL_CLOSED,
            "ms2_authorized": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=pack_root)
    return AccountEquitySourceMappingRatificationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        ratification_as_of=ratification_as_of,
        store_root=str(pack_root),
        sealed_s6_pack=str(s6_pack),
        sealed_observation_pack=str(observation),
        sealed_input_only=TRUE_TOKEN,
        manifests_verify=TRUE_TOKEN,
        ratification_candidate_count=str(len(candidate_paths)),
        ratified_source_kinds=NONE_TOKEN,
        ratified_non_source_fields=_csv(non_source),
        ratified_other_domain_fields=_csv(other_domain),
        unresolved_fields=_csv(unresolved),
        u05_kind_decision=U05_KIND_DECISION,
        u06_kind_decision=U06_KIND_DECISION,
        residual_kind_decision=RESIDUAL_KIND_DECISION,
        f12_f13_f16_f17_f18_status="UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN",
        kind_set=OBSERVED_KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        source_mapping=MAPPING_COVERAGE_PARTIAL,
        mapping_persisted=TRUE_TOKEN,
        mapping_coverage_status=MAPPING_COVERAGE_PARTIAL,
        raw_eq_source_authority=FALSE_TOKEN,
        retention_coverage_status=RETENTION_COVERAGE_FAIL_CLOSED,
        ordering_completeness_status=ORDERING_COMPLETENESS_FAIL_CLOSED,
        complete_classified_event_stream_proven=FALSE_TOKEN,
        remaining_d6_blockers=remaining,
        new_network_get_count="0",
        network_post_performed=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        ms2_executed=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )
