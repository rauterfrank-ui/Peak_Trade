"""Tests for M9-S1 operator-authorized max-age parameter research and selection boundary v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.governance.m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1 import (
    ENFORCEMENT_ENABLED,
    EXTERNAL_EFFECT_AUTHORIZED,
    NUMERIC_MAX_AGE_DECIDED,
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
    SELECTION_RESULT_UNRESOLVED,
    SELECTION_RULE_STATUS_NO_DETERMINISTIC_POINT,
    STATUS_AUTHORIZED_RESEARCH,
    STATUS_DENIED,
    TRADING_DECISION_AUTHORITY_UNCHANGED,
    build_owner_m9_s1_research_authorization_input_v1,
    evaluate_m9_s1_operator_research_authorization_v1,
    load_committed_owner_m9_s1_research_authorization_input_v1,
    run_m9_s1_operator_authorized_parameter_research_and_selection_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED as POLICY_ENFORCEMENT,
    NUMERIC_MAX_AGE_DECIDED as POLICY_DECIDED,
    resolve_canonical_volatility_max_age_policy_for_evaluation_v1,
)
from tests.research.test_canonical_volatility_numeric_max_age_parameter_research_execution_v1 import (
    _fixture_records,
)

BASE_SHA = "798bb481c60f619cec34ee8f408626725921e544"


def _owner_input() -> Any:
    return build_owner_m9_s1_research_authorization_input_v1(bound_origin_main_sha=BASE_SHA)


def test_committed_owner_input_digest_valid() -> None:
    load_committed_owner_m9_s1_research_authorization_input_v1()


def test_missing_owner_authorization_denied() -> None:
    result = evaluate_m9_s1_operator_research_authorization_v1(
        owner_authorization_input=None,
        repository_sha=BASE_SHA,
    )
    assert result.authorization_status == STATUS_DENIED
    assert "OWNER_AUTHORIZATION_INPUT_REQUIRED" in result.reason_codes


def test_owner_authorization_digest_mismatch_denied() -> None:
    owner = _owner_input()
    bad = type(owner)(
        owner_authorization_record=owner.owner_authorization_record,
        owner_authorization_record_digest="0" * 64,
    )
    result = evaluate_m9_s1_operator_research_authorization_v1(
        owner_authorization_input=bad,
        repository_sha=BASE_SHA,
    )
    assert result.authorization_status == STATUS_DENIED
    assert "OWNER_AUTHORIZATION_DIGEST_MISMATCH" in result.reason_codes


def test_authorized_operator_research_input() -> None:
    result = evaluate_m9_s1_operator_research_authorization_v1(
        owner_authorization_input=_owner_input(),
        repository_sha=BASE_SHA,
    )
    assert result.authorization_status == STATUS_AUTHORIZED_RESEARCH
    assert result.numeric_max_age_decided is False
    assert result.enforcement_enabled is False
    assert result.external_effect_authorized is False


def test_full_pipeline_selection_unresolved_and_lineage(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = tmp_path / "m9_s1_out"
    package1 = run_m9_s1_operator_authorized_parameter_research_and_selection_v1(
        repo_root=repo_root,
        owner_authorization_input=_owner_input(),
        output_root=out,
        records=_fixture_records(),
        repository_sha=BASE_SHA,
        created_at_utc="2026-09-20T12:00:00Z",
    )
    package2 = run_m9_s1_operator_authorized_parameter_research_and_selection_v1(
        repo_root=repo_root,
        owner_authorization_input=_owner_input(),
        output_root=tmp_path / "m9_s1_out_replay",
        records=_fixture_records(),
        repository_sha=BASE_SHA,
        created_at_utc="2026-09-20T12:00:00Z",
    )

    assert package1["selection_result"] == SELECTION_RESULT_UNRESOLVED
    assert package1["selection_rule_status"] == SELECTION_RULE_STATUS_NO_DETERMINISTIC_POINT
    assert package1["numeric_max_age_decided"] is False
    assert package1["enforcement_enabled"] is False
    assert package1["external_effect_authorized"] is False
    assert package1["trading_decision_authority_unchanged"] is True

    boundary = package1["selection_boundary"]
    assert boundary["candidate_set"] == list(OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS)
    assert boundary["proposed_candidate_max_age_seconds"] is None
    assert boundary["proposed_numeric_max_age_seconds"] is None

    assert package1["package_digest"] == package2["package_digest"]
    assert (
        package1["selection_boundary"]["selection_boundary_digest"]
        == package2["selection_boundary"]["selection_boundary_digest"]
    )
    assert (
        package1["selection_boundary"]["deterministic_comparison_digest"]
        == package2["selection_boundary"]["deterministic_comparison_digest"]
    )

    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1()
    assert policy.enforcement_enabled is POLICY_ENFORCEMENT is False
    assert policy.numeric_max_age_seconds is None
    assert POLICY_DECIDED is False


def test_denied_pipeline_writes_failure_evidence(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = tmp_path / "denied"
    result = run_m9_s1_operator_authorized_parameter_research_and_selection_v1(
        repo_root=repo_root,
        owner_authorization_input=None,
        output_root=out,
        records=_fixture_records(),
        repository_sha=BASE_SHA,
    )
    assert result["research_execution_status"] == "NOT_STARTED"
    assert (out / "m9_s1_authorization_denied.json").is_file()


def test_invariants_module_constants() -> None:
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert TRADING_DECISION_AUTHORITY_UNCHANGED is True
