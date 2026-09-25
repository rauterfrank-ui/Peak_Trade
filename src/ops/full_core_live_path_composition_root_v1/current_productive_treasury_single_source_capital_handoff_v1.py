"""Full-Core single-source Treasury → E4/C08 → B05/29P capital handoff v1.

One trusted account-balance GET is delegated through Treasury reconciliation and
C08 transport before B05 Q0 production. No second venue read. No quantity authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Tuple

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    CapitalAdmissionEvidenceV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_AUTHORITY_NONE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    CapitalAdmissionStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    Step29PCapitalRiskAdmissibilityClaimV1,
    Step29PCapitalRiskAdmissibilityV1,
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    PRODUCER_IDENTITY,
    CurrentProductive29PRiskCapitalOutputV1,
    CurrentProductiveUsdcFreeMarginObservationV1,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1 import (
    CurrentProductiveU04P01EligibilityHostInputsV1,
    CurrentProductiveU04ReservationTypedEvidenceV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1 import (
    bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_PRESENT,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.join_v1 import (
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryReconciliationClassV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.account_balance_usdc_avail_eq_adapter_v1 import (
    build_treasury_venue_observation_from_trusted_account_balance_usdc_avail_eq_v1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_TREASURY_SINGLE_SOURCE_CAPITAL_HANDOFF_V1"
FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT = 1
TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE = False

_DEFAULT_U04_WITNESS_DIGEST = hashlib.sha256(
    b"full-core-enter-live-empty-u04-reservation-v1"
).hexdigest()


@dataclass(frozen=True)
class CurrentProductiveTreasurySingleSourceCapitalHandoffV1:
    join_seam_id: str
    equity_observation_count: int
    treasury_e4_host_reachable: bool
    base_bind_count: int
    p01_application_count: int
    capital_admission_count: int
    step_29p_admissibility_count: int
    ct_sizing_eligibility_inputs_bound: bool
    treasury_reconciliation_class: str
    producer_output: CurrentProductive29PRiskCapitalOutputV1
    capital_admission: CapitalAdmissionEvidenceV1
    step_29p_claim: Step29PCapitalRiskAdmissibilityClaimV1
    step_29p_admissibility: Step29PCapitalRiskAdmissibilityV1
    reason_codes: Tuple[str, ...]
    fail_closed: bool


class CurrentProductiveTreasurySingleSourceCapitalHandoffError(RuntimeError):
    """Fail-closed single-source Treasury capital handoff violation."""


def build_default_full_core_u04_p01_eligibility_host_inputs_v1(
    *,
    raw_acct_lv: str,
) -> CurrentProductiveU04P01EligibilityHostInputsV1:
    return CurrentProductiveU04P01EligibilityHostInputsV1(
        u01_raw_acct_lv=str(raw_acct_lv or ""),
        u04_evidence=CurrentProductiveU04ReservationTypedEvidenceV1(
            reservation_value_raw="0",
            empty_reservation_proven="true",
            witness_kind="TYPED_FULL_CORE_EMPTY_RESERVATION_WITNESS_V1",
            witness_digest=_DEFAULT_U04_WITNESS_DIGEST,
        ),
    )


def execute_current_productive_treasury_single_source_capital_handoff_v1(
    *,
    margin_observation: CurrentProductiveUsdcFreeMarginObservationV1,
    instrument_id: str,
    body_sha256: str,
    fresh_pretrade_get_status: str,
    live_account_bound_status: str,
    u04_p01_host_inputs: CurrentProductiveU04P01EligibilityHostInputsV1 | None = None,
    clear_treasury_idempotency: bool = True,
) -> CurrentProductiveTreasurySingleSourceCapitalHandoffV1:
    """Delegate one margin observation through Treasury/E4/C08 then B05 29P produce."""
    if clear_treasury_idempotency:
        clear_treasury_reconciliation_idempotency_cache_v1()
    host_inputs = u04_p01_host_inputs or build_default_full_core_u04_p01_eligibility_host_inputs_v1(
        raw_acct_lv="2",
    )
    treasury_obs = build_treasury_venue_observation_from_trusted_account_balance_usdc_avail_eq_v1(
        avail_eq_raw=str(margin_observation.value),
        account_identity=str(margin_observation.bound_account_identity),
        instrument_id=str(instrument_id),
        observed_at_utc=str(margin_observation.observed_at_as_of),
        body_sha256=str(body_sha256),
        decision_epoch=str(margin_observation.decision_epoch),
    )
    host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        treasury_obs,
        expected_account_identity=str(margin_observation.bound_account_identity),
        expected_instrument_id=str(instrument_id),
        usdc_row_status=CURRENCY_ROW_STATUS_PRESENT,
        u04_p01_eligibility_host_inputs=host_inputs,
    )
    reasons: list[str] = [JOIN_SEAM_ID]
    if host.host_evaluation.fail_closed is True:
        reasons.extend(str(code) for code in host.host_evaluation.reason_codes)
        return _fail_closed(
            reasons=tuple(dict.fromkeys(reasons)),
            treasury_class=str(host.host_evaluation.treasury_reconciliation_status or ""),
        )
    if host.host_evaluation.productive_host_reachable is not True:
        return _fail_closed(reasons=("PRODUCTIVE_HOST_UNREACHABLE",), treasury_class="")
    if host.c08_sizing_source_binding.fail_closed is True:
        reasons.extend(str(code) for code in host.c08_sizing_source_binding.reason_codes)
        return _fail_closed(
            reasons=tuple(dict.fromkeys(reasons)),
            treasury_class=str(host.treasury_join.reconciliation.reconciliation_class),
        )
    if (
        host.base_numeric_binding.fail_closed is True
        or host.base_numeric_binding.numeric_base_bound is not True
    ):
        reasons.extend(str(code) for code in host.base_numeric_binding.reason_codes)
        return _fail_closed(
            reasons=tuple(dict.fromkeys(reasons)),
            treasury_class=str(host.treasury_join.reconciliation.reconciliation_class),
        )
    u04_binding = host.u04_p01_eligibility_binding
    if u04_binding is None or u04_binding.inputs_bound is not True:
        blockers = (
            tuple(str(code) for code in u04_binding.reason_codes)
            if u04_binding is not None
            else ("U04_P01_BINDING_MISSING",)
        )
        return _fail_closed(
            reasons=blockers,
            treasury_class=str(host.treasury_join.reconciliation.reconciliation_class),
            ct_bound=False,
        )
    p01 = u04_binding.p01_fact
    eligibility = u04_binding.eligibility_fact
    if p01 is None or eligibility is None:
        return _fail_closed(
            reasons=("P01_OR_ELIGIBILITY_MISSING",),
            treasury_class=str(host.treasury_join.reconciliation.reconciliation_class),
            ct_bound=False,
        )
    base_value = str(
        host.base_numeric_binding.base_fact.value if host.base_numeric_binding.base_fact else ""
    )
    try:
        treasury_base = Decimal(base_value)
        margin_value = Decimal(str(margin_observation.value))
    except (InvalidOperation, ValueError):
        return _fail_closed(
            reasons=("TREASURY_BASE_OR_MARGIN_NOT_DECIMAL",),
            treasury_class=str(host.treasury_join.reconciliation.reconciliation_class),
            ct_bound=True,
        )
    if treasury_base > margin_value:
        return _fail_closed(
            reasons=("TREASURY_CANNOT_INCREASE_ABOVE_TRUSTED_MARGIN",),
            treasury_class=str(host.treasury_join.reconciliation.reconciliation_class),
            ct_bound=True,
        )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=margin_observation,
        p01=p01,
        eligibility=eligibility,
        eq_target=None,
        u04=None,
        restart_from_kind_set="false",
    )
    if output.produced != "true":
        return _fail_closed(
            reasons=tuple(str(code) for code in output.reason_codes),
            treasury_class=str(host.treasury_join.reconciliation.reconciliation_class),
            ct_bound=True,
            producer=output,
        )
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=str(margin_observation.bound_account_identity),
            instrument_id=str(instrument_id),
            observed_capital_raw=output.value,
            observed_field_name=PRODUCER_IDENTITY,
            evidence_class="LIVE_TYPED",
            evidence_id=str(margin_observation.decision_epoch),
        ),
        expected_account_identity=str(margin_observation.bound_account_identity),
        expected_instrument_id=str(instrument_id),
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=fresh_pretrade_get_status,
        live_account_bound_status=live_account_bound_status,
        expected_instrument_id=str(instrument_id),
        observed_instrument_id=str(instrument_id),
        fresh_evidence_fetched=True,
        fresh_evidence_validated=output.produced == "true",
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    recon = str(host.treasury_join.reconciliation.reconciliation_class or "")
    if recon != TreasuryReconciliationClassV1.RECONCILED.value:
        reasons.append(f"TREASURY_RECONCILIATION_NOT_RECONCILED:{recon}")
    fail_closed = (
        admissibility.risk_admissible is not True
        or recon != TreasuryReconciliationClassV1.RECONCILED.value
    )
    return CurrentProductiveTreasurySingleSourceCapitalHandoffV1(
        join_seam_id=JOIN_SEAM_ID,
        equity_observation_count=1,
        treasury_e4_host_reachable=True,
        base_bind_count=1,
        p01_application_count=1,
        capital_admission_count=1,
        step_29p_admissibility_count=1,
        ct_sizing_eligibility_inputs_bound=True,
        treasury_reconciliation_class=recon,
        producer_output=output,
        capital_admission=capital,
        step_29p_claim=claim,
        step_29p_admissibility=admissibility,
        reason_codes=tuple(dict.fromkeys(reasons)),
        fail_closed=fail_closed,
    )


def _fail_closed(
    *,
    reasons: Tuple[str, ...],
    treasury_class: str,
    ct_bound: bool = False,
    producer: CurrentProductive29PRiskCapitalOutputV1 | None = None,
) -> CurrentProductiveTreasurySingleSourceCapitalHandoffV1:
    empty_producer = producer or CurrentProductive29PRiskCapitalOutputV1(
        produced="false",
        value="",
        settlement_currency="USDC",
        dimension_id="RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING",
        producer_identity=PRODUCER_IDENTITY,
        algebra_id="",
        output_unit="",
        output_class="",
        bound_account_identity="",
        bound_venue_identity="",
        bound_td_mode="",
        decision_epoch="",
        observed_at_as_of="",
        input_set_digest="",
        observation_surface="",
        u04_applied="false",
        p01_applied="false",
        double_counting_guard="",
        reconciliation_status="",
        restart_reconstruction_status="",
        reason_codes=reasons,
    )
    capital = CapitalAdmissionEvidenceV1(
        evidence_status=CapitalAdmissionStatusV1.MISSING.value,
        capital_source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
        capital_authority_class=CAPITAL_AUTHORITY_NONE,
        risk_admissible=False,
        observed_capital_raw="",
        claimed_risk_admissible_capital="",
        previously_admitted_risk_capital="",
        expected_account_identity="",
        observed_account_identity="",
        expected_instrument_id="",
        observed_instrument_id="",
        reason_codes=reasons,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
    )
    claim = Step29PCapitalRiskAdmissibilityClaimV1(
        fresh_pretrade_get_status="MISSING",
        live_account_bound_status="MISSING",
        expected_instrument_id="",
        observed_instrument_id="",
        expected_currency="USDC",
        observed_currency="",
        equity_dimension="RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING",
        typed_account_equity_raw="",
        typed_account_equity_source_field="",
        fresh_evidence_fetched=False,
        fresh_evidence_validated=False,
    )
    adm = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    return CurrentProductiveTreasurySingleSourceCapitalHandoffV1(
        join_seam_id=JOIN_SEAM_ID,
        equity_observation_count=1,
        treasury_e4_host_reachable=False,
        base_bind_count=0 if "TREASURY_CANNOT_INCREASE" in " ".join(reasons) else 1,
        p01_application_count=0,
        capital_admission_count=0,
        step_29p_admissibility_count=0,
        ct_sizing_eligibility_inputs_bound=ct_bound,
        treasury_reconciliation_class=treasury_class,
        producer_output=empty_producer,
        capital_admission=capital,
        step_29p_claim=claim,
        step_29p_admissibility=adm,
        reason_codes=reasons,
        fail_closed=True,
    )


__all__ = (
    "FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT",
    "JOIN_SEAM_ID",
    "TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE",
    "CurrentProductiveTreasurySingleSourceCapitalHandoffError",
    "CurrentProductiveTreasurySingleSourceCapitalHandoffV1",
    "build_default_full_core_u04_p01_eligibility_host_inputs_v1",
    "execute_current_productive_treasury_single_source_capital_handoff_v1",
)
