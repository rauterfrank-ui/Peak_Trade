from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.execution.bridge.artifact_sink import FileSystemArtifactSink
from src.execution.bridge.beta_event_bridge import BetaEventBridge, BetaEventBridgeConfig
from src.execution.bridge.int_ledger_engine import IntLedgerEngine


def _read_normalized_jsonl(base: Path) -> bytes:
    # normalized artifact is at out/<fingerprint>/normalized_beta_events.jsonl
    files = [p for p in base.rglob("normalized_beta_events.jsonl") if p.is_file()]
    assert len(files) == 1
    return files[0].read_bytes()


def _events_from_fixture() -> list[dict[str, Any]]:
    p = Path("tests/fixtures/slice3_beta_events_minimal.jsonl")
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def test_beta_event_bridge_ordering_shuffle_invariant(tmp_path: Path):
    baseline_events = _events_from_fixture()
    shuffled_events = [
        baseline_events[3],
        baseline_events[0],
        baseline_events[4],
        baseline_events[2],
        baseline_events[1],
    ]

    prices_manifest = {"prices_ref": "sha256:deadbeef", "price_scale": 10000, "money_scale": 10000}
    cfg = BetaEventBridgeConfig(emit_equity_curve=False)

    out_a = tmp_path / "baseline"
    out_b = tmp_path / "shuffled"

    eng_a = IntLedgerEngine(
        base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000
    )
    BetaEventBridge(eng_a, prices_manifest_or_ref=prices_manifest, config=cfg).run(
        baseline_events, sink=FileSystemArtifactSink(out_a)
    )

    eng_b = IntLedgerEngine(
        base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000
    )
    BetaEventBridge(eng_b, prices_manifest_or_ref=prices_manifest, config=cfg).run(
        shuffled_events, sink=FileSystemArtifactSink(out_b)
    )

    assert _read_normalized_jsonl(out_a) == _read_normalized_jsonl(out_b)


def test_beta_event_bridge_forbidden_imports_scan():
    # Best-effort guard: scan AST imports only (ignore docstrings/comments).
    import ast

    root = Path("src/execution/bridge")
    forbidden_modules = {"datetime", "time", "uuid", "random"}
    files = sorted(p for p in root.rglob("*.py") if p.is_file())
    assert files, "expected src/execution/bridge/**/*.py files"

    for p in files:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".", 1)[0]
                    assert top not in forbidden_modules, (
                        f"forbidden import {alias.name!r} found in {p}"
                    )
            if isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".", 1)[0]
                assert top not in forbidden_modules, (
                    f"forbidden import from {node.module!r} found in {p}"
                )


def test_beta_event_bridge_rejects_float_payload(tmp_path: Path):
    prices_manifest = {"prices_ref": "sha256:deadbeef", "price_scale": 10000, "money_scale": 10000}
    cfg = BetaEventBridgeConfig(emit_equity_curve=False)
    eng = IntLedgerEngine(
        base_ccy="USD", money_scale=10000, price_scale=10000, qty_scale=1, cash_int=10_000_000
    )

    bad_events = [
        {"event_type": "Price", "t": 0, "payload": {"symbol": "ACME", "price_int": 123450000}},
        # float should hard-error
        {
            "event_type": "OrderIntent",
            "t": 1,
            "payload": {"symbol": "ACME", "qty_int": 10, "slippage": 0.1},
        },
    ]

    import pytest
    from src.execution.bridge.beta_event_bridge import BetaEventBridgeError

    with pytest.raises(BetaEventBridgeError):
        BetaEventBridge(eng, prices_manifest_or_ref=prices_manifest, config=cfg).run(
            bad_events, sink=FileSystemArtifactSink(tmp_path / "out")
        )
