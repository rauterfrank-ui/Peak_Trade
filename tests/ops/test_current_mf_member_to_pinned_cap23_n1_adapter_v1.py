"""CURRENT MF-member → pinned Cap23 N=1 adapter and additive Cap23 pin tests."""

from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
    GovernedCap23PinAdapterError,
    build_governed_cap23_pin_v1,
)
from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.constants_v1 import (
    ADAPTER_MAY_WRITE_CAP23_SELECTION,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_UNIVERSE_MERGE,
    PIN_IS_SELECTION_AUTHORITY,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    EVIDENCE_FILENAME as UNI_EVIDENCE,
    SNAPSHOT_FILENAME as UNI_SNAPSHOT,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    GovernedUniverseSingleWriterV1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    EVIDENCE_FILENAME as RANK_EVIDENCE,
    SNAPSHOT_FILENAME as RANK_SNAPSHOT,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    ProductiveRankingSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    STATE_REPLACEMENT_PENDING,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)


REPO_SHA = "22e6174ce1bcfa94d1256ebfe6bce6525df23022"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"
ADAPTER_SOURCE = Path("src/ops/current_mf_member_to_pinned_cap23_n1_adapter_v1/adapter_v1.py")


def _perp(inst_id: str, *, base: str | None = None) -> dict:
    token = inst_id.split("-", 1)[0]
    cc = base or token
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": cc,
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": cc,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{cc}-USDT",
        "expTime": "",
    }


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _ranking(rows: list[dict]) -> dict:
    mark_ids = [r["instId"] for r in rows]
    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot.to_dict()
    return produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(uni),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot.to_dict()


def _row(ranking: dict, native: str) -> dict:
    return next(c for c in ranking["ranked_candidates"] if c["venue_native_id"] == native)


def test_adapter_authority_bounds() -> None:
    assert PIN_IS_SELECTION_AUTHORITY is False
    assert ADAPTER_MAY_WRITE_CAP23_SELECTION is False
    assert INSTRUMENT_ID_ALONE_SUFFICIENT is False
    assert CROSS_UNIVERSE_SELECTION is False
    assert CROSS_UNIVERSE_PIN is False
    assert CROSS_UNIVERSE_REPLACEMENT is False
    assert CROSS_UNIVERSE_FALLBACK is False
    assert CROSS_UNIVERSE_CANDIDATE_BORROWING is False
    assert CROSS_UNIVERSE_RERANKING is False
    assert MULTI_UNIVERSE_MERGE is False
    assert MF_PRODUCTIVE_JOIN is False
    assert FIVE_LANE_RUNTIME_CREATED is False
    assert HOST_JOIN is False
    assert MF_SINGLE_EGRESS_REWIRED is False
    source = ADAPTER_SOURCE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in source
    assert "def produce_single_selected_future_v1" not in source
    sig = inspect.signature(build_governed_cap23_pin_v1)
    assert "SingleSelectedFutureSelectionV1" not in str(sig.return_annotation)


def test_unpinned_cap23_default_path_unchanged() -> None:
    ranking = _ranking(
        [
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
        ]
    )
    unpinned = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    explicit_none = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=None,
        lane_state_root=None,
    )
    assert unpinned.ok is True
    assert unpinned.selection.venue_native_id == "ADA-USDT-SWAP"
    assert unpinned.selection.to_dict() == explicit_none.selection.to_dict()
    assert unpinned.selection.max_positions_effective == MAX_POSITIONS_EFFECTIVE == 1


def test_valid_pin_selects_pinned_eligible_instrument(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
        ]
    )
    eth = _row(ranking, "ETH-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=tmp_path,
    )
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=pin,
        lane_state_root=tmp_path,
    )
    assert result.ok is True
    assert result.selection.state == STATE_SELECTED_ACTIVE
    assert result.selection.venue_native_id == "ETH-USDT-SWAP"
    assert result.selection.instrument_id == eth["canonical_instrument_id"]
    assert result.selection.ranking_snapshot_id == ranking["ranking_snapshot_id"]
    assert result.selection.ranking_integrity_digest == ranking["integrity_digest"]
    assert result.selection.max_positions_effective == 1
    assert result.selection.selected_future_count == 1


def test_pin_absent_instrument_fails(tmp_path: Path) -> None:
    ranking = _ranking([_perp("ETH-USDT-SWAP"), _perp("ADA-USDT-SWAP", base="ADA")])
    with pytest.raises(GovernedCap23PinAdapterError) as exc:
        build_governed_cap23_pin_v1(
            canonical_instrument_id="missing-instrument",
            ranking_snapshot=ranking,
            lane_state_root=tmp_path,
        )
    assert (
        exc.value.failure_code
        == SelectionFailureCodeV1.GOVERNED_PIN_INSTRUMENT_NOT_IN_RANKING.value
    )


def test_pin_ineligible_candidate_fails(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    sol = _row(ranking, "SOL-USDT-SWAP")
    mutated_rows = []
    for row in ranking["ranked_candidates"]:
        item = dict(row)
        if item["venue_native_id"] == "SOL-USDT-SWAP":
            item["eligibility_status"] = "EXCLUDED"
        mutated_rows.append(item)
    mutated = dict(ranking)
    mutated["ranked_candidates"] = mutated_rows
    ineligible = ProductiveFuturesRankingSnapshotV1.from_dict(mutated).with_integrity_digest()
    with pytest.raises(GovernedCap23PinAdapterError) as exc:
        build_governed_cap23_pin_v1(
            canonical_instrument_id=sol["canonical_instrument_id"],
            ranking_snapshot=ineligible.to_dict(),
            lane_state_root=tmp_path,
        )
    assert exc.value.failure_code == SelectionFailureCodeV1.GOVERNED_PIN_CANDIDATE_INELIGIBLE.value


def test_provenance_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    eth = _row(ranking, "ETH-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=tmp_path,
    )
    bad = replace(pin, ranking_integrity_digest="0" * 64)
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=bad,
        lane_state_root=tmp_path,
    )
    assert result.selection.instrument_id == ""
    assert SelectionFailureCodeV1.GOVERNED_PIN_PROVENANCE_MISMATCH.value in result.failure_codes


def test_wrong_lane_state_root_fails_closed(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    eth = _row(ranking, "ETH-USDT-SWAP")
    lane_a = tmp_path / "a"
    lane_b = tmp_path / "b"
    lane_a.mkdir()
    lane_b.mkdir()
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=lane_a,
    )
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=pin,
        lane_state_root=lane_b,
    )
    assert (
        SelectionFailureCodeV1.GOVERNED_PIN_LANE_STATE_ROOT_MISMATCH.value in result.failure_codes
    )


def test_two_isolated_lanes_share_full_ranking_snapshot(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
        ]
    )
    eth = _row(ranking, "ETH-USDT-SWAP")
    sol = _row(ranking, "SOL-USDT-SWAP")
    lane_eth = tmp_path / "eth"
    lane_sol = tmp_path / "sol"
    pin_eth = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=lane_eth,
    )
    pin_sol = build_governed_cap23_pin_v1(
        canonical_instrument_id=sol["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=lane_sol,
    )
    out_eth = run_single_selected_future_policy_v1(
        state_root=lane_eth,
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="eth",
        governed_pin=pin_eth,
    )
    out_sol = run_single_selected_future_policy_v1(
        state_root=lane_sol,
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="sol",
        governed_pin=pin_sol,
    )
    assert out_eth["ok"] is True
    assert out_sol["ok"] is True
    assert out_eth["selection"]["venue_native_id"] == "ETH-USDT-SWAP"
    assert out_sol["selection"]["venue_native_id"] == "SOL-USDT-SWAP"
    assert out_eth["selection"]["ranking_snapshot_id"] == ranking["ranking_snapshot_id"]
    assert out_sol["selection"]["ranking_integrity_digest"] == ranking["integrity_digest"]
    assert out_eth["max_positions_effective"] == 1
    assert ranking["top20_candidate_context_limit"] == 20


def test_cross_universe_pin_and_same_instrument_other_context_fail(tmp_path: Path) -> None:
    ranking_a = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    ranking_b = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("BTC-USDT-SWAP", base="BTC"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    assert ranking_a["universe_snapshot_id"] != ranking_b["universe_snapshot_id"]
    eth_a = _row(ranking_a, "ETH-USDT-SWAP")
    eth_b = _row(ranking_b, "ETH-USDT-SWAP")
    assert eth_a["canonical_instrument_id"] == eth_b["canonical_instrument_id"]
    pin_a = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth_a["canonical_instrument_id"],
        ranking_snapshot=ranking_a,
        lane_state_root=tmp_path,
    )
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking_b,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=pin_a,
        lane_state_root=tmp_path,
    )
    codes = set(result.failure_codes)
    assert SelectionFailureCodeV1.GOVERNED_PIN_UNIVERSE_MISMATCH.value in codes or (
        SelectionFailureCodeV1.GOVERNED_PIN_PROVENANCE_MISMATCH.value in codes
    )
    assert result.selection.instrument_id == ""


def test_valid_instrument_wrong_universe_identity_fails_closed(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    eth = _row(ranking, "ETH-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=tmp_path,
    )
    bad = replace(pin, universe_snapshot_id="foreign-universe-snapshot")
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=bad,
        lane_state_root=tmp_path,
    )
    assert SelectionFailureCodeV1.GOVERNED_PIN_UNIVERSE_MISMATCH.value in result.failure_codes
    assert result.selection.instrument_id == ""


def test_cross_universe_replacement_and_fallback_rejected(tmp_path: Path) -> None:
    ranking_a = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    ranking_b = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("BTC-USDT-SWAP", base="BTC"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    eth = _row(ranking_b, "ETH-USDT-SWAP")
    with pytest.raises(GovernedCap23PinAdapterError) as replacement:
        build_governed_cap23_pin_v1(
            canonical_instrument_id=eth["canonical_instrument_id"],
            ranking_snapshot=ranking_a,
            lane_state_root=tmp_path,
            replacement_ranking_snapshot=ranking_b,
        )
    with pytest.raises(GovernedCap23PinAdapterError) as fallback:
        build_governed_cap23_pin_v1(
            canonical_instrument_id=eth["canonical_instrument_id"],
            ranking_snapshot=ranking_a,
            lane_state_root=tmp_path,
            fallback_ranking_snapshot=ranking_b,
        )
    with pytest.raises(GovernedCap23PinAdapterError) as underfill:
        build_governed_cap23_pin_v1(
            canonical_instrument_id=eth["canonical_instrument_id"],
            ranking_snapshot=ranking_a,
            lane_state_root=tmp_path,
            underfill_ranking_snapshot=ranking_b,
        )
    assert replacement.value.failure_code == (
        SelectionFailureCodeV1.GOVERNED_PIN_CROSS_UNIVERSE_FORBIDDEN.value
    )
    assert fallback.value.failure_code == replacement.value.failure_code
    assert underfill.value.failure_code == replacement.value.failure_code


def test_wrong_ranking_snapshot_id_fails(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    eth = _row(ranking, "ETH-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=tmp_path,
    )
    bad = replace(pin, ranking_snapshot_id="other-universe-ranking")
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=bad,
        lane_state_root=tmp_path,
    )
    assert SelectionFailureCodeV1.GOVERNED_PIN_PROVENANCE_MISMATCH.value in result.failure_codes


def test_pin_preserves_min_holding_and_hysteresis(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
        ]
    )
    first = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        min_holding_period_seconds=3_600.0,
    )
    assert first.selection.venue_native_id == "ADA-USDT-SWAP"
    sol = _row(ranking, "SOL-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=sol["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=tmp_path,
    )
    held = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 60.0,
        previous_selection=first.selection,
        min_holding_period_seconds=3_600.0,
        governed_pin=pin,
        lane_state_root=tmp_path,
    )
    assert held.selection.venue_native_id == "ADA-USDT-SWAP"
    assert SelectionFailureCodeV1.WITHIN_MIN_HOLDING_PERIOD.value in held.selection.reason_codes

    hyst = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 10_000.0,
        previous_selection=first.selection,
        min_holding_period_seconds=0.0,
        hysteresis_rank_improvement=20,
        governed_pin=pin,
        lane_state_root=tmp_path,
    )
    assert hyst.selection.venue_native_id == "ADA-USDT-SWAP"
    assert SelectionFailureCodeV1.HYSTERESIS_BLOCKS_CHURN.value in hyst.selection.reason_codes


def test_pin_preserves_open_position_replacement_pending(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ADA-USDT-SWAP", base="ADA"),
        ]
    )
    first = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        min_holding_period_seconds=0.0,
    )
    sol = _row(ranking, "SOL-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=sol["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=tmp_path,
    )
    pending = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 10.0,
        previous_selection=first.selection,
        open_position_instrument_id=first.selection.instrument_id,
        min_holding_period_seconds=0.0,
        governed_pin=pin,
        lane_state_root=tmp_path,
    )
    assert pending.selection.state == STATE_REPLACEMENT_PENDING
    assert pending.selection.venue_native_id == first.selection.venue_native_id
    assert pending.selection.replacement_instrument_id == sol["canonical_instrument_id"]


def test_cap24_consumes_pinned_cap23_without_cap24_change(tmp_path: Path) -> None:
    ranking_rows = [
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ETH-USDT-SWAP"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]
    uni_root = tmp_path / "universe"
    rank_root = tmp_path / "ranking"
    sel_root = tmp_path / "selection"
    recon_root = tmp_path / "recon"
    for path in (uni_root, rank_root, sel_root, recon_root):
        path.mkdir()
    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(ranking_rows),
        mark_price_payload=_marks(*[r["instId"] for r in ranking_rows]),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    uni_writer = GovernedUniverseSingleWriterV1(
        state_root=uni_root, writer_identity="test_uni", session_id="s"
    )
    uni_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_universe_bundle_atomic_v1(
        state_root=uni_root,
        writer=uni_writer,
        snapshot=uni.snapshot,
        evidence={"ok": True, "capability_id": "CAPABILITY_2_1"},
    )
    uni_writer.release()
    ranking_result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni.snapshot.to_dict(),
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(
            uni.snapshot.to_dict()
        ),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    rank_writer = ProductiveRankingSingleWriterV1(
        state_root=rank_root, writer_identity="test_rank", session_id="s"
    )
    rank_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_ranking_bundle_atomic_v1(
        state_root=rank_root,
        writer=rank_writer,
        snapshot=ranking_result.snapshot,
        evidence={"ok": True, "capability_id": "CAPABILITY_2_2"},
    )
    rank_writer.release()
    ranking = ranking_result.snapshot.to_dict()
    eth = _row(ranking, "ETH-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=sel_root,
    )
    sel = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_state_root=rank_root,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="sel",
        governed_pin=pin,
    )
    assert sel["ok"] is True
    assert sel["selection"]["venue_native_id"] == "ETH-USDT-SWAP"
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        repository_sha=REPO_SHA,
        session_id="cap24",
        now_unix=OBSERVED_UNIX,
        reconciliation_state_root=recon_root,
        observed_portfolio=PortfolioTruthSnapshotV1(
            positions=(),
            event_time_unix=OBSERVED_UNIX,
            wall_time_unix=OBSERVED_UNIX,
            source_id="analytical_execution_state",
        ),
        mark_price_by_native_id={"ETH-USDT-SWAP": "100.5"},
        expected_selection_config_digest=sel["selection"]["config_digest"],
    )
    assert gate.ok is True
    assert gate.bound is not None
    assert gate.bound.venue_native_id == "ETH-USDT-SWAP"
    assert gate.bound.selected_future_count == 1
    assert gate.bound.max_positions_effective == 1
    assert UNI_SNAPSHOT
    assert RANK_SNAPSHOT
    assert UNI_EVIDENCE
    assert RANK_EVIDENCE


def test_no_filtered_ranking_and_cap23_remains_writer(tmp_path: Path) -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    eth = _row(ranking, "ETH-USDT-SWAP")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=eth["canonical_instrument_id"],
        ranking_snapshot=ranking,
        lane_state_root=tmp_path,
    )
    assert "ranked_candidates" not in pin.to_dict()
    produced = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=pin,
        lane_state_root=tmp_path,
    )
    assert produced.selection.capability_id == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert produced.selection.schema_version == "single_selected_future_selection.v1"
    adapter_src = ADAPTER_SOURCE.read_text(encoding="utf-8")
    assert "persist_selection_bundle_atomic_v1" not in adapter_src
    assert "run_single_selected_future_policy_v1" not in adapter_src
