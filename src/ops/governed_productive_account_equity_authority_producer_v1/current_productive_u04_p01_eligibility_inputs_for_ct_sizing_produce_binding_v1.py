"""Bind canonical U04/P01/eligibility inputs into CT AVAILABLE_FOR_SIZING produce.

Reuses standing P01 policy, U01 eligibility adapter, and existing producer algebra.
Does not mint BASE, change 29P policy, or authorize external effect.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Mapping

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_ALGEBRA,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    P01_APPLIES,
    P01_DOES_NOT_APPLY,
    P01_FACT_ID,
    P01_UNKNOWN,
    REQUIRED_TD_MODE,
    TRUE_TOKEN,
    U04_FACT_ID,
    CurrentProductiveAvailableForSizingBaseFactV1,
    CurrentProductiveP01ReductionFactV1,
    CurrentProductiveU04ReservationFactV1,
    produce_current_productive_available_for_sizing_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 import (
    SOURCE_CLASS as P01_POLICY_SOURCE_CLASS,
    evaluate_current_productive_p01_policy_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1 import (
    CurrentProductiveU04P01EligibilityHostInputsV1,
    CurrentProductiveU04P01EligibilityInputsBindingError,
    CurrentProductiveU04P01EligibilityInputsBindingV1,
    CurrentProductiveU04ReservationTypedEvidenceV1,
)

SCHEMA_CLASS = "CURRENT_PRODUCTIVE_U04_P01_ELIGIBILITY_INPUTS_FOR_CT_SIZING_PRODUCE_BINDING_V1"
CONTRACT_VERSION = "v1"
WP_ID = "CURRENT_PRODUCTIVE_U04_P01_ELIGIBILITY_INPUTS_FOR_CT_SIZING_PRODUCE_BINDING_V1"
OWNER_GO = f"OWNER_GO_{WP_ID}"
JOIN_SEAM_ID = WP_ID

U04_SOURCE_CLASS = "CURRENT_PRODUCTIVE_PENDING_ORDER_RESERVATION"
P01_APPLICABILITY_SOURCE = "CURRENT_PRODUCTIVE_P01_POLICY_DOES_NOT_APPLY_V1"
ELIGIBILITY_SOURCE = "CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_ADAPTER_V1"
AVAILABLE_FOR_SIZING_FORMULA = "AVAILABLE_FOR_SIZING=BASE-U04-P01_IF_APPLIES"

PRIOR_BLOCKER = "CURRENT_PRODUCTIVE_CT_SIZING_PRODUCE_BLOCKED_U04_P01_ELIGIBILITY_INPUTS_UNBOUND"
EARLIEST_NEW_REAL_BLOCKER_AFTER_WP = (
    "CURRENT_PRODUCTIVE_CT_SIZING_PRODUCE_ELIGIBILITY_INPUTS_BOUND;"
    "NEXT_REMAINDER=TRUSTED_29P_PRETRADE_AND_EXTERNAL_EFFECT_OWNER_GOS"
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _digest(payload: Mapping[str, str]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _assert_envelope() -> None:
    from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
        AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
        RISK_ADMISSIBLE_MINT_AUTHORIZED,
        STEP_29P_MINT_AUTHORIZED,
    )

    if RISK_ADMISSIBLE_MINT_AUTHORIZED or STEP_29P_MINT_AUTHORIZED:
        raise CurrentProductiveU04P01EligibilityInputsBindingError("DOWNSTREAM_MINT_FORBIDDEN")
    if AVAILABLE_FOR_SIZING_MINT_AUTHORIZED:
        raise CurrentProductiveU04P01EligibilityInputsBindingError(
            "AVAILABLE_FOR_SIZING_MINT_FORBIDDEN"
        )


def _parse_non_negative(value: str) -> Decimal | None:
    raw = str(value or "").strip()
    if raw == "":
        return None
    try:
        parsed = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or parsed < 0:
        return None
    return parsed


def bind_current_productive_u04_reservation_fact_from_typed_evidence_v1(
    *,
    base: CurrentProductiveAvailableForSizingBaseFactV1,
    evidence: CurrentProductiveU04ReservationTypedEvidenceV1,
    age_seconds: str,
    freshness_max_age: str,
) -> CurrentProductiveU04ReservationFactV1:
    witness_kind = str(evidence.witness_kind or "").strip()
    witness_digest = str(evidence.witness_digest or "").strip().lower()
    if witness_kind == "":
        raise CurrentProductiveU04P01EligibilityInputsBindingError("U04_WITNESS_KIND_MISSING")
    if not _HEX64.match(witness_digest):
        raise CurrentProductiveU04P01EligibilityInputsBindingError("U04_WITNESS_DIGEST_INVALID")
    parsed = _parse_non_negative(evidence.reservation_value_raw)
    if parsed is None:
        raise CurrentProductiveU04P01EligibilityInputsBindingError("U04_VALUE_INVALID")
    empty_proven = str(evidence.empty_reservation_proven or "").strip().lower()
    if empty_proven not in {"true", "false"}:
        raise CurrentProductiveU04P01EligibilityInputsBindingError(
            "U04_EMPTY_RESERVATION_PROVEN_MALFORMED"
        )
    if parsed == 0 and empty_proven != TRUE_TOKEN:
        raise CurrentProductiveU04P01EligibilityInputsBindingError(
            "U04_ZERO_WITHOUT_EMPTY_RESERVATION_PROOF"
        )
    provenance = _digest(
        {
            "witness_kind": witness_kind,
            "witness_digest": witness_digest,
            "reservation_value_raw": str(evidence.reservation_value_raw),
            "empty_reservation_proven": empty_proven,
            "base_fact_id": base.fact_id,
            "decision_epoch": base.decision_epoch,
        }
    )
    return CurrentProductiveU04ReservationFactV1(
        fact_id=U04_FACT_ID,
        value=str(evidence.reservation_value_raw),
        settlement_currency=base.settlement_currency,
        bound_account_identity=base.bound_account_identity,
        bound_venue_identity=base.bound_venue_identity,
        bound_td_mode=base.bound_td_mode,
        decision_epoch=base.decision_epoch,
        observed_at_as_of=base.observed_at_as_of,
        age_seconds=age_seconds,
        freshness_max_age=freshness_max_age,
        provenance_digest=provenance,
        source_class=U04_SOURCE_CLASS,
        empty_reservation_proven=empty_proven,
    )


def bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
    *,
    base: CurrentProductiveAvailableForSizingBaseFactV1,
    age_seconds: str,
    freshness_max_age: str,
    applicability_state: str | None = None,
    value: str | None = None,
) -> CurrentProductiveP01ReductionFactV1:
    decision = evaluate_current_productive_p01_policy_v1()
    state = str(applicability_state or decision.decision_state or "").strip()
    if state == "":
        state = P01_UNKNOWN
    if state not in {P01_APPLIES, P01_DOES_NOT_APPLY, P01_UNKNOWN}:
        raise CurrentProductiveU04P01EligibilityInputsBindingError("P01_APPLICABILITY_INVALID")
    if applicability_state is None and state != P01_DOES_NOT_APPLY:
        raise CurrentProductiveU04P01EligibilityInputsBindingError(
            "P01_POLICY_MUST_BE_DOES_NOT_APPLY_FOR_STANDING_BIND"
        )
    p01_value = "" if value is None else str(value)
    if state == P01_DOES_NOT_APPLY and p01_value not in {"", "0"}:
        raise CurrentProductiveU04P01EligibilityInputsBindingError(
            "P01_DOES_NOT_APPLY_NONZERO_FORBIDDEN"
        )
    provenance = _digest(
        {
            "policy": P01_APPLICABILITY_SOURCE,
            "applicability_state": state,
            "decision_epoch": base.decision_epoch,
            "account": base.bound_account_identity,
        }
    )
    return CurrentProductiveP01ReductionFactV1(
        fact_id=P01_FACT_ID,
        applicability_state=state,
        value=p01_value,
        settlement_currency=base.settlement_currency,
        bound_account_identity=base.bound_account_identity,
        bound_venue_identity=base.bound_venue_identity,
        bound_td_mode=base.bound_td_mode,
        decision_epoch=base.decision_epoch,
        observed_at_as_of=base.observed_at_as_of,
        age_seconds=age_seconds,
        freshness_max_age=freshness_max_age,
        provenance_digest=provenance,
        source_class=P01_POLICY_SOURCE_CLASS,
    )


def bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
    *,
    base: CurrentProductiveAvailableForSizingBaseFactV1 | None,
    host_inputs: CurrentProductiveU04P01EligibilityHostInputsV1 | None,
    age_seconds: str = "1",
    freshness_max_age: str = "5",
) -> CurrentProductiveU04P01EligibilityInputsBindingV1:
    """Wire U04/P01/eligibility into produce when base and host inputs are present."""
    _assert_envelope()
    reasons: list[str] = []
    if base is None:
        reasons.append("BASE_FACT_MISSING")
        return _result(
            inputs_bound=False,
            fail_closed=True,
            reasons=tuple(reasons),
            base=None,
        )
    if host_inputs is None:
        reasons.append(PRIOR_BLOCKER)
        return _result(
            inputs_bound=False,
            fail_closed=True,
            reasons=tuple(reasons),
            base=base,
        )
    try:
        u04 = bind_current_productive_u04_reservation_fact_from_typed_evidence_v1(
            base=base,
            evidence=host_inputs.u04_evidence,
            age_seconds=age_seconds,
            freshness_max_age=freshness_max_age,
        )
        p01 = bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
            base=base,
            age_seconds=age_seconds,
            freshness_max_age=freshness_max_age,
        )
        adaptation = adapt_current_productive_u01_account_mode_v1(host_inputs.u01_raw_acct_lv)
        eligibility = build_current_productive_u01_eligibility_fact_v1(
            adaptation=adaptation,
            bound_account_identity=base.bound_account_identity,
            bound_venue_identity=base.bound_venue_identity,
            bound_td_mode=base.bound_td_mode,
            decision_epoch=base.decision_epoch,
            provenance_digest=_digest(
                {
                    "u01_raw": str(host_inputs.u01_raw_acct_lv),
                    "epoch": base.decision_epoch,
                }
            ),
        )
    except CurrentProductiveU04P01EligibilityInputsBindingError as exc:
        reasons.append(str(exc))
        return _result(
            inputs_bound=False,
            fail_closed=True,
            reasons=tuple(reasons),
            base=base,
        )
    if eligibility is None:
        reasons.append("ELIGIBILITY_FACT_MISSING")
        return _result(
            inputs_bound=False,
            fail_closed=True,
            reasons=tuple(reasons),
            base=base,
            u04=u04,
            p01=p01,
        )
    output = produce_current_productive_available_for_sizing_v1(
        base=base,
        u04=u04,
        p01=p01,
        eligibility=eligibility,
    )
    produced = output.produced == TRUE_TOKEN
    if not produced:
        reasons.extend(str(code) for code in output.reason_codes)
    return _result(
        inputs_bound=produced,
        fail_closed=not produced,
        reasons=tuple(dict.fromkeys(reasons)),
        base=base,
        u04=u04,
        p01=p01,
        eligibility=eligibility,
        output=output,
    )


def _result(
    *,
    inputs_bound: bool,
    fail_closed: bool,
    reasons: tuple[str, ...],
    base: CurrentProductiveAvailableForSizingBaseFactV1 | None,
    u04: CurrentProductiveU04ReservationFactV1 | None = None,
    p01: CurrentProductiveP01ReductionFactV1 | None = None,
    eligibility: object | None = None,
    output: object | None = None,
) -> CurrentProductiveU04P01EligibilityInputsBindingV1:
    if inputs_bound:
        seam_reasons = (*reasons, "U04_P01_ELIGIBILITY_INPUTS_BOUND", JOIN_SEAM_ID)
    else:
        seam_reasons = reasons if reasons else (PRIOR_BLOCKER,)
    return CurrentProductiveU04P01EligibilityInputsBindingV1(
        inputs_binding_implemented=True,
        inputs_bound=inputs_bound,
        u04_fact=u04,
        p01_fact=p01,
        eligibility_fact=eligibility,  # type: ignore[arg-type]
        producer_output=output,  # type: ignore[arg-type]
        base_fact=base,
        formula=AVAILABLE_FOR_SIZING_FORMULA,
        fail_closed=fail_closed,
        reason_codes=tuple(dict.fromkeys(seam_reasons)),
        join_seam_id=JOIN_SEAM_ID,
        u04_source_class=U04_SOURCE_CLASS,
        p01_source_class=P01_POLICY_SOURCE_CLASS,
        p01_applicability_source=P01_APPLICABILITY_SOURCE,
        eligibility_source=ELIGIBILITY_SOURCE,
        authority_graph_changed=False,
        fallback_numerics_present=False,
    )


__all__ = [
    "AVAILABLE_FOR_SIZING_FORMULA",
    "EARLIEST_NEW_REAL_BLOCKER_AFTER_WP",
    "JOIN_SEAM_ID",
    "OWNER_GO",
    "PRIOR_BLOCKER",
    "SCHEMA_CLASS",
    "WP_ID",
    "bind_current_productive_p01_fact_for_ct_sizing_produce_v1",
    "bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1",
    "bind_current_productive_u04_reservation_fact_from_typed_evidence_v1",
]
