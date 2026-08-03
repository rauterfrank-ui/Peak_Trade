"""Tests for PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.checkpoint_bridge_v1 import (
    CheckpointBridgeError,
    build_checkpoint_from_public_md_observations_v1,
    checkpoint_digest_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
    DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
    EXIT_CODE_82_CLASSIFICATION,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    RESTART_CAMPAIGN_ID,
    SEGMENT_COUNT,
    SEGMENT_PLAN,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.evidence_v1 import (
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.failure_injection_v1 import (
    run_failure_injection_matrix_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.fake_public_md_v1 import (
    build_fake_ticker_fetcher_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.orchestrator_v1 import (
    reject_productive_session_start_v1,
    run_offline_productive_restart_orchestration_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.parity_v1 import (
    prove_phase92_productive_entrypoint_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    SegmentAuthorizationError,
    build_segment_authorization_envelope_v1,
    load_confirm_token_secure_v1,
    validate_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (
    verify_restart_bundle_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py"
)
NOW = 1_700_000_000.0


class _Clock:
    def __init__(self, start: float = NOW) -> None:
        self._t = float(start)

    def time(self) -> float:
        return self._t

    def sleep(self, seconds: float) -> None:
        self._t += float(seconds)


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _pre(auth: str = "auth_pre_1"):
    return build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=_sha(),
        config_digest=_cfg(),
        authorization_id=auth,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=NOW + 3600,
        max_segment_duration_seconds=DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )


def _post_builder_factory(auth: str = "auth_post_1"):
    def _builder(**kwargs):
        return build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=_sha(),
            config_digest=kwargs["config_digest"],
            authorization_id=auth,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=NOW + 3600,
            max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
        )

    return _builder


def _transport(clock: _Clock | None = None):
    c = clock or _Clock()
    calls: list[tuple[str, str]] = []
    transport = EeaPublicMdTransportV1(
        fetcher=build_fake_ticker_fetcher_v1(calls=calls, clock=c),
        sleep=c.sleep,
        environ={},
    )
    return transport, calls


def test_01_entrypoint_importable_and_cli_preflight() -> None:
    import src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1 as mod

    assert mod.CAPABILITY_ID.endswith("NETWORK_ENTRYPOINT_V1")
    assert list(mod.SEGMENT_PLAN) == ["PRE_RESTART", "POST_RESTART"]
    proc = subprocess.run(
        [sys.executable, str(CLI), "preflight"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["segment_plan"] == ["PRE_RESTART", "POST_RESTART"]
    assert payload["controlled_restart_exit_code"] == 82


def test_02_segment_plan_exact() -> None:
    assert SEGMENT_PLAN == (SEGMENT_ROLE_PRE, SEGMENT_ROLE_POST)
    assert SEGMENT_COUNT == 2


def test_03_pre_authorization_bound() -> None:
    env = _pre()
    validated = validate_segment_authorization_envelope_v1(
        env.to_dict(),
        expected_segment_role=SEGMENT_ROLE_PRE,
        expected_session_id=TARGET_SESSION_ID,
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        now_unix=NOW,
    )
    assert validated.authorization_id.startswith("auth_pre")
    assert validated.predecessor_checkpoint_digest is None
    assert validated.single_use is True


def test_04_to_08_auth_rejections() -> None:
    env = _pre("auth_reject").to_dict()
    with pytest.raises(SegmentAuthorizationError, match="fixture"):
        build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            repository_sha=_sha(),
            config_digest=_cfg(),
            authorization_id="fx",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id="rt",
            expires_at=NOW + 10,
            max_segment_duration_seconds=60,
            expected_successor_state="X",
            fixture=True,
            productive=False,
        )
    with pytest.raises(SegmentAuthorizationError, match="authorization_already_consumed"):
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
            now_unix=NOW,
            consumed_authorization_ids={"auth_reject"},
        )
    with pytest.raises(SegmentAuthorizationError, match="authorization_revoked"):
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
            now_unix=NOW,
            revoked_authorization_ids={"auth_reject"},
        )
    with pytest.raises(SegmentAuthorizationError, match="repository_sha_mismatch"):
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha="0" * 40,
            expected_config_digest=_cfg(),
            now_unix=NOW,
        )
    with pytest.raises(SegmentAuthorizationError, match="config_digest_mismatch"):
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=_sha(),
            expected_config_digest="1" * 64,
            now_unix=NOW,
        )
    with pytest.raises(SegmentAuthorizationError, match="segment_role_mismatch"):
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_POST,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
            expected_predecessor_checkpoint_digest="a" * 64,
            now_unix=NOW,
        )
    with pytest.raises(SegmentAuthorizationError, match="session_id_mismatch"):
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id="other",
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
            now_unix=NOW,
        )


def test_12_13_offline_integration_checkpoint_and_exit_82(tmp_path: Path) -> None:
    transport, calls = _transport()
    result = run_offline_productive_restart_orchestration_v1(
        persistence_root=tmp_path / "camp",
        repository_sha=_sha(),
        pre_envelope=_pre("auth_pre_camp"),
        post_envelope_builder=_post_builder_factory("auth_post_camp"),
        transport=transport,
        now_unix=NOW,
        repo_root=REPO_ROOT,
        applied_confirmation_ids=["conf_1"],
        candidate_observation_id="conf_1",
    )
    assert result.ok is True
    assert result.controlled_restart_exit_code == CONTROLLED_RESTART_EXIT_CODE
    assert result.pre is not None
    assert result.pre.checkpoint_digest
    assert EXIT_CODE_82_CLASSIFICATION == "CONTROLLED_SEGMENT_TRANSITION"
    assert all(m == "GET" for m, _u in calls)
    assert len(calls) >= MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS
    assert result.network_session_started is False
    assert result.real_authorization_issued is False


def test_14_16_post_checkpoint_binding(tmp_path: Path) -> None:
    with pytest.raises(SegmentAuthorizationError, match="predecessor_checkpoint"):
        build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=_sha(),
            config_digest=_cfg(),
            authorization_id="auth_post_missing",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=NOW + 10,
            max_segment_duration_seconds=60,
            expected_successor_state="X",
            predecessor_checkpoint_digest=None,
        )
    post = build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_POST,
        segment_id=SEGMENT_POST_ID,
        repository_sha=_sha(),
        config_digest=_cfg(),
        authorization_id="auth_post_wrong",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:post",
        expires_at=NOW + 10,
        max_segment_duration_seconds=60,
        expected_successor_state="X",
        predecessor_checkpoint_digest="b" * 64,
    ).to_dict()
    with pytest.raises(SegmentAuthorizationError, match="predecessor_checkpoint_digest_mismatch"):
        validate_segment_authorization_envelope_v1(
            post,
            expected_segment_role=SEGMENT_ROLE_POST,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
            expected_predecessor_checkpoint_digest="c" * 64,
            now_unix=NOW,
        )


def test_17_24_recovery_invariants(tmp_path: Path) -> None:
    transport, _calls = _transport()
    result = run_offline_productive_restart_orchestration_v1(
        persistence_root=tmp_path / "rec",
        repository_sha=_sha(),
        pre_envelope=_pre("auth_pre_rec"),
        post_envelope_builder=_post_builder_factory("auth_post_rec"),
        transport=transport,
        now_unix=NOW,
        repo_root=REPO_ROOT,
        open_position_present=True,
        applied_fill_ids=["fill_natural_1"],
        applied_confirmation_ids=["conf_natural_1"],
        candidate_observation_id="conf_natural_1",
        candidate_fill_id="fill_natural_1",
    )
    assert result.ok is True
    assert result.post is not None
    assert result.post.reconciliation_before_alpha is True
    tel = result.post.telemetry
    assert tel["confirmation_session_id_before"] == tel["confirmation_session_id_after"]
    assert tel["duplicate_confirmation_prevented_count"] == 1
    assert tel["duplicate_fill_prevented_count"] == 1
    assert tel["portfolio_digest_before"] == tel["portfolio_digest_after"]
    assert tel["scope_digest_before"] == tel["scope_digest_after"]
    assert tel["accounting_digest_before"] == tel["accounting_digest_after"]
    # Idempotent evidence recovery: re-verify same bundle.
    v1 = verify_restart_bundle_v1(persistence_root=tmp_path / "rec")
    v2 = verify_restart_bundle_v1(persistence_root=tmp_path / "rec")
    assert v1.verified is True and v2.verified is True
    assert v1.to_dict()["claims"] == v2.to_dict()["claims"]


def test_25_parallel_lock_and_26_29_network_boundary(tmp_path: Path) -> None:
    failures = run_failure_injection_matrix_v1(
        tmp_root=tmp_path / "fi",
        repository_sha=_sha(),
        repo_root=REPO_ROOT,
        now_unix=NOW,
    )
    assert failures["ok"] is True
    assert failures["parallel_lock_rejected"] is True
    boundary = prove_public_md_network_boundary_v1(environ={})
    assert boundary["ok"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert boundary["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert boundary["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert boundary["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert boundary["GET_ONLY_BOUND"] is True


def test_30_confirm_token_secure_path_and_no_plaintext_in_evidence(tmp_path: Path) -> None:
    token_path = tmp_path / "tok.txt"
    token_path.write_text(
        "GO_PSO_SESSION_PREREG_V1_testtokenvalue_not_for_logs\n", encoding="utf-8"
    )
    loaded = load_confirm_token_secure_v1(
        confirm_token_file=token_path, env_token="", stdin_token=""
    )
    assert loaded.startswith("GO_PSO_SESSION_PREREG_V1_")
    with pytest.raises(SegmentAuthorizationError, match="dual_source"):
        load_confirm_token_secure_v1(
            confirm_token_file=token_path, env_token="GO_PSO_SESSION_PREREG_V1_x", stdin_token=""
        )
    summary = materialize_capability_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "ev",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    blob = "\n".join(p.read_text(encoding="utf-8") for p in (tmp_path / "ev").rglob("*.json"))
    assert "GO_PSO_SESSION_PREREG_V1_testtokenvalue_not_for_logs" not in blob
    assert summary["claims"]["CONFIRM_TOKEN_PLAINTEXT_EXPOSED"] is False


def test_31_33_offline_integration_cli_and_verifier(tmp_path: Path) -> None:
    persistence = tmp_path / "cli_camp"
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "offline-integration",
            "--persistence-root",
            str(persistence),
            "--expected-repository-sha",
            _sha(),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    # Exit 82 is the controlled segment transition classification for a complete campaign
    # that includes PRE controlled restart.
    assert proc.returncode in {0, CONTROLLED_RESTART_EXIT_CODE}, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["fake_md_methods"] == ["GET"]
    verified = verify_restart_bundle_v1(persistence_root=persistence)
    assert verified.verified is True
    # Incomplete bundle rejected.
    bad = tmp_path / "bad"
    bad.mkdir()
    incomplete = verify_restart_bundle_v1(persistence_root=bad)
    assert incomplete.verified is False


def test_34_parity() -> None:
    parity = prove_phase92_productive_entrypoint_parity_v1()
    assert parity["ok"] is True
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True
    assert parity["STATE_TRANSITION_PARITY_PROVEN"] is True
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["CORE_LOGIC_CHANGED"] is False


def test_productive_session_command_fail_closed() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "productive-session", "--real-network"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["network_session_started"] is False
    gate = reject_productive_session_start_v1(use_real_network=True, environ={})
    assert gate["ok"] is False


def test_checkpoint_bridge_insufficient_observations() -> None:
    with pytest.raises(CheckpointBridgeError, match="insufficient"):
        build_checkpoint_from_public_md_observations_v1(
            distinct_observation_count=1,
            observation_identities=["a"],
        )


def test_instrument_identity_stable_in_checkpoint() -> None:
    ids = [f"obs:{i}" for i in range(MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS)]
    cp = build_checkpoint_from_public_md_observations_v1(
        distinct_observation_count=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
        observation_identities=ids,
    )
    assert cp.selected_instrument_reference
    assert CANONICAL_INSTRUMENT_ID in json.dumps(cp.to_dict())
    assert len(checkpoint_digest_v1(cp)) == 64
