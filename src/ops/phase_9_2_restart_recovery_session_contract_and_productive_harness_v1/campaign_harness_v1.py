"""Offline campaign harness: PRE then POST restart segments with fixture state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (
    authorization_digest_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    BUNDLE_MANIFEST_FILENAME,
    CANONICAL_INSTRUMENT_ID,
    CONFIRMATION_SESSION_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    DURABLE_STATE_LINEAGE_ID,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    RESTART_CAMPAIGN_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    VERIFIER_RESULT_FILENAME,
    repo_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (
    build_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.segment_harness_v1 import (
    run_post_restart_segment_v1,
    run_pre_restart_segment_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.state_root_adapter_v1 import (
    build_fixture_checkpoint_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (
    verify_restart_bundle_v1,
)


def run_restart_campaign_fixture_v1(
    *,
    persistence_root: Path,
    repository_sha: str,
    open_position_present: bool = False,
    distinct_observation_count: int = MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    applied_fill_ids: list[str] | None = None,
    applied_confirmation_ids: list[str] | None = None,
    candidate_observation_id: str | None = None,
    candidate_fill_id: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    persistence = Path(persistence_root)
    persistence.mkdir(parents=True, exist_ok=True)

    fill_ids = list(
        applied_fill_ids or ([] if not open_position_present else ["fill_entry_natural_001"])
    )
    conf_ids = list(applied_confirmation_ids or ["conf_obs_001"])

    checkpoint = build_fixture_checkpoint_v1(
        confirmation_session_id=CONFIRMATION_SESSION_ID,
        observation_epoch=distinct_observation_count,
        open_position_present=open_position_present,
        distinct_observation_count=distinct_observation_count,
        evidence_cursor=sha256_canonical_v1({"cursor": "phase92", "n": distinct_observation_count}),
        portfolio_seed="portfolio_v1",
        scope_seed="scope_v1",
        accounting_seed="accounting_v1",
        runtime_seed="runtime_v1",
        instrument_id=CANONICAL_INSTRUMENT_ID,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        durable_state_lineage_id=DURABLE_STATE_LINEAGE_ID,
        applied_fill_ids=fill_ids,
        applied_confirmation_ids=conf_ids,
    )

    pre_runtime = "phase92_restart_pre_runtime_session_v1"
    pre_auth = "phase92_restart_pre_auth_v1"
    pre_contract = build_restart_session_contract_v1(
        repository_sha=repository_sha,
        segment_role=SEGMENT_ROLE_PRE,
        segment_id="segment_pre_restart_v1",
        runtime_session_id=pre_runtime,
        authorization_id=pre_auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=pre_auth,
            segment_role=SEGMENT_ROLE_PRE,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=pre_runtime,
        ),
        expected_runtime_state_digest=checkpoint.runtime_state_digest,
        expected_portfolio_digest=checkpoint.portfolio_digest,
        expected_scope_digest=checkpoint.scope_digest,
        expected_accounting_digest=checkpoint.accounting_digest,
        expected_evidence_cursor=checkpoint.evidence_cursor,
        repo_root=root,
    )
    pre_result = run_pre_restart_segment_v1(
        contract=pre_contract,
        persistence_root=persistence,
        checkpoint=checkpoint,
        request_controlled_restart=True,
    )
    if not pre_result.ok:
        return {
            "ok": False,
            "pre": pre_result.to_dict(),
            "post": None,
            "verifier": None,
            "controlled_restart_exit_code": None,
        }

    post_runtime = "phase92_restart_post_runtime_session_v1"
    post_auth = "phase92_restart_post_auth_v1"
    post_contract = build_restart_session_contract_v1(
        repository_sha=repository_sha,
        segment_role=SEGMENT_ROLE_POST,
        segment_id="segment_post_restart_v1",
        runtime_session_id=post_runtime,
        authorization_id=post_auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=post_auth,
            segment_role=SEGMENT_ROLE_POST,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=post_runtime,
        ),
        expected_runtime_state_digest=checkpoint.runtime_state_digest,
        expected_portfolio_digest=checkpoint.portfolio_digest,
        expected_scope_digest=checkpoint.scope_digest,
        expected_accounting_digest=checkpoint.accounting_digest,
        expected_evidence_cursor=checkpoint.evidence_cursor,
        predecessor_segment_id=pre_contract.segment_id,
        predecessor_terminal_manifest_digest=pre_result.terminal_manifest_digest,
        repo_root=root,
    )
    post_result = run_post_restart_segment_v1(
        contract=post_contract,
        persistence_root=persistence,
        candidate_observation_id=candidate_observation_id or conf_ids[0],
        candidate_fill_id=candidate_fill_id or (fill_ids[0] if fill_ids else None),
    )
    verifier = verify_restart_bundle_v1(persistence_root=persistence)
    write_json_atomic_v1(persistence / VERIFIER_RESULT_FILENAME, verifier.to_dict())
    bundle = {
        "restart_campaign_id": RESTART_CAMPAIGN_ID,
        "durable_state_lineage_id": DURABLE_STATE_LINEAGE_ID,
        "pre_segment": pre_result.to_dict(),
        "post_segment": post_result.to_dict(),
        "verifier": verifier.to_dict(),
        "controlled_restart_exit_code": CONTROLLED_RESTART_EXIT_CODE,
        "ok": bool(pre_result.ok and post_result.ok and verifier.verified),
    }
    write_json_atomic_v1(persistence / BUNDLE_MANIFEST_FILENAME, bundle)
    return bundle
