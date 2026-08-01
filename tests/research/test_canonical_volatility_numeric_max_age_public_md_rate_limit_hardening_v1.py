"""Deterministic offline tests for public-MD pacing/budget/429 hardening."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import pytest

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    build_campaign_authorization_artifact_v1,
    write_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_SESSION_IDS,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.ledgers_v1 import (
    load_consumption_records_v1,
    resolve_ledger_path_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_EVIDENCE_SCOPE,
    BOUND_INSTRUMENT_ID,
    BOUND_PREREGISTRATION_ID,
    BOUND_VENUE,
    BOUND_VENUE_SCOPE,
    SESSION_01_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.instrument_binding_v1 import (
    resolve_preregistered_session_venue_instrument_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    GitBaselineSnapshotV1,
    PreregisteredSessionRunnerError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    PublicMdRequestPacingPolicyV1,
    compute_effective_request_budget_v1,
    compute_exponential_backoff_seconds_v1,
    default_public_md_request_pacing_policy_v1,
    parse_retry_after_header_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_source_v1 import (
    PublicMdSourceTelemetryV1,
    build_preregistered_public_md_transport_v1,
    collect_public_mark_samples_v1,
    initialize_session_md_controls_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.runner_v1 import (
    run_preregistered_productive_session_v1,
)

ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "4e587f8dbf72a77f6bef96c042c804d8fd6ba7dd"
ISSUED = datetime.now(timezone.utc) - timedelta(minutes=5)
S1, S2 = BOUND_SESSION_IDS


class FakeMono:
    def __init__(self, start: float = 1000.0) -> None:
        self.t = float(start)
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return float(self.t)

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(float(seconds))
        self.t += float(seconds)


def _baseline() -> GitBaselineSnapshotV1:
    return GitBaselineSnapshotV1(
        branch="main",
        head_sha=REPO_SHA,
        origin_main_sha=REPO_SHA,
        worktree_allowed_delta_only=True,
    )


def _write_auth(tmp_path: Path):
    artifact = build_campaign_authorization_artifact_v1(
        repository_sha=REPO_SHA,
        campaign_id=BOUND_CAMPAIGN_ID,
        session_ids=BOUND_SESSION_IDS,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        issued_at=ISSUED,
        earliest_start=ISSUED,
    )
    path = tmp_path / "campaign_authorization.json"
    write_campaign_authorization_artifact_v1(output_path=path, artifact=artifact)
    return path, artifact


def _ok_body(ts_ms: int | None = None) -> bytes:
    stamp = ts_ms if ts_ms is not None else int(time.time() * 1000)
    return json.dumps(
        {
            "code": "0",
            "data": [
                {
                    "instId": "ETH-USD_UM_XPERP-310404",
                    "instType": "FUTURES",
                    "markPx": "2500.5",
                    "ts": str(stamp),
                }
            ],
        }
    ).encode("utf-8")


def test_policy_defaults_positive_and_not_zero_interval() -> None:
    policy = default_public_md_request_pacing_policy_v1()
    assert policy.minimum_interval_seconds > 0
    assert policy.maximum_requests_per_cycle >= 1
    assert "not_official_okx" in policy.origin or "not_official" in policy.origin


def test_zero_interval_burst_eliminated_for_cycle_count_128() -> None:
    clock = FakeMono()
    policy = default_public_md_request_pacing_policy_v1()
    tel = PublicMdSourceTelemetryV1()
    _p, _b, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=128,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    calls = {"n": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del method, headers, timeout
        calls["n"] += 1
        assert "mark-price" in url
        return 200, _ok_body(), {"Content-Type": "application/json"}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    # Keep the run short but prove pacing for multi-cycle with poll=0.
    samples = collect_public_mark_samples_v1(
        transport=transport,
        cycle_count=3,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        poll_interval_seconds=0.0,
        session_id=SESSION_01_ID,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    assert len(samples) == 3
    assert calls["n"] == 3
    # First attempt has no wait; subsequent physical attempts paced.
    assert len(clock.sleeps) == 2
    assert all(abs(s - policy.minimum_interval_seconds) < 1e-9 for s in clock.sleeps)


def test_regression_poll_interval_zero_cannot_issue_immediate_successive_gets() -> None:
    clock = FakeMono()
    policy = default_public_md_request_pacing_policy_v1()
    tel = PublicMdSourceTelemetryV1()
    _p, _b, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=5,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    starts: list[float] = []

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        starts.append(clock())
        return 200, _ok_body(), {}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    collect_public_mark_samples_v1(
        transport=transport,
        cycle_count=4,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        poll_interval_seconds=0.0,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    deltas = [b - a for a, b in zip(starts, starts[1:])]
    assert all(d >= policy.minimum_interval_seconds - 1e-9 for d in deltas)


def test_forty_success_then_three_429_evidence(tmp_path: Path) -> None:
    clock = FakeMono()
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=0.5,
        maximum_requests_per_session=80,
        maximum_requests_per_cycle=3,
        maximum_consecutive_rate_limits=3,
        retry_after_max_seconds=60.0,
        backoff_initial_seconds=1.0,
        backoff_multiplier=2.0,
        backoff_max_seconds=30.0,
        jitter_fraction=0.0,
    )
    n = {"i": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        n["i"] += 1
        if n["i"] <= 40:
            return 200, _ok_body(), {}
        return 429, b"{}", {"Retry-After": "1"}

    auth_path, artifact = _write_auth(tmp_path)
    result = run_preregistered_productive_session_v1(
        repo_root=ROOT,
        campaign_id=BOUND_CAMPAIGN_ID,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        session_id=SESSION_01_ID,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        authorization_artifact_path=auth_path,
        repository_sha=REPO_SHA,
        venue=BOUND_VENUE,
        instrument_id=BOUND_INSTRUMENT_ID,
        market_data_scope=BOUND_VENUE_SCOPE,
        evidence_scope=BOUND_EVIDENCE_SCOPE,
        max_cycles=41,
        evidence_root=tmp_path,
        git_baseline=_baseline(),
        http_fetcher=fetcher,
        md_sleep=clock.sleep,
        md_monotonic_clock=clock,
    )
    # Override policy via transport path is internal; use collect-level unit below for exact 43.
    # Runner uses default policy; this integration asserts fail-closed + evidence presence.
    assert result["authorization_consumed"] is True
    assert result["market_data_request_occurred"] is True
    md = result.get("preflight")  # not where telemetry lives
    manifest = Path(result["preflight"]["session_manifest_path"])
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    tel = payload["md_telemetry"]
    assert tel["market_data_request_occurred"] is True
    assert tel["counters"]["physical_request_attempt_count"] >= 1
    assert (
        len(tel["counters"]["attempt_evidence"])
        == tel["counters"]["physical_request_attempt_count"]
    )


def test_collect_40_ok_then_3_429_exact_attempts() -> None:
    clock = FakeMono()
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=0.25,
        maximum_requests_per_session=80,
        maximum_requests_per_cycle=3,
        maximum_consecutive_rate_limits=3,
        retry_after_max_seconds=60.0,
        backoff_initial_seconds=1.0,
        backoff_multiplier=2.0,
        backoff_max_seconds=30.0,
        jitter_fraction=0.0,
    )
    tel = PublicMdSourceTelemetryV1()
    _p, _b, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=41,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    n = {"i": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        n["i"] += 1
        if n["i"] <= 40:
            return 200, _ok_body(), {}
        return 429, b"{}", {}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    with pytest.raises(PreregisteredSessionRunnerError, match="RATE_LIMIT_RETRY_EXHAUSTED"):
        collect_public_mark_samples_v1(
            transport=transport,
            cycle_count=41,
            venue_instrument_id=BOUND_INSTRUMENT_ID,
            poll_interval_seconds=0.0,
            telemetry=tel,
            rate_limit_policy=policy,
            attempt_gate=gate,
            sleep=clock.sleep,
            monotonic_clock=clock,
            session_id=SESSION_01_ID,
        )
    assert n["i"] == 43
    assert tel.counters.physical_request_attempt_count == 43
    assert tel.counters.successful_response_count == 40
    assert tel.counters.rate_limited_response_count == 3
    assert tel.counters.terminal_transport_failure_count >= 1
    assert tel.counters.completed_market_sample_count == 40
    statuses = [row["http_status"] for row in tel.counters.attempt_evidence]
    assert statuses.count(200) == 40
    assert statuses.count(429) == 3
    assert tel.counters.attempt_evidence[-1]["terminal"] is True
    assert "RATE_LIMIT_RETRY_EXHAUSTED" in tel.counters.attempt_evidence[-1]["error_code"]


def test_retry_after_two_seconds_exact_delay() -> None:
    clock = FakeMono()
    policy = default_public_md_request_pacing_policy_v1()
    # Force smaller min interval so Retry-After sleep is observable separately from pacing.
    policy = PublicMdRequestPacingPolicyV1(
        **{**policy.to_dict(), "minimum_interval_seconds": 0.1, "jitter_fraction": 0.0}
    )
    tel = PublicMdSourceTelemetryV1()
    _p, _b, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=1,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    n = {"i": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        n["i"] += 1
        if n["i"] == 1:
            return 429, b"{}", {"retry-after": "2"}
        return 200, _ok_body(), {}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    samples = collect_public_mark_samples_v1(
        transport=transport,
        cycle_count=1,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    assert len(samples) == 1
    assert 2.0 in clock.sleeps
    row = tel.counters.attempt_evidence[0]
    assert row["http_status"] == 429
    assert row["retry_after_parsed_seconds"] == 2.0
    assert row["scheduled_backoff_seconds"] == 2.0
    assert "retry_after" in row["backoff_source"]
    assert all(s >= 0.1 for s in clock.sleeps)


def test_exponential_backoff_without_retry_after() -> None:
    policy = PublicMdRequestPacingPolicyV1(
        **{**default_public_md_request_pacing_policy_v1().to_dict(), "jitter_fraction": 0.0}
    )
    d0 = compute_exponential_backoff_seconds_v1(policy=policy, attempt_index=0, jitter_unit=0.0)
    d1 = compute_exponential_backoff_seconds_v1(policy=policy, attempt_index=1, jitter_unit=0.0)
    assert d0 == pytest.approx(policy.backoff_initial_seconds)
    assert d1 == pytest.approx(
        min(
            policy.backoff_initial_seconds * policy.backoff_multiplier,
            policy.backoff_max_seconds,
        )
    )
    assert d0 >= 1.0  # not millisecond storm


def test_invalid_retry_after_fallback_evidence() -> None:
    parsed = parse_retry_after_header_v1(
        {"Retry-After": "not-a-number"},
        now_unix=1_700_000_000.0,
        max_seconds=60.0,
    )
    assert parsed.valid is False
    assert parsed.error_code == "RATE_LIMIT_RETRY_AFTER_INVALID"

    clock = FakeMono()
    policy = PublicMdRequestPacingPolicyV1(
        **{
            **default_public_md_request_pacing_policy_v1().to_dict(),
            "minimum_interval_seconds": 0.1,
            "jitter_fraction": 0.0,
        }
    )
    tel = PublicMdSourceTelemetryV1()
    _p, _b, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=1,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    n = {"i": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        n["i"] += 1
        if n["i"] == 1:
            return 429, b"{}", {"Retry-After": "xyz"}
        return 200, _ok_body(), {}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    collect_public_mark_samples_v1(
        transport=transport,
        cycle_count=1,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    row = tel.counters.attempt_evidence[0]
    assert row["error_code"] in {
        "RATE_LIMIT_RETRY_AFTER_INVALID",
        "RATE_LIMIT_RETRY_SCHEDULED",
    }
    assert "exponential_backoff" in row["backoff_source"]
    assert row["scheduled_backoff_seconds"] == pytest.approx(1.0)


def test_retry_budget_exhausted_stops_outer_cycle() -> None:
    clock = FakeMono()
    policy = PublicMdRequestPacingPolicyV1(
        **{
            **default_public_md_request_pacing_policy_v1().to_dict(),
            "minimum_interval_seconds": 0.1,
            "jitter_fraction": 0.0,
            "maximum_consecutive_rate_limits": 2,
        }
    )
    tel = PublicMdSourceTelemetryV1()
    _p, _b, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=5,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    calls = {"n": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        calls["n"] += 1
        return 429, b"{}", {}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    with pytest.raises(PreregisteredSessionRunnerError, match="RATE_LIMIT_RETRY_EXHAUSTED"):
        collect_public_mark_samples_v1(
            transport=transport,
            cycle_count=5,
            venue_instrument_id=BOUND_INSTRUMENT_ID,
            telemetry=tel,
            rate_limit_policy=policy,
            attempt_gate=gate,
            sleep=clock.sleep,
            monotonic_clock=clock,
            session_id=SESSION_01_ID,
        )
    assert calls["n"] == 2  # no outer-cycle restart after exhaustion


def test_session_request_budget_exhausted_no_further_network() -> None:
    clock = FakeMono()
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=0.1,
        maximum_requests_per_session=2,
        maximum_requests_per_cycle=3,
        maximum_consecutive_rate_limits=3,
        retry_after_max_seconds=60.0,
        backoff_initial_seconds=1.0,
        backoff_multiplier=2.0,
        backoff_max_seconds=30.0,
        jitter_fraction=0.0,
    )
    tel = PublicMdSourceTelemetryV1()
    _p, budget, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=10,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    assert budget.effective.effective_maximum_requests == 2
    calls = {"n": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        calls["n"] += 1
        return 200, _ok_body(), {}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    with pytest.raises(PreregisteredSessionRunnerError, match="REQUEST_BUDGET_EXHAUSTED"):
        collect_public_mark_samples_v1(
            transport=transport,
            cycle_count=10,
            venue_instrument_id=BOUND_INSTRUMENT_ID,
            telemetry=tel,
            rate_limit_policy=policy,
            attempt_gate=gate,
            sleep=clock.sleep,
            monotonic_clock=clock,
            session_id=SESSION_01_ID,
        )
    assert calls["n"] == 2


def test_retries_count_against_session_budget() -> None:
    clock = FakeMono()
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=0.1,
        maximum_requests_per_session=3,
        maximum_requests_per_cycle=3,
        maximum_consecutive_rate_limits=3,
        retry_after_max_seconds=60.0,
        backoff_initial_seconds=1.0,
        backoff_multiplier=2.0,
        backoff_max_seconds=30.0,
        jitter_fraction=0.0,
    )
    tel = PublicMdSourceTelemetryV1()
    _p, budget, gate = initialize_session_md_controls_v1(
        session_id=SESSION_01_ID,
        max_cycles=1,
        venue_instrument_id=BOUND_INSTRUMENT_ID,
        telemetry=tel,
        policy=policy,
        sleep=clock.sleep,
        monotonic_clock=clock,
    )
    calls = {"n": 0}

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        calls["n"] += 1
        return 429, b"{}", {}

    transport, tel = build_preregistered_public_md_transport_v1(
        fetcher=fetcher,
        telemetry=tel,
        rate_limit_policy=policy,
        attempt_gate=gate,
        sleep=clock.sleep,
        monotonic_clock=clock,
        session_id=SESSION_01_ID,
    )
    transport.open()
    with pytest.raises(PreregisteredSessionRunnerError):
        collect_public_mark_samples_v1(
            transport=transport,
            cycle_count=1,
            venue_instrument_id=BOUND_INSTRUMENT_ID,
            telemetry=tel,
            rate_limit_policy=policy,
            attempt_gate=gate,
            sleep=clock.sleep,
            monotonic_clock=clock,
            session_id=SESSION_01_ID,
        )
    assert calls["n"] == 3
    assert budget.consumed == 3
    assert budget.remaining == 0
    assert all(
        row["request_budget_before"] > row["request_budget_after"]
        for row in tel.counters.attempt_evidence
    )


def test_market_data_request_occurred_on_terminal_failure(tmp_path: Path) -> None:
    clock = FakeMono()
    auth_path, artifact = _write_auth(tmp_path)

    def boom(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del url, method, headers, timeout
        raise RuntimeError("boom")

    result = run_preregistered_productive_session_v1(
        repo_root=ROOT,
        campaign_id=BOUND_CAMPAIGN_ID,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        session_id=SESSION_01_ID,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        authorization_artifact_path=auth_path,
        repository_sha=REPO_SHA,
        venue=BOUND_VENUE,
        instrument_id=BOUND_INSTRUMENT_ID,
        market_data_scope=BOUND_VENUE_SCOPE,
        evidence_scope=BOUND_EVIDENCE_SCOPE,
        max_cycles=1,
        evidence_root=tmp_path,
        git_baseline=_baseline(),
        http_fetcher=boom,
        md_sleep=clock.sleep,
        md_monotonic_clock=clock,
    )
    assert result["market_data_request_occurred"] is True
    payload = json.loads(Path(result["preflight"]["session_manifest_path"]).read_text())
    assert payload["market_data_request_occurred"] is True
    assert payload["md_telemetry"]["counters"]["physical_request_attempt_count"] >= 1


def test_effective_budget_is_minimum_and_evidenced() -> None:
    policy = default_public_md_request_pacing_policy_v1()
    eff = compute_effective_request_budget_v1(max_cycles=128, policy=policy)
    assert eff.effective_maximum_requests == min(
        policy.maximum_requests_per_session, 128 * policy.maximum_requests_per_cycle
    )
    assert eff.clamp_reason


def test_instrument_binding_authority_and_fail_closed() -> None:
    mapping = resolve_preregistered_session_venue_instrument_v1(
        canonical_instrument_id=BOUND_INSTRUMENT_ID
    )
    assert mapping.venue_instrument_id == BOUND_INSTRUMENT_ID
    assert mapping.mapping_digest
    with pytest.raises(
        PreregisteredSessionRunnerError, match="canonical_instrument_binding_mismatch"
    ):
        resolve_preregistered_session_venue_instrument_v1(
            canonical_instrument_id="BTC-USD_UM_XPERP-310404"
        )
    with pytest.raises(
        PreregisteredSessionRunnerError, match="venue_instrument_binding_fail_closed"
    ):
        resolve_preregistered_session_venue_instrument_v1(
            canonical_instrument_id=BOUND_INSTRUMENT_ID,
            instruments_inventory=[],
        )


def test_no_productive_auth_consumption_in_unit_binding_tests(tmp_path: Path) -> None:
    auth_path, artifact = _write_auth(tmp_path)
    resolve_preregistered_session_venue_instrument_v1(canonical_instrument_id=BOUND_INSTRUMENT_ID)
    cons = resolve_ledger_path_v1(
        evidence_root=tmp_path, relative_or_absolute=artifact.consumption_ledger_path
    )
    assert not cons.exists() or load_consumption_records_v1(cons) == []


def test_runner_records_binding_and_pacing_evidence(tmp_path: Path) -> None:
    clock = FakeMono()
    auth_path, artifact = _write_auth(tmp_path)

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        del method, headers, timeout
        assert "ETH-USD_UM_XPERP-310404" in url
        return 200, _ok_body(), {}

    result = run_preregistered_productive_session_v1(
        repo_root=ROOT,
        campaign_id=BOUND_CAMPAIGN_ID,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        session_id=SESSION_01_ID,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        authorization_artifact_path=auth_path,
        repository_sha=REPO_SHA,
        venue=BOUND_VENUE,
        instrument_id=BOUND_INSTRUMENT_ID,
        market_data_scope=BOUND_VENUE_SCOPE,
        evidence_scope=BOUND_EVIDENCE_SCOPE,
        max_cycles=2,
        evidence_root=tmp_path,
        git_baseline=_baseline(),
        http_fetcher=fetcher,
        md_sleep=clock.sleep,
        md_monotonic_clock=clock,
    )
    assert result["status"] == "PASS"
    payload = json.loads(Path(result["preflight"]["session_manifest_path"]).read_text())
    bind = payload["md_telemetry"]["instrument_binding"]
    assert bind["canonical_instrument_id"] == BOUND_INSTRUMENT_ID
    assert bind["venue_instrument_id"] == BOUND_INSTRUMENT_ID
    assert bind["mapping_digest"]
    assert bind["second_mapping_authority_present"] is False
    assert (
        payload["md_telemetry"]["effective_budget"]["effective"]["effective_maximum_requests"] > 0
    )
    assert payload["side_effect_probe"]["events"].index("AUTHORIZATION_CONSUMED") < payload[
        "side_effect_probe"
    ]["events"].index("TRANSPORT_OPENED")
