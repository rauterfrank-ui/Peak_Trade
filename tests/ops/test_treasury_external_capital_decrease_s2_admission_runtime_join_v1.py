"""S2: external capital decrease → productive capital admission runtime join."""

from __future__ import annotations

import inspect
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    join_capital_admission_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    OWNER_ONE_SHOT_PERMIT_TOKEN,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CapitalAdmissionStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED as FULL_CORE_EXTERNAL_EFFECT,
    FullCoreExternalEffectNotAuthorizedError,
    refuse_external_effect_v1,
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
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.constants_v1 import (
    DEPOSIT_E5_TOUCHED,
    DEPOSIT_INCREASE_SEMANTICS_ENABLED,
    EXTERNAL_EFFECT_AUTHORIZED,
    JOIN_SEAM_ID,
    TREASURY_MUTATION_AUTHORIZED,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.errors_v1 import (
    TreasuryExternalCapitalDecreaseS2AdmissionError,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.join_v1 import (
    join_treasury_external_capital_decrease_into_capital_admission_runtime_v1,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.context_v1 import (
    TreasuryExternalCapitalDecreaseObservationContextV1,
    TreasuryWithdrawalHistorySignalV1,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_for_external_capital_decrease_v1,
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

_ACCOUNT = "acct-treasury-s2-decrease-001"
_INSTRUMENT = "BTC-USDT-SWAP"
_TS = "2026-09-20T11:00:00Z"
_S1_PACKAGE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1"
)
_S2_PACKAGE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/treasury_external_capital_decrease_s2_admission_runtime_join_v1"
)


def _ctx(**overrides) -> TreasuryExternalCapitalDecreaseObservationContextV1:
    payload = {
        "evidence_id": "tevidence-s2-decrease-001",
        "account_identity": _ACCOUNT,
        "instrument_id": _INSTRUMENT,
        "withdrawal_history_freshness": TreasuryWithdrawalHistorySignalV1.UNKNOWN.value,
        "withdrawal_history_confirms_decrease": False,
        "prior_reconciled_capital_raw": "100",
        "cached_trading_capital_raw": "100",
    }
    payload.update(overrides)
    return TreasuryExternalCapitalDecreaseObservationContextV1(**payload)


def _funding(body: bytes) -> object:
    return parse_funding_account_balance_observation_v1(
        body_bytes=body,
        http_status=200,
        observed_at_utc=_TS,
        venue="okx",
        rest_host="eea.okx.com",
        endpoint="/api/v5/asset/balances",
        headers={},
        transport_class="RecordingFakeCanaryTransportV1",
        get_performed=True,
    )


def _decrease_observation(**ctx_overrides) -> TreasuryVenueObservationV1:
    body = (
        b'{"code":"0","msg":"","data":[{"ccy":"USDC","bal":"80","frozenBal":"0","availBal":"80"}]}'
    )
    return build_treasury_venue_observation_for_external_capital_decrease_v1(
        _funding(body),
        _ctx(**ctx_overrides),
    )


def _admission_inputs(**overrides):
    payload = {
        "plan_identity": "plan-s2",
        "venue_plan_identity": "venue-s2",
        "instrument_identity_ok": True,
        "pretrade_admissible": True,
        "pretrade_source_kind": "FROZEN_OFFLINE_PRETRADE_EVIDENCE",
        "pretrade_freshness_status": "FROZEN_OFFLINE",
        "capital_risk_mode": CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        "owner_go": OWNER_ONE_SHOT_PERMIT_TOKEN,
        "admission_context": ADMISSION_CONTEXT_LIVE,
        "instrument_id": _INSTRUMENT,
        "expected_account_identity": _ACCOUNT,
    }
    payload.update(overrides)
    return join_capital_admission_into_admission_inputs_v1(**payload)


@pytest.fixture(autouse=True)
def _clear_idempotency_cache() -> None:
    clear_treasury_reconciliation_idempotency_cache_v1()
    yield
    clear_treasury_reconciliation_idempotency_cache_v1()


def test_standing_constants_fail_closed_and_no_deposit_e5() -> None:
    assert DEPOSIT_E5_TOUCHED is False
    assert DEPOSIT_INCREASE_SEMANTICS_ENABLED is False
    assert TREASURY_MUTATION_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    joined = "\n".join(path.read_text(encoding="utf-8") for path in _S2_PACKAGE.glob("*.py"))
    assert "urllib.request" not in joined
    assert "/asset/withdrawal" not in joined


def test_credible_decrease_conservative_admission_via_productive_seam() -> None:
    observation = _decrease_observation(
        withdrawal_history_freshness=TreasuryWithdrawalHistorySignalV1.CONFIRMED.value,
        withdrawal_history_confirms_decrease=True,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
    )
    assert (
        observation.external_depletion_signal
        == TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value
    )
    runtime_join = join_treasury_external_capital_decrease_into_capital_admission_runtime_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    evidence = runtime_join.capital_admission_evidence
    assert evidence.risk_admissible is False
    assert evidence.capital_authority_class != CAPITAL_AUTHORITY_RISK_ADMISSIBLE
    assert runtime_join.contract.fail_closed is True
    assert runtime_join.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.STALE.value
    )

    inputs = _admission_inputs(treasury_external_capital_decrease_observation=observation)
    assert inputs.capital_admission_status != CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    assert inputs.step_29p_risk_admissible is False
    assert JOIN_SEAM_ID in inputs.provenance_refs
    decision = evaluate_execution_admission_v1(inputs)
    assert decision.admitted is False
    assert decision.fail_closed is True


def test_unknown_and_stale_fail_closed_without_optimistic_restore() -> None:
    unknown_obs = _decrease_observation()
    runtime = join_treasury_external_capital_decrease_into_capital_admission_runtime_v1(
        unknown_obs,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert runtime.contract.fail_closed is True
    assert "S2_UNKNOWN_NO_OPTIMISTIC_RESTORE" in runtime.contract.reason_codes
    assert runtime.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.UNKNOWN.value
    )

    inputs = _admission_inputs(treasury_external_capital_decrease_observation=unknown_obs)
    assert inputs.capital_admission_status != CapitalAdmissionStatusV1.TRUSTED_PRESENT.value


def test_idempotent_observation_does_not_double_reduce_admission() -> None:
    observation = _decrease_observation(
        withdrawal_history_freshness=TreasuryWithdrawalHistorySignalV1.CONFIRMED.value,
        withdrawal_history_confirms_decrease=True,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
    )
    first = _admission_inputs(treasury_external_capital_decrease_observation=observation)
    second = _admission_inputs(treasury_external_capital_decrease_observation=observation)
    assert first.capital_admission_status == second.capital_admission_status
    assert first.capital_authority_class == second.capital_authority_class
    assert first.provenance_refs == second.provenance_refs


def test_deposit_increase_path_rejected_by_s2_contract() -> None:
    observation = TreasuryVenueObservationV1(
        evidence_id="tevidence-s2-deposit-drift",
        evidence_fingerprint="fp-s2-deposit-drift",
        observed_at_utc=_TS,
        account_identity=_ACCOUNT,
        instrument_id=_INSTRUMENT,
        venue_balance_raw="150",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
        deposit_history_confirms_increase=True,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )
    with pytest.raises(TreasuryExternalCapitalDecreaseS2AdmissionError, match="DEPOSIT"):
        join_treasury_external_capital_decrease_into_capital_admission_runtime_v1(
            observation,
            expected_account_identity=_ACCOUNT,
            expected_instrument_id=_INSTRUMENT,
        )


def test_reconciled_decrease_marks_capital_admission_stale_not_trusted() -> None:
    observation = TreasuryVenueObservationV1(
        evidence_id="tevidence-s2-reconciled-decrease",
        evidence_fingerprint="fp-s2-reconciled-decrease",
        observed_at_utc=_TS,
        account_identity=_ACCOUNT,
        instrument_id=_INSTRUMENT,
        venue_balance_raw="90",
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.MISSING.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
    )
    runtime = join_treasury_external_capital_decrease_into_capital_admission_runtime_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert runtime.treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.RECONCILED.value
    )
    evidence = runtime.capital_admission_evidence
    assert evidence.evidence_status == CapitalAdmissionStatusV1.STALE.value
    assert "CAPITAL_DECREASE_STALE_HIGHER_DENIED" in evidence.reason_codes
    prior = Decimal(str(observation.prior_reconciled_capital_raw))
    venue = Decimal(str(observation.venue_balance_raw))
    assert venue < prior


def test_productive_seam_rejects_claim_and_observation_together() -> None:
    observation = _decrease_observation()
    with pytest.raises(ValueError, match="MUTUALLY_EXCLUSIVE"):
        _admission_inputs(
            treasury_external_capital_decrease_observation=observation,
            capital_admission_claim=object(),
        )


def test_s1_binding_package_unchanged() -> None:
    s1_before = {
        path.name: path.read_text(encoding="utf-8") for path in sorted(_S1_PACKAGE.glob("*.py"))
    }
    assert s1_before
    assert (
        "build_treasury_venue_observation_for_external_capital_decrease_v1"
        in s1_before["producer_v1.py"]
    )


def test_treasury_interference_proof_and_external_effect_unreachable() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
    assert proof["TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY"] is False
    assert FULL_CORE_EXTERNAL_EFFECT is False
    with pytest.raises(FullCoreExternalEffectNotAuthorizedError):
        refuse_external_effect_v1(reason="S2_TEST_EXTERNAL_EFFECT_DENIED")


def test_capital_admission_owner_signature_unchanged_except_optional_observation() -> None:
    sig = inspect.signature(join_capital_admission_into_admission_inputs_v1)
    assert "treasury_external_capital_decrease_observation" in sig.parameters
    assert sig.parameters["treasury_external_capital_decrease_observation"].default is None
    owner_sig = inspect.signature(evaluate_execution_admission_v1)
    assert list(owner_sig.parameters) == ["inputs"]
