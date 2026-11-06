"""Durable artifact paths for POST-REAL-CAMPAIGN productive handoff."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, Mapping

HANDOFF_DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_post_real_campaign_productive_handoff_v1_decision_v1.json"
)
PRODUCTIVE_APPLY_BOUNDARY_DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_productive_apply_execution_boundary_v1_decision_v1.json"
)

EXPLICIT_AUTH_ARTIFACT_REL: Final[str] = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "campaigns/cv_maxage_f1_m9_prospective_candidate_selection_v1_2bab88a8289fb032/"
    "productive_handoff/explicit_productive_authorization_v1.json"
)


def post_real_campaign_handoff_bounded_complete_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    handoff_path = root / HANDOFF_DECISION_CONFIG
    if handoff_path.is_file():
        payload = json.loads(handoff_path.read_text(encoding="utf-8"))
        if payload.get("bounded_handoff_complete") is True:
            return True
    boundary_path = root / PRODUCTIVE_APPLY_BOUNDARY_DECISION_CONFIG
    if not boundary_path.is_file():
        return False
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    ref = boundary.get("post_real_campaign_handoff_decision")
    if not isinstance(ref, str):
        return False
    ref_path = root / ref
    if not ref_path.is_file():
        return False
    return json.loads(ref_path.read_text(encoding="utf-8")).get("bounded_handoff_complete") is True


def explicit_productive_authorization_artifact_path_v1(*, repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return (root / EXPLICIT_AUTH_ARTIFACT_REL).resolve()


def load_explicit_productive_authorization_artifact_v1(
    *, repo_root: Path | None = None
) -> Mapping[str, Any] | None:
    path = explicit_productive_authorization_artifact_path_v1(repo_root=repo_root)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def persist_explicit_productive_authorization_artifact_v1(
    payload: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
) -> Path:
    path = explicit_productive_authorization_artifact_path_v1(repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


__all__ = [
    "HANDOFF_DECISION_CONFIG",
    "PRODUCTIVE_APPLY_BOUNDARY_DECISION_CONFIG",
    "EXPLICIT_AUTH_ARTIFACT_REL",
    "post_real_campaign_handoff_bounded_complete_v1",
    "explicit_productive_authorization_artifact_path_v1",
    "load_explicit_productive_authorization_artifact_v1",
    "persist_explicit_productive_authorization_artifact_v1",
]
