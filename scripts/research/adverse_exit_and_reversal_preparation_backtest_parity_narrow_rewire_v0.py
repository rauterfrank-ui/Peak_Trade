from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import NO_AUTHORITY_FLAGS
from scripts.research.scope_adverse_exit_and_reversal_preparation_narrow_reuse_first_rewire_v0 import (
    REVERSAL_CONTRACT_TEST_PATH,
    SCOPE_CONTRACT_TEST_PATH,
    SURFACE_ID,
    evaluate_scope_adverse_exit_and_reversal_parity_fixtures_v0,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import CanonicalScopeEventType
from trading.master_v2.directional_assessment_v1 import mirror_price_path_for_short
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionStatus,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    EntryExitPolicyDecisionV0,
    ExitClass,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayInputV1,
    resolve_integrated_reversal_preparation_entry_exit_binding_v0,
    resolve_integrated_scope_adverse_exit_signal_v0,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    canonical_owner_refs_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import SYNTHETIC_FUTURES_INSTRUMENT
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
    reversal_preparation_decision_is_reduce_only_preparation_v0,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
    SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER,
    derive_scope_adverse_exit_signal_v0,
)

PLAN_TYPE = "BACKTEST_PARITY_NARROW_REWIRE"
TRACE_ASSERTION_SOURCE_PR = 5060
REWIRE_STATE = "REWIRE_BOUND_INTEGRATED_BACKTEST_PARITY_PATH"
ASSESSMENT_SOURCE_PR = 5060

BACKTEST_CONSUMER = "src/backtest/mv2_research_wiring_v1.py"
INTEGRATED_REPLAY_PATH = "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
SCOPE_ADAPTER_PATH = "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py"
REVERSAL_ADAPTER_PATH = "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py"
ASSESSMENT_CONTRACT_PATH = "docs/research/adverse_exit_and_reversal_preparation_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
OWNER_BOUND_PATHS = (
    BACKTEST_CONSUMER,
    INTEGRATED_REPLAY_PATH,
    SCOPE_ADAPTER_PATH,
    REVERSAL_ADAPTER_PATH,
    SCOPE_CONTRACT_TEST_PATH,
    REVERSAL_CONTRACT_TEST_PATH,
)


@dataclass(frozen=True)
class RewireBinding:
    surface_id: str
    reused_scope_canonical_owner: str
    reused_scope_adapter_owner: str
    reused_reversal_adapter_owner: str
    backtest_consumer_path: str
    integrated_replay_path: str
    scope_adapter_path: str
    reversal_adapter_path: str
    scope_contract_test_path: str
    reversal_contract_test_path: str
    integrated_derives_scope_adverse_exit_signal: bool
    integrated_reversal_preparation_projection_bound: bool
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
    if refs["scope_event_generator"] != CANONICAL_SCOPE_EVENT_GENERATOR_OWNER:
        raise ValueError("scope event generator owner drift")
    if (
        refs["scope_event_generator_scenario_binding_adapter"]
        != SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER
    ):
        raise ValueError("scope adapter owner drift")
    if (
        refs["reversal_preparation_scenario_binding_adapter"]
        != REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER
    ):
        raise ValueError("reversal preparation adapter owner drift")


def _build_integrated_replay_input_for_fixture(
    *,
    price_path: tuple[float, ...],
    scope_direction_state: object,
    position_management_context: PositionManagementContext,
    existing_position_side: ExistingPositionSide,
    side_state: SideState,
    direction_state: EntryExitDirectionState,
    mark_price: float,
) -> Any:
    from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
        _market_context,
        _replay_input,
    )

    return _replay_input(
        canonical_market_context=_market_context(mark_price=mark_price),
        price_path=price_path,
        current_price=float(price_path[-1]),
        scope_direction_state=scope_direction_state,
        position_management_context=position_management_context,
        existing_position_side=existing_position_side,
        position_state=PositionState.OPEN_FULL,
        side_state=side_state,
        direction_state=direction_state,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        up_distance=2.0,
        adverse_exit_distance=2.0,
        reversal_distance=4.0,
    )


def evaluate_adverse_exit_integrated_backtest_parity_fixtures_v0() -> tuple[Any, Any]:
    from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState

    long_path = (100.0, 96.0)
    long_inp = _build_integrated_replay_input_for_fixture(
        price_path=long_path,
        scope_direction_state=ScopeDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        mark_price=100.0,
    )
    long_result = run_integrated_offline_trading_logic_replay_v1(long_inp)
    if long_result.intermediate is None:
        raise ValueError("long adverse fixture must produce intermediate replay state")
    long_scope = long_result.intermediate.scope_event
    long_signal = resolve_integrated_scope_adverse_exit_signal_v0(
        long_scope,
        PolicySignalV0(triggered=False),
    )
    if not long_signal.triggered:
        raise ValueError("long adverse fixture must derive triggered scope adverse exit signal")
    if "adverse_exit" not in long_scope.matched_conditions:
        raise ValueError("long adverse fixture must match adverse_exit condition")
    if long_scope.event_type not in (
        CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
    ):
        raise ValueError(
            "long adverse fixture must keep adverse dimension "
            "(ADVERSE_EXIT_CANDIDATE or nested DOWNSCOPE_*)"
        )

    short_path = mirror_price_path_for_short(long_path, reference=100.0)
    short_inp = _build_integrated_replay_input_for_fixture(
        price_path=short_path,
        scope_direction_state=ScopeDirectionState.SHORT,
        position_management_context=PositionManagementContext.SHORT_POSITION,
        existing_position_side=ExistingPositionSide.SHORT,
        side_state=SideState.SHORT_ACTIVE,
        direction_state=EntryExitDirectionState.SHORT_ACTIVE,
        mark_price=100.0,
    )
    short_result = run_integrated_offline_trading_logic_replay_v1(short_inp)
    if short_result.intermediate is None:
        raise ValueError("short adverse fixture must produce intermediate replay state")
    short_scope = short_result.intermediate.scope_event
    short_signal = resolve_integrated_scope_adverse_exit_signal_v0(
        short_scope,
        PolicySignalV0(triggered=False),
    )
    if not short_signal.triggered:
        raise ValueError("short adverse fixture must derive triggered scope adverse exit signal")
    if "adverse_exit" not in short_scope.matched_conditions:
        raise ValueError("short adverse fixture must match adverse_exit condition")
    if short_scope.event_type not in (
        CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
    ):
        raise ValueError(
            "short adverse fixture must keep adverse dimension "
            "(ADVERSE_EXIT_CANDIDATE or nested DOWNSCOPE_*)"
        )
    return long_result, short_result


def evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0() -> tuple[Any, Any]:
    from dataclasses import replace

    from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
    from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
    from trading.master_v2.double_play_composition_matrix_v1 import (
        CompositionSelectedSide,
        compute_composition_input_digest,
        evaluate_double_play_composition_matrix_v1,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import (
        DoublePlayEntryExitPolicyInputV0,
        compute_entry_exit_policy_input_digest,
        evaluate_double_play_entry_exit_policy_v0,
    )
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        build_scenario_matrix_composition_input_v0,
        evaluate_reversal_preparation_matrix_v0,
    )

    def _decision_for_matrix(
        matrix: Any,
        inp: IntegratedOfflineReplayInputV1,
        *,
        direction_state: EntryExitDirectionState,
    ) -> EntryExitPolicyDecisionV0:
        projected, existing_side, position_state, venue_flat = (
            resolve_integrated_reversal_preparation_entry_exit_binding_v0(matrix, inp)
        )
        entry_exit_inp = DoublePlayEntryExitPolicyInputV0(
            instrument_id=inp.instrument_id,
            trading_epoch=inp.trading_epoch,
            context_reference=inp.context_reference,
            composition_result=projected,
            direction_state=direction_state,
            position_state=position_state,
            reconciliation_state=inp.reconciliation_state,
            trading_gate=inp.trading_gate,
            safety_mode=inp.safety_mode,
            data_integrity_state=inp.canonical_market_context.data_integrity_status,
            clock_trust_status=inp.canonical_market_context.clock_trust_status,
            clock_trust_valid=True,
            cooldown_pass=inp.cooldown_pass,
            existing_position_side=existing_side,
            venue_flat=venue_flat,
            scope_adverse_exit_signal=PolicySignalV0(triggered=False),
            profit_protection_signal=inp.profit_protection_signal,
            time_exit_signal=inp.time_exit_signal,
            strategy_invalidation_signal=inp.strategy_invalidation_signal,
            hard_risk_reduction_signal=inp.hard_risk_reduction_signal,
            safety_exit_signal=inp.safety_exit_signal,
            input_complete=True,
            input_digest="",
            explicit_blocked_reasons=(),
            policy_version=inp.policies.entry_exit.policy_version,
        )
        entry_exit_inp = replace(
            entry_exit_inp,
            input_digest=compute_entry_exit_policy_input_digest(entry_exit_inp),
        )
        return evaluate_double_play_entry_exit_policy_v0(entry_exit_inp, inp.policies.entry_exit)

    long_inp = _build_integrated_replay_input_for_fixture(
        price_path=(3500.0, 3400.0),
        scope_direction_state=ScopeDirectionState.SHORT,
        position_management_context=PositionManagementContext.LONG_POSITION,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        mark_price=3500.0,
    )
    long_matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=long_inp.instrument_id,
        trading_epoch=long_inp.trading_epoch,
        context_reference=f"{long_inp.context_reference}-long-reversal",
    )
    long_projected, _, _, _ = resolve_integrated_reversal_preparation_entry_exit_binding_v0(
        long_matrix,
        long_inp,
    )
    if long_projected.selected_side is not CompositionSelectedSide.SHORT:
        raise ValueError("long reversal projection must select opposite SHORT side")
    long_decision = _decision_for_matrix(
        long_matrix,
        long_inp,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
    )
    if long_decision.exit_class is not ExitClass.REVERSAL_PREPARATION_EXIT:
        raise ValueError("long reversal binding must reach REVERSAL_PREPARATION_EXIT")

    short_inp = _build_integrated_replay_input_for_fixture(
        price_path=(3500.0, 3600.0),
        scope_direction_state=ScopeDirectionState.LONG,
        position_management_context=PositionManagementContext.SHORT_POSITION,
        existing_position_side=ExistingPositionSide.SHORT,
        side_state=SideState.SHORT_ACTIVE,
        direction_state=EntryExitDirectionState.SHORT_ACTIVE,
        mark_price=3500.0,
    )
    short_matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=short_inp.instrument_id,
        trading_epoch=short_inp.trading_epoch,
        context_reference=f"{short_inp.context_reference}-short-reversal",
        side_st=SideState.SHORT_ACTIVE,
    )
    short_matrix_input = replace(
        short_matrix_input,
        bull_directional_assessment=replace(
            short_matrix_input.bull_directional_assessment,
            status=DirectionalAssessmentStatus.CONFIRMED,
        ),
        bear_directional_assessment=replace(
            short_matrix_input.bear_directional_assessment,
            status=DirectionalAssessmentStatus.OBSERVE,
        ),
        position_management_context=PositionManagementContext.SHORT_POSITION,
        input_digest="",
    )
    short_matrix_input = replace(
        short_matrix_input,
        input_digest=compute_composition_input_digest(short_matrix_input),
    )
    short_matrix = evaluate_double_play_composition_matrix_v1(
        short_matrix_input,
        short_inp.policies.composition,
    )
    short_projected, _, _, _ = resolve_integrated_reversal_preparation_entry_exit_binding_v0(
        short_matrix,
        short_inp,
    )
    if short_projected.selected_side is not CompositionSelectedSide.LONG:
        raise ValueError("short reversal projection must select opposite LONG side")
    short_decision = _decision_for_matrix(
        short_matrix,
        short_inp,
        direction_state=EntryExitDirectionState.SHORT_ACTIVE,
    )
    if short_decision.exit_class is not ExitClass.REVERSAL_PREPARATION_EXIT:
        raise ValueError("short reversal binding must reach REVERSAL_PREPARATION_EXIT")
    return long_decision, short_decision


def build_rewire_binding(repo_root: Path) -> dict[str, Any]:
    _assert_owner_bound_paths_exist(repo_root)
    _assert_canonical_owner_reuse()
    scope_binding, reversal_decision = evaluate_scope_adverse_exit_and_reversal_parity_fixtures_v0()
    evaluate_adverse_exit_integrated_backtest_parity_fixtures_v0()
    evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0()

    integrated_source = (repo_root / INTEGRATED_REPLAY_PATH).read_text(encoding="utf-8")
    binding = RewireBinding(
        surface_id=SURFACE_ID,
        reused_scope_canonical_owner=CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
        reused_scope_adapter_owner=SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER,
        reused_reversal_adapter_owner=REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
        backtest_consumer_path=BACKTEST_CONSUMER,
        integrated_replay_path=INTEGRATED_REPLAY_PATH,
        scope_adapter_path=SCOPE_ADAPTER_PATH,
        reversal_adapter_path=REVERSAL_ADAPTER_PATH,
        scope_contract_test_path=SCOPE_CONTRACT_TEST_PATH,
        reversal_contract_test_path=REVERSAL_CONTRACT_TEST_PATH,
        integrated_derives_scope_adverse_exit_signal=(
            "derive_scope_adverse_exit_signal_v0" in integrated_source
            and "resolve_integrated_scope_adverse_exit_signal_v0" in integrated_source
        ),
        integrated_reversal_preparation_projection_bound=(
            "resolve_integrated_reversal_preparation_entry_exit_binding_v0" in integrated_source
        ),
        rewire_state=REWIRE_STATE,
        functional_rewire_performed=True,
        new_parallel_owner_created=False,
    )
    if not binding.integrated_derives_scope_adverse_exit_signal:
        raise ValueError("integrated replay must derive scope adverse exit signal")
    if not binding.integrated_reversal_preparation_projection_bound:
        raise ValueError("integrated replay must bind reversal preparation projection")
    if not scope_binding.scope_adverse_exit_signal.triggered:
        raise ValueError("offline scope fixture must keep adverse-exit signal")
    if "adverse_exit" not in scope_binding.scope_event_evidence.matched_conditions:
        raise ValueError("offline scope fixture must match adverse_exit condition")
    if scope_binding.scope_event_evidence.event_type not in (
        CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
    ):
        raise ValueError(
            "offline scope fixture must keep adverse dimension "
            "(ADVERSE_EXIT_CANDIDATE or nested DOWNSCOPE_*)"
        )
    if reversal_decision.exit_class is not ExitClass.REVERSAL_PREPARATION_EXIT:
        raise ValueError("offline reversal fixture must remain reversal-preparation bound")
    if not reversal_preparation_decision_is_reduce_only_preparation_v0(reversal_decision):
        raise ValueError("reversal preparation must remain reduce-only preparation")

    return {
        "schema": "AdverseExitAndReversalPreparationBacktestParityNarrowRewireV1",
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_source_pr": TRACE_ASSERTION_SOURCE_PR,
        "assessment_source_pr": ASSESSMENT_SOURCE_PR,
        "assessment_source_contract": ASSESSMENT_CONTRACT_PATH,
        "canonical_owner": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
        "backtest_consumer": BACKTEST_CONSUMER,
        "reuse_decision": "REUSE_WITH_NARROW_INTEGRATED_CONSUMER_BINDING",
        "rewire_binding": asdict(binding),
        "adverse_scope_exit_backtest_parity_status": "WIRED",
        "reversal_preparation_backtest_parity_status": "WIRED",
        "scope_exit_reversal_backtest_parity_pass": True,
        "forbidden_claims_remain_false": {
            "FULL_CANONICAL_CHAIN_WIRED": False,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": False,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
            "RUNTIME_AUTHORITY": False,
            "ORDERS_ALLOWED": False,
            "ECONOMIC_CLAIM": False,
        },
        **NO_AUTHORITY_FLAGS,
    }


def render_markdown(rewire: dict[str, Any]) -> str:
    binding = rewire["rewire_binding"]
    lines = [
        "# Adverse Exit and Reversal Preparation Backtest Parity Narrow Rewire v0",
        "",
        "```text",
        "NARROW_BACKTEST_PARITY_REWIRE=true",
        "FUNCTIONAL_REWIRE_PERFORMED=true",
        "NEW_PARALLEL_OWNER_CREATED=false",
        "SCOPE_EXIT_REVERSAL_BACKTEST_PARITY_PASS=true",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "AUTHORITY_EFFECT=NONE",
        "RUNTIME_EFFECT=NONE",
        "```",
        "",
        f"- reused_scope_canonical_owner: `{binding['reused_scope_canonical_owner']}`",
        f"- reused_scope_adapter_owner: `{binding['reused_scope_adapter_owner']}`",
        f"- reused_reversal_adapter_owner: `{binding['reused_reversal_adapter_owner']}`",
        f"- backtest_consumer: `{binding['backtest_consumer_path']}`",
        f"- integrated_replay_path: `{binding['integrated_replay_path']}`",
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
    (
        output_dir / "adverse_exit_and_reversal_preparation_backtest_parity_narrow_rewire_v0.json"
    ).write_text(json.dumps(rewire, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (
        output_dir / "ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_NARROW_REWIRE_V0.md"
    ).write_text(render_markdown(rewire) + "\n", encoding="utf-8")
    verdict = "PASS_SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_NARROW_REWIRE_V0"
    (output_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                "SCOPE_EXIT_REVERSAL_BACKTEST_PARITY_PASS=true",
                "ADVERSE_SCOPE_EXIT_BACKTEST_PARITY_STATUS=WIRED",
                "REVERSAL_PREPARATION_BACKTEST_PARITY_STATUS=WIRED",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"CANONICAL_OWNER={INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER}")
    print(f"BACKTEST_CONSUMER={BACKTEST_CONSUMER}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
