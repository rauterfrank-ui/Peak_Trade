from __future__ import annotations

import json
from pathlib import Path

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack

# Unit-ish: import the pure(ish) inspect helper from the CLI script (no subprocess).
from scripts.execution.pt_replay_pack import inspect_bundle, inspect_bundle_json


def _mk_event(run_id: str, ts_sim: int) -> dict:
    fields = {
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "BTC/EUR",
        "event_type": "FILL",
        "ts_sim": ts_sim,
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "payload": {
            "fill_id": f"fill_{ts_sim}",
            "side": "BUY",
            "quantity": "0.01000000",
            "price": "50000.00000000",
            "fee": "0.50000000",
            "fee_currency": "EUR",
        },
    }
    event_id = stable_id(kind="execution_event", fields=fields)
    return {
        "schema_version": "BETA_EXEC_V1",
        "event_id": event_id,
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "BTC/EUR",
        "event_type": "FILL",
        "ts_sim": ts_sim,
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "reason_detail": None,
        "payload": fields["payload"],
    }


def _write_events(path: Path, run_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(
                _mk_event(run_id, 0), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        f.write("\n")


def test_inspect_bundle_is_stable_for_v1_and_v2(tmp_path: Path) -> None:
    events = tmp_path / "execution_events.jsonl"
    run_id = "run_inspect_stable_001"
    _write_events(events, run_id)

    # Build v1
    b1 = build_replay_pack(
        str(events),
        tmp_path / "out_v1",
        bundle_version="1",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )
    # Build v2
    b2 = build_replay_pack(
        str(events),
        tmp_path / "out_v2",
        bundle_version="2",
        include_fifo=True,
        include_fifo_entries=True,
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    # Determinism: calling inspect twice yields identical dict (deep).
    v1_a = inspect_bundle(b1)
    v1_b = inspect_bundle(b1)
    assert v1_a == v1_b

    v2_a = inspect_bundle(b2)
    v2_b = inspect_bundle(b2)
    assert v2_a == v2_b

    # Determinism (JSON contract): stable schema and stable values.
    j1_a = inspect_bundle_json(b1)
    j1_b = inspect_bundle_json(b1)
    assert j1_a == j1_b
    j2_a = inspect_bundle_json(b2)
    j2_b = inspect_bundle_json(b2)
    assert j2_a == j2_b

    # Presence matrix must include the required keys with stable relpaths.
    for doc in (v1_a, v2_a):
        assert "presence" in doc and isinstance(doc["presence"], dict)
        for k in (
            "events/execution_events.jsonl",
            "hashes/sha256sums.txt",
            "manifest.json",
            "ledger/ledger_fifo_snapshot.json",
            "ledger/ledger_fifo_entries.jsonl",
        ):
            assert k in doc["presence"]
            assert isinstance(doc["presence"][k], bool)

        # Structured fields exist with stable keys.
        assert isinstance(doc.get("counts"), dict)
        assert set(doc["counts"].keys()) == {"events_lines", "fifo_entries_lines", "file_count"}
        assert isinstance(doc.get("sha256"), dict)
        assert set(doc["sha256"].keys()) == {"manifest", "sha256sums"}
        assert isinstance(doc.get("fifo_snapshot"), dict)
        assert set(doc["fifo_snapshot"].keys()) == {"seq_last", "ts_utc_last"}

    # v1 expectations
    assert v1_a["contract_version"] == "1"
    assert v1_a["has_fifo_ledger"] is False
    assert v1_a["presence"]["ledger/ledger_fifo_snapshot.json"] is False
    assert v1_a["presence"]["ledger/ledger_fifo_entries.jsonl"] is False
    assert isinstance(v1_a["counts"]["events_lines"], int) and v1_a["counts"]["events_lines"] >= 1
    assert v1_a["counts"]["fifo_entries_lines"] is None
    assert v1_a["fifo_snapshot"]["ts_utc_last"] is None
    assert v1_a["fifo_snapshot"]["seq_last"] is None

    # v2 expectations
    assert v2_a["contract_version"] == "2"
    assert v2_a["has_fifo_ledger"] is True
    assert v2_a["presence"]["ledger/ledger_fifo_snapshot.json"] is True
    assert v2_a["presence"]["ledger/ledger_fifo_entries.jsonl"] is True
    assert isinstance(v2_a["counts"]["events_lines"], int) and v2_a["counts"]["events_lines"] >= 1
    assert (
        isinstance(v2_a["counts"]["fifo_entries_lines"], int)
        and v2_a["counts"]["fifo_entries_lines"] >= 1
    )
    assert isinstance(v2_a["fifo_snapshot"]["ts_utc_last"], str)
    assert isinstance(v2_a["fifo_snapshot"]["seq_last"], int)

    # JSON schema expectations (compact contract)
    for doc in (j1_a, j2_a):
        assert set(doc.keys()) == {
            "bundle",
            "contract_version",
            "files",
            "hashes",
            "events",
            "fifo",
        }
        assert isinstance(doc["bundle"], str) and doc["bundle"]
        assert doc["contract_version"] in {"1", "2"}
        assert set(doc["files"].keys()) == {
            "execution_events_jsonl",
            "ledger_fifo_entries_jsonl",
            "ledger_fifo_snapshot_json",
            "manifest_json",
            "sha256sums_txt",
        }
        assert set(doc["hashes"].keys()) == {"sha256sums_count", "manifest_sha256"}
        assert set(doc["events"].keys()) == {"lines"}
        assert set(doc["fifo"].keys()) == {
            "has_fifo_ledger",
            "fifo_engine",
            "last_ts_utc",
            "last_seq",
            "entries_lines",
        }

    assert j1_a["contract_version"] == "1"
    assert j1_a["fifo"]["has_fifo_ledger"] is False
    assert j1_a["files"]["ledger_fifo_snapshot_json"] is False
    assert j1_a["files"]["ledger_fifo_entries_jsonl"] is False
    assert isinstance(j1_a["events"]["lines"], int) and j1_a["events"]["lines"] >= 1
    assert j1_a["fifo"]["entries_lines"] is None

    assert j2_a["contract_version"] == "2"
    assert j2_a["fifo"]["has_fifo_ledger"] is True
    assert j2_a["files"]["ledger_fifo_snapshot_json"] is True
    assert j2_a["files"]["ledger_fifo_entries_jsonl"] is True
    assert isinstance(j2_a["events"]["lines"], int) and j2_a["events"]["lines"] >= 1
    assert isinstance(j2_a["fifo"]["entries_lines"], int) and j2_a["fifo"]["entries_lines"] >= 1
