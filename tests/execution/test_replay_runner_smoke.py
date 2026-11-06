from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from src.execution.determinism import stable_id


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
) -> Dict[str, Any]:
    payload = payload or {}
    canonical_fields = {
        "run_id": run_id,
        "session_id": session_id,
        "intent_id": intent_id,
        "symbol": symbol,
        "event_type": event_type,
        "ts_sim": ts_sim,
        "request_id": None,
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
        "request_id": None,
        "client_order_id": client_order_id,
        "reason_code": None,
        "reason_detail": None,
        "payload": payload,
    }


def test_replay_runner_cli_smoke(tmp_path: Path) -> None:
    run_id = "run_replay_smoke_001"
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

    script = Path("scripts") / "execution" / "pt_replay_pack.py"
    out_dir = tmp_path / "out"

    build = subprocess.run(
        [
            sys.executable,
            str(script),
            "build",
            "--run-id-or-dir",
            str(run_dir),
            "--out",
            str(out_dir),
            "--created-at-utc",
            "2000-01-01T00:00:00+00:00",
            "--include-outputs",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
    )
    assert build.returncode == 0, build.stderr

    bundle = out_dir / "replay_pack"

    val = subprocess.run(
        [sys.executable, str(script), "validate", "--bundle", str(bundle)],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
    )
    assert val.returncode == 0, val.stderr

    rep = subprocess.run(
        [sys.executable, str(script), "replay", "--bundle", str(bundle), "--check-outputs"],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
    )
    assert rep.returncode == 0, rep.stderr
