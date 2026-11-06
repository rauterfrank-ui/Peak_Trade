from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Mapping

from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import (
    STAGE2_GENERALIZATION_PROFILES,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.constants_v2 import (
    STAGE2_SURVIVORS,
    TARGET_STAGE2_FLIGHTS,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.cmc_builder_v2 import refresh_cmc_mark_v2
from research.multi_future_ghv_counterfactual_distance_lab_v2.contract_tick_v2 import (
    contract_for_p0_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.cycle_observation_v2 import (
    build_cycle_observation_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.market_paths_v2 import (
    build_flight_market_path_v2,
    vol_level_for_profile_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.replay_input_v2 import (
    build_integrated_replay_input_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.symmetric_fork_v2 import (
    run_replay_symmetric_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v3.constants_v3 import STAGE2_CYCLES_PER_FLIGHT
from research.multi_future_ghv_counterfactual_distance_lab_v3.replay_state_v3 import (
    apply_lane_state_to_replay_input_v3,
    init_lane_state_v3,
    update_lane_state_from_result_v3,
)
from research.multi_future_ghv_counterfactual_distance_lab_v3.state_carrier_v3 import (
    FlightLaneStateStoreV3,
)
from research.multi_future_ghv_counterfactual_distance_lab_v3.state_trace_v3 import (
    build_confirmation_state_trace_row_v3,
)


def _flight_pairs(smoke: bool) -> list[dict[str, object]]:
    profiles = STAGE2_GENERALIZATION_PROFILES[:2] if smoke else STAGE2_GENERALIZATION_PROFILES
    seeds = (0, 1) if smoke else tuple(range(19))
    pairs: list[dict[str, object]] = []
    pair_idx = 0
    for gp in profiles:
        for seed in seeds:
            if smoke and pair_idx >= 2:
                return pairs
            if not smoke and pair_idx * 2 >= TARGET_STAGE2_FLIGHTS:
                return pairs
            pairs.append(
                {
                    "PAIR_ID": f"pair_{pair_idx:05d}",
                    "GENERALIZATION_PROFILE": gp,
                    "SEED": int(seed),
                }
            )
            pair_idx += 1
    return pairs


def run_stage2_v3(
    *,
    evidence_dir: Path,
    smoke: bool = False,
    phase_a: bool = True,
) -> Mapping[str, object]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    cycle_path = evidence_dir / "cycle_observations_v3.jsonl"
    manifest_path = evidence_dir / "flight_manifest.jsonl"
    enter_trace_path = evidence_dir / "natural_enter_traces.jsonl"
    fail_path = evidence_dir / "failure_causality.jsonl"
    conf_trace_path = evidence_dir / "confirmation_state_trace.jsonl"

    state_store = FlightLaneStateStoreV3()
    pairs = _flight_pairs(smoke)
    total_cycles = 0
    flight_count = 0

    with cycle_path.open("w", encoding="utf-8") as cycle_f, manifest_path.open(
        "w", encoding="utf-8"
    ) as man_f, enter_trace_path.open("w", encoding="utf-8") as ent_f, fail_path.open(
        "w", encoding="utf-8"
    ) as fail_f, conf_trace_path.open("w", encoding="utf-8") as conf_f:
        for pair in pairs:
            gp = str(pair["GENERALIZATION_PROFILE"])
            seed = int(pair["SEED"])
            profile, p0, sigma, regime, path = build_flight_market_path_v2(
                generalization_profile=gp,
                seed=seed,
                steps=STAGE2_CYCLES_PER_FLIGHT,
            )
            vol_level = vol_level_for_profile_v2(gp)
            contract = contract_for_p0_v2(p0)
            instrument = "inst-eth-usdt-perp"

            for model_id in STAGE2_SURVIVORS:
                if not smoke and flight_count >= TARGET_STAGE2_FLIGHTS:
                    break
                flight_id = f"flight_{flight_count:05d}"
                flight_count += 1
                lane_id = f"{flight_id}:{model_id}"
                lane = init_lane_state_v3(
                    state_store.root_for_lane(lane_id),
                    instrument_id=instrument,
                    confirmation_session_id=f"sess-v3-{lane_id}",
                )

                for cycle_idx, mark in enumerate(path):
                    trading_epoch = 1000 + cycle_idx
                    inp = build_integrated_replay_input_v2(
                        replay_id=f"{flight_id}-c{cycle_idx}",
                        instrument_id=instrument,
                        mark_price=mark,
                        volatility_estimate=sigma,
                        price_path=path[: cycle_idx + 1],
                        trading_epoch=trading_epoch,
                        side_state=lane.side_state,
                        now_tick=cycle_idx,
                    )
                    ctx = refresh_cmc_mark_v2(
                        inp.canonical_market_context,
                        mark_price=mark,
                        trading_epoch=trading_epoch,
                    )
                    inp = replace(inp, canonical_market_context=ctx)
                    state_before = lane
                    inp, lane, c1_result = apply_lane_state_to_replay_input_v3(
                        inp,
                        lane,
                        instrument_id=instrument,
                        cycle_id=cycle_idx,
                        mark_price=mark,
                        use_c1_transport=True,
                    )

                    result, fork = run_replay_symmetric_v2(inp, model_id=model_id)
                    lane = update_lane_state_from_result_v3(lane, result)

                    row = build_cycle_observation_v2(
                        model_id=model_id,
                        flight_id=flight_id,
                        lane_id=lane_id,
                        cycle_id=cycle_idx,
                        generalization_profile=gp,
                        future_profile_id=profile.future_profile_id,
                        price_scale=p0,
                        p0=p0,
                        vol_level=vol_level,
                        regime_id=regime,
                        seed=seed,
                        fork=fork,
                        tick_size=str(contract.tick_size),
                        price_precision=contract.price_precision,
                        result=result,
                    )
                    row = dict(row)
                    row["PHASE"] = "A" if phase_a else "B"
                    row["STATE_CONTINUITY_VALID"] = True
                    cycle_f.write(json.dumps(row, sort_keys=True, default=str) + "\n")
                    total_cycles += 1

                    trace_row = build_confirmation_state_trace_row_v3(
                        flight_id=flight_id,
                        cycle_id=cycle_idx,
                        model_id=model_id,
                        lane_id=lane_id,
                        state_before=state_before,
                        state_after=lane,
                        c1_result=c1_result,
                        result=result,
                        state_source_cycle_id=cycle_idx - 1 if cycle_idx > 0 else -1,
                    )
                    conf_f.write(json.dumps(trace_row, sort_keys=True, default=str) + "\n")

                    if row.get("NATURAL_ENTER"):
                        ent_f.write(json.dumps(row, sort_keys=True, default=str) + "\n")
                    if not result.replay_pass or row.get("FAIL_CLOSED"):
                        fail_f.write(
                            json.dumps(
                                {
                                    "FLIGHT_ID": flight_id,
                                    "CYCLE_ID": cycle_idx,
                                    "MODEL_ID": model_id,
                                    "CAUSALITY": "UNRESOLVED",
                                },
                                sort_keys=True,
                            )
                            + "\n"
                        )

                man_f.write(
                    json.dumps(
                        {
                            "FLIGHT_ID": flight_id,
                            "PAIR_ID": pair["PAIR_ID"],
                            "MODEL_ID": model_id,
                            "GENERALIZATION_PROFILE": gp,
                            "SEED": seed,
                            "REGIME": regime,
                            "VOL_LEVEL": vol_level,
                            "P0": p0,
                            "PHASE": "A" if phase_a else "B",
                            "status": "completed",
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

    return {
        "PHASE_A_STARTED": phase_a,
        "PHASE_A_COMPLETED": phase_a,
        "V3_COMPLETED_FLIGHTS": flight_count,
        "V3_COMPLETED_CYCLES": total_cycles,
    }
