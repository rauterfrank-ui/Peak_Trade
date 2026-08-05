"""Tests for PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.binding_gate_v1 import (
    assert_no_parallel_productive_authority_v1,
    evaluate_rate_limit_reconnect_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CORE_LOGIC_CHANGE,
    FAULT_SESSION_EXECUTION_AUTHORIZED,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.evidence_v1 import (
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.failure_injection_v1 import (
    run_rate_limit_reconnect_binding_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.fault_path_v1 import (
    prove_governed_fault_path_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
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


def _issue_sgo(path: Path, *, sha: str, cfg: str, network: bool = True) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_rl_binding_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=NOW,
        not_before=NOW,
        expires_at=NOW + 3600,
        network_session_execution_authorized_by_this_go=network,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(path, auth.to_dict())


def test_parity_and_no_parallel_authority() -> None:
    parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()
    assert parity["ok"] is True
    assert CORE_LOGIC_CHANGE is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert FAULT_SESSION_EXECUTION_AUTHORIZED is False
    assert authority["ok"] is True
    assert authority["parallel_productive_authority_detected"] is False


def test_session_contract_loads_and_reuses_smoke_budgets() -> None:
    contract = load_and_validate_session_contract_v1(repo_root=REPO_ROOT)
    assert contract["session_id"] == TARGET_SESSION_ID
    assert contract["session_ladder_step"] == "RATE_LIMIT_RECONNECT_SESSION"
    assert contract["network_session_authorized"] is False
    assert contract["fault_session_execution_authorized"] is False


def test_gate_fail_closed_matrix(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)

    missing = evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=None,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert missing.ok is False
    assert "SESSION_GO_MISSING" in missing.blockers

    no_owner = evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=False,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert no_owner.ok is False
    assert "OWNER_GO_REQUIRED" in no_owner.blockers

    happy = evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=False,
    )
    assert happy.ok is True
    assert happy.network_session_started is False
    assert happy.fault_session_started is False
    assert happy.real_network_may_proceed is False


def test_confirm_token_argv_rejected() -> None:
    blockers = reject_confirm_token_argv_v1(["gate", "--confirm-token", "secret"])
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in blockers


def test_governed_fault_path_offline() -> None:
    fault = prove_governed_fault_path_offline_v1()
    assert fault["ok"] is True
    assert fault["fault_session_started"] is False
    assert fault["network_session_started"] is False
    assert fault["claims"]["GOVERNED_FAULT_PATH_BOUND"] is True
    assert fault["claims"]["ZERO_INTERVAL_RETRY"] is False


def test_failure_injection_matrix(tmp_path: Path) -> None:
    result = run_rate_limit_reconnect_binding_failure_injection_v1(
        persistence_root=tmp_path / "fi",
        repository_sha=_sha(),
        repo_root=REPO_ROOT,
        now_unix=NOW,
    )
    assert result["ok"] is True
    assert result["fault_session_started"] is False
    assert result["network_session_started"] is False


def test_materialize_evidence(tmp_path: Path) -> None:
    summary = materialize_capability_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "evidence",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["claims"]["RATE_LIMIT_RECONNECT_BINDING_IMPLEMENTED"] is True
    assert summary["claims"]["RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED"] is False
    assert summary["claims"]["NETWORK_SESSION_STARTED"] is False
    assert summary["claims"]["FAULT_SESSION_STARTED"] is False
    assert (tmp_path / "evidence" / "SUMMARY.json").is_file()
    assert (tmp_path / "evidence" / "MANIFEST.sha256").is_file()


def test_cli_preflight_and_prove_fault_path() -> None:
    pre = subprocess.run(
        [sys.executable, str(CLI), "preflight"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert pre.returncode == 0, pre.stdout + pre.stderr
    payload = json.loads(pre.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False

    fault = subprocess.run(
        [sys.executable, str(CLI), "prove-fault-path"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert fault.returncode == 0, fault.stdout + fault.stderr
    fault_payload = json.loads(fault.stdout)
    assert fault_payload["ok"] is True

    refused = subprocess.run(
        [sys.executable, str(CLI), "prove-fault-path", "--request-real-network"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 2
    refused_payload = json.loads(refused.stdout)
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI" in refused_payload["blockers"]
