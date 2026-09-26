"""Durable artifact paths for F1/M9 governed productive runtime apply start Owner GO."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, Mapping

OWNER_RUNTIME_APPLY_START_WP_DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_f1_m9_scoped_owner_productive_runtime_apply_start_wp_v1_owner_decision_v1.json"
)
RUNTIME_APPLY_START_CONTINUATION_DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1_decision_v1.json"
)

RUNTIME_APPLY_START_EVIDENCE_ARTIFACT_REL: Final[str] = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "campaigns/cv_maxage_f1_m9_prospective_candidate_selection_v1_2bab88a8289fb032/"
    "productive_handoff/governed_productive_runtime_apply_start_evidence_v1.json"
)


def runtime_apply_start_evidence_artifact_path_v1(*, repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return (root / RUNTIME_APPLY_START_EVIDENCE_ARTIFACT_REL).resolve()


def load_owner_runtime_apply_start_wp_decision_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    path = root / OWNER_RUNTIME_APPLY_START_WP_DECISION_CONFIG
    if not path.is_file():
        raise FileNotFoundError(OWNER_RUNTIME_APPLY_START_WP_DECISION_CONFIG)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("OWNER_WP_DECISION_NOT_MAPPING")
    return payload


def persist_runtime_apply_start_evidence_artifact_v1(
    payload: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
) -> Path:
    path = runtime_apply_start_evidence_artifact_path_v1(repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


__all__ = [
    "OWNER_RUNTIME_APPLY_START_WP_DECISION_CONFIG",
    "RUNTIME_APPLY_START_CONTINUATION_DECISION_CONFIG",
    "RUNTIME_APPLY_START_EVIDENCE_ARTIFACT_REL",
    "load_owner_runtime_apply_start_wp_decision_v1",
    "persist_runtime_apply_start_evidence_artifact_v1",
    "runtime_apply_start_evidence_artifact_path_v1",
]
