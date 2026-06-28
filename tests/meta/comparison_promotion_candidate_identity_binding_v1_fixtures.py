"""Fixtures for comparison_promotion_candidate_identity_binding_v1 contract tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME as EXPERIMENT_IDENTITY_ARTIFACT,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    LineageRelation,
    build_candidate_lineage_manifest_v1_from_producer_input,
    serialize_candidate_lineage_manifest_v1,
)
from src.meta.learning_loop.comparison_completion_promotion_input_binding_v1 import (
    ComparisonCompletionPromotionInputBindingInputs,
    produce_comparison_completion_promotion_input_binding_v1,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    produce_comparison_metric_input_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from tests.meta.comparison_completion_promotion_input_binding_v1_fixtures import (
    UpstreamBindingBundle,
    produce_upstream_binding_bundle,
)

CANDIDATE_LINEAGE_ARTIFACT_REL = "candidate_lineage_manifest_v1.json"
FIXED_NOW = datetime(1970, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class PromotionInputBindingBundle:
    promotion_input_binding_bundle_dir: Path
    upstream: UpstreamBindingBundle


@dataclass(frozen=True)
class CandidateIdentityFixtureBundle:
    candidate_identity_bundle_dir: Path
    source_type: str


def produce_promotion_input_binding_bundle(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    binding_name: str = "promotion_input_binding",
) -> PromotionInputBindingBundle:
    upstream = produce_upstream_binding_bundle(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
    )
    out = durable_root / binding_name
    produce_comparison_completion_promotion_input_binding_v1(
        inputs=ComparisonCompletionPromotionInputBindingInputs(
            completion_validity_binding_bundle_dir=upstream.completion_validity_binding_bundle_dir,
        ),
        output_dir=out,
    )
    return PromotionInputBindingBundle(
        promotion_input_binding_bundle_dir=out,
        upstream=upstream,
    )


def produce_metric_input_candidate_bundle(
    tmp_path: Path,
    durable_root: Path,
    *,
    promotion_input: PromotionInputBindingBundle,
    binding_name: str = "candidate_metric_input",
) -> CandidateIdentityFixtureBundle:
    """Explicit metric-input candidate bundle aligned with promotion input experiment lineage."""
    checkpoint_index = read_manifest(
        promotion_input.upstream.matched.checkpoint_bundle_dir
        / "comparison_checkpoint_index_v1.json"
    )
    common_bundle_ref = checkpoint_index.get("common_bundle_ref", {})
    common_bundle_dir = Path(str(common_bundle_ref.get("source_path", "")))
    metric_manifest_path = (
        common_bundle_dir
        / "embedded/metric_input_bindings/00/comparison_metric_input_manifest_v1.json"
    )
    if not metric_manifest_path.is_file():
        raise RuntimeError(f"metric input manifest not found: {metric_manifest_path}")

    out = durable_root / binding_name
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=metric_manifest_path,
        output_dir=out,
    )
    return CandidateIdentityFixtureBundle(
        candidate_identity_bundle_dir=out,
        source_type="comparison_metric_input_durable_evidence_binding_v1",
    )


def produce_candidate_lineage_candidate_bundle(
    durable_root: Path,
    *,
    promotion_input: PromotionInputBindingBundle,
    binding_name: str = "candidate_lineage",
    candidate_id: str = "candidate-bundle-binding-test-001",
) -> CandidateIdentityFixtureBundle:
    experiment_ref = read_manifest(
        promotion_input.promotion_input_binding_bundle_dir
        / "comparison_completion_promotion_input_binding_v1.json"
    )["experiment_identity_ref"]
    experiment_manifest = read_manifest(Path(experiment_ref) / EXPERIMENT_IDENTITY_ARTIFACT)
    experiment_identity_id = experiment_manifest["experiment_identity_id"]
    experiment_digest = experiment_manifest["integrity"]["content_sha256"]

    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        {
            "lineage_manifest_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            "candidate_id": candidate_id,
            "candidate_type": "config_patch_bundle",
            "candidate_contract_ref": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            "refs": [
                {
                    "ref_type": LineageRefType.EXPERIMENT.value,
                    "ref_id": experiment_identity_id,
                    "relation": LineageRelation.SOURCES.value,
                    "owner_domain": "experiments/base",
                    "required": True,
                    "digest": experiment_digest,
                }
            ],
            "created_at": FIXED_NOW.isoformat(),
            "created_by": "comparison_promotion_candidate_identity_binding_v1_fixtures",
        },
        created_at=FIXED_NOW,
    )
    out = durable_root / binding_name
    out.mkdir(parents=True, exist_ok=True)
    artifact_path = out / CANDIDATE_LINEAGE_ARTIFACT_REL
    artifact_path.write_text(serialize_candidate_lineage_manifest_v1(manifest), encoding="utf-8")
    write_manifest_sha256(out)
    return CandidateIdentityFixtureBundle(
        candidate_identity_bundle_dir=out,
        source_type="candidate_lineage_manifest_v1",
    )
