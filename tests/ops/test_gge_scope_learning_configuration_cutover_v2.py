"""Both distance configurations: real replay consumers and isolated learning lineage."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1 import (
    derive_productive_n_bars_evaluation_identity_v1,
    produce_n_bars_evaluation_runtime_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    derive_learning_state_scope_id_v1,
    ingest_evaluation_bundle_into_learning_state_v1,
    reduce_learning_state_transition_v1,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    resolve_current_productive_live_29p_adverse_exit_distance_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_ddo_learning_capture_join_v1 import (
    productive_scope_learning_config_hash_v1,
    run_integrated_offline_replay_with_productive_ddo_capture_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_learning_outcome_evidence_ingest_host_binding_v1 import (
    apply_learning_state_feedback_to_next_cycle_v1,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeInitializationPolicyV1,
    default_instrument_relative_scope_initialization_policy_v1,
)
from trading.master_v2.double_play_state import RuntimeScopeState, SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.layered_core_authority_seal_v1 import build_layered_core_authority_seal_v1
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _snapshot
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _market_context,
    _replay_input,
)


def _input(price=0.02, side=SideState.LONG_ACTIVE, *, raw=True):
    ctx = _market_context(
        mark_price=price,
        index_price=price,
        best_bid=price * 0.999,
        best_ask=price * 1.001,
        spread=price * 0.002,
        volatility_estimate=0.02,
    )
    inp = _replay_input(
        canonical_market_context=ctx,
        current_price=price,
        price_path=(price, price),
        side_state=side,
    )
    if raw:
        policy = default_instrument_relative_scope_initialization_policy_v1()
        inp = replace(
            inp,
            policies=replace(inp.policies, scope_initialization=policy),
            policy_versions={**inp.policy_versions, "scope_initialization": policy.policy_version},
        )
    else:
        policy = CanonicalScopeInitializationPolicyV1(50.0, 500.0)
        inp = replace(
            inp,
            policies=replace(inp.policies, scope_initialization=policy),
            policy_versions={**inp.policy_versions, "scope_initialization": policy.policy_version},
        )
    return inp


@pytest.mark.parametrize("price", [0.00001, 0.02, 1.0, 100.0, 50000.0, 100000.0])
@pytest.mark.parametrize(
    "side", [SideState.LONG_ACTIVE, SideState.SHORT_ACTIVE, SideState.LONG_ARMED_NEUTRAL_START]
)
def test_full_replay_uses_raw_gge_in_scope_events_and_protective_distance(price, side):
    result = run_integrated_offline_trading_logic_replay_v1(_input(price, side))
    assert result.intermediate is not None, result.fail_reasons
    intermediate = result.intermediate
    assert intermediate.runtime_scope_state_after.current_hysteresis_band == pytest.approx(
        price * 0.02
    )
    effective = intermediate.scope_event.semantic_binding.adverse_exit_distance
    distance, reasons = resolve_current_productive_live_29p_adverse_exit_distance_v1(result)
    assert reasons == ()
    assert distance == effective
    assert distance < price  # Small-price stop geometry remains possible.


def test_legacy_scope_is_not_an_executable_double_play_configuration():
    raw, legacy = _input(), _input(raw=False)
    a = run_integrated_offline_trading_logic_replay_v1(raw)
    b = run_integrated_offline_trading_logic_replay_v1(legacy)
    assert a.intermediate is not None
    assert a.intermediate.runtime_scope_state_after.current_hysteresis_band < 1
    assert b.intermediate is None
    assert "fixed_scope_policy_retired" in b.fail_reasons
    assert productive_scope_learning_config_hash_v1(
        raw
    ) != productive_scope_learning_config_hash_v1(legacy)


@pytest.mark.parametrize(
    "side", [SideState.LONG_ACTIVE, SideState.SHORT_ACTIVE, SideState.LONG_ARMED_NEUTRAL_START]
)
def test_restored_legacy_band_cannot_override_raw_magnitude(side):
    inp = _input(side=side)
    restored = RuntimeScopeState(
        anchor_price=0.02,
        current_hysteresis_band=50.0,
        current_upscope_boundary=50.02,
        current_downscope_boundary=-49.98,
    )
    result = run_integrated_offline_trading_logic_replay_v1(
        replace(
            inp,
            runtime_scope_state=restored,
            runtime_scope_bound_instrument_id=inp.instrument_id,
        )
    )
    assert result.intermediate is not None
    assert result.intermediate.runtime_scope_state_after.current_hysteresis_band == pytest.approx(
        0.0004
    )


def _capture_and_evaluate(tmp_path, *, raw):
    inp = _input()
    if not raw:
        # A second current configuration tests isolation; retired fixed Scope
        # is no longer executable even as a comparison Double-Play path.
        inp = replace(inp, config_digest="b" * 64)
    binding = DdoCaptureBindingV0(ledger_path=tmp_path / "capture.jsonl")
    result, summary = run_integrated_offline_replay_with_productive_ddo_capture_v1(
        inp,
        ddo_capture_binding=binding,
        repository_sha="a" * 40,
        session_id="scope-cutover-session",
        cycle_index=1,
        event_ts_unix=1788264000.0,
        observation_acceptance_result=None,
        features=None,
        confirmation_binding=None,
    )
    assert result.intermediate is not None and summary["ok"]
    decision = next(
        r
        for r in binding.captured_records
        if r.get("producer_id") == "deterministic_scope_event_generator_v1"
    )
    assert decision["code_sha"] != "UNKNOWN"
    assert decision["config_hash"] == productive_scope_learning_config_hash_v1(inp)
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(
        decision,
        _snapshot(decision_event_ref=decision["record_id"]),
        economic_score="OBSERVED_LABEL",
    )
    identity = derive_productive_n_bars_evaluation_identity_v1(
        decision_record_id=decision["record_id"],
        evaluation_time_utc="2026-09-01T14:00:00Z",
        correlation_id=decision["correlation_id"],
        code_sha=decision["code_sha"],
        config_hash=decision["config_hash"],
    )
    evaluated = produce_n_bars_evaluation_runtime_bundle_v1(
        horizon, decision, identity, ledger=binding.ledger()
    )
    return binding, evaluated["bundle"]


def test_captured_configuration_survives_outcome_learning_and_export_without_pool_mixing(tmp_path):
    binding_a, a = _capture_and_evaluate(tmp_path, raw=True)
    _, b = _capture_and_evaluate(tmp_path, raw=False)
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "capture.jsonl")
    states = []
    for bundle in (a, b):
        outcome = bundle["outcome_record"]
        scope = derive_learning_state_scope_id_v1(
            session_id="same-session",
            config_hash=outcome["config_hash"],
            code_sha=outcome["code_sha"],
        )
        ingested = ingest_evaluation_bundle_into_learning_state_v1(
            ledger,
            state_scope_id=scope,
            outcome=outcome,
            attribution=bundle["attribution_record"],
            counterfactual=bundle["counterfactual_record"],
            event_time_utc=outcome["event_time_utc"],
            correlation_id=outcome["correlation_id"],
        )["learning_state_record"]
        assert ingested["config_hash"] == outcome["config_hash"]
        exported = export_learning_evidence_from_state_v1(ingested)
        assert exported["config_hash"] == outcome["config_hash"]
        assert exported["code_sha"] == outcome["code_sha"]
        states.append(ingested)
    assert states[0]["state_scope_id"] != states[1]["state_scope_id"]
    assert all(s["state_version"] == 1 for s in states)
    with pytest.raises(DdoValidationError, match="CONFIGURATION_POOL_MISMATCH"):
        reduce_learning_state_transition_v1(
            state_scope_id=states[0]["state_scope_id"],
            prior_state=states[0],
            bundle={
                "outcome": b["outcome_record"],
                "attribution": b["attribution_record"],
                "counterfactual": b["counterfactual_record"],
            },
            record_id="ls.cross.mode0001",
            event_time_utc=b["outcome_record"]["event_time_utc"],
            correlation_id="cross.mode.correlation",
            cycle_id=None,
        )
    state = SimpleNamespace(
        last_ddo_learning_state=states[1],
        ddo_capture_binding=binding_a,
        ddo_n_bars_economic_score="UNCHANGED",
    )
    apply_learning_state_feedback_to_next_cycle_v1(state)
    assert state.ddo_n_bars_economic_score == "UNCHANGED"
    state.last_ddo_learning_state = states[0]
    apply_learning_state_feedback_to_next_cycle_v1(state)
    assert state.ddo_n_bars_economic_score == "OBSERVED_LABEL"


def test_unknown_historical_feedback_is_not_admitted(tmp_path):
    state = SimpleNamespace(
        last_ddo_learning_state={
            "config_hash": "UNKNOWN",
            "code_sha": "UNKNOWN",
            "next_cycle_economic_score_label": "OLD_LABEL",
        },
        ddo_capture_binding=DdoCaptureBindingV0(),
        ddo_n_bars_economic_score="CURRENT",
    )
    apply_learning_state_feedback_to_next_cycle_v1(state)
    assert state.ddo_n_bars_economic_score == "CURRENT"


def test_delegated_distance_is_the_sealed_distance_despite_a_stale_legacy_carrier():
    from tests.trading.master_v2.test_integrated_replay_p5_cz4_delegated_seal_v1 import (
        _existing_scope,
    )

    inp = _input()
    seal = build_layered_core_authority_seal_v1(
        seal_id="seal-small-price-cutover",
        instrument_id=inp.instrument_id,
        episode_snapshot_id="e" * 64,
        store_manifest_digest="f" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BULL,
        nullline_price=0.02,
        d_t=0.0004,
        r_t=0.02,
        cm_t=0.0,
        switch_condition_met=False,
        mechanical_step_count=1,
    )
    result = run_integrated_offline_trading_logic_replay_v1(
        replace(
            inp,
            existing_scope=_existing_scope(),
            layered_core_authority_seal=seal,
            runtime_scope_state=RuntimeScopeState(
                anchor_price=3500.0, current_hysteresis_band=50.0
            ),
        )
    )
    assert result.intermediate is not None, result.fail_reasons
    st = result.intermediate.runtime_scope_state_after
    assert st.current_hysteresis_band == 0.0004
    assert st.anchor_price == 0.02
    assert result.intermediate.scope_event.semantic_binding.adverse_exit_distance < 0.02


def test_export_cannot_relabel_historical_state_as_another_configuration(tmp_path):
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    with pytest.raises(DdoValidationError, match="SOURCE_CONFIGURATION_MISMATCH"):
        export_learning_evidence_from_state_v1(_learning_state(tmp_path), config_hash="f" * 64)


def test_configuration_identity_does_not_change_with_prices_or_restore():
    a, b = _input(0.02), _input(100000.0)
    assert productive_scope_learning_config_hash_v1(a) == productive_scope_learning_config_hash_v1(
        b
    )
    replay = run_integrated_offline_trading_logic_replay_v1(a)
    assert replay.intermediate is not None
    restored = replace(a, existing_scope=replay.intermediate.current_scope)
    assert productive_scope_learning_config_hash_v1(a) == productive_scope_learning_config_hash_v1(
        restored
    )


def test_mismatched_restored_scope_policy_is_rejected():
    from tests.trading.master_v2.test_integrated_replay_p5_cz4_delegated_seal_v1 import (
        _existing_scope,
    )

    result = run_integrated_offline_trading_logic_replay_v1(
        replace(_input(), existing_scope=_existing_scope())
    )
    assert not result.replay_pass
    assert "scope_policy_mismatch" in result.fail_reasons


def test_unversioned_chop_state_requires_migration_and_does_not_clear_the_latch():
    inp = _input()
    legacy = RuntimeScopeState(anchor_price=0.02, current_hysteresis_band=50.0, chop_latched=True)
    result = run_integrated_offline_trading_logic_replay_v1(
        replace(
            inp,
            runtime_scope_state=legacy,
            runtime_scope_bound_instrument_id=inp.instrument_id,
        )
    )
    assert not result.replay_pass
    assert "legacy_chop_scope_requires_explicit_policy_migration" in result.fail_reasons
    assert legacy.chop_latched


def test_raw_scope_mode_survives_persistence_round_trip():
    from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
        runtime_scope_state_from_dict,
        runtime_scope_state_to_dict,
    )

    result = run_integrated_offline_trading_logic_replay_v1(_input())
    assert result.intermediate is not None
    state = result.intermediate.runtime_scope_state_after
    restored = runtime_scope_state_from_dict(runtime_scope_state_to_dict(state))
    assert restored.scope_distance_mode == "gge_raw_v2"
    assert restored.current_hysteresis_band == state.current_hysteresis_band


def test_ghv_effective_magnitude_is_the_consumed_value_not_the_restored_band():
    inp = _input()
    result = run_integrated_offline_trading_logic_replay_v1(
        replace(
            inp,
            runtime_scope_state=RuntimeScopeState(anchor_price=0.02, current_hysteresis_band=50),
            runtime_scope_bound_instrument_id=inp.instrument_id,
        )
    )
    assert result.intermediate is not None
    assert result.intermediate.runtime_scope_state_before.current_hysteresis_band == 50
    assert result.intermediate.effective_scope_magnitude == pytest.approx(0.0004)
