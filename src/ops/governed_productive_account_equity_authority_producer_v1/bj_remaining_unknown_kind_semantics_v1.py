"""D6 BJ remaining-unknown kind semantics layer.

Typed fail-closed status/reason evaluation for F12, F13, U05, F16, F17,
and F18. Does not GET. Does not POST. Does not execute GATE_A or GATE_B.
Does not invent venue field semantics. Empty KIND_SET remains
EMPTY_FAIL_CLOSED. AUTHORITY_EFFECT=NONE.

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
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    UNKNOWN_EMBEDDING_FACTS,
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
    CANONICAL_PACK_RELPATH as CANONICAL_BJ_PACK_RELPATH,
    CURRENTLY_DECISION_CAPABLE,
    EARLIEST_REMAINING_D6_BLOCKER as BJ_EARLIEST_REMAINING_D6_BLOCKER,
    GATE_A_ID,
    GATE_B_ID,
    KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY as BJ_KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = "OWNER_GO_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION_WP1"
EXPECTED_ORIGIN_MAIN_SHA = "6ed3c97a361b30f46b9ccfc0dbb62408eae03855"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_d6_bj_semantics_bounded_implementation_wp1/2026-09-14T061500Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
CLAIMS_FILE = "claims.json"

FACT_F12 = "F12"
FACT_F13 = "F13"
FACT_U05 = "U05"
FACT_F16 = "F16"
FACT_F17 = "F17"
FACT_F18 = "F18"
FACT_IDS: tuple[str, ...] = (
    FACT_F12,
    FACT_F13,
    FACT_U05,
    FACT_F16,
    FACT_F17,
    FACT_F18,
)
FACT_TO_EMBEDDING: dict[str, str] = {
    FACT_F12: "F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    FACT_F13: "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
    FACT_U05: "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND",
    FACT_F16: "F16_FEE_ALREADY_EMBEDDED_IN_EQ",
    FACT_F17: "F17_FEE_SEPARATE_ACCOUNT_DELTA",
    FACT_F18: "F18_FEE_RECONCILIATION_ONLY",
}

STATUS_RESOLVED = "RESOLVED"
STATUS_UNRESOLVED = "UNRESOLVED"
STATUS_MISSING = "MISSING"
STATUS_MALFORMED = "MALFORMED"
STATUS_CONTRADICTORY = "CONTRADICTORY"
STATUS_UNKNOWN_ALIAS = "UNKNOWN"
TYPED_STATUSES: frozenset[str] = frozenset(
    {
        STATUS_RESOLVED,
        STATUS_UNRESOLVED,
        STATUS_MISSING,
        STATUS_MALFORMED,
        STATUS_CONTRADICTORY,
        STATUS_UNKNOWN_ALIAS,
    }
)
DECISION_INCLUDE = "INCLUDE"
DECISION_EXCLUDE = "EXCLUDE"
TYPED_DECISIONS: frozenset[str] = frozenset(
    {DECISION_REMAIN_UNKNOWN, DECISION_INCLUDE, DECISION_EXCLUDE}
)

LAYER_CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
LAYER_FORENSIC_RAW = "FORENSIC_RAW_EVIDENCE"
LAYER_ADJUDICATED = "ADJUDICATED_CONCLUSION"
LAYER_HISTORICAL = "HISTORICAL_INTERMEDIATE"
LAYER_NAVIGATION = "NAVIGATION_ONLY"
LAYER_INTERPRETATION = "INTERPRETATION"
LAYER_HYPOTHESIS = "HYPOTHESIS"
LAYER_OPEN_OR_CONTRADICTORY = "OPEN_OR_CONTRADICTORY"
FORBIDDEN_AUTHORITY_LAYERS: frozenset[str] = frozenset(
    {LAYER_INTERPRETATION, LAYER_HYPOTHESIS, LAYER_NAVIGATION}
)

REASON_CONTRADICTORY_TYPED_CLAIMS = "CONTRADICTORY_TYPED_CLAIMS"
REASON_MALFORMED_RECORD = "MALFORMED_RECORD"
REASON_MISSING_RECORD = "MISSING_RECORD"
REASON_CLAIMED_INCLUDE_EMPTY_KIND_SET = "CLAIMED_INCLUDE_WITH_EMPTY_KIND_SET"
REASON_CLAIMED_INCLUDE_UNRATIFIED_KIND = "CLAIMED_INCLUDE_WITH_UNRATIFIED_KIND"
REASON_CLAIMED_EXCLUDE_NOT_RATIFIED_NON_SOURCE = (
    "CLAIMED_EXCLUDE_WITHOUT_RATIFIED_NON_SOURCE_OR_OTHER_DOMAIN"
)
REASON_CLAIMED_RESOLVED_NO_DECISION_CLASS = (
    "CLAIMED_RESOLVED_WITHOUT_DECISION_CAPABLE_EVIDENCE_CLASS"
)
REASON_NO_DECISION_CAPABLE_CLASS = "NO_CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASS"
REASON_KIND_SET_EMPTY = "KIND_SET_EMPTY_FAIL_CLOSED"
REASON_RESOLVED_INCLUDE_ADMISSIBLE = "RESOLVED_INCLUDE_ADMISSIBLE"
REASON_RESOLVED_EXCLUDE_ADMISSIBLE = "RESOLVED_EXCLUDE_ADMISSIBLE"

REASON_PRECEDENCE: tuple[str, ...] = (
    REASON_CONTRADICTORY_TYPED_CLAIMS,
    REASON_MALFORMED_RECORD,
    REASON_MISSING_RECORD,
    REASON_CLAIMED_INCLUDE_EMPTY_KIND_SET,
    REASON_CLAIMED_INCLUDE_UNRATIFIED_KIND,
    REASON_CLAIMED_EXCLUDE_NOT_RATIFIED_NON_SOURCE,
    REASON_CLAIMED_RESOLVED_NO_DECISION_CLASS,
    REASON_NO_DECISION_CAPABLE_CLASS,
    REASON_KIND_SET_EMPTY,
    REASON_RESOLVED_INCLUDE_ADMISSIBLE,
    REASON_RESOLVED_EXCLUDE_ADMISSIBLE,
)
_REASON_RANK = {code: index for index, code in enumerate(REASON_PRECEDENCE)}
STATUS_PRECEDENCE: tuple[str, ...] = (
    STATUS_CONTRADICTORY,
    STATUS_MALFORMED,
    STATUS_MISSING,
    STATUS_UNRESOLVED,
    STATUS_RESOLVED,
)
_STATUS_RANK = {code: index for index, code in enumerate(STATUS_PRECEDENCE)}

FUTURE_ADMISSIBLE_EVIDENCE_CLASSES: frozenset[str] = frozenset({GATE_A_ID, GATE_B_ID})
RATIFIED_NON_SOURCE_OR_OTHER_DOMAIN_IDS: frozenset[str] = frozenset({"eq"})
STANDING_D6_DIAGNOSTIC_KEYS: tuple[str, ...] = (
    "KIND_SET_RESOLVED",
    "D6_FULLY_CLOSED",
    "D7_AUTHORIZED",
    "MS2_AUTHORIZED",
    "RAW_EQ_SOURCE_AUTHORITY",
    "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY",
    "U05_KIND_DECISION",
)


class BjRemainingUnknownKindSemanticsError(ValueError):
    """Fail-closed BJ remaining-unknown kind-semantics violation."""


@dataclass(frozen=True)
class BjFactSemanticsRecordV1:
    fact_id: str
    status: str
    decision: str
    reason_code: str
    evidence_class: str
    layer: str
    embedding_fact: str
    source_kind_admissible: str


@dataclass(frozen=True)
class BjRemainingUnknownKindSemanticsResultV1:
    genesis_id: str
    genesis_as_of: str
    semantics_as_of: str
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
    f12_reason_code: str
    f13_reason_code: str
    u05_reason_code: str
    f16_reason_code: str
    f17_reason_code: str
    f18_reason_code: str
    aggregate_status: str
    aggregate_reason_code: str
    kind_set: str
    kind_set_resolved: str
    venue_get_count: str
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
        raise BjRemainingUnknownKindSemanticsError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise BjRemainingUnknownKindSemanticsError(f"{field}_DRIFT:{actual}")


def _assert_standing_pins() -> None:
    if KIND_SET_RESOLVED is not False:
        raise BjRemainingUnknownKindSemanticsError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET or RATIFIED_SOURCE_KIND_SET:
        raise BjRemainingUnknownKindSemanticsError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if MS2_AUTHORIZED is not False:
        raise BjRemainingUnknownKindSemanticsError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise BjRemainingUnknownKindSemanticsError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise BjRemainingUnknownKindSemanticsError("D7_AUTHORIZED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise BjRemainingUnknownKindSemanticsError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    reject_unratified_equity_stock_source_kind_v1(
        event_kind=NONE_TOKEN,
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )


def select_precedent_reason_code_v1(reason_codes: Sequence[str]) -> str:
    if not reason_codes:
        raise BjRemainingUnknownKindSemanticsError("REASON_CODES_EMPTY")
    unknown = [code for code in reason_codes if code not in _REASON_RANK]
    if unknown:
        raise BjRemainingUnknownKindSemanticsError(f"REASON_CODE_UNKNOWN:{unknown[0]}")
    return min(reason_codes, key=lambda code: _REASON_RANK[code])


def select_precedent_status_v1(statuses: Sequence[str]) -> str:
    if not statuses:
        raise BjRemainingUnknownKindSemanticsError("STATUSES_EMPTY")
    unknown = [status for status in statuses if status not in _STATUS_RANK]
    if unknown:
        raise BjRemainingUnknownKindSemanticsError(f"STATUS_UNKNOWN:{unknown[0]}")
    return min(statuses, key=lambda status: _STATUS_RANK[status])


def _normalize_optional_token(*, field: str, raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise BjRemainingUnknownKindSemanticsError(f"{field}_NOT_STRING")
    if raw != raw.strip() or raw == "":
        raise BjRemainingUnknownKindSemanticsError(f"{field}_MALFORMED")
    return raw


def _source_kind_admissible(*, fact_id: str, kind_set: str, kind_set_resolved: bool) -> str:
    if kind_set != KIND_SET_EMPTY:
        return FALSE_TOKEN
    if kind_set_resolved:
        return FALSE_TOKEN
    if fact_id in RATIFIED_NON_SOURCE_OR_OTHER_DOMAIN_IDS:
        return FALSE_TOKEN
    return FALSE_TOKEN


def _evaluate_single_record(
    *,
    fact_id: str,
    record: Mapping[str, Any],
    kind_set: str,
    kind_set_resolved: bool,
    ratified_source_kinds: frozenset[str],
) -> BjFactSemanticsRecordV1:
    layer = _normalize_optional_token(field="layer", raw=record.get("layer")) or LAYER_ADJUDICATED
    if layer in FORBIDDEN_AUTHORITY_LAYERS:
        raise BjRemainingUnknownKindSemanticsError(f"FORBIDDEN_EVIDENCE_LAYER:{layer}:{fact_id}")
    evidence_class = (
        _normalize_optional_token(field="evidence_class", raw=record.get("evidence_class"))
        or CURRENTLY_DECISION_CAPABLE
    )
    claimed_status = _normalize_optional_token(
        field="claimed_status", raw=record.get("claimed_status")
    )
    claimed_decision = _normalize_optional_token(
        field="claimed_decision", raw=record.get("claimed_decision")
    )
    if claimed_status and claimed_status not in TYPED_STATUSES:
        return BjFactSemanticsRecordV1(
            fact_id=fact_id,
            status=STATUS_MALFORMED,
            decision=DECISION_REMAIN_UNKNOWN,
            reason_code=REASON_MALFORMED_RECORD,
            evidence_class=evidence_class,
            layer=LAYER_OPEN_OR_CONTRADICTORY,
            embedding_fact=FACT_TO_EMBEDDING[fact_id],
            source_kind_admissible=FALSE_TOKEN,
        )
    if claimed_decision and claimed_decision not in TYPED_DECISIONS:
        return BjFactSemanticsRecordV1(
            fact_id=fact_id,
            status=STATUS_MALFORMED,
            decision=DECISION_REMAIN_UNKNOWN,
            reason_code=REASON_MALFORMED_RECORD,
            evidence_class=evidence_class,
            layer=LAYER_OPEN_OR_CONTRADICTORY,
            embedding_fact=FACT_TO_EMBEDDING[fact_id],
            source_kind_admissible=FALSE_TOKEN,
        )
    if claimed_status == STATUS_MISSING:
        return BjFactSemanticsRecordV1(
            fact_id=fact_id,
            status=STATUS_CONTRADICTORY,
            decision=DECISION_REMAIN_UNKNOWN,
            reason_code=REASON_CONTRADICTORY_TYPED_CLAIMS,
            evidence_class=evidence_class,
            layer=LAYER_OPEN_OR_CONTRADICTORY,
            embedding_fact=FACT_TO_EMBEDDING[fact_id],
            source_kind_admissible=FALSE_TOKEN,
        )
    decision = claimed_decision or DECISION_REMAIN_UNKNOWN
    empty_kind_set = kind_set == KIND_SET_EMPTY or kind_set_resolved is False
    if decision == DECISION_INCLUDE:
        if empty_kind_set:
            return BjFactSemanticsRecordV1(
                fact_id=fact_id,
                status=STATUS_CONTRADICTORY,
                decision=DECISION_REMAIN_UNKNOWN,
                reason_code=REASON_CLAIMED_INCLUDE_EMPTY_KIND_SET,
                evidence_class=evidence_class,
                layer=LAYER_OPEN_OR_CONTRADICTORY,
                embedding_fact=FACT_TO_EMBEDDING[fact_id],
                source_kind_admissible=FALSE_TOKEN,
            )
        if fact_id not in ratified_source_kinds:
            return BjFactSemanticsRecordV1(
                fact_id=fact_id,
                status=STATUS_CONTRADICTORY,
                decision=DECISION_REMAIN_UNKNOWN,
                reason_code=REASON_CLAIMED_INCLUDE_UNRATIFIED_KIND,
                evidence_class=evidence_class,
                layer=LAYER_OPEN_OR_CONTRADICTORY,
                embedding_fact=FACT_TO_EMBEDDING[fact_id],
                source_kind_admissible=FALSE_TOKEN,
            )
        if evidence_class not in FUTURE_ADMISSIBLE_EVIDENCE_CLASSES:
            return BjFactSemanticsRecordV1(
                fact_id=fact_id,
                status=STATUS_UNRESOLVED,
                decision=DECISION_REMAIN_UNKNOWN,
                reason_code=REASON_CLAIMED_RESOLVED_NO_DECISION_CLASS,
                evidence_class=evidence_class,
                layer=LAYER_ADJUDICATED,
                embedding_fact=FACT_TO_EMBEDDING[fact_id],
                source_kind_admissible=FALSE_TOKEN,
            )
        return BjFactSemanticsRecordV1(
            fact_id=fact_id,
            status=STATUS_RESOLVED,
            decision=DECISION_INCLUDE,
            reason_code=REASON_RESOLVED_INCLUDE_ADMISSIBLE,
            evidence_class=evidence_class,
            layer=LAYER_ADJUDICATED,
            embedding_fact=FACT_TO_EMBEDDING[fact_id],
            source_kind_admissible=TRUE_TOKEN,
        )
    if decision == DECISION_EXCLUDE:
        if fact_id not in RATIFIED_NON_SOURCE_OR_OTHER_DOMAIN_IDS:
            return BjFactSemanticsRecordV1(
                fact_id=fact_id,
                status=STATUS_CONTRADICTORY,
                decision=DECISION_REMAIN_UNKNOWN,
                reason_code=REASON_CLAIMED_EXCLUDE_NOT_RATIFIED_NON_SOURCE,
                evidence_class=evidence_class,
                layer=LAYER_OPEN_OR_CONTRADICTORY,
                embedding_fact=FACT_TO_EMBEDDING[fact_id],
                source_kind_admissible=FALSE_TOKEN,
            )
        return BjFactSemanticsRecordV1(
            fact_id=fact_id,
            status=STATUS_RESOLVED,
            decision=DECISION_EXCLUDE,
            reason_code=REASON_RESOLVED_EXCLUDE_ADMISSIBLE,
            evidence_class=evidence_class,
            layer=LAYER_ADJUDICATED,
            embedding_fact=FACT_TO_EMBEDDING[fact_id],
            source_kind_admissible=FALSE_TOKEN,
        )
    if claimed_status == STATUS_RESOLVED:
        return BjFactSemanticsRecordV1(
            fact_id=fact_id,
            status=STATUS_CONTRADICTORY,
            decision=DECISION_REMAIN_UNKNOWN,
            reason_code=REASON_CONTRADICTORY_TYPED_CLAIMS,
            evidence_class=evidence_class,
            layer=LAYER_OPEN_OR_CONTRADICTORY,
            embedding_fact=FACT_TO_EMBEDDING[fact_id],
            source_kind_admissible=FALSE_TOKEN,
        )
    if claimed_status in {STATUS_MALFORMED, STATUS_CONTRADICTORY}:
        reason = (
            REASON_MALFORMED_RECORD
            if claimed_status == STATUS_MALFORMED
            else REASON_CONTRADICTORY_TYPED_CLAIMS
        )
        return BjFactSemanticsRecordV1(
            fact_id=fact_id,
            status=claimed_status,
            decision=DECISION_REMAIN_UNKNOWN,
            reason_code=reason,
            evidence_class=evidence_class,
            layer=LAYER_OPEN_OR_CONTRADICTORY,
            embedding_fact=FACT_TO_EMBEDDING[fact_id],
            source_kind_admissible=FALSE_TOKEN,
        )
    reason = REASON_NO_DECISION_CAPABLE_CLASS
    if empty_kind_set and evidence_class == CURRENTLY_DECISION_CAPABLE:
        reason = select_precedent_reason_code_v1(
            (REASON_NO_DECISION_CAPABLE_CLASS, REASON_KIND_SET_EMPTY)
        )
    return BjFactSemanticsRecordV1(
        fact_id=fact_id,
        status=STATUS_UNRESOLVED,
        decision=DECISION_REMAIN_UNKNOWN,
        reason_code=reason,
        evidence_class=evidence_class,
        layer=LAYER_ADJUDICATED,
        embedding_fact=FACT_TO_EMBEDDING[fact_id],
        source_kind_admissible=_source_kind_admissible(
            fact_id=fact_id,
            kind_set=kind_set,
            kind_set_resolved=kind_set_resolved,
        ),
    )


def _canonical_record_fingerprint(record: Mapping[str, Any]) -> str:
    payload = {
        "claimed_decision": record.get("claimed_decision"),
        "claimed_status": record.get("claimed_status"),
        "evidence_class": record.get("evidence_class"),
        "fact_id": record.get("fact_id"),
        "layer": record.get("layer"),
    }
    return _canonical_json(payload)


def evaluate_bj_remaining_unknown_kind_semantics_v1(
    *,
    records: Sequence[Mapping[str, Any]],
    kind_set: str = KIND_SET_EMPTY,
    kind_set_resolved: bool = False,
    ratified_source_kinds: Sequence[str] = (),
    gate_a_executed: bool = False,
    gate_b_executed: bool = False,
) -> tuple[BjFactSemanticsRecordV1, ...]:
    _assert_standing_pins()
    if gate_a_executed or gate_b_executed:
        raise BjRemainingUnknownKindSemanticsError("GATE_EXECUTION_FORBIDDEN_IN_THIS_LAYER")
    if kind_set != KIND_SET_EMPTY and kind_set_resolved is False:
        raise BjRemainingUnknownKindSemanticsError("KIND_SET_NONEMPTY_WHILE_UNRESOLVED")
    if kind_set == KIND_SET_EMPTY and kind_set_resolved is True:
        raise BjRemainingUnknownKindSemanticsError("KIND_SET_EMPTY_CANNOT_BE_RESOLVED")
    ratified = frozenset(ratified_source_kinds)
    grouped: dict[str, list[Mapping[str, Any]]] = {fact_id: [] for fact_id in FACT_IDS}
    for index, raw in enumerate(records):
        if not isinstance(raw, Mapping):
            raise BjRemainingUnknownKindSemanticsError(f"RECORD_NOT_OBJECT:{index}")
        fact_id = raw.get("fact_id")
        if not isinstance(fact_id, str) or fact_id not in grouped:
            evaluated_unknown = BjFactSemanticsRecordV1(
                fact_id=str(fact_id or f"INDEX_{index}"),
                status=STATUS_MALFORMED,
                decision=DECISION_REMAIN_UNKNOWN,
                reason_code=REASON_MALFORMED_RECORD,
                evidence_class=NONE_TOKEN,
                layer=LAYER_OPEN_OR_CONTRADICTORY,
                embedding_fact=NONE_TOKEN,
                source_kind_admissible=FALSE_TOKEN,
            )
            raise BjRemainingUnknownKindSemanticsError(
                f"MALFORMED_FACT_ID:{evaluated_unknown.fact_id}"
            )
        grouped[fact_id].append(raw)
    evaluated: list[BjFactSemanticsRecordV1] = []
    for fact_id in FACT_IDS:
        group = grouped[fact_id]
        if not group:
            evaluated.append(
                BjFactSemanticsRecordV1(
                    fact_id=fact_id,
                    status=STATUS_MISSING,
                    decision=DECISION_REMAIN_UNKNOWN,
                    reason_code=REASON_MISSING_RECORD,
                    evidence_class=NONE_TOKEN,
                    layer=LAYER_OPEN_OR_CONTRADICTORY,
                    embedding_fact=FACT_TO_EMBEDDING[fact_id],
                    source_kind_admissible=FALSE_TOKEN,
                )
            )
            continue
        fingerprints = {_canonical_record_fingerprint(item) for item in group}
        if len(fingerprints) > 1:
            evaluated.append(
                BjFactSemanticsRecordV1(
                    fact_id=fact_id,
                    status=STATUS_CONTRADICTORY,
                    decision=DECISION_REMAIN_UNKNOWN,
                    reason_code=REASON_CONTRADICTORY_TYPED_CLAIMS,
                    evidence_class=CURRENTLY_DECISION_CAPABLE,
                    layer=LAYER_OPEN_OR_CONTRADICTORY,
                    embedding_fact=FACT_TO_EMBEDDING[fact_id],
                    source_kind_admissible=FALSE_TOKEN,
                )
            )
            continue
        evaluated.append(
            _evaluate_single_record(
                fact_id=fact_id,
                record=group[0],
                kind_set=kind_set,
                kind_set_resolved=kind_set_resolved,
                ratified_source_kinds=ratified,
            )
        )
    return tuple(evaluated)


def attach_bj_semantics_to_d6_diagnostics_v1(
    *,
    existing: Mapping[str, Any],
    records: Sequence[BjFactSemanticsRecordV1],
    kind_set: str,
    kind_set_resolved: str,
    venue_get_count: str,
    gate_a_executed: str,
    gate_b_executed: str,
) -> dict[str, Any]:
    attached = dict(existing)
    by_fact = {record.fact_id: record for record in records}
    additions = {
        "F12_STATUS": by_fact[FACT_F12].status,
        "F13_STATUS": by_fact[FACT_F13].status,
        "U05_STATUS": by_fact[FACT_U05].status,
        "F16_STATUS": by_fact[FACT_F16].status,
        "F17_STATUS": by_fact[FACT_F17].status,
        "F18_STATUS": by_fact[FACT_F18].status,
        "F12_REASON_CODE": by_fact[FACT_F12].reason_code,
        "F13_REASON_CODE": by_fact[FACT_F13].reason_code,
        "U05_REASON_CODE": by_fact[FACT_U05].reason_code,
        "F16_REASON_CODE": by_fact[FACT_F16].reason_code,
        "F17_REASON_CODE": by_fact[FACT_F17].reason_code,
        "F18_REASON_CODE": by_fact[FACT_F18].reason_code,
        "F12_DECISION": by_fact[FACT_F12].decision,
        "F13_DECISION": by_fact[FACT_F13].decision,
        "U05_KIND_DECISION": by_fact[FACT_U05].decision,
        "F16_DECISION": by_fact[FACT_F16].decision,
        "F17_DECISION": by_fact[FACT_F17].decision,
        "F18_DECISION": by_fact[FACT_F18].decision,
        "KIND_SET": kind_set,
        "KIND_SET_RESOLVED": kind_set_resolved,
        "VENUE_GET_COUNT": venue_get_count,
        "GATE_A_EXECUTED": gate_a_executed,
        "GATE_B_EXECUTED": gate_b_executed,
        "UNKNOWN_SEMANTICS_INVENTED": FALSE_TOKEN,
        "BJ_SEMANTICS_AGGREGATE_STATUS": select_precedent_status_v1(
            tuple(record.status for record in records)
        ),
        "BJ_SEMANTICS_AGGREGATE_REASON_CODE": select_precedent_reason_code_v1(
            tuple(record.reason_code for record in records)
        ),
        "EARLIEST_REMAINING_D6_BLOCKER": BJ_EARLIEST_REMAINING_D6_BLOCKER,
    }
    for key, value in additions.items():
        if key in attached and attached[key] != value:
            raise BjRemainingUnknownKindSemanticsError(f"DIAGNOSTIC_AUTHORITY_COLLISION:{key}")
        attached[key] = value
    for key in STANDING_D6_DIAGNOSTIC_KEYS:
        if key in existing and key not in attached:
            raise BjRemainingUnknownKindSemanticsError(f"DIAGNOSTIC_KEY_DROPPED:{key}")
    return attached


def _records_from_bj_claims(claims: Mapping[str, Any]) -> list[dict[str, str]]:
    mapping = {
        FACT_F12: ("F12_STATUS", "F12_DECISION"),
        FACT_F13: ("F13_STATUS", "F13_DECISION"),
        FACT_U05: ("U05_STATUS", "U05_KIND_DECISION"),
        FACT_F16: ("F16_STATUS", "F16_DECISION"),
        FACT_F17: ("F17_STATUS", "F17_DECISION"),
        FACT_F18: ("F18_STATUS", "F18_DECISION"),
    }
    records: list[dict[str, str]] = []
    for fact_id, (status_field, decision_field) in mapping.items():
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


def reject_claimed_bj_semantics_authority_mutation_v1(*, claimed_proof: str, fact_id: str) -> None:
    forbidden = {
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "EXECUTE_GATE_B",
        "HOPE_BALANCE_GET",
        "KIND_SET_RESOLVED_TRUE",
        "D6_FULLY_CLOSED",
        "INVENT_VENUE_FIELD_SEMANTICS",
        "NORMALIZE_UNKNOWN_TO_INCLUDE",
        "NORMALIZE_UNKNOWN_TO_EXCLUDE",
        "RESTORE_LEGACY_EQUITY_LOGIC",
    }
    if claimed_proof in forbidden:
        raise BjRemainingUnknownKindSemanticsError(f"BJ_SEMANTICS_CANNOT_{claimed_proof}:{fact_id}")
    if claimed_proof not in {
        "TYPED_UNRESOLVED_REMAIN_UNKNOWN",
        "TYPED_MISSING_REMAIN_UNKNOWN",
        "TYPED_MALFORMED_REMAIN_UNKNOWN",
        "TYPED_CONTRADICTORY_REMAIN_UNKNOWN",
        "FUTURE_EVIDENCE_MAY_RESOLVE_WITHOUT_CONTRACT_BREAK",
    }:
        raise BjRemainingUnknownKindSemanticsError(f"BJ_SEMANTICS_PROOF_UNKNOWN:{claimed_proof}")


def execute_bj_remaining_unknown_kind_semantics_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    sealed_bj_pack: Path,
    evidence_root: Path,
    semantics_as_of: str,
) -> BjRemainingUnknownKindSemanticsResultV1:
    _assert_standing_pins()
    if owner_go != OWNER_GO:
        raise BjRemainingUnknownKindSemanticsError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise BjRemainingUnknownKindSemanticsError("ORIGIN_MAIN_SHA_MISMATCH")
    bj_pack = Path(sealed_bj_pack)
    if verify_manifest_sha256_v1(store_root=bj_pack) != 0:
        raise BjRemainingUnknownKindSemanticsError("BJ_MANIFEST_VERIFY_FAILED")
    bj_claims = _load_json_object(path=bj_pack / CLAIMS_FILE)
    _require_token(field="F12_DECISION", payload=bj_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F13_DECISION", payload=bj_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_KIND_DECISION", payload=bj_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F16_DECISION", payload=bj_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F17_DECISION", payload=bj_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="F18_DECISION", payload=bj_claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="KIND_SET", payload=bj_claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_A_EXECUTED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(field="GATE_B_EXECUTED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(field="VENUE_GET_COUNT", payload=bj_claims, expected="0")
    _require_token(field="D6_FULLY_CLOSED", payload=bj_claims, expected=FALSE_TOKEN)
    _require_token(
        field="CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13",
        payload=bj_claims,
        expected=CURRENTLY_DECISION_CAPABLE,
    )
    records = evaluate_bj_remaining_unknown_kind_semantics_v1(
        records=_records_from_bj_claims(bj_claims),
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=False,
        ratified_source_kinds=(),
        gate_a_executed=False,
        gate_b_executed=False,
    )
    by_fact = {record.fact_id: record for record in records}
    standing = {
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": DAG_PIN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
    }
    diagnostics = attach_bj_semantics_to_d6_diagnostics_v1(
        existing=standing,
        records=records,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        venue_get_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
    )
    folder = _folder_from_as_of(semantics_as_of)
    store = Path(evidence_root) / folder
    store.mkdir(parents=True, exist_ok=True)
    fact_payload = {
        record.fact_id: {
            "status": record.status,
            "decision": record.decision,
            "reason_code": record.reason_code,
            "evidence_class": record.evidence_class,
            "layer": record.layer,
            "embedding_fact": record.embedding_fact,
            "source_kind_admissible": record.source_kind_admissible,
        }
        for record in records
    }
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": "NONE",
        "ATLAS_AUTHORITY": "NONE",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "SEMANTICS_AS_OF": semantics_as_of,
        "SEALED_BJ_PACK": CANONICAL_BJ_PACK_RELPATH,
        "SEALED_INPUT_ONLY": TRUE_TOKEN,
        "VENUE_GET_COUNT": "0",
        "POST_COUNT": "0",
        "GATE_A_EXECUTED": FALSE_TOKEN,
        "GATE_B_EXECUTED": FALSE_TOKEN,
        "UNKNOWN_SEMANTICS_INVENTED": FALSE_TOKEN,
        "F12_STATUS": by_fact[FACT_F12].status,
        "F13_STATUS": by_fact[FACT_F13].status,
        "U05_STATUS": by_fact[FACT_U05].status,
        "F16_STATUS": by_fact[FACT_F16].status,
        "F17_STATUS": by_fact[FACT_F17].status,
        "F18_STATUS": by_fact[FACT_F18].status,
        "F12_DECISION": by_fact[FACT_F12].decision,
        "F13_DECISION": by_fact[FACT_F13].decision,
        "U05_KIND_DECISION": by_fact[FACT_U05].decision,
        "F16_DECISION": by_fact[FACT_F16].decision,
        "F17_DECISION": by_fact[FACT_F17].decision,
        "F18_DECISION": by_fact[FACT_F18].decision,
        "F12_REASON_CODE": by_fact[FACT_F12].reason_code,
        "F13_REASON_CODE": by_fact[FACT_F13].reason_code,
        "U05_REASON_CODE": by_fact[FACT_U05].reason_code,
        "F16_REASON_CODE": by_fact[FACT_F16].reason_code,
        "F17_REASON_CODE": by_fact[FACT_F17].reason_code,
        "F18_REASON_CODE": by_fact[FACT_F18].reason_code,
        "AGGREGATE_STATUS": diagnostics["BJ_SEMANTICS_AGGREGATE_STATUS"],
        "AGGREGATE_REASON_CODE": diagnostics["BJ_SEMANTICS_AGGREGATE_REASON_CODE"],
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY": BJ_KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
        "EARLIEST_REMAINING_D6_BLOCKER": BJ_EARLIEST_REMAINING_D6_BLOCKER,
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
        "BJ_MANIFEST_VERIFY_RC": "0",
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "fact_semantics_v1.json", payload=fact_payload)
    _persist_json(path=store / "d6_diagnostics_v1.json", payload=diagnostics)
    _persist_json(
        path=store / "reason_precedence_v1.json",
        payload={"order": list(REASON_PRECEDENCE), "status_order": list(STATUS_PRECEDENCE)},
    )
    _persist_json(
        path=store / "layers_v1.json",
        payload={
            "CANONICAL_AUTHORITY": "claims.json,reason_precedence_v1.json",
            "FORENSIC_RAW": "NONE_NEW_THIS_GO",
            "ADJUDICATED_CONCLUSION": "fact_semantics_v1.json,d6_diagnostics_v1.json",
            "HISTORICAL_INTERMEDIATE": CANONICAL_BJ_PACK_RELPATH,
            "NAVIGATION_ONLY": "NONE",
            "INTERPRETATION": "FORBIDDEN",
            "HYPOTHESIS": "FORBIDDEN",
            "OPEN_OR_CONTRADICTORY": "NONE_ON_SEALED_BJ_PIN",
        },
    )
    _persist_json(
        path=store / "fail_closed_guards_v1.json",
        payload={
            "include_from_unknown": "FORBIDDEN",
            "exclude_from_unknown": "FORBIDDEN",
            "empty_kind_set": KIND_SET_EMPTY,
            "unratified_kind": "NO_ADMISSIBLE_SOURCE_KIND",
            "gate_a_executed": FALSE_TOKEN,
            "gate_b_executed": FALSE_TOKEN,
            "venue_get_count": "0",
            "unknown_semantics_invented": FALSE_TOKEN,
            "d6_fully_closed": FALSE_TOKEN,
            "d7_authorized": FALSE_TOKEN,
            "ms2_authorized": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "parent_bj_pack": CANONICAL_BJ_PACK_RELPATH,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "semantics_as_of": semantics_as_of,
            "owner_go": OWNER_GO,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    if FACT_TO_EMBEDDING[FACT_F12] not in UNKNOWN_EMBEDDING_FACTS:
        raise BjRemainingUnknownKindSemanticsError("EMBEDDING_FACT_PIN_DRIFT")
    return BjRemainingUnknownKindSemanticsResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        semantics_as_of=semantics_as_of,
        store_root=str(store),
        f12_status=by_fact[FACT_F12].status,
        f13_status=by_fact[FACT_F13].status,
        u05_status=by_fact[FACT_U05].status,
        f16_status=by_fact[FACT_F16].status,
        f17_status=by_fact[FACT_F17].status,
        f18_status=by_fact[FACT_F18].status,
        f12_decision=by_fact[FACT_F12].decision,
        f13_decision=by_fact[FACT_F13].decision,
        u05_decision=by_fact[FACT_U05].decision,
        f16_decision=by_fact[FACT_F16].decision,
        f17_decision=by_fact[FACT_F17].decision,
        f18_decision=by_fact[FACT_F18].decision,
        f12_reason_code=by_fact[FACT_F12].reason_code,
        f13_reason_code=by_fact[FACT_F13].reason_code,
        u05_reason_code=by_fact[FACT_U05].reason_code,
        f16_reason_code=by_fact[FACT_F16].reason_code,
        f17_reason_code=by_fact[FACT_F17].reason_code,
        f18_reason_code=by_fact[FACT_F18].reason_code,
        aggregate_status=str(diagnostics["BJ_SEMANTICS_AGGREGATE_STATUS"]),
        aggregate_reason_code=str(diagnostics["BJ_SEMANTICS_AGGREGATE_REASON_CODE"]),
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        venue_get_count="0",
        gate_a_executed=FALSE_TOKEN,
        gate_b_executed=FALSE_TOKEN,
        unknown_semantics_invented=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        evidence_manifest=str(manifest),
    )
