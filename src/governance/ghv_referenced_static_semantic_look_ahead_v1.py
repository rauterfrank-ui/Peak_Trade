"""GHV-referenced static semantic look-ahead v1 (read-only; no trading authority)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.evaluation.golden_vectors.evaluators import ptp_owners_v1
from src.governance.ghv_referenced_intelligence_superstructure_ghv_reference_manifest_v1 import (
    GHV_AUTHORITY,
    ghv_semantic_checkpoints_v1,
    load_ghv_reference_manifest_config_v1,
    prove_ghv_reference_artifacts_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
)
from src.governance.m10_promotion_boundary_v1 import AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "ghv_referenced_static_semantic_look_ahead_v1"


def run_ghv_referenced_static_semantic_look_ahead_v1() -> MappingProxyType[str, Any]:
    """Compare CURRENT owner/boundary constants against GHV manifest snapshot."""
    manifest = load_ghv_reference_manifest_config_v1()
    invariants = manifest.get("intelligence_boundary_invariants") or {}
    divergences: list[str] = []

    if GHV_AUTHORITY != "NONE":
        divergences.append("GHV_AUTHORITY_NOT_NONE")
    if invariants.get("ghv_authority") != "NONE":
        divergences.append("MANIFEST_GHV_AUTHORITY_NOT_NONE")
    if CAPTURE_FAILURE_CHANGES_DECISION is not False:
        divergences.append("DDO_CAPTURE_FAILURE_CHANGES_DECISION")
    if PRODUCTIVE_ACTIVATION_AUTHORIZED is not False:
        divergences.append("EIP_PRODUCTIVE_ACTIVATION_AUTHORIZED")
    if AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is not False:
        divergences.append("AUTONOMY_SUPERVISOR_RUNTIME_REACHABLE")
    if AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is not False:
        divergences.append("M10_AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY")

    productive_first = _productive_owner_divergence()
    if productive_first:
        divergences.append(f"PRODUCTIVE_OWNER:{productive_first}")

    ghv_proof = prove_ghv_reference_artifacts_v1()
    if not ghv_proof.get("artifacts_ok"):
        divergences.append("GHV_REFERENCE_ARTIFACTS_MISSING")
    checkpoints = ghv_semantic_checkpoints_v1()
    if not checkpoints.get("ok"):
        divergences.append("GHV_SEMANTIC_CHECKPOINTS_UNAVAILABLE")
    else:
        cp = checkpoints.get("checkpoints") or {}
        for key in manifest.get("semantic_checkpoint_keys") or ():
            if key == "GENUINE_NATURAL_ENTER" and not cp.get("GENUINE_NATURAL_ENTER"):
                divergences.append("GHV_CHECKPOINT_NATURAL_ENTER")
            if key == "PRE_EXTERNAL_REACHED" and not cp.get("PRE_EXTERNAL_REACHED"):
                divergences.append("GHV_CHECKPOINT_PRE_EXTERNAL")
            if key == "POST_COUNT_ZERO" and not cp.get("POST_COUNT_ZERO"):
                divergences.append("GHV_CHECKPOINT_POST_COUNT")
            if key == "EXTERNAL_EFFECT_COUNT_ZERO" and not cp.get("EXTERNAL_EFFECT_COUNT_ZERO"):
                divergences.append("GHV_CHECKPOINT_EXTERNAL_EFFECT")

    intelligence_first = _intelligence_boundary_divergence()
    if intelligence_first:
        divergences.append(f"INTELLIGENCE_BOUNDARY:{intelligence_first}")

    productive_div = productive_first or "NONE"
    intelligencediv = intelligence_first or "NONE"
    if divergences and productive_first is None and intelligence_first is None:
        intelligencediv = divergences[0]

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ghv_authority": GHV_AUTHORITY,
        "productive_first_causal_divergence": productive_div,
        "intelligence_first_causal_divergence": (
            "NONE"
            if not divergences
            else (intelligencediv if intelligencediv != "NONE" else divergences[0])
        ),
        "divergence_codes": tuple(divergences),
        "ghv_artifact_proof_digest": ghv_proof.get("manifest_digest"),
        "ghv_checkpoint_digest": checkpoints.get("checkpoint_digest"),
        "ptp_stage_count": len(ptp_owners_v1.PTP_STAGE_ORDER),
    }
    if not divergences:
        body["productive_first_causal_divergence"] = "NONE"
        body["intelligence_first_causal_divergence"] = "NONE"
    body["look_ahead_digest"] = compute_content_sha256(body)
    return MappingProxyType(body)


def _productive_owner_divergence() -> str | None:
    for stage in ptp_owners_v1.PTP_STAGE_ORDER:
        owner = ptp_owners_v1.PTP_STAGE_OWNERS.get(stage)
        if not owner:
            return f"MISSING_OWNER:{stage}"
    return None


def _intelligence_boundary_divergence() -> str | None:
    if PRODUCTIVE_ACTIVATION_AUTHORIZED:
        return "EIP_PRODUCTIVE_ACTIVATION"
    if AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY:
        return "AUTONOMY_SUPERVISOR_REACHABLE"
    return None


__all__ = [
    "SCHEMA_VERSION",
    "run_ghv_referenced_static_semantic_look_ahead_v1",
]
