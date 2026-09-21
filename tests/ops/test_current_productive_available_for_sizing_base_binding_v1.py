"""CURRENT_PRODUCTIVE AVAILABLE_FOR_SIZING numeric BASE binding (Treasury host)."""

from __future__ import annotations

import pytest

from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
    Step29PCapitalRiskAdmissibilityClaimV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
    EXACT_ALLOWED_NUMERIC_SOURCE,
    OWNER_GO,
    SCHEMA_CLASS,
    clear_current_productive_base_binding_state_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveP01ReductionFactV1,
    CurrentProductiveU04ReservationFactV1,
    produce_current_productive_available_for_sizing_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.non_forbidden_non_eq_non_stock_usdc_current_productive_observation_v1 import (
    SCHEMA_CLASS as OBS_SCHEMA,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
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
    TreasuryReconciliationClassV1,
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
)

_ACCOUNT = "acct-base-bind-001"
_INSTRUMENT = "BTC-USDT-SWAP"
_TS = "2026-09-21T04:00:00Z"


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    clear_treasury_reconciliation_idempotency_cache_v1()
    clear_current_productive_base_binding_state_v1()
    yield
    clear_treasury_reconciliation_idempotency_cache_v1()
    clear_current_productive_base_binding_state_v1()


def _reconciled_obs(**overrides: object) -> TreasuryVenueObservationV1:
    payload = {
        "evidence_id": "tevidence-base-a",
        "evidence_fingerprint": "fp-base-a",
        "observed_at_utc": _TS,
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


def _host(obs: TreasuryVenueObservationV1, **kwargs: object):
    return join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        obs,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
        **kwargs,
    )


def test_standing_pins_and_owner_go() -> None:
    assert OWNER_GO == "OWNER_GO_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1"
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS == "UNBOUND"
    assert EXACT_ALLOWED_NUMERIC_SOURCE.startswith("TreasuryVenueObservationV1.")


def test_a_valid_fresh_reconciled_c08_and_numeric_base_bound() -> None:
    result = _host(_reconciled_obs())
    base = result.base_numeric_binding
    c08 = result.c08_sizing_source_binding
    assert c08.base_candidate_created is True
    assert base.numeric_base_bound is True
    assert base.base_fact is not None
    assert base.base_fact.fact_id == CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID
    assert base.base_fact.value == "100.00"
    assert base.base_fact.source_class == OBS_SCHEMA
    assert base.risk_admissible is False
    assert base.sizing_increase is False
    assert base.treasury_risk_admissible_mint is False
    assert base.fail_closed is False


def test_b_numeric_without_c08_candidacy_fail_closed() -> None:
    obs = _reconciled_obs(
        balance_freshness=TreasuryFreshnessSignalV1.STALE.value,
        prior_reconciled_capital_raw="",
    )
    result = _host(obs)
    assert result.c08_sizing_source_binding.base_candidate_created is False
    assert result.base_numeric_binding.numeric_base_bound is False
    assert result.base_numeric_binding.fail_closed is True


def test_c_c08_without_numeric_usdc_absent() -> None:
    obs = _reconciled_obs(venue_balance_raw="", prior_reconciled_capital_raw="")
    result = _host(
        obs,
        usdc_row_status=CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    )
    assert result.c08_sizing_source_binding.base_candidate_created is False
    assert result.base_numeric_binding.numeric_base_bound is False


def test_d_unknown_reconciliation_fail_closed() -> None:
    obs = _reconciled_obs(
        prior_reconciled_capital_raw="",
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.UNKNOWN.value,
    )
    result = _host(obs)
    assert result.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.UNKNOWN.value
    )
    assert result.base_numeric_binding.numeric_base_bound is False


def test_e_absent_not_zero_fail_closed() -> None:
    obs = _reconciled_obs(venue_balance_raw="")
    result = _host(obs, usdc_row_status=CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO)
    assert result.base_numeric_binding.numeric_base_bound is False
    assert any(
        "USDC_ROW_ABSENT" in code or "C08_BASE_CANDIDACY" in code
        for code in result.base_numeric_binding.reason_codes
    )


def test_f_stale_balance_fail_closed() -> None:
    obs = _reconciled_obs(balance_freshness=TreasuryFreshnessSignalV1.STALE.value)
    result = _host(obs)
    assert result.base_numeric_binding.numeric_base_bound is False


def test_g_provenance_conflict_host_fail_closed() -> None:
    first = _reconciled_obs(evidence_id="ev-1", evidence_fingerprint="same-fp")
    second = _reconciled_obs(evidence_id="ev-2", evidence_fingerprint="same-fp")
    _host(first)
    host = _host(second).host_evaluation
    assert host.fail_closed is True


def _algebra_inputs():
    u04 = CurrentProductiveU04ReservationFactV1(
        fact_id="CURRENT_PRODUCTIVE_U04_PENDING_ORDER_RESERVATION",
        value="0",
        settlement_currency="USDC",
        bound_account_identity=_ACCOUNT,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=_TS,
        observed_at_as_of=_TS,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest="b" * 64,
        source_class="CURRENT_PRODUCTIVE_PENDING_ORDER_RESERVATION",
        empty_reservation_proven="true",
    )
    p01 = CurrentProductiveP01ReductionFactV1(
        fact_id="CURRENT_PRODUCTIVE_P01_GOVERNED_REDUCTION",
        applicability_state="DOES_NOT_APPLY",
        value="",
        settlement_currency="USDC",
        bound_account_identity=_ACCOUNT,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=_TS,
        observed_at_as_of=_TS,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest="c" * 64,
        source_class="CURRENT_PRODUCTIVE_P01_DIRECTIVE",
    )
    eligibility = CurrentProductiveAccountEligibilityFactV1(
        fact_id="CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY",
        account_mode="FUTURES_MODE",
        bound_account_identity=_ACCOUNT,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=_TS,
        provenance_digest="d" * 64,
    )
    return u04, p01, eligibility


def test_h_wrong_currency_on_base_fact_fail_closed_in_producer() -> None:
    result = _host(_reconciled_obs())
    fact = result.base_numeric_binding.base_fact
    assert fact is not None
    bad = fact.__class__(**{**fact.__dict__, "settlement_currency": "EUR"})
    u04, p01, eligibility = _algebra_inputs()
    out = produce_current_productive_available_for_sizing_v1(
        base=bad,
        u04=u04,
        p01=p01,
        eligibility=eligibility,
    )
    assert out.produced == "false"
    assert "BASE_CURRENCY_NOT_USDC" in out.reason_codes


def test_i_wrong_unit_forbidden_source_class() -> None:
    result = _host(_reconciled_obs())
    fact = result.base_numeric_binding.base_fact
    assert fact is not None
    bad = fact.__class__(**{**fact.__dict__, "source_class": "availEq"})
    u04, p01, eligibility = _algebra_inputs()
    out = produce_current_productive_available_for_sizing_v1(
        base=bad,
        u04=u04,
        p01=p01,
        eligibility=eligibility,
    )
    assert out.produced == "false"
    assert "BASE_FORBIDDEN_OR_UNCLASSIFIED_SOURCE_CLASS" in out.reason_codes


def test_j_credible_depletion_block() -> None:
    obs = _reconciled_obs(
        venue_balance_raw="50",
        prior_reconciled_capital_raw="100",
        external_depletion_signal=TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value,
    )
    result = _host(obs)
    assert result.c08_sizing_source_binding.block_or_decrease is True
    assert result.base_numeric_binding.sizing_increase is False


def test_k_positive_restoration_requires_full_readmission() -> None:
    account = "acct-base-k-restore"
    depleted = _reconciled_obs(
        account_identity=account,
        evidence_id="tevidence-base-k-depletion",
        evidence_fingerprint="fp-base-k-depletion",
        observed_at_utc="2026-09-21T01:00:00Z",
        venue_balance_raw="80",
        prior_reconciled_capital_raw="100",
        deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value,
    )
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        depleted,
        expected_account_identity=account,
        expected_instrument_id=_INSTRUMENT,
    )
    restored = _reconciled_obs(
        account_identity=account,
        evidence_id="tevidence-base-k-restore",
        evidence_fingerprint="fp-base-k-restore",
        observed_at_utc="2026-09-21T02:00:00Z",
        venue_balance_raw="150",
        prior_reconciled_capital_raw="100",
        deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
        deposit_history_confirms_increase=True,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
    )
    result = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        restored,
        expected_account_identity=account,
        expected_instrument_id=_INSTRUMENT,
    )
    assert result.base_numeric_binding.numeric_base_bound is True
    assert result.base_numeric_binding.risk_admissible is False
    assert result.base_numeric_binding.sizing_increase is False


def test_l_restart_unknown_preserved() -> None:
    obs = _reconciled_obs(
        prior_reconciled_capital_raw="",
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.UNKNOWN.value,
    )
    first = _host(obs)
    clear_treasury_reconciliation_idempotency_cache_v1()
    second = _host(obs)
    assert first.base_numeric_binding.numeric_base_bound is False
    assert second.base_numeric_binding.numeric_base_bound is False


def test_m_old_after_newer_replay_fail_closed() -> None:
    newer = _reconciled_obs(
        evidence_id="ev-new",
        evidence_fingerprint="fp-new",
        observed_at_utc="2026-09-21T05:00:00Z",
        venue_balance_raw="100",
    )
    _host(newer)
    older = _reconciled_obs(
        evidence_id="ev-old",
        evidence_fingerprint="fp-old",
        observed_at_utc="2026-09-21T04:00:00Z",
        venue_balance_raw="200",
        balance_freshness=TreasuryFreshnessSignalV1.STALE.value,
    )
    result = _host(older)
    assert result.base_numeric_binding.numeric_base_bound is False


def test_n_duplicate_evidence_idempotent() -> None:
    obs = _reconciled_obs()
    first = _host(obs)
    second = _host(obs)
    assert first.base_numeric_binding.numeric_base_bound is True
    assert second.base_numeric_binding.numeric_base_bound is True
    assert (
        "DUPLICATE_EVIDENCE_NO_ADDITIONAL_CAPITAL_EFFECT"
        in second.base_numeric_binding.reason_codes
    )


def test_o_step_29p_deny() -> None:
    result = _host(_reconciled_obs())
    assert result.base_numeric_binding.risk_admissible is False


def test_p_step_29p_admit_still_requires_separate_claim() -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
        bind_current_productive_available_for_sizing_base_from_treasury_host_v1,
    )

    result = _host(_reconciled_obs())
    claim = Step29PCapitalRiskAdmissibilityClaimV1(
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        expected_instrument_id=_INSTRUMENT,
        observed_instrument_id=_INSTRUMENT,
        expected_currency="USDC",
        observed_currency="USDC",
        equity_dimension=RISK_EQUITY_DIMENSION,
        typed_account_equity_raw="100.00",
        typed_account_equity_source_field="CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    bound = bind_current_productive_available_for_sizing_base_from_treasury_host_v1(
        treasury_observation=_reconciled_obs(),
        c08_binding=result.c08_sizing_source_binding,
        host_evaluation=result.host_evaluation,
        usdc_row_status=CURRENCY_ROW_STATUS_PRESENT,
        capital_admission_evidence=result.treasury_join.capital_admission_evidence,
        step_29p_claim=claim,
    )
    assert bound.numeric_base_bound is True
    assert bound.risk_admissible is True
    assert bound.sizing_increase is True
    assert bound.treasury_risk_admissible_mint is False


def test_productive_host_reachability() -> None:
    result = _host(_reconciled_obs())
    assert result.base_numeric_binding.productive_host_code_reachable is True
    assert result.base_numeric_binding.observation_schema_class == OBS_SCHEMA
    assert SCHEMA_CLASS.endswith("_V1")
