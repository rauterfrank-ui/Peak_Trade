"""Minimum higher-authority class for making P08 closable.

Chooses the lowest class that is both semantically capable and technically
supported. Does not choose Live because it exists in architecture. Does not
choose Testnet because it is safer. Never executes.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    FUTURE_EXECUTION_GO_DRAFT_STATUS,
    MINIMUM_HIGHER_AUTHORITY,
    NEXT_AUTHORITY_BOUNDARY,
    P08_NEXT_AUTHORITY_RESULT,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.mechanism_census_v1 import (
    DISPOSITION_EXTERNAL_ONLY,
    DISPOSITION_NOT_P08_CAPABLE,
    MECHANISMS,
)


class P08AuthorityBoundaryError(RuntimeError):
    """Fail-closed authority-boundary selection violation."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise P08AuthorityBoundaryError(code)


def adjudicate_minimum_higher_authority_v1(
    *,
    census: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> dict[str, Any]:
    """Select the lowest capable authority class. Not execute."""
    viable = list(census.get("VIABLE_MECHANISM_IDS") or [])
    _require(census.get("TESTNET_CAN_SATISFY_P08") is False, "TESTNET_MUST_REMAIN_NOT_P08_CAPABLE")
    _require(
        census.get("CANARY_FIRST_PARTY_CREATE_CURRENTLY_VIABLE") is False,
        "CANARY_MUST_REMAIN_NOT_CURRENTLY_VIABLE",
    )
    _require(
        census.get("LIVE_FIRST_PARTY_CREATE_CURRENTLY_VIABLE") is False,
        "LIVE_MUST_REMAIN_NOT_CURRENTLY_VIABLE",
    )
    _require(
        census.get("AVAILABLE_WITHOUT_MUTATION_CURRENTLY_TRUE") is False,
        "MUST_NOT_CLAIM_AVAILABLE_WITHOUT_MUTATION",
    )
    _require(
        viable == ["M02_EXTERNAL_MANUAL_VENUE_UI_POSITION"], "VIABLE_SET_MUST_BE_EXTERNAL_ONLY"
    )
    _require(
        readiness.get("G_POSMODE_SUBMIT_BODY_PROVEN") is False,
        "G_POSMODE_MUST_REMAIN_UNPROVEN",
    )
    testnet_capable = any(
        item.would_create_exact_p08_observation and item.disposition != DISPOSITION_NOT_P08_CAPABLE
        for item in MECHANISMS
        if item.mechanism_id == "M06_OKX_EEA_DEMO_TESTNET_EXECUTION"
    )
    _require(not testnet_capable, "TESTNET_MARKED_P08_CAPABLE")
    external = next(
        item for item in MECHANISMS if item.mechanism_id == "M02_EXTERNAL_MANUAL_VENUE_UI_POSITION"
    )
    _require(external.disposition == DISPOSITION_EXTERNAL_ONLY, "EXTERNAL_DISPOSITION_DRIFT")
    _require(external.currently_viable_for_p08 is True, "EXTERNAL_MUST_REMAIN_VIABLE")
    _require(
        external.would_create_exact_p08_observation is True, "EXTERNAL_MUST_REMAIN_P08_CAPABLE"
    )
    return {
        "P08_NEXT_AUTHORITY_RESULT": P08_NEXT_AUTHORITY_RESULT,
        "MINIMUM_HIGHER_AUTHORITY": MINIMUM_HIGHER_AUTHORITY,
        "SELECTION_REASON": (
            "Z2DN_SOURCE_IRRELEVANT_IF_CANONICAL_NONZERO_OBSERVED;"
            "G_POSMODE_BLOCKS_FIRST_PARTY_PEAK_TRADE_CREATE;"
            "TESTNET_WRONG_HOST_AND_ACCOUNT;"
            "CANARY_AND_LIVE_ARE_HIGHER_AND_CURRENTLY_UNAUTHORIZED"
        ),
        "REJECTED_TESTNET_BECAUSE_SAFER": False,
        "REJECTED_LIVE_BECAUSE_AVAILABLE_IN_ARCHITECTURE": False,
        "FIRST_PARTY_CANARY_CREATE_BLOCKED_BY_G_POSMODE": True,
        "FIRST_PARTY_LIVE_CREATE_BLOCKED_BY_STANDING_AUTH": True,
        "FUNDING_DOES_NOT_CHANGE_MINIMUM_CLASS": True,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "FUTURE_EXECUTION_GO_DRAFT_STATUS": FUTURE_EXECUTION_GO_DRAFT_STATUS,
        "VIABLE_MECHANISM_IDS": viable,
    }
