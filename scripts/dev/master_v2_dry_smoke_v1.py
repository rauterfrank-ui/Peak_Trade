#!/usr/bin/env python3
"""
Nicht-produktiver, opt-in Master-V2-Dry-Smoke (v1).

Fuehrt die kanonische Scenario-Matrix gegen den lokalen Evaluator aus
(`local_evaluator_scenarios_v1`) und prueft zusaetzlich einen minimalen
Wire-Format-Pfad: JSON-Roundtrip -> `adapt_inputs_to_master_v2_flow_v1` mit
lokalem Evaluator. Kein Live, kein Paper, keine Broker-Logik.

Verwendung (explizit):
  PYTHONPATH=src python scripts/dev/master_v2_dry_smoke_v1.py --run
  # oder mit uv (Repo-Root):
  uv run python scripts/dev/master_v2_dry_smoke_v1.py --run

Ohne --run: nur kurzer Hinweis auf stdout, Exit 0 (kein Side-Effect).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _setup_src_path() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent
    src = repo_root / "src"
    s = str(src)
    if s not in sys.path:
        sys.path.insert(0, s)


def _run_wire_format_smoke_v1() -> None:
    """
    Simuliert Wire: JSON dump/load -> Input-Adapter inkl. Local-Evaluator.
    Fail-closed: wirft, wenn Adapter oder Flow nicht dem Happy-Path entsprechen.
    """
    from trading.master_v2.happy_raw_input_v1 import build_master_v2_happy_scenario_raw_input_v1
    from trading.master_v2.input_adapter_v1 import adapt_inputs_to_master_v2_flow_v1

    raw = build_master_v2_happy_scenario_raw_input_v1()
    as_wire = json.loads(json.dumps(raw))
    ar = adapt_inputs_to_master_v2_flow_v1(as_wire, run_evaluator=True, with_snapshot=True)
    if not ar.ok:
        raise RuntimeError(f"wire_smoke: adapter rejected: {ar.rejection_reason!r}")
    if ar.local_flow is None:
        raise RuntimeError("wire_smoke: expected local_flow when run_evaluator=True")
    if not ar.local_flow.flow_ok:
        raise RuntimeError(f"wire_smoke: local flow not ok: {ar.local_flow.rejection_reason!r}")


def run_master_v2_dry_smoke_v1() -> dict[str, Any]:
    """
    Laeuft die volle Szenario-Matrix gegen den Local-Flow-Evaluator; wirft bei Drift.
    Dann: minimaler Wire-Format-Smoke (JSON -> Adapter -> Local Evaluator).
    Reine In-Memory-Contracts, kein I/O.
    """
    from trading.master_v2.local_evaluator_scenarios_v1 import (
        assert_master_v2_scenario_harness_outcome_v1,
        run_master_v2_scenario_matrix_v1,
    )
    from trading.master_v2.scenario_matrix_v1 import build_master_v2_scenario_matrix_v1

    m = build_master_v2_scenario_matrix_v1()
    results = run_master_v2_scenario_matrix_v1()
    for name, r in results.items():
        assert_master_v2_scenario_harness_outcome_v1(m[name], r)
    _run_wire_format_smoke_v1()
    return {
        "ok": True,
        "dry_smoke_adapter_version": "v1",
        "scenario_count": len(results),
        "scenarios": sorted(results.keys()),
        "wire_path_ok": True,
        "wire_smoke_version": "v1",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Master V2: opt-in dry smoke (Scenario-Matrix + minimaler Wire-Format / Adapter)."
        ),
    )
    p.add_argument(
        "--run",
        action="store_true",
        help="Explizit opt-in: Dry-Smoke tatsaechlich ausfuehren",
    )
    args = p.parse_args(argv)
    if not args.run:
        print(
            "master_v2_dry_smoke_v1: nichts ausgefuehrt. "
            "Zum Opt-in: dieses Skript mit --run aufrufen (siehe Docstring).",
            file=sys.stdout,
        )
        return 0
    _setup_src_path()
    try:
        out = run_master_v2_dry_smoke_v1()
    except Exception as e:
        err = {
            "ok": False,
            "dry_smoke_adapter_version": "v1",
            "error": f"{type(e).__name__}: {e}",
        }
        print(json.dumps(err, indent=2), file=sys.stdout)
        return 1
    print(json.dumps(out, indent=2), file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
