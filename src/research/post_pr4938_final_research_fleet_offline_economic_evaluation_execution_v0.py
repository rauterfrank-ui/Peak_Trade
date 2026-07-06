"""Post-PR4938 final research fleet offline economic evaluation execution v0.

Bounded offline execution for trend_following/v1, bollinger_bands/v1, and
momentum_1h/v1 using ratified Class-D bindings from PR #4938. Reuses canonical
narrow-dataset adapter and economic viability evidence runner. No runtime authority.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops import primary_evidence_retention_v0 as retention
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
    FleetTerminalStatus,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    dumps_execution_canonical_v1,
    materialize_fleet_evaluation_summary_v0,
    resolve_fleet_terminal_status_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0 import (
    CONFIG_REL_PATH as PR4937_RATIFICATION_CONFIG_REL,
    validate_ratification_config_v0,
)
from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
    FundingCoverageReportV0,
    PanelMemberBindingV0,
    compute_funding_coverage_report_v0,
    load_panel_member_binding_v0,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    NarrowDatasetMaterializationV0,
    _load_period_policy,
    _run_candidate_with_runtime_config_v0,
    build_runtime_step31f_config_v0,
    materialize_narrow_evaluation_dataset_v0,
)

PACKAGE_MARKER = "POST_PR4938_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

CONFIRM_GO = "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_ONLY_NO_RUNTIME_AUTHORITY_V0"
PROCESS_CLASSIFICATION = "BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_ONLY"
SCOPE_CLASSIFICATION = (
    "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_AFTER_PR4938_NO_RUNTIME_AUTHORITY_V0"
)
PR4938_MERGE_COMMIT = "cd33cd097f5cae512024b9cbf15a9396ef8a1b5e"
CLASS_D_BINDING_COMPLETION_REL = (
    "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
CLASS_D_SCOPE_RATIFICATION_REL = "config/research/final_research_fleet_class_d_offline_economic_evaluation_scope_ratification_v0.json"
PR4938_CLOSEOUT_SUFFIX = (
    "final_research_fleet_bindings_and_offline_eval_scope_merge_closeout_20260706T180525Z"
)
DURABLE_EVIDENCE_BUNDLE_PREFIX = "final_research_fleet_offline_economic_evaluation_after_pr4938"


class FleetEconomicVerdict(str, Enum):
    FLEET_ECONOMIC_VALIDITY_PASS = "FLEET_ECONOMIC_VALIDITY_PASS"
    FLEET_ECONOMIC_VALIDITY_FAIL = "FLEET_ECONOMIC_VALIDITY_FAIL"
    FLEET_ECONOMIC_VALIDITY_INCONCLUSIVE = "FLEET_ECONOMIC_VALIDITY_INCONCLUSIVE"


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    fleet_status: FleetTerminalStatus
    fleet_verdict: FleetEconomicVerdict
    economic_validity_offline_gate_pass: bool
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    candidate_terminal: dict[str, str]
    evidence_root: Path
    manifest_verify_rc: int
    origin_main_sha: str
    binding_integrity: str


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _resolve_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _worktree_clean(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    allowed = {".python-version", "tests/.pytest_archive_roots/"}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path in allowed:
            continue
        return False
    return True


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _classify_fleet_verdict(status: FleetTerminalStatus) -> FleetEconomicVerdict:
    if status is FleetTerminalStatus.PASS:
        return FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_PASS
    if status is FleetTerminalStatus.INCONCLUSIVE:
        return FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_INCONCLUSIVE
    return FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_FAIL


def _origin_main_is_at_least(repo_root: Path, minimum_sha: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", minimum_sha, "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _verify_panel_preconditions_v0(
    staging_root: Path,
) -> tuple[bool, tuple[str, ...], PanelMemberBindingV0 | None, FundingCoverageReportV0]:
    reasons: list[str] = []
    panel_binding: PanelMemberBindingV0 | None = None
    coverage = FundingCoverageReportV0(
        row_count_total=0,
        missing_funding_count=0,
        populated_funding_count=0,
        coverage_ratio=0.0,
        fetched_from_okx_public=None,
        instrument_count=0,
        manifest_verified=False,
    )
    if not staging_root.is_dir():
        reasons.append("STAGING_MISSING")
    else:
        try:
            panel_binding = load_panel_member_binding_v0(staging_root)
        except FileNotFoundError as exc:
            reasons.append(str(exc))
        coverage = compute_funding_coverage_report_v0(staging_root)
        if coverage.coverage_ratio < 1.0 or coverage.missing_funding_count > 0:
            reasons.append("FAIL_CLOSED_DATASET_OR_FUNDING_COVERAGE_INCOMPLETE")
    return not reasons, tuple(reasons), panel_binding, coverage


def verify_binding_integrity_v0(
    *, repo_root: Path
) -> tuple[bool, str, dict[str, Any], dict[str, Any]]:
    ratification = _load_json(repo_root / PR4937_RATIFICATION_CONFIG_REL)
    validation = validate_ratification_config_v0(ratification, repo_root=repo_root)
    if not validation.valid:
        return False, "RATIFICATION_CONFIG_INVALID", ratification, {}

    binding_completion = _load_json(repo_root / CLASS_D_BINDING_COMPLETION_REL)
    expected_digest = str(ratification.get("expected_binding_completion_digest", ""))
    actual_digest = str(binding_completion.get("completion_digest", ""))
    if expected_digest != actual_digest:
        return False, "BINDING_COMPLETION_DIGEST_MISMATCH", ratification, binding_completion

    pr4937_closeout_dir = Path(ratification["parent_closeout_dir"])
    if not pr4937_closeout_dir.is_dir():
        return False, "PR4937_PARENT_CLOSEOUT_MISSING", ratification, binding_completion
    ok, _msg = retention.verify_manifest_sha256(pr4937_closeout_dir)
    if not ok:
        return False, "PR4937_PARENT_CLOSEOUT_MANIFEST_INVALID", ratification, binding_completion

    pr4938_closeout_dir = DEFAULT_DURABLE_ARCHIVE_ROOT / "research" / PR4938_CLOSEOUT_SUFFIX
    if not pr4938_closeout_dir.is_dir():
        return False, "PR4938_CLOSEOUT_MISSING", ratification, binding_completion
    ok, _msg = retention.verify_manifest_sha256(pr4938_closeout_dir)
    if not ok:
        return False, "PR4938_CLOSEOUT_MANIFEST_INVALID", ratification, binding_completion

    return True, "BINDING_INTEGRITY_PASS", ratification, binding_completion


def run_bounded_scope_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path = DEFAULT_DURABLE_ARCHIVE_ROOT,
) -> ScopeExecutionResultV0:
    if confirm != CONFIRM_GO:
        raise ValueError(f"GO_TOKEN_INVALID:{confirm}")

    if not _worktree_clean(repo_root):
        raise ValueError("WORKTREE_NOT_CLEAN")

    origin_main = _resolve_origin_main(repo_root)
    if not origin_main:
        raise ValueError("ORIGIN_MAIN_RESOLVE_FAILED")
    if not _origin_main_is_at_least(repo_root, PR4938_MERGE_COMMIT):
        raise ValueError(f"ORIGIN_MAIN_TOO_OLD:{origin_main}")

    integrity_ok, integrity_status, ratification, binding_completion = verify_binding_integrity_v0(
        repo_root=repo_root
    )
    if not integrity_ok:
        raise ValueError(f"BINDING_INTEGRITY_FAILED:{integrity_status}")

    staging_root = Path(
        binding_completion["candidates"][0]["dataset_binding"]["panel_staging_root"]
    )
    ok, reasons, _panel_binding, _coverage = _verify_panel_preconditions_v0(staging_root)
    if not ok:
        raise ValueError(f"PRECONDITION_FAILED:{reasons}")

    ts_slug = _utc_slug()
    evidence_root = (
        durable_evidence_root / "research" / f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=False)

    narrow_root = evidence_root / "narrow_evaluation_dataset" / "inst-eth-usdt-perp" / "v1"
    period_policy = _load_period_policy(repo_root)
    narrow_dataset: NarrowDatasetMaterializationV0 = materialize_narrow_evaluation_dataset_v0(
        staging_root=staging_root,
        output_root=narrow_root,
        period_policy=period_policy,
    )

    scope_ratification = _load_json(repo_root / CLASS_D_SCOPE_RATIFICATION_REL)
    runtime_config_paths: dict[str, Path] = {}
    config_dir = evidence_root / "RUNTIME_STEP31F_CONFIGS"
    for strategy_id, _strategy_version in FLEET_CANDIDATES:
        runtime_config_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=config_dir / f"step31f_{strategy_id}_v1_economic_evaluation_v1.json",
        )

    (evidence_root / "ratification_config_snapshot.json").write_text(
        json.dumps(ratification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "binding_completion_snapshot.json").write_text(
        json.dumps(binding_completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "scope_ratification_snapshot.json").write_text(
        json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "EXECUTION_BOUNDARY.md").write_text(
        "\n".join(
            [
                "# Execution Boundary",
                "",
                f"- go_token: `{CONFIRM_GO}`",
                f"- origin_main: `{origin_main}`",
                f"- pr4938_merge_commit: `{PR4938_MERGE_COMMIT}`",
                f"- binding_integrity: `{integrity_status}`",
                f"- evaluation_executed: `true`",
                f"- runtime_authority_touched: `false`",
                f"- promotion_granted: `false`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    candidate_results: list[CandidateExecutionResultV0] = []
    for strategy_id, strategy_version in FLEET_CANDIDATES:
        config_path = runtime_config_paths[strategy_id]
        output_dir = evidence_root / "candidates" / f"{strategy_id}_{strategy_version}"
        result = _run_candidate_with_runtime_config_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            config_path=config_path,
            output_dir=output_dir,
        )
        candidate_results.append(result)

    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    fleet_verdict = _classify_fleet_verdict(fleet_status)
    gate_pass = fleet_status is FleetTerminalStatus.PASS and all(
        r.economic_validity_offline_gate_pass for r in candidate_results
    )

    fleet_summary = materialize_fleet_evaluation_summary_v0(
        ratification=scope_ratification,
        candidate_results=candidate_results,
        execution_bundle_dir=str(evidence_root),
        origin_main_sha=origin_main,
    )
    (evidence_root / "fleet_evaluation_summary_v0.json").write_text(
        dumps_execution_canonical_v1(fleet_summary) + "\n",
        encoding="utf-8",
    )

    candidate_terminal = {r.strategy_id: r.terminal_status.value for r in candidate_results}
    (evidence_root / "candidate_terminal_verdicts.json").write_text(
        json.dumps(candidate_terminal, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    final_report_lines = [
        f"VERDICT={fleet_verdict.value}",
        f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
        f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
        "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
        f"BASE_HEAD={origin_main}",
        f"ORIGIN_MAIN={origin_main}",
        "WORKTREE_STATUS=clean",
        "FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h",
        f"BINDING_INTEGRITY={integrity_status}",
        "EVALUATION_EXECUTED=true",
        "RUNTIME_AUTHORITY_TOUCHED=false",
        "PROMOTION_GRANTED=false",
        f"CANDIDATE_RESULTS={json.dumps(candidate_terminal, sort_keys=True)}",
        f"AGGREGATE_FLEET_VERDICT={fleet_verdict.value}",
        f"DURABLE_EVIDENCE_DIR={evidence_root}",
        f"FLEET_STATUS={fleet_status.value}",
        f"ECONOMIC_VALIDITY_OFFLINE_GATE_PASS={gate_pass}",
        f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
        f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
        f"ORDER_EFFECT={ORDER_EFFECT}",
    ]
    (evidence_root / "FINAL_REPORT.md").write_text(
        "\n".join(final_report_lines) + "\n",
        encoding="utf-8",
    )

    manifest_rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)

    return ScopeExecutionResultV0(
        fleet_status=fleet_status,
        fleet_verdict=fleet_verdict,
        economic_validity_offline_gate_pass=gate_pass,
        candidate_results=tuple(candidate_results),
        candidate_terminal=candidate_terminal,
        evidence_root=evidence_root,
        manifest_verify_rc=manifest_rc,
        origin_main_sha=origin_main,
        binding_integrity=integrity_status,
    )


__all__ = [
    "CONFIRM_GO",
    "DEFAULT_DURABLE_ARCHIVE_ROOT",
    "PROCESS_CLASSIFICATION",
    "SCOPE_CLASSIFICATION",
    "PR4938_MERGE_COMMIT",
    "run_bounded_scope_v0",
    "ScopeExecutionResultV0",
    "verify_binding_integrity_v0",
]
