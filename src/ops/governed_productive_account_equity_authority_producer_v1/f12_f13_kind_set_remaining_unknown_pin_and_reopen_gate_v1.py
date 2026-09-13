"""D6 F12/F13 KIND_SET remaining-unknown pin and reopen-gate persist.

Sealed-input-only. Re-reads already persisted BH+BI packs. Pins F12/F13/U05
and F16-F18 as durable REMAIN_UNKNOWN without PATH_C closeout. Names the
only later reopen gates. Does not GET. Does not POST. Does not execute
GATE_A or GATE_B. Does not INCLUDE or EXCLUDE. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

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
    PATH_A_ARCHIVE_OR_REPO_SEARCH,
    PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    CANONICAL_BH_PACK_RELPATH,
    CANONICAL_PACK_RELPATH as CANONICAL_BI_PACK_RELPATH,
    DAG_PIN,
    EARLIEST_REMAINING_D6_BLOCKER as BI_EARLIEST_REMAINING_D6_BLOCKER,
    F16_F17_F18_BLOCKER,
    IDENTITY_NONE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
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

OWNER_GO = "OWNER_GO_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE_V1"
EXPECTED_ORIGIN_MAIN_SHA = "5bb3f690612454ce6c00ab4297cb5291f6a38855"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_d6_f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1/"
    "2026-09-13T235900Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATUS_UNKNOWN = "UNKNOWN"
DECISION_INCLUDE = "INCLUDE"
DECISION_EXCLUDE = "EXCLUDE"
RETENTION_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
SELECTED_BALANCE_SURFACE = "GET_/api/v5/account/balance"
CURRENTLY_DECISION_CAPABLE = "NONE"
EARLIEST_REMAINING_D6_BLOCKER = (
    "F12_F13_REMAIN_UNKNOWN_NO_CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASS_AFTER_BH_AND_BI"
)
KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY = "NO_CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASS_FOR_F12_F13"
GATE_A_ID = "GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK"
GATE_B_ID = "GATE_B_NEWLY_BOUND_UNIQUE_EXTERNAL_EQ_COMPOSITION_AUTHORITY"
CLAIMS_FILE = "claims.json"
EXHAUSTED_OR_FORBIDDEN_CLASSES: tuple[str, ...] = (
    "BH_EMPTY_ZERO_ABSENT_BALANCE_SNAPSHOT",
    "REPEAT_BALANCE_HOPE_GET",
    "ALGEBRAIC_EQ_CASHBAL_UPL_LIAB_COMPOSITION",
    "REPEAT_BI_EQ_IDENTITY_RATIFICATION_FROM_SAME_SOURCES",
    "PACKAGE_1_S1_S5_AND_S6",
    "LEGACY_LEDGER_AS_D6_EQUITY_AUTHORITY",
    "LEGACY_STRUCTURE_RESTORE",
    "C01_C16_REVIVAL",
    "PATH_A_ARCHIVE_OR_REPO_SEARCH",
    "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT",
    "UNSELECTED_POSITIONS_INTEREST_MAX_LOAN_HYPOTHESIS_SURFACES",
    "INCLUDE_EXCLUDE_WITHOUT_PRIMARY_PROOF",
)


class F12F13KindSetRemainingUnknownPinAndReopenGateError(ValueError):
    """Fail-closed remaining-unknown pin and reopen-gate violation."""


@dataclass(frozen=True)
class F12F13KindSetRemainingUnknownPinAndReopenGateResultV1:
    genesis_id: str
    genesis_as_of: str
    pin_as_of: str
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
    currently_decision_capable_evidence_classes: str
    unknown_durable_not_closeout: str
    gate_a_persisted: str
    gate_a_executed: str
    gate_b_persisted: str
    gate_b_executed: str
    venue_get_count: str
    post_count: str
    ms2_authorized: str
    d6_fully_closed: str
    d7_authorized: str
    earliest_remaining_d6_blocker: str
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
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(f"{field}_DRIFT:{actual}")


def reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1(
    *,
    claimed_proof: str,
    fact_id: str,
) -> None:
    forbidden = {
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "INCLUDE_AS_NECESSARY_EQUITY_STOCK_KIND",
        "EXCLUDE_AS_NON_SOURCE_OR_OTHER_DOMAIN",
        "PATH_C_UNKNOWN_CLOSEOUT",
        "D6_FULLY_CLOSED",
        "KIND_SET_RESOLVED_TRUE",
        "EXECUTE_GATE_A",
        "EXECUTE_GATE_B",
        "HOPE_BALANCE_GET",
        "ALGEBRAIC_EQ_IDENTITY",
        "VENDOR_WEB_REPO_ARCHIVE_SEARCH",
        "CREATE_LIABILITY",
        "RESTORE_LEGACY_EQUITY_LOGIC",
        "RESTORE_C01_C16_MAPPING",
    }
    if claimed_proof in forbidden:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(
            f"REMAINING_UNKNOWN_PIN_CANNOT_{claimed_proof}:{fact_id}"
        )
    if claimed_proof not in {
        "REMAIN_UNKNOWN_NO_CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASS",
        "DURABLE_UNKNOWN_NOT_D6_CLOSEOUT",
    }:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(
            f"REMAINING_UNKNOWN_PIN_PROOF_UNKNOWN:{claimed_proof}"
        )


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(
            "SOURCE_KIND_SET_MUST_REMAIN_EMPTY"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if MS2_AUTHORIZED is not False:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if PATH_A_ARCHIVE_OR_REPO_SEARCH != "REJECT":
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("PATH_A_MUST_REMAIN_REJECT")
    if PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT != "REJECT":
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("PATH_C_MUST_REMAIN_REJECT")
    if "eq" not in FORBIDDEN_SOURCE_FIELDS or "cashBal" not in FORBIDDEN_SOURCE_FIELDS:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("FORBIDDEN_SOURCE_FIELD_PIN_DRIFT")
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


def _build_pin() -> dict[str, str]:
    reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1(
        claimed_proof="DURABLE_UNKNOWN_NOT_D6_CLOSEOUT",
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    )
    reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1(
        claimed_proof="REMAIN_UNKNOWN_NO_CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASS",
        fact_id="F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
    )
    return {
        "layer": "ADJUDICATED",
        "f12_decision": DECISION_REMAIN_UNKNOWN,
        "f13_decision": DECISION_REMAIN_UNKNOWN,
        "u05_kind_decision": DECISION_REMAIN_UNKNOWN,
        "f16_decision": DECISION_REMAIN_UNKNOWN,
        "f17_decision": DECISION_REMAIN_UNKNOWN,
        "f18_decision": DECISION_REMAIN_UNKNOWN,
        "f12_status": STATUS_UNKNOWN,
        "f13_status": STATUS_UNKNOWN,
        "u05_status": STATUS_UNKNOWN,
        "f16_status": STATUS_UNKNOWN,
        "f17_status": STATUS_UNKNOWN,
        "f18_status": STATUS_UNKNOWN,
        "ratified_eq_identity": IDENTITY_NONE,
        "ratified_source_kinds": NONE_TOKEN,
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "eq_reconciliation_target_only": TRUE_TOKEN,
        "currently_decision_capable_evidence_classes_for_f12_f13": CURRENTLY_DECISION_CAPABLE,
        "unknown_is_durable_but_not_d6_closeout": TRUE_TOKEN,
        "include_from_unknown_forbidden": TRUE_TOKEN,
        "exclude_from_unknown_forbidden": TRUE_TOKEN,
        "further_read_only_slices_on_exhausted_classes_forbidden": TRUE_TOKEN,
        "d6_fully_closed": FALSE_TOKEN,
        "path_c_unknown_closeout": "REJECT",
        "semantic_salvage_rule_applied": TRUE_TOKEN,
        "legacy_structure_restored": FALSE_TOKEN,
    }


def _build_reopen_gates() -> dict[str, Any]:
    return {
        "layer": "ADJUDICATED",
        "gate_a_persisted": TRUE_TOKEN,
        "gate_a_executed": FALSE_TOKEN,
        "gate_b_persisted": TRUE_TOKEN,
        "gate_b_executed": FALSE_TOKEN,
        "this_workpackage_authorizes_gate_a_get": FALSE_TOKEN,
        "this_workpackage_authorizes_gate_b_binding": FALSE_TOKEN,
        "this_workpackage_performs_vendor_web_repo_archive_search": FALSE_TOKEN,
        "records": [
            {
                "gate_id": GATE_A_ID,
                "prerequisite": (
                    "INDEPENDENTLY_ATTESTED_GENUINE_PRODUCTIVE_NONZERO_LIABILITY_STOCK_"
                    "ON_BOUND_D4_ACCOUNT"
                ),
                "separate_owner_go_required": TRUE_TOKEN,
                "authorized_surface_if_later_go": SELECTED_BALANCE_SURFACE,
                "max_get_count_if_later_go": "1",
                "hope_get_forbidden": TRUE_TOKEN,
                "post_borrow_account_mutation_forbidden": TRUE_TOKEN,
                "get_alone_may_include": FALSE_TOKEN,
                "get_alone_may_exclude": FALSE_TOKEN,
                "nonzero_zero_empty_insufficient_without_source_semantics_and_embedding": (
                    TRUE_TOKEN
                ),
                "executed_this_go": FALSE_TOKEN,
                "outcome_domain_this_go": "NOT_EXECUTED",
            },
            {
                "gate_id": GATE_B_ID,
                "prerequisite": (
                    "NEWLY_BOUND_UNIQUE_EXTERNAL_EQ_COMPOSITION_AUTHORITY_NOT_EXHAUSTED_BY_BI"
                ),
                "separate_owner_go_required": TRUE_TOKEN,
                "no_uniqueness_means": DECISION_REMAIN_UNKNOWN,
                "vendor_web_repo_archive_search_this_go": "FORBIDDEN",
                "executed_this_go": FALSE_TOKEN,
                "outcome_domain_this_go": "NOT_EXECUTED",
            },
        ],
    }


def _build_exhausted_classes() -> dict[str, Any]:
    return {
        "layer": "ADJUDICATED",
        "currently_decision_capable_evidence_classes_for_f12_f13": CURRENTLY_DECISION_CAPABLE,
        "records": [
            {"class_id": class_id, "status": "EXHAUSTED_OR_FORBIDDEN"}
            for class_id in EXHAUSTED_OR_FORBIDDEN_CLASSES
        ],
    }


def execute_f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bi_pack: Path | str,
    sealed_bh_pack: Path | str,
    sealed_observation_pack: Path | str,
    sealed_s6_pack: Path | str,
    sealed_mapping_pack: Path | str,
    evidence_root: Path | str,
    pin_as_of: str,
) -> F12F13KindSetRemainingUnknownPinAndReopenGateResultV1:
    if owner_go != OWNER_GO:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    bi_pack = Path(sealed_bi_pack)
    bh_pack = Path(sealed_bh_pack)
    observation = Path(sealed_observation_pack)
    s6_pack = Path(sealed_s6_pack)
    mapping = Path(sealed_mapping_pack)
    verify_codes = {
        "BI": verify_manifest_sha256_v1(store_root=bi_pack),
        "BH": verify_manifest_sha256_v1(store_root=bh_pack),
        "S1_S5": verify_manifest_sha256_v1(store_root=observation),
        "S6": verify_manifest_sha256_v1(store_root=s6_pack),
        "MAPPING": verify_manifest_sha256_v1(store_root=mapping),
    }
    if any(code != 0 for code in verify_codes.values()):
        raise F12F13KindSetRemainingUnknownPinAndReopenGateError("MANIFEST_VERIFY_NOT_ZERO")
    bi_claims = _load_json_object(path=bi_pack / CLAIMS_FILE)
    _require_token(field="GENESIS_ID", payload=bi_claims, expected=EXPECTED_GENESIS_ID)
    _require_token(field="GENESIS_AS_OF", payload=bi_claims, expected=EXPECTED_GENESIS_AS_OF)
    _require_token(field="RATIFIED_EQ_IDENTITY", payload=bi_claims, expected=IDENTITY_NONE)
    _require_token(field="F12_DECISION", payload=bi_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F13_DECISION", payload=bi_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_KIND_DECISION", payload=bi_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F16_DECISION", payload=bi_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F17_DECISION", payload=bi_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F18_DECISION", payload=bi_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="RATIFIED_SOURCE_KINDS", payload=bi_claims, expected=NONE_TOKEN)
    _require_token(field="KIND_SET", payload=bi_claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=bi_claims, expected=FALSE_TOKEN)
    _require_token(field="RAW_EQ_SOURCE_AUTHORITY", payload=bi_claims, expected=FALSE_TOKEN)
    _require_token(field="EQ_RECONCILIATION_TARGET_ONLY", payload=bi_claims, expected=TRUE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bi_claims, expected="0")
    _require_token(field="POST_COUNT", payload=bi_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bi_claims, expected=FALSE_TOKEN)
    _require_token(field="D7_AUTHORIZED", payload=bi_claims, expected=FALSE_TOKEN)
    _require_token(field="MS2_AUTHORIZED", payload=bi_claims, expected=FALSE_TOKEN)
    _require_token(
        field="EARLIEST_REMAINING_D6_BLOCKER",
        payload=bi_claims,
        expected=BI_EARLIEST_REMAINING_D6_BLOCKER,
    )
    bh_claims = _load_json_object(path=bh_pack / CLAIMS_FILE)
    _require_token(field="GET_COUNT", payload=bh_claims, expected="1")
    _require_token(field="NONZERO_LIABILITY_OBSERVED", payload=bh_claims, expected=FALSE_TOKEN)
    pin = _build_pin()
    gates = _build_reopen_gates()
    exhausted = _build_exhausted_classes()
    ranked = [
        {
            "rank": "1",
            "blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "covers_facts": (
                "F12_LIABILITY_AFFECTS_EQUITY_STOCK,F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ,"
                "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND"
            ),
            "blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "role": "EARLIEST_REMAINING_D6_BLOCKER",
            "currently_decision_capable_evidence_classes": CURRENTLY_DECISION_CAPABLE,
            "parent_bi_blocker": BI_EARLIEST_REMAINING_D6_BLOCKER,
            "new_get_authorized": FALSE_TOKEN,
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
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
    folder = _folder_from_as_of(pin_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": "NONE",
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PIN_AS_OF": pin_as_of,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "SEALED_BI_PACK": CANONICAL_BI_PACK_RELPATH,
        "SEALED_BH_PACK": CANONICAL_BH_PACK_RELPATH,
        "SEALED_OBSERVATION_PACK": CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
        "SEALED_S6_PACK": CANONICAL_S6_PACK_RELPATH,
        "SEALED_MAPPING_PACK": CANONICAL_MAPPING_PACK_RELPATH,
        "MANIFESTS_VERIFY": TRUE_TOKEN,
        "VENUE_GET_COUNT": "0",
        "POST_COUNT": "0",
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "NEW_NETWORK_GET_COUNT": "0",
        "GATE_A_EXECUTED": FALSE_TOKEN,
        "GATE_B_EXECUTED": FALSE_TOKEN,
        "GATE_A_PERSISTED": TRUE_TOKEN,
        "GATE_B_PERSISTED": TRUE_TOKEN,
        "RATIFIED_EQ_IDENTITY": IDENTITY_NONE,
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
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "UNKNOWN_IS_DURABLE_BUT_NOT_D6_CLOSEOUT": TRUE_TOKEN,
        "INCLUDE_FROM_UNKNOWN_FORBIDDEN": TRUE_TOKEN,
        "EXCLUDE_FROM_UNKNOWN_FORBIDDEN": TRUE_TOKEN,
        "FURTHER_READ_ONLY_SLICES_ON_EXHAUSTED_CLASSES_FORBIDDEN": TRUE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": EARLIEST_REMAINING_D6_BLOCKER,
        "NARROWER_THAN_BI": TRUE_TOKEN,
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
        "PATH_A": "REJECT",
        "PATH_C": "REJECT",
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
        "BI_MANIFEST_VERIFY_RC": str(verify_codes["BI"]),
        "BH_MANIFEST_VERIFY_RC": str(verify_codes["BH"]),
        "S1_S5_MANIFEST_VERIFY_RC": str(verify_codes["S1_S5"]),
        "S6_MANIFEST_VERIFY_RC": str(verify_codes["S6"]),
        "MAPPING_MANIFEST_VERIFY_RC": str(verify_codes["MAPPING"]),
    }
    _persist_json(
        path=store / "layers_v1.json",
        payload={
            "CANONICAL_AUTHORITY": "remaining_unknown_pin_v1.json,reopen_gates_v1.json",
            "FORENSIC_RAW": "NONE_NEW_THIS_GO",
            "ADJUDICATED": (
                "remaining_unknown_pin_v1.json,reopen_gates_v1.json,"
                "exhausted_or_forbidden_evidence_classes_v1.json"
            ),
            "HISTORICAL": ",".join(
                [
                    CANONICAL_BI_PACK_RELPATH,
                    CANONICAL_BH_PACK_RELPATH,
                    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
                    CANONICAL_S6_PACK_RELPATH,
                    CANONICAL_MAPPING_PACK_RELPATH,
                ]
            ),
            "NAVIGATION": "NONE",
            "INTERPRETATION": "FORBIDDEN",
            "HYPOTHESIS": "FORBIDDEN",
            "UNRESOLVED": "ranked_remaining_d6_blockers_v1.json",
        },
    )
    _persist_json(path=store / "remaining_unknown_pin_v1.json", payload=pin)
    _persist_json(path=store / "reopen_gates_v1.json", payload=gates)
    _persist_json(
        path=store / "exhausted_or_forbidden_evidence_classes_v1.json",
        payload=exhausted,
    )
    _persist_json(
        path=store / "ranked_remaining_d6_blockers_v1.json",
        payload={
            "layer": "UNRESOLVED",
            "earliest_remaining_d6_blocker": EARLIEST_REMAINING_D6_BLOCKER,
            "kind_set_include_exclude_blocked_by": KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
            "currently_decision_capable_evidence_classes_for_f12_f13": CURRENTLY_DECISION_CAPABLE,
            "narrower_than_bi": TRUE_TOKEN,
            "records": ranked,
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "algebraic_inference": "FORBIDDEN",
            "new_network_get": "FORBIDDEN",
            "repeat_get_hoping_for_nonzero": "FORBIDDEN",
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "vendor_web_repo_archive_search": "FORBIDDEN",
            "raw_eq_source_authority": FALSE_TOKEN,
            "legacy_structure_restored": FALSE_TOKEN,
            "c01_c16_revived": FALSE_TOKEN,
            "path_a": "REJECT",
            "path_c": "REJECT",
            "ms2_authorized": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "classified_kind_set": KIND_SET_EMPTY,
            "further_read_only_slices_on_exhausted_classes": "FORBIDDEN",
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "layer": "HISTORICAL",
            "origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
            "owner_go": OWNER_GO,
            "genesis_id": EXPECTED_GENESIS_ID,
            "parent_bi": CANONICAL_BI_PACK_RELPATH,
            "parent_bh": CANONICAL_BH_PACK_RELPATH,
            "sealed_s1_s5": CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
            "sealed_s6": CANONICAL_S6_PACK_RELPATH,
            "pr_6452_mapping": CANONICAL_MAPPING_PACK_RELPATH,
            "legacy_structure_restored": FALSE_TOKEN,
        },
    )
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    manifest = persist_manifest_sha256_v1(store_root=store)
    return F12F13KindSetRemainingUnknownPinAndReopenGateResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        pin_as_of=pin_as_of,
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
        currently_decision_capable_evidence_classes=CURRENTLY_DECISION_CAPABLE,
        unknown_durable_not_closeout=TRUE_TOKEN,
        gate_a_persisted=TRUE_TOKEN,
        gate_a_executed=FALSE_TOKEN,
        gate_b_persisted=TRUE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
        venue_get_count="0",
        post_count="0",
        ms2_authorized=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        earliest_remaining_d6_blocker=EARLIEST_REMAINING_D6_BLOCKER,
        evidence_manifest=str(manifest),
    )
