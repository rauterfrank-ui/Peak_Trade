"""Tests for PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (  # noqa: E501
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (  # noqa: E501
    DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
    DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED,
    RESTART_CAMPAIGN_ID,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.fake_public_md_v1 import (  # noqa: E501
    build_fake_ticker_fetcher_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.network_boundary_v1 import (  # noqa: E501
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (  # noqa: E501
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.constants_v1 import (  # noqa: E501
    CANONICAL_RUNTIME_RUNNER,
    CAPABILITY_ID,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.failure_injection_v1 import (  # noqa: E501
    run_post_unlock_failure_injection_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.invocation_v1 import (  # noqa: E501
    invoke_post_unlock_canonical_runtime_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.parity_v1 import (  # noqa: E501
    prove_phase92_post_unlock_invocation_parity_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.verifier_v1 import (  # noqa: E501
    verify_post_unlock_invocation_manifest_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (  # noqa: E501
    ledger_path_for_root_v1,
    load_consumed_authorization_ids_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (  # noqa: E501
    lock_path_for_root_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT_CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py"
)
SESSION_GO_CLI = (
    REPO_ROOT / "scripts/ops/run_phase_9_2_productive_restart_recovery_session_go_capability_v1.py"
)
CAPABILITY_CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.py"
)
NOW = 1_700_000_000.0


class _Clock:
    def __init__(self, start: float = NOW) -> None:
        self._t = float(start)

    def time(self) -> float:
        return self._t

    def sleep(self, seconds: float) -> None:
        self._t += float(seconds)


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


def _write_sgo(path: Path, *, sha: str, cfg: str, now: float = NOW) -> str:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_post_unlock_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=now - 10,
        not_before=now - 5,
        expires_at=now + 3600,
        activation_status=ACTIVATION_STATUS_ACTIVE,
    )
    write_json_atomic_v1(path, auth.to_dict())
    return auth.session_go_digest


def _transport(clock: _Clock | None = None) -> tuple[EeaPublicMdTransportV1, list[tuple[str, str]]]:
    clock = clock or _Clock()
    calls: list[tuple[str, str]] = []
    transport = EeaPublicMdTransportV1(
        fetcher=build_fake_ticker_fetcher_v1(calls=calls, clock=clock),
        sleep=clock.sleep,
        environ={},
    )
    return transport, calls


def _pre(sha: str, cfg: str, auth_id: str = "auth_pre_test_v1"):
    return build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=sha,
        config_digest=cfg,
        authorization_id=auth_id,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=NOW + 3600,
        max_segment_duration_seconds=DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )


def _post_builder(sha: str, auth_id: str = "auth_post_test_v1"):
    def builder(**kwargs):
        return build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=sha,
            config_digest=kwargs["config_digest"],
            authorization_id=auth_id,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=NOW + 3600,
            max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
        )

    return builder


def test_01_preflight_and_constants() -> None:
    assert CAPABILITY_ID.endswith("POST_UNLOCK_RUNTIME_INVOCATION_V1")
    assert "run_offline_productive_restart_orchestration_v1" in CANONICAL_RUNTIME_RUNNER
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED is False
    proc = subprocess.run(
        [sys.executable, str(CAPABILITY_CLI), "preflight"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False


def test_02_a_gate_false_no_runner_no_consume_no_lock(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    transport, _ = _transport()
    result = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=tmp_path / "missing.json",
        pre_envelope=_pre(sha, cfg),
        post_envelope_builder=_post_builder(sha),
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.canonical_runner_invoked is False
    assert result.authorization_consumed is False
    assert result.canonical_runner_invocation_count == 0
    assert not lock_path_for_root_v1(tmp_path).is_file()
    assert load_consumed_authorization_ids_v1(ledger_path_for_root_v1(tmp_path)) == set()


def test_03_b_gate_true_auth_flag_missing_hard_stop(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    _write_sgo(sgo, sha=sha, cfg=cfg)
    transport, _ = _transport()
    result = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        pre_envelope=_pre(sha, cfg),
        post_envelope_builder=_post_builder(sha),
        transport=transport,
        confirm_token_present=True,
        authorization_present=False,
        execute=True,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.canonical_runner_invoked is False
    assert result.authorization_consumed is False
    assert "SESSION_GO_VALID_BUT_AUTHORIZATION_REQUIRED" in result.blockers


def test_04_c_gate_true_auth_valid_consume_lock_runner_once(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    digest = _write_sgo(sgo, sha=sha, cfg=cfg)
    transport, calls = _transport()
    result = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        pre_envelope=_pre(sha, cfg, auth_id="auth_pre_c"),
        post_envelope_builder=_post_builder(sha, auth_id="auth_post_c"),
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        repo_root=REPO_ROOT,
        applied_confirmation_ids=["conf_c_001"],
        candidate_observation_id="conf_c_001",
    )
    assert result.ok is True, result.blockers
    assert result.productive_session_execution_permitted is True
    assert result.authorization_validated is True
    assert result.authorization_consumed is True
    assert result.authorization_consumed_exactly_once is True
    assert result.session_lock_acquired is True
    assert result.session_lock_released is True
    assert result.canonical_runner_invoked is True
    assert result.canonical_runner_invocation_count == 1
    assert result.restart_recovery_completed is True
    assert result.reconciliation_before_alpha is True
    assert result.network_session_started is False
    assert result.session_go_digest == digest
    assert not lock_path_for_root_v1(tmp_path).is_file()
    consumed = load_consumed_authorization_ids_v1(ledger_path_for_root_v1(tmp_path))
    assert "auth_pre_c" in consumed
    assert "auth_post_c" in consumed
    assert all(m == "GET" for m, _u in calls)
    verified = verify_post_unlock_invocation_manifest_v1(
        persistence_root=tmp_path, expected_ok=True
    )
    assert verified["ok"] is True
    assert verified["claims_match_telemetry"] is True


def test_05_d_double_invocation_fail_closed(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    _write_sgo(sgo, sha=sha, cfg=cfg)
    transport, _ = _transport()
    first = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        pre_envelope=_pre(sha, cfg, auth_id="auth_pre_d"),
        post_envelope_builder=_post_builder(sha, auth_id="auth_post_d"),
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        repo_root=REPO_ROOT,
        applied_confirmation_ids=["conf_d_001"],
        candidate_observation_id="conf_d_001",
    )
    assert first.ok is True
    second = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        pre_envelope=_pre(sha, cfg, auth_id="auth_pre_d"),
        post_envelope_builder=_post_builder(sha, auth_id="auth_post_d2"),
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        repo_root=REPO_ROOT,
    )
    assert second.ok is False
    assert second.canonical_runner_invoked is False
    assert "AUTHORIZATION_ALREADY_CONSUMED_FAIL_CLOSED" in second.blockers


def test_06_e_runner_exception_abort_no_blind_retry(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    _write_sgo(sgo, sha=sha, cfg=cfg)
    transport, _ = _transport()

    def boom(**_kwargs):
        raise RuntimeError("INJECTED")

    result = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        pre_envelope=_pre(sha, cfg, auth_id="auth_pre_e"),
        post_envelope_builder=_post_builder(sha),
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        runtime_runner=boom,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.terminal_state == "ABORT"
    assert result.canonical_runner_invocation_count == 1
    assert result.claims.get("BLIND_RETRY_PERFORMED") is False
    assert not lock_path_for_root_v1(tmp_path).is_file()


def test_07_f_restart_recovery_ids_and_reconciliation(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    _write_sgo(sgo, sha=sha, cfg=cfg)
    transport, _ = _transport()
    result = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        pre_envelope=_pre(sha, cfg, auth_id="auth_pre_f"),
        post_envelope_builder=_post_builder(sha, auth_id="auth_post_f"),
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        repo_root=REPO_ROOT,
        applied_confirmation_ids=["conf_f_001"],
        candidate_observation_id="conf_f_001",
    )
    assert result.ok is True
    assert result.restart_recovery_completed is True
    assert result.reconciliation_before_alpha is True
    assert result.session_id == TARGET_SESSION_ID
    campaign = result.campaign or {}
    assert campaign.get("session_id") == TARGET_SESSION_ID
    post = campaign.get("post") or {}
    assert post.get("reconciliation_before_alpha") is True
    telemetry = post.get("telemetry") or {}
    # Harness proves no duplicate confirmation/fill/accounting application.
    assert telemetry.get("duplicate_confirmation_advance") in (None, False, 0)
    assert telemetry.get("duplicate_fill_application") in (None, False, 0)


def test_08_g_negative_network_safety() -> None:
    boundary = prove_public_md_network_boundary_v1(environ={})
    assert boundary["ok"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert boundary["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert boundary["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert boundary["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert boundary["GET_ONLY_BOUND"] is True
    assert boundary["PUBLIC_MD_ONLY_BOUND"] is True


def test_09_h_parity() -> None:
    parity = prove_phase92_post_unlock_invocation_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGED"] is False
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True
    assert parity["INPUT_OUTPUT_PARITY_PROVEN"] is True
    assert parity["DECISION_REASON_PARITY_PROVEN"] is True
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True


def test_10_i_verifier_rejects_incomplete_manifest(tmp_path: Path) -> None:
    write_json_atomic_v1(
        tmp_path / "post_unlock_runtime_invocation_manifest_v1.json",
        {
            "ok": True,
            "session_id": TARGET_SESSION_ID,
            "canonical_runner_invoked": False,
            "canonical_runner_invocation_count": 0,
            "authorization_consumed": False,
            "authorization_consumed_exactly_once": False,
            "session_lock_acquired": False,
            "session_lock_released": False,
            "restart_recovery_completed": False,
            "reconciliation_before_alpha": False,
            "network_session_started": False,
            "claims": {"POST_UNLOCK_RUNTIME_INVOCATION_ADDED": True},
        },
    )
    verified = verify_post_unlock_invocation_manifest_v1(
        persistence_root=tmp_path, expected_ok=True
    )
    assert verified["ok"] is False
    assert verified["claims_match_telemetry"] is False


def test_11_execute_flag_required(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    _write_sgo(sgo, sha=sha, cfg=cfg)
    transport, _ = _transport()
    result = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=tmp_path,
        repository_sha=sha,
        config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        pre_envelope=_pre(sha, cfg),
        post_envelope_builder=_post_builder(sha),
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=False,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert "EXECUTE_MODE_REQUIRED" in result.blockers
    assert result.canonical_runner_invoked is False


def test_12_productive_session_remains_gate_only(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    now = float(time.time())
    _write_sgo(sgo, sha=sha, cfg=cfg, now=now)
    proc = subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT_CLI),
            "productive-session",
            "--session-go-file",
            str(sgo),
            "--owner-go",
            "--owner-session-go",
            "--authorization-present",
            "--confirm-token-present",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["productive_session_execution_permitted"] is True
    assert payload["session_started"] is False
    assert payload["authorization_consumed"] is False
    assert payload["network_request_count"] == 0
    assert "PRODUCTIVE_SESSION_COMMAND_IS_GATE_EVALUATION_ONLY" in payload["notes"]


def test_13_execute_post_unlock_cli(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "session_go.json"
    now = float(time.time())
    _write_sgo(sgo, sha=sha, cfg=cfg, now=now)
    persistence = tmp_path / "persist"
    proc = subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT_CLI),
            "execute-post-unlock",
            "--execute",
            "--persistence-root",
            str(persistence),
            "--session-go-file",
            str(sgo),
            "--owner-go",
            "--owner-session-go",
            "--confirm-token-present",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["canonical_runner_invoked"] is True
    assert payload["authorization_consumed_exactly_once"] is True
    assert payload["network_session_started"] is False


def test_14_session_go_issue_cli(tmp_path: Path) -> None:
    out = tmp_path / "issued_session_go.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SESSION_GO_CLI),
            "issue",
            "--output",
            str(out),
            "--expected-repository-sha",
            _sha(),
            "--expires-in-seconds",
            "600",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert out.is_file()
    artifact = json.loads(out.read_text(encoding="utf-8"))
    assert artifact["activation_status"] == ACTIVATION_STATUS_ACTIVE
    assert artifact["expected_repository_sha"] == _sha()
    assert "confirm_token" not in artifact


def test_15_failure_injection_batch(tmp_path: Path) -> None:
    report = run_post_unlock_failure_injection_v1(
        work_root=tmp_path,
        repository_sha=_sha(),
        config_digest=_cfg(),
        now_unix=NOW,
        repo_root=REPO_ROOT,
    )
    assert report["ok"] is True


def test_16_real_network_flag_rejected_by_cli(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT_CLI),
            "execute-post-unlock",
            "--execute",
            "--real-network",
            "--persistence-root",
            str(tmp_path),
            "--session-go-file",
            str(tmp_path / "x.json"),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert "REAL_NETWORK_FORBIDDEN_IN_POST_UNLOCK_CAPABILITY_DEFAULT" in payload["blockers"]
