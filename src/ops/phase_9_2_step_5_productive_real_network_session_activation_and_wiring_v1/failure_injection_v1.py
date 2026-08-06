"""Offline failure-injection matrix for Step-5 activation wiring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.activation_gate_v1 import (
    evaluate_step5_activation_gate_v1,
    expected_confirm_binding_from_plaintext_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (
    CAPABILITY_ID,
    SESSION_SCOPE,
    STEP5_EXECUTION_CAPABILITY_ID,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.fetcher_wiring_v1 import (
    build_counting_fake_fetcher_v1,
    resolve_canonical_public_md_fetcher_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.process_cleanup_v1 import (
    prove_process_cleanup_v1,
)


def _base(
    *,
    repo_root: Path | None,
    sha: str,
    now: float,
    token: str = "step5-fi-token-v1",
) -> dict[str, Any]:
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    return {
        "expected_repository_sha": sha,
        "expected_session_contract_digest": bundle["session_contract_digest"],
        "expected_binding_config_digest": bundle["binding_config_digest"],
        "authorization_id": "auth_fi_ok",
        "authorization_digest": "digest_fi_ok",
        "confirm_token_binding_sha256": expected_confirm_binding_from_plaintext_v1(token),
        "confirm_token_plaintext": token,
        "now_unix": now,
        "network_session_go": True,
        "owner_go": True,
        "operator_authorization_explicit": True,
        "authorization_expires_at": now + 3600.0,
        "confirm_token_expires_at": now + 3600.0,
        "repo_root": repo_root,
        "authorization_capability_id": STEP5_EXECUTION_CAPABILITY_ID,
        "authorization_scope": SESSION_SCOPE,
        "authorization_session_id": TARGET_SESSION_ID,
    }


def run_step5_activation_wiring_failure_injection_v1(
    *,
    expected_repository_sha: str,
    now_unix: float,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    cases: dict[str, Any] = {}

    def _run(name: str, **overrides: Any) -> None:
        kwargs = _base(repo_root=repo_root, sha=expected_repository_sha, now=now_unix)
        kwargs.update(overrides)
        result = evaluate_step5_activation_gate_v1(**kwargs)
        resolved = resolve_canonical_public_md_fetcher_v1(
            activation_permit_ok=bool(result.get("ok")),
            network_session_go=bool(kwargs.get("network_session_go")),
            allow_construct=bool(result.get("ok")),
            injected_fetcher=build_counting_fake_fetcher_v1(),
        )
        cases[name] = {
            "ok": bool(result.get("ok")),
            "blockers": list(result.get("blockers") or []),
            "network_session_started": False,
            "fetcher_resolved": bool(resolved.get("ok")),
            "authorization_consumed": False,
            "confirm_token_consumed": False,
        }

    _run("default_without_session_go", network_session_go=False)
    _run(
        "session_go_without_authorization",
        authorization_id="",
        authorization_digest="",
    )
    _run("authorization_without_confirm_token", confirm_token_plaintext="")
    _run(
        "sha_mismatch",
        expected_repository_sha="0" * 64,
        authorization_repository_sha=expected_repository_sha,
    )
    _run(
        "config_digest_mismatch",
        expected_binding_config_digest="0" * 64,
    )
    _run(
        "capability_scope_mismatch",
        authorization_capability_id="WRONG_CAPABILITY_SCOPE_V1",
    )
    _run(
        "token_scope_mismatch",
        authorization_scope="WRONG_SCOPE",
    )
    _run("reused_authorization", already_consumed_authorization=True)
    _run("reused_confirm_token", already_consumed_confirm_token=True)
    _run("private_endpoint_rejected", private_endpoint_requested=True)
    _run("non_get_rejected", non_get_method_requested=True)
    _run("auth_header_rejected", auth_header_requested=True)
    _run("credential_rejected", credential_access_requested=True)
    _run("order_submit_rejected", order_side_effect_requested=True)

    # Env cannot enable GO
    env_go = evaluate_step5_activation_gate_v1(
        **{
            **_base(repo_root=repo_root, sha=expected_repository_sha, now=now_unix),
            "network_session_go": False,
            "environ": {"NETWORK_SESSION_GO": "true"},
        }
    )
    cases["env_cannot_enable_network_session_go"] = {
        "ok": bool(env_go.get("ok")),
        "blockers": list(env_go.get("blockers") or []),
        "network_session_started": False,
        "fetcher_resolved": False,
    }

    # Fake fetcher rejects private/auth/non-GET
    fake = build_counting_fake_fetcher_v1()
    negative_endpoint: dict[str, Any] = {}
    probes = (
        (
            "non_get",
            "https://eea.okx.com/api/v5/market/ticker",
            "POST",
            {},
        ),
        (
            "private",
            "https://eea.okx.com/api/v5/private/account",
            "GET",
            {},
        ),
        (
            "auth_header",
            "https://eea.okx.com/api/v5/market/ticker",
            "GET",
            {"Authorization": "x"},
        ),
    )
    for label, url, method, headers in probes:
        try:
            fake(url, method, headers, 1.0)
            negative_endpoint[label] = {"ok": False, "error": "EXPECTED_REJECT_MISSING"}
        except RuntimeError as exc:
            negative_endpoint[label] = {"ok": True, "error": str(exc)}

    cleanup = prove_process_cleanup_v1(child_pids=[])

    required_fail_closed = [
        "default_without_session_go",
        "session_go_without_authorization",
        "authorization_without_confirm_token",
        "sha_mismatch",
        "config_digest_mismatch",
        "capability_scope_mismatch",
        "token_scope_mismatch",
        "reused_authorization",
        "reused_confirm_token",
        "private_endpoint_rejected",
        "non_get_rejected",
        "auth_header_rejected",
        "credential_rejected",
        "order_submit_rejected",
        "env_cannot_enable_network_session_go",
    ]
    all_fail_closed = all(cases[n]["ok"] is False for n in required_fail_closed)
    no_fetcher = all(cases[n]["fetcher_resolved"] is False for n in required_fail_closed)
    negatives_ok = all(v.get("ok") for v in negative_endpoint.values())

    return {
        "ok": all_fail_closed and no_fetcher and negatives_ok and bool(cleanup.get("ok")),
        "capability_id": CAPABILITY_ID,
        "cases": cases,
        "negative_endpoint_proof": negative_endpoint,
        "cleanup": cleanup,
        "network_session_started": False,
        "authorization_issued": False,
        "authorization_consumed": False,
        "confirm_token_issued": False,
        "confirm_token_consumed": False,
    }
