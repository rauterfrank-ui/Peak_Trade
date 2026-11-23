import json
from hashlib import sha256
from types import SimpleNamespace
from decimal import Decimal

import pytest

from src.ops import ranked_shadow_entry_selection_v1 as selection
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    RANKED_SWAP_SCOPES,
)
from src.ops.ranked_slot_run_source_v1 import RankedRunSlotV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.single_selected_future_runtime_binding_v1.persistence_v1 import (
    persist_binding_evidence_atomic_v1,
)


@pytest.mark.parametrize("scope", RANKED_SWAP_SCOPES)
def test_ranked_shadow_uses_native_positions_and_real_cap24(tmp_path, monkeypatch, scope):
    from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
        load_and_validate_universe_snapshot_v1,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        HardenedBridgeSessionStateV2,
    )
    from tests.ops.test_single_selected_future_runtime_binding_v1 import (
        _build_chain,
        _perp,
        OBSERVED_UNIX,
        REPO_SHA,
    )

    chain = _build_chain(tmp_path, [_perp(scope.native_id, base=scope.base, ct_val="10")])
    universe = load_and_validate_universe_snapshot_v1(
        chain["universe_root"], expected_repository_sha=REPO_SHA
    ).snapshot
    assignment = RankedRunSlotV1(
        scope.lane_id,
        chain["selection"],
        universe.instruments[0],
        universe.snapshot_id,
        "test-transition",
        chain["selection_root"],
    )
    monkeypatch.setattr(selection, "read_ranked_run_slot_v1", lambda config: assignment)
    state = HardenedBridgeSessionStateV2(
        instrument_id=scope.canonical_id,
        venue_instrument_id=scope.native_id,
        session_id="shadow-test",
    )
    cfg = dict(
        session_id=state.session_id,
        lane=scope.lane_id,
        surface="SHADOW",
        native_instrument_id=scope.native_id,
        canonical_instrument_id=scope.canonical_id,
        n5_source={k: str(chain[k]) for k in ("ranking_root", "universe_root")},
    )
    path = tmp_path / "slot.json"
    path.write_text(json.dumps(cfg))
    payload = {
        "code": "0",
        "data": [
            {
                "instId": scope.native_id,
                "instType": "SWAP",
                "markPx": "2",
                "ts": str(int(OBSERVED_UNIX * 1000)),
            }
        ],
    }
    body = json.dumps(payload).encode()
    (tmp_path / "mark.json").write_bytes(body)
    mark_path = "/api/v5/public/mark-price"
    receipt_path = tmp_path / "receipts.json"
    mark_receipt = dict(
        path=mark_path,
        query={"instType": "SWAP", "instId": scope.native_id},
        sha256=sha256(body).hexdigest(),
        received_at_unix=OBSERVED_UNIX,
    )
    market = SimpleNamespace(
        receipt_path=receipt_path,
        mark=2.0,
        market_event_unix=OBSERVED_UNIX,
        mark_acquired_unix=OBSERVED_UNIX,
        canonical_id=scope.canonical_id,
        native_id=scope.native_id,
        source_observations={
            "mark": SimpleNamespace(body=body, payload=payload, path=mark_path, status=200)
        },
        source_hashes={"mark": sha256(body).hexdigest()},
    )

    def check():
        return selection.resolve_ranked_shadow_entry_selection_v1(
            path,
            session_id=state.session_id,
            assignment=assignment,
            state=state,
            market=market,
            decision_id="original-decision",
            clock=lambda: OBSERVED_UNIX,
            reconciliation_root=chain["recon_root"],
        )[0]

    receipt_path.write_text(json.dumps({"mark": {**mark_receipt, "path": "/api/v5/market/ticker"}}))
    with pytest.raises(ValueError, match="ORIGINAL_MARK"):
        check()
    assert not (tmp_path / "cap24").exists()
    receipt_path.write_text(json.dumps({"mark": mark_receipt}))
    result = check()
    assert result["blockers"] == []
    receipt = json.loads((tmp_path / "cap24" / selection.BINDING_RESULT_FILENAME).read_bytes())
    assert receipt["observed_portfolio"]["cash"] is None
    assert receipt["observed_portfolio"]["positions"] == []
    assert receipt["gate"]["bound"]["venue_native_id"] == scope.native_id
    assert cfg == json.loads(path.read_bytes())
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
        WallclockSessionRuntimeV1,
    )

    reconnect = WallclockSessionRuntimeV1(evidence_root=tmp_path / "reconnect", transport=None)
    reconnect.bridge_state = state
    reconnect._expected_repository_sha = REPO_SHA

    def reconnect_slot():
        return reconnect._run_post_reconnect_reconciliation_before_alpha_v1(
            session_id=state.session_id, now_wall=OBSERVED_UNIX, ranked_slot=assignment
        )

    assert reconnect_slot()
    for step, (side, qty, expected) in enumerate((("BUY", "20", "2"), ("SELL", "30", "-1"))):
        state.portfolio.apply_intended_action(
            instrument_id=scope.canonical_id,
            side=side,
            quantity=Decimal(qty),
            mark_price=Decimal("2"),
            intent_id=str(step),
            fill_id=str(step),
        )
        observed = selection.observe_ranked_shadow_positions_v1(
            state, assignment, session_id=state.session_id, now=OBSERVED_UNIX
        )
        assert observed.positions[0].signed_quantity == Decimal(expected)
        assert check()["blockers"] == ["SHADOW_FIRST_PURCHASE_REQUIRES_FLAT_SLOT"]
        assert not reconnect_slot()
    monkeypatch.setattr(state.portfolio, "snapshot", lambda: {"stub": True})
    with pytest.raises((ValueError, KeyError)):
        check()
    assert not reconnect_slot()


@pytest.mark.parametrize("scope", RANKED_SWAP_SCOPES)
def test_entry_selection_needs_the_original_session_gate_and_current_window(
    tmp_path, monkeypatch, scope
):
    s = SimpleNamespace(
        repository_sha="f" * 40,
        selected_rank=int(scope.lane_id[-1]),
        state="SELECTED_ACTIVE",
        instrument_id=scope.canonical_id,
        venue_native_id=scope.native_id,
        selection_id="selected",
        integrity_digest="a" * 64,
        ranking_snapshot_id="ranking",
        ranking_integrity_digest="b" * 64,
        valid_from="2026-11-23T10:00:00Z",
        valid_until="2026-11-23T11:00:00Z",
    )
    original = RankedRunSlotV1(scope.lane_id, s, None, "universe", "transition")
    monkeypatch.setattr(selection, "read_ranked_run_slot_v1", lambda config: original)
    cfg = dict(
        lane=scope.lane_id,
        session_id="shadow-test",
        canonical_instrument_id=scope.canonical_id,
        native_instrument_id=scope.native_id,
        surface="SHADOW",
    )
    path = tmp_path / "slot.json"

    def inspect():
        path.write_text(json.dumps(cfg))
        return selection.inspect_ranked_shadow_entry_selection_v1(path, now=1795429800.0)

    assert inspect()["blockers"] == ["SHADOW_ENTRY_CAP24_MISSING"]
    bound = BoundInstrumentV1(
        s.instrument_id,
        s.venue_native_id,
        s.ranking_snapshot_id,
        s.ranking_integrity_digest,
        original.universe_id,
        s.selection_id,
        s.integrity_digest,
        s.state,
    )
    flags = dict(ok=True, alpha_enabled=True, new_alpha_allowed=True, hard_stop=False)
    evidence = dict(
        **bound.to_dict(),
        **flags,
        bound=bound.to_dict(),
        owner=selection.OWNER,
        capability_id=selection.CAPABILITY_ID,
        schema_version=selection.SCHEMA_VERSION,
        repository_sha=s.repository_sha,
        failure_codes=[],
        reconciliation_before_alpha=True,
        reconciliation_alpha_enabled=True,
    )
    gate = dict(
        **flags,
        evidence=evidence,
        bound=bound.to_dict(),
        selection_state=s.state,
        blockers=[],
        reconciliation_result=dict(
            ok=True, alpha_enabled=True, hard_stop=False, blockers=[], evidence_digest="c" * 64
        ),
    )
    receipt = dict(
        gate=gate,
        session_id=cfg["session_id"],
        lane=scope.lane_id,
        n5_assignment=original.reference(),
    )
    root = tmp_path / "cap24"

    def retain():
        persist_binding_evidence_atomic_v1(evidence_root=root, evidence=evidence, result=receipt)
        cfg["shadow_cap24"] = dict(
            root=str(root),
            evidence_sha256=sha256((root / selection.EVIDENCE_FILENAME).read_bytes()).hexdigest(),
            result_digest=selection.canonical_digest_v1(receipt),
        )

    retain()
    assert inspect()["blockers"] == []
    assert selection.inspect_ranked_shadow_entry_selection_v1(path, now=1795435200.0)[
        "blockers"
    ] == ["RANKED_SLOT_CAP23_OUTSIDE_SELECTION_WINDOW"]
    receipt["session_id"] = "other"
    retain()
    assert inspect()["blockers"]
    receipt["session_id"] = cfg["session_id"]
    gate["reconciliation_result"]["alpha_enabled"] = False
    retain()
    assert inspect()["blockers"]
    with (root / selection.EVIDENCE_FILENAME).open("a") as out:
        out.write(" ")
    assert "MANIFEST_MISMATCH" in inspect()["blockers"][0]

    # A later entry window belongs to the same occupied slot, even if its rank changes.
    gate["reconciliation_result"]["alpha_enabled"] = True
    renewed_selection = SimpleNamespace(
        **{
            **vars(s),
            "selected_rank": 5,
            "selection_id": "renewed",
            "integrity_digest": "d" * 64,
            "ranking_snapshot_id": "next-ranking",
            "ranking_integrity_digest": "e" * 64,
            "valid_from": "2026-11-23T11:00:00Z",
            "valid_until": "2026-11-23T12:30:00Z",
        }
    )
    renewed = RankedRunSlotV1(scope.lane_id, renewed_selection, None, "next-universe", "transition")
    monkeypatch.setattr(selection, "read_shadow_entry_admission_v1", lambda config, slot: renewed)
    retain()
    path.write_text(json.dumps(cfg))

    def renewed_result():
        return selection.inspect_ranked_shadow_entry_selection_v1(path, now=1795435200.0)

    assert renewed_result()["blockers"] == [
        "SHADOW_ENTRY_CAP24_INVALID:SHADOW_ENTRY_CAP24_SCOPE_MISMATCH"
    ]
    receipt["entry_admission"] = renewed.reference()
    retain()
    path.write_text(json.dumps(cfg))
    assert renewed_result()["blockers"] == [
        "SHADOW_ENTRY_CAP24_INVALID:RANKED_SLOT_CAP24_ORIGINAL_REQUIRED"
    ]
    bound = BoundInstrumentV1(
        s.instrument_id,
        s.venue_native_id,
        renewed_selection.ranking_snapshot_id,
        renewed_selection.ranking_integrity_digest,
        renewed.universe_id,
        renewed_selection.selection_id,
        renewed_selection.integrity_digest,
        renewed_selection.state,
    )
    evidence.update(**bound.to_dict(), bound=bound.to_dict())
    gate["bound"] = bound.to_dict()
    retain()
    path.write_text(json.dumps(cfg))
    checked = renewed_result()
    assert checked["blockers"] == []
    assert checked["n5_assignment"] == original.reference()
    assert checked["entry_admission"] == renewed.reference()
