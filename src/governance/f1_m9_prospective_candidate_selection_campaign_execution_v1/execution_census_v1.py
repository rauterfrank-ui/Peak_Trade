"""Read-only execution census for F1/M9 prospective campaign execution owner build."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    REAL_MD_SUPPLIER_ID,
    REAL_MD_SUPPLIER_MODULE,
    WORKPACKAGE_ID,
)

CensusClassification = str

REUSE_CURRENT: Final[CensusClassification] = "REUSE_CURRENT"
ADAPT_REQUIRED: Final[CensusClassification] = "ADAPT_REQUIRED"
NOT_AUTHORIZED: Final[CensusClassification] = "NOT_AUTHORIZED_FOR_THIS_CAMPAIGN"
MISSING: Final[CensusClassification] = "MISSING"


def run_f1_m9_prospective_campaign_execution_census_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]

    def _module_exists(dotted: str) -> bool:
        parts = dotted.split(".")
        path = root / "src" / "/".join(parts[:-1]) / f"{parts[-1]}.py"
        if path.is_file():
            return True
        pkg = root / "src" / "/".join(parts) / "__init__.py"
        return pkg.is_file()

    entries: list[dict[str, Any]] = [
        {
            "component_id": "A_REAL_PUBLIC_MD_ACQUISITION",
            "classification": REUSE_CURRENT
            if _module_exists(REAL_MD_SUPPLIER_MODULE.rsplit(".", 1)[0])
            else MISSING,
            "reuse_target": REAL_MD_SUPPLIER_MODULE,
            "supplier_id": REAL_MD_SUPPLIER_ID,
            "notes": "Preregistered OKX-EEA public REST MD; no credentials/orders.",
        },
        {
            "component_id": "B_CAMPAIGN_SESSION_RUNNER",
            "classification": ADAPT_REQUIRED,
            "reuse_target": (
                "research.canonical_volatility_numeric_max_age_preregistered_productive_"
                "session_runner_v1.runner_v1"
            ),
            "notes": "Historical R1 runner bound to different preregistration; adapt under F1 owner.",
        },
        {
            "component_id": "C_EVIDENCE_MATERIALIZATION",
            "classification": ADAPT_REQUIRED,
            "reuse_target": (
                "research.canonical_volatility_max_age_productive_research_evidence_"
                "accumulation_v1.runtime_v1"
            ),
        },
        {
            "component_id": "D_DURABLE_EVIDENCE_ROOT",
            "classification": REUSE_CURRENT,
            "reuse_target": "f1_m9_prospective durable_paths_v1 resolver",
        },
        {
            "component_id": "E_EVALUATORS_OOS_ROBUSTNESS_ECONOMIC",
            "classification": REUSE_CURRENT,
            "reuse_target": (
                "research.canonical_volatility_numeric_max_age_parameter_research_"
                "execution_v1.evaluator_v1"
            ),
        },
        {
            "component_id": "F_CONTAMINATION_PROVENANCE",
            "classification": REUSE_CURRENT,
            "reuse_target": (
                "src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1"
            ),
        },
        {
            "component_id": "G_DETERMINISTIC_REPLAY",
            "classification": ADAPT_REQUIRED,
            "reuse_target": "research.m9_s1_durable_market_session_evidence_accumulation_v1.runner_v1",
            "notes": "M9 S1 replay is observation-only; F1 owner replay is selection-bound.",
        },
        {
            "component_id": "H_SELECTION_RULE",
            "classification": REUSE_CURRENT,
            "reuse_target": "src.governance.f1_m9_productive_candidate_selection_policy_v1.apply_f1_m9_selection_rule_v1",
        },
        {
            "component_id": "I_LEAKAGE_GUARD",
            "classification": REUSE_CURRENT,
            "reuse_target": (
                "src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1"
            ),
        },
        {
            "component_id": "J_NETWORK_AUTHORIZATION_PATTERN",
            "classification": NOT_AUTHORIZED,
            "reuse_target": (
                "research.canonical_volatility_numeric_max_age_campaign_authorization_v1"
            ),
            "notes": "Historical campaign authorization; F1 prospective uses separate runtime record.",
        },
    ]

    return {
        "workpackage_id": WORKPACKAGE_ID,
        "census_class": "F1_M9_PROSPECTIVE_CAMPAIGN_EXECUTION_READ_ONLY_CENSUS_V1",
        "entries": entries,
        "implementation_reuse_not_authority_reuse": True,
    }


__all__ = [
    "ADAPT_REQUIRED",
    "MISSING",
    "NOT_AUTHORIZED",
    "REUSE_CURRENT",
    "run_f1_m9_prospective_campaign_execution_census_v1",
]
