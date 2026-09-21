"""Typed models for CURRENT_PRODUCTIVE AVAILABLE_FOR_SIZING BASE binding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAvailableForSizingBaseFactV1,
)


class CurrentProductiveAvailableForSizingBaseBindingError(ValueError):
    """Fail-closed BASE numeric binding violation."""


@dataclass(frozen=True)
class CurrentProductiveAvailableForSizingBaseBindingV1:
    base_binding_implemented: bool
    base_slot_id: str
    numeric_base_bound: bool
    base_fact: CurrentProductiveAvailableForSizingBaseFactV1 | None
    observation_schema_class: str
    exact_allowed_numeric_source: str
    source_owner: str
    c08_base_candidate_required: bool
    c08_base_candidate_present: bool
    risk_admissible: bool
    sizing_increase: bool
    block_or_decrease: bool
    fail_closed: bool
    treasury_reconciliation_status: str
    usdc_row_status: str
    reason_codes: Tuple[str, ...]
    authority_owner: str
    join_seam_id: str
    step_29p_authority: str
    productive_host_code_reachable: bool
    provenance_digest: str
    treasury_risk_admissible_mint: bool
    treasury_available_for_sizing_mint: bool
