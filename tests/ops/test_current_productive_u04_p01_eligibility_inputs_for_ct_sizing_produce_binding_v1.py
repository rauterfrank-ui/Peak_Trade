"""U04/P01/eligibility inputs binding for CT AVAILABLE_FOR_SIZING produce."""

from __future__ import annotations

import hashlib

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    P01_APPLIES,
    P01_DOES_NOT_APPLY,
    P01_UNKNOWN,
    CurrentProductiveAvailableForSizingBaseFactV1,
    produce_current_productive_available_for_sizing_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1 import (
    CurrentProductiveU04P01EligibilityHostInputsV1,
    CurrentProductiveU04ReservationTypedEvidenceV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1 import (
    AVAILABLE_FOR_SIZING_FORMULA,
    EARLIEST_NEW_REAL_BLOCKER_AFTER_WP,
    OWNER_GO,
    PRIOR_BLOCKER,
    bind_current_productive_p01_fact_for_ct_sizing_produce_v1,
    bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1,
    bind_current_productive_u04_reservation_fact_from_typed_evidence_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_PRESENT,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.join_v1 import (
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
    TreasuryVenueObservationV1,
)

_EPOCH = "2026-09-21T04:00:00Z"
_ACCOUNT = "acct-u04-p01-bind-001"
_INSTRUMENT = "BTC-USDT-SWAP"


def _base(**overrides: object) -> CurrentProductiveAvailableForSizingBaseFactV1:
    payload = {
        "fact_id": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
        "value": "100.00",
        "settlement_currency": "USDC",
        "bound_account_identity": _ACCOUNT,
        "bound_venue_identity": "okx",
        "bound_td_mode": "cross",
        "decision_epoch": _EPOCH,
        "observed_at_as_of": _EPOCH,
        "age_seconds": "1",
        "freshness_max_age": "5",
        "provenance_digest": "a" * 64,
        "source_class": "NON_FORBIDDEN_NON_EQ_NON_STOCK_USDC_CURRENT_PRODUCTIVE_OBSERVATION_V1",
        "already_net_of_u04": "false",
    }
    payload.update(overrides)
    return CurrentProductiveAvailableForSizingBaseFactV1(**payload)


def _witness(**overrides: object) -> CurrentProductiveU04ReservationTypedEvidenceV1:
    payload = {
        "reservation_value_raw": "0",
        "empty_reservation_proven": "true",
        "witness_kind": "TYPED_OFFLINE_EMPTY_RESERVATION_WITNESS_V1",
        "witness_digest": hashlib.sha256(b"empty-u04").hexdigest(),
    }
    payload.update(overrides)
    return CurrentProductiveU04ReservationTypedEvidenceV1(**payload)


def _host_inputs(**overrides: object) -> CurrentProductiveU04P01EligibilityHostInputsV1:
    payload = {
        "u01_raw_acct_lv": "2",
        "u04_evidence": _witness(),
    }
    payload.update(overrides)
    return CurrentProductiveU04P01EligibilityHostInputsV1(**payload)


def _reconciled_obs(**overrides: object) -> TreasuryVenueObservationV1:
    payload = {
        "evidence_id": "tevidence-u04-p01-a",
        "evidence_fingerprint": "fp-u04-p01-a",
        "observed_at_utc": _EPOCH,
        "account_identity": _ACCOUNT,
        "instrument_id": _INSTRUMENT,
        "venue_balance_raw": "100.00",
        "balance_freshness": TreasuryFreshnessSignalV1.FRESH.value,
        "deposit_history_freshness": TreasuryDepositHistorySignalV1.MISSING.value,
        "deposit_history_confirms_increase": False,
        "internal_transfer_signal": TreasuryInternalTransferSignalV1.CLEAR.value,
        "external_depletion_signal": TreasuryExternalDepletionSignalV1.NONE.value,
        "prior_reconciled_capital_raw": "100.00",
        "cached_trading_capital_raw": "100.00",
    }
    payload.update(overrides)
    return TreasuryVenueObservationV1(**payload)


def test_standing_owner_and_formula() -> None:
    assert OWNER_GO == (
        "OWNER_GO_CURRENT_PRODUCTIVE_U04_P01_ELIGIBILITY_INPUTS_FOR_CT_SIZING_PRODUCE_BINDING_V1"
    )
    assert AVAILABLE_FOR_SIZING_FORMULA == "AVAILABLE_FOR_SIZING=BASE-U04-P01_IF_APPLIES"
    assert PRIOR_BLOCKER.endswith("U04_P01_ELIGIBILITY_INPUTS_UNBOUND")
    assert "ELIGIBILITY_INPUTS_BOUND" in EARLIEST_NEW_REAL_BLOCKER_AFTER_WP


def test_valid_inputs_reach_produce_path() -> None:
    result = bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
        base=_base(),
        host_inputs=_host_inputs(),
    )
    assert result.inputs_bound is True
    assert result.fail_closed is False
    assert result.producer_output is not None
    assert result.producer_output.produced == "true"
    assert result.producer_output.value == "100.00"
    assert result.authority_graph_changed is False
    assert result.fallback_numerics_present is False


def test_p01_applies_reduces_output() -> None:
    base = _base()
    u04 = bind_current_productive_u04_reservation_fact_from_typed_evidence_v1(
        base=base,
        evidence=_witness(reservation_value_raw="10", empty_reservation_proven="false"),
        age_seconds="1",
        freshness_max_age="5",
    )
    p01 = bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
        base=base,
        age_seconds="1",
        freshness_max_age="5",
        applicability_state=P01_APPLIES,
        value="5.25",
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
        adapt_current_productive_u01_account_mode_v1,
        build_current_productive_u01_eligibility_fact_v1,
    )

    eligibility = build_current_productive_u01_eligibility_fact_v1(
        adaptation=adapt_current_productive_u01_account_mode_v1("2"),
        bound_account_identity=base.bound_account_identity,
        bound_venue_identity=base.bound_venue_identity,
        bound_td_mode=base.bound_td_mode,
        decision_epoch=base.decision_epoch,
        provenance_digest="d" * 64,
    )
    assert eligibility is not None
    out = produce_current_productive_available_for_sizing_v1(
        base=base,
        u04=u04,
        p01=p01,
        eligibility=eligibility,
    )
    assert out.produced == "true"
    assert out.value == "84.75"
    assert out.p01_applied == "true"


def test_p01_does_not_apply() -> None:
    base = _base(value="100.50")
    result = bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
        base=base,
        host_inputs=_host_inputs(
            u04_evidence=_witness(reservation_value_raw="10", empty_reservation_proven="false")
        ),
    )
    assert result.producer_output is not None
    assert result.producer_output.p01_applied == "false"
    assert result.producer_output.value == "90.50"


def test_p01_unknown_fail_closed() -> None:
    base = _base()
    p01 = bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
        base=base,
        age_seconds="1",
        freshness_max_age="5",
        applicability_state=P01_UNKNOWN,
    )
    out = produce_current_productive_available_for_sizing_v1(
        base=base,
        u04=bind_current_productive_u04_reservation_fact_from_typed_evidence_v1(
            base=base,
            evidence=_witness(),
            age_seconds="1",
            freshness_max_age="5",
        ),
        p01=p01,
        eligibility=bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
            base=base,
            host_inputs=_host_inputs(),
        ).eligibility_fact,
    )
    assert out.produced == "false"
    assert "P01_APPLICABILITY_UNKNOWN_FAIL_CLOSED" in out.reason_codes


def test_u04_missing_via_host_join() -> None:
    host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        _reconciled_obs(),
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
        usdc_row_status=CURRENCY_ROW_STATUS_PRESENT,
    )
    binding = host.u04_p01_eligibility_binding
    assert binding.inputs_bound is False
    assert PRIOR_BLOCKER in binding.reason_codes


def test_u04_invalid_and_stale_fail_closed() -> None:
    base = _base(age_seconds="99")
    result = bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
        base=base,
        host_inputs=_host_inputs(
            u04_evidence=_witness(reservation_value_raw="not-a-number"),
        ),
    )
    assert result.inputs_bound is False
    stale = bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
        base=base,
        host_inputs=_host_inputs(),
    )
    assert stale.inputs_bound is False
    assert stale.producer_output is not None
    assert "BASE_STALE" in stale.producer_output.reason_codes


def test_p01_missing_invalid_via_produce() -> None:
    base = _base()
    out = produce_current_productive_available_for_sizing_v1(
        base=base,
        u04=bind_current_productive_u04_reservation_fact_from_typed_evidence_v1(
            base=base,
            evidence=_witness(),
            age_seconds="1",
            freshness_max_age="5",
        ),
        p01=None,
        eligibility=bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
            base=base,
            host_inputs=_host_inputs(),
        ).eligibility_fact,
    )
    assert "P01_FACT_MISSING" in out.reason_codes


def test_no_double_u04_application_guard() -> None:
    base = _base()
    u04 = bind_current_productive_u04_reservation_fact_from_typed_evidence_v1(
        base=base,
        evidence=_witness(reservation_value_raw="10", empty_reservation_proven="false"),
        age_seconds="1",
        freshness_max_age="5",
    )
    p01 = bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
        base=base,
        age_seconds="1",
        freshness_max_age="5",
        applicability_state=P01_DOES_NOT_APPLY,
    )
    p01_bad = p01.__class__(**{**p01.__dict__, "source_class": "U04_PENDING_ORDER_RESERVATION"})
    out = produce_current_productive_available_for_sizing_v1(
        base=base,
        u04=u04,
        p01=p01_bad,
        eligibility=bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1(
            base=base,
            host_inputs=_host_inputs(),
        ).eligibility_fact,
    )
    assert "P01_MUST_NOT_ENCODE_U04" in out.reason_codes


def test_treasury_host_produce_with_bound_inputs() -> None:
    host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        _reconciled_obs(),
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
        usdc_row_status=CURRENCY_ROW_STATUS_PRESENT,
        u04_p01_eligibility_host_inputs=_host_inputs(
            u04_evidence=_witness(reservation_value_raw="10", empty_reservation_proven="false")
        ),
    )
    assert host.base_numeric_binding.numeric_base_bound is True
    binding = host.u04_p01_eligibility_binding
    assert binding.inputs_bound is True
    assert binding.producer_output is not None
    assert binding.producer_output.value == "90.00"
