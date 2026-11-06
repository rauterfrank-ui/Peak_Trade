"""Conditional Owner Apply record materialization (record only; never applies)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationResultV1,
)
from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
    build_owner_apply_authorization_input_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressAuthorizationBindingV1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationResultV1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    build_productive_target_contract_v1 as build_target_contract_v1,
)

SCHEMA_VERSION: Final[str] = "f1_m9_owner_apply_record_materialization/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_V1"

STATUS_NOT_ATTEMPTED: Final[str] = "OWNER_APPLY_RECORD_MATERIALIZATION_NOT_ATTEMPTED"
STATUS_DENIED: Final[str] = "OWNER_APPLY_RECORD_MATERIALIZATION_DENIED"
STATUS_MATERIALIZED: Final[str] = "OWNER_APPLY_RECORD_MATERIALIZED"


@dataclass(frozen=True, slots=True)
class OwnerApplyRecordMaterializationResultV1:
    materialization_status: str
    reason_codes: tuple[str, ...]
    owner_apply_input: OwnerApplyAuthorizationInputV1 | None
    candidate_adjudication: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_adjudication": dict(self.candidate_adjudication),
            "materialization_status": self.materialization_status,
            "owner_apply_record_digest": (
                None
                if self.owner_apply_input is None
                else self.owner_apply_input.owner_apply_authorization_record_digest
            ),
            "reason_codes": list(self.reason_codes),
        }


def materialize_owner_apply_record_when_canonical_candidate_resolved_v1(
    *,
    registry_digest: str,
    ingress_digest: str,
    binding: PerIngressAuthorizationBindingV1,
    authorization: ExplicitProductiveAuthorizationResultV1,
    configuration: GovernedProductiveConfigurationResultV1,
    not_before: datetime,
    expires_at: datetime,
    repo_root: Path | None = None,
) -> OwnerApplyRecordMaterializationResultV1:
    """Fail-closed: no record unless canonical candidate + explicit auth chain is CURRENT."""
    adjudication = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=repo_root)
    adj_dict = adjudication.to_dict()
    if not adjudication.resolved:
        return OwnerApplyRecordMaterializationResultV1(
            materialization_status=STATUS_NOT_ATTEMPTED,
            reason_codes=(adjudication.earliest_blocker, *adjudication.reason_codes),
            owner_apply_input=None,
            candidate_adjudication=adj_dict,
        )
    if not adjudication.explicit_productive_authorization_resolved:
        return OwnerApplyRecordMaterializationResultV1(
            materialization_status=STATUS_DENIED,
            reason_codes=("EXPLICIT_PRODUCTIVE_AUTHORIZATION_NOT_RESOLVED",),
            owner_apply_input=None,
            candidate_adjudication=adj_dict,
        )

    config_record = configuration.configuration_record
    if config_record is None:
        return OwnerApplyRecordMaterializationResultV1(
            materialization_status=STATUS_DENIED,
            reason_codes=("CONFIGURATION_NOT_MATERIALIZED",),
            owner_apply_input=None,
            candidate_adjudication=adj_dict,
        )

    contract = build_target_contract_v1()
    apply_input = build_owner_apply_authorization_input_v1(
        registry_digest=registry_digest,
        ingress_digest=ingress_digest,
        binding_digest=binding.binding_digest,
        owner_authorization_record_digest=str(
            config_record.get("owner_authorization_record_digest") or ""
        ),
        authorization_id=str(config_record.get("authorization_id") or ""),
        authorization_digest=str(config_record.get("authorization_digest") or ""),
        configuration_id=str(config_record.get("configuration_id") or ""),
        configuration_digest=str(config_record.get("configuration_digest") or ""),
        candidate_parameter_value_digest=str(
            config_record.get("candidate_parameter_value_digest") or ""
        ),
        productive_target_id=str(config_record.get("productive_target_id") or ""),
        productive_target_version=str(config_record.get("productive_target_version") or ""),
        productive_target_contract_digest=str(contract["contract_digest"]),
        not_before=not_before.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expires_at=expires_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    return OwnerApplyRecordMaterializationResultV1(
        materialization_status=STATUS_MATERIALIZED,
        reason_codes=("OWNER_APPLY_RECORD_MATERIALIZED",),
        owner_apply_input=apply_input,
        candidate_adjudication=adj_dict,
    )


__all__ = [
    "OwnerApplyRecordMaterializationResultV1",
    "SCHEMA_VERSION",
    "STATUS_MATERIALIZED",
    "STATUS_NOT_ATTEMPTED",
    "WORKPACKAGE_ID",
    "materialize_owner_apply_record_when_canonical_candidate_resolved_v1",
]
