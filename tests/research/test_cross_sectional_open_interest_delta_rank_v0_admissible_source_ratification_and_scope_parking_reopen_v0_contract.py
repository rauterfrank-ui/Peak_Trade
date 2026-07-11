"""Contract tests for cross_sectional open interest delta rank v0 source ratification and reopen."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_and_scope_parking_reopen_v0 import (
    BOUND_OBSERVATION_COUNT,
    CONFIRM_GO,
    DATASET_REGISTRY_REL_PATH,
    PARKING_CONFIG_REL_PATH,
    RATIFICATION_ID,
    REOPEN_REQUIRES,
    RESEARCH_SCOPE,
    SCOPE_STATUS_REOPENED,
    SourceRatificationStatus,
    apply_source_ratification_and_scope_reopen_fields,
    assess_source_admissibility_v0,
    coverage_freshness_reexecution_required_by_contract,
    execute_source_ratification_and_scope_reopen_v0,
    ratification_result_to_dict_v0,
    validate_required_source_evidence_bundles,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    SCOPE_STATUS as PARKED_SCOPE_STATUS,
    materialize_registration_config,
    validate_source_evidence_preconditions,
)
from src.research.okx_self_accumulated_forward_open_interest_overlap_validation_v0 import (
    OverlapValidationStatus,
    OverlapValidationVerdict,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_REGISTRY_CONFIG = REPO_ROOT / DATASET_REGISTRY_REL_PATH
RATIFICATION_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_"
    "and_scope_parking_reopen_v0.json"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)
AS_OF_UTC = "2026-07-11T19:50:00Z"


class TestSourceEvidenceBundles:
    def test_required_source_evidence_manifests_verify(self) -> None:
        bundles = validate_required_source_evidence_bundles()
        assert set(bundles) == {
            "correction_reexecution",
            "overlap_corrected_archive",
            "scope_parking",
            "pr5111_closeout",
        }
        for bundle in bundles.values():
            assert bundle.manifest_verify_rc == 0


class TestCoverageFreshnessContract:
    def test_post_correction_reexecution_not_required_by_contract(self) -> None:
        assert coverage_freshness_reexecution_required_by_contract() is False


class TestSourceAdmissibilityAssessment:
    def test_admissible_for_self_accumulation_insufficient_for_panel(self) -> None:
        assessment = assess_source_admissibility_v0(
            overlap_result={
                "status": OverlapValidationStatus.PASS.value,
                "verdict": OverlapValidationVerdict.PASS.value,
            },
            correction_reexecution_report={
                "PROVENANCE_VALIDATION_PASS": True,
                "INTEGRITY_AUDIT_PASS": True,
                "APPEND_ONLY_PRESERVED": True,
                "HISTORICAL_EVIDENCE_PRESERVED": True,
            },
            observation_count=BOUND_OBSERVATION_COUNT,
        )
        assert assessment.source_provenance_verified is True
        assert assessment.archive_integrity_verified is True
        assert assessment.overlap_agreement_verified is True
        assert assessment.source_admissible_for_continued_self_accumulation is True
        assert assessment.source_sufficient_for_panel_materialization is False
        assert assessment.source_sufficient_for_economic_evaluation is False
        assert assessment.source_sufficient_for_runtime_promotion is False
        assert assessment.historical_depth_sufficient is False
        assert assessment.observation_count == 2


class TestRatificationExecution:
    def test_execute_ratification_and_reopen_pass(self) -> None:
        result = execute_source_ratification_and_scope_reopen_v0(
            confirm_go=CONFIRM_GO,
            as_of_utc=AS_OF_UTC,
            enabled=True,
        )
        assert result.verdict.value == "PASS"
        assert result.source_ratification_status is SourceRatificationStatus.ADMISSIBLE
        assert result.overlap_validation_status == OverlapValidationStatus.PASS.value
        assert result.scope_status_before == PARKED_SCOPE_STATUS
        assert result.scope_status_after == SCOPE_STATUS_REOPENED
        assert result.reopen_requirements_satisfied is True
        assert result.coverage_freshness_reexecution_status == "NOT_REQUIRED_BY_CANONICAL_CONTRACT"
        assert result.assessment.observation_count == BOUND_OBSERVATION_COUNT
        assert result.registration_config["dataset_ready"] is False
        assert result.registration_config["economic_evaluation_allowed"] is False
        assert result.registration_config["ready_for_zero_order_runtime"] is False
        assert result.dataset_registry["dataset_registration"]["dataset_ready"] is False
        assert (
            result.dataset_registry["dataset_registration"]["dataset_materialization_allowed"]
            is False
        )

    def test_deterministic_ratification_result_dict(self) -> None:
        first = execute_source_ratification_and_scope_reopen_v0(
            confirm_go=CONFIRM_GO,
            as_of_utc=AS_OF_UTC,
            enabled=True,
        )
        second = execute_source_ratification_and_scope_reopen_v0(
            confirm_go=CONFIRM_GO,
            as_of_utc=AS_OF_UTC,
            enabled=True,
        )
        assert ratification_result_to_dict_v0(first) == ratification_result_to_dict_v0(second)


class TestRegistryRoundtrip:
    def test_apply_reopen_fields_preserves_prior_parking_evidence(self) -> None:
        source = validate_source_evidence_preconditions()
        parking = materialize_registration_config(source=source)
        registry = json.loads(DATASET_REGISTRY_CONFIG.read_text(encoding="utf-8"))
        bundles = validate_required_source_evidence_bundles()
        assessment = assess_source_admissibility_v0(
            overlap_result={
                "status": OverlapValidationStatus.PASS.value,
                "verdict": OverlapValidationVerdict.PASS.value,
            },
            correction_reexecution_report={
                "PROVENANCE_VALIDATION_PASS": True,
                "INTEGRITY_AUDIT_PASS": True,
                "APPEND_ONLY_PRESERVED": True,
                "HISTORICAL_EVIDENCE_PRESERVED": True,
            },
            observation_count=BOUND_OBSERVATION_COUNT,
        )
        registration, updated = apply_source_ratification_and_scope_reopen_fields(
            parking_registration=parking,
            registry=registry,
            assessment=assessment,
            evidence_bundles=bundles,
        )
        assert registration["prior_parking_evidence_dir"]
        assert registration["scope_parking_guard_report"] is not None
        assert updated["scope_parking"] is not None
        assert updated["scope_status"] == SCOPE_STATUS_REOPENED
        assert updated["dataset_registration"]["prior_parking_evidence_ref"]
        assert updated["dataset_registration"]["dataset_ready"] is False


class TestRatificationModuleSafety:
    def test_no_runtime_or_scheduler_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_"
            "and_scope_parking_reopen_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_reopen_requires_unchanged(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        assert config["research_scope"] == RESEARCH_SCOPE
        assert config["reopen_requires"] == REOPEN_REQUIRES
        assert config["ratification_owner"] == RATIFICATION_ID
        assert config["runtime_effect"] == "NONE"
        assert config["authority_effect"] == "NONE"

    def test_parking_config_rel_path_present(self) -> None:
        assert (REPO_ROOT / PARKING_CONFIG_REL_PATH).is_file()
