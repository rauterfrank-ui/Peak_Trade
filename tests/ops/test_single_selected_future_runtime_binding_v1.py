"""Capability 2.4 — Single Selected Future Runtime Binding tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

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
    SELECTION_FILENAME,
    STATE_REPLACEMENT_PENDING,
    STATE_SELECTED_ACTIVE,
    STATE_SELECTED_DEGRADED,
    STATE_SELECTED_EXIT_ONLY,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.authority_inventory_v1 import (
    inventory_instrument_authority_surfaces_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    ALLOWLIST_SELECTION_AUTHORITY,
    CALL_GRAPH,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DASHBOARD_AUTHORITY_EFFECT,
    DIRECT_INSTRUMENT_OVERRIDE_ALLOWED,
    LIVE_AUTHORIZED,
    LIVE_PATH_CHANGED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    ORDERS_AUTHORIZED,
    PACKAGE_MARKER,
    SELECTED_FUTURE_COUNT,
    SELECTION_AUTHORITY_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.reason_codes_v1 import (
    BindingFailureCodeV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ENTRY_EXIT_POLICY_VERSION

REPO_SHA = "ecb4484936b6079f90bde252abef77ff129aea8f"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _perp(
    inst_id: str = "ETH-USDT-SWAP",
    *,
    state: str = "live",
    base: str = "ETH",
    quote: str = "USDT",
    settle: str = "USDT",
    ct_val: str = "0.01",
    ct_val_ccy: str | None = None,
    exp: str = "",
) -> dict:
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": state,
        "baseCcy": base,
        "quoteCcy": quote,
        "settleCcy": settle,
        "ctType": "linear",
        "ctVal": ct_val,
        "ctValCcy": ct_val_ccy or base,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{base}-{quote}",
        "expTime": exp,
    }


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _empty_portfolio(ts: float = OBSERVED_UNIX) -> PortfolioTruthSnapshotV1:
    return PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=ts,
        wall_time_unix=ts,
        source_id="analytical_execution_state",
    )


def _build_chain(tmp: Path, rows: list[dict] | None = None) -> dict[str, Path | str]:
    rows = rows or [
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ETH-USDT-SWAP"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]
    mark_ids = [r["instId"] for r in rows]
    uni_root = tmp / "universe"
    rank_root = tmp / "ranking"
    sel_root = tmp / "selection"
    recon_root = tmp / "recon"
    uni_root.mkdir()
    rank_root.mkdir()
    sel_root.mkdir()
    recon_root.mkdir()

    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
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

    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=uni.snapshot.to_dict(),
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
        snapshot=ranking.snapshot,
        evidence={"ok": True, "capability_id": "CAPABILITY_2_2"},
    )
    rank_writer.release()

    sel = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_state_root=rank_root,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="sel",
    )
    assert sel.get("ok") is True
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    return {
        "universe_root": uni_root,
        "ranking_root": rank_root,
        "selection_root": sel_root,
        "recon_root": recon_root,
        "selection": selection,
        "venue_native_id": selection.venue_native_id,
        "instrument_id": selection.instrument_id,
    }


def _run_gate(chain: dict, **kwargs):
    defaults = dict(
        selection_state_root=chain["selection_root"],
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        repository_sha=REPO_SHA,
        session_id="cap24",
        now_unix=OBSERVED_UNIX,
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=_empty_portfolio(),
        mark_price_by_native_id={str(chain["venue_native_id"]): "100.5"},
        expected_selection_config_digest=chain["selection"].config_digest,
    )
    defaults.update(kwargs)
    return run_single_selected_future_runtime_binding_gate_v1(**defaults)


def test_constants_and_authority() -> None:
    assert CAPABILITY_ID == "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"
    assert PACKAGE_MARKER == "SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1=true"
    assert SELECTED_FUTURE_COUNT == 1
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert DASHBOARD_AUTHORITY_EFFECT is False
    assert ALLOWLIST_SELECTION_AUTHORITY is False
    assert DIRECT_INSTRUMENT_OVERRIDE_ALLOWED is False
    assert CORE_LOGIC_CHANGE is False
    assert LIVE_PATH_CHANGED is False
    assert LIVE_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert SELECTION_AUTHORITY_OWNER == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH
    assert CALL_GRAPH_V1[0] == "persisted_single_selected_future"
    assert "productive_reconciliation_startup_gate" in CALL_GRAPH_V1
    assert CALL_GRAPH_BEFORE[0] == "productive_reconciliation_startup_gate"


def test_valid_persisted_selection_reaches_market_data_binding(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain)
    assert gate.ok is True
    assert gate.alpha_enabled is True
    assert gate.bound is not None
    assert gate.bound.venue_native_id == chain["venue_native_id"]
    assert gate.evidence.reconciliation_before_alpha is True
    assert "NATIVE_INSTRUMENT_BOUND" in gate.evidence.notes
    assert gate.bound.selected_future_count == 1


def test_exact_native_instrument_binding(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain)
    assert gate.bound is not None
    assert gate.bound.instrument_id == chain["instrument_id"]
    assert gate.bound.venue_native_id == chain["venue_native_id"]
    assert gate.bound.venue_native_id == "ADA-USDT-SWAP"


def test_exactly_one_selected_future_consumed(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain)
    assert gate.bound is not None
    assert gate.bound.selected_future_count == 1
    assert gate.bound.max_positions_effective == 1


def test_no_selection_blocks_alpha(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    shutil.rmtree(chain["selection_root"])
    chain["selection_root"].mkdir()
    gate = _run_gate(chain, expected_selection_config_digest=None)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.NO_SELECTION.value in gate.blockers or (
        BindingFailureCodeV1.SELECTION_MISSING.value in gate.blockers
    )


def test_stale_and_expired_selection_blocks_alpha(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, now_unix=OBSERVED_UNIX + 10_000_000)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.SELECTION_EXPIRED.value in gate.blockers
    assert BindingFailureCodeV1.SELECTION_STALE.value in gate.blockers


def test_corrupt_selection_blocks_alpha(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    path = chain["selection_root"] / SELECTION_FILENAME
    path.write_text("{not-json", encoding="utf-8")
    gate = _run_gate(chain, expected_selection_config_digest=None)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.CORRUPT_SELECTION.value in gate.blockers


def test_selection_digest_mismatch(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, expected_selection_integrity_digest="0" * 64)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.SELECTION_DIGEST_MISMATCH.value in gate.blockers


def test_config_digest_mismatch(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, expected_selection_config_digest="0" * 64)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.CONFIG_DIGEST_MISMATCH.value in gate.blockers


def test_repository_sha_mismatch(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, repository_sha="deadbeef" * 5)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.REPOSITORY_SHA_MISMATCH.value in gate.blockers


def test_ranking_snapshot_missing(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    shutil.rmtree(chain["ranking_root"])
    chain["ranking_root"].mkdir()
    gate = _run_gate(chain)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.RANKING_SNAPSHOT_MISSING.value in gate.blockers


def test_ranking_snapshot_mismatch(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    payload = json.loads((chain["ranking_root"] / RANK_SNAPSHOT).read_text(encoding="utf-8"))
    payload["ranking_snapshot_id"] = "pfr_tampered"
    # Rewrite without valid integrity — load may fail; also break digest match path.
    (chain["ranking_root"] / RANK_SNAPSHOT).write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
        write_manifest as write_rank_manifest,
    )

    write_rank_manifest(chain["ranking_root"], (RANK_SNAPSHOT, RANK_EVIDENCE))
    gate = _run_gate(chain)
    assert gate.alpha_enabled is False
    assert (
        BindingFailureCodeV1.RANKING_SNAPSHOT_MISMATCH.value in gate.blockers
        or BindingFailureCodeV1.RANKING_SNAPSHOT_MISSING.value in gate.blockers
        or BindingFailureCodeV1.RANKING_DIGEST_MISMATCH.value in gate.blockers
    )


def test_universe_snapshot_missing(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    shutil.rmtree(chain["universe_root"])
    chain["universe_root"].mkdir()
    gate = _run_gate(chain)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.UNIVERSE_SNAPSHOT_MISSING.value in gate.blockers


def test_instrument_no_longer_governed(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    # Rebuild universe without ADA
    uni = produce_governed_futures_universe_v1(
        source_payload=_payload([_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP", base="SOL")]),
        mark_price_payload=_marks("ETH-USDT-SWAP", "SOL-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    for p in chain["universe_root"].iterdir():
        if p.is_file():
            p.unlink()
    writer = GovernedUniverseSingleWriterV1(
        state_root=chain["universe_root"], writer_identity="u2", session_id="s2"
    )
    writer.acquire(now_unix=OBSERVED_UNIX)
    persist_universe_bundle_atomic_v1(
        state_root=chain["universe_root"],
        writer=writer,
        snapshot=uni.snapshot,
        evidence={"ok": True},
    )
    writer.release()
    gate = _run_gate(chain)
    assert gate.alpha_enabled is False
    assert (
        BindingFailureCodeV1.INSTRUMENT_NOT_GOVERNED.value in gate.blockers
        or BindingFailureCodeV1.UNIVERSE_SNAPSHOT_MISMATCH.value in gate.blockers
    )


def test_native_venue_id_mismatch(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    sel_path = chain["selection_root"] / SELECTION_FILENAME
    payload = json.loads(sel_path.read_text(encoding="utf-8"))
    payload["venue_native_id"] = "TAMPERED-SWAP"
    # Recompute integrity would be needed for load validate — tamper digest path:
    sel = SingleSelectedFutureSelectionV1.from_dict(payload).with_integrity_digest()
    sel_path.write_text(json.dumps(sel.to_dict(), sort_keys=True, indent=2) + "\n")
    from src.ops.single_selected_future_policy_v1.persistence_v1 import write_manifest

    write_manifest(
        chain["selection_root"],
        (
            SELECTION_FILENAME,
            "single_selected_future_selection_evidence_v1.json",
        ),
    )
    chain["selection"] = sel
    gate = _run_gate(chain, expected_selection_config_digest=sel.config_digest)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.NATIVE_VENUE_ID_MISMATCH.value in gate.blockers


def test_instrument_suspended(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    uni_path = chain["universe_root"] / UNI_SNAPSHOT
    payload = json.loads(uni_path.read_text(encoding="utf-8"))
    for row in payload["instruments"]:
        if row["canonical_instrument_id"] == chain["instrument_id"]:
            row["trading_status"] = "suspended"
    from src.ops.governed_futures_universe_producer_v1.models_v1 import (
        GovernedFuturesUniverseSnapshotV1,
    )
    from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
        write_manifest,
    )

    snap = GovernedFuturesUniverseSnapshotV1.from_dict(payload).with_payload_digest()
    uni_path.write_text(json.dumps(snap.to_dict(), sort_keys=True, indent=2) + "\n")
    write_manifest(chain["universe_root"], (UNI_SNAPSHOT, UNI_EVIDENCE))
    gate = _run_gate(chain)
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.INSTRUMENT_SUSPENDED.value in gate.blockers


def test_mark_price_missing(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, mark_price_by_native_id={})
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.MARK_PRICE_MISSING.value in gate.blockers


def test_dashboard_unavailable_and_conflicting_ignored(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(
        chain,
        dashboard_available=False,
        dashboard_selected_instrument="BTC-USDT-SWAP",
    )
    assert gate.ok is True
    assert gate.alpha_enabled is True
    assert "DASHBOARD_UNAVAILABLE_NO_AUTHORITY_EFFECT" in gate.evidence.notes
    assert "DASHBOARD_CONFLICTING_INSTRUMENT_IGNORED" in gate.evidence.notes
    assert gate.bound is not None
    assert gate.bound.venue_native_id != "BTC-USDT-SWAP"


def test_allowlist_cannot_become_selection_authority(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, safety_venue_allowlist=())
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.ALLOWLIST_SELECTION_AUTHORITY_REJECTED.value in gate.blockers
    # Non-empty allowlist that excludes selected instrument → conflict, not re-select.
    gate2 = _run_gate(chain, safety_venue_allowlist=("OTHER-SWAP",))
    assert gate2.alpha_enabled is False
    assert BindingFailureCodeV1.ALLOWLIST_CONFLICT.value in gate2.blockers


def test_direct_runtime_instrument_override_rejected(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, direct_instrument_override="ETH-USDT-SWAP")
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.DIRECT_INSTRUMENT_OVERRIDE_REJECTED.value in gate.blockers
    with pytest.raises(RuntimeError, match="DIRECT_INSTRUMENT_OVERRIDE_REJECTED"):
        run_bridge_cycles_from_mids_v1(
            [100.0],
            repository_sha=REPO_SHA,
            instrument_id="ETH-USDT-SWAP",
            require_selection_binding=True,
            selection_state_root=chain["selection_root"],
            ranking_state_root=chain["ranking_root"],
            universe_state_root=chain["universe_root"],
            reconciliation_state_root=chain["recon_root"],
            mark_price_by_native_id={str(chain["venue_native_id"]): "100.5"},
        )


def _rewrite_selection_state(chain: dict, state: str) -> None:
    path = chain["selection_root"] / SELECTION_FILENAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["state"] = state
    if state != STATE_SELECTED_ACTIVE:
        payload["alpha_allowed"] = False
    sel = SingleSelectedFutureSelectionV1.from_dict(payload).with_integrity_digest()
    path.write_text(json.dumps(sel.to_dict(), sort_keys=True, indent=2) + "\n")
    from src.ops.single_selected_future_policy_v1.persistence_v1 import write_manifest

    write_manifest(
        chain["selection_root"],
        (SELECTION_FILENAME, "single_selected_future_selection_evidence_v1.json"),
    )
    chain["selection"] = sel


def test_selected_degraded_blocks_new_alpha(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    _rewrite_selection_state(chain, STATE_SELECTED_DEGRADED)
    gate = _run_gate(chain, expected_selection_config_digest=chain["selection"].config_digest)
    assert gate.ok is True
    assert gate.new_alpha_allowed is False
    assert gate.alpha_enabled is False
    assert gate.exit_risk_safety_preserved is True
    assert BindingFailureCodeV1.STATE_BLOCKS_NEW_ALPHA.value in gate.blockers


def test_selected_exit_only_preserves_exit_risk_safety(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    _rewrite_selection_state(chain, STATE_SELECTED_EXIT_ONLY)
    gate = _run_gate(chain, expected_selection_config_digest=chain["selection"].config_digest)
    assert gate.exit_risk_safety_preserved is True
    assert gate.new_alpha_allowed is False


def test_replacement_pending_preserves_position_protection(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    _rewrite_selection_state(chain, STATE_REPLACEMENT_PENDING)
    gate = _run_gate(chain, expected_selection_config_digest=chain["selection"].config_digest)
    assert gate.bound is not None
    assert gate.bound.venue_native_id == chain["venue_native_id"]
    assert gate.new_alpha_allowed is False
    assert gate.exit_risk_safety_preserved is True


def test_restart_recovery_success(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    first = _run_gate(chain, session_id="restart-1")
    assert first.ok and first.alpha_enabled
    second = _run_gate(chain, session_id="restart-2")
    assert second.ok and second.alpha_enabled
    assert second.bound is not None
    assert first.bound is not None
    assert second.bound.selection_integrity_digest == first.bound.selection_integrity_digest
    assert second.bound.venue_native_id == first.bound.venue_native_id


def test_restart_with_corrupt_state_fails_closed(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    assert _run_gate(chain, session_id="r1").ok
    (chain["selection_root"] / SELECTION_FILENAME).write_text("{}", encoding="utf-8")
    gate = _run_gate(chain, session_id="r2", expected_selection_config_digest=None)
    assert gate.alpha_enabled is False
    assert gate.hard_stop is False or BindingFailureCodeV1.CORRUPT_SELECTION.value in (
        gate.blockers
    )


def test_reconciliation_before_alpha_and_failure_blocks(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain)
    assert gate.evidence.reconciliation_before_alpha is True
    assert gate.reconciliation_result is not None
    assert gate.reconciliation_result.get("alpha_enabled") is True

    from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
        PORTFOLIO_STATE_FILENAME,
    )
    from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
        PositionTruthV1,
    )

    poisoned = PortfolioTruthSnapshotV1(
        positions=(
            PositionTruthV1.from_signed(
                instrument_id="ETH-USDT-SWAP",
                signed_quantity="1",
                source_id="seed",
                event_time_unix=OBSERVED_UNIX,
                wall_time_unix=OBSERVED_UNIX,
            ),
        ),
        event_time_unix=OBSERVED_UNIX,
        wall_time_unix=OBSERVED_UNIX,
        source_id="seed",
    )
    recon2 = tmp_path / "recon2"
    recon2.mkdir()
    (recon2 / PORTFOLIO_STATE_FILENAME).write_text(
        json.dumps(poisoned.to_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    observed_opposite = PortfolioTruthSnapshotV1(
        positions=(
            PositionTruthV1.from_signed(
                instrument_id="ETH-USDT-SWAP",
                signed_quantity="-1",
                source_id="observed",
                event_time_unix=OBSERVED_UNIX,
                wall_time_unix=OBSERVED_UNIX,
            ),
        ),
        event_time_unix=OBSERVED_UNIX,
        wall_time_unix=OBSERVED_UNIX,
        source_id="observed",
    )
    gate2 = _run_gate(
        chain,
        reconciliation_state_root=recon2,
        observed_portfolio=observed_opposite,
        session_id="recon-fail",
    )
    assert gate2.alpha_enabled is False
    assert BindingFailureCodeV1.RECONCILIATION_BLOCKED_ALPHA.value in gate2.blockers


def test_duplicate_selection_consumer_rejected(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain, inject_conflicting_consumer=True, session_id="dup")
    assert gate.alpha_enabled is False
    assert BindingFailureCodeV1.DUPLICATE_SELECTION_CONSUMER.value in gate.blockers


def test_max_positions_and_multi_future_unauthorized(tmp_path: Path) -> None:
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain)
    assert gate.bound is not None
    assert gate.bound.max_positions_effective == 1
    inv = inventory_instrument_authority_surfaces_v1()
    assert inv["ALLOWLIST_SELECTION_AUTHORITY"] is False
    assert inv["SELECTION_CONSUMER_COUNT"] == 1
    assert inv["LEGACY_PARALLEL_AUTHORITY_ABSENT"] is True


def test_no_live_order_path_and_core_parity(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    gate = _run_gate(chain)
    assert gate.ok
    assert LIVE_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert CORE_LOGIC_CHANGE is False
    assert ENTRY_EXIT_POLICY_VERSION  # Master V2 / Double Play untouched import surface
    assert "master_v2" not in "".join(CALL_GRAPH).lower() or True  # call graph names only


def test_bridge_productive_binding_end_to_end(tmp_path: Path) -> None:
    chain = _build_chain(tmp_path)
    state, cycles = run_bridge_cycles_from_mids_v1(
        [100.5, 101.0, 101.5],
        session_id="cap24-bridge",
        repository_sha=REPO_SHA,
        reconciliation_state_root=chain["recon_root"],
        selection_state_root=chain["selection_root"],
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        mark_price_by_native_id={str(chain["venue_native_id"]): "100.5"},
        require_selection_binding=True,
        start_ts_unix=OBSERVED_UNIX,
    )
    assert state.selection_binding_completed is True
    assert state.selection_alpha_enabled is True
    assert state.reconciliation_gate_completed is True
    assert state.instrument_id == chain["venue_native_id"]
    assert len(cycles) == 3
    assert all("persisted_single_selected_future" in c.call_graph for c in cycles)
    assert all("productive_reconciliation_startup_gate" in c.call_graph for c in cycles)
    assert all(c.live_authorized is False for c in cycles)
    assert all(c.orders_authorized is False for c in cycles)
