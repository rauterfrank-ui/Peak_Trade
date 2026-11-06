"""Offline failure-injection matrix for Step-7 productive campaign path."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT,
    STEP7_STARTED,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.executor_contrast_v1 import (
    prove_binding_vs_productive_campaign_executor_contrast_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.productive_campaign_executor_v1 import (
    evaluate_productive_campaign_execution_gate_v1,
    invoke_productive_campaign_executor_offline_fail_closed_v1,
    prove_productive_campaign_execution_path_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as BINDING_NETWORK_SESSION_ALLOWED,
)


def run_step7_productive_campaign_execution_path_failure_injection_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Any = None,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def _add(name: str, ok: bool, detail: dict[str, Any] | None = None) -> None:
        cases.append({"case": name, "ok": ok, "detail": detail or {}})

    proof = prove_productive_campaign_execution_path_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
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

    contrast = prove_binding_vs_productive_campaign_executor_contrast_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    _add(
        "binding_campaign_remains_real_network_forbidden",
        bool(contrast.get("ok"))
        and bool((contrast.get("binding_campaign_executor") or {}).get("real_network_forbidden")),
        contrast,
    )
    _add(
        "only_productive_campaign_authorizes_may_start_under_go",
        bool(contrast.get("ok"))
        and bool(
            (contrast.get("productive_campaign_executor") or {}).get(
                "campaign_may_start_under_full_go"
            )
        )
        and not bool(
            (contrast.get("binding_campaign_executor") or {}).get("network_session_may_start")
        ),
        {
            "binding_may_start": (contrast.get("binding_campaign_executor") or {}).get(
                "network_session_may_start"
            ),
            "productive_may_start": (contrast.get("productive_campaign_executor") or {}).get(
                "campaign_may_start_under_full_go"
            ),
        },
    )

    no_go = invoke_productive_campaign_executor_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        stdin_isatty=True,
        repo_root=repo_root,
    )
    _add(
        "productive_campaign_fails_without_network_session_go",
        (not no_go.ok)
        and no_go.network_session_started is False
        and not no_go.campaign_may_start
        and "NETWORK_SESSION_GO_REQUIRED" in no_go.blockers,
        {"blockers": no_go.blockers},
    )

    one = invoke_productive_campaign_executor_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=1,
        stdin_isatty=True,
        repo_root=repo_root,
    )
    _add(
        "productive_campaign_rejects_single_session",
        (not one.ok)
        and not one.campaign_may_start
        and "MULTI_SESSION_REQUIREMENT_NOT_SATISFIED" in one.blockers,
        {"blockers": one.blockers},
    )

    orders = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=False,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
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

    _add(
        "step7_harness_verifier_bound_and_step7_remains_open",
        bool(proof.ok)
        and bool(proof.claims.get("STEP7_CAMPAIGN_HARNESS_BOUND"))
        and bool(proof.claims.get("STEP7_CAMPAIGN_VERIFIER_PRESENT"))
        and PHASE_9_2_STEP_6_STATUS == "CLOSED_PASS"
        and PHASE_9_2_STEP_7_STATUS == "OPEN"
        and STEP7_STARTED is False
        and STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT is True,
        {},
    )

    _add(
        "permanent_network_flags_remain_false",
        NETWORK_SESSION_ALLOWED is False and BINDING_NETWORK_SESSION_ALLOWED is False,
        {
            "NETWORK_SESSION_ALLOWED": NETWORK_SESSION_ALLOWED,
            "BINDING_NETWORK_SESSION_ALLOWED": BINDING_NETWORK_SESSION_ALLOWED,
        },
    )

    _add(
        "multi_session_requirement_expression_gt_one",
        MULTI_SESSION_REQUIREMENT_EXPRESSION == ">1"
        and multi_session_requirement_satisfied_v1(1) is False
        and multi_session_requirement_satisfied_v1(2) is True
        and proof.claims.get("REPEATED_MULTI_SESSION_SUPPORTED") is True,
        {"expression": MULTI_SESSION_REQUIREMENT_EXPRESSION},
    )

    side_effects = invoke_productive_campaign_executor_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        stdin_isatty=True,
        repo_root=repo_root,
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
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT": True,
    }
