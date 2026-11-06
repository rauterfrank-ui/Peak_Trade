"""F1/M9 per-ingress authorization chain resolver v1 (composition through runtime transport).

Resolves governance ingress → explicit authorization → configuration → optional F1/M9
Owner Apply → seam → runtime transport for the presence-gate consumer.
Without a valid Owner Apply record, stops before productive apply.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, Mapping

from src.governance.authorized_productive_parameter_seam_v1 import (
    AuthorizedProductiveParameterSeamBindRequestV1,
    AuthorizedProductiveParameterSeamResultV1,
    bind_authorized_productive_parameter_seam_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    AUTHORIZED_FOR_PRODUCTIVE_APPLY,
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    ExplicitProductiveAuthorizationResultV1,
    OwnerExplicitProductiveAuthorizationInputV1,
    STATUS_AUTHORIZED_BOUNDARY,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
)
from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
    OwnerThresholdValueAuthorizationInputV1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressAuthorizationBindingV1,
    PerIngressBindingStatusV1,
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    F1M9ProductiveApplyExecutionPhaseV1,
    F1M9ProductiveApplyExecutionRequestV1,
    STATUS_EXECUTION_READY,
    evaluate_f1_m9_productive_apply_execution_boundary_v1,
)
from src.governance.f1_m9_scoped_owner_apply_constants_v1 import RUNTIME_APPLY_AUTHORITY_VALUE
from src.governance.f1_m9_scoped_owner_threshold_value_authority_v1 import (
    F1M9ScopedOwnerThresholdValueAdjudicationRequestV1,
    evaluate_f1_m9_scoped_owner_threshold_value_authority_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    GovernedProductiveConfigurationResultV1,
    RUNTIME_APPLY_AUTHORITY,
    STATUS_MATERIALIZED,
    materialize_governed_productive_configuration_v1,
    runtime_apply_possible_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    GovernedRuntimeSeamTransportResultV1,
    STATUS_TRANSPORT_READY,
    resolve_governed_runtime_seam_for_presence_gate_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    OptimizationProposalGovernanceAdmissionResultV1,
)

SCHEMA_VERSION: Final[str] = "f1_m9_per_ingress_authorization_chain_resolver/v1"
PRODUCTIVE_APPLY_STAGE_STATUS: Final[str] = "OWNER_POLICY_REQUIRED_NO_AUTHORITY_EDGE"
CHAIN_STOP_BEFORE: Final[str] = "PRODUCTIVE_APPLY"


class ChainStageV1(str, Enum):
    SCOPED_JOIN_BINDING = "SCOPED_JOIN_BINDING"
    PROPOSAL_REVIEW_ADMISSION = "PROPOSAL_REVIEW_ADMISSION"
    EXPLICIT_PRODUCTIVE_AUTHORIZATION = "EXPLICIT_PRODUCTIVE_AUTHORIZATION"
    PRODUCTIVE_CONFIGURATION_MATERIALIZATION = "PRODUCTIVE_CONFIGURATION_MATERIALIZATION"
    AUTHORIZED_PARAMETER_SEAM = "AUTHORIZED_PARAMETER_SEAM"
    RUNTIME_TRANSPORT = "RUNTIME_TRANSPORT"
    PRODUCTIVE_APPLY = "PRODUCTIVE_APPLY"
    THRESHOLD_VALUE_AUTHORIZATION = "THRESHOLD_VALUE_AUTHORIZATION"


@dataclass(frozen=True, slots=True)
class PerIngressChainResolutionV1:
    chain_status: str
    stop_stage: ChainStageV1
    reason_codes: tuple[str, ...]
    per_ingress_binding: PerIngressAuthorizationBindingV1 | None
    authorization: ExplicitProductiveAuthorizationResultV1 | None
    configuration: GovernedProductiveConfigurationResultV1 | None
    seam: AuthorizedProductiveParameterSeamResultV1 | None
    runtime_transport: GovernedRuntimeSeamTransportResultV1 | None
    productive_apply_authorized: bool
    runtime_apply_authority: str
    threshold_value_authorized: bool
    runtime_threshold_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_status": self.chain_status,
            "productive_apply_authorized": self.productive_apply_authorized,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_authority": self.runtime_apply_authority,
            "runtime_threshold_authority": self.runtime_threshold_authority,
            "stop_stage": self.stop_stage.value,
            "threshold_value_authorized": self.threshold_value_authorized,
        }


def resolve_f1_m9_per_ingress_authorization_chain_v1(
    *,
    ingress: Mapping[str, Any],
    admission: OptimizationProposalGovernanceAdmissionResultV1,
    owner_input: OwnerExplicitProductiveAuthorizationInputV1,
    registry_digest: str,
    owner_apply_input: OwnerApplyAuthorizationInputV1 | None = None,
    ledger_paths: F1M9ProductiveApplyLedgerPathsV1 | None = None,
    apply_execution_phase: F1M9ProductiveApplyExecutionPhaseV1 = (
        F1M9ProductiveApplyExecutionPhaseV1.EXECUTION_PROOF
    ),
    owner_threshold_input: OwnerThresholdValueAuthorizationInputV1 | None = None,
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1 | None = None,
) -> PerIngressChainResolutionV1:
    """Fail-closed chain through runtime transport; apply requires Owner Apply record."""
    apply_blocked = AUTHORIZED_FOR_PRODUCTIVE_APPLY is False and not runtime_apply_possible_v1()
    if not apply_blocked:
        return PerIngressChainResolutionV1(
            chain_status="DENIED_FAIL_CLOSED",
            stop_stage=ChainStageV1.PRODUCTIVE_APPLY,
            reason_codes=("PRODUCTIVE_APPLY_MUST_REMAIN_BLOCKED",),
            per_ingress_binding=None,
            authorization=None,
            configuration=None,
            seam=None,
            runtime_transport=None,
            productive_apply_authorized=False,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
            threshold_value_authorized=False,
            runtime_threshold_authority="NONE",
        )

    binding = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest=registry_digest,
    )
    if binding.status != PerIngressBindingStatusV1.BOUND:
        return PerIngressChainResolutionV1(
            chain_status="DENIED_FAIL_CLOSED",
            stop_stage=ChainStageV1.SCOPED_JOIN_BINDING,
            reason_codes=binding.reason_codes,
            per_ingress_binding=binding,
            authorization=None,
            configuration=None,
            seam=None,
            runtime_transport=None,
            productive_apply_authorized=False,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
            threshold_value_authorized=False,
            runtime_threshold_authority="NONE",
        )

    if admission.admission_status != ADMISSION_ADMITTED:
        return PerIngressChainResolutionV1(
            chain_status="DENIED_FAIL_CLOSED",
            stop_stage=ChainStageV1.PROPOSAL_REVIEW_ADMISSION,
            reason_codes=("GOVERNANCE_REVIEW_ADMISSION_NOT_ADMITTED",),
            per_ingress_binding=binding,
            authorization=None,
            configuration=None,
            seam=None,
            runtime_transport=None,
            productive_apply_authorized=False,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
            threshold_value_authorized=False,
            runtime_threshold_authority="NONE",
        )

    authorization = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    if authorization.authorization_status != STATUS_AUTHORIZED_BOUNDARY:
        return PerIngressChainResolutionV1(
            chain_status="DENIED_FAIL_CLOSED",
            stop_stage=ChainStageV1.EXPLICIT_PRODUCTIVE_AUTHORIZATION,
            reason_codes=authorization.reason_codes,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=None,
            seam=None,
            runtime_transport=None,
            productive_apply_authorized=False,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
            threshold_value_authorized=False,
            runtime_threshold_authority="NONE",
        )

    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    if configuration.configuration_status != STATUS_MATERIALIZED:
        return PerIngressChainResolutionV1(
            chain_status="DENIED_FAIL_CLOSED",
            stop_stage=ChainStageV1.PRODUCTIVE_CONFIGURATION_MATERIALIZATION,
            reason_codes=configuration.reason_codes,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            seam=None,
            runtime_transport=None,
            productive_apply_authorized=False,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
            threshold_value_authorized=False,
            runtime_threshold_authority="NONE",
        )

    configuration_for_seam = configuration
    runtime_apply_authority = RUNTIME_APPLY_AUTHORITY
    productive_apply_authorized = False
    threshold_value_authorized = False
    runtime_threshold_authority = "NONE"

    if owner_apply_input is not None:
        if ledger_paths is None:
            return PerIngressChainResolutionV1(
                chain_status="DENIED_FAIL_CLOSED",
                stop_stage=ChainStageV1.PRODUCTIVE_APPLY,
                reason_codes=("APPLY_LEDGER_PATHS_REQUIRED",),
                per_ingress_binding=binding,
                authorization=authorization,
                configuration=configuration,
                seam=None,
                runtime_transport=None,
                productive_apply_authorized=False,
                runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
                threshold_value_authorized=False,
                runtime_threshold_authority="NONE",
            )
        execution_result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
            F1M9ProductiveApplyExecutionRequestV1(
                owner_apply_input=owner_apply_input,
                per_ingress_binding=binding,
                authorization=authorization,
                configuration=configuration,
                registry_digest=registry_digest,
                ledger_paths=ledger_paths,
                execution_phase=apply_execution_phase,
            )
        )
        if (
            execution_result.execution_status != STATUS_EXECUTION_READY
            or not execution_result.productive_apply_authorized
            or execution_result.configuration_after_execution is None
        ):
            return PerIngressChainResolutionV1(
                chain_status="DENIED_FAIL_CLOSED",
                stop_stage=ChainStageV1.PRODUCTIVE_APPLY,
                reason_codes=execution_result.reason_codes,
                per_ingress_binding=binding,
                authorization=authorization,
                configuration=configuration,
                seam=None,
                runtime_transport=None,
                productive_apply_authorized=False,
                runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
                threshold_value_authorized=False,
                runtime_threshold_authority="NONE",
            )
        configuration_for_seam = execution_result.configuration_after_execution
        runtime_apply_authority = execution_result.runtime_apply_authority
        productive_apply_authorized = True

    if owner_threshold_input is not None:
        if not productive_apply_authorized:
            return PerIngressChainResolutionV1(
                chain_status="DENIED_FAIL_CLOSED",
                stop_stage=ChainStageV1.THRESHOLD_VALUE_AUTHORIZATION,
                reason_codes=("PRODUCTIVE_APPLY_REQUIRED_BEFORE_THRESHOLD",),
                per_ingress_binding=binding,
                authorization=authorization,
                configuration=configuration_for_seam,
                seam=None,
                runtime_transport=None,
                productive_apply_authorized=productive_apply_authorized,
                runtime_apply_authority=runtime_apply_authority,
                threshold_value_authorized=False,
                runtime_threshold_authority="NONE",
            )
        if ledger_paths is None or threshold_ledger_paths is None:
            return PerIngressChainResolutionV1(
                chain_status="DENIED_FAIL_CLOSED",
                stop_stage=ChainStageV1.THRESHOLD_VALUE_AUTHORIZATION,
                reason_codes=("THRESHOLD_LEDGER_PATHS_REQUIRED",),
                per_ingress_binding=binding,
                authorization=authorization,
                configuration=configuration_for_seam,
                seam=None,
                runtime_transport=None,
                productive_apply_authorized=productive_apply_authorized,
                runtime_apply_authority=runtime_apply_authority,
                threshold_value_authorized=False,
                runtime_threshold_authority="NONE",
            )
        threshold_result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
            F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
                owner_threshold_input=owner_threshold_input,
                per_ingress_binding=binding,
                authorization=authorization,
                configuration=configuration_for_seam,
                registry_digest=registry_digest,
                apply_ledger_paths=ledger_paths,
                threshold_ledger_paths=threshold_ledger_paths,
            )
        )
        if (
            not threshold_result.threshold_value_authorized
            or threshold_result.configuration_after_threshold is None
        ):
            return PerIngressChainResolutionV1(
                chain_status="DENIED_FAIL_CLOSED",
                stop_stage=ChainStageV1.THRESHOLD_VALUE_AUTHORIZATION,
                reason_codes=threshold_result.reason_codes,
                per_ingress_binding=binding,
                authorization=authorization,
                configuration=configuration_for_seam,
                seam=None,
                runtime_transport=None,
                productive_apply_authorized=productive_apply_authorized,
                runtime_apply_authority=runtime_apply_authority,
                threshold_value_authorized=False,
                runtime_threshold_authority="NONE",
            )
        configuration_for_seam = threshold_result.configuration_after_threshold
        threshold_value_authorized = True
        runtime_threshold_authority = threshold_result.runtime_threshold_authority

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=configuration_for_seam)
    )
    if seam.seam_record is None:
        return PerIngressChainResolutionV1(
            chain_status="DENIED_FAIL_CLOSED",
            stop_stage=ChainStageV1.AUTHORIZED_PARAMETER_SEAM,
            reason_codes=seam.reason_codes,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            seam=seam,
            runtime_transport=None,
            productive_apply_authorized=productive_apply_authorized,
            runtime_apply_authority=runtime_apply_authority,
            threshold_value_authorized=threshold_value_authorized,
            runtime_threshold_authority=runtime_threshold_authority,
        )

    transport = resolve_governed_runtime_seam_for_presence_gate_v1(dict(seam.seam_record))
    if transport.transport_status != STATUS_TRANSPORT_READY:
        return PerIngressChainResolutionV1(
            chain_status="DENIED_FAIL_CLOSED",
            stop_stage=ChainStageV1.RUNTIME_TRANSPORT,
            reason_codes=transport.reason_codes,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            seam=seam,
            runtime_transport=transport,
            productive_apply_authorized=productive_apply_authorized,
            runtime_apply_authority=runtime_apply_authority,
            threshold_value_authorized=threshold_value_authorized,
            runtime_threshold_authority=runtime_threshold_authority,
        )

    if not productive_apply_authorized:
        return PerIngressChainResolutionV1(
            chain_status="RESOLVED_THROUGH_RUNTIME_TRANSPORT_APPLY_BLOCKED",
            stop_stage=ChainStageV1.PRODUCTIVE_APPLY,
            reason_codes=(PRODUCTIVE_APPLY_STAGE_STATUS, CHAIN_STOP_BEFORE),
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            seam=seam,
            runtime_transport=transport,
            productive_apply_authorized=False,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
            threshold_value_authorized=False,
            runtime_threshold_authority="NONE",
        )

    chain_status = "RESOLVED_THROUGH_RUNTIME_TRANSPORT_F1_M9_APPLY_AUTHORIZED"
    reason_codes: tuple[str, ...] = ("F1_M9_OWNER_APPLY_AUTHORIZED",)
    if threshold_value_authorized:
        chain_status = "RESOLVED_THROUGH_RUNTIME_TRANSPORT_F1_M9_THRESHOLD_AUTHORIZED"
        reason_codes = ("F1_M9_OWNER_THRESHOLD_VALUE_AUTHORIZED",)

    return PerIngressChainResolutionV1(
        chain_status=chain_status,
        stop_stage=ChainStageV1.RUNTIME_TRANSPORT,
        reason_codes=reason_codes,
        per_ingress_binding=binding,
        authorization=authorization,
        configuration=configuration_for_seam,
        seam=seam,
        runtime_transport=transport,
        productive_apply_authorized=True,
        runtime_apply_authority=runtime_apply_authority,
        threshold_value_authorized=threshold_value_authorized,
        runtime_threshold_authority=runtime_threshold_authority,
    )


__all__ = [
    "CHAIN_STOP_BEFORE",
    "ChainStageV1",
    "PerIngressChainResolutionV1",
    "PRODUCTIVE_APPLY_STAGE_STATUS",
    "SCHEMA_VERSION",
    "resolve_f1_m9_per_ingress_authorization_chain_v1",
]
