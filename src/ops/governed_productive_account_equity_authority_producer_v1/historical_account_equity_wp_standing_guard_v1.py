"""Standing guards for historical account-equity WPs after mapping closure."""

from __future__ import annotations

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED,
)


def mapping_closure_consumed_reexecute_forbidden_v1() -> bool:
    return CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is True


def assert_canonical_mapping_still_invalid_for_historical_wp_standing_v1() -> None:
    if mapping_closure_consumed_reexecute_forbidden_v1():
        raise MappingClosureConsumedReexecuteForbiddenError(
            "MAPPING_CLOSURE_CONSUMED_REEXECUTE_FORBIDDEN"
        )
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise MappingMustRemainInvalidForHistoricalWpError("MAPPING_MUST_REMAIN_INVALID")


class MappingClosureConsumedReexecuteForbiddenError(Exception):
    """Historical WP execute after CURRENT productive mapping closure."""


class MappingMustRemainInvalidForHistoricalWpError(Exception):
    """Unexpected canonical mapping validity during historical WP standing pins."""
