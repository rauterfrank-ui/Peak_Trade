"""Tests for governed productive runtime parameter seam join v1."""

from __future__ import annotations

from typing import Any

from src.governance.authorized_productive_parameter_seam_v1 import (
    AuthorizedProductiveParameterSeamBindRequestV1,
    bind_authorized_productive_parameter_seam_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    STATUS_TRANSPORT_DENIED,
    STATUS_TRANSPORT_READY,
    optimization_can_direct_write_runtime_seam_v1,
    resolve_governed_runtime_seam_for_presence_gate_v1,
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


def _valid_seam_record(tmp_path: Any):
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
    assert seam.seam_record is not None
    return dict(seam.seam_record)


def test_valid_seam_transport_reaches_presence_gate_consumer(tmp_path: Any) -> None:
    seam_record = _valid_seam_record(tmp_path)
    transport = resolve_governed_runtime_seam_for_presence_gate_v1(seam_record)
    assert transport.transport_status == STATUS_TRANSPORT_READY
    assert transport.seam_for_consumer is not None

    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        ctx,
        eligibility=elig,
        authorized_productive_parameter_seam=transport.seam_for_consumer,
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.threshold_status == THRESHOLD_STATUS_UNRESOLVED
    assert gate.max_age_policy_evidence.enforcement_applied is False


def test_missing_seam_fail_closed_unresolved() -> None:
    transport = resolve_governed_runtime_seam_for_presence_gate_v1(None)
    assert transport.seam_for_consumer is None
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        ctx,
        eligibility=elig,
        authorized_productive_parameter_seam=transport.seam_for_consumer,
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.threshold_status == THRESHOLD_STATUS_UNRESOLVED


def test_invalid_digest_rejected(tmp_path: Any) -> None:
    seam_record = _valid_seam_record(tmp_path)
    seam_record["seam_digest"] = "0" * 64
    transport = resolve_governed_runtime_seam_for_presence_gate_v1(seam_record)
    assert transport.transport_status == STATUS_TRANSPORT_DENIED
    assert transport.seam_for_consumer is None


def test_unauthorized_candidate_payload_rejected() -> None:
    transport = resolve_governed_runtime_seam_for_presence_gate_v1(
        {
            "candidate_ref": "evil",
            "parameter_config_delta": {"max_age_seconds": 60},
        }
    )
    assert transport.transport_status == STATUS_TRANSPORT_DENIED
    assert "CANDIDATE_REF_FORBIDDEN" in transport.reason_codes


def test_optimization_cannot_direct_write_runtime() -> None:
    assert optimization_can_direct_write_runtime_seam_v1() is False


def test_authority_constants_unchanged() -> None:
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED is False
