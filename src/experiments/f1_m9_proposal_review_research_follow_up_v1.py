"""Use a persisted M9 governance review to route one bounded offline follow-up."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (
    run_max_age_parameter_research_execution_v1,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    compute_m9_reproducibility_digest_v1,
)
from src.governance.f1_m9_proposal_review_feedback_v1 import (
    read_f1_m9_proposal_review_feedback_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import ADMISSION_ADMITTED
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)

_RECEIPT = "proposal_review_research_follow_up.json"
_LEDGER = "input_research_ledger.jsonl"
_OUT_OF_BOUNDS = ("CANDIDATE_TARGET_OUT_OF_BOUNDS",)


@dataclass(frozen=True, slots=True)
class F1M9ProposalReviewResearchContextV1:
    review_store: Path
    original_ingress: Mapping[str, Any]
    review_policy_digest: str
    review_feedback_digest: str


def _read_completed(output_root: Path, expected_inputs: Mapping[str, Any]) -> dict[str, Any]:
    receipt_path = output_root / _RECEIPT
    if not receipt_path.is_file():
        raise ValueError("M9_REVIEW_RESEARCH_OUTPUT_INCOMPLETE")
    payload = json.loads(receipt_path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError("M9_REVIEW_RESEARCH_RECEIPT_INVALID")
    digest = payload.pop("receipt_digest", None)
    if compute_content_sha256(payload) != digest:
        raise ValueError("M9_REVIEW_RESEARCH_RECEIPT_INVALID")
    if payload.get("inputs") != expected_inputs:
        raise ValueError("M9_REVIEW_RESEARCH_INPUT_CONFLICT")
    artifacts = payload["artifact_sha256"]
    if not isinstance(artifacts, dict) or set(artifacts) != {
        p.name for p in output_root.iterdir() if p.name != _RECEIPT
    }:
        raise ValueError("M9_REVIEW_RESEARCH_ARTIFACT_SET_MISMATCH")
    for name, expected_digest in artifacts.items():
        if name != Path(name).name:
            raise ValueError("M9_REVIEW_RESEARCH_ARTIFACT_PATH_INVALID")
        artifact = output_root / name
        if (
            artifact.is_symlink()
            or not artifact.is_file()
            or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected_digest
        ):
            raise ValueError(f"M9_REVIEW_RESEARCH_ARTIFACT_DIGEST_MISMATCH:{name}")
    return {**payload, "receipt_digest": digest}


def run_f1_m9_proposal_review_research_follow_up_v1(
    *,
    context: F1M9ProposalReviewResearchContextV1,
    repo_root: Path,
    native_baseline_evidence_v1: Mapping[str, Any],
    ledger_path: Path | None,
    output_root: Path | None,
    repository_sha: str | None,
    created_at_utc: str | None,
) -> dict[str, Any]:
    """Preserve the review disposition and call the original runner only when applicable."""
    review = read_f1_m9_proposal_review_feedback_v1(
        store_root=context.review_store,
        ingress=context.original_ingress,
        review_policy_digest=context.review_policy_digest,
        expected_feedback_digest=context.review_feedback_digest,
    )
    decision = {
        "schema_version": "f1_m9_proposal_review_research_follow_up_v1",
        "ingress_digest": review.ingress_digest,
        "proposal_identity_digest": review.proposal_identity_digest,
        "review_policy_digest": review.review_policy_digest,
        "review_feedback_digest": review.feedback_digest,
        "admission_status": review.admission_status,
        "reason_codes": list(review.reason_codes),
        "authority": "NONE",
    }
    if review.review_policy_digest != compute_m9_reproducibility_digest_v1():
        return {"inputs": decision, "action": "REVIEW_POLICY_CHANGED", "research": None}
    if review.admission_status == ADMISSION_ADMITTED:
        return {"inputs": decision, "action": "KEEP_ADMITTED_PROPOSAL", "research": None}
    if review.reason_codes != _OUT_OF_BOUNDS:
        return {"inputs": decision, "action": "RESOLVE_ORIGINAL_REVIEW_REASONS", "research": None}
    if ledger_path is None:
        return {"inputs": decision, "action": "WAIT_FOR_M9_EVIDENCE", "research": None}
    if (
        output_root is None
        or repository_sha is None
        or not re.fullmatch(r"[0-9a-f]{40}", repository_sha)
        or not created_at_utc
    ):
        raise ValueError("M9_REVIEW_RESEARCH_REQUIRES_OUTPUT_REVISION_AND_TIME")
    created = datetime.fromisoformat(created_at_utc.replace("Z", "+00:00"))
    if created.utcoffset() != timedelta(0):
        raise ValueError("M9_REVIEW_RESEARCH_TIME_NOT_UTC")

    ledger = ledger_path.read_bytes()
    baseline = json.loads(deterministic_json_dumps(dict(native_baseline_evidence_v1)))
    inputs = {
        **decision,
        "repository_sha": repository_sha,
        "created_at_utc": created_at_utc,
        "native_baseline_digest": compute_content_sha256(baseline),
        "ledger_sha256": hashlib.sha256(ledger).hexdigest(),
    }
    try:
        output_root.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return _read_completed(output_root, inputs)

    # The original runner records the ledger path and hash in its input manifest.
    # Give it the exact snapshot bound above and leave the supplied ledger untouched.
    ledger_snapshot = output_root / _LEDGER
    ledger_snapshot.write_bytes(ledger)
    result = run_max_age_parameter_research_execution_v1(
        repo_root=repo_root,
        native_baseline_evidence_v1=baseline,
        ledger_path=ledger_snapshot,
        output_root=output_root,
        repository_sha=repository_sha,
        created_at_utc=created_at_utc,
    )
    original_inputs = json.loads((output_root / "input_evidence_manifest.json").read_bytes())
    if (
        result["input_evidence_valid"]
        and original_inputs["ledger_sha256"] != inputs["ledger_sha256"]
    ):
        raise ValueError("M9_REVIEW_RESEARCH_LEDGER_BINDING_MISMATCH")
    artifacts = {
        name: hashlib.sha256((output_root / name).read_bytes()).hexdigest()
        for name in sorted(result["artifact_digests"])
    }
    receipt = {
        "inputs": inputs,
        "action": "RUN_REGISTERED_M9_RESEARCH",
        "research": {
            key: result[key]
            for key in (
                "status",
                "execution_id",
                "research_conclusion",
                "input_evidence_manifest_digest",
                "final_holdout_executed",
            )
        },
        "artifact_sha256": {**artifacts, _LEDGER: inputs["ledger_sha256"]},
    }
    receipt["receipt_digest"] = compute_content_sha256(receipt)
    with NamedTemporaryFile(dir=output_root.parent, prefix=".m9-review-", delete=False) as stream:
        staging = Path(stream.name)
        try:
            stream.write((deterministic_json_dumps(receipt) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(staging, output_root / _RECEIPT)
        finally:
            staging.unlink(missing_ok=True)
    return _read_completed(output_root, inputs)
