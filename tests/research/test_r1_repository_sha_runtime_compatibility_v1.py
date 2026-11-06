"""R1 materialization provenance vs checkout SHA (post-merge compatibility)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    build_campaign_authorization_artifact_v1,
    write_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    GitBaselineSnapshotV1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.preflight_v1 import (
    run_static_preflight_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
    load_active_campaign_binding_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.compatibility_v1 import (
    assert_r1_materialization_provenance_locked_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.gate_v1 import (
    resolve_active_campaign_binding_for_runtime_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ProductiveCampaignR1RecoveryError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_PREREGISTRATION_ID,
    SESSION_01_ID,
)

ROOT = Path(__file__).resolve().parents[2]


def _checkout_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()


def _binding():
    return load_active_campaign_binding_v1(repo_root=ROOT)


def _baseline() -> GitBaselineSnapshotV1:
    sha = _checkout_sha()
    return GitBaselineSnapshotV1(
        branch="main",
        head_sha=sha,
        origin_main_sha=sha,
        worktree_allowed_delta_only=True,
    )


def test_t1_exact_valid_materialization_passes() -> None:
    binding = resolve_active_campaign_binding_for_runtime_v1(repo_root=ROOT)
    assert_r1_materialization_provenance_locked_v1(binding, repo_root=ROOT)


def test_t2_stale_binding_campaign_mismatch_fails(tmp_path: Path) -> None:
    binding = _binding()
    gov = tmp_path / "config" / "governance"
    gov.mkdir(parents=True)
    bad = binding.to_dict()
    bad["campaign_id"] = "cv_maxage_productive_evidence_campaign_v1_" + ("f" * 16)
    (
        gov / "canonical_volatility_numeric_max_age_productive_campaign_active_binding_v1.json"
    ).write_text(json.dumps(bad, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ProductiveCampaignR1RecoveryError):
        resolve_active_campaign_binding_for_runtime_v1(repo_root=tmp_path)


def test_t6_post_merge_checkout_differs_from_materialization_preflight_passes(
    tmp_path: Path,
) -> None:
    binding = _binding()
    assert _checkout_sha() != binding.repository_sha
    from datetime import datetime, timedelta, timezone

    issued = datetime.now(timezone.utc) - timedelta(minutes=5)
    artifact = build_campaign_authorization_artifact_v1(
        repository_sha=binding.repository_sha,
        campaign_id=binding.campaign_id,
        session_ids=binding.session_ids,
        preregistration_digest=binding.preregistration_digest,
        issued_at=issued,
        earliest_start=issued,
    )
    auth_path = tmp_path / "campaign_authorization.json"
    write_campaign_authorization_artifact_v1(output_path=auth_path, artifact=artifact)
    run_static_preflight_v1(
        repo_root=ROOT,
        campaign_id=binding.campaign_id,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=binding.preregistration_digest,
        session_id=SESSION_01_ID,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.artifact_digest,
        authorization_artifact_path=auth_path,
        repository_sha=_checkout_sha(),
        git_baseline=_baseline(),
    )
