"""Tests for Phase 9.2 Step-4 final generic session activation binding.

No real DNS/socket/HTTP. Fixture authorizations only. No production secrets.
"""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path
from typing import Any

import pytest

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    CONFIRM_TOKEN_PREFIX,
    compute_confirm_token_binding_sha256,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID,
    GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE,
    PERMANENT_UNSCOPED_ENABLE,
    SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.final_generic_session_activation_binding_v1 import (
    FinalGenericActivationError,
    build_final_generic_side_effect_grant_v1,
    consume_final_generic_side_effect_grant_v1,
    prove_final_generic_activation_binding_complete_v1,
    run_final_generic_step4_activation_binding_v1,
    validate_final_generic_side_effect_grant_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.final_generic_session_activation_evidence_v1 import (
    materialize_final_generic_activation_evidence_v1,
    run_final_generic_activation_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_productive_session_execution_v1 import (
    execute_governed_productive_session_execution_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKEN = CONFIRM_TOKEN_PREFIX + ("FINALGENACTBINDV1" + "Z" * 23)
SESSION_ID = TARGET_SESSION_ID
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


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> None:
        raise AssertionError("REAL_NETWORK_FORBIDDEN_IN_TESTS")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


def _binding(sha: str = "") -> str:
    return compute_confirm_token_binding_sha256(
        confirm_token=TOKEN,
        session_id=SESSION_ID,
        scope_digest=SESSION_SCOPE,
        repository_sha=sha or _sha(),
        expires_at=NOW + 3600.0,
    )


def _grant(**overrides: Any) -> dict[str, Any]:
    sha = str(overrides.pop("repository_sha", _sha()))
    cfg = str(overrides.pop("config_digest", _cfg()))
    binding = str(overrides.pop("confirm_token_digest", _binding(sha)))
    grant = build_final_generic_side_effect_grant_v1(
        authorization_id=str(overrides.pop("authorization_id", "auth_final_generic_v1")),
        authorization_digest=str(overrides.pop("authorization_digest", "digest_final_generic_v1")),
        repository_sha=sha,
        config_digest=cfg,
        confirm_token_digest=binding,
        issued_at=float(overrides.pop("issued_at", NOW)),
        not_before=float(overrides.pop("not_before", NOW)),
        expires_at=float(overrides.pop("expires_at", NOW + 3600.0)),
        owner_go=bool(overrides.pop("owner_go", True)),
        operator_authorization_explicit=bool(
            overrides.pop("operator_authorization_explicit", True)
        ),
        network_session_go=bool(overrides.pop("network_session_go", True)),
        session_id=str(overrides.pop("session_id", SESSION_ID)),
    )
    grant.update(overrides)
    body = {k: v for k, v in grant.items() if k != "grant_digest"}
    grant["grant_digest"] = sha256_canonical_v1(body)
    return grant


def _session_request(sha: str, binding: str) -> dict[str, Any]:
    class _Go:
        scope_digest = SESSION_SCOPE
        confirm_token_binding_sha256 = binding

    return {
        "session_id": SESSION_ID,
        "prereg": object(),
        "go": _Go(),
        "confirm_token": TOKEN,
        "artifact_path": Path("/tmp/peak_trade_final_generic_artifact.json"),
        "evidence_root": Path("/tmp/peak_trade_final_generic_evidence"),
        "expected_repository_sha": sha,
        "fingerprint_ledger_path": Path("/tmp/peak_trade_final_generic_fp.txt"),
    }


def test_defaults_remain_fail_closed() -> None:
    assert SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED is False
    assert DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED is False
    assert PERMANENT_UNSCOPED_ENABLE is False
    assert GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE is True
    assert FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID.endswith(
        "FINAL_GENERIC_SESSION_ACTIVATION_BINDING_V1"
    )


def test_structural_complete_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    proof = prove_final_generic_activation_binding_complete_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert proof["ok"] is True
    assert proof["claims"][
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP4_SESSION"
    ]
    assert proof["claims"]["FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CODE_CHANGE"]
    assert proof["claims"]["FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CONSTANT_FLIP"]


def test_missing_authorization_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = validate_final_generic_side_effect_grant_v1(
        grant=None,
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        expected_confirm_token_digest="",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path,
    )
    assert result["ok"] is False
    assert "SIDE_EFFECT_AUTHORIZATION_GRANT_REQUIRED" in result["blockers"]


@pytest.mark.parametrize(
    ("kwargs", "blocker"),
    [
        ({"repository_sha": "0" * 40}, "AUTHORIZATION_SHA_MISMATCH"),
        ({"config_digest": "badcfg"}, "AUTHORIZATION_CONFIG_MISMATCH"),
        ({"binding_capability_id": "WRONG"}, "BINDING_CAPABILITY_MISMATCH"),
        ({"session_type": "WRONG_MODE"}, "SESSION_TYPE_MISMATCH"),
        ({"owner_go": False}, "OWNER_GO_REQUIRED"),
        ({"operator_authorization_explicit": False}, "OPERATOR_AUTHORIZATION_REQUIRED"),
        ({"network_session_go": False}, "NETWORK_SESSION_GO_REQUIRED"),
        (
            {"expires_at": NOW - 1, "not_before": NOW - 10, "issued_at": NOW - 20},
            "AUTHORIZATION_EXPIRED",
        ),
        ({"confirm_token_digest": "e" * 64}, "CONFIRM_TOKEN_DIGEST_MISMATCH"),
    ],
)
def test_grant_binding_mismatches_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, Any],
    blocker: str,
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    binding = _binding(sha)
    # Prefer kwargs confirm_token_digest when provided (mismatch cases).
    if "confirm_token_digest" in kwargs:
        grant = _grant(**kwargs)
        expected_digest = binding
    else:
        grant = _grant(confirm_token_digest=binding, **kwargs)
        expected_digest = binding
    result = validate_final_generic_side_effect_grant_v1(
        grant=grant,
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        expected_confirm_token_digest=expected_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path,
    )
    assert result["ok"] is False
    assert blocker in result["blockers"]


def test_missing_owner_operator_network_gos_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    binding = _binding(sha)
    grant = _grant(confirm_token_digest=binding)
    for owner, op, net, code in (
        (False, True, True, "OWNER_GO_REQUIRED"),
        (True, False, True, "OPERATOR_AUTHORIZATION_REQUIRED"),
        (True, True, False, "NETWORK_SESSION_GO_REQUIRED"),
    ):
        result = validate_final_generic_side_effect_grant_v1(
            grant=grant,
            expected_repository_sha=sha,
            expected_config_digest=_cfg(),
            expected_confirm_token_digest=binding,
            owner_go=owner,
            operator_authorization_explicit=op,
            network_session_go=net,
            now_unix=NOW,
            persistence_root=tmp_path,
        )
        assert result["ok"] is False
        assert code in result["blockers"]


def test_private_non_get_auth_cred_order_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    binding = _binding(sha)
    grant = _grant(confirm_token_digest=binding)
    for kwargs, code in (
        ({"private_endpoint_access_requested": True}, "PRIVATE_ENDPOINT_REQUEST_REJECTED"),
        ({"non_get_method_requested": True}, "NON_GET_METHOD_REJECTED"),
        ({"auth_header_requested": True}, "AUTH_HEADER_REQUEST_REJECTED"),
        ({"credential_access_requested": True}, "CREDENTIAL_ACCESS_REQUEST_REJECTED"),
        ({"order_side_effect_requested": True}, "ORDER_SIDE_EFFECT_REQUEST_REJECTED"),
    ):
        result = validate_final_generic_side_effect_grant_v1(
            grant=grant,
            expected_repository_sha=sha,
            expected_config_digest=_cfg(),
            expected_confirm_token_digest=binding,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            now_unix=NOW,
            persistence_root=tmp_path,
            **kwargs,
        )
        assert result["ok"] is False
        assert code in result["blockers"]


def test_atomic_consume_replay_and_crash_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    binding = _binding(sha)
    grant = _grant(confirm_token_digest=binding)

    first = consume_final_generic_side_effect_grant_v1(
        grant=grant,
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        expected_confirm_token_digest=binding,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path / "ok",
    )
    assert first["ok"] is True
    assert first["consumed"] is True

    replay = consume_final_generic_side_effect_grant_v1(
        grant=grant,
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        expected_confirm_token_digest=binding,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path / "ok",
    )
    assert replay["ok"] is False
    assert "AUTHORIZATION_ALREADY_CONSUMED" in replay["blockers"] or (
        "AUTHORIZATION_REPLAY_REJECTED" in replay["blockers"]
    )

    with pytest.raises(FinalGenericActivationError, match="CRASH_BEFORE_RESERVE"):
        consume_final_generic_side_effect_grant_v1(
            grant=_grant(authorization_id="auth_crash_before", confirm_token_digest=binding),
            expected_repository_sha=sha,
            expected_config_digest=_cfg(),
            expected_confirm_token_digest=binding,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            now_unix=NOW,
            persistence_root=tmp_path / "crash_before",
            crash_before_reserve=True,
        )

    with pytest.raises(FinalGenericActivationError, match="CRASH_AFTER_RESERVE"):
        consume_final_generic_side_effect_grant_v1(
            grant=_grant(authorization_id="auth_crash_after", confirm_token_digest=binding),
            expected_repository_sha=sha,
            expected_config_digest=_cfg(),
            expected_confirm_token_digest=binding,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            now_unix=NOW,
            persistence_root=tmp_path / "crash_after",
            crash_after_reserve=True,
        )
    # Reserved burns the auth — reuse rejected.
    burned = validate_final_generic_side_effect_grant_v1(
        grant=_grant(authorization_id="auth_crash_after", confirm_token_digest=binding),
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        expected_confirm_token_digest=binding,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path / "crash_after",
    )
    assert burned["ok"] is False
    assert "AUTHORIZATION_RESERVED_OR_HALF_CONSUMED" in burned["blockers"] or (
        "AUTHORIZATION_REUSE_REJECTED" in burned["blockers"]
    )


def test_happy_path_mocked_runner_and_no_second_start_after_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    binding = _binding(sha)
    grant = _grant(confirm_token_digest=binding)
    req = _session_request(sha, binding)
    (tmp_path / "fp.txt").write_text("", encoding="utf-8")
    req["fingerprint_ledger_path"] = tmp_path / "fp.txt"
    req["artifact_path"] = tmp_path / "artifact.json"
    req["evidence_root"] = tmp_path / "ev"
    req["artifact_path"].write_text("{}", encoding="utf-8")
    calls = {"n": 0}

    def _runner(**kwargs: Any) -> dict[str, Any]:
        calls["n"] += 1
        assert kwargs.get("use_real_network") is False
        return {"ok": True, "network_request_count": 0, "dry": True}

    result = run_final_generic_step4_activation_binding_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        grant=grant,
        session_request=req,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=binding,
        confirm_token_expires_at=NOW + 3600.0,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path / "happy",
        wallclock_runner=_runner,
        allow_real_network=False,
        invoke_runner=True,
        confirm_token_expected_scope_digest=SESSION_SCOPE,
    )
    assert result.ok is True
    assert result.authorization_consumed is True
    assert result.confirm_token_consumed is True
    assert result.wallclock_runner_invoked is True
    assert calls["n"] == 1
    assert result.network_session_executed is False
    assert result.claims[
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP4_SESSION"
    ]

    crashed = run_final_generic_step4_activation_binding_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        grant=_grant(authorization_id="auth_crash_runner", confirm_token_digest=binding),
        session_request=req,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=binding,
        confirm_token_expires_at=NOW + 3600.0,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path / "crash_runner",
        wallclock_runner=_runner,
        crash_after_consume_before_runner=True,
        confirm_token_expected_scope_digest=SESSION_SCOPE,
    )
    assert crashed.ok is False
    assert crashed.authorization_consumed is True
    assert crashed.wallclock_runner_invoked is False
    assert "INJECTED_CRASH_AFTER_CONSUME_BEFORE_RUNNER" in crashed.blockers

    # Recovery must not start a second runner with the burned authorization.
    recovery = run_final_generic_step4_activation_binding_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        grant=_grant(authorization_id="auth_crash_runner", confirm_token_digest=binding),
        session_request=req,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=binding,
        confirm_token_expires_at=NOW + 3600.0,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path / "crash_runner",
        wallclock_runner=_runner,
        confirm_token_expected_scope_digest=SESSION_SCOPE,
    )
    assert recovery.ok is False
    assert recovery.wallclock_runner_invoked is False


def test_execute_runtime_entrypoint_uses_ephemeral_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    binding = _binding(sha)
    req = _session_request(sha, binding)
    req["fingerprint_ledger_path"] = tmp_path / "fp.txt"
    req["artifact_path"] = tmp_path / "a.json"
    req["evidence_root"] = tmp_path / "ev"
    req["fingerprint_ledger_path"].write_text("", encoding="utf-8")
    req["artifact_path"].write_text("{}", encoding="utf-8")

    def _runner(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "network_request_count": 0}

    result = execute_governed_productive_session_execution_v1(
        expected_capability_id=SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        session_request=req,
        network_allowed_from_authorization=True,
        authorization_id="auth_runtime_ephemeral_v1",
        authorization_digest="digest_runtime_ephemeral_v1",
        confirm_token_binding_sha256=binding,
        confirm_token_plaintext=TOKEN,
        confirm_token_expires_at=NOW + 3600.0,
        now_unix=NOW,
        persistence_root=tmp_path / "runtime",
        wallclock_runner=_runner,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        allow_real_network_side_effects=False,
        invoke_runner=True,
    )
    assert result.ok is True
    assert result.authorization_consumed is True
    assert result.wallclock_runner_invoked is True
    assert result.network_session_executed is False
    assert result.claims["GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE"] is True
    assert SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED is False


def test_failure_injection_and_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    fi = run_final_generic_activation_failure_injection_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        persistence_root=tmp_path / "fi",
    )
    assert fi["ok"] is True
    summary = materialize_final_generic_activation_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "evidence",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["network_session_executed"] is False
    assert summary["authorization_issued"] is False
    assert (tmp_path / "evidence" / "SUMMARY.json").is_file()
    assert (tmp_path / "evidence" / "MANIFEST.sha256").is_file()
