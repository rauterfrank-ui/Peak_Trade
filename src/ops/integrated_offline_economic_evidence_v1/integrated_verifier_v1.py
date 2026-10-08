"""Integrated offline economic evidence index verifier v1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.binding_v1 import (
    VerificationBindingContextV1,
    resolve_verification_binding_context_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.canonical_identity_verifier_v1 import (
    verify_canonical_identity_binding_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    EVIDENCE_SCOPE_PRODUCTIVE_CURRENT,
    INTEGRATED_ARTIFACT,
    INTEGRATED_SCHEMA_ID,
    INTEGRATED_SCHEMA_VERSION,
    INTEGRATED_VERIFIER_ID,
    SUPPORTED_INTEGRATED_SCHEMA_VERSIONS,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_contracts_v1 import (
    load_json_object,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_verifiers_v1 import (
    verify_economic_metrics_domain_evidence_v1,
    verify_monte_carlo_domain_evidence_v1,
    verify_stress_domain_evidence_v1,
    verify_walk_forward_domain_evidence_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.forbidden_substitution_v1 import (
    check_forbidden_substitution_v1,
)


@dataclass
class IntegratedOfflineEconomicEvidenceVerificationResultV1:
    verified: bool
    economic_metrics_verified: bool = False
    walk_forward_verified: bool = False
    monte_carlo_verified: bool = False
    stress_verified: bool = False
    bindings_verified: bool = False
    forbidden_classes_absent: bool = False
    canonical_identity_verified: bool = False
    offline_economic_evidence_complete: bool = False
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_integrated_offline_economic_evidence_v1(
    *,
    repo_root: Path,
    evidence_root: Path | None = None,
    index_document: Mapping[str, Any] | None = None,
    binding_context: VerificationBindingContextV1 | None = None,
    expected_implementation_surface_digest_sha256: str | None = None,
    expected_config_digest_sha256: str | None = None,
    expected_proven_source_sha: str | None = None,
    cap23_residency_gate_enabled: bool | None = None,
) -> IntegratedOfflineEconomicEvidenceVerificationResultV1:
    """Fail-closed verification of index + domain references."""
    root = repo_root.resolve()
    blockers: list[str] = []
    notes = ["INCREMENT_A_CONTRACT_VERIFIER", f"VERIFIER_ID={INTEGRATED_VERIFIER_ID}"]

    doc: dict[str, Any] = {}
    if index_document is not None:
        doc = dict(index_document)
    elif evidence_root is not None:
        index_path = Path(evidence_root) / INTEGRATED_ARTIFACT
        loaded, load_blockers = load_json_object(index_path)
        blockers.extend(load_blockers)
        doc = loaded
    else:
        blockers.append("INDEX_MISSING")

    if doc:
        if doc.get("schema_id") != INTEGRATED_SCHEMA_ID:
            blockers.append("INDEX_SCHEMA_ID_MISMATCH")
        schema_version = str(doc.get("schema_version") or "")
        if schema_version not in SUPPORTED_INTEGRATED_SCHEMA_VERSIONS:
            blockers.append("INDEX_SCHEMA_VERSION_MISMATCH")
        if doc.get("authority_effect") != AUTHORITY_EFFECT_NONE:
            blockers.append("INDEX_AUTHORITY_EFFECT_NOT_NONE")
        if doc.get("verifier_id") != INTEGRATED_VERIFIER_ID:
            blockers.append("INDEX_VERIFIER_ID_MISMATCH")
        if not str(doc.get("producer_id") or ""):
            blockers.append("INDEX_PRODUCER_ID_MISSING")

    ctx = binding_context
    if ctx is None:
        ctx, ctx_blockers = resolve_verification_binding_context_v1(
            repo_root=root,
            expected_implementation_surface_digest_sha256=expected_implementation_surface_digest_sha256,
            expected_config_digest_sha256=expected_config_digest_sha256,
        )
        blockers.extend(ctx_blockers)

    forbidden_blockers = check_forbidden_substitution_v1(
        artifact_relpath=str(doc.get("evidence_root_relpath") or ""),
        producer_id=str(doc.get("producer_id") or ""),
        repo_root=root,
        index_doc=doc,
    )
    forbidden_classes_absent = not forbidden_blockers
    blockers.extend(forbidden_blockers)

    canonical_identity_verified = True
    if doc.get("evidence_scope_class") == EVIDENCE_SCOPE_PRODUCTIVE_CURRENT:
        identity = verify_canonical_identity_binding_v1(
            index_document=doc,
            repo_root=root,
            expected_proven_source_sha=expected_proven_source_sha,
            cap23_residency_gate_enabled=cap23_residency_gate_enabled,
        )
        canonical_identity_verified = identity.productive_identity_verified
        if not identity.verified:
            blockers.extend(f"IDENTITY:{b}" for b in identity.blockers)

    bindings_verified = True
    for ref_key in (
        "economic_metrics_domain_ref",
        "walk_forward_domain_ref",
        "monte_carlo_domain_ref",
        "stress_domain_ref",
    ):
        ref = doc.get(ref_key)
        if not isinstance(ref, dict):
            blockers.append(f"{ref_key.upper()}_MISSING")
            bindings_verified = False

    domain_binding_kwargs = (
        {"binding_context": ctx}
        if ctx is not None
        else {
            "expected_implementation_surface_digest_sha256": (
                expected_implementation_surface_digest_sha256
            ),
            "expected_config_digest_sha256": expected_config_digest_sha256,
        }
    )
    metrics = verify_economic_metrics_domain_evidence_v1(
        repo_root=root,
        reference=doc.get("economic_metrics_domain_ref")
        if isinstance(doc.get("economic_metrics_domain_ref"), dict)
        else None,
        **domain_binding_kwargs,
    )
    wf = verify_walk_forward_domain_evidence_v1(
        repo_root=root,
        reference=doc.get("walk_forward_domain_ref")
        if isinstance(doc.get("walk_forward_domain_ref"), dict)
        else None,
        **domain_binding_kwargs,
    )
    mc = verify_monte_carlo_domain_evidence_v1(
        repo_root=root,
        reference=doc.get("monte_carlo_domain_ref")
        if isinstance(doc.get("monte_carlo_domain_ref"), dict)
        else None,
        **domain_binding_kwargs,
    )
    stress = verify_stress_domain_evidence_v1(
        repo_root=root,
        reference=doc.get("stress_domain_ref")
        if isinstance(doc.get("stress_domain_ref"), dict)
        else None,
        **domain_binding_kwargs,
    )

    if not metrics.verified:
        blockers.extend(f"ECONOMIC_METRICS:{b}" for b in metrics.blockers)
    if not wf.verified:
        blockers.extend(f"WALK_FORWARD:{b}" for b in wf.blockers)
    if not mc.verified:
        blockers.extend(f"MONTE_CARLO:{b}" for b in mc.blockers)
    if not stress.verified:
        blockers.extend(f"STRESS:{b}" for b in stress.blockers)

    if blockers:
        bindings_verified = bindings_verified and not any(
            b.endswith("_MISSING") or "MISMATCH" in b for b in blockers
        )

    unique = sorted(set(blockers))
    verified = (
        not unique
        and metrics.verified
        and wf.verified
        and mc.verified
        and stress.verified
        and bindings_verified
        and forbidden_classes_absent
        and canonical_identity_verified
    )
    offline_complete = (
        verified and doc.get("evidence_scope_class") == EVIDENCE_SCOPE_PRODUCTIVE_CURRENT
    )

    return IntegratedOfflineEconomicEvidenceVerificationResultV1(
        verified=verified,
        offline_economic_evidence_complete=offline_complete,
        economic_metrics_verified=metrics.verified,
        walk_forward_verified=wf.verified,
        monte_carlo_verified=mc.verified,
        stress_verified=stress.verified,
        bindings_verified=bindings_verified and not unique,
        forbidden_classes_absent=forbidden_classes_absent,
        canonical_identity_verified=canonical_identity_verified,
        blockers=unique,
        notes=notes,
    )
