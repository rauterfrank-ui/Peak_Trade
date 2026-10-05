"""PASS_008 root-class isolation regression guards."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRESH = ROOT / "scripts/ops/peak_trade_v2_fresh_discovery_v1.py"
DISC = ROOT / "scripts/ops/peak_trade_canonical_entrypoint_discovery_v2.py"


def _load(path: Path, name: str):
    import sys

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def test_operator_tool_root_not_productive_seed() -> None:
    fresh = _load(FRESH, "peak_trade_v2_fresh_discovery_v1")
    assert "OPERATOR_TOOL_ROOT" not in fresh.PRODUCTIVE_SEED_CLASSES


def test_forensic_root_not_productive_seed() -> None:
    fresh = _load(FRESH, "peak_trade_v2_fresh_discovery_v1")
    assert "FORENSIC_ROOT" not in fresh.PRODUCTIVE_SEED_CLASSES


def test_test_root_not_productive_seed() -> None:
    fresh = _load(FRESH, "peak_trade_v2_fresh_discovery_v1")
    assert "TEST_ROOT" not in fresh.PRODUCTIVE_SEED_CLASSES


def test_verify_helper_classification_deterministic() -> None:
    disc = _load(DISC, "peak_trade_canonical_entrypoint_discovery_v2")
    repo = ROOT
    rel = "scripts/ops/verify_docs_reference_targets.sh"
    if not (repo / rel).is_file():
        return
    rel_py = "scripts/ops/verify_peak_trade_runtime_contract_v1.py"
    if not (repo / rel_py).is_file():
        return
    ev = disc.analyze_python_module(repo, rel_py, {})
    c1, r1, _ = disc.classify_root(rel_py, ev)
    c2, r2, _ = disc.classify_root(rel_py, ev)
    assert c1 == c2 and r1 == r2


def test_entrypoint_hash_changes_when_root_identity_changes() -> None:
    disc = _load(DISC, "peak_trade_canonical_entrypoint_discovery_v2")
    base = [
        {
            "PATH": "scripts/a.py",
            "ROOT_CLASS": "TESTNET_ROOT",
            "STRUCTURAL_ROOT_EVIDENCE": ["__main__"],
            "IS_STRUCTURAL_ROOT": True,
        }
    ]
    alt = [{**base[0], "PATH": "scripts/b.py"}]
    assert disc.entrypoint_identity_hash(base) != disc.entrypoint_identity_hash(alt)


def test_reachability_hash_changes_when_tuple_changes() -> None:
    disc = _load(DISC, "peak_trade_canonical_entrypoint_discovery_v2")
    base = [
        {
            "ROOT_ID": "r1",
            "ROOT_CLASS": "TESTNET_ROOT",
            "NODE_ID": "n1",
            "REACHABILITY_CLASS": "TESTNET_ROOT",
        }
    ]
    assert disc.reachability_hash(base) != disc.reachability_hash([{**base[0], "NODE_ID": "n2"}])
