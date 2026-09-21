"""E4 productive host join — Treasury → E4 → governed account-equity host."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    evaluate_capital_admission_v1,
    join_capital_admission_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    OWNER_ONE_SHOT_PERMIT_TOKEN,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CapitalAdmissionStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    parse_funding_account_balance_observation_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    JOIN_SEAM_ID,
    NETWORK_ALLOWED,
    RISK_ADMISSIBLE_MINT_AUTHORIZED,
    TREASURY_MUTATION_AUTHORIZED,
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
from src.ops.treasury_phase_2_read_only_reconciliation_v1.errors_v1 import (
    TreasuryPhase2ReconciliationError,
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
_PACKAGE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1"
)


def _obs(**overrides) -> TreasuryVenueObservationV1:
    payload = {
        "evidence_id": "tevidence-e4-host-001",
        "evidence_fingerprint": "fp-e4-host-001",
        "observed_at_utc": _TS,
        "account_identity": _ACCOUNT,
        "instrument_id": _INSTRUMENT,
        "venue_balance_raw": "96.00191",
        "balance_freshness": TreasuryFreshnessSignalV1.FRESH.value,
        "deposit_history_freshness": TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        "deposit_history_confirms_increase": False,
        "internal_transfer_signal": TreasuryInternalTransferSignalV1.UNKNOWN.value,
        "external_depletion_signal": TreasuryExternalDepletionSignalV1.NONE.value,
        "prior_reconciled_capital_raw": "",
        "cached_trading_capital_raw": "",
    }
    payload.update(overrides)
    return TreasuryVenueObservationV1(**payload)


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
    assert funding.usdc_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    ctx = TreasuryCapitalDepositObservationContextV1(
        evidence_id="tevidence-6672-host",
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


@pytest.fixture(autouse=True)
def _clear_idempotency_cache() -> None:
    clear_treasury_reconciliation_idempotency_cache_v1()
    yield
    clear_treasury_reconciliation_idempotency_cache_v1()


def test_standing_constants_no_network_mutation_or_mint() -> None:
    assert JOIN_SEAM_ID.endswith("_PRODUCTIVE_HOST_JOIN_V1")
    assert NETWORK_ALLOWED is False
    assert TREASURY_MUTATION_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert RISK_ADMISSIBLE_MINT_AUTHORIZED is False
    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in _PACKAGE.glob("*.py")
        if path.name != "constants_v1.py"
    )
    assert "urllib.request" not in joined


def test_a_6672_unknown_and_absent_not_zero_fail_closed_e2e() -> None:
    observation = _6672_style_observation()
    result = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
        usdc_row_status=CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    )
    host = result.host_evaluation
    assert result.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.UNKNOWN.value
    )
    assert host.treasury_reconciliation_status == TreasuryReconciliationClassV1.UNKNOWN.value
    assert host.usdc_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    assert host.fail_closed is True
    assert host.treasury_capital_admitted is False
    assert host.observed_equity_minted is False
    assert host.reconciled_equity_minted is False
    assert host.risk_admissible_mint is False
    assert host.sizing_authority_changed is False
    assert host.productive_host_reachable is True

    chain = execute_treasury_productive_reconciliation_chain_v1(observation)
    assert chain["PRODUCTIVE_HOST_JOIN_STATUS"] == "PRODUCTIVE_HOST_JOIN_WIRED"
    assert chain["PRODUCTIVE_HOST_EVALUATION"]["fail_closed"] is True
    assert chain["RECONCILIATION_STATUS"] == TreasuryReconciliationClassV1.UNKNOWN.value


def test_b_reconciled_stable_orchestration_consumed_without_risk_mint() -> None:
    account = "acct-treasury-e4-001"
    instrument = "BTC-USDT-SWAP"
    observation = TreasuryVenueObservationV1(
        evidence_id="tevidence-e4-host-reconciled",
        evidence_fingerprint="fp-e4-host-reconciled",
        observed_at_utc=_TS,
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
    result = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=account,
        expected_instrument_id=instrument,
    )
    host = result.host_evaluation
    assert host.orchestration_ingress_admitted is True
    assert host.fail_closed is False
    assert host.treasury_capital_admitted is False
    assert host.risk_admissible_mint is False
    assert result.treasury_join.capital_admission_evidence.evidence_status == (
        CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    )


def test_c_stale_balance_fail_closed() -> None:
    observation = _obs(balance_freshness=TreasuryFreshnessSignalV1.STALE.value)
    host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    assert host.fail_closed is True
    assert host.treasury_capital_admitted is False


def test_d_conflicted_fingerprint_fail_closed() -> None:
    first = _obs(evidence_id="ev-a", evidence_fingerprint="same-fp")
    second = _obs(evidence_id="ev-b", evidence_fingerprint="same-fp")
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        first,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        second,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    assert host.fail_closed is True


def test_e_missing_prior_reconciled_unknown_fail_closed() -> None:
    observation = _6672_style_observation()
    host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    assert host.treasury_reconciliation_status == TreasuryReconciliationClassV1.UNKNOWN.value


def test_f_restart_replay_unknown_preserved() -> None:
    observation = _6672_style_observation()
    first = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    clear_treasury_reconciliation_idempotency_cache_v1()
    second = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    assert (
        first.treasury_reconciliation_status
        == second.treasury_reconciliation_status
        == (TreasuryReconciliationClassV1.UNKNOWN.value)
    )
    assert first.fail_closed and second.fail_closed


def test_g_idempotent_replay_same_observation() -> None:
    observation = _6672_style_observation()
    first = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    second = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    assert first.treasury_reconciliation_status == second.treasury_reconciliation_status


def test_h_no_treasury_state_not_applicable_to_join() -> None:
    with pytest.raises(TreasuryPhase2ReconciliationError):
        join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
            _obs(evidence_id="", evidence_fingerprint=""),
            expected_account_identity=_ACCOUNT,
            expected_instrument_id=_INSTRUMENT,
        )


def test_i_duplicate_persisted_observation_idempotent() -> None:
    observation = _6672_style_observation()
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    replay = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    ).host_evaluation
    assert replay.treasury_reconciliation_status == TreasuryReconciliationClassV1.UNKNOWN.value


def test_j_full_core_without_treasury_still_works() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
    inputs = join_capital_admission_into_admission_inputs_v1(
        plan_identity="plan-1",
        venue_plan_identity="venue-plan-1",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind="real",
        pretrade_freshness_status="FRESH",
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN,
        admission_context=ADMISSION_CONTEXT_LIVE,
        expected_account_identity=_ACCOUNT,
        instrument_id=_INSTRUMENT,
        capital_admission_claim=None,
        treasury_external_capital_decrease_observation=None,
    )
    assert inputs.capital_admission_status
    assert evaluate_capital_admission_v1 is not None


def test_treasury_interference_proof_still_passes() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["TREASURY_INTERFERENCE_PROOF"] == "PASS"
