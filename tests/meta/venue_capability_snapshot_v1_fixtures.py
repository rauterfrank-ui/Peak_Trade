"""Fixtures for venue_capability_snapshot_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.venue_capability_snapshot_v1 import (
    VenueCapabilityInput,
    compute_source_digest,
    default_venue_capability_input,
    produce_venue_capability_snapshot_v1,
    venue_capability_input_to_dict,
)


@dataclass(frozen=True)
class VenueCapabilitySnapshotFixtureBundle:
    input_data: VenueCapabilityInput
    snapshot_bundle_dir: Path | None = None


def build_valid_venue_capability_input(**overrides: object) -> VenueCapabilityInput:
    base = venue_capability_input_to_dict(default_venue_capability_input())
    base.update(overrides)
    if "source_digest" not in overrides:
        base["source_digest"] = compute_source_digest(base)
    payload = {
        "contract_name": base["contract_name"],
        "contract_version": base["contract_version"],
        "snapshot_id": base["snapshot_id"],
        "venue": base["venue"],
        "account_scope": base["account_scope"],
        "instrument": base["instrument"],
        "market_type": base["market_type"],
        "contract_type": base["contract_type"],
        "contract_multiplier": base["contract_multiplier"],
        "tick_size": base["tick_size"],
        "lot_size": base["lot_size"],
        "minimum_notional": base["minimum_notional"],
        "maximum_order_size": base["maximum_order_size"],
        "position_mode": base["position_mode"],
        "margin_mode": base["margin_mode"],
        "leverage_cap": base["leverage_cap"],
        "supported_order_types": base["supported_order_types"],
        "supported_time_in_force": base["supported_time_in_force"],
        "reduce_only_semantics": base["reduce_only_semantics"],
        "source_ref": base["source_ref"],
        "source_digest": base["source_digest"],
        "source_timestamp": base["source_timestamp"],
        "builder_version": base["builder_version"],
    }
    from src.meta.learning_loop.venue_capability_snapshot_v1 import parse_venue_capability_input

    return parse_venue_capability_input(payload)


def produce_venue_capability_snapshot_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    produce_output: bool = True,
    snapshot_name: str = "venue_capability_snapshot",
    **input_overrides: object,
) -> VenueCapabilitySnapshotFixtureBundle:
    input_data = build_valid_venue_capability_input(**input_overrides)
    snapshot_dir: Path | None = None
    if produce_output:
        snapshot_dir = durable_root / snapshot_name
        produce_venue_capability_snapshot_v1(
            input_data=input_data,
            output_dir=snapshot_dir,
        )
    return VenueCapabilitySnapshotFixtureBundle(
        input_data=input_data,
        snapshot_bundle_dir=snapshot_dir,
    )
