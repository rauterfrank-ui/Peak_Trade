from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.execution.bridge.artifact_sink import FileSystemArtifactSink
from src.execution.bridge.beta_event_bridge import BetaEventBridge, BetaEventBridgeConfig
from src.execution.bridge.int_ledger_engine import IntLedgerEngine


def _collect_files(base: Path) -> list[Path]:
    files = [p for p in base.rglob("*") if p.is_file()]
    return sorted(files, key=lambda p: str(p.relative_to(base)))


def _read_all_bytes(base: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in _collect_files(base):
        out[str(p.relative_to(base))] = p.read_bytes()
    return out


def _beta_events_from_fixture() -> list[dict[str, Any]]:
    p = Path("tests/fixtures/slice3_beta_events_minimal.jsonl")
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def test_beta_event_bridge_determinism_byte_identical(tmp_path: Path):
    events = _beta_events_from_fixture()

    # Fixed prices manifest/ref used only for fingerprinting (no absolute paths).
    prices_manifest = {"prices_ref": "sha256:deadbeef", "price_scale": 10000, "money_scale": 10000}

    cfg = BetaEventBridgeConfig(emit_equity_curve=True, equity_snapshot_every_n_events=1)

    out_a = tmp_path / "a"
    out_b = tmp_path / "b"

    eng_a = IntLedgerEngine(
        base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000
    )
    bridge_a = BetaEventBridge(
        eng_a,
        prices_manifest_or_ref=prices_manifest,
        config=cfg,
    )
    bridge_a.run(events, sink=FileSystemArtifactSink(out_a))

    eng_b = IntLedgerEngine(
        base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000
    )
    bridge_b = BetaEventBridge(
        eng_b,
        prices_manifest_or_ref=prices_manifest,
        config=cfg,
    )
    bridge_b.run(events, sink=FileSystemArtifactSink(out_b))

    files_a = [str(p.relative_to(out_a)) for p in _collect_files(out_a)]
    files_b = [str(p.relative_to(out_b)) for p in _collect_files(out_b)]
    assert files_a == files_b

    assert _read_all_bytes(out_a) == _read_all_bytes(out_b)
