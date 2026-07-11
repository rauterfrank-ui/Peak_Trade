"""Contract tests for cross_sectional open interest delta rank v0 capability gap parking."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    CAPABILITY_STATUS,
    DATASET_REGISTRY_REL_PATH,
    CONFIRM_GO,
    PARK_REASON,
    REGISTRATION_ID,
    RESEARCH_SCOPE,
    REOPEN_REQUIRES,
    SCOPE_STATUS,
    SOURCE_EVIDENCE_DIR,
    apply_dataset_registry_parking_fields,
    compute_registration_digest,
    is_dataset_materialization_2024_allowed,
    is_economic_evaluation_allowed,
    is_historical_backfill_allowed,
    is_live_oi_collection_blocked,
    is_scope_parked,
    is_self_accumulated_archive_allowed,
    is_unchanged_retry_blocked,
    materialize_registration_config,
    validate_source_evidence_preconditions,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0.json"
)
DATASET_REGISTRY_CONFIG = REPO_ROOT / DATASET_REGISTRY_REL_PATH
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


class TestCapabilityGapParkingModule:
    def test_source_evidence_preconditions_and_deterministic_registration(self) -> None:
        source = validate_source_evidence_preconditions()
        assert source.manifest_verify_rc == 0
        assert source.capability_classification == "NO_ADMISSIBLE_PUBLIC_HISTORICAL_OI_SOURCE"
        first = materialize_registration_config(source=source)
        second = materialize_registration_config(source=source)
        assert first == second
        assert first["registration_digest"] == compute_registration_digest(first)

    def test_no_runtime_or_scheduler_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_scope_parked_and_retry_blocked(self) -> None:
        registration = materialize_registration_config()
        guard = registration["scope_parking_guard_report"]
        assert is_scope_parked(guard=guard)
        assert is_unchanged_retry_blocked(guard=guard)
        assert registration["scope_status"] == SCOPE_STATUS
        assert registration["capability_status"] == CAPABILITY_STATUS
        assert registration["park_reason"] == PARK_REASON

    def test_evaluation_and_2024_materialization_blocked(self) -> None:
        registration = materialize_registration_config()
        guard = registration["scope_parking_guard_report"]
        assert not is_economic_evaluation_allowed(guard=guard)
        assert not is_dataset_materialization_2024_allowed(guard=guard)
        assert registration["economic_evaluation_allowed"] is False
        assert registration["dataset_materialization_2024_allowed"] is False

    def test_live_collection_and_self_accumulated_archive_allowed(self) -> None:
        registration = materialize_registration_config()
        guard = registration["scope_parking_guard_report"]
        assert not is_live_oi_collection_blocked(guard=guard)
        assert is_self_accumulated_archive_allowed(guard=guard)
        assert registration["live_oi_collection"] == "CONTINUE"
        assert registration["primary_forward_data_path"] == "SELF_ACCUMULATED_HISTORY"

    def test_historical_backfill_deferred_requires_overlap_validation(self) -> None:
        registration = materialize_registration_config()
        guard = registration["scope_parking_guard_report"]
        assert not is_historical_backfill_allowed(guard=guard)
        assert registration["historical_backfill"] == "DEFERRED"
        assert registration["backfill_validation"] == "REQUIRED_OVERLAP"
        assert registration["reopen_requires"] == REOPEN_REQUIRES
        assert guard["reopen_requires"] == REOPEN_REQUIRES

    def test_no_runtime_or_authority_effect(self) -> None:
        registration = materialize_registration_config()
        assert registration["runtime_effect"] == "NONE"
        assert registration["authority_effect"] == "NONE"
        assert registration["no_runtime_or_promotion_action"] is True
        assert registration["no_scheduler_runtime"] is True

    def test_dataset_registry_parking_fields_applied(self) -> None:
        registry = json.loads(DATASET_REGISTRY_CONFIG.read_text(encoding="utf-8"))
        registration = materialize_registration_config()
        updated = apply_dataset_registry_parking_fields(registry, registration)
        assert updated["scope_status"] == "PARKED"
        assert updated["capability_status"] == CAPABILITY_STATUS
        assert updated["capability_gap_registration_ref"] == REGISTRATION_ID
        dataset = updated["dataset_registration"]
        assert dataset["materialization_status"] == "PARKED_EXTERNAL_DATA_CAPABILITY_GAP"
        assert dataset["scope_status"] == "PARKED"
        assert dataset["unchanged_retry_blocked"] is True
        assert dataset["live_oi_collection_blocked"] is False
        assert dataset["self_accumulated_archive_allowed"] is True
        assert dataset["historical_backfill_allowed"] is False
        assert dataset["economic_evaluation_allowed"] is False
        assert dataset["dataset_materialization_2024_allowed"] is False
        assert dataset["source_evidence_ref"] == str(SOURCE_EVIDENCE_DIR)


class TestCapabilityGapParkingArtifacts:
    def test_registration_config_matches_guard_semantics(self) -> None:
        on_disk = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        materialized = materialize_registration_config()
        for field in (
            "research_scope",
            "scope_status",
            "capability_status",
            "park_reason",
            "unchanged_retry_blocked",
            "live_oi_collection_blocked",
            "self_accumulated_archive_allowed",
            "historical_backfill_allowed",
            "reopen_requires",
            "runtime_effect",
            "authority_effect",
        ):
            assert on_disk[field] == materialized[field]

    def test_dataset_registry_entry_parked(self) -> None:
        registry = json.loads(DATASET_REGISTRY_CONFIG.read_text(encoding="utf-8"))
        assert registry["research_scope"] == RESEARCH_SCOPE
        assert registry["scope_status"] == "PARKED"
        assert registry["capability_status"] == CAPABILITY_STATUS
        assert (
            "cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0"
            in registry["registered_capabilities"]
        )
        dataset = registry["dataset_registration"]
        assert dataset["materialization_status"] == "PARKED_EXTERNAL_DATA_CAPABILITY_GAP"
        assert dataset["unchanged_retry_blocked"] is True
        assert dataset["live_oi_collection_blocked"] is False
        assert dataset["self_accumulated_archive_allowed"] is True

    def test_operator_go_token_present(self) -> None:
        on_disk = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert on_disk["go_token"] == CONFIRM_GO
