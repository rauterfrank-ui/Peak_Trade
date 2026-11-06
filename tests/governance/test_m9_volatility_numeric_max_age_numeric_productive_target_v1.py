"""Governance tests for M9 numeric productive target + ratified threshold capability."""

from __future__ import annotations

from typing import Any

import pytest

from src.experiments.canonical_optimizable_envelope_v1 import (
    ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
    build_authorized_surface_registry_v1,
)
from src.experiments.canonical_optimization_universe_v1 import (
    build_optimization_universe_capability_registry_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    PRODUCTIVE_TARGET_ID,
    PRODUCTIVE_TARGET_VERSION,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
    ProductiveApplyAuthorizationStatusV1,
    ProductiveNumericMaxAgePolicyAdmissionV1,
    authorized_productive_target_ids_v1,
    build_productive_target_contract_v1,
    build_productive_target_registry_snapshot_v1,
    direct_productive_write_possible_v1,
    validate_policy_admission_request_v1,
    validate_productive_target_id_v1,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID,
    CONCRETE_THRESHOLD_VALUE_RATIFIED,
    ENFORCEMENT_ENABLED,
    ThresholdValueAuthorizationStatusV1,
    assert_ratified_threshold_capability_non_goals_v1,
    build_ratified_threshold_capability_identity_v1,
    materialize_ratified_numeric_max_age_threshold_value_v1,
    validate_numeric_max_age_seconds_domain_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    DISPOSITION_PROPOSAL_ONLY,
    OptimizationProposalGovernanceAdmissionRequestV1,
    direct_productive_write_possible_v1 as optimization_direct_write,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED as POLICY_ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
    THRESHOLD_STATUS_UNRESOLVED,
    build_ratified_numeric_threshold_policy_contract_v1,
    build_ratified_unresolved_max_age_policy_contract_v1,
    resolve_canonical_volatility_max_age_policy_for_evaluation_v1,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)


def _valid_digest() -> str:
    return "a" * 64


def test_productive_target_registry_exactly_one_target() -> None:
    targets = authorized_productive_target_ids_v1()
    assert targets == frozenset({PRODUCTIVE_TARGET_ID})
    snap = build_productive_target_registry_snapshot_v1()
    assert snap["authorized_productive_target_count"] == 1
    assert snap["zero_authorized_productive_targets"] is False
    assert ZERO_AUTHORIZED_PRODUCTIVE_TARGETS is False


def test_universe_and_envelope_registry_reflect_target() -> None:
    universe = build_optimization_universe_capability_registry_v1()
    assert PRODUCTIVE_TARGET_ID in universe["authorized_productive_targets"]
    assert universe["zero_authorized_productive_targets"] is False
    envelope = build_authorized_surface_registry_v1()
    assert PRODUCTIVE_TARGET_ID in envelope["authorized_productive_target_ids"]


def test_target_contract_semantics() -> None:
    contract = build_productive_target_contract_v1()
    assert contract["optimization_surface_id"] == OPTIMIZATION_SURFACE_ID
    assert contract["source_candidate_parameter"] == SOURCE_CANDIDATE_PARAMETER
    assert contract["target_policy_parameter"] == TARGET_POLICY_PARAMETER
    assert contract["productive_target_id"] == PRODUCTIVE_TARGET_ID


def test_ratified_threshold_capability_non_goals() -> None:
    identity = build_ratified_threshold_capability_identity_v1()
    assert identity["capability_id"] == CAPABILITY_ID
    non_goals = assert_ratified_threshold_capability_non_goals_v1()
    assert non_goals["concrete_threshold_value_ratified"] is False
    assert non_goals["enforcement_enabled"] is False
    assert CONCRETE_THRESHOLD_VALUE_RATIFIED is False
    assert ENFORCEMENT_ENABLED is False


def test_domain_validation_matches_m9_bounds() -> None:
    ok, _ = validate_numeric_max_age_seconds_domain_v1(300)
    assert ok is True
    bad, reason = validate_numeric_max_age_seconds_domain_v1(301)
    assert bad is False
    assert reason == "NUMERIC_OUT_OF_DISCRETE_DOMAIN"


def test_unresolved_policy_default_unchanged() -> None:
    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1(None)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert policy.numeric_max_age_seconds is None
    assert policy.enforcement_enabled is False
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert POLICY_ENFORCEMENT_ENABLED is False


def test_admission_missing_or_invalid_stays_unresolved(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    admission = ProductiveNumericMaxAgePolicyAdmissionV1(
        productive_target_id=PRODUCTIVE_TARGET_ID,
        productive_target_version=PRODUCTIVE_TARGET_VERSION,
        ratified_threshold_capability_id=CAPABILITY_ID,
        ratified_threshold_capability_version="m9_volatility_numeric_max_age_ratified_threshold_capability/v1",
        threshold_value_authorization_status="NONE",
        threshold_value_authorization_digest=None,
        threshold_numeric_max_age_seconds=300.0,
        productive_apply_authorization_status=ProductiveApplyAuthorizationStatusV1.NONE.value,
        productive_apply_authorization_digest=None,
        optimization_ingress_digest=str(ingress["ingress_digest"]),
        optimization_candidate_ref=str(ingress["candidate_ref"]),
        governance_review_admission_status=ADMISSION_ADMITTED,
    )
    ok, reasons = validate_policy_admission_request_v1(admission)
    assert ok is False
    assert "OPTIMIZATION_INGRESS_DIGEST_FORBIDDEN" in reasons
    assert "GOVERNANCE_REVIEW_ADMISSION_NOT_PRODUCTIVE_AUTHORIZATION" in reasons
    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1(admission)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert policy.numeric_max_age_seconds is None


def test_governance_review_admission_alone_cannot_change_policy(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert result.admission_status == ADMISSION_ADMITTED
    assert ingress["disposition"] == DISPOSITION_PROPOSAL_ONLY
    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1(None)
    assert policy == build_ratified_unresolved_max_age_policy_contract_v1()


def test_fully_authorized_admission_builds_non_enforcing_ratified_policy() -> None:
    admission = ProductiveNumericMaxAgePolicyAdmissionV1(
        productive_target_id=PRODUCTIVE_TARGET_ID,
        productive_target_version=PRODUCTIVE_TARGET_VERSION,
        ratified_threshold_capability_id=CAPABILITY_ID,
        ratified_threshold_capability_version="m9_volatility_numeric_max_age_ratified_threshold_capability/v1",
        threshold_value_authorization_status=ThresholdValueAuthorizationStatusV1.AUTHORIZED.value,
        threshold_value_authorization_digest=_valid_digest(),
        threshold_numeric_max_age_seconds=300.0,
        productive_apply_authorization_status=ProductiveApplyAuthorizationStatusV1.AUTHORIZED.value,
        productive_apply_authorization_digest=_valid_digest(),
    )
    ok, _ = validate_policy_admission_request_v1(admission)
    assert ok is True
    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1(admission)
    assert policy.threshold_status == THRESHOLD_STATUS_RATIFIED_NUMERIC
    assert policy.numeric_max_age_seconds == 300.0
    assert policy.enforcement_enabled is False
    threshold = materialize_ratified_numeric_max_age_threshold_value_v1(
        numeric_max_age_seconds=300.0,
        authorization_status=ThresholdValueAuthorizationStatusV1.AUTHORIZED,
        authorization_digest=_valid_digest(),
    )
    assert threshold.threshold_status == THRESHOLD_STATUS_RATIFIED_NUMERIC


def test_ratified_policy_builder_rejects_enforcement() -> None:
    policy = build_ratified_numeric_threshold_policy_contract_v1(numeric_max_age_seconds=120.0)
    assert policy.enforcement_enabled is False


def test_wrong_target_denied() -> None:
    ok, reason = validate_productive_target_id_v1(
        "peak_trade.governance.productive_target.other/v1"
    )
    assert ok is False
    assert reason == "PRODUCTIVE_TARGET_ID_NOT_AUTHORIZED"


def test_direct_productive_write_impossible() -> None:
    assert direct_productive_write_possible_v1() is False
    assert optimization_direct_write() is False


def test_threshold_capability_cannot_materialize_without_authorization() -> None:
    with pytest.raises(Exception):
        materialize_ratified_numeric_max_age_threshold_value_v1(
            numeric_max_age_seconds=300.0,
            authorization_status=ThresholdValueAuthorizationStatusV1.NONE,
            authorization_digest=_valid_digest(),
        )
