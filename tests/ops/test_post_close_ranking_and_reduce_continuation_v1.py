"""Offline custody/rotation rules; terminal orders alone never release a slot."""

from decimal import Decimal

import pytest

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lifecycle_v1 import (
    rotation_decision_for_lane_v1,
    pin_open_positions_in_membership_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from tests.ops.test_current_mf_n5_isolated_lane_instance_topology_v1 import (
    _five_ranking,
    _cid,
    _apply,
    _membership,
)


@pytest.mark.parametrize("remaining", [Decimal("1"), Decimal("0.4")])
def test_open_or_partially_reduced_position_retains_custody_and_blocks_replacement(
    tmp_path, remaining
):
    ranking = _five_ranking()
    old, new = _cid(ranking, "SOL-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    initial = _apply(ranking, [old], tmp_path)
    proposed = _membership(ranking, [new], bootstrap=False, prior=initial.membership_instance_id)
    portfolio = PortfolioTruthSnapshotV1(
        positions=(PositionTruthV1.from_signed(instrument_id=old, signed_quantity=remaining),)
    )
    pinned = pin_open_positions_in_membership_v1(proposed, portfolio=portfolio)
    assert old in pinned.ordered_instrument_ids
    rotation = rotation_decision_for_lane_v1(
        venue_flat=False, reconciled=True, lane_health_allows_replacement=True
    )
    assert not rotation.allowed
    assert rotation.retain_custody_for_open_position


@pytest.mark.parametrize("keep", [True, False])
def test_confirmed_flat_allows_ranking_to_keep_or_replace_the_future(tmp_path, keep):
    ranking = _five_ranking()
    old, new = _cid(ranking, "SOL-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    initial = _apply(ranking, [old], tmp_path)
    rotation = rotation_decision_for_lane_v1(
        venue_flat=True, reconciled=True, lane_health_allows_replacement=True
    )
    assert rotation.allowed
    selected = old if keep else new
    after = _apply(
        ranking,
        [selected],
        tmp_path,
        prior=initial,
        open_position_custody_portfolio=PortfolioTruthSnapshotV1(),
    )
    assert after.instrument_to_lane()[selected] == initial.instrument_to_lane()[old]


def test_zero_report_without_reconciliation_does_not_allow_replacement():
    result = rotation_decision_for_lane_v1(
        venue_flat=True, reconciled=False, lane_health_allows_replacement=True
    )
    assert not result.allowed
