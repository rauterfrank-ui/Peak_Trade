from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence

from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import (
    EXPERIMENT_ID,
    STAGE2_CYCLES_PER_FLIGHT,
    STAGE2_GENERALIZATION_PROFILES,
    TARGET_STAGE2_FLIGHTS,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.counterfactual_replay_v1 import (
    run_counterfactual_integrated_replay_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.replay_fixtures_v1 import (
    build_integrated_replay_input_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.synthetic_market_v1 import (
    generalization_future_profile_v1,
    p0_from_price_tag,
    generate_price_path_v1,
    sigma_for_profile,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.trading_logic_digest_v1 import (
    replay_semantic_digest_v1,
)
from trading.master_v2.double_play_state import SideState


def _flight_plan(survivors: Sequence[str], smoke: bool) -> list[dict[str, object]]:
    profiles = STAGE2_GENERALIZATION_PROFILES[:2] if smoke else STAGE2_GENERALIZATION_PROFILES
    seed_variants = (0, 1) if smoke else tuple(range(19))
    flights: list[dict[str, object]] = []
    fid = 0
    for model_id in survivors:
        for gp in profiles:
            for seed in seed_variants:
                if smoke and fid >= 4:
                    return flights
                if not smoke and fid >= TARGET_STAGE2_FLIGHTS:
                    return flights
                flights.append(
                    {
                        "FLIGHT_ID": f"flight_{fid:05d}",
                        "MODEL_ID": model_id,
                        "GENERALIZATION_PROFILE": gp,
                        "SEED": int(seed),
                    }
                )
                fid += 1
    return flights


def run_stage2_flights_v1(
    *,
    evidence_dir: Path,
    survivor_models: Sequence[str],
    smoke: bool = False,
    completed_flights: frozenset[str] = frozenset(),
) -> Mapping[str, object]:
    flights = _flight_plan(survivor_models, smoke)
    cycle_path = evidence_dir / "cycle_observations.jsonl"
    cons_path = evidence_dir / "system_consequences.jsonl"
    manifest_path = evidence_dir / "flight_manifest.jsonl"

    cycles_done = 0
    metrics: MutableMapping[str, MutableMapping[str, int]] = {}

    with cycle_path.open("a", encoding="utf-8") as cycle_f, cons_path.open(
        "a", encoding="utf-8"
    ) as cons_f, manifest_path.open("a", encoding="utf-8") as man_f:
        for flight in flights:
            flight_id = str(flight["FLIGHT_ID"])
            if flight_id in completed_flights:
                continue
            model_id = str(flight["MODEL_ID"])
            gp = str(flight["GENERALIZATION_PROFILE"])
            seed = int(flight["SEED"])
            profile = generalization_future_profile_v1(gp)
            price_tag = next(t for t in profile.tags if t.endswith("_PRICE"))
            p0 = p0_from_price_tag(price_tag)
            sigma = sigma_for_profile(vol_level="MEDIUM", profile=profile, mode="MODE_B")
            path = generate_price_path_v1(
                p0=p0,
                sigma=sigma,
                profile=profile,
                regime_id="R02",
                seed=seed,
                mode="MODE_B",
                steps=STAGE2_CYCLES_PER_FLIGHT,
            )
            instrument = f"lab-{profile.future_profile_id}"
            side_state = SideState.LONG_ARMED
            runtime_scope_state = None
            existing_scope = None
            flight_metrics = {
                "HOLD_COUNT": 0,
                "ENTER_LONG_COUNT": 0,
                "ENTER_SHORT_COUNT": 0,
                "EXIT_COUNT": 0,
                "SWITCH_COUNT": 0,
                "PRE_EXTERNAL_REACHED_COUNT": 0,
                "EXECUTION_ELIGIBLE_COUNT": 0,
                "29P_FAIL_COUNT": 0,
            }
            for cycle_idx, mark in enumerate(path):
                inp = build_integrated_replay_input_v1(
                    instrument_id=instrument,
                    mark_price=mark,
                    volatility_estimate=sigma,
                    price_path=path[: cycle_idx + 1],
                    trading_epoch=100 + cycle_idx,
                    side_state=side_state,
                    now_tick=cycle_idx,
                    replay_id=f"{flight_id}-cycle-{cycle_idx}",
                )
                if existing_scope is not None:
                    inp = replace(inp, existing_scope=existing_scope)
                if runtime_scope_state is not None:
                    inp = replace(
                        inp,
                        runtime_scope_state=runtime_scope_state,
                        runtime_scope_bound_instrument_id=instrument,
                    )
                result = run_counterfactual_integrated_replay_v1(
                    inp,
                    model_id=model_id,
                )
                ev = result.evidence
                outcome = ev.decision_outcome
                if outcome == "hold":
                    flight_metrics["HOLD_COUNT"] += 1
                elif outcome == "enter_long":
                    flight_metrics["ENTER_LONG_COUNT"] += 1
                elif outcome == "enter_short":
                    flight_metrics["ENTER_SHORT_COUNT"] += 1
                elif outcome.startswith("exit"):
                    flight_metrics["EXIT_COUNT"] += 1
                if ev.execution_eligible:
                    flight_metrics["EXECUTION_ELIGIBLE_COUNT"] += 1
                if not result.replay_pass:
                    flight_metrics["29P_FAIL_COUNT"] += 1
                if ev.authority_effect == "NONE" and ev.order_effect == "NONE":
                    flight_metrics["PRE_EXTERNAL_REACHED_COUNT"] += 1
                cycle_row = {
                    "EXPERIMENT_ID": EXPERIMENT_ID,
                    "FLIGHT_ID": flight_id,
                    "LANE_ID": f"{flight_id}:{model_id}",
                    "CYCLE_ID": cycle_idx,
                    "MODEL_ID": model_id,
                    "decision_outcome": outcome,
                    "semantic_digest": replay_semantic_digest_v1(result),
                    "execution_eligible": ev.execution_eligible,
                    "replay_pass": result.replay_pass,
                }
                cycle_f.write(json.dumps(cycle_row, sort_keys=True) + "\n")
                cycles_done += 1
                if result.intermediate is not None:
                    im = result.intermediate
                    existing_scope = im.current_scope
                    runtime_scope_state = im.runtime_scope_state_after
                    try:
                        side_state = SideState(im.state_switch.next_side_state)
                    except Exception:
                        pass
            cons_row = {
                "EXPERIMENT_ID": EXPERIMENT_ID,
                "FLIGHT_ID": flight_id,
                "MODEL_ID": model_id,
                **flight_metrics,
            }
            cons_f.write(json.dumps(cons_row, sort_keys=True) + "\n")
            metrics[flight_id] = flight_metrics
            man_f.write(json.dumps({**flight, "status": "completed"}, sort_keys=True) + "\n")

    summary = {
        "STAGE2_PLANNED_FLIGHTS": len(flights),
        "STAGE2_COMPLETED_FLIGHTS": len(metrics),
        "STAGE2_COMPLETED_CYCLES": cycles_done,
    }
    (evidence_dir / "stage2_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary
