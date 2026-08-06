"""Offline tests for Step-5 final generic consume/start binding.

No real DNS/socket/HTTP. Fixture authorizations only. No production secrets.
"""

from __future__ import annotations

import hashlib
import socket
import subprocess
from pathlib import Path
from typing import Any

import pytest

from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.binding_v1 import (  # noqa: E501
    build_step5_final_generic_side_effect_grant_v1,
    prove_step5_final_generic_consume_start_binding_complete_v1,
    run_step5_final_generic_consume_and_network_start_binding_v1,
    validate_step5_final_generic_side_effect_grant_v1,
)
from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.constants_v1 import (  # noqa: E501
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE,
    NETWORK_SESSION_ALLOWED,
    SESSION_SCOPE,
    STEP5_EXECUTION_CAPABILITY_ID,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.evidence_v1 import (  # noqa: E501
    materialize_step5_final_generic_binding_evidence_v1,
    run_step5_final_generic_failure_injection_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (  # noqa: E501
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.governed_session_execution_v1 import (  # noqa: E501
    execute_governed_step5_session_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_CT = "step5-final-generic-fixture-token-v1"
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


def _digests() -> tuple[str, str]:
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    return str(bundle["session_contract_digest"]), str(bundle["binding_config_digest"])


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> None:
        raise AssertionError("REAL_NETWORK_FORBIDDEN_IN_TESTS")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


def _binding(token: str = _CT) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _grant(**overrides: Any) -> dict[str, Any]:
    sha = str(overrides.pop("repository_sha", _sha()))
    cfg = str(overrides.pop("config_digest", _cfg()))
    contract, binding = _digests()
    contract = str(overrides.pop("session_contract_digest", contract))
    binding = str(overrides.pop("binding_config_digest", binding))
    token_digest = str(overrides.pop("confirm_token_digest", _binding()))
    grant = build_step5_final_generic_side_effect_grant_v1(
        authorization_id=str(overrides.pop("authorization_id", "auth_step5_final_generic_v1")),
        authorization_digest=str(
            overrides.pop("authorization_digest", "digest_step5_final_generic_v1")
        ),
        repository_sha=sha,
        config_digest=cfg,
        session_contract_digest=contract,
        binding_config_digest=binding,
        confirm_token_digest=token_digest,
        issued_at=float(overrides.pop("issued_at", NOW)),
        not_before=float(overrides.pop("not_before", NOW)),
        expires_at=float(overrides.pop("expires_at", NOW + 3600.0)),
        owner_go=bool(overrides.pop("owner_go", True)),
        operator_authorization_explicit=bool(
            overrides.pop("operator_authorization_explicit", True)
        ),
        network_session_go=bool(overrides.pop("network_session_go", True)),
        session_id=str(overrides.pop("session_id", TARGET_SESSION_ID)),
    )
    grant.update(overrides)
    body = {k: v for k, v in grant.items() if k != "grant_digest"}
    grant["grant_digest"] = sha256_canonical_v1(body)
    return grant


def _run(tmp_path: Path, **kwargs: Any) -> Any:
    return run_step5_final_generic_consume_and_network_start_binding_v1(
        expected_repository_sha=kwargs.pop("expected_repository_sha", _sha()),
        expected_config_digest=kwargs.pop("expected_config_digest", _cfg()),
        grant=kwargs.pop("grant", _grant()),
        confirm_token_plaintext=kwargs.pop("confirm_token_plaintext", _CT),
        confirm_token_binding_sha256=kwargs.pop("confirm_token_binding_sha256", _binding()),
        confirm_token_expires_at=kwargs.pop("confirm_token_expires_at", NOW + 3600.0),
        owner_go=kwargs.pop("owner_go", True),
        operator_authorization_explicit=kwargs.pop("operator_authorization_explicit", True),
        network_session_go=kwargs.pop("network_session_go", True),
        now_unix=NOW,
        persistence_root=tmp_path / "persistence",
        evidence_root=tmp_path / "evidence",
        repo_root=REPO_ROOT,
        **kwargs,
    )


def test_defaults_remain_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert AUTHORIZATION_CONSUMPTION_ALLOWED is False
    assert CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False
    assert GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE is True
    assert CAPABILITY_ID.endswith("NETWORK_START_BINDING_V1")
    assert STEP5_EXECUTION_CAPABILITY_ID.endswith("EXECUTION_CAPABILITY_V1")


def test_structural_complete_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    proof = prove_step5_final_generic_consume_start_binding_complete_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert proof["ok"] is True
    assert proof["claims"]["STEP5_EXISTING_EXECUTOR_PRODUCTIVELY_REACHABLE"] is True
    assert proof["claims"]["NETWORK_SESSION_STARTED"] is False
    assert proof["network_session_started"] is False


def test_happy_path_reaches_executor_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    calls: list[int] = []

    def _fake_executor(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {
            "ok": True,
            "terminal_class": "PASS",
            "network_session_started": False,
            "authorization_consumed": True,
            "confirm_token_consumed": True,
            "blockers": [],
            "claims": {"NETWORK_SESSION_STARTED": False},
        }

    result = _run(tmp_path, executor=_fake_executor, grant=_grant(authorization_id="auth_happy"))
    assert result.ok is True
    assert result.executor_invoked is True
    assert result.executor_invocation_count == 1
    assert len(calls) == 1
    assert result.authorization_consumed is True
    assert result.confirm_token_consumed is True
    assert result.network_session_started is False
    assert result.claims["STEP5_ATOMIC_SINGLE_USE_CONSUMPTION_BOUND"] is True


def test_missing_network_session_go(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, network_session_go=False)
    assert result.ok is False
    assert "NETWORK_SESSION_GO_REQUIRED" in result.blockers
    assert result.executor_invoked is False


def test_wrong_sha(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, grant=_grant(repository_sha="0" * 40))
    assert result.ok is False
    assert "AUTHORIZATION_SHA_MISMATCH" in result.blockers
    assert result.executor_invoked is False


def test_wrong_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, grant=_grant(config_digest="a" * 64))
    assert result.ok is False
    assert "AUTHORIZATION_CONFIG_MISMATCH" in result.blockers


def test_wrong_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, grant=_grant(session_contract_digest="b" * 64))
    assert result.ok is False
    assert "AUTHORIZATION_CONTRACT_DIGEST_MISMATCH" in result.blockers


def test_wrong_binding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, grant=_grant(binding_config_digest="c" * 64))
    assert result.ok is False
    assert "AUTHORIZATION_BINDING_DIGEST_MISMATCH" in result.blockers


def test_wrong_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, grant=_grant(session_scope="WRONG"))
    assert result.ok is False
    assert "SESSION_SCOPE_MISMATCH" in result.blockers


def test_expired_authorization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(
        tmp_path,
        grant=_grant(issued_at=NOW - 100, not_before=NOW - 90, expires_at=NOW - 10),
    )
    assert result.ok is False
    assert "AUTHORIZATION_EXPIRED" in result.blockers


def test_invalid_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, confirm_token_plaintext="wrong-token-value")
    assert result.ok is False
    assert result.executor_invoked is False


def test_authorization_reuse_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    first = _run(tmp_path, grant=_grant(authorization_id="auth_reuse_once"))
    assert first.ok is True
    second = _run(tmp_path, grant=_grant(authorization_id="auth_reuse_once"))
    assert second.ok is False
    assert second.executor_invoked is False
    assert any(
        b in second.blockers
        for b in ("AUTHORIZATION_ALREADY_CONSUMED", "AUTHORIZATION_REPLAY_REJECTED")
    )


def test_token_reuse_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    first = _run(tmp_path, grant=_grant(authorization_id="auth_token_reuse_1"))
    assert first.ok is True
    # Same token fingerprint with new auth id still hits token ledger.
    second = _run(tmp_path, grant=_grant(authorization_id="auth_token_reuse_2"))
    assert second.ok is False
    assert any("CONFIRM_TOKEN" in b for b in second.blockers)


def test_partial_token_consume_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(
        tmp_path,
        grant=_grant(authorization_id="auth_partial_token"),
        force_token_consume_fail=True,
    )
    assert result.ok is False
    assert result.executor_invoked is False
    assert "INJECTED_CONFIRM_TOKEN_CONSUMPTION_FAILURE" in result.blockers


def test_partial_auth_consume_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(
        tmp_path,
        grant=_grant(authorization_id="auth_partial_auth"),
        crash_during_auth_consume=True,
    )
    assert result.ok is False
    assert result.executor_invoked is False


def test_executor_raises_before_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)

    def _boom(**_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("injected")

    result = _run(tmp_path, executor=_boom, grant=_grant(authorization_id="auth_boom"))
    assert result.ok is False
    assert result.authorization_consumed is True
    assert any(b.startswith("EXECUTOR_EXCEPTION:") for b in result.blockers)
    # No automatic second start
    assert result.executor_invocation_count == 1


def test_executor_terminal_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)

    def _fail(**_kwargs: Any) -> dict[str, Any]:
        return {
            "ok": False,
            "terminal_class": "HARD_STOP",
            "network_session_started": False,
            "blockers": ["INJECTED_TERMINAL_FAILURE"],
            "claims": {"NETWORK_SESSION_STARTED": False},
        }

    result = _run(tmp_path, executor=_fail, grant=_grant(authorization_id="auth_term_fail"))
    assert result.executor_invoked is True
    assert result.network_session_started is False


def test_hidden_input_path_unavailable_via_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    result = _run(
        tmp_path,
        grant=_grant(authorization_id="auth_argv"),
        argv=["--confirm-token", "leaked"],
    )
    assert result.ok is False
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in result.blockers


def test_token_plaintext_not_in_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(tmp_path, grant=_grant(authorization_id="auth_redact"))
    dumped = str(result.to_dict())
    assert _CT not in dumped
    assert "leaked" not in dumped.lower()


def test_private_order_paths_unreachable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = _run(
        tmp_path,
        grant=_grant(authorization_id="auth_boundary"),
        private_endpoint_access_requested=True,
        order_side_effect_requested=True,
        auth_header_requested=True,
        credential_access_requested=True,
    )
    assert result.ok is False
    assert "PRIVATE_ENDPOINT_REQUEST_REJECTED" in result.blockers
    assert "ORDER_SIDE_EFFECT_REQUEST_REJECTED" in result.blockers


def test_crash_after_consume_no_second_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    result = _run(
        tmp_path,
        grant=_grant(authorization_id="auth_crash_post"),
        crash_after_consume_before_executor=True,
    )
    assert result.ok is False
    assert result.authorization_consumed is True
    assert result.executor_invoked is False
    # Replay rejected
    replay = _run(tmp_path, grant=_grant(authorization_id="auth_crash_post"))
    assert replay.ok is False
    assert replay.executor_invoked is False


def test_failure_injection_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    fi = run_step5_final_generic_failure_injection_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        persistence_root=tmp_path / "fi",
        repo_root=REPO_ROOT,
    )
    assert fi["ok"] is True
    assert fi["network_session_started"] is False


def test_materialize_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    # Seed legacy shared path with consumed state; materialize must ignore it.
    shared = REPO_ROOT / "var" / "tmp" / "step5_final_generic_failure_injection"
    (shared / "happy_reuse" / "persistence").mkdir(parents=True, exist_ok=True)
    ledger = (
        shared / "happy_reuse" / "persistence" / "step5_authorization_consumption_ledger_v1.jsonl"
    )
    ledger.write_text('{"authorization_id":"auth_happy_reuse","consumed":true}\n', encoding="utf-8")

    root_a = tmp_path / "fi_a"
    root_b = tmp_path / "fi_b"
    first = materialize_step5_final_generic_binding_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "evidence_out_1",
        repo_root=REPO_ROOT,
        failure_injection_persistence_root=root_a,
    )
    second = materialize_step5_final_generic_binding_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "evidence_out_2",
        repo_root=REPO_ROOT,
        failure_injection_persistence_root=root_b,
    )
    assert first["ok"] is True
    assert second["ok"] is True
    assert first["claims"]["FAILURE_INJECTION_OK"] is True
    assert second["claims"]["FAILURE_INJECTION_OK"] is True
    iso_a = first["failure_injection_persistence_isolation"]
    iso_b = second["failure_injection_persistence_isolation"]
    assert iso_a["shared_var_tmp_path_used"] is False
    assert iso_b["shared_var_tmp_path_used"] is False
    assert iso_a["persistence_root_token"] != iso_b["persistence_root_token"]
    assert iso_a["happy_path_once_ok"] is True
    assert iso_b["happy_path_once_ok"] is True
    assert iso_a["intra_run_reuse_blocked"] is True
    assert iso_b["intra_run_reuse_blocked"] is True
    assert first["manifest_digest"] == second["manifest_digest"]
    assert (tmp_path / "evidence_out_1" / "SUMMARY.json").is_file()
    assert (tmp_path / "evidence_out_2" / "MANIFEST.sha256").is_file()
    assert first["network_session_started"] is False
    assert first["authorization_issued"] is False
    text = (tmp_path / "evidence_out_1" / "SUMMARY.json").read_text(encoding="utf-8")
    assert "step5-final-generic-fixture-token-v1" not in text
    assert str(root_a) not in text


def test_materialize_evidence_ephemeral_double_run_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: two consecutive materialize calls must both PASS without shared FI state."""
    _block_network(monkeypatch)
    observed_roots: list[Path] = []
    real_fi = run_step5_final_generic_failure_injection_v1

    def _capture_fi(**kwargs: Any) -> dict[str, Any]:
        root = Path(kwargs["persistence_root"])
        observed_roots.append(root)
        return real_fi(**kwargs)

    monkeypatch.setattr(
        "src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.evidence_v1.run_step5_final_generic_failure_injection_v1",
        _capture_fi,
    )
    first = materialize_step5_final_generic_binding_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "ev1",
        repo_root=REPO_ROOT,
    )
    second = materialize_step5_final_generic_binding_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "ev2",
        repo_root=REPO_ROOT,
    )
    assert first["ok"] is True
    assert second["ok"] is True
    assert first["claims"]["FAILURE_INJECTION_OK"] is True
    assert second["claims"]["FAILURE_INJECTION_OK"] is True
    assert len(observed_roots) == 2
    assert observed_roots[0].resolve() != observed_roots[1].resolve()
    assert (
        first["failure_injection_persistence_isolation"]["persistence_root_token"]
        != second["failure_injection_persistence_isolation"]["persistence_root_token"]
    )
    for root in observed_roots:
        assert "step5_final_generic_failure_injection" not in str(root)
        assert not root.exists(), "ephemeral FI persistence root must be cleaned up"
    assert first["failure_injection_persistence_isolation"]["mode"] == (
        "ephemeral_temporary_directory"
    )
    assert first["failure_injection_persistence_isolation"]["intra_run_reuse_blocked"] is True
    assert second["failure_injection_persistence_isolation"]["intra_run_reuse_blocked"] is True
    assert first["manifest_digest"] == second["manifest_digest"]


def test_existing_executor_no_longer_deferred_with_binding_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    contract, binding = _digests()
    # Without GO still blocked
    denied = execute_governed_step5_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        expected_session_contract_digest=contract,
        expected_binding_config_digest=binding,
        authorization_id="auth_exec",
        authorization_digest="digest_exec",
        confirm_token_binding_sha256=_binding(),
        persistence_root=tmp_path / "p1",
        evidence_root=tmp_path / "e1",
        now_unix=NOW,
        confirm_token_plaintext=_CT,
        allow_authorization_consumption=True,
        allow_confirm_token_consumption=True,
        network_session_go=False,
        owner_go=False,
        operator_authorization_explicit=False,
        repo_root=REPO_ROOT,
    )
    assert denied.network_session_started is False
    assert "AUTHORIZATION_CONSUMPTION_DEFERRED_TO_LATER_SESSION_CAPABILITY" not in denied.blockers
    assert "LATER_SESSION_CAPABILITY_REQUIRED_FOR_CONSUME_AND_START" not in denied.blockers


def test_determinism_repeat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    a = prove_step5_final_generic_consume_start_binding_complete_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    b = prove_step5_final_generic_consume_start_binding_complete_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert a["ok"] == b["ok"]
    assert a["claims"]["STEP5_NETWORK_START_EDGE_PRODUCTIVELY_BOUND"] is True
    assert SESSION_SCOPE == "PHASE_9_2_PROLONGED_NATURAL_MARKET_SESSION"


def test_grant_validate_helper(tmp_path: Path) -> None:
    grant = _grant()
    evaluated = validate_step5_final_generic_side_effect_grant_v1(
        grant=grant,
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        expected_session_contract_digest=_digests()[0],
        expected_binding_config_digest=_digests()[1],
        expected_confirm_token_digest=_binding(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        now_unix=NOW,
        persistence_root=tmp_path,
    )
    assert evaluated["ok"] is True
