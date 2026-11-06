"""Fixtures for comparison_config_patch_manifest_cross_domain_lineage_binding_v1 tests."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.meta.learning_loop.comparison_config_patch_manifest_cross_domain_lineage_binding_v1 import (
    ComparisonConfigPatchManifestCrossDomainLineageBindingInputs,
    produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ComparisonPromotionCandidateModelParameterIdentityBindingInputs,
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1,
)
from src.meta.learning_loop.config_patch_manifest_v1 import (
    build_empty_config_patch_manifest_v1,
    serialize_config_patch_manifest_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from tests.meta.comparison_promotion_candidate_model_parameter_identity_binding_v1_fixtures import (
    produce_eligibility_evidence_bundle,
)

CANDIDATE_LINEAGE_MANIFEST_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
CONFIG_PATCH_MANIFEST_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
FIXED_NOW = datetime(1970, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class CrossDomainLineageBindingFixtureBundle:
    model_parameter_identity_binding_bundle_dir: Path
    config_patch_manifest_path: Path
    cross_domain_binding_bundle_dir: Path | None = None


def write_matching_config_patch_manifest(
    path: Path,
    *,
    lineage_manifest_ref: str = CANDIDATE_LINEAGE_MANIFEST_ID,
    manifest_id: str = CONFIG_PATCH_MANIFEST_ID,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=manifest_id,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=lineage_manifest_ref,
        generated_by="comparison_config_patch_manifest_cross_domain_lineage_binding_v1_fixtures",
    )
    path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")
    return path


def produce_model_parameter_identity_binding_bundle(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    binding_name: str = "model_parameter_identity_binding",
) -> Path:
    eligibility = produce_eligibility_evidence_bundle(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
    )
    out = durable_root / binding_name
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=ComparisonPromotionCandidateModelParameterIdentityBindingInputs(
            eligibility_evidence_bundle_dir=eligibility.eligibility_evidence_bundle_dir,
        ),
        output_dir=out,
    )
    return out


def produce_cross_domain_lineage_binding_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    model_parameter_binding_name: str = "model_parameter_identity_binding",
    config_patch_name: str = "config_patch_manifest_v1.json",
    cross_domain_binding_name: str = "cross_domain_lineage_binding",
    produce_output: bool = True,
    lineage_manifest_ref: str = CANDIDATE_LINEAGE_MANIFEST_ID,
) -> CrossDomainLineageBindingFixtureBundle:
    step1_dir = produce_model_parameter_identity_binding_bundle(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        binding_name=model_parameter_binding_name,
    )
    config_patch_path = write_matching_config_patch_manifest(
        durable_root / config_patch_name,
        lineage_manifest_ref=lineage_manifest_ref,
    )
    cross_domain_dir: Path | None = None
    if produce_output:
        cross_domain_dir = durable_root / cross_domain_binding_name
        produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
            inputs=ComparisonConfigPatchManifestCrossDomainLineageBindingInputs(
                model_parameter_identity_binding_bundle_dir=step1_dir,
                config_patch_manifest_path=config_patch_path,
            ),
            output_dir=cross_domain_dir,
        )
    return CrossDomainLineageBindingFixtureBundle(
        model_parameter_identity_binding_bundle_dir=step1_dir,
        config_patch_manifest_path=config_patch_path,
        cross_domain_binding_bundle_dir=cross_domain_dir,
    )


def read_step1_artifact(step1_dir: Path) -> dict:
    return read_manifest(
        step1_dir / "comparison_promotion_candidate_model_parameter_identity_binding_v1.json"
    )


def fresh_config_patch_manifest_id() -> str:
    return str(uuid.uuid4())
