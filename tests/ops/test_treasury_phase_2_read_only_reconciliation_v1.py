"""Treasury Phase-2 read-only reconciliation foundation tests. No network."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    live_venue_capital_may_bind_step_29p_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CapitalAdmissionStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_interference_absent_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.constants_v1 import (
    NETWORK_ALLOWED,
    TREASURY_MUTATION_AUTHORIZED,
    TREASURY_PHASE_2_STATUS,
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
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
    evaluate_treasury_read_only_reconciliation_v1,
)

_ACCOUNT = "acct-treasury-phase2-001"
_INSTRUMENT = "BTC-USDT-SWAP"
_TS = "2026-09-20T08:00:00Z"
_PACKAGE = (
    Path(__file__).resolve().parents[2] / "src/ops/treasury_phase_2_read_only_reconciliation_v1"
)


def _obs(**overrides) -> TreasuryVenueObservationV1:
    payload = {
        "evidence_id": "tevidence-phase2-001",
        "evidence_fingerprint": "fp-phase2-001",
        "observed_at_utc": _TS,
        "account_identity": _ACCOUNT,
        "instrument_id": _INSTRUMENT,
        "venue_balance_raw": "100",
        "balance_freshness": TreasuryFreshnessSignalV1.FRESH.value,
        "deposit_history_freshness": TreasuryDepositHistorySignalV1.CONFIRMED.value,
        "deposit_history_confirms_increase": True,
        "internal_transfer_signal": TreasuryInternalTransferSignalV1.CLEAR.value,
        "external_depletion_signal": TreasuryExternalDepletionSignalV1.NONE.value,
        "prior_reconciled_capital_raw": "100",
        "cached_trading_capital_raw": "100",
    }
    payload.update(overrides)
    return TreasuryVenueObservationV1(**payload)


@pytest.fixture(autouse=True)
def _clear_idempotency_cache() -> None:
    clear_treasury_reconciliation_idempotency_cache_v1()
    yield
    clear_treasury_reconciliation_idempotency_cache_v1()


def test_standing_constants_no_network_or_mutation() -> None:
    assert TREASURY_PHASE_2_STATUS == "READ_ONLY_FOUNDATION_BOUND"
    assert NETWORK_ALLOWED is False
    assert TREASURY_MUTATION_AUTHORIZED is False
    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in _PACKAGE.glob("*.py")
        if path.name != "constants_v1.py"
    )
    assert "urllib.request" not in joined
    assert "requests" not in joined
    assert "LiveCanaryHttpClientV1" not in joined


def test_at01_balance_increase_before_deposit_reconciliation_denies_increase() -> None:
    observation = _obs(
        venue_balance_raw="150",
        prior_reconciled_capital_raw="100",
        deposit_history_confirms_increase=False,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.OBSERVED.value
    assert recon.capital_increase_authority is False
    assert "OBSERVED_INCREASE_DEPOSIT_HISTORY_NOT_RECONCILED" in recon.reason_codes

    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    evidence = join.capital_admission_evidence
    assert evidence.risk_admissible is False
    assert evidence.capital_authority_class != CAPITAL_AUTHORITY_RISK_ADMISSIBLE
    assert live_venue_capital_may_bind_step_29p_v1(evidence) is False


def test_at02_external_depletion_against_stale_cached_state_conservative_deny() -> None:
    observation = _obs(
        venue_balance_raw="80",
        prior_reconciled_capital_raw="100",
        cached_trading_capital_raw="100",
        external_depletion_signal=TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value,
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.STALE.value
    assert recon.capital_increase_authority is False
    assert "CREDIBLE_DEPLETION_CACHED_TRADING_STALE" in recon.reason_codes

    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    evidence = join.capital_admission_evidence
    assert evidence.risk_admissible is False
    assert_treasury_join_never_mints_risk_admissible_v1(join)


def test_at10_internal_transfer_debit_before_credit_is_ambiguous() -> None:
    observation = _obs(
        internal_transfer_signal=TreasuryInternalTransferSignalV1.DEBIT_BEFORE_CREDIT_UNSETTLED.value,
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.AMBIGUOUS.value
    assert recon.capital_increase_authority is False
    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert_treasury_join_never_mints_risk_admissible_v1(join)


def test_at11_fresh_balance_stale_history_no_optimistic_reconciliation() -> None:
    observation = _obs(
        deposit_history_freshness=TreasuryDepositHistorySignalV1.STALE.value,
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.AMBIGUOUS.value
    assert "FRESH_BALANCE_STALE_DEPOSIT_HISTORY" in recon.reason_codes
    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert join.reconciliation.capital_increase_authority is False
    assert_treasury_join_never_mints_risk_admissible_v1(join)


def test_reconciled_produces_capital_admission_evidence_without_risk_mint() -> None:
    observation = _obs(
        venue_balance_raw="90",
        prior_reconciled_capital_raw="100",
        deposit_history_confirms_increase=False,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.MISSING.value,
    )
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.RECONCILED.value
    join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    evidence = join.capital_admission_evidence
    assert evidence.risk_admissible is False
    assert evidence.evidence_status == CapitalAdmissionStatusV1.STALE.value
    assert "CAPITAL_DECREASE_STALE_HIGHER_DENIED" in evidence.reason_codes
    assert_treasury_join_never_mints_risk_admissible_v1(join)


def test_unknown_and_conflicting_fail_closed() -> None:
    unknown = _obs(balance_freshness=TreasuryFreshnessSignalV1.UNKNOWN.value)
    recon = evaluate_treasury_read_only_reconciliation_v1(unknown)
    assert recon.reconciliation_class == TreasuryReconciliationClassV1.UNKNOWN.value
    assert recon.fail_closed is True

    first = evaluate_treasury_read_only_reconciliation_v1(_obs())
    second = evaluate_treasury_read_only_reconciliation_v1(
        _obs(evidence_id="tevidence-phase2-other")
    )
    assert first.evidence_fingerprint == second.evidence_fingerprint
    assert second.reconciliation_class == TreasuryReconciliationClassV1.AMBIGUOUS.value


def test_duplicate_evidence_is_idempotent() -> None:
    observation = _obs()
    first = evaluate_treasury_read_only_reconciliation_v1(observation)
    second = evaluate_treasury_read_only_reconciliation_v1(observation)
    assert first == second


def test_treasury_not_in_full_core_interference_proof() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
    assert "treasury_phase_2" not in "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path(__file__).resolve().parents[2] / "src/ops/full_core_live_path_composition_root_v1"
        ).glob("*.py")
        if path.name != "treasury_interference_proof_v1.py"
    )
