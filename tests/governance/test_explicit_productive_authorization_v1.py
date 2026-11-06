"""Tests for explicit productive authorization v1 (M10 Slice A)."""

from __future__ import annotations

from typing import Any

from src.governance.explicit_productive_authorization_v1 import (
    DISPOSITION_AUTHORIZATION_ONLY,
    PRODUCTIVE_TARGET_ID,
    SOURCE_CANDIDATE_PARAMETER,
    STATUS_AUTHORIZED_BOUNDARY,
    STATUS_DENIED,
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    build_owner_explicit_productive_authorization_input_v1,
    compute_candidate_parameter_value_digest_v1,
    compute_owner_authorization_record_digest_v1,
    direct_productive_write_possible_v1,
    evaluate_explicit_productive_authorization_v1,
    governed_productive_configuration_write_possible_v1,
    policy_mutation_possible_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    TARGET_POLICY_PARAMETER,
    TARGET_UNIT,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    ADMISSION_DENIED,
    DISPOSITION_PROPOSAL_ONLY,
    OptimizationProposalGovernanceAdmissionRequestV1,
    OptimizationProposalGovernanceAdmissionResultV1,
    direct_productive_write_possible_v1 as optimization_direct_write,
    evaluate_optimization_proposal_governance_admission_v1,
    project_optimization_ingress_to_config_patch_manifest_v1,
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


def _admitted(tmp_path: Any) -> tuple[Any, OptimizationProposalGovernanceAdmissionResultV1]:
    ingress = _ingress_for_m9(tmp_path)
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert admission.admission_status == ADMISSION_ADMITTED
    return ingress, admission


def _authorized(tmp_path: Any):
    ingress, admission = _admitted(tmp_path)
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    return ingress, admission, owner_input, result


def test_admitted_review_without_owner_authorization_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=None,
        )
    )
    assert result.authorization_status == STATUS_DENIED
    assert "OWNER_AUTHORIZATION_INPUT_REQUIRED" in result.reason_codes


def test_raw_ingress_without_admission_path_denied(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    denied_admission = OptimizationProposalGovernanceAdmissionResultV1(
        admission_status=ADMISSION_DENIED,
        reason_codes=("DENIED",),
        ingress_digest=str(ingress["ingress_digest"]),
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=denied_admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=None,
        )
    )
    assert result.authorization_status == STATUS_DENIED


def test_proposal_only_projection_alone_denied(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    manifest = project_optimization_ingress_to_config_patch_manifest_v1(ingress)
    assert manifest.patches[0].status.value == "PROPOSED"
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=OptimizationProposalGovernanceAdmissionResultV1(
                admission_status=ADMISSION_ADMITTED,
                reason_codes=("ADMITTED_FOR_GOVERNANCE_REVIEW_ONLY",),
                ingress_digest=str(ingress["ingress_digest"]),
                config_patch_manifest_projection=manifest,
            ),
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=None,
        )
    )
    assert result.authorization_status == STATUS_DENIED


def test_wrong_ingress_digest_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    bad_admission = OptimizationProposalGovernanceAdmissionResultV1(
        admission_status=ADMISSION_ADMITTED,
        reason_codes=admission.reason_codes,
        ingress_digest="b" * 64,
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=bad_admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    assert "ADMISSION_INGRESS_DIGEST_MISMATCH" in result.reason_codes


def test_wrong_surface_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    bad_ingress = dict(ingress)
    bad_ingress["optimization_surface_id"] = "OTHER_SURFACE"
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=bad_ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    assert result.authorization_status == STATUS_DENIED


def test_unregistered_target_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id="peak_trade.governance.productive_target.other/v1",
            owner_authorization_input=owner_input,
        )
    )
    assert "PRODUCTIVE_TARGET_ID_NOT_AUTHORIZED" in result.reason_codes


def test_wrong_parameter_mapping_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    bad_ingress = dict(ingress)
    bad_ingress["parameter_config_delta"] = {"wrong_param": 300}
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=bad_ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    assert "CANDIDATE_PARAMETER_MAPPING_MISMATCH" in result.reason_codes


def test_owner_binding_mismatch_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    tampered_record = dict(owner_input.owner_authorization_record)
    tampered_record["bound_target_unit"] = "MINUTES"
    bad_input = type(owner_input)(
        owner_authorization_record=tampered_record,
        owner_authorization_record_digest=compute_owner_authorization_record_digest_v1(
            tampered_record
        ),
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=bad_input,
        )
    )
    assert "OWNER_BINDING_MISMATCH:bound_target_unit" in result.reason_codes


def test_missing_provenance_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    bad_ingress = dict(ingress)
    bad_ingress.pop("optimization_provenance")
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=bad_ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    assert result.authorization_status == STATUS_DENIED


def test_positive_harness_requires_owner_input_and_ends_authorization_only(
    tmp_path: Any,
) -> None:
    ingress, admission, owner_input, result = _authorized(tmp_path)
    assert result.authorization_status == STATUS_AUTHORIZED_BOUNDARY
    assert result.authorization_disposition == DISPOSITION_AUTHORIZATION_ONLY
    assert result.authorized_for_productive_configuration_boundary is True
    assert result.authorization_record is not None
    record = result.authorization_record
    assert record["threshold_value_ratified"] is False
    assert record["candidate_value_applied"] is False
    assert record["enforcement_enabled"] is False
    assert record["disposition"] == DISPOSITION_PROPOSAL_ONLY
    assert record["source_candidate_parameter"] == SOURCE_CANDIDATE_PARAMETER
    assert record["target_policy_parameter"] == TARGET_POLICY_PARAMETER
    assert record["target_unit"] == TARGET_UNIT
    assert record["ratified_threshold_capability_id"] == CAPABILITY_ID
    assert record["owner_authorization_record_digest"] == (
        owner_input.owner_authorization_record_digest
    )
    assert ingress["disposition"] == DISPOSITION_PROPOSAL_ONLY
    assert admission.promotion_authority == "NONE"


def test_authorization_does_not_mutate_policy(tmp_path: Any) -> None:
    _authorized(tmp_path)
    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1(None)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert policy.numeric_max_age_seconds is None
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False


def test_no_productive_config_or_direct_write() -> None:
    assert governed_productive_configuration_write_possible_v1() is False
    assert policy_mutation_possible_v1() is False
    assert direct_productive_write_possible_v1() is False
    assert optimization_direct_write() is False


def test_candidate_value_digest_stable(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    first = compute_candidate_parameter_value_digest_v1(ingress["parameter_config_delta"])
    second = compute_candidate_parameter_value_digest_v1(ingress["parameter_config_delta"])
    assert first == second


def test_stale_owner_digest_denied(tmp_path: Any) -> None:
    ingress, admission = _admitted(tmp_path)
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    bad_input = type(owner_input)(
        owner_authorization_record=owner_input.owner_authorization_record,
        owner_authorization_record_digest="c" * 64,
    )
    result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=bad_input,
        )
    )
    assert "OWNER_AUTHORIZATION_RECORD_DIGEST_MISMATCH" in result.reason_codes
