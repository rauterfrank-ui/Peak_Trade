"""Synthetic treasury STEP-29P handoff fixture for productive join contract tests."""

from __future__ import annotations

from dataclasses import replace

from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    CurrentProductiveTreasurySingleSourceCapitalHandoffV1,
    build_default_full_core_u04_p01_eligibility_host_inputs_v1,
    execute_current_productive_treasury_single_source_capital_handoff_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    CurrentProductiveUsdcFreeMarginObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import NUMERIC_EQUITY_TTL_SECONDS
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _balance_payload,
    _bound,
    _enter_replay,
    _host_enter_cycle,
)


def build_synthetic_treasury_handoff_v1(
    *,
    avail_eq: str = "12345.67",
    decision_epoch: str = EPOCH,
) -> CurrentProductiveTreasurySingleSourceCapitalHandoffV1:
    """Treasury single-source handoff using the same synthetic margin path as enter-live tests."""
    bound = _bound()
    instrument_id = str(bound.instrument_id or DEFAULT_INSTRUMENT_ID)
    body_sha = "b" * 64
    observation = CurrentProductiveUsdcFreeMarginObservationV1(
        fact_id=OBSERVATION_FACT_ID,
        surface=OBSERVATION_SURFACE,
        value=str(avail_eq),
        settlement_currency="USDC",
        selected_ccy="USDC",
        bound_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=decision_epoch,
        observed_at_as_of=decision_epoch,
        age_seconds="1",
        freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
        provenance_digest=body_sha,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )
    return execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=observation,
        instrument_id=instrument_id,
        body_sha256=body_sha,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        u04_p01_host_inputs=build_default_full_core_u04_p01_eligibility_host_inputs_v1(
            raw_acct_lv="2",
        ),
        clear_treasury_idempotency=True,
    )


def build_synthetic_enter_live_replay_v1():
    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    return replace(replay, evidence=replace(replay.evidence, decision_outcome="enter_long"))


def synthetic_balance_payload_v1(*, avail_eq: str) -> dict[str, object]:
    return _balance_payload(avail_eq=avail_eq)
