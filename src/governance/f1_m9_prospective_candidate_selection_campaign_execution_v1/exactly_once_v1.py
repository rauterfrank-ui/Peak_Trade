"""Exactly-once / resume adjudication for F1/M9 prospective campaign execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    PREREGISTRATION_DIGEST,
    RESUME_STATE_ALREADY_COMPLETE,
    RESUME_STATE_FAIL_CLOSED,
    RESUME_STATE_RESUME_AUTHORIZED,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


def derive_campaign_execution_identity_v1(
    *,
    campaign_id: str,
    preregistration_digest: str,
    execution_idempotency_key: str,
) -> str:
    return compute_content_sha256(
        {
            "campaign_id": campaign_id,
            "preregistration_digest": preregistration_digest,
            "execution_idempotency_key": execution_idempotency_key,
        }
    )


def adjudicate_execution_resume_state_v1(
    *,
    campaign_root: Path,
    execution_identity: str,
    sealed_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    state_path = campaign_root / "execution_state.json"
    if sealed_manifest and sealed_manifest.get("campaign_sealed") is True:
        manifest_identity = str(sealed_manifest.get("execution_identity") or "")
        if manifest_identity and manifest_identity != execution_identity:
            return {
                "resume_state": RESUME_STATE_FAIL_CLOSED,
                "reason_codes": ["EXECUTION_IDENTITY_MISMATCH_ON_SEALED_CAMPAIGN"],
            }
        return {
            "resume_state": RESUME_STATE_ALREADY_COMPLETE,
            "reason_codes": ["CAMPAIGN_ALREADY_SEALED"],
        }

    if not state_path.is_file():
        return {
            "resume_state": RESUME_STATE_RESUME_AUTHORIZED,
            "reason_codes": ["NO_PRIOR_EXECUTION_STATE"],
        }

    state = json.loads(state_path.read_text(encoding="utf-8"))
    prior = str(state.get("execution_identity") or "")
    if prior == execution_identity and state.get("partial") is True:
        return {
            "resume_state": RESUME_STATE_FAIL_CLOSED,
            "reason_codes": ["PARTIAL_RUN_AMBIGUOUS_NO_BLIND_RETRY"],
        }
    if prior == execution_identity and state.get("complete") is True:
        return {"resume_state": RESUME_STATE_ALREADY_COMPLETE, "reason_codes": []}
    if prior and prior != execution_identity:
        return {
            "resume_state": RESUME_STATE_FAIL_CLOSED,
            "reason_codes": ["DUPLICATE_EXECUTION_IDENTITY_CONFLICT"],
        }
    return {"resume_state": RESUME_STATE_RESUME_AUTHORIZED, "reason_codes": []}


def default_execution_identity_v1(*, execution_idempotency_key: str) -> str:
    return derive_campaign_execution_identity_v1(
        campaign_id=CAMPAIGN_ID,
        preregistration_digest=PREREGISTRATION_DIGEST,
        execution_idempotency_key=execution_idempotency_key,
    )


__all__ = [
    "adjudicate_execution_resume_state_v1",
    "default_execution_identity_v1",
    "derive_campaign_execution_identity_v1",
]
