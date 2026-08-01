#!/usr/bin/env python3
"""CLI: productive max-age research evidence accumulation (non-enforcing)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.coverage_v1 import (  # noqa: E402
    evaluate_coverage_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.runtime_v1 import (  # noqa: E402
    accumulate_from_cycles_batch_v1,
    bind_accumulation_state_v1,
    reconstruct_coverage_from_ledgers_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (  # noqa: E402
    coverage_summary_v1,
    load_research_evidence_records_v1,
)


def _git_sha(repo_root: Path) -> str:
    out = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        text=True,
    ).strip()
    return out


def _synthetic_probe_cycles_v1() -> list[dict]:
    """Deterministic offline probe cycles for operator-controlled dry accumulation.

    These are typed fixture cycles (event-time based), not wallclock/poll inventions.
    """
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def _cycle(
        *,
        session_id: str,
        cycle_id: str,
        regime_id: str,
        slope: float,
        age: float,
        offset: int,
        estimate_id: str,
        observation_count: int,
    ) -> dict:
        ref = t0.timestamp() + offset
        as_of = ref - age
        ref_iso = datetime.fromtimestamp(ref, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        as_of_iso = (
            datetime.fromtimestamp(as_of, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        )
        source = f"src_{estimate_id}"
        return {
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": "ETH-USD_UM_XPERP-310404",
            "venue": "OKX",
            "venue_instrument_id": "ETH-USD-SWAP",
            "market_event_time": ref_iso,
            "decision_outcome": "HOLD",
            "selected_side": "FLAT",
            "economic_metrics": {"net_pnl": 0.0},
            "feature_regime": {
                "ok": True,
                "warmup_complete": True,
                "regime_id": regime_id,
                "regime_state_source": "CANONICAL_RUNTIME_PIPELINE",
                "trend_features": {"slope": slope, "strength": 0.2},
                "momentum_features": {"rsi": 50.0, "roc": slope},
                "liquidity_features": {"depth_score": 1.0},
                "market_structure_features": {"range_ratio": 0.01},
                "volatility_estimate": 0.02,
                "mark_price": 3500.0,
                "blockers": [],
                "default_regime_fallback_active": False,
            },
            "canonical_volatility_typed_binding": {
                "session_id": session_id,
                "cycle_id": cycle_id,
                "instrument_id": "ETH-USD_UM_XPERP-310404",
                "venue": "OKX",
                "venue_instrument_id": "ETH-USD-SWAP",
                "producer_outcome": "PRODUCED",
                "estimate_present": True,
                "observation_count": observation_count,
                "source_digest": source,
                "source_estimate_id": estimate_id,
                "estimate_id": estimate_id,
                "volatility_value": 0.02,
                "volatility_unit": "DECIMAL_FRACTION",
                "volatility_horizon_seconds": 3600.0,
                "volatility_estimator": "TYPED_RUNTIME_PRODUCER",
                "reuse_status": "FRESHLY_PRODUCED",
                "restart_status": "NOT_APPLICABLE",
                "fallback_used": False,
            },
            "double_play_typed_volatility_presence_gate": {
                "session_id": session_id,
                "cycle_id": cycle_id,
                "instrument_id": "ETH-USD_UM_XPERP-310404",
                "regime_id": regime_id,
                "max_age_policy_evidence": {
                    "estimate_as_of_event_time": as_of_iso,
                    "reference_event_time": ref_iso,
                    "computed_age_seconds": float(age),
                    "max_age_status": "AGE_COMPUTED_THRESHOLD_UNRESOLVED",
                    "threshold_status": "UNRESOLVED_MAX_AGE",
                    "presence_status": "PRESENT",
                    "clock_trust_status": "TRUSTED",
                    "data_integrity_status": "TRUSTED",
                    "reuse_status": "FRESHLY_PRODUCED",
                    "restart_status": "NOT_APPLICABLE",
                    "source_digest": source,
                    "decision": "AGE_COMPUTED",
                    "reason_code": "VOLATILITY_ESTIMATE_AGE_UNRESOLVED",
                    "enforcement_applied": False,
                    "numeric_threshold_selected": False,
                    "session_id": session_id,
                    "cycle_id": cycle_id,
                    "instrument_id": "ETH-USD_UM_XPERP-310404",
                    "regime_id": regime_id,
                },
            },
        }

    cycles = [
        _cycle(
            session_id="sess-a",
            cycle_id="c-a1",
            regime_id="trending",
            slope=0.01,
            age=60,
            offset=0,
            estimate_id="est-a1",
            observation_count=60,
        ),
        _cycle(
            session_id="sess-a",
            cycle_id="c-a2",
            regime_id="trending",
            slope=0.01,
            age=120,
            offset=120,
            estimate_id="est-a1",
            observation_count=60,
        ),
        _cycle(
            session_id="sess-a",
            cycle_id="c-a3",
            regime_id="ranging",
            slope=0.0,
            age=180,
            offset=240,
            estimate_id="est-a2",
            observation_count=60,
        ),
        _cycle(
            session_id="sess-a",
            cycle_id="c-a4",
            regime_id="volatile",
            slope=0.0,
            age=240,
            offset=360,
            estimate_id="est-a3",
            observation_count=60,
        ),
    ]
    # Second independent session.
    for i, age in enumerate((90, 150, 210, 270), start=1):
        cycles.append(
            _cycle(
                session_id="sess-b",
                cycle_id=f"c-b{i}",
                regime_id="ranging" if i % 2 else "trending",
                slope=-0.01 if i % 2 == 0 else 0.0,
                age=age,
                offset=1000 + i * 120,
                estimate_id=f"est-b{i}",
                observation_count=60,
            )
        )
    return cycles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Accumulate productive canonical-volatility max-age research evidence. "
            "Never selects or enforces a numeric threshold."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--productive-ledger-path", type=Path, default=None)
    parser.add_argument("--join-ledger-path", type=Path, default=None)
    parser.add_argument("--quarantine-ledger-path", type=Path, default=None)
    parser.add_argument("--repository-sha", type=str, default=None)
    parser.add_argument(
        "--mode",
        choices=("probe-accumulate", "coverage-only", "verify-join-load"),
        default="probe-accumulate",
    )
    parser.add_argument("--session-id", type=str, default="operator-probe-session")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    sha = args.repository_sha or _git_sha(repo_root)

    if args.mode == "coverage-only":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH,
            DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH,
        )

        productive = args.productive_ledger_path or (
            repo_root / DEFAULT_PRODUCTIVE_LEDGER_RELATIVE_PATH
        )
        quarantine = args.quarantine_ledger_path or (
            repo_root / DEFAULT_QUARANTINE_LEDGER_RELATIVE_PATH
        )
        result = reconstruct_coverage_from_ledgers_v1(
            productive_ledger_path=productive,
            quarantine_ledger_path=quarantine,
        )
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0

    if args.mode == "verify-join-load":
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
            DEFAULT_JOIN_LEDGER_RELATIVE_PATH,
        )

        join_path = args.join_ledger_path or (repo_root / DEFAULT_JOIN_LEDGER_RELATIVE_PATH)
        records = load_research_evidence_records_v1(join_path)
        summary = coverage_summary_v1(records)
        print(
            json.dumps(
                {"join_coverage": summary, "status": "PASS"},
                sort_keys=True,
                indent=2,
                default=str,
            )
        )
        return 0

    # probe-accumulate: two independent sessions for multi-session coverage
    all_cycles = _synthetic_probe_cycles_v1()
    by_session: dict[str, list[dict]] = {}
    for cycle in all_cycles:
        by_session.setdefault(str(cycle["session_id"]), []).append(cycle)

    session_reports = []
    join_path = None
    productive_path = None
    quarantine_path = None
    for session_id, cycles in by_session.items():
        state = bind_accumulation_state_v1(
            session_id=session_id,
            session_start_event_time=str(cycles[0]["market_event_time"]),
            repository_sha=sha,
            venue="OKX",
            canonical_instrument_id="ETH-USD_UM_XPERP-310404",
            venue_instrument_id="ETH-USD-SWAP",
            repo_root=repo_root,
            productive_ledger_path=args.productive_ledger_path,
            join_ledger_path=args.join_ledger_path,
            quarantine_ledger_path=args.quarantine_ledger_path,
        )
        report = accumulate_from_cycles_batch_v1(cycles, state=state, complete_session=True)
        session_reports.append(report)
        join_path = state.join_ledger_path
        productive_path = state.productive_ledger_path
        quarantine_path = state.quarantine_ledger_path

    coverage = evaluate_coverage_from_ledger_v1(
        productive_ledger_path=productive_path,
        quarantine_ledger_path=quarantine_path,
    )
    join_records = load_research_evidence_records_v1(join_path)
    join_coverage = coverage_summary_v1(join_records)
    result = {
        "coverage": coverage.to_dict(),
        "join_coverage": join_coverage,
        "join_ledger_path": str(join_path),
        "productive_ledger_path": str(productive_path),
        "ready_for_research_execution": coverage.ready_for_research_execution,
        "repository_sha": sha,
        "session_reports": session_reports,
        "status": "PASS",
        "threshold_status": "UNRESOLVED_MAX_AGE",
        "numeric_threshold_selected": False,
        "enforcement_applied": False,
    }
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
