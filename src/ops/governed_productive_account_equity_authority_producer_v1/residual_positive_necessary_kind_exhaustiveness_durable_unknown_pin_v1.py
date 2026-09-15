"""Pin residual necessary-kind exhaustiveness as durable UNKNOWN after NONE_BINDABLE.

Consumes the workpackage Owner-GO with SELECTED_PATH=PATH_B. Satisfies the
CH-named pin GO. Does not GET. Does not POST. Does not INCLUDE or EXCLUDE
residual. Does not invent PATH_C closeout. Does not Hope-GET. Does not
resolve secrets. Durable UNKNOWN is not INCLUDE, EXCLUDE, zero, absent,
or no-residual. NONE_BINDABLE and GET_COUNT=0 are provenance, not a
zero/none finding. U05/U06 remain REMAIN_UNKNOWN / DURABLE_UNKNOWN.
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
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_CLOSEOUT_STATUS,
    KIND_SET_EVIDENCE_PERSIST_STATUS,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    UNRESOLVED_ALGEBRA_TERMS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_primary_proof_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CH_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    NEXT_PRODUCTIVE_NODE as PARENT_NEXT_PRODUCTIVE_NODE,
    SELECTION_STATUS as PARENT_SELECTION_STATUS,
    reject_unknown_as_absent_v1,
    reject_unknown_as_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
    reject_none_bindable_as_exclude_v1,
)

OWNER_GO = "OWNER_GO_RESIDUAL_DURABLE_UNKNOWN_TO_NEXT_DEFINITIVE_BLOCK_V1"
SELECTED_PATH = "PATH_B"
EXPECTED_ORIGIN_MAIN_SHA = "6ab9e5230eeefe87a46f5572ea18ff095e6a186c"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_residual_positive_necessary_kind_exhaustiveness_"
    "durable_unknown_pin_v1/2026-09-15T050000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T05:00:00Z"
SCHEMA_CLASS = "RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
PRIMARY_PROOF_STATUS = "EXHAUSTIVENESS_BRANCH_CLOSED_DURABLE_UNKNOWN_RESIDUAL_REMAIN_UNKNOWN"
DECISION_BASIS = (
    "NONE_BINDABLE_GET_COUNT_0_PATH_B_PIN_DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE_"
    "U05_U06_UNKNOWN_NOT_ABSENT_OR_EXCLUDE"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_KIND_SET_REMAINS_"
    "EMPTY_FAIL_CLOSED_U05_U06_RESIDUAL_DURABLE_UNKNOWN_NOT_INCLUDE_OR_EXCLUDE"
)
ARCHITECTURE_BLOCKER = (
    "KIND_SET_AND_MAPPING_REQUIRE_NEW_OWNER_AUTHORITY_AFTER_THREE_NAMED_"
    "DURABLE_UNKNOWNS_NO_LOCAL_INCLUDE_EXCLUDE_OR_CERTIFICATE"
)
NEXT_PRODUCTIVE_NODE = "ACCOUNT_EQUITY_SOURCE_MAPPING"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_RATIFY_KIND_SET_OR_ACCOUNT_EQUITY_SOURCE_MAPPING_"
    "AFTER_U05_U06_RESIDUAL_DURABLE_UNKNOWN_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_NO_GET"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_NORMALIZERS = frozenset(
    {
        OUTCOME_INCLUDE,
        OUTCOME_EXCLUDE,
        "INCLUDE",
        "EXCLUDE",
        "FALSE",
        "false",
        "true",
        "0",
        "zero",
        "absent",
        "ABSENT",
        "EMPTY",
        "empty",
        "NONE",
        "NO_RESIDUAL",
        "NO_CLASS",
        "NONE_BINDABLE_MEANS_NO_RESIDUAL",
        "NONE_BINDABLE_MEANS_EXCLUDE",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(ValueError):
    """Fail-closed residual exhaustiveness durable-unknown pin violation."""


@dataclass(frozen=True)
class ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    selected_path: str
    target_unknown: str
    exhaustiveness_status: str
    residual_decision_after: str
    further_residual_exhaustiveness_acquisition: str
    exhaustiveness_branch_closed: str
    first_definitive_block: str
    next_productive_node: str
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
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            f"JSON_NOT_OBJECT:{path.name}"
        )
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            f"{field}_DRIFT:{actual}"
        )


def reject_durable_unknown_as_include_or_exclude_v1(*, claimed: str) -> None:
    if claimed in _NORMALIZERS:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            f"DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE:{claimed}"
        )


def reject_none_bindable_get_count_zero_as_absent_v1(*, claimed: str) -> None:
    if claimed in {
        "ABSENT",
        "absent",
        "0",
        "zero",
        "EMPTY",
        "NO_RESIDUAL",
        "NO_CLASS",
        "NONE_BINDABLE_MEANS_NO_RESIDUAL",
        "NONE_BINDABLE_MEANS_EXCLUDE",
    }:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            f"NONE_BINDABLE_GET_COUNT_0_IS_NOT_ABSENT_OR_EXCLUDE:{claimed}"
        )


def _assert_standing_pins() -> None:
    if LIVE_ARMED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "LIVE_ARMED_NOT_FALSE"
        )
    if WIRE_SEND_PERMITTED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "WIRE_SEND_PERMITTED_NOT_FALSE"
        )
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "U05_UNKNOWN_PRESERVED"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "U06_UNKNOWN_PRESERVED"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_COMPLETENESS_PROVEN is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "RESIDUAL_COMPLETENESS_MUST_REMAIN_UNPROVEN"
        )
    if RESIDUAL_NO_REMAINDER_NORMALIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "RESIDUAL_NO_REMAINDER_MUST_NOT_NORMALIZE"
        )
    if KIND_SET_RESOLVED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "KIND_SET_MUST_REMAIN_EMPTY"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "SOURCE_SEAM_MUST_REMAIN_ABSENT"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if CANDIDATE_SURFACE_SELECTION != "NONE_SELECTED":
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "CANDIDATE_SURFACE_SELECTION_NOT_NONE"
        )
    if MS2_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "MS2_AUTHORIZED_NOT_FALSE"
        )
    if D6_FULLY_CLOSED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "D6_FULLY_CLOSED_NOT_FALSE"
        )
    if D7_AUTHORIZED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "D7_AUTHORIZED_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "C17_CREATED_NOT_FALSE"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "NO_EQ_SOURCE_AUTHORITY"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "BILLS_MUST_REMAIN_NONCANONICAL"
        )
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "MAPPING_MUST_REMAIN_NOT_CANONICALLY_VALID"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "RECONSTRUCTION_ALGEBRA_MUST_REMAIN_INCOMPLETE"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError("DAG_PIN_DRIFT")


def _assert_parent_ch_pack(*, sealed_ch_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_ch_pack) != 0:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "CH_MANIFEST_VERIFY_NOT_ZERO"
        )
    claims = _load_json_object(path=sealed_ch_pack / CLAIMS_FILE)
    _require_token(field="OWNER_GO_STATUS", payload=claims, expected="CONSUMED")
    _require_token(
        field="CONCRETE_SURFACE_SELECTION_STATUS",
        payload=claims,
        expected=PARENT_SELECTION_STATUS,
    )
    _require_token(field="SELECTED_CANDIDATE_ID", payload=claims, expected=NONE_TOKEN)
    _require_token(field="MAX_GET_COUNT", payload=claims, expected="0")
    _require_token(field="AUTHORIZED_GET_COUNT", payload=claims, expected="0")
    _require_token(field="ACTUAL_GET_COUNT", payload=claims, expected="0")
    _require_token(field="POST_COUNT", payload=claims, expected="0")
    _require_token(field="HOPE_GET_FORBIDDEN", payload=claims, expected=TRUE_TOKEN)
    _require_token(
        field="RESIDUAL_DECISION_AFTER", payload=claims, expected=DECISION_REMAIN_UNKNOWN
    )
    _require_token(
        field="EXHAUSTIVENESS_STATUS_AFTER", payload=claims, expected=DECISION_REMAIN_UNKNOWN
    )
    _require_token(field="U05_DECISION_UNCHANGED", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U06_DECISION_UNCHANGED", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U06_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_EMBEDDING_IDENTITY", payload=claims, expected=DURABLE_UNKNOWN_TOKEN)
    _require_token(field="U06_PLACEMENT_IDENTITY", payload=claims, expected=DURABLE_UNKNOWN_TOKEN)
    _require_token(field="NONE_BINDABLE_IS_NOT_EXCLUDE", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="UNKNOWN_NOT_ABSENT", payload=claims, expected=TRUE_TOKEN)
    _require_token(field="UNKNOWN_NOT_EXCLUDE", payload=claims, expected=TRUE_TOKEN)
    _require_token(
        field="DURABLE_UNKNOWN_PIN_IMPLEMENTED_THIS_SLICE",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(field="PATH_C_CLOSEOUT", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_EQ_SOURCE_AUTHORITY", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="ACCOUNT_BILLS_CANONICALIZED", payload=claims, expected=FALSE_TOKEN)
    _require_token(field="BLOCKER_ID", payload=claims, expected=PARENT_BLOCKER_ID)
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=PIN_OWNER_GO)
    _require_token(
        field="NEXT_PRODUCTIVE_NODE",
        payload=claims,
        expected=PARENT_NEXT_PRODUCTIVE_NODE,
    )


def build_downstream_dependency_tree_v1() -> dict[str, Any]:
    records = (
        {
            "node_id": "RESIDUAL_EXHAUSTIVENESS_IDENTITY",
            "classification": "ALREADY_CLOSED",
            "status": DURABLE_UNKNOWN_TOKEN,
            "reason": (
                "PATH_B_PIN_NONE_BINDABLE_GET_COUNT_0_IS_NOT_EXCLUDE_OR_ABSENT_"
                "NO_BINDABLE_INDEPENDENT_TAXONOMY_CERTIFICATE"
            ),
        },
        {
            "node_id": "RESIDUAL_KIND",
            "classification": "BLOCKED_BY_RESIDUAL",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "INCLUDE_EXCLUDE_FORBIDDEN_WITHOUT_POSITIVE_COMPLETENESS_CERTIFICATE",
        },
        {
            "node_id": "RESIDUAL_SURFACE_BINDING",
            "classification": "ALREADY_CLOSED",
            "status": PARENT_SELECTION_STATUS,
            "reason": "PARENT_NONE_BINDABLE_GET_COUNT_0_CONSUMED_AS_PROVENANCE_NOT_ABSENCE",
        },
        {
            "node_id": "U05_KIND",
            "classification": "UNCHANGED",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "U05_PATH_B_PIN_REMAINS_DURABLE_UNKNOWN",
        },
        {
            "node_id": "U06_KIND",
            "classification": "UNCHANGED",
            "status": DECISION_REMAIN_UNKNOWN,
            "reason": "U06_PATH_B_PIN_REMAINS_DURABLE_UNKNOWN",
        },
        {
            "node_id": "D6_KIND_SET",
            "classification": "BLOCKED_BY_NAMED_REMAINING_UNKNOWNS",
            "status": KIND_SET_EMPTY,
            "reason": (
                "KIND_SET_CANNOT_RESOLVE_WHILE_U05_U06_RESIDUAL_REMAIN_UNKNOWN_"
                "DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE"
            ),
        },
        {
            "node_id": "RECONSTRUCTION_ALGEBRA",
            "classification": "ALREADY_FAIL_CLOSED_UNCHANGED",
            "status": "INCOMPLETE",
            "reason": (
                "EXISTING_UNRESOLVED_TERMS_U04_U05_U06_RESIDUAL_IS_NOT_AN_ALGEBRA_TERM_"
                "DURABLE_UNKNOWN_DOES_NOT_COMPLETE_ALGEBRA"
            ),
        },
        {
            "node_id": "ACCOUNT_EQUITY_SOURCE_MAPPING",
            "classification": "FIRST_DEFINITIVE_BLOCK",
            "status": "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
            "reason": (
                "NO_OWNER_RATIFIED_MAPPING_ARCHITECTURE_FOR_THREE_DURABLE_UNKNOWNS_"
                "KIND_SET_EMPTY_FAIL_CLOSED_NO_LOCAL_ADVANCEMENT"
            ),
        },
        {
            "node_id": "MS2",
            "classification": "BLOCKED_BY_KIND_SET",
            "status": "NOT_AUTHORIZED",
            "reason": "MS1_KIND_SET_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "D7",
            "classification": "BLOCKED_BY_D6",
            "status": "NOT_AUTHORIZED",
            "reason": "D6_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "PATH_C_CLOSEOUT",
            "classification": "FORBIDDEN",
            "status": FALSE_TOKEN,
            "reason": "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT_REJECT",
        },
        {
            "node_id": "FURTHER_RESIDUAL_CERTIFICATE_ACQUISITION",
            "classification": "STOPPED",
            "status": "STOPPED",
            "reason": "NO_BINDABLE_INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE",
        },
    )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "selected_path": SELECTED_PATH,
        "exhaustiveness_branch_closed": TRUE_TOKEN,
        "further_residual_exhaustiveness_acquisition": "STOPPED",
        "path_c_closeout": FALSE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_productive_classification": "REQUIRES_NEW_AUTHORITY",
        "first_definitive_block": DAG_PIN,
        "local_advancement_exhausted": TRUE_TOKEN,
        "standing_full_core_dag_pin": DAG_PIN,
        "records": list(records),
    }


def build_mapping_and_reconstruction_fail_closed_v1() -> dict[str, Any]:
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "MAPPING_MUST_REMAIN_NOT_CANONICALLY_VALID"
        )
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "RECONSTRUCTION_ALGEBRA_MUST_REMAIN_INCOMPLETE"
        )
    unresolved = ",".join(UNRESOLVED_ALGEBRA_TERMS)
    return {
        "layer": "CANONICAL_AUTHORITY",
        "existing_fail_closed_mapping_consumed": TRUE_TOKEN,
        "new_mapping_invented": FALSE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "standing_full_core_dag_pin": DAG_PIN,
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
        "kind_set_closeout_status": KIND_SET_CLOSEOUT_STATUS,
        "kind_set_evidence_persist_status": KIND_SET_EVIDENCE_PERSIST_STATUS,
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "earliest_unresolved_algebra_term": EARLIEST_UNRESOLVED_ALGEBRA_TERM,
        "unresolved_algebra_terms": unresolved,
        "residual_is_not_an_algebra_term": TRUE_TOKEN,
        "durable_unknown_does_not_complete_algebra": TRUE_TOKEN,
        "u05_liability_inclusion_or_value_synthesized": FALSE_TOKEN,
        "u06_fee_inclusion_synthesized": FALSE_TOKEN,
        "u05_economic_value_synthesized": FALSE_TOKEN,
        "u06_economic_value_synthesized": FALSE_TOKEN,
        "source_mapping_synthesized": FALSE_TOKEN,
        "why_mapping_cannot_advance_locally": (
            "KIND_SET_EMPTY_FAIL_CLOSED_AND_U05_U06_RESIDUAL_DURABLE_UNKNOWN_"
            "ARE_NOT_INCLUDE_OR_EXCLUDE_NO_OWNER_RATIFIED_MAPPING_WITH_UNKNOWNS"
        ),
    }


def execute_residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_ch_pack: Path | str | None = None,
    persist_as_of: str | None = None,
    selected_path: str = SELECTED_PATH,
) -> ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinResultV1:
    if owner_go != OWNER_GO:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "ORIGIN_MAIN_SHA_MISMATCH"
        )
    if selected_path != SELECTED_PATH:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "SELECTED_PATH_NOT_PATH_B"
        )
    _assert_standing_pins()
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_none_bindable_as_exclude_v1(claimed=PARENT_SELECTION_STATUS)
    reject_none_bindable_get_count_zero_as_absent_v1(claimed=PARENT_SELECTION_STATUS)
    reject_unknown_as_absent_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_unknown_as_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    law_outcome = evaluate_residual_primary_proof_v1(proof={})
    if law_outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "ABSENT_PROOF_MUST_NOT_DECIDE"
        )
    if law_outcome.outcome != OUTCOME_NONQUALIFYING:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "ABSENT_PROOF_MUST_BE_NONQUALIFYING"
        )
    reject_durable_unknown_as_include_or_exclude_v1(claimed=law_outcome.outcome)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    ch_pack = (
        Path(sealed_ch_pack) if sealed_ch_pack is not None else repo / CANONICAL_CH_PACK_RELPATH
    )
    _assert_parent_ch_pack(sealed_ch_pack=ch_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "FIELD_MISSING:persist_as_of"
        )
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    tree = build_downstream_dependency_tree_v1()
    mapping = build_mapping_and_reconstruction_fail_closed_v1()
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "SATISFIED_BY_WORKPACKAGE",
        "SELECTED_PATH": SELECTED_PATH,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CH_PACK": CANONICAL_CH_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "TARGET_UNKNOWN": TARGET_RESIDUAL,
        "RESIDUAL_EVIDENCE_CLASS": CLASS_RESIDUAL,
        "EXPECTED_PRIMARY_PROOF_OBJECT": PROOF_OBJECT_RESIDUAL,
        "PARENT_CONCRETE_SURFACE_SELECTION_STATUS": PARENT_SELECTION_STATUS,
        "PARENT_SELECTED_CANDIDATE_ID": NONE_TOKEN,
        "PARENT_BLOCKER_ID": PARENT_BLOCKER_ID,
        "PARENT_GET_COUNT": "0",
        "NONE_BINDABLE_GET_COUNT_0_IS_PROVENANCE_NOT_ABSENCE": TRUE_TOKEN,
        "NO_ACQUIRABLE_INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE": TRUE_TOKEN,
        "EXHAUSTIVENESS_STATUS_BEFORE": DECISION_REMAIN_UNKNOWN,
        "EXHAUSTIVENESS_STATUS_AFTER": DURABLE_UNKNOWN_TOKEN,
        "EXHAUSTIVENESS_IDENTITY_STATUS": DURABLE_UNKNOWN_TOKEN,
        "SEMANTIC_NORMALIZATION_FORBIDDEN": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_FALSE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_IS_NOT_ZERO_OR_ABSENT": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "NONE_BINDABLE_IS_NOT_EXCLUDE": TRUE_TOKEN,
        "NONE_BINDABLE_IS_NOT_ZERO_OR_NO_RESIDUAL": TRUE_TOKEN,
        "UNKNOWN_NOT_ABSENT": TRUE_TOKEN,
        "UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "NO_GET_REQUIRED": TRUE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "NO_ALGEBRAIC_UPLIFT": TRUE_TOKEN,
        "NO_RETROACTIVE_SEALED_EVIDENCE_UPLIFT": TRUE_TOKEN,
        "NO_HOPE_GET": TRUE_TOKEN,
        "RESIDUAL_DECISION_BEFORE": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_BASIS": DECISION_BASIS,
        "RESIDUAL_PRIMARY_PROOF_STATUS": PRIMARY_PROOF_STATUS,
        "FURTHER_RESIDUAL_EXHAUSTIVENESS_ACQUISITION": "STOPPED",
        "EXHAUSTIVENESS_BRANCH_CLOSED": TRUE_TOKEN,
        "PATH_C_CLOSEOUT": FALSE_TOKEN,
        "U05_EVIDENCE_CLASS": CLASS_U05,
        "U06_EVIDENCE_CLASS": CLASS_U06,
        "U05_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "U06_DECISION_UNCHANGED": DECISION_REMAIN_UNKNOWN,
        "U05_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_EMBEDDING_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "U06_PLACEMENT_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "U05_ECONOMIC_VALUE_SYNTHESIZED": FALSE_TOKEN,
        "U06_ECONOMIC_VALUE_SYNTHESIZED": FALSE_TOKEN,
        "U05_EVENT_KIND_SYNTHESIZED": FALSE_TOKEN,
        "U06_EVENT_KIND_SYNTHESIZED": FALSE_TOKEN,
        "U05_SOURCE_MAPPING_SYNTHESIZED": FALSE_TOKEN,
        "U06_SOURCE_MAPPING_SYNTHESIZED": FALSE_TOKEN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING": DAG_PIN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING_STATUS": DAG_PIN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_CLOSEOUT_STATUS": KIND_SET_CLOSEOUT_STATUS,
        "RECONSTRUCTION_ALGEBRA_COMPLETE": FALSE_TOKEN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAX_GET_COUNT": "0",
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "RETRY_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": "NOT_ATTEMPTED",
        "GET_ALONE_MAY_INCLUDE": FALSE_TOKEN,
        "GET_ALONE_MAY_EXCLUDE": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ALGEBRAIC_EQ_IDENTITY_FORBIDDEN": TRUE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "LOCAL_ADVANCEMENT_EXHAUSTED": TRUE_TOKEN,
        "FIRST_DEFINITIVE_BLOCK": DAG_PIN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
        "TARGET_U05": TARGET_U05,
        "TARGET_U06": TARGET_U06,
    }
    lineage = {
        "layer": "HISTORICAL",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "pin_owner_go": PIN_OWNER_GO,
        "selected_path": SELECTED_PATH,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_ch_pack": CANONICAL_CH_PACK_RELPATH,
        "parent_selection_status": PARENT_SELECTION_STATUS,
        "parent_get_count": "0",
        "reconstruction_source_authority": FALSE_TOKEN,
        "witness_acquisition_authorized": FALSE_TOKEN,
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
        "trading_authority_unchanged": TRUE_TOKEN,
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
    current_proof = {
        "layer": "ADJUDICATED_CONCLUSION",
        "target_unknown": TARGET_RESIDUAL,
        "exhaustiveness_status": DURABLE_UNKNOWN_TOKEN,
        "residual_decision_after": DECISION_REMAIN_UNKNOWN,
        "u05_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "u06_decision_unchanged": DECISION_REMAIN_UNKNOWN,
        "include_from_unknown": "FORBIDDEN_RESIDUAL_IS_NOT_AN_INCLUDE_KIND",
        "exclude_from_unknown": "FORBIDDEN_UNTIL_POSITIVE_COMPLETENESS_CERTIFICATE",
        "path_c_closeout": FALSE_TOKEN,
        "further_residual_exhaustiveness_acquisition": "STOPPED",
        "venue_eq_source_authority": FALSE_TOKEN,
        "no_get_required": TRUE_TOKEN,
        "none_bindable_get_count_0_is_provenance": TRUE_TOKEN,
        "first_definitive_block": DAG_PIN,
        "local_advancement_exhausted": TRUE_TOKEN,
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "no_acquirable_independent_taxonomy_exhaustiveness_certificate": TRUE_TOKEN,
        "path_c_closeout": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "algebraic_eq_identity_forbidden": TRUE_TOKEN,
        "durable_unknown_is_not_include": TRUE_TOKEN,
        "durable_unknown_is_not_exclude": TRUE_TOKEN,
        "none_bindable_is_not_exclude": TRUE_TOKEN,
        "unknown_is_not_absent": TRUE_TOKEN,
        "first_definitive_block": DAG_PIN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
    }
    provenance = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "parent_concrete_surface_selection_status": PARENT_SELECTION_STATUS,
        "parent_selected_candidate_id": NONE_TOKEN,
        "parent_get_count": "0",
        "authorized_get_count": "0",
        "actual_get_count": "0",
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "none_bindable_caused_the_pin": TRUE_TOKEN,
        "get_count_zero_caused_the_pin": TRUE_TOKEN,
        "none_bindable_is_not_zero_or_no_residual": TRUE_TOKEN,
        "get_count_zero_is_not_absent": TRUE_TOKEN,
        "reinterpretation_forbidden": TRUE_TOKEN,
    }
    historical = {
        "layer": "HISTORICAL",
        "parent_ch_pack": CANONICAL_CH_PACK_RELPATH,
        "sealed_u05_u06_packs_not_residual_authority": TRUE_TOKEN,
        "enumeration_is_not_exhaustiveness": TRUE_TOKEN,
        "reinterpretation_forbidden": TRUE_TOKEN,
        "sealed_evidence_uplift_forbidden": TRUE_TOKEN,
    }
    layers = {
        "CANONICAL_AUTHORITY": (
            "architecture_blocker_v1.json,mapping_and_reconstruction_fail_closed_v1.json"
        ),
        "FORENSIC_RAW_EVIDENCE": "none_bindable_get_count_zero_provenance_v1.json",
        "ADJUDICATED_CONCLUSION": (
            "current_proof_evaluation_v1.json,downstream_dependency_tree_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json,historical_non_uplift_v1.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=tree)
    _persist_json(path=store / "mapping_and_reconstruction_fail_closed_v1.json", payload=mapping)
    _persist_json(path=store / "current_proof_evaluation_v1.json", payload=current_proof)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(
        path=store / "none_bindable_get_count_zero_provenance_v1.json", payload=provenance
    )
    _persist_json(path=store / "historical_non_uplift_v1.json", payload=historical)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "SECRET_MARKER_PERSISTED"
        )
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError(
            "MANIFEST_VERIFY_NOT_ZERO"
        )
    return ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        selected_path=SELECTED_PATH,
        target_unknown=TARGET_RESIDUAL,
        exhaustiveness_status=DURABLE_UNKNOWN_TOKEN,
        residual_decision_after=DECISION_REMAIN_UNKNOWN,
        further_residual_exhaustiveness_acquisition="STOPPED",
        exhaustiveness_branch_closed=TRUE_TOKEN,
        first_definitive_block=DAG_PIN,
        next_productive_node=NEXT_PRODUCTIVE_NODE,
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
    "DECISION_BASIS",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "SELECTED_PATH",
    "ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError",
    "execute_residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1",
    "reject_durable_unknown_as_include_or_exclude_v1",
    "reject_none_bindable_get_count_zero_as_absent_v1",
)
