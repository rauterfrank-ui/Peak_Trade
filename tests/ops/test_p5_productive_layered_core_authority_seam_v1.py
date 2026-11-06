"""P5.1 authority seam: durable episode + seal (infrastructure)."""

from __future__ import annotations

from pathlib import Path

from trading.market_state.distinct_market_observation_acceptor_v1 import ObservationCandidateV1
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    restore_episode_from_store_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
)
from trading.master_v2.layered_core_authority_seal_v1 import validate_layered_core_authority_seal_v1

from src.ops.p5_productive_layered_core_authority_seam_v1 import (
    P4_PRODUCTIVE_BINDING,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    build_p5_cursor_v2_provenance_from_seal_v1,
    run_p5_layered_core_authority_seam_v1,
)


def _key() -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="ETH-PERP",
        venue_instrument_id="ETH-USDT-SWAP",
    )


def _cand(*, t: float, mark: float) -> ObservationCandidateV1:
    k = _key()
    return ObservationCandidateV1(
        venue=k.venue,
        canonical_instrument_id=k.canonical_instrument_id,
        venue_instrument_id=k.venue_instrument_id,
        venue_event_time=t,
        mark_price=mark,
    )


def test_seam_init_persist_restore_and_seal(tmp_path: Path) -> None:
    selected = SelectedFutureInputV1(
        instrument_id="ETH-PERP",
        instrument_key=_key(),
    )
    result = run_p5_layered_core_authority_seam_v1(
        store_root=tmp_path,
        selected=selected,
        mark_price_m_t=100.0,
        mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=25.0),
        restore_existing=False,
        initialization_observations=[
            _cand(t=1.0, mark=100.0),
            _cand(t=2.0, mark=110.0),
        ],
    )
    assert result.ok is True
    assert result.seal is not None
    validation = validate_layered_core_authority_seal_v1(result.seal, instrument_id="ETH-PERP")
    assert validation.ok is True
    restored = restore_episode_from_store_v1(tmp_path, expected_instrument_id="ETH-PERP")
    assert restored.mechanical_step_count >= 1
    prov, failures = build_p5_cursor_v2_provenance_from_seal_v1(
        result.seal, instrument_id="ETH-PERP"
    )
    assert failures == ()
    assert prov is not None
    assert prov.scope_mirror_non_authoritative is True


def test_seam_fail_closed_without_d_t() -> None:
    selected = SelectedFutureInputV1(
        instrument_id="ETH-PERP",
        instrument_key=_key(),
    )
    result = run_p5_layered_core_authority_seam_v1(
        store_root=Path("/tmp/unused"),
        selected=selected,
        mark_price_m_t=100.0,
        restore_existing=False,
        initialization_observations=[_cand(t=1.0, mark=100.0)],
    )
    assert result.ok is False
    assert result.seal is None


def test_guards() -> None:
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert P4_PRODUCTIVE_BINDING is False
