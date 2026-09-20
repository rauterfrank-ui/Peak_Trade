"""Fail-closed errors for Treasury Phase-2 venue observation binding."""


class TreasuryPhase2VenueObservationBindingError(RuntimeError):
    """Typed binding violation. No fallback observation mint."""
