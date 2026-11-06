"""Tests for PHASE_9_2_PRODUCTIVE_PUBLIC_MD_PROLONGED_NATURAL_MARKET_WALLCLOCK_BINDING_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.authorization_binding_v1 import (
    validate_authorization_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.binding_gate_v1 import (
    assert_no_parallel_productive_authority_v1,
    evaluate_prolonged_natural_market_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.claims_v1 import (
    classify_reconnect_claims_v1,
    classify_trade_outcome_claims_v1,
    prove_claim_semantics_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    CORE_LOGIC_CHANGE,
    FAULT_SESSION_EXECUTION_AUTHORIZED,
    MAX_WALLCLOCK_DURATION_SECONDS,
    MIN_WALLCLOCK_DURATION_SECONDS,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    RECONNECT_PATH_STATUS_NOT_NATURAL,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.disk_preflight_v1 import (
    evaluate_disk_capacity_preflight_v1,
    prove_disk_and_evidence_bounds_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.evidence_v1 import (
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.failure_injection_v1 import (
    run_prolonged_natural_market_binding_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.parity_v1 import (
    prove_phase92_prolonged_natural_market_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
    validate_planned_duration_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_go_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_request_cli_adapter_v1 import (
    SessionRequestAdapterError,
    bind_session_request_to_runner_kwargs_v1,
    build_step5_session_request_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.py"
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
        session_go_id="sgo_test_step5_binding_v1",
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
    parity = prove_phase92_prolonged_natural_market_wallclock_binding_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()
    assert parity["ok"] is True
    assert CORE_LOGIC_CHANGE is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert FAULT_SESSION_EXECUTION_AUTHORIZED is False
    assert authority["ok"] is True
    assert authority["parallel_productive_authority_detected"] is False
    assert authority["reuse_proof"]["STEP5_BINDING_EXPLICIT"] is True


def test_session_contract_loads_with_prolonged_bounds() -> None:
    contract = load_and_validate_session_contract_v1(repo_root=REPO_ROOT)
    assert contract["session_id"] == TARGET_SESSION_ID
    assert contract["session_ladder_step"] == "PROLONGED_NATURAL_MARKET_SESSION"
    assert contract["min_session_duration_seconds"] == MIN_WALLCLOCK_DURATION_SECONDS
    assert contract["max_session_duration_seconds"] == MAX_WALLCLOCK_DURATION_SECONDS
    assert contract["network_session_authorized"] is False
    assert contract["fault_session_execution_authorized"] is False


def test_duration_bounds_unit() -> None:
    assert validate_planned_duration_v1(7200) == []
    assert validate_planned_duration_v1(21600) == []
    assert "DURATION_BELOW_MIN" in validate_planned_duration_v1(7199)
    assert "DURATION_BOUND_VIOLATION" in validate_planned_duration_v1(21601)


def test_reconnect_claim_not_overstated() -> None:
    claims = classify_reconnect_claims_v1(
        reconnect_path_reachable=True,
        reconnect_timeline=[],
        reconnect_path_status=RECONNECT_PATH_STATUS_NOT_NATURAL,
    )
    assert claims["RECONNECT_PATH_REACHABLE"] is True
    assert claims["RECONNECT_NATURALLY_OCCURRED"] is False
    assert claims["RECONNECT_OBSERVED"] is False
    trade = classify_trade_outcome_claims_v1()
    assert trade["ENTRY_OBSERVED"] is False
    assert trade["NATURAL_ABSENCE_ALLOWED"] is True
    proof = prove_claim_semantics_offline_v1()
    assert proof["ok"] is True


def test_gate_fail_closed_matrix(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)

    missing = evaluate_prolonged_natural_market_wallclock_binding_gate_v1(
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

    no_owner = evaluate_prolonged_natural_market_wallclock_binding_gate_v1(
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

    happy = evaluate_prolonged_natural_market_wallclock_binding_gate_v1(
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


def test_authorization_negatives() -> None:
    sha, cfg = _sha(), _cfg()
    ok = validate_authorization_binding_v1(
        authorization_id="auth1",
        authorization_digest="a" * 64,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
    )
    assert ok["ok"] is True
    reuse = validate_authorization_binding_v1(
        authorization_id="auth1",
        authorization_digest="a" * 64,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        step4_authorization_reuse=True,
    )
    assert reuse["ok"] is False
    assert "STEP4_AUTHORIZATION_REUSE_FORBIDDEN" in reuse["blockers"]
    consumed = validate_authorization_binding_v1(
        authorization_id="auth1",
        authorization_digest="a" * 64,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        already_consumed=True,
    )
    assert "AUTHORIZATION_ALREADY_CONSUMED" in consumed["blockers"]


def test_session_request_adapter_integration() -> None:
    sha, cfg = _sha(), _cfg()
    request = build_step5_session_request_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        planned_session_duration_seconds=7200,
    )
    kwargs = bind_session_request_to_runner_kwargs_v1(request)
    assert kwargs["invoke_runner"] is False
    assert kwargs["network_session_allowed"] is False
    assert kwargs["duration_seconds"] == 7200
    try:
        build_step5_session_request_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            planned_session_duration_seconds=21601,
        )
        raise AssertionError("expected duration failure")
    except SessionRequestAdapterError as exc:
        assert "DURATION_BOUND_VIOLATION" in str(exc)


def test_disk_preflight_and_failure_injection(tmp_path: Path) -> None:
    disk = prove_disk_and_evidence_bounds_offline_v1(check_path=tmp_path / "disk")
    assert disk["ok"] is True
    fail = evaluate_disk_capacity_preflight_v1(
        check_path=tmp_path / "disk2",
        free_bytes=1,
    )
    assert fail["ok"] is False
    assert "DISK_PREFLIGHT_FAIL" in fail["blockers"]

    result = run_prolonged_natural_market_binding_failure_injection_v1(
        persistence_root=tmp_path / "fi",
        repository_sha=_sha(),
        repo_root=REPO_ROOT,
        now_unix=NOW,
    )
    assert result["ok"] is True
    assert result["fault_session_started"] is False
    assert result["network_session_started"] is False
    assert result["authorization_consumed"] is False
    assert result["confirm_token_consumed"] is False


def test_materialize_evidence(tmp_path: Path) -> None:
    summary = materialize_capability_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "evidence",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["claims"]["PROLONGED_NATURAL_MARKET_BINDING_IMPLEMENTED"] is True
    assert summary["claims"]["PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED"] is False
    assert summary["claims"]["CAPABILITY_CLOSED"] is False
    assert summary["claims"]["NETWORK_SESSION_STARTED"] is False
    assert summary["claims"]["RECONNECT_OBSERVED"] is False
    assert summary["claims"]["RECONNECT_PATH_STATUS"] == RECONNECT_PATH_STATUS_NOT_NATURAL
    assert summary["claims"]["AUTHORIZATION_CONSUMED"] is False
    assert (tmp_path / "evidence" / "SUMMARY.json").is_file()
    assert (tmp_path / "evidence" / "MANIFEST.sha256").is_file()


def test_cli_preflight_and_claim_semantics() -> None:
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

    claims = subprocess.run(
        [sys.executable, str(CLI), "prove-claim-semantics"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert claims.returncode == 0, claims.stdout + claims.stderr
    claim_payload = json.loads(claims.stdout)
    assert claim_payload["ok"] is True
    assert claim_payload["natural_absence"]["RECONNECT_OBSERVED"] is False

    refused = subprocess.run(
        [sys.executable, str(CLI), "prove-claim-semantics", "--request-real-network"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 2
    refused_payload = json.loads(refused.stdout)
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI" in refused_payload["blockers"]
