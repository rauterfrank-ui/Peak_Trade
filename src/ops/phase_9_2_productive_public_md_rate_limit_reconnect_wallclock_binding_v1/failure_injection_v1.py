"""Offline failure-injection matrix for rate-limit/reconnect wallclock binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.binding_gate_v1 import (
    evaluate_rate_limit_reconnect_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.fault_path_v1 import (
    prove_governed_fault_path_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_contract_v1 import (
    load_session_contract_v1,
    validate_session_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_go_v1 import (
    build_session_go_authority_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def _cfg(repo_root: Path) -> str:
    return str(
        load_activation_config_v1(
            config_path=repo_root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _issue_session_go(
    *,
    path: Path,
    repository_sha: str,
    config_digest: str,
    now: float,
    network_authorized: bool = True,
) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_phase92_rl_binding_fi_v1",
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        network_session_execution_authorized_by_this_go=network_authorized,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(path, auth.to_dict())


def run_rate_limit_reconnect_binding_failure_injection_v1(
    *,
    persistence_root: Path,
    repository_sha: str,
    repo_root: Path,
    now_unix: float = 1_700_000_000.0,
) -> dict[str, Any]:
    root = Path(repo_root)
    base = Path(persistence_root)
    base.mkdir(parents=True, exist_ok=True)
    cfg = _cfg(root)
    results: dict[str, Any] = {}

    def _case(name: str, fn: Callable[[], dict[str, Any]]) -> None:
        results[name] = fn()

    _case(
        "session_go_missing",
        lambda: evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    sgo = base / "session_go.json"
    _issue_session_go(path=sgo, repository_sha=repository_sha, config_digest=cfg, now=now_unix)

    _case(
        "owner_go_missing",
        lambda: evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=False,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )
    _case(
        "owner_session_go_missing",
        lambda: evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=False,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )
    _case(
        "authorization_missing",
        lambda: evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=False,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )
    _case(
        "wrong_repository_sha",
        lambda: evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
            expected_repository_sha="deadbeef" * 5,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )
    _case(
        "wrong_config_digest",
        lambda: evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest="0" * 64,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )
    _case(
        "confirm_token_argv",
        lambda: {
            "ok": False,
            "blockers": reject_confirm_token_argv_v1(["--confirm-token", "secret"]),
        },
    )
    sgo_no_net = base / "session_go_no_network.json"
    write_json_atomic_v1(
        sgo_no_net,
        build_session_go_authority_v1(
            session_go_id="sgo_phase92_rl_no_net_v1",
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            issued_at=now_unix,
            not_before=now_unix,
            expires_at=now_unix + 3600,
            network_session_execution_authorized_by_this_go=False,
        ).to_dict(),
    )
    _case(
        "request_real_network_without_network_auth",
        lambda: evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=sgo_no_net,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    # Contract negative: unbounded reconnect / network preauth
    contract = load_session_contract_v1(repo_root=root)
    bad_reconnect = dict(contract)
    bad_reconnect["reconnect_attempt_limit"] = 0
    bad_preauth = dict(contract)
    bad_preauth["network_session_authorized"] = True
    results["unbounded_reconnect_contract"] = {
        "ok": "UNBOUNDED_OR_EMPTY_RECONNECT" in validate_session_contract_v1(bad_reconnect),
        "gaps": validate_session_contract_v1(bad_reconnect),
    }
    results["network_preauth_contract"] = {
        "ok": "NETWORK_SESSION_PREAUTHORIZED" in validate_session_contract_v1(bad_preauth),
        "gaps": validate_session_contract_v1(bad_preauth),
    }

    fault = prove_governed_fault_path_offline_v1()
    results["governed_fault_path_offline"] = fault

    expected_fail = {
        "session_go_missing",
        "owner_go_missing",
        "owner_session_go_missing",
        "authorization_missing",
        "wrong_repository_sha",
        "wrong_config_digest",
        "confirm_token_argv",
        "request_real_network_without_network_auth",
    }
    fail_ok = True
    for name in expected_fail:
        payload = results[name]
        if name == "confirm_token_argv":
            if "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" not in payload.get("blockers", []):
                fail_ok = False
        elif payload.get("ok") is True:
            fail_ok = False
    if not results["unbounded_reconnect_contract"]["ok"]:
        fail_ok = False
    if not results["network_preauth_contract"]["ok"]:
        fail_ok = False
    if not fault.get("ok"):
        fail_ok = False

    return {
        "ok": fail_ok,
        "cases": results,
        "fault_session_started": False,
        "network_session_started": False,
    }
