"""Hard GET-attempt ceiling for one CURRENT productive selection run.

Counts every authorized HTTP attempt before the socket opens. Does not choose
a numeric ceiling: the caller supplies it. Does not change ranking weights,
eligible-set membership, or the global Economic-MD retry constant.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SELECTION_INVENTORY_GETS = 4
SELECTION_ECONOMIC_MD_GETS_PER_INSTRUMENT = 2
SELECTION_ECONOMIC_MD_MAX_RETRIES = 0


class SelectionNetworkBudgetError(RuntimeError):
    """Caller supplied a budget that cannot be enforced."""


class SelectionNetworkBudgetExceeded(RuntimeError):
    """The next HTTP attempt would pass the caller ceiling. No partial publish."""


@dataclass
class SelectionNetworkBudgetV1:
    """Shared counter for inventory GETs and the following Economic-MD GETs."""

    max_total_attempts: int
    attempts: int = 0

    def __post_init__(self) -> None:
        ceiling = self.max_total_attempts
        if isinstance(ceiling, bool) or not isinstance(ceiling, int) or ceiling < 1:
            raise SelectionNetworkBudgetError("SELECTION_MAX_TOTAL_GET_ATTEMPTS_INVALID")
        if (
            isinstance(self.attempts, bool)
            or not isinstance(self.attempts, int)
            or self.attempts < 0
        ):
            raise SelectionNetworkBudgetError("SELECTION_ATTEMPT_COUNTER_INVALID")
        if self.attempts > ceiling:
            raise SelectionNetworkBudgetError("SELECTION_ATTEMPT_COUNTER_ABOVE_CEILING")

    def before_http_attempt(self) -> None:
        """Authorize one HTTP attempt, then count it. Raises before the transport."""

        if self.attempts >= self.max_total_attempts:
            raise SelectionNetworkBudgetExceeded(
                "SELECTION_NETWORK_BUDGET_EXCEEDED:"
                f"used={self.attempts}:ceiling={self.max_total_attempts}"
            )
        self.attempts += 1

    def require_complete_economic_md_collection(self, *, eligible_count: int) -> None:
        """Refuse Economic-MD collection unless every eligible instrument fits."""

        if (
            isinstance(eligible_count, bool)
            or not isinstance(eligible_count, int)
            or eligible_count < 0
        ):
            raise SelectionNetworkBudgetError("SELECTION_ELIGIBLE_COUNT_INVALID")
        attempts_per_get = SELECTION_ECONOMIC_MD_MAX_RETRIES + 1
        additional = eligible_count * SELECTION_ECONOMIC_MD_GETS_PER_INSTRUMENT * attempts_per_get
        projected = self.attempts + additional
        if projected > self.max_total_attempts:
            raise SelectionNetworkBudgetExceeded(
                "SELECTION_ECONOMIC_MD_BUDGET_INSUFFICIENT:"
                f"eligible={eligible_count}:additional={additional}:"
                f"used={self.attempts}:ceiling={self.max_total_attempts}"
            )


def build_budgeted_economic_md_source_v1(
    *,
    budget: SelectionNetworkBudgetV1,
    capture_timestamp: str,
) -> Any:
    """Public Economic-MD source whose attempts share ``budget``.

    Lives outside the protected Cap-2.4 writer. ``max_retries`` is the
    selection-path constant 0. The global Economic-MD retry constant is not
    read or written here. The source carries ``selection_budget`` so Cap-2.1
    to Cap-2.3 can refuse the whole eligible set before the first Economic-MD
    GET. The protected writer only forwards this source.
    """

    if not isinstance(budget, SelectionNetworkBudgetV1):
        raise SelectionNetworkBudgetError("SELECTION_BUDGET_REQUIRED")
    stamp = str(capture_timestamp or "").strip()
    if stamp == "":
        raise SelectionNetworkBudgetError("SELECTION_MD_CAPTURE_TIMESTAMP_REQUIRED")
    from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
        OkxPublicEconomicMdReadAdapterV1,
    )

    source = OkxPublicEconomicMdReadAdapterV1(
        capture_timestamp=stamp,
        max_retries=SELECTION_ECONOMIC_MD_MAX_RETRIES,
        before_attempt=budget.before_http_attempt,
    )
    source.selection_budget = budget
    return source
