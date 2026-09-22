"""P3 durable L1–L10 episode state: roundtrip, restart parity, fail-closed guards."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    AUTHORITY_CUTOVER_OCCURRED,
    EXTERNAL_EFFECT_AUTHORIZED,
    LEGACY_SEMANTIC_FALLBACK_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NakedLayeredCoreDurableStateError,
    PRODUCTIVE_BINDING_AUTHORIZED,
    SNAPSHOT_SCHEMA_VERSION,
    assert_no_legacy_semantic_fields_v1,
    atomic_persist_episode_v1,
    episode_from_snapshot_v1,
    episode_to_snapshot_v1,
    execute_naked_layered_core_mechanical_step_v1,
    initialize_naked_layered_core_episode_v1,
    restore_episode_from_store_v1,
    roundtrip_episode_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    ExplicitPassthroughDynamicScopeGeneratorV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
    orchestrate_naked_layered_core_v1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1


def _key() -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="BTC-PERP",
        venue_instrument_id="BTC-USDT-SWAP",
    )


def _selected() -> SelectedFutureInputV1:
    k = _key()
    return SelectedFutureInputV1(instrument_id=k.canonical_instrument_id, instrument_key=k)


def _cand(*, t: float, mark: float) -> ObservationCandidateV1:
    k = _key()
    return ObservationCandidateV1(
        venue=k.venue,
        canonical_instrument_id=k.canonical_instrument_id,
        venue_instrument_id=k.venue_instrument_id,
        venue_event_time=t,
        mark_price=mark,
    )


def _init_episode(*, with_first_step: bool = True):
    gen = ExplicitPassthroughDynamicScopeGeneratorV1()
    step = (
        MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=50.0) if with_first_step else None
    )
    episode, _ = initialize_naked_layered_core_episode_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=110.0)],
        first_mechanical_step=step,
        scope_generator=gen,
    )
    return episode, gen


def test_roundtrip_codec() -> None:
    episode, _ = _init_episode()
    restored = roundtrip_episode_v1(episode)
    assert restored == episode


def test_atomic_persist_restore_restart_parity(tmp_path: Path) -> None:
    episode, gen = _init_episode(with_first_step=True)
    atomic_persist_episode_v1(tmp_path, episode)
    restored = restore_episode_from_store_v1(tmp_path, expected_instrument_id="BTC-PERP")
    step2 = MechanicalStepSpecV1(mark_price_m_t=95.0, proposed_d_t=5.0)
    r1 = execute_naked_layered_core_mechanical_step_v1(
        episode=restored, step=step2, scope_generator=gen
    )
    assert not r1.fail_closed
    full = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=110.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=50.0),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
        follow_on_steps=[step2],
    )
    assert not full.fail_closed
    assert r1.regime_post is full.final_regime
    assert r1.r_t_post == pytest.approx(full.final_running_r_t or 0.0)
    assert restored.nullline.nullline_price == pytest.approx(full.final_nullline_price or 0.0)


def test_corrupt_snapshot_reject(tmp_path: Path) -> None:
    episode, _ = _init_episode()
    atomic_persist_episode_v1(tmp_path, episode)
    path = tmp_path / "naked_layered_core_episode_v1.json"
    path.write_text(path.read_text().replace("BTC-PERP", "BTC-PERP-X"), encoding="utf-8")
    with pytest.raises(NakedLayeredCoreDurableStateError, match="MANIFEST_DIGEST_MISMATCH"):
        restore_episode_from_store_v1(tmp_path)


def test_partial_missing_field_reject() -> None:
    episode, _ = _init_episode()
    snap = episode_to_snapshot_v1(episode)
    del snap["nullline"]
    with pytest.raises(NakedLayeredCoreDurableStateError, match="SNAPSHOT_MISSING_FIELDS"):
        episode_from_snapshot_v1(snap)


def test_unknown_schema_version_reject() -> None:
    episode, _ = _init_episode()
    snap = episode_to_snapshot_v1(episode)
    snap["schema_version"] = "v999"
    with pytest.raises(NakedLayeredCoreDurableStateError, match="SCHEMA_VERSION_UNKNOWN"):
        episode_from_snapshot_v1(snap)


def test_selected_future_mismatch_reject() -> None:
    episode, _ = _init_episode()
    snap = episode_to_snapshot_v1(episode)
    with pytest.raises(NakedLayeredCoreDurableStateError, match="SELECTED_FUTURE_MISMATCH"):
        episode_from_snapshot_v1(snap, expected_instrument_id="ETH-PERP")


def test_nullline_continuity_across_steps() -> None:
    episode, gen = _init_episode()
    frozen = episode.nullline.nullline_price
    r = execute_naked_layered_core_mechanical_step_v1(
        episode=episode,
        step=MechanicalStepSpecV1(mark_price_m_t=115.0, proposed_d_t=5.0),
        scope_generator=gen,
    )
    assert r.episode.nullline.nullline_price == pytest.approx(frozen)


def test_d_t_provenance_requires_explicit_positive() -> None:
    episode, _ = _init_episode()
    snap = episode_to_snapshot_v1(episode)
    assert snap["scope"] is not None
    snap["scope"]["d_t"] = -1.0
    snap["snapshot_id"] = "0" * 64
    with pytest.raises(NakedLayeredCoreDurableStateError, match="D_T_INVALID"):
        episode_from_snapshot_v1(snap)


def test_bull_bear_switch_symmetry_restart(tmp_path: Path) -> None:
    _, gen = _init_episode()
    ep_bull, _ = initialize_naked_layered_core_episode_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=110.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=50.0),
        scope_generator=gen,
    )
    r_bear = execute_naked_layered_core_mechanical_step_v1(
        episode=ep_bull,
        step=MechanicalStepSpecV1(mark_price_m_t=95.0, proposed_d_t=5.0),
        scope_generator=gen,
    )
    assert r_bear.regime_post is NakedRegimeV1.BEAR
    atomic_persist_episode_v1(tmp_path, r_bear.episode)
    restored = restore_episode_from_store_v1(tmp_path, expected_instrument_id="BTC-PERP")
    assert restored.regime is NakedRegimeV1.BEAR

    ep_bear, _ = initialize_naked_layered_core_episode_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=90.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=50.0),
        scope_generator=gen,
    )
    r_bull = execute_naked_layered_core_mechanical_step_v1(
        episode=ep_bear,
        step=MechanicalStepSpecV1(mark_price_m_t=105.0, proposed_d_t=5.0),
        scope_generator=gen,
    )
    assert r_bull.regime_post is NakedRegimeV1.BULL


def test_post_switch_r_t_carry() -> None:
    episode, gen = _init_episode()
    r = execute_naked_layered_core_mechanical_step_v1(
        episode=episode,
        step=MechanicalStepSpecV1(mark_price_m_t=115.0, proposed_d_t=50.0),
        scope_generator=gen,
    )
    assert r.r_t_post == pytest.approx(115.0)
    r2 = execute_naked_layered_core_mechanical_step_v1(
        episode=r.episode,
        step=MechanicalStepSpecV1(mark_price_m_t=114.0, proposed_d_t=5.0),
        scope_generator=gen,
    )
    assert r2.episode.running_reference.reference_price_r_t == pytest.approx(r.r_t_post)


def test_no_legacy_side_state_fallback() -> None:
    with pytest.raises(NakedLayeredCoreDurableStateError, match="LEGACY_SEMANTIC"):
        assert_no_legacy_semantic_fields_v1({"side_state": "LONG_ACTIVE"})
    episode, _ = _init_episode()
    snap = episode_to_snapshot_v1(episode)
    snap["runtime_scope_state"] = {"anchor_price": 1.0}
    with pytest.raises(NakedLayeredCoreDurableStateError, match="LEGACY_SEMANTIC"):
        episode_from_snapshot_v1(snap)


def test_no_productive_binding_or_cutover_flags() -> None:
    assert PRODUCTIVE_BINDING_AUTHORIZED is False
    assert AUTHORITY_CUTOVER_OCCURRED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert LEGACY_SEMANTIC_FALLBACK_AUTHORIZED is False
    episode, _ = _init_episode()
    snap = episode_to_snapshot_v1(episode)
    assert snap["productive_binding_authorized"] is False
    assert snap["authority_cutover_occurred"] is False


def test_process_boundary_restart_parity_same_inputs(tmp_path: Path) -> None:
    """Same prior core state + same step => same post state before/after persist."""
    episode, gen = _init_episode()
    step = MechanicalStepSpecV1(mark_price_m_t=95.0, proposed_d_t=5.0)
    in_memory = execute_naked_layered_core_mechanical_step_v1(
        episode=episode, step=step, scope_generator=gen
    )
    atomic_persist_episode_v1(tmp_path, episode)
    restored = restore_episode_from_store_v1(tmp_path, expected_instrument_id="BTC-PERP")
    after_boundary = execute_naked_layered_core_mechanical_step_v1(
        episode=restored, step=step, scope_generator=gen
    )
    assert after_boundary.regime_post is in_memory.regime_post
    assert after_boundary.r_t_post == pytest.approx(in_memory.r_t_post)
    assert after_boundary.d_t == pytest.approx(in_memory.d_t)


def test_manifest_and_schema_contract() -> None:
    episode, _ = _init_episode()
    snap = episode_to_snapshot_v1(episode)
    assert snap["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert "snapshot_id" in snap
    json.loads(json.dumps(snap))
