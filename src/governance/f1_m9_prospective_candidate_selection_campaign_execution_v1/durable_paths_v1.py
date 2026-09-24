"""Durable campaign root resolver for F1/M9 prospective selection campaign."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ARTIFACT_NAMES,
    CAMPAIGN_ID,
    DURABLE_CAMPAIGN_ROOT_REL,
)


@dataclass(frozen=True, slots=True)
class F1M9ProspectiveCampaignDurablePathsV1:
    campaign_root: Path
    campaign_id: str
    artifact_names: tuple[str, ...]

    def artifact_path(self, name: str) -> Path:
        if name not in self.artifact_names:
            raise ValueError(f"UNKNOWN_CAMPAIGN_ARTIFACT:{name}")
        return self.campaign_root / name

    def to_dict(self) -> dict[str, str]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_root": str(self.campaign_root),
        }


def resolve_f1_m9_prospective_campaign_durable_paths_v1(
    *, repo_root: Path | None = None
) -> F1M9ProspectiveCampaignDurablePathsV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    campaign_root = (root / DURABLE_CAMPAIGN_ROOT_REL).resolve()
    return F1M9ProspectiveCampaignDurablePathsV1(
        campaign_root=campaign_root,
        campaign_id=CAMPAIGN_ID,
        artifact_names=CAMPAIGN_ARTIFACT_NAMES,
    )


__all__ = [
    "F1M9ProspectiveCampaignDurablePathsV1",
    "resolve_f1_m9_prospective_campaign_durable_paths_v1",
]
