"""E4: capital admission → account-equity orchestration ingress tests."""

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
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY,
    AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    EDGE_SEAM_ID,
    EXTERNAL_EFFECT_AUTHORIZED,
    NETWORK_ALLOWED,
    STEP_29P_MINT_AUTHORIZED,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.join_v1 import (
    assert_orchestration_never_mints_sizing_or_step_29p_v1,
    join_treasury_capital_admission_into_account_equity_orchestration_v1,
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
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
)

_ACCOUNT = "acct-treasury-e4-001"
_INSTRUMENT = "BTC-USDT-SWAP"
_TS = "2026-09-20T10:00:00Z"
_PACKAGE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/treasury_capital_admission_to_account_equity_orchestration_v1"
)


def _obs(**overrides) -> TreasuryVenueObservationV1:
    payload = {
        "evidence_id": "tevidence-e4-001",
        "evidence_fingerprint": "fp-e4-001",
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


def test_standing_constants_no_network_sizing_or_external_effect() -> None:
    assert EDGE_SEAM_ID == "TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_V1"
    assert NETWORK_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert STEP_29P_MINT_AUTHORIZED is False
    assert AVAILABLE_FOR_SIZING_MINT_AUTHORIZED is False
    assert ACCOUNT_EQUITY_AUTHORITY.endswith(
        "governed_productive_account_equity_authority_producer_v1"
    )
    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in _PACKAGE.glob("*.py")
        if path.name != "constants_v1.py"
    )
    assert "urllib.request" not in joined
    assert "produce_current_productive_29p_risk_capital_v1" not in joined


def test_at01_observed_increase_denies_orchestration_ingress() -> None:
    observation = _obs(
        venue_balance_raw="150",
        prior_reconciled_capital_raw="100",
        deposit_history_confirms_increase=False,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
    )
    treasury_join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    result = join_treasury_capital_admission_into_account_equity_orchestration_v1(treasury_join)
    ingress = result.ingress
    assert ingress.orchestration_admitted is False
    assert ingress.fail_closed is True
    assert ingress.treasury_reconciliation_class == TreasuryReconciliationClassV1.OBSERVED.value
    assert live_venue_capital_may_bind_step_29p_v1(ingress.capital_admission_evidence) is False
    assert_orchestration_never_mints_sizing_or_step_29p_v1(result)


def test_reconciled_capital_increase_defers_to_account_equity_orchestration() -> None:
    observation = _obs(
        venue_balance_raw="150",
        prior_reconciled_capital_raw="100",
    )
    treasury_join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert treasury_join.reconciliation.reconciliation_class == (
        TreasuryReconciliationClassV1.RECONCILED.value
    )
    evidence = treasury_join.capital_admission_evidence
    assert evidence.evidence_status == CapitalAdmissionStatusV1.CONTRADICTORY.value
    assert "CAPITAL_INCREASE_NOT_AUTO_ADMITTED" in evidence.reason_codes

    result = join_treasury_capital_admission_into_account_equity_orchestration_v1(treasury_join)
    ingress = result.ingress
    assert ingress.orchestration_admitted is True
    assert ingress.fail_closed is False
    assert "CAPITAL_INCREASE_DEFERRED_TO_ACCOUNT_EQUITY_ORCHESTRATION" in ingress.reason_codes
    assert ingress.capital_admission_evidence.risk_admissible is False
    assert (
        ingress.capital_admission_evidence.capital_authority_class
        != CAPITAL_AUTHORITY_RISK_ADMISSIBLE
    )
    assert live_venue_capital_may_bind_step_29p_v1(ingress.capital_admission_evidence) is False
    assert_orchestration_never_mints_sizing_or_step_29p_v1(result)


def test_reconciled_stable_capital_trusted_present_admits_ingress() -> None:
    observation = _obs(
        venue_balance_raw="100",
        deposit_history_confirms_increase=False,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.MISSING.value,
    )
    treasury_join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    assert treasury_join.capital_admission_evidence.evidence_status == (
        CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
    )
    result = join_treasury_capital_admission_into_account_equity_orchestration_v1(treasury_join)
    ingress = result.ingress
    assert ingress.orchestration_admitted is True
    assert ingress.fail_closed is False
    assert_orchestration_never_mints_sizing_or_step_29p_v1(result)


def test_treasury_interference_proof_still_passes() -> None:
    proof = prove_treasury_interference_absent_v1()
    assert proof["ok"] is True
