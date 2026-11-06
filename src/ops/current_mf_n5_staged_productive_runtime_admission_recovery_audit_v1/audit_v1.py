"""Typed audit/evidence bundle (observability only — not authority)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.aggregate_admission_v1 import (
    AggregateMultiLaneAdmissionV1,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.constants_v1 import (
    ATLAS_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    N_GT_1_PRODUCTIVE_AUTHORIZATION,
    PERMIT_MINT_STATUS,
    POST_ALLOWED,
    TERMINAL_BOUNDARY_FAIL_CLOSED,
    TERMINAL_BOUNDARY_PRE_EXTERNAL,
    VENUE_SUBMISSION_STATUS,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.recovery_classification_v1 import (
    ProductiveRuntimeRecoveryClassificationV1,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.staged_cardinality_v1 import (
    StagedTargetCardinalityDecisionV1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import MembershipContextArtifactV1


@dataclass(frozen=True)
class ProductiveN5RuntimeAuditEvidenceV1:
    schema_version: str
    requested_target_cardinality: int
    authorized_productive_cardinality: int
    invocation_cardinality: int
    admission_class: str
    productive_admitted: bool
    occupied_lane_ids: tuple[str, ...]
    membership_instance_id: str
    ordered_instrument_ids: tuple[str, ...]
    per_lane_mv2_dp_provenance: tuple[tuple[str, str, str], ...]
    per_lane_dispositions: tuple[tuple[str, str], ...]
    aggregate_class: str
    aggregate_disposition: str
    portfolio_admitted: bool
    portfolio_active_sum: Decimal
    recovery_lane_class: str
    recovery_portfolio_class: str
    terminal_boundary: str
    external_effect_authorized: bool
    post_allowed: bool
    permit_mint_status: str
    venue_submission_status: str
    n_gt_1_enabled: bool
    multi_future_runtime_authorized: bool
    max_positions_effective: int
    n_gt_1_productive_authorization: bool
    atlas_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "requested_target_cardinality": self.requested_target_cardinality,
            "authorized_productive_cardinality": self.authorized_productive_cardinality,
            "invocation_cardinality": self.invocation_cardinality,
            "admission_class": self.admission_class,
            "productive_admitted": self.productive_admitted,
            "occupied_lane_ids": list(self.occupied_lane_ids),
            "membership_instance_id": self.membership_instance_id,
            "ordered_instrument_ids": list(self.ordered_instrument_ids),
            "per_lane_mv2_dp_provenance": [list(row) for row in self.per_lane_mv2_dp_provenance],
            "per_lane_dispositions": [list(row) for row in self.per_lane_dispositions],
            "aggregate_class": self.aggregate_class,
            "aggregate_disposition": self.aggregate_disposition,
            "portfolio_admitted": self.portfolio_admitted,
            "portfolio_active_sum": str(self.portfolio_active_sum),
            "recovery_lane_class": self.recovery_lane_class,
            "recovery_portfolio_class": self.recovery_portfolio_class,
            "terminal_boundary": self.terminal_boundary,
            "external_effect_authorized": self.external_effect_authorized,
            "post_allowed": self.post_allowed,
            "permit_mint_status": self.permit_mint_status,
            "venue_submission_status": self.venue_submission_status,
            "n_gt_1_enabled": self.n_gt_1_enabled,
            "multi_future_runtime_authorized": self.multi_future_runtime_authorized,
            "max_positions_effective": self.max_positions_effective,
            "n_gt_1_productive_authorization": self.n_gt_1_productive_authorization,
            "atlas_authority": self.atlas_authority,
        }


def build_productive_n5_runtime_audit_evidence_v1(
    *,
    schema_version: str,
    membership: MembershipContextArtifactV1,
    cardinality: StagedTargetCardinalityDecisionV1,
    aggregate: AggregateMultiLaneAdmissionV1,
    occupied_lane_ids: tuple[str, ...],
    per_lane_mv2_dp_provenance: tuple[tuple[str, str, str], ...],
    recovery: ProductiveRuntimeRecoveryClassificationV1,
    terminal_boundary: str,
    portfolio_admitted: bool,
    portfolio_active_sum: Decimal,
) -> ProductiveN5RuntimeAuditEvidenceV1:
    return ProductiveN5RuntimeAuditEvidenceV1(
        schema_version=schema_version,
        requested_target_cardinality=cardinality.requested_target_cardinality,
        authorized_productive_cardinality=cardinality.authorized_productive_cardinality,
        invocation_cardinality=cardinality.invocation_cardinality,
        admission_class=cardinality.admission_class,
        productive_admitted=cardinality.productive_admitted,
        occupied_lane_ids=occupied_lane_ids,
        membership_instance_id=membership.instance_id,
        ordered_instrument_ids=membership.ordered_instrument_ids,
        per_lane_mv2_dp_provenance=per_lane_mv2_dp_provenance,
        per_lane_dispositions=aggregate.per_lane_dispositions,
        aggregate_class=aggregate.aggregate_class,
        aggregate_disposition=aggregate.aggregate_disposition,
        portfolio_admitted=portfolio_admitted,
        portfolio_active_sum=portfolio_active_sum,
        recovery_lane_class=recovery.lane_recovery_class,
        recovery_portfolio_class=recovery.portfolio_restart_class,
        terminal_boundary=terminal_boundary,
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED,
        post_allowed=POST_ALLOWED,
        permit_mint_status=PERMIT_MINT_STATUS,
        venue_submission_status=VENUE_SUBMISSION_STATUS,
        n_gt_1_enabled=bool(N_GT_1_ENABLED),
        multi_future_runtime_authorized=bool(MULTI_FUTURE_RUNTIME_AUTHORIZED),
        max_positions_effective=int(MAX_POSITIONS_EFFECTIVE),
        n_gt_1_productive_authorization=N_GT_1_PRODUCTIVE_AUTHORIZATION,
        atlas_authority=ATLAS_AUTHORITY,
    )
