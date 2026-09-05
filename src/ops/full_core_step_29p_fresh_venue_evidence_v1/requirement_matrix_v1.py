"""Requirement matrix for STEP-29P fresh venue GETs.

Derived from current Full-Core REQUIRED_GET_ITEM_SPECS plus ticker as
max-size query px only. Historical GET lists inform endpoints; they do
not replace freshness. availEq is observation, not 29P equity authority.
"""

from __future__ import annotations

from typing import Tuple

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    REQUIRED_GET_ITEM_SPECS,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
    RISK_EQUITY_DIMENSION,
    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.constants_v1 import (
    AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY,
    BOUND_INSTRUMENT_ID,
    BOUND_SETTLEMENT_CURRENCY,
    BOUND_TD_MODE,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT_PUBLIC_TICKER,
    TICKER_CONSUMER,
    TICKER_IS_NOT_29P_PRICE_AUTHORITY,
)

FRESHNESS_REQUIREMENT = "FRESH_GET_PER_PRETRADE_DECISION"


def fresh_evidence_requirement_matrix_v1() -> Tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for spec in REQUIRED_GET_ITEM_SPECS:
        currency_scope = (
            BOUND_SETTLEMENT_CURRENCY
            if spec.item_id == "AVAILABLE_MARGIN"
            else "NOT_CURRENCY_SCOPED"
        )
        fail_closed = "code!=0 OR HTTP/auth error OR missing expected row → fail-closed"
        if spec.item_id == "MARGIN_MODE":
            fail_closed = (
                "code!=0 OR HTTP/auth error → fail-closed; empty positions data is "
                f"NOT_OBSERVED (EMPTY_DATA_IS_ZERO={EMPTY_DATA_IS_ZERO})"
            )
        if spec.item_id == "AVAILABLE_MARGIN":
            fail_closed = (
                "code!=0 OR HTTP/auth error OR missing USDC details row → NOT_OBSERVED; "
                f"availEq is observation only (AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY="
                f"{AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY}); never maps to {RISK_EQUITY_DIMENSION}"
            )
        rows.append(
            {
                "REQUIREMENT": spec.item_id,
                "SOURCE_AUTHORITY": "REQUIRED_GET_ITEM_SPECS+VENUE_PRETRADE_GATES",
                "ENDPOINT": spec.endpoint_path,
                "AUTH_CLASS": "PRIVATE_SIGNED" if spec.auth_required else "PUBLIC_UNAUTHENTICATED",
                "EXPECTED_INSTRUMENT_SCOPE": BOUND_INSTRUMENT_ID,
                "EXPECTED_CURRENCY_SCOPE": currency_scope,
                "EXPECTED_TD_MODE": BOUND_TD_MODE,
                "FRESHNESS_REQUIREMENT": FRESHNESS_REQUIREMENT,
                "CONSUMER": STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
                "FAIL_CLOSED_BEHAVIOR": fail_closed,
            }
        )
    rows.append(
        {
            "REQUIREMENT": "TICKER_LAST_FOR_MAX_SIZE_QUERY_PX",
            "SOURCE_AUTHORITY": "account/max-size query px helper; not STEP 29P price authority",
            "ENDPOINT": ENDPOINT_PUBLIC_TICKER,
            "AUTH_CLASS": "PUBLIC_UNAUTHENTICATED",
            "EXPECTED_INSTRUMENT_SCOPE": BOUND_INSTRUMENT_ID,
            "EXPECTED_CURRENCY_SCOPE": "NOT_CURRENCY_SCOPED",
            "EXPECTED_TD_MODE": BOUND_TD_MODE,
            "FRESHNESS_REQUIREMENT": FRESHNESS_REQUIREMENT,
            "CONSUMER": TICKER_CONSUMER,
            "FAIL_CLOSED_BEHAVIOR": (
                "code!=0 OR missing last → max-size proceeds without px; "
                f"TICKER_IS_NOT_29P_PRICE_AUTHORITY={TICKER_IS_NOT_29P_PRICE_AUTHORITY}"
            ),
        }
    )
    rows.append(
        {
            "REQUIREMENT": RISK_EQUITY_DIMENSION,
            "SOURCE_AUTHORITY": STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
            "ENDPOINT": "NONE_CANONICAL_VENUE_MAPPING",
            "AUTH_CLASS": "NOT_FETCHABLE",
            "EXPECTED_INSTRUMENT_SCOPE": BOUND_INSTRUMENT_ID,
            "EXPECTED_CURRENCY_SCOPE": REQUIRED_SETTLEMENT_CURRENCY,
            "EXPECTED_TD_MODE": BOUND_TD_MODE,
            "FRESHNESS_REQUIREMENT": FRESHNESS_REQUIREMENT,
            "CONSUMER": STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
            "FAIL_CLOSED_BEHAVIOR": (
                "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED; observation fields "
                "availEq/totalEq/eq/adjEq/availBal/cashBal are forbidden 29P authority; "
                "missing typed equity → RISK_ADMISSIBLE=false"
            ),
        }
    )
    return tuple(rows)


FRESH_EVIDENCE_REQUIREMENT_MATRIX = fresh_evidence_requirement_matrix_v1()
