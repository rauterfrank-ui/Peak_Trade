from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.execution.bridge.artifact_sink import FileSystemArtifactSink
from src.execution.bridge.beta_event_bridge import BetaEventBridge, BetaEventBridgeConfig
from src.execution.bridge.int_ledger_engine import IntLedgerEngine


def _read_fixture_events() -> list[dict[str, Any]]:
    p = Path("tests/fixtures/slice3_beta_events_minimal.jsonl")
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def _collect_files(base: Path) -> list[Path]:
    files = [p for p in base.rglob("*") if p.is_file()]
    return sorted(files, key=lambda p: str(p.relative_to(base)))


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_slice3_equity_curve_golden_byte_identical(tmp_path: Path) -> None:
    events = _read_fixture_events()

    prices_manifest = {"prices_ref": "sha256:deadbeef", "price_scale": 10000, "money_scale": 10000}
    cfg = BetaEventBridgeConfig(emit_equity_curve=True, equity_snapshot_every_n_events=1)

    eng = IntLedgerEngine(
        base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000
    )
    bridge = BetaEventBridge(eng, prices_manifest_or_ref=prices_manifest, config=cfg)

    out_dir = tmp_path / "out"
    result = bridge.run(events, sink=FileSystemArtifactSink(out_dir))

    equity_rel = result.artifact_relpaths["equity_curve.jsonl"]
    equity_bytes = (out_dir / equity_rel).read_bytes()
    golden_bytes = Path("tests/golden/slice3_equity_curve_minimal.jsonl").read_bytes()
    assert equity_bytes == golden_bytes

    # Optional: full artifact set manifest (relpaths + sha256).
    manifest_path = Path("tests/golden/slice3_artifact_manifest_minimal.json")
    if manifest_path.exists():
        expected = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert isinstance(expected, list)
        expected_sorted = sorted(expected, key=lambda e: e["relpath"])

        got_entries: list[dict[str, str]] = []
        for p in _collect_files(out_dir):
            got_entries.append(
                {"relpath": str(p.relative_to(out_dir)), "sha256": _sha256_hex(p.read_bytes())}
            )
        got_sorted = sorted(got_entries, key=lambda e: e["relpath"])

        assert got_sorted == expected_sorted
