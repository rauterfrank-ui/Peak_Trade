from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.soph_shadow_bootstrap_v1 import (
    SOPH_I17,
    SOPH_SHADOW_INITIAL_ASSIGNMENT_POLICY,
    SophShadowSlot2BootstrapV1,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1 import (
    checked_publication_v1 as publisher,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.composition_v1 import (
    Wp02ProductiveDefaultChainRequestV1,
    run_wp02_productive_default_chain_v1,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.soph_shadow_bootstrap_v1 import (
    publish_wp02_soph_shadow_bootstrap_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    persist_bound_ranking_mark_window_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1 import rest_recovery_v1
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1
from src.ops.soph_slot_assignment_v1 import SophSlotSourcesV1
from tests.ops.test_current_mf_n5_isolated_lane_instance_topology_v1 import _marks, _payload, _perp

OBSERVED = 1795414175
SHA = "a" * 40


def _case(tmp_path, monkeypatch, others=()):
    root = tmp_path / "wp02-shadow-offline"
    store = root / "public_facts"
    scope = SophShadowSlot2BootstrapV1(root, "SHADOW", SOPH_I17.lane_id, SOPH_I17.canonical_id)
    rows = [
        dict(
            instId=SOPH_I17.native_id,
            instType="FUTURES",
            state="live",
            settleCcy="USD",
            ctType="linear",
            ctVal="100",
            ctValCcy="SOPH",
            tickSz="0.0000001",
            lotSz="1",
            minSz="1",
            uly="SOPH-USD",
            expTime="1946966400000",
            instFamily="SOPH-USD_UM_XPERP",
            ruleType="xperp",
        ),
        *(_perp(native) for native in others),
    ]
    monkeypatch.setattr(rest_recovery_v1, "time", SimpleNamespace(time=lambda: OBSERVED))
    for n, row in enumerate(rows):
        native = row["instId"]
        canonical = (
            SOPH_I17.canonical_id
            if n == 0
            else f"okx_eea:linear_perpetual:{row['baseCcy']}:USDT:USDT:{native.lower()}"
        )
        ref = InstrumentRefV1(
            canonical, native, "okx_eea", row["instType"], row["settleCcy"], "b" * 64
        )
        data = []
        for minute in range(61):
            ts = (OBSERVED // 60 - 61 + minute) * 60000
            price = str(100 + (n + 1) ** 2 * (minute % 2))
            data.append([str(ts), price, price, price, price, "1"])
        window = persist_bound_ranking_mark_window_v1(
            store_root=store,
            instrument_ref=ref,
            session_id="offline",
            fetch_json=lambda path, params: {"code": "0", "data": data},
        )
        if n == 0:
            soph_window = window
    req = Wp02ProductiveDefaultChainRequestV1(
        wp02_state_root=root / "wp02_runtime",
        public_store_root=store,
        venue_native_id=SOPH_I17.native_id,
        repository_sha=SHA,
        universe_source_payload=_payload(rows),
        universe_mark_price_payload=_marks(*(r["instId"] for r in rows)),
        source_event_time=str((OBSERVED - 10) * 1000),
        topology_state_root_base=root / "topology",
        bound_mark_window=soph_window,
    )
    return req, scope


def _publish(req, scope):
    return publish_wp02_soph_shadow_bootstrap_v1(
        req, scope=scope, publication_observed_at_unix=OBSERVED + 1
    )


@pytest.mark.parametrize("others,rank", [((), 1), (("ETH-USDT-SWAP", "SOL-USDT-SWAP"), 3)])
def test_shadow_genesis_rereads_original_rank_and_replays(tmp_path, monkeypatch, others, rank):
    req, scope = _case(tmp_path, monkeypatch, others)
    pub = _publish(req, scope)
    assert pub.topology.initial_assignment_policy == SOPH_SHADOW_INITIAL_ASSIGNMENT_POLICY
    sources = SophSlotSourcesV1(
        req.topology_state_root_base,
        req.wp02_state_root / "ranking",
        req.wp02_state_root / "universe",
    )
    card = sources.inspect(SHA)
    assert card.selection.selected_rank == rank and card.lane_id == "LANE_2"
    assert card.cap24.status == "MISSING"
    by_lane = {slot.lane_id: slot.canonical_instrument_id for slot in pub.topology.occupied_slots()}
    assert by_lane.pop("LANE_2") == SOPH_I17.canonical_id
    remainder = [
        candidate.canonical_instrument_id
        for candidate in card.ranking.ranked_candidates
        if candidate.venue_native_id != SOPH_I17.native_id
    ]
    assert by_lane == dict(zip(["LANE_1", "LANE_3"], remainder))
    receipt = publisher.load_completed_selection_publication_v1(req.topology_state_root_base)
    assert _publish(req, scope).resumed
    with pytest.raises(ValueError, match="INPUT_CONFLICT"):
        _publish(replace(req, source_event_time=str(OBSERVED * 1000)), scope)
    assert (
        publisher.load_completed_selection_publication_v1(req.topology_state_root_base) == receipt
    )


def test_default_genesis_and_existing_topology_are_preserved(tmp_path, monkeypatch):
    req, scope = _case(tmp_path, monkeypatch)
    ordinary = run_wp02_productive_default_chain_v1(req)
    assert ordinary.handoff.topology.instrument_to_lane() == {SOPH_I17.canonical_id: "LANE_1"}
    with pytest.raises(ValueError, match="UNPUBLISHED_CHECKPOINT"):
        _publish(req, scope)
    assert not (req.topology_state_root_base / "LANE_2").exists()


@pytest.mark.parametrize("surface", ["LIVE", "PAPER", "TESTNET"])
def test_shadow_scope_required_before_writes(tmp_path, monkeypatch, surface):
    req, scope = _case(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="SCOPE_MISMATCH"):
        _publish(req, replace(scope, surface=surface))
    with pytest.raises(ValueError, match="REQUEST_MISMATCH"):
        _publish(replace(req, venue_native_id="SOPH-USDT-SWAP"), scope)
    assert not req.topology_state_root_base.exists()
    assert not req.wp02_state_root.exists()


def test_shadow_publication_recovers_same_genesis(tmp_path, monkeypatch):
    req, scope = _case(tmp_path, monkeypatch)

    def interrupt(**kwargs):
        raise RuntimeError("offline interruption")

    with monkeypatch.context() as patch:
        patch.setattr(publisher, "persist_durable_lane_assignment_v1", interrupt)
        with pytest.raises(RuntimeError, match="offline interruption"):
            _publish(req, scope)
    assert publisher.load_pending_selection_publication_v1(req.topology_state_root_base)
    pub = _publish(req, scope)
    assert pub.resumed and pub.selections["LANE_2"].selected_rank == 1
    assert publisher.load_pending_selection_publication_v1(req.topology_state_root_base) is None


def test_shadow_cannot_add_soph_outside_membership(tmp_path, monkeypatch):
    competitors = tuple(f"{base}-USDT-SWAP" for base in ("ETH", "SOL", "ADA", "LINK", "APT"))
    req, scope = _case(tmp_path, monkeypatch, competitors)
    with pytest.raises(ValueError, match="ELIGIBLE_MEMBER_REQUIRED"):
        _publish(req, scope)
    assert publisher.load_completed_selection_publication_v1(req.topology_state_root_base) is None
    assert not (req.topology_state_root_base / "LANE_2").exists()
