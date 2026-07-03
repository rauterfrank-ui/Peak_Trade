"""Contract tests for pit_futures_universe_manifest_validator_v1."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.research.pit_futures_universe_manifest_v1 import (
    DataAvailabilityStatus,
    MembershipStatus,
    PointInTimeFuturesUniverseMemberV1,
    attach_computed_digests,
)
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidatorErrorCode,
    validate_pit_futures_universe_manifest_v1,
)
from tests.research.fixtures.pit_futures_universe_manifest_v1.fixture_builder import (
    _member,
    build_synthetic_epoch,
    build_synthetic_manifest,
    synthetic_eligible_members,
)


def _validate(manifest):
    return validate_pit_futures_universe_manifest_v1(manifest)


def test_valid_single_epoch_accepted() -> None:
    result = _validate(build_synthetic_manifest())
    assert result.verdict.value == "ACCEPTED"
    assert result.valid is True


def test_valid_multi_epoch_accepted() -> None:
    members = synthetic_eligible_members()
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=members,
            ),
            build_synthetic_epoch(
                score_epoch=1,
                finalized_bar_close="2024-06-01T02:00:00Z",
                members=members,
            ),
        )
    )
    result = _validate(manifest)
    assert result.verdict.value == "ACCEPTED"


def test_duplicate_epoch_rejected() -> None:
    members = synthetic_eligible_members()
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=members,
            ),
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T02:00:00Z",
                members=members,
            ),
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.DUPLICATE_SCORE_EPOCH.value in result.reason_codes


def test_out_of_order_epoch_rejected() -> None:
    members = synthetic_eligible_members()
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=1,
                finalized_bar_close="2024-06-01T02:00:00Z",
                members=members,
            ),
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=members,
            ),
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.OUT_OF_ORDER_EPOCHS.value in result.reason_codes


def test_missing_epoch_in_sequence_rejected() -> None:
    members = synthetic_eligible_members()
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=members,
            ),
            build_synthetic_epoch(
                score_epoch=2,
                finalized_bar_close="2024-06-01T03:00:00Z",
                members=members,
            ),
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.MISSING_EPOCH_IN_SEQUENCE.value in result.reason_codes


def test_empty_epochs_rejected() -> None:
    manifest = build_synthetic_manifest(epochs=())
    result = _validate(manifest)
    assert ValidatorErrorCode.EMPTY_EPOCHS.value in result.reason_codes


def test_insufficient_panel_rejected() -> None:
    members = synthetic_eligible_members()[:4]
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=members,
            ),
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.INSUFFICIENT_PANEL.value in result.reason_codes


def test_insufficient_history_rejected() -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id=members[0].instrument_id,
        venue_id=members[0].venue_id,
        venue_symbol=members[0].venue_symbol,
        base_asset=members[0].base_asset,
        history_bars_available=5,
        required_history_bars=21,
    )
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=tuple(members),
            ),
        )
    )
    manifest = attach_computed_digests(manifest)
    result = _validate(manifest)
    assert ValidatorErrorCode.INSUFFICIENT_HISTORY.value in result.reason_codes


@pytest.mark.parametrize(
    "base_asset,expected",
    [
        ("BTC", ValidatorErrorCode.BITCOIN_MEMBER_REJECTED.value),
        ("XBT", ValidatorErrorCode.BITCOIN_MEMBER_REJECTED.value),
        ("WBTC", ValidatorErrorCode.BITCOIN_MEMBER_REJECTED.value),
    ],
)
def test_bitcoin_members_rejected(base_asset: str, expected: str) -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id=f"okx:linear_perpetual:{base_asset}:USDT:USDT:perp",
        venue_id="okx",
        venue_symbol=f"{base_asset}-USDT-SWAP",
        base_asset=base_asset,
    )
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=tuple(members),
                ),
            )
        )
    )
    result = _validate(manifest)
    assert expected in result.reason_codes


def test_spot_member_rejected() -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id="okx:spot:ETH:USDT:USDT:perp",
        venue_id="okx",
        venue_symbol="ETH-USDT",
        base_asset="ETH",
        contract_type="spot",
    )
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=tuple(members),
                ),
            )
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.SPOT_MEMBER_REJECTED.value in result.reason_codes


def test_synthetic_spot_member_rejected() -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id="okx:synthetic_spot:ETH:USDT:USDT:perp",
        venue_id="okx",
        venue_symbol="ETH-USDT-SYN",
        base_asset="ETH",
        contract_type="synthetic_spot",
    )
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=tuple(members),
                ),
            )
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.SPOT_MEMBER_REJECTED.value in result.reason_codes


def test_duplicate_instrument_rejected() -> None:
    members = list(synthetic_eligible_members())
    duplicate = members[0]
    members = tuple(list(members) + [duplicate])
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=members,
                ),
            )
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.DUPLICATE_INSTRUMENT_ID.value in result.reason_codes


def test_unsorted_membership_rejected() -> None:
    members = tuple(reversed(synthetic_eligible_members()))
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=members,
                ),
            )
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.UNSORTED_MEMBERSHIP.value in result.reason_codes


def test_listing_boundary_rejects_future_listing() -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id=members[0].instrument_id,
        venue_id=members[0].venue_id,
        venue_symbol=members[0].venue_symbol,
        base_asset=members[0].base_asset,
        listing_time="2024-06-02T00:00:00Z",
    )
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=tuple(members),
                ),
            )
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.LISTING_BOUNDARY_VIOLATION.value in result.reason_codes


def test_delisting_boundary_rejects_delisted_at_epoch() -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id=members[0].instrument_id,
        venue_id=members[0].venue_id,
        venue_symbol=members[0].venue_symbol,
        base_asset=members[0].base_asset,
        delisting_time="2024-06-01T01:00:00Z",
    )
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=tuple(members),
                ),
            )
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.DELISTING_BOUNDARY_VIOLATION.value in result.reason_codes


def test_delisting_after_epoch_does_not_affect_earlier_epoch() -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id=members[0].instrument_id,
        venue_id=members[0].venue_id,
        venue_symbol=members[0].venue_symbol,
        base_asset=members[0].base_asset,
        delisting_time="2024-06-01T03:00:00Z",
    )
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=tuple(members),
            ),
            build_synthetic_epoch(
                score_epoch=1,
                finalized_bar_close="2024-06-01T02:00:00Z",
                members=tuple(members),
            ),
        )
    )
    result = _validate(manifest)
    assert result.verdict.value == "ACCEPTED"


def test_unfinalized_epoch_rejected() -> None:
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=synthetic_eligible_members(),
                membership_status=MembershipStatus.UNFINALIZED.value,
            ),
        )
    )
    manifest = attach_computed_digests(manifest)
    result = _validate(manifest)
    assert ValidatorErrorCode.UNFINALIZED_EPOCH.value in result.reason_codes


def test_data_unavailable_rejected() -> None:
    members = list(synthetic_eligible_members())
    members[0] = _member(
        instrument_id=members[0].instrument_id,
        venue_id=members[0].venue_id,
        venue_symbol=members[0].venue_symbol,
        base_asset=members[0].base_asset,
        data_availability_status=DataAvailabilityStatus.UNAVAILABLE.value,
    )
    manifest = attach_computed_digests(
        build_synthetic_manifest(
            epochs=(
                build_synthetic_epoch(
                    score_epoch=0,
                    finalized_bar_close="2024-06-01T01:00:00Z",
                    members=tuple(members),
                ),
            )
        )
    )
    result = _validate(manifest)
    assert ValidatorErrorCode.MEMBER_DATA_UNAVAILABLE.value in result.reason_codes


def test_unknown_canonicalization_version_rejected() -> None:
    manifest = build_synthetic_manifest()
    manifest = replace(
        manifest,
        instrument_id_canonicalization_version="instrument_id_canonicalization.v999",
    )
    result = _validate(manifest)
    assert (
        ValidatorErrorCode.UNKNOWN_INSTRUMENT_CANONICALIZATION_VERSION.value in result.reason_codes
    )


def test_member_digest_mismatch_rejected() -> None:
    manifest = build_synthetic_manifest()
    member = manifest.epochs[0].members[0]
    bad_member = replace(member, member_digest="f" * 64)
    epoch = replace(manifest.epochs[0], members=(bad_member, *manifest.epochs[0].members[1:]))
    manifest = replace(manifest, epochs=(epoch,))
    result = _validate(manifest)
    assert ValidatorErrorCode.MEMBER_DIGEST_MISMATCH.value in result.reason_codes


def test_manifest_digest_mismatch_rejected() -> None:
    manifest = build_synthetic_manifest()
    manifest = replace(manifest, manifest_digest="e" * 64)
    result = _validate(manifest)
    assert ValidatorErrorCode.MANIFEST_DIGEST_MISMATCH.value in result.reason_codes


def test_unknown_schema_version_rejected() -> None:
    manifest = replace(build_synthetic_manifest(), schema_version="v999")
    result = _validate(manifest)
    assert ValidatorErrorCode.INVALID_SCHEMA_VERSION.value in result.reason_codes


def test_absolute_host_path_forbidden() -> None:
    manifest = replace(build_synthetic_manifest(), period_binding_ref="/tmp/period.json")
    result = _validate(manifest)
    assert ValidatorErrorCode.ABSOLUTE_HOST_PATH_FORBIDDEN.value in result.reason_codes


def test_inverse_perpetual_non_btc_accepted() -> None:
    members = list(synthetic_eligible_members())
    members.append(
        _member(
            instrument_id="okx:inverse_perpetual:ETH:USD:ETH:perp",
            venue_id="okx",
            venue_symbol="ETH-USD-SWAP",
            contract_type="inverse_perpetual",
            base_asset="ETH",
            quote_asset="USD",
            settlement_asset="ETH",
        )
    )
    members = tuple(sorted(members, key=lambda item: item.instrument_id))
    manifest = build_synthetic_manifest(
        epochs=(
            build_synthetic_epoch(
                score_epoch=0,
                finalized_bar_close="2024-06-01T01:00:00Z",
                members=members,
            ),
        )
    )
    result = _validate(manifest)
    assert result.verdict.value == "ACCEPTED"
