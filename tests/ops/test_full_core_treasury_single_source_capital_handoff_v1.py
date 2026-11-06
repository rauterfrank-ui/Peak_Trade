"""Full-Core Treasury single-source capital handoff + enter-live integration."""

from __future__ import annotations

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT,
    TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE,
    execute_current_productive_treasury_single_source_capital_handoff_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import NUMERIC_EQUITY_TTL_SECONDS
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    CurrentProductiveUsdcFreeMarginObservationV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_bounded_full_core_reachability_v1 as prove_bounded,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1 import (
    C08_PRODUCTIVE_BINDING_AUTHORIZED,
    C08_PRODUCTIVE_BINDING_IMPLEMENTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    _balance_payload,
    _enter_replay,
    _host_enter_cycle,
    _injected,
    _join,
)


def test_standing_pins_and_bounded_reachability() -> None:
    assert FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT == 1
    assert TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE is False
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS == "BOUND"
    assert C08_PRODUCTIVE_BINDING_AUTHORIZED is True
    assert C08_PRODUCTIVE_BINDING_IMPLEMENTED is True
    proof = prove_bounded()
    assert proof["ok"] is True
    assert proof["TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY"] is True
    assert proof["TREASURY_MUTATION_AUTHORIZED"] is False
    assert proof["TREASURY_CAN_OVERRIDE_WIRE_SEND_PERMISSION"] is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1


def test_enter_live_uses_single_source_treasury_handoff() -> None:
    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    result = _join(replay=replay, injected=_injected(payload=_balance_payload()))
    assert result.decision_class == "ENTER"
    assert result.get_count == 1
    assert result.status == "PASS"
    assert result.producer_output_value != ""
    assert result.step_29p_risk_admissible == "true"


def _minimal_margin_observation_v1() -> CurrentProductiveUsdcFreeMarginObservationV1:
    body_sha = "c" * 64
    return CurrentProductiveUsdcFreeMarginObservationV1(
        fact_id=OBSERVATION_FACT_ID,
        surface=OBSERVATION_SURFACE,
        value="1000",
        settlement_currency="USDC",
        selected_ccy="USDC",
        bound_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=EPOCH,
        observed_at_as_of=EPOCH,
        age_seconds="1",
        freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
        provenance_digest=body_sha,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )


def test_treasury_handoff_fail_closed_without_u01_witness_host_inputs() -> None:
    handoff = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=_minimal_margin_observation_v1(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        body_sha256="c" * 64,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        u04_p01_host_inputs=None,
        clear_treasury_idempotency=True,
    )
    assert handoff.fail_closed is True
    assert "U01_WITNESS_REQUIRED_NO_IMPLICIT_ACCT_LV_DEFAULT" in handoff.reason_codes


def test_treasury_handoff_fail_closed_on_empty_u01_raw_acct_lv_witness() -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
        build_default_full_core_u04_p01_eligibility_host_inputs_v1,
    )

    handoff = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=_minimal_margin_observation_v1(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        body_sha256="c" * 64,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        u04_p01_host_inputs=build_default_full_core_u04_p01_eligibility_host_inputs_v1(
            raw_acct_lv="",
        ),
        clear_treasury_idempotency=True,
    )
    assert handoff.fail_closed is True
    assert "U01_RAW_ACCT_LV_WITNESS_MISSING" in handoff.reason_codes


def test_stale_age_fails_closed() -> None:
    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    result = _join(
        replay=replay,
        injected=_injected(payload=_balance_payload(), age_seconds="99999"),
    )
    assert result.status in {"STALE", "FAIL", "UNKNOWN"}
    assert result.producer_output_status != "PRODUCED"
