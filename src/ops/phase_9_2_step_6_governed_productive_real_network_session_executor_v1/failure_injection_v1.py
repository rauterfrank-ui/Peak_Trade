"""Offline failure-injection matrix for Step-6 productive executor binding."""

from __future__ import annotations

import hashlib
from typing import Any

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as PREDECESSOR_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (
    prepare_adverse_stale_runtime_overrides_v1,
    prove_adverse_stale_executor_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    MAX_NETWORK_SESSION_COUNT,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.governed_session_execution_v1 import (
    evaluate_productive_session_gate_v1,
    execute_governed_step6_productive_session_offline_fail_closed_v1,
    prove_step6_productive_executor_binding_v1,
    request_real_network_offline_fail_closed_v1,
)


def run_step6_productive_executor_failure_injection_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def _add(name: str, ok: bool, detail: dict[str, Any] | None = None) -> None:
        cases.append({"case": name, "ok": ok, "detail": detail or {}})

    proof = prove_step6_productive_executor_binding_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )
    _add(
        "default_invocation_cannot_start_network",
        bool(proof.ok) and proof.network_session_started is False and proof.network_calls == 0,
        {"ok": proof.ok, "network_session_started": proof.network_session_started},
    )

    non_tty = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="auth_1",
        authorization_digest="b" * 64,
        confirm_token_binding_sha256="c" * 64,
        getpass_fn=lambda _p: "must-not-consume",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=False,
    )
    _add(
        "non_tty_cannot_start_network",
        (not non_tty.ok)
        and non_tty.network_session_started is False
        and non_tty.confirm_token_consumed is False
        and any("TTY" in b for b in non_tty.blockers),
        {"blockers": non_tty.blockers},
    )

    missing_go = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="auth_1",
        authorization_digest="d" * 64,
        confirm_token_binding_sha256=hashlib.sha256(b"tok").hexdigest(),
        getpass_fn=lambda _p: "tok",
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=True,
    )
    _add(
        "missing_owner_go_cannot_start_network",
        (not missing_go.ok)
        and missing_go.network_session_started is False
        and "OWNER_GO_REQUIRED" in missing_go.blockers,
        {"blockers": missing_go.blockers},
    )

    invalid_confirm = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="auth_1",
        authorization_digest="e" * 64,
        confirm_token_binding_sha256=hashlib.sha256(b"expected").hexdigest(),
        getpass_fn=lambda _p: "wrong",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=True,
    )
    _add(
        "invalid_confirm_token_cannot_start_network",
        (not invalid_confirm.ok)
        and invalid_confirm.confirm_token_consumed is False
        and any("CONFIRM_TOKEN" in b for b in invalid_confirm.blockers),
        {"blockers": invalid_confirm.blockers},
    )

    gate_no_stale = evaluate_productive_session_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=False,
        stdin_isatty=True,
    )
    _add(
        "stale_control_absent_cannot_start_step6_session",
        (not gate_no_stale.get("ok"))
        and "STALE_CONTROL_ABSENT" in (gate_no_stale.get("blockers") or []),
        gate_no_stale,
    )

    _add(
        "permanent_network_session_allowed_flip_not_required",
        NETWORK_SESSION_ALLOWED is False and PREDECESSOR_NETWORK_SESSION_ALLOWED is False,
        {
            "NETWORK_SESSION_ALLOWED": NETWORK_SESSION_ALLOWED,
            "PREDECESSOR_NETWORK_SESSION_ALLOWED": PREDECESSOR_NETWORK_SESSION_ALLOWED,
        },
    )

    _add(
        "public_md_only_invariant",
        bool(proof.claims.get("PUBLIC_MD_ONLY_ENFORCED"))
        and proof.claims.get("PRIVATE_ENDPOINT_REACHABLE") is False
        and proof.claims.get("ORDER_SIDE_EFFECT_REACHABLE") is False,
        {
            "PUBLIC_MD_ONLY_ENFORCED": proof.claims.get("PUBLIC_MD_ONLY_ENFORCED"),
            "ORDERS_DISABLED": proof.claims.get("ORDERS_DISABLED"),
        },
    )

    _add(
        "order_trading_mutation_impossible",
        bool(proof.claims.get("ORDERS_DISABLED"))
        and proof.claims.get("ORDER_SIDE_EFFECT_REACHABLE") is False
        and proof.claims.get("CREDENTIAL_PATH_REACHABLE") is False,
        {},
    )

    stale = prove_adverse_stale_executor_binding_v1()
    _add(
        "step6_fault_schedule_reaches_receive_lag_control",
        bool(stale.get("ok"))
        and bool((stale.get("classification") or {}).get("ok"))
        and bool((stale.get("receive_lag_enabled_binding") or {}).get("receive_lag_schedule")),
        {"stale_ok": stale.get("ok")},
    )

    absent = prepare_adverse_stale_runtime_overrides_v1(enable_receive_lag=True)
    overrides = dict(absent.get("runtime_overrides") or {})
    overrides.pop("governed_stale_data_control", None)
    _add(
        "verifier_evidence_structurally_bound",
        bool(proof.ok)
        and bool(proof.claims.get("PRODUCTIVE_EXECUTOR_BOUND"))
        and PHASE_9_2_STEP_6_STATUS == "OPEN",
        {},
    )

    _add(
        "max_session_count_exactly_one",
        MAX_NETWORK_SESSION_COUNT == 1 and proof.claims.get("MAX_NETWORK_SESSION_COUNT") == 1,
        {"MAX_NETWORK_SESSION_COUNT": MAX_NETWORK_SESSION_COUNT},
    )

    req = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=True,
    )
    _add(
        "binding_capability_zero_network_calls",
        (not req.ok)
        and req.network_session_started is False
        and req.network_calls == 0
        and proof.network_calls == 0
        and "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in req.blockers,
        {"blockers": req.blockers},
    )

    ok = all(bool(c.get("ok")) for c in cases)
    return {
        "ok": ok,
        "FAILURE_INJECTION_TESTS_PASS": ok,
        "cases": cases,
        "network_session_started": False,
        "network_calls": 0,
        "confirm_token_consumed": False,
        "authorization_consumed": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
    }
