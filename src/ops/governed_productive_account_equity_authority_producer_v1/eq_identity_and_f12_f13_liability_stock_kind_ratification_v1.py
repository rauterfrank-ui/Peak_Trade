"""D6 eq-identity and F12/F13/U05 liability-stock kind ratification.

Sealed-input-only. Extracts forensic eq/cashBal/upl/liab* tokens from the
already-sealed BH raw body without rewriting it. Inventories today's
canonical semantic sources and ratifies D6 eq IDENTITY as embedding
identity, not as RAW_EQ or STEP-29P source authority.

Governed semantic salvage: preserve evidence, re-ratify under current
canonical semantics, do not restore legacy equity structure or C01-C16.
Algebraic eq-vs-cashBal/upl/liab identity is forbidden. NONE and
REMAIN_UNKNOWN are valid fail-closed outcomes. No GET. No POST.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_and_complete_event_stream_acquisition_v1 import (
    CANONICAL_MAPPING_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    CANONICAL_S6_PACK_RELPATH,
    RATIFIED_SOURCE_KIND_SET,
    assert_eq_is_not_source_authority_v1,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_f16_f17_f18_necessary_equity_stock_kind_resolution_v1 import (
    CANONICAL_ACQUISITION_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_primary_liability_stock_observation_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BH_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.option_d_ssot_architecture_contract_v1 import (
    FORBIDDEN_SOURCE_FIELDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    reject_include_exclude_from_unknown_embedding_v1,
)

OWNER_GO = "OWNER_GO_D6_EQ_IDENTITY_AND_F12_F13_LIABILITY_STOCK_KIND_RATIFICATION_V1"
EXPECTED_ORIGIN_MAIN_SHA = "afa6b7c51cb73bbd36b91c01e40e4947ada10873"
CANONICAL_BG_PACK_RELPATH = (
    "evidence/ops/full_core_d6_f12_f13_f16_f17_f18_necessary_equity_stock_kind_resolution_v1/"
    "2026-09-13T200000Z"
)
RATIFICATION_STORE_RELPATH = (
    "evidence/ops/full_core_d6_eq_identity_and_f12_f13_liability_stock_kind_ratification_v1"
)
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_d6_eq_identity_and_f12_f13_liability_stock_kind_ratification_v1/"
    "2026-09-13T230000Z"
)
BH_RAW_BODY_FILE = "raw_account_balance_response_body.json"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATUS_UNKNOWN = "UNKNOWN"
DECISION_INCLUDE = "INCLUDE"
DECISION_EXCLUDE = "EXCLUDE"
IDENTITY_INCLUDES_LIABILITY = "INCLUDES_LIABILITY"
IDENTITY_EXCLUDES_LIABILITY = "EXCLUDES_LIABILITY"
IDENTITY_COMPOSITION_PARTIAL = "COMPOSITION_PARTIAL"
IDENTITY_NONE = "NONE"
RETENTION_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
DAG_PIN = "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
F16_F17_F18_BLOCKER = (
    "F16_F17_F18_RESOLUTION_REQUIRES_PAIRED_FEE_EVENT_AND_EQUITY_STOCK_OBSERVATION"
    "_OR_RATIFIED_EQ_IDENTITY"
)
EARLIEST_REMAINING_D6_BLOCKER = (
    "F12_F13_REMAIN_UNKNOWN_AFTER_EQ_IDENTITY_NONE_AND_AUTHORIZED_FRESH_BALANCE_GET_"
    "EMPTY_OR_ZERO_DOES_NOT_PROVE_ABSENCE"
)
KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY = (
    "F12_F13_EQ_IDENTITY_NONE_AND_AUTHORIZED_FRESH_BALANCE_GET_EMPTY_OR_ZERO_DOES_NOT_PROVE_ABSENCE"
)
IDENTITY_RAW_FIELDS: tuple[str, ...] = (
    "eq",
    "cashBal",
    "upl",
    "uplLiab",
    "liab",
    "crossLiab",
    "isoLiab",
    "borrowFroz",
)
ALLOWED_IDENTITY_OUTCOMES = frozenset(
    {
        IDENTITY_INCLUDES_LIABILITY,
        IDENTITY_EXCLUDES_LIABILITY,
        IDENTITY_COMPOSITION_PARTIAL,
        IDENTITY_NONE,
    }
)
ALLOWED_FACT_DECISIONS = frozenset({DECISION_INCLUDE, DECISION_EXCLUDE, DECISION_REMAIN_UNKNOWN})
CLAIMS_FILE = "claims.json"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class EqIdentityAndF12F13LiabilityStockKindRatificationError(ValueError):
    """Fail-closed D6 eq-identity and F12/F13/U05 ratification violation."""


@dataclass(frozen=True)
class EqIdentityAndF12F13LiabilityStockKindRatificationResultV1:
    genesis_id: str
    genesis_as_of: str
    ratification_as_of: str
    store_root: str
    ratified_eq_identity: str
    f12_decision: str
    f13_decision: str
    u05_kind_decision: str
    f16_decision: str
    f17_decision: str
    f18_decision: str
    ratified_source_kinds: str
    kind_set: str
    kind_set_resolved: str
    raw_eq_source_authority: str
    eq_reconciliation_target_only: str
    earliest_remaining_d6_blocker: str
    new_network_get_count: str
    network_post_performed: str
    ms2_authorized: str
    d6_fully_closed: str
    d7_authorized: str
    legacy_structure_restored: str
    semantic_salvage_rule_applied: str
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
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(f"{field}_DRIFT:{actual}")


def reject_claimed_eq_identity_or_kind_proof_v1(
    *,
    claimed_proof: str,
    fact_id: str,
) -> None:
    forbidden = {
        IDENTITY_INCLUDES_LIABILITY,
        IDENTITY_EXCLUDES_LIABILITY,
        IDENTITY_COMPOSITION_PARTIAL,
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "INCLUDE_AS_NECESSARY_EQUITY_STOCK_KIND",
        "EXCLUDE_AS_NON_SOURCE_OR_OTHER_DOMAIN",
        "ALGEBRAIC_EQ_IDENTITY",
        "EQ_MINUS_CASHBAL_PROVES_EMBEDDING",
        "EMPTY_LIAB_MEANS_F12_FALSE",
        "ZERO_LIAB_MEANS_F13_TRUE",
        "RESTORE_LEGACY_EQUITY_LOGIC",
        "RESTORE_C01_C16_MAPPING",
        "ELEVATE_EQ_TO_RAW_EQ_SOURCE_AUTHORITY",
        "FIELD_PRESENCE_PROVES_COMPOSITION",
    }
    if claimed_proof in forbidden:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            f"EQ_IDENTITY_CANNOT_{claimed_proof}:{fact_id}"
        )
    if claimed_proof not in {
        "REMAIN_UNKNOWN_NO_UNIQUE_EQ_IDENTITY_PROOF",
        IDENTITY_NONE,
    }:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            f"EQ_IDENTITY_PROOF_UNKNOWN:{claimed_proof}"
        )


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            "SOURCE_KIND_SET_MUST_REMAIN_EMPTY"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if MS2_AUTHORIZED is not False:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if "eq" not in FORBIDDEN_SOURCE_FIELDS or "cashBal" not in FORBIDDEN_SOURCE_FIELDS:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            "FORBIDDEN_SOURCE_FIELD_PIN_DRIFT"
        )
    assert_eq_is_not_source_authority_v1(
        field_name="eq",
        ratification_status="RATIFIED_NON_SOURCE",
    )
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )
    reject_include_exclude_from_unknown_embedding_v1(
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        decision=DECISION_REMAIN_UNKNOWN,
    )


def _classify_raw_token(*, row: Mapping[str, Any], field: str) -> dict[str, str]:
    if field not in row:
        return {
            "field": field,
            "presence": "ABSENT",
            "python_type": "MISSING",
            "raw_token": "",
            "exact_empty_string": FALSE_TOKEN,
            "exact_zero_string": FALSE_TOKEN,
            "nonzero_string_token": FALSE_TOKEN,
            "empty_zero_null_missing_not_normalized": TRUE_TOKEN,
        }
    raw = row[field]
    if raw is None:
        return {
            "field": field,
            "presence": "NULL",
            "python_type": "NoneType",
            "raw_token": "",
            "exact_empty_string": FALSE_TOKEN,
            "exact_zero_string": FALSE_TOKEN,
            "nonzero_string_token": FALSE_TOKEN,
            "empty_zero_null_missing_not_normalized": TRUE_TOKEN,
        }
    if isinstance(raw, bool):
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            f"FORENSIC_BOOL_TOKEN_FORBIDDEN:{field}"
        )
    if isinstance(raw, (int, float)):
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            f"FORENSIC_NUMERIC_NORMALIZATION_FORBIDDEN:{field}"
        )
    if not isinstance(raw, str):
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            f"FORENSIC_TOKEN_NOT_STRING:{field}:{type(raw).__name__}"
        )
    return {
        "field": field,
        "presence": "STRING",
        "python_type": "str",
        "raw_token": raw,
        "exact_empty_string": TRUE_TOKEN if raw == "" else FALSE_TOKEN,
        "exact_zero_string": TRUE_TOKEN if raw == "0" else FALSE_TOKEN,
        "nonzero_string_token": TRUE_TOKEN if raw not in {"", "0"} else FALSE_TOKEN,
        "empty_zero_null_missing_not_normalized": TRUE_TOKEN,
    }


def _extract_forensic_identity_tokens(*, payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if data is None:
        rows: list[Any] = []
        data_presence = "ABSENT"
    elif not isinstance(data, list):
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("VENUE_DATA_NOT_LIST")
    else:
        rows = list(data)
        data_presence = "LIST"
    details_out: list[dict[str, Any]] = []
    account_tokens: list[dict[str, str]] = []
    if rows and isinstance(rows[0], Mapping):
        account_row = rows[0]
        account_tokens = [
            _classify_raw_token(row=account_row, field=field) for field in IDENTITY_RAW_FIELDS
        ]
        nested = account_row.get("details")
        if isinstance(nested, list):
            for item in nested:
                if not isinstance(item, Mapping):
                    continue
                ccy_token = _classify_raw_token(row=item, field="ccy")
                details_out.append(
                    {
                        "ccy_presence": ccy_token["presence"],
                        "ccy_raw_token": ccy_token["raw_token"],
                        "tokens": [
                            _classify_raw_token(row=item, field=field)
                            for field in IDENTITY_RAW_FIELDS
                        ],
                    }
                )
    return {
        "layer": "FORENSIC_RAW",
        "interpretation_status": "FORBIDDEN",
        "algebraic_eq_identity": "FORBIDDEN",
        "numeric_composition_derived": FALSE_TOKEN,
        "legacy_equity_logic_restored": FALSE_TOKEN,
        "data_presence": data_presence,
        "row_count": str(len(rows)),
        "account_level_identity_tokens": account_tokens,
        "details": details_out,
        "eq_remains_reconciliation_target_only": TRUE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
    }


def _semantic_source_inventory() -> dict[str, Any]:
    records = [
        {
            "source_id": "RUNBOOK_11_2_1_AR",
            "source_path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.AR",
            "layer": "CANONICAL_AUTHORITY",
            "quoted_binding": "EQ_RECONCILIATION_TARGET_ONLY=true;RAW_EQ_SOURCE_AUTHORITY=false",
            "unique_eq_composition_proof": FALSE_TOKEN,
            "unique_liability_inclusion_proof": FALSE_TOKEN,
            "unique_liability_exclusion_proof": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
        },
        {
            "source_id": "RUNBOOK_11_2_1_S",
            "source_path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.S",
            "layer": "CANONICAL_AUTHORITY",
            "quoted_binding": (
                "ADJUDICATION_RESULT=NO_CANONICALLY_VALID_MAPPING_AVAILABLE;"
                "eq/availEq/totalEq/adjEq/availBal/cashBal_FORBIDDEN_AS_RUNNING_EQUITY_SOURCE"
            ),
            "unique_eq_composition_proof": FALSE_TOKEN,
            "unique_liability_inclusion_proof": FALSE_TOKEN,
            "unique_liability_exclusion_proof": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
        },
        {
            "source_id": "RUNBOOK_11_2_1_BE",
            "source_path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.BE",
            "layer": "CANONICAL_AUTHORITY",
            "quoted_binding": "details.eq=FRESH_EQ_RECONCILIATION_TARGET_NOT_SOURCE;U05=UNRESOLVED_AMBIGUOUS",
            "unique_eq_composition_proof": FALSE_TOKEN,
            "unique_liability_inclusion_proof": FALSE_TOKEN,
            "unique_liability_exclusion_proof": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
        },
        {
            "source_id": "RUNBOOK_11_2_1_BG",
            "source_path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.BG",
            "layer": "CANONICAL_AUTHORITY",
            "quoted_binding": "ratified_eq_identity_absent;algebraic_inference=FORBIDDEN",
            "unique_eq_composition_proof": FALSE_TOKEN,
            "unique_liability_inclusion_proof": FALSE_TOKEN,
            "unique_liability_exclusion_proof": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
        },
        {
            "source_id": "RUNBOOK_11_2_1_BH",
            "source_path": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#11.2.1.BH",
            "layer": "CANONICAL_AUTHORITY",
            "quoted_binding": (
                "does_not_infer_eq_identity_from_cashBal_or_upl;"
                "F12_DECISION=REMAIN_UNKNOWN;F13_DECISION=REMAIN_UNKNOWN"
            ),
            "unique_eq_composition_proof": FALSE_TOKEN,
            "unique_liability_inclusion_proof": FALSE_TOKEN,
            "unique_liability_exclusion_proof": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
        },
        {
            "source_id": "OPTION_D_FORBIDDEN_SOURCE_FIELDS",
            "source_path": (
                "src/ops/governed_productive_account_equity_authority_producer_v1/"
                "option_d_ssot_architecture_contract_v1.py"
            ),
            "layer": "CANONICAL_AUTHORITY",
            "quoted_binding": "FORBIDDEN_SOURCE_FIELDS includes eq and cashBal",
            "unique_eq_composition_proof": FALSE_TOKEN,
            "unique_liability_inclusion_proof": FALSE_TOKEN,
            "unique_liability_exclusion_proof": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
        },
    ]
    unique_proofs = [
        record["unique_eq_composition_proof"] == TRUE_TOKEN
        or record["unique_liability_inclusion_proof"] == TRUE_TOKEN
        or record["unique_liability_exclusion_proof"] == TRUE_TOKEN
        for record in records
    ]
    return {
        "layer": "CANONICAL_AUTHORITY",
        "semantic_salvage_rule_applied": TRUE_TOKEN,
        "legacy_structure_restored": FALSE_TOKEN,
        "historical_semantics_are_not_current_authority": TRUE_TOKEN,
        "c01_c16_revival_forbidden": TRUE_TOKEN,
        "unique_composition_proof_present": TRUE_TOKEN if any(unique_proofs) else FALSE_TOKEN,
        "records": records,
    }


def _ratify_eq_identity(*, inventory: Mapping[str, Any]) -> dict[str, str]:
    unique = inventory["unique_composition_proof_present"] == TRUE_TOKEN
    if unique:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            "UNEXPECTED_UNIQUE_COMPOSITION_PROOF"
        )
    outcome = IDENTITY_NONE
    if outcome not in ALLOWED_IDENTITY_OUTCOMES:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("IDENTITY_OUTCOME_NOT_ALLOWED")
    return {
        "layer": "ADJUDICATED",
        "ratified_eq_identity": outcome,
        "identity_role": "D6_EMBEDDING_IDENTITY_NOT_RUNNING_EQUITY_SOURCE",
        "raw_eq_source_authority": FALSE_TOKEN,
        "eq_reconciliation_target_only": TRUE_TOKEN,
        "algebraic_inference": "FORBIDDEN",
        "legacy_equity_logic_restored": FALSE_TOKEN,
        "c01_c16_revived": FALSE_TOKEN,
        "reason": "NO_UNIQUE_CANONICAL_EQ_COMPOSITION_PROOF",
        "semantic_salvage_rule_applied": TRUE_TOKEN,
    }


def _adjudicate_facts(*, identity: str) -> list[dict[str, str]]:
    if identity != IDENTITY_NONE:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError(
            f"IDENTITY_NOT_FAIL_CLOSED_NONE:{identity}"
        )
    reject_claimed_eq_identity_or_kind_proof_v1(
        claimed_proof="REMAIN_UNKNOWN_NO_UNIQUE_EQ_IDENTITY_PROOF",
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    )
    f12_f13_u05 = DECISION_REMAIN_UNKNOWN
    f16_f17_f18 = DECISION_REMAIN_UNKNOWN
    if f12_f13_u05 not in ALLOWED_FACT_DECISIONS:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("FACT_DECISION_NOT_ALLOWED")
    return [
        {
            "fact_id": "F12_LIABILITY_AFFECTS_EQUITY_STOCK",
            "decision": f12_f13_u05,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "ratified_eq_identity": identity,
            "missing_evidence": (
                "UNIQUE_EQ_IDENTITY_PROOF_OR_NONZERO_LIABILITY_STOCK_PRIMARY_OBSERVATION"
            ),
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "algebraic_inference": "FORBIDDEN",
            "legacy_structure_restored": FALSE_TOKEN,
            "layer": "ADJUDICATED",
        },
        {
            "fact_id": "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
            "decision": f12_f13_u05,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "ratified_eq_identity": identity,
            "missing_evidence": "UNIQUE_EQ_IDENTITY_PROOF_OR_PAIRED_LIABILITY_AND_EQ_OBSERVATION",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "algebraic_inference": "FORBIDDEN",
            "legacy_structure_restored": FALSE_TOKEN,
            "layer": "ADJUDICATED",
        },
        {
            "fact_id": "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "decision": f12_f13_u05,
            "status": STATUS_UNKNOWN,
            "kind_disposition": DECISION_REMAIN_UNKNOWN,
            "ratified_eq_identity": identity,
            "blocked_by": "F12_AND_F13_REMAIN_UNKNOWN",
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "legacy_structure_restored": FALSE_TOKEN,
            "layer": "ADJUDICATED",
        },
        {
            "fact_id": "F16_FEE_ALREADY_EMBEDDED_IN_EQ",
            "decision": f16_f17_f18,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "same_identity_uniquely_decides": FALSE_TOKEN,
            "missing_evidence": F16_F17_F18_BLOCKER,
            "layer": "ADJUDICATED",
        },
        {
            "fact_id": "F17_FEE_SEPARATE_ACCOUNT_DELTA",
            "decision": f16_f17_f18,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "same_identity_uniquely_decides": FALSE_TOKEN,
            "missing_evidence": F16_F17_F18_BLOCKER,
            "layer": "ADJUDICATED",
        },
        {
            "fact_id": "F18_FEE_RECONCILIATION_ONLY",
            "decision": f16_f17_f18,
            "status": STATUS_UNKNOWN,
            "kind_candidate": "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "same_identity_uniquely_decides": FALSE_TOKEN,
            "missing_evidence": F16_F17_F18_BLOCKER,
            "layer": "ADJUDICATED",
        },
    ]


def execute_eq_identity_and_f12_f13_liability_stock_kind_ratification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bh_pack: Path | str,
    sealed_observation_pack: Path | str,
    sealed_s6_pack: Path | str,
    sealed_mapping_pack: Path | str,
    sealed_acquisition_pack: Path | str,
    sealed_bg_pack: Path | str,
    evidence_root: Path | str,
    ratification_as_of: str,
) -> EqIdentityAndF12F13LiabilityStockKindRatificationResultV1:
    if owner_go != OWNER_GO:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    bh_pack = Path(sealed_bh_pack)
    observation = Path(sealed_observation_pack)
    s6_pack = Path(sealed_s6_pack)
    mapping = Path(sealed_mapping_pack)
    acquisition = Path(sealed_acquisition_pack)
    bg_pack = Path(sealed_bg_pack)
    verify_codes = {
        "BH": verify_manifest_sha256_v1(store_root=bh_pack),
        "S1_S5": verify_manifest_sha256_v1(store_root=observation),
        "S6": verify_manifest_sha256_v1(store_root=s6_pack),
        "MAPPING": verify_manifest_sha256_v1(store_root=mapping),
        "ACQUISITION": verify_manifest_sha256_v1(store_root=acquisition),
        "BG": verify_manifest_sha256_v1(store_root=bg_pack),
    }
    if any(code != 0 for code in verify_codes.values()):
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("MANIFEST_VERIFY_NOT_ZERO")
    bh_claims = _load_json_object(path=bh_pack / CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=bh_claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="GENESIS_AS_OF", payload=bh_claims, expected=EXPECTED_GENESIS_AS_OF)
    _require_token(field="GET_COUNT", payload=bh_claims, expected="1")
    _require_token(field="POST_COUNT", payload=bh_claims, expected="0")
    _require_token(field="NONZERO_LIABILITY_OBSERVED", payload=bh_claims, expected=FALSE_TOKEN)
    _require_token(field="F12_DECISION", payload=bh_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F13_DECISION", payload=bh_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="RAW_EQ_SOURCE_AUTHORITY", payload=bh_claims, expected=FALSE_TOKEN)
    raw_path = bh_pack / BH_RAW_BODY_FILE
    raw_bytes = raw_path.read_bytes()
    payload_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    expected_sha = str(bh_claims.get("PAYLOAD_SHA256") or "")
    if expected_sha and expected_sha != payload_sha256:
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("BH_RAW_BODY_HASH_DRIFT")
    payload = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise EqIdentityAndF12F13LiabilityStockKindRatificationError("BH_RAW_BODY_NOT_OBJECT")
    forensic = _extract_forensic_identity_tokens(payload=payload)
    inventory = _semantic_source_inventory()
    identity_record = _ratify_eq_identity(inventory=inventory)
    facts = _adjudicate_facts(identity=identity_record["ratified_eq_identity"])
    ranked = [
        {
            "rank": "1",
            "blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "covers_facts": "F12_LIABILITY_AFFECTS_EQUITY_STOCK,F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ,U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
            "blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "role": "EARLIEST_REMAINING_D6_BLOCKER",
            "new_get_authorized": FALSE_TOKEN,
            "repeat_get_hoping_for_nonzero_forbidden": TRUE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
        },
        {
            "rank": "2",
            "blocker": F16_F17_F18_BLOCKER,
            "covers_facts": (
                "F16_FEE_ALREADY_EMBEDDED_IN_EQ,"
                "F17_FEE_SEPARATE_ACCOUNT_DELTA,"
                "F18_FEE_RECONCILIATION_ONLY"
            ),
            "same_identity_uniquely_decides": FALSE_TOKEN,
            "not_changed_this_go": TRUE_TOKEN,
            "new_get_authorized": FALSE_TOKEN,
        },
    ]
    folder = _folder_from_as_of(ratification_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": "NONE",
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "RATIFICATION_AS_OF": ratification_as_of,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "SEALED_BH_PACK": CANONICAL_BH_PACK_RELPATH,
        "SEALED_OBSERVATION_PACK": CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
        "SEALED_S6_PACK": CANONICAL_S6_PACK_RELPATH,
        "SEALED_MAPPING_PACK": CANONICAL_MAPPING_PACK_RELPATH,
        "SEALED_ACQUISITION_PACK": CANONICAL_ACQUISITION_PACK_RELPATH,
        "SEALED_BG_PACK": CANONICAL_BG_PACK_RELPATH,
        "BH_RAW_BODY_REWRITTEN": FALSE_TOKEN,
        "BH_RAW_PAYLOAD_SHA256": payload_sha256,
        "MANIFESTS_VERIFY": TRUE_TOKEN,
        "NEW_NETWORK_GET_COUNT": "0",
        "VENUE_GET_COUNT": "0",
        "POST_COUNT": "0",
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "RATIFIED_EQ_IDENTITY": identity_record["ratified_eq_identity"],
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "F12_STATUS": STATUS_UNKNOWN,
        "F13_STATUS": STATUS_UNKNOWN,
        "U05_STATUS": STATUS_UNKNOWN,
        "F16_STATUS": STATUS_UNKNOWN,
        "F17_STATUS": STATUS_UNKNOWN,
        "F18_STATUS": STATUS_UNKNOWN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": EARLIEST_REMAINING_D6_BLOCKER,
        "NARROWER_THAN_BH": TRUE_TOKEN,
        "RATIFIED_SOURCE_KINDS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "EQ_RECONCILIATION_TARGET_ONLY": TRUE_TOKEN,
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
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "C01_REHABILITATION_FORBIDDEN": TRUE_TOKEN,
        "C01_C16_REVIVED": FALSE_TOKEN,
        "LEGACY_STRUCTURE_RESTORED": FALSE_TOKEN,
        "SEMANTIC_SALVAGE_RULE_APPLIED": TRUE_TOKEN,
        "EXISTING_NON_SOURCE_AND_OTHER_DOMAIN_UNCHANGED": TRUE_TOKEN,
        "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED": FALSE_TOKEN,
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "BULL_BEAR_STATE_SWITCH_UNCHANGED": TRUE_TOKEN,
        "TOP20_RANKING_UNIVERSE_UNCHANGED": TRUE_TOKEN,
        "TOP20_SELECTION_BINDINGS_UNCHANGED": TRUE_TOKEN,
        "SELF_LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_AUTONOMY_UNCHANGED": TRUE_TOKEN,
        "STEP_29P_UNCHANGED": TRUE_TOKEN,
        "BH_MANIFEST_VERIFY_RC": str(verify_codes["BH"]),
        "S1_S5_MANIFEST_VERIFY_RC": str(verify_codes["S1_S5"]),
        "S6_MANIFEST_VERIFY_RC": str(verify_codes["S6"]),
        "MAPPING_MANIFEST_VERIFY_RC": str(verify_codes["MAPPING"]),
        "ACQUISITION_MANIFEST_VERIFY_RC": str(verify_codes["ACQUISITION"]),
        "BG_MANIFEST_VERIFY_RC": str(verify_codes["BG"]),
    }
    _persist_json(
        path=store / "layers_v1.json",
        payload={
            "CANONICAL_AUTHORITY": "semantic_source_inventory_v1.json",
            "FORENSIC_RAW": "forensic_eq_identity_tokens_v1.json",
            "ADJUDICATED": "eq_identity_ratification_v1.json,f12_f13_u05_adjudication_v1.json",
            "HISTORICAL": ",".join(
                [
                    CANONICAL_BH_PACK_RELPATH,
                    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
                    CANONICAL_S6_PACK_RELPATH,
                    CANONICAL_MAPPING_PACK_RELPATH,
                    CANONICAL_ACQUISITION_PACK_RELPATH,
                    CANONICAL_BG_PACK_RELPATH,
                ]
            ),
            "NAVIGATION": "NONE",
            "INTERPRETATION": "FORBIDDEN",
            "HYPOTHESIS": "FORBIDDEN",
            "UNRESOLVED": "ranked_remaining_d6_blockers_v1.json,missing_primary_evidence_v1.json",
        },
    )
    _persist_json(path=store / "semantic_source_inventory_v1.json", payload=inventory)
    _persist_json(path=store / "forensic_eq_identity_tokens_v1.json", payload=forensic)
    _persist_json(path=store / "eq_identity_ratification_v1.json", payload=identity_record)
    _persist_json(
        path=store / "f12_f13_u05_adjudication_v1.json",
        payload={"facts": facts, "layer": "ADJUDICATED"},
    )
    _persist_json(
        path=store / "missing_primary_evidence_v1.json",
        payload={
            "layer": "UNRESOLVED",
            "ratified_eq_identity": IDENTITY_NONE,
            "unique_eq_composition_proof_present": FALSE_TOKEN,
            "algebraic_inference": "FORBIDDEN",
            "authorized_fresh_balance_get_consumed": TRUE_TOKEN,
            "empty_or_zero_does_not_prove_absence": TRUE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
            "semantic_salvage_rule_applied": TRUE_TOKEN,
            "f16_f17_f18_uniquely_decided_by_same_identity": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "ranked_remaining_d6_blockers_v1.json",
        payload={
            "layer": "UNRESOLVED",
            "earliest_remaining_d6_blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "kind_set_include_exclude_blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "narrower_than_bh": TRUE_TOKEN,
            "records": ranked,
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "include_exclude_from_unknown": "FORBIDDEN",
            "algebraic_inference": "FORBIDDEN",
            "new_network_get": "FORBIDDEN",
            "repeat_get_hoping_for_nonzero": "FORBIDDEN",
            "raw_eq_source_authority": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
            "c01_c16_revived": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "classified_kind_set": KIND_SET_EMPTY,
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "layer": "HISTORICAL",
            "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
            "owner_go": OWNER_GO,
            "genesis_id": EXPECTED_GENESIS_ID,
            "parent_bh": CANONICAL_BH_PACK_RELPATH,
            "sealed_s1_s5": CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
            "sealed_s6": CANONICAL_S6_PACK_RELPATH,
            "pr_6452_mapping": CANONICAL_MAPPING_PACK_RELPATH,
            "pr_6453_acquisition": CANONICAL_ACQUISITION_PACK_RELPATH,
            "pr_6454_bg_resolution": CANONICAL_BG_PACK_RELPATH,
            "bh_raw_payload_sha256": payload_sha256,
            "legacy_structure_restored": FALSE_TOKEN,
        },
    )
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    manifest = persist_manifest_sha256_v1(store_root=store)
    return EqIdentityAndF12F13LiabilityStockKindRatificationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        ratification_as_of=ratification_as_of,
        store_root=str(store),
        ratified_eq_identity=IDENTITY_NONE,
        f12_decision=DECISION_REMAIN_UNKNOWN,
        f13_decision=DECISION_REMAIN_UNKNOWN,
        u05_kind_decision=DECISION_REMAIN_UNKNOWN,
        f16_decision=DECISION_REMAIN_UNKNOWN,
        f17_decision=DECISION_REMAIN_UNKNOWN,
        f18_decision=DECISION_REMAIN_UNKNOWN,
        ratified_source_kinds=NONE_TOKEN,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        raw_eq_source_authority=FALSE_TOKEN,
        eq_reconciliation_target_only=TRUE_TOKEN,
        earliest_remaining_d6_blocker=EARLIEST_REMAINING_D6_BLOCKER,
        new_network_get_count="0",
        network_post_performed=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        legacy_structure_restored=FALSE_TOKEN,
        semantic_salvage_rule_applied=TRUE_TOKEN,
        evidence_manifest=str(manifest),
    )
