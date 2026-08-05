"""Tests for Step-4 productive real-network session executor wiring."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    FAULT_SESSION_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED,
    TARGET_SESSION_ID,
    WIRING_CAPABILITY_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.evidence_v1 import (
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.productive_executor_v1 import (
    execute_productive_rate_limit_reconnect_session_wiring_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
    validate_session_evidence_schema_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_go_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.verifier_v1 import (
    verify_binding_manifest_v1,
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


def _issue_sgo(
    path: Path,
    *,
    sha: str,
    cfg: str,
    network: bool = True,
    expires_at: float | None = None,
) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_rl_executor_wiring_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=NOW,
        not_before=NOW,
        expires_at=expires_at if expires_at is not None else NOW + 3600,
        network_session_execution_authorized_by_this_go=network,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(path, auth.to_dict())


def test_wiring_constants_remain_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert FAULT_SESSION_ALLOWED is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED is False
    assert WIRING_CAPABILITY_ID.endswith("EXECUTOR_WIRING_V1")


def test_network_boundary_rejects_private_auth_and_credentials() -> None:
    boundary = prove_public_md_network_boundary_v1(environ={"PATH": "/usr/bin", "HOME": "/tmp"})
    assert boundary["ok"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert boundary["AUTH_HEADER_PRESENT"] is False
    assert boundary["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert boundary["ORDER_SIDE_EFFECT_OCCURRED"] is False


def test_evidence_schema_complete_and_not_observed() -> None:
    template = build_session_evidence_template_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        authorization_id_or_digest="auth_digest_test",
    )
    checked = validate_session_evidence_schema_v1(template)
    assert checked["ok"] is True
    assert template["session_id"] == TARGET_SESSION_ID
    assert template["claims"]["RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED"] is False
    assert template["claims"]["OBSERVED_SESSION"] is False


def test_executor_requires_execute_flag(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    result = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=False,
        allow_real_network=False,
    )
    assert result.ok is False
    assert "EXECUTE_MODE_REQUIRED" in result.blockers
    assert result.network_session_started is False
    assert result.claims["READY_FOR_PRODUCTIVE_SESSION_EXECUTION"] is False


def test_executor_rejects_real_network_flag(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    result = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=True,
        allow_real_network=True,
    )
    assert result.ok is False
    assert "REAL_NETWORK_FORBIDDEN_IN_WIRING_CAPABILITY" in result.blockers
    assert result.network_session_started is False
    assert result.wallclock_runner_invoked is False


def test_executor_gate_rejects_wrong_sha_cfg_auth_token_expiry(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)

    bad_sha = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha="0" * 40,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=True,
    )
    assert bad_sha.ok is False
    assert "SESSION_GO_REPOSITORY_SHA_MISMATCH" in bad_sha.blockers

    bad_cfg = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest="deadbeef",
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=True,
    )
    assert bad_cfg.ok is False
    assert "SESSION_GO_CONFIG_DIGEST_MISMATCH" in bad_cfg.blockers

    no_auth = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=False,
        confirm_token_present_flag=True,
        execute=True,
    )
    assert no_auth.ok is False
    assert "AUTHORIZATION_REQUIRED" in no_auth.blockers

    missing_confirm = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=False,
        execute=True,
    )
    assert missing_confirm.ok is False
    assert "CONFIRM_TOKEN_REQUIRED" in missing_confirm.blockers

    expired = tmp_path / "expired.json"
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_rl_executor_expired_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=NOW - 100,
        not_before=NOW - 100,
        expires_at=NOW - 1,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(expired, auth.to_dict())
    expired_res = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=expired,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=True,
    )
    assert expired_res.ok is False
    assert "SESSION_GO_EXPIRED" in expired_res.blockers


def test_executor_happy_path_binds_without_starting_network(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    result = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=True,
        allow_real_network=False,
    )
    assert result.ok is True
    assert result.productive_session_reachable is True
    assert result.ready_for_productive_session_execution is True
    assert result.canonical_wallclock_runner_bound is True
    assert result.rate_limit_owner_reused is True
    assert result.reconnect_owner_reused is True
    assert result.heartbeat_staleness_owner_reused is True
    assert result.fault_owner_reused is True
    assert result.network_session_started is False
    assert result.fault_session_started is False
    assert result.rate_limit_path_productively_observed is False
    assert result.reconnect_path_productively_observed is False
    assert result.rate_limit_reconnect_ladder_step_closed is False
    assert result.wallclock_runner_invoked is False
    assert result.productive_step_4_session_path_runtime_reachable is True
    assert result.productive_call_graph_complete is True
    assert "run_productive_wallclock_session_v1" in result.call_graph
    assert result.claims["PARALLEL_SESSION_RUNTIME_CREATED"] is False


def test_verifier_separates_readiness_from_closure() -> None:
    good = {
        "claims": {
            "RATE_LIMIT_RECONNECT_BINDING_IMPLEMENTED": True,
            "REAL_NETWORK_SESSION_NOT_STARTED": True,
            "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": True,
            "GOVERNED_FAULT_PATH_BOUND": True,
            "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": True,
            "EXECUTOR_CODE_EXISTS": True,
            "EXECUTOR_PRODUCTIVELY_BOUND": True,
            "PRODUCTIVE_SESSION_REACHABLE": True,
            "NETWORK_SESSION_STARTED": False,
            "FAULT_SESSION_STARTED": False,
            "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": False,
            "RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED": False,
            "RECONNECT_PATH_PRODUCTIVELY_OBSERVED": False,
        }
    }
    verified = verify_binding_manifest_v1(good)
    assert verified["ok"] is True
    assert verified["readiness_vs_closure"]["READY_FOR_PRODUCTIVE_SESSION_EXECUTION"] is True
    assert verified["readiness_vs_closure"]["RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED"] is False

    closed = {
        "claims": {
            **good["claims"],
            "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": True,
        }
    }
    bad = verify_binding_manifest_v1(closed)
    assert bad["ok"] is False
    assert any("FORBIDDEN_CLAIM_TRUE" in b for b in bad["blockers"])


def test_materialize_includes_executor_readiness(tmp_path: Path) -> None:
    summary = materialize_capability_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "evidence",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["claims"]["READY_FOR_PRODUCTIVE_SESSION_EXECUTION"] is True
    assert summary["claims"]["PRODUCTIVE_SESSION_REACHABLE"] is True
    assert summary["claims"]["RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED"] is False
    assert summary["claims"]["NETWORK_SESSION_STARTED"] is False
    assert (tmp_path / "evidence" / "fixtures" / "productive_executor_result_v1.json").is_file()
    assert (tmp_path / "evidence" / "fixtures" / "session_evidence_template_v1.json").is_file()


def test_cli_execute_productive_session_and_request_real_network_refuse(tmp_path: Path) -> None:
    import time

    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    now = float(time.time())
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_rl_executor_cli_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(sgo, auth.to_dict())

    ok = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--execute",
            "--owner-go",
            "--owner-session-go",
            "--authorization-present",
            "--confirm-token-present",
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
    assert ok.returncode == 0, ok.stdout + ok.stderr
    payload = json.loads(ok.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False
    assert payload["ready_for_productive_session_execution"] is True

    refused = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--execute",
            "--owner-go",
            "--owner-session-go",
            "--authorization-present",
            "--confirm-token-present",
            "--session-go-file",
            str(sgo),
            "--request-real-network",
            "--expected-repository-sha",
            sha,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 2
    refused_payload = json.loads(refused.stdout)
    # Activation path: without network_session_allowed / auth artifacts, fail closed.
    assert refused_payload["network_session_started"] is False
    assert refused_payload.get("wallclock_runner_invoked") is False
    assert "NETWORK_SESSION_ALLOWED_REQUIRED" in refused_payload["blockers"]

    no_execute = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--owner-go",
            "--owner-session-go",
            "--authorization-present",
            "--confirm-token-present",
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
    assert no_execute.returncode == 2
    no_exec_payload = json.loads(no_execute.stdout)
    assert "EXECUTE_MODE_REQUIRED" in no_exec_payload["blockers"]
