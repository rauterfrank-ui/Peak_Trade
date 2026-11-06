"""Failure-injection cases for post-unlock runtime invocation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (  # noqa: E501
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.fake_public_md_v1 import (  # noqa: E501
    build_fake_ticker_fetcher_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (  # noqa: E501
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (  # noqa: E501
    RESTART_CAMPAIGN_ID,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.constants_v1 import (  # noqa: E501
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.invocation_v1 import (  # noqa: E501
    invoke_post_unlock_canonical_runtime_v1,
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


class _Clock:
    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self._t = float(start)

    def time(self) -> float:
        return self._t

    def sleep(self, seconds: float) -> None:
        self._t += float(seconds)


def _write_active_session_go(path: Path, *, sha: str, cfg: str, now: float) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_failure_injection_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=now - 10,
        not_before=now - 5,
        expires_at=now + 3600,
        activation_status=ACTIVATION_STATUS_ACTIVE,
    )
    write_json_atomic_v1(path, auth.to_dict())


def run_post_unlock_failure_injection_v1(
    *,
    work_root: Path,
    repository_sha: str,
    config_digest: str,
    now_unix: float = 1_700_000_000.0,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Deterministic failure injection; no real network, no real auth issuance."""
    root = Path(work_root)
    root.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    # A: gate false → no runner
    case_a = root / "gate_false"
    case_a.mkdir(parents=True, exist_ok=True)
    clock = _Clock(now_unix)
    calls: list[tuple[str, str]] = []
    transport = EeaPublicMdTransportV1(
        fetcher=build_fake_ticker_fetcher_v1(calls=calls, clock=clock),
        sleep=clock.sleep,
        environ={},
    )
    pre = build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=repository_sha,
        config_digest=config_digest,
        authorization_id="auth_fi_pre_a",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=now_unix + 3600,
        max_segment_duration_seconds=180,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )

    def _post_builder(**kwargs: Any):
        return build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=repository_sha,
            config_digest=kwargs["config_digest"],
            authorization_id="auth_fi_post_a",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=180,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
        )

    gate_false = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=case_a,
        repository_sha=repository_sha,
        config_digest=config_digest,
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=case_a / "missing_session_go.json",
        pre_envelope=pre,
        post_envelope_builder=_post_builder,
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        repo_root=repo_root,
    )
    results["A_GATE_FALSE"] = {
        "ok": (not gate_false.ok)
        and (not gate_false.canonical_runner_invoked)
        and (not gate_false.authorization_consumed)
        and gate_false.canonical_runner_invocation_count == 0,
        "blockers": gate_false.blockers,
    }

    # B: gate would pass bindings but authorization flag missing
    case_b = root / "auth_missing"
    case_b.mkdir(parents=True, exist_ok=True)
    sgo_b = case_b / "session_go.json"
    _write_active_session_go(sgo_b, sha=repository_sha, cfg=config_digest, now=now_unix)
    auth_missing = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=case_b,
        repository_sha=repository_sha,
        config_digest=config_digest,
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo_b,
        pre_envelope=pre,
        post_envelope_builder=_post_builder,
        transport=transport,
        confirm_token_present=True,
        authorization_present=False,
        execute=True,
        repo_root=repo_root,
    )
    results["B_AUTH_MISSING"] = {
        "ok": (not auth_missing.ok)
        and (not auth_missing.canonical_runner_invoked)
        and (not auth_missing.authorization_consumed),
        "blockers": auth_missing.blockers,
    }

    # E: runner exception → lock released, abort, no blind retry
    case_e = root / "runner_exception"
    case_e.mkdir(parents=True, exist_ok=True)
    sgo_e = case_e / "session_go.json"
    _write_active_session_go(sgo_e, sha=repository_sha, cfg=config_digest, now=now_unix)

    def _boom_runner(**_kwargs: Any):
        raise RuntimeError("INJECTED_RUNNER_FAILURE")

    boom = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=case_e,
        repository_sha=repository_sha,
        config_digest=config_digest,
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo_e,
        pre_envelope=build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            repository_sha=repository_sha,
            config_digest=config_digest,
            authorization_id="auth_fi_pre_e",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:pre",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=180,
            expected_successor_state="CHECKPOINT_MATERIALIZED",
        ),
        post_envelope_builder=_post_builder,
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        runtime_runner=_boom_runner,
        repo_root=repo_root,
    )
    results["E_RUNNER_EXCEPTION"] = {
        "ok": (not boom.ok)
        and boom.terminal_state == "ABORT"
        and boom.canonical_runner_invocation_count == 1
        and bool(boom.claims.get("BLIND_RETRY_PERFORMED") is False),
        "terminal_state": boom.terminal_state,
        "blockers": boom.blockers,
    }

    ok = all(bool(v.get("ok")) for v in results.values())
    return {"ok": ok, "cases": results}
