from __future__ import annotations

import json
from pathlib import Path

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
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


def test_golden_manifest_and_sha256sums_v1(tmp_path: Path, monkeypatch) -> None:
    import src.execution.replay_pack.builder as builder_mod

    monkeypatch.setattr(builder_mod, "_git_info", lambda _p: {"commit_sha": "TEST", "dirty": False})
    monkeypatch.setattr(
        builder_mod,
        "_env_info",
        lambda: {
            "python_version": "0.0.0",
            "python_implementation": "TEST",
            "platform": "test",
            "platform_release": "0",
        },
    )

    run_id = "run_golden_001"
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

    validate_replay_pack(bundle_root)

    manifest_text = (bundle_root / "manifest.json").read_text(encoding="utf-8")
    sums_text = (bundle_root / "hashes" / "sha256sums.txt").read_text(encoding="utf-8")

    golden_manifest = Path("tests/golden/replay_pack_manifest_v1.json").read_text(encoding="utf-8")
    golden_sums = Path("tests/golden/replay_pack_sha256sums_v1.txt").read_text(encoding="utf-8")

    assert manifest_text == golden_manifest
    assert sums_text == golden_sums
