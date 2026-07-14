#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from research.linear_evidence.drift import (  # noqa: E402
    records_from_parameter_sensitivity_inputs,
)
from research.linear_evidence.window_robustness import (  # noqa: E402
    GO_TOKEN_REQUIRED,
    SCHEMA_VERSION,
    WindowRobustnessConfigV0,
    make_fixture_records_v0,
    make_small_fixture_records_v0,
    run_outlier_and_window_robustness_diagnostic_v0,
    semantic_payload_for_replay,
)
from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (  # noqa: E402
    MaterializationStatus,
    load_signal_matrix_rows,
    materialize_offline_parameter_sensitivity_productive_inputs_v0,
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
SCOPE = "OUTLIER_AND_WINDOW_ROBUSTNESS_DIAGNOSTIC_V0"
CANONICAL_ENTRY_POINT = "scripts/research/offline_outlier_and_window_robustness_diagnostic_v0.py"

DEFAULT_SOURCE_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/read_only_post_drift_terminal_fail_next_economic_scope_discovery_v0_20260714T151907Z"
)

DEFAULT_DRIFT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/offline_rolling_linear_drift_interpretation_reevaluation_v0_20260714T151318Z"
)

DEFAULT_SIGNAL_MATRIX = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/offline_parameter_sensitivity_surface_v0_reevaluation_20260714T140501Z/"
    "productive_signal_matrix_materialization/signal_matrix.jsonl"
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verify_source_manifest(source_path: Path) -> tuple[str, int]:
    manifest = source_path / "MANIFEST.sha256"
    if not manifest.is_file():
        return "manifest_missing", 1
    ok, reason = verify_manifest_sha256(source_path)
    return reason, 0 if ok else 1


def _owner_inventory() -> dict[str, object]:
    return {
        "rolling_drift_owner": "src/research/linear_evidence/drift.py",
        "linear_evidence_contracts_owner": "src/research/linear_evidence/contracts.py",
        "feature_matrix_owner": "src/research/linear_evidence/feature_matrix.py",
        "ols_fitter_owner": "src/research/linear_evidence/fitters.py",
        "diagnostics_owner": "src/research/linear_evidence/diagnostics.py",
        "window_robustness_owner": "src/research/linear_evidence/window_robustness.py",
        "manifest_owner": "scripts/ops/primary_evidence_retention_v0.py",
        "entry_point": CANONICAL_ENTRY_POINT,
    }


def _reuse_decision() -> dict[str, object]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "reused_owners": [
            "drift.py input records and digests",
            "feature_matrix.py binding builder",
            "fitters.py OLS lstsq and zero-variance exclusion",
            "primary_evidence_retention_v0 manifest helpers",
        ],
        "new_surface": "window_robustness.py additive diagnostic module",
        "parallel_linear_stack_created": False,
    }


def _materialize_bundle(
    out: Path,
    *,
    result: object,
    source_evidence: str,
    source_manifest_rc: int,
    input_binding: dict[str, object],
    test_results: str,
    ruff_results: str,
    boundary_guard_results: str,
    changed_files: str,
    deterministic_replay: str,
    go_token: str,
) -> int:
    out.mkdir(parents=True, exist_ok=True)
    payload = result.to_dict()
    scope_contract = {
        "scope": SCOPE,
        "schema_version": SCHEMA_VERSION,
        "go_token": go_token,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "economic_evaluation_executed": False,
        "offline_only": True,
    }

    _write_json(out / "scope_contract.json", scope_contract)
    _write_json(out / "owner_inventory.json", _owner_inventory())
    _write_json(out / "reuse_decision.json", _reuse_decision())
    _write_json(out / "input_binding.json", input_binding)
    _write_json(out / "window_plan.json", payload["window_plan"])
    _write_json(out / "feature_variance_diagnostics.json", payload["feature_variance_diagnostics"])
    _write_json(
        out / "active_feature_subset_stability.json",
        payload["active_feature_subset_stability"],
    )
    _write_json(
        out / "rank_and_conditioning_diagnostics.json",
        payload["rank_and_conditioning_diagnostics"],
    )
    _write_json(out / "ill_conditioning_attribution.json", payload["ill_conditioning_attribution"])
    _write_json(
        out / "outlier_influence_diagnostics.json", payload["outlier_influence_diagnostics"]
    )
    _write_json(out / "counterfactual_diagnostics.json", payload["counterfactual_diagnostics"])
    _write_json(
        out / "window_sufficiency_diagnostics.json", payload["window_sufficiency_diagnostics"]
    )
    _write_json(out / "window_statuses.json", payload["window_statuses"])

    (out / "preflight.txt").write_text(
        "\n".join(
            [
                "PREFLIGHT=PASS",
                f"SCOPE={SCOPE}",
                f"GO_TOKEN={go_token}",
                f"SOURCE_EVIDENCE={source_evidence}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "source_manifest_verification.txt").write_text(
        f"SOURCE_EVIDENCE={source_evidence}\nSOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}\n",
        encoding="utf-8",
    )
    (out / "deterministic_replay_verification.txt").write_text(
        deterministic_replay + "\n",
        encoding="utf-8",
    )
    (out / "changed_files.txt").write_text(changed_files + "\n", encoding="utf-8")
    (out / "test_results.txt").write_text(test_results + "\n", encoding="utf-8")
    (out / "ruff_results.txt").write_text(ruff_results + "\n", encoding="utf-8")
    (out / "boundary_guard_results.txt").write_text(boundary_guard_results + "\n", encoding="utf-8")

    w1 = next(
        (
            s
            for s in payload.get("window_statuses", {}).get("windows", [])
            if str(s.get("window_id")) == "W1"
        ),
        {},
    )
    w14 = next(
        (
            s
            for s in payload.get("window_statuses", {}).get("windows", [])
            if str(s.get("window_id")) == "W14"
        ),
        {},
    )
    final_lines = [
        f"STATUS={payload['status']}",
        f"VERDICT={payload['verdict']}",
        f"SCOPE={SCOPE}",
        f"GO_TOKEN={go_token}",
        f"CANONICAL_ENTRY_POINT={CANONICAL_ENTRY_POINT}",
        f"SOURCE_EVIDENCE={source_evidence}",
        f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
        f"W1_CLASSIFICATION={w1.get('primary_status', 'UNKNOWN')}",
        f"W14_CLASSIFICATION={w14.get('primary_status', 'UNKNOWN')}",
        f"PRIMARY_DIAGNOSTIC_CLASSIFICATION={payload['verdict']}",
        f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
        f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
        "economic_evaluation_executed=false",
        "MANIFEST_VERIFY_RC=pending",
    ]
    (out / "final_report.txt").write_text("\n".join(final_lines) + "\n", encoding="utf-8")

    write_manifest_sha256(out)
    ok, reason = verify_manifest_sha256(out)
    manifest_rc = 0 if ok else 1
    final_lines[-1] = f"MANIFEST_VERIFY_RC={manifest_rc}"
    (out / "final_report.txt").write_text("\n".join(final_lines) + "\n", encoding="utf-8")
    write_manifest_sha256(out)
    ok, reason = verify_manifest_sha256(out)
    if not ok:
        print(f"MANIFEST_VERIFY_FAILED reason={reason}", file=sys.stderr)
        return 1
    return manifest_rc


def _run_mode(
    out: Path,
    *,
    records: list,
    go_token: str,
    source_evidence: str,
    source_manifest_rc: int,
    input_binding: dict[str, object],
    config: WindowRobustnessConfigV0,
    test_results: str,
    ruff_results: str,
    boundary_guard_results: str,
    changed_files: str,
    input_mode: str,
) -> int:
    first = run_outlier_and_window_robustness_diagnostic_v0(
        records, config=config, go_token=go_token
    )
    second = run_outlier_and_window_robustness_diagnostic_v0(
        records, config=config, go_token=go_token
    )
    semantic_a = semantic_payload_for_replay(first.to_dict())
    semantic_b = semantic_payload_for_replay(second.to_dict())
    semantic_diff_empty = semantic_a == semantic_b
    deterministic_replay = "\n".join(
        [
            "RUN_A=complete",
            "RUN_B=complete",
            f"SEMANTIC_DIFF_EMPTY={str(semantic_diff_empty).lower()}",
        ]
    )

    manifest_rc = _materialize_bundle(
        out,
        result=first,
        source_evidence=source_evidence,
        source_manifest_rc=source_manifest_rc,
        input_binding=input_binding,
        test_results=test_results,
        ruff_results=ruff_results,
        boundary_guard_results=boundary_guard_results,
        changed_files=changed_files,
        deterministic_replay=deterministic_replay,
        go_token=go_token,
    )

    print(f"STATUS={first.status}")
    print(f"VERDICT={first.verdict}")
    print(f"SCOPE={SCOPE}")
    print(f"INPUT_MODE={input_mode}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print("economic_evaluation_executed=false")
    print(f"SEMANTIC_DIFF_EMPTY={str(semantic_diff_empty).lower()}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"REPORT={out / 'final_report.txt'}")
    diagnostic_complete = first.status not in {"FAIL_CLOSED"} and manifest_rc == 0
    return 0 if diagnostic_complete else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--go-token", default=None)
    parser.add_argument("--source-evidence", type=Path, default=Path(DEFAULT_SOURCE_EVIDENCE))
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--small-fixture", action="store_true")
    parser.add_argument("--signal-matrix", type=Path, default=None)
    parser.add_argument("--parameter-grid", default="trend_following")
    parser.add_argument("--window-size", type=int, default=120)
    parser.add_argument("--window-step", type=int, default=60)
    parser.add_argument("--min-samples", type=int, default=20)
    parser.add_argument("--test-results", default="not_provided")
    parser.add_argument("--ruff-results", default="not_provided")
    parser.add_argument("--boundary-guard-results", default="not_provided")
    parser.add_argument("--changed-files", default="not_provided")
    args = parser.parse_args()

    if args.go_token != GO_TOKEN_REQUIRED:
        print("STATUS=FAIL_CLOSED")
        print("VERDICT=BLOCKED_INPUT_OR_CONTRACT_FAILURE")
        print(f"REASON=GO_TOKEN_REQUIRED expected={GO_TOKEN_REQUIRED}")
        return 1

    source_path = args.source_evidence.expanduser().resolve()
    _, source_manifest_rc = _verify_source_manifest(source_path)
    if source_manifest_rc != 0:
        print("STATUS=FAIL_CLOSED")
        print("VERDICT=BLOCKED_INPUT_OR_CONTRACT_FAILURE")
        print(f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}")
        return 1

    config = WindowRobustnessConfigV0(
        base_window_size=args.window_size,
        window_step=args.window_step,
        min_samples=args.min_samples,
    )
    out = Path(args.out)

    if args.small_fixture:
        records = list(make_small_fixture_records_v0())
        input_binding = {
            "input_mode": "SMALL_FIXTURE",
            "n_records": len(records),
            "source_evidence": str(source_path),
            "drift_evidence_ref": DEFAULT_DRIFT_EVIDENCE,
        }
        return _run_mode(
            out,
            records=records,
            go_token=args.go_token,
            source_evidence=str(source_path),
            source_manifest_rc=source_manifest_rc,
            input_binding=input_binding,
            config=WindowRobustnessConfigV0(
                base_window_size=6,
                window_step=1,
                min_samples=4,
                focus_window_ids=(0, 1, 2),
                adjacent_window_sizes=(5, 6, 7),
                larger_comparison_window_sizes=(10, 12),
            ),
            test_results=args.test_results,
            ruff_results=args.ruff_results,
            boundary_guard_results=args.boundary_guard_results,
            changed_files=args.changed_files,
            input_mode="SMALL_FIXTURE",
        )

    if args.fixture:
        records = list(make_fixture_records_v0())
        input_binding = {
            "input_mode": "FIXTURE",
            "n_records": len(records),
            "source_evidence": str(source_path),
            "drift_evidence_ref": DEFAULT_DRIFT_EVIDENCE,
        }
        return _run_mode(
            out,
            records=records,
            go_token=args.go_token,
            source_evidence=str(source_path),
            source_manifest_rc=source_manifest_rc,
            input_binding=input_binding,
            config=config,
            test_results=args.test_results,
            ruff_results=args.ruff_results,
            boundary_guard_results=args.boundary_guard_results,
            changed_files=args.changed_files,
            input_mode="FIXTURE",
        )

    signal_matrix = args.signal_matrix or Path(DEFAULT_SIGNAL_MATRIX)
    signal_rows = load_signal_matrix_rows(signal_matrix)
    materialization = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=signal_rows,
        repo_root=REPO_ROOT,
        strategy_id=args.parameter_grid,
    )
    if materialization.status != MaterializationStatus.PASS:
        print("STATUS=FAIL_CLOSED")
        print("VERDICT=BLOCKED_INPUT_OR_CONTRACT_FAILURE")
        print(f"MATERIALIZATION_STATUS={materialization.status.value}")
        return 1

    records = list(records_from_parameter_sensitivity_inputs(materialization.records))
    input_binding = {
        "input_mode": "PRODUCTIVE_BINDING",
        "n_records": len(records),
        "source_evidence": str(source_path),
        "drift_evidence_ref": DEFAULT_DRIFT_EVIDENCE,
        "productive_input_digest": materialization.productive_input_digest,
        "source_signal_matrix_digest": materialization.source_signal_matrix_digest,
        "source_binding_digest": materialization.source_binding_digest,
    }
    return _run_mode(
        out,
        records=records,
        go_token=args.go_token,
        source_evidence=str(source_path),
        source_manifest_rc=source_manifest_rc,
        input_binding=input_binding,
        config=config,
        test_results=args.test_results,
        ruff_results=args.ruff_results,
        boundary_guard_results=args.boundary_guard_results,
        changed_files=args.changed_files,
        input_mode="PRODUCTIVE_BINDING",
    )


if __name__ == "__main__":
    raise SystemExit(main())
