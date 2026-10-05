"""Regression: GHV forensic probe G17/session parity with Full-Core E2E."""

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


_FORENSIC_ENV_KEYS = (
    "PEAK_TRADE_FORENSIC_REPO",
    "PEAK_TRADE_GHV_CONTROL_FIXPOINT_SHA",
    "PEAK_TRADE_GHV_FORENSIC_RESEARCH_V1",
)


@pytest.fixture(autouse=True)
def _isolate_probe_import_pollution() -> None:
    """GHV probe mutates sys.path, env, and sys.modules; restore main-repo productive surface."""
    saved_env = {k: os.environ.get(k) for k in _FORENSIC_ENV_KEYS}
    saved_path = sys.path.copy()
    yield
    for k, v in saved_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    sys.path[:] = saved_path
    for name in list(sys.modules):
        if name.startswith(
            ("src.", "trading.", "run_discovery_lab_v1", "run_full_core_ghv_e2e_v1")
        ):
            del sys.modules[name]


PROBE_SCRIPT = REPO / "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py"
WORKTREE = REPO / ".ghv_worktrees/b36ccbaa"
REF_GHV = (
    REPO
    / "evidence/research/peak_trade_ghv_forensic_system_reconciliation_and_bounded_repair_v1"
    / "20261005T055500Z/run002_ghv_at_b36ccbaa"
)
CONTROL_SHA = "b36ccbaa0468369db634c7bbb6130dcb3713045c"


def _load_probe_module():
    spec = importlib.util.spec_from_file_location("ghv_forensic_probe_v1", PROBE_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


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


def _prepare_probe_context(mod):
    for k in _FORENSIC_ENV_KEYS:
        os.environ.pop(k, None)
    for head in (mod.MAIN_REPO / "src", mod.MAIN_REPO):
        ps = str(head)
        if ps not in sys.path:
            sys.path.insert(0, ps)
    mod._ensure_import_paths()
    import run_discovery_lab_v1 as D  # noqa: E402

    entry_rows = [
        json.loads(line)
        for line in (REF_GHV / "entry_exit_observations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    probe_vectors = mod._select_probe_vectors(entry_rows)
    baseline_cycles = D._load_cycles()
    flights: dict[str, list] = defaultdict(list)
    for c in baseline_cycles:
        flights[str(c["FLIGHT_ID"])].append(c)
    replay_repo = WORKTREE
    return mod, probe_vectors, flights, replay_repo


@pytest.mark.skipif(not _worktree_ready(), reason="fixpoint worktree b36ccbaa not present")
def test_ghv_probe_repaired_path_matches_all_reference_vectors(tmp_path: Path) -> None:
    mod, probe_vectors, flights, replay_repo = _prepare_probe_context(_load_probe_module())
    g17_root = tmp_path / "repaired"
    ordered = sorted(
        probe_vectors,
        key=lambda pv: (str(pv.get("FLIGHT_ID", "")), int(pv.get("CYCLE_ID", 0))),
    )
    matches = 0
    for pv in ordered:
        replay = mod._replay_probe_vector(
            pv,
            flights,
            repo_root=replay_repo,
            g17_store_root=g17_root,
            g17_producers={},
        )
        if replay.get("MATCH"):
            matches += 1
    assert matches == len(probe_vectors)


def test_probe_main_and_purge_paths_enforce_g17_lifecycle_coherence() -> None:
    """Guard: fixpoint replay purges import generation with producer-cache invalidation."""
    source = PROBE_SCRIPT.read_text(encoding="utf-8")
    assert "g17_producers.clear()" in source
    assert "g17_producers={}" in source
    assert 'probe_scope = str(row.get("PROBE_ID") or fid)' in source
