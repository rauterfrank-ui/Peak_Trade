"""Tests for Step-4 owner-permit + runner-signature wiring (no network session)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CLI_OWNER_SESSION_PERMIT_DEFAULT,
    NETWORK_SESSION_ALLOWED,
    OWNER_PERMIT_WIRING_CAPABILITY_ID,
    PRODUCTIVE_SESSION_PATH_STRUCTURALLY_RUNTIME_REACHABLE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.productive_executor_v1 import (
    execute_productive_rate_limit_reconnect_session_activation_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    REQUIRED_RUNNER_KWARGS,
    build_canonical_wallclock_runner_kwargs_v1,
    discover_canonical_wallclock_runner_signature_v1,
    prove_runner_invoke_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_go_v1 import (
    build_session_go_authority_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py"
)
NOW = 1_700_000_000.0


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _sgo(path: Path, *, sha: str, cfg: str, network: bool = False) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_owner_permit_wiring_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=NOW,
        not_before=NOW,
        expires_at=NOW + 3600,
        network_session_execution_authorized_by_this_go=network,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(path, auth.to_dict())


def _binding(tmp_path: Path, *, sha: str) -> dict[str, Any]:
    return {
        "session_id": TARGET_SESSION_ID,
        "prereg": {"test_double": "prereg"},
        "go": {"test_double": "go"},
        "confirm_token": "WIRING_TEST_TOKEN_IN_MEMORY_ONLY",
        "artifact_path": str(tmp_path / "auth.json"),
        "evidence_root": str(tmp_path / "ev"),
        "expected_repository_sha": sha,
        "fingerprint_ledger_path": str(tmp_path / "fp.txt"),
        "use_real_network": False,
    }


def test_constants_remain_fail_closed_no_network() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert CLI_OWNER_SESSION_PERMIT_DEFAULT is False
    assert PRODUCTIVE_SESSION_PATH_STRUCTURALLY_RUNTIME_REACHABLE is True
    assert OWNER_PERMIT_WIRING_CAPABILITY_ID.endswith("OWNER_PERMIT_WIRING_V1")


def test_runner_signature_discovered_from_repository() -> None:
    discovered = discover_canonical_wallclock_runner_signature_v1()
    assert discovered["ok"] is True
    assert discovered["keyword_only"] is True
    assert discovered["required_kwargs"] == list(REQUIRED_RUNNER_KWARGS)
    assert "session_request" in discovered["forbidden_legacy_keys"]


def test_build_kwargs_signature_compatible(tmp_path: Path) -> None:
    sha = _sha()
    req = _binding(tmp_path, sha=sha)
    kwargs = build_canonical_wallclock_runner_kwargs_v1(req)
    assert set(REQUIRED_RUNNER_KWARGS).issubset(kwargs)
    assert "session_request" not in kwargs
    assert kwargs["expected_repository_sha"] == sha
    assert kwargs["use_real_network"] is False


def test_build_kwargs_rejects_incomplete_and_legacy(tmp_path: Path) -> None:
    sha = _sha()
    try:
        build_canonical_wallclock_runner_kwargs_v1({"session_id": TARGET_SESSION_ID})
        raise AssertionError("expected missing required")
    except ValueError as exc:
        assert "RUNNER_INVOKE_BINDING_MISSING_REQUIRED" in str(exc)

    bad = _binding(tmp_path, sha=sha)
    bad["session_request"] = {"nested": True}
    try:
        build_canonical_wallclock_runner_kwargs_v1(bad)
        raise AssertionError("expected legacy reject")
    except ValueError as exc:
        assert "FORBIDDEN_LEGACY_KEY" in str(exc)


def test_permit_missing_fail_closed_no_runner(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _sgo(sgo, sha=sha, cfg=cfg, network=False)
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    # No injected runner and permit false.
    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        request_real_network=True,
        network_session_allowed=False,
        execute=True,
        permit_canonical_runner_invoke=False,
        session_request=_binding(tmp_path, sha=sha),
        wallclock_runner=None,
    )
    assert result.ok is False
    assert "OWNER_SESSION_PERMIT_REQUIRED" in result.blockers
    assert result.wallclock_runner_invoked is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert calls == []


def test_permit_true_network_false_dry_no_runner_no_consume(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _sgo(sgo, sha=sha, cfg=cfg, network=False)
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        request_real_network=True,
        network_session_allowed=False,
        execute=True,
        permit_canonical_runner_invoke=True,
        session_request=_binding(tmp_path, sha=sha),
        wallclock_runner=runner,
    )
    assert result.ok is False
    assert "NETWORK_SESSION_ALLOWED_REQUIRED" in result.blockers
    assert "DRY_NO_NETWORK=true" in result.notes
    assert result.wallclock_runner_invoked is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.claims.get("PRODUCTIVE_SESSION_PATH_STRUCTURALLY_RUNTIME_REACHABLE") is True
    assert result.claims.get("DRY_NO_NETWORK") is True
    assert "CLI_PERMIT_FALSE_AND_RUNNER_SIGNATURE_MISMATCH" not in " ".join(result.blockers)
    assert calls == []


def test_signature_compatible_invoke_via_injected_spy(tmp_path: Path) -> None:
    """Prove invoke uses real kwargs; no HTTP; local mock consumers only."""
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _sgo(sgo, sha=sha, cfg=cfg, network=True)
    seen: list[dict[str, Any]] = []

    def runner(**runner_kwargs: Any) -> dict[str, Any]:
        seen.append(dict(runner_kwargs))
        return {"ok": True, "network_opened": False}

    def auth_validator(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": True}

    def auth_consumer(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "consumed": True}

    def token_validator(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "fingerprint": "a" * 64}

    def token_consumer(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "consumed": True}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        request_real_network=True,
        network_session_allowed=True,
        authorization_id="auth_owner_permit_wiring_v1",
        authorization_digest="b" * 64,
        authorization_repository_sha=sha,
        authorization_config_digest=cfg,
        confirm_token_binding_sha256="c" * 64,
        confirm_token_in_memory="WIRING_SPY_TOKEN",
        confirm_token_expires_at=NOW + 3600,
        persistence_root=tmp_path / "persist",
        execute=True,
        permit_canonical_runner_invoke=True,
        session_request=_binding(tmp_path, sha=sha),
        wallclock_runner=runner,
        authorization_validator=auth_validator,
        authorization_consumer=auth_consumer,
        confirm_token_validator=token_validator,
        confirm_token_consumer=token_consumer,
    )
    assert result.ok is True
    assert result.wallclock_runner_invoked is True
    assert len(seen) == 1
    assert "session_request" not in seen[0]
    for key in REQUIRED_RUNNER_KWARGS:
        assert key in seen[0]
    assert result.network_session_started is False
    assert result.network_request_count == 0
    assert result.claims.get("RUNNER_SIGNATURE_MATCH") is True


def test_cli_permit_propagated_dry_path(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    now = float(time.time())
    auth = build_session_go_authority_v1(
        session_go_id="sgo_cli_permit_dry_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        network_session_execution_authorized_by_this_go=False,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(sgo, auth.to_dict())

    missing = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--execute",
            "--owner-go",
            "--owner-session-go",
            "--request-real-network",
            "--session-go-file",
            str(sgo),
            "--expected-repository-sha",
            sha,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert missing.returncode == 2
    missing_payload = json.loads(missing.stdout)
    assert "OWNER_SESSION_PERMIT_REQUIRED" in missing_payload["blockers"]
    assert missing_payload.get("wallclock_runner_invoked") is False

    dry = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--execute",
            "--owner-go",
            "--owner-session-go",
            "--request-real-network",
            "--permit-canonical-runner-invoke",
            "--session-go-file",
            str(sgo),
            "--expected-repository-sha",
            sha,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert dry.returncode == 2
    dry_payload = json.loads(dry.stdout)
    assert "NETWORK_SESSION_ALLOWED_REQUIRED" in dry_payload["blockers"]
    assert dry_payload.get("wallclock_runner_invoked") is False
    assert dry_payload.get("authorization_consumed") is False
    assert (dry_payload.get("claims") or {}).get("AUTHORIZATION_CONSUMED") is False
    assert "NO_CONFIRM_TOKEN_CONSUMPTION=true" in (dry_payload.get("notes") or [])
    assert dry_payload.get("network_session_started") is False
    claims = dry_payload.get("claims") or {}
    assert claims.get("PRODUCTIVE_SESSION_PATH_STRUCTURALLY_RUNTIME_REACHABLE") is True
    assert claims.get("DRY_NO_NETWORK") is True
    assert "CLI_PERMIT_FALSE_AND_RUNNER_SIGNATURE_MISMATCH" not in " ".join(
        dry_payload.get("blockers") or []
    )


def test_prove_binding_offline() -> None:
    proof = prove_runner_invoke_binding_v1(None)
    assert proof["runner_signature_discovered_from_repository"] is True
    assert proof["runner_signature_match"] is True
    assert proof["productive_session_path_structurally_runtime_reachable"] is True
