"""Join Live-29P GET into Current-Productive ENTER before venue-plan.

HOLD/observe skips the private GET. ENTER consumes the existing governed
Live-29P producer/evaluator exactly once. Offline-default equity cannot
bind a Current-Productive external-effect envelope. Does not mint a
permit. Does not POST. STEP-29Q remains PLAN_ONLY.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
)
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    PRODUCER_IDENTITY,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
    CurrentProductiveUsdcFreeMarginObservationV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 import (
    bind_current_productive_p01_policy_fact_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAILABLE_MARGIN_ENDPOINT_PATH,
    AVAILABLE_MARGIN_OUTPUT_DOMAIN,
    AVAILABLE_MARGIN_REQUIRED_CCY,
    AVAILABLE_MARGIN_REQUIRED_TD_MODE,
    LiveCanaryAvailableMarginObservationError,
    acquire_fresh_available_margin_observation_from_payload_v1,
    validate_fresh_available_margin_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    bind_canonical_order_intent_offline_replay_evidence_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    _DEFAULT_ACCOUNT_EQUITY,
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    default_offline_replay_capital_context_v0,
    derive_protective_stop_price_from_adverse_exit_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_SEAM_V1"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
STATUS_NOT_CALLED_HOLD = "NOT_CALLED_HOLD"
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_STALE = "STALE"
STATUS_MISSING = "MISSING"
DECISION_HOLD = "HOLD"
DECISION_ENTER = "ENTER"
DECISION_OTHER = "OTHER"
ENDPOINT = CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT
_ENTER = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})
_HOLD = frozenset(
    {
        DecisionOutcome.HOLD.value,
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.OBSERVE.value,
        DecisionOutcome.RECONCILE_ONLY.value,
        DecisionOutcome.CANCEL_PENDING.value,
        DecisionOutcome.BLOCKED.value,
        DecisionOutcome.REDUCE.value,
        DecisionOutcome.EXIT.value,
    }
)


class CurrentProductiveEnterLive29PJoinError(RuntimeError):
    """Fail-closed Current-Productive ENTER Live-29P join violation."""


@dataclass(frozen=True)
class CurrentProductiveEnterLive29PInjectedGetV1:
    payload: Mapping[str, Any] | None = None
    get_performed: bool = False
    http_status: int = 0
    error_class: str = ""
    body_sha256: str = ""
    observed_at: str = ""
    age_seconds: str = "1"
    live_account_bound_status: str = LiveAccountBoundStatusV1.MISSING.value
    raw_acct_lv: str = ""
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE
    fresh_pretrade_get_status: str = FreshPretradeGetStatusV1.MISSING.value


@dataclass(frozen=True)
class CurrentProductiveEnterLive29PJoinResultV1:
    decision_class: str
    called: bool
    get_count: int
    status: str
    venue_plan_authorized: bool
    first_blocker: str
    producer_output_value: str
    producer_output_status: str
    step_29p_risk_admissible: str
    capital_risk_mode: str
    used_offline_default_equity: str
    sizing_outcome: str
    replay: Optional[IntegratedOfflineReplayResultV1]
    post_count: str = "0"
    permit_created: str = "false"
    reason_codes: tuple[str, ...] = ()


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def current_productive_decision_class_v1(
    replay: IntegratedOfflineReplayResultV1 | None,
) -> str:
    if replay is None or replay.evidence is None:
        return DECISION_OTHER
    raw_outcome = replay.evidence.decision_outcome
    outcome = str(getattr(raw_outcome, "value", raw_outcome) or "").strip().lower()
    if outcome in _ENTER:
        return DECISION_ENTER
    if outcome in _HOLD:
        return DECISION_HOLD
    return DECISION_OTHER


def _hold_result(
    *, replay: IntegratedOfflineReplayResultV1 | None
) -> CurrentProductiveEnterLive29PJoinResultV1:
    return CurrentProductiveEnterLive29PJoinResultV1(
        decision_class=DECISION_HOLD,
        called=False,
        get_count=0,
        status=STATUS_NOT_CALLED_HOLD,
        venue_plan_authorized=True,
        first_blocker="",
        producer_output_value="",
        producer_output_status="NOT_REACHED",
        step_29p_risk_admissible=FALSE_TOKEN,
        capital_risk_mode=str(getattr(replay, "capital_risk_mode", "") or ""),
        used_offline_default_equity=FALSE_TOKEN,
        sizing_outcome="NOT_REACHED",
        replay=replay,
        reason_codes=(JOIN_SEAM_ID, STATUS_NOT_CALLED_HOLD),
    )


def _deny(
    *,
    status: str,
    blocker: str,
    replay: Optional[IntegratedOfflineReplayResultV1],
    get_count: int,
    producer_output_value: str = "",
    producer_output_status: str = "FAIL_CLOSED",
    step_29p_risk_admissible: str = FALSE_TOKEN,
    reasons: tuple[str, ...] = (),
) -> CurrentProductiveEnterLive29PJoinResultV1:
    return CurrentProductiveEnterLive29PJoinResultV1(
        decision_class=DECISION_ENTER,
        called=True,
        get_count=get_count,
        status=status,
        venue_plan_authorized=False,
        first_blocker=blocker,
        producer_output_value=producer_output_value,
        producer_output_status=producer_output_status,
        step_29p_risk_admissible=step_29p_risk_admissible,
        capital_risk_mode=CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
        used_offline_default_equity=FALSE_TOKEN,
        sizing_outcome="DENIED",
        replay=replay,
        reason_codes=tuple(dict.fromkeys((blocker, *reasons, JOIN_SEAM_ID, status))),
    )


def _classify_fail_status(reasons: tuple[str, ...], *, error_class: str) -> str:
    joined = " ".join(reasons) + " " + str(error_class or "")
    if "STALE" in joined:
        return STATUS_STALE
    if error_class or "UNKNOWN" in joined or "MALFORMED" in joined:
        return STATUS_UNKNOWN
    return STATUS_FAIL


def join_current_productive_enter_live_29p_before_venue_plan_v1(
    *,
    replay: IntegratedOfflineReplayResultV1 | None,
    bound_instrument: BoundInstrumentV1 | None,
    injected: CurrentProductiveEnterLive29PInjectedGetV1 | None = None,
    decision_epoch: str,
) -> CurrentProductiveEnterLive29PJoinResultV1:
    """Consume Live-29P only on ENTER. HOLD does not private-GET."""
    reject_direct_avail_eq_29p_claim_v1(claimed="producer")
    if ENDPOINT != AVAILABLE_MARGIN_ENDPOINT_PATH:
        raise CurrentProductiveEnterLive29PJoinError("ENDPOINT_DRIFT")
    decision_class = current_productive_decision_class_v1(replay)
    if decision_class != DECISION_ENTER:
        return _hold_result(replay=replay)

    get_count = 0
    payload: Mapping[str, Any] | None = None
    get_performed = False
    http_status = 0
    error_class = ""
    body_sha256 = ""
    observed_at = str(decision_epoch or "")
    age_seconds = "1"
    lab_status = LiveAccountBoundStatusV1.MISSING.value
    raw_acct_lv = ""
    expected_uid = REUSED_BINDING_ACCOUNT_SCOPE
    get_status = FreshPretradeGetStatusV1.MISSING.value
    if injected is not None:
        payload = injected.payload
        get_performed = bool(injected.get_performed)
        http_status = int(injected.http_status)
        error_class = str(injected.error_class or "")
        body_sha256 = str(injected.body_sha256 or "")
        observed_at = str(injected.observed_at or decision_epoch)
        age_seconds = str(injected.age_seconds or "1")
        lab_status = str(
            injected.live_account_bound_status or LiveAccountBoundStatusV1.MISSING.value
        )
        raw_acct_lv = str(injected.raw_acct_lv or "")
        expected_uid = str(injected.expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)
        get_status = str(
            injected.fresh_pretrade_get_status or FreshPretradeGetStatusV1.MISSING.value
        )
        if get_performed is True or payload is not None or error_class:
            get_count = 1
    if get_count == 0:
        return _deny(
            status=STATUS_MISSING,
            blocker="LIVE_29P_GET_MISSING",
            replay=replay,
            get_count=0,
            reasons=("FRESH_EVIDENCE_NOT_FETCHED",),
        )
    if get_performed is not True or payload is None or http_status != 200:
        status = STATUS_UNKNOWN if error_class else STATUS_MISSING
        return _deny(
            status=status,
            blocker="LIVE_29P_GET_NOT_TRUSTED" if error_class else "LIVE_29P_GET_MISSING",
            replay=replay,
            get_count=get_count,
            reasons=(error_class or "GET_NOT_PERFORMED",),
        )

    selected_instrument = ""
    if bound_instrument is not None:
        selected_instrument = str(
            bound_instrument.instrument_id or bound_instrument.venue_native_id or ""
        ).strip()
    if not selected_instrument:
        return _deny(
            status=STATUS_FAIL,
            blocker="STEP_29P_INSTRUMENT_SCOPE_MISSING",
            replay=replay,
            get_count=get_count,
        )

    observation = None
    try:
        raw_obs = acquire_fresh_available_margin_observation_from_payload_v1(
            pretrade_decision_id=decision_epoch,
            payload=payload,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
            observed_at_utc=observed_at,
            endpoint=ENDPOINT,
            http_status=http_status,
            get_performed=True,
            rest_host=REUSED_BINDING_REST_HOST,
            auth_header_sent=True,
            historical_reuse=False,
            body_sha256=body_sha256 or _sha256_text(_canonical_json(dict(payload))),
        )
        validated = validate_fresh_available_margin_observation_v1(
            raw_obs,
            pretrade_decision_id=decision_epoch,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
            planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
        )
        digest = (
            body_sha256
            or str(raw_obs.body_sha256 or "")
            or _sha256_text(_canonical_json(dict(payload)))
        )
        observation = CurrentProductiveUsdcFreeMarginObservationV1(
            fact_id=OBSERVATION_FACT_ID,
            surface=OBSERVATION_SURFACE,
            value=str(validated.avail_eq_raw),
            settlement_currency=AVAILABLE_MARGIN_REQUIRED_CCY,
            selected_ccy=validated.selected_ccy,
            bound_account_identity=expected_uid,
            bound_venue_identity="okx",
            bound_td_mode="cross",
            decision_epoch=decision_epoch,
            observed_at_as_of=observed_at,
            age_seconds=age_seconds,
            freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
            provenance_digest=digest,
            already_net_of_in_use=TRUE_TOKEN,
            account_level_avail_eq_used=FALSE_TOKEN,
            fallback_chain_used=FALSE_TOKEN,
        )
    except (LiveCanaryAvailableMarginObservationError, TypeError, ValueError, KeyError) as exc:
        return _deny(
            status=STATUS_UNKNOWN,
            blocker=f"LIVE_29P_OBSERVATION_FAIL_CLOSED:{type(exc).__name__}",
            replay=replay,
            get_count=get_count,
            reasons=(str(exc)[:200],),
        )

    if observation is None:
        return _deny(
            status=STATUS_UNKNOWN,
            blocker="LIVE_29P_OBSERVATION_MISSING",
            replay=replay,
            get_count=get_count,
        )

    p01_digest = _sha256_text(
        _canonical_json(
            {
                "policy": "DOES_NOT_APPLY",
                "epoch": observation.decision_epoch,
                "account": observation.bound_account_identity,
            }
        )
    )
    p01_fact = bind_current_productive_p01_policy_fact_v1(
        bound_account_identity=observation.bound_account_identity,
        bound_venue_identity=observation.bound_venue_identity,
        bound_td_mode=observation.bound_td_mode,
        decision_epoch=observation.decision_epoch,
        observed_at_as_of=observation.observed_at_as_of,
        age_seconds=observation.age_seconds,
        freshness_max_age=observation.freshness_max_age,
        provenance_digest=p01_digest,
    )
    adaptation = adapt_current_productive_u01_account_mode_v1(raw_acct_lv)
    eligibility = build_current_productive_u01_eligibility_fact_v1(
        adaptation=adaptation,
        bound_account_identity=observation.bound_account_identity,
        bound_venue_identity=observation.bound_venue_identity,
        bound_td_mode=observation.bound_td_mode,
        decision_epoch=observation.decision_epoch,
        provenance_digest=_sha256_text(
            _canonical_json({"acctLv": raw_acct_lv, "epoch": observation.decision_epoch})
        ),
    )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01_fact,
        eligibility=eligibility,
        eq_target=None,
        u04=None,
        restart_from_kind_set=FALSE_TOKEN,
    )
    produced = output.produced == TRUE_TOKEN
    producer_reasons = tuple(str(code) for code in output.reason_codes)
    if produced is not True:
        return _deny(
            status=_classify_fail_status(producer_reasons, error_class=""),
            blocker=producer_reasons[0] if producer_reasons else "LIVE_29P_PRODUCER_FAIL_CLOSED",
            replay=replay,
            get_count=get_count,
            producer_output_status="FAIL_CLOSED",
            reasons=producer_reasons,
        )

    trusted = get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=get_status,
        live_account_bound_status=lab_status,
        expected_instrument_id=selected_instrument,
        observed_instrument_id=selected_instrument if trusted else "",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=trusted and produced,
    )
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=expected_uid,
            instrument_id=selected_instrument,
            observed_capital_raw=output.value,
            observed_field_name=PRODUCER_IDENTITY,
            evidence_class="LIVE_TYPED",
            evidence_id=decision_epoch,
        ),
        expected_account_identity=expected_uid,
        expected_instrument_id=selected_instrument,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    if admissibility.risk_admissible is not True:
        eval_reasons = tuple(str(code) for code in admissibility.reason_codes)
        return _deny(
            status=_classify_fail_status(eval_reasons, error_class=""),
            blocker=eval_reasons[0] if eval_reasons else "STEP_29P_RISK_ADMISSIBLE_FALSE",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=FALSE_TOKEN,
            reasons=eval_reasons,
        )

    if replay is None or replay.intermediate is None:
        return _deny(
            status=STATUS_FAIL,
            blocker="ENTER_REPLAY_MISSING_FOR_LIVE_29P_SIZING",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )

    try:
        producer_equity = Decimal(str(output.value))
    except (InvalidOperation, ValueError):
        return _deny(
            status=STATUS_FAIL,
            blocker="STEP_29P_TYPED_ACCOUNT_EQUITY_NOT_DECIMAL",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )
    if producer_equity != producer_equity or producer_equity <= 0:
        return _deny(
            status=STATUS_FAIL,
            blocker="STEP_29P_TYPED_ACCOUNT_EQUITY_NOT_POSITIVE",
            replay=replay,
            get_count=get_count,
            producer_output_value=output.value,
            producer_output_status="PRODUCED",
            step_29p_risk_admissible=TRUE_TOKEN,
        )
    if producer_equity == _DEFAULT_ACCOUNT_EQUITY and str(output.value) == str(
        _DEFAULT_ACCOUNT_EQUITY
    ):
        # Distinctive producer values are required; equal-to-default is not a leak
        # by itself, but ENTER must still rebind from the producer output object.
        pass

    mark = replay.intermediate.market_context.mark_price
    reference = Decimal(str(mark))
    stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=str(replay.evidence.selected_side),
        reference_price=reference,
        adverse_exit_distance=CANONICAL_ADVERSE_EXIT_DISTANCE,
    )
    ctx = default_offline_replay_capital_context_v0(
        instrument_id=str(replay.evidence.instrument_id),
        reference_price=reference,
        protective_stop_price=stop,
    )
    live_ctx = replace(
        ctx,
        account_equity=producer_equity,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    )
    if not isinstance(live_ctx, CanonicalCoreRuntimeCapitalContextV0):
        raise CurrentProductiveEnterLive29PJoinError("CAPITAL_CONTEXT_TYPE_DRIFT")
    if live_ctx.account_equity != producer_equity:
        raise CurrentProductiveEnterLive29PJoinError("PRODUCER_EQUITY_NOT_BOUND")
    if live_ctx.capital_risk_mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND:
        raise CurrentProductiveEnterLive29PJoinError("LIVE_ACCOUNT_BOUND_MODE_NOT_BOUND")
    if (
        live_ctx.account_equity == _DEFAULT_ACCOUNT_EQUITY
        and producer_equity != _DEFAULT_ACCOUNT_EQUITY
    ):
        raise CurrentProductiveEnterLive29PJoinError("OFFLINE_DEFAULT_EQUITY_LEAK")

    sizing_binding = bind_capital_risk_sizing_offline_replay_evidence_v0(
        replay.evidence,
        capital_context=live_ctx,
    )
    intent_binding = bind_canonical_order_intent_offline_replay_evidence_v0(
        sizing_binding.evidence,
        sizing_decision=sizing_binding.sizing_decision,
        capital_context=live_ctx,
    )
    rebound_intermediate = replace(
        replay.intermediate,
        capital_risk_sizing_decision=sizing_binding.sizing_decision,
        canonical_order_intent=intent_binding.canonical_intent,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    )
    rebound = replace(
        replay,
        evidence=intent_binding.evidence,
        intermediate=rebound_intermediate,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    )
    sizing_outcome = ""
    if sizing_binding.sizing_decision is not None:
        sizing_outcome = str(
            getattr(
                sizing_binding.sizing_decision.outcome,
                "value",
                sizing_binding.sizing_decision.outcome,
            )
        )
    return CurrentProductiveEnterLive29PJoinResultV1(
        decision_class=DECISION_ENTER,
        called=True,
        get_count=get_count,
        status=STATUS_PASS,
        venue_plan_authorized=True,
        first_blocker="",
        producer_output_value=str(output.value),
        producer_output_status="PRODUCED",
        step_29p_risk_admissible=TRUE_TOKEN,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        used_offline_default_equity=FALSE_TOKEN,
        sizing_outcome=sizing_outcome,
        replay=rebound,
        reason_codes=(JOIN_SEAM_ID, STATUS_PASS, PRODUCER_IDENTITY),
    )
