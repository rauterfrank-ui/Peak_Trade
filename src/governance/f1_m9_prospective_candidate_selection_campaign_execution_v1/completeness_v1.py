"""Deterministic campaign completeness adjudication for F1/M9 prospective campaign."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    EVIDENCE_SOURCE_FIXTURE,
    EVIDENCE_SOURCE_HISTORICAL,
    EVIDENCE_SOURCE_REAL,
    REQUIREMENT_VERDICT_FAIL,
    REQUIREMENT_VERDICT_INCOMPLETE,
    REQUIREMENT_VERDICT_PASS,
)
from src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1 import (
    assert_decision_evidence_downstream_of_new_preregistration_v1,
)
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    MINIMUM_EVIDENCE_COUNT,
    MINIMUM_REGIME_COUNT,
    MINIMUM_SESSION_COUNT,
)


@dataclass(frozen=True, slots=True)
class F1M9CampaignCompletenessVerdictV1:
    real_evidence_requirement: str
    session_coverage_requirement: str
    regime_coverage_requirement: str
    oos_requirement: str
    robustness_requirement: str
    economic_requirement: str
    failure_evidence_requirement: str
    contamination_requirement: str
    campaign_selection_eligible: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "real_evidence_requirement": self.real_evidence_requirement,
            "session_coverage_requirement": self.session_coverage_requirement,
            "regime_coverage_requirement": self.regime_coverage_requirement,
            "oos_requirement": self.oos_requirement,
            "robustness_requirement": self.robustness_requirement,
            "economic_requirement": self.economic_requirement,
            "failure_evidence_requirement": self.failure_evidence_requirement,
            "contamination_requirement": self.contamination_requirement,
            "campaign_selection_eligible": self.campaign_selection_eligible,
            "reason_codes": list(self.reason_codes),
        }


def _verdict_all_pass(verdict: F1M9CampaignCompletenessVerdictV1) -> bool:
    fields = (
        verdict.real_evidence_requirement,
        verdict.session_coverage_requirement,
        verdict.regime_coverage_requirement,
        verdict.oos_requirement,
        verdict.robustness_requirement,
        verdict.economic_requirement,
        verdict.failure_evidence_requirement,
        verdict.contamination_requirement,
    )
    return all(v == REQUIREMENT_VERDICT_PASS for v in fields)


def adjudicate_campaign_completeness_v1(
    sealed_bundle: Mapping[str, Any],
    *,
    repo_root=None,
) -> F1M9CampaignCompletenessVerdictV1:
    reasons: list[str] = []
    source_class = str(sealed_bundle.get("evidence_source_class") or "")
    if source_class == EVIDENCE_SOURCE_FIXTURE:
        real_v = REQUIREMENT_VERDICT_FAIL
        reasons.append("FIXTURE_CANNOT_SATISFY_REAL")
    elif source_class == EVIDENCE_SOURCE_HISTORICAL:
        real_v = REQUIREMENT_VERDICT_FAIL
        reasons.append("HISTORICAL_CANNOT_SATISFY_REAL")
    elif source_class == EVIDENCE_SOURCE_REAL:
        real_v = REQUIREMENT_VERDICT_PASS
    else:
        real_v = REQUIREMENT_VERDICT_INCOMPLETE
        reasons.append("REAL_EVIDENCE_SOURCE_UNKNOWN")

    session_count = int(sealed_bundle.get("session_count") or 0)
    regime_count = int(sealed_bundle.get("regime_count") or 0)
    evidence_count = int(sealed_bundle.get("evidence_count") or 0)

    session_v = (
        REQUIREMENT_VERDICT_PASS
        if session_count >= MINIMUM_SESSION_COUNT
        else REQUIREMENT_VERDICT_INCOMPLETE
        if session_count > 0
        else REQUIREMENT_VERDICT_FAIL
    )
    regime_v = (
        REQUIREMENT_VERDICT_PASS
        if regime_count >= MINIMUM_REGIME_COUNT
        else REQUIREMENT_VERDICT_INCOMPLETE
        if regime_count > 0
        else REQUIREMENT_VERDICT_FAIL
    )

    oos = sealed_bundle.get("oos_evidence") or {}
    oos_v = (
        REQUIREMENT_VERDICT_PASS if oos.get("holdout_pass") is True else REQUIREMENT_VERDICT_FAIL
    )
    if oos.get("present") is not True and oos_v == REQUIREMENT_VERDICT_FAIL:
        oos_v = REQUIREMENT_VERDICT_INCOMPLETE

    robust = sealed_bundle.get("robustness_evidence") or {}
    robust_v = (
        REQUIREMENT_VERDICT_PASS
        if robust.get("robustness_pass") is True
        else REQUIREMENT_VERDICT_FAIL
    )
    if robust.get("present") is not True and robust_v == REQUIREMENT_VERDICT_FAIL:
        robust_v = REQUIREMENT_VERDICT_INCOMPLETE

    econ = sealed_bundle.get("economic_evidence") or {}
    econ_v = (
        REQUIREMENT_VERDICT_PASS if econ.get("economic_pass") is True else REQUIREMENT_VERDICT_FAIL
    )
    if econ.get("present") is not True and econ_v == REQUIREMENT_VERDICT_FAIL:
        econ_v = REQUIREMENT_VERDICT_INCOMPLETE

    failure = sealed_bundle.get("failure_evidence") or {}
    failure_v = REQUIREMENT_VERDICT_PASS
    if failure.get("rejection_matrix_present") is not True:
        failure_v = REQUIREMENT_VERDICT_INCOMPLETE
    elif failure.get("rejection_reasons_complete") is not True:
        failure_v = REQUIREMENT_VERDICT_FAIL

    leakage = assert_decision_evidence_downstream_of_new_preregistration_v1(
        sealed_bundle, repo_root=repo_root
    )
    contamination_v = (
        REQUIREMENT_VERDICT_FAIL
        if leakage.get("historical_evidence_decision_leakage")
        else REQUIREMENT_VERDICT_PASS
    )
    if contamination_v == REQUIREMENT_VERDICT_FAIL:
        reasons.append("CONTAMINATION_LEAKAGE")

    if evidence_count < MINIMUM_EVIDENCE_COUNT:
        reasons.append("INSUFFICIENT_EVIDENCE_COUNT")
        if real_v == REQUIREMENT_VERDICT_PASS:
            real_v = REQUIREMENT_VERDICT_INCOMPLETE

    verdict = F1M9CampaignCompletenessVerdictV1(
        real_evidence_requirement=real_v,
        session_coverage_requirement=session_v,
        regime_coverage_requirement=regime_v,
        oos_requirement=oos_v,
        robustness_requirement=robust_v,
        economic_requirement=econ_v,
        failure_evidence_requirement=failure_v,
        contamination_requirement=contamination_v,
        campaign_selection_eligible=False,
        reason_codes=tuple(sorted(set(reasons))),
    )
    eligible = _verdict_all_pass(verdict) and sealed_bundle.get("campaign_sealed") is True
    return F1M9CampaignCompletenessVerdictV1(
        real_evidence_requirement=verdict.real_evidence_requirement,
        session_coverage_requirement=verdict.session_coverage_requirement,
        regime_coverage_requirement=verdict.regime_coverage_requirement,
        oos_requirement=verdict.oos_requirement,
        robustness_requirement=verdict.robustness_requirement,
        economic_requirement=verdict.economic_requirement,
        failure_evidence_requirement=verdict.failure_evidence_requirement,
        contamination_requirement=verdict.contamination_requirement,
        campaign_selection_eligible=eligible,
        reason_codes=verdict.reason_codes,
    )


__all__ = [
    "F1M9CampaignCompletenessVerdictV1",
    "adjudicate_campaign_completeness_v1",
]
