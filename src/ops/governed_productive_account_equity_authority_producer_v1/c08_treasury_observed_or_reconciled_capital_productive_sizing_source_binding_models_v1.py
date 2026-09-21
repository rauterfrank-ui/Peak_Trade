"""Typed models for C08 productive sizing-source binding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


class C08ProductiveSizingSourceBindingError(ValueError):
    """Fail-closed C08 productive sizing-source binding violation."""


@dataclass(frozen=True)
class C08ProductiveSizingSourceBindingV1:
    c08_binding_implemented: bool
    c08_input_class: str
    base_slot_id: str
    base_value_status: str
    base_candidate_transport_status: str
    base_candidate_created: bool
    base_candidate_directly_available_for_sizing: bool
    risk_admissible: bool
    risk_admissibility_separate: bool
    treasury_risk_admissible_mint: bool
    treasury_available_for_sizing_mint: bool
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
