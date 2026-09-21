"""C08 productive sizing-source binding — productive host reachability and adversarial matrix."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CapitalAdmissionStatusV1,
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
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    parse_funding_account_balance_observation_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.join_v1 import (
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_productive_sizing_source_binding_v1 import (
    C08_CURRENT_BINDING,
    C08_INPUT_CLASS,
    C08_PRODUCTIVE_BINDING_IMPLEMENTED,
    EARLIEST_NEW_REAL_BLOCKER_AFTER_WP,
    bind_c08_productive_sizing_source_from_e4_host_join_v1,
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
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.context_v1 import (
    TreasuryCapitalDepositObservationContextV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_from_funding_balance_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.chain_v1 import (
    execute_treasury_productive_reconciliation_chain_v1,
)

_ACCOUNT = "okx-eea-uid:6672-fixture"
_INSTRUMENT = "ETH-USDT-SWAP"
_TS = "2026-09-21T01:16:57Z"
_RUNBOOK = (
    Path(__file__).resolve().parents[2] / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
)


@pytest.fixture(autouse=True)
def _clear_idempotency_cache() -> None:
    clear_treasury_reconciliation_idempotency_cache_v1()
    yield
    clear_treasury_reconciliation_idempotency_cache_v1()


def _6672_style_observation() -> TreasuryVenueObservationV1:
    eur_only_body = (
        b'{"code":"0","msg":"","data":[{"ccy":"EUR","bal":"96.00191",'
        b'"frozenBal":"0","availBal":"96.00191"}]}'
    )
    funding = parse_funding_account_balance_observation_v1(
        body_bytes=eur_only_body,
        http_status=200,
        observed_at_utc=_TS,
        venue="okx",
        rest_host="eea.okx.com",
        endpoint="/api/v5/asset/balances",
        headers={},
        transport_class="RecordingFakeCanaryTransportV1",
        get_performed=True,
    )
    ctx = TreasuryCapitalDepositObservationContextV1(
        evidence_id="tevidence-6672-c08",
        account_identity=_ACCOUNT,
        instrument_id=_INSTRUMENT,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.UNKNOWN.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="",
        cached_trading_capital_raw="",
    )
    return build_treasury_venue_observation_from_funding_balance_v1(funding, ctx)


def _host_join(
    observation: TreasuryVenueObservationV1,
    *,
    account: str,
    instrument: str = _INSTRUMENT,
    usdc_row_status: str = "",
):
    return join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=account,
        expected_instrument_id=instrument,
        usdc_row_status=usdc_row_status,
    )


def _observed_only_increase_not_reconciled() -> TreasuryVenueObservationV1:
    """Phase-2 AT01-style OBSERVED-only (never RECONCILED)."""
    return TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-adv-a",
        evidence_fingerprint="fp-c08-adv-a",
        observed_at_utc=_TS,
        account_identity="acct-c08-adv-a",
        instrument_id="BTC-USDT-SWAP",
        venue_balance_raw="150",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )


def _reconciled_observation(
    *,
    account: str = "acct-c08-reconciled-001",
    instrument: str = "BTC-USDT-SWAP",
    balance: str = "100",
    prior: str = "100",
) -> TreasuryVenueObservationV1:
    return TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-reconciled",
        evidence_fingerprint="fp-c08-reconciled",
        observed_at_utc=_TS,
        account_identity=account,
        instrument_id=instrument,
        venue_balance_raw=balance,
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.MISSING.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw=prior,
        cached_trading_capital_raw=prior,
    )


def test_standing_binding_constants_and_runbook() -> None:
    runbook = _RUNBOOK.read_text(encoding="utf-8")
    assert C08_CURRENT_BINDING == "BOUND"
    assert C08_PRODUCTIVE_BINDING_IMPLEMENTED is True
    assert C08_INPUT_CLASS.endswith("RECONCILED_BASE_CANDIDATE_EVIDENCE")
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS == "UNBOUND"
    assert "C08_PRODUCTIVE_BINDING_IMPLEMENTED=true" in runbook
    assert (
        EARLIEST_NEW_REAL_BLOCKER_AFTER_WP
        == "CURRENT_PRODUCTIVE_CT_SIZING_PRODUCE_BLOCKED_U04_P01_ELIGIBILITY_INPUTS_UNBOUND"
    )


def test_6672_unknown_absent_not_zero_fail_closed_e2e() -> None:
    observation = _6672_style_observation()
    result = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
        usdc_row_status=CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    )
    c08 = result.c08_sizing_source_binding
    assert result.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.UNKNOWN.value
    )
    assert c08.base_candidate_created is False
    assert c08.risk_admissible is False
    assert c08.sizing_increase is False
    assert c08.fail_closed is True
    assert c08.treasury_available_for_sizing_mint is False
    assert c08.productive_host_code_reachable is True
    assert c08.base_slot_id == CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID

    chain = execute_treasury_productive_reconciliation_chain_v1(observation)
    assert chain["C08_SIZING_SOURCE_BINDING"]["fail_closed"] is True


def test_reconciled_stable_base_candidate_without_sizing_increase() -> None:
    account = "acct-c08-stable"
    instrument = "BTC-USDT-SWAP"
    observation = _reconciled_observation(account=account, instrument=instrument)
    result = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=account,
        expected_instrument_id=instrument,
    )
    c08 = result.c08_sizing_source_binding
    assert c08.base_candidate_created is True
    assert c08.base_value_status == "UNBOUND"
    assert c08.risk_admissible is False
    assert c08.sizing_increase is False
    assert c08.treasury_risk_admissible_mint is False
    assert result.treasury_join.capital_admission_evidence.evidence_status == (
        CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    )


def test_stale_observed_fail_closed_no_base_candidate() -> None:
    observation = TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-stale",
        evidence_fingerprint="fp-stale",
        observed_at_utc=_TS,
        account_identity=_ACCOUNT,
        instrument_id=_INSTRUMENT,
        venue_balance_raw="96",
        balance_freshness=TreasuryFreshnessSignalV1.STALE.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.UNKNOWN.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
    )
    c08 = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).c08_sizing_source_binding
    assert c08.base_candidate_created is False
    assert c08.fail_closed is True


def test_step_29p_admit_only_with_full_claim_not_treasury_mint() -> None:
    account = "acct-c08-29p-admit"
    instrument = "BTC-USDT-SWAP"
    observation = _reconciled_observation(account=account, instrument=instrument)
    joined = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=account,
        expected_instrument_id=instrument,
    )
    claim = Step29PCapitalRiskAdmissibilityClaimV1(
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        expected_instrument_id=instrument,
        observed_instrument_id=instrument,
        expected_currency="USDC",
        observed_currency="USDC",
        equity_dimension=RISK_EQUITY_DIMENSION,
        typed_account_equity_raw="100",
        typed_account_equity_source_field="CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    c08 = bind_c08_productive_sizing_source_from_e4_host_join_v1(
        treasury_join=joined.treasury_join,
        orchestration_join=joined.orchestration_join,
        host_evaluation=joined.host_evaluation,
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        step_29p_claim=claim,
    )
    assert c08.base_candidate_created is True
    assert c08.risk_admissible is True
    assert c08.sizing_increase is True
    assert c08.treasury_risk_admissible_mint is False
    assert c08.authority_owner == "capital_risk_admissibility_owner_v1"


def test_adversarial_a_observed_only_c08_edge_fail_closed() -> None:
    observation = _observed_only_increase_not_reconciled()
    account = observation.account_identity
    result = _host_join(observation, account=account, instrument=observation.instrument_id)
    recon = result.treasury_join.reconciliation.reconciliation_class
    assert recon == TreasuryReconciliationClassV1.OBSERVED.value
    assert recon != TreasuryReconciliationClassV1.RECONCILED.value
    c08 = result.c08_sizing_source_binding
    assert c08.base_candidate_created is False
    assert c08.risk_admissible is False
    assert c08.sizing_increase is False
    assert c08.fail_closed is True
    assert c08.treasury_risk_admissible_mint is False
    assert c08.treasury_available_for_sizing_mint is False


def test_adversarial_g_absent_treasury_capital_not_zero_coerced() -> None:
    """Empty venue balance is absent capital, not numeric zero."""
    account = "acct-c08-adv-g"
    observation = TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-adv-g",
        evidence_fingerprint="fp-c08-adv-g",
        observed_at_utc=_TS,
        account_identity=account,
        instrument_id="BTC-USDT-SWAP",
        venue_balance_raw="",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.MISSING.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="",
        cached_trading_capital_raw="",
    )
    assert observation.venue_balance_raw != "0"
    result = _host_join(observation, account=account, instrument=observation.instrument_id)
    c08 = result.c08_sizing_source_binding
    assert result.treasury_join.reconciliation.reconciliation_class != (
        TreasuryReconciliationClassV1.RECONCILED.value
    )
    assert c08.base_candidate_created is False
    assert c08.risk_admissible is False
    assert c08.sizing_increase is False
    assert c08.fail_closed is True


def test_adversarial_h_credible_depletion_e4_c08_conservative_block() -> None:
    account = "acct-c08-adv-h"
    observation = TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-adv-h",
        evidence_fingerprint="fp-c08-adv-h",
        observed_at_utc=_TS,
        account_identity=account,
        instrument_id="BTC-USDT-SWAP",
        venue_balance_raw="80",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )
    result = _host_join(observation, account=account, instrument=observation.instrument_id)
    assert (
        observation.external_depletion_signal
        == TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value
    )
    assert result.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.STALE.value
    )
    assert "CREDIBLE_DEPLETION_CACHED_TRADING_STALE" in (
        result.treasury_join.reconciliation.reason_codes
    )
    c08 = result.c08_sizing_source_binding
    assert c08.base_candidate_created is False
    assert c08.risk_admissible is False
    assert c08.sizing_increase is False
    assert c08.treasury_risk_admissible_mint is False
    assert c08.treasury_available_for_sizing_mint is False
    assert c08.block_or_decrease is True


def test_adversarial_i_restoration_after_depletion_no_auto_sizing() -> None:
    account = "acct-c08-adv-i"
    instrument = "BTC-USDT-SWAP"
    depletion = TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-adv-i-depletion",
        evidence_fingerprint="fp-c08-adv-i-depletion",
        observed_at_utc="2026-09-21T01:00:00Z",
        account_identity=account,
        instrument_id=instrument,
        venue_balance_raw="80",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )
    depletion_result = _host_join(depletion, account=account, instrument=instrument)
    assert depletion_result.c08_sizing_source_binding.sizing_increase is False
    assert depletion_result.c08_sizing_source_binding.base_candidate_created is False

    restoration = TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-adv-i-restore",
        evidence_fingerprint="fp-c08-adv-i-restore",
        observed_at_utc="2026-09-21T02:00:00Z",
        account_identity=account,
        instrument_id=instrument,
        venue_balance_raw="150",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
        deposit_history_confirms_increase=True,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )
    restore_result = _host_join(restoration, account=account, instrument=instrument)
    assert restore_result.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.RECONCILED.value
    )
    c08 = restore_result.c08_sizing_source_binding
    assert c08.base_candidate_created is True
    assert c08.risk_admissible is False
    assert c08.sizing_increase is False
    assert c08.treasury_risk_admissible_mint is False
    assert c08.treasury_available_for_sizing_mint is False


def test_adversarial_k_replay_older_after_newer_state_no_override() -> None:
    account = "acct-c08-adv-k"
    instrument = "BTC-USDT-SWAP"
    newer = TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-adv-k-new",
        evidence_fingerprint="fp-c08-adv-k-new",
        observed_at_utc="2026-09-21T02:00:00Z",
        account_identity=account,
        instrument_id=instrument,
        venue_balance_raw="100",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.MISSING.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )
    newer_result = _host_join(newer, account=account, instrument=instrument)
    assert newer_result.c08_sizing_source_binding.base_candidate_created is True
    assert newer_result.c08_sizing_source_binding.sizing_increase is False

    older = TreasuryVenueObservationV1(
        evidence_id="tevidence-c08-adv-k-old",
        evidence_fingerprint="fp-c08-adv-k-old",
        observed_at_utc="2026-09-21T01:00:00Z",
        account_identity=account,
        instrument_id=instrument,
        venue_balance_raw="200",
        balance_freshness=TreasuryFreshnessSignalV1.STALE.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.UNKNOWN.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )
    older_result = _host_join(older, account=account, instrument=instrument)
    assert older_result.treasury_join.reconciliation.reconciliation_class in {
        TreasuryReconciliationClassV1.STALE.value,
        TreasuryReconciliationClassV1.UNKNOWN.value,
    }
    older_c08 = older_result.c08_sizing_source_binding
    assert older_c08.base_candidate_created is False
    assert older_c08.sizing_increase is False
    assert older_c08.fail_closed is True

    replay_newer = _host_join(newer, account=account, instrument=instrument)
    assert replay_newer.c08_sizing_source_binding.base_candidate_created is True
    assert replay_newer.c08_sizing_source_binding.sizing_increase is False


def test_restart_unknown_preserved() -> None:
    observation = _6672_style_observation()
    first = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).c08_sizing_source_binding
    clear_treasury_reconciliation_idempotency_cache_v1()
    second = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).c08_sizing_source_binding
    assert first.treasury_reconciliation_status == second.treasury_reconciliation_status
    assert first.fail_closed and second.fail_closed
