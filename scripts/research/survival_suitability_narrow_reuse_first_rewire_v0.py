from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_state import SideState, TransitionDecision
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_survival_suitability_non_authority_boundary_v0,
    canonical_owner_refs_v0,
    extract_survival_suitability_parity_envelope_v0,
)
from trading.master_v2.double_play_suitability import project_strategy_suitability
from trading.master_v2.double_play_survival import evaluate_survival_envelope
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    _survival_envelope,
    _suitability_input,
)
from trading.master_v2.survival_assessment_v1 import (
    SurvivalAssessmentStatus,
    SurvivalHardFailReason,
    SurvivalMetricInputsV1,
)
from trading.master_v2.survival_suitability_scenario_binding_adapter_v0 import (
    CANONICAL_SUITABILITY_BINDING_OWNER,
    CANONICAL_SURVIVAL_ASSESSMENT_OWNER,
    SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioSurvivalSuitabilityEvaluationV0,
    ScenarioSurvivalSuitabilityOverridesV0,
    apply_canonical_survival_suitability_pre_matrix_gates_v0,
    canonical_survival_blocks_entry_v0,
    evaluate_scenario_survival_suitability_v0,
)
from trading.master_v2.suitability_binding_v1 import (
    SuitabilityBindingStatus,
    SuitabilityRegimeStatus,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
)

SURFACE_ID = "survival_and_suitability"
PLAN_TYPE = "NARROW_REUSE_FIRST_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5017
REWIRE_STATE = "REWIRE_BOUND_OFFLINE_PARITY_PATH"

REUSED_SURVIVAL_ASSESSMENT_OWNER = CANONICAL_SURVIVAL_ASSESSMENT_OWNER
REUSED_SUITABILITY_BINDING_OWNER = CANONICAL_SUITABILITY_BINDING_OWNER
REUSED_SCENARIO_BINDING_ADAPTER_OWNER = SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER
CANONICAL_SURVIVAL_OWNER_PATH = "src/trading/master_v2/survival_assessment_v1.py"
CANONICAL_SUITABILITY_OWNER_PATH = "src/trading/master_v2/suitability_binding_v1.py"
LEGACY_SURVIVAL_ENVELOPE_PATH = "src/trading/master_v2/double_play_survival.py"
LEGACY_SUITABILITY_PROJECTION_PATH = "src/trading/master_v2/double_play_suitability.py"
SCENARIO_BINDING_ADAPTER_PATH = (
    "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py"
)
OFFLINE_REPLAY_PATH = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
HARNESS_PATH = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py"
)
SCENARIO_REPLAY_CONTRACT_TEST_PATH = "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py"
CHAINED_CONTRACT_TEST_PATH = (
    "tests/research/test_survival_suitability_narrow_reuse_first_rewire_v0.py"
)
OWNER_BOUND_PATHS = (
    CANONICAL_SURVIVAL_OWNER_PATH,
    CANONICAL_SUITABILITY_OWNER_PATH,
    SCENARIO_BINDING_ADAPTER_PATH,
    OFFLINE_REPLAY_PATH,
    HARNESS_PATH,
    SCENARIO_REPLAY_CONTRACT_TEST_PATH,
    CHAINED_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_survival_assessment_owner: str
    reused_suitability_binding_owner: str
    reused_scenario_binding_adapter_owner: str
    canonical_survival_owner_path: str
    canonical_suitability_owner_path: str
    legacy_survival_envelope_path: str
    legacy_suitability_projection_path: str
    scenario_binding_adapter_path: str
    offline_replay_path: str
    harness_path: str
    scenario_replay_contract_test_path: str
    chained_contract_test_path: str
    double_play_composition_chain_preserved: bool
    survival_hard_fail_blocks_composition: bool
    survival_required_unknown_fail_closed: bool
    suitability_deterministic_strategy_selection: bool
    no_list_order_strategy_override: bool
    no_confidence_only_selection: bool
    cost_model_boundary_bound: bool
    regime_owner_boundary_bound: bool
    survival_suitability_offline_only: bool
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
    if refs["survival_assessment"] != REUSED_SURVIVAL_ASSESSMENT_OWNER:
        raise ValueError("survival assessment owner drift")
    if refs["suitability_binding"] != REUSED_SUITABILITY_BINDING_OWNER:
        raise ValueError("suitability binding owner drift")
    if refs["survival_suitability_scenario_binding_adapter"] != (
        REUSED_SCENARIO_BINDING_ADAPTER_OWNER
    ):
        raise ValueError("survival suitability scenario binding adapter owner drift")


def _composition_input(*, requested: RequestedSide) -> DoublePlayCompositionInput:
    return DoublePlayCompositionInput(
        transition=TransitionDecision(
            allowed=True,
            reason_code="TEST",
            live_authorization_granted=False,
        ),
        resulting_side_state=SideState.LONG_ACTIVE,
        survival=evaluate_survival_envelope(_survival_envelope()),
        suitability=project_strategy_suitability(_suitability_input()),
        requested_side=requested,
    )


def _assert_survival_hard_fail_blocks(evaluation: ScenarioSurvivalSuitabilityEvaluationV0) -> None:
    if not canonical_survival_blocks_entry_v0(evaluation.bull_survival):
        raise ValueError("survival hard fail must block entry")
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    if decision is None or decision.status is not DoublePlayCompositionStatus.BLOCKED:
        raise ValueError("survival hard fail must block composition")


def _assert_survival_required_unknown_blocks(
    evaluation: ScenarioSurvivalSuitabilityEvaluationV0,
) -> None:
    if evaluation.bull_survival.status is not SurvivalAssessmentStatus.BLOCKED:
        raise ValueError("required unknown survival inputs must yield BLOCKED")
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    if decision is None or decision.status is not DoublePlayCompositionStatus.BLOCKED:
        raise ValueError("survival required unknown must block composition fail-closed")


def _strategy_entry(
    *,
    strategy_id: str,
    priority_rank: int,
    confidence_score: float,
) -> SuitabilityStrategyEntryV1:
    return SuitabilityStrategyEntryV1(
        strategy_id=strategy_id,
        supported_regime_ids=("trending",),
        supported_sides=(DirectionalAssessmentSide.LONG,),
        priority_rank=priority_rank,
        disabled=False,
        confidence_score=confidence_score,
    )


def _assert_deterministic_strategy_selection(
    *,
    instrument_id: str,
    trading_epoch: int,
) -> None:
    registry_ab = SuitabilityStrategyRegistryV1(
        entries=(
            _strategy_entry(strategy_id="strat-a", priority_rank=10, confidence_score=0.99),
            _strategy_entry(strategy_id="strat-b", priority_rank=10, confidence_score=0.01),
        )
    )
    registry_ba = SuitabilityStrategyRegistryV1(
        entries=(
            _strategy_entry(strategy_id="strat-b", priority_rank=10, confidence_score=0.99),
            _strategy_entry(strategy_id="strat-a", priority_rank=10, confidence_score=0.01),
        )
    )
    eval_ab = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=SideState.LONG_ACTIVE,
        overrides=ScenarioSurvivalSuitabilityOverridesV0(strategy_registry=registry_ab),
    )
    eval_ba = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=SideState.LONG_ACTIVE,
        overrides=ScenarioSurvivalSuitabilityOverridesV0(strategy_registry=registry_ba),
    )
    if eval_ab.bull_suitability.selected_strategy_id != "strat-a":
        raise ValueError("deterministic selection must prefer priority_rank then strategy_id")
    if eval_ba.bull_suitability.selected_strategy_id != "strat-a":
        raise ValueError("list order must not override deterministic strategy selection")
    if (
        eval_ab.bull_suitability.selected_strategy_id
        != eval_ba.bull_suitability.selected_strategy_id
    ):
        raise ValueError("registry list order must not change selected strategy")


def _assert_regime_unknown_blocks(
    *,
    instrument_id: str,
    trading_epoch: int,
) -> None:
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=SideState.LONG_ACTIVE,
        overrides=ScenarioSurvivalSuitabilityOverridesV0(
            regime_status=SuitabilityRegimeStatus.UNKNOWN,
        ),
    )
    if evaluation.bull_suitability.status is not SuitabilityBindingStatus.BLOCKED:
        raise ValueError("unknown regime must block suitability fail-closed")
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    if decision is None or decision.status is not DoublePlayCompositionStatus.BLOCKED:
        raise ValueError("unknown regime must block composition")


def _assert_cost_model_boundary_bound(evaluation: ScenarioSurvivalSuitabilityEvaluationV0) -> None:
    if evaluation.bull_survival.cost_survival_result is None:
        raise ValueError("cost model boundary must be represented in survival assessment")
    if evaluation.bull_survival.expected_roundtrip_cost is None:
        raise ValueError("cost model boundary must expose roundtrip cost evidence")


def evaluate_survival_suitability_parity_fixtures_v0(
    *,
    instrument_id: str = SYNTHETIC_FUTURES_INSTRUMENT,
    trading_epoch: int = 61,
    context_reference: str = "survival-suitability-narrow-rewire-v0",
) -> ScenarioSurvivalSuitabilityEvaluationV0:
    del context_reference
    hard_fail_overrides = ScenarioSurvivalSuitabilityOverridesV0(
        bull_survival_status=SurvivalAssessmentStatus.FAIL,
        bull_explicit_hard_fail_reasons=(SurvivalHardFailReason.EXPLICIT_HARD_FAIL,),
    )
    hard_fail_eval = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=SideState.LONG_ACTIVE,
        overrides=hard_fail_overrides,
    )
    _assert_survival_hard_fail_blocks(hard_fail_eval)

    unknown_metrics = SurvivalMetricInputsV1(
        data_completeness_complete=None,
        volatility_survival_ratio=0.8,
        sequence_survival_ratio=0.8,
        drawdown_survival_ratio=0.8,
        liquidation_buffer_ratio=0.2,
    )
    unknown_eval = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=SideState.LONG_ACTIVE,
        overrides=ScenarioSurvivalSuitabilityOverridesV0(
            bull_metric_inputs=unknown_metrics,
            bear_metric_inputs=unknown_metrics,
        ),
    )
    _assert_survival_required_unknown_blocks(unknown_eval)

    _assert_deterministic_strategy_selection(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
    )
    _assert_regime_unknown_blocks(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
    )

    baseline = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=SideState.LONG_ACTIVE,
    )
    _assert_cost_model_boundary_bound(baseline)

    envelope = extract_survival_suitability_parity_envelope_v0(baseline)
    assert_survival_suitability_non_authority_boundary_v0(envelope, evaluation=baseline)
    return baseline


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    result = evaluate_survival_suitability_parity_fixtures_v0()
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_survival_assessment_owner=REUSED_SURVIVAL_ASSESSMENT_OWNER,
        reused_suitability_binding_owner=REUSED_SUITABILITY_BINDING_OWNER,
        reused_scenario_binding_adapter_owner=REUSED_SCENARIO_BINDING_ADAPTER_OWNER,
        canonical_survival_owner_path=CANONICAL_SURVIVAL_OWNER_PATH,
        canonical_suitability_owner_path=CANONICAL_SUITABILITY_OWNER_PATH,
        legacy_survival_envelope_path=LEGACY_SURVIVAL_ENVELOPE_PATH,
        legacy_suitability_projection_path=LEGACY_SUITABILITY_PROJECTION_PATH,
        scenario_binding_adapter_path=SCENARIO_BINDING_ADAPTER_PATH,
        offline_replay_path=OFFLINE_REPLAY_PATH,
        harness_path=HARNESS_PATH,
        scenario_replay_contract_test_path=SCENARIO_REPLAY_CONTRACT_TEST_PATH,
        chained_contract_test_path=CHAINED_CONTRACT_TEST_PATH,
        double_play_composition_chain_preserved=True,
        survival_hard_fail_blocks_composition=True,
        survival_required_unknown_fail_closed=True,
        suitability_deterministic_strategy_selection=True,
        no_list_order_strategy_override=True,
        no_confidence_only_selection=True,
        cost_model_boundary_bound=True,
        regime_owner_boundary_bound=True,
        survival_suitability_offline_only=True,
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    return {
        "schema": "SurvivalSuitabilityNarrowReuseFirstRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "rewire_scope": "survival_and_suitability_only",
        "rewire_binding": asdict(binding),
        "bull_survival_status": result.bull_survival.status.value,
        "bull_suitability_status": result.bull_suitability.status.value,
        "selected_strategy_id": result.bull_suitability.selected_strategy_id,
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
        "# Survival and Suitability Narrow Reuse-First Rewire V1",
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
        "SURVIVAL_HARD_FAIL_BLOCKS_COMPOSITION=true",
        "SURVIVAL_REQUIRED_UNKNOWN_FAIL_CLOSED=true",
        "SUITABILITY_DETERMINISTIC_STRATEGY_SELECTION=true",
        "```",
        "",
        f"- reused_survival_assessment_owner: `{binding['reused_survival_assessment_owner']}`",
        f"- reused_suitability_binding_owner: `{binding['reused_suitability_binding_owner']}`",
        f"- reused_scenario_binding_adapter_owner: `{binding['reused_scenario_binding_adapter_owner']}`",
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
    (output_dir / "survival_suitability_narrow_reuse_first_rewire_v0.json").write_text(
        json.dumps(rewire, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "survival_suitability_narrow_reuse_first_rewire_v0.md").write_text(
        render_markdown(rewire) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_SURVIVAL_SUITABILITY_NARROW_REUSE_FIRST_REWIRE_BOUND"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"REUSED_SURVIVAL_ASSESSMENT_OWNER={REUSED_SURVIVAL_ASSESSMENT_OWNER}")
    print(f"REUSED_SUITABILITY_BINDING_OWNER={REUSED_SUITABILITY_BINDING_OWNER}")
    print("FUNCTIONAL_REWIRE_PERFORMED=true")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
