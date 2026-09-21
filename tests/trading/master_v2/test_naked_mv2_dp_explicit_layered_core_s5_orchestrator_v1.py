"""S5 — full orchestrator proof and isolation guards."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    DynamicScopeGeneratorInputV1,
    DynamicScopeGeneratorOutputV1,
    LayerReachabilityV1,
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.evidence_v1 import (
    build_layer_separation_evidence_v1,
    write_layer_separation_evidence_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (
    ExplicitPassthroughDynamicScopeGeneratorV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
    orchestrate_naked_layered_core_v1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

_REPO = Path(__file__).resolve().parents[3]


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


def test_a_rising_init_bull_then_bear_switch() -> None:
    result = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=110.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=50.0),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
        follow_on_steps=[MechanicalStepSpecV1(mark_price_m_t=95.0, proposed_d_t=5.0)],
    )
    assert not result.fail_closed
    assert result.final_regime is NakedRegimeV1.BEAR
    assert result.final_nullline_price == pytest.approx(110.0)
    reached = {
        e.layer_id for e in result.layer_trace if e.reachability is LayerReachabilityV1.REACHED
    }
    for lid in LayerIdV1:
        assert lid in reached


def test_b_falling_init_bear_then_bull_switch() -> None:
    result = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=90.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=50.0),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
        follow_on_steps=[MechanicalStepSpecV1(mark_price_m_t=105.0, proposed_d_t=5.0)],
    )
    assert not result.fail_closed
    assert result.final_regime is NakedRegimeV1.BULL


def test_c_no_distinct_direction_fail_closed_before_l5() -> None:
    result = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=100.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=5.0),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
    )
    assert result.fail_closed
    assert not any(
        e.layer_id is LayerIdV1.L5_NULLLINE and e.reachability is LayerReachabilityV1.REACHED
        for e in result.layer_trace
    )


def test_d_invalid_d_t_l7_l10_not_reached() -> None:
    result = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=101.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=None),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
    )
    assert result.fail_closed
    not_reached = {
        e.layer_id for e in result.layer_trace if e.reachability is LayerReachabilityV1.NOT_REACHED
    }
    assert LayerIdV1.L7_SCOPE_STATE in not_reached
    assert LayerIdV1.L10_BULL_BEAR_STATE_SWITCH in not_reached


@dataclass(frozen=True)
class AltScopeGeneratorV1:
    generator_id: str = "alt_scope/v1"

    def generate(self, inp: DynamicScopeGeneratorInputV1) -> DynamicScopeGeneratorOutputV1:
        return DynamicScopeGeneratorOutputV1(
            d_t=12.0,
            fail_closed=False,
            fail_reasons=(),
            generator_id=self.generator_id,
        )


def test_e_replaceable_scope_generator() -> None:
    base = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=101.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=5.0),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
    )
    alt = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=101.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=None),
        scope_generator=AltScopeGeneratorV1(),
    )
    assert base.final_nullline_price == alt.final_nullline_price
    assert base.fail_closed is alt.fail_closed is False


def test_f_running_r_t_moves_nullline_fixed() -> None:
    result = orchestrate_naked_layered_core_v1(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=110.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=115.0, proposed_d_t=50.0),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
    )
    assert result.final_nullline_price == pytest.approx(110.0)
    assert result.final_running_r_t == pytest.approx(115.0)


def test_g_deterministic_replay() -> None:
    kwargs = dict(
        selected=_selected(),
        initialization_observations=[_cand(t=1.0, mark=100.0), _cand(t=2.0, mark=105.0)],
        first_mechanical_step=MechanicalStepSpecV1(mark_price_m_t=100.0, proposed_d_t=50.0),
        scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
        follow_on_steps=[MechanicalStepSpecV1(mark_price_m_t=99.0, proposed_d_t=5.0)],
    )
    a = orchestrate_naked_layered_core_v1(**kwargs)
    b = orchestrate_naked_layered_core_v1(**kwargs)
    assert a == b


def test_evidence_separation_flags() -> None:
    payload = build_layer_separation_evidence_v1()
    assert payload["NULLLINE_SCOPE_SEPARATION"] is True
    assert payload["NULLLINE_RUNNING_REFERENCE_SEPARATION"] is True
    assert payload["SCOPE_RUNNING_REFERENCE_SEPARATION"] is True
    assert payload["SCOPE_GENERATOR_REPLACEABLE"] is True
    assert payload["FINAL_D_T_FORMULA_SELECTED"] is False
    assert len(payload["LAYERS"]) == 10


def test_h_no_account_equity_or_29p_diff() -> None:
    diff = subprocess.check_output(
        ["git", "diff", "7aa7f1208cd455d64da551982ed21bd43b35bd07", "--name-only"],
        cwd=_REPO,
        text=True,
    )
    forbidden_fragments = (
        "account_equity",
        "29p",
        "29P",
        "PEAK_TRADE_MASTER_RUNBOOK",
        "docs/system_atlas",
    )
    for line in diff.splitlines():
        low = line.lower()
        for frag in forbidden_fragments:
            assert frag.lower() not in low, line


def test_write_evidence_artifact() -> None:
    path = write_layer_separation_evidence_v1(repo_root=_REPO)
    assert path.is_file()
