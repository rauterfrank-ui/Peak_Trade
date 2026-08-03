"""Owner tests + failure injection for CAPABILITY_O3."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import pytest

from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1 import (
    CAPABILITY_ID,
    FAMILY_PSO_GOVERNED_PUBLIC_MD,
    FAMILY_RESEARCH_S03,
    PURPOSE_PSO_WALLCLOCK_OBSERVE,
    PURPOSE_S03_ADDITIONAL_EVIDENCE,
    SecureEphemeralConfirmTokenHandleV1,
    acquire_and_verify_secure_handoff_v1,
    assert_dashboard_only_auth_boundary_v1,
    assert_no_argv_plaintext_token_v1,
    assert_no_governed_env_plaintext_v1,
    bind_plaintext_to_family_v1,
    cleanup_all_registered_token_files_v1,
    create_confirm_token_file_exclusive_v1,
    delete_confirm_token_file_v1,
    family_matrix_public_v1,
    inspect_secure_input_topology_v1,
    load_confirm_token_file_secure_v1,
    mint_noninteractive_handoff_v1,
    validate_family_matrix_complete_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    CrossFamilySubstitutionError,
    DashboardOnlyTokenForbiddenError,
    SecureConfirmTokenError,
    SecureInputChannelError,
    TokenFileSecurityError,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.handoff_v1 import (
    assert_hidden_input_unavailable_fails_closed_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.secure_input_v1 import (
    assert_control_stdin_not_used_as_secure_channel_v1,
    assert_single_secure_source_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.token_file_v1 import (
    ConfirmTokenFileLeaseV1,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONSUMER = "tests.ops.test_secure_confirm_token_family_and_hidden_input_handoff_v1"


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    # Token files must live outside repository + evidence roots.
    token_root = tmp_path / "token_home"
    token_root.mkdir(mode=0o700)
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    return REPO_ROOT, evidence_root, token_root


def test_family_matrix_complete() -> None:
    matrix = validate_family_matrix_complete_v1()
    assert matrix["token_family_matrix_complete"] is True
    assert matrix["cross_family_substitution_blocked"] is True
    public = family_matrix_public_v1()
    assert FAMILY_PSO_GOVERNED_PUBLIC_MD in public["families"]
    assert FAMILY_RESEARCH_S03 in public["families"]
    assert CAPABILITY_ID in public["capability_id"]


def test_noninteractive_ephemeral_handoff_and_no_plaintext_in_public() -> None:
    handle = mint_noninteractive_handoff_v1(
        family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
        purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
        session_id="sess-1",
        repository_sha="abc1234",
        consumer_id=CONSUMER,
    )
    pub = handle.public_dict_v1()
    blob = json.dumps(pub)
    assert "GO_PSO_SESSION_PREREG_V1_" not in blob
    assert "plaintext" not in blob.lower() or pub.get("plaintext_persisted") is False
    meta = handle.metadata
    result = acquire_and_verify_secure_handoff_v1(
        family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
        purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
        session_id="sess-1",
        repository_sha="abc1234",
        consumer_id=CONSUMER,
        expected_metadata=meta.to_public_dict(),
        ephemeral_handle=handle,
    )
    assert result.ok is True
    assert result.plaintext_exposed is False
    assert "GO_PSO" not in json.dumps(result.to_public_dict())
    with pytest.raises(SecureConfirmTokenError):
        handle.borrow_plaintext_once_v1()


def test_cross_family_pso_vs_s03_blocked_despite_shared_prefix() -> None:
    pso = SecureEphemeralConfirmTokenHandleV1.mint_pso_v1(
        session_id="s",
        repository_sha="deadbeef",
        consumer_id=CONSUMER,
    )
    # Same plaintext body format cannot verify under S03 family metadata.
    with pytest.raises((CrossFamilySubstitutionError, SecureConfirmTokenError)):
        acquire_and_verify_secure_handoff_v1(
            family_id=FAMILY_RESEARCH_S03,
            purpose=PURPOSE_S03_ADDITIONAL_EVIDENCE,
            session_id="s",
            repository_sha="deadbeef",
            consumer_id=CONSUMER,
            expected_metadata={
                **pso.metadata.to_public_dict(),
                "family_id": FAMILY_RESEARCH_S03,
                "purpose": PURPOSE_S03_ADDITIONAL_EVIDENCE,
            },
            ephemeral_handle=pso,
        )


def test_wrong_purpose_rejected() -> None:
    handle = SecureEphemeralConfirmTokenHandleV1.mint_pso_v1(
        session_id="s2",
        repository_sha="sha2",
        consumer_id=CONSUMER,
    )
    with pytest.raises(SecureConfirmTokenError):
        bind_plaintext_to_family_v1(
            confirm_token=handle.borrow_plaintext_once_v1(),
            family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
            purpose=PURPOSE_S03_ADDITIONAL_EVIDENCE,
            session_id="s2",
            repository_sha="sha2",
            consumer_id=CONSUMER,
        )


def test_token_replay_rejected() -> None:
    handle = SecureEphemeralConfirmTokenHandleV1.mint_pso_v1(
        session_id="s3",
        repository_sha="sha3",
        consumer_id=CONSUMER,
    )
    meta = handle.metadata.to_public_dict()
    acquire_and_verify_secure_handoff_v1(
        family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
        purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
        session_id="s3",
        repository_sha="sha3",
        consumer_id=CONSUMER,
        expected_metadata=meta,
        ephemeral_handle=handle,
    )
    # New handle with same fingerprint in seen set.
    handle2 = SecureEphemeralConfirmTokenHandleV1.mint_pso_v1(
        session_id="s3",
        repository_sha="sha3",
        consumer_id=CONSUMER,
    )
    # Force replay by verifying against previously seen fingerprint of handle2 itself twice.
    fp = handle2.metadata.token_fingerprint
    plain = handle2.borrow_plaintext_once_v1()
    from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.family_binding_v1 import (
        verify_family_bound_token_v1,
    )

    with pytest.raises(SecureConfirmTokenError, match="REPLAY"):
        verify_family_bound_token_v1(
            confirm_token=plain,
            expected=handle2.metadata.to_public_dict(),
            family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
            purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
            session_id="s3",
            repository_sha="sha3",
            consumer_id=CONSUMER,
            previously_seen_fingerprints=frozenset({fp}),
        )


def test_token_file_exclusive_mode_owner_and_cleanup(tmp_path: Path) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    token_path = token_home / "tok"
    handle = SecureEphemeralConfirmTokenHandleV1.mint_pso_v1(
        session_id="sf",
        repository_sha="sha",
        consumer_id=CONSUMER,
    )
    plain = handle.borrow_plaintext_once_v1()
    created = create_confirm_token_file_exclusive_v1(
        path=token_path,
        token=plain,
        repository_root=repo,
        evidence_root=evidence,
    )
    plain = ""
    assert created.exists()
    assert stat.S_IMODE(created.stat().st_mode) == 0o600
    assert stat.S_IMODE(created.parent.stat().st_mode) == 0o700
    loaded = load_confirm_token_file_secure_v1(
        path=created, repository_root=repo, evidence_root=evidence
    )
    assert loaded.startswith("GO_PSO_SESSION_PREREG_V1_")
    assert delete_confirm_token_file_v1(created) is True
    assert not created.exists()


def test_token_file_existing_target_rejected(tmp_path: Path) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    path = token_home / "exists"
    path.write_text("x\n", encoding="utf-8")
    with pytest.raises(TokenFileSecurityError, match="EXISTING_TARGET"):
        create_confirm_token_file_exclusive_v1(
            path=path,
            token="GO_PSO_SESSION_PREREG_V1_" + ("a" * 40),
            repository_root=repo,
            evidence_root=evidence,
        )


def test_token_file_symlink_rejected(tmp_path: Path) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    real = token_home / "real"
    real.write_text("GO_PSO_SESSION_PREREG_V1_" + ("b" * 40) + "\n", encoding="utf-8")
    os.chmod(real, 0o600)
    link = token_home / "link"
    link.symlink_to(real)
    with pytest.raises(TokenFileSecurityError, match="SYMLINK"):
        load_confirm_token_file_secure_v1(path=link, repository_root=repo, evidence_root=evidence)


def test_token_path_inside_repository_rejected(tmp_path: Path) -> None:
    repo, evidence, _token_home = _roots(tmp_path)
    inside = repo / "src" / "_o3_should_not_write_token"
    with pytest.raises(TokenFileSecurityError, match="INSIDE_REPOSITORY"):
        create_confirm_token_file_exclusive_v1(
            path=inside,
            token="GO_PSO_SESSION_PREREG_V1_" + ("c" * 40),
            repository_root=repo,
            evidence_root=evidence,
            register_cleanup=False,
        )


def test_token_path_inside_evidence_rejected(tmp_path: Path) -> None:
    repo, evidence, _token_home = _roots(tmp_path)
    inside = evidence / "tok"
    with pytest.raises(TokenFileSecurityError, match="INSIDE_EVIDENCE"):
        create_confirm_token_file_exclusive_v1(
            path=inside,
            token="GO_PSO_SESSION_PREREG_V1_" + ("d" * 40),
            repository_root=repo,
            evidence_root=evidence,
            register_cleanup=False,
        )


def test_wrong_owner_uid_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    path = token_home / "uid"
    create_confirm_token_file_exclusive_v1(
        path=path,
        token="GO_PSO_SESSION_PREREG_V1_" + ("e" * 40),
        repository_root=repo,
        evidence_root=evidence,
        register_cleanup=False,
    )
    real_uid = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: real_uid + 1)
    with pytest.raises(TokenFileSecurityError, match="OWNER_UID"):
        load_confirm_token_file_secure_v1(path=path, repository_root=repo, evidence_root=evidence)


def test_non_regular_file_rejected(tmp_path: Path) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    fifo = token_home / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(TokenFileSecurityError):
        load_confirm_token_file_secure_v1(path=fifo, repository_root=repo, evidence_root=evidence)


def test_cleanup_after_success_and_failure(tmp_path: Path) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    path = token_home / "lease"
    token = "GO_PSO_SESSION_PREREG_V1_" + ("f" * 40)
    with ConfirmTokenFileLeaseV1(
        path=path, token=token, repository_root=repo, evidence_root=evidence
    ) as leased:
        assert leased.exists()
    assert not path.exists()

    path2 = token_home / "lease2"
    try:
        with ConfirmTokenFileLeaseV1(
            path=path2, token=token, repository_root=repo, evidence_root=evidence
        ):
            raise RuntimeError("controlled_failure")
    except RuntimeError:
        pass
    assert not path2.exists()


def test_cleanup_after_simulated_signal(tmp_path: Path) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    path = token_home / "sig"
    create_confirm_token_file_exclusive_v1(
        path=path,
        token="GO_PSO_SESSION_PREREG_V1_" + ("g" * 40),
        repository_root=repo,
        evidence_root=evidence,
        register_cleanup=True,
    )
    assert path.exists()
    cleanup_all_registered_token_files_v1()
    assert not path.exists()


def test_dual_source_env_file_and_file_stdin_rejected() -> None:
    with pytest.raises(SecureInputChannelError, match="DUAL_SOURCE|ENVIRONMENT"):
        assert_single_secure_source_v1(
            has_ephemeral_handle=False,
            has_token_file=True,
            has_env_plaintext=True,
            has_stdin_plaintext=False,
            has_argv_plaintext=False,
        )
    with pytest.raises(SecureInputChannelError, match="DUAL_SOURCE|STDIN|COLLISION"):
        # stdin plaintext is rejected at single-source and control-stdin guards
        try:
            assert_single_secure_source_v1(
                has_ephemeral_handle=False,
                has_token_file=True,
                has_env_plaintext=False,
                has_stdin_plaintext=True,
                has_argv_plaintext=False,
            )
        except SecureInputChannelError:
            raise
    topology = inspect_secure_input_topology_v1()
    with pytest.raises(SecureInputChannelError, match="STDIN_COLLISION"):
        assert_control_stdin_not_used_as_secure_channel_v1(
            topology=topology, attempting_stdin_token=True
        )


def test_pipe_and_heredoc_collision_and_hidden_unavailable() -> None:
    class _Pipe:
        def isatty(self) -> bool:
            return False

    topo = inspect_secure_input_topology_v1(stdin_stream=_Pipe())
    assert topo.control_stdin_is_tty is False
    assert "PIPE_OR_HEREDOC" in ",".join(topo.notes)
    with pytest.raises(SecureInputChannelError, match="STDIN_COLLISION"):
        assert_control_stdin_not_used_as_secure_channel_v1(
            topology=topo, attempting_stdin_token=True
        )
    assert_hidden_input_unavailable_fails_closed_v1()


def test_argv_and_governed_env_plaintext_rejected() -> None:
    with pytest.raises(SecureInputChannelError, match="ARGV"):
        assert_no_argv_plaintext_token_v1(["--confirm-token", "GO_PSO_SESSION_PREREG_V1_xxx"])
    with pytest.raises(SecureInputChannelError, match="ENVIRONMENT"):
        assert_no_governed_env_plaintext_v1(
            {"PEAK_TRADE_PSO_WALLCLOCK_CONFIRM_TOKEN": "GO_PSO_SESSION_PREREG_V1_xxx"}
        )


def test_dashboard_only_mint_and_consume_forbidden() -> None:
    env = {
        "PEAK_TRADE_CONFIRM_TOKEN_FILE": "/tmp/unused_confirm_token_o3_test",
    }
    ok = assert_dashboard_only_auth_boundary_v1(
        mode="dashboard-only",
        parent_environ=env,
        mint_requested=False,
        consume_requested=False,
    )
    assert ok["confirm_token_minted"] is False
    with pytest.raises(DashboardOnlyTokenForbiddenError):
        assert_dashboard_only_auth_boundary_v1(
            mode="dashboard-only",
            parent_environ=env,
            mint_requested=True,
            consume_requested=False,
        )
    with pytest.raises(DashboardOnlyTokenForbiddenError):
        assert_dashboard_only_auth_boundary_v1(
            mode="dashboard-only",
            parent_environ=env,
            mint_requested=False,
            consume_requested=True,
        )


def test_o2_start_passes_auth_validated_without_mint(tmp_path: Path) -> None:
    from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
        CanonicalLocalLauncherV1,
        LauncherPathsV1,
    )

    state = tmp_path / "state"
    logs = tmp_path / "logs"
    evidence = tmp_path / "evidence"
    cfg = tmp_path / "cfg.toml"
    cfg.write_text("[o2]\nmode='dashboard-only'\n", encoding="utf-8")
    launcher = CanonicalLocalLauncherV1(
        LauncherPathsV1(
            repository_root=REPO_ROOT,
            state_root=state,
            log_root=logs,
            evidence_root=evidence,
        )
    )
    started = launcher.start(
        mode="dashboard-only",
        config_path=cfg,
        session_id="o3-dash",
        repository_sha="deadbeef" * 5,
    )
    assert started["ok"] is True
    session = started["session"]
    assert session["lifecycle_state"] == "RUNNING"
    assert session["safety_invariants"]["CONFIRM_TOKEN_MINTED"] is False
    # Transitions should include AUTH_VALIDATED
    transitions = (
        state / "canonical_local_launcher_v1" / "sessions" / "o3-dash" / "transitions.jsonl"
    )
    text = transitions.read_text(encoding="utf-8")
    assert "AUTH_VALIDATED" in text
    assert "O3_DASHBOARD_ONLY_NO_TOKEN" in text
    launcher.stop("o3-dash")


def test_file_handoff_verify_and_cleanup(tmp_path: Path) -> None:
    repo, evidence, token_home = _roots(tmp_path)
    handle = SecureEphemeralConfirmTokenHandleV1.mint_pso_v1(
        session_id="fh",
        repository_sha="sha-fh",
        consumer_id=CONSUMER,
    )
    meta = handle.metadata.to_public_dict()
    path = token_home / "handoff"
    plain = handle.borrow_plaintext_once_v1()
    create_confirm_token_file_exclusive_v1(
        path=path,
        token=plain,
        repository_root=repo,
        evidence_root=evidence,
        register_cleanup=False,
    )
    plain = ""
    # New handle already consumed; pass file only.
    result = acquire_and_verify_secure_handoff_v1(
        family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
        purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
        session_id="fh",
        repository_sha="sha-fh",
        consumer_id=CONSUMER,
        expected_metadata=meta,
        token_file=path,
        repository_root=repo,
        evidence_root=evidence,
        cleanup_token_file=True,
    )
    assert result.ok is True
    assert not path.exists()
