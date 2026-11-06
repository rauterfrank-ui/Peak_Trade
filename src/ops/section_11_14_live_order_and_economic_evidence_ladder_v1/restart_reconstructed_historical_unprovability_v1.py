"""Historical identity unprovability bind for LIVE_RESTART_RECONSTRUCTED.

Does not deny that the bound Live order, ACK, fill, position, or accounting
were observed. It binds only that the §11.14 restart-handoff criterion cannot
be made true retroactively for this identity.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    HISTORICAL_LIVE_RESTART_HANDOFF_STATUS,
    RETROACTIVE_PROOF_FROM_POST_SUBMIT_VENUE_STATE_ALLOWED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    bound_live_restart_identity_v1,
)


def bind_historical_live_restart_unprovability_v1() -> dict[str, Any]:
    identity = bound_live_restart_identity_v1()
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_HISTORICAL_LIVE_RESTART_UNPROVABILITY_BIND_V1",
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_POS_SIDE": BOUND_POS_SIDE,
        "BOUND_FILL_SZ": BOUND_FILL_SZ,
        "BOUND_IDENTITY": identity,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": (
            CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED
        ),
        "RETROACTIVE_PROOF_FROM_POST_SUBMIT_VENUE_STATE_ALLOWED": (
            RETROACTIVE_PROOF_FROM_POST_SUBMIT_VENUE_STATE_ALLOWED
        ),
        "HISTORICAL_LIVE_RESTART_HANDOFF_STATUS": HISTORICAL_LIVE_RESTART_HANDOFF_STATUS,
        "DOES_NOT_DENY_ORDER_WAS_REAL": True,
        "DOES_NOT_DENY_ACK_WAS_OBSERVED": True,
        "DOES_NOT_DENY_FILL_WAS_OBSERVED": True,
        "DOES_NOT_DENY_POSITION_WAS_OBSERVED": True,
        "DOES_NOT_DENY_ACCOUNTING_WAS_OBSERVED": True,
        "MEANS_ONLY": (
            "The specific §11.14 restart-handoff criterion cannot be made true "
            "retroactively for this historical identity."
        ),
    }
