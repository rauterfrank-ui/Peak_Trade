"""Ratified final fleet offline economic evaluation execution v0.

Bounded offline execution for trend_following/v1, bollinger_bands/v1, and
momentum_1h/v1 after PR #4917 scope ratification, reusing Class-D materialized
bindings and canonical STEP31F economic viability owners. No runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    EconomicViabilityEvidenceError,
    load_economic_viability_evidence_bundle_v1,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    GO_TOKEN_RATIFIED_PR4917,
    ORDER_EFFECT,
    PR4917_MERGE_COMMIT,
    REASON_GO_TOKEN_INVALID,
    REASON_ORIGIN_MAIN_MISMATCH,
    RUNTIME_EFFECT,
    CandidateExecutionResultV0,
    FleetTerminalStatus,
    dumps_execution_canonical_v1,
    load_scope_ratification_for_execution_v0,
    materialize_fleet_evaluation_summary_v0,
    resolve_fleet_terminal_status_v0,
    run_candidate_economic_evaluation_v0,
    validate_binding_completion_for_execution_v0,
    verify_origin_main_sha_for_binding_v0,
    verify_unmodified_retry_admissibility_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    STEP31F_CONFIG_PATHS,
)
from src.research.post_v4_versioned_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateEconomicVerdict,
    FleetEconomicVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
)

PACKAGE_MARKER = "RATIFIED_FINAL_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

CONFIRM_GO = GO_TOKEN_RATIFIED_PR4917
PROCESS_CLASSIFICATION = "RATIFIED_FINAL_FLEET_VERSIONED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "RATIFIED_FINAL_FLEET_VERSIONED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
EVIDENCE_CLASS_ID = PROCESS_CLASSIFICATION
EXPECTED_ORIGIN_MAIN_SHA = PR4917_MERGE_COMMIT

RATIFICATION_REL = "config/research/ratify_versioned_final_fleet_bindings_and_offline_economic_evaluation_scope_v0.json"
EXECUTION_SCOPE_REL = (
    "config/research/ratified_final_fleet_offline_economic_evaluation_execution_scope_v0.json"
)
BINDING_COMPLETION_REL = (
    "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
GOVERNANCE_REL = "docs/governance/RATIFIED_FINAL_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0.md"

RATIFIED_SCOPE_FILES = (
    RATIFICATION_REL,
    "docs/governance/RATIFY_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0.md",
    "tests/ops/test_ratify_versioned_final_fleet_bindings_and_offline_evaluation_scope_v0_contract.py",
)

REUSABLE_OWNERS = (
    "scripts/run_backtest.py",
    "src/backtest/engine.py",
    "src/backtest/walkforward.py",
    "src/experiments/monte_carlo.py",
    "src/experiments/stress_tests.py",
    "src/experiments/portfolio_robustness.py",
    "src/backtest/stats.py",
    "src/experiments/evidence_chain.py",
    "src/experiments/strategy_profiles.py",
    "src/core/experiments.py",
    "scripts/ops/run_economic_viability_evidence_evaluation_v1.py",
    "src/research/final_research_fleet_offline_economic_evaluation_execution_v0.py",
)

REQUIRED_BINDINGS = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
)

BLOCKED_AUTHORITY_FLAGS = (
    "runtime_rewire_admissible",
    "live_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "scheduler_runtime_allowed",
    "orders_allowed",
    "credentials_allowed",
)

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DURABLE_EVIDENCE_SUBDIR = "implementation"
DURABLE_EVIDENCE_BUNDLE_PREFIX = "ratified_final_fleet_offline_economic_evaluation_execution"

REASON_WORKTREE_DIRTY = "WORKTREE_NOT_CLEAN"
REASON_RATIFICATION_MISSING = "PR4917_RATIFICATION_CONFIG_MISSING"
REASON_EXECUTION_SCOPE_MISSING = "EXECUTION_SCOPE_CONFIG_MISSING"
REASON_BINDING_COMPLETION_MISSING = "CLASS_D_BINDING_COMPLETION_MISSING"
REASON_RATIFICATION_FLEET_MISMATCH = "PR4917_FLEET_MISMATCH"
REASON_BINDING_FIELDS_MISSING = "REQUIRED_BINDING_FIELDS_MISSING"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    ratification: dict[str, Any]
    execution_scope: dict[str, Any]
    fleet_binding_completion: dict[str, Any]
    scope_ratification: dict[str, Any]


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    ratification: dict[str, Any]
    execution_scope: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    candidate_verdicts: dict[str, CandidateEconomicVerdict]
    fleet_verdict: FleetEconomicVerdict
    fleet_status: FleetTerminalStatus
    economic_validity_offline_gate_pass: bool
    manifest_verify_rc: int
    evidence_root: Path
    process_classification: str
    blockers: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(REASON_ORIGIN_MAIN_MISMATCH)
    return result.stdout.strip()


def _worktree_dirty_count(repo_root: Path) -> int:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return 1
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return len(lines)


def _git_status(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--short"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json_not_object:{path}")
    return payload


def verify_pr4917_ratification_v0(ratification: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    expected_fleet = ["trend_following", "bollinger_bands", "momentum_1h"]
    if list(ratification.get("final_research_fleet") or []) != expected_fleet:
        reasons.append(REASON_RATIFICATION_FLEET_MISMATCH)
    for flag in BLOCKED_AUTHORITY_FLAGS:
        if ratification.get(flag) is not False:
            reasons.append(f"AUTHORITY_FLAG_NOT_FALSE:{flag}")
    if ratification.get("offline_evaluation_scope_defined") is not True:
        reasons.append("OFFLINE_EVALUATION_SCOPE_NOT_DEFINED")
    return not reasons, tuple(reasons)


def verify_candidate_bindings_complete_v0(
    fleet_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    expected_refs = {f"{sid}/v1" for sid, _ in FLEET_CANDIDATES}
    seen: set[str] = set()
    for candidate in fleet_binding_completion.get("candidates", ()):
        if not isinstance(candidate, Mapping):
            continue
        ref = f"{candidate.get('strategy_id')}/{candidate.get('strategy_version')}"
        seen.add(ref)
        missing = [field for field in REQUIRED_BINDINGS if field not in candidate]
        if missing:
            reasons.append(f"{REASON_BINDING_FIELDS_MISSING}:{ref}:{','.join(missing)}")
    if seen != expected_refs:
        reasons.append(f"CANDIDATE_SET_MISMATCH:{sorted(seen)}")
    return not reasons, tuple(reasons)


def verify_preconditions_v0(
    *,
    repo_root: Path,
    confirm: str,
    require_clean_worktree: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if confirm != CONFIRM_GO:
        reasons.append(REASON_GO_TOKEN_INVALID)
    origin = _resolve_origin_main_sha(repo_root)
    if origin != EXPECTED_ORIGIN_MAIN_SHA:
        reasons.append(f"{REASON_ORIGIN_MAIN_MISMATCH}:{origin}")
    if require_clean_worktree and _worktree_dirty_count(repo_root) > 0:
        reasons.append(REASON_WORKTREE_DIRTY)
    for rel in (RATIFICATION_REL, EXECUTION_SCOPE_REL, BINDING_COMPLETION_REL):
        if not (repo_root / rel).is_file():
            reasons.append(f"MISSING_REQUIRED_CONFIG:{rel}")
    return not reasons, tuple(reasons)


def verify_execution_start_state_v0_ratified(
    *,
    repo_root: Path,
    durable_evidence_root: Path,
) -> StartStateVerificationResultV0:
    del durable_evidence_root  # reserved for future parent-closeout checks
    reasons: list[str] = []
    origin_main_sha = _resolve_origin_main_sha(repo_root)
    ratification = _load_json(repo_root / RATIFICATION_REL)
    execution_scope = _load_json(repo_root / EXECUTION_SCOPE_REL)
    fleet_binding_completion = _load_json(repo_root / BINDING_COMPLETION_REL)

    ok, rat_reasons = verify_pr4917_ratification_v0(ratification)
    if not ok:
        reasons.extend(rat_reasons)

    if execution_scope.get("execution_go_token") != CONFIRM_GO:
        reasons.append(REASON_GO_TOKEN_INVALID)
    if execution_scope.get("execution_performed") is True:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)

    binding_ok, binding_reasons = verify_candidate_bindings_complete_v0(fleet_binding_completion)
    if not binding_ok:
        reasons.extend(binding_reasons)

    origin_ok, origin_reasons = verify_origin_main_sha_for_binding_v0(
        origin_main_sha=origin_main_sha,
        fleet_binding_completion=fleet_binding_completion,
        repo_root=repo_root,
        live_origin_main_sha=origin_main_sha,
    )
    if not origin_ok:
        reasons.extend(origin_reasons)

    binding_exec_ok, binding_exec_reasons = validate_binding_completion_for_execution_v0(
        fleet_binding_completion,
        repo_root=repo_root,
        require_ready_for_eval=True,
    )
    if not binding_exec_ok:
        reasons.extend(binding_exec_reasons)

    scope_ratification = load_scope_ratification_for_execution_v0(
        repo_root=repo_root,
        fleet_binding_completion=fleet_binding_completion,
    )
    if scope_ratification.get("offline_economic_evaluation_scope_ratified") is not True:
        reasons.append("OFFLINE_ECONOMIC_EVALUATION_SCOPE_NOT_RATIFIED")
    candidate_refs = scope_ratification.get("candidate_refs") or []
    expected_refs = [f"{sid}/v1" for sid, _ in FLEET_CANDIDATES]
    if sorted(candidate_refs) != sorted(expected_refs):
        reasons.append("CLASS_D_SCOPE_CANDIDATE_SET_MISMATCH")

    retry_ok, retry_reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=fleet_binding_completion,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
    )
    if not retry_ok:
        reasons.extend(retry_reasons)

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main_sha,
        ratification=dict(ratification),
        execution_scope=dict(execution_scope),
        fleet_binding_completion=dict(fleet_binding_completion),
        scope_ratification=dict(scope_ratification),
    )


def _write_task_evidence_artifacts_v0(
    *,
    evidence_root: Path,
    repo_root: Path,
    start_state: StartStateVerificationResultV0,
    candidate_results: Sequence[CandidateExecutionResultV0],
    candidate_verdicts: Mapping[str, CandidateEconomicVerdict],
    fleet_verdict: FleetEconomicVerdict,
    fleet_status: FleetTerminalStatus,
    gate_pass: bool,
    command_log: Sequence[str],
    git_status_before: str,
    git_status_after: str,
    blockers: Sequence[str],
) -> None:
    (evidence_root / "BASE_HEAD.txt").write_text(
        f"{start_state.origin_main_sha}\n", encoding="utf-8"
    )
    (evidence_root / "git_status_before.txt").write_text(git_status_before, encoding="utf-8")
    (evidence_root / "git_status_after.txt").write_text(git_status_after, encoding="utf-8")
    inventory_lines = []
    for rel in RATIFIED_SCOPE_FILES:
        path = repo_root / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "MISSING"
        inventory_lines.append(f"{digest}  {rel}")
    (evidence_root / "ratified_scope_files_inventory.txt").write_text(
        "\n".join(inventory_lines) + "\n",
        encoding="utf-8",
    )
    owner_lines = []
    for rel in REUSABLE_OWNERS:
        path = repo_root / rel
        owner_lines.append(f"{'present' if path.is_file() else 'missing'}  {rel}")
    (evidence_root / "reusable_owner_inventory.txt").write_text(
        "\n".join(owner_lines) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "command_log.txt").write_text("\n".join(command_log) + "\n", encoding="utf-8")

    evaluation_results = {
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": CONFIRM_GO,
        "origin_main_sha": start_state.origin_main_sha,
        "fleet_verdict": fleet_verdict.value,
        "fleet_status": fleet_status.value,
        "economic_validity_offline_gate_pass": gate_pass,
        "candidate_verdicts": {sid: v.value for sid, v in candidate_verdicts.items()},
        "candidates": [
            {
                "strategy_id": r.strategy_id,
                "strategy_version": r.strategy_version,
                "terminal_status": r.terminal_status.value,
                "economic_validity_result": r.economic_validity_result,
                "economic_validity_offline_gate_pass": r.economic_validity_offline_gate_pass,
                "evidence_status": r.evidence_status,
                "manifest_verify_rc": r.manifest_verify_rc,
                "stage_return_codes": dict(r.stage_return_codes),
            }
            for r in candidate_results
        ],
        "blockers": list(blockers),
    }
    (evidence_root / "evaluation_results.json").write_text(
        json.dumps(evaluation_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fleet_evidence = {
        "schema_version": "economic_viability_evidence_fleet_aggregate_v1",
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "fleet_verdict": fleet_verdict.value,
        "candidate_evidence_files": [
            f"candidates/{r.strategy_id}_v1/{ARTIFACT_FILENAME}" for r in candidate_results
        ],
    }
    (evidence_root / "economic_viability_evidence_v1.json").write_text(
        json.dumps(fleet_evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary_lines = [
        "# Candidate Result Summary",
        "",
        f"- fleet_verdict: `{fleet_verdict.value}`",
        f"- fleet_status: `{fleet_status.value}`",
        f"- economic_validity_offline_gate_pass: `{gate_pass}`",
        "",
        "| candidate | terminal_status | verdict | gate_pass |",
        "|---|---|---|---|",
    ]
    for result in candidate_results:
        verdict = candidate_verdicts.get(
            result.strategy_id, CandidateEconomicVerdict.INCONCLUSIVE_EXECUTION_GAP
        )
        summary_lines.append(
            f"| `{result.strategy_id}/v1` | `{result.terminal_status.value}` | "
            f"`{verdict.value}` | `{result.economic_validity_offline_gate_pass}` |"
        )
    (evidence_root / "candidate_result_summary.md").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    blocker_lines = ["# Failure Or Blocker Matrix", ""]
    if blockers:
        blocker_lines.extend(f"- `{item}`" for item in blockers)
    else:
        blocker_lines.append("- none")
    blocker_lines.extend(["", "## Candidate stage return codes", ""])
    for result in candidate_results:
        blocker_lines.append(f"### {result.strategy_id}/v1")
        for stage, code in sorted(result.stage_return_codes.items()):
            status = (
                "PASS" if code == 0 else "BLOCKED_PRECONDITION_MISSING" if code != 0 else "PASS"
            )
            blocker_lines.append(f"- `{stage}`: rc={code} ({status})")
    (evidence_root / "failure_or_blocker_matrix.md").write_text(
        "\n".join(blocker_lines) + "\n",
        encoding="utf-8",
    )


def run_bounded_scope_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    require_clean_worktree: bool = True,
) -> ScopeExecutionResultV0:
    git_status_before = _git_status(repo_root)
    command_log: list[str] = [
        f"confirm_go_token={confirm}",
        f"repo_root={repo_root}",
        f"durable_evidence_root={durable_evidence_root}",
    ]

    pre_ok, pre_reasons = verify_preconditions_v0(
        repo_root=repo_root,
        confirm=confirm,
        require_clean_worktree=require_clean_worktree,
    )
    if not pre_ok:
        raise ValueError(f"PRECONDITION_FAILED:{pre_reasons}")

    start_state = verify_execution_start_state_v0_ratified(
        repo_root=repo_root,
        durable_evidence_root=durable_evidence_root,
    )
    if not start_state.valid:
        raise ValueError(f"START_STATE_INVALID:{start_state.fail_reasons}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / DURABLE_EVIDENCE_SUBDIR
        / f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=False)
    command_log.append(f"evidence_root={evidence_root}")

    for name, payload in (
        ("pr4917_ratification_v0.json", start_state.ratification),
        ("execution_scope_v0.json", start_state.execution_scope),
        ("class_d_binding_completion_v0.json", start_state.fleet_binding_completion),
        ("class_d_scope_ratification_v0.json", start_state.scope_ratification),
    ):
        (evidence_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    candidate_results: list[CandidateExecutionResultV0] = []
    candidate_verdicts: dict[str, CandidateEconomicVerdict] = {}

    for strategy_id, strategy_version in FLEET_CANDIDATES:
        config_path = repo_root / STEP31F_CONFIG_PATHS[strategy_id]
        candidate_dir = evidence_root / "candidates" / f"{strategy_id}_{strategy_version}"
        candidate_dir.parent.mkdir(parents=True, exist_ok=True)
        command_log.append(
            f"run_candidate_economic_evaluation_v0 strategy_id={strategy_id} "
            f"config={config_path.relative_to(repo_root)} output={candidate_dir.name}"
        )
        result = run_candidate_economic_evaluation_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            config_path=config_path,
            output_dir=candidate_dir,
        )
        candidate_results.append(result)

        evidence_payload: dict[str, Any] = {}
        if (candidate_dir / ARTIFACT_FILENAME).is_file():
            try:
                loaded = load_economic_viability_evidence_bundle_v1(candidate_dir)
                evidence_payload = loaded.evidence.to_dict()
            except EconomicViabilityEvidenceError:
                evidence_payload = {}
        candidate_verdicts[strategy_id] = classify_candidate_verdict_v0(
            result,
            evidence_payload=evidence_payload,
        )
        artifact_path = candidate_dir / ARTIFACT_FILENAME
        if artifact_path.is_file():
            shutil.copy2(
                artifact_path,
                evidence_root / f"economic_viability_evidence_{strategy_id}.json",
            )

    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    fleet_verdict = classify_fleet_verdict_v0(list(candidate_verdicts.values()))
    gate_pass = fleet_verdict is FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_PASS
    blockers = list(start_state.fail_reasons)

    fleet_summary = materialize_fleet_evaluation_summary_v0(
        ratification=start_state.scope_ratification,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_root),
        origin_main_sha=start_state.origin_main_sha,
    )
    fleet_summary["process_classification"] = PROCESS_CLASSIFICATION
    fleet_summary["scope_classification"] = SCOPE_CLASSIFICATION
    fleet_summary["go_token_consumed"] = CONFIRM_GO
    fleet_summary["evidence_class_id"] = EVIDENCE_CLASS_ID
    fleet_summary["pr4917_ratification_verdict"] = start_state.ratification.get("verdict")
    fleet_summary["fleet_verdict"] = fleet_verdict.value
    fleet_summary["candidate_verdicts"] = {
        sid: verdict.value for sid, verdict in candidate_verdicts.items()
    }
    (evidence_root / "fleet_evaluation_summary_v0.json").write_text(
        dumps_execution_canonical_v1(fleet_summary) + "\n",
        encoding="utf-8",
    )

    git_status_after = _git_status(repo_root)
    _write_task_evidence_artifacts_v0(
        evidence_root=evidence_root,
        repo_root=repo_root,
        start_state=start_state,
        candidate_results=candidate_results,
        candidate_verdicts=candidate_verdicts,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        gate_pass=gate_pass,
        command_log=command_log,
        git_status_before=git_status_before,
        git_status_after=git_status_after,
        blockers=blockers,
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    manifest_rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)

    return ScopeExecutionResultV0(
        ratification=start_state.ratification,
        execution_scope=start_state.execution_scope,
        candidate_results=tuple(candidate_results),
        candidate_verdicts=candidate_verdicts,
        fleet_verdict=fleet_verdict,
        fleet_status=fleet_status,
        economic_validity_offline_gate_pass=gate_pass,
        manifest_verify_rc=manifest_rc,
        evidence_root=evidence_root,
        process_classification=PROCESS_CLASSIFICATION,
        blockers=tuple(blockers),
    )


__all__ = [
    "CONFIRM_GO",
    "PROCESS_CLASSIFICATION",
    "SCOPE_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "EVIDENCE_CLASS_ID",
    "REUSABLE_OWNERS",
    "RATIFIED_SCOPE_FILES",
    "ScopeExecutionResultV0",
    "verify_preconditions_v0",
    "verify_execution_start_state_v0_ratified",
    "run_bounded_scope_v0",
]
