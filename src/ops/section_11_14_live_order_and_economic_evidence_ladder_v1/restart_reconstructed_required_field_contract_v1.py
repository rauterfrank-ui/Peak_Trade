"""Required-field contract for the §11.14 Live durable pre-restart handoff.

Reconstructs the bound identity fields from current authority. Does not
normalize ambiguous `pos` semantics. Does not write productive state.
Does not GET. Does not POST.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    ACCOUNTING_ONLY_IS_NOT_RESTART,
    LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
    NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
    NO_TIMESTAMP_BACKFILL,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    RESTART_IDENTITY_EQUATION,
)

POS_SEMANTICS = "UNPROVEN"
POS_TYPE = "DECIMAL_PARSEABLE_NONEMPTY_STRING_CONSTRAINT_PROVEN;QUANTITY_KIND_UNPROVEN"
POS_SOURCE_AUTHORITY = (
    "LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION+RESTART_IDENTITY_EQUATION;"
    "VENUE_NATIVE_POS_DEFINED_ONLY_FOR_LIVE_POSITION_RECONCILED"
)
POS_CAPTURE_TIME_REQUIREMENT = "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_CAPTURE"
POS_PEAK_TRADE_OWNERSHIP_REQUIRED = True
EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT = "NONE"
EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM = "UNPROVEN"
EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN = False
COMPLETE_CAPTURE_SEAM = "UNPROVEN"
PRE_RESTART_CAPTURE_SEAM = (
    "CANARY_ACK_RETURN_PARTIAL_IDENTITY_ONLY;COMPLETE_IDENTITY_INCLUDING_POS=UNPROVEN"
)
POST_RESTART_READ_SEAM = "adjudicate_live_restart_reconstructed_v1"
MINIMAL_SAFE_ARCHITECTURE = "UNPROVEN"


def bind_required_handoff_field_contracts_v1() -> tuple[dict[str, Any], ...]:
    common = {
        "PEAK_TRADE_OWNERSHIP_REQUIRED": True,
        "VENUE_DERIVATION_ALLOWED": False,
        "ACCOUNTING_DERIVATION_ALLOWED": False,
        "POST_HOC_DERIVATION_ALLOWED": False,
        "NULL_ALLOWED": False,
        "CAPTURE_TIME_REQUIREMENT": POS_CAPTURE_TIME_REQUIREMENT,
        "SOURCE_AUTHORITY": RESTART_IDENTITY_EQUATION,
    }
    return (
        {
            **common,
            "FIELD_NAME": "clOrdId",
            "SEMANTIC_MEANING": (
                "Peak_Trade client order identity sent on the Live POST and "
                "returned on the synchronous ACK."
            ),
            "TYPE": "nonempty_string",
            "ZERO_ALLOWED": False,
            "RESTART_VALIDATION_RULE": "Must equal BOUND_CLORDID.",
            "EVIDENCE": (
                "LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION; "
                "OKX_ORDER_DATA_ENTRY_FIELDS_V1 includes clOrdId."
            ),
        },
        {
            **common,
            "FIELD_NAME": "ordId",
            "SEMANTIC_MEANING": (
                "Venue order identity returned on the synchronous ACK. Absent "
                "before HTTP acknowledgement."
            ),
            "TYPE": "nonempty_string",
            "ZERO_ALLOWED": False,
            "RESTART_VALIDATION_RULE": "Must equal BOUND_ORDID.",
            "EVIDENCE": (
                "LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION; "
                "OKX_ORDER_DATA_ENTRY_FIELDS_V1 includes ordId."
            ),
        },
        {
            **common,
            "FIELD_NAME": "instId",
            "SEMANTIC_MEANING": (
                "Bound Live instrument identity from the Peak_Trade order plan "
                "and venue-native request body."
            ),
            "TYPE": "nonempty_string",
            "ZERO_ALLOWED": False,
            "RESTART_VALIDATION_RULE": "Must equal BOUND_INSTID.",
            "EVIDENCE": (
                "VENUE_NATIVE_BODY_KEYS includes instId; ACK data-entry allowlist omits instId."
            ),
        },
        {
            **common,
            "FIELD_NAME": "posSide",
            "SEMANTIC_MEANING": (
                "Bound fill posSide identity. Observed Live net-mode plan omits "
                "posSide from the Place Order body."
            ),
            "TYPE": "nonempty_string",
            "ZERO_ALLOWED": False,
            "RESTART_VALIDATION_RULE": "Must equal BOUND_POS_SIDE.",
            "EVIDENCE": (
                "submit_ack_contract_v1 posSide=OMITTED_ON_OBSERVED_NET_MODE_PLAN; "
                "fill GET posSide=net is later venue observation."
            ),
        },
        {
            **common,
            "FIELD_NAME": "pos",
            "SEMANTIC_MEANING": POS_SEMANTICS,
            "TYPE": POS_TYPE,
            "ZERO_ALLOWED": False,
            "RESTART_VALIDATION_RULE": (
                "Present, nonempty, Decimal-parseable, and not zero when bound "
                "fillSz is nonzero. Quantity-kind remains UNPROVEN. Must not be "
                "substituted from venue GET, accounting, fillSz, submitted sz, "
                "or retroactive synthesis."
            ),
            "EVIDENCE": (
                "LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION; "
                "HANDOFF_POS_MUST_BE_DECIMAL_PARSEABLE; "
                "HANDOFF_POS_MUST_BE_NONZERO_WHEN_FILL_SZ_NONZERO; "
                "FILL_IS_NOT_POSITION_PROOF; "
                "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF."
            ),
        },
    )


def bind_required_field_contract_v1() -> dict[str, Any]:
    fields = bind_required_handoff_field_contracts_v1()
    pos_row = next(row for row in fields if row["FIELD_NAME"] == "pos")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_REQUIRED_FIELD_CONTRACT_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT_REQUIRED_FIELD_CONTRACT",
        "REQUIRED_HANDOFF_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        "RESTART_IDENTITY_EQUATION": RESTART_IDENTITY_EQUATION,
        "LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION": (
            LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION
        ),
        "fields": [dict(row) for row in fields],
        "POS_SEMANTICS": POS_SEMANTICS,
        "POS_TYPE": POS_TYPE,
        "POS_SOURCE_AUTHORITY": POS_SOURCE_AUTHORITY,
        "POS_CAPTURE_TIME_REQUIREMENT": POS_CAPTURE_TIME_REQUIREMENT,
        "POS_PEAK_TRADE_OWNERSHIP_REQUIRED": POS_PEAK_TRADE_OWNERSHIP_REQUIRED,
        "POS_NULL_ALLOWED": False,
        "POS_ZERO_ALLOWED": False,
        "POS_VENUE_DERIVATION_ALLOWED": False,
        "POS_ACCOUNTING_DERIVATION_ALLOWED": False,
        "POS_POST_HOC_DERIVATION_ALLOWED": False,
        "POS_IS_INTENDED_POSITION": POS_SEMANTICS,
        "POS_IS_ACKNOWLEDGED_POSITION": POS_SEMANTICS,
        "POS_IS_FILLED_POSITION": POS_SEMANTICS,
        "POS_IS_VENUE_POSITION_AFTER_FILL": POS_SEMANTICS,
        "POS_IS_PEAK_TRADE_ACCOUNTING_POSITION": POS_SEMANTICS,
        "POS_IS_SIGNED_QUANTITY": POS_SEMANTICS,
        "POS_IS_CONTRACTS": POS_SEMANTICS,
        "POS_IS_INSTRUMENT_UNITS": POS_SEMANTICS,
        "VENUE_NATIVE_POS_FOR_LIVE_POSITION_RECONCILED_IS_NOT_THIS_HANDOFF_FIELD": True,
        "FILL_SZ_IS_NOT_THIS_HANDOFF_FIELD": True,
        "SUBMITTED_SZ_IS_NOT_THIS_HANDOFF_FIELD": True,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": (
            VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF
        ),
        "ACCOUNTING_ONLY_IS_NOT_RESTART": ACCOUNTING_ONLY_IS_NOT_RESTART,
        "NO_TIMESTAMP_BACKFILL": NO_TIMESTAMP_BACKFILL,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": NO_SYNTHETIC_PRE_RESTART_PROVENANCE,
        "pos_row": pos_row,
    }


def bind_live_order_timeline_capture_v1() -> dict[str, Any]:
    moments = (
        {
            "MOMENT": "T0_DECISION",
            "clOrdId": False,
            "ordId": False,
            "instId": False,
            "posSide": False,
            "pos": False,
            "PEAK_TRADE_OWNED": False,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": False,
            "MISSING_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        },
        {
            "MOMENT": "T1_ORDER_PLAN",
            "clOrdId": True,
            "ordId": False,
            "instId": True,
            "posSide": False,
            "pos": False,
            "PEAK_TRADE_OWNED": True,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": False,
            "MISSING_FIELDS": ["ordId", "posSide", "pos"],
            "NOTE": "Plan sz exists. Plan sz is not handoff pos. posSide omitted.",
        },
        {
            "MOMENT": "T2_PRE_SUBMIT_GATES",
            "clOrdId": True,
            "ordId": False,
            "instId": True,
            "posSide": False,
            "pos": False,
            "PEAK_TRADE_OWNED": True,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": False,
            "MISSING_FIELDS": ["ordId", "posSide", "pos"],
        },
        {
            "MOMENT": "T3_WIRE_SEND",
            "clOrdId": True,
            "ordId": False,
            "instId": True,
            "posSide": False,
            "pos": False,
            "PEAK_TRADE_OWNED": True,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": True,
            "MISSING_FIELDS": ["ordId", "posSide", "pos"],
            "NOTE": "Request body sz is not handoff pos. posSide omitted on net-mode plan.",
        },
        {
            "MOMENT": "T4_HTTP_VENUE_ACKNOWLEDGEMENT",
            "clOrdId": True,
            "ordId": True,
            "instId": True,
            "posSide": False,
            "pos": False,
            "PEAK_TRADE_OWNED": True,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": True,
            "MISSING_FIELDS": ["posSide", "pos"],
            "NOTE": (
                "ACK data-entry allowlist is sCode,sMsg,ordId,clOrdId,tag. "
                "instId is Peak_Trade-owned from the request/plan, not ACK data."
            ),
        },
        {
            "MOMENT": "T5_ORDER_ACCEPTED_OPEN",
            "clOrdId": True,
            "ordId": True,
            "instId": True,
            "posSide": False,
            "pos": False,
            "PEAK_TRADE_OWNED": False,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": True,
            "MISSING_FIELDS": ["posSide", "pos"],
            "NOTE": "Order-state is not position proof.",
        },
        {
            "MOMENT": "T6_PARTIAL_OR_FULL_FILLS",
            "clOrdId": True,
            "ordId": True,
            "instId": True,
            "posSide": True,
            "pos": False,
            "PEAK_TRADE_OWNED": False,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": True,
            "MISSING_FIELDS": ["pos"],
            "NOTE": "fillSz and fill posSide are venue GET fills. Fill is not position proof.",
        },
        {
            "MOMENT": "T7_VENUE_POSITION_MUTATION",
            "clOrdId": False,
            "ordId": False,
            "instId": True,
            "posSide": True,
            "pos": False,
            "PEAK_TRADE_OWNED": False,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": True,
            "MISSING_FIELDS": ["clOrdId", "ordId", "pos"],
            "NOTE": "Venue owns venue position. VENUE_OKX_EEA is not Peak_Trade handoff owner.",
        },
        {
            "MOMENT": "T8_PEAK_TRADE_ACCOUNTING_RECONCILIATION_OBSERVATION",
            "clOrdId": True,
            "ordId": True,
            "instId": True,
            "posSide": True,
            "pos": False,
            "PEAK_TRADE_OWNED": False,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": True,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": True,
            "MISSING_FIELDS": ["pos"],
            "NOTE": (
                "GET /account/positions.pos is venue-native accounting path. "
                "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF. "
                "ACCOUNTING_ONLY_IS_NOT_RESTART."
            ),
        },
        {
            "MOMENT": "T9_RESTART_BOUNDARY",
            "clOrdId": False,
            "ordId": False,
            "instId": False,
            "posSide": False,
            "pos": False,
            "PEAK_TRADE_OWNED": False,
            "CONTEMPORANEOUS_PERSIST_RELIABLE": False,
            "BEFORE_RESTART_BOUNDARY": False,
            "LIVE_TRANSPORT_TOUCH_IF_JOIN": False,
            "MISSING_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
            "NOTE": "No Peak_Trade durable pre-restart handoff exists.",
        },
    )
    missing_at_each = {str(row["MOMENT"]): list(row["MISSING_FIELDS"]) for row in moments}
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_CAPTURE_MOMENT_CENSUS_V1",
        "moments": [dict(row) for row in moments],
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT": EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT,
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM": EARLIEST_COMPLETE_HANDOFF_CAPTURE_SEAM,
        "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN": EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN,
        "COMPLETE_CAPTURE_SEAM": COMPLETE_CAPTURE_SEAM,
        "PRE_RESTART_CAPTURE_SEAM": PRE_RESTART_CAPTURE_SEAM,
        "POST_RESTART_READ_SEAM": POST_RESTART_READ_SEAM,
        "MINIMAL_SAFE_ARCHITECTURE": MINIMAL_SAFE_ARCHITECTURE,
        "MISSING_FIELD_AT_EACH_CANDIDATE_SEAM": missing_at_each,
        "CANARY_ACK_RETURN_FIELDS": ("sCode", "sMsg", "ordId", "clOrdId", "tag"),
        "CANARY_ACK_OMITS_POS": True,
        "CANARY_ACK_OMITS_POSSIDE": True,
        "CANARY_ACK_OMITS_INSTID": True,
        "CANARY_REQUEST_OMITS_POSSIDE": True,
        "CANARY_REQUEST_HAS_SZ_NOT_POS": True,
    }
