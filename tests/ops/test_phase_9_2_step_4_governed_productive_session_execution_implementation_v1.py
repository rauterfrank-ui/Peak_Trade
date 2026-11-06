"""Tests for Step-4 governed productive session execution implementation.

No real DNS/socket/HTTP. No auth/token consumption. No productive secrets.
"""

from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path
from typing import Any, Callable

import pytest

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    CONFIRM_TOKEN_PREFIX,
    compute_confirm_token_binding_sha256,
    fingerprint_confirm_token,
    sha256_text,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    parse_preregistration_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.authorization_binding_v1 import (
    consume_authorization_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_binding_v1 import (
    consume_confirm_token_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_LEDGER_FILENAME,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_LEDGER_FILENAME,
    GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED,
    GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
    SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_SCOPE,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_productive_session_execution_evidence_v1 import (
    materialize_session_execution_implementation_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_productive_session_execution_failure_injection_v1 import (
    run_governed_productive_session_execution_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_productive_session_execution_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    execute_governed_productive_session_execution_v1,
    prove_governed_productive_session_execution_implementation_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_request_cli_adapter_v1 import (
    build_canonical_session_request_from_issuance_artifacts_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1 import (
    FAMILY_PSO_GOVERNED_PUBLIC_MD,
    PURPOSE_PSO_WALLCLOCK_OBSERVE,
    SecureEphemeralConfirmTokenHandleV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
TOKEN = CONFIRM_TOKEN_PREFIX + ("GOVERNEDEXECIMPLV1" + "Z" * 23)
SESSION_ID = "phase_9_2_governed_exec_impl_session_v1"
NOW = 1_700_000_000.0
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py"
)


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


def _write_issuance(
    tmp_path: Path,
    *,
    sha: str,
    token: str = TOKEN,
    network_authorized: bool = True,
) -> dict[str, Path]:
    evidence_root = tmp_path / "evidence_root"
    evidence_root.mkdir(parents=True, exist_ok=True)
    ledger = tmp_path / "fingerprint_ledger.txt"
    ledger.write_text("", encoding="utf-8")

    prereg_raw = json.loads(
        (FIXTURE_DIR / "preregistration_wallclock_valid_non_authoritative.json").read_text(
            encoding="utf-8"
        )
    )
    go_raw = json.loads(
        (FIXTURE_DIR / "operator_go_wallclock_valid_non_authoritative.json").read_text(
            encoding="utf-8"
        )
    )
    prereg_raw["session_id"] = SESSION_ID
    prereg_raw["expected_repository_sha"] = sha
    prereg_raw["evidence_root"] = str(evidence_root)
    prereg_raw["expires_at"] = NOW + 3600.0
    prereg_raw.pop("issued_at", None)
    prereg_raw.pop("not_before", None)
    provisional = parse_preregistration_contract_v1(prereg_raw)
    scope = provisional.scope_digest()
    binding = compute_confirm_token_binding_sha256(
        session_id=SESSION_ID,
        scope_digest=scope,
        expires_at=float(prereg_raw["expires_at"]),
        repository_sha=sha,
        confirm_token=token,
    )
    prereg_raw["confirm_token_binding_sha256"] = binding
    prereg_raw["confirm_token_hash_reference"] = "sha256:" + sha256_text(token)
    provisional = parse_preregistration_contract_v1(prereg_raw)
    scope = provisional.scope_digest()
    binding = compute_confirm_token_binding_sha256(
        session_id=SESSION_ID,
        scope_digest=scope,
        expires_at=float(prereg_raw["expires_at"]),
        repository_sha=sha,
        confirm_token=token,
    )
    prereg_raw["confirm_token_binding_sha256"] = binding

    go_raw["session_id"] = SESSION_ID
    go_raw["expected_repository_sha"] = sha
    go_raw["confirm_token_binding_sha256"] = binding
    go_raw["confirm_token_hash_reference"] = prereg_raw["confirm_token_hash_reference"]
    go_raw["scope_digest"] = scope
    go_raw["network_authorized"] = network_authorized
    go_raw["session_execution_authorized"] = network_authorized
    go_raw["network_scope"] = GOVERNED_PUBLIC_MD_NETWORK_SCOPE
    go_raw["session_execution_scope"] = "paper_shadow_observation_wallclock_v1"
    go_raw["orders_authorized"] = False
    go_raw["live_authorized"] = False
    go_raw["testnet_authorized"] = False
    go_raw["paper_execution_authorized"] = False
    go_raw["credentials_authorized"] = False
    go_raw["expires_at"] = NOW + 3600.0
    go_raw["not_before"] = NOW
    go_raw["issued_at"] = NOW

    prereg_path = tmp_path / "preregistration.json"
    go_path = tmp_path / "operator_go.json"
    art_path = tmp_path / "authorization_artifact.json"
    write_json_atomic_v1(prereg_path, prereg_raw)
    write_json_atomic_v1(go_path, go_raw)
    write_json_atomic_v1(
        art_path,
        {
            "schema": "authorization_artifact_governed_exec_impl_probe_v1",
            "authorization_id": "auth_governed_exec_impl_v1",
            "preregistration_id": SESSION_ID,
            "repository_sha": sha,
            "network_scope": PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
            "network_authorized": network_authorized,
            "confirm_token_fingerprint": fingerprint_confirm_token(token),
            "notes": ["GOVERNED_EXEC_IMPL_UNIT_ONLY"],
        },
    )
    return {
        "preregistration": prereg_path,
        "operator_go": go_path,
        "authorization_artifact": art_path,
        "fingerprint_ledger": ledger,
        "evidence_root": evidence_root,
        "binding": binding,
        "scope": scope,
    }


def _getpass_for_token(token: str) -> Callable[[str], str]:
    handle = SecureEphemeralConfirmTokenHandleV1.mint_bound_v1(
        family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
        purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
        session_id=SESSION_ID,
        repository_sha=_sha(),
        consumer_id="tests.ops.test_phase_9_2_step_4_governed_exec_impl",
        mint_fn=lambda: token,
    )
    return handle.as_getpass_fn_v1()


def test_constants_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert REAL_NETWORK_REQUESTS_ALLOWED is False
    assert AUTHORIZATION_CONSUMPTION_ALLOWED is False
    assert CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False
    assert SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED is False
    assert GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED is False
    assert NETWORK_ALLOWLIST == "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
    assert HTTP_METHOD_ALLOWLIST == "GET_ONLY"
    assert SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID.endswith(
        "SESSION_EXECUTION_IMPLEMENTATION_V1"
    )
    assert SESSION_EXECUTION_RUNTIME_CAPABILITY_ID.endswith("SESSION_EXECUTION_V1")
    assert "stub" in " ".join(CALL_GRAPH_BEFORE).lower() or "stub" in str(CALL_GRAPH_BEFORE)
    assert any("Productive Wallclock Session Runner" in x for x in CALL_GRAPH_AFTER)


def test_implementation_proof_without_session_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        now_unix=NOW,
    )
    assert proof.ok is True
    assert proof.claims["NETWORK_SESSION_EXECUTED"] is False
    assert proof.claims["AUTHORIZATION_CONSUMED"] is False
    assert proof.claims["CONFIRM_TOKEN_CONSUMED"] is False
    assert proof.claims["REAL_NETWORK_REQUEST_COUNT"] == 0
    assert proof.productive_runner_bound is True
    assert proof.claims["READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION"] is True


def test_capability_id_wrong_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        expected_capability_id="WRONG",
        now_unix=NOW,
    )
    assert proof.ok is False
    assert "CAPABILITY_ID_MISMATCH_OR_MISSING" in proof.blockers


def test_real_network_and_consumption_flags_forbidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        allow_real_network_side_effects=True,
        allow_authorization_consumption=True,
        allow_confirm_token_consumption=True,
        now_unix=NOW,
    )
    assert proof.ok is False
    assert "REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_IMPLEMENTATION" in proof.blockers
    assert "AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_IMPLEMENTATION" in proof.blockers
    assert "CONFIRM_TOKEN_CONSUMPTION_FORBIDDEN_IN_IMPLEMENTATION" in proof.blockers


def test_authorization_expired_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        session_request=adapter.session_request,
        network_allowed_from_authorization=True,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_session_id=SESSION_ID,
        authorization_expires_at=NOW - 1.0,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
    )
    assert proof.ok is False
    assert "AUTHORIZATION_EXPIRED" in proof.blockers
    assert proof.authorization_consumed is False
    assert proof.confirm_token_consumed is False


def test_repository_sha_mismatch_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha="deadbeef" * 5,
        expected_config_digest=_cfg(),
        session_request=adapter.session_request,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_session_id=SESSION_ID,
        authorization_repository_sha=sha,
        authorization_config_digest=_cfg(),
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
    )
    assert proof.ok is False
    assert any("AUTHORIZATION" in b or "SHA" in b for b in proof.blockers)


def test_config_digest_mismatch_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest="wrong_config_digest",
        session_request=adapter.session_request,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_session_id=SESSION_ID,
        authorization_repository_sha=sha,
        authorization_config_digest=_cfg(),
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
    )
    assert proof.ok is False
    assert any("CONFIG" in b or "AUTHORIZATION" in b for b in proof.blockers)


def test_invalid_confirm_token_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        session_request=adapter.session_request,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_session_id=SESSION_ID,
        confirm_token_plaintext="not-a-valid-token",
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
    )
    assert proof.ok is False
    assert any("CONFIRM_TOKEN" in b for b in proof.blockers)


def test_already_consumed_authorization_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    persist = tmp_path / "persist"
    persist.mkdir(parents=True, exist_ok=True)
    consume_authorization_binding_v1(
        ledger_path=persist / AUTHORIZATION_LEDGER_FILENAME,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        session_id=SESSION_ID,
        now_unix=NOW,
    )
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        session_request=adapter.session_request,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_session_id=SESSION_ID,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=persist,
    )
    assert proof.ok is False
    assert "AUTHORIZATION_ALREADY_CONSUMED" in proof.blockers


def test_hidden_pty_missing_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=None,
        require_hidden_pty=True,
    )
    assert adapter.ok is False
    assert any("HIDDEN_PTY" in b or "PTY" in b or "TTY" in b for b in adapter.blockers)


def test_dry_productive_runner_invoke_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    calls = {"n": 0}

    def _dry_runner(**kwargs: Any) -> dict[str, Any]:
        calls["n"] += 1
        assert kwargs.get("use_real_network") is False
        assert "confirm_token" in kwargs
        return {"ok": True, "dry": True, "use_real_network": False, "network_request_count": 0}

    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        session_request=adapter.session_request,
        network_allowed_from_authorization=True,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_session_id=SESSION_ID,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
        wallclock_runner=_dry_runner,
        invoke_productive_runner_dry=True,
    )
    assert proof.ok is True
    assert calls["n"] == 1
    assert proof.wallclock_runner_invoked is True
    assert proof.authorization_consumed is False
    assert proof.confirm_token_consumed is False
    assert proof.real_network_request_count == 0


def test_runtime_execute_fail_closed_no_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    result = execute_governed_productive_session_execution_v1(
        expected_capability_id=SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        session_request={"session_id": SESSION_ID},
        network_allowed_from_authorization=True,
        authorization_id="auth_x",
        authorization_digest="digest_x",
        confirm_token_binding_sha256="a" * 64,
        confirm_token_plaintext=TOKEN,
        confirm_token_expires_at=NOW + 3600.0,
        now_unix=NOW,
        persistence_root=tmp_path,
        allow_real_network_side_effects=True,
        allow_authorization_consumption=True,
        allow_confirm_token_consumption=True,
    )
    assert result.ok is False
    assert result.network_session_executed is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.real_network_request_count == 0
    assert (
        "OWNER_GO_REQUIRED" in result.blockers or "NETWORK_SESSION_GO_REQUIRED" in result.blockers
    )
    assert "RUNTIME_SESSION_REQUIRES_SEPARATE_OWNER_GO_AFTER_IMPLEMENTATION_MERGE" not in (
        result.blockers
    )


def test_direct_runner_without_runtime_capability_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    result = execute_governed_productive_session_execution_v1(
        expected_capability_id="NOT_THE_RUNTIME_CAPABILITY",
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        session_request={"session_id": SESSION_ID},
        network_allowed_from_authorization=True,
        authorization_id="auth_y",
        authorization_digest="digest_y",
        confirm_token_binding_sha256="b" * 64,
        confirm_token_plaintext=TOKEN,
        confirm_token_expires_at=NOW + 3600.0,
        now_unix=NOW,
        persistence_root=tmp_path,
    )
    assert result.ok is False
    assert "CAPABILITY_ID_MISMATCH_OR_MISSING" in result.blockers


def test_network_boundary_negatives(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    boundary = prove_public_md_network_boundary_v1(environ={"PATH": "/usr/bin", "HOME": "/tmp"})
    assert boundary["ok"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert boundary["AUTH_HEADER_PRESENT"] is False
    assert boundary["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert boundary["ORDER_SIDE_EFFECT_OCCURRED"] is False
    assert boundary["GET_ONLY_BOUND"] is True


def test_parity_core_logic_unchanged() -> None:
    parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
    assert parity["ok"] is True
    assert parity["claims"]["CORE_LOGIC_CHANGE"] is False
    assert parity["claims"]["EFFECTIVE_NUMERIC_VALUES_UNCHANGED"] is True


def test_failure_injection_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    fi = run_governed_productive_session_execution_failure_injection_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        persistence_root=tmp_path / "fi",
        now_unix=NOW,
    )
    assert fi["ok"] is True
    assert fi["claims"]["NO_NETWORK_SESSION"] is True
    assert fi["claims"]["NO_AUTHORIZATION_CONSUMPTION"] is True


def test_evidence_materialization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    summary = materialize_session_execution_implementation_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "evidence",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["network_session_executed"] is False
    assert summary["authorization_consumed"] is False
    assert summary["confirm_token_consumed"] is False
    assert (tmp_path / "evidence" / "SUMMARY.json").is_file()
    assert (tmp_path / "evidence" / "MANIFEST.sha256").is_file()
    blob = json.dumps(summary)
    assert TOKEN not in blob


def test_cli_prove_governed_productive_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    proc = subprocess.run(
        ["python3", str(CLI), "prove-governed-productive-execution", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["network_session_executed"] is False
    assert payload["authorization_consumed"] is False
    assert payload["real_network_request_count"] == 0
    assert payload["claims"]["NETWORK_SESSION_EXECUTED"] is False
    assert payload["claims"]["REAL_NETWORK_REQUEST_COUNT"] == 0
    assert payload["claims"]["AUTHORIZATION_CONSUMED"] is False
    # confirm_token_* claim keys are redacted by redact_mapping_for_logs; presence only.
    assert "CONFIRM_TOKEN_CONSUMED" in payload["claims"]
    assert TOKEN not in proc.stdout


def test_no_second_session_on_evidence_abort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    calls = {"n": 0}

    def _boom(**_kwargs: Any) -> dict[str, Any]:
        calls["n"] += 1
        raise RuntimeError("EVIDENCE_WRITE_FAILED")

    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        session_request=adapter.session_request,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_session_id=SESSION_ID,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
        wallclock_runner=_boom,
        invoke_productive_runner_dry=True,
    )
    assert proof.ok is False
    assert calls["n"] == 1
    assert proof.claims["NO_SECOND_SESSION_ON_EVIDENCE_FAILURE"] is True
    # Ensure no accidental consumption ledgers were written by implementation path.
    persist = tmp_path / "persist"
    assert not (persist / AUTHORIZATION_LEDGER_FILENAME).exists()
    assert not (persist / CONFIRM_TOKEN_LEDGER_FILENAME).exists()


def test_scope_mismatch_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha = _sha()
    paths = _write_issuance(tmp_path, sha=sha)
    adapter = build_canonical_session_request_from_issuance_artifacts_v1(
        preregistration_path=paths["preregistration"],
        operator_go_path=paths["operator_go"],
        authorization_artifact_path=paths["authorization_artifact"],
        confirm_token_file=None,
        fingerprint_ledger_path=paths["fingerprint_ledger"],
        expected_repository_sha=sha,
        permit_canonical_runner_invoke=True,
        request_governed_public_network=True,
        cli_network_session_allowed=True,
        expected_config_digest=_cfg(),
        confirm_token_getpass_fn=_getpass_for_token(TOKEN),
        require_hidden_pty=True,
    )
    assert adapter.ok is True
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=_cfg(),
        session_request=adapter.session_request,
        authorization_id=adapter.authorization_id,
        authorization_digest=adapter.authorization_digest,
        authorization_scope="WRONG_SCOPE",
        authorization_session_id=SESSION_ID,
        confirm_token_plaintext=TOKEN,
        confirm_token_binding_sha256=str(paths["binding"]),
        confirm_token_expires_at=NOW + 3600.0,
        confirm_token_expected_scope_digest=str(paths["scope"]),
        now_unix=NOW,
        persistence_root=tmp_path / "persist",
    )
    assert proof.ok is False
    assert any("SCOPE" in b for b in proof.blockers)


def test_confirm_token_not_in_argv_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        now_unix=NOW,
        argv=["--confirm-token", TOKEN],
    )
    assert proof.ok is False
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in proof.blockers
