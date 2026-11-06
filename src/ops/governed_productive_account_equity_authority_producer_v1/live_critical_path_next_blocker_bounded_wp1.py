"""Live-critical-path next-blocker bounded workpackage.

Consumes sealed BL/BJ remaining-unknown kind semantics. Does not reconstruct
F12/F13/U05/F16/F17/F18. Persists a NEW_CANONICAL_DEFINITION of the live
KIND_SET boundary. Does not GET. Does not POST. Does not execute GATE_A
or GATE_B. Empty historical KIND_SET remains EMPTY_FAIL_CLOSED.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    RATIFIED_SOURCE_KIND_SET,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    FACT_F12,
    FACT_F13,
    FACT_F16,
    FACT_F17,
    FACT_F18,
    FACT_IDS,
    FACT_U05,
    FALSE_TOKEN,
    KIND_SET_EMPTY,
    NONE_TOKEN,
    TRUE_TOKEN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bk_bj_semantics_consumption_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BL_PACK_RELPATH,
    CLAIMS_FILE,
    consume_bj_remaining_unknown_kind_semantics_v1,
    records_from_bj_semantics_claims_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CURRENTLY_DECISION_CAPABLE,
    EARLIEST_REMAINING_D6_BLOCKER as HISTORICAL_D6_BLOCKER,
    GATE_A_ID,
    GATE_B_ID,
    KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY as HISTORICAL_KIND_SET_BLOCKED_BY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CRITICAL_PATH_NEXT_BLOCKER_BOUNDED_WORKPACKAGE"
EXPECTED_ORIGIN_MAIN_SHA = "07d8903e3aa609ae982ead2fdf3bba4061dd82ec"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_live_critical_path_next_blocker_wp1/2026-09-14T090000Z"
)
NEW_CANONICAL_DEFINITION_ID = "NEW_CANONICAL_LIVE_EQUITY_STOCK_KIND_SET_V1"
LIVE_CRITICAL_KIND_SET_IDENTITY = NEW_CANONICAL_DEFINITION_ID
LIVE_CRITICAL_KIND_SET = KIND_SET_EMPTY
EARLIEST_LIVE_CRITICAL_PATH_BLOCKER = (
    "NO_OWNER_RATIFIED_NEW_CANONICAL_LIVE_EQUITY_STOCK_SOURCE_KIND"
)
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION_V1"
CLASS_LIVE_CRITICAL = "A_LIVE_CRITICAL_PATH_BLOCKER"
CLASS_DOWNSTREAM = "B_DOWNSTREAM_NOT_YET_BLOCKING"
CLASS_HISTORICAL = "C_HISTORICAL_NON_CRITICAL"
CLASS_ALREADY_CLOSED = "D_ALREADY_CLOSED"
LAYER_CANONICAL = "CANONICAL_AUTHORITY"
LAYER_FORENSIC = "FORENSIC_RAW_EVIDENCE"
LAYER_ADJUDICATED = "ADJUDICATED_CONCLUSION"
LAYER_HISTORICAL = "HISTORICAL_INTERMEDIATE"
LAYER_NAVIGATION = "NAVIGATION_ONLY"
LAYER_INTERPRETATION = "INTERPRETATION"
LAYER_HYPOTHESIS = "HYPOTHESIS"
LAYER_OPEN = "OPEN_OR_CONTRADICTORY"
HISTORICAL_UNKNOWN_FACTS: tuple[str, ...] = FACT_IDS


class LiveCriticalPathNextBlockerError(ValueError):
    """Fail-closed live-critical-path next-blocker workpackage violation."""


@dataclass(frozen=True)
class LiveCriticalPathItemAdjudicationV1:
    item_id: str
    classification: str
    layer: str
    reconstruct_historical_unknown: str
    live_kind_set_member: str
    rationale: str


@dataclass(frozen=True)
class LiveCriticalKindSetBoundaryV1:
    definition_class: str
    definition_id: str
    live_critical_kind_set: str
    live_critical_kind_set_resolved: str
    historical_kind_set: str
    historical_kind_set_resolved: str
    historical_unknown_on_critical_path: str
    ratified_live_source_kinds: str
    kinds_invented_this_go: str


@dataclass(frozen=True)
class LiveCriticalPathNextBlockerResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    historical_unknown_on_critical_path: str
    live_critical_kind_set: str
    live_critical_kind_set_resolved: str
    earliest_live_critical_path_blocker: str
    earliest_remaining_d6_blocker: str
    next_owner_go_required: str
    venue_get_count: str
    venue_post_count: str
    gate_a_executed: str
    gate_b_executed: str
    kinds_invented_this_go: str
    d6_fully_closed: str
    d7_authorized: str
    ms2_authorized: str
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
        raise LiveCriticalPathNextBlockerError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise LiveCriticalPathNextBlockerError(f"{field}_DRIFT:{actual}")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise LiveCriticalPathNextBlockerError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise LiveCriticalPathNextBlockerError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise LiveCriticalPathNextBlockerError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise LiveCriticalPathNextBlockerError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise LiveCriticalPathNextBlockerError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise LiveCriticalPathNextBlockerError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )


def reject_claimed_live_critical_path_authority_mutation_v1(
    *,
    claimed_proof: str,
    fact_id: str,
) -> None:
    forbidden = {
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "EXECUTE_GATE_B",
        "HOPE_BALANCE_GET",
        "VENUE_POST",
        "KIND_SET_RESOLVED_TRUE",
        "D6_FULLY_CLOSED",
        "D7_AUTHORIZED_TRUE",
        "MS2_AUTHORIZED_TRUE",
        "INVENT_LIVE_SOURCE_KIND",
        "RECONSTRUCT_HISTORICAL_UNKNOWN",
        "PROMOTE_HISTORICAL_UNKNOWN_TO_LIVE_KIND",
        "PATH_C_UNKNOWN_CLOSEOUT",
        "RESTORE_LEGACY_EQUITY_LOGIC",
        "NORMALIZE_UNKNOWN_TO_INCLUDE",
        "NORMALIZE_UNKNOWN_TO_EXCLUDE",
    }
    if claimed_proof in forbidden:
        raise LiveCriticalPathNextBlockerError(
            f"LIVE_CRITICAL_PATH_CANNOT_{claimed_proof}:{fact_id}"
        )
    if claimed_proof not in {
        "TYPED_UNRESOLVED_REMAIN_UNKNOWN",
        "NEW_CANONICAL_DEFINITION_EMPTY_FAIL_CLOSED",
        "HISTORICAL_UNKNOWN_NOT_LIVE_KIND_SET_MEMBER",
    }:
        raise LiveCriticalPathNextBlockerError(
            f"LIVE_CRITICAL_PATH_PROOF_UNKNOWN:{claimed_proof}:{fact_id}"
        )


def build_live_critical_path_item_adjudications_v1() -> tuple[
    LiveCriticalPathItemAdjudicationV1, ...
]:
    _assert_standing_pins()
    historical = [
        LiveCriticalPathItemAdjudicationV1(
            item_id=fact_id,
            classification=CLASS_HISTORICAL,
            layer=LAYER_ADJUDICATED,
            reconstruct_historical_unknown=FALSE_TOKEN,
            live_kind_set_member=FALSE_TOKEN,
            rationale="STANDING_REMAIN_UNKNOWN_FAIL_CLOSED_NOT_LIVE_KIND_SET_MEMBER",
        )
        for fact_id in HISTORICAL_UNKNOWN_FACTS
    ]
    closed = [
        LiveCriticalPathItemAdjudicationV1(
            item_id=item_id,
            classification=CLASS_ALREADY_CLOSED,
            layer=LAYER_CANONICAL,
            reconstruct_historical_unknown=FALSE_TOKEN,
            live_kind_set_member=FALSE_TOKEN,
            rationale=rationale,
        )
        for item_id, rationale in (
            ("D4_BOUND_ACCOUNT_IDENTITY", "CONTRACT_AND_GENESIS_ALREADY_BOUND"),
            ("D5_CHECKPOINT_OBSERVATION", "ACQUISITION_CONTRACT_ALREADY_BOUND"),
            ("D6_BJ_REMAINING_UNKNOWN_PIN", "TYPED_PIN_ALREADY_CONSUMED"),
            ("D6_BK_BL_SEMANTICS_CONSUMPTION", "TYPED_CONSUMPTION_ALREADY_CONSUMED"),
        )
    ]
    downstream = [
        LiveCriticalPathItemAdjudicationV1(
            item_id=item_id,
            classification=CLASS_DOWNSTREAM,
            layer=LAYER_ADJUDICATED,
            reconstruct_historical_unknown=FALSE_TOKEN,
            live_kind_set_member=FALSE_TOKEN,
            rationale=rationale,
        )
        for item_id, rationale in (
            (GATE_A_ID, "REOPENS_HISTORICAL_F12_F13_NOT_CURRENT_LIVE_KIND_SET"),
            (GATE_B_ID, "REQUIRES_UNIQUE_EXTERNAL_AUTHORITY_NOT_THIS_GO"),
            ("MS2_EVENT_SOURCE_SEAM", "MS2_UNAUTHORIZED_UNTIL_LIVE_KIND_SET_RATIFIED"),
            ("D7_DETERMINISTIC_STOCK_RECONSTRUCTION", "D7_UNAUTHORIZED"),
            ("D8_FRESH_EQ_RECONCILE", "TARGET_ONLY_UNTIL_STOCK_RECONSTRUCTED"),
            ("C17_SOURCE_CANDIDATE", "FROZEN_UNTIL_D1_D9_PROVEN"),
            ("LIVE_ENABLED", "STANDING_FALSE"),
            ("LIVE_ARMED", "STANDING_FALSE"),
            ("WIRE_SEND_PERMITTED", "STANDING_FALSE"),
        )
    ]
    live = (
        LiveCriticalPathItemAdjudicationV1(
            item_id=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
            classification=CLASS_LIVE_CRITICAL,
            layer=LAYER_ADJUDICATED,
            reconstruct_historical_unknown=FALSE_TOKEN,
            live_kind_set_member=FALSE_TOKEN,
            rationale="NEW_CANONICAL_DEFINITION_EMPTY_FAIL_CLOSED_NO_KIND_INVENTED",
        ),
    )
    return (*live, *historical, *closed, *downstream)


def build_live_critical_kind_set_boundary_v1() -> LiveCriticalKindSetBoundaryV1:
    _assert_standing_pins()
    return LiveCriticalKindSetBoundaryV1(
        definition_class="NEW_CANONICAL_DEFINITION",
        definition_id=LIVE_CRITICAL_KIND_SET_IDENTITY,
        live_critical_kind_set=LIVE_CRITICAL_KIND_SET,
        live_critical_kind_set_resolved=FALSE_TOKEN,
        historical_kind_set=KIND_SET_EMPTY,
        historical_kind_set_resolved=FALSE_TOKEN,
        historical_unknown_on_critical_path=FALSE_TOKEN,
        ratified_live_source_kinds=NONE_TOKEN,
        kinds_invented_this_go=FALSE_TOKEN,
    )


def join_live_critical_path_to_d6_diagnostics_v1(
    *,
    existing: Mapping[str, Any],
    items: Sequence[LiveCriticalPathItemAdjudicationV1],
    boundary: LiveCriticalKindSetBoundaryV1,
) -> dict[str, Any]:
    attached = dict(existing)
    additions = {
        "LIVE_CRITICAL_KIND_SET_IDENTITY": boundary.definition_id,
        "LIVE_CRITICAL_KIND_SET": boundary.live_critical_kind_set,
        "LIVE_CRITICAL_KIND_SET_RESOLVED": boundary.live_critical_kind_set_resolved,
        "LIVE_CRITICAL_DEFINITION_CLASS": boundary.definition_class,
        "HISTORICAL_UNKNOWN_ON_CRITICAL_PATH": boundary.historical_unknown_on_critical_path,
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "KINDS_INVENTED_THIS_GO": boundary.kinds_invented_this_go,
        "LIVE_CRITICAL_ITEM_COUNT": str(len(items)),
        "VENUE_POST_COUNT": "0",
    }
    for key, value in additions.items():
        if key in attached and attached[key] != value:
            raise LiveCriticalPathNextBlockerError(f"DIAGNOSTIC_AUTHORITY_COLLISION:{key}")
        attached[key] = value
    return attached


def execute_live_critical_path_next_blocker_bounded_wp1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bl_pack: Path,
    evidence_root: Path,
    persist_as_of: str,
) -> LiveCriticalPathNextBlockerResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise LiveCriticalPathNextBlockerError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise LiveCriticalPathNextBlockerError("ORIGIN_MAIN_SHA_MISMATCH")
    bl_pack = Path(sealed_bl_pack)
    try:
        manifest_rc = verify_manifest_sha256_v1(store_root=bl_pack)
    except Exception as exc:
        raise LiveCriticalPathNextBlockerError("BL_MANIFEST_VERIFY_FAILED") from exc
    if manifest_rc != 0:
        raise LiveCriticalPathNextBlockerError("BL_MANIFEST_VERIFY_FAILED")
    claims_path = bl_pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise LiveCriticalPathNextBlockerError("BL_CLAIMS_MISSING")
    try:
        bl_claims = _load_json_object(path=claims_path)
    except json.JSONDecodeError as exc:
        raise LiveCriticalPathNextBlockerError("BL_CLAIMS_MALFORMED") from exc
    _require_token(field="KIND_SET", payload=bl_claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=bl_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_A_EXECUTED", payload=bl_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bl_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bl_claims, expected="0")
    _require_token(field="VENUE_POST_COUNT", payload=bl_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bl_claims, expected=FALSE_TOKEN)
    _require_token(field="CONSUMPTION_ADMITTED", payload=bl_claims, expected=FALSE_TOKEN)
    _require_token(field="UNKNOWN_SEMANTICS_INVENTED", payload=bl_claims, expected=FALSE_TOKEN)
    records = records_from_bj_semantics_claims_v1(bl_claims)
    consumed = consume_bj_remaining_unknown_kind_semantics_v1(
        records=records,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=False,
    )
    for item in consumed:
        if item.bj_decision != DECISION_REMAIN_UNKNOWN:
            raise LiveCriticalPathNextBlockerError(
                f"HISTORICAL_FACT_NOT_REMAIN_UNKNOWN:{item.fact_id}"
            )
        if item.admitted == TRUE_TOKEN:
            raise LiveCriticalPathNextBlockerError(f"HISTORICAL_FACT_ADMITTED:{item.fact_id}")
        reject_claimed_live_critical_path_authority_mutation_v1(
            claimed_proof="TYPED_UNRESOLVED_REMAIN_UNKNOWN",
            fact_id=item.fact_id,
        )
    reject_claimed_live_critical_path_authority_mutation_v1(
        claimed_proof="NEW_CANONICAL_DEFINITION_EMPTY_FAIL_CLOSED",
        fact_id=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    )
    reject_claimed_live_critical_path_authority_mutation_v1(
        claimed_proof="HISTORICAL_UNKNOWN_NOT_LIVE_KIND_SET_MEMBER",
        fact_id=FACT_F12,
    )
    items = build_live_critical_path_item_adjudications_v1()
    boundary = build_live_critical_kind_set_boundary_v1()
    standing = {
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
    }
    diagnostics = join_live_critical_path_to_d6_diagnostics_v1(
        existing=standing,
        items=items,
        boundary=boundary,
    )
    folder = _folder_from_as_of(persist_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": "NONE",
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": persist_as_of,
        "SEALED_BL_PACK": CANONICAL_BL_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "BL_CONTRACT_REUSED": TRUE_TOKEN,
        "VENUE_GET_COUNT": "0",
        "VENUE_POST_COUNT": "0",
        "POST_COUNT": "0",
        "GATE_A_EXECUTED": FALSE_TOKEN,
        "GATE_B_EXECUTED": FALSE_TOKEN,
        "UNKNOWN_SEMANTICS_INVENTED": FALSE_TOKEN,
        "KINDS_INVENTED_THIS_GO": FALSE_TOKEN,
        "HISTORICAL_UNKNOWN_ON_CRITICAL_PATH": FALSE_TOKEN,
        "LIVE_CRITICAL_DEFINITION_CLASS": boundary.definition_class,
        "LIVE_CRITICAL_KIND_SET_IDENTITY": boundary.definition_id,
        "LIVE_CRITICAL_KIND_SET": boundary.live_critical_kind_set,
        "LIVE_CRITICAL_KIND_SET_RESOLVED": FALSE_TOKEN,
        "RATIFIED_LIVE_SOURCE_KINDS": NONE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": HISTORICAL_KIND_SET_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": HISTORICAL_D6_BLOCKER,
        "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER": EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "F12_STATUS": "UNRESOLVED",
        "F13_STATUS": "UNRESOLVED",
        "U05_STATUS": "UNRESOLVED",
        "F16_STATUS": "UNRESOLVED",
        "F17_STATUS": "UNRESOLVED",
        "F18_STATUS": "UNRESOLVED",
        "F12_DECISION": DECISION_REMAIN_UNKNOWN,
        "F13_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "F16_DECISION": DECISION_REMAIN_UNKNOWN,
        "F17_DECISION": DECISION_REMAIN_UNKNOWN,
        "F18_DECISION": DECISION_REMAIN_UNKNOWN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "BULL_BEAR_STATE_SWITCH_UNCHANGED": TRUE_TOKEN,
        "TOP20_RANKING_UNIVERSE_UNCHANGED": TRUE_TOKEN,
        "TOP20_SELECTION_BINDINGS_UNCHANGED": TRUE_TOKEN,
        "SELF_LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_AUTONOMY_UNCHANGED": TRUE_TOKEN,
        "STEP_29P_UNCHANGED": TRUE_TOKEN,
        "BL_MANIFEST_VERIFY_RC": "0",
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "adjudication_v1.json",
        payload={
            item.item_id: {
                "classification": item.classification,
                "layer": item.layer,
                "reconstruct_historical_unknown": item.reconstruct_historical_unknown,
                "live_kind_set_member": item.live_kind_set_member,
                "rationale": item.rationale,
            }
            for item in items
        },
    )
    _persist_json(
        path=store / "live_kind_set_boundary_v1.json",
        payload={
            "definition_class": boundary.definition_class,
            "definition_id": boundary.definition_id,
            "live_critical_kind_set": boundary.live_critical_kind_set,
            "live_critical_kind_set_resolved": boundary.live_critical_kind_set_resolved,
            "historical_kind_set": boundary.historical_kind_set,
            "historical_kind_set_resolved": boundary.historical_kind_set_resolved,
            "historical_unknown_on_critical_path": boundary.historical_unknown_on_critical_path,
            "ratified_live_source_kinds": boundary.ratified_live_source_kinds,
            "kinds_invented_this_go": boundary.kinds_invented_this_go,
        },
    )
    _persist_json(path=store / "d6_diagnostics_v1.json", payload=diagnostics)
    _persist_json(
        path=store / "layers_v1.json",
        payload={
            LAYER_CANONICAL: "claims.json,live_kind_set_boundary_v1.json",
            LAYER_FORENSIC: "NONE_NEW_THIS_GO",
            LAYER_ADJUDICATED: "adjudication_v1.json",
            LAYER_HISTORICAL: CANONICAL_BL_PACK_RELPATH,
            LAYER_NAVIGATION: "NONE",
            LAYER_INTERPRETATION: "FORBIDDEN",
            LAYER_HYPOTHESIS: "FORBIDDEN",
            LAYER_OPEN: "NONE_ON_SEALED_BL_PIN",
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "reconstruct_historical_unknown": "FORBIDDEN",
            "invent_live_source_kind": "FORBIDDEN",
            "empty_historical_kind_set": KIND_SET_EMPTY,
            "live_critical_kind_set": LIVE_CRITICAL_KIND_SET,
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "venue_get_count": "0",
            "venue_post_count": "0",
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bl_pack": CANONICAL_BL_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "persist_as_of": persist_as_of,
            "owner_go": OWNER_GO,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return LiveCriticalPathNextBlockerResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=persist_as_of,
        store_root=str(store),
        historical_unknown_on_critical_path=FALSE_TOKEN,
        live_critical_kind_set=LIVE_CRITICAL_KIND_SET,
        live_critical_kind_set_resolved=FALSE_TOKEN,
        earliest_live_critical_path_blocker=EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
        earliest_remaining_d6_blocker=HISTORICAL_D6_BLOCKER,
        next_owner_go_required=NEXT_OWNER_GO_REQUIRED,
        venue_get_count="0",
        venue_post_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
        kinds_invented_this_go=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "CLASS_ALREADY_CLOSED",
    "CLASS_DOWNSTREAM",
    "CLASS_HISTORICAL",
    "CLASS_LIVE_CRITICAL",
    "EARLIEST_LIVE_CRITICAL_PATH_BLOCKER",
    "LIVE_CRITICAL_KIND_SET",
    "LIVE_CRITICAL_KIND_SET_IDENTITY",
    "LiveCriticalKindSetBoundaryV1",
    "LiveCriticalPathItemAdjudicationV1",
    "LiveCriticalPathNextBlockerError",
    "LiveCriticalPathNextBlockerResultV1",
    "NEW_CANONICAL_DEFINITION_ID",
    "NEXT_OWNER_GO_REQUIRED",
    "OWNER_GO",
    "build_live_critical_kind_set_boundary_v1",
    "build_live_critical_path_item_adjudications_v1",
    "execute_live_critical_path_next_blocker_bounded_wp1",
    "join_live_critical_path_to_d6_diagnostics_v1",
    "reject_claimed_live_critical_path_authority_mutation_v1",
]
