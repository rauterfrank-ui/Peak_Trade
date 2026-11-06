"""Atomic durable campaign evidence writer (authorized durable write only)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    PREREGISTRATION_DIGEST,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


class CampaignEvidenceWriteDeniedError(PermissionError):
    """Fail-closed when durable evidence write is not authorized."""


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(dict(payload), sort_keys=True, indent=2, default=str) + "\n"
    digest = compute_content_sha256({"content": text})
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return digest


def write_campaign_artifact_v1(
    *,
    artifact_path: Path,
    payload: Mapping[str, Any],
    durable_evidence_write_authorized: bool,
    campaign_id: str = CAMPAIGN_ID,
    preregistration_digest: str = PREREGISTRATION_DIGEST,
) -> dict[str, Any]:
    if not durable_evidence_write_authorized:
        raise CampaignEvidenceWriteDeniedError("DURABLE_EVIDENCE_WRITE_NOT_AUTHORIZED")
    if str(payload.get("campaign_id") or campaign_id) != campaign_id:
        raise ValueError("CAMPAIGN_ID_BINDING_MISMATCH")
    if (
        str(payload.get("preregistration_digest") or preregistration_digest)
        != preregistration_digest
    ):
        raise ValueError("PREREGISTRATION_DIGEST_BINDING_MISMATCH")
    digest = _atomic_write_json(artifact_path, payload)
    return {
        "artifact_path": str(artifact_path),
        "artifact_digest": digest,
        "atomic": True,
    }


__all__ = [
    "CampaignEvidenceWriteDeniedError",
    "write_campaign_artifact_v1",
]
