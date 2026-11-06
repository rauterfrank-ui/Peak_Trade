"""PASS_007A canonical root discovery regression guards."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "scripts/ops/peak_trade_canonical_entrypoint_discovery_v2.py"


def _disc():
    import sys

    spec = importlib.util.spec_from_file_location(
        "peak_trade_canonical_entrypoint_discovery_v2", DISC
    )
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def test_filename_run_alone_not_structural_root_without_main() -> None:
    disc = _disc()
    repo = ROOT
    rel = "src/execution/bridge/run_fingerprint.py"
    if not (repo / rel).is_file():
        return
    ev = disc.analyze_python_module(repo, rel, {})
    cls, is_root, _why = disc.classify_root(rel, ev)
    assert is_root is False
    assert cls == "LIBRARY_MODULE_NOT_ROOT"


def test_cli_main_testnet_is_structural_root() -> None:
    disc = _disc()
    repo = ROOT
    rel = "scripts/run_testnet_session.py"
    if not (repo / rel).is_file():
        return
    ev = disc.analyze_python_module(repo, rel, {})
    cls, is_root, _why = disc.classify_root(rel, ev)
    assert is_root is True
    assert cls == "TESTNET_ROOT"


def test_node_hash_identity_sensitive() -> None:
    disc = _disc()
    rows = [
        {
            "NODE_ID": "a",
            "PATH": "a",
            "SYMBOL_OR_MODULE": "a",
            "NODE_CLASS": "PYTHON_MODULE",
            "DOMAIN": "OTHER",
            "ROOT_REACHABILITY_CLASSES": [],
        },
    ]
    h1 = disc.node_rows_hash(rows)
    rows2 = list(rows)
    rows2[0] = {**rows2[0], "DOMAIN": "MARKET"}
    h2 = disc.node_rows_hash(rows2)
    assert h1 != h2


def test_edge_hash_identity_sensitive() -> None:
    disc = _disc()
    base = [
        {
            "SOURCE_NODE_ID": "a.py",
            "TARGET_NODE_ID": "b.py",
            "EDGE_CLASS": "COMPOSITION_CURRENT",
            "ROOT_PROVENANCE": "x",
            "RUNTIME_RELEVANCE": True,
        }
    ]
    h1 = disc.edge_rows_hash(base)
    h2 = disc.edge_rows_hash([{**base[0], "EDGE_CLASS": "DORMANT_CURRENT"}])
    assert h1 != h2


def test_reachability_hash_identity_sensitive() -> None:
    disc = _disc()
    base = [
        {
            "ROOT_ID": "r1",
            "ROOT_CLASS": "TESTNET_ROOT",
            "NODE_ID": "n1",
            "REACHABILITY_CLASS": "TESTNET_ROOT",
        }
    ]
    h1 = disc.reachability_hash(base)
    h2 = disc.reachability_hash([{**base[0], "NODE_ID": "n2"}])
    assert h1 != h2


def test_entrypoint_hash_deterministic() -> None:
    disc = _disc()
    rows = [
        {
            "PATH": "scripts/a.py",
            "ROOT_CLASS": "TESTNET_ROOT",
            "STRUCTURAL_ROOT_EVIDENCE": ["__main__"],
            "IS_STRUCTURAL_ROOT": True,
        }
    ]
    assert disc.entrypoint_identity_hash(rows) == disc.entrypoint_identity_hash(list(rows))
