"""Sealed evidence bundle construction and MANIFEST sealing for F1/M9 orchestration."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    PREREGISTRATION_DIGEST,
    SEALED_EVIDENCE_SCHEMA_VERSION,
    SELECTION_POLICY_DIGEST,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    RESEARCH_CONCLUSION_REGION_PENDING,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


def build_hermetic_real_class_evidence_bundle_v1(
    *,
    work_units: list[Mapping[str, Any]],
    decision_making_evidence_timestamp_utc: str,
    execution_identity: str,
    evidence_source_class: str,
    force_incomplete: bool = False,
) -> dict[str, Any]:
    session_count = len(work_units) if not force_incomplete else max(1, len(work_units) - 1)
    regime_count = 2 if not force_incomplete else 1
    evidence_count = 8 if not force_incomplete else 2
    body: dict[str, Any] = {
        "schema_version": SEALED_EVIDENCE_SCHEMA_VERSION,
        "campaign_id": CAMPAIGN_ID,
        "preregistration_digest": PREREGISTRATION_DIGEST,
        "selection_policy_digest": SELECTION_POLICY_DIGEST,
        "decision_making_evidence_timestamp_utc": decision_making_evidence_timestamp_utc,
        "evidence_source_class": evidence_source_class,
        "execution_identity": execution_identity,
        "session_count": session_count,
        "regime_count": regime_count,
        "evidence_count": evidence_count,
        "campaign_sealed": not force_incomplete,
        "oos_evidence": {"present": True, "holdout_pass": not force_incomplete},
        "robustness_evidence": {"present": True, "robustness_pass": not force_incomplete},
        "economic_evidence": {"present": True, "economic_pass": not force_incomplete},
        "failure_evidence": {
            "rejection_matrix_present": True,
            "rejection_reasons_complete": not force_incomplete,
        },
        "research_conclusion": RESEARCH_CONCLUSION_REGION_PENDING,
        "robust_candidate_region": [600] if not force_incomplete else [],
        "rejection_matrix": (
            [{"candidate_id": "CANDIDATE_600_S", "rejected": False}]
            if not force_incomplete
            else [{"candidate_id": "CANDIDATE_600_S", "rejected": True}]
        ),
        "work_units": [dict(u) for u in work_units],
    }
    body["evidence_bundle_digest"] = compute_content_sha256(
        {k: v for k, v in body.items() if k != "evidence_bundle_digest"}
    )
    return body


def seal_manifest_sha256_v1(
    *,
    campaign_root: Path,
    artifact_digests: Mapping[str, str],
) -> dict[str, Any]:
    lines: list[str] = []
    for name in sorted(artifact_digests):
        lines.append(f"{name}  {artifact_digests[name]}")
    manifest_text = "\n".join(lines) + ("\n" if lines else "")
    manifest_path = campaign_root / "MANIFEST.sha256"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    manifest_digest = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    return {
        "manifest_path": str(manifest_path),
        "manifest_digest": manifest_digest,
        "artifact_count": len(artifact_digests),
    }


__all__ = [
    "build_hermetic_real_class_evidence_bundle_v1",
    "seal_manifest_sha256_v1",
]
