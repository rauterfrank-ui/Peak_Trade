"""V32 D29 F1/M9 explicit Owner productive apply policy and authority edge v1.

Defines and evaluates the typed Owner Apply policy edge at the governed configuration
apply boundary. Does not execute productive apply, mutate configuration, or append ledgers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    AUTHORIZED_FOR_PRODUCTIVE_APPLY,
    ExplicitProductiveAuthorizationResultV1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OWNER_APPLY_RECORD_FIELD_KEYS,
    OwnerApplyAuthorizationInputV1,
    verify_owner_apply_authorization_record_digest_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressAuthorizationBindingV1,
    PerIngressBindingStatusV1,
)
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    RUNTIME_APPLY_AUTHORITY_VALUE,
    validate_f1_m9_owner_apply_lineage_v1,
    validate_f1_m9_owner_apply_temporal_v1,
)
from src.governance.f1_m9_scoped_owner_apply_constants_v1 import (
    is_f1_m9_scoped_runtime_apply_authority_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationResultV1,
    RUNTIME_APPLY_AUTHORITY,
    STATUS_MATERIALIZED,
    runtime_apply_possible_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    POLICY_CONSUMER_MODULE,
    PRODUCTIVE_TARGET_ID,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    F1_M9_SCOPE_PAIR_ID,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = (
    "v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "V32_D29_F1_M9_EXPLICIT_OWNER_PRODUCTIVE_APPLY_POLICY_AND_AUTHORITY_EDGE_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D29_F1_M9_EXPLICIT_OWNER_PRODUCTIVE_APPLY_POLICY_AND_AUTHORITY_EDGE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1_decision_v1.json"
)
PREDECESSOR_DECISION: Final[str] = (
    "config/governance/"
    "v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1_decision_v1.json"
)
F1_M9_APPLY_AUTHORITY_MODULE: Final[str] = "src/governance/f1_m9_scoped_owner_apply_authority_v1.py"
F1_M9_APPLY_RECORD_MODULE: Final[str] = (
    "src/governance/f1_m9_owner_apply_authorization_record_v1.py"
)

CLOSED_D29_BLOCKER: Final[str] = (
    "F1_M9_PER_INGRESS_PRODUCTIVE_APPLY_REQUIRES_EXPLICIT_OWNER_APPLY_INPUT_AND_AUTHORITY_EDGE"
)
NEXT_TRUE_BLOCKER: Final[str] = "F1_M9_REAL_PRODUCTIVE_APPLY_REQUIRES_EXPLICIT_OWNER_GO"
BLOCKER_EDGE: Final[str] = "governed_productive_configuration_v1.runtime_apply_authority"
AUTHORITY_EDGE_ID: Final[str] = "PRODUCTIVE_APPLY_BOUNDARY"

OWNER_APPLY_INPUT_SCHEMA_VERSION: Final[str] = "f1_m9_owner_apply_authorization_record/v1"
POLICY_EDGE_STATUS_BOUND: Final[str] = "OWNER_APPLY_POLICY_EDGE_BOUND"
POLICY_EDGE_STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

PRODUCTIVE_APPLY_OCCURRED: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
SELECTION_AUTHORITY_CHANGED: Final[bool] = False
PROMOTION_AUTHORITY_CHANGED: Final[bool] = False


class PolicyEdgeEpistemicClassV1(str, Enum):
    CANONICAL_AUTHORITY = "CANONICAL_AUTHORITY"
    ADJUDICATED_CURRENT_FACT = "ADJUDICATED_CURRENT_FACT"
    NAVIGATION_ONLY = "NAVIGATION_ONLY"
    INTERPRETATION = "INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN_OR_CONTRADICTORY = "UNKNOWN_OR_CONTRADICTORY"


@dataclass(frozen=True, slots=True)
class ExplicitOwnerProductiveApplyPolicyEdgeRequestV1:
    owner_apply_input: OwnerApplyAuthorizationInputV1
    per_ingress_binding: PerIngressAuthorizationBindingV1
    authorization: ExplicitProductiveAuthorizationResultV1
    configuration: GovernedProductiveConfigurationResultV1
    registry_digest: str
    evaluation_time_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class ExplicitOwnerProductiveApplyPolicyEdgeResultV1:
    policy_edge_status: str
    reason_codes: tuple[str, ...]
    productive_apply_occurred: bool
    productive_apply_authorized: bool
    runtime_apply_authority: str
    authority_edge_id: str
    consumer_module: str
    owner_apply_record_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_edge_id": self.authority_edge_id,
            "consumer_module": self.consumer_module,
            "owner_apply_record_digest": self.owner_apply_record_digest,
            "policy_edge_status": self.policy_edge_status,
            "productive_apply_authorized": self.productive_apply_authorized,
            "productive_apply_occurred": self.productive_apply_occurred,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_authority": self.runtime_apply_authority,
        }


def build_f1_m9_owner_apply_policy_edge_descriptor_v1() -> Mapping[str, Any]:
    """Typed authority-edge descriptor (policy binding only; no runtime authorization)."""
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "authority_edge_id": AUTHORITY_EDGE_ID,
            "scoped_join_pair_id": F1_M9_SCOPE_PAIR_ID,
            "surface_id": OPTIMIZATION_SURFACE_ID,
            "productive_target_id": PRODUCTIVE_TARGET_ID,
            "consumer_module": POLICY_CONSUMER_MODULE,
            "producer_module": "src.governance.governed_productive_configuration_v1",
            "apply_adjudicator_module": F1_M9_APPLY_AUTHORITY_MODULE,
            "owner_apply_input_schema_version": OWNER_APPLY_INPUT_SCHEMA_VERSION,
            "owner_apply_record_field_keys": list(OWNER_APPLY_RECORD_FIELD_KEYS),
            "runtime_apply_authority_at_policy_edge": RUNTIME_APPLY_AUTHORITY,
            "runtime_apply_authority_on_execution": RUNTIME_APPLY_AUTHORITY_VALUE,
            "explicit_authorization_implies_apply": False,
            "materialization_implies_apply": False,
            "transport_implies_apply": False,
            "global_runtime_apply_possible": runtime_apply_possible_v1(),
            "authorized_for_productive_apply_flag": AUTHORIZED_FOR_PRODUCTIVE_APPLY,
            "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
            "closed_d29_blocker": CLOSED_D29_BLOCKER,
            "epistemic_class": PolicyEdgeEpistemicClassV1.ADJUDICATED_CURRENT_FACT.value,
        }
    )


def evaluate_explicit_owner_productive_apply_policy_edge_v1(
    request: ExplicitOwnerProductiveApplyPolicyEdgeRequestV1,
) -> ExplicitOwnerProductiveApplyPolicyEdgeResultV1:
    """Validate Owner Apply input against lineage; bind policy edge fail-closed; no apply."""
    reason_codes: list[str] = []

    if runtime_apply_possible_v1() is not False:
        reason_codes.append("GLOBAL_RUNTIME_APPLY_MUST_REMAIN_IMPOSSIBLE")
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        reason_codes.append("GLOBAL_PRODUCTIVE_APPLY_FLAG_MUST_REMAIN_FALSE")

    configuration = request.configuration
    if configuration.configuration_status != STATUS_MATERIALIZED:
        reason_codes.append("CONFIGURATION_NOT_MATERIALIZED")
        return _deny(reason_codes)

    record = configuration.configuration_record
    if record is not None and record.get("runtime_applied") is True:
        reason_codes.append("CONFIGURATION_ALREADY_RUNTIME_APPLIED")
    if record is not None:
        existing_apply_auth = str(record.get("runtime_apply_authority") or RUNTIME_APPLY_AUTHORITY)
        if is_f1_m9_scoped_runtime_apply_authority_v1(existing_apply_auth):
            reason_codes.append("CONFIGURATION_ALREADY_SCOPED_APPLY_AUTHORITY")

    apply_input = request.owner_apply_input
    owner_record = apply_input.owner_apply_authorization_record
    if apply_input.owner_apply_authorization_record_digest != owner_record.get(
        "owner_apply_authorization_record_digest"
    ):
        reason_codes.append("OWNER_APPLY_INPUT_DIGEST_MISMATCH")
    if not verify_owner_apply_authorization_record_digest_v1(owner_record):
        reason_codes.append("OWNER_APPLY_RECORD_DIGEST_INVALID")
    if str(owner_record.get("schema_version") or "") != OWNER_APPLY_INPUT_SCHEMA_VERSION:
        reason_codes.append("OWNER_APPLY_SCHEMA_VERSION_MISMATCH")

    now = request.evaluation_time_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    reason_codes.extend(
        validate_f1_m9_owner_apply_lineage_v1(
            record=owner_record,
            binding=request.per_ingress_binding,
            authorization=request.authorization,
            configuration=configuration,
            registry_digest=request.registry_digest,
        )
    )
    reason_codes.extend(validate_f1_m9_owner_apply_temporal_v1(owner_record, now))

    if request.per_ingress_binding.status != PerIngressBindingStatusV1.BOUND:
        reason_codes.append("PER_INGRESS_BINDING_NOT_BOUND")

    if reason_codes:
        return _deny(reason_codes)

    apply_digest = str(owner_record.get("owner_apply_authorization_record_digest") or "")
    return ExplicitOwnerProductiveApplyPolicyEdgeResultV1(
        policy_edge_status=POLICY_EDGE_STATUS_BOUND,
        reason_codes=(),
        productive_apply_occurred=False,
        productive_apply_authorized=False,
        runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
        authority_edge_id=AUTHORITY_EDGE_ID,
        consumer_module=POLICY_CONSUMER_MODULE,
        owner_apply_record_digest=apply_digest,
    )


def _deny(reason_codes: list[str]) -> ExplicitOwnerProductiveApplyPolicyEdgeResultV1:
    return ExplicitOwnerProductiveApplyPolicyEdgeResultV1(
        policy_edge_status=POLICY_EDGE_STATUS_DENIED,
        reason_codes=tuple(reason_codes),
        productive_apply_occurred=False,
        productive_apply_authorized=False,
        runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
        authority_edge_id=AUTHORITY_EDGE_ID,
        consumer_module=POLICY_CONSUMER_MODULE,
        owner_apply_record_digest=None,
    )


def prove_negative_stage_separation_v1() -> bool:
    """Authorization/materialization/transport must not imply apply at policy edge."""
    descriptor = build_f1_m9_owner_apply_policy_edge_descriptor_v1()
    return (
        descriptor["explicit_authorization_implies_apply"] is False
        and descriptor["materialization_implies_apply"] is False
        and descriptor["transport_implies_apply"] is False
        and descriptor["authorized_for_productive_apply_flag"] is False
        and descriptor["global_runtime_apply_possible"] is False
    )


__all__ = [
    "AUTHORITY_EDGE_ID",
    "BLOCKER_EDGE",
    "CLOSED_D29_BLOCKER",
    "DECISION_CONFIG",
    "ExplicitOwnerProductiveApplyPolicyEdgeRequestV1",
    "ExplicitOwnerProductiveApplyPolicyEdgeResultV1",
    "NEXT_TRUE_BLOCKER",
    "NORMATIVE_SPEC",
    "POLICY_EDGE_STATUS_BOUND",
    "POLICY_EDGE_STATUS_DENIED",
    "PRODUCTIVE_APPLY_OCCURRED",
    "PROMOTION_AUTHORITY_CHANGED",
    "SCHEMA_VERSION",
    "SELECTION_AUTHORITY_CHANGED",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "build_f1_m9_owner_apply_policy_edge_descriptor_v1",
    "evaluate_explicit_owner_productive_apply_policy_edge_v1",
    "prove_negative_stage_separation_v1",
]
