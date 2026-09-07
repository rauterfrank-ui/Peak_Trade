"""Complete contemporaneous capture-seam acceptance and required-field provenance.

Proves the capture-owner acceptance contract and traces every required
handoff field to its current producer/consumer path. Does not GET. Does
not POST. Does not execute the productive lifecycle hook as Live. Does
not claim COMPLETE_CAPTURE_SEAM=PROVEN. Does not invent
PROVEN_STRUCTURALLY. Does not promote LIVE_RESTART_RECONSTRUCTED.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    FORBIDDEN_BOUND_FILL_KINDS,
    HOOK_RELPATH,
    IDENTITY_FIELDS,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    PRODUCTIVE_S05_QTY_SOURCE,
    evaluate_productive_capture_gates_v1,
    require_future_bound_fill_identity_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_v1 import (
    PRODUCER_RELPATH,
    PRODUCER_SYMBOL,
    WRITER_RELPATH,
    WRITER_SYMBOL,
    census_symbol_call_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
    WRITER_SEAM_ID,
    construct_five_field_handoff_record_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    FORBIDDEN_INPUT_KEYS,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_bind_v1 import (
    bind_restart_reader_provenance_and_consumer_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    FORBIDDEN_PROVENANCE_CLASSES,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_UNIT,
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    bind_required_handoff_field_contracts_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    parse_handoff_pos_v1,
)

COMPLETE_CAPTURE_SEAM = "UNPROVEN"
COMPLETE_CAPTURE_SEAM_TAXONOMY: tuple[str, ...] = ("UNPROVEN", "PROVEN")
COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND = True
REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND = True
PARTIAL_CAPTURE_ALLOWED = False
RETROACTIVE_SYNTHESIS_ALLOWED = False
CONTEMPORANEOUS_IDENTITY_BINDING = "CONTRACT_PROVEN"
CONTEMPORANEOUS_PROVENANCE_BINDING = "CONTRACT_PROVEN"
CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED = False
INPUT_CLASS_TEST_FIXTURE = "TEST_FIXTURE"
INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT = "PRODUCTIVE_BOUND_FILL_INPUT"
ALLOWED_INPUT_CLASSES: frozenset[str] = frozenset(
    {INPUT_CLASS_TEST_FIXTURE, INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT}
)
FORBIDDEN_INPUT_CLASSES: frozenset[str] = frozenset(
    {
        "PRODUCTIVE_CAPTURE_EXECUTED",
        "LIVE_OBSERVED",
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED",
        "UNDECLARED",
        "",
    }
)
FORBIDDEN_FIELD_SOURCE_KINDS: frozenset[str] = frozenset(
    {
        "RESTART_READER",
        "RESTART_DERIVED",
        "HISTORICAL_EVIDENCE",
        "RETROACTIVE_SYNTHESIS",
        "VENUE_GET_COPY",
        "TIMESTAMP_BACKFILL",
        "STALE_CACHE",
        "FILL_SZ_COPY",
        "DEFAULT_VALUE",
        "SILENT_COERCION",
        "ACCOUNTING_ONLY",
        "POST_HOC_IDENTITY_MATCH",
    }
)
ADMISSIBLE_FIELD_SOURCE_KINDS: frozenset[str] = frozenset(
    {
        "PARAMETERIZED_BOUND_FILL_IDENTITY",
        "TEST_FIXTURE_PARAMETERIZED_BOUND_FILL_IDENTITY",
        "PEAK_TRADE_OWNED_S05_QTY",
        "TEST_FIXTURE_PEAK_TRADE_OWNED_S05_QTY",
    }
)
FRESHNESS_CONTEMPORANEOUS = "CONTEMPORANEOUS"
FORBIDDEN_FRESHNESS: frozenset[str] = frozenset(
    {"STALE", "STALE_CACHE", "BACKFILLED", "RECONSTRUCTED", "RESTART_DERIVED"}
)
FIELD_STATUS_PROVEN_COMPLETE = "PROVEN_COMPLETE"
FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT = "PROVEN_FAIL_CLOSED_IF_ABSENT"
FIELD_STATUS_UNPROVEN = "UNPROVEN"
FIELD_STATUS_CONTRADICTORY = "CONTRADICTORY"
ALLOWED_FIELD_STATUSES: frozenset[str] = frozenset(
    {
        FIELD_STATUS_PROVEN_COMPLETE,
        FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT,
        FIELD_STATUS_UNPROVEN,
        FIELD_STATUS_CONTRADICTORY,
    }
)
CASE_ADJUDICATION = (
    "CASE_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND_"
    "REQUIRED_FIELD_PROVENANCE_BOUND_COMPLETE_CAPTURE_SEAM_REMAINS_UNPROVEN"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_"
    "REQUIRES_SEPARATE_OWNER_GO_V1"
)
IDENTITY_HANDOFF_FIELDS: tuple[str, ...] = ("clOrdId", "ordId", "instId", "posSide")
HOOK_CONSUMER_SYMBOL = "run_capture_hook_after_bound_fill_before_restart_v1"
CAPTURE_OWNER_ACCEPTANCE_SYMBOL = "accept_complete_contemporaneous_capture_inputs_v1"
READER_SYMBOL = "read_validated_durable_pre_restart_handoff_v1"
PRODUCTIVE_HOOK_CALLER_SYMBOL = "call_pre_restart_handoff_capture_after_bound_fill_v1"
PRODUCTIVE_HOOK_CALLER_RELPATH = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
    "pre_restart_handoff_capture_caller_v1.py"
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _decimal(value: object) -> Decimal | None:
    text = _text(value)
    if text == "":
        return None
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite():
        return None
    return parsed


def census_productive_capture_dataflow_v1(*, repo_root: object | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    hook_census = census_symbol_call_graph_v1(
        repo_root=root,
        symbol=HOOK_CONSUMER_SYMBOL,
        definition_relpath=HOOK_RELPATH,
    )
    productive_hook_callers = [
        row for row in hook_census["rows"] if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    hook_caller_count = len(productive_hook_callers)
    upstream_join = (
        "PROVEN"
        if hook_caller_count == 1
        and productive_hook_callers[0]["FILE"] == PRODUCTIVE_HOOK_CALLER_RELPATH
        else "UNPROVEN_NO_PRODUCTIVE_HOOK_CALLER"
    )
    transitions = (
        {
            "TRANSITION_ID": "T1_PRODUCTIVE_BOUND_FILL",
            "PRODUCER": "LIVE_ORDER::LIVE_IDENTITY_BOUND_VENUE_FILL",
            "CONSUMER": HOOK_CONSUMER_SYMBOL,
            "CONCRETE_SYMBOL": CANONICAL_BOUND_FILL_KIND,
            "CONCRETE_PATH": (f"{PRODUCTIVE_HOOK_CALLER_RELPATH}::{PRODUCTIVE_HOOK_CALLER_SYMBOL}"),
            "INVOCATION_BINDING_RELATION": (
                "STRUCTURAL_PARAMETERIZATION_VIA_UNIQUE_PRODUCTIVE_HOOK_CALLER; "
                f"HOOK_PRODUCTIVE_CALLER_COUNT={hook_caller_count}"
            ),
            "DATA_TYPE_SCHEMA": "bound_fill_identity={clOrdId,ordId,instId,posSide,fillSz}",
            "OPTIONAL_OR_REQUIRED": "REQUIRED_AT_CAPTURE_OWNER_ACCEPTANCE",
            "PROVENANCE_PRESERVATION": "MUST_REMAIN_PARAMETERIZED_FROM_SAME_BOUND_FILL",
            "FRESHNESS_SEMANTICS": "BOUND_FILL_PROVEN_AT <= CAPTURE_STARTED_AT",
            "IDENTITY_SEMANTICS": "FUTURE_BOUND_IDENTITY_PARAMETERIZED_NOT_HISTORICAL_HARDCODE",
            "ERROR_BEHAVIOR": "CAPTURE_BEFORE_BOUND_FILL_PROVEN or BOUND_FILL_KIND_REJECTED",
            "FAIL_OPEN_OR_FAIL_CLOSED": "FAIL_CLOSED",
            "RUNTIME_EXECUTION_REQUIRED_FOR_PROOF": False,
            "RUNTIME_EXECUTION_REQUIRED_FOR_PRODUCTIVE_VALUE": True,
        },
        {
            "TRANSITION_ID": "T2_POST_FILL_NORMALIZATION",
            "PRODUCER": "NONE",
            "CONSUMER": "NONE",
            "CONCRETE_SYMBOL": "ABSENT",
            "CONCRETE_PATH": "NONE",
            "INVOCATION_BINDING_RELATION": (
                "NO_SEPARATE_POST_FILL_NORMALIZATION_OWNER_BETWEEN_BOUND_FILL_AND_HOOK"
            ),
            "DATA_TYPE_SCHEMA": "NONE",
            "OPTIONAL_OR_REQUIRED": "NOT_A_CANONICAL_SEAM",
            "PROVENANCE_PRESERVATION": "NOT_APPLICABLE",
            "FRESHNESS_SEMANTICS": "NOT_APPLICABLE",
            "IDENTITY_SEMANTICS": "NOT_APPLICABLE",
            "ERROR_BEHAVIOR": "NOT_INVENTED",
            "FAIL_OPEN_OR_FAIL_CLOSED": "FAIL_CLOSED_BY_ABSENCE_NOT_NORMALIZED",
            "RUNTIME_EXECUTION_REQUIRED_FOR_PROOF": False,
            "RUNTIME_EXECUTION_REQUIRED_FOR_PRODUCTIVE_VALUE": False,
        },
        {
            "TRANSITION_ID": "T3_LIFECYCLE_HOOK",
            "PRODUCER": HOOK_CONSUMER_SYMBOL,
            "CONSUMER": CAPTURE_OWNER_ACCEPTANCE_SYMBOL,
            "CONCRETE_SYMBOL": PRODUCTIVE_LIFECYCLE_HOOK,
            "CONCRETE_PATH": HOOK_RELPATH,
            "INVOCATION_BINDING_RELATION": (
                "UNIQUE_PRODUCTIVE_CALLER_OF_WRITER; "
                f"UNIQUE_PRODUCTIVE_HOOK_CALLER={PRODUCTIVE_HOOK_CALLER_SYMBOL}"
            ),
            "DATA_TYPE_SCHEMA": "hook kwargs including bound_fill_identity and S05 qty",
            "OPTIONAL_OR_REQUIRED": "REQUIRED",
            "PROVENANCE_PRESERVATION": "MUST_PASS_ACCEPTANCE_CONTRACT_BEFORE_WRITER",
            "FRESHNESS_SEMANTICS": "CAPTURE_WINDOW_TIMESTAMP_ORDERING=CONTRACT_PROVEN",
            "IDENTITY_SEMANTICS": "SAME_LIFECYCLE_AS_BOUND_FILL",
            "ERROR_BEHAVIOR": "Section1114OfflineSurfaceError; no partial record",
            "FAIL_OPEN_OR_FAIL_CLOSED": "FAIL_CLOSED",
            "RUNTIME_EXECUTION_REQUIRED_FOR_PROOF": False,
            "RUNTIME_EXECUTION_REQUIRED_FOR_PRODUCTIVE_VALUE": True,
        },
        {
            "TRANSITION_ID": "T4_CAPTURE_OWNER",
            "PRODUCER": PRODUCTIVE_CAPTURE_OWNER,
            "CONSUMER": WRITER_SYMBOL,
            "CONCRETE_SYMBOL": evaluate_productive_capture_gates_v1.__name__,
            "CONCRETE_PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1.py"
            ),
            "INVOCATION_BINDING_RELATION": "OWNER_GATES_THEN_WRITER_KWARGS",
            "DATA_TYPE_SCHEMA": "writer_kwargs plus identity and capture_window",
            "OPTIONAL_OR_REQUIRED": "REQUIRED",
            "PROVENANCE_PRESERVATION": CONTEMPORANEOUS_PROVENANCE_CLASS,
            "FRESHNESS_SEMANTICS": "NO_STALE_CACHE; NO_TIMESTAMP_BACKFILL",
            "IDENTITY_SEMANTICS": (f"{','.join(IDENTITY_FIELDS)} must equal bound_fill_identity"),
            "ERROR_BEHAVIOR": "hard fail; no synthesis; no defaulting",
            "FAIL_OPEN_OR_FAIL_CLOSED": "FAIL_CLOSED",
            "RUNTIME_EXECUTION_REQUIRED_FOR_PROOF": False,
            "RUNTIME_EXECUTION_REQUIRED_FOR_PRODUCTIVE_VALUE": True,
        },
        {
            "TRANSITION_ID": "T5_PRODUCER_AND_PERSIST",
            "PRODUCER": PRODUCER_SYMBOL,
            "CONSUMER": "durable_state/section_11_14_live_durable_pre_restart_handoff_v1/pre_restart",
            "CONCRETE_SYMBOL": WRITER_SYMBOL,
            "CONCRETE_PATH": WRITER_RELPATH,
            "INVOCATION_BINDING_RELATION": (
                f"{WRITER_SYMBOL} calls {PRODUCER_SYMBOL} then "
                "construct_five_field_handoff_record_v1 then atomic persist"
            ),
            "DATA_TYPE_SCHEMA": "HANDOFF_DOCUMENT_CLASS five required fields plus envelope",
            "OPTIONAL_OR_REQUIRED": "REQUIRED",
            "PROVENANCE_PRESERVATION": "envelope provenance_class stamped contemporaneous",
            "FRESHNESS_SEMANTICS": "captured_at_utc from capture_started_at; no backfill",
            "IDENTITY_SEMANTICS": "record identity copied from producer output",
            "ERROR_BEHAVIOR": "MISSING_REQUIRED_HANDOFF_FIELDS; no partial persist",
            "FAIL_OPEN_OR_FAIL_CLOSED": "FAIL_CLOSED",
            "RUNTIME_EXECUTION_REQUIRED_FOR_PROOF": False,
            "RUNTIME_EXECUTION_REQUIRED_FOR_PRODUCTIVE_VALUE": True,
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_CAPTURE_DATAFLOW_CENSUS_V1",
        "AUTHORITY_CLASS": "FORENSIC_OBSERVATION",
        "NAMING_SIMILARITY_IS_NOT_BINDING": True,
        "POST_FILL_NORMALIZATION_OWNER": "NONE",
        "HOOK_PRODUCTIVE_CALLER_COUNT": hook_caller_count,
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER_SYMBOL,
        "UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK": upstream_join,
        "WRITER_PRODUCTIVE_CALLER": HOOK_RELPATH,
        "PRODUCER_REMAINS_INTERNAL_TO_WRITER": True,
        "STORAGE_OWNER_IS_NOT_CAPTURE_OWNER": True,
        "STORAGE_OWNER": FIRST_OWNER_ID,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "SELECTED_CAPTURE_TRIGGER": REQUIRED_CAPTURE_TRIGGER,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCER_PATH": PRODUCER_RELPATH,
        "READER_IS_NOT_A_PRE_RESTART_SOURCE": True,
        "READER_SYMBOL": READER_SYMBOL,
        "transitions": list(transitions),
    }


def bind_required_field_provenance_matrix_v1() -> dict[str, Any]:
    historical = {row["FIELD_NAME"]: row for row in bind_required_handoff_field_contracts_v1()}
    identity_producer = (
        "LIVE_IDENTITY_BOUND_VENUE_FILL::bound_fill_identity parameterized into "
        f"{PRODUCTIVE_CAPTURE_OWNER}"
    )
    identity_producer_symbol = "require_future_bound_fill_identity_v1"
    rows = []
    for name in REQUIRED_HANDOFF_FIELDS:
        historical_row = historical[name]
        if name in IDENTITY_HANDOFF_FIELDS:
            row = {
                "FIELD": name,
                "CANONICAL_REQUIREMENT_SOURCE": (
                    "REQUIRED_HANDOFF_FIELDS+"
                    "LIVE_RESTART_RECONSTRUCTED identity equation+"
                    "FUTURE_BOUND_IDENTITY_PARAMETERIZATION"
                ),
                "PRODUCTIVE_PRODUCER": identity_producer,
                "PRODUCER_SYMBOL": identity_producer_symbol,
                "PRODUCER_VALUE_SEMANTICS": historical_row["SEMANTIC_MEANING"],
                "CONSUMER_SYMBOL": HOOK_CONSUMER_SYMBOL,
                "TRANSFER_PATH": (
                    "bound_fill_identity -> accept_complete_contemporaneous_capture_inputs_v1 "
                    f"-> evaluate_productive_capture_gates_v1 -> {PRODUCER_SYMBOL} -> "
                    "construct_five_field_handoff_record_v1"
                ),
                "IDENTITY_BINDING": "MUST_EQUAL_SAME_BOUND_FILL_LIFECYCLE",
                "FRESHNESS_BINDING": "CONTEMPORANEOUS_WITH_BOUND_FILL_PROVEN_AT",
                "PROVENANCE_BINDING": CONTEMPORANEOUS_PROVENANCE_CLASS,
                "NULLABILITY": "FORBIDDEN",
                "MISSING_BEHAVIOR": "HARD_FAIL",
                "AMBIGUITY_BEHAVIOR": "HARD_FAIL",
                "CAPTURE_OWNER_ACCEPTANCE_RULE": (
                    "nonempty exact string from the same bound-fill identity; "
                    "no historical BOUND_* hardcode; no restart-reader source"
                ),
                "EVIDENCE": (
                    f"{HOOK_RELPATH}; {PRODUCER_RELPATH}; "
                    "restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1.py"
                ),
                "STATUS": FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT,
                "UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK": "PROVEN",
                "HISTORICAL_BOUND_IDENTITY_IS_NOT_CURRENT_PRODUCER": True,
            }
        else:
            row = {
                "FIELD": name,
                "CANONICAL_REQUIREMENT_SOURCE": (
                    "REQUIRED_HANDOFF_FIELDS+S05_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY"
                ),
                "PRODUCTIVE_PRODUCER": PRODUCTIVE_S05_QTY_SOURCE,
                "PRODUCER_SYMBOL": PRODUCER_SYMBOL,
                "PRODUCER_VALUE_SEMANTICS": (
                    "Peak_Trade-owned resulting/current position qty; unsigned "
                    "venue contract count; Decimal-equal fillSz; not fillSz copy"
                ),
                "CONSUMER_SYMBOL": HOOK_CONSUMER_SYMBOL,
                "TRANSFER_PATH": (
                    "peak_trade_owned_resulting_current_position_qty -> "
                    "accept_complete_contemporaneous_capture_inputs_v1 -> "
                    f"{PRODUCER_SYMBOL} -> construct_five_field_handoff_record_v1.pos"
                ),
                "IDENTITY_BINDING": "POS_MUST_DECIMAL_EQUAL_BOUND_FILL_SZ_OF_SAME_LIFECYCLE",
                "FRESHNESS_BINDING": "CONTEMPORANEOUS_AT_HANDOFF_COMMIT_AFTER_BOUND_FILL",
                "PROVENANCE_BINDING": CONTEMPORANEOUS_PROVENANCE_CLASS,
                "NULLABILITY": "FORBIDDEN",
                "MISSING_BEHAVIOR": "HARD_FAIL",
                "AMBIGUITY_BEHAVIOR": "HARD_FAIL",
                "CAPTURE_OWNER_ACCEPTANCE_RULE": (
                    "nonempty unsigned Decimal; source_kind must be "
                    f"{ADMISSIBLE_POS_SOURCE_KIND}; unit must be {POS_UNIT}; "
                    "must Decimal-equal fillSz; FILL_SZ_COPY forbidden"
                ),
                "EVIDENCE": (
                    f"{PRODUCER_RELPATH}; PRODUCTIVE_S05_QTY_SOURCE={PRODUCTIVE_S05_QTY_SOURCE}"
                ),
                "STATUS": FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT,
                "UPSTREAM_LIVE_ORDER_JOIN_TO_HOOK": "PROVEN",
                "HISTORICAL_BOUND_IDENTITY_IS_NOT_CURRENT_PRODUCER": True,
            }
        if row["STATUS"] not in ALLOWED_FIELD_STATUSES:
            raise Section1114OfflineSurfaceError("FIELD_STATUS_TAXONOMY_DRIFT")
        rows.append(row)
    counts = {
        FIELD_STATUS_PROVEN_COMPLETE: sum(
            1 for row in rows if row["STATUS"] == FIELD_STATUS_PROVEN_COMPLETE
        ),
        FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT: sum(
            1 for row in rows if row["STATUS"] == FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT
        ),
        FIELD_STATUS_UNPROVEN: sum(1 for row in rows if row["STATUS"] == FIELD_STATUS_UNPROVEN),
        FIELD_STATUS_CONTRADICTORY: sum(
            1 for row in rows if row["STATUS"] == FIELD_STATUS_CONTRADICTORY
        ),
    }
    if len(rows) != len(REQUIRED_HANDOFF_FIELDS):
        raise Section1114OfflineSurfaceError("REQUIRED_HANDOFF_FIELD_COUNT_DRIFT")
    if counts[FIELD_STATUS_CONTRADICTORY] != 0:
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_CONTRADICTION")
    if counts[FIELD_STATUS_UNPROVEN] != 0:
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_UNPROVEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_REQUIRED_FIELD_PROVENANCE_MATRIX_V1",
        "HANDOFF_REQUIRED_FIELD_COUNT": len(rows),
        "PROVEN_COMPLETE_FIELD_COUNT": counts[FIELD_STATUS_PROVEN_COMPLETE],
        "PROVEN_FAIL_CLOSED_FIELD_COUNT": counts[FIELD_STATUS_PROVEN_FAIL_CLOSED_IF_ABSENT],
        "UNPROVEN_FIELD_COUNT": counts[FIELD_STATUS_UNPROVEN],
        "CONTRADICTORY_FIELD_COUNT": counts[FIELD_STATUS_CONTRADICTORY],
        "PARTIAL_CAPTURE_ALLOWED": PARTIAL_CAPTURE_ALLOWED,
        "RETROACTIVE_SYNTHESIS_ALLOWED": RETROACTIVE_SYNTHESIS_ALLOWED,
        "SCHEMA_CHANGE_REQUIRED": False,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "rows": rows,
    }


def adjudicate_contemporaneousness_v1() -> dict[str, Any]:
    properties = (
        {
            "PROPERTY": "SAME_BOUND_FILL_LIFECYCLE_NOT_LATER_RECONSTRUCTION",
            "STATUS": "CONTRACT_PROVEN",
            "PROOF": (
                "accept_complete_contemporaneous_capture_inputs_v1 requires one "
                "lifecycle_id and rejects restart_derived/historical/restart-reader sources"
            ),
        },
        {
            "PROPERTY": "FILL_ORDER_INSTRUMENT_POSITION_IDENTITY_CANNOT_DRIFT",
            "STATUS": "CONTRACT_PROVEN",
            "PROOF": (
                "identity fields must exact-match the same bound_fill_identity; "
                "duplicate conflicting identity hard-fails"
            ),
        },
        {
            "PROPERTY": "STALE_CACHED_VALUE_CANNOT_PASS_AS_CONTEMPORANEOUS",
            "STATUS": "CONTRACT_PROVEN",
            "PROOF": "forbidden freshness STALE/STALE_CACHE/BACKFILLED/RECONSTRUCTED/RESTART_DERIVED",
        },
        {
            "PROPERTY": "NO_RETROACTIVE_SYNTHESIS_OF_MISSING_REQUIRED_FIELDS",
            "STATUS": "CONTRACT_PROVEN",
            "PROOF": "missing required field or provenance hard-fails; no defaults; no coercion",
        },
        {
            "PROPERTY": "RESTART_READER_IS_NOT_A_PRE_RESTART_SOURCE",
            "STATUS": "CONTRACT_PROVEN",
            "PROOF": "source_is_restart_reader and RESTART_READER source_kind hard-fail",
        },
        {
            "PROPERTY": "HISTORICAL_EVIDENCE_IS_NOT_CURRENT_RUNTIME_EVIDENCE",
            "STATUS": "CONTRACT_PROVEN",
            "PROOF": "source_is_historical_evidence and HISTORICAL_EVIDENCE source_kind hard-fail",
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CONTEMPORANEOUSNESS_ADJUDICATION_V1",
        "CONTEMPORANEOUS_IDENTITY_BINDING": CONTEMPORANEOUS_IDENTITY_BINDING,
        "CONTEMPORANEOUS_PROVENANCE_BINDING": CONTEMPORANEOUS_PROVENANCE_BINDING,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "ENVELOPE_PROVENANCE_IS_NOT_EMPIRICAL_LIVE_OBSERVATION": True,
        "TEST_FIXTURE_IS_NOT_PRODUCTIVE_CAPTURE": True,
        "properties": list(properties),
    }


def build_test_fixture_field_provenance_v1(
    *,
    bound_fill_identity: Mapping[str, Any],
    lifecycle_id: object,
) -> dict[str, Any]:
    identity = require_future_bound_fill_identity_v1(bound_fill_identity=bound_fill_identity)
    lifecycle = _text(lifecycle_id)
    if lifecycle == "":
        raise Section1114OfflineSurfaceError("TEST_FIXTURE_LIFECYCLE_ID_MISSING")
    rows: dict[str, dict[str, str]] = {}
    for name in IDENTITY_HANDOFF_FIELDS:
        rows[name] = {
            "FIELD": name,
            "INPUT_CLASS": INPUT_CLASS_TEST_FIXTURE,
            "PRODUCER_SYMBOL": identity_producer_symbol_for_tests(),
            "SOURCE_KIND": "TEST_FIXTURE_PARAMETERIZED_BOUND_FILL_IDENTITY",
            "FRESHNESS": FRESHNESS_CONTEMPORANEOUS,
            "LIFECYCLE_ID": lifecycle,
            "VALUE": identity[name],
        }
    rows["pos"] = {
        "FIELD": "pos",
        "INPUT_CLASS": INPUT_CLASS_TEST_FIXTURE,
        "PRODUCER_SYMBOL": PRODUCTIVE_S05_QTY_SOURCE,
        "SOURCE_KIND": "TEST_FIXTURE_PEAK_TRADE_OWNED_S05_QTY",
        "FRESHNESS": FRESHNESS_CONTEMPORANEOUS,
        "LIFECYCLE_ID": lifecycle,
        "VALUE": identity["fillSz"],
    }
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_TEST_FIXTURE_FIELD_PROVENANCE_V1",
        "INPUT_CLASS": INPUT_CLASS_TEST_FIXTURE,
        "TEST_FIXTURE": True,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "LIFECYCLE_ID": lifecycle,
        "fields": rows,
    }


def identity_producer_symbol_for_tests() -> str:
    return "TEST_FIXTURE::require_future_bound_fill_identity_v1"


def _require_input_class(input_class: object) -> str:
    klass = _text(input_class)
    if klass in FORBIDDEN_INPUT_CLASSES or klass not in ALLOWED_INPUT_CLASSES:
        raise Section1114OfflineSurfaceError("INPUT_CLASS_REJECTED")
    return klass


def _require_field_provenance(
    *,
    field_name: str,
    provenance: Mapping[str, Any],
    expected_lifecycle: str,
    input_class: str,
) -> dict[str, str]:
    payload = dict(provenance or {})
    source_kind = _text(payload.get("SOURCE_KIND"))
    freshness = _text(payload.get("FRESHNESS"))
    lifecycle = _text(payload.get("LIFECYCLE_ID"))
    declared_class = _text(payload.get("INPUT_CLASS") or input_class)
    if declared_class != input_class:
        raise Section1114OfflineSurfaceError("FIELD_INPUT_CLASS_MISMATCH")
    if source_kind in FORBIDDEN_FIELD_SOURCE_KINDS or source_kind == "":
        raise Section1114OfflineSurfaceError("FIELD_SOURCE_KIND_REJECTED")
    if source_kind not in ADMISSIBLE_FIELD_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError("FIELD_SOURCE_KIND_REJECTED")
    if freshness in FORBIDDEN_FRESHNESS or freshness != FRESHNESS_CONTEMPORANEOUS:
        raise Section1114OfflineSurfaceError("STALE_OR_INVALID_PROVENANCE")
    if lifecycle == "" or lifecycle != expected_lifecycle:
        raise Section1114OfflineSurfaceError("LIFECYCLE_IDENTITY_DRIFT")
    if field_name in IDENTITY_HANDOFF_FIELDS:
        expected_source_prefix = "PARAMETERIZED_BOUND_FILL_IDENTITY"
        if input_class == INPUT_CLASS_TEST_FIXTURE:
            expected_source_prefix = "TEST_FIXTURE_PARAMETERIZED_BOUND_FILL_IDENTITY"
        if source_kind != expected_source_prefix:
            raise Section1114OfflineSurfaceError("IDENTITY_SOURCE_KIND_REJECTED")
    if field_name == "pos":
        expected_pos_source = "PEAK_TRADE_OWNED_S05_QTY"
        if input_class == INPUT_CLASS_TEST_FIXTURE:
            expected_pos_source = "TEST_FIXTURE_PEAK_TRADE_OWNED_S05_QTY"
        if source_kind != expected_pos_source:
            raise Section1114OfflineSurfaceError("POS_SOURCE_KIND_REJECTED")
    return {
        "FIELD": field_name,
        "INPUT_CLASS": declared_class,
        "SOURCE_KIND": source_kind,
        "FRESHNESS": freshness,
        "LIFECYCLE_ID": lifecycle,
        "PRODUCER_SYMBOL": _text(payload.get("PRODUCER_SYMBOL")),
        "VALUE": _text(payload.get("VALUE")),
    }


def accept_complete_contemporaneous_capture_inputs_v1(
    *,
    input_class: object,
    bound_fill_proven: object,
    bound_fill_kind: object,
    bound_fill_identity: Mapping[str, Any] | None,
    peak_trade_owned_resulting_current_position_qty: object,
    source_kind: object,
    unit: object,
    restart_already_occurred: object,
    restart_not_yet_occurred_proven: object,
    bound_fill_proven_at: object,
    capture_started_at: object,
    attempt_identity: object,
    lifecycle_id: object,
    field_provenance: Mapping[str, Any] | None,
    restart_boundary_at: object | None = None,
    extra_fields: Mapping[str, Any] | None = None,
    restart_derived: object = False,
    source_is_restart_reader: object = False,
    source_is_historical_evidence: object = False,
    contemporaneous_productive_capture_executed: object = False,
) -> dict[str, Any]:
    klass = _require_input_class(input_class)
    if contemporaneous_productive_capture_executed is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    if restart_derived is True:
        raise Section1114OfflineSurfaceError("RESTART_DERIVED_INPUT_FORBIDDEN")
    if source_is_restart_reader is True:
        raise Section1114OfflineSurfaceError("RESTART_READER_IS_NOT_A_PRE_RESTART_SOURCE")
    if source_is_historical_evidence is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_EVIDENCE_IS_NOT_CURRENT_RUNTIME")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if NO_TIMESTAMP_BACKFILL is not True:
        raise Section1114OfflineSurfaceError("NO_TIMESTAMP_BACKFILL_MUST_REMAIN_TRUE")
    if NO_SYNTHETIC_PRE_RESTART_PROVENANCE is not True:
        raise Section1114OfflineSurfaceError("NO_SYNTHETIC_PROVENANCE_MUST_REMAIN_TRUE")
    if PARTIAL_CAPTURE_ALLOWED is True:
        raise Section1114OfflineSurfaceError("PARTIAL_CAPTURE_MUST_REMAIN_FORBIDDEN")
    lifecycle = _text(lifecycle_id)
    if lifecycle == "":
        raise Section1114OfflineSurfaceError("LIFECYCLE_ID_MISSING")
    identity = require_future_bound_fill_identity_v1(bound_fill_identity=bound_fill_identity)
    extras = dict(extra_fields or {})
    forbidden_keys = sorted(name for name in extras if name in FORBIDDEN_INPUT_KEYS)
    if forbidden_keys:
        raise Section1114OfflineSurfaceError("FORBIDDEN_DERIVATION_FIELD")
    for name in IDENTITY_HANDOFF_FIELDS:
        extra_value = _text(extras.get(name))
        if extra_value != "" and extra_value != identity[name]:
            raise Section1114OfflineSurfaceError("AMBIGUOUS_DUPLICATE_IDENTITY")
    extra_pos = _text(extras.get("pos"))
    if extra_pos != "":
        extra_pos_value = _decimal(extra_pos)
        fill_sz_for_dup = parse_handoff_pos_v1(identity["fillSz"])
        if extra_pos_value is None or fill_sz_for_dup is None or extra_pos_value != fill_sz_for_dup:
            raise Section1114OfflineSurfaceError("AMBIGUOUS_DUPLICATE_IDENTITY")
    provenance_root = dict(field_provenance or {})
    provenance_fields = dict(provenance_root.get("fields") or provenance_root)
    missing_provenance = [name for name in REQUIRED_HANDOFF_FIELDS if name not in provenance_fields]
    if missing_provenance:
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_PROVENANCE_MISSING")
    validated_provenance: dict[str, dict[str, str]] = {}
    for name in REQUIRED_HANDOFF_FIELDS:
        validated_provenance[name] = _require_field_provenance(
            field_name=name,
            provenance=dict(provenance_fields.get(name) or {}),
            expected_lifecycle=lifecycle,
            input_class=klass,
        )
    for name in IDENTITY_HANDOFF_FIELDS:
        actual = _text(validated_provenance[name].get("VALUE"))
        if actual == "":
            raise Section1114OfflineSurfaceError("REQUIRED_FIELD_MISSING")
        if actual != identity[name]:
            raise Section1114OfflineSurfaceError("IDENTITY_MISMATCH")
    qty_text = _text(peak_trade_owned_resulting_current_position_qty)
    if qty_text == "":
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_MISSING")
    pos_provenance_value = _text(validated_provenance["pos"].get("VALUE"))
    if pos_provenance_value == "":
        raise Section1114OfflineSurfaceError("REQUIRED_FIELD_MISSING")
    qty = _decimal(qty_text)
    fill_sz = parse_handoff_pos_v1(identity["fillSz"])
    pos_prov = _decimal(pos_provenance_value)
    if qty is None or fill_sz is None or pos_prov is None:
        raise Section1114OfflineSurfaceError("POS_MALFORMED")
    if qty != fill_sz or pos_prov != fill_sz:
        raise Section1114OfflineSurfaceError("POS_MUST_DECIMAL_EQUAL_BOUND_IDENTITY")
    kind = _text(bound_fill_kind)
    if kind in FORBIDDEN_BOUND_FILL_KINDS or kind != CANONICAL_BOUND_FILL_KIND:
        raise Section1114OfflineSurfaceError("BOUND_FILL_KIND_REJECTED")
    gates = evaluate_productive_capture_gates_v1(
        bound_fill_proven=bound_fill_proven,
        bound_fill_kind=bound_fill_kind,
        bound_fill_identity=identity,
        peak_trade_owned_resulting_current_position_qty=qty_text,
        source_kind=source_kind,
        unit=unit,
        restart_already_occurred=restart_already_occurred,
        restart_not_yet_occurred_proven=restart_not_yet_occurred_proven,
        bound_fill_proven_at=bound_fill_proven_at,
        capture_started_at=capture_started_at,
        restart_boundary_at=restart_boundary_at,
        attempt_identity=attempt_identity,
        extra_fields=extras,
    )
    produced = {
        "clOrdId": identity["clOrdId"],
        "ordId": identity["ordId"],
        "instId": identity["instId"],
        "posSide": identity["posSide"],
        "pos": format(qty, "f"),
    }
    record = construct_five_field_handoff_record_v1(
        producer_output=produced,
        attempt_identity=attempt_identity,
        captured_at_utc=capture_started_at,
        bound_fill_identity=identity,
    )
    if str(record.get("provenance_class") or "").strip() in FORBIDDEN_PROVENANCE_CLASSES:
        raise Section1114OfflineSurfaceError("FORBIDDEN_PROVENANCE")
    missing_record = [name for name in REQUIRED_HANDOFF_FIELDS if _text(record.get(name)) == ""]
    if missing_record:
        raise Section1114OfflineSurfaceError("PARTIAL_CAPTURE_FORBIDDEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CONTEMPORANEOUS_CAPTURE_ACCEPTANCE_V1",
        "ALLOWED": True,
        "INPUT_CLASS": klass,
        "TEST_FIXTURE": klass == INPUT_CLASS_TEST_FIXTURE,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "PARTIAL_CAPTURE": False,
        "COMPLETE_RECORD_STRUCTURALLY_CONSTRUCTIBLE": True,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "LIFECYCLE_ID": lifecycle,
        "CONTEMPORANEOUS_IDENTITY_BINDING": CONTEMPORANEOUS_IDENTITY_BINDING,
        "CONTEMPORANEOUS_PROVENANCE_BINDING": CONTEMPORANEOUS_PROVENANCE_BINDING,
        "identity": dict(identity),
        "record": dict(record),
        "field_provenance": validated_provenance,
        "writer_kwargs": dict(gates["writer_kwargs"]),
        "gates": dict(gates),
    }


def bind_complete_contemporaneous_capture_seam_and_required_field_provenance_v1(
    *,
    repo_root: object | None = None,
) -> dict[str, Any]:
    dataflow = census_productive_capture_dataflow_v1(repo_root=repo_root)
    matrix = bind_required_field_provenance_matrix_v1()
    contemporaneous = adjudicate_contemporaneousness_v1()
    reader_binding = bind_restart_reader_provenance_and_consumer_v1()
    missing = list(reader_binding["COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"])
    if "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL" not in missing:
        raise Section1114OfflineSurfaceError("MISSING_CONTEMPORANEOUS_PREDICATE_DRIFT")
    seam = str(reader_binding["COMPLETE_CAPTURE_SEAM"] or "").strip()
    if seam not in COMPLETE_CAPTURE_SEAM_TAXONOMY:
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_TAXONOMY_DRIFT")
    if seam != COMPLETE_CAPTURE_SEAM:
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("HISTORICAL_CANARY_MUST_REMAIN_UNOBSERVED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_"
            "AND_REQUIRED_FIELD_PROVENANCE_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "STRUCTURAL_RUNTIME_BINDING_PROVEN": True,
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "COMPLETE_CAPTURE_SEAM_TAXONOMY": list(COMPLETE_CAPTURE_SEAM_TAXONOMY),
        "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND": (
            COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND
        ),
        "REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND": REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": False,
        "CONTEMPORANEOUS_IDENTITY_BINDING": CONTEMPORANEOUS_IDENTITY_BINDING,
        "CONTEMPORANEOUS_PROVENANCE_BINDING": CONTEMPORANEOUS_PROVENANCE_BINDING,
        "RETROACTIVE_SYNTHESIS_ALLOWED": RETROACTIVE_SYNTHESIS_ALLOWED,
        "PARTIAL_CAPTURE_ALLOWED": PARTIAL_CAPTURE_ALLOWED,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "HANDOFF_REQUIRED_FIELD_COUNT": matrix["HANDOFF_REQUIRED_FIELD_COUNT"],
        "PROVEN_COMPLETE_FIELD_COUNT": matrix["PROVEN_COMPLETE_FIELD_COUNT"],
        "PROVEN_FAIL_CLOSED_FIELD_COUNT": matrix["PROVEN_FAIL_CLOSED_FIELD_COUNT"],
        "UNPROVEN_FIELD_COUNT": matrix["UNPROVEN_FIELD_COUNT"],
        "CONTRADICTORY_FIELD_COUNT": matrix["CONTRADICTORY_FIELD_COUNT"],
        "CAN_STRUCTURALLY_CONSTRUCT_COMPLETE_RECORD": True,
        "HAS_PRODUCTIVELY_CONSTRUCTED_COMPLETE_RECORD": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "dataflow": dataflow,
        "required_field_provenance_matrix": matrix,
        "contemporaneousness": contemporaneous,
        "reader_binding": {
            "COMPLETE_CAPTURE_SEAM": reader_binding["COMPLETE_CAPTURE_SEAM"],
            "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        },
    }
