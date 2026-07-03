"""Synthetic test-only helpers for pit_futures_universe_manifest_v1 fixtures."""

from __future__ import annotations

from typing import Any

from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)
from src.research.pit_futures_universe_manifest_v1 import (
    MARKET_TYPE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SCORE_EPOCH_SEMANTICS,
    DataAvailabilityStatus,
    EligibilityStatus,
    MembershipStatus,
    PointInTimeFuturesUniverseEpochV1,
    PointInTimeFuturesUniverseExclusionV1,
    PointInTimeFuturesUniverseManifestV1,
    PointInTimeFuturesUniverseMemberV1,
    attach_computed_digests,
    compute_sha256_digest,
)

_SYNTHETIC_SOURCE_REF = "synthetic:test:fixture:v0"
_SYNTHETIC_DATASET_REF = "synthetic:dataset:snapshot:v0"
_SYNTHETIC_PERIOD_REF = "synthetic:period:binding:v0"
_PLACEHOLDER_DIGEST = "0" * 64


def _member(
    *,
    instrument_id: str,
    venue_id: str,
    venue_symbol: str,
    contract_type: str = "linear_perpetual",
    base_asset: str,
    quote_asset: str = "USDT",
    settlement_asset: str = "USDT",
    listing_time: str = "2024-01-01T00:00:00Z",
    delisting_time: str | None = None,
    eligible_from: str = "2024-01-01T00:00:00Z",
    eligible_until: str | None = None,
    history_bars_available: int = 30,
    required_history_bars: int = 21,
    data_availability_status: str = DataAvailabilityStatus.AVAILABLE.value,
    eligibility_status: str = EligibilityStatus.ELIGIBLE.value,
    reason_codes: tuple[str, ...] = (),
) -> PointInTimeFuturesUniverseMemberV1:
    return PointInTimeFuturesUniverseMemberV1(
        instrument_id=instrument_id,
        venue_id=venue_id,
        venue_symbol=venue_symbol,
        contract_type=contract_type,
        base_asset=base_asset,
        quote_asset=quote_asset,
        settlement_asset=settlement_asset,
        listing_time=listing_time,
        delisting_time=delisting_time,
        eligible_from=eligible_from,
        eligible_until=eligible_until,
        history_bars_available=history_bars_available,
        required_history_bars=required_history_bars,
        data_availability_status=data_availability_status,
        eligibility_status=eligibility_status,
        reason_codes=reason_codes,
        source_ref=_SYNTHETIC_SOURCE_REF,
        member_digest=_PLACEHOLDER_DIGEST,
    )


def synthetic_eligible_members() -> tuple[PointInTimeFuturesUniverseMemberV1, ...]:
    specs = [
        ("okx:linear_perpetual:ETH:USDT:USDT:perp", "okx", "ETH-USDT-SWAP", "ETH"),
        ("okx:linear_perpetual:SOL:USDT:USDT:perp", "okx", "SOL-USDT-SWAP", "SOL"),
        ("okx:linear_perpetual:AVAX:USDT:USDT:perp", "okx", "AVAX-USDT-SWAP", "AVAX"),
        ("okx:linear_perpetual:LINK:USDT:USDT:perp", "okx", "LINK-USDT-SWAP", "LINK"),
        ("okx:linear_perpetual:DOT:USDT:USDT:perp", "okx", "DOT-USDT-SWAP", "DOT"),
        ("binance_usdm:linear_perpetual:ADA:USDT:USDT:perp", "binance_usdm", "ADAUSDT", "ADA"),
    ]
    members = tuple(
        _member(
            instrument_id=instrument_id,
            venue_id=venue_id,
            venue_symbol=venue_symbol,
            base_asset=base_asset,
        )
        for instrument_id, venue_id, venue_symbol, base_asset in specs
    )
    return tuple(sorted(members, key=lambda item: item.instrument_id))


def build_synthetic_epoch(
    *,
    score_epoch: int,
    finalized_bar_close: str,
    members: tuple[PointInTimeFuturesUniverseMemberV1, ...],
    excluded_members: tuple[PointInTimeFuturesUniverseExclusionV1, ...] = (),
    minimum_required_member_count: int = 5,
    membership_status: str = MembershipStatus.FINALIZED.value,
) -> PointInTimeFuturesUniverseEpochV1:
    eligible_count = sum(
        1 for member in members if member.eligibility_status == EligibilityStatus.ELIGIBLE.value
    )
    return PointInTimeFuturesUniverseEpochV1(
        score_epoch=score_epoch,
        finalized_bar_close=finalized_bar_close,
        eligible_member_count=eligible_count,
        minimum_required_member_count=minimum_required_member_count,
        membership_status=membership_status,
        members=members,
        excluded_members=excluded_members,
        epoch_input_digest=compute_sha256_digest(
            {
                "score_epoch": score_epoch,
                "source_ref": _SYNTHETIC_SOURCE_REF,
            }
        ),
        epoch_membership_digest=_PLACEHOLDER_DIGEST,
    )


def build_synthetic_manifest(
    *,
    manifest_id: str = "synthetic_pit_manifest_v0",
    epochs: tuple[PointInTimeFuturesUniverseEpochV1, ...] | None = None,
    generated_at: str = "2026-07-03T00:00:00Z",
) -> PointInTimeFuturesUniverseManifestV1:
    if epochs is None:
        epochs = (
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=synthetic_eligible_members(),
            ),
        )
    config_payload = {
        "manifest_id": manifest_id,
        "universe_policy_id": "synthetic_cross_sectional_okx_non_btc_perp_v0",
        "universe_policy_version": "v0",
    }
    source_payload = {"source_dataset_refs": [_SYNTHETIC_DATASET_REF]}
    implementation_payload = {
        "module": "synthetic_fixture_builder_v0",
        "version": "v0",
    }
    manifest = PointInTimeFuturesUniverseManifestV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        manifest_id=manifest_id,
        hypothesis_id="CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0",
        universe_policy_id="synthetic_cross_sectional_okx_non_btc_perp_v0",
        universe_policy_version="v0",
        venue_scope=("binance_usdm", "okx"),
        market_type=MARKET_TYPE,
        generated_at=generated_at,
        score_epoch_semantics=SCORE_EPOCH_SEMANTICS,
        bar_interval="PT1H",
        minimum_history_bars=21,
        futures_only=True,
        bitcoin_direction_allowed=False,
        spot_allowed=False,
        synthetic_spot_allowed=False,
        non_authorizing=True,
        research_binding_only=True,
        instrument_id_canonicalization_version=INSTRUMENT_ID_CANONICALIZATION_VERSION,
        source_dataset_refs=(_SYNTHETIC_DATASET_REF,),
        period_binding_ref=_SYNTHETIC_PERIOD_REF,
        implementation_digest=compute_sha256_digest(implementation_payload),
        config_digest=compute_sha256_digest(config_payload),
        source_data_digest=compute_sha256_digest(source_payload),
        membership_digest=_PLACEHOLDER_DIGEST,
        manifest_digest=_PLACEHOLDER_DIGEST,
        epochs=epochs,
    )
    return attach_computed_digests(manifest)


def manifest_to_fixture_dict(manifest: PointInTimeFuturesUniverseManifestV1) -> dict[str, Any]:
    from src.research.pit_futures_universe_manifest_v1 import manifest_to_dict

    return manifest_to_dict(manifest)
