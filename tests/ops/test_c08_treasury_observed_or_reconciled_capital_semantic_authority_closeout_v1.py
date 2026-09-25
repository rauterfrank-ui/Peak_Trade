"""C08 treasury capital semantic authority closeout. No productive binding."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    RISK_SIZING_OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1 import (
    AUTHORITY_EFFECT,
    C08_ABSENT_BEHAVIOR,
    C08_CONFLICTED_BEHAVIOR,
    C08_CURRENT_BINDING,
    C08_INCREASE_ELIGIBILITY,
    C08_INPUT_CLASS,
    C08_PRODUCTIVE_BINDING_AUTHORIZED,
    C08_PRODUCTIVE_BINDING_IMPLEMENTED,
    C08_SEMANTIC_CLOSEOUT,
    C08_STALE_BEHAVIOR,
    C08_UNKNOWN_BEHAVIOR,
    C08_PROPOSED_CONSUMER,
    CURRENT_ACCOUNT_EQUITY_OWNER,
    CURRENT_RISK_ADMISSIBILITY_OWNER,
    CURRENT_SIZING_OWNER,
    NEXT_PRODUCTIVE_BLOCKER,
    OBSERVED_CAPITAL_SIZING_INCREASE_ALLOWED,
    RECONCILED_CAPITAL_SIZING_INCREASE_ALLOWED,
    RISK_ADMISSIBLE_CAPITAL_SIZING_INCREASE_ALLOWED,
    adjudicate_c08_adversarial_semantic_case_v1,
    build_c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1,
    c08_adversarial_semantic_matrix_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.join_v1 import (
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryInternalTransferSignalV1,
    TreasuryReconciliationClassV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.context_v1 import (
    TreasuryCapitalDepositObservationContextV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_from_funding_balance_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    parse_funding_account_balance_observation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC = (
    REPO_ROOT
    / "docs/ops/specs/C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_SEMANTIC_AUTHORITY_CLOSEOUT_V1.md"
)
_TS = "2026-09-21T01:16:57Z"
_ACCOUNT = "okx-eea-uid:6672-fixture"
_INSTRUMENT = "ETH-USDT-SWAP"


def test_closeout_contract_and_runbook_tokens() -> None:
    contract = (
        build_c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1(
            c08_semantic_authority_closeout_contract_id="C08_CLOSEOUT_FIXTURE_001",
        )
    )
    assert contract.c08_semantic_closeout == "CLOSED"
    assert contract.c08_productive_binding_authorized is True
    assert contract.c08_productive_binding_implemented is True
    assert contract.c08_semantic_authority_closeout_contract_authority_effect == "NONE"
    assert AUTHORITY_EFFECT == "NONE"
    assert C08_SEMANTIC_CLOSEOUT == "CLOSED"
    assert C08_INPUT_CLASS == contract.c08_input_class
    assert C08_INCREASE_ELIGIBILITY == contract.c08_increase_eligibility
    for behavior in (
        C08_UNKNOWN_BEHAVIOR,
        C08_STALE_BEHAVIOR,
        C08_ABSENT_BEHAVIOR,
        C08_CONFLICTED_BEHAVIOR,
    ):
        assert behavior == "FAIL_CLOSED"

    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert "C08_SEMANTIC_CLOSEOUT=CLOSED" in runbook
    assert "C08_PRODUCTIVE_BINDING_AUTHORIZED=true" in runbook
    assert "C08_PRODUCTIVE_BINDING_IMPLEMENTED=true" in runbook
    assert "C08_OBSERVED_CAPITAL_ALLOWED_AS_SIZING_SOURCE=false" in runbook
    assert "C08_RECONCILED_CAPITAL_ALLOWED_AS_SIZING_SOURCE=false" in runbook
    spec = SPEC.read_text(encoding="utf-8")
    assert "C08_SEMANTIC_CLOSEOUT=CLOSED" in spec
    assert C08_CURRENT_BINDING == "BOUND"
    assert C08_PRODUCTIVE_BINDING_AUTHORIZED is True
    assert C08_PRODUCTIVE_BINDING_IMPLEMENTED is True
    assert "TRUSTED_29P" in NEXT_PRODUCTIVE_BLOCKER or "SIZING_SOURCE" in NEXT_PRODUCTIVE_BLOCKER


def test_authority_owners_unchanged() -> None:
    assert CURRENT_SIZING_OWNER == "capital_risk_admissibility_owner_v1"
    assert CURRENT_RISK_ADMISSIBILITY_OWNER == "capital_risk_admissibility_owner_v1"
    assert RISK_SIZING_OWNER == CURRENT_SIZING_OWNER
    assert CURRENT_ACCOUNT_EQUITY_OWNER == ACCOUNT_EQUITY_AUTHORITY_OWNER
    assert C08_PROPOSED_CONSUMER.startswith("CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1")
    assert OBSERVED_CAPITAL_SIZING_INCREASE_ALLOWED is False
    assert RECONCILED_CAPITAL_SIZING_INCREASE_ALLOWED is False
    assert RISK_ADMISSIBLE_CAPITAL_SIZING_INCREASE_ALLOWED is True


def test_adversarial_semantic_matrix() -> None:
    matrix = c08_adversarial_semantic_matrix_v1()
    assert len(matrix) == 12
    for case in matrix:
        if case.case_id in {
            "D_risk_admissible_fresh",
        }:
            assert case.increase_allowed is True
            assert case.risk_admissible is True
        else:
            assert case.increase_allowed is False
        if case.case_id == "C_reconciled_not_risk_admissible":
            assert case.treasury_reconciled is True
            assert case.risk_admissible is False
            assert case.fail_closed is False
        if case.case_id == "B_observed_reconciliation_unknown":
            assert case.fail_closed is True
            assert case.treasury_reconciliation_class == "UNKNOWN"

    case_b = adjudicate_c08_adversarial_semantic_case_v1("B_observed_reconciliation_unknown")
    assert case_b.decrease_or_block_allowed is True
    with pytest.raises(ValueError, match="C08_ADVERSARIAL_CASE_UNKNOWN"):
        adjudicate_c08_adversarial_semantic_case_v1("Z_invalid")


def test_6672_style_host_join_regression_unchanged() -> None:
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
        evidence_id="tevidence-6672-closeout",
        account_identity=_ACCOUNT,
        instrument_id=_INSTRUMENT,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.UNCONFIRMED.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.UNKNOWN.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw="",
        cached_trading_capital_raw="",
    )
    observation = build_treasury_venue_observation_from_funding_balance_v1(funding, ctx)
    result = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        observation,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
        usdc_row_status=CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    )
    host = result.host_evaluation
    assert host.usdc_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    assert host.treasury_reconciliation_status == TreasuryReconciliationClassV1.UNKNOWN.value
    assert host.fail_closed is True
    assert host.treasury_capital_admitted is False
    assert host.observed_equity_minted is False
    assert host.reconciled_equity_minted is False
    assert host.risk_admissible_mint is False
    assert host.sizing_authority_changed is False
