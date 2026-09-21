"""Typed E4 productive host join result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.models_v1 import (
    TreasuryAccountEquityOrchestrationJoinV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryCapitalAdmissionJoinV1,
)


@dataclass(frozen=True)
class ProductiveHostTreasuryCapitalAdmissionEvaluationV1:
    """Governed productive host evaluation of E4 ingress. No equity or sizing mint."""

    productive_host_reachable: bool
    fail_closed: bool
    orchestration_ingress_admitted: bool
    treasury_capital_admitted: bool
    observed_equity_minted: bool
    reconciled_equity_minted: bool
    risk_admissible_mint: bool
    sizing_authority_changed: bool
    treasury_reconciliation_status: str
    usdc_row_status: str
    reason_codes: Tuple[str, ...]
    join_seam_id: str
    account_equity_authority: str
    e4_join_seam_id: str
    capital_admission_authority: str


@dataclass(frozen=True)
class TreasuryE4ProductiveHostJoinResultV1:
    treasury_join: TreasuryCapitalAdmissionJoinV1
    orchestration_join: TreasuryAccountEquityOrchestrationJoinV1
    host_evaluation: ProductiveHostTreasuryCapitalAdmissionEvaluationV1
    join_seam_id: str
