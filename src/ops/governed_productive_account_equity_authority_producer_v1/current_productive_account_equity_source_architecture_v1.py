"""Ratify current-productive account-equity source architecture v1.

Consumes Owner-GO DESIGN_AND_RATIFY_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE_V1.
Supersedes the CQ-named historical-artifact GO by retiring the sealed
legacy reconstruction path from the live-critical path. Does not reopen
the sealed census. Does not reconstruct historical INCLUDE/EXCLUDE.
Does not treat venue eq as source. Does not mint AVAILABLE_FOR_SIZING.
Does not GET. Does not POST. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
    CURRENT_PRODUCTIVE_ARCHITECTURE_IS_NOT_HISTORICAL_RECONSTRUCTION,
    CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
    CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    EQ_RECONCILIATION_TARGET_ONLY,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    GOVERNED_PRODUCER_CREATED,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    PRIMARY_PROOF_SURFACE,
    PRIMARY_PROOF_SURFACE_BOUND_THIS_WORKPACKAGE,
    PRIMARY_PROOF_SURFACE_STATUS,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEALED_LEGACY_CENSUS_REOPENED,
    SOURCE_KIND_COMPLETENESS_STATUS,
    SOURCE_SELECTED,
    STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER,
    U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE,
    U04_LEGACY_STATUS,
    U04_PLACEMENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.non_eq_equity_stock_source_kind_or_completeness_v1 import (
    reject_kind_set_uplift_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.non_eq_equity_stock_source_kind_primary_proof_surface_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CQ_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.remaining_necessary_kind_evidence_classification_v1 import (
    reject_u04_reclassify_as_equity_stock_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    reject_eq_as_source_authority_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = "OWNER_GO_DESIGN_AND_RATIFY_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE_V1"
EXPECTED_ORIGIN_MAIN_SHA = "9b156d219ccd01ca71f8470ea2d66bcb0265aa48"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_account_equity_source_architecture_v1/"
    "2026-09-15T120000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T12:00:00Z"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
STATE_UNRESOLVED = "UNRESOLVED"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
LAYER_ACCOUNT_EQUITY_STOCK = "ACCOUNT_EQUITY_STOCK"
LAYER_RECONCILIATION_TARGET = "RECONCILIATION_TARGET"
LAYER_AVAILABLE_FOR_SIZING = "AVAILABLE_FOR_SIZING"
LAYER_LEGACY_RECONSTRUCTION = "LEGACY_SEALED_UNKNOWN"
CONSUMER_STEP_29P = "STEP_29P_CAPITAL_RISK_ADMISSIBILITY"
PRODUCER_SLOT = "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER"
SAMPLE_SCHEMA = "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1"
FORBIDDEN_AUTHORITY_FIELDS = (
    "availEq",
    "totalEq",
    "eq",
    "adjEq",
    "availBal",
    "cashBal",
)
EXACT_MISSING_PREDICATE = (
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND_AFTER_ARCHITECTURE_"
    "RATIFICATION_STOCK_NOT_29P_INPUT_EQ_RECONCILIATION_TARGET_ONLY_U04_SIZING_"
    "RESERVATION_LEGACY_KIND_SET_NOT_ON_LIVE_CRITICAL_PATH"
)
BLOCKER_ID = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND_AFTER_ARCHITECTURE_RATIFIED"
ARCHITECTURE_BLOCKER = (
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND_EQ_REMAINS_"
    "RECONCILIATION_TARGET_STOCK_NOT_29P_SIZING_INPUT_LEGACY_CENSUS_SEALED"
)
NEXT_PRODUCTIVE_NODE = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SELECT_OR_BIND_A_CURRENT_PRODUCTIVE_AVAILABLE_FOR_"
    "SIZING_SOURCE_NOT_EQ_NOT_LEGACY_KIND_SET_AND_NOT_FORBIDDEN_VENUE_FIELD_V1"
)
NEXT_ACTION = (
    "STOP_CURRENT_LIVE_CRITICAL_BLOCKER_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND_"
    "NO_LEGACY_RECONSTRUCTION_NO_GET"
)
PIN_OWNER_GO_STATUS = (
    "SUPERSEDED_BY_CURRENT_PRODUCTIVE_ARCHITECTURE_LEGACY_ARTIFACT_PATH_"
    "RETIRED_FROM_LIVE_CRITICAL_PATH"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveAccountEquitySourceArchitectureError(ValueError):
    """Fail-closed current-productive account-equity architecture violation."""


@dataclass(frozen=True)
class CurrentProductiveAccountEquitySourceArchitectureResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    architecture_ratified: str
    current_productive_model: str
    available_for_sizing_source_status: str
    equity_stock_source_status: str
    reconciliation_target: str
    u04_role: str
    restart_reconstruction_status: str
    current_live_critical_blocker: str
    first_definitive_block: str
    exact_missing_predicate: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveAccountEquitySourceArchitectureError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def reject_equity_stock_as_29p_sizing_input_v1(*, claimed: str) -> None:
    if claimed in {
        "true",
        "TRUE",
        "STEP_29P_SIZING_INPUT",
        LAYER_ACCOUNT_EQUITY_STOCK,
        "RUNNING_ACCOUNT_EQUITY_STOCK",
    }:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            f"ACCOUNT_EQUITY_STOCK_IS_NOT_29P_SIZING_INPUT:{claimed}"
        )


def reject_available_for_sizing_mint_without_source_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "MINTED", "AUTHORITY", "SELECTED", "BOUND"}:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            f"AVAILABLE_FOR_SIZING_MINT_FORBIDDEN_UNTIL_SOURCE_BOUND:{claimed}"
        )


def reject_layer_mix_stock_and_sizing_v1(*, claimed: str) -> None:
    if claimed in {
        "true",
        "MIXED",
        "EQUITY_STOCK_EQUALS_AVAILABLE_FOR_SIZING",
        "SAME_LAYER",
    }:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            f"EQUITY_STOCK_AND_AVAILABLE_FOR_SIZING_MUST_REMAIN_DISTINCT:{claimed}"
        )


def reject_legacy_reconstruction_as_live_requirement_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "REQUIRED_FOR_LIVE", "KIND_SET_ON_LIVE_CRITICAL_PATH"}:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            f"LEGACY_RECONSTRUCTION_IS_NOT_REQUIRED_FOR_LIVE:{claimed}"
        )


def reject_eq_authority_uplift_v1(*, claimed: str) -> None:
    reject_eq_as_source_authority_v1(claimed=claimed)
    if claimed in {"AUTHORITY_UPLIFT", "SIZING_SOURCE", "EQUITY_STOCK_SOURCE"}:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            f"EQ_AUTHORITY_UPLIFT_FORBIDDEN:{claimed}"
        )


def classify_current_productive_consumer_graph_v1() -> dict[str, Any]:
    """CURRENT_PRODUCTIVE_DESIGN of today's 29P/pre-wire consumer requirement."""

    rows = (
        {
            "consumer_id": CONSUMER_STEP_29P,
            "authority": STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
            "required_dimension": RISK_EQUITY_DIMENSION,
            "layer": LAYER_AVAILABLE_FOR_SIZING,
            "required_for_risk_admissible": TRUE_TOKEN,
            "consumes_account_equity_stock": FALSE_TOKEN,
            "consumes_venue_eq_as_source": FALSE_TOKEN,
            "u04_role": PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
            "binding_status": CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
        },
        {
            "consumer_id": "RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE",
            "authority": "RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1",
            "required_dimension": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
            "layer": LAYER_AVAILABLE_FOR_SIZING,
            "required_for_risk_admissible": TRUE_TOKEN,
            "consumes_account_equity_stock": FALSE_TOKEN,
            "consumes_venue_eq_as_source": FALSE_TOKEN,
            "u04_role": PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
            "binding_status": CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
        },
    )
    return {
        "epistemic_class": "CURRENT_PRODUCTIVE_DESIGN",
        "live_critical_consumer": CONSUMER_STEP_29P,
        "required_dimension": RISK_EQUITY_DIMENSION,
        "account_equity_stock_required_for_29p": FALSE_TOKEN,
        "legacy_kind_set_required_for_29p": FALSE_TOKEN,
        "consumer_count": str(len(rows)),
        "consumers": list(rows),
    }


def classify_current_productive_layers_v1() -> dict[str, Any]:
    return {
        "epistemic_class": "CURRENT_PRODUCTIVE_DESIGN",
        "model_version": CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        "architecture_ratified": TRUE_TOKEN,
        "is_historical_reconstruction": FALSE_TOKEN,
        "layers": {
            LAYER_ACCOUNT_EQUITY_STOCK: {
                "role": CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
                "source_status": CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
                "required_for_29p_sizing": FALSE_TOKEN,
                "legacy_kind_set_membership": "NOT_REQUIRED_FOR_LIVE",
            },
            LAYER_RECONCILIATION_TARGET: {
                "role": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
                "object": "eq",
                "authority_uplift": FALSE_TOKEN,
                "forbidden_as_sizing_source": TRUE_TOKEN,
            },
            LAYER_AVAILABLE_FOR_SIZING: {
                "dimension": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
                "source_status": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
                "producer_slot": PRODUCER_SLOT,
                "sample_schema": SAMPLE_SCHEMA,
                "producer_mint_authorized": FALSE_TOKEN,
                "u04_role": PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
                "required_for_29p_sizing": TRUE_TOKEN,
            },
            LAYER_LEGACY_RECONSTRUCTION: {
                "status": "SEALED_UNKNOWN_PRESERVED",
                "census_reopened": FALSE_TOKEN,
                "required_for_live": FALSE_TOKEN,
                "kind_set": KIND_SET_EMPTY,
                "ratified_source_kinds": NONE_TOKEN,
            },
        },
    }


def classify_reconciliation_and_restart_v1() -> dict[str, Any]:
    return {
        "epistemic_class": "CURRENT_PRODUCTIVE_DESIGN",
        "reconciliation_target": "eq",
        "reconciliation_target_role": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        "compare_eq_to_equity_stock_when_both_present": TRUE_TOKEN,
        "missing_stock_does_not_admit_29p_sizing": TRUE_TOKEN,
        "missing_available_for_sizing_fails_29p": TRUE_TOKEN,
        "divergence_does_not_mint_sizing": TRUE_TOKEN,
        "restart_reconstruction_status": CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
        "restart_source": "GOVERNED_CURRENT_PRODUCTIVE_PRODUCER_NOT_LEGACY_KIND_SET",
        "forbidden_authority_fields": ",".join(FORBIDDEN_AUTHORITY_FIELDS),
    }


def _assert_standing_pins() -> None:
    if WIRE_SEND_PERMITTED is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED is not True:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "CURRENT_PRODUCTIVE_ARCHITECTURE_NOT_RATIFIED"
        )
    if CURRENT_PRODUCTIVE_ARCHITECTURE_IS_NOT_HISTORICAL_RECONSTRUCTION is not True:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "ARCHITECTURE_MUST_NOT_BE_HISTORICAL_RECONSTRUCTION"
        )
    if LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "LEGACY_RECONSTRUCTION_MUST_NOT_BE_REQUIRED_FOR_LIVE"
        )
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED"
        )
    if CURRENT_PRODUCTIVE_SOURCE_SELECTED is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "CURRENT_PRODUCTIVE_SOURCE_MUST_REMAIN_UNSELECTED"
        )
    if CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "PRODUCER_MINT_MUST_REMAIN_UNAUTHORIZED"
        )
    if GOVERNED_PRODUCER_CREATED is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "GOVERNED_PRODUCER_MUST_REMAIN_ABSENT"
        )
    if SOURCE_SELECTED is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("SOURCE_SELECTED_MUST_BE_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("RAW_EQ_SOURCE_AUTHORITY_TRUE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "EQ_MUST_REMAIN_RECONCILIATION_TARGET_ONLY"
        )
    if EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("EQ_TREATED_AS_SOURCE")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("MAPPING_PROVEN_TRUE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "ALGEBRA_MUST_REMAIN_INCOMPLETE"
        )
    if KIND_SET_RESOLVED is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("KIND_SET_RESOLVED_TRUE")
    if KIND_SET_UPLIFT_THIS_WORKPACKAGE is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("KIND_SET_UPLIFT_FORBIDDEN")
    if PRIMARY_PROOF_SURFACE_BOUND_THIS_WORKPACKAGE is not False:
        raise CurrentProductiveAccountEquitySourceArchitectureError("PRIMARY_PROOF_SURFACE_BOUND")
    if PRIMARY_PROOF_SURFACE_STATUS != "NONE_IN_EXISTING_REPO_HISTORICAL_FORENSIC_EVIDENCE":
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "PRIMARY_PROOF_SURFACE_STATUS_DRIFT"
        )
    if PRIMARY_PROOF_SURFACE != NONE_TOKEN:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "PRIMARY_PROOF_SURFACE_NOT_NONE"
        )
    if SOURCE_KIND_COMPLETENESS_STATUS != "INSUFFICIENT_UNPROVEN":
        raise CurrentProductiveAccountEquitySourceArchitectureError("COMPLETENESS_DRIFT")
    if U04_LEGACY_STATUS != STATE_UNRESOLVED:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "LEGACY_U04_UNRESOLVED_PRESERVED"
        )
    if U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE != STATE_UNRESOLVED:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "U04_INCLUSION_MUST_REMAIN_UNRESOLVED"
        )
    if PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP != "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET":
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "PRODUCTIVE_U04_MEMBERSHIP_DRIFT"
        )
    if PRODUCTIVE_U04_EQUITY_STOCK_ROLE != DISPOSITION_NOT_EQUITY_STOCK:
        raise CurrentProductiveAccountEquitySourceArchitectureError("U04_STOCK_ROLE_DRIFT")
    if PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise CurrentProductiveAccountEquitySourceArchitectureError("U04_SIZING_ROLE_DRIFT")
    if U04_PLACEMENT != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise CurrentProductiveAccountEquitySourceArchitectureError("U04_PLACEMENT_DRIFT")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAccountEquitySourceArchitectureError("U05_UNKNOWN_PRESERVED")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAccountEquitySourceArchitectureError("U06_UNKNOWN_PRESERVED")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAccountEquitySourceArchitectureError("RESIDUAL_UNKNOWN_PRESERVED")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION != RISK_EQUITY_DIMENSION:
        raise CurrentProductiveAccountEquitySourceArchitectureError("SIZING_DIMENSION_DRIFT")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS != "UNBOUND":
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "SIZING_SOURCE_MUST_REMAIN_UNBOUND"
        )
    if CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS != "UNBOUND":
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "STOCK_SOURCE_MUST_REMAIN_UNBOUND"
        )
    if CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY != (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND"
    ):
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "LIVE_CRITICAL_DEPENDENCY_DRIFT"
        )
    if STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER is not True:
        raise CurrentProductiveAccountEquitySourceArchitectureError("STEP_29P_MUST_REMAIN_CONSUMER")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise CurrentProductiveAccountEquitySourceArchitectureError("LEGACY_DAG_PIN_DRIFT")
    reject_eq_authority_uplift_v1(claimed=FALSE_TOKEN)
    reject_kind_set_uplift_v1(claimed=FALSE_TOKEN)
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_equity_stock_as_29p_sizing_input_v1(claimed=FALSE_TOKEN)
    reject_available_for_sizing_mint_without_source_v1(claimed=FALSE_TOKEN)
    reject_layer_mix_stock_and_sizing_v1(claimed=FALSE_TOKEN)
    reject_legacy_reconstruction_as_live_requirement_v1(claimed=FALSE_TOKEN)


def _assert_parent_cq_pack_sealed(*, repo_root: Path) -> None:
    pack = repo_root / CANONICAL_CQ_PACK_RELPATH
    claims_path = pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise CurrentProductiveAccountEquitySourceArchitectureError("PARENT_CQ_PACK_MISSING")
    claims = _load_json_object(path=claims_path)
    if claims.get("PRIMARY_PROOF_SURFACE") != NONE_TOKEN:
        raise CurrentProductiveAccountEquitySourceArchitectureError("PARENT_CQ_SURFACE_DRIFT")
    if claims.get("RATIFIED_SOURCE_KINDS") != NONE_TOKEN:
        raise CurrentProductiveAccountEquitySourceArchitectureError("PARENT_CQ_KIND_DRIFT")
    if claims.get("SOURCE_KIND_COMPLETENESS_STATUS") != "INSUFFICIENT_UNPROVEN":
        raise CurrentProductiveAccountEquitySourceArchitectureError("PARENT_CQ_COMPLETENESS_DRIFT")
    if claims.get("DURABLE_UNKNOWN_REOPENED") != FALSE_TOKEN:
        raise CurrentProductiveAccountEquitySourceArchitectureError("PARENT_CQ_UNKNOWN_REOPENED")
    if verify_manifest_sha256_v1(store_root=pack) != 0:
        raise CurrentProductiveAccountEquitySourceArchitectureError(
            "PARENT_CQ_MANIFEST_VERIFY_NOT_ZERO"
        )


def execute_current_productive_account_equity_source_architecture_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    persist_as_of: str = CANONICAL_PERSIST_AS_OF,
    repo_root: Path | str | None = None,
) -> CurrentProductiveAccountEquitySourceArchitectureResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveAccountEquitySourceArchitectureError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveAccountEquitySourceArchitectureError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    _assert_parent_cq_pack_sealed(repo_root=root)
    as_of = str(persist_as_of or "").strip()
    if as_of == "":
        raise CurrentProductiveAccountEquitySourceArchitectureError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    consumers = classify_current_productive_consumer_graph_v1()
    layers = classify_current_productive_layers_v1()
    reconciliation = classify_reconciliation_and_restart_v1()
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": PIN_OWNER_GO_STATUS,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CQ_PACK": CANONICAL_CQ_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "EPISTEMIC_CLASS": "CURRENT_PRODUCTIVE_DESIGN",
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CR",
        "LEGACY_SEALED_UNKNOWN": "CQ_PRIMARY_PROOF_SURFACE_ABSENCE_AND_KIND_SET_EMPTY",
        "FORENSIC_EVIDENCE": "SEALED_CQ_PACK_PLUS_CURRENT_29P_CONSUMER_CODE",
        "ADJUDICATED": "CURRENT_PRODUCTIVE_FOUR_LAYER_MODEL_RATIFIED_SOURCE_UNBOUND",
        "INTERPRETATION": "FORBIDDEN_AS_SOURCE",
        "HYPOTHESIS": "FORBIDDEN_AS_SOURCE",
        "UNRESOLVED": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "START_BLOCK": DAG_PIN,
        "LEGACY_SEALED_FULL_CORE_DAG_PIN": DAG_PIN,
        "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE": FALSE_TOKEN,
        "SEALED_LEGACY_CENSUS_REOPENED": FALSE_TOKEN,
        "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL": CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        "CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED": TRUE_TOKEN,
        "CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE": CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
        "CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE": CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
        "CURRENT_PRODUCTIVE_EQUITY_SOURCE": "UNBOUND_AVAILABLE_FOR_SIZING_SOURCE",
        "RECONCILIATION_TARGET": "eq",
        "RECONCILIATION_TARGET_STATUS": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        "AVAILABLE_FOR_SIZING_MODEL": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
        "AVAILABLE_FOR_SIZING_SOURCE_STATUS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
        "U04_ROLE": PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
        "U04_EQUITY_STOCK_ROLE": DISPOSITION_NOT_EQUITY_STOCK,
        "U04_LEGACY_STATUS": STATE_UNRESOLVED,
        "U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE": STATE_UNRESOLVED,
        "U05_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_REOPENED": FALSE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_UPLIFT_THIS_WORKPACKAGE": FALSE_TOKEN,
        "EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE": FALSE_TOKEN,
        "AUTHORITY_UPLIFT": FALSE_TOKEN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAPPING_PROVEN": FALSE_TOKEN,
        "SOURCE_SELECTED": FALSE_TOKEN,
        "GOVERNED_PRODUCER_CREATED": FALSE_TOKEN,
        "PRODUCER_MINT_AUTHORIZED": FALSE_TOKEN,
        "STEP_29P_CONSUMER_BINDING_STATUS": CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
        "STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER": TRUE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
        "RESTART_RECONSTRUCTION_STATUS": CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
        "STEP_29P_BINDING_STATUS": "CONSUMER_BOUND_SOURCE_UNBOUND",
        "CURRENT_LIVE_CRITICAL_BLOCKER": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "LIVE_CRITICAL_PATH_FOLLOWS": "CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY",
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "FIRST_DEFINITIVE_BLOCK": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "EXACT_MISSING_PREDICATE": EXACT_MISSING_PREDICATE,
        "NO_GET_REQUIRED": TRUE_TOKEN,
        "NO_HOPE_GET": TRUE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "VENUE_GET_COUNT": "0",
        "POST_COUNT": "0",
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "LIVE_ENABLED": FALSE_TOKEN,
        "LIVE_ARMED": FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": FALSE_TOKEN,
        "LOCAL_ADVANCEMENT_EXHAUSTED": TRUE_TOKEN,
        "PARENT_BLOCKER_ID": PARENT_BLOCKER_ID,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
    }
    lineage = {
        "layer": "CURRENT_PRODUCTIVE_DESIGN",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "pin_owner_go": PIN_OWNER_GO,
        "pin_owner_go_status": PIN_OWNER_GO_STATUS,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cq_pack": CANONICAL_CQ_PACK_RELPATH,
        "sealed_legacy_census_reopened": FALSE_TOKEN,
        "historical_artifacts_rewritten": FALSE_TOKEN,
        "legacy_reconstruction_required_for_live": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "source_selected": FALSE_TOKEN,
        "producer_minted": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_consumer_semantics_unchanged": TRUE_TOKEN,
        "trading_logic_unchanged": TRUE_TOKEN,
        "trading_signal_authority_unchanged": TRUE_TOKEN,
        "u04_not_reclassified_as_equity_stock_kind": TRUE_TOKEN,
        "legacy_u04_unresolved_preserved": TRUE_TOKEN,
        "legacy_u05_unknown_preserved": TRUE_TOKEN,
        "legacy_u06_unknown_preserved": TRUE_TOKEN,
        "legacy_residual_unknown_preserved": TRUE_TOKEN,
        "eq_not_elevated_to_source": TRUE_TOKEN,
        "kind_set_not_uplifted": TRUE_TOKEN,
        "sealed_legacy_census_not_reopened": TRUE_TOKEN,
        "single_selected_future_unchanged": TRUE_TOKEN,
        "max_positions_one_unchanged": TRUE_TOKEN,
        "treasury_untouched": TRUE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "legacy_dag_pin": DAG_PIN,
    }
    architecture = {
        "layer": "CURRENT_CANONICAL_AUTHORITY",
        "model_version": CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        "architecture_ratified": TRUE_TOKEN,
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "current_live_critical_blocker": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "legacy_sealed_dag_pin": DAG_PIN,
        "source_selected": FALSE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
        "atlas_authority": NONE_TOKEN,
    }
    epistemic = {
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CR",
        "CURRENT_PRODUCTIVE_DESIGN": SCHEMA_CLASS,
        "LEGACY_SEALED_UNKNOWN": "CQ_KIND_SET_EMPTY_AND_RATIFIED_SOURCE_KINDS_NONE",
        "FORENSIC_EVIDENCE": "SEALED_CQ_PACK_PLUS_STEP_29P_CONSUMER_CODE",
        "ADJUDICATED": "FOUR_LAYER_CURRENT_PRODUCTIVE_MODEL",
        "INTERPRETATION": "FORBIDDEN_AS_SOURCE",
        "HYPOTHESIS": "FORBIDDEN_AS_SOURCE",
        "UNRESOLVED": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "consumer_graph_v1.json", payload=consumers)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "reconciliation_and_restart_v1.json", payload=reconciliation)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "epistemic_separation_v1.json", payload=epistemic)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise CurrentProductiveAccountEquitySourceArchitectureError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise CurrentProductiveAccountEquitySourceArchitectureError("MANIFEST_VERIFY_NOT_ZERO")
    return CurrentProductiveAccountEquitySourceArchitectureResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        architecture_ratified=TRUE_TOKEN,
        current_productive_model=CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        available_for_sizing_source_status=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
        equity_stock_source_status=CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
        reconciliation_target=CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        u04_role=PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
        restart_reconstruction_status=CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
        current_live_critical_blocker=CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        first_definitive_block=CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        exact_missing_predicate=EXACT_MISSING_PREDICATE,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


__all__ = (
    "ARCHITECTURE_BLOCKER",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "CurrentProductiveAccountEquitySourceArchitectureError",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "FORBIDDEN_AUTHORITY_FIELDS",
    "LAYER_ACCOUNT_EQUITY_STOCK",
    "LAYER_AVAILABLE_FOR_SIZING",
    "LAYER_LEGACY_RECONSTRUCTION",
    "LAYER_RECONCILIATION_TARGET",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "PIN_OWNER_GO_STATUS",
    "classify_current_productive_consumer_graph_v1",
    "classify_current_productive_layers_v1",
    "classify_reconciliation_and_restart_v1",
    "execute_current_productive_account_equity_source_architecture_v1",
    "reject_available_for_sizing_mint_without_source_v1",
    "reject_eq_authority_uplift_v1",
    "reject_equity_stock_as_29p_sizing_input_v1",
    "reject_layer_mix_stock_and_sizing_v1",
    "reject_legacy_reconstruction_as_live_requirement_v1",
)
