"""Fail-closed errors for external capital decrease observation binding."""


class TreasuryExternalCapitalDecreaseObservationBindingError(RuntimeError):
    """Typed binding violation. No fallback observation mint."""
