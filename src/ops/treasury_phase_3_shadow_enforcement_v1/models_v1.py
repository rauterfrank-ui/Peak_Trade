"""Typed models for Treasury Phase-3 shadow enforcement results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TreasuryShadowEnforcementResultV1:
    shadow_permitted: bool
    fail_closed: bool
    capital_uplift_permitted: bool
    reconciliation_class: str
    reason_codes: tuple[str, ...]
    join_seam_id: str
    gate_wired: bool
    shadow_surface: str
