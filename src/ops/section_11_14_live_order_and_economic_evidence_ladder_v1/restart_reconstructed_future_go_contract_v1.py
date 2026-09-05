"""Machine-readable future Owner-GO contract for LIVE_RESTART_RECONSTRUCTED.

Specifies the minimum later operation. Does not execute it. Does not
authorize restart, GET, POST, or productive runtime mutation.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    NEXT_OWNER_GO_REQUIRED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    HANDOFF_DOCUMENT_CLASS,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    RESTART_IDENTITY_EQUATION,
)


def bind_future_live_restart_owner_go_contract_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_RESTART_FUTURE_OWNER_GO_CONTRACT_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT_FUTURE_GO_SPEC_ONLY",
        "THIS_CENSUS_DOES_NOT_AUTHORIZE_THE_FUTURE_GO": True,
        "FUTURE_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "FUTURE_LIVE_OR_RESTART_OWNER_GO_REQUIRED": True,
        "EARLIEST_MISSING_FACT": "DURABLE_LIVE_PRE_RESTART_HANDOFF",
        "FUTURE_MINIMUM_OPERATION": (
            "PERSIST_IDENTITY_BOUND_PEAK_TRADE_DURABLE_PRE_RESTART_HANDOFF"
        ),
        "FUTURE_MINIMUM_OPERATION_DETAIL": (
            "Persist a Peak_Trade durable pre-restart handoff for the bound Live "
            "submit identity, distinct from venue-GET fill/fee/position artifacts, "
            "then adjudicate LIVE_RESTART_RECONSTRUCTED offline from that handoff "
            "using source_kind GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF."
        ),
        "FRESH_PROCESS_RESTART_REQUIRED_FOR_THIS_FIELD": False,
        "FRESH_PROCESS_RESTART_INSUFFICIENT_WITHOUT_HANDOFF": True,
        "FRESH_PROCESS_RESTART_NOT_AUTHORIZED_HERE": True,
        "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET_ACCOUNTING_PATH": True,
        "HANDOFF_DOCUMENT_CLASS": HANDOFF_DOCUMENT_CLASS,
        "HANDOFF_REQUIRED_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        "HANDOFF_POS_MUST_BE_DECIMAL_PARSEABLE": True,
        "HANDOFF_POS_MUST_BE_NONZERO_WHEN_FILL_SZ_NONZERO": True,
        "RESTART_IDENTITY_EQUATION": RESTART_IDENTITY_EQUATION,
        "SOURCE_KIND_REQUIRED": ADMISSIBLE_SOURCE_KIND,
        "GET_NOT_REQUIRED_WHEN_HANDOFF_ALREADY_PERSISTED": True,
        "POST_NOT_REQUIRED": True,
        "RETRY_DEFAULT": False,
        "SECOND_SUBMIT_DEFAULT": False,
        "ACCOUNTING_CLOSURE_IS_NOT_RESTART": True,
        "TESTNET_RESTART_PROVEN_IS_NOT_THIS_FIELD": True,
        "SECTION_11_17_LIVE_RESTART_PROVEN_IS_NOT_THIS_FIELD": True,
        "LIVE_DURABLE_STATE_WRITER_ON_SECTION_11_14_CANARY_EXISTS": False,
        "RUNTIME_CHANGE_REQUIRES_SEPARATE_OWNER_SCOPE": True,
        "RUNTIME_CHANGE_REQUIRED_IF_NO_EXISTING_WRITER": (
            "A Peak_Trade Live durable_state writer on the bound Live identity "
            "path is absent. Adding that writer is productive runtime scope and "
            "is not authorized by this offline census."
        ),
        "POST_RESTART_RECOVERY_EVIDENCE": (
            "Offline reconstruction from the durable handoff is sufficient for "
            "this field when the bound criterion is met. LIVE_AUTONOMOUS_RECOVERY_OBSERVED "
            "remains a later field and is not satisfied by this persist."
        ),
    }
