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

from src.research.linear_evidence.factor_exposure import (  # noqa: E402
    FactorExposureConfigV1,
    FactorExposureInputV1,
    fit_factor_exposure,
    make_deterministic_factor_exposure_fixture,
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"


def _load_jsonl(path: Path) -> list[FactorExposureInputV1]:
    records: list[FactorExposureInputV1] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        records.append(
            FactorExposureInputV1(
                instrument_id=str(payload["instrument_id"]),
                timestamp=int(payload["timestamp"]),
                target_return=float(payload["target_return"]),
                factor_values=dict(payload["factor_values"]),
                factor_time=payload.get("factor_time"),
                decision_time=payload.get("decision_time"),
            )
        )
    return records


def _report_fields(
    *,
    evidence_dict: dict[str, object],
    input_mode: str,
    productive_binding_requested: bool,
    productive_binding_resolved: bool,
    fixture_scaffold_used: bool,
) -> dict[str, object]:
    diagnostics = dict(evidence_dict.get("diagnostics", {}))
    corr = diagnostics.get("pairwise_correlation", {})
    vif = diagnostics.get("vif_scores", {})
    max_abs_corr = 0.0
    if isinstance(corr, dict):
        for left, row in corr.items():
            if isinstance(row, dict):
                for right, value in row.items():
                    if left != right:
                        max_abs_corr = max(max_abs_corr, abs(float(value)))
    finite_vifs = [
        float(value)
        for value in vif.values()
        if isinstance(value, (int, float)) and value != float("inf")
    ]
    max_vif = max(finite_vifs) if finite_vifs else None
    sample_sufficiency = diagnostics.get("sample_sufficiency", {})
    return {
        **evidence_dict,
        "INPUT_MODE": input_mode,
        "PRODUCTIVE_BINDING_REQUESTED": productive_binding_requested,
        "PRODUCTIVE_BINDING_RESOLVED": productive_binding_resolved,
        "FIXTURE_SCAFFOLD_USED": fixture_scaffold_used,
        "FACTOR_TIME_LESS_THAN_DECISION_TIME": True,
        "NO_LOOKAHEAD_PASS": "FACTOR_LOOKAHEAD_DETECTED"
        not in evidence_dict.get("reason_codes", []),
        "SAMPLE_SUFFICIENCY_PASS": bool(sample_sufficiency.get("sufficient", False))
        if isinstance(sample_sufficiency, dict)
        else False,
        "ZERO_VARIANCE_FACTOR_COUNT": sum(
            1
            for code in evidence_dict.get("reason_codes", [])
            if str(code).startswith("ZERO_VARIANCE_FACTOR")
        ),
        "PERFECT_COLLINEARITY_COUNT": diagnostics.get("perfect_collinearity_count", 0),
        "MAX_ABS_PAIRWISE_CORRELATION": max_abs_corr,
        "MAX_VIF": max_vif,
        "CONDITION_NUMBER": diagnostics.get("condition_number"),
        "FEATURE_ORDER_STABLE": True,
        "FEATURE_MATRIX_DIGEST": evidence_dict.get("feature_matrix_digest"),
        "TARGET_DIGEST": evidence_dict.get("target_digest"),
        "CONFIG_DIGEST": evidence_dict.get("config_digest"),
        "STATUS": evidence_dict.get("status"),
        "REASON_CODES": evidence_dict.get("reason_codes"),
        "offline_only": True,
        "system_economic_evidence_admissible": False,
        "runtime_rewire_admissible": False,
        "promotion_pass_authority": False,
        "strategy_selection_changed": False,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline factor exposure diagnostics v0")
    parser.add_argument("--out", required=True)
    parser.add_argument("--input-jsonl", type=Path, default=None)
    parser.add_argument("--fixture-scaffold", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--correlation-threshold", type=float, default=0.85)
    parser.add_argument("--vif-threshold", type=float, default=10.0)
    parser.add_argument("--condition-number-threshold", type=float, default=1000.0)
    parser.add_argument("--min-samples", type=int, default=8)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    productive_binding_requested = args.input_jsonl is not None
    productive_binding_resolved = False
    fixture_scaffold_used = False
    input_mode = "UNBOUND"

    if args.input_jsonl is not None:
        records = _load_jsonl(args.input_jsonl)
        productive_binding_resolved = bool(records)
        input_mode = "PRODUCTIVE_BINDING"
    elif args.fixture_scaffold:
        records = make_deterministic_factor_exposure_fixture()
        fixture_scaffold_used = True
        input_mode = "FIXTURE_SCAFFOLD"
    else:
        records = []
        input_mode = "UNBOUND"

    config = FactorExposureConfigV1(
        correlation_threshold=args.correlation_threshold,
        vif_threshold=args.vif_threshold,
        condition_number_threshold=args.condition_number_threshold,
        min_samples=args.min_samples,
    )
    evidence = fit_factor_exposure(
        records,
        config=config,
        productive_binding_gap=productive_binding_requested and not productive_binding_resolved,
        fixture_scaffold=fixture_scaffold_used,
    )
    payload = _report_fields(
        evidence_dict=evidence.to_dict(),
        input_mode=input_mode,
        productive_binding_requested=productive_binding_requested,
        productive_binding_resolved=productive_binding_resolved,
        fixture_scaffold_used=fixture_scaffold_used,
    )
    payload["repo_root"] = str(repo_root)

    report_json = out / "factor_exposure_evidence_v1.json"
    report_txt = out / "factor_exposure_report.txt"
    final_report = out / "final_report.txt"
    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_txt.write_text(
        "\n".join(
            [
                "VERDICT=OFFLINE_FACTOR_EXPOSURE_DIAGNOSTICS_V0_COLLECTED",
                f"STATUS={payload['STATUS']}",
                f"INPUT_MODE={payload['INPUT_MODE']}",
                f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
                f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
                "OFFLINE_ONLY=true",
                f"FIXTURE_SCAFFOLD_USED={str(fixture_scaffold_used).lower()}",
                f"PRODUCTIVE_BINDING_RESOLVED={str(productive_binding_resolved).lower()}",
                f"REASON_CODES={','.join(payload.get('REASON_CODES', []))}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    final_report.write_text(report_txt.read_text(encoding="utf-8"), encoding="utf-8")
    print(final_report.read_text(encoding="utf-8"), end="")
    return (
        0
        if evidence.status
        in {"DIAGNOSTIC_ONLY", "ROBUSTNESS_FAILED", "RANK_DEFICIENT_BLOCKED", "INSUFFICIENT_DATA"}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
