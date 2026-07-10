from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from scripts.research.entry_position_exit_policy_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    ENTRY_EXIT_CONTRACT_TEST_PATH,
    FLAT_BEFORE_CONTRACT_TEST_PATH,
    REUSED_CANONICAL_OWNER,
    REUSED_ENTRY_EXIT_ADAPTER_OWNER,
    REUSED_FLAT_BEFORE_ADAPTER_OWNER,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_entry_position_exit_policy_parity_fixtures_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    canonical_owner_refs_v0,
)

PLAN_TYPE = "BACKTEST_PARITY_WIRING_ASSESSMENT"
ASSESSMENT_SOURCE_PR = 5065
TRACE_ASSERTION_SOURCE_PR = 5010
TRACE_STATE = "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"

ASSESSMENT_CONTRACT_PATH = "docs/research/entry_position_exit_policy_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
ASSESSMENT_MARKDOWN_PATH = "docs/research/ENTRY_POSITION_EXIT_POLICY_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0.md"
ASSESSMENT_CONTRACT_TEST_PATH = "tests/research/test_entry_position_exit_policy_backtest_parity_wiring_assessment_or_narrow_rewire_v0.py"
BACKTEST_CONSUMER = "src/backtest/mv2_research_wiring_v1.py"
INTEGRATED_REPLAY_PATH = "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
ENTRY_EXIT_POLICY_PATH = "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
ENTRY_EXIT_ADAPTER_PATH = (
    "src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py"
)
FLAT_BEFORE_ADAPTER_PATH = (
    "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
OWNER_BOUND_PATHS = (
    BACKTEST_CONSUMER,
    INTEGRATED_REPLAY_PATH,
    ENTRY_EXIT_POLICY_PATH,
    ENTRY_EXIT_ADAPTER_PATH,
    FLAT_BEFORE_ADAPTER_PATH,
    OFFLINE_REPLAY_PATH,
    ENTRY_EXIT_CONTRACT_TEST_PATH,
    FLAT_BEFORE_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
    ASSESSMENT_CONTRACT_PATH,
    ASSESSMENT_MARKDOWN_PATH,
    ASSESSMENT_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class AssessmentBinding:
    surface_id: str
    reused_canonical_owner: str
    reused_entry_exit_adapter_owner: str
    reused_flat_before_adapter_owner: str
    backtest_consumer_path: str
    integrated_replay_path: str
    entry_exit_policy_path: str
    entry_exit_adapter_path: str
    flat_before_adapter_path: str
    offline_replay_path: str
    entry_exit_contract_test_path: str
    flat_before_contract_test_path: str
    chained_contract_test_path: str
    assessment_contract_path: str
    assessment_contract_test_path: str
    entry_policy_backtest_parity_pass: bool
    position_management_backtest_parity_pass: bool
    exit_policy_backtest_parity_pass: bool
    narrow_rewire_required: bool
    narrow_rewire_performed: bool
    partial_fill_semantics_status: str
    reduce_only_invariant_status: str
    position_flip_forbidden_status: str
    trace_state: str
    functional_rewire_performed: bool
    new_parallel_owner_created: bool


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_owner_bound_paths_exist(repo_root: Path) -> None:
    for rel in OWNER_BOUND_PATHS:
        if not (repo_root / rel).is_file():
            raise ValueError(f"owner-bound path missing: {rel}")


def _assert_canonical_owner_reuse() -> None:
    refs = canonical_owner_refs_v0()
    if refs["entry_exit_policy"] != REUSED_CANONICAL_OWNER:
        raise ValueError("entry-exit policy owner drift")
    if refs["entry_exit_scenario_binding_adapter"] != REUSED_ENTRY_EXIT_ADAPTER_OWNER:
        raise ValueError("entry-exit scenario binding adapter owner drift")
    if (
        refs["flat_before_opposite_side_scenario_binding_adapter"]
        != REUSED_FLAT_BEFORE_ADAPTER_OWNER
    ):
        raise ValueError("flat-before-opposite-side adapter owner drift")


def build_assessment_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    decision = evaluate_entry_position_exit_policy_parity_fixtures_v0()
    rewire = build_rewire_binding(repo_root)
    rewire_binding = rewire["rewire_binding"]
    contract = json.loads((repo_root / ASSESSMENT_CONTRACT_PATH).read_text(encoding="utf-8"))

    if decision.decision_outcome in (DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT):
        raise ValueError("fixture must block opposite entry while position not flat")

    binding = AssessmentBinding(
        surface_id=SURFACE_ID,
        reused_canonical_owner=REUSED_CANONICAL_OWNER,
        reused_entry_exit_adapter_owner=REUSED_ENTRY_EXIT_ADAPTER_OWNER,
        reused_flat_before_adapter_owner=REUSED_FLAT_BEFORE_ADAPTER_OWNER,
        backtest_consumer_path=BACKTEST_CONSUMER,
        integrated_replay_path=INTEGRATED_REPLAY_PATH,
        entry_exit_policy_path=ENTRY_EXIT_POLICY_PATH,
        entry_exit_adapter_path=ENTRY_EXIT_ADAPTER_PATH,
        flat_before_adapter_path=FLAT_BEFORE_ADAPTER_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        entry_exit_contract_test_path=ENTRY_EXIT_CONTRACT_TEST_PATH,
        flat_before_contract_test_path=FLAT_BEFORE_CONTRACT_TEST_PATH,
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        assessment_contract_path=ASSESSMENT_CONTRACT_PATH,
        assessment_contract_test_path=ASSESSMENT_CONTRACT_TEST_PATH,
        entry_policy_backtest_parity_pass=contract["entry_policy_backtest_parity_pass"],
        position_management_backtest_parity_pass=contract[
            "position_management_backtest_parity_pass"
        ],
        exit_policy_backtest_parity_pass=contract["exit_policy_backtest_parity_pass"],
        narrow_rewire_required=contract["narrow_rewire_required"],
        narrow_rewire_performed=contract["narrow_rewire_performed"],
        partial_fill_semantics_status=contract["partial_fill_semantics_status"],
        reduce_only_invariant_status=contract["reduce_only_invariant_status"],
        position_flip_forbidden_status=contract["position_flip_forbidden_status"],
        trace_state=TRACE_STATE,
        functional_rewire_performed=rewire_binding["functional_rewire_performed"],
        new_parallel_owner_created=rewire_binding["new_parallel_owner_created"],
    )
    return {
        "schema": "EntryPositionExitPolicyBacktestParityWiringAssessmentV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "assessment_source_pr": ASSESSMENT_SOURCE_PR,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "assessment_status": contract["assessment_status"],
        "entry_policy_backtest_parity_status": contract["entry_policy_backtest_parity_status"],
        "position_management_backtest_parity_status": contract[
            "position_management_backtest_parity_status"
        ],
        "exit_policy_backtest_parity_status": contract["exit_policy_backtest_parity_status"],
        "assessment_binding": asdict(binding),
        "decision_outcome": decision.decision_outcome.value,
        "position_flip_allowed": decision.position_flip_allowed,
        "source_evidence_referenced": contract["source_evidence_referenced"],
        "source_evidence_not_referenced": contract["source_evidence_not_referenced"],
        "source_manifest_verify_rc": contract["source_manifest_verify_rc"],
        "forbidden_claims_remain_false": {
            "FULL_CANONICAL_CHAIN_WIRED": False,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": False,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
            "RUNTIME_AUTHORITY": False,
            "ORDERS_ALLOWED": False,
            "ECONOMIC_CLAIM": False,
        },
        **NO_AUTHORITY_FLAGS,
    }


def render_markdown(assessment: dict[str, Any]) -> str:
    binding = assessment["assessment_binding"]
    lines = [
        "# Entry Position Exit Policy Backtest Parity Wiring Assessment V1",
        "",
        "```text",
        "ENTRY_POLICY_BACKTEST_PARITY_STATUS=ASSESSED",
        f"ENTRY_POLICY_BACKTEST_PARITY_PASS={str(binding['entry_policy_backtest_parity_pass']).lower()}",
        f"POSITION_MANAGEMENT_BACKTEST_PARITY_PASS={str(binding['position_management_backtest_parity_pass']).lower()}",
        f"EXIT_POLICY_BACKTEST_PARITY_PASS={str(binding['exit_policy_backtest_parity_pass']).lower()}",
        f"NARROW_REWIRE_REQUIRED={str(binding['narrow_rewire_required']).lower()}",
        f"NARROW_REWIRE_PERFORMED={str(binding['narrow_rewire_performed']).lower()}",
        "AUTHORITY_EFFECT=NONE",
        "RUNTIME_EFFECT=NONE",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "```",
        "",
        f"- reused_canonical_owner: `{binding['reused_canonical_owner']}`",
        f"- reused_entry_exit_adapter_owner: `{binding['reused_entry_exit_adapter_owner']}`",
        f"- reused_flat_before_adapter_owner: `{binding['reused_flat_before_adapter_owner']}`",
        f"- assessment_contract_path: `{binding['assessment_contract_path']}`",
        "",
    ]
    return "\n".join(lines)


def write_manifest(output_dir: Path) -> int:
    rows: list[str] = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rows.append(f"{_sha256(path)}  {path.relative_to(output_dir).as_posix()}")
    (output_dir / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")
    for row in rows:
        digest, rel = row.split("  ", 1)
        if _sha256(output_dir / rel) != digest:
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--durable-evidence-root", default=None)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    assessment = build_assessment_binding(repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    (
        output_dir / "entry_position_exit_policy_backtest_parity_wiring_assessment_v0.json"
    ).write_text(json.dumps(assessment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "entry_position_exit_policy_backtest_parity_wiring_assessment_v0.md").write_text(
        render_markdown(assessment) + "\n", encoding="utf-8"
    )
    shutil.copy2(
        repo_root / ASSESSMENT_CONTRACT_PATH,
        output_dir
        / "entry_position_exit_policy_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json",
    )
    verdict = (
        "PASS_ENTRY_POSITION_EXIT_POLICY_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0"
    )
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)

    if args.durable_evidence_root:
        archive_root = Path(args.durable_evidence_root).resolve()
        archive_dir = (
            archive_root
            / "research"
            / "entry_position_exit_policy_backtest_parity_wiring_assessment_or_narrow_rewire_v0_20260710T024500Z"
        )
        if archive_dir.exists():
            shutil.rmtree(archive_dir)
        shutil.copytree(output_dir, archive_dir)
        manifest_rc = write_manifest(archive_dir)
        (archive_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")

    print(verdict)
    print(
        "ENTRY_POLICY_BACKTEST_PARITY_PASS="
        f"{assessment['assessment_binding']['entry_policy_backtest_parity_pass']}"
    )
    print(f"NARROW_REWIRE_REQUIRED={assessment['assessment_binding']['narrow_rewire_required']}")
    print(f"NARROW_REWIRE_PERFORMED={assessment['assessment_binding']['narrow_rewire_performed']}")
    print(f"SOURCE_EVIDENCE_REFERENCED={assessment['source_evidence_referenced']}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
