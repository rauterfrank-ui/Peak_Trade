"""Evidence materialization for the productive restart network entrypoint (fixtures only)."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    CAPABILITY_ID,
    DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
    DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
    EVIDENCE_DIRNAME,
    OWNER,
    PRODUCER_VERSION,
    RESTART_CAMPAIGN_ID,
    SCHEMA_VERSION,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
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
    run_offline_productive_restart_orchestration_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.parity_v1 import (
    prove_phase92_productive_entrypoint_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    build_segment_authorization_envelope_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


class _Clock:
    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self._t = float(start)

    def time(self) -> float:
        return self._t

    def sleep(self, seconds: float) -> None:
        self._t += float(seconds)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_capability_evidence_v1(
    *,
    repository_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    out = (
        Path(evidence_root)
        if evidence_root is not None
        else root / "docs" / "evidence" / EVIDENCE_DIRNAME
    )
    fixtures = out / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    # Idempotent rematerialization of this capability's own fixture roots only.
    for ephemeral in (
        fixtures / "offline_campaign_root",
        fixtures / "failure_injection",
    ):
        if ephemeral.exists():
            shutil.rmtree(ephemeral)

    cfg = str(
        load_activation_config_v1(
            config_path=root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )
    now = 1_700_000_000.0
    clock = _Clock(now)
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
        config_digest=cfg,
        authorization_id="phase92_productive_pre_auth_evidence_v1",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=now + 3600,
        max_segment_duration_seconds=DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )

    def _post_builder(**kwargs: Any):
        return build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=repository_sha,
            config_digest=kwargs["config_digest"],
            authorization_id="phase92_productive_post_auth_evidence_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now + 3600,
            max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
        )

    campaign = run_offline_productive_restart_orchestration_v1(
        persistence_root=fixtures / "offline_campaign_root",
        repository_sha=repository_sha,
        pre_envelope=pre,
        post_envelope_builder=_post_builder,
        transport=transport,
        now_unix=now,
        repo_root=root,
        applied_confirmation_ids=["conf_obs_natural_001"],
        candidate_observation_id="conf_obs_natural_001",
    )
    write_json_atomic_v1(fixtures / "offline_campaign_bundle_v1.json", campaign.to_dict())

    failures = run_failure_injection_matrix_v1(
        tmp_root=fixtures / "failure_injection",
        repository_sha=repository_sha,
        repo_root=root,
        now_unix=now,
    )
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", failures)

    boundary = prove_public_md_network_boundary_v1(environ={})
    write_json_atomic_v1(fixtures / "network_boundary_proof_v1.json", boundary)

    parity = prove_phase92_productive_entrypoint_parity_v1()
    write_json_atomic_v1(fixtures / "parity_proof_v1.json", parity)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": repository_sha,
        "ok": bool(campaign.ok and failures.get("ok") and boundary.get("ok") and parity.get("ok")),
        "claims": {
            **(campaign.claims or {}),
            "AUTHORIZATION_ISSUED": False,
            "NETWORK_SESSION_STARTED": False,
            "FAILURE_INJECTION_OK": bool(failures.get("ok")),
            "PARITY_OK": bool(parity.get("ok")),
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        },
        "offline_campaign_ok": bool(campaign.ok),
        "failure_injection_ok": bool(failures.get("ok")),
        "network_boundary_ok": bool(boundary.get("ok")),
        "parity_ok": bool(parity.get("ok")),
    }
    evidence_digest = sha256_canonical_v1(summary)
    summary["evidence_digest"] = evidence_digest
    write_json_atomic_v1(out / "SUMMARY.json", summary)

    manifest_lines = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(out).as_posix()
            manifest_lines.append(f"{_file_sha256(path)}  {rel}")
    (out / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return summary
