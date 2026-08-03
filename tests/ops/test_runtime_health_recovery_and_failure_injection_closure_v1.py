"""Deterministic contract tests for CAPABILITY_O6."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.component_health_v1 import (
    ComponentHealthErrorV1,
    assert_non_healthy_cannot_render_green_v1,
    assert_process_alive_alone_insufficient_v1,
    build_component_health_report_v1,
    classify_component_health_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.composite_health_v1 import (
    derive_composite_health_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    BOUNDED_FAILURE_CLASSES,
    CAPABILITY_ID,
    COMPONENT_DASHBOARD_BACKEND,
    COMPONENT_MARKET_DATA,
    COMPONENT_PERSISTENCE,
    COMPONENT_READ_MODEL_PROJECTOR,
    COMPONENT_RUNTIME,
    COMPONENT_SUPERVISOR,
    COMPOSITE_HEALTH_KEYS,
    HEALTH_COMPONENTS,
    HEALTH_DEGRADED,
    HEALTH_DISCONNECTED,
    HEALTH_HEALTHY,
    HEALTH_MISSING_SOURCE,
    HEALTH_STALE,
    RECOVERY_INVARIANTS,
    REQUIRED_HEALTH_FIELDS,
    SAFETY_INVARIANTS,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.failure_injection_v1 import (
    run_failure_injection_matrix_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.failure_taxonomy_v1 import (
    classify_failure_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.idempotency_proofs_v1 import (
    prove_no_duplicate_bar_finalization_v1,
    prove_no_duplicate_market_observation_v1,
    prove_no_duplicate_read_model_commit_v1,
    prove_recovery_idempotency_bundle_v1,
    prove_stale_dashboard_cannot_be_healthy_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
    PersistedRuntimeCursorV1,
    RecoveryErrorV1,
    assert_single_writer_enforced_v1,
    bounded_retry_policy_v1,
    fence_session_before_recovery_v1,
    recover_from_persisted_active_state_v1,
    reconcile_persisted_state_before_resume_v1,
    resume_after_reconciliation_v1,
    write_persisted_cursor_v1,
)


def _report(
    component: str,
    *,
    now: float = 1_703_000_000.0,
    process_alive: bool = True,
    heartbeat_time: float | None = 1_703_000_000.0,
    last_success_time: float | None = 1_703_000_000.0,
    disconnected: bool = False,
    source_present: bool = True,
    error_class: str | None = None,
):
    return build_component_health_report_v1(
        component=component,
        process_alive=process_alive,
        heartbeat_time=heartbeat_time,
        last_success_time=last_success_time,
        last_error_time=None if error_class is None else now,
        error_class=error_class,
        restart_count=0,
        input_lag=0.0,
        output_lag=0.0,
        state_commit_position=1,
        evidence_cursor=1,
        session_id="o6-test",
        repository_sha="f" * 40,
        config_digest="cfg-test",
        now_unix=now,
        disconnected=disconnected,
        source_present=source_present,
    )


def test_capability_constants_and_safety() -> None:
    assert CAPABILITY_ID.endswith("_V1")
    assert SAFETY_INVARIANTS["CORE_LOGIC_CHANGE_ALLOWED"] is False
    assert SAFETY_INVARIANTS["HEALTH_HAS_ALPHA_AUTHORITY"] is False
    assert SAFETY_INVARIANTS["ORDERS_ALLOWED"] is False
    assert SAFETY_INVARIANTS["PROCESS_ALIVE_ALONE_INSUFFICIENT"] is True
    assert RECOVERY_INVARIANTS["RECOVERY_HAS_ALPHA_AUTHORITY"] is False
    assert RECOVERY_INVARIANTS["SESSION_FENCED_BEFORE_RECOVERY"] is True
    assert set(HEALTH_COMPONENTS) == {
        COMPONENT_SUPERVISOR,
        COMPONENT_MARKET_DATA,
        COMPONENT_RUNTIME,
        COMPONENT_PERSISTENCE,
        COMPONENT_READ_MODEL_PROJECTOR,
        COMPONENT_DASHBOARD_BACKEND,
    }
    assert len(REQUIRED_HEALTH_FIELDS) == 13
    assert len(COMPOSITE_HEALTH_KEYS) == 7
    assert len(BOUNDED_FAILURE_CLASSES) == 17


def test_process_alive_alone_insufficient_for_healthy() -> None:
    proof = assert_process_alive_alone_insufficient_v1(
        process_alive=True,
        heartbeat_time=None,
        last_success_time=None,
        now_unix=1.0,
    )
    assert proof["classification"] != HEALTH_HEALTHY
    assert (
        classify_component_health_v1(
            process_alive=True,
            heartbeat_time=None,
            last_success_time=1.0,
            now_unix=1.0,
        )
        == HEALTH_DEGRADED
    )


def test_component_health_fields_and_classifications() -> None:
    healthy = _report(COMPONENT_RUNTIME)
    assert healthy.classification == HEALTH_HEALTHY
    payload = healthy.to_dict()
    for field in REQUIRED_HEALTH_FIELDS:
        assert field in payload

    assert (
        _report(COMPONENT_MARKET_DATA, source_present=False).classification == HEALTH_MISSING_SOURCE
    )
    assert _report(COMPONENT_MARKET_DATA, disconnected=True).classification == HEALTH_DISCONNECTED
    assert (
        _report(
            COMPONENT_SUPERVISOR,
            heartbeat_time=1_703_000_000.0 - 120.0,
            last_success_time=1_703_000_000.0 - 120.0,
        ).classification
        == HEALTH_STALE
    )


def test_stale_cannot_render_healthy() -> None:
    assert_non_healthy_cannot_render_green_v1(
        classification=HEALTH_STALE,
        render_as_healthy=False,
    )
    with pytest.raises(ComponentHealthErrorV1):
        assert_non_healthy_cannot_render_green_v1(
            classification=HEALTH_DISCONNECTED,
            render_as_healthy=True,
        )


def test_composite_health_derivation_and_stale_dashboard_block() -> None:
    now = 1_703_000_000.0
    reports = {c: _report(c, now=now) for c in HEALTH_COMPONENTS}
    composite = derive_composite_health_v1(reports)
    assert composite["may_render_green"] is True
    assert composite["composite"]["END_TO_END_DATA_HEALTH"] == HEALTH_HEALTHY

    reports[COMPONENT_DASHBOARD_BACKEND] = _report(
        COMPONENT_DASHBOARD_BACKEND,
        now=now,
        process_alive=False,
        heartbeat_time=now - 1.0,
        last_success_time=now - 1.0,
    )
    degraded = derive_composite_health_v1(reports)
    assert degraded["may_render_green"] is False
    assert degraded["composite"]["DASHBOARD_BACKEND_HEALTH"] == HEALTH_DISCONNECTED
    assert degraded["composite"]["END_TO_END_DATA_HEALTH"] != HEALTH_HEALTHY


def test_failure_taxonomy_structured_fields() -> None:
    record = classify_failure_v1(
        root_cause_class="HEARTBEAT_LOSS",
        reason_code="HB_STALE",
        affected_component=COMPONENT_SUPERVISOR,
        session_id="s1",
        first_failure_time=10.0,
        last_good_time=9.0,
        data_loss_possible=False,
        state_divergence_possible=True,
        automatic_recovery_allowed=True,
        owner_action_required=False,
        recovery_eligibility="ELIGIBLE",
    )
    payload = record.to_dict()
    assert payload["root_cause_class"] == "HEARTBEAT_LOSS"
    assert payload["owner_action_required"] is False
    assert payload["recovery_eligibility"] == "ELIGIBLE"


def test_fence_reconcile_resume_order(tmp_path: Path) -> None:
    cursor = PersistedRuntimeCursorV1(
        session_id="o6-rec",
        repository_sha="a" * 40,
        config_digest="cfg",
        market_observation_epoch=2,
    )
    with pytest.raises(RecoveryErrorV1):
        reconcile_persisted_state_before_resume_v1(
            cursor,
            expected_session_id="o6-rec",
            expected_repository_sha="a" * 40,
            expected_config_digest="cfg",
        )
    fence_session_before_recovery_v1(cursor)
    with pytest.raises(RecoveryErrorV1):
        resume_after_reconciliation_v1(cursor)
    reconcile_persisted_state_before_resume_v1(
        cursor,
        expected_session_id="o6-rec",
        expected_repository_sha="a" * 40,
        expected_config_digest="cfg",
    )
    resume_after_reconciliation_v1(cursor)
    assert cursor.processing_allowed is True

    path = tmp_path / "cursor.json"
    write_persisted_cursor_v1(
        path,
        PersistedRuntimeCursorV1(
            session_id="o6-rec2",
            repository_sha="a" * 40,
            config_digest="cfg",
            processing_allowed=True,
        ),
    )
    recovered = recover_from_persisted_active_state_v1(
        path,
        expected_session_id="o6-rec2",
        expected_repository_sha="a" * 40,
        expected_config_digest="cfg",
    )
    assert recovered["session_fenced_before_recovery"] is True
    assert recovered["reconciliation_before_resume"] is True


def test_bounded_retry_and_single_writer(tmp_path: Path) -> None:
    allowed = bounded_retry_policy_v1(attempt=0, retry_limit=3, automatic_recovery_allowed=True)
    assert allowed["retry_allowed"] is True
    exhausted = bounded_retry_policy_v1(attempt=3, retry_limit=3, automatic_recovery_allowed=True)
    assert exhausted["retry_allowed"] is False
    assert exhausted["owner_action_required"] is True
    proof = assert_single_writer_enforced_v1(tmp_path / "reg", "sess")
    assert proof["single_writer_enforced"] is True


def test_idempotency_proofs() -> None:
    assert prove_no_duplicate_market_observation_v1()["ok"] is True
    assert prove_no_duplicate_bar_finalization_v1()["ok"] is True
    assert prove_no_duplicate_read_model_commit_v1()["ok"] is True
    assert prove_stale_dashboard_cannot_be_healthy_v1()["ok"] is True
    assert prove_recovery_idempotency_bundle_v1()["ok"] is True


def test_failure_injection_matrix_offline(tmp_path: Path) -> None:
    matrix = run_failure_injection_matrix_v1(tmp_path / "fi")
    assert matrix["ok"] is True
    assert matrix["FAILURE_INJECTION_PROVEN"] is True
    assert matrix["network_session_started"] is False
    assert matrix["authorization_consumed"] is False
    assert matrix["orders_submitted"] is False
    assert set(matrix["results"]) == set(BOUNDED_FAILURE_CLASSES)
    for name in BOUNDED_FAILURE_CLASSES:
        assert matrix["results"][name]["ok"] is True, name
        failure = matrix["results"][name]["failure"]
        assert failure["root_cause_class"] == name
        assert "last_good_time" in failure
        assert "data_loss_possible" in failure
        assert "state_divergence_possible" in failure
        assert "recovery_eligibility" in failure
        assert "owner_action_required" in failure


def test_path_sanitization_repo_relative_and_external_temp(tmp_path: Path) -> None:
    from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.path_sanitization_v1 import (
        contains_absolute_local_path_v1,
        sanitize_evidence_payload_v1,
        sanitize_path_value_v1,
        sanitize_pytest_output_v1,
    )

    repo = tmp_path / "repo"
    (repo / "docs" / "evidence").mkdir(parents=True)
    internal = repo / "docs" / "evidence" / "capability_o6" / "session.json"
    internal.parent.mkdir(parents=True, exist_ok=True)
    internal.write_text("{}\n", encoding="utf-8")

    relative = sanitize_path_value_v1(str(internal), repository_root=repo)
    assert relative == "docs/evidence/capability_o6/session.json"
    assert not relative.startswith("/")
    assert "Users" not in relative

    external = sanitize_path_value_v1(
        "/var/folders/xx/tmp_o6_harness/cursor.json",
        repository_root=repo,
    )
    assert external.startswith("o6://external-temp/")
    assert not contains_absolute_local_path_v1(external)

    nested = sanitize_evidence_payload_v1(
        {
            "detail": f"tmp={internal}",
            "session": {"config_path": str(internal), "log_root": "/tmp/o6-log"},
            "ok": True,
        },
        repository_root=repo,
    )
    assert nested["ok"] is True
    assert nested["session"]["config_path"] == "docs/evidence/capability_o6/session.json"
    assert nested["session"]["log_root"].startswith("o6://external-temp/")
    assert "tmp=" in nested["detail"]
    assert not contains_absolute_local_path_v1(json.dumps(nested))

    pytest_raw = (
        "============================= test session starts ==============================\n"
        f"rootdir: {repo}\n"
        "collected 10 items\n"
        "10 passed in 0.17s\n"
    )
    hygienic = sanitize_pytest_output_v1(pytest_raw, repository_root=repo)
    assert "rootdir: <REPOSITORY_ROOT>" in hygienic
    assert "10 passed" in hygienic
    assert not contains_absolute_local_path_v1(hygienic)


def test_failure_injection_sanitized_for_publication(tmp_path: Path) -> None:
    import json as _json

    from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.path_sanitization_v1 import (
        contains_absolute_local_path_v1,
    )

    repo = tmp_path / "repo"
    fi_root = repo / "docs" / "evidence" / "capability_o6" / "_tmp_failure_injection"
    fi_root.mkdir(parents=True)
    matrix = run_failure_injection_matrix_v1(fi_root, repository_root=repo)
    assert matrix["ok"] is True
    assert matrix["FAILURE_INJECTION_PROVEN"] is True
    blob = _json.dumps(matrix, sort_keys=True)
    assert not contains_absolute_local_path_v1(blob)
    detail = matrix["results"]["GRACEFUL_SHUTDOWN_TIMEOUT"]["failure"]["detail"]
    assert detail.startswith("tmp=o6://external-temp/")
    stale_session = matrix["results"]["STALE_PID_OR_SESSION_REGISTRY"]["evidence"]["recover"][
        "session"
    ]
    for key in ("config_path", "evidence_root", "heartbeat_path", "log_root", "state_root"):
        value = str(stale_session[key])
        assert not value.startswith("/Users/")
        assert not value.startswith("/private/")
        assert not value.startswith("/var/folders/")
        assert not value.startswith("/tmp/")
