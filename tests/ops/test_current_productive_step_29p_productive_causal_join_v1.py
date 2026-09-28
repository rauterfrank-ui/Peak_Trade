"""STEP-29P → EEA acquisition and portfolio budget productive causal joins."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_step_29p_to_eea_acquisition_productive_join_v1 import (
    CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE,
    JOIN_SEAM_ID as EEA_JOIN_SEAM,
    Step29pToEeaAcquisitionProductiveJoinRequestV1,
    join_step_29p_admitted_capital_into_eea_universe_acquisition_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_step_29p_to_portfolio_budget_productive_join_v1 import (
    JOIN_SEAM_ID as BUDGET_JOIN_SEAM,
    join_step_29p_handoff_into_portfolio_capital_reservation_budget_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from tests.ops._synthetic_treasury_step29p_handoff_fixture_v1 import (
    build_synthetic_treasury_handoff_v1,
)
from tests.ops.test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_MARK_PRICE,
    FakeEeaPublicUniverseGetTransportV1,
    _marks,
    _okx_envelope,
)


def _fake_transport() -> FakeEeaPublicUniverseGetTransportV1:
    rows = [
        {
            "instId": "ETH-USDT-SWAP",
            "instType": "SWAP",
            "state": "live",
            "baseCcy": "ETH",
            "quoteCcy": "USDT",
            "settleCcy": "USDT",
            "ctType": "linear",
            "ctVal": "0.01",
            "ctValCcy": "ETH",
            "tickSz": "0.01",
            "lotSz": "1",
            "minSz": "1",
            "uly": "ETH-USDT",
        }
    ]
    return FakeEeaPublicUniverseGetTransportV1(
        {
            (ENDPOINT_PUBLIC_INSTRUMENTS, "FUTURES"): _okx_envelope(rows=rows),
            (ENDPOINT_PUBLIC_MARK_PRICE, "FUTURES"): _marks(rows),
            (ENDPOINT_PUBLIC_INSTRUMENTS, "SWAP"): _okx_envelope(rows=rows),
            (ENDPOINT_PUBLIC_MARK_PRICE, "SWAP"): _marks(rows),
        }
    )


def _request(
    *, handoff, e2e_run_id: str = "e2e-test-join"
) -> Step29pToEeaAcquisitionProductiveJoinRequestV1:
    return Step29pToEeaAcquisitionProductiveJoinRequestV1(
        handoff=handoff,
        e2e_run_id=e2e_run_id,
        capital_lineage_class=CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE,
        expected_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
        expected_instrument_id=str(handoff.step_29p_claim.expected_instrument_id),
    )


def test_eea_join_stamps_lineage_after_valid_29p_admission() -> None:
    handoff = build_synthetic_treasury_handoff_v1()
    assert handoff.step_29p_admissibility.risk_admissible is True
    result = join_step_29p_admitted_capital_into_eea_universe_acquisition_v1(
        _request(handoff=handoff),
        transport=_fake_transport(),
        observed_at="2026-09-28T05:00:00Z",
    )
    assert result.ok is True
    assert result.join_seam_id == EEA_JOIN_SEAM
    assert result.acquisition is not None
    prov = result.acquisition.provenance
    assert prov["STEP_29P_LINEAGE_BINDING_DIGEST"] == result.lineage_binding_digest
    assert prov["STEP_29P_PRODUCER_INPUT_SET_DIGEST"] == handoff.producer_output.input_set_digest
    assert prov["E2E_RUN_ID"] == "e2e-test-join"
    assert prov["SYNTHETIC_TEST_VALUE_HAS_PRODUCTIVE_AUTHORITY"] == "false"


def test_eea_join_fail_closed_without_risk_admission() -> None:
    handoff = build_synthetic_treasury_handoff_v1()
    bad = replace(
        handoff,
        step_29p_admissibility=replace(
            handoff.step_29p_admissibility,
            risk_admissible=False,
            reason_codes=("FORCED_TEST_DENY",),
        ),
    )
    result = join_step_29p_admitted_capital_into_eea_universe_acquisition_v1(
        _request(handoff=bad),
        transport=_fake_transport(),
    )
    assert result.ok is False
    assert result.acquisition is None
    assert "STEP_29P_NOT_RISK_ADMISSIBLE" in result.reason_codes


def test_portfolio_budget_bind_from_same_handoff() -> None:
    handoff = build_synthetic_treasury_handoff_v1(avail_eq="12345.67")
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    bound = join_step_29p_handoff_into_portfolio_capital_reservation_budget_v1(
        handoff=handoff,
        owner=owner,
        e2e_run_id="e2e-budget",
    )
    assert bound.ok is True
    assert bound.join_seam_id == BUDGET_JOIN_SEAM
    assert bound.admitted_budget == "12345.67"
    state = owner.budget_state_v1()
    assert state.admitted is True


def test_portfolio_budget_fail_closed_on_missing_epoch() -> None:
    handoff = build_synthetic_treasury_handoff_v1()
    bad_output = replace(handoff.producer_output, decision_epoch="")
    bad = replace(handoff, producer_output=bad_output)
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    bound = join_step_29p_handoff_into_portfolio_capital_reservation_budget_v1(
        handoff=bad,
        owner=owner,
        e2e_run_id="e2e-budget",
    )
    assert bound.ok is False
    assert owner.budget_state_v1().admitted is False
