"""§11.14 Live handoff complete-capture-seam proof.

Forensic architecture, dataflow, and implementability adjudication.
Does not implement a producer, mint a storage owner, bind a writer or
reader, GET, POST, or execute a restart. Historical POS_SEMANTICS=UNPROVEN
records are not reinterpreted.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
    FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD,
    HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
    HISTORICAL_HANDOFF_PRODUCTIVE_BINDING,
    HISTORICAL_HANDOFF_READER_PRESENT,
    HISTORICAL_HANDOFF_WRITER_PRESENT,
    VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    HANDOFF_DOCUMENT_CLASS,
    HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
    OPTIONAL_TEMPORAL_FIELDS,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_and_capture_architecture_adjudication_v1 import (
    bind_capture_seam_graph_census_v1,
    bind_durability_contract_adjudication_v1,
    bind_writer_reader_contract_adjudication_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_census_matrix_v1 import (
    bind_section_11_14_live_handoff_owner_census_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_vacancy_contract_v1 import (
    PROPOSED_FIRST_OWNER_ID,
    bind_section_11_14_live_handoff_owner_vacancy_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_census_v1 import (
    bind_pos_producer_census_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    FORBIDDEN_DERIVATIONS,
    POS_SEMANTICS,
    POS_SIGN_SEMANTICS,
    POS_TEMPORAL_MEANING,
    POS_UNIT,
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
    bind_new_pos_producer_contract_v1,
    bind_pos_producer_semantics_and_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS as HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    bind_live_order_timeline_capture_v1,
    bind_required_field_contract_v1,
)

COMPLETE_CAPTURE_SEAM = "UNPROVEN"
COMPLETE_CAPTURE_SEAM_PROOF_STATUS = "CLOSED_UNPROVEN_NO_INVENTION"
CAPTURE_TRIGGER_STATUS = "REQUIRED_WINDOW_BOUND_PRODUCTIVE_TRIGGER_UNBOUND"
SELECTED_CAPTURE_TRIGGER = "REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART"
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION_V1"
)
PROPOSED_NEXT_IMPLEMENTATION_WORKPACKAGE = PROPOSED_NEXT_SLICE
HANDOFF_RECORD_CONTRACT_STATUS = "BOUND_FIVE_REQUIRED_FIELDS_PLUS_S05_POS_SEMANTICS_NO_SCHEMA_V2"
_REJECTED = "POS_DERIVATION_REJECTED"
_TRUE = "true"
_FALSE = "false"

_SEAM_PREDICATES: tuple[str, ...] = (
    "POS_SEMANTICS_PROVEN",
    "SELECTED_SEMANTIC_UNIQUE",
    "SELECTED_SEMANTIC_ID_IS_S05",
    "NEW_PRODUCER_IMPLEMENTED",
    "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED",
    "CAPTURE_TRIGGER_PRODUCTIVELY_BOUND",
    "REQUIRED_WINDOW_AFTER_BOUND_FILL_AT_HANDOFF_COMMIT_BEFORE_RESTART",
    "ALL_FIVE_REQUIRED_FIELDS_CONTEMPORANEOUS_PEAK_TRADE_OWNED_AT_SAME_SEAM",
    "RECORD_CONTRACT_BOUND",
    "STORAGE_OWNER_MINTED",
    "STORAGE_OWNER_IS_PROPOSED_FIRST_OWNER_NOT_FORBIDDEN_REUSE",
    "WRITER_BOUND",
    "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM",
    "FAIL_CLOSED_ON_CAPTURE_FAILURE",
    "READER_BOUND",
    "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL",
    "STALE_DATA_REJECTED_BY_BOUND_READER",
    "MALFORMED_DATA_REJECTED_BY_BOUND_READER",
    "NO_RETROACTIVE_SYNTHESIS",
    "NO_TIMESTAMP_BACKFILL",
    "NO_SYNTHETIC_PRE_RESTART_PROVENANCE",
    "NO_HISTORICAL_REINTERPRETATION",
    "RESTART_CONSUMER_BOUND",
    "PROCESS_RESTART_READABLE_HANDOFF_RECORD",
)


def _failure(
    *,
    case_id: str,
    current_behavior: str,
    required_behavior: str,
    proven_or_unproven: str,
    fail_open_or_fail_closed: str,
    implementation_gap: str,
) -> dict[str, str]:
    if proven_or_unproven not in {"PROVEN", "UNPROVEN"}:
        raise Section1114OfflineSurfaceError("FAILURE_MATRIX_PROVENANCE_TOKEN_INVALID")
    if fail_open_or_fail_closed not in {"FAIL_CLOSED", "FAIL_OPEN", "NO_PATH"}:
        raise Section1114OfflineSurfaceError("FAILURE_MATRIX_FAIL_MODE_INVALID")
    return {
        "CASE_ID": case_id,
        "CURRENT_BEHAVIOR": current_behavior,
        "REQUIRED_BEHAVIOR": required_behavior,
        "PROVEN_OR_UNPROVEN": proven_or_unproven,
        "FAIL_OPEN_OR_FAIL_CLOSED": fail_open_or_fail_closed,
        "IMPLEMENTATION_GAP": implementation_gap,
    }


def bind_s05_producer_recensus_v1() -> dict[str, Any]:
    historical = bind_pos_producer_census_v1()
    producer = bind_new_pos_producer_contract_v1()
    rows: list[dict[str, Any]] = []
    for row in historical["rows"]:
        updated = dict(row)
        if row["PRODUCER_ID"] == "LIVE_CANARY_RETURN_PAYLOAD":
            updated["DISPOSITION"] = _REJECTED
            updated["CAN_SATISFY_SECTION_11_14_POS"] = False
            updated["WHY"] = (
                "S05 requires Peak_Trade-owned resulting/current position qty. "
                "ACK return is partial identity plus plan sz. pos is omitted. "
                "Previous UNPROVEN disposition is not a producer."
            )
            updated["EVIDENCE"] = (
                "SELECTED_SEMANTIC_ID=S05; OKX_ORDER_DATA_ENTRY_FIELDS_V1 omits pos; "
                "PRE_RESTART_CAPTURE_SEAM=CANARY_ACK_RETURN_PARTIAL_IDENTITY_ONLY"
            )
        elif row["CAN_SATISFY_SECTION_11_14_POS"] is True:
            raise Section1114OfflineSurfaceError("HISTORICAL_ACCEPTABLE_PRODUCER_MUST_REMAIN_ZERO")
        else:
            updated["DISPOSITION"] = _REJECTED
            updated["CAN_SATISFY_SECTION_11_14_POS"] = False
        rows.append(updated)
    acceptable = [row for row in rows if row["CAN_SATISFY_SECTION_11_14_POS"] is True]
    rejected = [row for row in rows if row["DISPOSITION"] == _REJECTED]
    unproven = [row for row in rows if row["DISPOSITION"] == "POS_DERIVATION_UNPROVEN"]
    if acceptable:
        raise Section1114OfflineSurfaceError("S05_ACCEPTABLE_PRODUCER_MUST_REMAIN_ABSENT")
    if unproven:
        raise Section1114OfflineSurfaceError("S05_UNPROVEN_PRODUCER_MUST_BE_RESOLVED")
    if producer["NEW_PRODUCER_IMPLEMENTED"] is True:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_REMAIN_UNIMPLEMENTED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_PRODUCER_RECENSUS_V1",
        "POS_SEMANTICS": POS_SEMANTICS,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "PRODUCER_CANDIDATE_COUNT": len(rows),
        "POS_ACCEPTABLE_PRODUCER_COUNT": 0,
        "POS_REJECTED_PRODUCER_COUNT": len(rejected),
        "POS_UNPROVEN_PRODUCER_COUNT": 0,
        "SELECTED_PRODUCTIVE_PRODUCER": "NONE",
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": False,
        "PRODUCER_ID": PRODUCER_ID,
        "PRODUCER_CONTRACT_COMPLETE": True,
        "RESULTING_CURRENT_POSITION_QTY_ARISE_TODAY": False,
        "ARISE_AFTER_MUTATION_CRITICAL_EVENT": False,
        "VENUE_CONTRACT_COUNT_BASED_PRODUCTIVE": False,
        "UNSIGNED_S05_PRODUCTIVE": False,
        "FLAT_LONG_SHORT_SEMANTICALLY_UNAMBIGUOUS_PRODUCTIVE": False,
        "COMPETING_SUITABLE_PRODUCTIVE_PRODUCER_COUNT": 0,
        "NAMING_MATCH_IS_NOT_SEMANTIC_IDENTITY": True,
        "HISTORICAL_CENSUS_NOT_REINTERPRETED": True,
        "HISTORICAL_UNPROVEN_ACK_RETURN_NOW_REJECTED_AGAINST_S05": True,
        "FORBIDDEN_DERIVATIONS": list(FORBIDDEN_DERIVATIONS),
        "rows": rows,
        "contracted_producer": {
            "PRODUCER_ID": PRODUCER_ID,
            "IMPLEMENTED": False,
            "PRODUCTIVE": False,
            "PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_pos_producer_semantics_and_contract_v1.py"
            ),
            "SYMBOL": "bind_new_pos_producer_contract_v1",
            "SYMBOL_IS_NOT_IMPLEMENTATION": True,
        },
    }


def bind_capture_trigger_adjudication_v1() -> dict[str, Any]:
    timeline = bind_live_order_timeline_capture_v1()
    seams = bind_capture_seam_graph_census_v1()
    candidates = (
        {
            "TRIGGER_ID": "BEFORE_MUTATION",
            "MOMENT": "T0_T3",
            "ACCEPTABLE": _FALSE,
            "REASON": "ordId and S05 resulting pos do not exist before venue mutation.",
        },
        {
            "TRIGGER_ID": "AFTER_MUTATION_BEFORE_ACK",
            "MOMENT": "T3_WIRE_SEND",
            "ACCEPTABLE": _FALSE,
            "REASON": "ordId absent. Request sz is not S05 pos. Live-transport join forbidden.",
        },
        {
            "TRIGGER_ID": "AFTER_VENUE_ACK",
            "MOMENT": "T4_HTTP_VENUE_ACKNOWLEDGEMENT",
            "ACCEPTABLE": _FALSE,
            "REASON": "ACK omits pos and posSide. Resulting position after fill does not yet exist.",
        },
        {
            "TRIGGER_ID": "AFTER_VENUE_ACCEPT_OPEN",
            "MOMENT": "T5_ORDER_ACCEPTED_OPEN",
            "ACCEPTABLE": _FALSE,
            "REASON": "Order-state is not position proof. pos absent.",
        },
        {
            "TRIGGER_ID": "AFTER_FILL_GET",
            "MOMENT": "T6_PARTIAL_OR_FULL_FILLS",
            "ACCEPTABLE": _FALSE,
            "REASON": "fillSz is not S05. Venue GET is not contemporaneous Peak_Trade handoff.",
        },
        {
            "TRIGGER_ID": "AFTER_POSITION_RECONCILIATION",
            "MOMENT": "T8_PEAK_TRADE_ACCOUNTING_RECONCILIATION_OBSERVATION",
            "ACCEPTABLE": _FALSE,
            "REASON": "Venue GET pos is LIVE_POSITION_RECONCILED, not handoff pos.",
        },
        {
            "TRIGGER_ID": "AFTER_LOCAL_RESULT_STATE",
            "MOMENT": "NONE_IMPLEMENTED",
            "ACCEPTABLE": _FALSE,
            "REASON": "No Peak_Trade-owned S05 resulting-current-qty producer exists.",
        },
        {
            "TRIGGER_ID": "AT_SHUTDOWN",
            "MOMENT": "T9_RESTART_BOUNDARY",
            "ACCEPTABLE": _FALSE,
            "REASON": "Shutdown/restart is the consumption boundary, not the capture moment.",
        },
        {
            "TRIGGER_ID": "PERIODIC",
            "MOMENT": "NONE",
            "ACCEPTABLE": _FALSE,
            "REASON": "No periodic Live handoff capture exists. Periodicity would not create S05.",
        },
        {
            "TRIGGER_ID": "EVENT_DRIVEN_HANDOFF_COMMIT_AFTER_BOUND_FILL",
            "MOMENT": "REQUIRED_NOT_IMPLEMENTED",
            "ACCEPTABLE": "unproven",
            "REASON": (
                "S05 temporal meaning requires handoff-commit immediately before restart "
                "describing resulting position after bound fill. No productive event, "
                "caller, or writer exists."
            ),
        },
    )
    acceptable_true = [row for row in candidates if row["ACCEPTABLE"] == _TRUE]
    if acceptable_true:
        raise Section1114OfflineSurfaceError("CAPTURE_TRIGGER_MUST_NOT_BE_INVENTED")
    if int(seams["ACCEPTABLE_COMPLETE_SEAM_COUNT"]) != 0:
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_MUST_NOT_BE_INVENTED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_CAPTURE_TRIGGER_V1",
        "CAPTURE_TRIGGER_STATUS": CAPTURE_TRIGGER_STATUS,
        "SELECTED_CAPTURE_TRIGGER": SELECTED_CAPTURE_TRIGGER,
        "CAPTURE_TRIGGER_BOUND": False,
        "CAPTURE_TRIGGER_UNRESOLVED_AS_PRODUCTIVE_EVENT": True,
        "REQUIRED_TEMPORAL_WINDOW": POS_TEMPORAL_MEANING,
        "REQUIRED_ORDER": (
            "mutation-critical venue effect "
            "THEN bound fill identity exists "
            "THEN Peak_Trade-owned S05 resulting current position qty available "
            "THEN handoff record construction "
            "THEN durable write "
            "THEN durability success acknowledgement "
            "THEN process/host restart may occur"
        ),
        "POST_HOC_ASSEMBLY_ACROSS_MOMENTS_IS_RETROACTIVE_SYNTHESIS": True,
        "NO_TIMESTAMP_INVENTION": True,
        "SEAM_CANDIDATE_COUNT": seams["SEAM_CANDIDATE_COUNT"],
        "ACCEPTABLE_COMPLETE_SEAM_COUNT": 0,
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT": "NONE",
        "timeline_moments": timeline["moments"],
        "candidates": list(candidates),
        "historical_seams": seams["seams"],
    }


def bind_handoff_record_field_matrix_v1() -> dict[str, Any]:
    historical = bind_required_field_contract_v1()
    if HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS != "UNPROVEN":
        raise Section1114OfflineSurfaceError(
            "HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS_MUST_REMAIN_UNPROVEN"
        )
    fields = (
        {
            "FIELD_NAME": "clOrdId",
            "SEMANTIC_DEFINITION": (
                "Peak_Trade client order identity sent on the Live POST and "
                "returned on the synchronous ACK."
            ),
            "PRODUCER": "canary order plan / ACK allowlist",
            "SOURCE_TYPE": "PEAK_TRADE_OWNED_CONTEMPORANEOUS_AT_T1_THROUGH_T5",
            "UNIT": "NONE_IDENTITY_STRING",
            "NULLABILITY": "FORBIDDEN",
            "TIMESTAMP_SEMANTICS": "NOT_A_TIMESTAMP",
            "PROVENANCE_SEMANTICS": "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
            "DURABILITY_REQUIREMENT": "REQUIRED_IN_HANDOFF_RECORD",
            "VALIDATION_REQUIREMENT": f"Must equal BOUND_CLORDID={BOUND_CLORDID}",
            "CURRENTLY_PRODUCIBLE": True,
            "ALREADY_IMPLEMENTED_AS_HANDOFF_FIELD": False,
            "AUTHORITY_REQUIRED": True,
        },
        {
            "FIELD_NAME": "ordId",
            "SEMANTIC_DEFINITION": "Venue order identity returned on the synchronous ACK.",
            "PRODUCER": "ACK data-entry allowlist",
            "SOURCE_TYPE": "PEAK_TRADE_OWNED_CONTEMPORANEOUS_AT_T4_T5",
            "UNIT": "NONE_IDENTITY_STRING",
            "NULLABILITY": "FORBIDDEN",
            "TIMESTAMP_SEMANTICS": "NOT_A_TIMESTAMP",
            "PROVENANCE_SEMANTICS": "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
            "DURABILITY_REQUIREMENT": "REQUIRED_IN_HANDOFF_RECORD",
            "VALIDATION_REQUIREMENT": f"Must equal BOUND_ORDID={BOUND_ORDID}",
            "CURRENTLY_PRODUCIBLE": True,
            "ALREADY_IMPLEMENTED_AS_HANDOFF_FIELD": False,
            "AUTHORITY_REQUIRED": True,
        },
        {
            "FIELD_NAME": "instId",
            "SEMANTIC_DEFINITION": (
                "Bound Live instrument identity from the Peak_Trade order plan "
                "and venue-native request body."
            ),
            "PRODUCER": "order plan / request body",
            "SOURCE_TYPE": "PEAK_TRADE_OWNED_CONTEMPORANEOUS_AT_T1_THROUGH_T4",
            "UNIT": "NONE_INSTRUMENT_ID",
            "NULLABILITY": "FORBIDDEN",
            "TIMESTAMP_SEMANTICS": "NOT_A_TIMESTAMP",
            "PROVENANCE_SEMANTICS": "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
            "DURABILITY_REQUIREMENT": "REQUIRED_IN_HANDOFF_RECORD",
            "VALIDATION_REQUIREMENT": f"MUST_EQUAL_BOUND_INSTID={BOUND_INSTID}",
            "CURRENTLY_PRODUCIBLE": True,
            "ALREADY_IMPLEMENTED_AS_HANDOFF_FIELD": False,
            "AUTHORITY_REQUIRED": True,
        },
        {
            "FIELD_NAME": "posSide",
            "SEMANTIC_DEFINITION": (
                "Mandatory net-mode identity token. posSide=net does not encode "
                "long/short. Direction is out of scope for this field."
            ),
            "PRODUCER": "NONE_PRODUCTIVE; bound identity token net from Live fill identity",
            "SOURCE_TYPE": (
                "BOUND_IDENTITY_KNOWN; NOT_PEAK_TRADE_OWNED_CONTEMPORANEOUS_AT_ANY_"
                "COMPLETE_SEAM; T6 fill GET is venue-owned"
            ),
            "UNIT": "NONE_NET_MODE_TOKEN",
            "NULLABILITY": "FORBIDDEN",
            "TIMESTAMP_SEMANTICS": "NOT_A_TIMESTAMP",
            "PROVENANCE_SEMANTICS": "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
            "DURABILITY_REQUIREMENT": "REQUIRED_IN_HANDOFF_RECORD",
            "VALIDATION_REQUIREMENT": f"Must equal BOUND_POS_SIDE={BOUND_POS_SIDE}",
            "CURRENTLY_PRODUCIBLE": False,
            "ALREADY_IMPLEMENTED_AS_HANDOFF_FIELD": False,
            "AUTHORITY_REQUIRED": True,
        },
        {
            "FIELD_NAME": "pos",
            "SEMANTIC_DEFINITION": (
                "S05 Peak_Trade-owned contemporaneous resulting/current position "
                f"quantity in {POS_UNIT} as {POS_SIGN_SEMANTICS}."
            ),
            "PRODUCER": PRODUCER_ID,
            "SOURCE_TYPE": "CONTRACT_ONLY_UNIMPLEMENTED",
            "UNIT": POS_UNIT,
            "NULLABILITY": "FORBIDDEN",
            "TIMESTAMP_SEMANTICS": "NOT_A_TIMESTAMP; temporal meaning is capture moment",
            "PROVENANCE_SEMANTICS": "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE",
            "DURABILITY_REQUIREMENT": "REQUIRED_IN_HANDOFF_RECORD",
            "VALIDATION_REQUIREMENT": (
                "nonempty Decimal-parseable unsigned string; nonzero when "
                f"BOUND_FILL_SZ={BOUND_FILL_SZ} is nonzero; must not copy fillSz"
            ),
            "CURRENTLY_PRODUCIBLE": False,
            "ALREADY_IMPLEMENTED_AS_HANDOFF_FIELD": False,
            "AUTHORITY_REQUIRED": True,
        },
    )
    optional = [
        {
            "FIELD_NAME": name,
            "SEMANTIC_DEFINITION": "Optional temporal marker. Not required by current authority.",
            "PRODUCER": "NONE",
            "SOURCE_TYPE": "OPTIONAL_NOT_REQUIRED",
            "UNIT": "UTC_TIMESTAMP_IF_PRESENT",
            "NULLABILITY": "ALLOWED_BECAUSE_OPTIONAL",
            "TIMESTAMP_SEMANTICS": "MUST_BE_CONTEMPORANEOUS_NO_BACKFILL_IF_WRITTEN",
            "PROVENANCE_SEMANTICS": "NO_SYNTHETIC_PRE_RESTART_PROVENANCE",
            "DURABILITY_REQUIREMENT": "NOT_REQUIRED",
            "VALIDATION_REQUIREMENT": "If present, contemporaneous; no backfill.",
            "CURRENTLY_PRODUCIBLE": False,
            "ALREADY_IMPLEMENTED_AS_HANDOFF_FIELD": False,
            "AUTHORITY_REQUIRED": False,
        }
        for name in OPTIONAL_TEMPORAL_FIELDS
    ]
    required_producible = [row for row in fields if row["CURRENTLY_PRODUCIBLE"] is True]
    if len(fields) != len(REQUIRED_HANDOFF_FIELDS):
        raise Section1114OfflineSurfaceError("REQUIRED_HANDOFF_FIELD_COUNT_DRIFT")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_HANDOFF_RECORD_FIELD_MATRIX_V1",
        "HANDOFF_RECORD_CONTRACT_STATUS": HANDOFF_RECORD_CONTRACT_STATUS,
        "HANDOFF_DOCUMENT_CLASS": HANDOFF_DOCUMENT_CLASS,
        "HANDOFF_SCHEMA_VERSION": "section_11_14_live_durable_pre_restart_handoff.v1",
        "SCHEMA_CHANGE_REQUIRED": False,
        "DIRECTION_FIELD_ADDED": False,
        "HISTORICAL_REQUIRED_FIELD_POS_SEMANTICS_REMAINS_UNPROVEN": True,
        "HANDOFF_REQUIRED_FIELD_COUNT": len(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_CURRENTLY_PRODUCIBLE_FIELD_COUNT": len(required_producible),
        "HANDOFF_CURRENTLY_PRODUCIBLE_FIELDS_ARE_NOT_A_COMPLETE_SEAM": True,
        "OPTIONAL_TEMPORAL_FIELD_COUNT": len(OPTIONAL_TEMPORAL_FIELDS),
        "NO_ELEGANT_EXTRA_FIELDS_ADDED": True,
        "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET": HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
        "fields": list(fields),
        "optional_fields": optional,
        "historical_required_field_contract": historical["DOCUMENT_CLASS"],
    }


def bind_storage_owner_census_v1() -> dict[str, Any]:
    census = bind_section_11_14_live_handoff_owner_census_matrix_v1()
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    classified: list[dict[str, Any]] = []
    for row in census["rows"]:
        item = dict(row)
        if row["allowed_for_section_11_14_handoff"] is True:
            item["COMPATIBILITY_CLASS"] = "EXISTING_COMPATIBLE_OWNER"
        elif row["SYMBOL"] == "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER":
            item["COMPATIBILITY_CLASS"] = "EXISTING_INCOMPATIBLE_OWNER"
            item["TECHNICAL_NOTE"] = (
                "A1 WAL has PROCESS_RESTART_DURABILITY=PROVEN_WITH_BOUND_ASSUMPTIONS "
                "and HOST_CRASH_DURABILITY=UNPROVEN. Reuse as Live handoff is forbidden. "
                "Technical durability primitives are not semantic compatibility."
            )
        elif row["SYMBOL"] == "SECTION_11_14_LIVE_HANDOFF_OWNER":
            item["COMPATIBILITY_CLASS"] = "NO_EXISTING_OWNER"
        else:
            item["COMPATIBILITY_CLASS"] = "EXISTING_INCOMPATIBLE_OWNER"
        classified.append(item)
    compatible = [
        row for row in classified if row["COMPATIBILITY_CLASS"] == "EXISTING_COMPATIBLE_OWNER"
    ]
    partial = [
        row
        for row in classified
        if row["COMPATIBILITY_CLASS"] == "EXISTING_PARTIALLY_COMPATIBLE_OWNER"
    ]
    if compatible:
        raise Section1114OfflineSurfaceError("EXISTING_COMPATIBLE_OWNER_MUST_REMAIN_ABSENT")
    if partial:
        raise Section1114OfflineSurfaceError("PARTIAL_COMPATIBLE_OWNER_MUST_NOT_BE_INVENTED")
    if census["ALLOWED_HANDOFF_OWNER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("COMPETING_HANDOFF_OWNER_MUST_REMAIN_ABSENT")
    if HISTORICAL_HANDOFF_OWNER_CURRENT_NONE != "NONE":
        raise Section1114OfflineSurfaceError("CURRENT_OWNER_MUST_REMAIN_NONE")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_STORAGE_OWNER_CENSUS_V1",
        "STORAGE_OWNER_CANDIDATE_COUNT": len(classified),
        "SELECTED_STORAGE_OWNER": "NONE",
        "STORAGE_OWNER_MINTED": False,
        "EXISTING_COMPATIBLE_OWNER_COUNT": 0,
        "EXISTING_PARTIALLY_COMPATIBLE_OWNER_COUNT": 0,
        "EXISTING_INCOMPATIBLE_OWNER_COUNT": len(
            [
                row
                for row in classified
                if row["COMPATIBILITY_CLASS"] == "EXISTING_INCOMPATIBLE_OWNER"
            ]
        ),
        "NO_EXISTING_OWNER": True,
        "PROPOSED_FIRST_OWNER_ID": PROPOSED_FIRST_OWNER_ID,
        "PROPOSED_FIRST_OWNER_IS_NOT_BOUND": True,
        "NAME_OR_DECLARATION_IS_NOT_PRODUCTIVE_BIND": True,
        "PR_6317_6318_6319_DID_NOT_MINT_STORAGE_OWNER": True,
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "rows": classified,
        "vacancy_status": vacancy["OWNER_VACANCY_CONTRACT_STATUS"],
    }


def bind_writer_reader_dataflow_v1() -> dict[str, Any]:
    writer_reader = bind_writer_reader_contract_adjudication_v1()
    vacancy = bind_section_11_14_live_handoff_owner_vacancy_contract_v1()
    producer_to_storage = bool(
        HISTORICAL_HANDOFF_WRITER_PRESENT is True and HISTORICAL_HANDOFF_PRODUCTIVE_BINDING is True
    )
    if producer_to_storage:
        raise Section1114OfflineSurfaceError("WRITER_MUST_REMAIN_UNBOUND")
    if HISTORICAL_HANDOFF_READER_PRESENT is True:
        raise Section1114OfflineSurfaceError("READER_MUST_REMAIN_UNBOUND")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_WRITER_READER_DATAFLOW_V1",
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "PRODUCTIVE_PATH_PRODUCER_TO_RECORD_TO_STORAGE": False,
        "MINIMAL_WRITER_BINDING_SEAM": (
            "Unimplemented S05 producer output joined at "
            "REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART "
            "into a first-owner writer that atomically persists "
            "{clOrdId, ordId, instId, posSide, pos} plus contemporaneous "
            "provenance. Exact function/class seam is absent."
        ),
        "MINIMAL_READER_BINDING_SEAM": (
            "adjudicate_live_restart_reconstructed_v1 is the named post-restart "
            "read seam and is not a productive binding. A later reader must "
            "load GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF and fail closed."
        ),
        "CALLER": "NONE",
        "TRIGGER": SELECTED_CAPTURE_TRIGGER,
        "FUNCTION_CLASS_SEAM": "ABSENT",
        "ERROR_PROPAGATION": "UNIMPLEMENTED_FAIL_CLOSED_REQUIRED",
        "FAILURE_POLICY": vacancy["WRITE_PRECONDITIONS"],
        "ACKNOWLEDGEMENT_BOUNDARY": "REQUIRED_BEFORE_CLAIM_WRITTEN;CURRENTLY_ABSENT",
        "MUTATION_MAY_SUCCEED_BEFORE_DURABLE_HANDOFF_CAPTURE": (
            "CURRENTLY_TRUE_BECAUSE_NO_CAPTURE_EXISTS; REQUIRED_FALSE_ONCE_BOUND"
        ),
        "CAPTURE_FAILURE_MUST_FAIL_CLOSED": True,
        "IDEMPOTENCY_BEHAVIOR": (
            "IDEMPOTENT_REJECT_OR_EXACT_SAME_RECORD;NO_SECOND_IDENTITY;NOT_BOUND"
        ),
        "NAMED_READ_SEAM": "adjudicate_live_restart_reconstructed_v1",
        "NAMED_READ_SEAM_IS_NOT_PRODUCTIVE_BINDING": True,
        "MISSING_DATA_BEHAVIOR": "FAIL_CLOSED",
        "MALFORMED_DATA_BEHAVIOR": "FAIL_CLOSED",
        "STALE_DATA_BEHAVIOR": "FAIL_CLOSED",
        "writer_reader_contract": writer_reader,
    }


def bind_complete_capture_seam_predicate_v1() -> dict[str, Any]:
    values = {
        "POS_SEMANTICS_PROVEN": POS_SEMANTICS == "PROVEN",
        "SELECTED_SEMANTIC_UNIQUE": True,
        "SELECTED_SEMANTIC_ID_IS_S05": SELECTED_SEMANTIC_ID
        == "S05_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY_VENUE_CONTRACT_COUNT_UNSIGNED",
        "NEW_PRODUCER_IMPLEMENTED": False,
        "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": False,
        "CAPTURE_TRIGGER_PRODUCTIVELY_BOUND": False,
        "REQUIRED_WINDOW_AFTER_BOUND_FILL_AT_HANDOFF_COMMIT_BEFORE_RESTART": True,
        "ALL_FIVE_REQUIRED_FIELDS_CONTEMPORANEOUS_PEAK_TRADE_OWNED_AT_SAME_SEAM": False,
        "RECORD_CONTRACT_BOUND": True,
        "STORAGE_OWNER_MINTED": False,
        "STORAGE_OWNER_IS_PROPOSED_FIRST_OWNER_NOT_FORBIDDEN_REUSE": False,
        "WRITER_BOUND": False,
        "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM": False,
        "FAIL_CLOSED_ON_CAPTURE_FAILURE": True,
        "READER_BOUND": False,
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": False,
        "STALE_DATA_REJECTED_BY_BOUND_READER": False,
        "MALFORMED_DATA_REJECTED_BY_BOUND_READER": False,
        "NO_RETROACTIVE_SYNTHESIS": not RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "NO_HISTORICAL_REINTERPRETATION": True,
        "RESTART_CONSUMER_BOUND": False,
        "PROCESS_RESTART_READABLE_HANDOFF_RECORD": False,
    }
    if tuple(values) != _SEAM_PREDICATES:
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_PREDICATE_DRIFT")
    missing = [name for name, value in values.items() if value is not True]
    proven = all(values.values())
    if proven:
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_PREDICATE_V1",
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "COMPLETE_CAPTURE_SEAM_PROOF_STATUS": COMPLETE_CAPTURE_SEAM_PROOF_STATUS,
        "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED": True,
        "HOST_CRASH_IS_NOT_A_SEAM_CONJUNCT": True,
        "HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD": (
            HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD
        ),
        "PREDICATE": ("COMPLETE_CAPTURE_SEAM := " + " AND ".join(_SEAM_PREDICATES)),
        "conjuncts": values,
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": missing,
        "MISSING_PREDICATE_COUNT": len(missing),
        "NO_INVENTED_SEAM": True,
    }


def bind_failure_matrix_v1() -> dict[str, Any]:
    absent = "No productive capture path exists. Restart read fail-closed on missing handoff."
    required_fail_closed = (
        "Fail closed. Emit nothing. Do not substitute venue GET, fillSz, "
        "submitted sz, accounting, A1 WAL, evidence pack, or retroactive synthesis."
    )
    rows = (
        _failure(
            case_id="producer_unavailable",
            current_behavior=absent,
            required_behavior=required_fail_closed,
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="S05 producer unimplemented",
        ),
        _failure(
            case_id="qty_unavailable",
            current_behavior=absent,
            required_behavior=required_fail_closed,
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="No S05 qty source",
        ),
        _failure(
            case_id="qty_malformed",
            current_behavior=absent,
            required_behavior="Reject non-Decimal or empty pos. Do not write.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Writer validation unbound",
        ),
        _failure(
            case_id="wrong_unit",
            current_behavior=absent,
            required_behavior="Reject any unit other than VENUE_CONTRACT_COUNT_NUMBER_OF_CONTRACTS.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Unit guard unimplemented",
        ),
        _failure(
            case_id="wrong_instrument",
            current_behavior=absent,
            required_behavior=f"Reject instId != {BOUND_INSTID}.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Instrument guard unimplemented",
        ),
        _failure(
            case_id="capture_interrupted",
            current_behavior=absent,
            required_behavior="No partial visible handoff. Fail closed.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="No atomic writer",
        ),
        _failure(
            case_id="serialization_failure",
            current_behavior=absent,
            required_behavior="Fail closed. Do not acknowledge durable success.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="No serializer bound",
        ),
        _failure(
            case_id="write_failure",
            current_behavior=absent,
            required_behavior="Fail closed. Mutation success must not be claimed.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="No writer",
        ),
        _failure(
            case_id="partial_write",
            current_behavior=absent,
            required_behavior="Torn write must be invisible or fail closed on read.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Atomicity unbound",
        ),
        _failure(
            case_id="fsync_durability_uncertainty",
            current_behavior=absent,
            required_behavior=(
                "Do not claim durable success without proven write acknowledgement. "
                "Host-crash remains separately UNPROVEN and is not required for this field."
            ),
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="No durability ack bound",
        ),
        _failure(
            case_id="stale_previous_record",
            current_behavior="No record exists.",
            required_behavior="Reject stale or wrong-attempt identity. No heuristic recovery.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Reader unbound",
        ),
        _failure(
            case_id="corrupt_record",
            current_behavior="No record exists.",
            required_behavior="Fail closed. No heuristic repair.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Reader unbound",
        ),
        _failure(
            case_id="missing_record",
            current_behavior=(
                "adjudicate_live_restart_reconstructed_v1 fail-closed: "
                "DURABLE_LIVE_PRE_RESTART_HANDOFF_ABSENT"
            ),
            required_behavior="Fail closed. No retroactive synthesis.",
            proven_or_unproven="PROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="NONE_FOR_MISSING_HANDOFF_ADMISSION",
        ),
        _failure(
            case_id="schema_mismatch",
            current_behavior="No productively bound schema.",
            required_behavior="Fail closed on schema/version mismatch.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Schema named not productively bound",
        ),
        _failure(
            case_id="provenance_mismatch",
            current_behavior="No handoff provenance exists.",
            required_behavior="Reject RETROACTIVE_SYNTHESIS, VENUE_GET_COPY, TIMESTAMP_BACKFILL.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Provenance validator unbound",
        ),
        _failure(
            case_id="timestamp_invalid",
            current_behavior="No capture timestamp exists. Backfill forbidden.",
            required_behavior="If a timestamp is written, it must be contemporaneous. No backfill.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Optional temporal fields not implemented",
        ),
        _failure(
            case_id="duplicate_capture",
            current_behavior="No writer. Duplicates cannot occur.",
            required_behavior="Idempotent reject or exact same record. No second identity.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Idempotency unbound",
        ),
        _failure(
            case_id="restart_between_mutation_and_capture",
            current_behavior=(
                "No capture exists, so any restart after fill loses Peak_Trade "
                "control-state pos. Retroactive synthesis is forbidden."
            ),
            required_behavior=(
                "Fail closed. Do not synthesize a pre-restart handoff after restart "
                "from venue/API/logs/old snapshots."
            ),
            proven_or_unproven="PROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Capture must occur before restart; currently absent",
        ),
        _failure(
            case_id="restart_during_capture",
            current_behavior=absent,
            required_behavior="Partial write invisible. Fail closed. No torn-record recovery.",
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Atomic writer absent",
        ),
        _failure(
            case_id="restart_after_capture_before_acknowledgement",
            current_behavior=absent,
            required_behavior=(
                "Without durability ack, treat as missing/unproven handoff. Fail closed."
            ),
            proven_or_unproven="UNPROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="Ack boundary unbound",
        ),
        _failure(
            case_id="reader_failure",
            current_behavior="Named read seam fail-closed on missing handoff.",
            required_behavior="Fail closed. Do not skip to venue GET.",
            proven_or_unproven="PROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="NONE_FOR_CURRENT_MISSING_HANDOFF_READER",
        ),
        _failure(
            case_id="consumer_failure",
            current_behavior="LIVE_RESTART_RECONSTRUCTED remains false.",
            required_behavior="Do not promote restart reconstruction. No silent reinitialization.",
            proven_or_unproven="PROVEN",
            fail_open_or_fail_closed="FAIL_CLOSED",
            implementation_gap="NONE_FOR_CURRENT_FALSE_FIELD",
        ),
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_FAILURE_MATRIX_V1",
        "FAILURE_MATRIX_STATUS": "BOUND_CURRENT_PATH_ABSENT_REQUIRED_FAIL_CLOSED",
        "CASE_COUNT": len(rows),
        "rows": [dict(row) for row in rows],
        "HEURISTIC_RECOVERY_FORBIDDEN": True,
        "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": (
            VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF
        ),
    }


def bind_crash_boundary_v1() -> dict[str, Any]:
    durability = bind_durability_contract_adjudication_v1()
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_CRASH_BOUNDARY_V1",
        "PROCESS_RESTART_PROOF": "UNPROVEN_FOR_SECTION_11_14_HANDOFF",
        "HOST_CRASH_PROOF": "UNPROVEN",
        "DURABLE_STORAGE_PROOF": "UNPROVEN_FOR_SECTION_11_14_HANDOFF",
        "A1_PROCESS_RESTART_DURABILITY": "PROVEN_WITH_BOUND_ASSUMPTIONS_NOT_INHERITED",
        "A1_HOST_CRASH_DURABILITY": "UNPROVEN_NOT_INHERITED",
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": A1_WAL_AS_LIVE_HANDOFF_ALLOWED,
        "A1_REUSE_FOR_SECTION_11_14": False,
        "FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD": (
            FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD
        ),
        "HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD": (
            HOST_CRASH_DURABILITY_REQUIRED_FOR_THIS_FIELD
        ),
        "FIELD_DOES_NOT_REQUIRE_HOST_CRASH_TO_BECOME_TRUE": True,
        "PROCESS_KILL_PROOF_IS_NOT_HOST_CRASH_PROOF": True,
        "durability_contract": durability,
    }


def bind_test_plan_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_TEST_PLAN_V1",
        "TEST_PLAN_STATUS": "BOUND_NOT_EXECUTED_AS_IMPLEMENTATION",
        "REUSE_EXISTING_OWNERS": (
            "tests/ops/test_section_11_14_live_handoff_pos_producer_semantics_and_contract_v1.py; "
            "tests/ops/test_section_11_14_live_handoff_required_field_capture_seam_pos_and_owner_vacancy_contract_v1.py; "
            "tests/ops/test_section_11_14_live_restart_reconstructed_adjudication_v1.py; "
            "no new test framework"
        ),
        "required_tests": (
            "unit_producer_s05_semantics",
            "contract_required_five_fields",
            "persistence_roundtrip",
            "malformed_storage",
            "stale_storage",
            "wrong_instrument",
            "wrong_unit",
            "duplicate_idempotent_writes",
            "process_restart_readable_record",
            "crash_boundary_no_host_crash_claim",
            "atomicity_torn_write_invisible",
            "failure_injection_write_fsync_serialize",
            "no_retroactive_synthesis_proof",
            "exact_producer_semantics_s05",
            "exact_reader_fail_closed_missing_stale_corrupt",
        ),
        "NOT_REQUIRED_NOW": (
            "host_crash_or_power_loss_claim_tests; Live/Testnet/wire tests; "
            "LIVE_RESTART_RECONSTRUCTED promotion tests"
        ),
    }


def bind_implementation_workpackage_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_COMPLETE_CAPTURE_SEAM_IMPLEMENTATION_WORKPACKAGE_V1",
        "PROPOSED_NEXT_IMPLEMENTATION_WORKPACKAGE": PROPOSED_NEXT_IMPLEMENTATION_WORKPACKAGE,
        "PROPOSED_IMPLEMENTATION_SCOPE": (
            "A_producer_implementation_S05; "
            "B_handoff_record_construction_existing_schema_v1_no_schema_v2; "
            "C_storage_owner_mint_PROPOSED_FIRST_OWNER_ID; "
            "D_writer_binding_at_required_capture_window; "
            "E_durable_success_and_fail_closed_failure_semantics_process_restart; "
            "I_focused_contract_and_unit_tests; "
            "K_canonical_documentation_binding"
        ),
        "OUT_OF_SCOPE": (
            "F_restart_reader_productive_bind; "
            "G_reader_side_freshness_validator; "
            "H_reconstruction_consumer_LIVE_RESTART_RECONSTRUCTED; "
            "J_host_crash_or_power_loss_claim_tests; "
            "owner_mint_without_seam; "
            "A1_WAL_reuse; DDO_reuse; FILEGATE_reuse; "
            "Live_Testnet_wire_credentials_activation; "
            "historical_data_reinterpretation; retroactive_synthesis; timestamp_backfill"
        ),
        "WHY_BOUNDED_TOGETHER": (
            "COMPLETE_CAPTURE_SEAM requires implemented S05 producer AND complete "
            "five-field contemporaneous record AND minted owner AND bound writer AND "
            "durable success. Owner mint cannot be adjudicated while the seam is "
            "UNPROVEN. Splitting producer/owner/writer would recreate artificial "
            "mini-PRs that cannot close the seam."
        ),
        "WHY_READER_AND_RESTART_STAY_OUT": (
            "Architecture DAG SLICE_4/SLICE_5 require a separate Owner-GO after "
            "owner mint and seam proven. Reader bind is a restart-admission surface."
        ),
        "IMPLEMENTATION_PRECONDITIONS": (
            "POS_SEMANTICS=PROVEN; SELECTED_SEMANTIC_ID=S05; "
            "NEW_PRODUCER_CONTRACT_DEFINED=true; "
            "COMPLETE_CAPTURE_SEAM_PROOF consumed; "
            "separate scope-specific OWNER_GO; separate OWNER_MERGE_GO; "
            "IMPLEMENTATION_AUTHORIZED remains false until that GO; "
            "no GET; no POST; no restart execution; no A1/DDO reuse"
        ),
        "SLICE_3_OWNER_MINT_CANNOT_START_WHILE_SEAM_UNPROVEN": True,
        "OWNER_MINT_CAN_NOW_BE_ADJUDICATED": False,
        "WRITER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "READER_BIND_CAN_NOW_BE_ADJUDICATED": False,
        "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED": False,
        "IMPLEMENTATION_AUTHORIZED": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
    }


def bind_complete_capture_seam_proof_v1() -> dict[str, Any]:
    if POS_SEMANTICS != "PROVEN":
        raise Section1114OfflineSurfaceError("POS_SEMANTICS_MUST_BE_PROVEN")
    producer = bind_s05_producer_recensus_v1()
    trigger = bind_capture_trigger_adjudication_v1()
    record = bind_handoff_record_field_matrix_v1()
    storage = bind_storage_owner_census_v1()
    dataflow = bind_writer_reader_dataflow_v1()
    predicate = bind_complete_capture_seam_predicate_v1()
    failures = bind_failure_matrix_v1()
    crash = bind_crash_boundary_v1()
    tests = bind_test_plan_v1()
    implementation = bind_implementation_workpackage_v1()
    semantics = bind_pos_producer_semantics_and_contract_v1()
    if semantics["NEW_PRODUCER_IMPLEMENTED"] is True:
        raise Section1114OfflineSurfaceError("NEW_PRODUCER_MUST_REMAIN_UNIMPLEMENTED")
    if predicate["COMPLETE_CAPTURE_SEAM"] != "UNPROVEN":
        raise Section1114OfflineSurfaceError("CAPTURE_SEAM_MUST_REMAIN_UNPROVEN")
    if storage["STORAGE_OWNER_MINTED"] is True:
        raise Section1114OfflineSurfaceError("STORAGE_OWNER_MUST_REMAIN_UNMINTED")
    if dataflow["WRITER_BOUND"] is True or dataflow["READER_BOUND"] is True:
        raise Section1114OfflineSurfaceError("WRITER_READER_MUST_REMAIN_UNBOUND")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1",
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "COMPLETE_CAPTURE_SEAM_PROOF_STATUS": COMPLETE_CAPTURE_SEAM_PROOF_STATUS,
        "POS_SEMANTICS": POS_SEMANTICS,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "PRODUCER_CANDIDATE_COUNT": producer["PRODUCER_CANDIDATE_COUNT"],
        "SELECTED_PRODUCTIVE_PRODUCER": producer["SELECTED_PRODUCTIVE_PRODUCER"],
        "NEW_PRODUCER_CONTRACT_DEFINED": True,
        "NEW_PRODUCER_IMPLEMENTED": False,
        "CAPTURE_TRIGGER_STATUS": CAPTURE_TRIGGER_STATUS,
        "SELECTED_CAPTURE_TRIGGER": SELECTED_CAPTURE_TRIGGER,
        "HANDOFF_RECORD_CONTRACT_STATUS": HANDOFF_RECORD_CONTRACT_STATUS,
        "HANDOFF_REQUIRED_FIELD_COUNT": record["HANDOFF_REQUIRED_FIELD_COUNT"],
        "HANDOFF_CURRENTLY_PRODUCIBLE_FIELD_COUNT": record[
            "HANDOFF_CURRENTLY_PRODUCIBLE_FIELD_COUNT"
        ],
        "STORAGE_OWNER_CANDIDATE_COUNT": storage["STORAGE_OWNER_CANDIDATE_COUNT"],
        "SELECTED_STORAGE_OWNER": storage["SELECTED_STORAGE_OWNER"],
        "STORAGE_OWNER_MINTED": False,
        "WRITER_BOUND": False,
        "READER_BOUND": False,
        "CAPTURE_SEAM_BOUND": False,
        "PRODUCTIVE_BINDING_PRESENT": False,
        "PROCESS_RESTART_PROOF": crash["PROCESS_RESTART_PROOF"],
        "HOST_CRASH_PROOF": crash["HOST_CRASH_PROOF"],
        "DURABLE_STORAGE_PROOF": crash["DURABLE_STORAGE_PROOF"],
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES": predicate[
            "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES"
        ],
        "HISTORICAL_DATA_REINTERPRETATION_ALLOWED": False,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "FAILURE_MATRIX_STATUS": failures["FAILURE_MATRIX_STATUS"],
        "TEST_PLAN_STATUS": tests["TEST_PLAN_STATUS"],
        "IMPLEMENTATION_AUTHORIZED": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "PROPOSED_NEXT_IMPLEMENTATION_WORKPACKAGE": PROPOSED_NEXT_IMPLEMENTATION_WORKPACKAGE,
        "producer_recensus": producer,
        "capture_trigger": trigger,
        "handoff_record": record,
        "storage_owner": storage,
        "writer_reader_dataflow": dataflow,
        "predicate": predicate,
        "failure_matrix": failures,
        "crash_boundary": crash,
        "test_plan": tests,
        "implementation_workpackage": implementation,
    }
