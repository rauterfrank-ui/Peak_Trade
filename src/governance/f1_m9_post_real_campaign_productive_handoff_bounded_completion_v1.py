"""Bounded POST-REAL-CAMPAIGN productive handoff (stops before threshold enforcement)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.authorized_productive_parameter_seam_v1 import (
    AuthorizedProductiveParameterSeamBindRequestV1,
    STATUS_BOUND as SEAM_STATUS_BOUND,
    bind_authorized_productive_parameter_seam_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    STATUS_AUTHORIZED_BOUNDARY,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    parse_aware_utc_datetime_v1,
)
from src.governance.f1_m9_owner_apply_record_materialization_v1 import (
    STATUS_MATERIALIZED as OWNER_APPLY_RECORD_MATERIALIZED,
    materialize_owner_apply_record_when_canonical_candidate_resolved_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_post_real_campaign_optimization_governance_ingress_v1 import (
    build_f1_m9_post_real_campaign_optimization_governance_ingress_v1,
)
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    verify_f1_m9_prospective_real_campaign_durable_evidence_v1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    F1M9ProductiveApplyExecutionPhaseV1,
    F1M9ProductiveApplyExecutionRequestV1,
    STATUS_PRODUCTIVE_APPLY_COMPLETED,
    evaluate_f1_m9_productive_apply_execution_boundary_v1,
    load_execution_boundary_decision_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.f1_m9_real_productive_apply_decision_binding_v1 import (
    STATUS_BOUND as DECISION_BINDING_BOUND,
    evaluate_real_productive_apply_decision_binding_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    STATUS_MATERIALIZED as CONFIG_STATUS_MATERIALIZED,
    materialize_governed_productive_configuration_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    STATUS_TRANSPORT_READY,
    resolve_governed_runtime_seam_for_presence_gate_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "f1_m9_post_real_campaign_productive_handoff_bounded_completion/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETION_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_post_real_campaign_productive_handoff_v1_decision_v1.json"
)

from src.governance.f1_m9_post_real_campaign_productive_handoff_artifacts_v1 import (
    load_explicit_productive_authorization_artifact_v1,
    persist_explicit_productive_authorization_artifact_v1,
)

DEFAULT_RUNTIME_AUTHORIZATION_ID: Final[str] = "F1_M9_POST_6800_REAL_RUN_20260924T224821Z"
DEFAULT_SELECTED_CANDIDATE_ID: Final[str] = "CANDIDATE_600_S"
DEFAULT_SELECTED_MAX_AGE_SECONDS: Final[int] = 600

THRESHOLD_ENFORCEMENT_AUTHORIZED: Final[bool] = False


def _load_handoff_decision_v1(*, repo_root: Path) -> dict[str, Any]:
    path = repo_root / DECISION_CONFIG
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _apply_window_from_decision_v1(
    *,
    repo_root: Path,
    evaluation_time_utc: datetime | None,
) -> tuple[datetime, datetime]:
    decision = _load_handoff_decision_v1(repo_root=repo_root)
    not_before_raw = str(decision.get("owner_apply_not_before_utc") or "")
    expires_raw = str(decision.get("owner_apply_expires_at_utc") or "")
    if not_before_raw and expires_raw:
        return (
            parse_aware_utc_datetime_v1(not_before_raw, field_name="owner_apply_not_before_utc"),
            parse_aware_utc_datetime_v1(expires_raw, field_name="owner_apply_expires_at_utc"),
        )
    now = evaluation_time_utc or datetime.now(timezone.utc)
    return now, now.replace(year=now.year + 1)


@dataclass(frozen=True, slots=True)
class F1M9PostRealCampaignHandoffResultV1:
    handoff_status: str
    reason_codes: tuple[str, ...]
    durable_evidence_verified: bool
    evidence_bundle_digest: str | None
    explicit_productive_authorization_present: bool
    productive_authorization_digest: str | None
    governed_productive_configuration_bound: bool
    owner_apply_record_bound: bool
    owner_apply_record_digest: str | None
    real_productive_apply_authorized: bool
    authorized_productive_parameter_seam_bound: bool
    authorized_parameter: str
    authorized_value: int | None
    threshold_enforcement_authorized: bool
    trading_decision_effect_occurred: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorized_parameter": self.authorized_parameter,
            "authorized_productive_parameter_seam_bound": (
                self.authorized_productive_parameter_seam_bound
            ),
            "authorized_value": self.authorized_value,
            "durable_evidence_verified": self.durable_evidence_verified,
            "evidence_bundle_digest": self.evidence_bundle_digest,
            "explicit_productive_authorization_present": (
                self.explicit_productive_authorization_present
            ),
            "governed_productive_configuration_bound": (
                self.governed_productive_configuration_bound
            ),
            "handoff_status": self.handoff_status,
            "owner_apply_record_bound": self.owner_apply_record_bound,
            "owner_apply_record_digest": self.owner_apply_record_digest,
            "productive_authorization_digest": self.productive_authorization_digest,
            "real_productive_apply_authorized": self.real_productive_apply_authorized,
            "reason_codes": list(self.reason_codes),
            "threshold_enforcement_authorized": self.threshold_enforcement_authorized,
            "trading_decision_effect_occurred": self.trading_decision_effect_occurred,
        }


def evaluate_f1_m9_post_real_campaign_productive_handoff_v1(
    *,
    repo_root: Path | None = None,
    ledger_paths: F1M9ProductiveApplyLedgerPathsV1,
    runtime_authorization_id: str = DEFAULT_RUNTIME_AUTHORIZATION_ID,
    selected_candidate_id: str = DEFAULT_SELECTED_CANDIDATE_ID,
    selected_max_age_seconds: int = DEFAULT_SELECTED_MAX_AGE_SECONDS,
    persist_explicit_authorization_artifact: bool = False,
    evaluation_time_utc: datetime | None = None,
) -> F1M9PostRealCampaignHandoffResultV1:
    """Run bounded handoff chain; stops before threshold enforcement activation."""
    root = repo_root or Path(__file__).resolve().parents[2]
    reasons: list[str] = []

    verification = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
        repo_root=root,
        expected_runtime_authorization_id=runtime_authorization_id,
        expected_selected_candidate_id=selected_candidate_id,
        expected_selected_max_age_seconds=selected_max_age_seconds,
    )
    if not verification.verified:
        return F1M9PostRealCampaignHandoffResultV1(
            handoff_status="DENIED_FAIL_CLOSED",
            reason_codes=verification.reason_codes,
            durable_evidence_verified=False,
            evidence_bundle_digest=verification.evidence_bundle_digest,
            explicit_productive_authorization_present=False,
            productive_authorization_digest=None,
            governed_productive_configuration_bound=False,
            owner_apply_record_bound=False,
            owner_apply_record_digest=None,
            real_productive_apply_authorized=False,
            authorized_productive_parameter_seam_bound=False,
            authorized_parameter="max_age_seconds",
            authorized_value=verification.selected_max_age_seconds,
            threshold_enforcement_authorized=THRESHOLD_ENFORCEMENT_AUTHORIZED,
            trading_decision_effect_occurred=False,
        )

    ingress = build_f1_m9_post_real_campaign_optimization_governance_ingress_v1(
        verification=verification,
        repo_root=root,
    )
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
        authorizer_identity="F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_OWNER_GO",
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
        reasons.extend(authorization.reason_codes)
        return _deny(reasons, verification)

    auth_artifact = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "campaign_id": verification.campaign_id,
        "evidence_bundle_digest": verification.evidence_bundle_digest,
        "runtime_authorization_id": verification.runtime_authorization_id,
        "authorization_status": authorization.authorization_status,
        "authorization_digest": authorization.authorization_digest,
        "ingress_digest": authorization.ingress_digest,
        "owner_authorization_record_digest": owner_input.owner_authorization_record_digest,
    }
    auth_artifact["artifact_digest"] = compute_content_sha256(
        {k: v for k, v in auth_artifact.items() if k != "artifact_digest"}
    )
    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    if configuration.configuration_status != CONFIG_STATUS_MATERIALIZED:
        reasons.extend(configuration.reason_codes)
        return _deny(reasons, verification)

    persist_explicit_productive_authorization_artifact_v1(auth_artifact, repo_root=root)

    registry = load_scoped_join_registry_v1(repo_root=root)
    binding = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
    )
    not_before, expires_at = _apply_window_from_decision_v1(
        repo_root=root,
        evaluation_time_utc=evaluation_time_utc,
    )
    mat = materialize_owner_apply_record_when_canonical_candidate_resolved_v1(
        registry_digest=str(registry["registry_digest"]),
        ingress_digest=str(ingress["ingress_digest"]),
        binding=binding,
        authorization=authorization,
        configuration=configuration,
        not_before=not_before,
        expires_at=expires_at,
        repo_root=root,
    )
    if (
        mat.materialization_status != OWNER_APPLY_RECORD_MATERIALIZED
        or mat.owner_apply_input is None
    ):
        reasons.extend(mat.reason_codes)
        return _deny(reasons, verification)

    apply_input = mat.owner_apply_input
    decision_binding = evaluate_real_productive_apply_decision_binding_v1(
        owner_apply_authorization_record_digest=apply_input.owner_apply_authorization_record_digest,
        repo_root=root,
    )
    if not decision_binding.apply_permitted:
        reasons.extend(decision_binding.reason_codes)
        return _deny(reasons, verification)

    execution = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            registry_digest=str(registry["registry_digest"]),
            ledger_paths=ledger_paths,
            execution_phase=F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY,
            evaluation_time_utc=not_before,
        ),
        repo_root=root,
    )
    if execution.execution_status != STATUS_PRODUCTIVE_APPLY_COMPLETED:
        reasons.extend(execution.reason_codes)
        return _deny(reasons, verification)

    config_after = execution.configuration_after_execution
    if config_after is None or config_after.configuration_record is None:
        reasons.append("CONFIGURATION_AFTER_APPLY_MISSING")
        return _deny(reasons, verification)

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=config_after)
    )
    if seam.seam_status != SEAM_STATUS_BOUND:
        reasons.extend(seam.reason_codes)
        return _deny(reasons, verification)

    transport = resolve_governed_runtime_seam_for_presence_gate_v1(
        dict(seam.seam_record) if seam.seam_record is not None else None
    )
    if transport.transport_status != STATUS_TRANSPORT_READY:
        reasons.extend(transport.reason_codes)
        return _deny(reasons, verification)

    decision = load_execution_boundary_decision_v1(repo_root=root)
    real_apply_auth = decision.get("real_productive_apply_authorized") is True

    return F1M9PostRealCampaignHandoffResultV1(
        handoff_status="F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETE",
        reason_codes=tuple(reasons),
        durable_evidence_verified=True,
        evidence_bundle_digest=verification.evidence_bundle_digest,
        explicit_productive_authorization_present=True,
        productive_authorization_digest=authorization.authorization_digest,
        governed_productive_configuration_bound=True,
        owner_apply_record_bound=True,
        owner_apply_record_digest=apply_input.owner_apply_authorization_record_digest,
        real_productive_apply_authorized=real_apply_auth
        and decision_binding.binding_status == DECISION_BINDING_BOUND,
        authorized_productive_parameter_seam_bound=True,
        authorized_parameter="max_age_seconds",
        authorized_value=selected_max_age_seconds,
        threshold_enforcement_authorized=THRESHOLD_ENFORCEMENT_AUTHORIZED,
        trading_decision_effect_occurred=False,
    )


def _deny(
    reasons: list[str],
    verification: Any,
) -> F1M9PostRealCampaignHandoffResultV1:
    return F1M9PostRealCampaignHandoffResultV1(
        handoff_status="DENIED_FAIL_CLOSED",
        reason_codes=tuple(dict.fromkeys(reasons)),
        durable_evidence_verified=verification.verified,
        evidence_bundle_digest=getattr(verification, "evidence_bundle_digest", None),
        explicit_productive_authorization_present=False,
        productive_authorization_digest=None,
        governed_productive_configuration_bound=False,
        owner_apply_record_bound=False,
        owner_apply_record_digest=None,
        real_productive_apply_authorized=False,
        authorized_productive_parameter_seam_bound=False,
        authorized_parameter="max_age_seconds",
        authorized_value=getattr(verification, "selected_max_age_seconds", None),
        threshold_enforcement_authorized=THRESHOLD_ENFORCEMENT_AUTHORIZED,
        trading_decision_effect_occurred=False,
    )


__all__ = [
    "DECISION_CONFIG",
    "DEFAULT_RUNTIME_AUTHORIZATION_ID",
    "DEFAULT_SELECTED_CANDIDATE_ID",
    "DEFAULT_SELECTED_MAX_AGE_SECONDS",
    "F1M9PostRealCampaignHandoffResultV1",
    "NORMATIVE_SPEC",
    "SCHEMA_VERSION",
    "THRESHOLD_ENFORCEMENT_AUTHORIZED",
    "WORKPACKAGE_ID",
    "evaluate_f1_m9_post_real_campaign_productive_handoff_v1",
]
