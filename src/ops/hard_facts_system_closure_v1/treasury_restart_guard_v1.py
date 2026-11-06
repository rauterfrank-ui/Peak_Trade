"""Structural treasury / reservation / restart fail-closed guards (no direction authority)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
    reservation_identity_material_v1,
)


@dataclass(frozen=True)
class TreasuryAdmissionGuardResultV1:
    admitted: bool
    reason_code: str
    stale_or_ambiguous: bool


def evaluate_treasury_admission_guard_v1(
    *,
    observation_trusted: bool,
    reconciliation_pass: bool,
    avail_eq_positive: bool,
    numeric_fresh: bool,
) -> TreasuryAdmissionGuardResultV1:
    if not observation_trusted or not reconciliation_pass:
        return TreasuryAdmissionGuardResultV1(
            admitted=False,
            reason_code="TREASURY_TRUTH_UNTRUSTED",
            stale_or_ambiguous=True,
        )
    if not numeric_fresh:
        return TreasuryAdmissionGuardResultV1(
            admitted=False,
            reason_code="TREASURY_STALE_EQUITY",
            stale_or_ambiguous=True,
        )
    if not avail_eq_positive:
        return TreasuryAdmissionGuardResultV1(
            admitted=False,
            reason_code="TREASURY_NON_POSITIVE_AVAIL_EQ",
            stale_or_ambiguous=False,
        )
    return TreasuryAdmissionGuardResultV1(
        admitted=True,
        reason_code="TREASURY_ADMISSION_OK",
        stale_or_ambiguous=False,
    )


def reservation_cross_epoch_forbidden_v1(
    *,
    prior_material: Mapping[str, str] | None,
    current: BoundInstrumentLaneIdentityV1,
    decision_id: str,
    cycle_id: str,
    observation_id: str,
) -> bool:
    current_material = reservation_identity_material_v1(
        lane_identity=current,
        decision_id=decision_id,
        cycle_id=cycle_id,
        observation_id=observation_id,
    )
    if prior_material is None:
        return False
    return prior_material.get("instrument_epoch") != current_material["instrument_epoch"]


def restart_silent_advance_forbidden_v1(
    *,
    prior_confirmation_epoch: int | None,
    restored_confirmation_epoch: int | None,
    identity_changed: bool,
) -> bool:
    if identity_changed:
        return False
    if prior_confirmation_epoch is None or restored_confirmation_epoch is None:
        return False
    return restored_confirmation_epoch > prior_confirmation_epoch


def stale_equity_reuse_forbidden_v1(
    *,
    prior_observation_id: str,
    current_observation_id: str,
    admitted_budget: Decimal,
    prior_budget: Decimal | None,
    restart_recovery: bool,
) -> bool:
    if not restart_recovery:
        return False
    if prior_observation_id == current_observation_id and prior_budget == admitted_budget:
        return True
    return False
