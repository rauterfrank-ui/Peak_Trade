#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve()


def discover_repo_root_from_script() -> Path | None:
    for parent in [_SCRIPT_PATH, *_SCRIPT_PATH.parents]:
        if (parent / "src").is_dir() and (parent / ".git").exists():
            return parent.resolve()
    return None


def validate_peak_trade_repo_root(repo_root: Path) -> Path:
    resolved = repo_root.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"REPO_ROOT_INVALID_NOT_DIRECTORY: {resolved}")
    if not (resolved / "src").is_dir():
        raise SystemExit(f"REPO_ROOT_INVALID_MISSING_SRC: {resolved}")
    if not (resolved / ".git").exists():
        raise SystemExit(f"REPO_ROOT_INVALID_MISSING_GIT: {resolved}")
    return resolved


def resolve_repo_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return validate_peak_trade_repo_root(explicit)
    discovered = discover_repo_root_from_script()
    if discovered is None:
        raise SystemExit("REPO_ROOT_DISCOVERY_FAILED: not inside Peak_Trade repo")
    return discovered


_discovered_repo_root = discover_repo_root_from_script()
if _discovered_repo_root is not None:
    repo_s = str(_discovered_repo_root)
    if repo_s not in sys.path:
        sys.path.insert(0, repo_s)

from scripts.ops.run_economic_viability_evidence_evaluation_v1 import (  # noqa: E402
    _load_bars_from_dataset_path,
)
from src.research.offline_productive_point_in_time_factor_snapshot_rematerializer_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    load_jsonl_rows,
    materialize_productive_point_in_time_factor_snapshots_v0,
    productive_factor_field_provenance_v0,
    serialize_productive_point_in_time_factor_snapshots_v0,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline productive point-in-time factor snapshot rematerializer v0"
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--trade-ledger", required=True, type=Path)
    parser.add_argument("--bars-dataset", required=True, type=Path)
    parser.add_argument("--spread-half-bps", required=True, type=float)
    parser.add_argument("--instrument-id", default=None)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    trade_rows = load_jsonl_rows(args.trade_ledger)
    bars = _load_bars_from_dataset_path(args.bars_dataset)
    result = materialize_productive_point_in_time_factor_snapshots_v0(
        trade_ledger_rows=trade_rows,
        bars=bars,
        spread_half_bps=args.spread_half_bps,
        source_dataset_ref=str(args.bars_dataset.resolve()),
        expected_instrument_id=args.instrument_id,
    )
    serialized = serialize_productive_point_in_time_factor_snapshots_v0(result.snapshots)
    (out / "productive_point_in_time_factor_snapshots_v0.jsonl").write_text(
        serialized, encoding="utf-8"
    )
    report = {
        "status": result.status.value,
        "admissible_count": result.admissible_count,
        "rejected_count": len(result.rejected),
        "dropped_rows_by_reason": dict(result.dropped_rows_by_reason),
        "materialization_digest": result.materialization_digest,
        "source_trade_ledger_digest": result.source_trade_ledger_digest,
        "source_bars_digest": result.source_bars_digest,
        "source_dataset_ref": result.source_dataset_ref,
        "spread_bps_binding": result.spread_bps_binding,
        "feature_provenance": productive_factor_field_provenance_v0(),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "offline_only": True,
        "repo_root": str(repo_root),
    }
    (out / "rematerialization_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    final_report = "\n".join(
        [
            "VERDICT=OFFLINE_PRODUCTIVE_POINT_IN_TIME_FACTOR_SNAPSHOT_REMATERIALIZATION_V0_COLLECTED",
            f"STATUS={result.status.value}",
            f"ADMISSIBLE_COUNT={result.admissible_count}",
            f"REJECTED_COUNT={len(result.rejected)}",
            f"DROPPED_ROWS_BY_REASON={json.dumps(result.dropped_rows_by_reason, sort_keys=True)}",
            f"MATERIALIZATION_DIGEST={result.materialization_digest}",
            f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
            f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
            "OFFLINE_ONLY=true",
            "",
        ]
    )
    (out / "final_report.txt").write_text(final_report, encoding="utf-8")
    print(final_report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
