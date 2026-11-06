"""Verify sealed F1/M9 prospective REAL campaign durable evidence (read-only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

DEFAULT_CAMPAIGN_ID: Final[str] = (
    "cv_maxage_f1_m9_prospective_candidate_selection_v1_2bab88a8289fb032"
)
DURABLE_CAMPAIGN_ROOT_REL: Final[str] = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    f"campaigns/{DEFAULT_CAMPAIGN_ID}"
)
PREREGISTRATION_DIGEST: Final[str] = (
    "44971151bc41b124bfa3642d38cba0bc43919160fec2e2d74df4f9e135101b0c"
)
EVIDENCE_SOURCE_REAL: Final[str] = "REAL_PUBLIC_MARKET_DATA"
REQUIREMENT_VERDICT_PASS: Final[str] = "PASS"
STATUS_REAL_TERMINAL_VERDICT_PASS: Final[str] = (
    "F1_M9_REAL_AUTHORIZED_CAMPAIGN_RUN_TERMINAL_VERDICT_PASS"
)
_CAMPAIGN_ARTIFACT_NAMES: Final[tuple[str, ...]] = (
    "campaign_manifest.json",
    "runtime_execution_authorization_ref.json",
    "source_provenance.json",
    "session_evidence.json",
    "candidate_grid_evaluation.json",
    "oos_evidence.json",
    "robustness_evidence.json",
    "economic_evidence.json",
    "failure_evidence.json",
    "contamination_adjudication.json",
    "campaign_completeness.json",
    "selection_result.json",
    "MANIFEST.sha256",
)

SCHEMA_VERSION: Final[str] = "f1_m9_prospective_real_campaign_durable_evidence_verification/v1"
WORKPACKAGE_ID: Final[str] = "F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETION_V1"

OUTCOME_SELECTED_PROPOSAL: Final[str] = "SELECTED_GOVERNED_CANDIDATE_PROPOSAL_ONLY"
EXECUTION_MODE_REAL: Final[str] = "REAL_AUTHORIZED_CAMPAIGN_EXECUTION"

_MANIFEST_ARTIFACTS: Final[tuple[str, ...]] = tuple(
    name for name in _CAMPAIGN_ARTIFACT_NAMES if name != "MANIFEST.sha256"
)


@dataclass(frozen=True, slots=True)
class F1M9ProspectiveRealCampaignDurableEvidenceVerificationV1:
    verified: bool
    reason_codes: tuple[str, ...]
    campaign_id: str
    execution_mode: str | None
    terminal_status: str | None
    campaign_sealed: bool
    evidence_bundle_digest: str | None
    execution_identity: str | None
    runtime_authorization_id: str | None
    selected_candidate_id: str | None
    selected_max_age_seconds: int | None
    proposal_only: bool
    productive_apply: bool
    selection_outcome: str | None
    preregistration_digest: str | None
    replay_ok: bool | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_sealed": self.campaign_sealed,
            "evidence_bundle_digest": self.evidence_bundle_digest,
            "execution_identity": self.execution_identity,
            "execution_mode": self.execution_mode,
            "preregistration_digest": self.preregistration_digest,
            "productive_apply": self.productive_apply,
            "proposal_only": self.proposal_only,
            "reason_codes": list(self.reason_codes),
            "replay_ok": self.replay_ok,
            "runtime_authorization_id": self.runtime_authorization_id,
            "selected_candidate_id": self.selected_candidate_id,
            "selected_max_age_seconds": self.selected_max_age_seconds,
            "selection_outcome": self.selection_outcome,
            "terminal_status": self.terminal_status,
            "verified": self.verified,
        }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON_NOT_MAPPING:{path}")
    return payload


def _artifact_content_digest(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return compute_content_sha256({"content": text})


def _verify_manifest_v1(*, campaign_root: Path) -> tuple[bool, tuple[str, ...]]:
    manifest_path = campaign_root / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return False, ("MANIFEST_MISSING",)
    reasons: list[str] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        name, expected = line.split("  ", 1)
        artifact = campaign_root / name
        if not artifact.is_file():
            reasons.append(f"MANIFEST_ARTIFACT_MISSING:{name}")
            continue
        actual = _artifact_content_digest(artifact)
        if actual != expected:
            reasons.append(f"MANIFEST_DIGEST_MISMATCH:{name}")
    return (not reasons, tuple(reasons))


def _completeness_pass(completeness: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    block = completeness.get("completeness")
    if not isinstance(block, Mapping):
        return False, ("COMPLETENESS_BLOCK_MISSING",)
    reasons: list[str] = []
    for key, value in block.items():
        if key == "reason_codes":
            continue
        if str(value) != REQUIREMENT_VERDICT_PASS and value is not True:
            reasons.append(f"COMPLETENESS_REQUIREMENT_FAIL:{key}")
    if block.get("campaign_selection_eligible") is not True:
        reasons.append("CAMPAIGN_SELECTION_NOT_ELIGIBLE")
    return (not reasons, tuple(reasons))


def verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
    *,
    repo_root: Path | None = None,
    campaign_id: str = DEFAULT_CAMPAIGN_ID,
    expected_runtime_authorization_id: str | None = None,
    expected_selected_candidate_id: str | None = None,
    expected_selected_max_age_seconds: int | None = None,
) -> F1M9ProspectiveRealCampaignDurableEvidenceVerificationV1:
    """Fail-closed verification of sealed REAL campaign durable artifacts."""
    root = repo_root or Path(__file__).resolve().parents[2]
    campaign_root = (root / DURABLE_CAMPAIGN_ROOT_REL).resolve()
    reasons: list[str] = []

    if campaign_id != DEFAULT_CAMPAIGN_ID:
        reasons.append("CAMPAIGN_ID_MISMATCH")

    manifest_ok, manifest_reasons = _verify_manifest_v1(campaign_root=campaign_root)
    reasons.extend(manifest_reasons)

    manifest = _load_json(campaign_root / "campaign_manifest.json")
    if str(manifest.get("campaign_id") or "") != campaign_id:
        reasons.append("CAMPAIGN_MANIFEST_ID_MISMATCH")
    if manifest.get("campaign_sealed") is not True:
        reasons.append("CAMPAIGN_NOT_SEALED")
    execution_mode = str(manifest.get("execution_mode") or "") or None
    if execution_mode != EXECUTION_MODE_REAL:
        reasons.append("EXECUTION_MODE_NOT_REAL_AUTHORIZED")
    execution_identity = str(manifest.get("execution_identity") or "") or None
    if not execution_identity or not is_valid_sha256_hex(execution_identity):
        reasons.append("EXECUTION_IDENTITY_INVALID")

    completeness = _load_json(campaign_root / "campaign_completeness.json")
    if str(completeness.get("preregistration_digest") or "") != PREREGISTRATION_DIGEST:
        reasons.append("PREREGISTRATION_DIGEST_MISMATCH")
    comp_ok, comp_reasons = _completeness_pass(completeness)
    reasons.extend(comp_reasons)

    bundle = completeness.get("sealed_evidence_bundle")
    evidence_bundle_digest: str | None = None
    if not isinstance(bundle, Mapping):
        reasons.append("SEALED_EVIDENCE_BUNDLE_MISSING")
    else:
        evidence_bundle_digest = str(bundle.get("evidence_bundle_digest") or "") or None
        if not evidence_bundle_digest or not is_valid_sha256_hex(evidence_bundle_digest):
            reasons.append("EVIDENCE_BUNDLE_DIGEST_INVALID")
        if bundle.get("evidence_source_class") != EVIDENCE_SOURCE_REAL:
            reasons.append("EVIDENCE_SOURCE_NOT_REAL_PUBLIC_MD")
        if bundle.get("campaign_sealed") is not True:
            reasons.append("BUNDLE_NOT_SEALED")

    contamination = _load_json(campaign_root / "contamination_adjudication.json")
    if contamination.get("historical_evidence_decision_leakage") is True:
        reasons.append("HISTORICAL_LEAKAGE_DETECTED")
    if contamination.get("selection_permitted") is not True:
        reasons.append("CONTAMINATION_SELECTION_NOT_PERMITTED")

    provenance = _load_json(campaign_root / "source_provenance.json")
    if provenance.get("real_authorized_campaign_execution_path") is not True:
        reasons.append("REAL_AUTHORIZED_PATH_NOT_PROVEN")
    if provenance.get("simulated_public_md_in_hermetic") is True:
        reasons.append("HERMETIC_SIMULATION_DETECTED")

    selection = _load_json(campaign_root / "selection_result.json")
    if selection.get("proposal_only") is not True:
        reasons.append("SELECTION_NOT_PROPOSAL_ONLY")
    if selection.get("productive_apply") is not False:
        reasons.append("PRODUCTIVE_APPLY_MUST_BE_FALSE")
    sel_block = selection.get("selection")
    if not isinstance(sel_block, Mapping):
        reasons.append("SELECTION_BLOCK_MISSING")
        selected_candidate_id = None
        selected_max_age_seconds = None
        selection_outcome = None
    else:
        selection_outcome = str(sel_block.get("outcome") or "") or None
        selected_candidate_id = str(sel_block.get("selected_candidate_id") or "") or None
        raw_age = sel_block.get("selected_max_age_seconds")
        selected_max_age_seconds = int(raw_age) if isinstance(raw_age, int) else None
        if selection_outcome != OUTCOME_SELECTED_PROPOSAL:
            reasons.append("SELECTION_OUTCOME_NOT_GOVERNED_PROPOSAL")
        if sel_block.get("productive_apply") is not False:
            reasons.append("SELECTION_PRODUCTIVE_APPLY_NOT_FALSE")
        if sel_block.get("productive_authorization") is not False:
            reasons.append("SELECTION_PRODUCTIVE_AUTHORIZATION_NOT_FALSE")

    auth_ref = _load_json(campaign_root / "runtime_execution_authorization_ref.json")
    runtime_authorization_id = str(auth_ref.get("authorization_id") or "") or None
    if expected_runtime_authorization_id and runtime_authorization_id != (
        expected_runtime_authorization_id
    ):
        reasons.append("RUNTIME_AUTHORIZATION_ID_MISMATCH")

    policy_path = root / "config/governance/f1_m9_productive_candidate_selection_policy_v1.json"
    if policy_path.is_file():
        policy = _load_json(policy_path)
        allowed = policy.get("admissible_parameter_space", {}).get("candidate_max_age_seconds")
        if isinstance(allowed, list) and selected_max_age_seconds is not None:
            if selected_max_age_seconds not in {int(x) for x in allowed}:
                reasons.append("CANDIDATE_OUTSIDE_ENVELOPE")
    else:
        reasons.append("SELECTION_POLICY_CONFIG_MISSING")

    if expected_selected_candidate_id and selected_candidate_id != expected_selected_candidate_id:
        reasons.append("SELECTED_CANDIDATE_ID_MISMATCH")
    if (
        expected_selected_max_age_seconds is not None
        and selected_max_age_seconds != expected_selected_max_age_seconds
    ):
        reasons.append("SELECTED_MAX_AGE_MISMATCH")

    session = _load_json(campaign_root / "session_evidence.json")
    session_results = session.get("session_results")
    if not isinstance(session_results, list) or len(session_results) != 2:
        reasons.append("SESSION_COVERAGE_INCOMPLETE")

    replay_ok: bool | None = None
    if manifest_ok and comp_ok and not reasons:
        replay_ok = True

    terminal_status = STATUS_REAL_TERMINAL_VERDICT_PASS if replay_ok else None

    verified = manifest_ok and comp_ok and not reasons and replay_ok is True
    return F1M9ProspectiveRealCampaignDurableEvidenceVerificationV1(
        verified=verified,
        reason_codes=tuple(dict.fromkeys(reasons)),
        campaign_id=campaign_id,
        execution_mode=execution_mode,
        terminal_status=terminal_status,
        campaign_sealed=manifest.get("campaign_sealed") is True,
        evidence_bundle_digest=evidence_bundle_digest,
        execution_identity=execution_identity,
        runtime_authorization_id=runtime_authorization_id,
        selected_candidate_id=selected_candidate_id,
        selected_max_age_seconds=selected_max_age_seconds,
        proposal_only=selection.get("proposal_only") is True,
        productive_apply=selection.get("productive_apply") is False,
        selection_outcome=selection_outcome,
        preregistration_digest=str(completeness.get("preregistration_digest") or "") or None,
        replay_ok=replay_ok,
    )


__all__ = [
    "F1M9ProspectiveRealCampaignDurableEvidenceVerificationV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "verify_f1_m9_prospective_real_campaign_durable_evidence_v1",
]
