#!/usr/bin/env python3
"""Materialize final research fleet offline economic evaluation execution v0.

Fail-closed offline execution of ratified fleet economic evaluation for
trend_following/v1, bollinger_bands/v1, and momentum_1h/v1. No runtime or
order effect.
Operator GO: GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0
"""

from __future__ import annotations

import argparse
import json
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

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCHEMA_VERSION,
    dumps_execution_canonical_v1,
    materialize_fleet_evaluation_summary_v0,
    run_candidate_economic_evaluation_v0,
    verify_execution_start_state_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    FLEET_CANDIDATES,
    STEP31F_CONFIG_PATHS,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (  # noqa: E402
    serialize_completion_canonical_v0,
)

CONFIRM_GO = GO_TOKEN


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _die(f"ERR: not_object:{path}")
    return payload


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


def run_execution(
    *,
    confirm: str,
    binding_completion_path: Path,
    durable_evidence_root: Path,
    primary_worktree: Path,
    skip_candidate_runs: bool = False,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    primary_before = _primary_worktree_snapshot(primary_worktree)

    if not binding_completion_path.is_file():
        _die(f"ERR: missing_binding_completion:{binding_completion_path}")

    fleet_binding_completion = _load_json(binding_completion_path)
    ratification = (
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
            fleet_binding_completion=fleet_binding_completion,
        )
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        fleet_binding_completion=fleet_binding_completion,
    )
    if not start_state.valid:
        _die(f"ERR: start_state_verification_failed:{start_state.fail_reasons}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"bounded_final_research_fleet_offline_economic_evaluation_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    start_state_payload = {
        "origin_main_head": start_state.origin_main_sha,
        "expected_origin_main_head": EXPECTED_ORIGIN_MAIN_SHA,
        "pr_4800_merged": True,
        "offline_economic_evaluation_scope_ratified": True,
        "economic_evaluation_executed": False,
        "economic_validity_offline_gate_pass": False,
        "runtime_rewire_admissible": False,
        "final_research_fleet": [
            f"{strategy_id}/{version}" for strategy_id, version in FLEET_CANDIDATES
        ],
        "ratification_digest": start_state.ratification_digest,
        "fleet_binding_digest": start_state.fleet_binding_digest,
        "primary_worktree_head_before": primary_before["head"],
        "primary_worktree_dirty_before": primary_before["dirty_count"],
        "verified_at_utc": _utc_now_z(),
    }
    (evidence_dir / "START_STATE_VERIFICATION.json").write_text(
        json.dumps(start_state_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (
        evidence_dir / "final_research_fleet_offline_economic_evaluation_scope_ratification_v0.json"
    ).write_text(
        serialize_ratification_canonical_v0(ratification),
        encoding="utf-8",
    )
    (evidence_dir / "final_research_fleet_versioned_binding_completion_v0.json").write_bytes(
        binding_completion_path.read_bytes()
    )

    candidate_results = []
    run_commands: list[str] = []
    for strategy_id, strategy_version in FLEET_CANDIDATES:
        candidate_dir = (
            evidence_dir
            / "candidates"
            / f"{strategy_id}_{strategy_version}_offline_economic_evaluation_v0"
        )
        config_path = _REPO_ROOT / STEP31F_CONFIG_PATHS[strategy_id]
        if skip_candidate_runs:
            continue
        result = run_candidate_economic_evaluation_v0(
            repo_root=_REPO_ROOT,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            config_path=config_path,
            output_dir=candidate_dir,
        )
        candidate_results.append(result)
        cfg = _load_json(config_path)
        binding = cfg["real_admissible_futures_evaluation_binding_v1"]
        run_commands.append(
            "\n".join(
                [
                    f"# {strategy_id}/{strategy_version}",
                    f"cd {_REPO_ROOT}",
                    f"python3 scripts/ops/run_economic_viability_evidence_evaluation_v1.py \\",
                    f'  --dataset-path "{binding["dataset_path"]}" \\',
                    f'  --dataset-manifest-path "{Path(binding["dataset_path"]).parent / "dataset_manifest.json"}" \\',
                    f'  --config-path "{config_path.relative_to(_REPO_ROOT)}" \\',
                    f'  --output-dir "{candidate_dir}" \\',
                    "  --json",
                ]
            )
        )

    if skip_candidate_runs:
        _die("ERR: skip_candidate_runs_not_allowed_for_execution")

    fleet_summary = materialize_fleet_evaluation_summary_v0(
        ratification=ratification,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_dir),
        origin_main_sha=start_state.origin_main_sha,
    )
    summary_path = evidence_dir / "fleet_evaluation_summary_v0.json"
    summary_path.write_text(dumps_execution_canonical_v1(fleet_summary) + "\n", encoding="utf-8")

    (evidence_dir / "RUN_COMMANDS.md").write_text(
        "# RUN_COMMANDS\n\n" + "\n\n".join(run_commands) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "SCOPE_LEAK_CHECK.json").write_text(
        json.dumps(
            {
                "runtime_effect": RUNTIME_EFFECT,
                "authority_effect": AUTHORITY_EFFECT,
                "order_effect": ORDER_EFFECT,
                "network_order_path": False,
                "policy_change": False,
                "binding_change": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    fleet_rc, fleet_verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    candidate_manifest_results = {}
    for result in candidate_results:
        rc, msg = retention.verify_manifest_sha256(Path(result.output_dir))
        candidate_manifest_results[result.canonical_candidate_identifier] = {
            "manifest_verify_rc": rc,
            "manifest_verify_msg": msg,
        }

    primary_after = _primary_worktree_snapshot(primary_worktree)
    payload = {
        "verdict": "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_COMPLETE",
        "schema_version": SCHEMA_VERSION,
        "go_token": GO_TOKEN,
        "go_token_consumed": True,
        "origin_main_sha": start_state.origin_main_sha,
        "ratification_digest": start_state.ratification_digest,
        "fleet_binding_digest": start_state.fleet_binding_digest,
        "fleet_status": fleet_summary["fleet_status"],
        "pass_count": fleet_summary["pass_count"],
        "fail_count": fleet_summary["fail_count"],
        "inconclusive_count": fleet_summary["inconclusive_count"],
        "economic_evaluation_executed": True,
        "economic_validity_offline_gate_pass": fleet_summary["economic_validity_offline_gate_pass"],
        "promotion_candidates": fleet_summary["promotion_candidates"],
        "runtime_rewire_admissible": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "durable_evidence_path": str(evidence_dir),
        "fleet_manifest_verify_rc": fleet_rc,
        "fleet_manifest_verify_msg": fleet_verify_msg,
        "candidate_manifest_verify_results": candidate_manifest_results,
        "primary_worktree_head_before": primary_before["head"],
        "primary_worktree_head_after": primary_after["head"],
        "primary_worktree_dirty_before": primary_before["dirty_count"],
        "primary_worktree_dirty_after": primary_after["dirty_count"],
        "primary_worktree_mutated": (
            primary_before["head"] != primary_after["head"]
            or primary_before["dirty_count"] != primary_after["dirty_count"]
        ),
        "generated_at_utc": _utc_now_z(),
    }
    (evidence_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _emit_machine_lines(payload, fleet_summary, candidate_results)
    return payload


def _emit_machine_lines(
    payload: Mapping[str, Any],
    fleet_summary: Mapping[str, Any],
    candidate_results: list[Any],
) -> None:
    for key in (
        "verdict",
        "origin_main_sha",
        "ratification_digest",
        "fleet_status",
        "pass_count",
        "fail_count",
        "inconclusive_count",
        "economic_evaluation_executed",
        "economic_validity_offline_gate_pass",
        "fleet_manifest_verify_rc",
        "primary_worktree_mutated",
    ):
        print(f"{key.upper()}={payload.get(key)}")
    for result in candidate_results:
        field = f"CANDIDATE_RESULT_{result.strategy_id.upper()}"
        print(f"{field}={result.terminal_status.value}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize final research fleet offline economic evaluation execution v0."
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--binding-completion-path", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument(
        "--primary-worktree",
        type=Path,
        default=Path("/Users/frnkhrz/Peak_Trade"),
        help="Primary worktree path for before/after protection snapshot.",
    )
    args = parser.parse_args()
    run_execution(
        confirm=args.confirm_go_token,
        binding_completion_path=args.binding_completion_path,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
    )


if __name__ == "__main__":
    main()
