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
    src_s = str(_discovered_repo_root / "src")
    if src_s not in sys.path:
        sys.path.insert(0, src_s)
    if repo_s not in sys.path:
        sys.path.insert(0, repo_s)

from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (  # noqa: E402
    materialize_from_manifest_paths_v0,
    serialize_materialized_productive_inputs_v0,
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline parameter sensitivity productive input join materializer v0"
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--signal-matrix", type=Path, required=True)
    parser.add_argument("--productive-binding", type=Path, default=None)
    parser.add_argument("--strategy-id", default="trend_following")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    result = materialize_from_manifest_paths_v0(
        repo_root=repo_root,
        signal_matrix_path=args.signal_matrix,
        binding_completion_path=args.productive_binding,
        strategy_id=args.strategy_id,
    )

    inputs_path = out / "productive_parameter_sensitivity_inputs.jsonl"
    inputs_path.write_text(
        serialize_materialized_productive_inputs_v0(result.records),
        encoding="utf-8",
    )
    report = {
        "status": result.status.value,
        "materialization_digest": result.materialization_digest,
        "output_digest": result.output_digest,
        "productive_input_digest": result.productive_input_digest,
        "grid_digest": result.grid_digest,
        "source_binding_digest": result.source_binding_digest,
        "source_signal_matrix_digest": result.source_signal_matrix_digest,
        "binding": result.join_result.binding.to_dict(),
        "grid": result.join_result.grid.to_dict(),
        "grid_specs": [
            {
                "parameter_name": spec.parameter_name,
                "scaled_feature_name": spec.scaled_feature_name,
                "parameter_values": list(spec.parameter_values),
            }
            for spec in result.join_result.grid_specs
        ],
        "provenance": result.provenance.to_dict(),
        "row_count_before_filter": result.join_result.row_count_before_filter,
        "row_count_after_filter": result.join_result.row_count_after_filter,
        "dropped_rows_by_reason": dict(result.join_result.dropped_rows_by_reason),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "offline_only": True,
        "economic_evaluation_executed": False,
    }
    report_path = out / "materialization_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    final_report = "\n".join(
        [
            f"STATUS={result.status.value}",
            f"VERDICT={'PASS' if result.status.value == 'PASS' else 'FAIL_CLOSED'}",
            f"PRODUCTIVE_BINDING_FOUND={bool(result.records)}",
            f"OUTPUT_DIGEST={result.output_digest}",
            f"PRODUCTIVE_INPUT_DIGEST={result.productive_input_digest}",
            f"GRID_DIGEST={result.grid_digest}",
            f"MATERIALIZATION_DIGEST={result.materialization_digest}",
            "AUTHORITY_EFFECT=NONE",
            "RUNTIME_EFFECT=NONE",
            f"REPORT={report_path}",
        ]
    )
    (out / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")

    print(final_report)
    return 0 if result.status.value == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
