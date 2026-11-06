"""D6 BK bounded consumption of sealed BJ remaining-unknown kind semantics.

Consumes typed BJ fact records. Does not re-evaluate INCLUDE/EXCLUDE
authority. Does not GET. Does not POST. Does not execute GATE_A or GATE_B.
Empty KIND_SET remains EMPTY_FAIL_CLOSED. AUTHORITY_EFFECT=NONE.

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
    CANONICAL_PACK_RELPATH as CANONICAL_BJ_SEMANTICS_PACK_RELPATH,
    CLAIMS_FILE,
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
    LAYER_ADJUDICATED,
    LAYER_OPEN_OR_CONTRADICTORY,
    NONE_TOKEN,
    REASON_CONTRADICTORY_TYPED_CLAIMS,
    REASON_MALFORMED_RECORD,
    REASON_MISSING_RECORD,
    STATUS_CONTRADICTORY,
    STATUS_MALFORMED,
    STATUS_MISSING,
    STATUS_RESOLVED,
    STATUS_UNRESOLVED,
    TRUE_TOKEN,
    BjFactSemanticsRecordV1,
    attach_bj_semantics_to_d6_diagnostics_v1,
    evaluate_bj_remaining_unknown_kind_semantics_v1,
    reject_claimed_bj_semantics_authority_mutation_v1,
    select_precedent_reason_code_v1,
    select_precedent_status_v1,
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
    EARLIEST_REMAINING_D6_BLOCKER as BJ_PIN_EARLIEST_REMAINING_D6_BLOCKER,
    KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY as BJ_KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_D6_BK_BOUNDED_IMPLEMENTATION_WP1"
EXPECTED_ORIGIN_MAIN_SHA = "ffe54a4bf2b224d990e7c0701cf3ba8733eab42f"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_d6_bk_bounded_implementation_wp1/2026-09-14T070000Z"
)
CONSUMPTION_NOT_ADMITTED = "FAIL_CLOSED_NOT_ADMITTED"
CLAIM_STATUS_FIELDS: dict[str, tuple[str, str, str]] = {
    FACT_F12: ("F12_STATUS", "F12_DECISION", "F12_REASON_CODE"),
    FACT_F13: ("F13_STATUS", "F13_DECISION", "F13_REASON_CODE"),
    FACT_U05: ("U05_STATUS", "U05_KIND_DECISION", "U05_REASON_CODE"),
    FACT_F16: ("F16_STATUS", "F16_DECISION", "F16_REASON_CODE"),
    FACT_F17: ("F17_STATUS", "F17_DECISION", "F17_REASON_CODE"),
    FACT_F18: ("F18_STATUS", "F18_DECISION", "F18_REASON_CODE"),
}


class BkBjSemanticsConsumptionError(ValueError):
    """Fail-closed BK consumption of BJ remaining-unknown kind semantics."""


@dataclass(frozen=True)
class BkFactConsumptionRecordV1:
    fact_id: str
    bj_status: str
    bj_decision: str
    bj_reason_code: str
    consumption_status: str
    admitted: str
    source_kind_admissible: str
    layer: str
    replay_matched: str


@dataclass(frozen=True)
class BkBoundedImplementationResultV1:
    genesis_id: str
    genesis_as_of: str
    consumption_as_of: str
    store_root: str
    f12_status: str
    f13_status: str
    u05_status: str
    f16_status: str
    f17_status: str
    f18_status: str
    f12_decision: str
    f13_decision: str
    u05_decision: str
    f16_decision: str
    f17_decision: str
    f18_decision: str
    aggregate_status: str
    aggregate_reason_code: str
    consumption_admitted: str
    kind_set: str
    kind_set_resolved: str
    venue_get_count: str
    venue_post_count: str
    gate_a_executed: str
    gate_b_executed: str
    unknown_semantics_invented: str
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
        raise BkBjSemanticsConsumptionError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise BkBjSemanticsConsumptionError(f"{field}_DRIFT:{actual}")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise BkBjSemanticsConsumptionError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise BkBjSemanticsConsumptionError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise BkBjSemanticsConsumptionError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise BkBjSemanticsConsumptionError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise BkBjSemanticsConsumptionError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise BkBjSemanticsConsumptionError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )


def records_from_bj_semantics_claims_v1(claims: Mapping[str, Any]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for fact_id, (status_field, decision_field, _reason_field) in CLAIM_STATUS_FIELDS.items():
        records.append(
            {
                "fact_id": fact_id,
                "claimed_status": str(claims.get(status_field) or ""),
                "claimed_decision": str(claims.get(decision_field) or ""),
                "evidence_class": CURRENTLY_DECISION_CAPABLE,
                "layer": LAYER_ADJUDICATED,
            }
        )
    return records


def _admitted(*, record: BjFactSemanticsRecordV1) -> str:
    if record.status == STATUS_RESOLVED and record.source_kind_admissible == TRUE_TOKEN:
        return TRUE_TOKEN
    return FALSE_TOKEN


def consume_bj_remaining_unknown_kind_semantics_v1(
    *,
    records: Sequence[Mapping[str, Any]],
    kind_set: str = KIND_SET_EMPTY,
    kind_set_resolved: bool = False,
    ratified_source_kinds: Sequence[str] = (),
    gate_a_executed: bool = False,
    gate_b_executed: bool = False,
    claimed_by_fact: Mapping[str, Mapping[str, str]] | None = None,
) -> tuple[BkFactConsumptionRecordV1, ...]:
    _assert_standing_pins()
    if gate_a_executed or gate_b_executed:
        raise BkBjSemanticsConsumptionError("GATE_EXECUTION_FORBIDDEN_IN_THIS_LAYER")
    evaluated = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=records,
        kind_set=kind_set,
        kind_set_resolved=kind_set_resolved,
        ratified_source_kinds=ratified_source_kinds,
        gate_a_executed=False,
        gate_b_executed=False,
    )
    consumed: list[BkFactConsumptionRecordV1] = []
    claimed = claimed_by_fact or {}
    for record in evaluated:
        replay_matched = TRUE_TOKEN
        consumption_status = record.status
        layer = record.layer
        if record.fact_id in claimed:
            claimed_record = claimed[record.fact_id]
            claimed_status = str(claimed_record.get("status") or "")
            claimed_decision = str(claimed_record.get("decision") or "")
            claimed_reason = str(claimed_record.get("reason_code") or "")
            if (
                claimed_status != record.status
                or claimed_decision != record.decision
                or (claimed_reason and claimed_reason != record.reason_code)
            ):
                replay_matched = FALSE_TOKEN
                consumption_status = STATUS_CONTRADICTORY
                layer = LAYER_OPEN_OR_CONTRADICTORY
        consumed.append(
            BkFactConsumptionRecordV1(
                fact_id=record.fact_id,
                bj_status=record.status,
                bj_decision=record.decision,
                bj_reason_code=record.reason_code,
                consumption_status=consumption_status,
                admitted=_admitted(record=record),
                source_kind_admissible=record.source_kind_admissible,
                layer=layer,
                replay_matched=replay_matched,
            )
        )
    return tuple(consumed)


def join_bk_consumption_to_d6_diagnostics_v1(
    *,
    existing: Mapping[str, Any],
    bj_records: Sequence[BjFactSemanticsRecordV1],
    consumed: Sequence[BkFactConsumptionRecordV1],
    kind_set: str,
    kind_set_resolved: str,
    venue_get_count: str,
    gate_a_executed: str,
    gate_b_executed: str,
) -> dict[str, Any]:
    attached = attach_bj_semantics_to_d6_diagnostics_v1(
        existing=existing,
        records=bj_records,
        kind_set=kind_set,
        kind_set_resolved=kind_set_resolved,
        venue_get_count=venue_get_count,
        gate_a_executed=gate_a_executed,
        gate_b_executed=gate_b_executed,
    )
    by_fact = {item.fact_id: item for item in consumed}
    additions = {
        "BK_CONSUMPTION_ADMITTED": (
            TRUE_TOKEN if all(item.admitted == TRUE_TOKEN for item in consumed) else FALSE_TOKEN
        ),
        "BK_CONSUMPTION_AGGREGATE_STATUS": select_precedent_status_v1(
            tuple(item.consumption_status for item in consumed)
        ),
        "BK_F12_CONSUMPTION_STATUS": by_fact[FACT_F12].consumption_status,
        "BK_F13_CONSUMPTION_STATUS": by_fact[FACT_F13].consumption_status,
        "BK_U05_CONSUMPTION_STATUS": by_fact[FACT_U05].consumption_status,
        "BK_F16_CONSUMPTION_STATUS": by_fact[FACT_F16].consumption_status,
        "BK_F17_CONSUMPTION_STATUS": by_fact[FACT_F17].consumption_status,
        "BK_F18_CONSUMPTION_STATUS": by_fact[FACT_F18].consumption_status,
        "BK_REPLAY_MATCHED": (
            TRUE_TOKEN
            if all(item.replay_matched == TRUE_TOKEN for item in consumed)
            else FALSE_TOKEN
        ),
        "UNKNOWN_SEMANTICS_INVENTED": FALSE_TOKEN,
        "VENUE_POST_COUNT": "0",
    }
    for key, value in additions.items():
        if key in attached and attached[key] != value:
            raise BkBjSemanticsConsumptionError(f"DIAGNOSTIC_AUTHORITY_COLLISION:{key}")
        attached[key] = value
    return attached


def reject_claimed_bk_authority_mutation_v1(*, claimed_proof: str, fact_id: str) -> None:
    forbidden = {
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "EXECUTE_GATE_B",
        "HOPE_BALANCE_GET",
        "VENUE_POST",
        "KIND_SET_RESOLVED_TRUE",
        "D6_FULLY_CLOSED",
        "ADMIT_UNRESOLVED_AS_SOURCE_KIND",
        "NORMALIZE_UNKNOWN_TO_INCLUDE",
        "NORMALIZE_UNKNOWN_TO_EXCLUDE",
        "RESTORE_LEGACY_EQUITY_LOGIC",
    }
    if claimed_proof in forbidden:
        raise BkBjSemanticsConsumptionError(f"BK_CONSUMPTION_CANNOT_{claimed_proof}:{fact_id}")
    reject_claimed_bj_semantics_authority_mutation_v1(
        claimed_proof=claimed_proof,
        fact_id=fact_id,
    )


def execute_bk_bounded_implementation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bj_semantics_pack: Path,
    evidence_root: Path,
    consumption_as_of: str,
) -> BkBoundedImplementationResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise BkBjSemanticsConsumptionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise BkBjSemanticsConsumptionError("ORIGIN_MAIN_SHA_MISMATCH")
    bj_pack = Path(sealed_bj_semantics_pack)
    try:
        manifest_rc = verify_manifest_sha256_v1(store_root=bj_pack)
    except Exception as exc:
        raise BkBjSemanticsConsumptionError("BJ_SEMANTICS_MANIFEST_VERIFY_FAILED") from exc
    if manifest_rc != 0:
        raise BkBjSemanticsConsumptionError("BJ_SEMANTICS_MANIFEST_VERIFY_FAILED")
    claims_path = bj_pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise BkBjSemanticsConsumptionError("BJ_SEMANTICS_CLAIMS_MISSING")
    try:
        bj_claims = _load_json_object(path=claims_path)
    except json.JSONDecodeError as exc:
        raise BkBjSemanticsConsumptionError("BJ_SEMANTICS_CLAIMS_MALFORMED") from exc
    _require_token(field="KIND_SET", payload=bj_claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_A_EXECUTED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bj_claims, expected="0")
    _require_token(field="POST_COUNT", payload=bj_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(field="UNKNOWN_SEMANTICS_INVENTED", payload=bj_claims, expected=FALSE_TOKEN)
    records = records_from_bj_semantics_claims_v1(bj_claims)
    bj_records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=records,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=False,
        ratified_source_kinds=(),
        gate_a_executed=False,
        gate_b_executed=False,
    )
    claimed_by_fact = {
        fact_id: {
            "status": str(bj_claims.get(status_field) or ""),
            "decision": str(bj_claims.get(decision_field) or ""),
            "reason_code": str(bj_claims.get(reason_field) or ""),
        }
        for fact_id, (status_field, decision_field, reason_field) in CLAIM_STATUS_FIELDS.items()
    }
    consumed = consume_bj_remaining_unknown_kind_semantics_v1(
        records=records,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=False,
        claimed_by_fact=claimed_by_fact,
    )
    by_fact = {item.fact_id: item for item in consumed}
    standing = {
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
    }
    diagnostics = join_bk_consumption_to_d6_diagnostics_v1(
        existing=standing,
        bj_records=bj_records,
        consumed=consumed,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        venue_get_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
    )
    folder = _folder_from_as_of(consumption_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    consumption_payload = {
        item.fact_id: {
            "bj_status": item.bj_status,
            "bj_decision": item.bj_decision,
            "bj_reason_code": item.bj_reason_code,
            "consumption_status": item.consumption_status,
            "admitted": item.admitted,
            "source_kind_admissible": item.source_kind_admissible,
            "layer": item.layer,
            "replay_matched": item.replay_matched,
        }
        for item in consumed
    }
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": "NONE",
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "CONSUMPTION_AS_OF": consumption_as_of,
        "SEALED_BJ_SEMANTICS_PACK": CANONICAL_BJ_SEMANTICS_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "BJ_CONTRACT_REUSED": TRUE_TOKEN,
        "VENUE_GET_COUNT": "0",
        "VENUE_POST_COUNT": "0",
        "POST_COUNT": "0",
        "GATE_A_EXECUTED": FALSE_TOKEN,
        "GATE_B_EXECUTED": FALSE_TOKEN,
        "UNKNOWN_SEMANTICS_INVENTED": FALSE_TOKEN,
        "F12_STATUS": by_fact[FACT_F12].bj_status,
        "F13_STATUS": by_fact[FACT_F13].bj_status,
        "U05_STATUS": by_fact[FACT_U05].bj_status,
        "F16_STATUS": by_fact[FACT_F16].bj_status,
        "F17_STATUS": by_fact[FACT_F17].bj_status,
        "F18_STATUS": by_fact[FACT_F18].bj_status,
        "F12_DECISION": by_fact[FACT_F12].bj_decision,
        "F13_DECISION": by_fact[FACT_F13].bj_decision,
        "U05_KIND_DECISION": by_fact[FACT_U05].bj_decision,
        "F16_DECISION": by_fact[FACT_F16].bj_decision,
        "F17_DECISION": by_fact[FACT_F17].bj_decision,
        "F18_DECISION": by_fact[FACT_F18].bj_decision,
        "F12_CONSUMPTION_STATUS": by_fact[FACT_F12].consumption_status,
        "F13_CONSUMPTION_STATUS": by_fact[FACT_F13].consumption_status,
        "U05_CONSUMPTION_STATUS": by_fact[FACT_U05].consumption_status,
        "F16_CONSUMPTION_STATUS": by_fact[FACT_F16].consumption_status,
        "F17_CONSUMPTION_STATUS": by_fact[FACT_F17].consumption_status,
        "F18_CONSUMPTION_STATUS": by_fact[FACT_F18].consumption_status,
        "AGGREGATE_STATUS": diagnostics["BK_CONSUMPTION_AGGREGATE_STATUS"],
        "AGGREGATE_REASON_CODE": diagnostics["BJ_SEMANTICS_AGGREGATE_REASON_CODE"],
        "CONSUMPTION_ADMITTED": diagnostics["BK_CONSUMPTION_ADMITTED"],
        "BK_REPLAY_MATCHED": diagnostics["BK_REPLAY_MATCHED"],
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": BJ_KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": BJ_PIN_EARLIEST_REMAINING_D6_BLOCKER,
        "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13": CURRENTLY_DECISION_CAPABLE,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "EXISTING_NON_SOURCE_AND_OTHER_DOMAIN_UNCHANGED": TRUE_TOKEN,
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
        "BJ_SEMANTICS_MANIFEST_VERIFY_RC": "0",
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "consumption_v1.json", payload=consumption_payload)
    _persist_json(path=store / "d6_diagnostics_v1.json", payload=diagnostics)
    _persist_json(
        path=store / "layers_v1.json",
        payload={
            "CANONICAL_AUTHORITY": "claims.json,d6_diagnostics_v1.json",
            "FORENSIC_RAW": "NONE_NEW_THIS_GO",
            "ADJUDICATED_CONCLUSION": "consumption_v1.json",
            "HISTORICAL_INTERMEDIATE": CANONICAL_BJ_SEMANTICS_PACK_RELPATH,
            "NAVIGATION_ONLY": "NONE",
            "INTERPRETATION": "FORBIDDEN",
            "HYPOTHESIS": "FORBIDDEN",
            "OPEN_OR_CONTRADICTORY": "NONE_ON_SEALED_BJ_SEMANTICS_PIN",
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "empty_kind_set": KIND_SET_EMPTY,
            "unratified_kind": "NO_ADMISSIBLE_SOURCE_KIND",
            "consumption_admitted": CONSUMPTION_NOT_ADMITTED,
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "venue_get_count": "0",
            "venue_post_count": "0",
            "unknown_semantics_invented": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bj_semantics_pack": CANONICAL_BJ_SEMANTICS_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "consumption_as_of": consumption_as_of,
            "owner_go": OWNER_GO,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    return BkBoundedImplementationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        consumption_as_of=consumption_as_of,
        store_root=str(store),
        f12_status=by_fact[FACT_F12].bj_status,
        f13_status=by_fact[FACT_F13].bj_status,
        u05_status=by_fact[FACT_U05].bj_status,
        f16_status=by_fact[FACT_F16].bj_status,
        f17_status=by_fact[FACT_F17].bj_status,
        f18_status=by_fact[FACT_F18].bj_status,
        f12_decision=by_fact[FACT_F12].bj_decision,
        f13_decision=by_fact[FACT_F13].bj_decision,
        u05_decision=by_fact[FACT_U05].bj_decision,
        f16_decision=by_fact[FACT_F16].bj_decision,
        f17_decision=by_fact[FACT_F17].bj_decision,
        f18_decision=by_fact[FACT_F18].bj_decision,
        aggregate_status=str(diagnostics["BK_CONSUMPTION_AGGREGATE_STATUS"]),
        aggregate_reason_code=str(diagnostics["BJ_SEMANTICS_AGGREGATE_REASON_CODE"]),
        consumption_admitted=str(diagnostics["BK_CONSUMPTION_ADMITTED"]),
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        venue_get_count="0",
        venue_post_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
        unknown_semantics_invented=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )


__all__ = [
    "BkBjSemanticsConsumptionError",
    "BkBoundedImplementationResultV1",
    "BkFactConsumptionRecordV1",
    "consume_bj_remaining_unknown_kind_semantics_v1",
    "execute_bk_bounded_implementation_v1",
    "join_bk_consumption_to_d6_diagnostics_v1",
    "records_from_bj_semantics_claims_v1",
    "reject_claimed_bk_authority_mutation_v1",
    "REASON_CONTRADICTORY_TYPED_CLAIMS",
    "REASON_MALFORMED_RECORD",
    "REASON_MISSING_RECORD",
    "STATUS_CONTRADICTORY",
    "STATUS_MALFORMED",
    "STATUS_MISSING",
    "STATUS_RESOLVED",
    "STATUS_UNRESOLVED",
]
