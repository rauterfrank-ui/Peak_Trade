"""E1: deposit/capital-increase → Treasury Phase-2 venue observation binding tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    live_venue_capital_may_bind_step_29p_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
)
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
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    assert_treasury_join_never_mints_risk_admissible_v1,
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
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    NETWORK_EXECUTION_AUTHORIZED,
    OBSERVED_BALANCE_ALONE_CONFIRMS_DEPOSIT,
    TREASURY_MUTATION_AUTHORIZED,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.context_v1 import (
    TreasuryCapitalDepositObservationContextV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.errors_v1 import (
    TreasuryPhase2VenueObservationBindingError,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_from_funding_balance_v1,
    produce_treasury_venue_observation_via_funding_balance_get_v1,
)

_ACCOUNT = "acct-treasury-e1-001"
_INSTRUMENT = "BTC-USDT-SWAP"
_TS = "2026-09-20T09:00:00Z"
_PACKAGE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/treasury_phase_2_read_only_venue_observation_binding_v1"
)


def _ctx(**overrides) -> TreasuryCapitalDepositObservationContextV1:
    payload = {
        "evidence_id": "tevidence-e1-001",
        "account_identity": _ACCOUNT,
        "instrument_id": _INSTRUMENT,
        "deposit_history_freshness": TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        "deposit_history_confirms_increase": False,
        "prior_reconciled_capital_raw": "100",
        "cached_trading_capital_raw": "100",
    }
    payload.update(overrides)
    return TreasuryCapitalDepositObservationContextV1(**payload)


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


def test_standing_constants_no_mutation_or_productive_network() -> None:
    assert OBSERVED_BALANCE_ALONE_CONFIRMS_DEPOSIT is False
    assert NETWORK_EXECUTION_AUTHORIZED is False
    assert TREASURY_MUTATION_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    joined = "\n".join(path.read_text(encoding="utf-8") for path in _PACKAGE.glob("*.py"))
    assert "urllib.request" not in joined
    assert "UrllibLiveCanaryTransportV1" not in joined


def test_e1_funding_get_produces_treasury_venue_observation() -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_usdc_nonzero_v1())
    observation = produce_treasury_venue_observation_via_funding_balance_get_v1(
        transport=transport,
        context=_ctx(),
    )
    assert observation.venue_balance_raw == "12.5"
    assert observation.balance_freshness == TreasuryFreshnessSignalV1.FRESH.value
    assert len(transport.calls) == 1


def test_at01_observed_balance_increase_without_deposit_reconciliation_denies_sizing() -> None:
    body = b'{"code":"0","msg":"","data":[{"ccy":"USDC","bal":"150","frozenBal":"0","availBal":"150"}]}'
    funding = _funding(body)
    observation = build_treasury_venue_observation_from_funding_balance_v1(
        funding,
        _ctx(
            deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
            deposit_history_confirms_increase=False,
            prior_reconciled_capital_raw="100",
        ),
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.OBSERVED.value
    assert recon.capital_increase_authority is False
    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    evidence = join.capital_admission_evidence
    assert evidence.risk_admissible is False
    assert evidence.capital_authority_class != CAPITAL_AUTHORITY_RISK_ADMISSIBLE
    assert live_venue_capital_may_bind_step_29p_v1(evidence) is False
    assert_treasury_join_never_mints_risk_admissible_v1(join)


def test_deposit_confirm_without_confirmed_history_rejected_at_context() -> None:
    with pytest.raises(TreasuryPhase2VenueObservationBindingError):
        build_treasury_venue_observation_from_funding_balance_v1(
            _funding(),
            _ctx(
                deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
                deposit_history_confirms_increase=True,
            ),
        )


def test_reconciled_capital_increase_passes_only_to_capital_admission_not_risk() -> None:
    body = b'{"code":"0","msg":"","data":[{"ccy":"USDC","bal":"150","frozenBal":"0","availBal":"150"}]}'
    observation = build_treasury_venue_observation_from_funding_balance_v1(
        _funding(body),
        _ctx(
            deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
            deposit_history_confirms_increase=True,
            prior_reconciled_capital_raw="100",
            internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
            external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        ),
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.RECONCILED.value
    assert recon.capital_increase_authority is True
    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert join.capital_admission_evidence.risk_admissible is False
    assert_treasury_join_never_mints_risk_admissible_v1(join)


def test_productive_urllib_transport_refused() -> None:
    with pytest.raises(Exception):
        produce_treasury_venue_observation_via_funding_balance_get_v1(
            transport=UrllibLiveCanaryTransportV1(),
            context=_ctx(),
        )


def test_treasury_interference_proof_still_passes() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
