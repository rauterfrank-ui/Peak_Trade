"""Persist residual positive necessary-kind exhaustiveness NONE_BINDABLE.

Consumes the Owner-GO named by §11.2.1.CG. Reconstructs the ratified
positive necessary-kind inventory and exhaustiveness contract. Does not
GET. Does not POST. Does not resolve secrets. Does not INCLUDE residual.
Does not EXCLUDE residual. Enumeration of known kinds is not
exhaustiveness. U05/U06 REMAIN_UNKNOWN is not absent and not EXCLUDE.
AUTHORITY_EFFECT=NONE.

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
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    CLASS_RESIDUAL,
    CLASS_U05,
    CLASS_U06,
    HYPOTHESIS_ONLY_TOKENS,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    PROOF_OBJECT_RESIDUAL,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
    evaluate_residual_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANDIDATE_SURFACE_SELECTION,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_COMPLETENESS_PROVEN,
    RESIDUAL_KIND_DECISION,
    RESIDUAL_NO_REMAINDER_NORMALIZED,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_anchor_v1 import (
    AUTHORIZED_ANCHOR_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_ratification_v1 import (
    AUTHORIZED_SETTLEMENT_CURRENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    TODAY_SOURCE_KIND,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_equity_stock_placement_identity_durable_unknown_pin_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CG_PACK_RELPATH,
    NEXT_OWNER_GO as CONSUMED_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
    reject_none_bindable_as_exclude_v1,
)

OWNER_GO = CONSUMED_OWNER_GO
EXPECTED_ORIGIN_MAIN_SHA = "ee39448839a473dbaa22ea3096d4637627b89b3c"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_residual_positive_necessary_kind_exhaustiveness_"
    "primary_proof_v1/2026-09-15T040000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T04:00:00Z"
SCHEMA_CLASS = "RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
SELECTION_STATUS = "NONE_BINDABLE"
BINDING_STATUS = "NOT_BOUND"
PRE_ACQUISITION_BOUND = "PRE_ACQUISITION_CONTRACT_BOUND"
RESIDUAL_ACQUISITION_SURFACE = "INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE_NOT_GET"
POSITIVE_INCLUDE_PREDICATE = "NONE_RESIDUAL_IS_NOT_AN_INCLUDE_KIND"
POSITIVE_EXCLUDE_PREDICATE = "positive_necessary_kind_inventory_exhaustiveness_certificate"
POSITIVE_CLOSE_SEMANTIC = "EXCLUDE_REQUIRES_POSITIVE_COMPLETENESS_CERTIFICATE_NOT_ENUMERATION"
SCOPE_BINDING = "D4_BOUND_ACCOUNT_AND_NAMED_WINDOW"
TEMPORAL_ANCHOR_ID = AUTHORIZED_ANCHOR_ID
PRIMARY_PROOF_STATUS = "NOT_ACQUIRED_NO_BINDABLE_INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE"
DECISION_BASIS = (
    "EXHAUSTIVENESS_NOT_PROVEN_NO_BINDABLE_CERTIFICATE_SURFACE_"
    "U05_U06_UNKNOWN_NOT_ABSENT_OR_EXCLUDE"
)
BLOCKER_ID = "NO_INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE_BINDABLE_ON_CURRENT_SURFACES"
ARCHITECTURE_BLOCKER = (
    "POSITIVE_NECESSARY_KIND_INVENTORY_EXHAUSTIVENESS_CERTIFICATE_V1_"
    "NOT_ACQUIRABLE_U05_U06_REMAIN_UNKNOWN"
)
NEXT_PRODUCTIVE_NODE = "RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_V1"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_PIN_RESIDUAL_POSITIVE_NECESSARY_KIND_"
    "EXHAUSTIVENESS_DURABLE_UNKNOWN_PATH_B_AFTER_NONE_BINDABLE_V1"
)
NEXT_ACTION = "STOP_AWAIT_OWNER_GO_FOR_RESIDUAL_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_NO_GET"
SECRET_RESOLUTION_NOT_ATTEMPTED = "NOT_ATTEMPTED"
CLAIMS_FILE = "claims.json"
RATIFIED_POSITIVE_LIVE_STOCK_KIND_SET = TODAY_SOURCE_KIND
NAMED_REMAINING_UNKNOWN_TOKEN = ",".join(NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES)
HYPOTHESIS_ONLY_TOKEN = ",".join(HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ABSENT_NORMALIZERS = frozenset(
    {
        "ABSENT",
        "absent",
        "0",
        "zero",
        "EMPTY",
        "empty",
        "NONE",
        "NO_CLASS",
        "NO_RESIDUAL",
    }
)
_ALGEBRAIC_MARKERS = (
    "".join(("eq=", "cash", "Bal")),
    "".join(("cash", "Bal", "+", "upl")),
    "".join(("eq=", "cash", "Bal", "+", "upl", "-liab")),
)


class ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(ValueError):
    """Fail-closed residual exhaustiveness primary-proof persist violation."""


@dataclass(frozen=True)
class ResidualPositiveNecessaryKindExhaustivenessPrimaryProofResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    concrete_surface_selection_status: str
    concrete_surface_id: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    residual_decision_after: str
    exhaustiveness_status_after: str
    blocker_id: str
    next_productive_node: str
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
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            f"JSON_NOT_OBJECT:{path.name}"
        )
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            f"{field}_DRIFT:{actual}"
        )


def reject_unknown_as_absent_v1(*, claimed: str) -> None:
    if claimed in _ABSENT_NORMALIZERS:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            f"UNKNOWN_NOT_ABSENT:{claimed}"
        )


def reject_unknown_as_exclude_v1(*, claimed: str) -> None:
    if claimed in {OUTCOME_EXCLUDE, "EXCLUDE"}:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            f"UNKNOWN_NOT_EXCLUDE:{claimed}"
        )


def reject_eq_source_authority_v1(*, venue_eq_source_authority: str) -> None:
    if venue_eq_source_authority != FALSE_TOKEN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("NO_EQ_SOURCE_AUTHORITY")


def reject_algebraic_uplift_v1(*, formula: str) -> None:
    if any(marker in formula for marker in _ALGEBRAIC_MARKERS):
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("NO_ALGEBRAIC_UPLIFT")


def reject_retroactive_evidence_uplift_v1(*, uplift_claimed: str) -> None:
    if uplift_claimed == TRUE_TOKEN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "NO_RETROACTIVE_EVIDENCE_UPLIFT"
        )


def reject_enumeration_as_exhaustiveness_v1(
    *,
    inventory: str,
    proven_complete: str,
) -> None:
    if proven_complete == TRUE_TOKEN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "EXHAUSTIVENESS_REQUIRES_POSITIVE_COMPLETENESS_PROOF"
        )
    if inventory.strip() != "" and proven_complete != TRUE_TOKEN:
        return
    if inventory.strip() == "" and proven_complete == TRUE_TOKEN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "EXHAUSTIVENESS_REQUIRES_POSITIVE_COMPLETENESS_PROOF"
        )


def reject_exhaustiveness_close_while_u05_u06_unknown_v1(
    *,
    u05_decision: str,
    u06_decision: str,
    residual_outcome: str,
) -> None:
    if u05_decision != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("U05_UNKNOWN_PRESERVED")
    if u06_decision != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("U06_UNKNOWN_PRESERVED")
    if residual_outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "EXHAUSTIVENESS_REQUIRES_POSITIVE_COMPLETENESS_PROOF"
        )


def reject_acquisition_without_bound_contract_v1(
    *,
    surface_binding_status: str,
    authorized_get_count: str,
    actual_get_count: str,
) -> None:
    if surface_binding_status == PRE_ACQUISITION_BOUND:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "PRE_ACQUISITION_CONTRACT_NOT_BINDABLE_ON_NOT_GET_SURFACE"
        )
    if surface_binding_status != BINDING_STATUS:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            f"SURFACE_BINDING_STATUS_DRIFT:{surface_binding_status}"
        )
    if authorized_get_count != "0" or actual_get_count != "0":
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "ACQUISITION_CANNOT_RUN_WITHOUT_CONCRETE_BOUND_CONTRACT"
        )


def _assert_standing_pins() -> None:
    if LIVE_ARMED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "WIRE_SEND_PERMITTED_NOT_FALSE"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("U05_UNKNOWN_PRESERVED")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("U06_UNKNOWN_PRESERVED")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_COMPLETENESS_PROVEN is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "RESIDUAL_COMPLETENESS_MUST_REMAIN_UNPROVEN"
        )
    if RESIDUAL_NO_REMAINDER_NORMALIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "RESIDUAL_NO_REMAINDER_MUST_NOT_NORMALIZE"
        )
    if KIND_SET_RESOLVED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "KIND_SET_MUST_REMAIN_EMPTY"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if CANDIDATE_SURFACE_SELECTION != "NONE_SELECTED":
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "CANDIDATE_SURFACE_SELECTION_NOT_NONE"
        )
    if MS2_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "MS2_AUTHORIZED_NOT_FALSE"
        )
    if D6_FULLY_CLOSED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "D6_FULLY_CLOSED_NOT_FALSE"
        )
    if D7_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "D7_AUTHORIZED_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("NO_EQ_SOURCE_AUTHORITY")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "BILLS_MUST_REMAIN_NONCANONICAL"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("DAG_PIN_DRIFT")
    if AUTHORIZED_SETTLEMENT_CURRENCY != "USDC":
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "SETTLEMENT_CURRENCY_NOT_USDC"
        )


def _assert_parent_cg_pack(*, sealed_cg_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_cg_pack) != 0:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "CG_MANIFEST_VERIFY_NOT_ZERO"
        )
    claims = _load_json_object(path=sealed_cg_pack / CLAIMS_FILE)
    _require_token(field="OWNER_GO_STATUS", payload=claims, expected="CONSUMED")
    _require_token(field="SELECTED_PATH", payload=claims, expected="PATH_B")
    _require_token(field="PLACEMENT_IDENTITY_STATUS", payload=claims, expected="DURABLE_UNKNOWN")
    _require_token(field="U06_DECISION_AFTER", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_DECISION_UNCHANGED", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(
        field="RESIDUAL_DECISION_UNCHANGED", payload=claims, expected=DECISION_REMAIN_UNKNOWN
    )
    _require_token(field="ACTUAL_GET_COUNT", payload=claims, expected="0")
    _require_token(field="POST_COUNT", payload=claims, expected="0")
    _require_token(field="HOPE_GET_FORBIDDEN", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="PATH_C_CLOSEOUT", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="ACCOUNT_BILLS_CANONICALIZED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=OWNER_GO)
    _require_token(field="NEXT_PRODUCTIVE_NODE", payload=claims, expected=CLASS_RESIDUAL)


def build_ratified_necessary_kind_inventory_v1() -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "target_unknown": TARGET_RESIDUAL,
        "evidence_class_id": CLASS_RESIDUAL,
        "primary_proof_object": PROOF_OBJECT_RESIDUAL,
        "positive_include_predicate": POSITIVE_INCLUDE_PREDICATE,
        "positive_exclude_predicate": POSITIVE_EXCLUDE_PREDICATE,
        "positive_close_semantic": POSITIVE_CLOSE_SEMANTIC,
        "completeness_requirement": "POSITIVE_EXHAUSTIVENESS_REQUIRED_FOR_EXCLUDE",
        "coverage_requirement": "CERTIFICATE_MUST_COVER_D4_BOUND_ACCOUNT_AND_NAMED_WINDOW",
        "account_d4_binding": EXPECTED_GENESIS_ID,
        "ccy_binding": AUTHORIZED_SETTLEMENT_CURRENCY,
        "temporal_anchor_id": TEMPORAL_ANCHOR_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "scope": SCOPE_BINDING,
        "live_equity_stock_kind_set_positive_members": RATIFIED_POSITIVE_LIVE_STOCK_KIND_SET,
        "ratified_classified_event_kind_set": KIND_SET_EMPTY,
        "named_remaining_unknown_necessary_classes": NAMED_REMAINING_UNKNOWN_TOKEN,
        "hypothesis_only_classes": HYPOTHESIS_ONLY_TOKEN,
        "enumeration_is_not_exhaustiveness": TRUE_TOKEN,
        "u05_in_positive_set": FALSE_TOKEN,
        "u06_in_positive_set": FALSE_TOKEN,
        "residual_is_not_an_include_kind": TRUE_TOKEN,
        "existing_evidence_sufficient": FALSE_TOKEN,
        "primary_proof_role_allowed": "INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE_ONLY",
    }


def build_frozen_candidate_census_v1() -> dict[str, Any]:
    records = (
        {
            "candidate_id": "C01_EXISTING_TAXONOMY_CONTRACT",
            "surface_id": "EQUITY_AFFECTING_EVENT_TAXONOMY_CONTRACT_V1",
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "RATIFIED_CLASSIFIED_KIND_SET_EMPTY;NO_CERTIFICATE_ID;"
                "NO_CERTIFICATE_DIGEST;PROVEN_COMPLETE_FALSE"
            ),
        },
        {
            "candidate_id": "C02_LIVE_EQUITY_STOCK_KIND_SET_ENUMERATION",
            "surface_id": RATIFIED_POSITIVE_LIVE_STOCK_KIND_SET,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "ENUMERATION_OF_KNOWN_KINDS_IS_NOT_EXHAUSTIVENESS;"
                "STOCK_KIND_IS_NOT_RESIDUAL_EVENT_CLASS_CERTIFICATE"
            ),
        },
        {
            "candidate_id": "C03_HYPOTHESIS_ONLY_KIND_LIST",
            "surface_id": HYPOTHESIS_ONLY_TOKEN,
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": "HYPOTHESIS_ONLY_LIST_IS_NOT_EXHAUSTIVENESS_PROOF",
        },
        {
            "candidate_id": "C04_PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT",
            "surface_id": "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT",
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT_REJECT",
        },
        {
            "candidate_id": "C05_VENUE_GET_AS_EXHAUSTIVENESS_CERTIFICATE",
            "surface_id": "GET_VENUE_SURFACE_HOPE",
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "ACQUISITION_SURFACE_IS_NOT_GET;HOPE_GET_FORBIDDEN;NO_PRE_ACQUISITION_CONTRACT"
            ),
        },
        {
            "candidate_id": "C06_U05_U06_UNKNOWN_AS_ABSENT_OR_EXCLUDE",
            "surface_id": f"{TARGET_U05}+{TARGET_U06}",
            "bindable": FALSE_TOKEN,
            "already_exhausted": TRUE_TOKEN,
            "disqualification_reason": (
                "UNKNOWN_NOT_ABSENT;UNKNOWN_NOT_EXCLUDE;"
                "EXHAUSTIVENESS_CANNOT_CLOSE_WHILE_U05_U06_REMAIN_UNKNOWN"
            ),
        },
    )
    if any(item["bindable"] == TRUE_TOKEN for item in records):
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "BINDABLE_SURFACE_MUST_NOT_EXIST"
        )
    if any(
        token in HYPOTHESIS_ONLY_TOKENS
        for token in RATIFIED_POSITIVE_LIVE_STOCK_KIND_SET.split(",")
    ):
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "HYPOTHESIS_ONLY_MUST_NOT_ENTER_POSITIVE_SET"
        )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "census_kind": "FROZEN_ALREADY_NAMED_SURFACES_NOT_GENERAL_VENUE_SEARCH",
        "candidate_count": str(len(records)),
        "selection_status": SELECTION_STATUS,
        "selected_candidate_id": NONE_TOKEN,
        "selected_surface_id": NONE_TOKEN,
        "selected_method": NONE_TOKEN,
        "selected_host": NONE_TOKEN,
        "selected_path": NONE_TOKEN,
        "selected_query": NONE_TOKEN,
        "selected_primary_proof_role": NONE_TOKEN,
        "residual_primary_proof_role_bound": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "retry_allowed": FALSE_TOKEN,
        "max_get_count": "0",
        "records": list(records),
    }


def execute_residual_positive_necessary_kind_exhaustiveness_primary_proof_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_cg_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> ResidualPositiveNecessaryKindExhaustivenessPrimaryProofResultV1:
    if owner_go != OWNER_GO:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "ORIGIN_MAIN_SHA_MISMATCH"
        )
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cg_pack = (
        Path(sealed_cg_pack) if sealed_cg_pack is not None else repo / CANONICAL_CG_PACK_RELPATH
    )
    _assert_parent_cg_pack(sealed_cg_pack=cg_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "FIELD_MISSING:persist_as_of"
        )
    reject_none_bindable_as_exclude_v1(claimed=SELECTION_STATUS)
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_eq_source_authority_v1(venue_eq_source_authority=FALSE_TOKEN)
    reject_algebraic_uplift_v1(formula="")
    reject_retroactive_evidence_uplift_v1(uplift_claimed=FALSE_TOKEN)
    reject_unknown_as_absent_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_unknown_as_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_enumeration_as_exhaustiveness_v1(
        inventory=RATIFIED_POSITIVE_LIVE_STOCK_KIND_SET,
        proven_complete=FALSE_TOKEN,
    )
    reject_acquisition_without_bound_contract_v1(
        surface_binding_status=BINDING_STATUS,
        authorized_get_count="0",
        actual_get_count="0",
    )
    law_outcome = evaluate_residual_primary_proof_v1(proof={})
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "ABSENT_PROOF_MUST_BE_NONQUALIFYING"
        )
    reject_none_bindable_as_exclude_v1(claimed=law_outcome.outcome)
    reject_exhaustiveness_close_while_u05_u06_unknown_v1(
        u05_decision=U05_KIND_DECISION,
        u06_decision=U06_KIND_DECISION,
        residual_outcome=law_outcome.outcome,
    )
    inventory = build_ratified_necessary_kind_inventory_v1()
    census = build_frozen_candidate_census_v1()
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "hope_get_forbidden": TRUE_TOKEN,
        "acquisition_surface": RESIDUAL_ACQUISITION_SURFACE,
        "venue_eq_source_authority": FALSE_TOKEN,
        "algebraic_eq_identity_forbidden": TRUE_TOKEN,
        "enumeration_is_not_exhaustiveness": TRUE_TOKEN,
        "none_bindable_is_not_exclude": TRUE_TOKEN,
        "unknown_is_not_absent": TRUE_TOKEN,
        "unknown_is_not_exclude": TRUE_TOKEN,
        "path_c_closeout": FALSE_TOKEN,
        "durable_unknown_pin_not_implemented_this_slice": TRUE_TOKEN,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_action": NEXT_ACTION,
    }
    surface = {
        "layer": "CANONICAL_AUTHORITY",
        "owner_go": OWNER_GO,
        "semantic_acquisition_surface": RESIDUAL_ACQUISITION_SURFACE,
        "expected_primary_proof_object": PROOF_OBJECT_RESIDUAL,
        "concrete_surface_id": NONE_TOKEN,
        "http_method": NONE_TOKEN,
        "bound_endpoint": NONE_TOKEN,
        "bound_query": NONE_TOKEN,
        "primary_proof_role_bound": FALSE_TOKEN,
        "selected_primary_proof_role": NONE_TOKEN,
        "max_get_count": "0",
        "retry_allowed": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "surface_binding_status": BINDING_STATUS,
        "concrete_surface_selection_status": SELECTION_STATUS,
        "productive_acquisition_authorized": FALSE_TOKEN,
        "event_acquisition_network_get_authorized": FALSE_TOKEN,
        "account_bills_canonicalized": FALSE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "fail_closed_policy": "NO_SURFACE_NO_GET_NO_INCLUDE_NO_EXCLUDE",
        "blocker_id": BLOCKER_ID,
    }
    evaluation = {
        "layer": "ADJUDICATED_CONCLUSION",
        "current_primary_proof_present": FALSE_TOKEN,
        "existing_evidence_sufficient": FALSE_TOKEN,
        "law_outcome": law_outcome.outcome,
        "law_basis": law_outcome.basis,
        "residual_primary_proof_status": PRIMARY_PROOF_STATUS,
        "blocker_id": BLOCKER_ID,
        "residual_decision_after": DECISION_REMAIN_UNKNOWN,
        "residual_decision_basis": DECISION_BASIS,
        "exhaustiveness_status_before": "UNPROVEN",
        "exhaustiveness_status_after": "REMAIN_UNKNOWN",
        "include_from_unknown": "FORBIDDEN_RESIDUAL_IS_NOT_AN_INCLUDE_KIND",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_COMPLETENESS_CERTIFICATE",
        "productive_acquisition_authorized": FALSE_TOKEN,
    }
    unknown_guard = {
        "layer": "ADJUDICATED_CONCLUSION",
        "u05_decision": DECISION_REMAIN_UNKNOWN,
        "u06_decision": DECISION_REMAIN_UNKNOWN,
        "u05_embedding_identity": "DURABLE_UNKNOWN",
        "u06_placement_identity": "DURABLE_UNKNOWN",
        "unknown_is_not_absent": TRUE_TOKEN,
        "unknown_is_not_exclude": TRUE_TOKEN,
        "unknown_is_not_zero": TRUE_TOKEN,
        "u05_not_treated_as_absent": TRUE_TOKEN,
        "u06_not_treated_as_absent": TRUE_TOKEN,
        "u05_not_treated_as_exclude": TRUE_TOKEN,
        "u06_not_treated_as_exclude": TRUE_TOKEN,
        "residual_decision_after": DECISION_REMAIN_UNKNOWN,
        "none_bindable_is_not_exclude": TRUE_TOKEN,
    }
    completeness = {
        "layer": "CANONICAL_AUTHORITY",
        "exhaustiveness_requires_positive_completeness_proof": TRUE_TOKEN,
        "hypothesis_only_list_is_not_proof": TRUE_TOKEN,
        "path_c_is_not_proof": TRUE_TOKEN,
        "non_observation_is_not_exclude": TRUE_TOKEN,
        "empty_set_is_not_zero_necessary_events": TRUE_TOKEN,
        "known_kind_enumeration_is_not_proof": TRUE_TOKEN,
        "u05_u06_unknown_blocks_positive_close": TRUE_TOKEN,
        "residual_completeness_proven": FALSE_TOKEN,
    }
    historical = {
        "layer": "HISTORICAL",
        "gate_a_uplift_forbidden": TRUE_TOKEN,
        "bh_bi_uplift_forbidden": TRUE_TOKEN,
        "package_1_uplift_forbidden": TRUE_TOKEN,
        "sealed_u05_u06_packs_not_residual_authority": TRUE_TOKEN,
        "reinterpretation_forbidden": TRUE_TOKEN,
        "parent_cg_pack": CANONICAL_CG_PACK_RELPATH,
    }
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "WORKPACKAGE": SCHEMA_CLASS,
        "TARGET_UNKNOWN": TARGET_RESIDUAL,
        "RESIDUAL_EVIDENCE_CLASS": CLASS_RESIDUAL,
        "EXPECTED_PRIMARY_PROOF_OBJECT": PROOF_OBJECT_RESIDUAL,
        "AUTHORIZED_ACQUISITION_SURFACE": RESIDUAL_ACQUISITION_SURFACE,
        "POSITIVE_INCLUDE_PREDICATE": POSITIVE_INCLUDE_PREDICATE,
        "POSITIVE_EXCLUDE_PREDICATE": POSITIVE_EXCLUDE_PREDICATE,
        "POSITIVE_CLOSE_SEMANTIC": POSITIVE_CLOSE_SEMANTIC,
        "SCOPE_BINDING": SCOPE_BINDING,
        "ACCOUNT_D4_BINDING": EXPECTED_GENESIS_ID,
        "CCY_BINDING": AUTHORIZED_SETTLEMENT_CURRENCY,
        "TEMPORAL_ANCHOR_ID": TEMPORAL_ANCHOR_ID,
        "RATIFIED_NECESSARY_KIND_SET": RATIFIED_POSITIVE_LIVE_STOCK_KIND_SET,
        "RATIFIED_CLASSIFIED_EVENT_KIND_SET": KIND_SET_EMPTY,
        "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES": NAMED_REMAINING_UNKNOWN_TOKEN,
        "U05_EVIDENCE_CLASS": CLASS_U05,
        "U06_EVIDENCE_CLASS": CLASS_U06,
        "CONCRETE_SURFACE_CANDIDATE_COUNT": census["candidate_count"],
        "CONCRETE_SURFACE_SELECTION_STATUS": SELECTION_STATUS,
        "CONCRETE_SURFACE_ID": NONE_TOKEN,
        "SELECTED_CANDIDATE_ID": NONE_TOKEN,
        "SELECTED_METHOD": NONE_TOKEN,
        "SELECTED_HOST": NONE_TOKEN,
        "SELECTED_PATH": NONE_TOKEN,
        "SELECTED_QUERY": NONE_TOKEN,
        "SELECTED_PRIMARY_PROOF_ROLE": NONE_TOKEN,
        "HTTP_METHOD": NONE_TOKEN,
        "BOUND_ENDPOINT": NONE_TOKEN,
        "PRIMARY_PROOF_ROLE_BOUND": FALSE_TOKEN,
        "MAX_GET_COUNT": "0",
        "RETRY_ALLOWED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "SURFACE_BINDING_STATUS": BINDING_STATUS,
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": SECRET_RESOLUTION_NOT_ATTEMPTED,
        "RAW_EVIDENCE_STATUS": "NOT_ACQUIRED",
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "EXISTING_EVIDENCE_SUFFICIENT": FALSE_TOKEN,
        "RESIDUAL_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "RESIDUAL_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_BASIS": DECISION_BASIS,
        "EXHAUSTIVENESS_STATUS_BEFORE": "UNPROVEN",
        "EXHAUSTIVENESS_STATUS_AFTER": "REMAIN_UNKNOWN",
        "NONE_BINDABLE_IS_NOT_EXCLUDE": TRUE_TOKEN,
        "UNKNOWN_NOT_ABSENT": TRUE_TOKEN,
        "UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "U05_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "U06_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "U05_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_EMBEDDING_IDENTITY": "DURABLE_UNKNOWN",
        "U06_PLACEMENT_IDENTITY": "DURABLE_UNKNOWN",
        "GET_ALONE_MAY_INCLUDE": FALSE_TOKEN,
        "GET_ALONE_MAY_EXCLUDE": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "NO_ALGEBRAIC_UPLIFT": TRUE_TOKEN,
        "NO_RETROACTIVE_EVIDENCE_UPLIFT": TRUE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "DURABLE_UNKNOWN_PIN_IMPLEMENTED_THIS_SLICE": FALSE_TOKEN,
        "PATH_C_CLOSEOUT": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "SECRETS_OR_SIGNATURES_PERSISTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
    }
    lineage = {
        "layer": "HISTORICAL",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cg_pack": CANONICAL_CG_PACK_RELPATH,
        "reconstruction_source_authority": FALSE_TOKEN,
        "new_candidate_search_executed": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "algebraic_uplift_used": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "u05_unchanged": TRUE_TOKEN,
        "u06_unchanged": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    layers = {
        "CANONICAL_AUTHORITY": (
            "acquisition_surface_binding_v1.json,"
            "ratified_necessary_kind_inventory_v1.json,"
            "exhaustiveness_completeness_requirement_v1.json,"
            "architecture_blocker_v1.json"
        ),
        "FORENSIC_RAW_EVIDENCE": "NONE_NO_GET_NO_SECRET_RESOLUTION",
        "ADJUDICATED_CONCLUSION": (
            "candidate_surface_capability_adjudication_v1.json,"
            "current_proof_evaluation_v1.json,"
            "unknown_not_absent_or_exclude_guard_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json,historical_non_uplift_v1.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    _persist_json(path=root / CLAIMS_FILE, payload=claims)
    _persist_json(path=root / "acquisition_surface_binding_v1.json", payload=surface)
    _persist_json(path=root / "ratified_necessary_kind_inventory_v1.json", payload=inventory)
    _persist_json(
        path=root / "candidate_surface_capability_adjudication_v1.json",
        payload=census,
    )
    _persist_json(path=root / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=root / "current_proof_evaluation_v1.json", payload=evaluation)
    _persist_json(path=root / "unknown_not_absent_or_exclude_guard_v1.json", payload=unknown_guard)
    _persist_json(
        path=root / "exhaustiveness_completeness_requirement_v1.json", payload=completeness
    )
    _persist_json(path=root / "historical_non_uplift_v1.json", payload=historical)
    _persist_json(path=root / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=root / "layers_v1.json", payload=layers)
    _persist_json(path=root / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=root)
    if verify_manifest_sha256_v1(store_root=root) != 0:
        raise ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError(
            "MANIFEST_VERIFY_NOT_ZERO"
        )
    return ResidualPositiveNecessaryKindExhaustivenessPrimaryProofResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(root),
        concrete_surface_selection_status=SELECTION_STATUS,
        concrete_surface_id=NONE_TOKEN,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        residual_decision_after=DECISION_REMAIN_UNKNOWN,
        exhaustiveness_status_after="REMAIN_UNKNOWN",
        blocker_id=BLOCKER_ID,
        next_productive_node=NEXT_PRODUCTIVE_NODE,
        evidence_manifest=str(root / "MANIFEST.sha256"),
    )


__all__ = [
    "ARCHITECTURE_BLOCKER",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "DECISION_BASIS",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PRIMARY_PROOF_STATUS",
    "RESIDUAL_ACQUISITION_SURFACE",
    "SELECTION_STATUS",
    "ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError",
    "build_frozen_candidate_census_v1",
    "build_ratified_necessary_kind_inventory_v1",
    "execute_residual_positive_necessary_kind_exhaustiveness_primary_proof_v1",
    "reject_acquisition_without_bound_contract_v1",
    "reject_algebraic_uplift_v1",
    "reject_enumeration_as_exhaustiveness_v1",
    "reject_eq_source_authority_v1",
    "reject_exhaustiveness_close_while_u05_u06_unknown_v1",
    "reject_retroactive_evidence_uplift_v1",
    "reject_unknown_as_absent_v1",
    "reject_unknown_as_exclude_v1",
]
