"""Contract/regression tests for Step-7 Campaign→Wallclock packaging.

No network session. No confirm-token mint via operator entrypoint execution
that would start a campaign. Latch minting in-process is limited to offline
broker/unit checks already covered elsewhere; packaging tests use doubles.
"""

from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (
    run_productive_wallclock_session_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    ALLOWED_RUNNER_KWARGS,
    REQUIRED_RUNNER_KWARGS,
    discover_canonical_wallclock_runner_signature_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.campaign_start_invoke_v1 import (
    invoke_step7_productive_campaign_sessions_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    TARGET_SESSION_ID_PREFIX,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.delegated_cursor_secure_confirm_broker_v1 import (
    mint_delegated_cursor_secure_confirm_latch_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.governed_campaign_execution_v1 import (
    execute_governed_step7_campaign_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.wallclock_packaging_v1 import (
    SESSION_IDENTITY_PACKAGING_PATH,
    package_step7_wallclock_runner_kwargs_v1,
    prove_step7_wallclock_packaging_bound_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


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


def _package(
    tmp_path: Path,
    *,
    session_id: str,
    sha: str,
    suffix: str,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "prereg": {"test_double": f"prereg_{suffix}", "session_id": session_id},
        "go": {"test_double": f"go_{suffix}", "session_id": session_id},
        "confirm_token": f"WIRING_TEST_TOKEN_{suffix}_IN_MEMORY_ONLY",
        "artifact_path": str(tmp_path / f"auth_{suffix}.json"),
        "evidence_root": str(tmp_path / f"ev_{suffix}"),
        "expected_repository_sha": sha,
        "fingerprint_ledger_path": str(tmp_path / f"fp_{suffix}.txt"),
        "use_real_network": False,
    }


def test_wallclock_actual_signature_matches_step4_contract() -> None:
    sig = inspect.signature(run_productive_wallclock_session_v1)
    names = list(sig.parameters)
    assert names == list(REQUIRED_RUNNER_KWARGS) + [
        p for p in sig.parameters if p not in REQUIRED_RUNNER_KWARGS
    ]
    assert "session_id" not in sig.parameters
    assert "campaign_session_index" not in sig.parameters
    assert "campaign_planned_session_count" not in sig.parameters
    for name, param in sig.parameters.items():
        assert param.kind is inspect.Parameter.KEYWORD_ONLY
        assert name in ALLOWED_RUNNER_KWARGS
    discovered = discover_canonical_wallclock_runner_signature_v1()
    assert discovered["ok"] is True
    assert discovered["keyword_only"] is True
    assert "session_id" not in discovered["required_kwargs"]


def test_regression_session_id_kwarg_typeerror_on_raw_wallclock_call(tmp_path: Path) -> None:
    """Reproduce the historical TypeError; packaging must prevent forwarding."""
    sha = _sha()
    base = _package(tmp_path, session_id="raw_should_fail", sha=sha, suffix="raw")
    # Drop metadata and add illegal kwarg the old invoke edge forwarded.
    illegal = {
        "prereg": base["prereg"],
        "go": base["go"],
        "confirm_token": base["confirm_token"],
        "artifact_path": Path(base["artifact_path"]),
        "evidence_root": Path(base["evidence_root"]),
        "expected_repository_sha": sha,
        "fingerprint_ledger_path": Path(base["fingerprint_ledger_path"]),
        "session_id": "phase_9_2_public_md_multi_session_continuity_session_v1_001",
    }
    with pytest.raises(TypeError, match="unexpected keyword argument 'session_id'"):
        run_productive_wallclock_session_v1(**illegal)

    packaged = package_step7_wallclock_runner_kwargs_v1(base, require_complete=True)
    assert "session_id" not in packaged
    # Signature-compatible: inspect.bind must succeed.
    inspect.signature(run_productive_wallclock_session_v1).bind(**packaged)


def test_step7_packaging_two_distinct_session_contexts_no_network(tmp_path: Path) -> None:
    sha = _sha()
    calls: list[dict[str, Any]] = []

    def runner(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True, "NETWORK_SESSION_STARTED": False}

    packages = [
        _package(
            tmp_path,
            session_id=f"{TARGET_SESSION_ID_PREFIX}_ctx_a",
            sha=sha,
            suffix="a",
        ),
        _package(
            tmp_path,
            session_id=f"{TARGET_SESSION_ID_PREFIX}_ctx_b",
            sha=sha,
            suffix="b",
        ),
    ]
    result = invoke_step7_productive_campaign_sessions_v1(
        planned_session_count=2,
        per_session_wallclock_packages=packages,
        wallclock_runner=runner,
        allow_real_network=False,
        campaign_start_state={},
    )
    assert result["ok"] is True
    assert result["network_session_started"] is False
    assert len(calls) == 2
    assert "session_id" not in calls[0]
    assert "session_id" not in calls[1]
    assert "campaign_session_index" not in calls[0]
    assert calls[0]["evidence_root"] != calls[1]["evidence_root"]
    assert str(calls[0]["evidence_root"]).endswith("ev_a")
    assert str(calls[1]["evidence_root"]).endswith("ev_b")
    assert result["session_results"][0]["package_session_id"].endswith("ctx_a")
    assert result["session_results"][1]["package_session_id"].endswith("ctx_b")
    proof = prove_step7_wallclock_packaging_bound_v1()
    assert proof["ok"] is True
    assert proof["session_identity_packaging_path"] == SESSION_IDENTITY_PACKAGING_PATH


def test_delegated_cursor_path_packaging_no_token_exposure(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    calls: list[dict[str, Any]] = []

    def runner(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True}

    packages = [
        _package(tmp_path, session_id="delegated_a", sha=sha, suffix="da"),
        _package(tmp_path, session_id="delegated_b", sha=sha, suffix="db"),
    ]
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    digest = latch.digest
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
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
        wallclock_runner=runner,
        per_session_wallclock_packages=packages,
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert result.ok is True
    assert result.claims["AUTHORIZATION_CHANNEL"] == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM
    assert result.claims["TOKEN_ROLE"] == CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH
    assert result.claims["CONFIRM_TOKEN_PLAINTEXT_EXPOSED"] is False
    assert result.claims["DELEGATED_SECURE_CONFIRM_VERIFIED"] is True
    assert result.claims["NETWORK_SESSION_STARTED"] is False
    assert len(calls) == 2
    assert all("session_id" not in c for c in calls)
    blob = json.dumps(result.to_dict(), sort_keys=True)
    assert digest in blob
    # Digest-only attestation is required.
    assert result.claims.get("confirm_token_fingerprint") == digest


def test_ephemeral_latch_one_time_still_bound(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    latch = mint_delegated_cursor_secure_confirm_latch_v1()

    def runner(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": True}

    packages = [
        _package(tmp_path, session_id="once_a", sha=sha, suffix="oa"),
        _package(tmp_path, session_id="once_b", sha=sha, suffix="ob"),
    ]
    first = execute_governed_step7_campaign_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=runner,
        per_session_wallclock_packages=packages,
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert first.ok is True
    assert latch.consumed is True

    # Replay same latch must fail-closed.
    second = execute_governed_step7_campaign_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        wallclock_runner=runner,
        per_session_wallclock_packages=packages,
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_confirm_latch=latch,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
    )
    assert second.ok is False
    assert second.claims["NETWORK_SESSION_STARTED"] is False


def test_real_tty_path_still_accepts_injected_runner_without_session_id_kwarg(
    tmp_path: Path,
) -> None:
    sha, cfg = _sha(), _cfg()
    calls: list[dict[str, Any]] = []

    def runner(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True}

    packages = [
        _package(tmp_path, session_id="tty_a", sha=sha, suffix="ta"),
        _package(tmp_path, session_id="tty_b", sha=sha, suffix="tb"),
    ]
    gate_box = ["hidden-confirm-token-for-test-only"]

    def _getpass(_prompt: str = "") -> str:
        return gate_box.pop() if gate_box else ""

    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=_getpass,
        wallclock_runner=runner,
        per_session_wallclock_packages=packages,
        campaign_start_state={},
        repo_root=REPO_ROOT,
        authorization_channel=AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
        expected_capability_id=TARGET_CAMPAIGN_CAPABILITY_ID,
    )
    assert result.ok is True
    assert result.claims["AUTHORIZATION_CHANNEL"] == AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM
    assert result.claims["NETWORK_SESSION_STARTED"] is False
    assert len(calls) == 2
    assert all("session_id" not in c for c in calls)


def test_productive_path_fail_closed_when_packaging_incomplete() -> None:
    result = invoke_step7_productive_campaign_sessions_v1(
        planned_session_count=2,
        wallclock_kwargs={"session_id": "only_metadata"},
        wallclock_runner=None,
        allow_real_network=True,
        campaign_start_state={},
    )
    assert result["ok"] is False
    assert result["network_session_started"] is False
    assert result["wallclock_invoked_count"] == 0
    assert any("RUNNER_INVOKE_BINDING_MISSING_REQUIRED" in b for b in result["blockers"])
