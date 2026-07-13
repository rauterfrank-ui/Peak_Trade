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

from src.research.offline_factor_exposure_productive_input_join_materializer_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    CANONICAL_JOIN_KEY,
    RUNTIME_EFFECT,
    SECONDARY_INTEGRITY_KEY,
    materialize_from_manifest_paths_v0,
    serialize_materialized_productive_inputs_v0,
)

AUTHORITY_EFFECT = AUTHORITY_EFFECT
RUNTIME_EFFECT = RUNTIME_EFFECT


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline factor exposure productive input join materializer v0"
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--trade-ledger", required=True, type=Path)
    parser.add_argument("--factor-snapshots", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    result = materialize_from_manifest_paths_v0(
        trade_ledger_path=args.trade_ledger,
        factor_snapshot_path=args.factor_snapshots,
    )
    serialized = serialize_materialized_productive_inputs_v0(result.records)
    (out / "productive_factor_exposure_inputs.jsonl").write_text(serialized, encoding="utf-8")
    (out / "materialization_report.json").write_text(
        json.dumps(
            {
                "status": result.status.value,
                "materialization_digest": result.materialization_digest,
                "output_digest": result.output_digest,
                "source_trade_ledger_digest": result.source_trade_ledger_digest,
                "source_factor_snapshot_digest": result.source_factor_snapshot_digest,
                "row_count_before_filter": result.join_result.row_count_before_filter,
                "row_count_after_filter": result.join_result.row_count_after_filter,
                "dropped_rows_by_reason": dict(result.join_result.dropped_rows_by_reason),
                "join_keys": {
                    "primary": CANONICAL_JOIN_KEY,
                    "secondary_integrity": SECONDARY_INTEGRITY_KEY,
                },
                "provenance": result.provenance.to_dict(),
                "authority_effect": AUTHORITY_EFFECT,
                "runtime_effect": RUNTIME_EFFECT,
                "offline_only": True,
                "repo_root": str(repo_root),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    final_report = "\n".join(
        [
            "VERDICT=OFFLINE_FACTOR_EXPOSURE_PRODUCTIVE_INPUT_JOIN_MATERIALIZATION_V0_COLLECTED",
            f"STATUS={result.status.value}",
            f"ROW_COUNT_BEFORE_JOIN={result.join_result.row_count_before_filter}",
            f"ROW_COUNT_AFTER_JOIN={result.join_result.row_count_after_filter}",
            f"DROPPED_ROWS_BY_REASON={json.dumps(result.join_result.dropped_rows_by_reason, sort_keys=True)}",
            f"OUTPUT_DIGEST={result.output_digest}",
            f"MATERIALIZATION_DIGEST={result.materialization_digest}",
            f"PRIMARY_JOIN_KEY={CANONICAL_JOIN_KEY}",
            f"SECONDARY_INTEGRITY_KEY={SECONDARY_INTEGRITY_KEY}",
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
