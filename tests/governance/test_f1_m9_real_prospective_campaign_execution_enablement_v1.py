"""Hermetic proofs for F1/M9 REAL prospective campaign execution enablement v1."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    F1M9AuthorizedCampaignRunOrchestrationRequestV1,
    HermeticEvidenceClass,
    run_f1_m9_prospective_authorized_campaign_run_orchestration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    PREREGISTRATION_DIGEST,
    REAL_MD_SUPPLIER_ID,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.enablement_closure_v1 import (
    prove_f1_m9_real_prospective_campaign_execution_enablement_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_mode_v1 import (
    F1M9OrchestrationExecutionModeV1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    STATUS_ALREADY_COMPLETE_REPLAY,
    STATUS_BUILD_SLICE_BOUND_ONLY,
    STATUS_ORCHESTRATION_DENIED,
    STATUS_REAL_TERMINAL_VERDICT_PASS,
    STATUS_TERMINAL_VERDICT_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_public_md_session_adapter_v1 import (
    FakeRealPublicMdSessionAdapterV1,
    resolve_canonical_real_md_supplier_runtime_binding_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_issuance_v1 import (
    AUTHORIZED_CAPABILITIES_V1,
    RuntimeAuthorizationIssuanceError,
    issue_f1_m9_prospective_campaign_runtime_authorization_v1,
    verify_issued_runtime_authorization_bindings_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    build_runtime_authorization_template_v1,
    compute_runtime_authorization_digest,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.session_work_units_v1 import (
    resolve_preregistered_session_work_units_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.work_unit_exactly_once_v1 import (
    WorkUnitExactlyOnceError,
    record_work_unit_execution_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import OUTCOME_SELECTED
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_BASE_SHA = "99d1f535cded085b9026d6936a45e3556bfc0e2a"
EVAL_TIME = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)


def _recompute_issued_digests(body: dict) -> dict:
    updated = dict(body)
    issuance_body = {k: v for k, v in updated.items() if k != "authorization_digest"}
    check = {k: v for k, v in issuance_body.items() if k != "issuance_record_digest"}
    updated["issuance_record_digest"] = compute_content_sha256(check)
    updated["authorization_digest"] = compute_runtime_authorization_digest(updated)
    return updated


def _issued_auth(**overrides: object) -> dict:
    body = issue_f1_m9_prospective_campaign_runtime_authorization_v1(
        authorization_id="TEST_ENABLEMENT_AUTH_1",
        bound_origin_main_sha=CANONICAL_BASE_SHA,
        execution_idempotency_key=str(
            overrides.pop("execution_idempotency_key", "enablement-key-1")
        ),
        owner_identity="TEST_OWNER",
        decision_identity="TEST_DECISION",
        earliest_valid_utc=EVAL_TIME,
        expires_at_utc=EVAL_TIME + timedelta(hours=1),
        repo_root=REPO_ROOT,
        allow_issuance=True,
    )
    if overrides:
        body.update(overrides)
        body = _recompute_issued_digests(body)
    return body


def _real_request(
    tmp_path: Path,
    auth: dict,
    *,
    adapter: FakeRealPublicMdSessionAdapterV1 | None = None,
    **kwargs: object,
) -> F1M9AuthorizedCampaignRunOrchestrationRequestV1:
    return F1M9AuthorizedCampaignRunOrchestrationRequestV1(
        runtime_authorization=auth,
        evaluation_time_utc=EVAL_TIME,
        repo_root=REPO_ROOT,
        execution_mode=F1M9OrchestrationExecutionModeV1.REAL_AUTHORIZED_CAMPAIGN_EXECUTION,
        real_campaign_root=tmp_path,
        real_public_md_adapter=adapter or FakeRealPublicMdSessionAdapterV1(),
        allow_real_execution_effects_for_test=True,
        expected_bound_origin_main_sha=CANONICAL_BASE_SHA,
        **kwargs,
    )


def test_issuance_valid_and_verify_passes() -> None:
    auth = _issued_auth()
    assert (
        verify_issued_runtime_authorization_bindings_v1(
            auth,
            repo_root=REPO_ROOT,
            expected_bound_origin_main_sha=CANONICAL_BASE_SHA,
        )
        == ()
    )
    with pytest.raises(RuntimeAuthorizationIssuanceError):
        issue_f1_m9_prospective_campaign_runtime_authorization_v1(
            authorization_id="X",
            bound_origin_main_sha=CANONICAL_BASE_SHA,
            execution_idempotency_key="k",
            owner_identity="o",
            decision_identity="d",
            earliest_valid_utc=EVAL_TIME,
            expires_at_utc=EVAL_TIME + timedelta(hours=1),
            allow_issuance=False,
        )


def test_issuance_rejects_wrong_bindings() -> None:
    wrong_base = _issued_auth(bound_origin_main_sha="0" * 40)
    reasons = verify_issued_runtime_authorization_bindings_v1(
        wrong_base,
        repo_root=REPO_ROOT,
        expected_bound_origin_main_sha=CANONICAL_BASE_SHA,
    )
    assert "BOUND_ORIGIN_MAIN_SHA_MISMATCH" in reasons

    wrong_supplier = _issued_auth(real_md_supplier_id="OTHER")
    assert "REAL_MD_SUPPLIER_BINDING_MISMATCH" in verify_issued_runtime_authorization_bindings_v1(
        wrong_supplier, repo_root=REPO_ROOT
    )

    wrong_campaign = _issued_auth(campaign_id="other")
    assert "CAMPAIGN_ID_MISMATCH" in verify_issued_runtime_authorization_bindings_v1(
        wrong_campaign, repo_root=REPO_ROOT
    )

    bad_caps = _issued_auth(authorized_capabilities=list(AUTHORIZED_CAPABILITIES_V1[:-1]))
    assert "AUTHORIZED_CAPABILITIES_INCOMPLETE" in verify_issued_runtime_authorization_bindings_v1(
        bad_caps, repo_root=REPO_ROOT
    )


def test_real_mode_requires_fresh_valid_issued_authorization(tmp_path: Path) -> None:
    template = build_runtime_authorization_template_v1(
        authorization_id="TEMPLATE_ONLY",
        earliest_valid_utc=EVAL_TIME.isoformat().replace("+00:00", "Z"),
        expires_at_utc=(EVAL_TIME + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        execution_idempotency_key="template-key",
    )
    template["campaign_execution_authorized"] = True
    template["public_market_data_read_authorized"] = True
    template["durable_evidence_write_authorized"] = True
    template["authorization_digest"] = compute_runtime_authorization_digest(template)
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path, template)
    )
    assert result.orchestration_status == STATUS_ORCHESTRATION_DENIED
    assert any("ISSUANCE" in r for r in result.reason_codes)


def test_real_mode_requires_adapter_when_not_injected(tmp_path: Path) -> None:
    auth = _issued_auth()
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=auth,
            evaluation_time_utc=EVAL_TIME,
            repo_root=REPO_ROOT,
            execution_mode=F1M9OrchestrationExecutionModeV1.REAL_AUTHORIZED_CAMPAIGN_EXECUTION,
            real_campaign_root=tmp_path,
            expected_bound_origin_main_sha=CANONICAL_BASE_SHA,
        )
    )
    assert result.orchestration_status == STATUS_ORCHESTRATION_DENIED
    assert "REAL_PUBLIC_MD_ADAPTER_REQUIRED" in result.reason_codes


def test_real_happy_path_wiring(tmp_path: Path) -> None:
    auth = _issued_auth(execution_idempotency_key="real-happy-1")
    adapter = FakeRealPublicMdSessionAdapterV1()
    units = resolve_preregistered_session_work_units_v1(repo_root=REPO_ROOT)
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path, auth, adapter=adapter)
    )
    assert result.orchestration_status == STATUS_REAL_TERMINAL_VERDICT_PASS
    assert result.real_authorized_campaign_execution_path_proven is True
    assert result.authorized_campaign_execution_terminal_path_proven is False
    assert result.terminal_selection.get("outcome") == OUTCOME_SELECTED
    assert len(adapter.executed_session_ids) == len(units)
    provenance = json.loads((tmp_path / "source_provenance.json").read_text(encoding="utf-8"))
    assert provenance.get("real_authorized_campaign_execution_path") is True
    assert provenance.get("simulated_public_md_in_hermetic") is False
    binding = resolve_canonical_real_md_supplier_runtime_binding_v1(repo_root=REPO_ROOT)
    assert binding["real_md_supplier_id"] == REAL_MD_SUPPLIER_ID


def test_build_bind_only_cannot_execute_real(tmp_path: Path) -> None:
    auth = _issued_auth()
    bound = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=auth,
            evaluation_time_utc=EVAL_TIME,
            repo_root=REPO_ROOT,
        )
    )
    assert bound.orchestration_status == STATUS_BUILD_SLICE_BOUND_ONLY
    assert bound.real_authorized_campaign_execution_path_proven is False


def test_hermetic_terminal_cannot_masquerade_as_real(tmp_path: Path) -> None:
    from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
        build_runtime_authorization_template_v1,
        compute_runtime_authorization_digest,
    )

    body = build_runtime_authorization_template_v1(
        authorization_id="HERMETIC_AUTH",
        earliest_valid_utc=EVAL_TIME.isoformat().replace("+00:00", "Z"),
        expires_at_utc=(EVAL_TIME + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        execution_idempotency_key="hermetic-key",
    )
    body["campaign_execution_authorized"] = True
    body["public_market_data_read_authorized"] = True
    body["durable_evidence_write_authorized"] = True
    body["authorization_digest"] = compute_runtime_authorization_digest(body)
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=body,
            evaluation_time_utc=EVAL_TIME,
            repo_root=REPO_ROOT,
            hermetic_isolated_campaign_root=tmp_path,
            allow_hermetic_terminal_effects=True,
            public_md_session_fn=lambda **_: {"simulated": True},
        )
    )
    assert result.orchestration_status == STATUS_TERMINAL_VERDICT_PASS
    assert result.authorized_campaign_execution_terminal_path_proven is True
    assert result.real_authorized_campaign_execution_path_proven is False


def test_exactly_once_work_unit_and_consume(tmp_path: Path) -> None:
    auth = _issued_auth(execution_idempotency_key="real-once-1")
    first = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path, auth)
    )
    assert first.orchestration_status == STATUS_REAL_TERMINAL_VERDICT_PASS
    retry = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path, auth)
    )
    assert retry.orchestration_status == STATUS_ALREADY_COMPLETE_REPLAY
    assert retry.real_evidence_written is False


def test_work_unit_ledger_duplicate_denied(tmp_path: Path) -> None:
    record_work_unit_execution_v1(
        campaign_root=tmp_path,
        session_id="session_01",
        execution_identity="exec-1",
        allow_record=True,
    )
    with pytest.raises(WorkUnitExactlyOnceError, match="ALREADY_EXECUTED"):
        record_work_unit_execution_v1(
            campaign_root=tmp_path,
            session_id="session_01",
            execution_identity="exec-1",
            allow_record=True,
        )


def test_real_incomplete_and_replay_no_new_evidence(tmp_path: Path) -> None:
    auth = _issued_auth(execution_idempotency_key="real-incomplete-1")
    incomplete = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path, auth, real_force_incomplete=True)
    )
    assert incomplete.orchestration_status == STATUS_ORCHESTRATION_DENIED

    auth2 = _issued_auth(execution_idempotency_key="real-replay-1")
    done = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path / "complete", auth2)
    )
    assert done.orchestration_status == STATUS_REAL_TERMINAL_VERDICT_PASS
    replay_only = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path / "complete", auth2)
    )
    assert replay_only.real_evidence_written is False
    assert "REPLAY" in replay_only.orchestration_status or replay_only.reason_codes


def test_fake_adapter_forbidden_side_effect_denied(tmp_path: Path) -> None:
    from dataclasses import replace

    class BadAdapter(FakeRealPublicMdSessionAdapterV1):
        def execute_work_unit_v1(self, *, work_unit, authorization):  # type: ignore[no-untyped-def]
            row = super().execute_work_unit_v1(work_unit=work_unit, authorization=authorization)
            return replace(row, order_effect=True)

    auth = _issued_auth(execution_idempotency_key="real-bad-adapter-1")
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        _real_request(tmp_path, auth, adapter=BadAdapter())
    )
    assert result.orchestration_status == STATUS_ORCHESTRATION_DENIED
    assert "FORBIDDEN_SIDE_EFFECT" in result.reason_codes[0]


def test_enablement_closure() -> None:
    assert prove_f1_m9_real_prospective_campaign_execution_enablement_v1(repo_root=REPO_ROOT)
