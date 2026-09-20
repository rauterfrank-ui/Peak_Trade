"""Typed S2 decrease admission runtime join models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryCapitalAdmissionJoinV1,
)


@dataclass(frozen=True)
class TreasuryExternalCapitalDecreaseS2AdmissionContractV1:
    contract_satisfied: bool
    fail_closed: bool
    optimistic_restore_denied: bool
    capital_increase_denied: bool
    reason_codes: Tuple[str, ...]
    join_seam_id: str


@dataclass(frozen=True)
class TreasuryExternalCapitalDecreaseAdmissionRuntimeJoinV1:
    contract: TreasuryExternalCapitalDecreaseS2AdmissionContractV1
    treasury_join: TreasuryCapitalAdmissionJoinV1
    capital_admission_evidence: object
    join_seam_id: str
    capital_admission_authority: str
