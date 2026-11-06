"""Preregistered session/work-unit resolution for F1/M9 prospective campaign orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    PREREGISTRATION_DIGEST,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_preregistration_v1 import (
    load_prospective_candidate_selection_campaign_preregistration_v1,
)
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    MINIMUM_SESSION_COUNT,
)


def resolve_preregistered_session_work_units_v1(
    *, repo_root: Path | None = None
) -> list[dict[str, Any]]:
    root = repo_root or Path(__file__).resolve().parents[3]
    prereg = load_prospective_candidate_selection_campaign_preregistration_v1(repo_root=root)
    if str(prereg.get("campaign_id") or "") != CAMPAIGN_ID:
        raise ValueError("PREREGISTRATION_CAMPAIGN_ID_MISMATCH")
    if str(prereg.get("preregistration_digest") or "") != PREREGISTRATION_DIGEST:
        raise ValueError("PREREGISTRATION_DIGEST_MISMATCH")
    minimum = int(prereg.get("planned_sessions_minimum") or MINIMUM_SESSION_COUNT)
    if minimum < MINIMUM_SESSION_COUNT:
        raise ValueError("PREREGISTERED_SESSION_MINIMUM_BELOW_CANONICAL")
    units: list[dict[str, Any]] = []
    for index in range(1, minimum + 1):
        units.append(
            {
                "session_id": f"session_{index:02d}",
                "work_unit_index": index,
                "campaign_id": CAMPAIGN_ID,
                "preregistration_digest": PREREGISTRATION_DIGEST,
            }
        )
    return units


__all__ = ["resolve_preregistered_session_work_units_v1"]
