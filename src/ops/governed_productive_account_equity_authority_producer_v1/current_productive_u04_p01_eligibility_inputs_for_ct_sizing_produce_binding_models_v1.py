"""Typed models for U04/P01/eligibility inputs → CT sizing produce binding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveAvailableForSizingBaseFactV1,
    CurrentProductiveAvailableForSizingProducerOutputV1,
    CurrentProductiveP01ReductionFactV1,
    CurrentProductiveU04ReservationFactV1,
)


class CurrentProductiveU04P01EligibilityInputsBindingError(ValueError):
    """Fail-closed U04/P01/eligibility binding violation."""


@dataclass(frozen=True)
class CurrentProductiveU04ReservationTypedEvidenceV1:
    """Explicit reservation witness. No venue-field inference."""

    reservation_value_raw: str
    empty_reservation_proven: str
    witness_kind: str
    witness_digest: str


@dataclass(frozen=True)
class CurrentProductiveU04P01EligibilityHostInputsV1:
    """Host-supplied canonical inputs for CT sizing produce (no GET in join)."""

    u01_raw_acct_lv: str
    u04_evidence: CurrentProductiveU04ReservationTypedEvidenceV1


@dataclass(frozen=True)
class CurrentProductiveU04P01EligibilityInputsBindingV1:
    inputs_binding_implemented: bool
    inputs_bound: bool
    u04_fact: CurrentProductiveU04ReservationFactV1 | None
    p01_fact: CurrentProductiveP01ReductionFactV1 | None
    eligibility_fact: CurrentProductiveAccountEligibilityFactV1 | None
    producer_output: CurrentProductiveAvailableForSizingProducerOutputV1 | None
    base_fact: CurrentProductiveAvailableForSizingBaseFactV1 | None
    formula: str
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    join_seam_id: str
    u04_source_class: str
    p01_source_class: str
    p01_applicability_source: str
    eligibility_source: str
    authority_graph_changed: bool
    fallback_numerics_present: bool
