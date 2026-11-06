"""Productive restart reader for the minted §11.14 Live durable handoff owner.

Reads only SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1.
Does not GET. Does not POST. Does not invent schema v2. Does not bind
host-crash durability. Does not promote LIVE_RESTART_RECONSTRUCTED.
Does not treat evidence packs, A1 WAL, DDO, FILEGATE, Testnet durable
state, or venue GET as a handoff source.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    durable_handoff_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    FORBIDDEN_PROVENANCE_CLASSES,
    HANDOFF_DOCUMENT_CLASS,
    REQUIRED_HANDOFF_FIELDS,
    VENUE_GET_ARTIFACT_NAMES,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    POS_SIGN_SEMANTICS,
    POS_UNIT,
    SELECTED_SEMANTIC_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    classify_artifact_role_v1,
    parse_handoff_pos_v1,
    validate_temporal_order_v1,
)

READER_BOUND = True
SELECTED_PRODUCTIVE_READER = "read_validated_durable_pre_restart_handoff_v1"
ALLOWED_POS_SIDE_VALUES: frozenset[str] = frozenset({BOUND_POS_SIDE})
FORBIDDEN_POS_SUBSTITUTION_KEYS: frozenset[str] = frozenset(
    {
        "fillSz",
        "fill_sz",
        "submitted_sz",
        "sz",
        "ackSz",
        "accFillSz",
        "venue_pos",
        "GET_pos",
        "accounting_pos",
    }
)

RESULT_VALID_HANDOFF = "VALID_HANDOFF"
RESULT_MISSING_HANDOFF = "MISSING_HANDOFF"
RESULT_MALFORMED_HANDOFF = "MALFORMED_HANDOFF"
RESULT_STALE_HANDOFF = "STALE_HANDOFF"
RESULT_WRONG_INSTRUMENT = "WRONG_INSTRUMENT"
RESULT_PROVENANCE_INVALID = "PROVENANCE_INVALID"
RESULT_SCHEMA_INVALID = "SCHEMA_INVALID"
RESULT_READ_FAILURE = "READ_FAILURE"

PROVENANCE_VALIDATION = "CONTRACT_PROVEN"
FRESHNESS_VALIDATION = "PARTIAL"


def _result(
    *,
    result: str,
    reason: str,
    record: Mapping[str, Any] | None = None,
    validated: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_RESTART_READER_RESULT_V1",
        "RESULT": result,
        "REASON": reason,
        "READER_BOUND": True,
        "SELECTED_PRODUCTIVE_READER": SELECTED_PRODUCTIVE_READER,
        "STORAGE_OWNER_ID": FIRST_OWNER_ID,
        "HANDOFF_SCHEMA_VERSION": HANDOFF_SCHEMA_VERSION,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "POS_UNIT": POS_UNIT,
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "PROVENANCE_VALIDATION": PROVENANCE_VALIDATION,
        "FRESHNESS_VALIDATION": FRESHNESS_VALIDATION,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "GET_PERFORMED": False,
        "POST_USED": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "VENUE_GET_FALLBACK": False,
        "EVIDENCE_PACK_FALLBACK": False,
        "TIMESTAMP_BACKFILL": False,
        "SYNTHETIC_PRE_RESTART_PROVENANCE": False,
        "record": dict(record) if record is not None else None,
        "validated_handoff": dict(validated) if validated is not None else None,
    }
    if extra:
        payload.update(dict(extra))
    return payload


def _parse_unsigned_pos(raw: object) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "":
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    return value


def read_validated_durable_pre_restart_handoff_v1(
    *,
    storage_root: Path,
    expected_inst_id: object = BOUND_INSTID,
    expected_clordid: object = BOUND_CLORDID,
    expected_ordid: object = BOUND_ORDID,
    expected_pos_side: object = BOUND_POS_SIDE,
    expected_attempt_identity: object | None = None,
    restart_at_utc: object | None = None,
    source_path: object | None = None,
) -> dict[str, Any]:
    expected_inst = str(expected_inst_id or "").strip()
    expected_cl = str(expected_clordid or "").strip()
    expected_ord = str(expected_ordid or "").strip()
    expected_side = str(expected_pos_side or "").strip()
    expected_attempt = str(expected_attempt_identity or "").strip()
    classified_source = classify_artifact_role_v1(path=str(source_path or storage_root))
    if classified_source in {
        "ACCOUNTING_VENUE_GET_NOT_RESTART_HANDOFF",
        "SECTION_11_14_EVIDENCE_PACK_NOT_CONTROL_HANDOFF",
        "A1_WAL_NOT_THIS_FIELD",
        "DDO_LEDGER_NOT_THIS_FIELD",
        "FILEGATE_KILL_SWITCH_NOT_THIS_FIELD",
        "TESTNET_DURABLE_STATE_NOT_THIS_FIELD",
        "PHASE_9_2_MD_OR_FIXTURE_NOT_THIS_FIELD",
        "CAP_72_SIDESTATE_NOT_THIS_FIELD",
    }:
        return _result(
            result=RESULT_PROVENANCE_INVALID,
            reason="FORBIDDEN_SOURCE_OWNER",
            extra={"ARTIFACT_ROLE": classified_source},
        )

    path = durable_handoff_path_v1(storage_root=storage_root)
    if any(name in path.name for name in VENUE_GET_ARTIFACT_NAMES) or path.name.startswith("GET_"):
        return _result(result=RESULT_PROVENANCE_INVALID, reason="VENUE_GET_FALLBACK_FORBIDDEN")
    if not path.exists():
        return _result(result=RESULT_MISSING_HANDOFF, reason="DURABLE_HANDOFF_ABSENT")
    if not path.is_file():
        return _result(result=RESULT_READ_FAILURE, reason="OWNER_READ_FAILURE")
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except FileNotFoundError:
        return _result(result=RESULT_MISSING_HANDOFF, reason="DURABLE_HANDOFF_ABSENT")
    except OSError:
        return _result(result=RESULT_READ_FAILURE, reason="OWNER_READ_FAILURE")
    except (UnicodeError, json.JSONDecodeError):
        return _result(result=RESULT_MALFORMED_HANDOFF, reason="MALFORMED_SERIALIZATION")
    if not isinstance(payload, dict):
        return _result(result=RESULT_MALFORMED_HANDOFF, reason="MALFORMED_SERIALIZATION")

    schema = str(payload.get("schema_version") or "").strip()
    if schema == "":
        return _result(
            result=RESULT_SCHEMA_INVALID,
            reason="SCHEMA_MISSING",
            record=payload,
        )
    if schema != HANDOFF_SCHEMA_VERSION:
        return _result(
            result=RESULT_SCHEMA_INVALID,
            reason="SCHEMA_OR_VERSION_MISMATCH",
            record=payload,
        )
    document_class = str(payload.get("DOCUMENT_CLASS") or "").strip()
    if document_class != HANDOFF_DOCUMENT_CLASS:
        return _result(
            result=RESULT_SCHEMA_INVALID,
            reason="DOCUMENT_CLASS_MISMATCH",
            record=payload,
        )

    missing = [
        name for name in REQUIRED_HANDOFF_FIELDS if str(payload.get(name) or "").strip() == ""
    ]
    if missing:
        return _result(
            result=RESULT_MALFORMED_HANDOFF,
            reason="MISSING_REQUIRED_HANDOFF_FIELDS",
            record=payload,
            extra={"MISSING_FIELDS": missing},
        )

    owner = str(payload.get("owner_id") or payload.get("claimed_owner") or "").strip()
    provenance = str(payload.get("provenance_class") or "").strip()
    if owner != FIRST_OWNER_ID:
        return _result(
            result=RESULT_PROVENANCE_INVALID,
            reason="OWNER_MISMATCH",
            record=payload,
        )
    if provenance in FORBIDDEN_PROVENANCE_CLASSES:
        return _result(
            result=RESULT_PROVENANCE_INVALID,
            reason="FORBIDDEN_PROVENANCE",
            record=payload,
        )
    if provenance != CONTEMPORANEOUS_PROVENANCE_CLASS:
        return _result(
            result=RESULT_PROVENANCE_INVALID,
            reason="PROVENANCE_MISMATCH",
            record=payload,
        )

    inst_id = str(payload.get("instId") or "").strip()
    if inst_id != expected_inst:
        return _result(
            result=RESULT_WRONG_INSTRUMENT,
            reason="WRONG_INSTRUMENT",
            record=payload,
            extra={"expected_instId": expected_inst, "actual_instId": inst_id},
        )

    pos_side = str(payload.get("posSide") or "").strip()
    if pos_side not in ALLOWED_POS_SIDE_VALUES or pos_side != expected_side:
        return _result(
            result=RESULT_MALFORMED_HANDOFF,
            reason="INVALID_POSSIDE",
            record=payload,
            extra={"expected_posSide": expected_side, "actual_posSide": pos_side},
        )

    pos_raw = payload.get("pos")
    pos_value = _parse_unsigned_pos(pos_raw)
    if parse_handoff_pos_v1(pos_raw) is None or pos_value is None:
        return _result(
            result=RESULT_MALFORMED_HANDOFF,
            reason="INVALID_POS",
            record=payload,
        )
    substitution_present = [name for name in FORBIDDEN_POS_SUBSTITUTION_KEYS if name in payload]
    if substitution_present:
        return _result(
            result=RESULT_MALFORMED_HANDOFF,
            reason="POS_SUBSTITUTION_FORBIDDEN",
            record=payload,
            extra={"FORBIDDEN_POS_SUBSTITUTION_KEYS": substitution_present},
        )
    bound_fill = parse_handoff_pos_v1(BOUND_FILL_SZ)
    if (
        expected_inst == BOUND_INSTID
        and expected_cl == BOUND_CLORDID
        and expected_ord == BOUND_ORDID
        and bound_fill is not None
        and pos_value != bound_fill
    ):
        return _result(
            result=RESULT_MALFORMED_HANDOFF,
            reason="POS_MUST_DECIMAL_EQUAL_BOUND_IDENTITY",
            record=payload,
        )
    if bound_fill is not None and bound_fill != 0 and pos_value == 0:
        return _result(
            result=RESULT_MALFORMED_HANDOFF,
            reason="SILENT_REINITIALIZATION_FORBIDDEN",
            record=payload,
        )

    clordid = str(payload.get("clOrdId") or "").strip()
    ord_id = str(payload.get("ordId") or "").strip()
    if clordid != expected_cl or ord_id != expected_ord:
        return _result(
            result=RESULT_STALE_HANDOFF,
            reason="IDENTITY_MISMATCH",
            record=payload,
            extra={
                "expected_clOrdId": expected_cl,
                "expected_ordId": expected_ord,
                "actual_clOrdId": clordid,
                "actual_ordId": ord_id,
            },
        )

    attempt = str(payload.get("attempt_identity") or "").strip()
    if attempt == "":
        return _result(
            result=RESULT_STALE_HANDOFF,
            reason="ATTEMPT_IDENTITY_MISSING",
            record=payload,
        )
    if expected_attempt and attempt != expected_attempt:
        return _result(
            result=RESULT_STALE_HANDOFF,
            reason="STALE_OR_NON_APPLICABLE_ATTEMPT",
            record=payload,
            extra={
                "expected_attempt_identity": expected_attempt,
                "actual_attempt_identity": attempt,
            },
        )
    temporal = validate_temporal_order_v1(
        handoff=payload,
        restart_at_utc=str(restart_at_utc or "").strip() or None,
    )
    if temporal["TEMPORAL_OK"] is not True:
        return _result(
            result=RESULT_STALE_HANDOFF,
            reason=str(temporal["REASON"]),
            record=payload,
            extra={"temporal": temporal},
        )

    validated = {
        "clOrdId": clordid,
        "ordId": ord_id,
        "instId": inst_id,
        "posSide": pos_side,
        "pos": format(pos_value, "f"),
        "schema_version": schema,
        "owner_id": owner,
        "provenance_class": provenance,
        "attempt_identity": attempt,
        "DOCUMENT_CLASS": document_class,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "POS_UNIT": POS_UNIT,
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET": True,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "captured_at_utc": str(payload.get("captured_at_utc") or "").strip(),
        "written_at_utc": str(payload.get("written_at_utc") or "").strip(),
    }
    return _result(
        result=RESULT_VALID_HANDOFF,
        reason="VALID_HANDOFF",
        record=payload,
        validated=validated,
        extra={
            "SCHEMA_VALIDATION": "PASS",
            "IDENTITY_VALIDATION": "PASS",
            "S05_VALIDATION": "PASS",
            "POSSIDE_VALIDATION": "PASS",
            "PROVENANCE_VALIDATION": PROVENANCE_VALIDATION,
            "FRESHNESS_VALIDATION": FRESHNESS_VALIDATION,
        },
    )
