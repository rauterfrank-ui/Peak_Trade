"""Additional tests for DELEGATED_CURSOR_SECURE_CONFIRM Step-7 campaign path."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
    DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH,
    TARGET_CAMPAIGN_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.delegated_cursor_secure_confirm_broker_v1 import (
    DelegatedCursorSecureConfirmError,
    DelegatedCursorSecureConfirmLatchV1,
    mint_delegated_cursor_secure_confirm_latch_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.governed_campaign_execution_v1 import (
    execute_governed_step7_campaign_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CURSOR_OPERATOR = REPO_ROOT / DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH


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


def _fake_runner_factory(bucket: list):
    def _runner(**kwargs):
        bucket.append(dict(kwargs))
        return {"ok": True, "NETWORK_SESSION_STARTED": False, "synthetic": True}

    return _runner


def test_cursor_operator_entrypoint_present() -> None:
    assert CURSOR_OPERATOR.is_file()


def test_cursor_no_tty_success_path() -> None:
    calls: list = []
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    digest = latch.digest
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        getpass_fn=None,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is True
    assert len(calls) == 2
    assert result.claims["AUTHORIZATION_CHANNEL"] == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM
    assert result.claims["TOKEN_ROLE"] == CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH
    assert result.claims["REAL_TTY_VERIFIED"] is False
    assert result.claims["DELEGATED_SECURE_CONFIRM_VERIFIED"] is True
    assert result.claims["confirm_token_fingerprint"] == digest
    blob = json.dumps(result.to_dict(), sort_keys=True)
    assert digest in blob
    # plaintext must not appear (digest-only)
    assert "plaintext" not in blob.lower() or "[REDACTED]" in blob


def test_delegated_missing_owner_go() -> None:
    calls: list = []
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is False
    assert calls == []
    assert "OWNER_GO_REQUIRED" in result.blockers


def test_delegated_wrong_capability() -> None:
    calls: list = []
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        expected_capability_id="WRONG_CAPABILITY",
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is False
    assert calls == []
    assert "WRONG_CAPABILITY_ID" in result.blockers
    assert TARGET_CAMPAIGN_CAPABILITY_ID != "WRONG_CAPABILITY"


def test_delegated_dirty_worktree() -> None:
    calls: list = []
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=False,
    )
    assert result.ok is False
    assert calls == []
    assert "TRACKED_WORKTREE_DIRTY" in result.blockers


def test_token_replay_fail_closed() -> None:
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    _ = latch.consume_once_v1()
    try:
        latch.consume_once_v1()
        raised = False
    except DelegatedCursorSecureConfirmError as exc:
        raised = True
        assert "REPLAY" in str(exc)
    assert raised is True

    calls: list = []
    # already consumed latch must fail campaign
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is False
    assert calls == []
    assert "CONFIRM_TOKEN_REPLAY" in result.blockers or "CONFIRM_TOKEN_FAILURE" in result.blockers


def test_token_missing_fail_closed() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=None,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is False
    assert calls == []
    assert "CONFIRM_TOKEN_MISSING" in result.blockers or "CONFIRM_TOKEN_FAILURE" in result.blockers


def test_token_disclosure_guard_and_tempfile_cleanup(tmp_path: Path) -> None:
    latch2 = mint_delegated_cursor_secure_confirm_latch_v1()
    digest = latch2.digest
    path = latch2.write_tempfile_0600_v1(
        repository_root=REPO_ROOT,
        directory=tmp_path,
    )
    assert path.exists()
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    secret2 = path.read_text(encoding="utf-8").strip()
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch2,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is True
    assert result.claims["TEMP_SECRET_CLEANED"] is True
    assert not path.exists()
    blob = json.dumps(result.to_dict(), sort_keys=True)
    assert secret2 not in blob
    assert result.claims["CONFIRM_TOKEN_PLAINTEXT_EXPOSED"] is False
    assert result.claims["CONFIRM_TOKEN_PERSISTED"] is False
    assert result.claims["confirm_token_fingerprint"] == digest


def test_cleanup_after_failure(tmp_path: Path) -> None:
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    path = latch.write_tempfile_0600_v1(
        repository_root=REPO_ROOT,
        directory=tmp_path,
    )
    assert path.exists()
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=False,  # force failure after confirm acquire
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is False
    assert calls == []
    assert "OWNER_GO_REQUIRED" in result.blockers
    # tempfile must be cleaned even on gate failure after consume
    assert not path.exists()
    assert result.claims.get("TEMP_SECRET_CLEANED") is True


def test_real_tty_path_regression_still_works() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    )
    assert result.ok is True
    assert len(calls) == 2
    assert result.claims["AUTHORIZATION_CHANNEL"] == AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM
    assert result.claims["REAL_TTY_VERIFIED"] is True
    assert result.claims["DELEGATED_SECURE_CONFIRM_VERIFIED"] is False


def test_latch_repr_hides_secret() -> None:
    latch = DelegatedCursorSecureConfirmLatchV1.mint_v1()
    secret = latch.consume_once_v1()
    # remint for repr check before consume
    latch2 = DelegatedCursorSecureConfirmLatchV1.mint_v1()
    text = repr(latch2) + str(latch2)
    assert secret not in text
    assert "digest=" in text
    latch2.clear_v1()
