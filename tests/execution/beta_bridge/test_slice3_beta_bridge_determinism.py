from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from src.execution.beta_bridge import (
    BetaBridgeConfig,
    BetaEventBridge,
    DeterministicArtifactSink,
    run_fingerprint,
)
from src.execution.determinism import stable_id


def _mk_event(
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
        # Simulate slice-1 wall-clock field; must be dropped by bridge.
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": request_id,
        "client_order_id": client_order_id,
        "reason_code": None,
        "reason_detail": None,
        "payload": payload,
    }


def _read_artifacts_bytes(out_dir: Path) -> dict[str, bytes]:
    return {
        "normalized_beta_events.jsonl": (out_dir / "normalized_beta_events.jsonl").read_bytes(),
        "ledger_applied_events.jsonl": (out_dir / "ledger_applied_events.jsonl").read_bytes(),
        "ledger_final_state.json": (out_dir / "ledger_final_state.json").read_bytes(),
    }


def test_slice3_bridge_determinism_same_inputs_byte_identical(tmp_path: Path):
    run_id = "run_s3_001"
    sess = "sess_s3_001"
    intent = "intent_s3_001"
    sym = "BTC/EUR"

    events = [
        _mk_event(
            run_id=run_id,
            session_id=sess,
            intent_id=intent,
            symbol=sym,
            event_type="INTENT",
            ts_sim=0,
        ),
        _mk_event(
            run_id=run_id,
            session_id=sess,
            intent_id=intent,
            symbol=sym,
            event_type="SUBMIT",
            ts_sim=1,
            client_order_id="order_001",
            payload={"side": "BUY", "quantity": "0.01000000", "order_type": "MARKET"},
        ),
        _mk_event(
            run_id=run_id,
            session_id=sess,
            intent_id=intent,
            symbol=sym,
            event_type="FILL",
            ts_sim=2,
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

    cfg = BetaBridgeConfig(
        quote_currency="EUR", opening_cash="1000.00000000", emit_equity_curve=False
    )
    bridge = BetaEventBridge(config=cfg)

    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"

    bridge.run(events=events, sink=DeterministicArtifactSink(out_a))
    bridge.run(events=events, sink=DeterministicArtifactSink(out_b))

    assert _read_artifacts_bytes(out_a) == _read_artifacts_bytes(out_b)


def test_slice3_bridge_ordering_shuffle_input_same_output(tmp_path: Path):
    run_id = "run_s3_002"
    sess = "sess_s3_002"
    intent = "intent_s3_002"
    sym = "BTC/EUR"

    e0 = _mk_event(
        run_id=run_id, session_id=sess, intent_id=intent, symbol=sym, event_type="INTENT", ts_sim=0
    )
    e1 = _mk_event(
        run_id=run_id,
        session_id=sess,
        intent_id=intent,
        symbol=sym,
        event_type="SUBMIT",
        ts_sim=1,
        client_order_id="order_001",
        payload={"side": "BUY", "quantity": "0.01000000", "order_type": "MARKET"},
    )
    e2 = _mk_event(
        run_id=run_id,
        session_id=sess,
        intent_id=intent,
        symbol=sym,
        event_type="FILL",
        ts_sim=2,
        client_order_id="order_001",
        payload={
            "fill_id": "fill_001",
            "side": "BUY",
            "quantity": "0.01000000",
            "price": "50000.00000000",
            "fee": "0.50000000",
            "fee_currency": "EUR",
        },
    )

    events_sorted = [e0, e1, e2]
    events_shuffled = [e2, e0, e1]

    cfg = BetaBridgeConfig(
        quote_currency="EUR", opening_cash="1000.00000000", emit_equity_curve=False
    )
    bridge = BetaEventBridge(config=cfg)

    out_sorted = tmp_path / "out_sorted"
    out_shuf = tmp_path / "out_shuf"
    bridge.run(events=events_sorted, sink=DeterministicArtifactSink(out_sorted))
    bridge.run(events=events_shuffled, sink=DeterministicArtifactSink(out_shuf))

    assert _read_artifacts_bytes(out_sorted) == _read_artifacts_bytes(out_shuf)


def test_slice3_bridge_no_wall_clock_calls_runtime_best_effort(tmp_path: Path):
    run_id = "run_s3_003"
    sess = "sess_s3_003"
    intent = "intent_s3_003"
    sym = "BTC/EUR"
    events = [
        _mk_event(
            run_id=run_id,
            session_id=sess,
            intent_id=intent,
            symbol=sym,
            event_type="INTENT",
            ts_sim=0,
        ),
        _mk_event(
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

    cfg = BetaBridgeConfig(
        quote_currency="EUR", opening_cash="1000.00000000", emit_equity_curve=False
    )
    bridge = BetaEventBridge(config=cfg)

    def _boom(*_a, **_kw):  # noqa: ANN001, D401
        raise AssertionError("forbidden non-deterministic call")

    with (
        patch("time.time", _boom),
        patch("time.monotonic", _boom),
        patch("uuid.uuid4", _boom),
        patch("random.random", _boom),
        patch("random.randint", _boom),
    ):
        bridge.run(events=events, sink=DeterministicArtifactSink(tmp_path / "out"))


def test_slice3_bridge_source_guard_no_forbidden_calls():
    root = Path("src/execution/beta_bridge")
    forbidden = [
        "datetime.now(",
        "time.time(",
        "time.monotonic(",
        "uuid.uuid4",
        "random.random",
        "random.randint",
    ]

    files = sorted(p for p in root.rglob("*.py") if p.is_file())
    assert files, "expected beta_bridge package files"

    for p in files:
        s = p.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in s, f"forbidden call {needle!r} found in {p}"


def test_slice3_run_fingerprint_depends_only_on_manifest_and_config():
    manifest = {"events_ref": "events_sha256:abc", "prices_ref": "prices_sha256:def"}
    cfg = {"quote_currency": "EUR", "opening_cash": "1000.00000000", "emit_equity_curve": False}

    a = run_fingerprint(input_manifest=manifest, config=cfg)
    b = run_fingerprint(input_manifest=manifest, config=cfg)
    assert a == b
