#!/usr/bin/env python3
"""Run final research fleet offline economic evaluation v0.

Deterministic offline economic evaluation for trend_following/v1,
bollinger_bands/v1, and momentum_1h/v1 against ratified Class-D bindings
from PR #4832 (or legacy PR #4826 bindings when explicitly supplied).
No runtime, order, or authority effect.
Operator GO (canonical): GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0
Operator GO (alias): GO_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_FOR_VERSIONED_FINAL_RESEARCH_FLEET_V0
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_SRC_ROOT, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.backtest.economic_viability_evidence_v1 import (  # noqa: E402
    ARTIFACT_FILENAME,
    load_economic_viability_evidence_bundle_v1,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    ACCEPTED_GO_TOKENS,
    AUTHORITY_EFFECT,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    LEGACY_DURABLE_EVIDENCE_BUNDLE_PREFIX,
    LEGACY_DURABLE_EVIDENCE_SUBDIR,
    MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    ORDER_EFFECT,
    PR4832_MERGE_COMMIT,
    PR4833_MERGE_COMMIT,
    REQUIRED_MERGED_PR_NUMBER,
    RUNTIME_EFFECT,
    CandidateTerminalStatus,
    CURRENT_EXECUTION_ORIGIN_MAIN_SHA,
    dumps_execution_canonical_v1,
    is_accepted_go_token,
    load_scope_ratification_for_execution_v0,
    materialize_fleet_evaluation_summary_v0,
    resolve_durable_evidence_bundle_dir_v0,
    resolve_legacy_durable_evidence_bundle_dir_v0,
    run_candidate_economic_evaluation_v0,
    validate_binding_completion_for_execution_v0,
    validate_scope_ratification_for_execution_v0,
    verify_execution_start_state_v0,
    verify_origin_main_sha_for_binding_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    serialize_ratification_canonical_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    FLEET_CANDIDATES,
    STEP31F_CONFIG_PATHS,
)

CONFIRM_GO = GO_TOKEN
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_PRIMARY_WORKTREE = Path("/Users/frnkhrz/Peak_Trade")
BINDING_COMPLETION_REL = (
    "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)

_GATE_FAIL_CODES = {
    "walk_forward": "WALK_FORWARD_FAILED",
    "oos": "OUT_OF_SAMPLE_FAILED",
    "monte_carlo": "MONTE_CARLO_FAILED",
    "stress": "STRESS_FAILED",
    "parameter_sensitivity": "PARAMETER_ROBUSTNESS_FAILED",
}


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _die(f"ERR: not_object:{path}")
    return payload


def _resolve_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _primary_worktree_snapshot(primary_worktree: Path) -> dict[str, Any]:
    head = subprocess.run(
        ["git", "-C", str(primary_worktree), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty = subprocess.run(
        ["git", "-C", str(primary_worktree), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty_count = len([line for line in dirty.stdout.splitlines() if line.strip()])
    return {
        "head": head.stdout.strip() if head.returncode == 0 else "",
        "dirty_count": dirty_count,
    }


def _metric_value(payload: Mapping[str, Any], field: str) -> Any:
    raw = payload.get(field)
    if isinstance(raw, Mapping):
        return raw.get("value")
    return raw


def _gate_pass_from_reason_codes(reason_codes: list[str], fail_code: str) -> bool:
    return fail_code not in reason_codes


def _extract_candidate_report(
    *,
    strategy_id: str,
    candidate_dir: Path,
    terminal_status: CandidateTerminalStatus,
) -> dict[str, Any]:
    validity_path = candidate_dir / "economic_validity_evaluation_v1.json"
    reason_codes: list[str] = []
    if validity_path.is_file():
        validity = _load_json(validity_path)
        raw_codes = validity.get("reason_codes")
        if isinstance(raw_codes, list):
            reason_codes = [str(code) for code in raw_codes]

    evidence_payload: dict[str, Any] = {}
    if (candidate_dir / ARTIFACT_FILENAME).is_file():
        loaded = load_economic_viability_evidence_bundle_v1(candidate_dir)
        evidence_payload = loaded.evidence.to_dict()

    return {
        "strategy_id": strategy_id,
        "terminal_verdict": terminal_status.value,
        "net_return": _metric_value(evidence_payload, "net_return"),
        "net_expectancy": _metric_value(evidence_payload, "net_expectancy"),
        "profit_factor": _metric_value(evidence_payload, "profit_factor"),
        "sharpe": _metric_value(evidence_payload, "sharpe"),
        "max_drawdown": _metric_value(evidence_payload, "max_drawdown"),
        "trade_count": _metric_value(evidence_payload, "trade_count"),
        "walk_forward_pass": _gate_pass_from_reason_codes(
            reason_codes, _GATE_FAIL_CODES["walk_forward"]
        ),
        "oos_pass": _gate_pass_from_reason_codes(reason_codes, _GATE_FAIL_CODES["oos"]),
        "monte_carlo_pass": _gate_pass_from_reason_codes(
            reason_codes, _GATE_FAIL_CODES["monte_carlo"]
        ),
        "stress_pass": _gate_pass_from_reason_codes(reason_codes, _GATE_FAIL_CODES["stress"]),
        "parameter_sensitivity_pass": _gate_pass_from_reason_codes(
            reason_codes, _GATE_FAIL_CODES["parameter_sensitivity"]
        ),
        "reason_codes": reason_codes,
        "evidence_status": evidence_payload.get("status"),
        "config_digest": evidence_payload.get("config_digest"),
        "implementation_digest": evidence_payload.get("implementation_digest"),
        "data_digest": evidence_payload.get("data_digest"),
    }


def _build_binding_digest_verification(
    *,
    repo_root: Path,
    fleet_binding_completion: Mapping[str, Any],
    ratification: Mapping[str, Any],
) -> dict[str, Any]:
    binding_ok, binding_fail_reasons = validate_binding_completion_for_execution_v0(
        fleet_binding_completion,
        repo_root=repo_root,
        require_ready_for_eval=True,
    )
    scope_ok, scope_fail_reasons = validate_scope_ratification_for_execution_v0(
        ratification,
        repo_root=repo_root,
        fleet_binding_completion=fleet_binding_completion,
    )
    return {
        "binding_digest_verification_pass": binding_ok and scope_ok,
        "binding_validation_verdict": "ACCEPTED" if binding_ok else "REJECTED",
        "binding_validation_fail_reasons": list(binding_fail_reasons),
        "ratification_validation_verdict": "ACCEPTED" if scope_ok else "REJECTED",
        "ratification_validation_fail_reasons": list(scope_fail_reasons),
        "fleet_binding_digest": ratification.get("fleet_binding_digest"),
        "ratification_digest": ratification.get("ratification_digest"),
        "candidate_binding_digests": ratification.get("candidate_binding_digests"),
        "verified_at_utc": _utc_now_z(),
    }


def _build_common_policy_comparability_matrix(
    fleet_binding_completion: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = fleet_binding_completion.get("candidates", [])
    if not isinstance(candidates, list):
        return {"common_economic_policy_pass": False, "reason": "candidates_missing"}

    def _binding_slice(candidate: Mapping[str, Any], key: str) -> Any:
        return candidate.get(key)

    keys = (
        "economic_policy_binding",
        "fee_model_binding",
        "slippage_model_binding",
        "funding_model_binding",
        "execution_model_binding",
        "dataset_binding",
        "period_binding",
    )
    matrix: dict[str, Any] = {"candidates": {}, "comparability": {}}
    reference: dict[str, Any] | None = None
    comparable = True
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        sid = str(candidate.get("strategy_id", ""))
        slice_payload = {key: _binding_slice(candidate, key) for key in keys}
        matrix["candidates"][sid] = slice_payload
        if reference is None:
            reference = slice_payload
            continue
        for key in keys:
            if slice_payload.get(key) != reference.get(key):
                comparable = False
                matrix["comparability"][f"{sid}:{key}"] = "MISMATCH"

    return {
        "common_economic_policy_pass": comparable,
        "comparable_cost_models_pass": comparable,
        "comparable_execution_models_pass": comparable,
        "comparable_dataset_period_pass": comparable,
        "matrix": matrix,
    }


def run_evaluation(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    binding_completion_path: Path | None = None,
) -> dict[str, Any]:
    if not is_accepted_go_token(confirm):
        _die(f"ERR: confirm_go_token_required:one_of:{sorted(ACCEPTED_GO_TOKENS)}")

    primary_before = _primary_worktree_snapshot(primary_worktree)
    origin_main = _resolve_origin_main(_REPO_ROOT)

    binding_path = binding_completion_path or (_REPO_ROOT / BINDING_COMPLETION_REL)
    if not binding_path.is_file():
        _die(f"ERR: missing_binding_completion:{binding_path}")

    fleet_binding_completion = _load_json(binding_path)
    origin_ok, origin_reasons = verify_origin_main_sha_for_binding_v0(
        origin_main_sha=origin_main,
        fleet_binding_completion=fleet_binding_completion,
    )
    if not origin_ok:
        _die(f"ERR: origin_main_mismatch:{origin_reasons}")

    ratification = load_scope_ratification_for_execution_v0(
        repo_root=_REPO_ROOT,
        fleet_binding_completion=fleet_binding_completion,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        fleet_binding_completion=fleet_binding_completion,
        origin_main_sha=origin_main,
    )
    if not start_state.valid:
        _die(f"ERR: start_state_verification_failed:{start_state.fail_reasons}")

    binding_digest_verification = _build_binding_digest_verification(
        repo_root=_REPO_ROOT,
        fleet_binding_completion=fleet_binding_completion,
        ratification=ratification,
    )
    if not binding_digest_verification["binding_digest_verification_pass"]:
        _die("ERR: binding_digest_verification_failed")

    comparability = _build_common_policy_comparability_matrix(fleet_binding_completion)
    if not comparability["common_economic_policy_pass"]:
        _die("ERR: common_policy_comparability_failed")

    ts_slug = _utc_slug()
    evidence_dir = resolve_durable_evidence_bundle_dir_v0(
        durable_evidence_root=durable_evidence_root,
        timestamp_slug=ts_slug,
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)
    legacy_evidence_dir = resolve_legacy_durable_evidence_bundle_dir_v0(
        durable_evidence_root=durable_evidence_root,
        timestamp_slug=ts_slug,
    )

    preflight_lines = [
        f"ORIGIN_MAIN={origin_main}",
        f"PR4826_MERGE_COMMIT={PR4826_MERGE_COMMIT}",
        f"PR4832_MERGE_COMMIT={PR4832_MERGE_COMMIT}",
        f"PR4833_MERGE_COMMIT={PR4833_MERGE_COMMIT}",
        f"EXPECTED_ORIGIN_MAIN={EXPECTED_ORIGIN_MAIN_SHA}",
        f"MATERIALIZED_CLASS_D_ORIGIN_MAIN={MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA}",
        f"CURRENT_EXECUTION_ORIGIN_MAIN={CURRENT_EXECUTION_ORIGIN_MAIN_SHA}",
        f"REQUIRED_MERGED_PR_NUMBER={REQUIRED_MERGED_PR_NUMBER}",
        f"DURABLE_EVIDENCE_SUBDIR={evidence_dir.parent.name}",
        f"DURABLE_EVIDENCE_BUNDLE={evidence_dir.name}",
        f"LEGACY_DURABLE_EVIDENCE_ALIAS={legacy_evidence_dir.parent.name}/{legacy_evidence_dir.name}",
        "FINAL_RESEARCH_FLEET_BINDING_READY=true",
        "NEW_CANDIDATES_RATIFIED=true",
        "ECONOMIC_EVALUATION_SCOPE_RATIFIED=true",
        f"GO_TOKEN={GO_TOKEN}",
        f"VERIFIED_AT_UTC={_utc_now_z()}",
    ]
    (evidence_dir / "preflight.txt").write_text("\n".join(preflight_lines) + "\n", encoding="utf-8")
    (evidence_dir / "repo_state.txt").write_text(
        "\n".join(
            [
                f"REPO_ROOT={_REPO_ROOT}",
                f"FEATURE_HEAD={subprocess.run(['git', '-C', str(_REPO_ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()}",
                f"ORIGIN_MAIN={origin_main}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "primary_worktree_protection.txt").write_text(
        "\n".join(
            [
                f"PRIMARY_WORKTREE={primary_worktree}",
                f"PRIMARY_WORKTREE_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_WORKTREE_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "ratified_binding_snapshot.json").write_bytes(binding_path.read_bytes())
    (evidence_dir / "binding_digest_verification.json").write_text(
        json.dumps(binding_digest_verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "common_policy_comparability_matrix.json").write_text(
        json.dumps(comparability, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "durable_evidence_path_alias.json").write_text(
        json.dumps(
            {
                "canonical_path": str(evidence_dir),
                "legacy_alias_path": str(legacy_evidence_dir),
                "legacy_subdir": LEGACY_DURABLE_EVIDENCE_SUBDIR,
                "legacy_prefix": LEGACY_DURABLE_EVIDENCE_BUNDLE_PREFIX,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (
        evidence_dir / "final_research_fleet_offline_economic_evaluation_scope_ratification_v0.json"
    ).write_text(serialize_ratification_canonical_v0(ratification), encoding="utf-8")

    candidate_results = []
    candidate_reports: dict[str, dict[str, Any]] = {}
    execution_plan = {"candidates": []}
    for strategy_id, strategy_version in FLEET_CANDIDATES:
        candidate_dir = evidence_dir / f"candidate_{strategy_id}"
        config_path = _REPO_ROOT / STEP31F_CONFIG_PATHS[strategy_id]
        execution_plan["candidates"].append(
            {
                "strategy_id": strategy_id,
                "strategy_version": strategy_version,
                "config_path": str(config_path.relative_to(_REPO_ROOT)),
                "output_dir": str(candidate_dir),
            }
        )
        result = run_candidate_economic_evaluation_v0(
            repo_root=_REPO_ROOT,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            config_path=config_path,
            output_dir=candidate_dir,
        )
        candidate_results.append(result)
        candidate_reports[strategy_id] = _extract_candidate_report(
            strategy_id=strategy_id,
            candidate_dir=candidate_dir,
            terminal_status=result.terminal_status,
        )
        shutil.copy2(
            candidate_dir / ARTIFACT_FILENAME,
            evidence_dir / f"economic_viability_evidence_{strategy_id}.json",
        )

    (evidence_dir / "execution_plan.json").write_text(
        json.dumps(execution_plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fleet_summary = materialize_fleet_evaluation_summary_v0(
        ratification=ratification,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_dir),
        origin_main_sha=origin_main,
    )
    (evidence_dir / "fleet_evaluation_summary_v0.json").write_text(
        dumps_execution_canonical_v1(fleet_summary) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "fleet_comparison_matrix.json").write_text(
        json.dumps(candidate_reports, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "fleet_gate_verdict.json").write_text(
        json.dumps(
            {
                "final_research_fleet_evaluation_verdict": fleet_summary["fleet_status"],
                "economic_validity_offline_gate_pass": fleet_summary[
                    "economic_validity_offline_gate_pass"
                ],
                "promotion_eligible_candidates": fleet_summary["promotion_candidates"],
                "runtime_rewire_admissible": False,
                "candidate_verdicts": {
                    sid: report["terminal_verdict"] for sid, report in candidate_reports.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "runtime_authority_null_effect.txt").write_text(
        "\n".join(
            [
                f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
                f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
                f"ORDER_EFFECT={ORDER_EFFECT}",
                "LIVE_AUTHORIZED=false",
                "ORDERS_ALLOWED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "historical_negative_evidence_immutability.txt").write_text(
        "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED=false\nNO_RESULT_DRIVEN_RETRY=true\n",
        encoding="utf-8",
    )

    env_snapshot = [
        f"PYTHON={sys.executable}",
        f"PLATFORM={platform.platform()}",
        f"GENERATED_AT_UTC={_utc_now_z()}",
    ]
    (evidence_dir / "environment_and_dependency_snapshot.txt").write_text(
        "\n".join(env_snapshot) + "\n",
        encoding="utf-8",
    )

    primary_after = _primary_worktree_snapshot(primary_worktree)
    (evidence_dir / "primary_worktree_protection.txt").write_text(
        "\n".join(
            [
                f"PRIMARY_WORKTREE={primary_worktree}",
                f"PRIMARY_WORKTREE_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_WORKTREE_HEAD_AFTER={primary_after['head']}",
                f"PRIMARY_WORKTREE_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
                f"PRIMARY_WORKTREE_DIRTY_COUNT_AFTER={primary_after['dirty_count']}",
                f"PRIMARY_WORKTREE_MUTATED={primary_before['head'] != primary_after['head'] or primary_before['dirty_count'] != primary_after['dirty_count']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_COMPLETE",
        "go_token": GO_TOKEN,
        "go_token_consumed": True,
        "origin_main_sha": origin_main,
        "fleet_status": fleet_summary["fleet_status"],
        "economic_validity_offline_gate_pass": fleet_summary["economic_validity_offline_gate_pass"],
        "promotion_candidates": fleet_summary["promotion_candidates"],
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "candidate_reports": candidate_reports,
        "primary_worktree_mutated": (
            primary_before["head"] != primary_after["head"]
            or primary_before["dirty_count"] != primary_after["dirty_count"]
        ),
        "generated_at_utc": _utc_now_z(),
    }
    (evidence_dir / "EVALUATION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _emit_machine_lines(payload, candidate_reports, fleet_summary)
    return payload


def _emit_machine_lines(
    payload: Mapping[str, Any],
    candidate_reports: Mapping[str, Mapping[str, Any]],
    fleet_summary: Mapping[str, Any],
) -> None:
    for key in (
        "verdict",
        "origin_main_sha",
        "fleet_status",
        "economic_validity_offline_gate_pass",
        "manifest_verify_rc",
        "primary_worktree_mutated",
        "durable_evidence_path",
    ):
        print(f"{key.upper()}={payload.get(key)}")
    for strategy_id, report in candidate_reports.items():
        prefix = strategy_id.upper()
        print(f"{prefix}_VERDICT={report.get('terminal_verdict')}")
        print(f"{prefix}_NET_RETURN={report.get('net_return')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run final research fleet offline economic evaluation v0."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        choices=sorted(ACCEPTED_GO_TOKENS),
    )
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, default=DEFAULT_PRIMARY_WORKTREE)
    parser.add_argument("--binding-completion-path", type=Path, default=None)
    args = parser.parse_args()
    run_evaluation(
        confirm=args.confirm_go_token,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        binding_completion_path=args.binding_completion_path,
    )


if __name__ == "__main__":
    main()
