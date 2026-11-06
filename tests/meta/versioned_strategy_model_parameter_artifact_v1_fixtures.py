"""Fixtures for versioned_strategy_model_parameter_artifact_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
    ARTIFACT_REL as ELIGIBILITY_ARTIFACT_REL,
    ComparisonPromotionCandidateEligibilityEvidenceInputs,
    produce_comparison_promotion_candidate_eligibility_evidence_v1,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ComparisonPromotionCandidateModelParameterIdentityBindingInputs,
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1,
)
from src.meta.learning_loop.comparison_promotion_policy_decision_v1 import (
    ARTIFACT_REL as POLICY_DECISION_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    VersionedStrategyModelParameterArtifactInputs,
    produce_versioned_strategy_model_parameter_artifact_v1,
)
from tests.meta.ai_promotion_assessment_v1_fixtures import (
    produce_ai_promotion_assessment_fixture,
)
from tests.meta.comparison_promotion_candidate_eligibility_evidence_v1_fixtures import (
    produce_candidate_identity_binding_bundle,
)


@dataclass(frozen=True)
class VersionedStrategyModelParameterArtifactFixtureBundle:
    candidate_identity_binding_bundle_dir: Path
    model_parameter_identity_binding_bundle_dir: Path
    ai_promotion_assessment_bundle_dir: Path | None
    versioned_artifact_bundle_dir: Path | None = None


def _binding_dirs_from_policy_chain(
    *,
    policy_decision_bundle_dir: Path,
) -> tuple[Path, Path]:
    policy_payload = read_manifest(policy_decision_bundle_dir / POLICY_DECISION_ARTIFACT_REL)
    eligibility_dir = Path(str(policy_payload["eligibility_evidence_ref"]))
    eligibility_payload = read_manifest(eligibility_dir / ELIGIBILITY_ARTIFACT_REL)
    candidate_dir = Path(str(eligibility_payload["candidate_identity_binding_bundle_ref"]))
    model_parameter_dir = Path(str(policy_payload["model_parameter_identity_binding_bundle_ref"]))
    return candidate_dir, model_parameter_dir


def produce_versioned_artifact_input_bundles(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    identity_binding_name: str = "identity_binding",
    eligibility_name: str = "eligibility_evidence",
    model_parameter_binding_name: str = "model_parameter_identity_binding",
    include_ai_assessment: bool = False,
    ai_assessment_name: str = "ai_assessment",
) -> VersionedStrategyModelParameterArtifactFixtureBundle:
    ai_dir: Path | None = None
    if include_ai_assessment:
        ai_fixture = produce_ai_promotion_assessment_fixture(
            tmp_path / "ai_promotion_chain",
            durable_root,
            all_domains_pass=all_domains_pass,
            use_candidate_lineage=use_candidate_lineage,
            ai_assessment_name=ai_assessment_name,
        )
        assert ai_fixture.policy_decision_bundle_dir is not None
        assert ai_fixture.ai_promotion_assessment_bundle_dir is not None
        candidate_dir, model_parameter_dir = _binding_dirs_from_policy_chain(
            policy_decision_bundle_dir=ai_fixture.policy_decision_bundle_dir,
        )
        return VersionedStrategyModelParameterArtifactFixtureBundle(
            candidate_identity_binding_bundle_dir=candidate_dir,
            model_parameter_identity_binding_bundle_dir=model_parameter_dir,
            ai_promotion_assessment_bundle_dir=ai_fixture.ai_promotion_assessment_bundle_dir,
        )

    identity = produce_candidate_identity_binding_bundle(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        binding_name=identity_binding_name,
    )
    eligibility_dir = durable_root / eligibility_name
    produce_comparison_promotion_candidate_eligibility_evidence_v1(
        inputs=ComparisonPromotionCandidateEligibilityEvidenceInputs(
            candidate_identity_binding_bundle_dir=identity.candidate_identity_binding_bundle_dir,
        ),
        output_dir=eligibility_dir,
    )
    model_parameter_dir = durable_root / model_parameter_binding_name
    produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        inputs=ComparisonPromotionCandidateModelParameterIdentityBindingInputs(
            eligibility_evidence_bundle_dir=eligibility_dir,
        ),
        output_dir=model_parameter_dir,
    )
    return VersionedStrategyModelParameterArtifactFixtureBundle(
        candidate_identity_binding_bundle_dir=identity.candidate_identity_binding_bundle_dir,
        model_parameter_identity_binding_bundle_dir=model_parameter_dir,
        ai_promotion_assessment_bundle_dir=ai_dir,
    )


def produce_versioned_artifact_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    include_ai_assessment: bool = False,
    versioned_artifact_name: str = "versioned_artifact",
    produce_output: bool = True,
) -> VersionedStrategyModelParameterArtifactFixtureBundle:
    bundles = produce_versioned_artifact_input_bundles(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
    )
    versioned_dir: Path | None = None
    if produce_output:
        versioned_dir = durable_root / versioned_artifact_name
        produce_versioned_strategy_model_parameter_artifact_v1(
            inputs=VersionedStrategyModelParameterArtifactInputs(
                candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
                model_parameter_identity_binding_bundle_dir=(
                    bundles.model_parameter_identity_binding_bundle_dir
                ),
                ai_promotion_assessment_bundle_dir=bundles.ai_promotion_assessment_bundle_dir,
            ),
            output_dir=versioned_dir,
        )
    return VersionedStrategyModelParameterArtifactFixtureBundle(
        candidate_identity_binding_bundle_dir=bundles.candidate_identity_binding_bundle_dir,
        model_parameter_identity_binding_bundle_dir=bundles.model_parameter_identity_binding_bundle_dir,
        ai_promotion_assessment_bundle_dir=bundles.ai_promotion_assessment_bundle_dir,
        versioned_artifact_bundle_dir=versioned_dir,
    )
