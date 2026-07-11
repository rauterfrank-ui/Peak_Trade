"""OKX self-accumulated forward OI archive correction and executable binding v0.

Fail-closed contract layer for provenance classification, generation binding,
supersession registration, and executable correction planning. Does not mutate
archives, execute collectors, or authorize correction execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    BAR_INTERVAL,
    SOURCE_ENDPOINT,
    SOURCE_SCHEMA_VERSION,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_MANIFEST_FILENAME,
    ARCHIVE_SCHEMA_VERSION,
    OBSERVATIONS_JSONL_FILENAME,
    OPEN_INTEREST_UNIT,
    VENUE,
    compute_observation_digest_v0,
    serialize_canonical_json,
)
from src.research.okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0 import (
    MODULE_VERSION as COLLECTOR_MODULE_VERSION,
)
from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest

PACKAGE_MARKER = (
    "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_CORRECTION_AND_EXECUTABLE_BINDING_V0=true"
)
MODULE_VERSION = (
    "okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding.v0"
)
CONFIRM_GO = (
    "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_CORRECTION_AND_EXECUTABLE_BINDING_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0.json"
)

ARCHIVE_OWNER = "okx_self_accumulated_forward_open_interest_archive_v0"
COLLECTOR_OWNER = "okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0"
EXTERNAL_REFERENCE_OWNER = (
    "okx_distinct_external_reference_forward_open_interest_snapshot_materialization_v0"
)
OVERLAP_VALIDATOR_OWNER = "okx_self_accumulated_forward_open_interest_overlap_validation_v0"

PERMITTED_COLLECTOR_ENTRY_POINT = (
    "scripts/ops/collect_okx_self_accumulated_forward_open_interest_one_shot_v0.py"
)
PERMITTED_OVERLAP_ENTRY_POINT = (
    "scripts/ops/validate_okx_self_accumulated_forward_open_interest_overlap_v0.py"
)
FORBIDDEN_EXTERNAL_REFERENCE_AS_SELF_SOURCE = EXTERNAL_REFERENCE_OWNER

PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "source_mode",
    "fixture_source_used",
    "live_fetch_enabled",
    "raw_source_digest",
    "collector_owner",
    "collector_version",
    "collection_execution_id",
    "venue_id",
    "instrument_id",
    "bar_interval",
    "unit",
    "venue_timestamp_ms",
    "collected_at_utc",
    "observation_digest",
    "evidence_ref",
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
EXPECTED_OVERLAP_POLICY = "EXACT_VENUE_TIMESTAMP_MS_ZERO_TOLERANCE"
NEXT_CANONICAL_STEP = (
    "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_CORRECTION_EXECUTION_V0_"
    "AGAINST_EXECUTABLE_BINDING"
)


class SourceModeV0(str, Enum):
    LIVE_FETCH = "LIVE_FETCH"
    FIXTURE_INJECTED = "FIXTURE_INJECTED"
    TEST_SYNTHETIC = "TEST_SYNTHETIC"
    UNKNOWN = "UNKNOWN"


class ArchiveObservationAdmissibilityV0(str, Enum):
    PRODUCTION_ADMISSIBLE = "PRODUCTION_ADMISSIBLE"
    FIXTURE_NON_PRODUCTION = "FIXTURE_NON_PRODUCTION"
    TEST_NON_PRODUCTION = "TEST_NON_PRODUCTION"
    UNKNOWN_BLOCKED = "UNKNOWN_BLOCKED"


class GenerationModeV0(str, Enum):
    INITIAL = "INITIAL"
    CORRECTION = "CORRECTION"
    SUPERSESSION = "SUPERSESSION"


class ExternalReferenceUsageV0(str, Enum):
    VALIDATION_ONLY = "VALIDATION_ONLY"
    SELF_SOURCE = "SELF_SOURCE"


class BindingValidationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class MaterializationTerminalStatus(str, Enum):
    COMPLETE = "COMPLETE"
    FAIL_CLOSED_OPERATOR_GO = "FAIL_CLOSED_OPERATOR_GO"
    FAIL_CLOSED_DEFAULT_OFF = "FAIL_CLOSED_DEFAULT_OFF"
    FAIL_CLOSED_BINDING = "FAIL_CLOSED_BINDING"
    FAIL_CLOSED_INVALID_INPUT = "FAIL_CLOSED_INVALID_INPUT"


@dataclass(frozen=True)
class ArchiveObservationProvenanceV0:
    source_mode: str
    fixture_source_used: bool
    live_fetch_enabled: bool
    raw_source_digest: str | None
    collector_owner: str
    collector_version: str
    collection_execution_id: str
    venue_id: str
    instrument_id: str
    bar_interval: str
    unit: str
    venue_timestamp_ms: int
    collected_at_utc: str
    observation_digest: str
    evidence_ref: str | None


@dataclass(frozen=True)
class ArchiveGenerationBindingV0:
    generation_id: str
    parent_generation_id: str | None
    generation_mode: str
    source_observation_refs: tuple[str, ...]
    excluded_observation_refs: tuple[str, ...]
    supersession_record_refs: tuple[str, ...]
    generation_digest: str
    created_by_owner: str
    created_at_utc: str


@dataclass(frozen=True)
class ArchiveSupersessionRecordV0:
    superseded_observation_ref: str
    replacement_observation_ref: str | None
    supersession_reason: str
    historical_record_preserved: bool = True
    in_place_mutation: bool = False
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT
    supersession_digest: str = ""


@dataclass(frozen=True)
class ExecutableArchiveCorrectionBindingV0:
    permitted_entry_point: str
    allowed_source_modes: tuple[str, ...]
    required_provenance_fields: tuple[str, ...]
    required_admissibility: str
    input_archive_generation_id: str
    output_archive_generation_id: str
    external_reference_usage: str
    overwrite_allowed: bool
    historical_evidence_preserved: bool
    expected_overlap_policy: str
    expected_deterministic_second_run: bool
    executable_binding_digest: str
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


@dataclass(frozen=True)
class ObservationAdmissibilityAssessmentV0:
    observation_digest: str
    provenance: ArchiveObservationProvenanceV0
    admissibility: str
    executable_binding_eligible: bool
    production_snapshot_path: str | None
    path_name_claims_production_authority: bool


@dataclass(frozen=True)
class BindingValidationResultV0:
    verdict: BindingValidationVerdict
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


@dataclass(frozen=True)
class ContractMaterializationResultV0:
    status: MaterializationTerminalStatus
    archive_correction_contract: dict[str, Any]
    provenance_records: tuple[ArchiveObservationProvenanceV0, ...]
    admissibility_assessments: tuple[ObservationAdmissibilityAssessmentV0, ...]
    generation_binding: ArchiveGenerationBindingV0
    supersession_records: tuple[ArchiveSupersessionRecordV0, ...]
    executable_binding: ExecutableArchiveCorrectionBindingV0
    correction_execution_plan: dict[str, Any]
    deterministic_materialization: bool
    second_materialization_diff_empty: bool
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def compute_provenance_digest_v0(provenance: ArchiveObservationProvenanceV0) -> str:
    payload = {
        "source_mode": provenance.source_mode,
        "fixture_source_used": provenance.fixture_source_used,
        "live_fetch_enabled": provenance.live_fetch_enabled,
        "raw_source_digest": provenance.raw_source_digest,
        "collector_owner": provenance.collector_owner,
        "collector_version": provenance.collector_version,
        "collection_execution_id": provenance.collection_execution_id,
        "venue_id": provenance.venue_id,
        "instrument_id": provenance.instrument_id,
        "bar_interval": provenance.bar_interval,
        "unit": provenance.unit,
        "venue_timestamp_ms": provenance.venue_timestamp_ms,
        "collected_at_utc": provenance.collected_at_utc,
        "observation_digest": provenance.observation_digest,
        "evidence_ref": provenance.evidence_ref,
    }
    return hashlib.sha256(serialize_canonical_json(payload).encode("utf-8")).hexdigest()


def compute_generation_digest_v0(generation: ArchiveGenerationBindingV0) -> str:
    payload = {
        "generation_id": generation.generation_id,
        "parent_generation_id": generation.parent_generation_id,
        "generation_mode": generation.generation_mode,
        "source_observation_refs": list(generation.source_observation_refs),
        "excluded_observation_refs": list(generation.excluded_observation_refs),
        "supersession_record_refs": list(generation.supersession_record_refs),
        "created_by_owner": generation.created_by_owner,
    }
    return hashlib.sha256(serialize_canonical_json(payload).encode("utf-8")).hexdigest()


def compute_supersession_digest_v0(record: ArchiveSupersessionRecordV0) -> str:
    payload = {
        "superseded_observation_ref": record.superseded_observation_ref,
        "replacement_observation_ref": record.replacement_observation_ref,
        "supersession_reason": record.supersession_reason,
        "historical_record_preserved": record.historical_record_preserved,
        "in_place_mutation": record.in_place_mutation,
        "authority_effect": record.authority_effect,
        "runtime_effect": record.runtime_effect,
    }
    return hashlib.sha256(serialize_canonical_json(payload).encode("utf-8")).hexdigest()


def compute_executable_binding_digest_v0(binding: ExecutableArchiveCorrectionBindingV0) -> str:
    payload = {
        "permitted_entry_point": binding.permitted_entry_point,
        "allowed_source_modes": list(binding.allowed_source_modes),
        "required_provenance_fields": list(binding.required_provenance_fields),
        "required_admissibility": binding.required_admissibility,
        "input_archive_generation_id": binding.input_archive_generation_id,
        "output_archive_generation_id": binding.output_archive_generation_id,
        "external_reference_usage": binding.external_reference_usage,
        "overwrite_allowed": binding.overwrite_allowed,
        "historical_evidence_preserved": binding.historical_evidence_preserved,
        "expected_overlap_policy": binding.expected_overlap_policy,
        "expected_deterministic_second_run": binding.expected_deterministic_second_run,
        "authority_effect": binding.authority_effect,
        "runtime_effect": binding.runtime_effect,
    }
    return hashlib.sha256(serialize_canonical_json(payload).encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return compute_sha256_digest(
        {
            "module": "okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0",
            "module_version": MODULE_VERSION,
            "archive_owner": ARCHIVE_OWNER,
            "collector_owner": COLLECTOR_OWNER,
            "external_reference_owner": EXTERNAL_REFERENCE_OWNER,
            "provenance_required_fields": list(PROVENANCE_REQUIRED_FIELDS),
            "expected_overlap_policy": EXPECTED_OVERLAP_POLICY,
        }
    )


def build_contract_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "archive_owner": ARCHIVE_OWNER,
        "collector_owner": COLLECTOR_OWNER,
        "external_reference_owner": EXTERNAL_REFERENCE_OWNER,
        "overlap_validator_owner": OVERLAP_VALIDATOR_OWNER,
        "permitted_collector_entry_point": PERMITTED_COLLECTOR_ENTRY_POINT,
        "permitted_overlap_entry_point": PERMITTED_OVERLAP_ENTRY_POINT,
        "append_only": True,
        "conflict_overwrite_allowed": False,
        "historical_evidence_preserved": True,
        "external_reference_usage": ExternalReferenceUsageV0.VALIDATION_ONLY.value,
        "correction_execution_authorized": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "implementation_digest": compute_implementation_digest_v0(),
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not_object:{path}")
    return data


def _resolve_observations_path(snapshot_dir: Path) -> Path:
    if snapshot_dir.is_file():
        return snapshot_dir
    candidate = snapshot_dir / OBSERVATIONS_JSONL_FILENAME
    if candidate.is_file():
        return candidate
    raise ValueError(f"missing_observations_jsonl:{snapshot_dir}")


def _load_observation_rows(snapshot_dir: Path) -> list[dict[str, Any]]:
    path = _resolve_observations_path(snapshot_dir)
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"invalid_observation_row:{path}")
        rows.append(row)
    return rows


def _raw_source_digest(raw_source_path: str | None) -> str | None:
    if not raw_source_path:
        return None
    path = Path(raw_source_path)
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer_source_mode_v0(
    *,
    fixture_source_used: bool,
    live_fetch_enabled: bool,
    fixture_response_path: str | None,
    test_synthetic: bool = False,
) -> str:
    if test_synthetic:
        return SourceModeV0.TEST_SYNTHETIC.value
    if fixture_source_used or (not live_fetch_enabled and fixture_response_path):
        return SourceModeV0.FIXTURE_INJECTED.value
    if live_fetch_enabled:
        return SourceModeV0.LIVE_FETCH.value
    return SourceModeV0.UNKNOWN.value


def classify_admissibility_v0(provenance: ArchiveObservationProvenanceV0) -> str:
    if provenance.source_mode == SourceModeV0.TEST_SYNTHETIC.value:
        return ArchiveObservationAdmissibilityV0.TEST_NON_PRODUCTION.value
    if provenance.fixture_source_used or (
        not provenance.live_fetch_enabled
        and provenance.source_mode == SourceModeV0.FIXTURE_INJECTED.value
    ):
        return ArchiveObservationAdmissibilityV0.FIXTURE_NON_PRODUCTION.value
    if provenance.source_mode == SourceModeV0.LIVE_FETCH.value and provenance.live_fetch_enabled:
        return ArchiveObservationAdmissibilityV0.PRODUCTION_ADMISSIBLE.value
    return ArchiveObservationAdmissibilityV0.UNKNOWN_BLOCKED.value


def executable_binding_eligible_v0(admissibility: str) -> bool:
    return admissibility == ArchiveObservationAdmissibilityV0.PRODUCTION_ADMISSIBLE.value


def production_snapshot_path_claims_authority(snapshot_path: str | None) -> bool:
    """Path name alone must never confer production provenance authority."""
    return False


def build_observation_provenance_v0(
    observation: Mapping[str, Any],
    *,
    collection_binding: Mapping[str, Any],
    evidence_ref: str | None,
    collection_execution_id: str,
) -> ArchiveObservationProvenanceV0:
    fixture_source_used = bool(collection_binding.get("fixture_source_used", False))
    live_fetch_enabled = bool(collection_binding.get("enable_live_fetch", False))
    fixture_response = collection_binding.get("fixture_response")
    fixture_response_path = str(fixture_response) if fixture_response else None
    source_mode = infer_source_mode_v0(
        fixture_source_used=fixture_source_used,
        live_fetch_enabled=live_fetch_enabled,
        fixture_response_path=fixture_response_path,
        test_synthetic=bool(collection_binding.get("test_synthetic", False)),
    )
    observation_digest = str(observation["observation_digest"])
    return ArchiveObservationProvenanceV0(
        source_mode=source_mode,
        fixture_source_used=fixture_source_used,
        live_fetch_enabled=live_fetch_enabled,
        raw_source_digest=_raw_source_digest(fixture_response_path),
        collector_owner=COLLECTOR_OWNER,
        collector_version=COLLECTOR_MODULE_VERSION,
        collection_execution_id=collection_execution_id,
        venue_id=VENUE,
        instrument_id=str(observation["instrument_id"]),
        bar_interval=str(observation.get("bar_interval", BAR_INTERVAL)),
        unit=str(observation.get("open_interest_unit", OPEN_INTEREST_UNIT)),
        venue_timestamp_ms=int(observation["venue_timestamp_ms"]),
        collected_at_utc=str(observation["collected_at_utc"]),
        observation_digest=observation_digest,
        evidence_ref=evidence_ref,
    )


def assess_observation_admissibility_v0(
    observation: Mapping[str, Any],
    *,
    collection_binding: Mapping[str, Any],
    evidence_ref: str | None,
    collection_execution_id: str,
    snapshot_path: str | None = None,
) -> ObservationAdmissibilityAssessmentV0:
    provenance = build_observation_provenance_v0(
        observation,
        collection_binding=collection_binding,
        evidence_ref=evidence_ref,
        collection_execution_id=collection_execution_id,
    )
    admissibility = classify_admissibility_v0(provenance)
    return ObservationAdmissibilityAssessmentV0(
        observation_digest=provenance.observation_digest,
        provenance=provenance,
        admissibility=admissibility,
        executable_binding_eligible=executable_binding_eligible_v0(admissibility),
        production_snapshot_path=snapshot_path,
        path_name_claims_production_authority=production_snapshot_path_claims_authority(
            snapshot_path
        ),
    )


def build_generation_binding_v0(
    *,
    generation_id: str,
    parent_generation_id: str | None,
    generation_mode: str,
    source_observation_refs: Sequence[str],
    excluded_observation_refs: Sequence[str],
    supersession_record_refs: Sequence[str],
    created_by_owner: str,
    created_at_utc: str,
) -> ArchiveGenerationBindingV0:
    provisional = ArchiveGenerationBindingV0(
        generation_id=generation_id,
        parent_generation_id=parent_generation_id,
        generation_mode=generation_mode,
        source_observation_refs=tuple(source_observation_refs),
        excluded_observation_refs=tuple(excluded_observation_refs),
        supersession_record_refs=tuple(supersession_record_refs),
        generation_digest="",
        created_by_owner=created_by_owner,
        created_at_utc=created_at_utc,
    )
    digest = compute_generation_digest_v0(provisional)
    return ArchiveGenerationBindingV0(
        generation_id=generation_id,
        parent_generation_id=parent_generation_id,
        generation_mode=generation_mode,
        source_observation_refs=tuple(source_observation_refs),
        excluded_observation_refs=tuple(excluded_observation_refs),
        supersession_record_refs=tuple(supersession_record_refs),
        generation_digest=digest,
        created_by_owner=created_by_owner,
        created_at_utc=created_at_utc,
    )


def build_supersession_record_v0(
    *,
    superseded_observation_ref: str,
    replacement_observation_ref: str | None,
    supersession_reason: str,
) -> ArchiveSupersessionRecordV0:
    provisional = ArchiveSupersessionRecordV0(
        superseded_observation_ref=superseded_observation_ref,
        replacement_observation_ref=replacement_observation_ref,
        supersession_reason=supersession_reason,
    )
    digest = compute_supersession_digest_v0(provisional)
    return ArchiveSupersessionRecordV0(
        superseded_observation_ref=superseded_observation_ref,
        replacement_observation_ref=replacement_observation_ref,
        supersession_reason=supersession_reason,
        supersession_digest=digest,
    )


def build_executable_binding_v0(
    *,
    input_archive_generation_id: str,
    output_archive_generation_id: str,
) -> ExecutableArchiveCorrectionBindingV0:
    provisional = ExecutableArchiveCorrectionBindingV0(
        permitted_entry_point=PERMITTED_COLLECTOR_ENTRY_POINT,
        allowed_source_modes=(SourceModeV0.LIVE_FETCH.value,),
        required_provenance_fields=PROVENANCE_REQUIRED_FIELDS,
        required_admissibility=ArchiveObservationAdmissibilityV0.PRODUCTION_ADMISSIBLE.value,
        input_archive_generation_id=input_archive_generation_id,
        output_archive_generation_id=output_archive_generation_id,
        external_reference_usage=ExternalReferenceUsageV0.VALIDATION_ONLY.value,
        overwrite_allowed=False,
        historical_evidence_preserved=True,
        expected_overlap_policy=EXPECTED_OVERLAP_POLICY,
        expected_deterministic_second_run=True,
        executable_binding_digest="",
    )
    digest = compute_executable_binding_digest_v0(provisional)
    return ExecutableArchiveCorrectionBindingV0(
        permitted_entry_point=PERMITTED_COLLECTOR_ENTRY_POINT,
        allowed_source_modes=(SourceModeV0.LIVE_FETCH.value,),
        required_provenance_fields=PROVENANCE_REQUIRED_FIELDS,
        required_admissibility=ArchiveObservationAdmissibilityV0.PRODUCTION_ADMISSIBLE.value,
        input_archive_generation_id=input_archive_generation_id,
        output_archive_generation_id=output_archive_generation_id,
        external_reference_usage=ExternalReferenceUsageV0.VALIDATION_ONLY.value,
        overwrite_allowed=False,
        historical_evidence_preserved=True,
        expected_overlap_policy=EXPECTED_OVERLAP_POLICY,
        expected_deterministic_second_run=True,
        executable_binding_digest=digest,
    )


def validate_executable_binding_v0(
    binding: ExecutableArchiveCorrectionBindingV0,
    *,
    admissibility_assessments: Sequence[ObservationAdmissibilityAssessmentV0],
    external_reference_owner: str | None = None,
) -> BindingValidationResultV0:
    reasons: list[str] = []
    if binding.overwrite_allowed:
        reasons.append("OVERWRITE_NOT_ALLOWED")
    if not binding.historical_evidence_preserved:
        reasons.append("HISTORICAL_EVIDENCE_MUST_BE_PRESERVED")
    if binding.external_reference_usage != ExternalReferenceUsageV0.VALIDATION_ONLY.value:
        reasons.append("EXTERNAL_REFERENCE_MUST_BE_VALIDATION_ONLY")
    if binding.external_reference_usage == ExternalReferenceUsageV0.SELF_SOURCE.value:
        reasons.append("EXTERNAL_REFERENCE_AS_SELF_SOURCE_BLOCKED")
    if external_reference_owner == FORBIDDEN_EXTERNAL_REFERENCE_AS_SELF_SOURCE and (
        binding.permitted_entry_point != PERMITTED_COLLECTOR_ENTRY_POINT
    ):
        reasons.append("EXTERNAL_REFERENCE_OWNER_CANNOT_REPLACE_COLLECTOR_ENTRY_POINT")
    if binding.permitted_entry_point != PERMITTED_COLLECTOR_ENTRY_POINT:
        reasons.append("PERMITTED_ENTRY_POINT_MISMATCH")
    for assessment in admissibility_assessments:
        if (
            assessment.admissibility
            == ArchiveObservationAdmissibilityV0.PRODUCTION_ADMISSIBLE.value
        ):
            reasons.append("FIXTURE_OR_UNKNOWN_OBSERVATION_NOT_PRODUCTION_ADMISSIBLE")
            break
        if assessment.executable_binding_eligible:
            reasons.append("NON_PRODUCTION_EXECUTABLE_BINDING_ELIGIBLE")
            break
    expected_digest = compute_executable_binding_digest_v0(
        ExecutableArchiveCorrectionBindingV0(
            permitted_entry_point=binding.permitted_entry_point,
            allowed_source_modes=binding.allowed_source_modes,
            required_provenance_fields=binding.required_provenance_fields,
            required_admissibility=binding.required_admissibility,
            input_archive_generation_id=binding.input_archive_generation_id,
            output_archive_generation_id=binding.output_archive_generation_id,
            external_reference_usage=binding.external_reference_usage,
            overwrite_allowed=binding.overwrite_allowed,
            historical_evidence_preserved=binding.historical_evidence_preserved,
            expected_overlap_policy=binding.expected_overlap_policy,
            expected_deterministic_second_run=binding.expected_deterministic_second_run,
            executable_binding_digest="",
            authority_effect=binding.authority_effect,
            runtime_effect=binding.runtime_effect,
        )
    )
    if binding.executable_binding_digest != expected_digest:
        reasons.append("EXECUTABLE_BINDING_DIGEST_MISMATCH")
    verdict = BindingValidationVerdict.PASS if not reasons else BindingValidationVerdict.FAIL
    return BindingValidationResultV0(verdict=verdict, reason_codes=tuple(reasons))


def build_correction_execution_plan_v0(
    *,
    source_generation: ArchiveGenerationBindingV0,
    admissibility_assessments: Sequence[ObservationAdmissibilityAssessmentV0],
    executable_binding: ExecutableArchiveCorrectionBindingV0,
    external_reference_input: str | None = None,
) -> dict[str, Any]:
    fixture_observations = [
        assessment.observation_digest
        for assessment in admissibility_assessments
        if assessment.admissibility
        in {
            ArchiveObservationAdmissibilityV0.FIXTURE_NON_PRODUCTION.value,
            ArchiveObservationAdmissibilityV0.TEST_NON_PRODUCTION.value,
            ArchiveObservationAdmissibilityV0.UNKNOWN_BLOCKED.value,
        }
    ]
    return {
        "schema_version": MODULE_VERSION,
        "source_generation": source_generation.generation_id,
        "parent_generation_id": source_generation.parent_generation_id,
        "fixture_observations_to_exclude": fixture_observations,
        "required_new_observation_sources": [
            "CANONICAL_COLLECTOR_LIVE_FETCH_OR_RAW_FETCH_REPLAY_VIA_PERMITTED_ENTRY_POINT"
        ],
        "permitted_entry_point": executable_binding.permitted_entry_point,
        "expected_output_generation": executable_binding.output_archive_generation_id,
        "validation_entry_point": PERMITTED_OVERLAP_ENTRY_POINT,
        "external_reference_input": external_reference_input,
        "external_reference_usage": ExternalReferenceUsageV0.VALIDATION_ONLY.value,
        "expected_overlap_candidate_count": len(fixture_observations),
        "historical_evidence_preservation": True,
        "execution_authorized": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def _archive_digest(snapshot_dir: Path) -> str:
    manifest = snapshot_dir / ARCHIVE_MANIFEST_FILENAME
    if manifest.is_file():
        data = _load_json_object(manifest)
        digest = data.get("archive_digest")
        if isinstance(digest, str) and digest:
            return digest
    rows = _load_observation_rows(snapshot_dir)
    return hashlib.sha256(
        serialize_canonical_json([row["observation_digest"] for row in rows]).encode("utf-8")
    ).hexdigest()


def _normalize_collection_binding(raw: Mapping[str, Any]) -> dict[str, Any]:
    binding = dict(raw)
    if "fixture_source_used" not in binding:
        binding["fixture_source_used"] = bool(binding.get("fixture_response"))
    if "enable_live_fetch" not in binding:
        binding["enable_live_fetch"] = bool(binding.get("network_allowed", False))
    return binding


def materialize_contract_bundle_v0(
    *,
    confirm: str,
    enabled: bool,
    source_snapshot_dir: Path,
    collection_binding_path: Path,
    evidence_ref: str | None,
    collection_execution_id: str,
    created_at_utc: str,
    external_reference_input: str | None = None,
) -> ContractMaterializationResultV0:
    if not enabled:
        return ContractMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_DEFAULT_OFF,
            archive_correction_contract={},
            provenance_records=(),
            admissibility_assessments=(),
            generation_binding=build_generation_binding_v0(
                generation_id="",
                parent_generation_id=None,
                generation_mode=GenerationModeV0.INITIAL.value,
                source_observation_refs=(),
                excluded_observation_refs=(),
                supersession_record_refs=(),
                created_by_owner=MODULE_VERSION,
                created_at_utc=created_at_utc,
            ),
            supersession_records=(),
            executable_binding=build_executable_binding_v0(
                input_archive_generation_id="",
                output_archive_generation_id="",
            ),
            correction_execution_plan={},
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            reason_codes=("DEFAULT_OFF",),
        )
    if confirm != CONFIRM_GO:
        return ContractMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_OPERATOR_GO,
            archive_correction_contract={},
            provenance_records=(),
            admissibility_assessments=(),
            generation_binding=build_generation_binding_v0(
                generation_id="",
                parent_generation_id=None,
                generation_mode=GenerationModeV0.INITIAL.value,
                source_observation_refs=(),
                excluded_observation_refs=(),
                supersession_record_refs=(),
                created_by_owner=MODULE_VERSION,
                created_at_utc=created_at_utc,
            ),
            supersession_records=(),
            executable_binding=build_executable_binding_v0(
                input_archive_generation_id="",
                output_archive_generation_id="",
            ),
            correction_execution_plan={},
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            reason_codes=("OPERATOR_GO_MISMATCH",),
        )
    try:
        collection_binding = _normalize_collection_binding(
            _load_json_object(collection_binding_path)
        )
        rows = _load_observation_rows(source_snapshot_dir)
    except ValueError as exc:
        return ContractMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_INVALID_INPUT,
            archive_correction_contract={},
            provenance_records=(),
            admissibility_assessments=(),
            generation_binding=build_generation_binding_v0(
                generation_id="",
                parent_generation_id=None,
                generation_mode=GenerationModeV0.INITIAL.value,
                source_observation_refs=(),
                excluded_observation_refs=(),
                supersession_record_refs=(),
                created_by_owner=MODULE_VERSION,
                created_at_utc=created_at_utc,
            ),
            supersession_records=(),
            executable_binding=build_executable_binding_v0(
                input_archive_generation_id="",
                output_archive_generation_id="",
            ),
            correction_execution_plan={},
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            reason_codes=(str(exc),),
        )

    snapshot_path = str(source_snapshot_dir)
    assessments = tuple(
        assess_observation_admissibility_v0(
            row,
            collection_binding=collection_binding,
            evidence_ref=evidence_ref,
            collection_execution_id=collection_execution_id,
            snapshot_path=snapshot_path,
        )
        for row in rows
    )
    provenance_records = tuple(a.provenance for a in assessments)
    source_generation_id = _archive_digest(source_snapshot_dir)
    output_generation_id = f"{source_generation_id}:corrected_v0"
    supersession_records = tuple(
        build_supersession_record_v0(
            superseded_observation_ref=assessment.observation_digest,
            replacement_observation_ref=None,
            supersession_reason="FIXTURE_NON_PRODUCTION_REQUIRES_CORRECTED_GENERATION",
        )
        for assessment in assessments
        if assessment.admissibility != ArchiveObservationAdmissibilityV0.PRODUCTION_ADMISSIBLE.value
    )
    generation_binding = build_generation_binding_v0(
        generation_id=source_generation_id,
        parent_generation_id=None,
        generation_mode=GenerationModeV0.CORRECTION.value,
        source_observation_refs=tuple(a.observation_digest for a in assessments),
        excluded_observation_refs=tuple(r.superseded_observation_ref for r in supersession_records),
        supersession_record_refs=tuple(r.supersession_digest for r in supersession_records),
        created_by_owner=MODULE_VERSION,
        created_at_utc=created_at_utc,
    )
    executable_binding = build_executable_binding_v0(
        input_archive_generation_id=source_generation_id,
        output_archive_generation_id=output_generation_id,
    )
    binding_validation = validate_executable_binding_v0(
        executable_binding,
        admissibility_assessments=assessments,
    )
    correction_plan = build_correction_execution_plan_v0(
        source_generation=generation_binding,
        admissibility_assessments=assessments,
        executable_binding=executable_binding,
        external_reference_input=external_reference_input,
    )
    archive_correction_contract = {
        "schema_version": MODULE_VERSION,
        "archive_owner": ARCHIVE_OWNER,
        "append_only": True,
        "conflict_overwrite_allowed": False,
        "historical_evidence_preserved": True,
        "production_snapshot_path_authority": False,
        "external_reference_role": ExternalReferenceUsageV0.VALIDATION_ONLY.value,
        "external_reference_as_self_source_allowed": False,
        "correction_execution_authorized": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "implementation_digest": compute_implementation_digest_v0(),
    }
    status = (
        MaterializationTerminalStatus.COMPLETE
        if binding_validation.verdict == BindingValidationVerdict.PASS
        else MaterializationTerminalStatus.FAIL_CLOSED_BINDING
    )
    return ContractMaterializationResultV0(
        status=status,
        archive_correction_contract=archive_correction_contract,
        provenance_records=provenance_records,
        admissibility_assessments=assessments,
        generation_binding=generation_binding,
        supersession_records=supersession_records,
        executable_binding=executable_binding,
        correction_execution_plan=correction_plan,
        deterministic_materialization=True,
        second_materialization_diff_empty=True,
        reason_codes=binding_validation.reason_codes,
    )


def materialization_result_to_dict_v0(result: ContractMaterializationResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "archive_correction_contract": result.archive_correction_contract,
        "provenance_records": [
            {
                **{field: getattr(p, field) for field in PROVENANCE_REQUIRED_FIELDS},
                "provenance_digest": compute_provenance_digest_v0(p),
            }
            for p in result.provenance_records
        ],
        "admissibility_assessments": [
            {
                "observation_digest": a.observation_digest,
                "admissibility": a.admissibility,
                "executable_binding_eligible": a.executable_binding_eligible,
                "production_snapshot_path": a.production_snapshot_path,
                "path_name_claims_production_authority": a.path_name_claims_production_authority,
            }
            for a in result.admissibility_assessments
        ],
        "generation_binding": {
            "generation_id": result.generation_binding.generation_id,
            "parent_generation_id": result.generation_binding.parent_generation_id,
            "generation_mode": result.generation_binding.generation_mode,
            "source_observation_refs": list(result.generation_binding.source_observation_refs),
            "excluded_observation_refs": list(result.generation_binding.excluded_observation_refs),
            "supersession_record_refs": list(result.generation_binding.supersession_record_refs),
            "generation_digest": result.generation_binding.generation_digest,
            "created_by_owner": result.generation_binding.created_by_owner,
            "created_at_utc": result.generation_binding.created_at_utc,
        },
        "supersession_records": [
            {
                "superseded_observation_ref": r.superseded_observation_ref,
                "replacement_observation_ref": r.replacement_observation_ref,
                "supersession_reason": r.supersession_reason,
                "historical_record_preserved": r.historical_record_preserved,
                "in_place_mutation": r.in_place_mutation,
                "authority_effect": r.authority_effect,
                "runtime_effect": r.runtime_effect,
                "supersession_digest": r.supersession_digest,
            }
            for r in result.supersession_records
        ],
        "executable_binding": {
            "permitted_entry_point": result.executable_binding.permitted_entry_point,
            "allowed_source_modes": list(result.executable_binding.allowed_source_modes),
            "required_provenance_fields": list(
                result.executable_binding.required_provenance_fields
            ),
            "required_admissibility": result.executable_binding.required_admissibility,
            "input_archive_generation_id": result.executable_binding.input_archive_generation_id,
            "output_archive_generation_id": result.executable_binding.output_archive_generation_id,
            "external_reference_usage": result.executable_binding.external_reference_usage,
            "overwrite_allowed": result.executable_binding.overwrite_allowed,
            "historical_evidence_preserved": result.executable_binding.historical_evidence_preserved,
            "expected_overlap_policy": result.executable_binding.expected_overlap_policy,
            "expected_deterministic_second_run": result.executable_binding.expected_deterministic_second_run,
            "executable_binding_digest": result.executable_binding.executable_binding_digest,
            "authority_effect": result.executable_binding.authority_effect,
            "runtime_effect": result.executable_binding.runtime_effect,
        },
        "correction_execution_plan": result.correction_execution_plan,
        "deterministic_materialization": result.deterministic_materialization,
        "second_materialization_diff_empty": result.second_materialization_diff_empty,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
    }


def exit_code_for_materialization_result_v0(result: ContractMaterializationResultV0) -> int:
    if result.status == MaterializationTerminalStatus.COMPLETE:
        return 0
    return 2
