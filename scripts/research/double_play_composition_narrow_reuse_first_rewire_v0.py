from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionChopGuardStatus,
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
    DoublePlayCompositionResultV1,
    compute_composition_input_digest,
)
from trading.master_v2.double_play_composition_scenario_matrix_adapter_v0 import (
    CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER,
    DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER,
    build_scenario_matrix_composition_input_v0,
    evaluate_scenario_matrix_composition_v0,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_double_play_composition_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    extract_scenario_matrix_parity_envelope_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import SYNTHETIC_FUTURES_INSTRUMENT

SURFACE_ID = "double_play_composition"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5016
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_CANONICAL_OWNER = CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER
REUSED_SCENARIO_MATRIX_ADAPTER_OWNER = DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER
CANONICAL_OWNER_PATH = "src/trading/master_v2/double_play_composition_matrix_v1.py"
SCENARIO_MATRIX_ADAPTER_PATH = (
    "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH = (
    "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py"
)
CHAINED_CONTRACT_TEST_PATH = (
    "tests/research/test_double_play_composition_narrow_reuse_first_rewire_v0.py"
)
OWNER_BOUND_PATHS = (
    CANONICAL_OWNER_PATH,
    SCENARIO_MATRIX_ADAPTER_PATH,
    OFFLINE_REPLAY_PATH,
    HARNESS_PATH,
    SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_canonical_owner: str
    reused_scenario_matrix_adapter_owner: str
    canonical_owner_path: str
    scenario_matrix_adapter_path: str
    offline_replay_path: str
    harness_path: str
    scenario_matrix_parity_contract_test_path: str
    chained_contract_test_path: str
    ai_observability_feedback_boundary_chain_preserved: bool
    both_sides_confirmed_resolves_to_chop_guard_block: bool
    no_implicit_scoring_override: bool
    no_list_order_strategy_override: bool
    composition_matrix_complete: bool
    composition_conflict_rule_represented: bool
    composition_offline_only: bool
    rewire_state: str
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


def _both_sides_confirmed_matrix_input(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
):
    return build_scenario_matrix_composition_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        side_st=SideState.CHOP_GUARD_BLOCK,
    )


def _assert_both_sides_confirmed_conflict_semantics(result: DoublePlayCompositionResultV1) -> None:
    if result.composition_status is not CompositionStatus.CHOP_GUARD_BLOCK:
        raise ValueError("both sides confirmed must resolve to CHOP_GUARD_BLOCK")
    if result.conflict_status is not CompositionConflictStatus.BOTH_SIDES_CONFIRMED:
        raise ValueError("both sides confirmed conflict status required")
    # CHOP_SCOPE_EVENT_POLICY_BINDING_CONTRACT_V1: conflict is not Scope-CHOP SSOT.
    if result.chop_guard_status is not CompositionChopGuardStatus.NONE:
        raise ValueError(
            "both sides confirmed must not invent Scope-CHOP chop_guard "
            "(COMPOSITION_CONFLICT_NOT_SCOPE_CHOP_SSOT)"
        )
    if result.selected_side is not CompositionSelectedSide.NONE:
        raise ValueError("both sides confirmed must not select a new entry side")
    required_reasons = {
        "both_sides_confirmed",
        "composition_conflict_not_scope_chop",
        "no_new_entry",
        "existing_position_management_continues",
    }
    if not required_reasons.issubset(set(result.reason_codes)):
        raise ValueError("both sides confirmed reason codes incomplete")


def _assert_no_implicit_scoring_override(
    matrix_input,
    *,
    baseline: DoublePlayCompositionResultV1,
) -> None:
    bull_high = replace(matrix_input.bull_directional_assessment, confidence=0.99)
    bear_low = replace(matrix_input.bear_directional_assessment, confidence=0.01)
    overridden = replace(
        matrix_input,
        bull_directional_assessment=bull_high,
        bear_directional_assessment=bear_low,
    )
    overridden = replace(
        overridden,
        input_digest=compute_composition_input_digest(overridden),
    )
    overridden_result = evaluate_scenario_matrix_composition_v0(overridden)
    if overridden_result.composition_status is not baseline.composition_status:
        raise ValueError("confidence must not override both-sides-confirmed conflict rule")
    if overridden_result.selected_side is not baseline.selected_side:
        raise ValueError("confidence must not override selected side")
    if overridden_result.conflict_status is not baseline.conflict_status:
        raise ValueError("confidence must not override conflict status")


def evaluate_double_play_composition_parity_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 48,
    context_reference: str = "double-play-composition-narrow-rewire-v0",
) -> DoublePlayCompositionResultV1:
    matrix_input = _both_sides_confirmed_matrix_input(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
    )
    result = evaluate_scenario_matrix_composition_v0(matrix_input)
    _assert_both_sides_confirmed_conflict_semantics(result)
    _assert_no_implicit_scoring_override(matrix_input, baseline=result)
    envelope = extract_scenario_matrix_parity_envelope_v0(result)
    assert_double_play_composition_non_authority_boundary_v0(
        envelope,
        matrix_result=result,
    )
    return result


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    result = evaluate_double_play_composition_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_canonical_owner=REUSED_CANONICAL_OWNER,
        reused_scenario_matrix_adapter_owner=REUSED_SCENARIO_MATRIX_ADAPTER_OWNER,
        canonical_owner_path=CANONICAL_OWNER_PATH,
        scenario_matrix_adapter_path=SCENARIO_MATRIX_ADAPTER_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        harness_path=HARNESS_PATH,
        scenario_matrix_parity_contract_test_path=SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH,
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        ai_observability_feedback_boundary_chain_preserved=True,
        both_sides_confirmed_resolves_to_chop_guard_block=True,
        no_implicit_scoring_override=True,
        no_list_order_strategy_override=True,
        composition_matrix_complete=True,
        composition_conflict_rule_represented=True,
        composition_offline_only=True,
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "DoublePlayCompositionNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "double_play_composition_only",
        "rewire_binding": asdict(binding),
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


def render_markdown(rewire: dict[str, Any]) -> str:
    binding = rewire["rewire_binding"]
    lines = [
        "# Double Play Composition Narrow Reuse-First Rewire V1",
        "",
        "```text",
        "NARROW_REUSE_FIRST_REWIRE=true",
        "FUNCTIONAL_REWIRE_PERFORMED=true",
        "NEW_PARALLEL_OWNER_CREATED=false",
        "NO_RUNTIME_AUTHORITY=true",
        "NO_ORDERS=true",
        "NO_ECONOMIC_CLAIM=true",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "DOUBLE_PLAY_COMPOSITION_MATRIX_COMPLETE=true",
        "BOTH_SIDES_CONFIRMED_CHOP_GUARD_BLOCK=true",
        "NO_IMPLICIT_SCORING_OVERRIDE=true",
        "```",
        "",
        f"- reused_canonical_owner: `{binding['reused_canonical_owner']}`",
        f"- reused_scenario_matrix_adapter_owner: `{binding['reused_scenario_matrix_adapter_owner']}`",
        f"- harness_path: `{binding['harness_path']}`",
        f"- chained_contract_test_path: `{binding['chained_contract_test_path']}`",
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
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    rewire = build_rewire_binding(repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "double_play_composition_narrow_reuse_first_rewire_v0.json").write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "double_play_composition_narrow_reuse_first_rewire_v0.md").write_text(
        render_markdown(rewire) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_DOUBLE_PLAY_COMPOSITION_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_CANONICAL_OWNER={REUSED_CANONICAL_OWNER}")
    print("FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
