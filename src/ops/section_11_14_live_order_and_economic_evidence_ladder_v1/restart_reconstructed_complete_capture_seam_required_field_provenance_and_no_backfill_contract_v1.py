"""Offline complete capture-seam provenance and no-backfill contract.

Proves the structural seam from the unique productive caller through persist
and the restart reader for every required handoff field. Does not GET. Does
not POST. Does not execute productive contemporaneous Live capture. Does not
promote LIVE_RESTART_RECONSTRUCTED. Does not claim host-crash durability.
Does not invent schema v2.

Historical reader-bind COMPLETE_CAPTURE_SEAM remains UNPROVEN for that
consumed GO. This GO evaluates the seam independently as an offline
contract proof. Empirical productive capture remains false.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    CALLER_RELPATH,
    HOST_JOIN_SYMBOL,
    PRODUCTIVE_HOOK_CALLER,
    compose_live_order_pre_restart_capture_host_graph_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    run_live_order_pre_restart_handoff_capture_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    LIVE_RESTART_RECONSTRUCTED,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    ADMISSIBLE_FIELD_SOURCE_KINDS,
    FORBIDDEN_FIELD_SOURCE_KINDS,
    FORBIDDEN_FRESHNESS,
    FRESHNESS_CONTEMPORANEOUS,
    IDENTITY_HANDOFF_FIELDS,
    INPUT_CLASS_TEST_FIXTURE,
    bind_required_field_provenance_matrix_v1,
    census_productive_capture_dataflow_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    HOOK_RELPATH,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    PRODUCTIVE_S05_QTY_SOURCE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_v1 import (
    PRODUCER_RELPATH,
    PRODUCER_SYMBOL,
    WRITER_RELPATH,
    WRITER_SYMBOL,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_offline_codec_v1 import (
    deserialize_handoff_offline_v1,
    serialize_handoff_offline_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    RELATIVE_DURABLE_DIR,
    HANDOFF_FILENAME,
    commit_handoff_after_bound_fill_before_restart_v1,
    durable_handoff_path_v1,
    load_durable_handoff_record_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_v1 import (
    RESULT_VALID_HANDOFF,
    read_validated_durable_pre_restart_handoff_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    FORBIDDEN_PROVENANCE_CLASSES,
    HANDOFF_DOCUMENT_CLASS,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
    POS_UNIT,
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_hook_caller_binding_and_offline_call_path_proof_v1 import (
    census_productive_hook_caller_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    bind_required_handoff_field_contracts_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    parse_handoff_pos_v1,
)

COMPLETE_CAPTURE_SEAM = "PROVEN"
COMPLETE_CAPTURE_SEAM_TAXONOMY: tuple[str, ...] = ("UNPROVEN", "PROVEN")
HISTORICAL_READER_BIND_COMPLETE_CAPTURE_SEAM = "UNPROVEN"
PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL = True
REQUIRED_FIELD_PROVENANCE_COMPLETE = True
NO_BACKFILL_CONTRACT_PROVEN = True
CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED = False
PARTIAL_CAPTURE_ALLOWED = False
RETROACTIVE_SYNTHESIS_ALLOWED = False
LEGACY_READABLE_IS_NOT_CONTEMPORANEOUS_VALID = True
AUTHORITATIVE_CAPTURE_PRODUCER = (
    f"LIVE_IDENTITY_BOUND_VENUE_FILL::require_future_bound_fill_identity_v1+{PRODUCER_SYMBOL}"
)
CAPTURE_HOOK = PRODUCTIVE_LIFECYCLE_HOOK
CAPTURE_OWNER = PRODUCTIVE_CAPTURE_OWNER
CASE_ADJUDICATION = (
    "CASE_COMPLETE_CAPTURE_SEAM_PROVEN_REQUIRED_FIELD_PROVENANCE_COMPLETE_"
    "NO_BACKFILL_CONTRACT_PROVEN_OFFLINE_NOT_LIVE_OBSERVED"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_"
    "REQUIRES_SEPARATE_OWNER_GO_V1"
)
IDENTITY_PRODUCER = (
    "LIVE_IDENTITY_BOUND_VENUE_FILL::bound_fill_identity parameterized into "
    f"{PRODUCTIVE_CAPTURE_OWNER}"
)
IDENTITY_PRODUCER_SYMBOL = "require_future_bound_fill_identity_v1"
IDENTITY_PRODUCER_OBJECT_FIELD = "bound_fill_identity.{field}"
POS_PRODUCER_OBJECT_FIELD = "peak_trade_owned_resulting_current_position_qty"
CAPTURE_INPUT_IDENTITY_FIELD = "bound_fill_identity.{field}"
CAPTURE_INPUT_POS_FIELD = "peak_trade_owned_resulting_current_position_qty"
TRANSFORM_IDENTITY = "EXACT_STRING_COPY_NO_CANONICALIZATION"
TRANSFORM_POS = "UNSIGNED_DECIMAL_FORMAT_F_EQUAL_TO_FILL_SZ"
READER_FIELD_IDENTITY = "validated_handoff.{field}"
READER_FIELD_POS = "validated_handoff.pos"


def _text(value: object) -> str:
    return str(value or "").strip()


def bind_complete_capture_seam_field_table_v1() -> dict[str, Any]:
    historical = {row["FIELD_NAME"]: row for row in bind_required_handoff_field_contracts_v1()}
    rows: list[dict[str, Any]] = []
    for name in REQUIRED_HANDOFF_FIELDS:
        historical_row = historical[name]
        identity = name in IDENTITY_HANDOFF_FIELDS
        rows.append(
            {
                "FIELD": name,
                "AUTHORITATIVE_PRODUCER": (
                    IDENTITY_PRODUCER if identity else PRODUCTIVE_S05_QTY_SOURCE
                ),
                "PRODUCER_OBJECT/FIELD": (
                    IDENTITY_PRODUCER_OBJECT_FIELD.replace("{field}", name)
                    if identity
                    else POS_PRODUCER_OBJECT_FIELD
                ),
                "CAPTURE_INPUT_FIELD": (
                    CAPTURE_INPUT_IDENTITY_FIELD.replace("{field}", name)
                    if identity
                    else CAPTURE_INPUT_POS_FIELD
                ),
                "TRANSFORM": TRANSFORM_IDENTITY if identity else TRANSFORM_POS,
                "PERSISTED_FIELD": name,
                "READER_FIELD": (
                    READER_FIELD_IDENTITY.replace("{field}", name) if identity else READER_FIELD_POS
                ),
                "VALIDATION": (
                    "nonempty exact string; same bound-fill lifecycle; "
                    "no historical BOUND_* hardcode"
                    if identity
                    else (
                        f"unsigned Decimal; unit={POS_UNIT}; source_kind="
                        f"{ADMISSIBLE_POS_SOURCE_KIND}; Decimal-equal fillSz; "
                        "FILL_SZ_COPY forbidden"
                    )
                ),
                "MISSING_BEHAVIOR": "HARD_FAIL",
                "BACKFILL_ALLOWED": False,
                "PROVENANCE_STATUS": "PROVEN_CONTEMPORANEOUS_NO_BACKFILL_OFFLINE",
                "WHY_REQUIRED": (
                    "REQUIRED_HANDOFF_FIELDS+LIVE_RESTART_RECONSTRUCTED identity "
                    "equation+FUTURE_BOUND_IDENTITY_PARAMETERIZATION"
                    if identity
                    else (
                        "REQUIRED_HANDOFF_FIELDS+"
                        "S05_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY"
                    )
                ),
                "TYPE": "str" if identity else "Decimal-string",
                "UNIT": "identity" if identity else POS_UNIT,
                "SEMANTICS": (
                    historical_row["SEMANTIC_MEANING"]
                    if identity
                    else (
                        "Peak_Trade-owned resulting/current position qty; unsigned "
                        "venue contract count; Decimal-equal fillSz; not fillSz copy"
                    )
                ),
                "OBSERVATION_TIME": (
                    "CONTEMPORANEOUS_WITH_BOUND_FILL_PROVEN_AT"
                    if identity
                    else "CONTEMPORANEOUS_AT_HANDOFF_COMMIT_AFTER_BOUND_FILL"
                ),
                "NULL_ALLOWED": False,
                "DEFAULT_EXISTS": False,
                "DEFAULT_SEMANTICALLY_ALLOWED": False,
                "READER_REQUIRES_FIELD": True,
                "READER_WRITER_SEMANTICS_IDENTICAL": True,
                "NAMING_SIMILARITY_IS_NOT_IDENTITY": True,
            }
        )
    if len(rows) != len(REQUIRED_HANDOFF_FIELDS):
        raise Section1114OfflineSurfaceError("REQUIRED_HANDOFF_FIELD_COUNT_DRIFT")
    backfill = [row["FIELD"] for row in rows if row["BACKFILL_ALLOWED"] is not False]
    if backfill:
        raise Section1114OfflineSurfaceError("BACKFILL_FORBIDDEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_FIELD_TABLE_V1",
        "HANDOFF_REQUIRED_FIELD_COUNT": len(rows),
        "REQUIRED_FIELD_PROVENANCE_COMPLETE": True,
        "NO_BACKFILL_CONTRACT_PROVEN": True,
        "SCHEMA_CHANGE_REQUIRED": False,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "rows": rows,
    }


def _require_persisted_field_provenance(
    *,
    record: Mapping[str, Any],
    expected_lifecycle: str,
) -> dict[str, dict[str, str]]:
    raw = record.get("field_provenance")
    if not isinstance(raw, Mapping):
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_MISSING")
    fields = dict(raw.get("fields") or raw)
    validated: dict[str, dict[str, str]] = {}
    for name in REQUIRED_HANDOFF_FIELDS:
        payload = dict(fields.get(name) or {})
        if not payload:
            raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_MISSING")
        source_kind = _text(payload.get("SOURCE_KIND"))
        freshness = _text(payload.get("FRESHNESS"))
        lifecycle = _text(payload.get("LIFECYCLE_ID"))
        backfill = _text(payload.get("BACKFILL_ALLOWED")).lower()
        value = _text(payload.get("VALUE"))
        if source_kind in FORBIDDEN_FIELD_SOURCE_KINDS or source_kind == "":
            raise Section1114OfflineSurfaceError("FIELD_SOURCE_KIND_REJECTED")
        if source_kind not in ADMISSIBLE_FIELD_SOURCE_KINDS:
            raise Section1114OfflineSurfaceError("FIELD_SOURCE_KIND_REJECTED")
        if freshness in FORBIDDEN_FRESHNESS or freshness != FRESHNESS_CONTEMPORANEOUS:
            raise Section1114OfflineSurfaceError("STALE_OR_INVALID_PROVENANCE")
        if lifecycle == "" or lifecycle != expected_lifecycle:
            raise Section1114OfflineSurfaceError("LIFECYCLE_IDENTITY_DRIFT")
        if backfill in {"true", "1", "yes"}:
            raise Section1114OfflineSurfaceError("BACKFILL_FORBIDDEN")
        if value == "":
            raise Section1114OfflineSurfaceError("REQUIRED_FIELD_MISSING")
        persisted = _text(record.get(name))
        if persisted == "" or persisted != value:
            raise Section1114OfflineSurfaceError("PROVENANCE_VALUE_MISMATCH")
        validated[name] = {
            "FIELD": name,
            "SOURCE_KIND": source_kind,
            "FRESHNESS": freshness,
            "LIFECYCLE_ID": lifecycle,
            "BACKFILL_ALLOWED": "false",
            "VALUE": value,
        }
    return validated


def validate_contemporaneous_no_backfill_persisted_record_v1(
    *,
    record: Mapping[str, Any],
    expected_identity: Mapping[str, Any],
    expected_lifecycle: object,
    expected_captured_at_utc: object,
    later_runtime_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if later_runtime_state:
        raise Section1114OfflineSurfaceError("LATER_RUNTIME_STATE_MUST_NOT_COMPLETE_CAPTURE")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if NO_TIMESTAMP_BACKFILL is not True:
        raise Section1114OfflineSurfaceError("NO_TIMESTAMP_BACKFILL_MUST_REMAIN_TRUE")
    if NO_SYNTHETIC_PRE_RESTART_PROVENANCE is not True:
        raise Section1114OfflineSurfaceError("NO_SYNTHETIC_PROVENANCE_MUST_REMAIN_TRUE")
    payload = dict(record or {})
    schema = _text(payload.get("schema_version"))
    if schema == "":
        raise Section1114OfflineSurfaceError("SCHEMA_MISSING")
    if schema != HANDOFF_SCHEMA_VERSION:
        raise Section1114OfflineSurfaceError("SCHEMA_OR_VERSION_MISMATCH")
    if _text(payload.get("DOCUMENT_CLASS")) != HANDOFF_DOCUMENT_CLASS:
        raise Section1114OfflineSurfaceError("DOCUMENT_CLASS_MISMATCH")
    provenance_class = _text(payload.get("provenance_class"))
    if provenance_class in FORBIDDEN_PROVENANCE_CLASSES or provenance_class == "":
        raise Section1114OfflineSurfaceError("FORBIDDEN_PROVENANCE")
    if provenance_class != CONTEMPORANEOUS_PROVENANCE_CLASS:
        raise Section1114OfflineSurfaceError("PROVENANCE_MISMATCH")
    missing = [name for name in REQUIRED_HANDOFF_FIELDS if _text(payload.get(name)) == ""]
    if missing:
        raise Section1114OfflineSurfaceError("MISSING_REQUIRED_HANDOFF_FIELDS")
    identity = dict(expected_identity or {})
    for name in IDENTITY_HANDOFF_FIELDS:
        actual = _text(payload.get(name))
        expected = _text(identity.get(name))
        if expected == "" or actual != expected:
            raise Section1114OfflineSurfaceError("IDENTITY_MISMATCH")
    pos = parse_handoff_pos_v1(payload.get("pos"))
    fill_sz = parse_handoff_pos_v1(identity.get("fillSz"))
    if pos is None or fill_sz is None or pos != fill_sz:
        raise Section1114OfflineSurfaceError("POS_MUST_DECIMAL_EQUAL_BOUND_IDENTITY")
    captured = _text(payload.get("captured_at_utc"))
    expected_captured = _text(expected_captured_at_utc)
    if captured == "" or expected_captured == "":
        raise Section1114OfflineSurfaceError("CAPTURE_TIMESTAMP_MISSING")
    if captured != expected_captured:
        raise Section1114OfflineSurfaceError("SOURCE_TIMESTAMP_REPLACED")
    lifecycle = _text(expected_lifecycle) or _text(payload.get("lifecycle_id"))
    if lifecycle == "":
        raise Section1114OfflineSurfaceError("LIFECYCLE_ID_MISSING")
    if _text(payload.get("lifecycle_id")) != lifecycle:
        raise Section1114OfflineSurfaceError("LIFECYCLE_IDENTITY_DRIFT")
    field_provenance = _require_persisted_field_provenance(
        record=payload,
        expected_lifecycle=lifecycle,
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CONTEMPORANEOUS_NO_BACKFILL_VALIDATION_V1",
        "VALID": True,
        "CONTEMPORANEOUS_VALID": True,
        "LEGACY_READABLE": True,
        "LEGACY_READABLE_IS_NOT_CONTEMPORANEOUS_VALID": True,
        "BACKFILL_USED": False,
        "SYNTHESIS_USED": False,
        "WALL_CLOCK_SUBSTITUTION": False,
        "LATER_RUNTIME_STATE_USED": False,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "field_provenance": field_provenance,
        "record": dict(payload),
    }


def refuse_incomplete_record_plus_later_runtime_state_v1(
    *,
    historical_record: Mapping[str, Any],
    later_runtime_state: Mapping[str, Any],
    expected_identity: Mapping[str, Any],
    expected_lifecycle: object,
    expected_captured_at_utc: object,
) -> dict[str, Any]:
    historical = dict(historical_record or {})
    runtime = dict(later_runtime_state or {})
    synthesized = dict(historical)
    for name in REQUIRED_HANDOFF_FIELDS:
        if _text(synthesized.get(name)) == "":
            candidate = runtime.get(name)
            if candidate is None and name in IDENTITY_HANDOFF_FIELDS:
                candidate = (runtime.get("bound_fill_identity") or {}).get(name)
            if candidate is None and name == "pos":
                candidate = runtime.get("peak_trade_owned_resulting_current_position_qty")
            if candidate is not None:
                synthesized[name] = candidate
    if "field_provenance" not in synthesized and "field_provenance" in runtime:
        synthesized["field_provenance"] = runtime["field_provenance"]
    if _text(synthesized.get("lifecycle_id")) == "" and "lifecycle_id" in runtime:
        synthesized["lifecycle_id"] = runtime["lifecycle_id"]
    if _text(synthesized.get("captured_at_utc")) == "" and "now_utc" in runtime:
        synthesized["captured_at_utc"] = runtime["now_utc"]
    try:
        validate_contemporaneous_no_backfill_persisted_record_v1(
            record=synthesized,
            expected_identity=expected_identity,
            expected_lifecycle=expected_lifecycle,
            expected_captured_at_utc=expected_captured_at_utc,
            later_runtime_state=runtime,
        )
    except Section1114OfflineSurfaceError as exc:
        return {
            "DOCUMENT_CLASS": "SECTION_11_14_NO_BACKFILL_REFUSAL_V1",
            "VALID_CONTEMPORANEOUS_CAPTURE_RECORD": False,
            "FAIL_CLOSED": True,
            "REASON": str(exc),
            "HISTORICAL_INCOMPLETE_PLUS_LATER_RUNTIME_IS_NOT_CONTEMPORANEOUS_VALID": True,
            "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        }
    raise Section1114OfflineSurfaceError("NO_BACKFILL_CONTRACT_BROKEN")


def read_contemporaneous_valid_handoff_v1(
    *,
    storage_root: Path,
    expected_identity: Mapping[str, Any],
    expected_lifecycle: object,
    expected_captured_at_utc: object,
    expected_attempt_identity: object,
    later_runtime_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    identity = dict(expected_identity or {})
    reader = read_validated_durable_pre_restart_handoff_v1(
        storage_root=storage_root,
        expected_inst_id=identity.get("instId"),
        expected_clordid=identity.get("clOrdId"),
        expected_ordid=identity.get("ordId"),
        expected_pos_side=identity.get("posSide"),
        expected_attempt_identity=expected_attempt_identity,
    )
    if reader["RESULT"] != RESULT_VALID_HANDOFF:
        raise Section1114OfflineSurfaceError(str(reader.get("REASON") or reader["RESULT"]))
    record = dict(reader.get("record") or {})
    validated = validate_contemporaneous_no_backfill_persisted_record_v1(
        record=record,
        expected_identity=identity,
        expected_lifecycle=expected_lifecycle,
        expected_captured_at_utc=expected_captured_at_utc,
        later_runtime_state=later_runtime_state,
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CONTEMPORANEOUS_VALID_READER_RESULT_V1",
        "RESULT": RESULT_VALID_HANDOFF,
        "CONTEMPORANEOUS_VALID": True,
        "LEGACY_READABLE_IS_NOT_CONTEMPORANEOUS_VALID": True,
        "reader": reader,
        "validation": validated,
    }


def prove_offline_capture_roundtrip_v1(
    *,
    storage_root: Path,
    bound_fill_identity: Mapping[str, Any],
    peak_trade_owned_resulting_current_position_qty: object,
    bound_fill_proven_at: object,
    capture_started_at: object,
    attempt_identity: object,
    lifecycle_id: object,
    field_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    original = copy.deepcopy(dict(bound_fill_identity))
    mutable = dict(bound_fill_identity)
    result = run_live_order_pre_restart_handoff_capture_v1(
        storage_root=storage_root,
        bound_fill_proven=True,
        bound_fill_kind=CANONICAL_BOUND_FILL_KIND,
        bound_fill_identity=mutable,
        peak_trade_owned_resulting_current_position_qty=(
            peak_trade_owned_resulting_current_position_qty
        ),
        source_kind=ADMISSIBLE_POS_SOURCE_KIND,
        unit=POS_UNIT,
        restart_already_occurred=False,
        restart_not_yet_occurred_proven=True,
        bound_fill_proven_at=bound_fill_proven_at,
        capture_started_at=capture_started_at,
        attempt_identity=attempt_identity,
        input_class=INPUT_CLASS_TEST_FIXTURE,
        lifecycle_id=lifecycle_id,
        lifecycle_event=REQUIRED_CAPTURE_TRIGGER,
        field_provenance=field_provenance,
    )
    mutable["clOrdId"] = "mutated-after-snapshot-must-not-rewrite-persist"
    mutable["ordId"] = "0000000000000000000"
    mutable["instId"] = "MUTATED-AFTER-SNAPSHOT"
    mutable["fillSz"] = "999"
    loaded = load_durable_handoff_record_v1(storage_root=storage_root)
    for name in IDENTITY_HANDOFF_FIELDS:
        if _text(loaded.get(name)) != _text(original.get(name)):
            raise Section1114OfflineSurfaceError("SNAPSHOT_MUTATION_REWROTE_PERSISTED_RECORD")
    if _text(loaded.get("pos")) != _text(peak_trade_owned_resulting_current_position_qty):
        raise Section1114OfflineSurfaceError("SNAPSHOT_MUTATION_REWROTE_PERSISTED_RECORD")
    contemporaneous = read_contemporaneous_valid_handoff_v1(
        storage_root=storage_root,
        expected_identity=original,
        expected_lifecycle=lifecycle_id,
        expected_captured_at_utc=capture_started_at,
        expected_attempt_identity=attempt_identity,
    )
    encoded = serialize_handoff_offline_v1(loaded)
    decoded = deserialize_handoff_offline_v1(encoded)
    for name in REQUIRED_HANDOFF_FIELDS:
        if _text(decoded.get(name)) != _text(loaded.get(name)):
            raise Section1114OfflineSurfaceError("ROUNDTRIP_FIELD_IDENTITY_DRIFT")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_OFFLINE_CAPTURE_ROUNDTRIP_PROOF_V1",
        "PASS": True,
        "TEST_FIXTURE": True,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "SNAPSHOT_IMMUTABLE_AFTER_BOUND_FILL_COPY": True,
        "caller_result": result,
        "persisted": loaded,
        "contemporaneous_reader": contemporaneous,
        "path": str(durable_handoff_path_v1(storage_root=storage_root)),
        "relative_path": f"{RELATIVE_DURABLE_DIR}/{HANDOFF_FILENAME}",
    }


def census_complete_capture_seam_v1(*, repo_root: object | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    dataflow = census_productive_capture_dataflow_v1(repo_root=root)
    if dataflow["HOOK_PRODUCTIVE_CALLER_COUNT"] != 1:
        raise Section1114OfflineSurfaceError("PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER")
    if dataflow["PRODUCTIVE_HOOK_CALLER"] != PRODUCTIVE_HOOK_CALLER:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_HOOK_CALLER_DRIFT")
    if dataflow["UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK"] != "PROVEN":
        raise Section1114OfflineSurfaceError("PRODUCTIVE_HOOK_CALLER_UNPROVEN")
    caller_census = census_productive_hook_caller_v1(repo_root=root)
    host_graph = compose_live_order_pre_restart_capture_host_graph_v1()
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_CENSUS_V1",
        "AUTHORITATIVE_CAPTURE_PRODUCER": AUTHORITATIVE_CAPTURE_PRODUCER,
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_PATH": CALLER_RELPATH,
        "HOST_JOIN_SYMBOL": HOST_JOIN_SYMBOL,
        "CAPTURE_HOOK": CAPTURE_HOOK,
        "CAPTURE_HOOK_PATH": HOOK_RELPATH,
        "CAPTURE_OWNER": CAPTURE_OWNER,
        "WRITER_SYMBOL": WRITER_SYMBOL,
        "WRITER_PATH": WRITER_RELPATH,
        "PRODUCER_SYMBOL": PRODUCER_SYMBOL,
        "PRODUCER_PATH": PRODUCER_RELPATH,
        "PRODUCER_ID": PRODUCER_ID,
        "STORAGE_OWNER": FIRST_OWNER_ID,
        "PERSIST_PATH": f"{RELATIVE_DURABLE_DIR}/{HANDOFF_FILENAME}",
        "READER_SYMBOL": "read_validated_durable_pre_restart_handoff_v1",
        "CONTEMPORANEOUS_VALIDATOR": ("validate_contemporaneous_no_backfill_persisted_record_v1"),
        "OVERWRITE_SEMANTICS": "IDEMPOTENT_SAME_IDENTITY_ONLY; NO_SECOND_IDENTITY",
        "APPEND_SEMANTICS": "FALSE_SINGLE_RECORD_REPLACE",
        "dataflow": dataflow,
        "caller_census": caller_census,
        "host_graph": host_graph,
    }


def bind_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1(
    *,
    repo_root: object | None = None,
) -> dict[str, Any]:
    census = census_complete_capture_seam_v1(repo_root=repo_root)
    table = bind_complete_capture_seam_field_table_v1()
    matrix = bind_required_field_provenance_matrix_v1()
    historical_reader = bind_restart_reader_provenance_and_consumer_v1()
    historical_missing = list(historical_reader["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    if "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL" not in historical_missing:
        raise Section1114OfflineSurfaceError("HISTORICAL_MISSING_PREDICATE_DRIFT")
    if historical_reader["COMPLETE_CAPTURE_SEAM"] != HISTORICAL_READER_BIND_COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("HISTORICAL_CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if COMPLETE_CAPTURE_SEAM not in COMPLETE_CAPTURE_SEAM_TAXONOMY:
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_TAXONOMY_DRIFT")
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    if table["REQUIRED_FIELD_PROVENANCE_COMPLETE"] is not True:
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_INCOMPLETE")
    if table["NO_BACKFILL_CONTRACT_PROVEN"] is not True:
        raise Section1114OfflineSurfaceError("NO_BACKFILL_CONTRACT_UNPROVEN")
    if census["PRODUCTIVE_HOOK_CALLER"] != PRODUCTIVE_HOOK_CALLER:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_HOOK_CALLER_DRIFT")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_"
            "PROVENANCE_AND_NO_BACKFILL_CONTRACT_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "AUTHORITATIVE_CAPTURE_PRODUCER": AUTHORITATIVE_CAPTURE_PRODUCER,
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": True,
        "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF": True,
        "CAPTURE_HOOK": CAPTURE_HOOK,
        "CAPTURE_OWNER": CAPTURE_OWNER,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "COMPLETE_CAPTURE_SEAM_TAXONOMY": list(COMPLETE_CAPTURE_SEAM_TAXONOMY),
        "HISTORICAL_READER_BIND_COMPLETE_CAPTURE_SEAM": (
            HISTORICAL_READER_BIND_COMPLETE_CAPTURE_SEAM
        ),
        "HISTORICAL_COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": historical_missing,
        "REQUIRED_FIELD_COUNT": table["HANDOFF_REQUIRED_FIELD_COUNT"],
        "REQUIRED_FIELD_PROVENANCE_COMPLETE": REQUIRED_FIELD_PROVENANCE_COMPLETE,
        "NO_BACKFILL_CONTRACT_PROVEN": NO_BACKFILL_CONTRACT_PROVEN,
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": (
            PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL
        ),
        "LEGACY_READABLE_IS_NOT_CONTEMPORANEOUS_VALID": (
            LEGACY_READABLE_IS_NOT_CONTEMPORANEOUS_VALID
        ),
        "OFFLINE_CAPTURE_ROUNDTRIP_PROOF": "CONTRACT_BOUND",
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "PARTIAL_CAPTURE_ALLOWED": PARTIAL_CAPTURE_ALLOWED,
        "RETROACTIVE_SYNTHESIS_ALLOWED": RETROACTIVE_SYNTHESIS_ALLOWED,
        "CAN_STRUCTURALLY_CONSTRUCT_COMPLETE_RECORD": True,
        "HAS_PRODUCTIVELY_CONSTRUCTED_COMPLETE_RECORD": False,
        "PROVEN_COMPLETE_FIELD_COUNT": matrix["PROVEN_COMPLETE_FIELD_COUNT"],
        "PROVEN_FAIL_CLOSED_FIELD_COUNT": matrix["PROVEN_FAIL_CLOSED_FIELD_COUNT"],
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "census": census,
        "caller_census": dict(census["caller_census"]),
        "host_graph": dict(census["host_graph"]),
        "required_field_table": table,
        "required_field_provenance_matrix": matrix,
    }


def prove_writer_rejects_wall_clock_substitution_v1(
    *,
    storage_root: Path,
    bound_fill_identity: Mapping[str, Any],
    peak_trade_owned_resulting_current_position_qty: object,
    attempt_identity: object,
) -> None:
    identity = dict(bound_fill_identity)
    try:
        commit_handoff_after_bound_fill_before_restart_v1(
            storage_root=storage_root,
            resulting_current_position_qty=peak_trade_owned_resulting_current_position_qty,
            unit=POS_UNIT,
            source_kind=ADMISSIBLE_POS_SOURCE_KIND,
            inst_id=identity["instId"],
            clordid=identity["clOrdId"],
            ord_id=identity["ordId"],
            pos_side=identity["posSide"],
            bound_fill_identity_exists=True,
            attempt_identity=attempt_identity,
            provenance_class=CONTEMPORANEOUS_PROVENANCE_CLASS,
            capture_trigger=REQUIRED_CAPTURE_TRIGGER,
            restart_already_occurred=False,
            bound_fill_identity=identity,
            now_utc="",
        )
    except Section1114OfflineSurfaceError as exc:
        if str(exc) != "CAPTURE_TIMESTAMP_MISSING":
            raise
        return
    raise Section1114OfflineSurfaceError("WALL_CLOCK_SUBSTITUTION_MUST_FAIL_CLOSED")


def classify_legacy_codec_document_class_synthesis_v1(
    *,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    document = dict(payload or {})
    synthesized = _text(document.get("DOCUMENT_CLASS")) == ""
    encoded = serialize_handoff_offline_v1(document)
    decoded = json.loads(encoded)
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LEGACY_CODEC_EPISTEMIC_SPLIT_V1",
        "LEGACY_READABLE": True,
        "CONTEMPORANEOUS_VALID": False,
        "LEGACY_READABLE_IS_NOT_CONTEMPORANEOUS_VALID": True,
        "DOCUMENT_CLASS_SYNTHESIZED": synthesized
        or _text(decoded.get("DOCUMENT_CLASS")) == HANDOFF_DOCUMENT_CLASS,
        "CODEC_MAY_STAMP_DOCUMENT_CLASS": True,
        "CODEC_STAMP_IS_NOT_CONTEMPORANEOUS_CAPTURE": True,
    }
