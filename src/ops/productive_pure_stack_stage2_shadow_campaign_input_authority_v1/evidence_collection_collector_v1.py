"""Evidence-collection collector: Surface B pack → shadow campaign runner.

Starts an isolated evidence-collection shadow campaign from a Surface-B
observation pack / ShadowCampaignRequestV1. Never flips INPUT_AUTHORITY or
RUNTIME_IMPLEMENTED, never sets productive numeric values, never touches
orders / testnet / live / credentials / dashboard writers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.campaign_runner_v1 import (
    run_shadow_campaign_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    ShadowCampaignRequestV1,
    ShadowCampaignResultV1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.authority_consumption_guards_v1 import (
    assert_surface_b_authority_consumable_v1,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
    ObservationPackV1,
)

COLLECTOR_ID = "surface_b_evidence_collection_collector.v1"


@dataclass(frozen=True)
class SurfaceBEvidenceCollectionResultV1:
    collector_id: str
    shadow_campaign_result: ShadowCampaignResultV1
    consumption_guard: Mapping[str, Any]
    authority_surface: str
    input_authority: bool
    runtime_implemented: bool
    productive_numeric_values_set: int
    shadow_campaign_startable: bool
    dashboard_authority_effect: str
    orders_testnet_live_paper_effects: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "collector_id": self.collector_id,
            "authority_surface": self.authority_surface,
            "input_authority": self.input_authority,
            "runtime_implemented": self.runtime_implemented,
            "productive_numeric_values_set": self.productive_numeric_values_set,
            "shadow_campaign_startable": self.shadow_campaign_startable,
            "dashboard_authority_effect": self.dashboard_authority_effect,
            "orders_testnet_live_paper_effects": self.orders_testnet_live_paper_effects,
            "consumption_guard": dict(self.consumption_guard),
            "campaign_id": self.shadow_campaign_result.campaign_id,
            "campaign_state": self.shadow_campaign_result.campaign_state.value,
            "pack_campaign_status": self.shadow_campaign_result.pack_campaign_status,
            "evidence_complete": self.shadow_campaign_result.evidence_complete,
            "output_dir": self.shadow_campaign_result.output_dir,
            "pack_digest": self.shadow_campaign_result.pack_digest,
            "rejection_reasons": list(self.shadow_campaign_result.rejection_reasons),
            "sole_trading_authority": self.shadow_campaign_result.sole_trading_authority,
        }


def _assert_request_bound_to_pack(
    *,
    pack: ObservationPackV1,
    request: ShadowCampaignRequestV1,
) -> None:
    repro = request.reproducibility
    if repro.observation_pack_digest != pack.observation_pack_digest:
        raise InputAuthorityErrorV1("REQUEST_OBSERVATION_PACK_DIGEST_MISMATCH")
    if repro.dataset_id != pack.provenance.dataset_id:
        raise InputAuthorityErrorV1("REQUEST_DATASET_MISMATCH")
    if repro.instrument_id != pack.provenance.instrument_id:
        raise InputAuthorityErrorV1("REQUEST_INSTRUMENT_MISMATCH")
    if repro.sole_trading_authority != C.SOLE_TRADING_AUTHORITY:
        raise InputAuthorityErrorV1("SOLE_TRADING_AUTHORITY_MISMATCH")
    if not request.observation_bars:
        raise InputAuthorityErrorV1("REQUEST_OBSERVATION_BARS_REQUIRED")
    if len(request.observation_bars) != len(pack.bars):
        raise InputAuthorityErrorV1("REQUEST_BAR_COUNT_MISMATCH")
    for req_bar, pack_bar in zip(request.observation_bars, pack.bars, strict=True):
        if not req_bar.finalized:
            raise InputAuthorityErrorV1("REQUEST_NON_FINALIZED_BAR")
        if req_bar.event_time_epoch_s != pack_bar.event_time_epoch_s:
            raise InputAuthorityErrorV1("REQUEST_BAR_EVENT_TIME_MISMATCH")
        if req_bar.source_id != C.SOURCE_ID:
            raise InputAuthorityErrorV1("REQUEST_SOURCE_ID_MISMATCH")
    for manifest in (
        request.dataset_manifest,
        request.train_calibration_validation_partition_manifest,
        request.walk_forward_manifest,
        request.bootstrap_monte_carlo_manifest,
        request.stress_pack_manifest,
    ):
        if manifest.status != "COMPLETE":
            raise InputAuthorityErrorV1(f"MANIFEST_NOT_COMPLETE:{manifest.status}")


def start_evidence_collection_shadow_campaign_from_surface_b_v1(
    *,
    pack: ObservationPackV1,
    request: ShadowCampaignRequestV1,
    productive_max_age_seconds: Optional[int] = None,
) -> SurfaceBEvidenceCollectionResultV1:
    """Validate Surface-B authority then start evidence-collection shadow campaign.

    Binding path (ratified Surface B):
      sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1
      → immutable ObservationPackV1 (PUBLIC_MARKET_FINALIZED_BARS / PT1M)
      → ShadowCampaignRequestV1
      → run_shadow_campaign_v1 (evidence only)
    """
    boundary = assert_forbidden_effects_remain_false()
    if not C.SHADOW_CAMPAIGN_STARTABLE:
        raise InputAuthorityErrorV1("SHADOW_CAMPAIGN_NOT_STARTABLE")
    if C.INPUT_AUTHORITY or C.RUNTIME_IMPLEMENTED or C.PRODUCTIVE_ACTIVATION:
        raise InputAuthorityErrorV1("FORBIDDEN_AUTHORITY_OR_RUNTIME_FLIP")
    consumption = assert_surface_b_authority_consumable_v1(
        pack=pack,
        as_of_event_time_epoch_s=int(request.reproducibility.event_time_epoch_s),
        productive_max_age_seconds=productive_max_age_seconds,
    )
    _assert_request_bound_to_pack(pack=pack, request=request)

    campaign_result = run_shadow_campaign_v1(request)
    if campaign_result.productive_numeric_values_set != 0:
        raise InputAuthorityErrorV1("CAMPAIGN_SET_PRODUCTIVE_NUMERIC_VALUES")
    if campaign_result.input_authority or campaign_result.runtime_implemented:
        raise InputAuthorityErrorV1("CAMPAIGN_FLIPPED_AUTHORITY_OR_RUNTIME")
    if campaign_result.productive_activation:
        raise InputAuthorityErrorV1("CAMPAIGN_PRODUCTIVE_ACTIVATION_TRUE")

    return SurfaceBEvidenceCollectionResultV1(
        collector_id=COLLECTOR_ID,
        shadow_campaign_result=campaign_result,
        consumption_guard={**dict(consumption), **dict(boundary)},
        authority_surface=C.AUTHORITY_SURFACE,
        input_authority=C.INPUT_AUTHORITY,
        runtime_implemented=C.RUNTIME_IMPLEMENTED,
        productive_numeric_values_set=C.PRODUCTIVE_NUMERIC_VALUES_SET,
        shadow_campaign_startable=C.SHADOW_CAMPAIGN_STARTABLE,
        dashboard_authority_effect=C.DASHBOARD_AUTHORITY_EFFECT,
        orders_testnet_live_paper_effects=False,
    )
