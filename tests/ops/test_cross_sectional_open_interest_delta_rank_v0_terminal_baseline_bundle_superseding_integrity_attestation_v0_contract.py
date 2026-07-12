"""Contract tests for cross_sectional_open_interest_delta_rank v0 terminal baseline superseding integrity attestation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_superseding_integrity_attestation_v0 import (
    ACTUAL_FILE_DIGEST,
    ATTESTATION_ID,
    BASELINE_BINDING_DIGEST,
    BASELINE_CLASSIFICATION,
    CONFIG_REL_PATH,
    DRIFTED_FILE,
    EXPECTED_FILE_DIGEST,
    GOVERNANCE_REL_PATH,
    OPERATOR_GO_TOKEN,
    PROVISIONAL_RANK1,
    RESEARCH_SCOPE,
    SUPERSESSION_MODE,
    TARGET_SOURCE_EVIDENCE_DIR,
    assess_downstream_ranking_operative_admissibility,
    build_external_superseding_integrity_attestation_contract,
    build_integrity_attestation,
    compute_attestation_digest,
    materialize_attestation_config,
    serialize_canonical_json,
    validate_attestation_preconditions,
    validate_target_bundle_unchanged,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MODULE_PATH = (
    REPO_ROOT / "src/research/"
    "cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


class TestIntegrityAttestationPreconditions:
    def test_target_manifest_verify_rc_is_one_for_final_report_only(self) -> None:
        preconditions = validate_attestation_preconditions()
        assert preconditions.target_snapshot.manifest_verify_rc == 1
        assert preconditions.target_snapshot.drifted_file_digest == ACTUAL_FILE_DIGEST
        assert preconditions.reconciliation_status.manifest_verify_rc == 0
        assert preconditions.downstream_status.manifest_verify_rc == 0
        assert all(
            item.manifest_verify_rc == 0 for item in preconditions.independent_source_statuses
        )

    def test_target_bundle_unchanged_after_validation(self) -> None:
        preconditions = validate_attestation_preconditions()
        validate_target_bundle_unchanged(preconditions.target_snapshot)


class TestIntegrityAttestationDeterminism:
    def test_attestation_digest_stable(self) -> None:
        preconditions = validate_attestation_preconditions()
        first = materialize_attestation_config(preconditions)
        second = materialize_attestation_config(preconditions)
        assert first["attestation"] == second["attestation"]
        assert first["attestation"]["attestation_digest"] == compute_attestation_digest(
            first["attestation"]
        )


class TestIntegrityAttestationContract:
    def test_config_exists_and_required_fields(self) -> None:
        assert CONFIG_PATH.is_file()
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert payload["artifact_kind"] == ATTESTATION_ID
        assert payload["go_token"] == OPERATOR_GO_TOKEN
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["target_manifest_verify_rc"] == 1
        assert payload["drifted_file"] == DRIFTED_FILE
        assert payload["expected_file_digest"] == EXPECTED_FILE_DIGEST
        assert payload["actual_file_digest"] == ACTUAL_FILE_DIGEST
        assert payload["baseline_binding_digest"] == BASELINE_BINDING_DIGEST
        assert payload["baseline_classification"] == BASELINE_CLASSIFICATION
        assert payload["supersession_mode"] == SUPERSESSION_MODE
        assert payload["does_not_convert_target_manifest_rc_to_zero"] is True
        assert payload["downstream_ranking_operatively_admissible"] is True
        assert payload["provisional_rank1"] == PROVISIONAL_RANK1
        assert payload["economic_evaluation_executed"] is False
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        contract = payload["external_superseding_integrity_attestation_contract"]
        assert contract["admissible_for_integrity_consumption_only"] is True

    def test_attestation_never_claims_target_rc_zero(self) -> None:
        preconditions = validate_attestation_preconditions()
        attestation = build_integrity_attestation(preconditions)
        assert attestation["target_manifest_verify_rc"] == 1
        assert attestation["does_not_convert_target_manifest_rc_to_zero"] is True

    def test_downstream_admissibility_true_with_additive_contract(self) -> None:
        preconditions = validate_attestation_preconditions()
        attestation = build_integrity_attestation(preconditions)
        assessment = assess_downstream_ranking_operative_admissibility(
            attestation,
            contract=build_external_superseding_integrity_attestation_contract(),
        )
        assert assessment["downstream_ranking_operatively_admissible"] is True
        assert assessment["remaining_contract_blockers"] == []

    def test_canonical_serialization_stable(self) -> None:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert serialize_canonical_json(payload) == serialize_canonical_json(payload)


class TestIntegrityAttestationGovernance:
    def test_governance_doc_contains_required_markers(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION" in text
        assert "TARGET_MANIFEST_VERIFY_RC" in text
        assert "COMPROMISED" in text
        assert "PRESERVED" in text
        assert "NON-authorizing" in text or "Non-authorizing" in text


class TestIntegrityAttestationModuleGuards:
    def test_no_runtime_or_scheduler_imports(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_target_dir_matches_expected_bundle(self) -> None:
        assert TARGET_SOURCE_EVIDENCE_DIR.is_dir()
        assert (TARGET_SOURCE_EVIDENCE_DIR / "terminal_classification.json").is_file()
        ok, _msg = verify_manifest_sha256(TARGET_SOURCE_EVIDENCE_DIR)
        assert ok is False

    def test_target_manifest_lists_expected_final_report_digest(self) -> None:
        manifest = (TARGET_SOURCE_EVIDENCE_DIR / "MANIFEST.sha256").read_text(encoding="utf-8")
        assert EXPECTED_FILE_DIGEST in manifest
        assert DRIFTED_FILE in manifest
