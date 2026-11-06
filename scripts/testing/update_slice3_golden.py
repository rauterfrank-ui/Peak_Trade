from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.execution.bridge.artifact_sink import FileSystemArtifactSink
from src.execution.bridge.beta_event_bridge import BetaEventBridge, BetaEventBridgeConfig
from src.execution.bridge.canonical_json import dumps_canonical
from src.execution.bridge.int_ledger_engine import IntLedgerEngine


def _read_jsonl_events(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError("Fixture JSONL must contain objects only")
        out.append(obj)
    return out


def _collect_files(base: Path) -> list[Path]:
    files = [p for p in base.rglob("*") if p.is_file()]
    return sorted(files, key=lambda p: str(p.relative_to(base)))


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update Slice-3 golden artifacts (opt-in, deterministic)."
    )
    parser.add_argument(
        "--fixture",
        required=True,
        help="Path to JSONL fixture, e.g. tests/fixtures/slice3_beta_events_minimal.jsonl",
    )
    parser.add_argument(
        "--equity-golden",
        default="tests/golden/slice3_equity_curve_minimal.jsonl",
        help="Path to write canonical equity_curve golden JSONL",
    )
    parser.add_argument(
        "--manifest-golden",
        default="tests/golden/slice3_artifact_manifest_minimal.json",
        help="Path to write optional artifact manifest JSON",
    )
    args = parser.parse_args(argv)

    fixture_path = (
        (REPO_ROOT / args.fixture).resolve()
        if not Path(args.fixture).is_absolute()
        else Path(args.fixture)
    )
    equity_golden_path = (
        (REPO_ROOT / args.equity_golden).resolve()
        if not Path(args.equity_golden).is_absolute()
        else Path(args.equity_golden)
    )
    manifest_golden_path = (
        (REPO_ROOT / args.manifest_golden).resolve()
        if not Path(args.manifest_golden).is_absolute()
        else Path(args.manifest_golden)
    )

    events = _read_jsonl_events(fixture_path)

    # Fixed manifest/ref: must remain deterministic (no absolute paths).
    prices_manifest = {"prices_ref": "sha256:deadbeef", "price_scale": 10000, "money_scale": 10000}
    cfg = BetaEventBridgeConfig(emit_equity_curve=True, equity_snapshot_every_n_events=1)

    eng = IntLedgerEngine(
        base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000
    )
    bridge = BetaEventBridge(eng, prices_manifest_or_ref=prices_manifest, config=cfg)

    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td)
        result = bridge.run(events, sink=FileSystemArtifactSink(out_dir))

        equity_rel = result.artifact_relpaths["equity_curve.jsonl"]
        equity_bytes = (out_dir / equity_rel).read_bytes()
        _write_bytes(equity_golden_path, equity_bytes)

        # Optional manifest: relpaths (from out_dir) + sha256, sorted by relpath.
        entries: list[dict[str, str]] = []
        for p in _collect_files(out_dir):
            rel = str(p.relative_to(out_dir))
            entries.append({"relpath": rel, "sha256": _sha256_hex(p.read_bytes())})
        entries.sort(key=lambda e: e["relpath"])

        manifest_bytes = dumps_canonical(entries) + b"\n"
        _write_bytes(manifest_golden_path, manifest_bytes)

    print(f"Wrote equity golden: {equity_golden_path}")
    print(f"Wrote manifest golden: {manifest_golden_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
