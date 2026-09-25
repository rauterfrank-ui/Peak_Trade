"""Bind typed Treasury reconciled numeric evidence to CURRENT_PRODUCTIVE BASE.

Requires C08 RECONCILED base candidacy transport. Does not mint AVAILABLE_FOR_SIZING,
risk-admissible capital, or treasury sizing authority. STEP-29P policy unchanged.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Protocol, Tuple

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionEvidenceV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
    Step29PCapitalRiskAdmissibilityClaimV1,
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_productive_sizing_source_binding_models_v1 import (
    C08ProductiveSizingSourceBindingV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1 import (
    CURRENT_RISK_ADMISSIBILITY_OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_models_v1 import (
    CurrentProductiveAvailableForSizingBaseBindingError,
    CurrentProductiveAvailableForSizingBaseBindingV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAvailableForSizingBaseFactV1,
    bind_step_29p_typed_equity_from_producer_v1,
    produce_current_productive_available_for_sizing_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.non_forbidden_non_eq_non_stock_usdc_current_productive_observation_v1 import (
    SCHEMA_CLASS as OBSERVATION_SCHEMA_CLASS,
    NonForbiddenNonEqNonStockUsdcCurrentProductiveObservationV1,
    NonForbiddenUsdcCurrentProductiveObservationError,
    build_non_forbidden_usdc_current_productive_observation_from_treasury_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    CURRENCY_ROW_STATUS_PRESENT,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryFreshnessSignalV1,
    TreasuryVenueObservationV1,
)

SCHEMA_CLASS = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1"
CONTRACT_VERSION = "v1"
WP_ID = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1"
OWNER_GO = "OWNER_GO_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1"

EXACT_ALLOWED_NUMERIC_SOURCE = (
    "TreasuryVenueObservationV1.venue_balance_raw_via_treasury_phase_2_reconciled_venue_balance"
)
SOURCE_OWNER = (
    "ops.treasury_phase_2_read_only_venue_observation_binding_v1;"
    "ops.treasury_phase_2_read_only_reconciliation_v1;"
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1"
)

BASE_BINDING_IMPLEMENTED = True
BASE_BINDING_AUTHORIZED = True


class _ProductiveHostEvaluationLike(Protocol):
    productive_host_reachable: bool
    fail_closed: bool
    treasury_reconciliation_status: str
    usdc_row_status: str


_latest_binding_by_account: dict[str, tuple[str, str]] = {}
_seen_evidence_fingerprints: set[str] = set()
_last_base_fact_by_fingerprint: dict[str, CurrentProductiveAvailableForSizingBaseFactV1] = {}


def clear_current_productive_base_binding_state_v1() -> None:
    """Test-only reset for ordering/idempotency proofs."""
    _latest_binding_by_account.clear()
    _seen_evidence_fingerprints.clear()
    _last_base_fact_by_fingerprint.clear()


def _digest(payload: Mapping[str, str]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _assert_binding_envelope() -> None:
    from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
        AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
        RISK_ADMISSIBLE_MINT_AUTHORIZED,
    )

    if not BASE_BINDING_AUTHORIZED or not BASE_BINDING_IMPLEMENTED:
        raise CurrentProductiveAvailableForSizingBaseBindingError("BASE_BINDING_NOT_AUTHORIZED")
    if RISK_ADMISSIBLE_MINT_AUTHORIZED or AVAILABLE_FOR_SIZING_MINT_AUTHORIZED:
        raise CurrentProductiveAvailableForSizingBaseBindingError("DOWNSTREAM_MINT_FORBIDDEN")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS != "BOUND":
        raise CurrentProductiveAvailableForSizingBaseBindingError(
            "STANDING_BASE_SLOT_MUST_BE_BOUND_AT_MODULE_LEVEL"
        )


def _observation_to_base_fact_v1(
    observation: NonForbiddenNonEqNonStockUsdcCurrentProductiveObservationV1,
) -> CurrentProductiveAvailableForSizingBaseFactV1:
    return CurrentProductiveAvailableForSizingBaseFactV1(
        fact_id=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
        value=observation.value_raw,
        settlement_currency=observation.settlement_currency,
        bound_account_identity=observation.bound_account_identity,
        bound_venue_identity=observation.bound_venue_identity,
        bound_td_mode=observation.bound_td_mode,
        decision_epoch=observation.decision_epoch,
        observed_at_as_of=observation.observed_at_as_of,
        age_seconds=observation.age_seconds,
        freshness_max_age=observation.freshness_max_age,
        provenance_digest=observation.provenance_digest,
        source_class=observation.schema_class,
        already_net_of_u04="false",
    )


def bind_current_productive_available_for_sizing_base_from_treasury_host_v1(
    *,
    treasury_observation: TreasuryVenueObservationV1,
    c08_binding: C08ProductiveSizingSourceBindingV1,
    host_evaluation: _ProductiveHostEvaluationLike,
    usdc_row_status: str = "",
    bound_venue_identity: str = "okx",
    bound_td_mode: str = "cross",
    decision_epoch: str = "",
    age_seconds: str = "1",
    freshness_max_age: str = "5",
    capital_admission_evidence: CapitalAdmissionEvidenceV1,
    step_29p_claim: Step29PCapitalRiskAdmissibilityClaimV1 | None = None,
) -> CurrentProductiveAvailableForSizingBaseBindingV1:
    """Bind numeric BASE when C08 base candidacy and typed observation both pass."""
    _assert_binding_envelope()
    reasons: list[str] = []
    account = str(treasury_observation.account_identity or "")
    row_status = str(usdc_row_status or host_evaluation.usdc_row_status or "")
    if row_status == "" and str(treasury_observation.venue_balance_raw or "").strip() != "":
        row_status = CURRENCY_ROW_STATUS_PRESENT
    recon_status = str(
        c08_binding.treasury_reconciliation_status or host_evaluation.treasury_reconciliation_status
    )

    if c08_binding.base_candidate_created is not True:
        reasons.append("C08_BASE_CANDIDACY_REQUIRED_FOR_NUMERIC_BASE")
        fail_closed = True
        numeric_bound = False
        base_fact = None
    elif host_evaluation.fail_closed is True or c08_binding.fail_closed is True:
        reasons.append("HOST_OR_C08_FAIL_CLOSED")
        fail_closed = True
        numeric_bound = False
        base_fact = None
    elif row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO:
        reasons.append("USDC_ROW_ABSENT_NOT_ZERO_FAIL_CLOSED")
        fail_closed = True
        numeric_bound = False
        base_fact = None
    elif str(treasury_observation.balance_freshness or "") == TreasuryFreshnessSignalV1.STALE.value:
        reasons.append("TREASURY_BALANCE_STALE_FAIL_CLOSED")
        fail_closed = True
        numeric_bound = False
        base_fact = None
    else:
        epoch = str(decision_epoch or treasury_observation.observed_at_utc or "").strip()
        try:
            typed = build_non_forbidden_usdc_current_productive_observation_from_treasury_v1(
                observation=treasury_observation,
                usdc_row_status=row_status,
                treasury_reconciliation_class=recon_status,
                bound_account_identity=account,
                bound_venue_identity=bound_venue_identity,
                bound_td_mode=bound_td_mode,
                decision_epoch=epoch,
                age_seconds=age_seconds,
                freshness_max_age=freshness_max_age,
            )
        except NonForbiddenUsdcCurrentProductiveObservationError as exc:
            reasons.append(str(exc))
            fail_closed = True
            numeric_bound = False
            base_fact = None
        else:
            fp = str(treasury_observation.evidence_fingerprint or "")
            prior = _latest_binding_by_account.get(account)
            if prior is not None:
                prior_ts, prior_fp = prior
                current_ts = str(treasury_observation.observed_at_utc or "")
                if current_ts < prior_ts and fp != prior_fp:
                    reasons.append("OLD_REPLAY_AFTER_NEWER_STATE_FAIL_CLOSED")
                    fail_closed = True
                    numeric_bound = False
                    base_fact = None
                elif fp in _seen_evidence_fingerprints and fp == prior_fp:
                    reasons.append("DUPLICATE_EVIDENCE_NO_ADDITIONAL_CAPITAL_EFFECT")
                    cached = _last_base_fact_by_fingerprint.get(fp)
                    if cached is None:
                        fail_closed = True
                        numeric_bound = False
                        base_fact = None
                    else:
                        base_fact = cached
                        numeric_bound = True
                        fail_closed = False
                else:
                    _seen_evidence_fingerprints.add(fp)
                    _latest_binding_by_account[account] = (
                        str(treasury_observation.observed_at_utc or ""),
                        fp,
                    )
                    base_fact = _observation_to_base_fact_v1(typed)
                    _last_base_fact_by_fingerprint[fp] = base_fact
                    numeric_bound = True
                    fail_closed = False
                    reasons.append("NUMERIC_BASE_BOUND_FROM_TYPED_OBSERVATION")
            else:
                _seen_evidence_fingerprints.add(fp)
                _latest_binding_by_account[account] = (
                    str(treasury_observation.observed_at_utc or ""),
                    fp,
                )
                base_fact = _observation_to_base_fact_v1(typed)
                _last_base_fact_by_fingerprint[fp] = base_fact
                numeric_bound = True
                fail_closed = False
                reasons.append("NUMERIC_BASE_BOUND_FROM_TYPED_OBSERVATION")

    if capital_admission_evidence.risk_admissible is True:
        raise CurrentProductiveAvailableForSizingBaseBindingError(
            "TREASURY_EVIDENCE_RISK_ADMISSIBLE_MINT"
        )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=capital_admission_evidence,
        claim=step_29p_claim,
    )
    if numeric_bound is True and base_fact is not None and step_29p_claim is None:
        producer_out = produce_current_productive_available_for_sizing_v1(
            base=base_fact,
            u04=None,
            p01=None,
            eligibility=None,
        )
        assert producer_out.produced == "false"
        _ = bind_step_29p_typed_equity_from_producer_v1(
            output=producer_out,
            fresh_pretrade_get_status="UNKNOWN",
            live_account_bound_status="UNKNOWN",
            expected_instrument_id=str(treasury_observation.instrument_id or ""),
            observed_instrument_id=str(treasury_observation.instrument_id or ""),
            fresh_evidence_fetched=False,
            fresh_evidence_validated=False,
        )

    risk_admissible = admissibility.risk_admissible is True and numeric_bound is True
    sizing_increase = risk_admissible is True
    if not sizing_increase:
        reasons.append("NO_SIZING_INCREASE_WITHOUT_STEP_29P_ADMIT_AND_BOUND_BASE")
    block_or_decrease = fail_closed or not sizing_increase

    digest = _digest(
        {
            "join_seam_id": JOIN_SEAM_ID,
            "evidence_id": str(treasury_observation.evidence_id or ""),
            "evidence_fingerprint": str(treasury_observation.evidence_fingerprint or ""),
            "numeric_bound": str(numeric_bound),
            "value_raw": str(treasury_observation.venue_balance_raw or ""),
        }
    )

    if risk_admissible:
        authority_owner = CURRENT_RISK_ADMISSIBILITY_OWNER
    elif numeric_bound:
        authority_owner = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1"
    else:
        authority_owner = "ops.treasury_phase_2_read_only_reconciliation_v1"

    return CurrentProductiveAvailableForSizingBaseBindingV1(
        base_binding_implemented=True,
        base_slot_id=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
        numeric_base_bound=numeric_bound,
        base_fact=base_fact,
        observation_schema_class=OBSERVATION_SCHEMA_CLASS,
        exact_allowed_numeric_source=EXACT_ALLOWED_NUMERIC_SOURCE,
        source_owner=SOURCE_OWNER,
        c08_base_candidate_required=True,
        c08_base_candidate_present=c08_binding.base_candidate_created is True,
        risk_admissible=risk_admissible,
        sizing_increase=sizing_increase,
        block_or_decrease=block_or_decrease,
        fail_closed=fail_closed,
        treasury_reconciliation_status=recon_status,
        usdc_row_status=row_status,
        reason_codes=tuple(dict.fromkeys((*reasons, JOIN_SEAM_ID))),
        authority_owner=authority_owner,
        join_seam_id=JOIN_SEAM_ID,
        step_29p_authority=STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
        productive_host_code_reachable=host_evaluation.productive_host_reachable is True,
        provenance_digest=digest,
        treasury_risk_admissible_mint=False,
        treasury_available_for_sizing_mint=False,
    )


__all__ = [
    "BASE_BINDING_AUTHORIZED",
    "BASE_BINDING_IMPLEMENTED",
    "CurrentProductiveAvailableForSizingBaseBindingError",
    "CurrentProductiveAvailableForSizingBaseBindingV1",
    "EXACT_ALLOWED_NUMERIC_SOURCE",
    "OWNER_GO",
    "SOURCE_OWNER",
    "WP_ID",
    "bind_current_productive_available_for_sizing_base_from_treasury_host_v1",
    "clear_current_productive_base_binding_state_v1",
]
