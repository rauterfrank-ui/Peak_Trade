#!/usr/bin/env python3
"""Recovery finalize: reuse completed WF fold aggregates from the first probe run.

Re-runs baseline once (needed for trades_compact / LOO / exit reasons), injects the
already-executed walk-forward fold aggregates, then continues through the fixed
stress/LOO/evidence path via --resume-checkpoint after writing the checkpoint.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

EVIDENCE = Path(__file__).resolve().parent


def main() -> int:
    # Import harness after path setup.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "econ_reeval_probe", EVIDENCE / "economic_reevaluation_probe_v1.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    SOURCE = mod.SOURCE
    cfg = mod._load(SOURCE / "runtime_evaluation_config.json")
    members = mod._panel_members()

    print(json.dumps({"phase": "recovery_baseline", "n": len(members)}), flush=True)
    baseline_rows = []
    t0 = time.perf_counter()
    for i, member_id in enumerate(members, start=1):
        t1 = time.perf_counter()
        row = mod._probe_member(member_id, cfg)
        row["wall_seconds"] = round(time.perf_counter() - t1, 3)
        baseline_rows.append(row)
        print(
            json.dumps(
                {
                    "phase": "baseline_member",
                    "i": i,
                    "n": len(members),
                    "instrument": row["instrument"],
                    "trades": row["total_trades"],
                    "long": row["long_trades"],
                    "short": row["short_trades"],
                    "net_pnl": row["net_pnl"],
                    "seconds": row["wall_seconds"],
                },
                default=str,
            ),
            flush=True,
        )

    baseline_agg = mod._aggregate_rows(baseline_rows)
    traded_members = [r for r in baseline_rows if int(r.get("total_trades") or 0) > 0]
    repro_member = (traded_members[0] if traded_members else baseline_rows[0])["member_id"]
    print(json.dumps({"phase": "repro", "member": repro_member}), flush=True)
    a = mod._probe_member(repro_member, cfg)
    b = mod._probe_member(repro_member, cfg)
    keys = (
        "total_trades",
        "long_trades",
        "short_trades",
        "gross_pnl",
        "net_pnl",
        "net_return",
        "fees",
        "engine_signal_source",
    )
    repro_ok = all(a.get(k) == b.get(k) for k in keys)

    # Fold aggregates from the completed first-run stream (identical cfg/seed/panel).
    wf_rows = [
        {
            "fold": "train",
            "start": "2024-05-01T00:00:00Z",
            "end": "2024-07-01T11:00:00Z",
            "total_trades": 455,
            "long_trades": 0,
            "short_trades": 0,
            "traded_instruments": 0,
            "gross_pnl": 0.0,
            "net_pnl": 0.0,
            "net_return": 0.4535997748365108,
            "profit_factor": "NOT_AVAILABLE",
            "max_drawdown": "NOT_AVAILABLE",
            "fees": 0.0,
            "cost_drag": "NOT_AVAILABLE",
            "source": "first_run_stream_aggregate",
        },
        {
            "fold": "validation",
            "start": "2024-07-01T12:00:00Z",
            "end": "2024-08-01T05:00:00Z",
            "total_trades": 499,
            "long_trades": 0,
            "short_trades": 0,
            "traded_instruments": 0,
            "gross_pnl": 0.0,
            "net_pnl": 0.0,
            "net_return": -0.9419867817405109,
            "profit_factor": "NOT_AVAILABLE",
            "max_drawdown": "NOT_AVAILABLE",
            "fees": 0.0,
            "cost_drag": "NOT_AVAILABLE",
            "source": "first_run_stream_aggregate",
        },
        {
            "fold": "oos",
            "start": "2024-08-01T06:00:00Z",
            "end": "2024-09-01T00:00:00Z",
            "total_trades": 142,
            "long_trades": 0,
            "short_trades": 0,
            "traded_instruments": 0,
            "gross_pnl": 0.0,
            "net_pnl": 0.0,
            "net_return": 0.41217047071955276,
            "profit_factor": "NOT_AVAILABLE",
            "max_drawdown": "NOT_AVAILABLE",
            "fees": 0.0,
            "cost_drag": "NOT_AVAILABLE",
            "source": "first_run_stream_aggregate",
        },
    ]

    checkpoint = {
        "baseline_rows": baseline_rows,
        "wf_rows": wf_rows,
        "baseline_agg": baseline_agg,
        "traded_member_ids": [r["member_id"] for r in traded_members],
        "repro_ok": repro_ok,
        "repro_member": repro_member,
        "recovery_note": (
            "WF fold aggregates reused from completed first probe stream; "
            "baseline re-executed for ledger/LOO/exit evidence."
        ),
        "recovery_baseline_wall_seconds": round(time.perf_counter() - t0, 2),
    }
    (EVIDENCE / "checkpoint_baseline_wf.json").write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "checkpoint": str(EVIDENCE / "checkpoint_baseline_wf.json"),
                "trades": baseline_agg["total_trades"],
                "repro_ok": repro_ok,
                "wall_seconds": checkpoint["recovery_baseline_wall_seconds"],
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
