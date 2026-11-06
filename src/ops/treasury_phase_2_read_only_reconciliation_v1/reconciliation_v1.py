"""Pure read-only Treasury reconciliation evaluator. No network."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from src.ops.treasury_phase_2_read_only_reconciliation_v1.constants_v1 import (
    CAPITAL_ADMISSION_AUTHORITY,
    JOIN_SEAM_ID,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.errors_v1 import (
    TreasuryPhase2ReconciliationError,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
    TreasuryReconciliationClassV1,
    TreasuryReconciliationEvaluationV1,
    TreasuryVenueObservationV1,
)

_IDEMPOTENCY_CACHE: dict[str, TreasuryReconciliationEvaluationV1] = {}


def _parse_amount(raw: str) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "":
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    return value


def _validate_observation(observation: TreasuryVenueObservationV1) -> None:
    if not str(observation.evidence_id or "").strip():
        raise TreasuryPhase2ReconciliationError("EVIDENCE_ID_REQUIRED")
    if not str(observation.evidence_fingerprint or "").strip():
        raise TreasuryPhase2ReconciliationError("EVIDENCE_FINGERPRINT_REQUIRED")
    if not str(observation.account_identity or "").strip():
        raise TreasuryPhase2ReconciliationError("ACCOUNT_IDENTITY_REQUIRED")
    if not str(observation.instrument_id or "").strip():
        raise TreasuryPhase2ReconciliationError("INSTRUMENT_ID_REQUIRED")


def evaluate_treasury_read_only_reconciliation_v1(
    observation: TreasuryVenueObservationV1,
    *,
    use_idempotency_cache: bool = True,
) -> TreasuryReconciliationEvaluationV1:
    _validate_observation(observation)
    fp = str(observation.evidence_fingerprint)
    if use_idempotency_cache and fp in _IDEMPOTENCY_CACHE:
        cached = _IDEMPOTENCY_CACHE[fp]
        if cached.evidence_id != observation.evidence_id:
            return _result(
                TreasuryReconciliationClassV1.AMBIGUOUS,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=("DUPLICATE_FINGERPRINT_CONFLICTING_EVIDENCE_ID",),
                observation=observation,
            )
        return cached

    reasons: list[str] = []
    balance_fresh = str(observation.balance_freshness or TreasuryFreshnessSignalV1.UNKNOWN.value)
    history = str(
        observation.deposit_history_freshness or TreasuryDepositHistorySignalV1.UNKNOWN.value
    )
    internal = str(
        observation.internal_transfer_signal or TreasuryInternalTransferSignalV1.UNKNOWN.value
    )
    depletion = str(
        observation.external_depletion_signal or TreasuryExternalDepletionSignalV1.UNKNOWN.value
    )

    venue = _parse_amount(observation.venue_balance_raw)
    prior = _parse_amount(observation.prior_reconciled_capital_raw)
    cached = _parse_amount(observation.cached_trading_capital_raw)

    if venue is None and str(observation.venue_balance_raw or "").strip() != "":
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.UNKNOWN,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=("VENUE_BALANCE_MALFORMED",),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    if balance_fresh == TreasuryFreshnessSignalV1.UNKNOWN.value:
        reasons.append("BALANCE_FRESHNESS_UNKNOWN")
    if history == TreasuryDepositHistorySignalV1.UNKNOWN.value:
        reasons.append("DEPOSIT_HISTORY_FRESHNESS_UNKNOWN")
    if internal == TreasuryInternalTransferSignalV1.UNKNOWN.value:
        reasons.append("INTERNAL_TRANSFER_SIGNAL_UNKNOWN")
    if depletion == TreasuryExternalDepletionSignalV1.UNKNOWN.value:
        reasons.append("EXTERNAL_DEPLETION_SIGNAL_UNKNOWN")

    if internal == TreasuryInternalTransferSignalV1.DEBIT_BEFORE_CREDIT_UNSETTLED.value:
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.AMBIGUOUS,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=tuple(dict.fromkeys((*reasons, "INTERNAL_TRANSFER_DEBIT_BEFORE_CREDIT"))),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    if (
        balance_fresh == TreasuryFreshnessSignalV1.FRESH.value
        and history == TreasuryDepositHistorySignalV1.STALE.value
    ):
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.AMBIGUOUS,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=tuple(dict.fromkeys((*reasons, "FRESH_BALANCE_STALE_DEPOSIT_HISTORY"))),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    if balance_fresh == TreasuryFreshnessSignalV1.STALE.value:
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.STALE,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=tuple(dict.fromkeys((*reasons, "BALANCE_OBSERVATION_STALE"))),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    if depletion == TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value:
        if cached is not None and venue is not None and cached > venue:
            return _finalize(
                _result(
                    TreasuryReconciliationClassV1.STALE,
                    capital_increase_authority=False,
                    fail_closed=True,
                    reasons=tuple(
                        dict.fromkeys(
                            (
                                *reasons,
                                "CREDIBLE_DEPLETION_CACHED_TRADING_STALE",
                            )
                        )
                    ),
                    observation=observation,
                ),
                fp,
                use_idempotency_cache,
            )

    increase_detected = venue is not None and prior is not None and venue > prior and venue != prior
    if increase_detected and not observation.deposit_history_confirms_increase:
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.OBSERVED,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=tuple(
                    dict.fromkeys(
                        (
                            *reasons,
                            "OBSERVED_INCREASE_DEPOSIT_HISTORY_NOT_RECONCILED",
                        )
                    )
                ),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    if reasons and any(code.endswith("_UNKNOWN") for code in reasons):
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.UNKNOWN,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=tuple(dict.fromkeys(reasons)),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    history_ok = history in {
        TreasuryDepositHistorySignalV1.CONFIRMED.value,
        TreasuryDepositHistorySignalV1.MISSING.value,
    }
    if increase_detected and history == TreasuryDepositHistorySignalV1.UNCONFIRMED.value:
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.OBSERVED,
                capital_increase_authority=False,
                fail_closed=True,
                reasons=("OBSERVED_INCREASE_DEPOSIT_HISTORY_UNCONFIRMED",),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    if (
        balance_fresh == TreasuryFreshnessSignalV1.FRESH.value
        and internal == TreasuryInternalTransferSignalV1.CLEAR.value
        and (not increase_detected or observation.deposit_history_confirms_increase)
        and history_ok
        and venue is not None
    ):
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.RECONCILED,
                capital_increase_authority=increase_detected
                and observation.deposit_history_confirms_increase,
                fail_closed=False,
                reasons=tuple(dict.fromkeys((*reasons, "TREASURY_READ_ONLY_RECONCILED"))),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    if venue is not None and not increase_detected:
        return _finalize(
            _result(
                TreasuryReconciliationClassV1.OBSERVED,
                capital_increase_authority=False,
                fail_closed=False,
                reasons=tuple(dict.fromkeys((*reasons, "TREASURY_OBSERVED_NO_INCREASE"))),
                observation=observation,
            ),
            fp,
            use_idempotency_cache,
        )

    return _finalize(
        _result(
            TreasuryReconciliationClassV1.AMBIGUOUS,
            capital_increase_authority=False,
            fail_closed=True,
            reasons=tuple(dict.fromkeys((*reasons, "TREASURY_RECONCILIATION_AMBIGUOUS"))),
            observation=observation,
        ),
        fp,
        use_idempotency_cache,
    )


def clear_treasury_reconciliation_idempotency_cache_v1() -> None:
    _IDEMPOTENCY_CACHE.clear()


def _result(
    reconciliation_class: TreasuryReconciliationClassV1,
    *,
    capital_increase_authority: bool,
    fail_closed: bool,
    reasons: tuple[str, ...],
    observation: TreasuryVenueObservationV1,
) -> TreasuryReconciliationEvaluationV1:
    if (
        capital_increase_authority
        and reconciliation_class != TreasuryReconciliationClassV1.RECONCILED
    ):
        raise TreasuryPhase2ReconciliationError("INCREASE_AUTHORITY_REQUIRES_RECONCILED")
    return TreasuryReconciliationEvaluationV1(
        reconciliation_class=reconciliation_class.value,
        capital_increase_authority=capital_increase_authority,
        fail_closed=fail_closed,
        reason_codes=tuple(dict.fromkeys(reasons)),
        evidence_id=str(observation.evidence_id),
        evidence_fingerprint=str(observation.evidence_fingerprint),
        observed_at_utc=str(observation.observed_at_utc),
        join_seam_id=JOIN_SEAM_ID,
        authority=CAPITAL_ADMISSION_AUTHORITY,
    )


def _finalize(
    result: TreasuryReconciliationEvaluationV1,
    fingerprint: str,
    use_cache: bool,
) -> TreasuryReconciliationEvaluationV1:
    if use_cache:
        _IDEMPOTENCY_CACHE[fingerprint] = result
    return result
