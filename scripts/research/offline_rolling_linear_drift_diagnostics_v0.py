#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from research.linear_evidence.drift import (  # noqa: E402
    GO_TOKEN_REQUIRED,
    MODEL_SPEC_VERSION,
    SCHEMA_VERSION,
    RollingLinearDriftInputV1,
    fit_rolling_linear_drift,
    records_from_parameter_sensitivity_inputs,
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
SCOPE = "OFFLINE_ROLLING_LINEAR_DRIFT_DIAGNOSTICS_V0"
CANONICAL_ENTRY_POINT = "scripts/research/offline_rolling_linear_drift_diagnostics_v0.py"

DEFAULT_SOURCE_EVIDENCE_REFS = {
    "PR5168_MERGE_CLOSEOUT_EVIDENCE": (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/pr5168_merge_closeout_offline_diagnostic_parameter_sensitivity_model_spec_alignment_v0_20260714T142944Z"
    ),
    "ALIGNMENT_SOURCE_EVIDENCE": (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/offline_diagnostic_parameter_sensitivity_model_spec_alignment_or_bounded_extended_sampling_v0_20260714T142100Z"
    ),
    "PREVIOUS_REEVALUATION_EVIDENCE": (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/offline_parameter_sensitivity_surface_v0_reevaluation_20260714T140501Z"
    ),
    "SAMPLE_SUFFICIENCY_DIAGNOSIS_EVIDENCE": (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/read_only_parameter_sensitivity_sample_sufficiency_diagnosis_v0_20260714T141028Z"
    ),
    "POST_ALIGNMENT_REEVALUATION_EVIDENCE": (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/offline_parameter_sensitivity_surface_v0_post_alignment_reevaluation_20260714T143318Z"
    ),
}

DEFAULT_SIGNAL_MATRIX = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/offline_parameter_sensitivity_surface_v0_reevaluation_20260714T140501Z/"
    "productive_signal_matrix_materialization/signal_matrix.jsonl"
)


def _fixture_records() -> list[RollingLinearDriftInputV1]:
    records: list[RollingLinearDriftInputV1] = []
    for index in range(1, 19):
        hour = index - 1
        decision_time = f"2026-01-01T{hour:02d}:00:00Z"
        feature_time = decision_time
        signal = float(index)
        if index <= 9:
            target = 0.5 * signal + 0.1
        else:
            target = 2.5 * signal - 1.0
        records.append(
            RollingLinearDriftInputV1(
                instrument_id="PF_ETHUSD",
                decision_time=decision_time,
                feature_availability_time=feature_time,
                target=target,
                features={"signal": signal, "aux": float(index % 3)},
            )
        )
    return records


def _verify_source_manifests(
    source_refs: dict[str, str],
) -> tuple[dict[str, object], int]:
    lines: list[str] = []
    manifest_results: dict[str, int] = {}
    worst_rc = 0
    for name, path_str in sorted(source_refs.items()):
        bundle = Path(path_str)
        manifest_path = bundle / "MANIFEST.sha256"
        if not manifest_path.is_file():
            manifest_results[name] = 1
            worst_rc = 1
            lines.append(f"{name}\t{bundle}\tmanifest_present=false\tmanifest_verify_rc=1")
            continue
        ok, reason = verify_manifest_sha256(bundle)
        rc = 0 if ok else 1
        manifest_results[name] = rc
        worst_rc = max(worst_rc, rc)
        lines.append(
            f"{name}\t{bundle}\tmanifest_present=true\tmanifest_verify_rc={rc}\treason={reason}"
        )
    return {"lines": lines, "manifest_verify_rc_by_bundle": manifest_results}, worst_rc


def _build_input_parity(
    *,
    productive_input_digest: str,
    source_signal_matrix_digest: str,
    source_binding_digest: str,
    feature_matrix_digest: str,
    target_digest: str,
    config_digest: str,
    instrument_universe_digest: str,
    reference_productive_input_digest: str,
    reference_signal_matrix_digest: str,
    reference_binding_digest: str,
) -> dict[str, object]:
    productive_match = productive_input_digest == reference_productive_input_digest
    signal_match = source_signal_matrix_digest == reference_signal_matrix_digest
    binding_match = source_binding_digest == reference_binding_digest
    return {
        "productive_input_digest": productive_input_digest,
        "source_signal_matrix_digest": source_signal_matrix_digest,
        "source_binding_digest": source_binding_digest,
        "feature_matrix_digest": feature_matrix_digest,
        "target_digest": target_digest,
        "config_digest": config_digest,
        "instrument_universe_digest": instrument_universe_digest,
        "INPUT_PARITY_PROVEN": productive_match and signal_match and binding_match,
        "productive_input_digest_match": productive_match,
        "signal_matrix_digest_match": signal_match,
        "binding_digest_match": binding_match,
        "ALLOWED_MATERIAL_DIFFERENCE": "ROLLING_TIME_WINDOW_MATERIALIZATION_FOR_DRIFT_DIAGNOSTICS_V0",
        "strategy_binding_change": False,
        "signal_change": False,
        "parameter_change": False,
        "dataset_change": False,
        "universe_change": False,
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _materialize_evidence_bundle(
    out: Path,
    *,
    evidence_report: dict[str, object],
    input_parity: dict[str, object],
    source_manifest_verification: dict[str, object],
    test_results: str,
    go_token: str,
    source_evidence_refs: dict[str, str],
    window_policy: dict[str, object],
) -> int:
    out.mkdir(parents=True, exist_ok=True)

    _write_json(out / "rolling_linear_drift_diagnostics_v0.json", evidence_report)
    _write_json(
        out / "coefficient_drift_summary.json",
        {
            "coefficient_drift": evidence_report.get("coefficient_drift", {}),
            "coefficient_sign_flip_counts": evidence_report.get("coefficient_sign_flip_counts", {}),
            "coefficient_stability_metrics": evidence_report.get(
                "coefficient_stability_metrics", {}
            ),
        },
    )
    _write_json(
        out / "fit_quality_drift_summary.json", evidence_report.get("fit_quality_metrics", {})
    )
    _write_json(
        out / "residual_drift_summary.json", evidence_report.get("residual_drift_metrics", {})
    )
    _write_json(
        out / "window_coverage_summary.json",
        {
            "window_policy": window_policy,
            "window_count": evidence_report.get("window_count", 0),
            "successful_window_count": evidence_report.get("successful_window_count", 0),
            "blocked_window_count": evidence_report.get("blocked_window_count", 0),
            "insufficient_window_count": evidence_report.get("insufficient_window_count", 0),
            "rank_deficient_window_count": evidence_report.get("rank_deficient_window_count", 0),
        },
    )
    _write_json(out / "input_parity.json", input_parity)

    with (out / "rolling_window_fits.jsonl").open("w", encoding="utf-8") as handle:
        for window in evidence_report.get("window_evidence", []):
            handle.write(json.dumps(window, sort_keys=True) + "\n")

    (out / "source_manifest_verification.txt").write_text(
        "\n".join(source_manifest_verification.get("lines", [])) + "\n",
        encoding="utf-8",
    )
    (out / "test_results.txt").write_text(test_results + "\n", encoding="utf-8")

    final_report_lines = [
        f"STATUS={evidence_report.get('status')}",
        f"VERDICT={evidence_report.get('verdict')}",
        f"SCOPE={SCOPE}",
        f"GO_TOKEN={go_token}",
        f"CANONICAL_ENTRY_POINT={CANONICAL_ENTRY_POINT}",
        f"MODEL_SPEC={MODEL_SPEC_VERSION}",
        f"MANIFEST_VERIFY_RC=pending",
        f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
        f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
        f"economic_validity_offline_gate_pass=false",
        f"runtime_rewire_admissible=false",
        f"window_count={evidence_report.get('window_count', 0)}",
        f"successful_window_count={evidence_report.get('successful_window_count', 0)}",
        f"REASON_CODES={','.join(evidence_report.get('reason_codes', [])) or 'NONE'}",
    ]
    for name, path_str in sorted(source_evidence_refs.items()):
        final_report_lines.append(f"SOURCE_EVIDENCE_{name}={path_str}")
    (out / "final_report.txt").write_text("\n".join(final_report_lines) + "\n", encoding="utf-8")

    write_manifest_sha256(out)
    ok, reason = verify_manifest_sha256(out)
    manifest_rc = 0 if ok else 1
    final_report_lines[-6] = f"MANIFEST_VERIFY_RC={manifest_rc}"
    (out / "final_report.txt").write_text("\n".join(final_report_lines) + "\n", encoding="utf-8")
    write_manifest_sha256(out)
    ok, reason = verify_manifest_sha256(out)
    if not ok:
        print(f"MANIFEST_VERIFY_FAILED reason={reason}", file=sys.stderr)
        return 1
    return manifest_rc


def _run_fixture_mode(out: Path, *, go_token: str, test_results: str) -> int:
    source_manifest_verification, manifest_rc = _verify_source_manifests(
        DEFAULT_SOURCE_EVIDENCE_REFS
    )
    if manifest_rc != 0:
        print("STATUS=FAIL_CLOSED")
        print("VERDICT=FAIL_CLOSED_EVIDENCE_MANIFEST_VERIFICATION_FAILED")
        return 1

    evidence = fit_rolling_linear_drift(_fixture_records(), window_size=6, min_samples=4)
    report = evidence.to_dict()
    report.update(
        {
            "scope": SCOPE,
            "go_token": go_token,
            "canonical_entry_point": CANONICAL_ENTRY_POINT,
            "offline_only": True,
            "INPUT_MODE": "FIXTURE_SCAFFOLD",
            "source_evidence_refs": DEFAULT_SOURCE_EVIDENCE_REFS,
            "window_policy": {
                "policy": "TIME_ORDERED_SLIDING_ROWS",
                "window_size": evidence.window_size,
                "window_step": evidence.window_step,
                "min_samples": 4,
                "validation_fraction": 0.25,
                "random_split": False,
                "lookahead": False,
            },
            "time_range": {
                "start": _fixture_records()[0].decision_time,
                "end": _fixture_records()[-1].decision_time,
            },
            "row_count": evidence.n_samples,
            "target_name": evidence.target_name,
            "economic_validity_offline_gate_pass": False,
            "runtime_rewire_admissible": False,
            "promotion_pass_authority": False,
            "system_economic_evidence_admissible": False,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
        }
    )
    input_parity = _build_input_parity(
        productive_input_digest="fixture_scaffold",
        source_signal_matrix_digest="fixture_scaffold",
        source_binding_digest="fixture_scaffold",
        feature_matrix_digest=evidence.feature_matrix_digest,
        target_digest=evidence.target_digest,
        config_digest=evidence.config_digest,
        instrument_universe_digest=evidence.instrument_universe_digest,
        reference_productive_input_digest="fixture_scaffold",
        reference_signal_matrix_digest="fixture_scaffold",
        reference_binding_digest="fixture_scaffold",
    )
    manifest_rc = _materialize_evidence_bundle(
        out,
        evidence_report=report,
        input_parity=input_parity,
        source_manifest_verification=source_manifest_verification,
        test_results=test_results,
        go_token=go_token,
        source_evidence_refs=DEFAULT_SOURCE_EVIDENCE_REFS,
        window_policy=report["window_policy"],
    )
    print(f"STATUS={evidence.status}")
    print(f"VERDICT={evidence.verdict}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print("INPUT_MODE=FIXTURE_SCAFFOLD")
    print(f"DRIFT_SCORE={evidence.drift_score}")
    print(f"REASON_CODES={','.join(evidence.reason_codes) or 'NONE'}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"REPORT={out / 'rolling_linear_drift_diagnostics_v0.json'}")
    return 0 if manifest_rc == 0 else 1


def _run_productive_mode(
    out: Path,
    *,
    go_token: str,
    signal_matrix_path: Path,
    strategy_id: str,
    test_results: str,
    window_size: int,
    window_step: int,
    min_samples: int,
) -> int:
    source_manifest_verification, manifest_rc = _verify_source_manifests(
        DEFAULT_SOURCE_EVIDENCE_REFS
    )
    if manifest_rc != 0:
        print("STATUS=FAIL_CLOSED")
        print("VERDICT=FAIL_CLOSED_EVIDENCE_MANIFEST_VERIFICATION_FAILED")
        return 1

    signal_rows = load_signal_matrix_rows(signal_matrix_path)
    materialization = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=signal_rows,
        repo_root=REPO_ROOT,
        strategy_id=strategy_id,
    )
    if materialization.status != MaterializationStatus.PASS:
        print(f"STATUS=FAIL_CLOSED")
        print(f"VERDICT=FAIL_CLOSED")
        print(f"MATERIALIZATION_STATUS={materialization.status.value}")
        return 1

    drift_records = records_from_parameter_sensitivity_inputs(materialization.records)
    sorted_records = tuple(
        sorted(
            drift_records,
            key=lambda record: (record.decision_time, record.instrument_id),
        )
    )
    evidence = fit_rolling_linear_drift(
        sorted_records,
        window_size=window_size,
        window_step=window_step,
        min_samples=min_samples,
    )
    report = evidence.to_dict()
    report.update(
        {
            "scope": SCOPE,
            "go_token": go_token,
            "canonical_entry_point": CANONICAL_ENTRY_POINT,
            "offline_only": True,
            "INPUT_MODE": "PRODUCTIVE_BINDING",
            "source_evidence_refs": DEFAULT_SOURCE_EVIDENCE_REFS,
            "window_policy": {
                "policy": "TIME_ORDERED_SLIDING_ROWS",
                "window_size": window_size,
                "window_step": window_step,
                "min_samples": min_samples,
                "validation_fraction": 0.25,
                "random_split": False,
                "lookahead": False,
            },
            "time_range": {
                "start": sorted_records[0].decision_time,
                "end": sorted_records[-1].decision_time,
            },
            "row_count": evidence.n_samples,
            "target_name": evidence.target_name,
            "productive_input_digest": materialization.productive_input_digest,
            "source_signal_matrix_digest": materialization.source_signal_matrix_digest,
            "source_binding_digest": materialization.source_binding_digest,
            "economic_validity_offline_gate_pass": False,
            "runtime_rewire_admissible": False,
            "promotion_pass_authority": False,
            "system_economic_evidence_admissible": False,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
        }
    )
    reference_summary_path = (
        Path(DEFAULT_SOURCE_EVIDENCE_REFS["POST_ALIGNMENT_REEVALUATION_EVIDENCE"])
        / "execution_summary.json"
    )
    reference_summary = json.loads(reference_summary_path.read_text(encoding="utf-8"))
    input_parity = _build_input_parity(
        productive_input_digest=materialization.productive_input_digest,
        source_signal_matrix_digest=materialization.source_signal_matrix_digest,
        source_binding_digest=materialization.source_binding_digest,
        feature_matrix_digest=evidence.feature_matrix_digest,
        target_digest=evidence.target_digest,
        config_digest=evidence.config_digest,
        instrument_universe_digest=evidence.instrument_universe_digest,
        reference_productive_input_digest=str(reference_summary["productive_input_digest"]),
        reference_signal_matrix_digest=str(reference_summary["source_signal_matrix_digest"]),
        reference_binding_digest=str(reference_summary["source_binding_digest"]),
    )
    manifest_rc = _materialize_evidence_bundle(
        out,
        evidence_report=report,
        input_parity=input_parity,
        source_manifest_verification=source_manifest_verification,
        test_results=test_results,
        go_token=go_token,
        source_evidence_refs=DEFAULT_SOURCE_EVIDENCE_REFS,
        window_policy=report["window_policy"],
    )
    print(f"STATUS={evidence.status}")
    print(f"VERDICT={evidence.verdict}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print("INPUT_MODE=PRODUCTIVE_BINDING")
    print(f"PRODUCTIVE_INPUT_DIGEST={materialization.productive_input_digest}")
    print(f"INPUT_PARITY_PROVEN={input_parity['INPUT_PARITY_PROVEN']}")
    print(f"DRIFT_SCORE={evidence.drift_score}")
    print(f"REASON_CODES={','.join(evidence.reason_codes) or 'NONE'}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"REPORT={out / 'rolling_linear_drift_diagnostics_v0.json'}")
    return 0 if manifest_rc == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--go-token", default=None)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--signal-matrix", type=Path, default=None)
    parser.add_argument("--parameter-grid", default="trend_following")
    parser.add_argument("--window-size", type=int, default=120)
    parser.add_argument("--window-step", type=int, default=60)
    parser.add_argument("--min-samples", type=int, default=20)
    parser.add_argument("--test-results", default="not_provided")
    args = parser.parse_args()

    if args.go_token != GO_TOKEN_REQUIRED:
        print(f"STATUS=FAIL_CLOSED")
        print(f"VERDICT=FAIL_CLOSED")
        print(f"REASON=GO_TOKEN_REQUIRED expected={GO_TOKEN_REQUIRED}")
        return 1

    out = Path(args.out)
    productive_requested = args.signal_matrix is not None
    if args.fixture and productive_requested:
        raise SystemExit("MIXED_MODE_BLOCKED: fixture and productive modes are mutually exclusive")

    if args.fixture:
        return _run_fixture_mode(out, go_token=args.go_token, test_results=args.test_results)
    signal_matrix = args.signal_matrix or Path(DEFAULT_SIGNAL_MATRIX)
    return _run_productive_mode(
        out,
        go_token=args.go_token,
        signal_matrix_path=signal_matrix,
        strategy_id=args.parameter_grid,
        test_results=args.test_results,
        window_size=args.window_size,
        window_step=args.window_step,
        min_samples=args.min_samples,
    )


if __name__ == "__main__":
    raise SystemExit(main())
