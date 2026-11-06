from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Mapping, Sequence

from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import (
    STAGE2_GENERALIZATION_PROFILES,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.constants_v2 import (
    EXPERIMENT_ID,
    STAGE2_CYCLES_PER_FLIGHT,
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
    last_distance_fork_snapshot_v2,
    run_replay_symmetric_v2,
)
from trading.master_v2.double_play_state import SideState


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


def run_stage2_v2(
    *,
    evidence_dir: Path,
    smoke: bool = False,
) -> Mapping[str, object]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    cycle_path = evidence_dir / "cycle_observations_v2.jsonl"
    manifest_path = evidence_dir / "flight_manifest.jsonl"
    enter_trace_path = evidence_dir / "natural_enter_traces.jsonl"
    fail_path = evidence_dir / "failure_causality.jsonl"

    pairs = _flight_pairs(smoke)
    total_cycles = 0
    flight_count = 0

    with cycle_path.open("w", encoding="utf-8") as cycle_f, manifest_path.open(
        "w", encoding="utf-8"
    ) as man_f, enter_trace_path.open("w", encoding="utf-8") as ent_f, fail_path.open(
        "w", encoding="utf-8"
    ) as fail_f:
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

            for model_idx, model_id in enumerate(STAGE2_SURVIVORS):
                if not smoke and flight_count >= TARGET_STAGE2_FLIGHTS:
                    break
                flight_id = f"flight_{flight_count:05d}"
                flight_count += 1
                lane_id = f"{flight_id}:{model_id}"
                side_state = SideState.LONG_ARMED
                runtime_scope_state = None
                existing_scope = None
                confirmation_progress = None

                for cycle_idx, mark in enumerate(path):
                    trading_epoch = 1000 + cycle_idx
                    inp = build_integrated_replay_input_v2(
                        replay_id=f"{flight_id}-c{cycle_idx}",
                        instrument_id=instrument,
                        mark_price=mark,
                        volatility_estimate=sigma,
                        price_path=path[: cycle_idx + 1],
                        trading_epoch=trading_epoch,
                        side_state=side_state,
                        now_tick=cycle_idx,
                    )
                    ctx = refresh_cmc_mark_v2(
                        inp.canonical_market_context,
                        mark_price=mark,
                        trading_epoch=trading_epoch,
                    )
                    inp = replace(inp, canonical_market_context=ctx)
                    if existing_scope is not None:
                        inp = replace(inp, existing_scope=existing_scope)
                    if runtime_scope_state is not None:
                        inp = replace(
                            inp,
                            runtime_scope_state=runtime_scope_state,
                            runtime_scope_bound_instrument_id=instrument,
                        )
                    if confirmation_progress is not None:
                        inp = replace(inp, directional_confirmation_progress=confirmation_progress)

                    result, fork = run_replay_symmetric_v2(inp, model_id=model_id)
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
                    cycle_f.write(json.dumps(row, sort_keys=True, default=str) + "\n")
                    total_cycles += 1

                    if row.get("NATURAL_ENTER"):
                        ent_f.write(json.dumps(row, sort_keys=True, default=str) + "\n")
                    if not result.replay_pass or row.get("FAIL_CLOSED"):
                        causality = {
                            "FLIGHT_ID": flight_id,
                            "CYCLE_ID": cycle_idx,
                            "MODEL_ID": model_id,
                            "FAIL_CLOSED": row.get("FAIL_CLOSED"),
                            "REPLAY_FAIL_REASON_CODES": row.get("REPLAY_FAIL_REASON_CODES"),
                            "FAIL_CLOSED_REASON_CODES": row.get("FAIL_CLOSED_REASON_CODES"),
                            "CAUSALITY": "UNRESOLVED",
                            "NOTE": "No per-layer trace in v2 row for automatic DISTANCE_CAUSED classification.",
                        }
                        fail_f.write(json.dumps(causality, sort_keys=True) + "\n")

                    if result.intermediate is not None:
                        im = result.intermediate
                        existing_scope = im.current_scope
                        runtime_scope_state = im.runtime_scope_state_after
                        confirmation_progress = im.directional_confirmation_progress_after
                        try:
                            side_state = SideState(im.state_switch.next_side_state)
                        except Exception:
                            pass

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
                            "status": "completed",
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )

    return {
        "STAGE2_V2_PLANNED_FLIGHTS": min(TARGET_STAGE2_FLIGHTS, len(pairs) * len(STAGE2_SURVIVORS))
        if not smoke
        else min(4, len(pairs) * len(STAGE2_SURVIVORS)),
        "STAGE2_V2_COMPLETED_FLIGHTS": flight_count,
        "STAGE2_V2_COMPLETED_CYCLES": total_cycles,
    }
