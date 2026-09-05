"""Fail-closed errors for Treasury Phase-1 offline contracts."""

from __future__ import annotations


class TreasuryPhase1ContractError(ValueError):
    """Typed fail-closed rejection. Never a network or mutation signal."""


class TreasurySecretHygieneError(TreasuryPhase1ContractError):
    """Secret-bearing payload rejected before serialization."""


class TreasuryLifecycleError(TreasuryPhase1ContractError):
    """Illegal or contradictory lifecycle transition."""


class TreasuryIdempotencyError(TreasuryPhase1ContractError):
    """Same intent with changed economic parameters, or unsafe retry."""


class TreasuryPersistenceError(TreasuryPhase1ContractError):
    """Malformed, corrupted, or unsupported persisted record."""
