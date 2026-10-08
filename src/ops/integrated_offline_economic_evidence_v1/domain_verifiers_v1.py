"""Fail-closed domain verifiers for integrated offline economic evidence v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.binding_v1 import (
    VerificationBindingContextV1,
    resolve_verification_binding_context_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    ALLOWED_CONTRACT_TEST_PRODUCER_PREFIX,
    ECONOMIC_METRICS_DOMAIN_SCHEMA_ID,
    ECONOMIC_METRICS_VERIFIER_ID,
    MONTE_CARLO_DOMAIN_SCHEMA_ID,
    MONTE_CARLO_VERIFIER_ID,
    STRESS_DOMAIN_SCHEMA_ID,
    STRESS_VERIFIER_ID,
    WALK_FORWARD_DOMAIN_SCHEMA_ID,
    WALK_FORWARD_VERIFIER_ID,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_contracts_v1 import (
    DomainVerificationResultV1,
    validate_reference_binding_fields,
    verify_reference_integrity,
)
from src.ops.integrated_offline_economic_evidence_v1.forbidden_substitution_v1 import (
    check_forbidden_substitution_v1,
)


def _require_producer_allowed(producer_id: str, prefix: str) -> list[str]:
    producer = str(producer_id or "")
    if not producer.startswith(ALLOWED_CONTRACT_TEST_PRODUCER_PREFIX):
        return [f"{prefix}PRODUCTIVE_PRODUCER_NOT_AUTHORIZED_IN_INCREMENT_A"]
    return []


def _common_domain_verify(
    *,
    repo_root: Path,
    reference: Mapping[str, Any] | None,
    domain: str,
    schema_id: str,
    verifier_id: str,
    extra_checks,
    binding_context: VerificationBindingContextV1 | None = None,
    expected_implementation_surface_digest_sha256: str | None = None,
    expected_config_digest_sha256: str | None = None,
) -> DomainVerificationResultV1:
    prefix = f"{domain.upper()}:"
    blockers: list[str] = []
    if reference is None:
        return DomainVerificationResultV1(verified=False, blockers=[f"{prefix}REFERENCE_MISSING"])

    ctx = binding_context
    if ctx is None:
        ctx, ctx_blockers = resolve_verification_binding_context_v1(
            repo_root=repo_root,
            expected_implementation_surface_digest_sha256=(
                expected_implementation_surface_digest_sha256
            ),
            expected_config_digest_sha256=expected_config_digest_sha256,
        )
        blockers.extend(f"{prefix}{b}" for b in ctx_blockers)
    if ctx is None:
        unique = sorted(set(blockers))
        return DomainVerificationResultV1(
            verified=False,
            blockers=unique,
            notes=[f"DOMAIN={domain}", "INCREMENT_A_CONTRACT_ONLY"],
        )

    blockers.extend(
        validate_reference_binding_fields(
            reference,
            expected_schema_id=schema_id,
            expected_verifier_id=verifier_id,
            prefix=prefix,
        )
    )
    blockers.extend(_require_producer_allowed(str(reference.get("producer_id") or ""), prefix))
    artifact_relpath = str(reference.get("artifact_relpath") or "")
    producer_id = str(reference.get("producer_id") or "")
    blockers.extend(
        check_forbidden_substitution_v1(
            artifact_relpath=artifact_relpath,
            producer_id=producer_id,
            repo_root=repo_root,
        )
    )

    integrity_blockers, _path, doc = verify_reference_integrity(
        repo_root=repo_root,
        ref=reference,
        prefix=prefix,
        expected_implementation_digest=ctx.expected_implementation_surface_digest_sha256,
        expected_config_digest=ctx.expected_config_digest_sha256,
    )
    blockers.extend(integrity_blockers)
    if doc and not integrity_blockers:
        blockers.extend(
            check_forbidden_substitution_v1(
                artifact_relpath=artifact_relpath,
                producer_id=producer_id,
                repo_root=repo_root,
                domain_doc=doc,
            )
        )
        blockers.extend(extra_checks(doc, prefix))

    unique = sorted(set(blockers))
    return DomainVerificationResultV1(
        verified=not unique,
        blockers=unique,
        notes=[f"DOMAIN={domain}", "INCREMENT_A_CONTRACT_ONLY"],
    )


def _increment_b_deferred(doc: Mapping[str, Any], prefix: str, label: str) -> list[str]:
    if doc.get("contract_test_increment_a_mechanics_only") is True:
        return []
    return [f"{prefix}PRODUCTIVE_{label}_SEMANTICS_DEFERRED_TO_INCREMENT_B"]


def _economic_metrics_extra(doc: Mapping[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if doc.get("schema_id") != ECONOMIC_METRICS_DOMAIN_SCHEMA_ID:
        blockers.append(f"{prefix}DOMAIN_ARTIFACT_SCHEMA_ID_MISMATCH")
    for field in ("fee_model_binding_digest_sha256", "slippage_model_binding_digest_sha256"):
        if not str(doc.get(field) or ""):
            blockers.append(f"{prefix}{field.upper()}_MISSING")
    blockers.extend(_increment_b_deferred(doc, prefix, "ECONOMIC_METRICS"))
    return blockers


def _walk_forward_extra(doc: Mapping[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if doc.get("schema_id") != WALK_FORWARD_DOMAIN_SCHEMA_ID:
        blockers.append(f"{prefix}DOMAIN_ARTIFACT_SCHEMA_ID_MISMATCH")
    if not str(doc.get("fold_binding_digest_sha256") or ""):
        blockers.append(f"{prefix}FOLD_BINDING_DIGEST_MISSING")
    blockers.extend(_increment_b_deferred(doc, prefix, "WALK_FORWARD"))
    return blockers


def _monte_carlo_extra(doc: Mapping[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if doc.get("schema_id") != MONTE_CARLO_DOMAIN_SCHEMA_ID:
        blockers.append(f"{prefix}DOMAIN_ARTIFACT_SCHEMA_ID_MISMATCH")
    for field in (
        "monte_carlo_method",
        "randomness_seed",
        "num_runs",
        "input_series_binding_digest_sha256",
        "result_summary_digest_sha256",
    ):
        if doc.get(field) in (None, ""):
            blockers.append(f"{prefix}{field.upper()}_MISSING")
    if doc.get("num_runs") is not None and int(doc.get("num_runs") or 0) < 1:
        blockers.append(f"{prefix}NUM_RUNS_INVALID")
    blockers.extend(_increment_b_deferred(doc, prefix, "MONTE_CARLO"))
    return blockers


def _stress_extra(doc: Mapping[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if doc.get("schema_id") != STRESS_DOMAIN_SCHEMA_ID:
        blockers.append(f"{prefix}DOMAIN_ARTIFACT_SCHEMA_ID_MISMATCH")
    if not str(doc.get("stress_suite_binding_digest_sha256") or ""):
        blockers.append(f"{prefix}STRESS_SUITE_BINDING_DIGEST_MISSING")
    blockers.extend(_increment_b_deferred(doc, prefix, "STRESS"))
    return blockers


def verify_economic_metrics_domain_evidence_v1(
    *,
    repo_root: Path,
    reference: Mapping[str, Any] | None = None,
    binding_context: VerificationBindingContextV1 | None = None,
    expected_implementation_surface_digest_sha256: str | None = None,
    expected_config_digest_sha256: str | None = None,
) -> DomainVerificationResultV1:
    return _common_domain_verify(
        repo_root=repo_root,
        reference=reference,
        domain="economic_metrics",
        schema_id=ECONOMIC_METRICS_DOMAIN_SCHEMA_ID,
        verifier_id=ECONOMIC_METRICS_VERIFIER_ID,
        extra_checks=_economic_metrics_extra,
        binding_context=binding_context,
        expected_implementation_surface_digest_sha256=expected_implementation_surface_digest_sha256,
        expected_config_digest_sha256=expected_config_digest_sha256,
    )


def verify_walk_forward_domain_evidence_v1(
    *,
    repo_root: Path,
    reference: Mapping[str, Any] | None = None,
    binding_context: VerificationBindingContextV1 | None = None,
    expected_implementation_surface_digest_sha256: str | None = None,
    expected_config_digest_sha256: str | None = None,
) -> DomainVerificationResultV1:
    return _common_domain_verify(
        repo_root=repo_root,
        reference=reference,
        domain="walk_forward",
        schema_id=WALK_FORWARD_DOMAIN_SCHEMA_ID,
        verifier_id=WALK_FORWARD_VERIFIER_ID,
        extra_checks=_walk_forward_extra,
        binding_context=binding_context,
        expected_implementation_surface_digest_sha256=expected_implementation_surface_digest_sha256,
        expected_config_digest_sha256=expected_config_digest_sha256,
    )


def verify_monte_carlo_domain_evidence_v1(
    *,
    repo_root: Path,
    reference: Mapping[str, Any] | None = None,
    binding_context: VerificationBindingContextV1 | None = None,
    expected_implementation_surface_digest_sha256: str | None = None,
    expected_config_digest_sha256: str | None = None,
) -> DomainVerificationResultV1:
    return _common_domain_verify(
        repo_root=repo_root,
        reference=reference,
        domain="monte_carlo",
        schema_id=MONTE_CARLO_DOMAIN_SCHEMA_ID,
        verifier_id=MONTE_CARLO_VERIFIER_ID,
        extra_checks=_monte_carlo_extra,
        binding_context=binding_context,
        expected_implementation_surface_digest_sha256=expected_implementation_surface_digest_sha256,
        expected_config_digest_sha256=expected_config_digest_sha256,
    )


def verify_stress_domain_evidence_v1(
    *,
    repo_root: Path,
    reference: Mapping[str, Any] | None = None,
    binding_context: VerificationBindingContextV1 | None = None,
    expected_implementation_surface_digest_sha256: str | None = None,
    expected_config_digest_sha256: str | None = None,
) -> DomainVerificationResultV1:
    return _common_domain_verify(
        repo_root=repo_root,
        reference=reference,
        domain="stress",
        schema_id=STRESS_DOMAIN_SCHEMA_ID,
        verifier_id=STRESS_VERIFIER_ID,
        extra_checks=_stress_extra,
        binding_context=binding_context,
        expected_implementation_surface_digest_sha256=expected_implementation_surface_digest_sha256,
        expected_config_digest_sha256=expected_config_digest_sha256,
    )
