"""Fail-closed errors for Owner-scoped GET budget enforcement."""


class OwnerScopedGetBudgetError(RuntimeError):
    """Owner-scoped cumulative GET budget violation."""
