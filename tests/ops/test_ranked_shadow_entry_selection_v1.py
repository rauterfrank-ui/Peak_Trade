import json
from hashlib import sha256
from types import SimpleNamespace

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
