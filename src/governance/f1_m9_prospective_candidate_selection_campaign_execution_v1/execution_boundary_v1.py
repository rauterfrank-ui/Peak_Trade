"""F1/M9 prospective candidate-selection campaign execution boundary v1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    DECISION_CONFIG,
    EXECUTION_OWNER_ID,
    NEXT_TRUE_BLOCKER,
    PREREGISTRATION_CONFIG,
    PREREGISTRATION_DIGEST,
    PREREGISTRATION_ID,
    SELECTION_POLICY_CONFIG,
    SELECTION_POLICY_DIGEST,
    SELECTION_POLICY_ID,
    SELECTION_RULE_ID,
    STATUS_AUTHORIZED_PATH_READY,
    STATUS_EXECUTION_DENIED,
    STATUS_EXECUTION_PROOF_PASS,
    WORKPACKAGE_ID,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.durable_paths_v1 import (
    resolve_f1_m9_prospective_campaign_durable_paths_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.evidence_writer_v1 import (
    CampaignEvidenceWriteDeniedError,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_census_v1 import (
    run_f1_m9_prospective_campaign_execution_census_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_md_supplier_v1 import (
    resolve_real_md_supplier_binding_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    resolve_runtime_authorization_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_preregistration_v1 import (
    load_prospective_candidate_selection_campaign_preregistration_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    load_owner_selection_policy_v1,
)

CAMPAIGN_EXECUTED: Final[bool] = False
NEW_DECISION_MAKING_EVIDENCE_GENERATED: Final[bool] = False
PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED: Final[bool] = False
EXCHANGE_PRIVATE_TRADING_EFFECT_OCCURRED: Final[bool] = False
ORDER_EFFECT_OCCURRED: Final[bool] = False


class F1M9ProspectiveCampaignExecutionPhaseV1(str, Enum):
    EXECUTION_PROOF = "EXECUTION_PROOF"
    AUTHORIZED_CAMPAIGN_EXECUTION = "AUTHORIZED_CAMPAIGN_EXECUTION"


@dataclass(frozen=True, slots=True)
class F1M9ProspectiveCampaignExecutionRequestV1:
    execution_phase: F1M9ProspectiveCampaignExecutionPhaseV1
    runtime_authorization: Mapping[str, Any] | None = None
    evaluation_time_utc: datetime | None = None
    repo_root: Path | None = None


@dataclass(frozen=True, slots=True)
class F1M9ProspectiveCampaignExecutionResultV1:
    execution_status: str
    execution_phase: str
    reason_codes: tuple[str, ...]
    campaign_executed: bool
    public_market_data_read_requested: bool
    durable_evidence_write_requested: bool
    trading_decision_authority: bool
    promotion_authority: bool
    productive_apply_authority: bool
    direct_productive_write_authority: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_status": self.execution_status,
            "execution_phase": self.execution_phase,
            "reason_codes": list(self.reason_codes),
            "campaign_executed": self.campaign_executed,
            "public_market_data_read_requested": self.public_market_data_read_requested,
            "durable_evidence_write_requested": self.durable_evidence_write_requested,
            "trading_decision_authority": self.trading_decision_authority,
            "promotion_authority": self.promotion_authority,
            "productive_apply_authority": self.productive_apply_authority,
            "direct_productive_write_authority": self.direct_productive_write_authority,
        }


def _verify_frozen_chain_v1(*, repo_root: Path) -> tuple[str, ...]:
    reasons: list[str] = []
    prereg = load_prospective_candidate_selection_campaign_preregistration_v1(repo_root=repo_root)
    policy = load_owner_selection_policy_v1(repo_root=repo_root)
    if str(prereg.get("campaign_id") or "") != CAMPAIGN_ID:
        reasons.append("CAMPAIGN_ID_DRIFT")
    if str(prereg.get("preregistration_id") or "") != PREREGISTRATION_ID:
        reasons.append("PREREGISTRATION_ID_DRIFT")
    if str(prereg.get("preregistration_digest") or "") != PREREGISTRATION_DIGEST:
        reasons.append("PREREGISTRATION_DIGEST_DRIFT")
    if str(policy.get("owner_selection_policy_id") or "") != SELECTION_POLICY_ID:
        reasons.append("SELECTION_POLICY_ID_DRIFT")
    if str(policy.get("owner_selection_policy_digest") or "") != SELECTION_POLICY_DIGEST:
        reasons.append("SELECTION_POLICY_DIGEST_DRIFT")
    rule_id = str((policy.get("selection_rule") or {}).get("selection_rule_id") or "")
    if rule_id != SELECTION_RULE_ID:
        reasons.append("SELECTION_RULE_DRIFT")
    return tuple(reasons)


def evaluate_f1_m9_prospective_campaign_execution_v1(
    request: F1M9ProspectiveCampaignExecutionRequestV1,
) -> F1M9ProspectiveCampaignExecutionResultV1:
    root = request.repo_root or Path(__file__).resolve().parents[3]
    chain_reasons = _verify_frozen_chain_v1(repo_root=root)
    if chain_reasons:
        return F1M9ProspectiveCampaignExecutionResultV1(
            execution_status=STATUS_EXECUTION_DENIED,
            execution_phase=request.execution_phase.value,
            reason_codes=chain_reasons,
            campaign_executed=False,
            public_market_data_read_requested=False,
            durable_evidence_write_requested=False,
            trading_decision_authority=False,
            promotion_authority=False,
            productive_apply_authority=False,
            direct_productive_write_authority=False,
        )

    if request.execution_phase == F1M9ProspectiveCampaignExecutionPhaseV1.EXECUTION_PROOF:
        md = resolve_real_md_supplier_binding_v1(repo_root=root)
        if md.get("missing_real_md_execution_dependency"):
            return F1M9ProspectiveCampaignExecutionResultV1(
                execution_status=STATUS_EXECUTION_DENIED,
                execution_phase=request.execution_phase.value,
                reason_codes=("MISSING_REAL_MD_EXECUTION_DEPENDENCY",),
                campaign_executed=False,
                public_market_data_read_requested=False,
                durable_evidence_write_requested=False,
                trading_decision_authority=False,
                promotion_authority=False,
                productive_apply_authority=False,
                direct_productive_write_authority=False,
            )
        run_f1_m9_prospective_campaign_execution_census_v1(repo_root=root)
        resolve_f1_m9_prospective_campaign_durable_paths_v1(repo_root=root)
        return F1M9ProspectiveCampaignExecutionResultV1(
            execution_status=STATUS_EXECUTION_PROOF_PASS,
            execution_phase=request.execution_phase.value,
            reason_codes=(),
            campaign_executed=False,
            public_market_data_read_requested=False,
            durable_evidence_write_requested=False,
            trading_decision_authority=False,
            promotion_authority=False,
            productive_apply_authority=False,
            direct_productive_write_authority=False,
        )

    auth, auth_reasons = resolve_runtime_authorization_v1(
        request.runtime_authorization,
        evaluation_time_utc=request.evaluation_time_utc,
    )
    if auth is None or auth_reasons:
        return F1M9ProspectiveCampaignExecutionResultV1(
            execution_status=STATUS_EXECUTION_DENIED,
            execution_phase=request.execution_phase.value,
            reason_codes=auth_reasons or ("RUNTIME_AUTHORIZATION_INVALID",),
            campaign_executed=False,
            public_market_data_read_requested=False,
            durable_evidence_write_requested=False,
            trading_decision_authority=False,
            promotion_authority=False,
            productive_apply_authority=False,
            direct_productive_write_authority=False,
        )

    wants_network = auth.public_market_data_read_authorized
    wants_write = auth.durable_evidence_write_authorized
    reasons: list[str] = []

    if auth.campaign_execution_authorized and not auth.public_market_data_read_authorized:
        reasons.append("REAL_PUBLIC_MD_READ_NOT_AUTHORIZED")
    if auth.campaign_execution_authorized and not auth.durable_evidence_write_authorized:
        reasons.append("DURABLE_EVIDENCE_WRITE_NOT_AUTHORIZED")

    if auth.campaign_execution_authorized and auth.durable_evidence_write_authorized:
        pass
    elif auth.campaign_execution_authorized:
        try:
            paths = resolve_f1_m9_prospective_campaign_durable_paths_v1(repo_root=root)
            from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.evidence_writer_v1 import (
                write_campaign_artifact_v1,
            )

            write_campaign_artifact_v1(
                artifact_path=paths.artifact_path("campaign_manifest.json"),
                payload={
                    "campaign_id": CAMPAIGN_ID,
                    "preregistration_digest": PREREGISTRATION_DIGEST,
                },
                durable_evidence_write_authorized=False,
            )
        except CampaignEvidenceWriteDeniedError:
            if "DURABLE_EVIDENCE_WRITE_NOT_AUTHORIZED" not in reasons:
                reasons.append("EVIDENCE_WRITE_BLOCKED_BY_AUTHORIZATION")

    status = STATUS_EXECUTION_DENIED if reasons else STATUS_AUTHORIZED_PATH_READY
    return F1M9ProspectiveCampaignExecutionResultV1(
        execution_status=status,
        execution_phase=request.execution_phase.value,
        reason_codes=tuple(reasons),
        campaign_executed=False,
        public_market_data_read_requested=wants_network,
        durable_evidence_write_requested=wants_write,
        trading_decision_authority=False,
        promotion_authority=False,
        productive_apply_authority=False,
        direct_productive_write_authority=False,
    )


def prove_execution_proof_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[3]
    result = evaluate_f1_m9_prospective_campaign_execution_v1(
        F1M9ProspectiveCampaignExecutionRequestV1(
            execution_phase=F1M9ProspectiveCampaignExecutionPhaseV1.EXECUTION_PROOF,
            repo_root=root,
        )
    )
    return result.execution_status == STATUS_EXECUTION_PROOF_PASS


def execution_owner_metadata_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    decision_path = root / DECISION_CONFIG
    decision = (
        json.loads(decision_path.read_text(encoding="utf-8")) if decision_path.is_file() else {}
    )
    return {
        "execution_owner_id": EXECUTION_OWNER_ID,
        "workpackage_id": WORKPACKAGE_ID,
        "campaign_id": CAMPAIGN_ID,
        "preregistration_config": PREREGISTRATION_CONFIG,
        "selection_policy_config": SELECTION_POLICY_CONFIG,
        "next_true_blocker": decision.get("next_true_blocker", NEXT_TRUE_BLOCKER),
        "runtime_authorization_active": decision.get("runtime_authorization_active", False),
    }


__all__ = [
    "CAMPAIGN_EXECUTED",
    "EXCHANGE_PRIVATE_TRADING_EFFECT_OCCURRED",
    "F1M9ProspectiveCampaignExecutionPhaseV1",
    "F1M9ProspectiveCampaignExecutionRequestV1",
    "F1M9ProspectiveCampaignExecutionResultV1",
    "NEW_DECISION_MAKING_EVIDENCE_GENERATED",
    "ORDER_EFFECT_OCCURRED",
    "PUBLIC_MARKET_DATA_EXTERNAL_READ_OCCURRED",
    "evaluate_f1_m9_prospective_campaign_execution_v1",
    "execution_owner_metadata_v1",
    "prove_execution_proof_v1",
]
