"""Hermetic proofs for F1/M9 authorized campaign run orchestration owner v1."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    F1M9AuthorizedCampaignRunOrchestrationRequestV1,
    HermeticEvidenceClass,
    orchestration_boundary_invariants_v1,
    run_f1_m9_prospective_authorized_campaign_run_orchestration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorization_consume_v1 import (
    AuthorizationConsumeError,
    atomic_consume_runtime_authorization_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    PREREGISTRATION_DIGEST,
    STATUS_AUTHORIZED_PATH_READY,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_boundary_v1 import (
    CAMPAIGN_EXECUTED,
    NEW_DECISION_MAKING_EVIDENCE_GENERATED,
    PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_closure_v1 import (
    prove_f1_m9_prospective_campaign_authorized_run_orchestration_owner_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    STATUS_BUILD_SLICE_BOUND_ONLY,
    STATUS_ORCHESTRATION_DENIED,
    STATUS_TERMINAL_VERDICT_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.replay_v1 import (
    CampaignReplayError,
    replay_sealed_campaign_evidence_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    build_runtime_authorization_template_v1,
    compute_runtime_authorization_digest,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
    HISTORICAL_PREREGISTRATION_DIGEST,
    OUTCOME_SELECTED,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _active_auth(**overrides: object) -> dict:
    now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    body = build_runtime_authorization_template_v1(
        authorization_id="TEST_ORCH_AUTH_1",
        earliest_valid_utc=now.isoformat().replace("+00:00", "Z"),
        expires_at_utc=(now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        execution_idempotency_key="orch-key-happy-1",
    )
    body["campaign_execution_authorized"] = True
    body["public_market_data_read_authorized"] = True
    body["durable_evidence_write_authorized"] = True
    body.update(overrides)
    body["authorization_digest"] = compute_runtime_authorization_digest(body)
    return body


def _hermetic_request(
    tmp_path: Path,
    auth: dict,
    **kwargs: object,
) -> F1M9AuthorizedCampaignRunOrchestrationRequestV1:
    return F1M9AuthorizedCampaignRunOrchestrationRequestV1(
        runtime_authorization=auth,
        evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
        repo_root=REPO_ROOT,
        hermetic_isolated_campaign_root=tmp_path,
        allow_hermetic_terminal_effects=True,
        public_md_session_fn=lambda **_: {"simulated": True},
        **kwargs,
    )


def test_build_slice_bound_without_real_effects() -> None:
    auth = _active_auth()
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=auth,
            evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
            repo_root=REPO_ROOT,
        )
    )
    assert result.orchestration_status == STATUS_BUILD_SLICE_BOUND_ONLY
    assert result.campaign_executed is False
    assert result.real_evidence_written is False


def test_authorized_hermetic_happy_path_terminal_selection(tmp_path: Path) -> None:
    auth = _active_auth()
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _hermetic_request(tmp_path, auth)
    )
    assert result.orchestration_status == STATUS_TERMINAL_VERDICT_PASS
    assert result.authorized_campaign_execution_terminal_path_proven is True
    assert result.real_authorized_campaign_execution_path_proven is False
    assert result.terminal_selection is not None
    assert result.terminal_selection.get("outcome") == OUTCOME_SELECTED
    assert result.productive_apply_occurred is False
    assert (tmp_path / "MANIFEST.sha256").is_file()
    assert CAMPAIGN_EXECUTED is False


def test_authorization_missing_invalid_stale_foreign() -> None:
    missing = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=None,
            repo_root=REPO_ROOT,
        )
    )
    assert missing.orchestration_status == STATUS_ORCHESTRATION_DENIED

    stale_auth = _active_auth(
        earliest_valid_utc="2020-01-01T00:00:00Z",
        expires_at_utc="2020-01-01T01:00:00Z",
    )
    stale = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=stale_auth,
            evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
            repo_root=REPO_ROOT,
            hermetic_isolated_campaign_root=Path("/tmp/unused"),
            allow_hermetic_terminal_effects=True,
        )
    )
    assert stale.orchestration_status == STATUS_ORCHESTRATION_DENIED
    assert "AUTHORIZATION_EXPIRED" in stale.reason_codes

    foreign = _active_auth(preregistration_digest="0" * 64)
    foreign["authorization_digest"] = compute_runtime_authorization_digest(foreign)
    foreign_result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=foreign,
            evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
            repo_root=REPO_ROOT,
        )
    )
    assert foreign_result.orchestration_status == STATUS_ORCHESTRATION_DENIED


def test_exactly_once_authorization_consumption(tmp_path: Path) -> None:
    auth = _active_auth(execution_idempotency_key="orch-key-consume-1")
    first = atomic_consume_runtime_authorization_v1(
        campaign_root=tmp_path,
        authorization_id=str(auth["authorization_id"]),
        authorization_digest=str(auth["authorization_digest"]),
        execution_identity="exec-id-1",
        consumed_at_utc="2026-09-25T12:00:00Z",
        allow_consume=True,
    )
    assert first["consumed"] is True
    with pytest.raises(AuthorizationConsumeError, match="ALREADY_CONSUMED"):
        atomic_consume_runtime_authorization_v1(
            campaign_root=tmp_path,
            authorization_id=str(auth["authorization_id"]),
            authorization_digest=str(auth["authorization_digest"]),
            execution_identity="exec-id-1",
            consumed_at_utc="2026-09-25T12:00:01Z",
            allow_consume=True,
        )


def test_duplicate_execution_restart_fail_closed(tmp_path: Path) -> None:
    from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.exactly_once_v1 import (
        derive_campaign_execution_identity_v1,
    )

    auth = _active_auth(execution_idempotency_key="orch-key-dup-1")
    identity = derive_campaign_execution_identity_v1(
        campaign_id=CAMPAIGN_ID,
        preregistration_digest=PREREGISTRATION_DIGEST,
        execution_idempotency_key="orch-key-dup-1",
    )
    state_path = tmp_path / "execution_state.json"
    state_path.write_text(
        json.dumps({"execution_identity": identity, "partial": True, "complete": False}),
        encoding="utf-8",
    )
    retry = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _hermetic_request(tmp_path, auth)
    )
    assert retry.orchestration_status == STATUS_ORCHESTRATION_DENIED
    assert any("PARTIAL" in r for r in retry.reason_codes)


def test_incomplete_campaign_not_terminal(tmp_path: Path) -> None:
    auth = _active_auth(execution_idempotency_key="orch-key-incomplete-1")
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _hermetic_request(tmp_path, auth, hermetic_force_incomplete=True)
    )
    assert result.orchestration_status == STATUS_ORCHESTRATION_DENIED
    assert result.terminal_selection is None


def test_contamination_leakage_failure(tmp_path: Path) -> None:
    auth = _active_auth(execution_idempotency_key="orch-key-leak-1")
    request = _hermetic_request(tmp_path, auth)

    def _leak(**_: object) -> dict:
        return {"leak": True}

    request = F1M9AuthorizedCampaignRunOrchestrationRequestV1(
        runtime_authorization=request.runtime_authorization,
        evaluation_time_utc=request.evaluation_time_utc,
        repo_root=request.repo_root,
        hermetic_isolated_campaign_root=request.hermetic_isolated_campaign_root,
        allow_hermetic_terminal_effects=True,
        public_md_session_fn=_leak,
    )
    bundle = {
        "campaign_id": HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
        "preregistration_digest": HISTORICAL_PREREGISTRATION_DIGEST,
        "decision_making_evidence_timestamp_utc": "2026-09-24T22:00:00Z",
    }
    from src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1 import (
        assert_decision_evidence_downstream_of_new_preregistration_v1,
    )

    guard = assert_decision_evidence_downstream_of_new_preregistration_v1(
        bundle, repo_root=REPO_ROOT
    )
    assert guard["historical_evidence_decision_leakage"] is True

    fixture_auth = _active_auth(execution_idempotency_key="orch-key-fixture-1")
    fixture_result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _hermetic_request(
            tmp_path / "fixture",
            fixture_auth,
            hermetic_evidence_class=HermeticEvidenceClass.FIXTURE_CLASS,
        )
    )
    assert fixture_result.orchestration_status == STATUS_ORCHESTRATION_DENIED


def test_evidence_integrity_replay_failure() -> None:
    auth = _active_auth()
    _ = auth
    from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
        SEALED_EVIDENCE_SCHEMA_VERSION,
        SELECTION_POLICY_DIGEST,
    )
    from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
        RESEARCH_CONCLUSION_REGION_PENDING,
    )
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body = {
        "schema_version": SEALED_EVIDENCE_SCHEMA_VERSION,
        "campaign_id": CAMPAIGN_ID,
        "preregistration_digest": PREREGISTRATION_DIGEST,
        "selection_policy_digest": SELECTION_POLICY_DIGEST,
        "decision_making_evidence_timestamp_utc": "2026-09-24T22:00:00Z",
        "evidence_source_class": "REAL_PUBLIC_MARKET_DATA",
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
    body["evidence_bundle_digest"] = compute_content_sha256(
        {k: v for k, v in body.items() if k != "evidence_bundle_digest"}
    )
    mutated = copy.deepcopy(body)
    mutated["session_count"] = 99
    with pytest.raises(CampaignReplayError):
        replay_sealed_campaign_evidence_v1(mutated, repo_root=REPO_ROOT)


def test_replay_and_selection_determinism(tmp_path: Path) -> None:
    auth = _active_auth(execution_idempotency_key="orch-key-determinism-1")
    first = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _hermetic_request(tmp_path, auth)
    )
    completeness = json.loads((tmp_path / "campaign_completeness.json").read_text(encoding="utf-8"))
    sealed = completeness["sealed_evidence_bundle"]
    replay_a = replay_sealed_campaign_evidence_v1(sealed, repo_root=REPO_ROOT)
    replay_b = replay_sealed_campaign_evidence_v1(sealed, repo_root=REPO_ROOT)
    assert replay_a == replay_b
    assert replay_a["selection"] == first.terminal_selection


def test_zero_productive_apply_and_no_trading_effects(tmp_path: Path) -> None:
    auth = _active_auth(execution_idempotency_key="orch-key-zero-prod-1")
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _hermetic_request(tmp_path, auth)
    )
    assert result.productive_apply_occurred is False
    assert result.terminal_selection.get("productive_apply") is False
    assert AUTHORIZED_FOR_PRODUCTIVE_APPLY is False
    assert int(PRODUCTIVE_NUMERIC_VALUES_SET) == 0
    provenance = json.loads((tmp_path / "source_provenance.json").read_text(encoding="utf-8"))
    assert provenance.get("private_api_effect") is False
    assert provenance.get("order_effect") is False


def test_module_invariants_and_closure() -> None:
    assert PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED is False
    assert NEW_DECISION_MAKING_EVIDENCE_GENERATED is False
    assert all(orchestration_boundary_invariants_v1().values())
    assert prove_f1_m9_prospective_campaign_authorized_run_orchestration_owner_v1(
        repo_root=REPO_ROOT
    )


def test_path_ready_still_distinct_from_terminal_execution() -> None:
    from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_boundary_v1 import (
        F1M9ProspectiveCampaignExecutionPhaseV1,
        F1M9ProspectiveCampaignExecutionRequestV1,
        evaluate_f1_m9_prospective_campaign_execution_v1,
    )

    auth = _active_auth()
    boundary = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.AUTHORIZED_CAMPAIGN_EXECUTION,
            runtime_authorization=auth,
            evaluation_time_utc=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc),
            repo_root=REPO_ROOT,
        )
    )
    assert boundary.execution_status == STATUS_AUTHORIZED_PATH_READY
    assert boundary.campaign_executed is False
