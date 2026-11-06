"""Offline failure-injection matrix for Step-6 productive Real-Network path."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as PREDECESSOR_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (
    prove_adverse_stale_executor_binding_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.constants_v1 import (
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    MAX_NETWORK_SESSION_COUNT,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT,
    STEP7_STARTED,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.executor_contrast_v1 import (
    prove_binding_vs_productive_executor_contrast_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.productive_executor_v1 import (
    evaluate_productive_real_network_execution_gate_v1,
    invoke_productive_executor_offline_fail_closed_v1,
    prove_productive_real_network_execution_path_v1,
)


def run_step6_productive_execution_path_failure_injection_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def _add(name: str, ok: bool, detail: dict[str, Any] | None = None) -> None:
        cases.append({"case": name, "ok": ok, "detail": detail or {}})

    proof = prove_productive_real_network_execution_path_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )
    _add(
        "default_path_proof_cannot_start_network",
        bool(proof.ok)
        and proof.network_session_started is False
        and proof.network_calls == 0
        and proof.confirm_token_minted is False
        and proof.confirm_token_consumed is False,
        {"ok": proof.ok, "claims": proof.claims},
    )

    contrast = prove_binding_vs_productive_executor_contrast_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )
    _add(
        "binding_executor_remains_real_network_forbidden",
        bool(contrast.get("ok"))
        and bool((contrast.get("binding_executor") or {}).get("real_network_forbidden")),
        contrast,
    )
    _add(
        "only_productive_executor_authorizes_may_start_under_go",
        bool(contrast.get("ok"))
        and bool(
            (contrast.get("productive_real_network_executor") or {}).get(
                "network_session_may_start_under_full_go"
            )
        )
        and not bool((contrast.get("binding_executor") or {}).get("network_session_may_start")),
        {
            "binding_may_start": (contrast.get("binding_executor") or {}).get(
                "network_session_may_start"
            ),
            "productive_may_start": (contrast.get("productive_real_network_executor") or {}).get(
                "network_session_may_start_under_full_go"
            ),
        },
    )

    no_go = invoke_productive_executor_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
    )
    _add(
        "productive_executor_fails_without_network_session_go",
        (not no_go.ok)
        and no_go.network_session_started is False
        and not no_go.network_session_may_start
        and "NETWORK_SESSION_GO_REQUIRED" in no_go.blockers,
        {"blockers": no_go.blockers},
    )

    orders = evaluate_productive_real_network_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=False,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        stdin_isatty=True,
    )
    _add(
        "orders_credentials_unreachable_public_md_only_required",
        (not orders.get("ok"))
        and "PUBLIC_MD_ONLY_REQUIRED" in (orders.get("blockers") or [])
        and bool(proof.claims.get("ORDERS_DISABLED"))
        and proof.claims.get("ORDER_SIDE_EFFECT_REACHABLE") is False
        and proof.claims.get("CREDENTIAL_PATH_REACHABLE") is False,
        {"blockers": orders.get("blockers"), "claims": proof.claims},
    )

    _add(
        "no_confirm_token_mint_or_consume_in_this_capability",
        proof.confirm_token_minted is False
        and proof.confirm_token_consumed is False
        and CONFIRM_TOKEN_ISSUANCE_ALLOWED is False
        and CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False
        and proof.claims.get("CONFIRM_TOKEN_MINTED") is False
        and proof.claims.get("CONFIRM_TOKEN_CONSUMED") is False
        and proof.claims.get("HIDDEN_CONFIRM_HANDOFF_USED") is False,
        {},
    )

    stale = prove_adverse_stale_executor_binding_v1()
    _add(
        "failure_injection_binding_preserved",
        bool(stale.get("ok"))
        and bool((stale.get("classification") or {}).get("ok"))
        and bool((stale.get("receive_lag_enabled_binding") or {}).get("receive_lag_schedule")),
        {"stale_ok": stale.get("ok")},
    )

    _add(
        "step6_verifier_bound_and_step6_remains_open",
        bool(proof.ok)
        and bool(proof.claims.get("STEP6_VERIFIER_BOUND"))
        and PHASE_9_2_STEP_6_STATUS == "OPEN"
        and STEP7_STARTED is False
        and STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT is True,
        {},
    )

    _add(
        "permanent_network_flags_remain_false",
        NETWORK_SESSION_ALLOWED is False and PREDECESSOR_NETWORK_SESSION_ALLOWED is False,
        {
            "NETWORK_SESSION_ALLOWED": NETWORK_SESSION_ALLOWED,
            "PREDECESSOR_NETWORK_SESSION_ALLOWED": PREDECESSOR_NETWORK_SESSION_ALLOWED,
        },
    )

    _add(
        "max_session_count_exactly_one",
        MAX_NETWORK_SESSION_COUNT == 1 and proof.claims.get("MAX_NETWORK_SESSION_COUNT") == 1,
        {"MAX_NETWORK_SESSION_COUNT": MAX_NETWORK_SESSION_COUNT},
    )

    side_effects = invoke_productive_executor_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        stdin_isatty=True,
    )
    _add(
        "implementation_capability_forbids_real_network_side_effects",
        (not side_effects.ok)
        and side_effects.network_session_started is False
        and "REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY"
        in side_effects.blockers,
        {"blockers": side_effects.blockers},
    )

    ok = all(bool(c.get("ok")) for c in cases)
    return {
        "ok": ok,
        "FAILURE_INJECTION_TESTS_PASS": ok,
        "cases": cases,
        "network_session_started": False,
        "network_calls": 0,
        "confirm_token_minted": False,
        "confirm_token_consumed": False,
        "authorization_consumed": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT": True,
    }
