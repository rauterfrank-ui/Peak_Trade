"""Fail-closed errors for Treasury Phase-3 shadow enforcement."""

from __future__ import annotations


class TreasuryPhase3ShadowEnforcementError(RuntimeError):
    """Shadow enforcement deny or contract violation."""
