"""Typed E4 orchestration handoff models. No equity mint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionEvidenceV1,
)


@dataclass(frozen=True)
class AccountEquityOrchestrationIngressV1:
    """Handoff envelope for governed account-equity orchestration. Not sizing authority."""

    orchestration_admitted: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    capital_admission_evidence: CapitalAdmissionEvidenceV1
    treasury_reconciliation_class: str
    treasury_capital_increase_authority: bool
    join_seam_id: str
    capital_admission_authority: str
    account_equity_authority: str


@dataclass(frozen=True)
class TreasuryAccountEquityOrchestrationJoinV1:
    treasury_join_seam_id: str
    ingress: AccountEquityOrchestrationIngressV1
