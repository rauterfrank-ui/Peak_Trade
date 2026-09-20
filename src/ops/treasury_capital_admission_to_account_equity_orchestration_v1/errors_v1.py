"""E4 orchestration join errors."""

from __future__ import annotations


class TreasuryAccountEquityOrchestrationError(Exception):
    """Fail-closed violation in capital-admission → account-equity orchestration join."""
