"""Policy-governed persistent Natural-ENTER + Owner-GO + live C1 source wiring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from src.governance.current_productive_activation_policy_v1 import (
    RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    GovernedF1M9ThresholdConsumerWiringRequestV1,
    run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
    DECISION_CONFIG,
    owner_go_consumption_semantics_v1,
    validate_bounded_continuous_run_owner_go_decision_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
    DISPOSITION_MAX_CYCLES,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    ScriptedContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    PersistentNaturalEnterConvergenceError,
    run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
    LiveFreshC1ContinuousObservationSourceV1,
)
from tests.governance.test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    _bound_context,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    NATIVE_ID,
    _bound_lane_1,
    _continuous_auth,
    _cursor_floor_or_zero,
    _observation_from_closes,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_productive_c1_event_ts_unix_v1,
    strong_uptrend_closes_v1,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    C1_A,
    _FakeClock,
    _obs,
    _seed_cursor,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _valid_estimate,
)

REPO = Path(__file__).resolve().parents[2]
POST_MERGE_MAIN_SHA = "7b706117695e0ef79d1510ae98c335dd5bc8630b"
CURRENT_MAIN_SHA = "7a3597e61966749a9e30d06f3514e23a9179fb9e"
BASELINE_SHA = CURRENT_MAIN_SHA


def test_owner_go_decision_present_and_pins_unchanged() -> None:
    assert (REPO / DECISION_CONFIG).is_file()
    ok, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
        repo_root=REPO,
        baseline_origin_main_sha=BASELINE_SHA,
    )
    assert ok, reasons
    sem = owner_go_consumption_semantics_v1()
    assert sem["module_pins_mutated"] == "false"
    assert CONTINUOUS_RUN_AUTHORIZED is False


def test_owner_go_decision_rejects_ancestor_main_when_pinned_at_current() -> None:
    ok, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
        repo_root=REPO,
        baseline_origin_main_sha=POST_MERGE_MAIN_SHA,
    )
    assert ok is False
    assert "BASELINE_SHA_MISMATCH" in reasons


def test_owner_go_decision_accepts_current_main_at_pinned_baseline() -> None:
    ok, reasons = validate_bounded_continuous_run_owner_go_decision_v1(
        repo_root=REPO,
        baseline_origin_main_sha=CURRENT_MAIN_SHA,
    )
    assert ok, reasons


@dataclass
class _MockGetResult:
    get_performed: bool
    payload: dict[str, Any] | None


class _MockTransport:
    def __init__(self, payload: dict[str, Any] | None) -> None:
        self._payload = payload
        self.calls = 0

    def get(
        self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str
    ) -> _MockGetResult:
        del endpoint, pretrade_decision_id
        assert auth_required is False
        self.calls += 1
        return _MockGetResult(
            get_performed=self._payload is not None,
            payload=self._payload,
        )


def test_live_fresh_c1_cold_lane_bootstrap_poll_with_mock_transport(tmp_path: Path) -> None:
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
        ENDPOINT_PUBLIC_MARK_PRICE,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_PATH,
    )
    from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
        okx_public_mark_price_payload_v1,
    )

    payload = {"code": "0", "msg": "", "data": [["1", "1", "1", "1", "1", "1", "1", "USDT", "1"]]}
    mark_payload = okx_public_mark_price_payload_v1(native_id=NATIVE_ID, mark_px=3500.0)

    class _DualMockTransport:
        def __init__(self) -> None:
            self.calls = 0

        def get(
            self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str
        ) -> _MockGetResult:
            del pretrade_decision_id
            assert auth_required is False
            self.calls += 1
            path = endpoint.split("?", 1)[0]
            if path == GET_PATH:
                return _MockGetResult(get_performed=True, payload=payload)
            if path == ENDPOINT_PUBLIC_MARK_PRICE:
                return _MockGetResult(get_performed=True, payload=mark_payload)
            return _MockGetResult(get_performed=False, payload=None)

    transport = _DualMockTransport()
    cold_lane = tmp_path / "cold_lane"
    cold_lane.mkdir()
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cold_lane,
        evidence_root=tmp_path / "evidence",
        run_id="cold-bootstrap",
        native_id=NATIVE_ID,
        transport=transport,
    )
    obs = source.poll()
    assert obs is not None
    assert obs.mark_price_payload is not None
    assert transport.calls == 2
    assert source.get_count == 1


def test_live_fresh_c1_observation_source_poll_with_mock_transport(tmp_path: Path) -> None:
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
        ENDPOINT_PUBLIC_MARK_PRICE,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_PATH,
    )
    from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
        okx_public_mark_price_payload_v1,
    )

    cursor = _seed_cursor(tmp_path / "lane", event_time=0.0)
    payload = {"code": "0", "msg": "", "data": [["1", "1", "1", "1", "1", "1", "1", "USDT", "1"]]}
    mark_payload = okx_public_mark_price_payload_v1(native_id=NATIVE_ID, mark_px=3500.0)

    class _DualMockTransport:
        def __init__(self) -> None:
            self.calls = 0

        def get(
            self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str
        ) -> _MockGetResult:
            del pretrade_decision_id
            assert auth_required is False
            self.calls += 1
            path = endpoint.split("?", 1)[0]
            if path == GET_PATH:
                return _MockGetResult(get_performed=True, payload=payload)
            if path == ENDPOINT_PUBLIC_MARK_PRICE:
                return _MockGetResult(get_performed=True, payload=mark_payload)
            return _MockGetResult(get_performed=False, payload=None)

    transport = _DualMockTransport()
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor,
        evidence_root=tmp_path / "evidence",
        run_id="test-run",
        native_id=NATIVE_ID,
        transport=transport,
    )
    obs = source.poll()
    assert obs is not None
    assert obs.mark_price_payload is not None
    assert transport.calls == 2
    assert (tmp_path / "evidence/fresh_c1_get_owner_go_consumptions_v1.jsonl").is_file()


def _f1_m9_evaluator_factory(tmp_path: Path):
    apply_rev = tmp_path / "apply_rev.jsonl"
    threshold_rev = tmp_path / "threshold_rev.jsonl"
    initialize_empty_revocation_ledger_v1(apply_rev)
    initialize_empty_threshold_revocation_ledger_v1(threshold_rev)
    continuation = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
        GovernedF1M9ThresholdConsumerWiringRequestV1(
            apply_ledger_paths=F1M9ProductiveApplyLedgerPathsV1(
                apply_ledger_path=tmp_path / "apply.jsonl",
                revocation_ledger_path=apply_rev,
            ),
            threshold_ledger_paths=F1M9ThresholdValueAuthorizationLedgerPathsV1(
                threshold_ledger_path=tmp_path / "threshold.jsonl",
                threshold_revocation_ledger_path=threshold_rev,
            ),
            repo_root=REPO,
        )
    )
    assert continuation.bound_seam_record is not None
    ctx, elig = _bound_context(_valid_estimate())

    def _eval(_cycle_index: int):
        return evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
            market_context=ctx,
            eligibility=elig,
            governed_seam_record=continuation.bound_seam_record,
            require_governed_seam=True,
            runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
            repo_root=REPO,
        )

    return _eval


def test_policy_governed_persistent_path_integrated(tmp_path: Path) -> None:
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
        _lane_g17,
        bootstrap_s8_lane_via_s7_compose_v1,
        build_s8_occupied_lane_pairs_v1,
    )

    bound = _bound_lane_1()
    native_id = str(bound.venue_native_id)
    lane_state = tmp_path / "lane_state"
    evidence = tmp_path / "evidence"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_state, bound=bound)
    g17 = _lane_g17(pairs)
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    obs_boot = _observation_from_closes(closes=path[:14], event_ts=t0 - 60.0)
    bootstrap_s8_lane_via_s7_compose_v1(
        composed_pairs=pairs,
        origin_main_sha=BASELINE_SHA,
        g17_producers=g17,
        candles_payload=obs_boot.candles_payload,
        mark_price_payload=obs_boot.mark_price_payload,
        venue_native_id=native_id,
        index_tickers_payload=obs_boot.index_tickers_payload,
    )
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    obs_source = ScriptedContinuousObservationSourceV1(
        [_observation_from_closes(closes=path[:16], event_ts=t0)]
    )
    result = run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
        authorization=auth,
        origin_main_sha=BASELINE_SHA,
        lane_state_root=lane_state,
        bound=bound,
        g17_producers=g17,
        observation_source=obs_source,
        evidence_root=evidence,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    orch = result.orchestrator_result
    assert orch.disposition == DISPOSITION_MAX_CYCLES
    assert orch.cycles_completed == 1
    assert orch.post_count == 0
    assert orch.permit_created is False
    assert result.post_allowed is False
    assert (evidence / "bounded_continuous_run_owner_go_consume_v1.json").is_file()
    assert (evidence / "continuous_run_policy_evidence_v1.json").is_file()


def test_owner_go_denied_without_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_bounded_continuous_run_owner_go_wiring_v1.load_bounded_continuous_run_owner_go_decision_v1",
        lambda **_: {},
    )
    lane_state = tmp_path / "lane_state"
    evidence = tmp_path / "evidence"
    with pytest.raises(PersistentNaturalEnterConvergenceError, match="OWNER_GO_DECISION_DENIED"):
        run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
            authorization=_continuous_auth(native_id=NATIVE_ID),
            origin_main_sha=BASELINE_SHA,
            lane_state_root=lane_state,
            bound=_bound_lane_1(),
            g17_producers={},
            observation_source=ScriptedContinuousObservationSourceV1([_obs(C1_A)]),
            evidence_root=evidence,
            f1_m9_cycle_evaluator=lambda _i: None,  # type: ignore[arg-type]
            repo_root=REPO,
        )
