"""Tests for CAPABILITY_O8_CANONICAL_RUNTIME_OPERATIONS_ACTIVATION_V1."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.ops.canonical_local_launcher_and_process_supervision_v1.cli_v1 import (
    build_parser,
    dispatch,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    MODE_DASHBOARD_ONLY,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    CanonicalLauncherError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
    CanonicalLocalLauncherV1,
    LauncherPathsV1,
)
from src.ops.canonical_runtime_operations_activation_v1.constants_v1 import (
    ACTIVATION_CONTRACT_RELATIVE_PATH,
    CANONICAL_OPERATOR_ENTRYPOINT,
    CANONICAL_SUBCOMMANDS,
    CAPABILITY_ID as O8_CAPABILITY_ID,
)
from src.ops.canonical_runtime_operations_activation_v1.contract_v1 import (
    ActivationContractError,
    default_activation_contract_path,
    load_activation_contract_v1,
    validate_activation_contract_v1,
)


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def launcher_env(tmp_path: Path, repo_root: Path) -> tuple[CanonicalLocalLauncherV1, Path]:
    state_root = tmp_path / "state"
    log_root = tmp_path / "logs"
    evidence_root = tmp_path / "evidence"
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps({"mode": "dashboard-only", "o8": True}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths = LauncherPathsV1(
        repository_root=repo_root,
        state_root=state_root,
        log_root=log_root,
        evidence_root=evidence_root,
    )
    return CanonicalLocalLauncherV1(paths), cfg


def _start(launcher: CanonicalLocalLauncherV1, cfg: Path, **kwargs):
    defaults = {
        "mode": MODE_DASHBOARD_ONLY,
        "config_path": cfg,
        "repository_sha": "deadbeef" * 5,
    }
    defaults.update(kwargs)
    return launcher.start(**defaults)


def test_activation_contract_valid_in_repository(repo_root: Path) -> None:
    path = default_activation_contract_path(repo_root)
    assert path.is_file()
    contract = validate_activation_contract_v1(load_activation_contract_v1(path))
    assert contract["capability_id"] == O8_CAPABILITY_ID
    assert contract["canonical_operator_entrypoint"] == CANONICAL_OPERATOR_ENTRYPOINT
    assert contract["core_logic_changed"] is False
    assert contract["dashboard_trading_authority"] is False
    assert contract["read_model_authority_effect"] == "NONE"
    assert contract["master_runbook_is_only_ssot"] is True
    assert contract["second_ssot_allowed"] is False
    for cmd in CANONICAL_SUBCOMMANDS:
        assert cmd in contract["canonical_subcommands"]


def test_activation_contract_rejects_authority_and_second_ssot(tmp_path: Path, repo_root: Path) -> None:
    good = load_activation_contract_v1(default_activation_contract_path(repo_root))
    bad = dict(good)
    bad["live_trading_authorized"] = True
    with pytest.raises(ActivationContractError) as exc:
        validate_activation_contract_v1(bad)
    assert exc.value.code == "ACTIVATION_CONTRACT_FORBIDDEN_AUTHORITY"

    bad2 = dict(good)
    bad2["second_ssot_allowed"] = True
    with pytest.raises(ActivationContractError) as exc2:
        validate_activation_contract_v1(bad2)
    assert exc2.value.code == "ACTIVATION_CONTRACT_SECOND_SSOT_RISK"


def test_single_operator_entrypoint_docs_and_contract_align(repo_root: Path) -> None:
    entry = repo_root / CANONICAL_OPERATOR_ENTRYPOINT
    assert entry.is_file()
    text = entry.read_text(encoding="utf-8")
    assert "CANONICAL_OPERATOR_ENTRYPOINT" in text or "peak_trade_runtime" in text
    docs = repo_root / "docs/ops/CANONICAL_RUNTIME_OPERATOR_ENTRYPOINT_O8_V1.md"
    assert docs.is_file()
    docs_text = docs.read_text(encoding="utf-8")
    assert CANONICAL_OPERATOR_ENTRYPOINT in docs_text
    assert ACTIVATION_CONTRACT_RELATIVE_PATH in docs_text
    contract = load_activation_contract_v1(default_activation_contract_path(repo_root))
    assert contract["canonical_operator_entrypoint"] == CANONICAL_OPERATOR_ENTRYPOINT


def test_cli_exposes_all_canonical_subcommands() -> None:
    parser = build_parser()
    # argparse stores subparsers on a private action; probe via help / choices.
    sub_actions = [a for a in parser._actions if getattr(a, "dest", None) == "command"]
    assert sub_actions
    choices = set(sub_actions[0].choices or {})
    for cmd in CANONICAL_SUBCOMMANDS:
        assert cmd in choices


def test_existing_lifecycle_semantics_unchanged(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="o8-sess-clean")
    assert started["ok"] is True
    assert started["session"]["lifecycle_state"] == "RUNNING"
    status = launcher.status("o8-sess-clean")
    assert status["ok"] is True
    health = launcher.health("o8-sess-clean")
    assert health["ok"] is True
    stopped = launcher.stop("o8-sess-clean")
    assert stopped["ok"] is True
    assert stopped["stopped"] is True


def test_logs_read_only_and_unknown_session_fail_closed(launcher_env) -> None:
    launcher, cfg = launcher_env
    with pytest.raises(CanonicalLauncherError) as exc:
        launcher.logs("missing-session")
    assert exc.value.code == "SESSION_NOT_FOUND"

    started = _start(launcher, cfg, session_id="o8-logs")
    assert started["ok"] is True
    log_dir = Path(launcher.paths.log_root) / "o8-logs"
    (log_dir / "stdout.log").write_text("hello\ntoken=should_redact_value\n", encoding="utf-8")
    (log_dir / "confirm_token.txt").write_text("secret-token\n", encoding="utf-8")

    result = launcher.logs("o8-logs", tail_lines=50)
    assert result["ok"] is True
    assert result["read_only"] is True
    assert result["process_started"] is False
    assert result["network_accessed"] is False
    assert result["authorization_consumed"] is False
    names = {f["name"] for f in result["files"]}
    assert "stdout.log" in names
    assert "confirm_token.txt" not in names
    joined = "\n".join(line for f in result["files"] for line in f["tail"])
    assert "should_redact_value" not in joined
    assert "<redacted>" in joined

    with pytest.raises(CanonicalLauncherError) as blocked:
        launcher.logs("o8-logs", log_name="../etc/passwd")
    assert blocked.value.code == "LOG_NAME_PATH_TRAVERSAL_BLOCKED"

    with pytest.raises(CanonicalLauncherError) as secret_name:
        launcher.logs("o8-logs", log_name="confirm_token.txt")
    assert secret_name.value.code == "LOG_NAME_SECRET_PATH_BLOCKED"

    launcher.stop("o8-logs")


def test_verify_pass_and_sha_fail_closed(launcher_env, repo_root: Path) -> None:
    launcher, cfg = launcher_env
    ok = launcher.verify()
    assert ok["ok"] is True
    assert ok["read_only"] is True
    assert ok["mutated"] is False
    assert ok["network_accessed"] is False
    assert ok["process_started"] is False
    assert ok["authorization_consumed"] is False
    assert ok["canonical_operator_entrypoint"] == CANONICAL_OPERATOR_ENTRYPOINT

    bad = launcher.verify(expected_repository_sha=("abcd" * 10))
    assert bad["ok"] is False
    assert "REPOSITORY_SHA_MISMATCH" in bad["blockers"]

    started = _start(launcher, cfg, session_id="o8-verify")
    assert started["ok"] is True
    # Session was started with fixture SHA; verify against real repo SHA should mismatch.
    sess = launcher.verify(session_id="o8-verify")
    assert sess["ok"] is False
    assert "SESSION_REPOSITORY_SHA_MISMATCH" in sess["blockers"]
    launcher.stop("o8-verify")


def test_verify_missing_registry_and_health_artifact(launcher_env, repo_root: Path) -> None:
    launcher, cfg = launcher_env
    missing = launcher.verify(session_id="no-such-session")
    assert missing["ok"] is False
    assert any("SESSION" in b for b in missing["blockers"])

    actual_sha = (
        __import__(
            "src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1",
            fromlist=["resolve_repository_sha"],
        ).resolve_repository_sha(repo_root)
    )
    started = _start(launcher, cfg, session_id="o8-health-req", repository_sha=actual_sha)
    hb = Path(started["session"]["heartbeat_path"])
    if hb.exists():
        hb.unlink()
    result = launcher.verify(
        session_id="o8-health-req",
        require_health_artifact=True,
        expected_repository_sha=actual_sha,
    )
    assert result["ok"] is False
    assert "HEALTH_ARTIFACT_MISSING" in result["blockers"]
    launcher.stop("o8-health-req")


def test_verify_rejects_contradictory_activation_contract(tmp_path: Path, launcher_env) -> None:
    launcher, _cfg = launcher_env
    bad_path = tmp_path / "bad_contract.json"
    good = load_activation_contract_v1(
        default_activation_contract_path(launcher.paths.repository_root)
    )
    bad = dict(good)
    bad["core_logic_changed"] = True
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    result = launcher.verify(activation_contract_path=bad_path)
    assert result["ok"] is False
    assert "ACTIVATION_CONTRACT_CORE_LOGIC_FLAG" in result["blockers"]


def test_legacy_paths_preserved(repo_root: Path) -> None:
    for rel in (
        "scripts/run_web_dashboard.py",
        "scripts/ops/refresh_okx_market_dashboard_v1.py",
        "scripts/serve_live_dashboard.py",
        "scripts/live_web_server.py",
        "src/live/web/app.py",
    ):
        assert (repo_root / rel).exists(), rel


def test_unknown_dependency_deauthorization_fail_closed(repo_root: Path) -> None:
    contract = load_activation_contract_v1(default_activation_contract_path(repo_root))
    legacy = contract["legacy_path_policy"]
    assert legacy["unknown_dependency_fail_closed"] is True
    assert legacy["deletion_allowed"] is False
    assert legacy["functional_change_allowed"] is False
    # Attempting to validate a contract that would deauthorize without fail-closed must fail.
    mutated = dict(contract)
    mutated_legacy = dict(legacy)
    mutated_legacy["unknown_dependency_fail_closed"] = False
    mutated["legacy_path_policy"] = mutated_legacy
    with pytest.raises(ActivationContractError) as exc:
        validate_activation_contract_v1(mutated)
    assert exc.value.code == "ACTIVATION_CONTRACT_UNKNOWN_DEPENDENCY_NOT_FAIL_CLOSED"


def test_rollback_boundary_and_authority_separation(repo_root: Path) -> None:
    contract = validate_activation_contract_v1(
        load_activation_contract_v1(default_activation_contract_path(repo_root))
    )
    rollback = contract["rollback_policy"]
    assert rollback["preserves_o1_o7_code"] is True
    assert rollback["preserves_o7_evidence"] is True
    assert rollback["preserves_legacy_callability"] is True
    assert contract["dashboard_trading_authority"] is False
    assert contract["read_model_authority_effect"] == "NONE"
    assert contract["live_trading_authorized"] is False
    assert contract["credentials_authorized"] is False


def test_cli_verify_and_logs_dispatch(tmp_path: Path, repo_root: Path, capsys) -> None:
    state_root = tmp_path / "state"
    log_root = tmp_path / "logs"
    evidence_root = tmp_path / "evidence"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"mode": "dashboard-only"}), encoding="utf-8")
    common = [
        "--repository-root",
        str(repo_root),
        "--state-root",
        str(state_root),
        "--log-root",
        str(log_root),
        "--evidence-root",
        str(evidence_root),
    ]
    rc = dispatch(
        [
            *common,
            "start",
            "--session-id",
            "cli-o8",
            "--config-path",
            str(cfg),
            "--repository-sha",
            "aa" * 20,
        ]
    )
    assert rc == 0
    (log_root / "cli-o8").mkdir(parents=True, exist_ok=True)
    (log_root / "cli-o8" / "stdout.log").write_text("ok\n", encoding="utf-8")
    rc_logs = dispatch([*common, "logs", "--session-id", "cli-o8", "--tail", "10"])
    assert rc_logs == 0
    out = capsys.readouterr().out
    assert '"read_only": true' in out or '"read_only": true'.replace(" ", "") in out.replace(
        " ", ""
    )
    rc_verify = dispatch([*common, "verify"])
    assert rc_verify == 0
    rc_stop = dispatch([*common, "stop", "--session-id", "cli-o8"])
    assert rc_stop == 0


def test_dirty_worktree_verify_optional_gate(launcher_env, monkeypatch) -> None:
    launcher, _cfg = launcher_env

    def _dirty(_root):
        return True

    monkeypatch.setattr(
        "src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1._tracked_worktree_dirty",
        _dirty,
    )
    result = launcher.verify(require_clean_tracked_worktree=True)
    assert result["ok"] is False
    assert "TRACKED_WORKTREE_DIRTY" in result["blockers"]
