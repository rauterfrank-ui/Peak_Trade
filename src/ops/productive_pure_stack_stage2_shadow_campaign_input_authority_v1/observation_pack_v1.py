"""Immutable observation packs and digests for Surface-B shadow calibration."""

from __future__ import annotations

from typing import Sequence

from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    EventTimeRangeV1,
    InputAuthorityErrorV1,
    InstrumentBindingV1,
    ObservationPackProvenanceV1,
    ObservationPackV1,
    ProducedFinalizedBarV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)


def build_observation_pack_v1(
    *,
    binding: InstrumentBindingV1,
    bars: Sequence[ProducedFinalizedBarV1],
    dataset_id: str,
    repository_sha: str,
    config_digest: str,
    raw_source_digest: str,
    ingestion_timestamp: str,
    finalization_timestamp: str,
) -> ObservationPackV1:
    if not bars:
        raise InputAuthorityErrorV1("OBSERVATION_BARS_REQUIRED")
    if len({b.instrument_id for b in bars}) != 1:
        raise InputAuthorityErrorV1("MULTI_INSTRUMENT_POOLING_FORBIDDEN")
    if bars[0].instrument_id != binding.canonical_instrument_id:
        raise InputAuthorityErrorV1("INSTRUMENT_BINDING_MISMATCH")
    if any(b.dataset_id != dataset_id for b in bars):
        raise InputAuthorityErrorV1("DATASET_ID_MISMATCH")
    if any(not b.finalized for b in bars):
        raise InputAuthorityErrorV1("NON_FINALIZED_BAR_IN_PACK")
    if any(b.source_id != C.SOURCE_ID for b in bars):
        raise InputAuthorityErrorV1("SOURCE_ID_MISMATCH")
    if len(repository_sha) != 40:
        raise InputAuthorityErrorV1("REPOSITORY_SHA_INVALID")

    ordered = tuple(sorted(bars, key=lambda b: b.event_time_epoch_s))
    start = ordered[0].event_time_epoch_s
    end = ordered[-1].event_time_epoch_s + C.PT1M_SECONDS
    provenance = ObservationPackProvenanceV1(
        dataset_id=dataset_id,
        source_id=C.SOURCE_ID,
        venue=binding.venue,
        instrument_id=binding.canonical_instrument_id,
        timeframe=C.BAR_INTERVAL,
        event_time_range=EventTimeRangeV1(start_epoch_s=start, end_epoch_s_exclusive=end),
        ingestion_timestamp=ingestion_timestamp,
        finalization_timestamp=finalization_timestamp,
        repository_sha=repository_sha.lower(),
        config_digest=config_digest,
        producer_version=C.PRODUCER_VERSION,
        raw_source_digest=raw_source_digest,
        correction_revision_policy=C.CORRECTION_REVISION_POLICY,
    )
    digest = digest_mapping(
        {
            "provenance": provenance.to_dict(),
            "bars": [b.to_dict() for b in ordered],
        }
    )
    return ObservationPackV1(
        provenance=provenance,
        bars=ordered,
        observation_pack_digest=digest,
        instrument_binding=binding,
    )


def assert_pack_immutable_rebuild_requires_new_dataset(
    *,
    existing_pack: ObservationPackV1,
    candidate_pack: ObservationPackV1,
) -> None:
    """Snapshots are immutable; digest/content change requires new dataset_id."""
    if existing_pack.observation_pack_digest == candidate_pack.observation_pack_digest:
        return
    if existing_pack.provenance.dataset_id == candidate_pack.provenance.dataset_id:
        raise InputAuthorityErrorV1("REBUILD_REQUIRES_NEW_DATASET_ID_AND_DIGEST")
