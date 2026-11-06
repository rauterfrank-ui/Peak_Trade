"""Actual bounded sequencer recovery and local stop delivery; no external calls."""

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_governed_continuous_cycle_orchestrator_v1 as sequencer,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1 import supervisor_v1 as supervisor
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1 import (
    runtime_notice_v1 as notices,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _run,
    _auth,
    _obs,
    _source,
    _FakeClock,
    C1_A,
    C1_B,
    _assert_zero_effect,
)


class FailingThenSource:
    def __init__(self, errors):
        self.errors = list(errors)
        self.calls = 0
        self.observation = _source(_obs(C1_A))

    def poll(self):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return self.observation.poll()


def _events(root):
    return [
        json.loads(line)
        for line in (root / "evidence" / notices.EVENTS_FILENAME).read_text().splitlines()
    ]


@pytest.mark.parametrize("error", [TimeoutError, ConnectionError])
def test_transient_source_failure_retries_and_processes_fresh_c1_once(tmp_path, error):
    source, clock = FailingThenSource([error("private transport details")]), _FakeClock()
    result = _run(
        tmp_path, observation_source=source, clock=clock, authorization=_auth(max_cycles_per_run=1)
    )
    assert result.cycles_completed == result.s5_invoke_count == 1
    assert source.calls == 2 and clock.sleeps == [1.0]
    events = _events(tmp_path)
    assert events[0]["reason_code"] == "OBSERVATION_SOURCE_FAULT"
    assert events[1]["reason_code"] == "OBSERVATION_POLL_RETRY_SCHEDULED"
    recovery = next(e for e in events if e["notification_kind"] == "RECOVERED")
    assert recovery["extra"]["incident_id"] == events[0]["event_id"]
    assert events[-1]["reason_code"] == "MAX_CYCLES_PER_RUN"
    assert "private transport details" not in json.dumps(events)
    _assert_zero_effect(result)


def test_exhausted_retry_delivers_actionable_terminal_and_cannot_replay(tmp_path, caplog):
    source = FailingThenSource([TimeoutError()] * 10)
    result = _run(tmp_path, observation_source=source)
    assert source.calls == 4  # existing O6 limit: initial poll + three retries
    assert result.reason_code == "OBSERVATION_POLL_RETRY_EXHAUSTED"
    assert result.s5_invoke_count == 0
    latest = _events(tmp_path)[-1]
    assert latest["owner_action_required"] and latest["recovery_action"]
    assert not latest["extra"]["automatic_restart_allowed"]
    assert result.reason_code in caplog.text
    with pytest.raises(
        sequencer.CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match="PARTIAL_CONTINUOUS_RUN_NOT_RESUMABLE",
    ):
        _run(tmp_path, observation_source=source)
    assert source.calls == 4
    _assert_zero_effect(result)


@pytest.mark.parametrize("kind", ["empty", "stale"])
def test_wait_deadline_does_not_reset_on_active_polling(tmp_path, kind):
    source = _source(_obs(C1_A), *([None] * 20 if kind == "empty" else [_obs(C1_A)] * 20))
    result = _run(
        tmp_path,
        observation_source=source,
        authorization=_auth(max_wait_for_next_c1_seconds=3, max_run_duration_seconds=20),
    )
    assert result.reason_code == "MAX_WAIT_FOR_NEXT_C1"
    assert result.cycles_completed == 1 and result.sequencer_elapsed_monotonic_seconds == 3
    assert _events(tmp_path)[-1]["owner_action_required"]


def test_first_fresh_c1_also_has_wait_deadline(tmp_path):
    result = _run(
        tmp_path,
        observation_source=_source(None),
        authorization=_auth(max_wait_for_next_c1_seconds=2, max_run_duration_seconds=20),
    )
    assert result.reason_code == "MAX_WAIT_FOR_NEXT_C1" and result.s5_invoke_count == 0
    assert result.sequencer_elapsed_monotonic_seconds == 2


def test_poll_returning_after_run_deadline_cannot_start_cycle(tmp_path):
    clock = _FakeClock()

    class SlowSource:
        def poll(self):
            clock.now += 5
            return _obs(C1_A)

    result = _run(
        tmp_path,
        observation_source=SlowSource(),
        clock=clock,
        authorization=_auth(max_run_duration_seconds=3),
    )
    assert result.reason_code == "MAX_RUN_DURATION" and result.s5_invoke_count == 0


@pytest.mark.parametrize("error", [ValueError, OSError])
def test_unknown_source_failure_is_not_retried_and_is_persisted(tmp_path, error, caplog):
    original = error("not safe to retry")
    source = FailingThenSource([original])
    with pytest.raises(error) as raised:
        _run(tmp_path, observation_source=source)
    assert raised.value is original and source.calls == 1
    assert _events(tmp_path)[-1]["owner_action_required"]
    assert "UNEXPECTED_RUNTIME_FAILURE" in caplog.text
    assert not (tmp_path / "lock" / sequencer.LOCK_NAME).exists()


def test_failure_after_s5_invoke_is_never_automatically_replayed(tmp_path):
    calls = []

    def broken_runner(**kwargs):
        calls.append(kwargs)
        raise TimeoutError("uncertain cycle outcome")

    with pytest.raises(TimeoutError):
        _run(tmp_path, s5_runner=broken_runner)
    assert len(calls) == 1
    event = _events(tmp_path)[-1]
    assert event["extra"]["s5_invoke_count"] == 1
    with pytest.raises(sequencer.CurrentProductiveGovernedContinuousCycleOrchestratorError):
        _run(tmp_path, s5_runner=broken_runner)
    assert len(calls) == 1


def test_market_payloads_reach_custom_cycle_runner_unchanged(tmp_path):
    mark, index = {"mark": "original"}, {"index": "original"}
    captured = []

    def runner(**kwargs):
        captured.append((kwargs.pop("mark_price_payload"), kwargs.pop("index_tickers_payload")))
        return sequencer.run_current_productive_governed_cycle_v1(**kwargs)

    result = _run(
        tmp_path,
        observation_source=_source(
            replace(_obs(C1_A), mark_price_payload=mark, index_tickers_payload=index)
        ),
        authorization=_auth(max_cycles_per_run=1),
        s5_runner=runner,
    )
    assert captured == [(mark, index)] and captured[0][0] is mark
    assert result.cycles_completed == 1


def test_supervisor_validation_failure_reaches_local_notice_without_bootstrap(
    tmp_path, monkeypatch, caplog
):
    monkeypatch.setattr(
        supervisor,
        "validate_bounded_continuous_run_owner_go_decision_v1",
        lambda **_: (False, ("missing",)),
    )
    config = supervisor.StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "lane",
        evidence_root=tmp_path / "evidence",
    )
    with pytest.raises(supervisor.StandingSupervisorError, match="OWNER_GO_VALIDATION_DENIED"):
        supervisor.run_n1_standing_pre_external_supervisor_v1(
            config=config,
            origin_main_sha="test",
            bound=None,
            authorization=_auth(),
            observation_source=_source(),
            g17_producers={},
            f1_m9_cycle_evaluator=lambda _: None,
            public_rest_fetch=lambda *args: pytest.fail("unexpected public fetch"),
            private_rest_fetch=lambda *args: pytest.fail("unexpected private fetch"),
        )
    event = _events(tmp_path)[-1]
    assert event["component"] == "STANDING_N1_SUPERVISOR"
    assert event["owner_action_required"] and not event["external_effect_authorized"]
    assert "OWNER_GO_VALIDATION_DENIED" in caplog.text


def test_failed_notice_persistence_is_logged_and_never_reported_as_delivered(
    tmp_path, monkeypatch, caplog
):
    monkeypatch.setattr(
        notices, "write_json", lambda *args: (_ for _ in ()).throw(OSError("disk full"))
    )
    with pytest.raises(OSError):
        notices.record_runtime_notice_v1(
            evidence_root=tmp_path,
            component="TEST",
            run_id="test",
            reason_code="BLOCKED",
            action="Inspect owner",
            owner_action_required=True,
        )
    assert "persistence failed" in caplog.text


def test_retry_budget_cannot_extend_run_duration(tmp_path):
    source = FailingThenSource([TimeoutError()] * 10)
    result = _run(
        tmp_path, observation_source=source, authorization=_auth(max_run_duration_seconds=2)
    )
    assert result.reason_code == "MAX_RUN_DURATION"
    assert source.calls == 2 and result.s5_invoke_count == 0


def test_cancellation_is_observed_between_source_retries(tmp_path):
    source = FailingThenSource([TimeoutError()] * 10)
    result = _run(tmp_path, observation_source=source, cancel_requested=lambda: source.calls >= 1)
    assert result.reason_code == "CANCELLED" and source.calls == 1


def test_retry_count_does_not_reset_after_one_successful_cycle(tmp_path):
    steps = iter([TimeoutError(), TimeoutError(), TimeoutError(), _obs(C1_A), ConnectionError()])

    class MixedSource:
        def poll(self):
            step = next(steps)
            if isinstance(step, Exception):
                raise step
            return step

    result = _run(tmp_path, observation_source=MixedSource())
    assert result.reason_code == "OBSERVATION_POLL_RETRY_EXHAUSTED"
    assert result.cycles_completed == result.s5_invoke_count == 1


@pytest.mark.parametrize(
    "disposition,expected_ok",
    [
        (sequencer.DISPOSITION_FAIL_CLOSED, False),
        (sequencer.DISPOSITION_STALL, False),
        (sequencer.DISPOSITION_MAX_CYCLES, True),
    ],
)
def test_supervisor_reports_policy_stop_and_does_not_render_failure_ok(
    tmp_path, monkeypatch, disposition, expected_ok
):
    # Inject startup/policy ports only. Exercise the actual supervisor's outcome
    # handling without treating synthetic ports as an integrated runtime proof.
    from types import SimpleNamespace

    config = supervisor.StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public",
        private_store_root=tmp_path / "private",
        lane_state_root=tmp_path / "lane",
        evidence_root=tmp_path / "evidence",
        wp02_productive_default_enabled=False,
        expected_account_identity="host-offline-account",
    )
    from tests.ops._host_private_rest_fixture_v1 import initialize_synthetic_host_budget_v1
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import _bound_lane_1

    initialize_synthetic_host_budget_v1(config.private_store_root, _bound_lane_1())
    config.evidence_root.mkdir()
    (config.evidence_root / "bounded_continuous_run_owner_go_consume_v1.json").write_text("{}")
    monkeypatch.setattr(
        supervisor, "validate_bounded_continuous_run_owner_go_decision_v1", lambda **_: (True, ())
    )
    monkeypatch.setattr(
        supervisor,
        "_run_unified_recovery_v1",
        lambda **_: SimpleNamespace(ok=True, steps_completed=[]),
    )
    monkeypatch.setattr(supervisor, "_refresh_public_supply_v1", lambda **_: 100)
    monkeypatch.setattr(supervisor, "_refresh_pretrade_truth_v1", lambda **_: "FRESH")
    policy = SimpleNamespace(
        orchestrator_result=SimpleNamespace(
            cycles_completed=0,
            accepted_c1_count=0,
            disposition=disposition,
            reason_code="POLICY_STOP",
            post_count=0,
            next_required_owner_decision="Reconcile and obtain fresh authorization",
        ),
        iteration_evidence=(),
        post_allowed=False,
        external_effect_authorized=False,
    )
    monkeypatch.setattr(
        supervisor,
        "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1",
        lambda **_: policy,
    )
    result = supervisor.run_n1_standing_pre_external_supervisor_v1(
        config=config,
        origin_main_sha="test",
        bound=SimpleNamespace(instrument_id="instrument"),
        authorization=_auth(),
        observation_source=_source(),
        g17_producers={},
        f1_m9_cycle_evaluator=lambda _: None,
        public_rest_fetch=lambda *args: {},
        private_rest_fetch=lambda *args: {},
    )
    assert result.ok is expected_ok
    event = _events(tmp_path)[-1]
    assert event["reason_code"] == "POLICY_STOP" and event["owner_action_required"]
