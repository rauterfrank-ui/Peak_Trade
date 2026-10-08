"""Integrated offline economic validity adjudication v1 (AUTHORITY=NONE)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.ops.integrated_offline_economic_evidence_v1.integrated_verifier_v1 import (
    IntegratedOfflineEconomicEvidenceVerificationResultV1,
    verify_integrated_offline_economic_evidence_v1,
)

ADJUDICATION_ID = "ops.integrated_offline_economic_validity_adjudication_v1"
AUTHORITY_EFFECT_NONE = "NONE"


@dataclass
class IntegratedOfflineEconomicValidityAdjudicationResultV1:
    economic_validity_evaluated: bool
    economic_validity_pass: bool
    offline_economic_evidence_complete: bool
    walk_forward_verified: bool
    monte_carlo_verified: bool
    stress_verified: bool
    walk_forward_monte_carlo_stress_requirements_met: bool
    walk_forward_policy_pass: bool
    monte_carlo_policy_pass: bool
    stress_policy_pass: bool
    operator_ratification_required: bool = True
    failure_reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjudication_id": ADJUDICATION_ID,
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "economic_validity_evaluated": self.economic_validity_evaluated,
            "economic_validity_pass": self.economic_validity_pass,
            "offline_economic_evidence_complete": self.offline_economic_evidence_complete,
            "walk_forward_verified": self.walk_forward_verified,
            "monte_carlo_verified": self.monte_carlo_verified,
            "stress_verified": self.stress_verified,
            "walk_forward_monte_carlo_stress_requirements_met": (
                self.walk_forward_monte_carlo_stress_requirements_met
            ),
            "walk_forward_policy_pass": self.walk_forward_policy_pass,
            "monte_carlo_policy_pass": self.monte_carlo_policy_pass,
            "stress_policy_pass": self.stress_policy_pass,
            "operator_ratification_required": self.operator_ratification_required,
            "failure_reasons": list(self.failure_reasons),
            "blockers": list(self.blockers),
            "promotion_pass": False,
        }


def evaluate_integrated_offline_economic_validity_v1(
    *,
    repo_root: Path,
    evidence_root: Path,
    expected_proven_source_sha: str | None = None,
    verification: IntegratedOfflineEconomicEvidenceVerificationResultV1 | None = None,
    min_trades_for_policy_pass: int = 1,
) -> IntegratedOfflineEconomicValidityAdjudicationResultV1:
    """Derive economic validity from verified evidence only; never grants execution authority."""
    root = repo_root.resolve()
    blockers: list[str] = []
    failure_reasons: list[str] = []

    result = verification or verify_integrated_offline_economic_evidence_v1(
        repo_root=root,
        evidence_root=evidence_root,
        expected_proven_source_sha=expected_proven_source_sha,
    )
    if not result.verified:
        blockers.extend(result.blockers)
        return IntegratedOfflineEconomicValidityAdjudicationResultV1(
            economic_validity_evaluated=False,
            economic_validity_pass=False,
            offline_economic_evidence_complete=False,
            walk_forward_verified=False,
            monte_carlo_verified=False,
            stress_verified=False,
            walk_forward_monte_carlo_stress_requirements_met=False,
            walk_forward_policy_pass=False,
            monte_carlo_policy_pass=False,
            stress_policy_pass=False,
            blockers=sorted(set(blockers)),
        )

    wf_ok = result.walk_forward_verified
    mc_ok = result.monte_carlo_verified
    stress_ok = result.stress_verified
    wf_mc_stress_met = wf_ok and mc_ok and stress_ok

    import json

    from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import INTEGRATED_ARTIFACT

    index_path = evidence_root / INTEGRATED_ARTIFACT
    index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    metrics_ref = index_doc.get("economic_metrics_domain_ref") or {}
    metrics_path = root / str(metrics_ref.get("artifact_relpath") or "")
    metrics_doc = (
        json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.is_file() else {}
    )
    trade_count = int(metrics_doc.get("trade_count") or 0)
    net_pnl = str(metrics_doc.get("net_pnl") or "0")

    wf_policy_pass = bool(metrics_doc.get("walk_forward_pass", True)) if wf_ok else False
    mc_policy_pass = mc_ok
    stress_policy_pass = stress_ok

    if trade_count < min_trades_for_policy_pass:
        failure_reasons.append("ECONOMIC_ZERO_OR_INSUFFICIENT_TRADES")
    try:
        if trade_count >= min_trades_for_policy_pass and float(net_pnl) <= 0:
            failure_reasons.append("ECONOMIC_NON_POSITIVE_NET_PNL")
    except ValueError:
        failure_reasons.append("ECONOMIC_NET_PNL_UNPARSEABLE")

    economic_pass = wf_mc_stress_met and not failure_reasons
    return IntegratedOfflineEconomicValidityAdjudicationResultV1(
        economic_validity_evaluated=True,
        economic_validity_pass=economic_pass,
        offline_economic_evidence_complete=result.offline_economic_evidence_complete,
        walk_forward_verified=wf_ok,
        monte_carlo_verified=mc_ok,
        stress_verified=stress_ok,
        walk_forward_monte_carlo_stress_requirements_met=wf_mc_stress_met,
        walk_forward_policy_pass=wf_policy_pass,
        monte_carlo_policy_pass=mc_policy_pass,
        stress_policy_pass=stress_policy_pass,
        failure_reasons=failure_reasons,
        blockers=blockers,
    )
