"""GHV-referenced PRE_EXTERNAL report observability: get_count single-authority delegation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    InjectedContinuousObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.session_integration_v1 import (
    PendingOutcomeAdvanceObservationSourceV1,
    wrap_observation_source_for_pending_outcome_advance_v1,
)


@dataclass
class _FakeFreshC1SourceV1:
    poll_count: int = field(default=0, init=False)
    get_count: int = field(default=0, init=False)
    poll_returns: InjectedContinuousObservationV1 | None = None

    def poll(self) -> InjectedContinuousObservationV1 | None:
        self.poll_count += 1
        self.get_count += 1
        return self.poll_returns


def _minimal_observation(*, mark_px: str = "1.0") -> InjectedContinuousObservationV1:
    return InjectedContinuousObservationV1(
        candles_payload={
            "data": [["1791308160000", mark_px, mark_px, mark_px, mark_px, "0"]],
        },
        occupancy_payloads={},
        mark_price_payload={
            "code": "0",
            "data": [{"markPx": mark_px, "instId": "TEST-USDT-SWAP"}],
        },
    )


def test_ghv_1_wrapper_exposes_get_count_read_only_from_inner() -> None:
    inner = _FakeFreshC1SourceV1()
    wrapped = PendingOutcomeAdvanceObservationSourceV1(
        inner=inner,
        lane_state_root=Path("/tmp/lane"),
        evidence_root=Path("/tmp/evidence"),
        canonical_instrument_id="test:instrument",
        native_id="TEST-USDT-SWAP",
        repository_sha="abc",
    )
    assert wrapped.get_count == 0
    inner.get_count = 7
    assert wrapped.get_count == 7


def test_ghv_3_get_count_single_authority_wrapper_does_not_increment() -> None:
    inner = _FakeFreshC1SourceV1(
        poll_returns=_minimal_observation(),
    )
    wrapped = wrap_observation_source_for_pending_outcome_advance_v1(
        inner,
        lane_state_root=Path("/tmp/lane"),
        evidence_root=Path("/tmp/evidence"),
        canonical_instrument_id="test:instrument",
        native_id="TEST-USDT-SWAP",
        repository_sha="abc",
    )
    assert isinstance(wrapped, PendingOutcomeAdvanceObservationSourceV1)
    before_inner = inner.get_count
    wrapped.poll()
    assert inner.get_count == before_inner + 1
    assert wrapped.get_count == inner.get_count
    assert wrapped.get_count == 1


def test_ghv_4_multiple_polls_no_duplicate_counter_on_wrapper() -> None:
    inner = _FakeFreshC1SourceV1(
        poll_returns=_minimal_observation(),
    )
    wrapped = wrap_observation_source_for_pending_outcome_advance_v1(
        inner,
        lane_state_root=Path("/tmp/lane"),
        evidence_root=Path("/tmp/evidence"),
        canonical_instrument_id="test:instrument",
        native_id="TEST-USDT-SWAP",
        repository_sha="abc",
    )
    for _ in range(3):
        wrapped.poll()
    assert inner.get_count == 3
    assert wrapped.get_count == 3


def test_natural_8_pre_external_report_live_public_c1_get_executed_field() -> None:
    inner = _FakeFreshC1SourceV1()
    obs_source = wrap_observation_source_for_pending_outcome_advance_v1(
        inner,
        lane_state_root=Path("/tmp/lane"),
        evidence_root=Path("/tmp/evidence"),
        canonical_instrument_id="test:instrument",
        native_id="TEST-USDT-SWAP",
        repository_sha="abc",
    )
    inner.get_count = 2
    live_public_c1_get_executed = str(obs_source.get_count > 0).lower()
    assert live_public_c1_get_executed == "true"


def test_natural_1_poll_without_mark_payload_does_not_advance_pending() -> None:
    inner = _FakeFreshC1SourceV1(
        poll_returns=InjectedContinuousObservationV1(
            candles_payload={"data": []},
            occupancy_payloads={},
            mark_price_payload=None,
        ),
    )
    wrapped = PendingOutcomeAdvanceObservationSourceV1(
        inner=inner,
        lane_state_root=Path("/tmp/lane"),
        evidence_root=Path("/tmp/evidence"),
        canonical_instrument_id="test:instrument",
        native_id="TEST-USDT-SWAP",
        repository_sha="abc",
    )
    assert wrapped.poll() is not None
    assert inner.get_count == 1
    assert wrapped.get_count == 1


def test_inner_without_get_count_reports_zero() -> None:
    class _PollOnly:
        def poll(self) -> None:
            return None

    wrapped = PendingOutcomeAdvanceObservationSourceV1(
        inner=_PollOnly(),
        lane_state_root=Path("/tmp/lane"),
        evidence_root=Path("/tmp/evidence"),
        canonical_instrument_id="test:instrument",
        native_id="TEST-USDT-SWAP",
        repository_sha="abc",
    )
    assert wrapped.get_count == 0
