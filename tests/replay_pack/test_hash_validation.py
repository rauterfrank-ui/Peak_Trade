from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.contract import HashMismatchError
from src.execution.replay_pack.validator import validate_replay_pack


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


def test_hash_validation_tamper_raises(tmp_path: Path) -> None:
    run_id = "run_hash_001"
    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(
                _mk_event(run_id, 0), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        f.write("\n")

    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    # Tamper with a content file that is covered by manifest + sums.
    cfg = bundle_root / "inputs" / "config_snapshot.json"
    with open(cfg, "w", encoding="utf-8", newline="\n") as f:
        f.write('{"tampered":true}\n')

    with pytest.raises(HashMismatchError):
        validate_replay_pack(bundle_root)
