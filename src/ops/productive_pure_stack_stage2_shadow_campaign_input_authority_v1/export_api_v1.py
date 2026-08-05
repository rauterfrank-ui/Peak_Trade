"""Export API composing Surface-B producer → pack → manifests → campaign binder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    ReproducibilityRecordV1,
    ShadowCampaignRequestV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    compute_config_digest,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.campaign_binder_v1 import (
    bind_observation_pack_to_shadow_campaign_request_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.git_sha_loader_v1 import (
    resolve_repository_sha,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.manifest_builders_v1 import (
    build_structural_manifest_set_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InstrumentBindingV1,
    MarkPriceInputV1,
    ObservationPackV1,
    VenueNativeCandleInputV1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.observation_pack_v1 import (
    build_observation_pack_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.pt1m_finalized_ohlcv_producer_v1 import (
    compute_raw_source_digest_v1,
    produce_pt1m_finalized_ohlcv_bars_v1,
)


@dataclass(frozen=True)
class SurfaceBExportResultV1:
    observation_pack: ObservationPackV1
    shadow_campaign_request: ShadowCampaignRequestV1
    repository_sha: str
    boundary_guard: Mapping[str, object]


def export_surface_b_shadow_campaign_input_v1(
    *,
    repo_root: Path,
    campaign_id: str,
    origin_main_sha: str,
    output_root: Path,
    dataset_id: str,
    scenario_id: str,
    seed: int,
    event_time_epoch_s: int,
    binding: InstrumentBindingV1,
    candles: Sequence[VenueNativeCandleInputV1],
    marks: Sequence[MarkPriceInputV1],
    segment_boundaries_event_time_epoch_s: Mapping[str, int],
    fold_ids: Sequence[str],
    bootstrap_seeds: Sequence[int],
    regime_coverage: Mapping[str, int],
    stage1_manifest_digest: str,
    calibration_protocol_digest: str,
    wall_time_utc: Optional[str] = None,
) -> SurfaceBExportResultV1:
    """Worktree-safe export: producer → immutable pack → structural manifests → binder."""
    boundary = assert_forbidden_effects_remain_false()
    repo_root = Path(repo_root).resolve()
    repository_sha = resolve_repository_sha(repo_root)
    config_digest = compute_config_digest(
        seed=seed, scenario_id=scenario_id, campaign_id=campaign_id
    )
    bars = produce_pt1m_finalized_ohlcv_bars_v1(
        binding=binding,
        dataset_id=dataset_id,
        candles=candles,
        marks=marks,
    )
    raw_digest = compute_raw_source_digest_v1(
        binding=binding,
        dataset_id=dataset_id,
        candles=candles,
        marks=marks,
    )
    now = wall_time_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pack = build_observation_pack_v1(
        binding=binding,
        bars=bars,
        dataset_id=dataset_id,
        repository_sha=repository_sha,
        config_digest=config_digest,
        raw_source_digest=raw_digest,
        ingestion_timestamp=now,
        finalization_timestamp=now,
    )
    manifests = build_structural_manifest_set_v1(
        pack=pack,
        segment_boundaries_event_time_epoch_s=segment_boundaries_event_time_epoch_s,
        fold_ids=fold_ids,
        bootstrap_seeds=bootstrap_seeds,
        regime_coverage=regime_coverage,
    )
    repro = ReproducibilityRecordV1(
        git_sha=repository_sha,
        config_digest=config_digest,
        stage1_manifest_digest=stage1_manifest_digest,
        calibration_protocol_digest=calibration_protocol_digest,
        dataset_id=dataset_id,
        instrument_id=binding.canonical_instrument_id,
        scenario_id=scenario_id,
        seed=int(seed),
        event_time_epoch_s=int(event_time_epoch_s),
        wall_time_utc=now,
        sole_trading_authority=C.SOLE_TRADING_AUTHORITY,
        observation_pack_digest=None,
    )
    request = bind_observation_pack_to_shadow_campaign_request_v1(
        pack=pack,
        campaign_id=campaign_id,
        origin_main_sha=origin_main_sha,
        repo_root=str(repo_root),
        output_root=str(output_root),
        reproducibility=repro,
        dataset_manifest=manifests["dataset_manifest"],
        train_calibration_validation_partition_manifest=manifests[
            "train_calibration_validation_partition_manifest"
        ],
        walk_forward_manifest=manifests["walk_forward_manifest"],
        bootstrap_monte_carlo_manifest=manifests["bootstrap_monte_carlo_manifest"],
        stress_pack_manifest=manifests["stress_pack_manifest"],
    )
    return SurfaceBExportResultV1(
        observation_pack=pack,
        shadow_campaign_request=request,
        repository_sha=repository_sha,
        boundary_guard=dict(boundary),
    )
