"""F1/M9 productive apply execution boundary v1 (policy edge + scoped apply orchestration).

Composes the merged D29 explicit Owner Apply policy edge with the scoped apply adjudicator.
Does not authorize real productive apply unless decision-bound REAL_PRODUCTIVE_APPLY_AUTHORIZED.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    AUTHORIZED_FOR_PRODUCTIVE_APPLY,
    ExplicitProductiveAuthorizationResultV1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressAuthorizationBindingV1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    F1M9ScopedOwnerApplyAdjudicationRequestV1,
    RUNTIME_APPLY_AUTHORITY_VALUE,
    STATUS_APPLY_AUTHORIZED,
    evaluate_f1_m9_scoped_owner_productive_apply_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationResultV1,
    RUNTIME_APPLY_AUTHORITY,
    STATUS_MATERIALIZED,
    runtime_apply_possible_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    POLICY_CONSUMER_MODULE,
    PRODUCTIVE_TARGET_ID,
)
from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1 import (
    AUTHORITY_EDGE_ID,
    ExplicitOwnerProductiveApplyPolicyEdgeRequestV1,
    POLICY_EDGE_STATUS_BOUND,
    POLICY_EDGE_STATUS_DENIED,
    evaluate_explicit_owner_productive_apply_policy_edge_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "f1_m9_productive_apply_execution_boundary/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_PRODUCTIVE_APPLY_EXECUTION_MAX_BUILD_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/F1_M9_PRODUCTIVE_APPLY_EXECUTION_BOUNDARY_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_productive_apply_execution_boundary_v1_decision_v1.json"
)
PREDECESSOR_DECISION: Final[str] = (
    "config/governance/"
    "v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1_decision_v1.json"
)
POLICY_EDGE_MODULE: Final[str] = (
    "src/governance/v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1.py"
)
APPLY_ADJUDICATOR_MODULE: Final[str] = "src/governance/f1_m9_scoped_owner_apply_authority_v1.py"

CLOSED_EXECUTION_BLOCKER: Final[str] = "F1_M9_PRODUCTIVE_APPLY_EXECUTION_REQUIRES_OWNER_MERGE_GO"
NEXT_TRUE_BLOCKER: Final[str] = "F1_M9_REAL_PRODUCTIVE_APPLY_REQUIRES_EXPLICIT_OWNER_GO"

PRODUCTIVE_APPLY_OCCURRED: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False
SELECTION_AUTHORITY_CHANGED: Final[bool] = False
PROMOTION_AUTHORITY_CHANGED: Final[bool] = False

STATUS_EXECUTION_READY: Final[str] = "F1_M9_APPLY_EXECUTION_BOUNDARY_READY"
STATUS_EXECUTION_DENIED: Final[str] = "DENIED_FAIL_CLOSED"
STATUS_REAL_APPLY_BLOCKED: Final[str] = "REAL_PRODUCTIVE_APPLY_NOT_AUTHORIZED"

_REPO_ROOT = Path(__file__).resolve().parents[2]


class F1M9ProductiveApplyExecutionPhaseV1(str, Enum):
    EXECUTION_PROOF = "EXECUTION_PROOF"
    AUTHORIZED_PRODUCTIVE_APPLY = "AUTHORIZED_PRODUCTIVE_APPLY"


@dataclass(frozen=True, slots=True)
class F1M9ProductiveApplyExecutionRequestV1:
    owner_apply_input: OwnerApplyAuthorizationInputV1
    per_ingress_binding: PerIngressAuthorizationBindingV1
    authorization: ExplicitProductiveAuthorizationResultV1
    configuration: GovernedProductiveConfigurationResultV1
    registry_digest: str
    ledger_paths: F1M9ProductiveApplyLedgerPathsV1
    execution_phase: F1M9ProductiveApplyExecutionPhaseV1 = (
        F1M9ProductiveApplyExecutionPhaseV1.EXECUTION_PROOF
    )
    evaluation_time_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class F1M9ProductiveApplyExecutionResultV1:
    execution_status: str
    reason_codes: tuple[str, ...]
    policy_edge_status: str
    apply_status: str | None
    execution_phase: str
    productive_apply_occurred: bool
    productive_apply_authorized: bool
    real_productive_apply_authorized: bool
    runtime_apply_authority: str
    authority_edge_id: str
    consumer_module: str
    configuration_after_execution: GovernedProductiveConfigurationResultV1 | None
    owner_apply_authorization_record_digest: str | None
    apply_ledger_entry_digest: str | None
    execution_evidence_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_ledger_entry_digest": self.apply_ledger_entry_digest,
            "apply_status": self.apply_status,
            "authority_edge_id": self.authority_edge_id,
            "configuration_after_execution_digest": (
                None
                if self.configuration_after_execution is None
                else self.configuration_after_execution.configuration_digest
            ),
            "consumer_module": self.consumer_module,
            "execution_evidence_digest": self.execution_evidence_digest,
            "execution_phase": self.execution_phase,
            "execution_status": self.execution_status,
            "owner_apply_authorization_record_digest": (
                self.owner_apply_authorization_record_digest
            ),
            "policy_edge_status": self.policy_edge_status,
            "productive_apply_authorized": self.productive_apply_authorized,
            "productive_apply_occurred": self.productive_apply_occurred,
            "real_productive_apply_authorized": self.real_productive_apply_authorized,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_authority": self.runtime_apply_authority,
        }


def load_execution_boundary_decision_v1(
    *, repo_root: Path | None = None
) -> MappingProxyType[str, Any]:
    root = repo_root or _REPO_ROOT
    payload = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("EXECUTION_BOUNDARY_DECISION_NOT_MAPPING")
    return MappingProxyType(payload)


def real_productive_apply_authorized_v1(*, repo_root: Path | None = None) -> bool:
    decision = load_execution_boundary_decision_v1(repo_root=repo_root)
    return decision.get("real_productive_apply_authorized") is True


def build_execution_evidence_record_v1(
    *,
    policy_edge_status: str,
    apply_status: str | None,
    execution_phase: str,
    owner_apply_record_digest: str | None,
    configuration_digest: str | None,
    apply_ledger_entry_digest: str | None,
    consumer_module: str,
) -> Mapping[str, Any]:
    body = {
        "apply_ledger_entry_digest": apply_ledger_entry_digest,
        "apply_status": apply_status,
        "authority_edge_id": AUTHORITY_EDGE_ID,
        "configuration_digest": configuration_digest,
        "consumer_module": consumer_module,
        "execution_phase": execution_phase,
        "owner_apply_record_digest": owner_apply_record_digest,
        "policy_edge_status": policy_edge_status,
        "productive_apply_occurred": False,
        "productive_numeric_values_set": int(PRODUCTIVE_NUMERIC_VALUES_SET),
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
    }
    digest = compute_content_sha256(body)
    return MappingProxyType({**body, "execution_evidence_digest": digest})


def _deny(
    reason_codes: list[str],
    *,
    policy_edge_status: str = POLICY_EDGE_STATUS_DENIED,
    execution_phase: str,
    real_authorized: bool,
) -> F1M9ProductiveApplyExecutionResultV1:
    evidence = build_execution_evidence_record_v1(
        policy_edge_status=policy_edge_status,
        apply_status=None,
        execution_phase=execution_phase,
        owner_apply_record_digest=None,
        configuration_digest=None,
        apply_ledger_entry_digest=None,
        consumer_module=POLICY_CONSUMER_MODULE,
    )
    return F1M9ProductiveApplyExecutionResultV1(
        execution_status=STATUS_EXECUTION_DENIED,
        reason_codes=tuple(reason_codes),
        policy_edge_status=policy_edge_status,
        apply_status=None,
        execution_phase=execution_phase,
        productive_apply_occurred=False,
        productive_apply_authorized=False,
        real_productive_apply_authorized=real_authorized,
        runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
        authority_edge_id=AUTHORITY_EDGE_ID,
        consumer_module=POLICY_CONSUMER_MODULE,
        configuration_after_execution=None,
        owner_apply_authorization_record_digest=None,
        apply_ledger_entry_digest=None,
        execution_evidence_digest=str(evidence["execution_evidence_digest"]),
    )


def evaluate_f1_m9_productive_apply_execution_boundary_v1(
    request: F1M9ProductiveApplyExecutionRequestV1,
    *,
    repo_root: Path | None = None,
) -> F1M9ProductiveApplyExecutionResultV1:
    """Orchestrate D29 policy edge + scoped apply; fail-closed; no real apply unless authorized."""
    phase = request.execution_phase.value
    real_authorized = real_productive_apply_authorized_v1(repo_root=repo_root)
    reason_codes: list[str] = []

    if runtime_apply_possible_v1() is not False:
        reason_codes.append("GLOBAL_RUNTIME_APPLY_MUST_REMAIN_IMPOSSIBLE")
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        reason_codes.append("GLOBAL_PRODUCTIVE_APPLY_FLAG_MUST_REMAIN_FALSE")
    if int(PRODUCTIVE_NUMERIC_VALUES_SET) != 0:
        reason_codes.append("PRODUCTIVE_NUMERIC_VALUES_SET_MUST_REMAIN_ZERO")

    if (
        request.execution_phase is F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY
        and not real_authorized
    ):
        return F1M9ProductiveApplyExecutionResultV1(
            execution_status=STATUS_REAL_APPLY_BLOCKED,
            reason_codes=("REAL_PRODUCTIVE_APPLY_NOT_AUTHORIZED",),
            policy_edge_status=POLICY_EDGE_STATUS_DENIED,
            apply_status=None,
            execution_phase=phase,
            productive_apply_occurred=False,
            productive_apply_authorized=False,
            real_productive_apply_authorized=False,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY,
            authority_edge_id=AUTHORITY_EDGE_ID,
            consumer_module=POLICY_CONSUMER_MODULE,
            configuration_after_execution=None,
            owner_apply_authorization_record_digest=None,
            apply_ledger_entry_digest=None,
            execution_evidence_digest=str(
                build_execution_evidence_record_v1(
                    policy_edge_status=POLICY_EDGE_STATUS_DENIED,
                    apply_status=None,
                    execution_phase=phase,
                    owner_apply_record_digest=None,
                    configuration_digest=None,
                    apply_ledger_entry_digest=None,
                    consumer_module=POLICY_CONSUMER_MODULE,
                )["execution_evidence_digest"]
            ),
        )

    if request.configuration.configuration_status != STATUS_MATERIALIZED:
        reason_codes.append("CONFIGURATION_NOT_MATERIALIZED")

    if reason_codes:
        return _deny(
            reason_codes,
            execution_phase=phase,
            real_authorized=real_authorized,
        )

    policy_result = evaluate_explicit_owner_productive_apply_policy_edge_v1(
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1(
            owner_apply_input=request.owner_apply_input,
            per_ingress_binding=request.per_ingress_binding,
            authorization=request.authorization,
            configuration=request.configuration,
            registry_digest=request.registry_digest,
            evaluation_time_utc=request.evaluation_time_utc,
        )
    )
    if policy_result.policy_edge_status != POLICY_EDGE_STATUS_BOUND:
        return _deny(
            list(policy_result.reason_codes) or ["POLICY_EDGE_NOT_BOUND"],
            policy_edge_status=policy_result.policy_edge_status,
            execution_phase=phase,
            real_authorized=real_authorized,
        )

    apply_result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=request.owner_apply_input,
            per_ingress_binding=request.per_ingress_binding,
            authorization=request.authorization,
            configuration=request.configuration,
            registry_digest=request.registry_digest,
            ledger_paths=request.ledger_paths,
            evaluation_time_utc=request.evaluation_time_utc,
        )
    )
    if (
        not apply_result.productive_apply_authorized
        or apply_result.configuration_after_apply is None
    ):
        return _deny(
            list(apply_result.reason_codes) or ["APPLY_ADJUDICATION_DENIED"],
            policy_edge_status=POLICY_EDGE_STATUS_BOUND,
            execution_phase=phase,
            real_authorized=real_authorized,
        )

    config_after = apply_result.configuration_after_apply
    record = config_after.configuration_record
    config_digest = str(config_after.configuration_digest or "")
    if record is not None:
        if record.get("candidate_value_applied") is True:
            return _deny(
                ["CANDIDATE_VALUE_APPLIED_FORBIDDEN"],
                policy_edge_status=POLICY_EDGE_STATUS_BOUND,
                execution_phase=phase,
                real_authorized=real_authorized,
            )
        if str(record.get("productive_target_id") or "") != PRODUCTIVE_TARGET_ID:
            return _deny(
                ["PRODUCTIVE_TARGET_MISMATCH"],
                policy_edge_status=POLICY_EDGE_STATUS_BOUND,
                execution_phase=phase,
                real_authorized=real_authorized,
            )

    productive_occurred = (
        request.execution_phase is F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY
        and real_authorized
        and apply_result.apply_status == STATUS_APPLY_AUTHORIZED
    )
    if productive_occurred:
        return _deny(
            ["PRODUCTIVE_APPLY_OCCURRED_FORBIDDEN_IN_CURRENT_GO"],
            policy_edge_status=POLICY_EDGE_STATUS_BOUND,
            execution_phase=phase,
            real_authorized=real_authorized,
        )

    evidence = build_execution_evidence_record_v1(
        policy_edge_status=POLICY_EDGE_STATUS_BOUND,
        apply_status=apply_result.apply_status,
        execution_phase=phase,
        owner_apply_record_digest=apply_result.owner_apply_authorization_record_digest,
        configuration_digest=config_digest or None,
        apply_ledger_entry_digest=apply_result.apply_ledger_entry_digest,
        consumer_module=POLICY_CONSUMER_MODULE,
    )

    return F1M9ProductiveApplyExecutionResultV1(
        execution_status=STATUS_EXECUTION_READY,
        reason_codes=("F1_M9_EXECUTION_BOUNDARY_OK",),
        policy_edge_status=POLICY_EDGE_STATUS_BOUND,
        apply_status=apply_result.apply_status,
        execution_phase=phase,
        productive_apply_occurred=False,
        productive_apply_authorized=apply_result.productive_apply_authorized,
        real_productive_apply_authorized=real_authorized,
        runtime_apply_authority=apply_result.runtime_apply_authority,
        authority_edge_id=AUTHORITY_EDGE_ID,
        consumer_module=POLICY_CONSUMER_MODULE,
        configuration_after_execution=config_after,
        owner_apply_authorization_record_digest=apply_result.owner_apply_authorization_record_digest,
        apply_ledger_entry_digest=apply_result.apply_ledger_entry_digest,
        execution_evidence_digest=str(evidence["execution_evidence_digest"]),
    )


__all__ = [
    "APPLY_ADJUDICATOR_MODULE",
    "CLOSED_EXECUTION_BLOCKER",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "F1M9ProductiveApplyExecutionPhaseV1",
    "F1M9ProductiveApplyExecutionRequestV1",
    "F1M9ProductiveApplyExecutionResultV1",
    "NEXT_TRUE_BLOCKER",
    "NORMATIVE_SPEC",
    "POLICY_EDGE_MODULE",
    "PREDECESSOR_DECISION",
    "PRODUCTIVE_APPLY_OCCURRED",
    "PROMOTION_AUTHORITY_CHANGED",
    "SCHEMA_VERSION",
    "SELECTION_AUTHORITY_CHANGED",
    "STATUS_EXECUTION_DENIED",
    "STATUS_EXECUTION_READY",
    "STATUS_REAL_APPLY_BLOCKED",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "build_execution_evidence_record_v1",
    "evaluate_f1_m9_productive_apply_execution_boundary_v1",
    "load_execution_boundary_decision_v1",
    "real_productive_apply_authorized_v1",
]
