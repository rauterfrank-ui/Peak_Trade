from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.canonical import dumps_canonical


def _mk_beta_event(
    *,
    run_id: str,
    session_id: str,
    intent_id: str,
    symbol: str,
    event_type: str,
    ts_sim: int,
    payload: Dict[str, Any] | None = None,
    client_order_id: str | None = None,
    request_id: str | None = None,
) -> Dict[str, Any]:
    payload = payload or {}
    canonical_fields = {
        "run_id": run_id,
        "session_id": session_id,
        "intent_id": intent_id,
        "symbol": symbol,
        "event_type": event_type,
        "ts_sim": ts_sim,
        "request_id": request_id,
        "client_order_id": client_order_id,
        "reason_code": None,
        "payload": payload,
    }
    event_id = stable_id(kind="execution_event", fields=canonical_fields)
    return {
        "schema_version": "BETA_EXEC_V1",
        "event_id": event_id,
        "run_id": run_id,
        "session_id": session_id,
        "intent_id": intent_id,
        "symbol": symbol,
        "event_type": event_type,
        "ts_sim": ts_sim,
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": request_id,
        "client_order_id": client_order_id,
        "reason_code": None,
        "reason_detail": None,
        "payload": payload,
    }


def test_manifest_contract_v1_required_keys_and_canonical_json(tmp_path: Path) -> None:
    run_id = "run_replay_pack_001"
    sess = "sess_001"
    intent = "intent_001"
    sym = "BTC/EUR"

    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    events = [
        _mk_beta_event(
            run_id=run_id,
            session_id=sess,
            intent_id=intent,
            symbol=sym,
            event_type="INTENT",
            ts_sim=0,
        ),
        _mk_beta_event(
            run_id=run_id,
            session_id=sess,
            intent_id=intent,
            symbol=sym,
            event_type="FILL",
            ts_sim=1,
            client_order_id="order_001",
            payload={
                "fill_id": "fill_001",
                "side": "BUY",
                "quantity": "0.01000000",
                "price": "50000.00000000",
                "fee": "0.50000000",
                "fee_currency": "EUR",
            },
        ),
    ]

    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        for e in events:
            f.write(json.dumps(e, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            f.write("\n")

    out_dir = tmp_path / "out"
    bundle_root = build_replay_pack(
        run_dir,
        out_dir,
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    manifest_path = bundle_root / "manifest.json"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    # Required keys exist.
    for k in (
        "contract_version",
        "bundle_id",
        "run_id",
        "created_at_utc",
        "peak_trade_git_sha",
        "producer",
        "contents",
        "canonicalization",
        "invariants",
    ):
        assert k in manifest

    # Canonical JSON file (exact bytes, including trailing newline).
    assert manifest_text == dumps_canonical(manifest) + "\n"

    # Deterministic ordering of contents list (sorted by path).
    content_paths = [c["path"] for c in manifest["contents"]]
    assert content_paths == sorted(content_paths)
