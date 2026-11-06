"""Tests for Step-3 governed restart/recovery session execution surface.

No real DNS/socket/HTTP. No productive auth/token issuance.
Ephemeral offline segment ledgers under tmp only.
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
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartSegmentLockV1,
    lock_path_for_root_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    RUNTIME_CAPABILITY_ID,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.evidence_v1 import (
    build_session_manifest_template_v1,
    materialize_implementation_evidence_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.failure_injection_v1 import (
    run_step3_surface_failure_injection_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.gates_v1 import (
    evaluate_step3_execution_gates_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.governed_execution_surface_v1 import (
    assemble_execution_request_v1,
    execute_offline_step3_campaign_v1,
    prove_step3_execution_surface_implementation_v1,
    request_real_network_fail_closed_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.network_boundary_v1 import (
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.offline_campaign_v1 import (
    run_offline_restart_recovery_campaign_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.pacing_policy_v1 import (
    prove_bounded_pacing_and_backoff_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH
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
        session_go_id="sgo_step3_surface_test_v1",
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
    write_json_atomic_v1(path, authority.to_dict())


def test_permanent_constants_remain_false() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert REAL_NETWORK_REQUESTS_ALLOWED is False
    assert AUTHORIZATION_CONSUMPTION_ALLOWED is False
    assert CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False
    assert SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False


def test_prove_implementation_and_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    proof = prove_step3_execution_surface_implementation_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        repo_root=REPO_ROOT,
    )
    assert proof.ok is True
    assert proof.claims["STEP3_PRODUCTIVE_ENTRYPOINT_FOUND"] is True
    assert proof.claims["NETWORK_SESSION_STARTED"] is False
    assert proof.claims["CORE_LOGIC_CHANGED"] is False
    assert proof.claims["CALL_ORDER_PARITY_PROVEN"] is True
    boundary = prove_public_md_get_only_boundary_v1()
    assert boundary["ok"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHABLE"] is False
    pacing = prove_bounded_pacing_and_backoff_v1()
    assert pacing["ok"] is True
    assert pacing["claims"]["ZERO_INTERVAL_RETRY_BURST"] is False


def test_gate_negatives() -> None:
    sha, cfg = _sha(), _cfg()
    assert (
        "OWNER_GO_REQUIRED"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=False,
            operator_authorization_explicit=True,
            network_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=True,
        )["blockers"]
    )
    assert (
        "OPERATOR_AUTHORIZATION_REQUIRED"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=False,
            network_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=True,
        )["blockers"]
    )
    assert (
        "NETWORK_SESSION_GO_REQUIRED"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=False,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=True,
        )["blockers"]
    )
    assert (
        "AUTHORIZATION_REQUIRED"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            session_go_path=None,
            authorization_present=False,
            confirm_token_present=True,
        )["blockers"]
    )
    assert (
        "CONFIRM_TOKEN_HANDOFF_REQUIRED"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=False,
        )["blockers"]
    )
    assert (
        "AUTHORIZATION_SHA_MISMATCH"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=True,
            authorization_artifact={
                "expected_repository_sha": "0" * 40,
                "expected_config_digest": cfg,
                "session_id": TARGET_SESSION_ID,
                "capability_id": CAPABILITY_ID,
            },
        )["blockers"]
    )
    assert (
        "AUTHORIZATION_CONFIG_DIGEST_MISMATCH"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=True,
            authorization_artifact={
                "expected_repository_sha": sha,
                "expected_config_digest": "f" * 64,
                "session_id": TARGET_SESSION_ID,
                "capability_id": CAPABILITY_ID,
            },
        )["blockers"]
    )
    assert (
        "INSTRUMENT_SCOPE_MISMATCH"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=True,
            authorization_artifact={
                "expected_repository_sha": sha,
                "expected_config_digest": cfg,
                "session_id": TARGET_SESSION_ID,
                "instrument_identity": "WRONG",
                "capability_id": CAPABILITY_ID,
            },
        )["blockers"]
    )
    assert (
        "CAPABILITY_SCOPE_MISMATCH"
        in evaluate_step3_execution_gates_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=NOW,
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present=True,
            expected_capability_id="WRONG_CAPABILITY",
        )["blockers"]
    )


def test_confirm_token_argv_and_env_rejected() -> None:
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in reject_confirm_token_argv_v1(
        ["execute-offline-campaign", "--confirm-token", "x"]
    )
    assert "CONFIRM_TOKEN_ENV_FALLBACK_FORBIDDEN" in reject_confirm_token_env_fallback_v1(
        {"PEAK_TRADE_PSO_CONFIRM_TOKEN": "secret"}
    )


def test_request_real_network_fail_closed() -> None:
    result = request_real_network_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert result.ok is False
    assert "REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION" in result.blockers


def test_offline_pre_post_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    campaign = run_offline_restart_recovery_campaign_v1(
        persistence_root=tmp_path / "camp",
        repository_sha=sha,
        config_digest=cfg,
        session_go_path=sgo,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        applied_confirmation_ids=["conf_001"],
        applied_fill_ids=["fill_001"],
        open_position_present=False,
        candidate_observation_id="conf_001",
        candidate_fill_id="fill_001",
        repo_root=REPO_ROOT,
    )
    assert campaign.ok is True
    assert campaign.claims["CONTROLLED_RESTART_OCCURRED"] is True
    assert campaign.claims["RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART"] is True
    assert campaign.claims["NO_DUPLICATE_CONFIRMATION_ADVANCE"] is True
    assert campaign.claims["NO_DUPLICATE_FILL"] is True
    assert campaign.network_session_started is False
    assert campaign.bundle_verify is not None
    assert campaign.bundle_verify.get("verified") is True


def test_offline_campaign_via_governed_execute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    result = execute_offline_step3_campaign_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        persistence_root=tmp_path / "camp2",
        session_go_path=sgo,
        now_unix=NOW,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_present=True,
        confirm_token_present=True,
        authorization_artifact={
            "expected_repository_sha": sha,
            "expected_config_digest": cfg,
            "session_id": TARGET_SESSION_ID,
            "capability_id": RUNTIME_CAPABILITY_ID,
            "instrument_identity": "ETH-USD_UM_XPERP-310404",
        },
        execute=True,
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert result.network_session_started is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False


def test_writer_conflict_orphan_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    root = tmp_path / "orphan"
    root.mkdir()
    lock = RestartSegmentLockV1(
        lock_path=lock_path_for_root_v1(root),
        runtime_session_id="foreign",
        owner="foreign",
    )
    lock.acquire()
    campaign = run_offline_restart_recovery_campaign_v1(
        persistence_root=root,
        repository_sha=sha,
        config_digest=cfg,
        session_go_path=sgo,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        repo_root=REPO_ROOT,
    )
    assert campaign.ok is False


def test_manifest_verifier_and_step5_relabel_rejected() -> None:
    good = build_session_manifest_template_v1(
        claims={
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CORE_LOGIC_CHANGED": False,
            "REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED": False,
            "RESTART_RECOVERY_LADDER_STEP_CLOSED": False,
        }
    )
    assert verify_session_manifest_v1(good)["ok"] is True

    bad = dict(good)
    bad["manifest_digest"] = "0" * 64
    assert verify_session_manifest_v1(bad)["ok"] is False

    overclaim = build_session_manifest_template_v1(
        claims={
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CORE_LOGIC_CHANGED": False,
            "REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED": True,
            "RESTART_RECOVERY_LADDER_STEP_CLOSED": False,
        }
    )
    assert verify_session_manifest_v1(overclaim)["ok"] is False

    relabel = dict(good)
    relabel["capability_id"] = (
        "PHASE_9_2_STEP_5_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
        "PROLONGED_NATURAL_MARKET_SESSION_EXECUTION_CAPABILITY_V1"
    )
    relabel.pop("manifest_digest", None)
    relabel["manifest_digest"] = sha256_canonical_v1(relabel)
    assert verify_session_manifest_v1(relabel)["ok"] is False


def test_assemble_request_and_materialize_and_failure_injection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _block_network(monkeypatch)
    sha, cfg = _sha(), _cfg()
    req = assemble_execution_request_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        repo_root=REPO_ROOT,
    )
    assert req["ok"] is True
    assert req["network_session_started"] is False

    fi = run_step3_surface_failure_injection_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        repo_root=REPO_ROOT,
        persistence_root=tmp_path / "fi",
    )
    assert fi["ok"] is True

    summary = materialize_implementation_evidence_v1(
        repository_sha=sha,
        evidence_root=tmp_path / "ev",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["network_session_started"] is False
    assert (tmp_path / "ev" / "SUMMARY.json").is_file()


def test_cli_preflight_and_request_real_network(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    proc = subprocess.run(
        [sys.executable, str(CLI), "preflight"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["capability_id"] == CAPABILITY_ID

    proc2 = subprocess.run(
        [sys.executable, str(CLI), "request-real-network"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc2.returncode != 0
    assert "REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION" in proc2.stdout

    proc3 = subprocess.run(
        [sys.executable, str(CLI), "preflight", "--confirm-token", "plaintext"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc3.returncode != 0
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in proc3.stdout
