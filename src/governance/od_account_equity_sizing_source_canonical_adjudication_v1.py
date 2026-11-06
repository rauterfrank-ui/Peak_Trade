"""OD_ACCOUNT_EQUITY_SIZING_SOURCE canonical adjudication (non-authorizing)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "OD_ACCOUNT_EQUITY_SIZING_SOURCE_CANONICAL_ADJUDICATION_V1"
ADJUDICATION_CONFIG: Final[str] = (
    "config/governance/od_account_equity_sizing_source_canonical_adjudication_v1.json"
)
RUNBOOK_REL: Final[str] = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAPPING_SPEC_REL: Final[str] = (
    "docs/ops/specs/FULL_CORE_SOURCE_TO_SEMANTIC_MAPPING_AND_"
    "SIZING_PRODUCER_BIND_UNDER_PARALLEL_DECOUPLED_TRACKS_V1.md"
)

INV_SIZE_KEYS: Final[tuple[str, ...]] = (
    "INV-SIZE-01",
    "INV-SIZE-02",
    "INV-SIZE-03",
    "INV-SIZE-04",
    "INV-SIZE-05",
    "INV-SIZE-06",
    "INV-SIZE-07",
    "INV-SIZE-08",
    "INV-SIZE-09",
    "INV-SIZE-10",
)


@dataclass(frozen=True)
class OdAccountEquitySizingSourceAdjudicationV1:
    payload: Mapping[str, Any]

    @property
    def decision_case(self) -> str:
        return str(self.payload.get("decision_case", ""))

    @property
    def canonical_unique_candidate_count(self) -> int:
        return int(self.payload.get("canonical_unique_candidate_count", 0))

    def to_report_v1(self) -> dict[str, Any]:
        sizing = self.payload.get("available_for_sizing", {})
        return {
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "DECISION_CASE": self.decision_case,
            "CANONICALLY_UNIQUE_CANDIDATE_COUNT": self.canonical_unique_candidate_count,
            "AVAILABLE_FOR_SIZING_CANONICAL_MEANING": sizing.get("canonical_meaning"),
            "AVAILABLE_FOR_SIZING_TRANSFORMATION": sizing.get("transformation_id"),
            "AVAILABLE_FOR_SIZING_OBSERVATION_SURFACE": sizing.get("observation_surface"),
            "SEM_SURF_DIV_00003_STATUS": self.payload.get("sem_surf_div_00003_status"),
            "UNK_ACCOUNT_EQUITY_SIZING_SOURCE_STATUS": self.payload.get(
                "unk_account_equity_sizing_source_status"
            ),
            "B05_CHAIN_CLOSED_CLAIM_SCOPE": self.payload.get("b05_chain_closed_claim_scope"),
            "ACTUAL_PROVEN_SCOPE": self.payload.get("actual_proven_scope"),
            "UNPROVEN_SCOPE": self.payload.get("unproven_scope"),
            "INV_SIZE_INVARIANTS_CHECKED": list(INV_SIZE_KEYS),
        }


def load_adjudication_v1(repo_root: Path) -> OdAccountEquitySizingSourceAdjudicationV1:
    path = repo_root / ADJUDICATION_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"))
    return OdAccountEquitySizingSourceAdjudicationV1(payload=payload)


def validate_adjudication_against_repo_v1(
    *,
    repo_root: Path,
    adjudication: OdAccountEquitySizingSourceAdjudicationV1 | None = None,
) -> tuple[bool, tuple[str, ...]]:
    adj = adjudication or load_adjudication_v1(repo_root)
    reasons: list[str] = []
    if adj.decision_case != "A":
        reasons.append("DECISION_CASE_MUST_BE_A_FOR_THIS_CONTRACT")
    if adj.canonical_unique_candidate_count != 1:
        reasons.append("CANONICALLY_UNIQUE_CANDIDATE_COUNT_MUST_BE_1")
    runbook = (repo_root / RUNBOOK_REL).read_text(encoding="utf-8")
    mapping_spec = (repo_root / MAPPING_SPEC_REL).read_text(encoding="utf-8")
    sizing = adj.payload.get("available_for_sizing", {})
    obs = str(sizing.get("observation_surface", ""))
    transform = str(sizing.get("transformation_id", ""))
    if obs not in runbook or obs not in mapping_spec:
        reasons.append("OBSERVATION_SURFACE_NOT_IN_PRIMARY_AUTHORITY_SURFACES")
    if transform not in runbook or transform not in mapping_spec:
        reasons.append("TRANSFORMATION_ID_NOT_IN_PRIMARY_AUTHORITY_SURFACES")
    if "SOURCE_OBJECT=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1" not in runbook:
        reasons.append("PRODUCER_WRAP_NOT_IN_RUNBOOK")
    if adj.payload.get("sem_surf_div_00003_status") != "PROVEN_CURRENT":
        reasons.append("SEM_SURF_DIV_00003_MUST_BE_PROVEN_CURRENT")
    if adj.payload.get("unk_account_equity_sizing_source_status") != "RESOLVED_NORMATIVE":
        reasons.append("UNK_ACCOUNT_EQUITY_SIZING_SOURCE_MUST_BE_RESOLVED")
    return (len(reasons) == 0, tuple(reasons))


def build_adjudication_report_v1(*, repo_root: Path) -> dict[str, Any]:
    adj = load_adjudication_v1(repo_root)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=repo_root, adjudication=adj)
    report = adj.to_report_v1()
    report["VALIDATION_OK"] = ok
    report["VALIDATION_REASONS"] = list(reasons)
    return report
