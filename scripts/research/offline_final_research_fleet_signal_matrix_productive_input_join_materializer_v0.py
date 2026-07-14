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

from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    DEFAULT_STAGING_REL,
    RUNTIME_EFFECT,
    materialize_offline_final_research_fleet_signal_matrix_v0,
    serialize_signal_matrix_rows_v0,
    write_signal_matrix_csv_v0,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Offline final research fleet signal matrix productive input join materializer v0"
        )
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--staging-root", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    staging_root = args.staging_root
    if staging_root is None:
        staging_root = (args.archive_root / DEFAULT_STAGING_REL).resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    result = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=repo_root,
        staging_root=staging_root,
    )
    write_signal_matrix_csv_v0(out / "signal_matrix.csv", result.rows)
    (out / "signal_matrix.jsonl").write_text(
        serialize_signal_matrix_rows_v0(result.rows),
        encoding="utf-8",
    )
    (out / "signal_matrix_binding.json").write_text(
        json.dumps(result.binding.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "signal_matrix_provenance.json").write_text(
        json.dumps(result.provenance.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "materialization_report.json").write_text(
        json.dumps(
            {
                "status": result.status.value,
                "materialization_digest": result.materialization_digest,
                "output_digest": result.output_digest,
                "signal_matrix_digest": result.signal_matrix_digest,
                "source_binding_digest": result.source_binding_digest,
                "row_count_before_join": result.join_result.row_count_before_filter,
                "row_count_after_join": result.join_result.row_count_after_filter,
                "dropped_rows_by_reason": dict(result.join_result.dropped_rows_by_reason),
                "per_signal_warmup_exclusion_count": dict(
                    result.join_result.per_signal_warmup_exclusion_count
                ),
                "time_range": dict(result.join_result.time_range),
                "productive_signal_binding_found": bool(result.rows),
                "signal_count": 3,
                "sample_count": len(result.rows),
                "authority_effect": AUTHORITY_EFFECT,
                "runtime_effect": RUNTIME_EFFECT,
                "offline_only": True,
                "repo_root": str(repo_root),
                "staging_root": str(staging_root),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    final_report = "\n".join(
        [
            "VERDICT=OFFLINE_FINAL_RESEARCH_FLEET_SIGNAL_MATRIX_PRODUCTIVE_INPUT_JOIN_MATERIALIZATION_V0_COLLECTED",
            f"STATUS={result.status.value}",
            f"PRODUCTIVE_SIGNAL_BINDING_FOUND={str(bool(result.rows)).lower()}",
            "SIGNAL_NAMES=trend_following,momentum_1h,bollinger_bands",
            f"SIGNAL_COUNT=3",
            f"SAMPLE_COUNT={len(result.rows)}",
            f"ROW_COUNT_BEFORE_JOIN={result.join_result.row_count_before_filter}",
            f"ROW_COUNT_AFTER_JOIN={result.join_result.row_count_after_filter}",
            f"SIGNAL_MATRIX_DIGEST={result.signal_matrix_digest}",
            f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
            f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
            "OFFLINE_ONLY=true",
            "",
        ]
    )
    (out / "final_report.txt").write_text(final_report, encoding="utf-8")
    print(final_report, end="")
    return 0 if result.rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
