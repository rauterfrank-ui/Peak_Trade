"""Tests for governed productive configuration v1 (M10 Slice B)."""

from __future__ import annotations

from typing import Any

import pytest

from src.governance.explicit_productive_authorization_v1 import (
    STATUS_AUTHORIZED_BOUNDARY,
    STATUS_DENIED,
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    ExplicitProductiveAuthorizationResultV1,
    build_owner_explicit_productive_authorization_input_v1,
    compute_candidate_parameter_value_digest_v1,
    evaluate_explicit_productive_authorization_v1,
    verify_authorization_record_digest_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    DISPOSITION_CONFIGURATION_ONLY,
    GLOBAL_THRESHOLD_VALUE_RATIFIED,
    PRODUCTIVE_TARGET_ID,
    SOURCE_CANDIDATE_PARAMETER,
    STATUS_MATERIALIZED,
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
    optimization_can_materialize_configuration_v1,
    policy_mutation_possible_v1,
    runtime_apply_possible_v1,
    verify_configuration_record_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    TARGET_POLICY_PARAMETER,
    TARGET_UNIT,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    THRESHOLD_STATUS_UNRESOLVED,
    resolve_canonical_volatility_max_age_policy_for_evaluation_v1,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)


def _authorized_chain(tmp_path: Any):
    ingress = _ingress_for_m9(tmp_path)
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    authorization = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    return ingress, authorization


def _materialized(tmp_path: Any):
    ingress, authorization = _authorized_chain(tmp_path)
    config = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    return ingress, authorization, config


def test_positive_materialization_exact_value_and_lineage(tmp_path: Any) -> None:
    ingress, authorization, config = _materialized(tmp_path)
    assert config.configuration_status == STATUS_MATERIALIZED
    assert config.configuration_disposition == DISPOSITION_CONFIGURATION_ONLY
    assert config.configuration_record is not None
    record = config.configuration_record
    assert verify_configuration_record_digest_v1(record)
    candidate_seconds = float(ingress["parameter_config_delta"]["max_age_seconds"])
    assert record["authorized_candidate_max_age_seconds"] == candidate_seconds
    assert record["numeric_max_age_seconds"] == candidate_seconds
    assert record["exact_value_preservation"] is True
    assert record["global_threshold_value_ratified"] is GLOBAL_THRESHOLD_VALUE_RATIFIED is False
    assert record["consumer_bound"] is False
    assert record["runtime_applied"] is False
    assert record["enforcement_enabled"] is False
    assert record["authorization_digest"] == authorization.authorization_digest
    assert record[
        "candidate_parameter_value_digest"
    ] == compute_candidate_parameter_value_digest_v1(ingress["parameter_config_delta"])
    assert authorization.authorization_record is not None
    assert verify_authorization_record_digest_v1(authorization.authorization_record)


def test_candidate_without_authorization_denied(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    denied = ExplicitProductiveAuthorizationResultV1(
        authorization_status=STATUS_DENIED,
        reason_codes=("DENIED",),
        authorization_disposition="AUTHORIZATION_ONLY",
        authorized_for_productive_configuration_boundary=False,
        authorization_digest=None,
        authorization_record=None,
        ingress_digest=str(ingress["ingress_digest"]),
    )
    result = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=denied,
            ingress=ingress,
        )
    )
    assert result.configuration_status == STATUS_DENIED


def test_ingress_without_authorization_denied(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    result = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=ExplicitProductiveAuthorizationResultV1(
                authorization_status=STATUS_DENIED,
                reason_codes=("NO_AUTH",),
                authorization_disposition="AUTHORIZATION_ONLY",
                authorized_for_productive_configuration_boundary=False,
                authorization_digest=None,
                authorization_record=None,
                ingress_digest=str(ingress["ingress_digest"]),
            ),
            ingress=ingress,
        )
    )
    assert result.configuration_status == STATUS_DENIED


def test_admission_alone_denied(tmp_path: Any) -> None:
    ingress, admission = (
        _ingress_for_m9(tmp_path),
        evaluate_optimization_proposal_governance_admission_v1(
            OptimizationProposalGovernanceAdmissionRequestV1(ingress=_ingress_for_m9(tmp_path))
        ),
    )
    assert admission.admission_status == ADMISSION_ADMITTED
    result = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=ExplicitProductiveAuthorizationResultV1(
                authorization_status=STATUS_DENIED,
                reason_codes=("NO_OWNER",),
                authorization_disposition="AUTHORIZATION_ONLY",
                authorized_for_productive_configuration_boundary=False,
                authorization_digest=None,
                authorization_record=None,
                ingress_digest=str(ingress["ingress_digest"]),
            ),
            ingress=ingress,
        )
    )
    assert result.configuration_status == STATUS_DENIED


def test_authorization_digest_mismatch_denied(tmp_path: Any) -> None:
    _, authorization, _ = _materialized(tmp_path)
    assert authorization.authorization_record is not None
    tampered = dict(authorization.authorization_record)
    tampered["candidate_ref"] = "tampered"
    bad = ExplicitProductiveAuthorizationResultV1(
        authorization_status=STATUS_AUTHORIZED_BOUNDARY,
        reason_codes=authorization.reason_codes,
        authorization_disposition=authorization.authorization_disposition,
        authorized_for_productive_configuration_boundary=True,
        authorization_digest=str(tampered.get("authorization_digest")),
        authorization_record=type(authorization.authorization_record)(tampered),
        ingress_digest=authorization.ingress_digest,
    )
    result = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(authorization=bad)
    )
    assert "AUTHORIZATION_DIGEST_MISMATCH" in result.reason_codes


def test_ingress_numeric_mismatch_denied(tmp_path: Any) -> None:
    ingress, authorization = _authorized_chain(tmp_path)
    bad_ingress = dict(ingress)
    bad_ingress["parameter_config_delta"] = {"max_age_seconds": 120}
    result = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=bad_ingress,
        )
    )
    assert "INGRESS_AUTHORIZATION_NUMERIC_MISMATCH" in result.reason_codes


def test_clamped_value_denied_via_invalid_domain(tmp_path: Any) -> None:
    ingress, authorization = _authorized_chain(tmp_path)
    assert authorization.authorization_record is not None
    tampered = dict(authorization.authorization_record)
    tampered["parameter_config_delta"] = {"max_age_seconds": 301}
    tampered["candidate_parameter_value_digest"] = compute_candidate_parameter_value_digest_v1(
        tampered["parameter_config_delta"]
    )
    body = {key: value for key, value in tampered.items() if key != "authorization_digest"}
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    tampered["authorization_digest"] = compute_content_sha256(body)
    bad = ExplicitProductiveAuthorizationResultV1(
        authorization_status=STATUS_AUTHORIZED_BOUNDARY,
        reason_codes=authorization.reason_codes,
        authorization_disposition=authorization.authorization_disposition,
        authorized_for_productive_configuration_boundary=True,
        authorization_digest=str(tampered["authorization_digest"]),
        authorization_record=type(authorization.authorization_record)(tampered),
        ingress_digest=authorization.ingress_digest,
    )
    result = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(authorization=bad, ingress=ingress)
    )
    assert "NUMERIC_OUT_OF_DISCRETE_DOMAIN" in result.reason_codes


def test_configuration_does_not_mutate_policy_or_enable_enforcement(tmp_path: Any) -> None:
    _materialized(tmp_path)
    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1(None)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False


def test_no_runtime_apply_or_optimization_materialization() -> None:
    assert runtime_apply_possible_v1() is False
    assert policy_mutation_possible_v1() is False
    assert optimization_can_materialize_configuration_v1() is False


def test_parameter_and_unit_fields_on_configuration(tmp_path: Any) -> None:
    _, _, config = _materialized(tmp_path)
    record = config.configuration_record
    assert record is not None
    assert record["source_candidate_parameter"] == SOURCE_CANDIDATE_PARAMETER
    assert record["target_policy_parameter"] == TARGET_POLICY_PARAMETER
    assert record["target_unit"] == TARGET_UNIT
    assert record["productive_target_id"] == PRODUCTIVE_TARGET_ID
