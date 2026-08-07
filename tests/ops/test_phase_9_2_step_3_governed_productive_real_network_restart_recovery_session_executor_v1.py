"""Offline tests for Step-3 governed restart/recovery session executor.

No real DNS/socket/HTTP. No auth/token issuance or productive consumption.
Surface fail-closed preserved. No secrets in logs/evidence/argv.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.digest_v1 import (
    write_json_atomic_v1 as write_sgo_json_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as SURFACE_NETWORK_SESSION_ALLOWED,
    REAL_NETWORK_REQUESTS_ALLOWED as SURFACE_REAL_NETWORK_ALLOWED,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.governed_execution_surface_v1 import (
    request_real_network_fail_closed_v1 as surface_request_real_network_fail_closed_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.authorization_gate_v1 import (
    record_authorization_consumption_boundary_v1,
    validate_execution_authorization_artifact_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_ENTRYPOINT_PATH,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_SCOPE,
    SURFACE_CLI_PATH,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.evidence_v1 import (
    materialize_implementation_evidence_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.failure_injection_v1 import (
    run_step3_executor_failure_injection_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.governed_executor_execution_v1 import (
    assemble_execution_request_v1,
    execute_governed_step3_executor_session_v1,
    prove_step3_executor_implementation_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.hidden_pty_handoff_v1 import (
    fingerprint_only_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.network_boundary_v1 import (
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.session_lock_gate_v1 import (
    prove_second_writer_rejected_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.surface_consumer_v1 import (
    consume_surface_implementation_proof_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SURFACE_CLI = REPO_ROOT / SURFACE_CLI_PATH
EXEC_CLI = REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH
TOKEN = "PTCONFIRMv1_STEP3EXECTEST" + ("A" * 16)
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


def _issue_sgo(path: Path, *, sha: str, cfg: str) -> None:
    authority = build_session_go_authority_v1(
        session_go_id="sgo_step3_executor_test_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=NOW,
        not_before=NOW,
        expires_at=NOW + 3600.0,
        activation_status=ACTIVATION_STATUS_ACTIVE,
        max_session_duration_seconds=3600,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
        notes=("TEST_EPHEMERAL_SESSION_GO",),
    )
    write_sgo_json_v1(path, authority.to_dict())


def test_constants_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert REAL_NETWORK_REQUESTS_ALLOWED is False
    assert AUTHORIZATION_CONSUMPTION_ALLOWED is False
    assert CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False
    assert SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED is False
    assert CAPABILITY_ID.endswith("EXECUTOR_IMPLEMENTATION_V1")
    assert SURFACE_NETWORK_SESSION_ALLOWED is False
    assert SURFACE_REAL_NETWORK_ALLOWED is False


def test_executor_and_surface_entrypoint_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    assert SURFACE_CLI.is_file()
    assert EXEC_CLI.is_file()
    assert SURFACE_CLI.resolve() != EXEC_CLI.resolve()
    surface = surface_request_real_network_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert surface.ok is False
    assert "REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION" in surface.blockers


def test_executor_import_and_surface_consumed(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    proof = prove_step3_executor_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        repo_root=REPO_ROOT,
    )
    assert proof.ok is True
    assert proof.claims["STEP3_PRODUCTIVE_EXECUTOR_IMPLEMENTED"] is True
    assert proof.claims["STEP3_EXECUTION_SURFACE_UNCHANGED_FAIL_CLOSED"] is True
    assert proof.claims["SURFACE_NOT_DUPLICATED"] is True
    assert proof.claims["NETWORK_SESSION_STARTED"] is False
    surface = consume_surface_implementation_proof_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        repo_root=REPO_ROOT,
    )
    assert surface["ok"] is True
    assert surface["SURFACE_NOT_DUPLICATED"] is True


def test_cli_offline_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    for command, expect_rc in (
        ("preflight", 0),
        ("assemble-execution-request", 0),
        ("request-real-network", 2),
        ("execute-governed-session", 2),
    ):
        proc = subprocess.run(
            [str(EXEC_CLI), command],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == expect_rc, (command, proc.stdout, proc.stderr)
        payload = json.loads(proc.stdout)
        assert payload.get("network_session_started") in (False, None) or (
            payload.get("claims", {}).get("NETWORK_SESSION_STARTED") is False
        )


def test_confirm_token_argv_env_rejected() -> None:
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in reject_confirm_token_argv_v1(
        ["--confirm-token", "secret"]
    )
    assert "CONFIRM_TOKEN_ENV_FALLBACK_FORBIDDEN" in reject_confirm_token_env_fallback_v1(
        {"CONFIRM_TOKEN": "secret"}
    )


def test_gates_and_bindings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    fp = fingerprint_only_v1(TOKEN)
    auth_id = "auth_step3_exec_test_v1"
    auth_digest = sha256_canonical_v1({"authorization_id": auth_id, "sha": sha})
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)

    assert (
        execute_governed_step3_executor_session_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_session_contract_digest=bundle["session_contract_digest"],
            expected_binding_config_digest=bundle["binding_config_digest"],
            authorization_id=auth_id,
            authorization_digest=auth_digest,
            confirm_token_binding_sha256=fp,
            persistence_root=tmp_path / "p1",
            evidence_root=tmp_path / "e1",
            session_go_path=sgo,
            now_unix=NOW,
            confirm_token_plaintext=TOKEN,
            owner_go=False,
            operator_authorization_explicit=True,
            network_session_go=True,
            repo_root=REPO_ROOT,
        ).blockers
        and "OWNER_GO_REQUIRED"
        in execute_governed_step3_executor_session_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_session_contract_digest=bundle["session_contract_digest"],
            expected_binding_config_digest=bundle["binding_config_digest"],
            authorization_id=auth_id,
            authorization_digest=auth_digest,
            confirm_token_binding_sha256=fp,
            persistence_root=tmp_path / "p1b",
            evidence_root=tmp_path / "e1b",
            session_go_path=sgo,
            now_unix=NOW,
            confirm_token_plaintext=TOKEN,
            owner_go=False,
            operator_authorization_explicit=True,
            network_session_go=True,
            repo_root=REPO_ROOT,
        ).blockers
    )

    no_net = execute_governed_step3_executor_session_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_id=auth_id,
        authorization_digest=auth_digest,
        confirm_token_binding_sha256=fp,
        persistence_root=tmp_path / "p2",
        evidence_root=tmp_path / "e2",
        session_go_path=sgo,
        now_unix=NOW,
        confirm_token_plaintext=TOKEN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        repo_root=REPO_ROOT,
    )
    assert "NETWORK_SESSION_GO_REQUIRED" in no_net.blockers
    assert no_net.network_session_started is False

    wrong_sha = validate_execution_authorization_artifact_v1(
        authorization_id=auth_id,
        authorization_digest=auth_digest,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_repository_sha="0" * 40,
        now_unix=NOW,
        authorization_expires_at=NOW + 10,
    )
    assert "AUTHORIZATION_SHA_MISMATCH" in wrong_sha["blockers"]

    expired = validate_execution_authorization_artifact_v1(
        authorization_id=auth_id,
        authorization_digest=auth_digest,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        now_unix=NOW,
        authorization_expires_at=NOW - 1,
    )
    assert "AUTHORIZATION_EXPIRED" in expired["blockers"]

    token_bad = validate_confirm_token_binding_v1(
        confirm_token_plaintext=TOKEN,
        expected_binding_sha256="0" * 64,
        expected_repository_sha=sha,
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        expires_at=NOW + 10,
        now_unix=NOW,
    )
    assert "CONFIRM_TOKEN_DIGEST_MISMATCH" in token_bad["blockers"]

    token_ok = validate_confirm_token_binding_v1(
        confirm_token_plaintext=TOKEN,
        expected_binding_sha256=fp,
        expected_repository_sha=sha,
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        expires_at=NOW + 10,
        now_unix=NOW,
    )
    assert token_ok["ok"] is True
    assert token_ok["plaintext_exposed"] is False


def test_single_consume_and_no_plaintext_in_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    ledger = tmp_path / "ledger.jsonl"
    first = record_authorization_consumption_boundary_v1(
        ledger_path=ledger,
        authorization_id="auth_once",
        authorization_digest="d1",
        session_id=TARGET_SESSION_ID,
        now_unix=NOW,
        allow_consume=True,
        allow_ephemeral_consume=True,
    )
    second = record_authorization_consumption_boundary_v1(
        ledger_path=ledger,
        authorization_id="auth_once",
        authorization_digest="d1",
        session_id=TARGET_SESSION_ID,
        now_unix=NOW + 1,
        allow_consume=True,
        allow_ephemeral_consume=True,
    )
    assert first["ok"] is True
    assert second["ok"] is False
    assert "AUTHORIZATION_ALREADY_CONSUMED" in second["blockers"]
    text = ledger.read_text(encoding="utf-8")
    assert TOKEN not in text
    assert "confirm_token" not in text.lower()
    assert '"plaintext_persisted":false' in text.replace(" ", "")


def test_network_boundary_and_methods(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    ok = prove_public_md_get_only_boundary_v1(method="GET", host="eea.okx.com")
    assert ok["ok"] is True
    assert ok["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert ok["AUTH_HEADER_PRESENT"] is False
    assert prove_public_md_get_only_boundary_v1(method="POST")["ok"] is False
    assert prove_public_md_get_only_boundary_v1(path="/api/v5/private/account")["ok"] is False
    assert prove_public_md_get_only_boundary_v1(auth_header_present=True)["ok"] is False


def test_session_lock_single_writer(tmp_path: Path) -> None:
    proof = prove_second_writer_rejected_v1(persistence_root=tmp_path)
    assert proof["ok"] is True
    assert proof["SINGLE_WRITER_ENFORCED"] is True


def test_offline_restart_campaign_and_digests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    fp = fingerprint_only_v1(TOKEN)
    auth_id = "auth_step3_exec_campaign_v1"
    auth_digest = sha256_canonical_v1({"authorization_id": auth_id, "sha": sha})
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    result = execute_governed_step3_executor_session_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_id=auth_id,
        authorization_digest=auth_digest,
        confirm_token_binding_sha256=fp,
        persistence_root=tmp_path / "persist",
        evidence_root=tmp_path / "evidence",
        session_go_path=sgo,
        now_unix=NOW,
        confirm_token_plaintext=TOKEN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        invoke_executor=True,
        allow_real_network_side_effects=False,
        repo_root=REPO_ROOT,
    )
    # Default path remains fail-closed for productive network start.
    assert result.network_session_started is False
    assert result.claims.get("OFFLINE_INJECTED_EXECUTOR_OBSERVED") is True
    assert result.executor_result is not None
    assert result.executor_result.get("pre_state_digest")
    assert result.executor_result.get("post_recovery_state_digest")
    assert result.claims.get("RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART") is True
    assert result.claims.get("NO_DUPLICATE_CONFIRMATION_ADVANCE") is True
    assert result.claims.get("CONFIRMATION_SESSION_ID_STABLE_ACROSS_RESTART") is True
    assert result.claims.get("INSTRUMENT_IDENTITY_STABLE") is True
    assert result.claims.get("EVIDENCE_RECOVERY_IDEMPOTENT") is True


def test_request_real_network_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY" in result.blockers


def test_parity_and_assemble(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    parity = prove_trading_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["claims"]["GOLDEN_VECTOR_PARITY_PASS"] is True
    assembled = assemble_execution_request_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert assembled["ok"] is True
    assert assembled["network_session_started"] is False


def test_manifest_verify_and_materialize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    summary = materialize_implementation_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "ev",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["network_session_started"] is False
    manifest = json.loads(
        (tmp_path / "ev" / "fixtures" / "session_manifest_template_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert verify_session_manifest_v1(manifest)["ok"] is True
    bad = dict(manifest)
    bad["claims"] = dict(manifest["claims"])
    bad["claims"]["NETWORK_SESSION_STARTED"] = True
    bad.pop("manifest_digest", None)
    bad["manifest_digest"] = sha256_canonical_v1(bad)
    assert verify_session_manifest_v1(bad)["ok"] is False


def test_failure_injection_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    fi = run_step3_executor_failure_injection_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        persistence_root=tmp_path / "fi",
        repo_root=REPO_ROOT,
    )
    assert fi["ok"] is True, fi
    assert fi["network_session_started"] is False


def test_surface_regression_still_green(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/ops/test_phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_surface_v1.py",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
