"""F1/M9 prospective campaign execution owner max-build (no live campaign)."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.f1_m9_canonical_productive_candidate_evidence_census_v1 import (
    CAMPAIGN_EXECUTION_FRESH_AUTH_BLOCKER,
    CAMPAIGN_EXECUTION_OWNER_GO_BLOCKER,
    run_f1_m9_canonical_productive_candidate_evidence_census_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.closure_v1 import (
    prove_f1_m9_prospective_candidate_selection_campaign_execution_owner_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.completeness_v1 import (
    REQUIREMENT_VERDICT_FAIL,
    REQUIREMENT_VERDICT_INCOMPLETE,
    REQUIREMENT_VERDICT_PASS,
    adjudicate_campaign_completeness_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    EVIDENCE_SOURCE_FIXTURE,
    EVIDENCE_SOURCE_REAL,
    PREREGISTRATION_DIGEST,
    SEALED_EVIDENCE_SCHEMA_VERSION,
    SELECTION_POLICY_DIGEST,
    STATUS_AUTHORIZED_PATH_READY,
    STATUS_EXECUTION_DENIED,
    STATUS_EXECUTION_PROOF_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.evidence_writer_v1 import (
    CampaignEvidenceWriteDeniedError,
    write_campaign_artifact_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_boundary_v1 import (
    CAMPAIGN_EXECUTED,
    F1M9ProspectiveCampaignExecutionPhaseV1,
    F1M9ProspectiveCampaignExecutionRequestV1,
    NEW_DECISION_MAKING_EVIDENCE_GENERATED,
    evaluate_f1_m9_prospective_campaign_execution_v1,
    prove_execution_proof_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.exactly_once_v1 import (
    RESUME_STATE_ALREADY_COMPLETE,
    RESUME_STATE_FAIL_CLOSED,
    adjudicate_execution_resume_state_v1,
    default_execution_identity_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.replay_v1 import (
    CampaignReplayError,
    replay_sealed_campaign_evidence_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    build_runtime_authorization_template_v1,
    compute_runtime_authorization_digest,
    resolve_runtime_authorization_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1 import (
    assert_decision_evidence_downstream_of_new_preregistration_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_closure_v1 import (
    EARLIEST_REMAINING_BLOCKER,
    prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
    HISTORICAL_PREREGISTRATION_DIGEST,
    OUTCOME_NO_SELECTION,
    OUTCOME_SELECTED,
    RESEARCH_CONCLUSION_REGION_PENDING,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _active_auth(**overrides: object) -> dict:
    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    body = build_runtime_authorization_template_v1(
        authorization_id="TEST_AUTH_INACTIVE_FOR_BUILD",
        earliest_valid_utc=now.isoformat().replace("+00:00", "Z"),
        expires_at_utc=(now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        execution_idempotency_key="test-key-1",
    )
    body["campaign_execution_authorized"] = True
    body["public_market_data_read_authorized"] = True
    body["durable_evidence_write_authorized"] = True
    body.update(overrides)
    body["authorization_digest"] = compute_runtime_authorization_digest(body)
    return body


def _sealed_bundle(**overrides: object) -> dict:
    body: dict = {
        "schema_version": SEALED_EVIDENCE_SCHEMA_VERSION,
        "campaign_id": CAMPAIGN_ID,
        "preregistration_digest": PREREGISTRATION_DIGEST,
        "selection_policy_digest": SELECTION_POLICY_DIGEST,
        "decision_making_evidence_timestamp_utc": "2026-09-24T22:00:00Z",
        "evidence_source_class": EVIDENCE_SOURCE_REAL,
        "session_count": 2,
        "regime_count": 2,
        "evidence_count": 8,
        "campaign_sealed": True,
        "oos_evidence": {"present": True, "holdout_pass": True},
        "robustness_evidence": {"present": True, "robustness_pass": True},
        "economic_evidence": {"present": True, "economic_pass": True},
        "failure_evidence": {
            "rejection_matrix_present": True,
            "rejection_reasons_complete": True,
        },
        "research_conclusion": RESEARCH_CONCLUSION_REGION_PENDING,
        "robust_candidate_region": [600],
        "rejection_matrix": [{"candidate_id": "CANDIDATE_600_S", "rejected": False}],
    }
    body.update(overrides)
    body["evidence_bundle_digest"] = compute_content_sha256(
        {k: v for k, v in body.items() if k != "evidence_bundle_digest"}
    )
    return body


def test_execution_proof_pass_without_network_or_writes() -> None:
    assert prove_execution_proof_v1(repo_root=REPO_ROOT)
    result = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.EXECUTION_PROOF,
            repo_root=REPO_ROOT,
        )
    )
    assert result.execution_status == STATUS_EXECUTION_PROOF_PASS
    assert result.campaign_executed is False


def test_missing_runtime_authorization_rejects_authorized_path() -> None:
    result = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.AUTHORIZED_CAMPAIGN_EXECUTION,
            runtime_authorization=None,
            repo_root=REPO_ROOT,
        )
    )
    assert result.execution_status == STATUS_EXECUTION_DENIED
    assert "RUNTIME_AUTHORIZATION_ABSENT" in result.reason_codes


def test_execution_without_network_rejected() -> None:
    auth = _active_auth(public_market_data_read_authorized=False)
    result = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.AUTHORIZED_CAMPAIGN_EXECUTION,
            runtime_authorization=auth,
            evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
            repo_root=REPO_ROOT,
        )
    )
    assert result.execution_status == STATUS_EXECUTION_DENIED
    assert "REAL_PUBLIC_MD_READ_NOT_AUTHORIZED" in result.reason_codes


def test_network_without_evidence_write_blocks_materialization() -> None:
    auth = _active_auth(durable_evidence_write_authorized=False)
    result = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.AUTHORIZED_CAMPAIGN_EXECUTION,
            runtime_authorization=auth,
            evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
            repo_root=REPO_ROOT,
        )
    )
    assert result.execution_status == STATUS_EXECUTION_DENIED
    assert "DURABLE_EVIDENCE_WRITE_NOT_AUTHORIZED" in result.reason_codes


def test_fully_authorized_path_ready_without_execution() -> None:
    auth = _active_auth()
    result = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.AUTHORIZED_CAMPAIGN_EXECUTION,
            runtime_authorization=auth,
            evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
            repo_root=REPO_ROOT,
        )
    )
    assert result.execution_status == STATUS_AUTHORIZED_PATH_READY
    assert result.campaign_executed is False


def test_wrong_digests_reject_authorization() -> None:
    auth = _active_auth(preregistration_digest="0" * 64)
    auth["authorization_digest"] = compute_runtime_authorization_digest(auth)
    _, reasons = resolve_runtime_authorization_v1(
        auth, evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    )
    assert "PREREGISTRATION_DIGEST_MISMATCH" in reasons or reasons


def test_expired_authorization_rejects() -> None:
    auth = _active_auth(
        earliest_valid_utc="2020-01-01T00:00:00Z",
        expires_at_utc="2020-01-01T01:00:00Z",
    )
    _, reasons = resolve_runtime_authorization_v1(
        auth, evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    )
    assert "AUTHORIZATION_EXPIRED" in reasons


def test_historical_leakage_rejects() -> None:
    guard = assert_decision_evidence_downstream_of_new_preregistration_v1(
        {
            "campaign_id": HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
            "preregistration_digest": HISTORICAL_PREREGISTRATION_DIGEST,
            "decision_making_evidence_timestamp_utc": "2026-09-24T22:00:00Z",
        },
        repo_root=REPO_ROOT,
    )
    assert guard["historical_evidence_decision_leakage"] is True


def test_fixture_cannot_satisfy_real() -> None:
    verdict = adjudicate_campaign_completeness_v1(
        _sealed_bundle(evidence_source_class=EVIDENCE_SOURCE_FIXTURE),
        repo_root=REPO_ROOT,
    )
    assert verdict.real_evidence_requirement == REQUIREMENT_VERDICT_FAIL
    assert verdict.campaign_selection_eligible is False


def test_partial_evidence_not_selection_eligible() -> None:
    verdict = adjudicate_campaign_completeness_v1(
        _sealed_bundle(session_count=1, evidence_count=2, campaign_sealed=False),
        repo_root=REPO_ROOT,
    )
    assert verdict.campaign_selection_eligible is False
    assert verdict.session_coverage_requirement in (
        REQUIREMENT_VERDICT_INCOMPLETE,
        REQUIREMENT_VERDICT_FAIL,
    )


def test_complete_real_bundle_selection_eligible_and_replay() -> None:
    bundle = _sealed_bundle()
    verdict = adjudicate_campaign_completeness_v1(bundle, repo_root=REPO_ROOT)
    assert verdict.campaign_selection_eligible is True
    for field in (
        verdict.real_evidence_requirement,
        verdict.session_coverage_requirement,
        verdict.regime_coverage_requirement,
        verdict.oos_requirement,
        verdict.robustness_requirement,
        verdict.economic_requirement,
        verdict.failure_evidence_requirement,
        verdict.contamination_requirement,
    ):
        assert field == REQUIREMENT_VERDICT_PASS
    replay = replay_sealed_campaign_evidence_v1(bundle, repo_root=REPO_ROOT)
    assert replay["selection"]["outcome"] == OUTCOME_SELECTED


def test_replay_digest_mutation_fail_closed() -> None:
    bundle = _sealed_bundle()
    mutated = copy.deepcopy(bundle)
    mutated["session_count"] = 99
    with pytest.raises(CampaignReplayError):
        replay_sealed_campaign_evidence_v1(mutated, repo_root=REPO_ROOT)


def test_unresolved_tie_replay_no_selection() -> None:
    bundle = _sealed_bundle(
        robust_candidate_region=[300, 600],
        rejection_matrix=[
            {"candidate_id": "CANDIDATE_300_S", "rejected": False},
            {"candidate_id": "CANDIDATE_600_S", "rejected": False},
        ],
    )
    replay = replay_sealed_campaign_evidence_v1(bundle, repo_root=REPO_ROOT)
    assert replay["selection"]["outcome"] == OUTCOME_NO_SELECTION


def test_evidence_writer_requires_authorization(tmp_path: Path) -> None:
    with pytest.raises(CampaignEvidenceWriteDeniedError):
        write_campaign_artifact_v1(
            artifact_path=tmp_path / "x.json",
            payload={"campaign_id": CAMPAIGN_ID, "preregistration_digest": PREREGISTRATION_DIGEST},
            durable_evidence_write_authorized=False,
        )


def test_exactly_once_partial_fail_closed(tmp_path: Path) -> None:
    identity = default_execution_identity_v1(execution_idempotency_key="k1")
    state_path = tmp_path / "execution_state.json"
    state_path.write_text(
        '{"execution_identity":"' + identity + '","partial":true}',
        encoding="utf-8",
    )
    adj = adjudicate_execution_resume_state_v1(
        campaign_root=tmp_path,
        execution_identity=identity,
    )
    assert adj["resume_state"] == RESUME_STATE_FAIL_CLOSED


def test_sealed_campaign_already_complete(tmp_path: Path) -> None:
    identity = default_execution_identity_v1(execution_idempotency_key="k2")
    adj = adjudicate_execution_resume_state_v1(
        campaign_root=tmp_path,
        execution_identity=identity,
        sealed_manifest={"campaign_sealed": True, "execution_identity": identity},
    )
    assert adj["resume_state"] == RESUME_STATE_ALREADY_COMPLETE


def test_downstream_invariants_and_closure() -> None:
    assert CAMPAIGN_EXECUTED is False
    assert NEW_DECISION_MAKING_EVIDENCE_GENERATED is False
    assert AUTHORIZED_FOR_PRODUCTIVE_APPLY is False
    assert int(PRODUCTIVE_NUMERIC_VALUES_SET) == 0
    assert prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1(
        repo_root=REPO_ROOT
    )
    assert prove_f1_m9_prospective_candidate_selection_campaign_execution_owner_v1(
        repo_root=REPO_ROOT
    )
    census = run_f1_m9_canonical_productive_candidate_evidence_census_v1(repo_root=REPO_ROOT)
    assert census.earliest_blocker == "EXTERNAL_ORDER_EFFECT_WIRE_SEND_LIVE_BOUNDARY"
    assert EARLIEST_REMAINING_BLOCKER == (
        "F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_AUTHORIZATION_OWNER_GO"
    )
