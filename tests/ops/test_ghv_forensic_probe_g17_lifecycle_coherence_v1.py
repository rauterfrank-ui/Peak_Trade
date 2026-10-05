"""GHV probe G17 lifecycle: producer cache vs import generation + per-probe store scope."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PROBE_SCRIPT = REPO / "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py"
WORKTREE = REPO / ".ghv_worktrees/b36ccbaa"
REF_GHV = (
    REPO
    / "evidence/research/peak_trade_ghv_forensic_system_reconciliation_and_bounded_repair_v1"
    / "20261005T055500Z/run002_ghv_at_b36ccbaa"
)
CONTROL_SHA = "b36ccbaa0468369db634c7bbb6130dcb3713045c"


def _worktree_ready() -> bool:
    if not WORKTREE.is_dir():
        return False
    try:
        head = subprocess.check_output(
            ["git", "-C", str(WORKTREE), "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return False
    return head == CONTROL_SHA


def _load_probe_module():
    spec = importlib.util.spec_from_file_location("ghv_forensic_probe_lifecycle_v1", PROBE_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _vectors_and_flights(mod):
    os.environ.pop("PEAK_TRADE_FORENSIC_REPO", None)
    for head in (mod.MAIN_REPO / "src", mod.MAIN_REPO):
        ps = str(head)
        if ps not in sys.path:
            sys.path.insert(0, ps)
    mod._ensure_import_paths()
    import run_discovery_lab_v1 as D  # noqa: E402

    flights: dict[str, list] = defaultdict(list)
    for c in D._load_cycles():
        flights[str(c["FLIGHT_ID"])].append(c)
    entry_rows = [
        json.loads(line)
        for line in (REF_GHV / "entry_exit_observations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    return mod._select_probe_vectors(entry_rows), flights


@pytest.mark.skipif(not _worktree_ready(), reason="fixpoint worktree b36ccbaa not present")
def test_producer_cache_cleared_on_fixpoint_replay_purge_boundary(tmp_path: Path) -> None:
    mod = _load_probe_module()
    vectors, flights = _vectors_and_flights(mod)
    pv0 = next(v for v in vectors if v.get("FLIGHT_ID") == "GHV-F0001" and int(v["CYCLE_ID"]) == 0)
    pv1 = next(v for v in vectors if v.get("FLIGHT_ID") == "GHV-F0001" and int(v["CYCLE_ID"]) == 1)
    shared: dict[str, object] = {}
    root = tmp_path / "producer_lifecycle"
    r0 = mod._replay_probe_vector(
        pv0, flights, repo_root=WORKTREE, g17_store_root=root, g17_producers=shared
    )
    r1 = mod._replay_probe_vector(
        pv1, flights, repo_root=WORKTREE, g17_store_root=root, g17_producers=shared
    )
    assert r0.get("MATCH") is True
    assert r1.get("MATCH") is True
    assert "G17_CMC_BIND" not in str(r1.get("ERROR", ""))


@pytest.mark.skipif(not _worktree_ready(), reason="fixpoint worktree b36ccbaa not present")
def test_g17_store_scoped_by_probe_id_prevents_f0066_cross_vector_leak(tmp_path: Path) -> None:
    mod = _load_probe_module()
    vectors, flights = _vectors_and_flights(mod)
    f0066 = sorted(
        [pv for pv in vectors if pv.get("FLIGHT_ID") == "GHV-F0066"],
        key=lambda pv: int(pv.get("CYCLE_ID", 0)),
    )
    assert len(f0066) >= 2
    root = tmp_path / "scoped"
    matches = 0
    for pv in f0066:
        replay = mod._replay_probe_vector(
            pv,
            flights,
            repo_root=WORKTREE,
            g17_store_root=root,
            g17_producers={},
        )
        probe_scope = str(pv.get("PROBE_ID"))
        store_path = root / probe_scope / str(pv.get("FLIGHT_ID"))
        assert store_path.is_dir(), "each vector owns isolated store subtree"
        if replay.get("MATCH"):
            matches += 1
    assert matches == len(f0066)
