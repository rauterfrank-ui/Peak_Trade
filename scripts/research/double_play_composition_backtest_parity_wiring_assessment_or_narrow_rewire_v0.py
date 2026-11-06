from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from scripts.research.double_play_composition_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    REUSED_CANONICAL_OWNER,
    REUSED_SCENARIO_MATRIX_ADAPTER_OWNER,
    SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_double_play_composition_parity_fixtures_v0,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionConflictStatus,
    CompositionStatus,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    canonical_owner_refs_v0,
)

PLAN_TYPE = "BACKTEST_PARITY_WIRING_ASSESSMENT"
ASSESSMENT_SOURCE_PR = 5064
TRACE_ASSERTION_SOURCE_PR = 5016
TRACE_STATE = "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"

ASSESSMENT_CONTRACT_PATH = "docs/research/double_play_composition_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
ASSESSMENT_MARKDOWN_PATH = (
    "docs/research/DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0.md"
)
ASSESSMENT_CONTRACT_TEST_PATH = "tests/research/test_double_play_composition_backtest_parity_wiring_assessment_or_narrow_rewire_v0.py"
BACKTEST_CONSUMER = "src/backtest/mv2_research_wiring_v1.py"
INTEGRATED_REPLAY_PATH = "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
COMPOSITION_MATRIX_PATH = "src/trading/master_v2/double_play_composition_matrix_v1.py"
SCENARIO_ADAPTER_PATH = (
    "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
OWNER_BOUND_PATHS = (
    BACKTEST_CONSUMER,
    INTEGRATED_REPLAY_PATH,
    COMPOSITION_MATRIX_PATH,
    SCENARIO_ADAPTER_PATH,
    OFFLINE_REPLAY_PATH,
    SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
    ASSESSMENT_CONTRACT_PATH,
    ASSESSMENT_MARKDOWN_PATH,
    ASSESSMENT_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class AssessmentBinding:
    surface_id: str
    reused_canonical_owner: str
    reused_scenario_matrix_adapter_owner: str
    backtest_consumer_path: str
    integrated_replay_path: str
    composition_matrix_path: str
    scenario_adapter_path: str
    offline_replay_path: str
    scenario_matrix_parity_contract_test_path: str
    chained_contract_test_path: str
    assessment_contract_path: str
    assessment_contract_test_path: str
    double_play_composition_backtest_parity_pass: bool
    double_play_canonical_owner_reused: bool
    separate_backtest_composition_logic_found: bool
    narrow_rewire_required: bool
    narrow_rewire_implemented: bool
    both_sides_confirmed_chop_guard_block: bool
    survival_suitability_pre_composition_gates: bool
    existing_position_management_continues: bool
    no_implicit_scoring_override: bool
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
    if refs["double_play_composition_matrix"] != REUSED_CANONICAL_OWNER:
        raise ValueError("double play composition matrix owner drift")
    if refs["scenario_matrix_adapter"] != REUSED_SCENARIO_MATRIX_ADAPTER_OWNER:
        raise ValueError("double play scenario matrix adapter owner drift")


def build_assessment_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    result = evaluate_double_play_composition_parity_fixtures_v0()
    rewire = build_rewire_binding(repo_root)
    rewire_binding = rewire["rewire_binding"]
    contract = json.loads((repo_root / ASSESSMENT_CONTRACT_PATH).read_text(encoding="utf-8"))

    if result.composition_status is not CompositionStatus.CHOP_GUARD_BLOCK:
        raise ValueError("both sides confirmed fixture must resolve to CHOP_GUARD_BLOCK")
    if result.conflict_status is not CompositionConflictStatus.BOTH_SIDES_CONFIRMED:
        raise ValueError("both sides confirmed conflict status required")

    binding = AssessmentBinding(
        surface_id=SURFACE_ID,
        reused_canonical_owner=REUSED_CANONICAL_OWNER,
        reused_scenario_matrix_adapter_owner=REUSED_SCENARIO_MATRIX_ADAPTER_OWNER,
        backtest_consumer_path=BACKTEST_CONSUMER,
        integrated_replay_path=INTEGRATED_REPLAY_PATH,
        composition_matrix_path=COMPOSITION_MATRIX_PATH,
        scenario_adapter_path=SCENARIO_ADAPTER_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        scenario_matrix_parity_contract_test_path=SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH,
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        assessment_contract_path=ASSESSMENT_CONTRACT_PATH,
        assessment_contract_test_path=ASSESSMENT_CONTRACT_TEST_PATH,
        double_play_composition_backtest_parity_pass=contract[
            "double_play_composition_backtest_parity_pass"
        ],
        double_play_canonical_owner_reused=contract["double_play_canonical_owner_reused"],
        separate_backtest_composition_logic_found=contract[
            "separate_backtest_composition_logic_found"
        ],
        narrow_rewire_required=contract["narrow_rewire_required"],
        narrow_rewire_implemented=contract["narrow_rewire_implemented"],
        both_sides_confirmed_chop_guard_block=contract["both_sides_confirmed_chop_guard_block"],
        survival_suitability_pre_composition_gates=contract[
            "survival_suitability_pre_composition_gates"
        ],
        existing_position_management_continues=contract["existing_position_management_continues"],
        no_implicit_scoring_override=rewire_binding["no_implicit_scoring_override"],
        trace_state=TRACE_STATE,
        functional_rewire_performed=rewire_binding["functional_rewire_performed"],
        new_parallel_owner_created=rewire_binding["new_parallel_owner_created"],
    )
    return {
        "schema": "DoublePlayCompositionBacktestParityWiringAssessmentV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "assessment_source_pr": ASSESSMENT_SOURCE_PR,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "assessment_status": contract["assessment_status"],
        "double_play_composition_backtest_parity_status": contract[
            "double_play_composition_backtest_parity_status"
        ],
        "assessment_binding": asdict(binding),
        "composition_status": result.composition_status.value,
        "conflict_status": result.conflict_status.value,
        "reason_codes": list(result.reason_codes),
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
        "# Double Play Composition Backtest Parity Wiring Assessment V1",
        "",
        "```text",
        "DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_STATUS=ASSESSED",
        f"DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_PASS={str(binding['double_play_composition_backtest_parity_pass']).lower()}",
        f"DOUBLE_PLAY_CANONICAL_OWNER_REUSED={str(binding['double_play_canonical_owner_reused']).lower()}",
        f"SEPARATE_BACKTEST_COMPOSITION_LOGIC_FOUND={str(binding['separate_backtest_composition_logic_found']).lower()}",
        f"NARROW_REWIRE_REQUIRED={str(binding['narrow_rewire_required']).lower()}",
        f"NARROW_REWIRE_IMPLEMENTED={str(binding['narrow_rewire_implemented']).lower()}",
        "AUTHORITY_EFFECT=NONE",
        "RUNTIME_EFFECT=NONE",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "```",
        "",
        f"- reused_canonical_owner: `{binding['reused_canonical_owner']}`",
        f"- reused_scenario_matrix_adapter_owner: `{binding['reused_scenario_matrix_adapter_owner']}`",
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

    (output_dir / "double_play_composition_backtest_parity_wiring_assessment_v0.json").write_text(
        json.dumps(assessment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "double_play_composition_backtest_parity_wiring_assessment_v0.md").write_text(
        render_markdown(assessment) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(
        repo_root / ASSESSMENT_CONTRACT_PATH,
        output_dir
        / "double_play_composition_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json",
    )
    verdict = "PASS_DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)

    if args.durable_evidence_root:
        archive_root = Path(args.durable_evidence_root).resolve()
        archive_dir = (
            archive_root
            / "research"
            / "pr5065_double_play_composition_backtest_parity_wiring_assessment_v0_20260710T022900Z"
        )
        if archive_dir.exists():
            shutil.rmtree(archive_dir)
        shutil.copytree(output_dir, archive_dir)
        manifest_rc = write_manifest(archive_dir)
        (archive_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")

    print(verdict)
    print(
        "DOUBLE_PLAY_COMPOSITION_BACKTEST_PARITY_PASS="
        f"{assessment['assessment_binding']['double_play_composition_backtest_parity_pass']}"
    )
    print(
        "SEPARATE_BACKTEST_COMPOSITION_LOGIC_FOUND="
        f"{assessment['assessment_binding']['separate_backtest_composition_logic_found']}"
    )
    print(f"NARROW_REWIRE_REQUIRED={assessment['assessment_binding']['narrow_rewire_required']}")
    print(
        f"NARROW_REWIRE_IMPLEMENTED={assessment['assessment_binding']['narrow_rewire_implemented']}"
    )
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
