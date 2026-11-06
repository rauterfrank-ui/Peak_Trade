"""Durable artifact paths for F1/M9 Owner threshold value ratification (600s Owner GO)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, Mapping

OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG: Final[str] = (
    "config/governance/governed_f1_m9_scoped_owner_threshold_value_ratification_wp_v1_owner_decision_v1.json"
)
THRESHOLD_RATIFICATION_CONTINUATION_DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1_decision_v1.json"
)

OWNER_THRESHOLD_RECORD_ARTIFACT_REL: Final[str] = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "campaigns/cv_maxage_f1_m9_prospective_candidate_selection_v1_2bab88a8289fb032/"
    "productive_handoff/owner_threshold_value_authorization_record_v1.json"
)


def owner_threshold_record_artifact_path_v1(*, repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return (root / OWNER_THRESHOLD_RECORD_ARTIFACT_REL).resolve()


def load_owner_threshold_record_artifact_v1(
    *, repo_root: Path | None = None
) -> Mapping[str, Any] | None:
    path = owner_threshold_record_artifact_path_v1(repo_root=repo_root)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def persist_owner_threshold_record_artifact_v1(
    payload: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
) -> Path:
    path = owner_threshold_record_artifact_path_v1(repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


__all__ = [
    "OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG",
    "OWNER_THRESHOLD_RECORD_ARTIFACT_REL",
    "THRESHOLD_RATIFICATION_CONTINUATION_DECISION_CONFIG",
    "load_owner_threshold_record_artifact_v1",
    "owner_threshold_record_artifact_path_v1",
    "persist_owner_threshold_record_artifact_v1",
]
