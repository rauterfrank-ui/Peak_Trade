"""OPTION_D SSOT architecture and dimension-split contract.

Schema/contract only. Event acquisition is recorded as a typed D6
surface pin. Does not reconstruct equity. Does not mint C17. Does
not map venue `eq` to source authority. Does not bind STEP-29P.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED,
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    C17_CREATED,
    DIMENSION_AVAILABLE_FOR_SIZING,
    DIMENSION_EQUITY_STOCK,
    DIMENSION_MARGIN_REQUIREMENTS,
    DIMENSION_P01_RISK_CAPITAL_REDUCTION,
    EARLIEST_OPTION_D_DEPENDENCY,
    EQ_RECONCILIATION_TARGET_ONLY,
    EVENT_ACQUISITION_CREATED,
    GOVERNED_PRODUCER_CREATED,
    OPTION_D_SELECTED,
    P01_PLACEMENT,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESTART_PROVEN,
    SOURCE_SELECTED,
    U04_PLACEMENT,
    U05_PLACEMENT,
    U06_PLACEMENT,
)

SCHEMA_CLASS = "OPTION_D_SSOT_ARCHITECTURE_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
SELECTED_OPTION = "OPTION_D"
ARCHITECTURE_CLASS = (
    "GOVERNED_CHECKPOINT_PLUS_EVENT_SOURCED_EQUITY_STOCK_RECONSTRUCTION"
    "_RECONCILED_TO_FRESH_EQ_TARGET_V1"
)
OPTION_A_STATUS = "REJECTED_AS_LONG_TERM_TARGET"
OPTION_B_STATUS = "FORBIDDEN"
OPTION_C_STATUS = "FAIL_CLOSED_FALLBACK_ONLY"
DEPENDENCY_GRAPH: Tuple[str, ...] = (
    "D1_SSOT_OPTION_D_AND_DIMENSION_SPLIT",
    "D2_CHECKPOINT_CONTRACT_NO_EQUITY_MINT",
    "D3_EVENT_TAXONOMY_UNKNOWN_FAIL_CLOSED",
    "D4_BOUND_ACCOUNT_IDENTITY",
    "D5_CHECKPOINT_OBSERVATION_ACQUISITION",
    "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION",
    "D7_DETERMINISTIC_STOCK_RECONSTRUCTION",
    "D8_FRESH_EQ_RECONCILE_FAIL_CLOSED",
    "D9_RESTART_FROM_CHECKPOINT_PLUS_EVENTS_PLUS_TARGET",
    "D10_C17_CANDIDATE_IF_AND_ONLY_IF_D1_D9_PROVEN",
    "D11_OWNER_RATIFY_AND_MAPPING",
    "D12_AVAILABLE_FOR_SIZING_U04_LAYER",
    "D13_P01_AFTER_EQUITY",
    "D14_STEP29P_AND_ADMISSION_CLOSEOUT",
)
THIS_WP_COMPLETED_NODES: Tuple[str, ...] = (
    "D1_SSOT_OPTION_D_AND_DIMENSION_SPLIT",
    "D2_CHECKPOINT_CONTRACT_NO_EQUITY_MINT",
    "D3_EVENT_TAXONOMY_UNKNOWN_FAIL_CLOSED",
    "D4_BOUND_ACCOUNT_IDENTITY",
    "D5_CHECKPOINT_OBSERVATION_ACQUISITION",
)
THIS_WP_CONTRACT_ONLY_PARTIAL_NODES: Tuple[str, ...] = ("D8_FRESH_EQ_RECONCILE_FAIL_CLOSED",)
UNRESOLVED_DEPENDENCY_NODES: Tuple[str, ...] = (
    "D6_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION",
    "D7_DETERMINISTIC_STOCK_RECONSTRUCTION",
    "D8_FRESH_EQ_RECONCILE_FAIL_CLOSED",
    "D9_RESTART_FROM_CHECKPOINT_PLUS_EVENTS_PLUS_TARGET",
    "D10_C17_CANDIDATE_IF_AND_ONLY_IF_D1_D9_PROVEN",
    "D11_OWNER_RATIFY_AND_MAPPING",
    "D12_AVAILABLE_FOR_SIZING_U04_LAYER",
    "D13_P01_AFTER_EQUITY",
    "D14_STEP29P_AND_ADMISSION_CLOSEOUT",
)
REQUIRED_FIELDS: Tuple[str, ...] = (
    "architecture_contract_id",
    "selected_option",
    "architecture_class",
    "authority_owner",
    "equity_stock_dimension_id",
    "available_for_sizing_dimension_id",
    "margin_requirements_dimension_id",
    "p01_dimension_id",
    "raw_eq_source_authority",
    "eq_reconciliation_target_only",
    "c17_created",
    "mapping_proven",
    "event_acquisition_created",
    "reconstruction_engine_created",
    "restart_proven",
    "earliest_option_d_dependency",
)
FORBIDDEN_SOURCE_FIELDS: Tuple[str, ...] = (
    "eq",
    "totalEq",
    "availEq",
    "adjEq",
    "availBal",
    "cashBal",
)
_TRUE = "true"
_FALSE = "false"


class OptionDSSOTArchitectureContractError(ValueError):
    """Fail-closed OPTION_D architecture/dimension-split contract violation."""


@dataclass(frozen=True)
class OptionDSSOTArchitectureContractV1:
    architecture_contract_id: str
    selected_option: str
    architecture_class: str
    authority_owner: str
    equity_stock_dimension_id: str
    available_for_sizing_dimension_id: str
    margin_requirements_dimension_id: str
    p01_dimension_id: str
    u04_placement: str
    u05_placement: str
    u06_placement: str
    p01_placement: str
    raw_eq_source_authority: str
    eq_reconciliation_target_only: str
    c17_created: str
    mapping_proven: str
    event_acquisition_created: str
    reconstruction_engine_created: str
    restart_proven: str
    earliest_option_d_dependency: str
    authority_effect: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise OptionDSSOTArchitectureContractError(f"ARCHITECTURE_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise OptionDSSOTArchitectureContractError(f"ARCHITECTURE_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise OptionDSSOTArchitectureContractError(f"ARCHITECTURE_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_option_d_architecture_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def assert_dimension_split_v1(
    *,
    equity_stock_dimension_id: str,
    available_for_sizing_dimension_id: str,
    margin_requirements_dimension_id: str,
    p01_dimension_id: str,
) -> None:
    ids = (
        equity_stock_dimension_id,
        available_for_sizing_dimension_id,
        margin_requirements_dimension_id,
        p01_dimension_id,
    )
    if any(item.strip() == "" for item in ids):
        raise OptionDSSOTArchitectureContractError("DIMENSION_ID_MISSING")
    if len(set(ids)) != 4:
        raise OptionDSSOTArchitectureContractError("DIMENSION_SPLIT_COLLAPSED")
    if equity_stock_dimension_id != DIMENSION_EQUITY_STOCK:
        raise OptionDSSOTArchitectureContractError("EQUITY_STOCK_DIMENSION_MISMATCH")
    if available_for_sizing_dimension_id != DIMENSION_AVAILABLE_FOR_SIZING:
        raise OptionDSSOTArchitectureContractError("AVAILABLE_FOR_SIZING_DIMENSION_MISMATCH")
    if margin_requirements_dimension_id != DIMENSION_MARGIN_REQUIREMENTS:
        raise OptionDSSOTArchitectureContractError("MARGIN_REQUIREMENTS_DIMENSION_MISMATCH")
    if p01_dimension_id != DIMENSION_P01_RISK_CAPITAL_REDUCTION:
        raise OptionDSSOTArchitectureContractError("P01_DIMENSION_MISMATCH")


def build_option_d_ssot_architecture_contract_v1(
    *,
    architecture_contract_id: str,
) -> OptionDSSOTArchitectureContractV1:
    contract_id = _require_non_empty_str(
        field="architecture_contract_id", raw=architecture_contract_id
    )
    if OPTION_D_SELECTED is not True:
        raise OptionDSSOTArchitectureContractError("OPTION_D_NOT_SELECTED")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise OptionDSSOTArchitectureContractError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise OptionDSSOTArchitectureContractError("EQ_RECONCILIATION_TARGET_ONLY_NOT_TRUE")
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise OptionDSSOTArchitectureContractError("AUTHORITY_OWNER_MUTATED")
    if C17_CREATED is not False:
        raise OptionDSSOTArchitectureContractError("C17_CREATED_NOT_FALSE")
    if CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is True:
        raise OptionDSSOTArchitectureContractError("MAPPING_CLOSURE_CONSUMED_REEXECUTE_FORBIDDEN")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise OptionDSSOTArchitectureContractError("MAPPING_PROVEN_NOT_FALSE")
    if SOURCE_SELECTED is not False:
        raise OptionDSSOTArchitectureContractError("SOURCE_SELECTED_NOT_FALSE")
    if GOVERNED_PRODUCER_CREATED is not False:
        raise OptionDSSOTArchitectureContractError("GOVERNED_PRODUCER_CREATED_NOT_FALSE")
    if EVENT_ACQUISITION_CREATED is not True:
        raise OptionDSSOTArchitectureContractError("EVENT_ACQUISITION_CREATED_NOT_TRUE")
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise OptionDSSOTArchitectureContractError("RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE")
    if RESTART_PROVEN is not False:
        raise OptionDSSOTArchitectureContractError("RESTART_PROVEN_NOT_FALSE")
    assert_dimension_split_v1(
        equity_stock_dimension_id=DIMENSION_EQUITY_STOCK,
        available_for_sizing_dimension_id=DIMENSION_AVAILABLE_FOR_SIZING,
        margin_requirements_dimension_id=DIMENSION_MARGIN_REQUIREMENTS,
        p01_dimension_id=DIMENSION_P01_RISK_CAPITAL_REDUCTION,
    )
    payload = {
        "architecture_contract_id": contract_id,
        "selected_option": SELECTED_OPTION,
        "architecture_class": ARCHITECTURE_CLASS,
        "authority_owner": ACCOUNT_EQUITY_AUTHORITY_OWNER,
        "equity_stock_dimension_id": DIMENSION_EQUITY_STOCK,
        "available_for_sizing_dimension_id": DIMENSION_AVAILABLE_FOR_SIZING,
        "margin_requirements_dimension_id": DIMENSION_MARGIN_REQUIREMENTS,
        "p01_dimension_id": DIMENSION_P01_RISK_CAPITAL_REDUCTION,
        "u04_placement": U04_PLACEMENT,
        "u05_placement": U05_PLACEMENT,
        "u06_placement": U06_PLACEMENT,
        "p01_placement": P01_PLACEMENT,
        "raw_eq_source_authority": _FALSE,
        "eq_reconciliation_target_only": _TRUE,
        "c17_created": _FALSE,
        "mapping_proven": _FALSE,
        "event_acquisition_created": _TRUE,
        "reconstruction_engine_created": _FALSE,
        "restart_proven": _FALSE,
        "earliest_option_d_dependency": EARLIEST_OPTION_D_DEPENDENCY,
        "authority_effect": AUTHORITY_EFFECT,
        "option_a_status": OPTION_A_STATUS,
        "option_b_status": OPTION_B_STATUS,
        "option_c_status": OPTION_C_STATUS,
        "dependency_graph": ",".join(DEPENDENCY_GRAPH),
        "this_wp_completed_nodes": ",".join(THIS_WP_COMPLETED_NODES),
        "unresolved_dependency_nodes": ",".join(UNRESOLVED_DEPENDENCY_NODES),
    }
    digest = compute_option_d_architecture_digest_v1(payload)
    return OptionDSSOTArchitectureContractV1(
        architecture_contract_id=contract_id,
        selected_option=SELECTED_OPTION,
        architecture_class=ARCHITECTURE_CLASS,
        authority_owner=ACCOUNT_EQUITY_AUTHORITY_OWNER,
        equity_stock_dimension_id=DIMENSION_EQUITY_STOCK,
        available_for_sizing_dimension_id=DIMENSION_AVAILABLE_FOR_SIZING,
        margin_requirements_dimension_id=DIMENSION_MARGIN_REQUIREMENTS,
        p01_dimension_id=DIMENSION_P01_RISK_CAPITAL_REDUCTION,
        u04_placement=U04_PLACEMENT,
        u05_placement=U05_PLACEMENT,
        u06_placement=U06_PLACEMENT,
        p01_placement=P01_PLACEMENT,
        raw_eq_source_authority=_FALSE,
        eq_reconciliation_target_only=_TRUE,
        c17_created=_FALSE,
        mapping_proven=_FALSE,
        event_acquisition_created=_TRUE,
        reconstruction_engine_created=_FALSE,
        restart_proven=_FALSE,
        earliest_option_d_dependency=EARLIEST_OPTION_D_DEPENDENCY,
        authority_effect=AUTHORITY_EFFECT,
        provenance_digest=digest,
    )
