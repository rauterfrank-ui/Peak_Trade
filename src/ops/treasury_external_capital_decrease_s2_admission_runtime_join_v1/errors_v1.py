"""S2 admission runtime join errors. Fail closed."""

from __future__ import annotations


class TreasuryExternalCapitalDecreaseS2AdmissionError(RuntimeError):
    """Typed S2 decrease admission join failure."""
