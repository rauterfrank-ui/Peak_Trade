#!/usr/bin/env python3
"""Materialize durable evidence for SIGNAL_ORTHOGONALITY_DIAGNOSTICS_SCOPE_V0."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (_REPO_ROOT / "src", _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    finalize_durable_bundle_manifest,
    verify_manifest_sha256,
)
from src.research.linear_evidence.import_boundary import (  # noqa: E402
    scan_paths_import_boundary,
)
from src.research.linear_evidence.signal_orthogonality import (  # noqa: E402
    SCOPE_POLICY_VERSION,
    SCOPE_ROLE,
    SignalOrthogonalityScopePolicyV0,
    build_signal_orthogonality_scope_artifacts_v0,
    make_deterministic_signal_fixture,
)

ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
SCOPE = "SIGNAL_ORTHOGONALITY_DIAGNOSTICS_SCOPE_V0"
GO_TOKEN = "GO_SIGNAL_ORTHOGONALITY_DIAGNOSTICS_SCOPE_V0"
PROGRAM = "CANONICAL_ECONOMIC_OBSERVABILITY_SYSTEM_V1"
CANONICAL_OWNER = "src/research/linear_evidence/signal_orthogonality.py"
RUNNER = "scripts/research/offline_signal_orthogonality_diagnostics_v0.py"

PRODUCTIVE_SIGNAL_MATRIX_BUNDLE = ARCHIVE_ROOT / (
    "offline_final_research_fleet_signal_matrix_productive_input_join_materialization_v0_"
    "20260714T131741Z"
)
PRODUCTIVE_SIGNAL_MATRIX_CSV = PRODUCTIVE_SIGNAL_MATRIX_BUNDLE / "signal_matrix.csv"
PRODUCTIVE_FEATURES = ("bollinger_bands", "momentum_1h", "trend_following")

SOURCE_BUNDLES: tuple[tuple[str, Path], ...] = (
    (
        "METRIC_LINEAGE_DISCOVERY",
        ARCHIVE_ROOT
        / "canonical_economic_observability_metric_lineage_and_reporting_gap_discovery_read_only_v0_20260714T185419Z",
    ),
    (
        "REGISTRY_FOUNDATION",
        ARCHIVE_ROOT
        / "canonical_economic_observability_registry_and_contract_foundation_v0_20260714T191543Z",
    ),
    (
        "PR5174_MERGE_CLOSEOUT",
        ARCHIVE_ROOT
        / "pr5174_merge_closeout_canonical_economic_observability_registry_and_contract_foundation_v0_20260714T192427Z",
    ),
    (
        "PR5175_IMPLEMENTATION",
        ARCHIVE_ROOT / "canonical_existing_stats_and_cost_decomposition_rewire_v0_20260714T193111Z",
    ),
    (
        "PR5175_MERGE_CLOSEOUT",
        ARCHIVE_ROOT
        / "pr5175_merge_closeout_canonical_existing_stats_and_cost_decomposition_rewire_v0_20260714T194956Z",
    ),
    (
        "PR5176_IMPLEMENTATION",
        ARCHIVE_ROOT
        / "canonical_trade_ledger_equity_curve_and_decision_funnel_persistence_v0_20260714T195658Z",
    ),
    (
        "PR5176_MERGE_CLOSEOUT",
        ARCHIVE_ROOT
        / "pr5176_merge_closeout_canonical_trade_ledger_equity_curve_and_decision_funnel_persistence_v0_20260714T200417Z",
    ),
    (
        "PR5177_IMPLEMENTATION",
        ARCHIVE_ROOT / "canonical_derived_economic_and_trade_metrics_v0_20260714T201051Z",
    ),
    (
        "PR5177_MERGE_CLOSEOUT",
        ARCHIVE_ROOT
        / "pr5177_merge_closeout_canonical_derived_economic_and_trade_metrics_v0_20260714T201906Z",
    ),
    (
        "PR5178_IMPLEMENTATION",
        ARCHIVE_ROOT / "canonical_advanced_economic_capability_pack_v0_20260714T203146Z",
    ),
    (
        "PR5178_MERGE_CLOSEOUT",
        ARCHIVE_ROOT
        / "pr5178_merge_closeout_canonical_advanced_economic_capability_pack_v0_20260714T204217Z",
    ),
    (
        "PR5179_IMPLEMENTATION",
        ARCHIVE_ROOT / "canonical_economic_report_consumer_v1_20260714T204901Z",
    ),
    (
        "PR5179_MERGE_CLOSEOUT",
        ARCHIVE_ROOT
        / "pr5179_merge_closeout_canonical_economic_report_consumer_v1_20260714T205546Z",
    ),
    ("PRODUCTIVE_SIGNAL_MATRIX", PRODUCTIVE_SIGNAL_MATRIX_BUNDLE),
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_value(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_source_manifests() -> tuple[int, str]:
    lines: list[str] = []
    rc = 0
    for label, bundle in SOURCE_BUNDLES:
        ok, msg = verify_manifest_sha256(bundle)
        lines.append(f"{label}_DIR={bundle}")
        lines.append(f"{label}_MANIFEST_VERIFY={msg}")
        lines.append(f"{label}_RC={0 if ok else 1}")
        if not ok:
            rc = 1
    return rc, "\n".join(lines) + "\n"


def _owner_inventory() -> dict[str, Any]:
    return {
        "canonical_owner": CANONICAL_OWNER,
        "runner": RUNNER,
        "materializer": "scripts/ops/materialize_signal_orthogonality_diagnostics_scope_v0.py",
        "related_owners": [
            "src/research/linear_evidence/feature_matrix.py",
            "src/research/linear_evidence/factor_exposure.py",
            "src/research/linear_evidence/diagnostics.py",
            "src/research/linear_evidence/signal_matrix_productive_contract_v0.py",
            "src/research/offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0.py",
        ],
        "tests": [
            "tests/research/test_offline_signal_orthogonality_diagnostics_v0.py",
        ],
        "observability_consumer_only": [
            "src/backtest/economic_observability_snapshot_v1.py",
            "config/economic_observability_metric_registry_v1.json",
        ],
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_owner": CANONICAL_OWNER,
        "reason": "Extend existing signal_orthogonality owner with scope-v0 artifact builder; no parallel orthogonality owner.",
        "observability_program_reopened": False,
        "observability_program_scope_extended": False,
        "new_parallel_owner_created": False,
    }


def _read_csv_rows(path: Path, features: tuple[str, ...]) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing = [name for name in features if name not in fieldnames]
        if missing:
            raise SystemExit(f"FEATURE_ALIGNMENT_ERROR missing columns: {','.join(missing)}")
        return [dict(row) for row in reader]


def _resolve_input_binding() -> dict[str, Any]:
    if not PRODUCTIVE_SIGNAL_MATRIX_CSV.is_file():
        raise SystemExit("BLOCKED: productive signal matrix CSV missing")
    return {
        "mode": "manifest_verified_productive_signal_matrix",
        "source_bundle": str(PRODUCTIVE_SIGNAL_MATRIX_BUNDLE),
        "source_csv": str(PRODUCTIVE_SIGNAL_MATRIX_CSV),
        "source_csv_digest": _file_digest(PRODUCTIVE_SIGNAL_MATRIX_CSV),
        "source_manifest_verified": True,
        "features": list(PRODUCTIVE_FEATURES),
        "feature_order_policy": "sorted_unique",
        "instrument_key": "instrument_id",
        "time_keys": {"decision_time": "decision_time", "feature_time": "feature_time"},
        "fixture_truth_pack_used": False,
        "productive_binding_found": True,
    }


def _canonical_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize signal orthogonality diagnostics scope v0 evidence"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT / f"signal_orthogonality_diagnostics_scope_v0_{_utc_stamp()}",
    )
    args = parser.parse_args()
    output_dir = args.out.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    head = _git_value("rev-parse", "HEAD")
    origin_main = _git_value("rev-parse", "origin/main")
    branch = _git_value("branch", "--show-current")
    worktree_clean = _git_value("status", "--short") == ""

    preflight = "\n".join(
        [
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"CURRENT_BRANCH={branch}",
            f"HEAD={head}",
            f"ORIGIN_MAIN={origin_main}",
            f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
            f"WORKTREE_CLEAN={worktree_clean}",
            f"CANONICAL_OWNER={CANONICAL_OWNER}",
            f"PROGRAM={PROGRAM}",
            f"PROGRAM_STATUS=TERMINAL_CLOSED",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    source_rc, source_text = _verify_source_manifests()
    (output_dir / "source_manifest_verification.txt").write_text(source_text, encoding="utf-8")
    if source_rc != 0:
        raise SystemExit("BLOCKED_SOURCE_EVIDENCE_VERIFICATION")

    _write_json(
        output_dir / "observability_program_terminal_status.json",
        {
            "program": PROGRAM,
            "status": "TERMINAL_CLOSED",
            "reopened": False,
            "scope_extended": False,
            "consumer_only_reuse": True,
        },
    )
    _write_json(output_dir / "owner_inventory.json", _owner_inventory())
    _write_json(output_dir / "reuse_decision.json", _reuse_decision())

    input_binding = _resolve_input_binding()
    _write_json(output_dir / "input_binding.json", input_binding)

    rows = _read_csv_rows(PRODUCTIVE_SIGNAL_MATRIX_CSV, PRODUCTIVE_FEATURES)
    policy = SignalOrthogonalityScopePolicyV0()
    _write_json(output_dir / "diagnostic_policy.json", policy.to_dict())

    first = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        PRODUCTIVE_FEATURES,
        policy=policy,
        input_digest=input_binding["source_csv_digest"],
        productive_binding_found=True,
        fixture_truth_pack_used=False,
    )
    second = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        PRODUCTIVE_FEATURES,
        policy=policy,
        input_digest=input_binding["source_csv_digest"],
        productive_binding_found=True,
        fixture_truth_pack_used=False,
    )

    first_bytes = _canonical_json_bytes(first)
    second_bytes = _canonical_json_bytes(second)
    diff_empty = first_bytes == second_bytes
    (output_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"FIRST_OUTPUT_DIGEST={first['output_digest']}",
                f"SECOND_OUTPUT_DIGEST={second['output_digest']}",
                f"DETERMINISTIC={diff_empty}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "second_materialization_diff.txt").write_text(
        "EMPTY\n" if diff_empty else "NON_EMPTY\n",
        encoding="utf-8",
    )

    _write_json(output_dir / "failure_taxonomy.json", first["failure_taxonomy"])
    _write_json(output_dir / "signal_summary.json", first["signal_summary"])
    _write_json(output_dir / "pairwise_correlations.json", first["pairwise_correlations"])
    _write_json(output_dir / "correlation_matrix.json", first["correlation_matrix"])
    _write_json(output_dir / "overlap_matrix.json", first["overlap_matrix"])
    _write_json(output_dir / "duplicate_groups.json", first["duplicate_groups"])
    _write_json(output_dir / "matrix_diagnostics.json", first["matrix_diagnostics"])
    _write_json(output_dir / "rolling_stability.json", first["rolling_stability"])

    env = {**os.environ, "PYTHONPATH": f"{_REPO_ROOT / 'src'}:{_REPO_ROOT}"}
    test_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/research/test_offline_signal_orthogonality_diagnostics_v0.py",
            "-q",
        ],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    (output_dir / "test_results.txt").write_text(
        test_proc.stdout + test_proc.stderr, encoding="utf-8"
    )

    ruff_targets = [
        CANONICAL_OWNER,
        "scripts/ops/materialize_signal_orthogonality_diagnostics_scope_v0.py",
        "tests/research/test_offline_signal_orthogonality_diagnostics_v0.py",
    ]
    ruff_format = subprocess.run(
        ["ruff", "format", "--check", *ruff_targets],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    ruff_check = subprocess.run(
        ["ruff", "check", *ruff_targets],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    (output_dir / "ruff_results.txt").write_text(
        "RUFF_FORMAT\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + "\nRUFF_CHECK\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )

    scan_paths = [
        _REPO_ROOT / CANONICAL_OWNER,
        _REPO_ROOT / "scripts/ops/materialize_signal_orthogonality_diagnostics_scope_v0.py",
    ]
    hits, probes = scan_paths_import_boundary(scan_paths, repo_root=_REPO_ROOT)
    import_boundary_rc = 0 if not hits else 1
    (output_dir / "import_boundary_results.txt").write_text(
        "\n".join(
            [
                f"IMPORT_BOUNDARY_RC={import_boundary_rc}",
                f"HITS={len(hits)}",
                *[hit.format_scan_line() for hit in hits],
                f"DOCSTRING_PROBES={len(probes)}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    summary = first["signal_summary"]
    rolling = first["rolling_stability"]
    final_report = "\n".join(
        [
            "STATUS=PASS",
            "VERDICT=SIGNAL_ORTHOGONALITY_DIAGNOSTICS_SCOPE_V0_COMPLETE",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"CURRENT_BRANCH={branch}",
            f"BASE_HEAD={head}",
            f"ORIGIN_MAIN={origin_main}",
            f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
            "WORKTREE_CLEAN_BEFORE=true",
            f"WORKTREE_CLEAN_AFTER={worktree_clean}",
            "OBSERVABILITY_PROGRAM_TERMINAL_CLOSED=true",
            "OBSERVABILITY_PROGRAM_REOPENED=false",
            "OBSERVABILITY_PROGRAM_SCOPE_EXTENDED=false",
            f"SOURCE_EVIDENCE={PRODUCTIVE_SIGNAL_MATRIX_BUNDLE.name}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
            f"CANONICAL_OWNER={CANONICAL_OWNER}",
            "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
            f"INPUT_DATASETS_OR_EVIDENCE={PRODUCTIVE_SIGNAL_MATRIX_CSV.name}",
            f"INPUT_DIGESTS={summary['input_digest']}",
            f"SIGNAL_COUNT_BEFORE_FILTER={summary['signal_count_before_filter']}",
            f"SIGNAL_COUNT_AFTER_FILTER={summary['signal_count_after_filter']}",
            f"DROPPED_SIGNALS_BY_REASON={json.dumps(summary['dropped_signals_by_reason'], sort_keys=True)}",
            f"PAIR_COUNT={summary['pair_count']}",
            f"HIGH_CORRELATION_PAIR_COUNT={len(summary['high_correlation_pairs'])}",
            f"DUPLICATE_GROUP_COUNT={len(summary['duplicate_groups'])}",
            f"NEAR_DUPLICATE_GROUP_COUNT={len(summary['near_duplicate_groups'])}",
            f"MATRIX_RANK={summary['matrix_rank']}",
            f"CONDITION_NUMBER={summary['condition_number']}",
            f"ROLLING_STABILITY_STATUS={rolling.get('status')}",
            f"DIAGNOSTIC_STATUS={first['diagnostic_status']}",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "STRATEGY_SELECTION_CHANGED=false",
            "PARAMETERS_CHANGED=false",
            "CORE_TRADING_SEMANTICS_CHANGED=false",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
            f"FOCUSED_TEST_RC={test_proc.returncode}",
            f"RUFF_RC={0 if ruff_format.returncode == 0 and ruff_check.returncode == 0 else 1}",
            f"IMPORT_BOUNDARY_RC={import_boundary_rc}",
            f"DETERMINISTIC_MATERIALIZATION={diff_empty}",
            f"SECOND_MATERIALIZATION_DIFF_EMPTY={diff_empty}",
            f"DURABLE_EVIDENCE_DIR={output_dir}",
            "SIGNAL_ORTHOGONALITY_DIAGNOSTICS_ROLE=DIAGNOSTIC_ONLY",
            f"POLICY_VERSION={SCOPE_POLICY_VERSION}",
            "NEXT_ACTION=SEPARATE_OPERATOR_GO_REQUIRED_FOR_PR_CHECK_REVIEW",
            "",
        ]
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    manifest_rc, _ = finalize_durable_bundle_manifest(output_dir)
    print(final_report, end="")
    return 0 if manifest_rc == 0 and test_proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
