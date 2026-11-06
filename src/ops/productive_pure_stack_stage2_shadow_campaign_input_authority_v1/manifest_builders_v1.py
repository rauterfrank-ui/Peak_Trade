"""Structural COMPLETE dataset / partition / walk-forward / bootstrap / stress builders.

Numeric Owner magnitudes remain unset (null). No productive calibration.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    EmptyCapableManifestV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    EventTimeRangeV1,
    InputAuthorityErrorV1,
    ObservationPackV1,
    StructuralManifestSpecV1,
)


def _complete(entries: Sequence[Mapping[str, Any]], *, notes: str) -> EmptyCapableManifestV1:
    materialized = tuple(dict(e) for e in entries)
    if not materialized:
        raise InputAuthorityErrorV1("MANIFEST_ENTRIES_REQUIRED")
    digest = digest_mapping({"entries": list(materialized), "notes": notes})
    return EmptyCapableManifestV1(
        status="COMPLETE",
        populated=True,
        entries=materialized,
        digest=digest,
        notes=notes,
    )


def build_dataset_manifest_v1(pack: ObservationPackV1) -> EmptyCapableManifestV1:
    prov = pack.provenance
    entry = {
        "dataset_id": prov.dataset_id,
        "source_id": prov.source_id,
        "venue": prov.venue,
        "instrument_id": prov.instrument_id,
        "timeframe": prov.timeframe,
        "event_time_range": prov.event_time_range.to_dict(),
        "ingestion_timestamp": prov.ingestion_timestamp,
        "finalization_timestamp": prov.finalization_timestamp,
        "repository_sha": prov.repository_sha,
        "config_digest": prov.config_digest,
        "producer_version": prov.producer_version,
        "raw_source_digest": prov.raw_source_digest,
        "correction_revision_policy": prov.correction_revision_policy,
        "observation_pack_digest": pack.observation_pack_digest,
        "bar_count": len(pack.bars),
        "authority_surface": C.AUTHORITY_SURFACE,
        "immutable_snapshot": True,
        "productive_numeric_values_set": 0,
    }
    return _complete(
        (entry,),
        notes="Structural COMPLETE dataset identity; no numeric policy values",
    )


def build_partition_manifest_v1(spec: StructuralManifestSpecV1) -> EmptyCapableManifestV1:
    if set(spec.segment_boundaries_event_time_epoch_s) != set(C.PARTITION_SEGMENTS):
        raise InputAuthorityErrorV1("PARTITION_SEGMENTS_INCOMPLETE")
    # Chronological order: train < calibration < validation < holdout
    ordered = [spec.segment_boundaries_event_time_epoch_s[s] for s in C.PARTITION_SEGMENTS]
    if ordered != sorted(ordered):
        raise InputAuthorityErrorV1("PARTITION_NOT_CHRONOLOGICAL")
    for label in spec.regime_coverage:
        if label not in C.REGIME_COVERAGE_LABELS:
            raise InputAuthorityErrorV1(f"UNKNOWN_REGIME_LABEL:{label}")
    entry = {
        "split_type": "CHRONOLOGICAL_POINT_IN_TIME",
        "random_bar_splitting": False,
        "segments": list(C.PARTITION_SEGMENTS),
        "segment_boundaries_event_time_epoch_s": dict(spec.segment_boundaries_event_time_epoch_s),
        "purge_and_embargo": "MANDATORY",
        "purge_seconds": None,  # Owner numeric unset
        "embargo_seconds": None,  # Owner numeric unset
        "preserve_atr_rv_warmup_history": True,
        "regime_coverage": {k: int(v) for k, v in spec.regime_coverage.items()},
        "invent_observations": False,
        "instrument_id": spec.instrument_id,
        "dataset_id": spec.dataset_id,
        "event_time_range": spec.event_time_range.to_dict(),
        "instrument_continuity_break_policy": "NEW_DATASET",
        "productive_numeric_values_set": 0,
    }
    if spec.purge_seconds is not None or spec.embargo_seconds is not None:
        raise InputAuthorityErrorV1("PURGE_EMBARGO_NUMERIC_MAGNITUDES_UNSET_REQUIRED")
    return _complete(
        (entry,),
        notes="Structural COMPLETE partition; purge/embargo magnitudes unset",
    )


def build_walk_forward_manifest_v1(spec: StructuralManifestSpecV1) -> EmptyCapableManifestV1:
    if len(spec.fold_ids) < 1:
        raise InputAuthorityErrorV1("WALK_FORWARD_FOLD_IDS_REQUIRED")
    if len(set(spec.fold_ids)) != len(spec.fold_ids):
        raise InputAuthorityErrorV1("WALK_FORWARD_FOLD_IDS_NOT_UNIQUE")
    if spec.fold_sizes is not None:
        raise InputAuthorityErrorV1("FOLD_SIZES_MUST_REMAIN_UNSET")
    entries = []
    for fold_id in spec.fold_ids:
        fold_payload = {
            "fold_id": fold_id,
            "mode": "EXPANDING_CALIBRATION_WINDOWS",
            "locked_forward_validation": True,
            "isolated_forward_holdout": True,
            "rebalance_boundaries": "EVENT_TIME_BASED",
            "calibration_may_access_validation_or_holdout_labels": False,
            "fold_sizes": None,
            "cadence_numbers": None,
            "dataset_id": spec.dataset_id,
            "instrument_id": spec.instrument_id,
            "productive_numeric_values_set": 0,
        }
        fold_payload["fold_digest"] = digest_mapping(fold_payload)
        entries.append(fold_payload)
    return _complete(
        entries,
        notes="Structural COMPLETE walk-forward; fold sizes/cadence unset",
    )


def build_bootstrap_manifest_v1(spec: StructuralManifestSpecV1) -> EmptyCapableManifestV1:
    if not spec.bootstrap_seeds:
        raise InputAuthorityErrorV1("BOOTSTRAP_SEEDS_REQUIRED")
    if spec.bootstrap_block_length is not None:
        raise InputAuthorityErrorV1("BOOTSTRAP_BLOCK_LENGTH_MUST_REMAIN_UNSET")
    if spec.bootstrap_path_count is not None:
        raise InputAuthorityErrorV1("BOOTSTRAP_PATH_COUNT_MUST_REMAIN_UNSET")
    if spec.resampling_unit is not None:
        raise InputAuthorityErrorV1("RESAMPLING_UNIT_MUST_REMAIN_UNSET")
    entry = {
        "method": "BLOCK_BOOTSTRAP",
        "preserve_temporal_structure": True,
        "iid_resampling": "FORBIDDEN_BY_DEFAULT",
        "deterministic_recorded_seeds": [int(s) for s in spec.bootstrap_seeds],
        "block_length": None,
        "resampling_unit_choice": None,
        "path_count": None,
        "path_ensemble_ownership": "SOLE_TRADING_AUTHORITY_SHADOW_CALIBRATION",
        "parallel_survival_kernel": False,
        "dataset_id": spec.dataset_id,
        "instrument_id": spec.instrument_id,
        "productive_numeric_values_set": 0,
    }
    return _complete(
        (entry,),
        notes="Structural COMPLETE block bootstrap; numeric magnitudes unset",
    )


def build_stress_manifest_v1(
    *,
    dataset_id: str,
    instrument_id: str,
    families: Optional[Sequence[str]] = None,
) -> EmptyCapableManifestV1:
    selected = tuple(families or C.STRESS_STRUCTURAL_FAMILIES)
    if set(selected) != set(C.STRESS_STRUCTURAL_FAMILIES):
        raise InputAuthorityErrorV1("STRESS_FAMILIES_MUST_MATCH_RATIFIED_SET")
    entries = [
        {
            "family": family,
            "numeric_magnitude": None,
            "numeric_magnitudes_ratified": False,
            "dataset_id": dataset_id,
            "instrument_id": instrument_id,
            "productive_numeric_values_set": 0,
        }
        for family in C.STRESS_STRUCTURAL_FAMILIES
    ]
    return _complete(
        entries,
        notes="Structural COMPLETE stress families; numeric magnitudes unset",
    )


def build_structural_manifest_set_v1(
    *,
    pack: ObservationPackV1,
    segment_boundaries_event_time_epoch_s: Mapping[str, int],
    fold_ids: Sequence[str],
    bootstrap_seeds: Sequence[int],
    regime_coverage: Mapping[str, int],
) -> dict[str, EmptyCapableManifestV1]:
    spec = StructuralManifestSpecV1(
        dataset_id=pack.provenance.dataset_id,
        instrument_id=pack.provenance.instrument_id,
        event_time_range=EventTimeRangeV1(
            start_epoch_s=pack.provenance.event_time_range.start_epoch_s,
            end_epoch_s_exclusive=pack.provenance.event_time_range.end_epoch_s_exclusive,
        ),
        segment_boundaries_event_time_epoch_s=dict(segment_boundaries_event_time_epoch_s),
        fold_ids=tuple(fold_ids),
        bootstrap_seeds=tuple(int(s) for s in bootstrap_seeds),
        regime_coverage=dict(regime_coverage),
        stress_families=C.STRESS_STRUCTURAL_FAMILIES,
        purge_seconds=None,
        embargo_seconds=None,
        fold_sizes=None,
        bootstrap_block_length=None,
        bootstrap_path_count=None,
        resampling_unit=None,
    )
    return {
        "dataset_manifest": build_dataset_manifest_v1(pack),
        "train_calibration_validation_partition_manifest": build_partition_manifest_v1(spec),
        "walk_forward_manifest": build_walk_forward_manifest_v1(spec),
        "bootstrap_monte_carlo_manifest": build_bootstrap_manifest_v1(spec),
        "stress_pack_manifest": build_stress_manifest_v1(
            dataset_id=pack.provenance.dataset_id,
            instrument_id=pack.provenance.instrument_id,
        ),
    }
