"""READ-ONLY Cold S7 layered-core bootstrap initialization golden vector harness.

No production/config/test mutation. Emits JSON artifacts in this directory.
Run: ./scripts/pt -c "import runpy; runpy.run_path('<this_file>', run_name='__main__')"
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = Path(__file__).resolve().parent

from trading.market_state.distinct_market_observation_acceptor_v1 import (  # noqa: E402
    ObservationClassification,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.elementary_direction_v1 import ElementaryDirectionV1  # noqa: E402
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1  # noqa: E402
from trading.master_v2.double_play_old_effective_host_contract_v1 import (  # noqa: E402
    layered_core_cmc_mark_observation_init_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (  # noqa: E402
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (  # noqa: E402
    NakedLayeredCoreDurableStateError,
    initialize_naked_layered_core_episode_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l3_initial_direction_v1 import (  # noqa: E402
    apply_l3_initial_direction_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l6_dynamic_scope_generator_v1 import (  # noqa: E402
    ExplicitPassthroughDynamicScopeGeneratorV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (  # noqa: E402
    InitialDirectionInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l2_market_observation_v1 import (  # noqa: E402
    MarketObservationInputV1,
    apply_l2_market_observation_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (  # noqa: E402
    _observation_candidates_from_cmc_mark_v1,
    _observation_candidates_from_finalized_closes_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (  # noqa: E402
    DEFAULT_VENUE,
)


def _init_result(obs: tuple[Any, ...]) -> str:
    key = InstrumentObservationKeyV1(
        venue=DEFAULT_VENUE,
        canonical_instrument_id="PROBE",
        venue_instrument_id="PROBE",
    )
    try:
        initialize_naked_layered_core_episode_v1(
            selected=SelectedFutureInputV1(instrument_id="PROBE", instrument_key=key),
            initialization_observations=obs,
            first_mechanical_step=None,
            scope_generator=ExplicitPassthroughDynamicScopeGeneratorV1(),
        )
        return "INITIALIZED"
    except NakedLayeredCoreDurableStateError as exc:
        return str(exc)


def _l3_trace(obs: tuple[Any, ...]) -> list[dict[str, Any]]:
    key = InstrumentObservationKeyV1(
        venue=DEFAULT_VENUE,
        canonical_instrument_id="PROBE",
        venue_instrument_id="PROBE",
    )
    from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
        initial_market_observation_state_v1,
        apply_l1_selected_future_v1,
    )

    l1 = apply_l1_selected_future_v1(SelectedFutureInputV1(instrument_id="PROBE", instrument_key=key))
    obs_state = initial_market_observation_state_v1(l1.state)
    rows: list[dict[str, Any]] = []
    for i, candidate in enumerate(obs):
        l2 = apply_l2_market_observation_v1(
            MarketObservationInputV1(observation_state=obs_state, candidate=candidate)
        )
        obs_state = l2.observation_state
        mark = float(candidate.mark_price)  # type: ignore[arg-type]
        l3 = apply_l3_initial_direction_v1(
            InitialDirectionInputV1(
                acceptance_result=l2.acceptance_result,
                bound_instrument_key=l1.state.instrument_key,
                current_mark=mark,
            )
        )
        rows.append(
            {
                "index": i,
                "venue_event_time": candidate.venue_event_time,
                "mark_price": mark,
                "c1_classification": l2.acceptance_result.classification.value,
                "l3_direction": (
                    None
                    if l3.direction_result.direction is None
                    else l3.direction_result.direction.value
                ),
                "l3_reason": l3.direction_result.reason_code,
            }
        )
    return rows


def build_contract_matrix() -> list[dict[str, Any]]:
    flag = layered_core_cmc_mark_observation_init_v1(repo_root=REPO)
    rows: list[dict[str, Any]] = []
    seq = 0

    def add(**row: Any) -> None:
        nonlocal seq
        seq += 1
        rows.append({"seq": seq, **row})

    add(
        init_contract_id="FAILURE_SITE",
        layer="LAYERED_INIT",
        field_or_state="initialize_naked_layered_core_episode_v1 nullline/regime_state",
        producer="durable_state_v1.initialize_naked_layered_core_episode_v1",
        live_value="NakedLayeredCoreDurableStateError: INITIALIZATION_INCOMPLETE",
        forensic_success_value="episode returned (initialized)",
        historical_value_if_relevant="historical used closes via run_p5 seam (23dccab)",
        consumer="ensure_productive_layered_core_episode_store_v1",
        required_semantics="≥1 DISTINCT observation yielding L3 BULL or BEAR then L4/L5",
        productive_reachable=True,
        forensic_continuation=False,
        classification="LIVE_VALUE_INVALID",
        root_cause=False,
        downstream_impact="S7 compose fail-closed",
        source_evidence="durable_state_v1.py:475-476",
    )
    add(
        init_contract_id="ADDRESSING_JOIN_PROPAGATION",
        layer="S7_COMPOSE",
        field_or_state="bootstrap_failures tuple",
        producer="compose_occupied_lane_mv2_dp_durable_cycle_v1",
        live_value="layered_core_bootstrap_init_fail_closed:INITIALIZATION_INCOMPLETE",
        forensic_success_value="not invoked on master_v2_runtime_cycle forensic path",
        consumer="FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError",
        required_semantics="empty bootstrap_failures",
        productive_reachable=True,
        forensic_continuation=False,
        classification="LIVE_WIRING_DIVERGENCE",
        root_cause=False,
        downstream_impact="PRODUCTIVE_CYCLES=0 on cold bootstrap_s8",
        source_evidence="addressing_join_v1.py:852-864",
    )
    add(
        init_contract_id="WP3_LAYERED_CMC_FLAG",
        layer="CONFIG",
        field_or_state="layered_core_cmc_mark_observation_init",
        producer="config/governance/double_play_old_effective_host_contract_v1_decision_v1.json",
        live_value=True,
        forensic_success_value=True,
        consumer="ensure_productive_layered_core_episode_store_v1 branch",
        required_semantics="select observation builder",
        productive_reachable=True,
        forensic_continuation=False,
        classification="WP3_COMPAT_EQUIVALENT",
        root_cause=False,
        source_evidence="WP-3 decision + productive_cycle_bind_seam uncommitted diff",
    )
    add(
        init_contract_id="INIT_OBS_BUILDER_LIVE",
        layer="BOOTSTRAP",
        field_or_state="initialization_observations",
        producer="_observation_candidates_from_cmc_mark_v1 when flag true",
        live_value="two DISTINCT marks, identical M_t at t-60 and t",
        forensic_success_value="finalized_closes grid (committed HEAD) OR fixture uptrend closes",
        historical_value_if_relevant="closes-only _observation_candidates_from_closes_v1",
        consumer="initialize_naked_layered_core_episode_v1",
        required_semantics="sequence must pass L3 BULL/BEAR gate",
        productive_reachable=True,
        forensic_continuation=True,
        classification="LIVE_WIRING_DIVERGENCE",
        root_cause=True,
        downstream_impact="INITIALIZATION_INCOMPLETE",
        source_evidence="productive_cycle_bind_seam_v1.py WP-3 diff",
    )
    add(
        init_contract_id="INIT_L3_DIRECTION_GATE",
        layer="LAYERED_INIT",
        field_or_state="L3 direction in BULL|BEAR",
        producer="apply_l3_initial_direction_v1 / elementary_direction_v1",
        live_value="NEUTRAL on first DISTINCT; NEUTRAL on second equal mark",
        forensic_success_value="BULL or BEAR on second DISTINCT when marks differ",
        consumer="initialize loop break condition durable_state_v1:449-453",
        required_semantics="direction in (BULL, BEAR) to reach L4/L5",
        productive_reachable=True,
        forensic_continuation=False,
        classification="CURRENT_EQUIVALENT",
        root_cause=True,
        downstream_impact="nullline stays None",
        source_evidence="durable_state_v1.py + test_elementary_direction_v1",
    )
    add(
        init_contract_id="SCOPE_ON_OUTGOING_CURSOR",
        layer="S7_COMPOSE",
        field_or_state="incoming_cursor_has_existing_scope_carrier_v1",
        producer="MV2 replay in same compose pass",
        live_value=True,
        forensic_success_value="true on cold compose; false on many forensic oneshot cycles",
        consumer="ensure_productive_layered_core_episode_store_v1 gate",
        required_semantics="scope present triggers episode bootstrap",
        productive_reachable=True,
        forensic_continuation=False,
        classification="EXPECTED_COLD_START_STATE",
        root_cause=False,
        source_evidence="productive_cycle_bind_seam_v1.py:465-467",
    )
    add(
        init_contract_id="BOOTSTRAP_MARK_PAYLOAD",
        layer="EXTERNAL_INPUT",
        field_or_state="mark_price_payload",
        producer="LiveFreshC1ContinuousObservationSourceV1.poll",
        live_value="valid real GET (ROOT_WIRING_01 closed)",
        forensic_success_value="fixture/harness payloads",
        consumer="bootstrap_s8_lane_via_s7_compose_v1",
        required_semantics="non-null provenance-valid mark",
        productive_reachable=True,
        forensic_continuation=False,
        classification="ROOT_WIRING_01_EQUIVALENT",
        root_cause=False,
        source_evidence="WP ROOT_WIRING_01 reproof",
    )
    add(
        init_contract_id="FINALIZED_CLOSES_LIVE",
        layer="EXTERNAL_INPUT",
        field_or_state="finalized_closes",
        producer="S7 alignment from injected C1 candles",
        live_value="≥2 real 1m closes (typically differ)",
        forensic_success_value="strong_uptrend fixture closes",
        consumer="ignored when WP3 CMC flag selects CMC builder",
        required_semantics="would satisfy L3 if used as observation marks",
        productive_reachable=True,
        forensic_continuation=False,
        classification="LIVE_VALUE_MISSING",
        root_cause=True,
        downstream_impact="available but not consumed for init obs when flag on",
        source_evidence="committed HEAD uses closes; WP-3 diff overrides",
    )
    add(
        init_contract_id="FORENSIC_PATH_SURFACE",
        layer="RUNTIME_ROUTING",
        field_or_state="cycle host entry",
        producer="run_current_productive_master_v2_runtime_cycle_v1",
        live_value="bootstrap_s8_lane_via_s7_compose_v1 → compose_occupied_lane",
        forensic_success_value="oneshot master_v2_runtime_cycle (ensure_productive calls=0)",
        consumer="E2E golden vector forensic enter_long",
        required_semantics="exercise same cold ensure bootstrap",
        productive_reachable=False,
        forensic_continuation=True,
        classification="FIXTURE_ONLY_VALUE",
        root_cause=False,
        downstream_impact="E2E did not catch cold ensure failure",
        source_evidence="harness trace ensure_calls=0",
    )
    _ = flag
    return rows


def build_causal_isolation() -> dict[str, Any]:
    key = InstrumentObservationKeyV1(
        venue=DEFAULT_VENUE,
        canonical_instrument_id="PROBE",
        venue_instrument_id="PROBE",
    )
    ts = 1_759_180_000.0
    mark = 0.3283
    closes = (0.3280, 0.3283)
    cmc = _observation_candidates_from_cmc_mark_v1(
        instrument_key=key, cmc_mark_price_m_t=mark, event_ts_unix=ts
    )
    close_obs = _observation_candidates_from_finalized_closes_v1(
        instrument_key=key, closes=closes, last_event_ts_unix=ts
    )
    tests = [
        {
            "test_id": "BASELINE_LIVE_CMC_WP3",
            "substitution": "none (WP3 CMC builder)",
            "init_result": _init_result(cmc),
            "l3_trace": _l3_trace(cmc),
        },
        {
            "test_id": "SUBSTITUTE_CLOSE_GRID_ONLY",
            "substitution": "finalized_closes observation builder (committed HEAD semantics)",
            "init_result": _init_result(close_obs),
            "l3_trace": _l3_trace(close_obs),
        },
        {
            "test_id": "SUBSTITUTE_VARIED_MARKS_ON_CMC_TIMES",
            "substitution": "CMC time grid with close[-2]/close[-1] marks",
            "init_result": _init_result(
                (
                    cmc[0].__class__(
                        venue=cmc[0].venue,
                        canonical_instrument_id=cmc[0].canonical_instrument_id,
                        venue_instrument_id=cmc[0].venue_instrument_id,
                        venue_event_time=cmc[0].venue_event_time,
                        mark_price=closes[0],
                    ),
                    cmc[1].__class__(
                        venue=cmc[1].venue,
                        canonical_instrument_id=cmc[1].canonical_instrument_id,
                        venue_instrument_id=cmc[1].venue_instrument_id,
                        venue_event_time=cmc[1].venue_event_time,
                        mark_price=closes[1],
                    ),
                )
            ),
            "l3_trace": _l3_trace(
                (
                    cmc[0].__class__(
                        venue=cmc[0].venue,
                        canonical_instrument_id=cmc[0].canonical_instrument_id,
                        venue_instrument_id=cmc[0].venue_instrument_id,
                        venue_event_time=cmc[0].venue_event_time,
                        mark_price=closes[0],
                    ),
                    cmc[1].__class__(
                        venue=cmc[1].venue,
                        canonical_instrument_id=cmc[1].canonical_instrument_id,
                        venue_instrument_id=cmc[1].venue_instrument_id,
                        venue_event_time=cmc[1].venue_event_time,
                        mark_price=closes[1],
                    ),
                )
            ),
        },
    ]
    return {
        "wp3_cmc_flag": layered_core_cmc_mark_observation_init_v1(repo_root=REPO),
        "minimal_causal_input_set": ["INIT_OBS_BUILDER_LIVE"],
        "divergent_init_inputs_total": 1,
        "tests": tests,
        "forensic_minimal_substitution_verdict": (
            "PASS"
            if tests[0]["init_result"] == "INITIALIZATION_INCOMPLETE"
            and tests[1]["init_result"] == "INITIALIZED"
            and tests[2]["init_result"] == "INITIALIZED"
            else "FAIL"
        ),
        "initialization_complete_after_close_grid_substitution": tests[1]["init_result"]
        == "INITIALIZED",
    }


def build_live_vs_forensic_diff() -> dict[str, Any]:
    return {
        "live_cold_path": {
            "entry": "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1",
            "bootstrap": "bootstrap_s8_lane_via_s7_compose_v1",
            "compose": "compose_occupied_lane_mv2_dp_durable_cycle_v1",
            "layered_bootstrap": "ensure_productive_layered_core_episode_store_v1",
            "observation_builder_when_wp3": "_observation_candidates_from_cmc_mark_v1",
            "terminal_error": (
                "FULL_AUTONOMY_MV2_DP_DECISION_STATE_ADDRESSING_MISMATCHED_LANE_STATE:"
                "LANE_1:layered_core_bootstrap_init_fail_closed:INITIALIZATION_INCOMPLETE"
            ),
            "productive_cycles": 0,
            "post_count": 0,
            "instrument": "0G-USDT-SWAP",
            "live_mark_snapshot": 0.3283,
            "source_evidence": (
                "evidence/ops/double_play_root_wiring_01_patch_golden_vector_reproof_v1/"
                "20260929T221500Z/runtime/run_stdout.json"
            ),
        },
        "forensic_success_path": {
            "entry": "run_natural_enter_long_sequence_for_governed_pre_external_v1",
            "cycle_host": "run_current_productive_master_v2_runtime_cycle_v1",
            "compose_s7_ensure_bootstrap_invoked": False,
            "enter_long_reached": True,
            "observation_builder_note": (
                "Forensic sequence does not invoke ensure_productive; layered init via "
                "prepare_productive_layered_core_replay_bind on later cycles when store exists"
            ),
            "productive_reachable": False,
            "forensic_continuation": True,
        },
        "committed_head_cold_bootstrap": {
            "observation_builder": "_observation_candidates_from_finalized_closes_v1",
            "wp3_flag_file_absent_effect": "closes path only in ensure_productive",
        },
    }


def build_root_cause_graph() -> dict[str, Any]:
    return {
        "nodes": [
            "LIVE_COLD_S7_COMPOSE",
            "SCOPE_ON_OUTGOING_CURSOR",
            "ENSURE_LAYERED_EPISODE_STORE",
            "WP3_CMC_OBS_BUILDER",
            "IDENTICAL_MARK_AT_T_MINUS_60_AND_T",
            "L3_NEUTRAL_NEUTRAL",
            "NULllINE_NONE",
            "INITIALIZATION_INCOMPLETE",
            "ADDRESSING_JOIN_FAIL",
            "PRODUCTIVE_CYCLES_0",
        ],
        "edges": [
            ["LIVE_COLD_S7_COMPOSE", "SCOPE_ON_OUTGOING_CURSOR"],
            ["SCOPE_ON_OUTGOING_CURSOR", "ENSURE_LAYERED_EPISODE_STORE"],
            ["ENSURE_LAYERED_EPISODE_STORE", "WP3_CMC_OBS_BUILDER"],
            ["WP3_CMC_OBS_BUILDER", "IDENTICAL_MARK_AT_T_MINUS_60_AND_T"],
            ["IDENTICAL_MARK_AT_T_MINUS_60_AND_T", "L3_NEUTRAL_NEUTRAL"],
            ["L3_NEUTRAL_NEUTRAL", "NULlline_NONE"],
            ["NULlline_NONE", "INITIALIZATION_INCOMPLETE"],
            ["INITIALIZATION_INCOMPLETE", "ADDRESSING_JOIN_FAIL"],
            ["ADDRESSING_JOIN_FAIL", "PRODUCTIVE_CYCLES_0"],
        ],
        "root_divergence_ids": ["INIT_ROOT_01_WP3_CMC_STATIC_MARK_L3_INCOMPATIBLE"],
        "addressing_join_root_cause": False,
        "layered_init_root_cause": True,
        "cold_start_dependency_cycle": False,
    }


def main() -> None:
    matrix = build_contract_matrix()
    causal = build_causal_isolation()
    diff = build_live_vs_forensic_diff()
    graph = build_root_cause_graph()
    summary = {
        "wp": "DOUBLE_PLAY_LIVE_COLD_S7_BOOTSTRAP_INITIALIZATION_GOLDEN_VECTOR_V1",
        "mode": "READ_ONLY_RUNTIME_DIFFERENTIAL_GOLDEN_VECTOR",
        "baseline_sha": "8475ebb948d246efd0c70a1cf4101fd3bf1b54db",
        "branch": "wp3/double-play-compatibility-boundary-v1",
        "failure_source_file": "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/durable_state_v1.py",
        "failure_source_function": "initialize_naked_layered_core_episode_v1",
        "failure_gate": "layered_core_bootstrap_init_fail_closed",
        "failure_reason": "INITIALIZATION_INCOMPLETE",
        "failure_branch": "nullline is None or regime_state is None after initialization_observations loop",
        "initialization_contracts_total": len(matrix),
        "minimal_causal_input_set": causal["minimal_causal_input_set"],
        "root_divergence_ids": graph["root_divergence_ids"],
        "historical_root_semantics": "DIFFERENT_WIRING",
        "production_files_changed": 0,
        "post_count": 0,
        "external_effect_count": 0,
    }
    (EVIDENCE_DIR / "initialization_contract_matrix.json").write_text(
        json.dumps(matrix, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    (EVIDENCE_DIR / "initialization_causal_isolation.json").write_text(
        json.dumps(causal, indent=2) + "\n", encoding="utf-8"
    )
    (EVIDENCE_DIR / "live_vs_forensic_success_diff.json").write_text(
        json.dumps(diff, indent=2) + "\n", encoding="utf-8"
    )
    (EVIDENCE_DIR / "initialization_root_cause_graph.json").write_text(
        json.dumps(graph, indent=2) + "\n", encoding="utf-8"
    )
    (EVIDENCE_DIR / "WP_DOUBLE_PLAY_LIVE_COLD_S7_BOOTSTRAP_INITIALIZATION_GOLDEN_VECTOR_V1.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
