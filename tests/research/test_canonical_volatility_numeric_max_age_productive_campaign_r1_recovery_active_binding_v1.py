"""Focused tests for productive campaign R1 recovery + sole ACTIVE binding v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    build_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    PreregisteredSessionRunnerError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.preflight_v1 import (
    run_static_preflight_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
    assert_exactly_one_active_binding_file_v1,
    build_active_campaign_binding_v1,
    load_active_campaign_binding_v1,
    verify_active_campaign_binding_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.architecture_guards_v1 import (
    assert_r1_recovery_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    ACTIVE_BINDING_REL_PATH,
    DISPOSITION_REL_PATH,
    OWNER_POLICY,
    R1_MATERIALIZED_REPOSITORY_SHA,
    R1_PREREGISTRATION_REL_PATH,
    TOMBSTONE_ABANDONED_CAMPAIGN_ID,
    TOMBSTONE_ABANDONED_SESSION_IDS,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.disposition_v1 import (
    assert_old_campaign_cannot_complete_v1,
    load_abandoned_campaign_disposition_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.gate_v1 import (
    assert_late_age_session_has_s01_persistence_v1,
    assert_not_additional_evidence_routing_v1,
    assert_runtime_matches_active_binding_v1,
    resolve_active_campaign_binding_for_runtime_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.identity_v1 import (
    derive_r1_campaign_identity_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.models_v1 import (
    ProductiveCampaignR1RecoveryError,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.preregistration_v1 import (
    build_r1_active_preregistration_payload_v1,
    verify_r1_active_preregistration_payload_v1,
)

ROOT = Path(__file__).resolve().parents[2]
SHA = R1_MATERIALIZED_REPOSITORY_SHA


def test_01_disposition_tombstone_non_authoritative() -> None:
    disp = load_abandoned_campaign_disposition_v1(repo_root=ROOT)
    assert disp.disposition == "ABANDONED_INCOMPLETE_NON_AUTHORITATIVE"
    assert disp.campaign_id == TOMBSTONE_ABANDONED_CAMPAIGN_ID
    assert disp.session_ids == TOMBSTONE_ABANDONED_SESSION_IDS
    assert disp.completion_allowed is False
    assert disp.reactivation_allowed is False
    assert disp.session_reuse_allowed is False
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="abandoned_campaign_completion"):
        assert_old_campaign_cannot_complete_v1(
            campaign_id=TOMBSTONE_ABANDONED_CAMPAIGN_ID, claimed_complete=True
        )


def test_02_old_ids_cannot_reactivate_via_auth() -> None:
    with pytest.raises(CampaignAuthorizationError, match="abandoned_campaign_reactivation"):
        build_campaign_authorization_artifact_v1(
            repository_sha=SHA,
            campaign_id=TOMBSTONE_ABANDONED_CAMPAIGN_ID,
            session_ids=TOMBSTONE_ABANDONED_SESSION_IDS,
            preregistration_digest="a" * 64,
            issued_at="2026-08-01T12:00:00+00:00",
            earliest_start="2026-08-01T12:00:00+00:00",
        )


def test_03_fresh_unique_campaign_and_session_ids() -> None:
    identity = derive_r1_campaign_identity_v1(repository_sha=SHA)
    assert identity["campaign_id"] != TOMBSTONE_ABANDONED_CAMPAIGN_ID
    assert identity["session_01_id"] not in TOMBSTONE_ABANDONED_SESSION_IDS
    assert identity["session_02_id"] not in TOMBSTONE_ABANDONED_SESSION_IDS
    assert identity["session_01_id"] != identity["session_02_id"]
    other = derive_r1_campaign_identity_v1(repository_sha="b" * 40)
    assert other["campaign_id"] != identity["campaign_id"]


def test_04_exactly_one_active_campaign_binding() -> None:
    path = assert_exactly_one_active_binding_file_v1(repo_root=ROOT)
    assert path == ROOT / ACTIVE_BINDING_REL_PATH
    binding = load_active_campaign_binding_v1(repo_root=ROOT, expected_repository_sha=SHA)
    assert binding.status == "ACTIVE"
    assert binding.owner_policy == OWNER_POLICY
    verify_active_campaign_binding_v1(binding, expected_repository_sha=SHA)


def test_05_multiple_active_binding_fails_closed(tmp_path: Path) -> None:
    gov = tmp_path / "config" / "governance"
    gov.mkdir(parents=True)
    binding = build_active_campaign_binding_v1(repository_sha=SHA)
    (
        gov / "canonical_volatility_numeric_max_age_productive_campaign_active_binding_v1.json"
    ).write_text(json.dumps(binding.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (
        gov / "canonical_volatility_numeric_max_age_productive_campaign_active_binding_alt.json"
    ).write_text(json.dumps(binding.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="multiple_active"):
        assert_exactly_one_active_binding_file_v1(repo_root=tmp_path)


def test_06_missing_active_binding_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "config" / "governance").mkdir(parents=True)
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="active_binding_missing"):
        assert_exactly_one_active_binding_file_v1(repo_root=tmp_path)


def test_07_stale_repository_sha_rejected() -> None:
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="repository_sha"):
        load_active_campaign_binding_v1(repo_root=ROOT, expected_repository_sha="0" * 40)


def test_08_missing_s01_persistence_rejects_s02(tmp_path: Path) -> None:
    binding = load_active_campaign_binding_v1(repo_root=ROOT, expected_repository_sha=SHA)
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="missing_s01_persistence"):
        assert_late_age_session_has_s01_persistence_v1(
            binding,
            session_id=binding.session_02_id,
            repo_root=tmp_path,
            evidence_root=tmp_path,
        )


def test_09_synthetic_and_cross_sha_s01_rejected() -> None:
    identity = derive_r1_campaign_identity_v1(repository_sha=SHA)
    binding = load_active_campaign_binding_v1(repo_root=ROOT, expected_repository_sha=SHA)
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="runtime_repository_sha"):
        assert_runtime_matches_active_binding_v1(
            binding,
            campaign_id=identity["campaign_id"],
            session_id=identity["session_01_id"],
            preregistration_digest=binding.preregistration_digest,
            repository_sha="c" * 40,
        )
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="runtime_campaign_not_active"):
        assert_runtime_matches_active_binding_v1(
            binding,
            campaign_id="synthetic_campaign_id",
            session_id=identity["session_01_id"],
            preregistration_digest=binding.preregistration_digest,
            repository_sha=SHA,
        )


def test_10_exactly_once_and_fresh_s01_s02_provenance_preserved() -> None:
    preg = build_r1_active_preregistration_payload_v1(repository_sha=SHA)
    binding = load_active_campaign_binding_v1(repo_root=ROOT, expected_repository_sha=SHA)
    verify_r1_active_preregistration_payload_v1(
        preg,
        expected_repository_sha=SHA,
        expected_campaign_id=binding.campaign_id,
        expected_session_ids=binding.session_ids,
    )
    on_disk = json.loads((ROOT / R1_PREREGISTRATION_REL_PATH).read_text(encoding="utf-8"))
    assert on_disk["preregistration_digest"] == binding.preregistration_digest
    assert on_disk["campaign_id"] == binding.campaign_id
    reach = on_disk["reachability_7200_plan"]["session_distribution"]
    assert reach["early_estimate_producer_session_id"] == binding.session_01_id
    assert reach["late_age_observation_session_id"] == binding.session_02_id
    assert binding.early_estimate_producer_session_id == binding.session_01_id
    assert binding.late_age_observation_session_id == binding.session_02_id
    assert binding.typed_volatility_persistence_path.endswith("typed_volatility_persistence.jsonl")


def test_11_no_additional_evidence_routing() -> None:
    assert_not_additional_evidence_routing_v1(
        campaign_id=load_active_campaign_binding_v1(
            repo_root=ROOT, expected_repository_sha=SHA
        ).campaign_id
    )
    with pytest.raises(ProductiveCampaignR1RecoveryError, match="additional_evidence"):
        assert_not_additional_evidence_routing_v1(
            campaign_id="cv_maxage_additional_evidence_campaign"
        )


def test_12_architecture_guards_no_trading_authority() -> None:
    guards = assert_r1_recovery_architecture_guards_v1()
    assert guards["cross_sha_reuse_allowed"] is False
    assert guards["synthetic_s01_allowed"] is False
    assert guards["additional_evidence_reclassification"] is False
    binding = resolve_active_campaign_binding_for_runtime_v1(repo_root=ROOT)
    assert binding.execution_authorized is False
    assert binding.network_authorized is False
    assert binding.evidence_write_authorized is False
    assert (ROOT / DISPOSITION_REL_PATH).is_file()


def test_13_preflight_rejects_tombstone_campaign() -> None:
    with pytest.raises(PreregisteredSessionRunnerError, match="abandoned_campaign"):
        run_static_preflight_v1(
            repo_root=ROOT,
            campaign_id=TOMBSTONE_ABANDONED_CAMPAIGN_ID,
            preregistration_id="x",
            preregistration_digest="a" * 64,
            session_id=TOMBSTONE_ABANDONED_SESSION_IDS[0],
            authorization_id="x",
            authorization_digest="b" * 64,
            authorization_artifact_path=ROOT / "missing_auth.json",
            repository_sha=SHA,
        )


def test_14_post_merge_checkout_sha_may_differ_from_materialization_provenance() -> None:
    import subprocess

    binding = load_active_campaign_binding_v1(repo_root=ROOT)
    checkout_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True
    ).strip()
    assert checkout_sha
    assert checkout_sha != binding.repository_sha
    resolved = resolve_active_campaign_binding_for_runtime_v1(repo_root=ROOT)
    assert resolved.repository_sha == binding.repository_sha
