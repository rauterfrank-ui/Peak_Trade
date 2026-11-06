"""S1: external capital decrease → Treasury Phase-2 venue observation binding tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.fixtures_v1 import (
    fixture_usdc_nonzero_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    parse_funding_account_balance_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    NETWORK_EXECUTION_AUTHORIZED,
    OBSERVED_BALANCE_ALONE_CONFIRMS_DEPLETION,
    PRODUCTIVE_WITHDRAWAL_PATH,
    TREASURY_MUTATION_AUTHORIZED,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.context_v1 import (
    TreasuryExternalCapitalDecreaseObservationContextV1,
    TreasuryWithdrawalHistorySignalV1,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.depletion_signal_v1 import (
    resolve_external_depletion_signal_for_decrease_context_v1,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.errors_v1 import (
    TreasuryExternalCapitalDecreaseObservationBindingError,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_for_external_capital_decrease_v1,
    produce_treasury_external_capital_decrease_observation_via_funding_balance_get_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    join_treasury_reconciliation_into_capital_admission_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
    TreasuryReconciliationClassV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
    evaluate_treasury_read_only_reconciliation_v1,
)

_ACCOUNT = "acct-treasury-s1-decrease-001"
_INSTRUMENT = "BTC-USDT-SWAP"
_TS = "2026-09-20T10:00:00Z"
_PACKAGE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1"
)


def _ctx(**overrides) -> TreasuryExternalCapitalDecreaseObservationContextV1:
    payload = {
        "evidence_id": "tevidence-s1-decrease-001",
        "account_identity": _ACCOUNT,
        "instrument_id": _INSTRUMENT,
        "withdrawal_history_freshness": TreasuryWithdrawalHistorySignalV1.UNKNOWN.value,
        "withdrawal_history_confirms_decrease": False,
        "prior_reconciled_capital_raw": "100",
        "cached_trading_capital_raw": "100",
    }
    payload.update(overrides)
    return TreasuryExternalCapitalDecreaseObservationContextV1(**payload)


def _funding(body: bytes | None = None) -> object:
    return parse_funding_account_balance_observation_v1(
        body_bytes=body or fixture_usdc_nonzero_v1(),
        http_status=200,
        observed_at_utc=_TS,
        venue="okx",
        rest_host="eea.okx.com",
        endpoint="/api/v5/asset/balances",
        headers={},
        transport_class="RecordingFakeCanaryTransportV1",
        get_performed=True,
    )


@pytest.fixture(autouse=True)
def _clear_idempotency_cache() -> None:
    clear_treasury_reconciliation_idempotency_cache_v1()
    yield
    clear_treasury_reconciliation_idempotency_cache_v1()


def test_standing_constants_no_mutation_or_withdraw_send() -> None:
    assert OBSERVED_BALANCE_ALONE_CONFIRMS_DEPLETION is False
    assert PRODUCTIVE_WITHDRAWAL_PATH is False
    assert NETWORK_EXECUTION_AUTHORIZED is False
    assert TREASURY_MUTATION_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    joined = "\n".join(path.read_text(encoding="utf-8") for path in _PACKAGE.glob("*.py"))
    assert "urllib.request" not in joined
    assert "UrllibLiveCanaryTransportV1" not in joined
    assert "/asset/withdrawal" not in joined


def test_funding_get_produces_decrease_observation_with_single_get() -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_usdc_nonzero_v1())
    observation = produce_treasury_external_capital_decrease_observation_via_funding_balance_get_v1(
        transport=transport,
        context=_ctx(),
    )
    assert observation.venue_balance_raw == "12.5"
    assert observation.balance_freshness == TreasuryFreshnessSignalV1.FRESH.value
    assert observation.deposit_history_freshness == TreasuryDepositHistorySignalV1.MISSING.value
    assert observation.deposit_history_confirms_increase is False
    assert len(transport.calls) == 1


def test_balance_drop_alone_does_not_mint_credible_depletion() -> None:
    body = (
        b'{"code":"0","msg":"","data":[{"ccy":"USDC","bal":"80","frozenBal":"0","availBal":"80"}]}'
    )
    observation = build_treasury_venue_observation_for_external_capital_decrease_v1(
        _funding(body),
        _ctx(
            withdrawal_history_freshness=TreasuryWithdrawalHistorySignalV1.UNCONFIRMED.value,
        ),
    )
    assert observation.external_depletion_signal == TreasuryExternalDepletionSignalV1.NONE.value
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.capital_increase_authority is False
    assert TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value not in recon.reason_codes


def test_confirmed_withdrawal_history_and_lower_venue_yields_credible_depletion() -> None:
    body = (
        b'{"code":"0","msg":"","data":[{"ccy":"USDC","bal":"80","frozenBal":"0","availBal":"80"}]}'
    )
    observation = build_treasury_venue_observation_for_external_capital_decrease_v1(
        _funding(body),
        _ctx(
            withdrawal_history_freshness=TreasuryWithdrawalHistorySignalV1.CONFIRMED.value,
            withdrawal_history_confirms_decrease=True,
            internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        ),
    )
    assert (
        observation.external_depletion_signal
        == TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.STALE.value
    assert "CREDIBLE_DEPLETION_CACHED_TRADING_STALE" in recon.reason_codes
    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert join.capital_admission_evidence.risk_admissible is False


def test_unknown_withdrawal_history_maps_to_unknown_depletion_fail_closed() -> None:
    signal = resolve_external_depletion_signal_for_decrease_context_v1(
        _ctx(),
        venue_balance_raw="80",
    )
    assert signal == TreasuryExternalDepletionSignalV1.UNKNOWN.value
    observation = build_treasury_venue_observation_for_external_capital_decrease_v1(
        _funding(
            b'{"code":"0","msg":"","data":[{"ccy":"USDC","bal":"80","frozenBal":"0","availBal":"80"}]}'
        ),
        _ctx(),
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.fail_closed is True
    assert "EXTERNAL_DEPLETION_SIGNAL_UNKNOWN" in recon.reason_codes


def test_decrease_confirm_without_confirmed_history_rejected_at_context() -> None:
    with pytest.raises(TreasuryExternalCapitalDecreaseObservationBindingError):
        build_treasury_venue_observation_for_external_capital_decrease_v1(
            _funding(),
            _ctx(
                withdrawal_history_freshness=TreasuryWithdrawalHistorySignalV1.UNCONFIRMED.value,
                withdrawal_history_confirms_decrease=True,
            ),
        )


def test_confirmed_history_but_venue_not_lower_rejected() -> None:
    with pytest.raises(TreasuryExternalCapitalDecreaseObservationBindingError):
        resolve_external_depletion_signal_for_decrease_context_v1(
            _ctx(
                withdrawal_history_freshness=TreasuryWithdrawalHistorySignalV1.CONFIRMED.value,
                withdrawal_history_confirms_decrease=True,
            ),
            venue_balance_raw="100",
        )


def test_duplicate_evidence_fingerprint_is_stable() -> None:
    ctx = _ctx(
        withdrawal_history_freshness=TreasuryWithdrawalHistorySignalV1.CONFIRMED.value,
        withdrawal_history_confirms_decrease=True,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
    )
    body = (
        b'{"code":"0","msg":"","data":[{"ccy":"USDC","bal":"80","frozenBal":"0","availBal":"80"}]}'
    )
    funding = _funding(body)
    first = build_treasury_venue_observation_for_external_capital_decrease_v1(funding, ctx)
    second = build_treasury_venue_observation_for_external_capital_decrease_v1(funding, ctx)
    assert first.evidence_fingerprint == second.evidence_fingerprint
    assert first == second


def test_productive_urllib_transport_refused() -> None:
    with pytest.raises(Exception):
        produce_treasury_external_capital_decrease_observation_via_funding_balance_get_v1(
            transport=UrllibLiveCanaryTransportV1(),
            context=_ctx(),
        )


def test_treasury_interference_proof_still_passes() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
