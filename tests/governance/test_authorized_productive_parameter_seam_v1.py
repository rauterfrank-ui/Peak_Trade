"""Tests for authorized productive parameter seam v1 (M10 Slice C)."""

from __future__ import annotations

from typing import Any

from src.governance.authorized_productive_parameter_seam_v1 import (
    PRODUCTIVE_TARGET_ID,
    STATUS_BOUND,
    STATUS_DENIED,
    AuthorizedProductiveParameterSeamBindRequestV1,
    bind_authorized_productive_parameter_seam_v1,
    evaluate_age_policy_at_consumer_boundary_v1,
    optimization_can_bind_seam_directly_v1,
    resolve_age_policy_from_authorized_seam_record_v1,
    verify_seam_record_digest_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    STATUS_AUTHORIZED_BOUNDARY,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    DISPOSITION_CONFIGURATION_ONLY,
    GovernedProductiveConfigurationMaterializeRequestV1,
    GovernedProductiveConfigurationResultV1,
    STATUS_DENIED as CONFIG_STATUS_DENIED,
    STATUS_MATERIALIZED,
    materialize_governed_productive_configuration_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    POLICY_CONSUMER_MODULE,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
    THRESHOLD_STATUS_UNRESOLVED,
    build_ratified_unresolved_max_age_policy_contract_v1,
)
from src.trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED,
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _context,
    _valid_estimate,
)
from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)


def _full_chain(tmp_path: Any):
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
    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=configuration)
    )
    return ingress, authorization, configuration, seam


def test_end_to_end_lineage_to_seam(tmp_path: Any) -> None:
    ingress, authorization, configuration, seam = _full_chain(tmp_path)
    assert authorization.authorization_status == STATUS_AUTHORIZED_BOUNDARY
    assert configuration.configuration_status == STATUS_MATERIALIZED
    assert seam.seam_status == STATUS_BOUND
    assert seam.seam_record is not None
    assert verify_seam_record_digest_v1(seam.seam_record)
    numeric = float(ingress["parameter_config_delta"]["max_age_seconds"])
    assert seam.seam_record["numeric_max_age_seconds"] == numeric
    assert seam.seam_record["configuration_digest"] == configuration.configuration_digest
    assert seam.seam_record["authorization_digest"] == authorization.authorization_digest
    assert seam.seam_record["policy_consumer_module"] == POLICY_CONSUMER_MODULE


def test_configuration_only_without_materialization_denied(tmp_path: Any) -> None:
    _ingress_for_m9(tmp_path)
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(
            configuration=GovernedProductiveConfigurationResultV1(
                configuration_status=CONFIG_STATUS_DENIED,
                reason_codes=("DENIED",),
                configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
                configuration_digest=None,
                configuration_record=None,
            )
        )
    )
    assert seam.seam_status == STATUS_DENIED
    assert "CONFIGURATION_NOT_MATERIALIZED" in seam.reason_codes


def test_authorization_without_configuration_denied(tmp_path: Any) -> None:
    _, authorization, _, _ = _full_chain(tmp_path)
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(
            configuration=GovernedProductiveConfigurationResultV1(
                configuration_status=CONFIG_STATUS_DENIED,
                reason_codes=("SKIP",),
                configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
                configuration_digest=None,
                configuration_record=None,
            )
        )
    )
    assert seam.seam_status == STATUS_DENIED
    assert authorization.authorization_record is not None


def test_invalid_seam_resolves_unresolved_policy() -> None:
    policy = resolve_age_policy_from_authorized_seam_record_v1({"seam_status": "BAD"})
    unresolved = build_ratified_unresolved_max_age_policy_contract_v1()
    assert policy.threshold_status == unresolved.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert policy.numeric_max_age_seconds is None


def test_valid_seam_without_threshold_stays_unresolved_policy(tmp_path: Any) -> None:
    _, _, _, seam = _full_chain(tmp_path)
    assert seam.seam_record is not None
    policy = resolve_age_policy_from_authorized_seam_record_v1(seam.seam_record)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert policy.numeric_max_age_seconds is None


def test_presence_gate_without_seam_unchanged_unresolved() -> None:
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx, eligibility=elig)
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert gate.max_age_policy_evidence.enforcement_applied is False


def test_presence_gate_with_seam_without_threshold_stays_unresolved(tmp_path: Any) -> None:
    _, _, _, seam = _full_chain(tmp_path)
    assert seam.seam_record is not None
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        ctx,
        eligibility=elig,
        authorized_productive_parameter_seam=seam.seam_record,
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert gate.max_age_policy_evidence.enforcement_applied is False


def test_tampered_configuration_digest_denied(tmp_path: Any) -> None:
    _, _, configuration, _ = _full_chain(tmp_path)
    assert configuration.configuration_record is not None
    tampered = dict(configuration.configuration_record)
    tampered["numeric_max_age_seconds"] = 120.0
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body = {k: v for k, v in tampered.items() if k != "configuration_digest"}
    tampered["configuration_digest"] = compute_content_sha256(body)
    from types import MappingProxyType
    from src.governance.governed_productive_configuration_v1 import (
        GovernedProductiveConfigurationResultV1,
        DISPOSITION_CONFIGURATION_ONLY,
    )

    bad_config = GovernedProductiveConfigurationResultV1(
        configuration_status=STATUS_MATERIALIZED,
        reason_codes=configuration.reason_codes,
        configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
        configuration_digest=str(tampered["configuration_digest"]),
        configuration_record=MappingProxyType(tampered),
    )
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=bad_config)
    )
    assert "CONFIGURATION_NUMERIC_VALUE_INTERNAL_MISMATCH" in seam.reason_codes


def test_optimization_cannot_bind_seam_directly() -> None:
    assert optimization_can_bind_seam_directly_v1() is False


def test_module_enforcement_flags_unchanged() -> None:
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED is False


def test_wrong_productive_target_denied(tmp_path: Any) -> None:
    _, _, configuration, _ = _full_chain(tmp_path)
    assert configuration.configuration_record is not None
    tampered = dict(configuration.configuration_record)
    tampered["productive_target_id"] = "peak_trade.governance.productive_target.other/v1"
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body = {k: v for k, v in tampered.items() if k != "configuration_digest"}
    tampered["configuration_digest"] = compute_content_sha256(body)
    bad = GovernedProductiveConfigurationResultV1(
        configuration_status=STATUS_MATERIALIZED,
        reason_codes=configuration.reason_codes,
        configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
        configuration_digest=str(tampered["configuration_digest"]),
        configuration_record=type(configuration.configuration_record)(tampered),
    )
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=bad)
    )
    assert seam.seam_status == STATUS_DENIED


def test_configuration_digest_mismatch_denied(tmp_path: Any) -> None:
    _, _, configuration, _ = _full_chain(tmp_path)
    assert configuration.configuration_record is not None
    tampered = dict(configuration.configuration_record)
    tampered["configuration_digest"] = "0" * 64
    bad = GovernedProductiveConfigurationResultV1(
        configuration_status=STATUS_MATERIALIZED,
        reason_codes=configuration.reason_codes,
        configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
        configuration_digest=str(tampered["configuration_digest"]),
        configuration_record=type(configuration.configuration_record)(tampered),
    )
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=bad)
    )
    assert "CONFIGURATION_DIGEST_MISMATCH" in seam.reason_codes


def test_consumer_identity_mismatch_unresolved_policy(tmp_path: Any) -> None:
    _, _, _, seam = _full_chain(tmp_path)
    assert seam.seam_record is not None
    bad = dict(seam.seam_record)
    bad["policy_consumer_module"] = "other.module"
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body = {k: v for k, v in bad.items() if k != "seam_digest"}
    bad["seam_digest"] = compute_content_sha256(body)
    policy = resolve_age_policy_from_authorized_seam_record_v1(bad)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED


def test_seam_numeric_mutation_unresolved_policy(tmp_path: Any) -> None:
    _, _, _, seam = _full_chain(tmp_path)
    assert seam.seam_record is not None
    bad = dict(seam.seam_record)
    bad["numeric_max_age_seconds"] = 999.0
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body = {k: v for k, v in bad.items() if k != "seam_digest"}
    bad["seam_digest"] = compute_content_sha256(body)
    policy = resolve_age_policy_from_authorized_seam_record_v1(bad)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED


def test_ingress_direct_to_seam_not_possible_without_materialized_config(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(
            configuration=GovernedProductiveConfigurationResultV1(
                configuration_status=CONFIG_STATUS_DENIED,
                reason_codes=("INGRESS_ONLY",),
                configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
                configuration_digest=str(ingress.get("ingress_digest")),
                configuration_record=None,
            )
        )
    )
    assert seam.seam_status == STATUS_DENIED


def test_evaluate_consumer_boundary_invalid_seam_non_enforcing() -> None:
    evidence = evaluate_age_policy_at_consumer_boundary_v1(
        seam_record={"seam_digest": "bad"},
        estimate=None,
        reference_market_event_time=None,
        presence_status=None,
    )
    assert evidence.enforcement_applied is False
