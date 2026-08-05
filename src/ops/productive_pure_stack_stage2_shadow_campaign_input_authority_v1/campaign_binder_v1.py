"""Semantic-free binder from observation packs to ShadowCampaignRequestV1."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    EmptyCapableManifestV1,
    FinalizedBarV1,
    ReproducibilityRecordV1,
    ShadowCampaignRequestV1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
    ObservationPackV1,
)


def to_finalized_bars_v1(pack: ObservationPackV1) -> tuple[FinalizedBarV1, ...]:
    """Map Surface-B produced bars onto campaign FinalizedBarV1 (no semantics added)."""
    assert_forbidden_effects_remain_false()
    out: list[FinalizedBarV1] = []
    for bar in pack.bars:
        out.append(
            FinalizedBarV1(
                instrument_id=bar.instrument_id,
                event_time_epoch_s=bar.event_time_epoch_s,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                mark_price=bar.mark_price,
                volume=bar.volume,
                finalized=bar.finalized,
                dataset_id=bar.dataset_id,
                source_id=bar.source_id,
            )
        )
    return tuple(out)


def bind_observation_pack_to_shadow_campaign_request_v1(
    *,
    pack: ObservationPackV1,
    campaign_id: str,
    origin_main_sha: str,
    repo_root: str,
    output_root: str,
    reproducibility: ReproducibilityRecordV1,
    dataset_manifest: EmptyCapableManifestV1,
    train_calibration_validation_partition_manifest: EmptyCapableManifestV1,
    walk_forward_manifest: EmptyCapableManifestV1,
    bootstrap_monte_carlo_manifest: EmptyCapableManifestV1,
    stress_pack_manifest: EmptyCapableManifestV1,
    best_bid: Optional[float] = None,
    best_ask: Optional[float] = None,
    recent_abs_log_return: Optional[float] = None,
    fee_bps: Optional[float] = None,
    slippage_bps: Optional[float] = None,
    path_above_barrier: Optional[tuple[bool, ...]] = None,
    sequence_metric_inputs: Optional[dict[str, Optional[float]]] = None,
    layer_metric_inputs: Optional[dict[str, Optional[float]]] = None,
    force_reject_reasons: tuple[str, ...] = (),
    allow_overwrite: bool = False,
) -> ShadowCampaignRequestV1:
    """Bind pack bars + digest into ShadowCampaignRequestV1 without inventing policy."""
    assert_forbidden_effects_remain_false()
    if reproducibility.dataset_id != pack.provenance.dataset_id:
        raise InputAuthorityErrorV1("REPRODUCIBILITY_DATASET_MISMATCH")
    if reproducibility.instrument_id != pack.provenance.instrument_id:
        raise InputAuthorityErrorV1("REPRODUCIBILITY_INSTRUMENT_MISMATCH")
    if reproducibility.sole_trading_authority != ("run_integrated_offline_trading_logic_replay_v1"):
        raise InputAuthorityErrorV1("SOLE_TRADING_AUTHORITY_MISMATCH")

    repro = replace(
        reproducibility,
        observation_pack_digest=pack.observation_pack_digest,
    )
    return ShadowCampaignRequestV1(
        campaign_id=campaign_id,
        origin_main_sha=origin_main_sha,
        repo_root=repo_root,
        output_root=output_root,
        reproducibility=repro,
        observation_bars=to_finalized_bars_v1(pack),
        best_bid=best_bid,
        best_ask=best_ask,
        recent_abs_log_return=recent_abs_log_return,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        path_above_barrier=path_above_barrier,
        sequence_metric_inputs=sequence_metric_inputs,
        layer_metric_inputs=layer_metric_inputs,
        dataset_manifest=dataset_manifest,
        train_calibration_validation_partition_manifest=(
            train_calibration_validation_partition_manifest
        ),
        walk_forward_manifest=walk_forward_manifest,
        bootstrap_monte_carlo_manifest=bootstrap_monte_carlo_manifest,
        stress_pack_manifest=stress_pack_manifest,
        force_reject_reasons=force_reject_reasons,
        allow_overwrite=allow_overwrite,
    )
