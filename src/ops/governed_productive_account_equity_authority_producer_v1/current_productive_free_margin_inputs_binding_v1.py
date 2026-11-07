"""Bind the existing 29P free-margin producer after Treasury/E4/C08 transport.

No CT BASE is constructed and no second sizing formula is introduced. U04 has
no coverage identity here: a nonempty witness cannot establish whether a local
hold is already represented at the venue. Such observations remain blocked.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    CurrentProductive29PRiskCapitalOutputV1,
    CurrentProductiveUsdcFreeMarginObservationV1,
    produce_current_productive_29p_risk_capital_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
    check_and_record_current_productive_capital_observation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveP01ReductionFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1 import (
    CurrentProductiveU04P01EligibilityHostInputsV1,
    CurrentProductiveU04P01EligibilityInputsBindingError,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1 import (
    bind_current_productive_p01_fact_for_ct_sizing_produce_v1,
    bind_current_productive_u04_reservation_fact_from_typed_evidence_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryBalanceSourceV1,
    TreasuryVenueObservationV1,
)


@dataclass(frozen=True)
class CurrentProductiveFreeMarginInputsBindingV1:
    inputs_bound: bool
    fail_closed: bool
    p01_fact: CurrentProductiveP01ReductionFactV1 | None
    eligibility_fact: CurrentProductiveAccountEligibilityFactV1 | None
    producer_output: CurrentProductive29PRiskCapitalOutputV1 | None
    reason_codes: tuple[str, ...]


def bind_current_productive_free_margin_inputs_and_produce_v1(
    *,
    treasury_observation: TreasuryVenueObservationV1,
    margin_observation: CurrentProductiveUsdcFreeMarginObservationV1 | None,
    host_inputs: CurrentProductiveU04P01EligibilityHostInputsV1 | None,
    treasury_host_admitted: bool,
    decision_epoch: str,
    age_seconds: str,
    freshness_max_age: str,
) -> CurrentProductiveFreeMarginInputsBindingV1:
    """Preserve source, value, account, acquisition time and decision at the consumer."""
    reasons: list[str] = []
    if not treasury_host_admitted:
        reasons.append("TREASURY_E4_C08_NOT_ADMITTED_FOR_FREE_MARGIN")
    if treasury_observation.balance_source != TreasuryBalanceSourceV1.ACCOUNT_FREE_MARGIN.value:
        reasons.append("FREE_MARGIN_REQUIRES_ACCOUNT_SOURCE")
    if margin_observation is None:
        reasons.append("ORIGINAL_FREE_MARGIN_OBSERVATION_MISSING")
    if host_inputs is None:
        reasons.append("FREE_MARGIN_HOST_INPUTS_MISSING")
    if reasons:
        return _blocked(reasons)
    assert margin_observation is not None
    assert host_inputs is not None
    original = margin_observation
    pairs = (
        (treasury_observation.venue_balance_raw, original.value, "VALUE"),
        (treasury_observation.account_identity, original.bound_account_identity, "ACCOUNT"),
        (treasury_observation.observed_at_utc, original.observed_at_as_of, "ACQUISITION_TIME"),
        (treasury_observation.evidence_fingerprint, original.provenance_digest, "PROVENANCE"),
        (decision_epoch, original.decision_epoch, "DECISION"),
        (age_seconds, original.age_seconds, "AGE"),
        (freshness_max_age, original.freshness_max_age, "TTL"),
    )
    for received, expected, name in pairs:
        if received != expected:
            reasons.append(f"TREASURY_FREE_MARGIN_{name}_MISMATCH")
    if reasons:
        return _blocked(reasons)
    try:
        # Validate the original explicit witness, without inventing an empty one.
        # This U04 fact is never an argument of the free-margin producer.
        witness = bind_current_productive_u04_reservation_fact_from_typed_evidence_v1(
            base=original,
            evidence=host_inputs.u04_evidence,
            age_seconds=original.age_seconds,
            freshness_max_age=original.freshness_max_age,
        )
        if Decimal(witness.value) != 0:
            return _blocked(["U04_COVERAGE_UNRESOLVED_FOR_FREE_MARGIN"])
        p01 = bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
            base=original,
            age_seconds=original.age_seconds,
            freshness_max_age=original.freshness_max_age,
        )
    except CurrentProductiveU04P01EligibilityInputsBindingError as exc:
        return _blocked([str(exc)])
    eligibility = build_current_productive_u01_eligibility_fact_v1(
        adaptation=adapt_current_productive_u01_account_mode_v1(host_inputs.u01_raw_acct_lv),
        bound_account_identity=original.bound_account_identity,
        bound_venue_identity=original.bound_venue_identity,
        bound_td_mode=original.bound_td_mode,
        decision_epoch=original.decision_epoch,
        provenance_digest=hashlib.sha256(
            f"{host_inputs.u01_raw_acct_lv}:{original.decision_epoch}".encode()
        ).hexdigest(),
    )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=original, p01=p01, eligibility=eligibility, u04=None
    )
    produced = output.produced == "true"
    if produced:
        ordered, ordering_reasons = check_and_record_current_productive_capital_observation_v1(
            source=treasury_observation.balance_source,
            account=original.bound_account_identity,
            observed_at=original.observed_at_as_of,
            fingerprint=original.provenance_digest,
            value=original.value,
        )
        if not ordered:
            return _blocked(list(ordering_reasons))
    return CurrentProductiveFreeMarginInputsBindingV1(
        inputs_bound=produced,
        fail_closed=not produced,
        p01_fact=p01,
        eligibility_fact=eligibility,
        producer_output=output,
        reason_codes=tuple(output.reason_codes),
    )


def _blocked(reasons: list[str]) -> CurrentProductiveFreeMarginInputsBindingV1:
    return CurrentProductiveFreeMarginInputsBindingV1(
        inputs_bound=False,
        fail_closed=True,
        p01_fact=None,
        eligibility_fact=None,
        producer_output=None,
        reason_codes=tuple(reasons),
    )
