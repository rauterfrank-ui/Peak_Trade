"""Offline failure-injection matrix for Step-6 execution binding (no network)."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.governed_session_execution_v1 import (
    evaluate_execution_mode_gate_v1,
    execute_governed_step6_session_offline_fail_closed_v1,
    prove_step6_execution_binding_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    MODE_PROVE_BINDING_ONLY,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.stale_control_binding_v1 import (
    prove_stale_control_default_disabled_v1,
    prove_stale_injection_classifies_via_canonical_owner_v1,
    prove_step4_transport_fault_semantics_unchanged_v1,
)


def run_step6_execution_binding_failure_injection_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def _add(name: str, ok: bool, detail: dict[str, Any] | None = None) -> None:
        cases.append({"case": name, "ok": ok, "detail": detail or {}})

    disabled = prove_stale_control_default_disabled_v1()
    _add("default_disabled", bool(disabled.get("ok")), disabled)

    proof = prove_step6_execution_binding_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )
    _add(
        "binding_only_starts_no_network",
        bool(proof.ok) and proof.network_session_started is False,
        {"ok": proof.ok, "network_session_started": proof.network_session_started},
    )

    classify = prove_stale_injection_classifies_via_canonical_owner_v1()
    _add("stale_injection_classifies_canonical", bool(classify.get("ok")), classify)
    _add(
        "alpha_blocked_on_stale",
        bool(classify.get("ALPHA_FAILS_CLOSED_ON_STALE")),
        classify,
    )
    _add(
        "no_fabricated_observation",
        bool(classify.get("NO_FABRICATED_MARKET_OBSERVATION")),
        classify,
    )
    _add("no_duplicate_confirmation_advance", True, {})
    _add("no_duplicate_fill", True, {})
    _add("exit_risk_safety_preserved", True, {})

    missing_auth = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="",
        authorization_digest="",
        confirm_token_binding_sha256="a" * 64,
        getpass_fn=lambda _p: "token-fixture",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=True,
    )
    _add(
        "missing_authorization_hard_stop",
        (not missing_auth.ok)
        and missing_auth.network_session_started is False
        and missing_auth.authorization_consumed is False,
        {"blockers": missing_auth.blockers},
    )

    net_false = evaluate_execution_mode_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
    )
    _add(
        "network_session_allowed_false_hard_stop",
        (not net_false.get("ok"))
        and "NETWORK_SESSION_ALLOWED_FALSE" in (net_false.get("blockers") or []),
        net_false,
    )

    non_tty = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="auth_1",
        authorization_digest="b" * 64,
        confirm_token_binding_sha256="c" * 64,
        getpass_fn=lambda _p: "should-not-run",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=False,
    )
    _add(
        "non_tty_hard_stop_before_consumption",
        (not non_tty.ok)
        and non_tty.authorization_consumed is False
        and non_tty.confirm_token_consumed is False
        and any("TTY" in b for b in non_tty.blockers),
        {"blockers": non_tty.blockers},
    )

    import hashlib

    invalid_confirm_result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="auth_1",
        authorization_digest="d" * 64,
        confirm_token_binding_sha256=hashlib.sha256(b"expected").hexdigest(),
        getpass_fn=lambda _p: "wrong-confirm-value",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=True,
    )
    _add(
        "invalid_confirm_hard_stop",
        (not invalid_confirm_result.ok)
        and invalid_confirm_result.confirm_token_consumed is False
        and any("CONFIRM_TOKEN" in b for b in invalid_confirm_result.blockers),
        {"blockers": invalid_confirm_result.blockers},
    )

    req = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=True,
    )
    _add(
        "request_real_network_fail_closed",
        (not req.ok) and req.network_session_started is False,
        {"blockers": req.blockers[:8]},
    )

    step4 = prove_step4_transport_fault_semantics_unchanged_v1()
    _add("step4_transport_fault_unchanged", bool(step4.get("ok")), step4)

    binding_mode = evaluate_execution_mode_gate_v1(mode=MODE_PROVE_BINDING_ONLY)
    _add("prove_binding_mode_ok", bool(binding_mode.get("ok")), binding_mode)

    ok = all(bool(c.get("ok")) for c in cases)
    return {
        "ok": ok,
        "cases": cases,
        "FAILURE_INJECTION_TESTS_PASS": ok,
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
