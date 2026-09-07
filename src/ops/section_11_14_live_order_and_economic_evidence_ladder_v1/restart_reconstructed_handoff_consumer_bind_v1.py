"""Bind the restart-reconstruction consumer to a validated reader result.

Accepts only VALID_HANDOFF from the productive owner-bound reader.
Does not GET. Does not POST. Does not invent contemporaneous Live
observation. Does not promote LIVE_RESTART_RECONSTRUCTED from tests or
envelope markers alone.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_adjudication_v1 import (
    adjudicate_live_restart_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    FIRST_OWNER_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_reader_v1 import (
    RESULT_VALID_HANDOFF,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
)

RESTART_CONSUMER_SELECTED = "adjudicate_live_restart_reconstructed_v1::consume_validated_handoff_for_restart_reconstruction_v1"
RESTART_CONSUMER_BOUND = True


def consume_validated_handoff_for_restart_reconstruction_v1(
    *,
    reader_result: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(reader_result or {})
    reader_class = str(result.get("RESULT") or "").strip()
    if reader_class != RESULT_VALID_HANDOFF:
        return {
            "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_RESTART_CONSUMER_RESULT_V1",
            "RESTART_CONSUMER_SELECTED": RESTART_CONSUMER_SELECTED,
            "RESTART_CONSUMER_BOUND": True,
            "CONSUMER_ACCEPTED": False,
            "READER_RESULT": reader_class or "READ_FAILURE",
            "REASON": "CONSUMER_REJECTS_INVALID_READER_RESULT",
            "LIVE_RESTART_RECONSTRUCTED": False,
            "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
            "HOST_CRASH_DURABILITY": "UNPROVEN",
            "GET_PERFORMED": False,
            "POST_USED": False,
            "WIRE_SEND": False,
            "LIVE_ACTION": "NONE",
            "FALLBACK_USED": False,
            "STORAGE_OWNER_ID": FIRST_OWNER_ID,
            "adjudication": None,
        }
    validated = dict(result.get("validated_handoff") or {})
    if not validated:
        return {
            "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_RESTART_CONSUMER_RESULT_V1",
            "RESTART_CONSUMER_SELECTED": RESTART_CONSUMER_SELECTED,
            "RESTART_CONSUMER_BOUND": True,
            "CONSUMER_ACCEPTED": False,
            "READER_RESULT": reader_class,
            "REASON": "VALIDATED_HANDOFF_MISSING",
            "LIVE_RESTART_RECONSTRUCTED": False,
            "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
            "HOST_CRASH_DURABILITY": "UNPROVEN",
            "GET_PERFORMED": False,
            "POST_USED": False,
            "WIRE_SEND": False,
            "LIVE_ACTION": "NONE",
            "FALLBACK_USED": False,
            "STORAGE_OWNER_ID": FIRST_OWNER_ID,
            "adjudication": None,
        }
    adjudication = adjudicate_live_restart_reconstructed_v1(
        restart_evidence={
            "source_kind": ADMISSIBLE_SOURCE_KIND,
            "POST_USED": False,
            "GET_PERFORMED": False,
            "PRIVATE_GET_USED": False,
            "CANCEL_USED": False,
            "AMEND_USED": False,
            "FLATTEN_EXECUTE_USED": False,
            "RESTART_EXECUTION": False,
            "LIVE_RESTART_RECONSTRUCTED": False,
            "durable_handoff": validated,
            "census": {
                "DURABLE_PRE_RESTART_HANDOFF_PRESENT": True,
                "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": True,
                "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
                "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
            },
        }
    )
    claim = bool(adjudication.get("LIVE_RESTART_RECONSTRUCTED") is True)
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_RESTART_CONSUMER_RESULT_V1",
        "RESTART_CONSUMER_SELECTED": RESTART_CONSUMER_SELECTED,
        "RESTART_CONSUMER_BOUND": True,
        "CONSUMER_ACCEPTED": True,
        "READER_RESULT": RESULT_VALID_HANDOFF,
        "REASON": (
            "IDENTITY_BOUND_LIVE_RESTART_HANDOFF_RECONSTRUCTED"
            if claim
            else str(adjudication.get("UNRESOLVED_REASON") or "CONTEMPORANEOUS_OBSERVATION_ABSENT")
        ),
        "LIVE_RESTART_RECONSTRUCTED": claim,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "GET_PERFORMED": False,
        "POST_USED": False,
        "WIRE_SEND": False,
        "LIVE_ACTION": "NONE",
        "FALLBACK_USED": False,
        "STORAGE_OWNER_ID": FIRST_OWNER_ID,
        "validated_handoff": validated,
        "adjudication": adjudication,
    }
