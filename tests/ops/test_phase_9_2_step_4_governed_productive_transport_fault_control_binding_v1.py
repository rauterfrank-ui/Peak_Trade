"""Tests for PHASE_9_2_STEP_4_GOVERNED_PRODUCTIVE_TRANSPORT_FAULT_CONTROL_BINDING_IMPLEMENTATION_V1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    classify_transport_message_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.rate_limit_metric_v1 import (
    compute_rate_limit_event_count_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_injected_transport_fault_v1 import (  # noqa: E501
    CAPABILITY_ID,
    FAULT_ORIGIN_GOVERNED,
    GovernedInjectedTransportDisconnectError,
    GovernedInjectedTransportFaultWrapperV1,
    GovernedTransportFaultControlError,
    GovernedTransportFaultScheduleV1,
    GovernedTransportFaultSpecV1,
    assert_schedule_bindings_v1,
    build_default_step4_fault_schedule_v1,
    build_transport_telemetry_document_v1,
    wrap_fetcher_with_governed_fault_control_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.productive_transport_fault_control_verifier_v1 import (  # noqa: E501
    verify_step4_productive_transport_fault_control_evidence_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (  # noqa: E501
    build_real_eea_public_md_transport_v1,
)

SHA = "a" * 40
CFG = "b" * 64
SESSION = "phase_9_2_public_md_rate_limit_reconnect_session_v1"


def _ok_body() -> bytes:
    return json.dumps({"code": "0", "data": [{"ts": "1700000000000"}]}).encode("utf-8")


def _real_ok_fetcher(url: str, method: str, headers: object, timeout: float):
    del url, method, headers, timeout
    return 200, _ok_body(), {"Content-Type": "application/json"}


def _enabled_schedule(
    *,
    http_429_after: int = 2,
    disconnect_after: int = 4,
) -> GovernedTransportFaultScheduleV1:
    return build_default_step4_fault_schedule_v1(
        schedule_id="sched_test_v1",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth_test",
        http_429_after_successful_gets=http_429_after,
        disconnect_after_successful_gets=disconnect_after,
        enabled=True,
    )


def test_wrapper_passthrough_when_schedule_none() -> None:
    wrapped = wrap_fetcher_with_governed_fault_control_v1(_real_ok_fetcher, None)
    assert wrapped is _real_ok_fetcher


def test_wrapper_passthrough_when_disabled() -> None:
    schedule = build_default_step4_fault_schedule_v1(
        schedule_id="sched_off",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth_test",
        enabled=False,
    )
    wrapped = wrap_fetcher_with_governed_fault_control_v1(_real_ok_fetcher, schedule)
    assert wrapped is _real_ok_fetcher


def test_default_build_transport_without_schedule_uses_real_fetcher_path(monkeypatch) -> None:
    calls: list[str] = []

    def fake_make(**kwargs):  # noqa: ANN003
        del kwargs

        def fetcher(url, method, headers, timeout):  # noqa: ANN001
            calls.append("real")
            return 200, _ok_body(), {"Content-Type": "application/json"}

        class Tel:
            def to_dict(self):
                return {}

        return fetcher, Tel()

    monkeypatch.setattr(
        "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1.make_real_eea_public_md_fetcher_v1",
        fake_make,
    )
    transport, _tel = build_real_eea_public_md_transport_v1(environ={"PATH": "/usr/bin"})
    transport.open()
    result = transport.get_json("/api/v5/public/time", {})
    assert result.status == 200
    assert calls == ["real"]
    assert not isinstance(transport.fetcher, GovernedInjectedTransportFaultWrapperV1)


def test_http_429_injection_once_then_delegate() -> None:
    from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (  # noqa: E501
        PublicMdRequestPacingPolicyV1,
    )

    sleeps: list[float] = []
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id="s429",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth_test",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="f429",
                sequence=1,
                kind="HTTP_429",
                after_successful_gets=1,
                retry_after_seconds=2.0,
            ),
        ),
    )
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=1.0,
        maximum_requests_per_session=100,
        maximum_requests_per_cycle=3,
        maximum_consecutive_rate_limits=3,
        retry_after_max_seconds=60.0,
        backoff_initial_seconds=1.0,
        backoff_multiplier=2.0,
        backoff_max_seconds=30.0,
        jitter_fraction=0.0,
    )
    policy.validate()
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_real_ok_fetcher, schedule=schedule
    )
    transport = EeaPublicMdTransportV1(
        fetcher=wrapper,
        max_retries=2,
        session_http_429_budget=5,
        sleep=sleeps.append,
        environ={"PATH": "/usr/bin"},
        rate_limit_policy=policy,
        jitter_unit_fn=lambda _i: 0.0,
    )
    transport.open()
    # First successful real GET
    assert transport.get_json("/api/v5/public/time", {}).status == 200
    # Second call hits injection point (after_successful_gets=1) → 429 then retry → ok
    assert transport.get_json("/api/v5/public/time", {}).status == 200
    assert transport.http_429_count == 1
    assert wrapper.telemetry.http_429_injected_count == 1
    assert sleeps and sleeps[0] == 2.0
    assert wrapper.telemetry.events[0]["fault_origin"] == FAULT_ORIGIN_GOVERNED
    # Further calls stay delegated (no second 429 injection)
    assert transport.get_json("/api/v5/public/time", {}).status == 200
    assert transport.http_429_count == 1


def test_rate_limit_metric_counts_injected_429_once() -> None:
    payloads = [
        {
            "http_status": 429,
            "fault_origin": FAULT_ORIGIN_GOVERNED,
            "fault_id": "f429",
        }
    ]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 1


def test_session_id_substring_not_counted_as_rate_limit() -> None:
    payloads = [
        {"session_id": SESSION, "event": "bridge_cycle_completed"},
        {"session_id": SESSION, "event": "bridge_cycle_completed"},
    ]
    assert compute_rate_limit_event_count_v1(payloads=payloads) == 0


def test_disconnect_injection_classified_reconnectable() -> None:
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id="sdisc",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth_test",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="fdisc",
                sequence=1,
                kind="TRANSPORT_DISCONNECT",
                after_successful_gets=1,
                disconnect_error_token="URL_ERROR",
            ),
        ),
    )
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_real_ok_fetcher, schedule=schedule
    )
    wrapper(_u := "https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
    with pytest.raises(GovernedInjectedTransportDisconnectError) as exc:
        wrapper(_u, "GET", {}, 1.0)
    msg = str(exc.value)
    cls, reconnectable = classify_transport_message_v1(f"FETCH_FAILED:{msg}")
    assert reconnectable is True
    assert cls == "TRANSPORT_FAILURE"
    assert FAULT_ORIGIN_GOVERNED in msg


def test_transport_raises_fetch_failed_on_injected_disconnect() -> None:
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id="sdisc2",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth_test",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="fdisc2",
                sequence=1,
                kind="TRANSPORT_DISCONNECT",
                after_successful_gets=1,
                disconnect_error_token="TIMEOUT",
            ),
        ),
    )
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_real_ok_fetcher, schedule=schedule
    )
    transport = EeaPublicMdTransportV1(
        fetcher=wrapper,
        max_retries=0,
        sleep=lambda _s: None,
        environ={"PATH": "/usr/bin"},
    )
    transport.open()
    transport.get_json("/api/v5/public/time", {})
    with pytest.raises(EeaPublicMdTransportError) as exc:
        transport.get_json("/api/v5/public/time", {})
    assert "FETCH_FAILED" in str(exc.value)
    assert FAULT_ORIGIN_GOVERNED in str(exc.value)


def test_schedule_rejects_zero_interval_and_flooding() -> None:
    with pytest.raises(GovernedTransportFaultControlError):
        GovernedTransportFaultScheduleV1(
            schedule_id="bad",
            session_id=SESSION,
            expected_repository_sha=SHA,
            expected_config_digest=CFG,
            authorization_id="auth",
            enabled=True,
            faults=(
                GovernedTransportFaultSpecV1(
                    fault_id="f1",
                    sequence=1,
                    kind="HTTP_429",
                    after_successful_gets=0,
                    retry_after_seconds=1.0,
                ),
            ),
        ).validate()
    with pytest.raises(GovernedTransportFaultControlError):
        GovernedTransportFaultScheduleV1(
            schedule_id="bad2",
            session_id=SESSION,
            expected_repository_sha=SHA,
            expected_config_digest=CFG,
            authorization_id="auth",
            enabled=True,
            faults=(
                GovernedTransportFaultSpecV1(
                    fault_id="f1",
                    sequence=1,
                    kind="HTTP_429",
                    after_successful_gets=1,
                    retry_after_seconds=0.0,
                ),
            ),
        ).validate()


def test_schedule_binding_fail_closed() -> None:
    schedule = _enabled_schedule()
    with pytest.raises(GovernedTransportFaultControlError):
        assert_schedule_bindings_v1(
            schedule,
            session_id="wrong",
            repository_sha=SHA,
            config_digest=CFG,
            authorization_id="auth_test",
        )
    with pytest.raises(GovernedTransportFaultControlError):
        assert_schedule_bindings_v1(
            schedule,
            session_id=SESSION,
            repository_sha="0" * 40,
            config_digest=CFG,
            authorization_id="auth_test",
        )


def test_duplicate_fault_id_rejected() -> None:
    with pytest.raises(GovernedTransportFaultControlError):
        GovernedTransportFaultScheduleV1(
            schedule_id="dup",
            session_id=SESSION,
            expected_repository_sha=SHA,
            expected_config_digest=CFG,
            authorization_id="auth",
            enabled=True,
            faults=(
                GovernedTransportFaultSpecV1(
                    fault_id="same",
                    sequence=1,
                    kind="HTTP_429",
                    after_successful_gets=1,
                    retry_after_seconds=1.0,
                ),
                GovernedTransportFaultSpecV1(
                    fault_id="same",
                    sequence=2,
                    kind="TRANSPORT_DISCONNECT",
                    after_successful_gets=2,
                    disconnect_error_token="URL_ERROR",
                ),
            ),
        ).validate()


def test_out_of_order_sequence_rejected() -> None:
    with pytest.raises(GovernedTransportFaultControlError):
        GovernedTransportFaultScheduleV1(
            schedule_id="oo",
            session_id=SESSION,
            expected_repository_sha=SHA,
            expected_config_digest=CFG,
            authorization_id="auth",
            enabled=True,
            faults=(
                GovernedTransportFaultSpecV1(
                    fault_id="f2",
                    sequence=2,
                    kind="HTTP_429",
                    after_successful_gets=1,
                    retry_after_seconds=1.0,
                ),
                GovernedTransportFaultSpecV1(
                    fault_id="f1",
                    sequence=1,
                    kind="TRANSPORT_DISCONNECT",
                    after_successful_gets=2,
                    disconnect_error_token="URL_ERROR",
                ),
            ),
        ).validate()


def test_no_market_observation_injection_on_429() -> None:
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id="nomkt",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="f429",
                sequence=1,
                kind="HTTP_429",
                after_successful_gets=1,
                retry_after_seconds=1.0,
            ),
        ),
    )
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_real_ok_fetcher, schedule=schedule
    )
    wrapper("https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
    status, body, headers = wrapper("https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
    assert status == 429
    assert body == b"{}"
    assert b"mark" not in body.lower()
    assert "markPx" not in headers
    assert wrapper.telemetry.fabricated_observation_count == 0


def test_verifier_rejects_substring_only_and_false_positive(tmp_path: Path) -> None:
    wc = tmp_path / "wallclock_session"
    wc.mkdir()
    (wc / "session_manifest.json").write_text(
        json.dumps({"session_id": SESSION}) + "\n", encoding="utf-8"
    )
    (wc / "transport_telemetry.json").write_text(
        json.dumps(
            {
                "http_429_count": 0,
                "rate_limit_event_count": 0,
                "governed_injected_fault_count": 0,
                "fabricated_observation_count": 0,
                "stale_gate_activation_count": 0,
                "reconnect_attempt_count": 0,
                "reconnect_success_count": 0,
                "post_reconnect_reconciliation_count": 0,
                "post_reconnect_continuation_count": 0,
                "events": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (wc / "runtime_events.jsonl").write_text(
        json.dumps({"session_id": SESSION, "event": "bridge_cycle_completed"}) + "\n",
        encoding="utf-8",
    )
    (wc / "reconnect_events.jsonl").write_text("", encoding="utf-8")
    (wc / "connectivity_events.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "operator_public_result.json").write_text(
        json.dumps(
            {
                "public_market_data_request_count": 108,
                "rate_limit_runtime_mentions": 108,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = verify_step4_productive_transport_fault_control_evidence_v1(
        evidence_root=tmp_path,
        claims={"rate_limit_runtime_mentions": 108},
    )
    assert result["ok"] is False
    assert "TYPED_HTTP_429_OR_RATE_LIMIT_EVENT_MISSING" in result["blockers"]
    assert "RATE_LIMIT_RUNTIME_MENTIONS_EQUALS_REQUEST_COUNT" in result["blockers"]
    assert "SUBSTRING_RATE_LIMIT_RUNTIME_MENTIONS_FORBIDDEN" in result["blockers"]


def test_verifier_pass_with_typed_injected_evidence(tmp_path: Path) -> None:
    wc = tmp_path / "wallclock_session"
    wc.mkdir()
    telemetry = build_transport_telemetry_document_v1(
        session_id=SESSION,
        transport_http_429_count=1,
        transport_events=[],
        wrapper_telemetry=None,
        reconnect_attempt_count=1,
        reconnect_success_count=1,
        post_reconnect_continuation_count=1,
        post_reconnect_reconciliation_count=1,
        stale_gate_activation_count=0,
        rate_limit_event_count=1,
        natural_transport_fault_count=0,
        last_retry_after_raw="2",
        last_retry_after_parsed_seconds=2.0,
        last_backoff_source="retry_after",
        last_backoff_seconds=2.0,
    )
    telemetry["governed_injected_fault_count"] = 1
    telemetry["events"] = [
        {
            "fault_id": "f429",
            "kind": "HTTP_429",
            "fault_origin": FAULT_ORIGIN_GOVERNED,
            "http_status": 429,
        }
    ]
    (wc / "transport_telemetry.json").write_text(json.dumps(telemetry) + "\n", encoding="utf-8")
    (wc / "session_manifest.json").write_text(
        json.dumps({"session_id": SESSION}) + "\n", encoding="utf-8"
    )
    (wc / "reconnect_events.jsonl").write_text(
        json.dumps(
            {
                "attempt": 1,
                "reconnectable": True,
                "fault_origin": FAULT_ORIGIN_GOVERNED,
                "session_id": SESSION,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (wc / "connectivity_events.jsonl").write_text(
        json.dumps(
            {
                "event": "transport_disconnect",
                "fault_origin": FAULT_ORIGIN_GOVERNED,
            }
        )
        + "\n"
        + json.dumps(
            {
                "event": "transport_reconnect_success",
                "fault_origin": FAULT_ORIGIN_GOVERNED,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (wc / "runtime_events.jsonl").write_text(
        json.dumps(
            {
                "event": "post_reconnect_reconciliation_before_alpha",
                "ok": True,
                "alpha_enabled": True,
                "session_id": SESSION,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (wc / "terminal_verdict.json").write_text(
        json.dumps({"orders_submitted": False, "credentials_used": False}) + "\n",
        encoding="utf-8",
    )
    (wc / "no_order_attestation.json").write_text(
        json.dumps({"orders_submitted": 0}) + "\n", encoding="utf-8"
    )
    result = verify_step4_productive_transport_fault_control_evidence_v1(
        evidence_root=tmp_path,
        claims={"GOVERNED_INJECTED_TRANSPORT_FAULT_USED": True},
    )
    assert result["ok"] is True, result["blockers"]
    assert result["claims"]["GOVERNED_INJECTED_TRANSPORT_FAULT_USED"] is True
    assert result["claims"]["NATURAL_EXCHANGE_HTTP_429_OBSERVED"] is False


def test_verifier_rejects_injected_as_natural(tmp_path: Path) -> None:
    wc = tmp_path / "wallclock_session"
    wc.mkdir()
    telemetry = build_transport_telemetry_document_v1(
        session_id=SESSION,
        transport_http_429_count=1,
        transport_events=[],
        wrapper_telemetry=None,
        reconnect_attempt_count=1,
        reconnect_success_count=1,
        post_reconnect_continuation_count=1,
        post_reconnect_reconciliation_count=1,
        stale_gate_activation_count=0,
        rate_limit_event_count=1,
    )
    telemetry["governed_injected_fault_count"] = 1
    telemetry["events"] = [{"http_status": 429, "fault_origin": FAULT_ORIGIN_GOVERNED}]
    (wc / "transport_telemetry.json").write_text(json.dumps(telemetry) + "\n", encoding="utf-8")
    (wc / "reconnect_events.jsonl").write_text(
        json.dumps({"attempt": 1, "fault_origin": FAULT_ORIGIN_GOVERNED}) + "\n",
        encoding="utf-8",
    )
    (wc / "connectivity_events.jsonl").write_text(
        json.dumps({"event": "transport_disconnect", "fault_origin": FAULT_ORIGIN_GOVERNED})
        + "\n"
        + json.dumps(
            {"event": "transport_reconnect_success", "fault_origin": FAULT_ORIGIN_GOVERNED}
        )
        + "\n",
        encoding="utf-8",
    )
    (wc / "runtime_events.jsonl").write_text(
        json.dumps(
            {
                "event": "post_reconnect_reconciliation_before_alpha",
                "ok": True,
                "alpha_enabled": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (wc / "terminal_verdict.json").write_text(
        json.dumps({"orders_submitted": False, "credentials_used": False}) + "\n",
        encoding="utf-8",
    )
    result = verify_step4_productive_transport_fault_control_evidence_v1(
        evidence_root=tmp_path,
        claims={
            "NATURAL_EXCHANGE_HTTP_429_OBSERVED": True,
            "GOVERNED_INJECTED_TRANSPORT_FAULT_USED": True,
        },
    )
    assert result["ok"] is False
    assert "INJECTED_CLAIMED_AS_NATURAL_HTTP_429" in result["blockers"]


def test_failure_injection_matrix_pass() -> None:
    from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.transport_fault_control_failure_injection_v1 import (  # noqa: E501
        run_transport_fault_control_failure_injection_v1,
    )

    result = run_transport_fault_control_failure_injection_v1()
    assert result["ok"] is True, result
    assert result["network_session_started"] is False


def test_capability_constants() -> None:
    assert CAPABILITY_ID.endswith("TRANSPORT_FAULT_CONTROL_BINDING_IMPLEMENTATION_V1")


def test_fault_before_injection_point_no_injection() -> None:
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id="early",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="f429",
                sequence=1,
                kind="HTTP_429",
                after_successful_gets=3,
                retry_after_seconds=1.0,
            ),
        ),
    )
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_real_ok_fetcher, schedule=schedule
    )
    for _ in range(3):
        status, _body, _headers = wrapper("https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
        assert status == 200
    assert wrapper.telemetry.governed_injected_fault_count == 0
    # 4th call: successful_gets==3 → inject
    status, body, _headers = wrapper("https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
    assert status == 429
    assert body == b"{}"


def test_restart_after_consume_does_not_reinject() -> None:
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id="once",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="f429",
                sequence=1,
                kind="HTTP_429",
                after_successful_gets=1,
                retry_after_seconds=1.0,
            ),
        ),
    )
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_real_ok_fetcher, schedule=schedule
    )
    wrapper("https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
    status1, _, _ = wrapper("https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
    assert status1 == 429
    status2, _, _ = wrapper("https://eea.okx.com/api/v5/public/time", "GET", {}, 1.0)
    assert status2 == 200
    assert wrapper.telemetry.http_429_injected_count == 1
