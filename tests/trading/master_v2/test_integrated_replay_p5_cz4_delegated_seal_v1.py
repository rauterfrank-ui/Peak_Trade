"""P5.1 CZ-4 delegated replay skips integrated I-1..I-3 writers when seal valid."""

from __future__ import annotations

from unittest.mock import patch

from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    initialize_canonical_scope,
    SCOPE_INITIALIZATION_POLICY_VERSION,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    ScopeEventGeneratorPolicyV1,
)
from trading.master_v2.integrated_offline_replay_p5_cz4_delegation_v1 import (
    P5_CZ4_DELEGATION_REASON,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.layered_core_authority_seal_v1 import build_layered_core_authority_seal_v1
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _EPOCH,
    _INSTRUMENT,
    _market_context,
    _replay_input,
)


def _existing_scope():
    ctx = _market_context()
    policy = CanonicalScopeInitializationPolicyV1(
        min_scope_band=50.0,
        max_scope_band=500.0,
        policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
    )
    prereq = ScopeInitializationPrerequisitesV1(
        required_window_complete=True,
        instrument_metadata_valid=True,
        finalized_market_context=True,
    )
    init = initialize_canonical_scope(
        ctx,
        policy,
        prereq,
        reinitialization_guard=ScopeReinitializationGuardV1(),
    )
    assert init.scope is not None
    return init.scope


def _valid_seal():
    return build_layered_core_authority_seal_v1(
        seal_id="seal-test-001",
        instrument_id=_INSTRUMENT,
        episode_snapshot_id="e" * 64,
        store_manifest_digest="f" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BULL,
        nullline_price=3500.0,
        d_t=200.0,
        r_t=3500.0,
        cm_t=5.0,
        switch_condition_met=False,
        mechanical_step_count=1,
    )


@patch("trading.master_v2.integrated_offline_trading_logic_replay_v1.transition_state")
@patch(
    "trading.master_v2.integrated_offline_trading_logic_replay_v1.generate_deterministic_scope_event"
)
@patch("trading.master_v2.integrated_offline_trading_logic_replay_v1.update_dynamic_boundaries")
@patch("trading.master_v2.integrated_offline_trading_logic_replay_v1.initialize_canonical_scope")
def test_delegated_replay_skips_i1_i3_writers(
    mock_init_scope,
    mock_update_boundaries,
    mock_generate_event,
    mock_transition,
) -> None:
    seal = _valid_seal()
    inp = _replay_input(
        existing_scope=_existing_scope(),
        layered_core_authority_seal=seal,
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    mock_init_scope.assert_not_called()
    mock_update_boundaries.assert_not_called()
    mock_generate_event.assert_not_called()
    mock_transition.assert_not_called()
    assert result.evidence is not None
    assert result.intermediate is not None
    assert result.intermediate.state_switch.transition_reason_code == P5_CZ4_DELEGATION_REASON


def test_invalid_seal_fail_closed() -> None:
    seal = _valid_seal()
    bad = seal.__class__(**{**seal.__dict__, "seal_digest": "0" * 64})
    inp = _replay_input(existing_scope=_existing_scope(), layered_core_authority_seal=bad)
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.replay_pass is False
    assert "seal_digest_mismatch" in result.fail_reasons


def test_baseline_replay_without_seal_unchanged() -> None:
    baseline = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert baseline.evidence is not None
