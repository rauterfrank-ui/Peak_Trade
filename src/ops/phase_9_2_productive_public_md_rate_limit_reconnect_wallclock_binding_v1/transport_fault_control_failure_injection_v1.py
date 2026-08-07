"""Failure-injection matrix for governed productive transport fault-control binding."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_injected_transport_fault_v1 import (  # noqa: E501
    CAPABILITY_ID,
    GovernedInjectedTransportFaultWrapperV1,
    GovernedTransportFaultControlError,
    GovernedTransportFaultScheduleV1,
    GovernedTransportFaultSpecV1,
    assert_schedule_bindings_v1,
    build_default_step4_fault_schedule_v1,
)

SHA = "c" * 40
CFG = "d" * 64
SESSION = "phase_9_2_public_md_rate_limit_reconnect_session_v1"


def _ok_fetcher(url: str, method: str, headers: object, timeout: float):
    del url, method, headers, timeout
    return 200, b'{"code":"0","data":[{"ts":"1"}]}', {"Content-Type": "application/json"}


def run_transport_fault_control_failure_injection_v1() -> dict[str, Any]:
    """Offline fail-closed cases for schedule/wrapper contracts."""
    results: dict[str, Any] = {}

    def _case(name: str, ok: bool, detail: str = "") -> None:
        results[name] = {"ok": bool(ok), "expected_fail_closed": True, "detail": detail}

    # Disabled schedule with bindings asserted → fail
    disabled = build_default_step4_fault_schedule_v1(
        schedule_id="fi_disabled",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth",
        enabled=False,
    )
    try:
        assert_schedule_bindings_v1(
            disabled,
            session_id=SESSION,
            repository_sha=SHA,
            config_digest=CFG,
            authorization_id="auth",
        )
        _case("feature_disabled_despite_schedule", False, "expected raise")
    except GovernedTransportFaultControlError as exc:
        _case("feature_disabled_despite_schedule", True, str(exc))

    # Wrong session id
    enabled = build_default_step4_fault_schedule_v1(
        schedule_id="fi_sess",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth",
        enabled=True,
    )
    try:
        assert_schedule_bindings_v1(
            enabled,
            session_id="other_session",
            repository_sha=SHA,
            config_digest=CFG,
            authorization_id="auth",
        )
        _case("wrong_session_id", False)
    except GovernedTransportFaultControlError as exc:
        _case("wrong_session_id", True, str(exc))

    # Wrong SHA
    try:
        assert_schedule_bindings_v1(
            enabled,
            session_id=SESSION,
            repository_sha="0" * 40,
            config_digest=CFG,
            authorization_id="auth",
        )
        _case("wrong_repository_sha", False)
    except GovernedTransportFaultControlError as exc:
        _case("wrong_repository_sha", True, str(exc))

    # Wrong config digest
    try:
        assert_schedule_bindings_v1(
            enabled,
            session_id=SESSION,
            repository_sha=SHA,
            config_digest="e" * 64,
            authorization_id="auth",
        )
        _case("wrong_config_digest", False)
    except GovernedTransportFaultControlError as exc:
        _case("wrong_config_digest", True, str(exc))

    # Corrupt / mismatched digest identity
    digest_a = enabled.digest()
    mutated = build_default_step4_fault_schedule_v1(
        schedule_id="fi_sess_mutated",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth",
        enabled=True,
    )
    _case("corrupt_schedule_digest_detected", digest_a != mutated.digest())

    # Duplicate fault id
    try:
        GovernedTransportFaultScheduleV1(
            schedule_id="dup",
            session_id=SESSION,
            expected_repository_sha=SHA,
            expected_config_digest=CFG,
            authorization_id="auth",
            enabled=True,
            faults=(
                GovernedTransportFaultSpecV1(
                    fault_id="x",
                    sequence=1,
                    kind="HTTP_429",
                    after_successful_gets=1,
                    retry_after_seconds=1.0,
                ),
                GovernedTransportFaultSpecV1(
                    fault_id="x",
                    sequence=2,
                    kind="TRANSPORT_DISCONNECT",
                    after_successful_gets=2,
                    disconnect_error_token="URL_ERROR",
                ),
            ),
        ).validate()
        _case("duplicate_fault_id", False)
    except GovernedTransportFaultControlError as exc:
        _case("duplicate_fault_id", True, str(exc))

    # Out-of-order sequence
    try:
        GovernedTransportFaultScheduleV1(
            schedule_id="oo",
            session_id=SESSION,
            expected_repository_sha=SHA,
            expected_config_digest=CFG,
            authorization_id="auth",
            enabled=True,
            faults=(
                GovernedTransportFaultSpecV1(
                    fault_id="a",
                    sequence=2,
                    kind="HTTP_429",
                    after_successful_gets=1,
                    retry_after_seconds=1.0,
                ),
                GovernedTransportFaultSpecV1(
                    fault_id="b",
                    sequence=1,
                    kind="TRANSPORT_DISCONNECT",
                    after_successful_gets=2,
                    disconnect_error_token="URL_ERROR",
                ),
            ),
        ).validate()
        _case("out_of_order_sequence", False)
    except GovernedTransportFaultControlError as exc:
        _case("out_of_order_sequence", True, str(exc))

    # Double consume prevention (wrapper internal)
    single = GovernedTransportFaultScheduleV1(
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
    wrapper = GovernedInjectedTransportFaultWrapperV1(real_fetcher=_ok_fetcher, schedule=single)
    wrapper("u", "GET", {}, 1.0)
    wrapper("u", "GET", {}, 1.0)  # inject
    # Force re-consume should raise
    try:
        wrapper._consume(single.faults[0])  # noqa: SLF001 — intentional failure injection
        _case("double_consume_rejected", False)
    except GovernedTransportFaultControlError as exc:
        _case("double_consume_rejected", True, str(exc))

    ok = all(bool(v.get("ok")) for v in results.values())
    return {
        "ok": ok,
        "capability_id": CAPABILITY_ID,
        "network_session_started": False,
        "cases": results,
        "claims": {
            "FAILURE_INJECTION_MATRIX_PASS": ok,
            "NO_NETWORK": True,
        },
    }
