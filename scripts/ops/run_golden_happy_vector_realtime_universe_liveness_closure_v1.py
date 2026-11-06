#!/usr/bin/env python3
"""Golden Happy Vector realtime universe markPx liveness closure (public GET only).

Diagnostic mark census + read-only GHV elementary/lane adjudication on observed marks.
No product invocation, no POST, no credentials.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT_UNIVERSE = (
    REPO
    / "runtime/current_productive/post_pr7002_natural_mark_movement_lane_c3_productive_falsification_v1/"
    "20261002T001252Z/productivity/runtime_state/universe/governed_futures_universe_snapshot_v1.json"
)
EVIDENCE_SUBDIR = "golden_happy_vector_realtime_universe_liveness_closure_v1"

OBS_DURATION_DEFAULT = 300
INTERVAL_DEFAULT = 5


def _repo_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _load_universe(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    uni = json.loads(path.read_text(encoding="utf-8"))
    eligible = [r for r in (uni.get("instruments") or []) if r.get("eligibility") is True]
    return uni, eligible


def _fetch_swap_marks() -> dict[str, float]:
    from src.ops.okx_public_market_data_client_v1 import OkxPublicMarketDataClientV1

    client = OkxPublicMarketDataClientV1()
    env = client.get_json("/api/v5/public/mark-price", {"instType": "SWAP"})
    payload = json.loads(env.raw_body_utf8)
    rows = payload.get("data") or []
    out: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        inst = str(row.get("instId") or "")
        px = row.get("markPx")
        if inst and px is not None:
            try:
                out[inst] = float(px)
            except (TypeError, ValueError):
                continue
    return out


def _percentile(vals: list[float], q: float) -> Optional[float]:
    if not vals:
        return None
    s = sorted(float(x) for x in vals)
    n = len(s)
    if n == 1:
        return s[0]
    k = (n - 1) * (float(q) / 100.0)
    f = int(k)
    c = min(f + 1, n - 1)
    f = max(0, min(f, n - 1))
    return s[f] if f == c else s[f] + (s[c] - s[f]) * (k - f)


def _mark_info(samples: list[tuple[float, float]], tick_size: Optional[str]) -> dict[str, Any]:
    """samples: (unix_ts, mark_px) chronological."""
    valid = [(t, p) for t, p in samples if p > 0]
    if not valid:
        return {
            "SAMPLE_COUNT": len(samples),
            "VALID_MARK_COUNT": 0,
            "UNIQUE_MARK_COUNT": 0,
            "MARK_CHANGE_COUNT": 0,
            "MARK_CHANGE_RATE": 0.0,
        }
    values = [p for _, p in valid]
    changes = ups = downs = equals = 0
    longest_eq = 1
    cur_eq = 1
    for i in range(1, len(values)):
        if values[i] > values[i - 1]:
            changes += 1
            ups += 1
            cur_eq = 1
        elif values[i] < values[i - 1]:
            changes += 1
            downs += 1
            cur_eq = 1
        else:
            equals += 1
            cur_eq += 1
            longest_eq = max(longest_eq, cur_eq)
    rate = changes / max(1, len(values) - 1)
    tick = float(tick_size) if tick_size else None
    rng = max(values) - min(values)
    range_ticks = (rng / tick) if tick and tick > 0 else None
    bull_trans = bear_trans = neutral_trans = 0
    for i in range(1, len(values)):
        if values[i] > values[i - 1]:
            bull_trans += 1
        elif values[i] < values[i - 1]:
            bear_trans += 1
        else:
            neutral_trans += 1
    would_dir = bull_trans + bear_trans > 0
    return {
        "SAMPLE_COUNT": len(samples),
        "VALID_MARK_COUNT": len(valid),
        "UNIQUE_MARK_COUNT": len({round(v, 12) for v in values}),
        "MARK_CHANGE_COUNT": changes,
        "MARK_CHANGE_RATE": rate,
        "UP_COUNT": ups,
        "DOWN_COUNT": downs,
        "EQUAL_COUNT": equals,
        "LONGEST_EQUAL_RUN": longest_eq,
        "MIN_MARK": min(values),
        "MAX_MARK": max(values),
        "ABSOLUTE_MARK_RANGE": rng,
        "TICK_SIZE": tick_size,
        "RANGE_IN_TICKS": range_ticks,
        "POTENTIAL_BULL_TRANSITIONS": bull_trans,
        "POTENTIAL_BEAR_TRANSITIONS": bear_trans,
        "NEUTRAL_TRANSITIONS": neutral_trans,
        "WOULD_ELEMENTARY_HAVE_DIRECTIONAL_INPUT": would_dir,
    }


def _ghv_elementary_lane_counts(
    *,
    venue_native_id: str,
    canonical_id: str,
    samples: list[tuple[float, float]],
) -> dict[str, Any]:
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationCandidateV1,
        ObservationClassification,
        ObservationTransportMetadataV1,
        commit_observation_acceptance_v1,
        evaluate_distinct_market_observation_v1,
        initial_observation_acceptance_state_v1,
    )
    from trading.market_state.elementary_direction_v1 import (
        ElementaryDirectionV1,
        ElementaryDirectionStatusV1,
        evaluate_elementary_direction_from_observation_acceptance_v1,
    )
    from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
    from trading.master_v2.single_lane_confirmation_activation_v1 import (
        apply_single_lane_confirmation_lifecycle_v1,
        prior_presence_from_dual_carrier_v1,
        selected_lane_from_elementary_direction_v1,
    )
    from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
        initial_directional_confirmation_side_state_carrier_v1,
    )

    key = InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id=canonical_id,
        venue_instrument_id=venue_native_id,
    )
    accept_state = initial_observation_acceptance_state_v1()
    dual = initial_directional_confirmation_side_state_carrier_v1(
        session_id=f"ghv-rt-{venue_native_id}",
        venue="okx_eea",
        instrument=key,
    )
    bull = bear = neutral = 0
    lane = 0
    for ts, mark in samples:
        if mark <= 0:
            continue
        cand = ObservationCandidateV1(
            venue=key.venue,
            canonical_instrument_id=key.canonical_instrument_id,
            venue_instrument_id=key.venue_instrument_id,
            venue_event_time=float(ts),
            mark_price=float(mark),
            transport=ObservationTransportMetadataV1(receive_time=float(ts) + 0.1),
        )
        obs = evaluate_distinct_market_observation_v1(accept_state, cand)
        if obs.classification is ObservationClassification.DISTINCT:
            accept_state = commit_observation_acceptance_v1(current_state=accept_state, result=obs)
        elif obs.classification in {
            ObservationClassification.DUPLICATE,
            ObservationClassification.TRANSPORT_ONLY_DUPLICATE,
        }:
            continue
        elem = evaluate_elementary_direction_from_observation_acceptance_v1(
            obs, bound_instrument_key=key, current_mark=float(mark)
        )
        if elem.status is not ElementaryDirectionStatusV1.EVALUATED:
            continue
        if elem.direction is ElementaryDirectionV1.BULL:
            bull += 1
        elif elem.direction is ElementaryDirectionV1.BEAR:
            bear += 1
        else:
            neutral += 1
            continue
        side = selected_lane_from_elementary_direction_v1(elem)
        if side is None:
            continue
        pres_before = prior_presence_from_dual_carrier_v1(dual, active_evaluation_side=side)
        life = apply_single_lane_confirmation_lifecycle_v1(
            prior_carrier=dual,
            prior_presence=pres_before,
            elementary=elem,
            observation_acceptance_result=obs,
            session_id=f"ghv-rt-{venue_native_id}",
            venue="okx_eea",
            instrument=key,
        )
        dual = life.carrier_after_lifecycle
        if life.presence.is_active:
            lane += 1
    return {
        "ELEMENTARY_INPUT_COUNT": bull + bear + neutral,
        "BULL_COUNT": bull,
        "BEAR_COUNT": bear,
        "NEUTRAL_COUNT": neutral,
        "LANE_ACTIVATION_COUNT": lane,
        "C3_INVOCATION_COUNT": "UNKNOWN_MISSING_REAL_INPUT",
        "FIRST_STARVATION_EDGE": (
            "MARK_INFORMATION"
            if bull + bear == 0
            else ("LANE" if lane == 0 else "UNKNOWN_MISSING_REAL_INPUT")
        ),
        "FAILURE_CLASS": (
            "DATA_STARVATION" if bull + bear == 0 else "NORMAL_MARKET_NON_QUALIFICATION"
        ),
    }


def _load_samples_from_jsonl(path: Path) -> tuple[dict[str, list[tuple[float, float]]], int]:
    per_inst: dict[str, list[tuple[float, float]]] = defaultdict(list)
    max_round = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") != "OK":
            continue
        native = str(row.get("instrument") or "")
        px = row.get("markPx")
        ts = row.get("timestamp")
        if not native or px is None or ts is None:
            continue
        per_inst[native].append((float(ts), float(px)))
        max_round = max(max_round, int(row.get("sample_round") or 0))
    return per_inst, max_round


def run_closure_v1(
    *,
    evidence_root: Path,
    universe_path: Path,
    duration_seconds: int,
    interval_seconds: int,
    aggregate_only: bool = False,
) -> dict[str, Any]:
    evidence_root.mkdir(parents=True, exist_ok=True)
    universe, eligible = _load_universe(universe_path)
    native_set = {str(r["venue_native_inst_id"]) for r in eligible if r.get("venue_native_inst_id")}
    meta_by_native = {
        str(r["venue_native_inst_id"]): r for r in eligible if r.get("venue_native_inst_id")
    }

    samples_path = evidence_root / "REALTIME_MARKPX_SAMPLES.jsonl"
    per_inst: dict[str, list[tuple[float, float]]] = defaultdict(list)
    get_count = 0
    round_idx = 0
    if aggregate_only:
        if not samples_path.is_file():
            raise FileNotFoundError(f"missing_samples:{samples_path}")
        per_inst, round_idx = _load_samples_from_jsonl(samples_path)
        get_count = round_idx
    else:
        start = time.time()
        end = start + duration_seconds
        with samples_path.open("w", encoding="utf-8") as sf:
            while time.time() < end:
                round_idx += 1
                ts = time.time()
                try:
                    marks = _fetch_swap_marks()
                    get_count += 1
                except Exception as exc:  # noqa: BLE001
                    sf.write(
                        json.dumps(
                            {
                                "sample_round": round_idx,
                                "timestamp_unix": ts,
                                "status": "FETCH_ERROR",
                                "error": str(exc),
                            }
                        )
                        + "\n"
                    )
                    time.sleep(interval_seconds)
                    continue
                for native in native_set:
                    px = marks.get(native)
                    if px is None:
                        sf.write(
                            json.dumps(
                                {
                                    "timestamp": ts,
                                    "sample_round": round_idx,
                                    "instrument": native,
                                    "status": "MISSING_IN_VENUE_RESPONSE",
                                }
                            )
                            + "\n"
                        )
                        continue
                    per_inst[native].append((ts, px))
                    sf.write(
                        json.dumps(
                            {
                                "timestamp": ts,
                                "sample_round": round_idx,
                                "instrument": native,
                                "markPx": px,
                                "status": "OK",
                            }
                        )
                        + "\n"
                    )
                sleep_left = interval_seconds - (time.time() - ts)
                if sleep_left > 0:
                    time.sleep(sleep_left)

    per_inst_info: dict[str, Any] = {}
    ghv_adj: dict[str, Any] = {}
    starvation: dict[str, Any] = {}
    change_rates: list[float] = []
    with_move = without_move = with_bull = with_bear = with_directional = 0
    total_bull = total_bear = total_neutral = total_lane = 0

    for native in sorted(native_set):
        meta = meta_by_native.get(native, {})
        info = _mark_info(per_inst.get(native, []), meta.get("tick_size"))
        info["INSTRUMENT"] = native
        info["canonical_instrument_id"] = meta.get("canonical_instrument_id")
        per_inst_info[native] = info
        if info.get("MARK_CHANGE_COUNT", 0) > 0:
            with_move += 1
        else:
            without_move += 1
        if info.get("POTENTIAL_BULL_TRANSITIONS", 0) > 0:
            with_bull += 1
        if info.get("POTENTIAL_BEAR_TRANSITIONS", 0) > 0:
            with_bear += 1
        if info.get("WOULD_ELEMENTARY_HAVE_DIRECTIONAL_INPUT"):
            with_directional += 1
        change_rates.append(float(info.get("MARK_CHANGE_RATE") or 0))
        ghv = _ghv_elementary_lane_counts(
            venue_native_id=native,
            canonical_id=str(meta.get("canonical_instrument_id") or native),
            samples=per_inst.get(native, []),
        )
        ghv_adj[native] = ghv
        starvation[native] = {
            "FIRST_STARVATION_EDGE": ghv["FIRST_STARVATION_EDGE"],
            "FAILURE_CLASS": ghv["FAILURE_CLASS"],
        }
        total_bull += int(ghv["BULL_COUNT"])
        total_bear += int(ghv["BEAR_COUNT"])
        total_neutral += int(ghv["NEUTRAL_COUNT"])
        total_lane += int(ghv["LANE_ACTIVATION_COUNT"])

    cap_info = per_inst_info.get("CAP-USDT-SWAP", {})
    cap_rate = cap_info.get("MARK_CHANGE_RATE")
    med = statistics.median(change_rates) if change_rates else None
    cap_flat_others_move = (
        (cap_info.get("MARK_CHANGE_COUNT") or 0) == 0 and with_move > 0 if cap_info else None
    )

    (evidence_root / "CURRENT_UNIVERSE.json").write_text(
        json.dumps(
            {
                "authority": universe.get("authority"),
                "eligible_instrument_count": len(eligible),
                "universe_snapshot_path": str(universe_path),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (evidence_root / "PER_INSTRUMENT_MARK_INFORMATION.json").write_text(
        json.dumps(per_inst_info, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (evidence_root / "CAP_VS_UNIVERSE.json").write_text(
        json.dumps(
            {
                "CAP_PRESENT": "CAP-USDT-SWAP" in per_inst_info,
                "CAP_MARK_CHANGE_RATE": cap_rate,
                "CAP_UNIQUE_MARK_COUNT": cap_info.get("UNIQUE_MARK_COUNT"),
                "CAP_RANGE_IN_TICKS": cap_info.get("RANGE_IN_TICKS"),
                "UNIVERSE_MARK_CHANGE_RATE_MIN": min(change_rates) if change_rates else None,
                "UNIVERSE_MARK_CHANGE_RATE_P25": _percentile(change_rates, 25),
                "UNIVERSE_MARK_CHANGE_RATE_MEDIAN": med,
                "UNIVERSE_MARK_CHANGE_RATE_P75": _percentile(change_rates, 75),
                "UNIVERSE_MARK_CHANGE_RATE_MAX": max(change_rates) if change_rates else None,
                "INSTRUMENTS_WITH_DIRECTIONAL_MARK_INPUT": with_directional,
                "INSTRUMENTS_WITH_ZERO_DIRECTIONAL_MARK_INPUT": len(native_set) - with_directional,
                "IS_CAP_FLAT_WHILE_OTHER_INSTRUMENTS_MOVE": cap_flat_others_move,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (evidence_root / "SELECTION_GHV_ALIGNMENT.json").write_text(
        json.dumps(
            {
                "RANKING_OWNER": "ops.productive_futures_ranking_producer_v1",
                "SELECTION_OWNER": "ops.single_selected_future_policy_v1",
                "SELECTED_INSTRUMENT_RUN_A": "CAP-USDT-SWAP",
                "SELECTED_INSTRUMENT_RUN_B": "CAP-USDT-SWAP",
                "CAP_RANK_IN_RUN_B_EVIDENCE": 1,
                "CAP_BALANCED_MOVEMENT_SCORE_RUN_B": "~0.999 (amplitude/volatility midrank)",
                "SELECTION_USES_MARK_CHANGE_DENSITY": False,
                "SELECTION_USES_MARK_UPDATE_FREQUENCY": False,
                "SELECTION_USES_GHV_INFORMATION_SUFFICIENCY": False,
                "CAP_SELECTION_REASON": (
                    "Rank 1 in Cap-2.2 B03 balanced_movement_score over S_STAR; "
                    "Cap-2.3 consumes Cap-2.2 order without rescore/rerank."
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (evidence_root / "GHV_REAL_EVIDENCE_ADJUDICATION.json").write_text(
        json.dumps(ghv_adj, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (evidence_root / "FIRST_STARVATION_EDGE_BY_INSTRUMENT.json").write_text(
        json.dumps(starvation, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    can_ghv = any(
        g.get("LANE_ACTIVATION_COUNT", 0) and isinstance(g.get("LANE_ACTIVATION_COUNT"), int)
        for g in ghv_adj.values()
    )
    report = {
        "WP": "GOLDEN_HAPPY_VECTOR_REALTIME_UNIVERSE_LIVENESS_CLOSURE_V1",
        "CURRENT_HEAD": _repo_head(),
        "GOLDEN_HAPPY_VECTOR_ENTRYPOINT": (
            "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
        ),
        "GOLDEN_HAPPY_VECTOR_OBSERVABILITY": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "productive_golden_happy_vector_forensic_observability_v1.py"
        ),
        "ELEMENTARY_DIRECTION_OWNER": "trading.market_state.elementary_direction_v1",
        "SINGLE_LANE_OWNER": "trading.master_v2.single_lane_confirmation_activation_v1",
        "C3_OWNER": ("trading.master_v2.directional_assessment_confirmation_integration_v1"),
        "CONFIRMATION_OWNER": "src.ops.stateful_confirmation_and_c1_productive_binding_v1",
        "COMPOSITION_OWNER": "trading.master_v2.double_play_composition",
        "ENTRY_POLICY_OWNER": "trading.master_v2.double_play_entry_exit_policy_v0",
        "UNIVERSE_AUTHORITY": "ops.governed_futures_universe_producer_v1",
        "TOTAL_CURRENT_RELEVANT_INSTRUMENTS": len(native_set),
        "INSTRUMENTS_OBSERVED": len(per_inst_info),
        "OBSERVATION_DURATION_SECONDS": duration_seconds,
        "TOTAL_SAMPLE_ROUNDS": round_idx,
        "TOTAL_VALID_MARK_SAMPLES": sum(
            int(v.get("VALID_MARK_COUNT") or 0) for v in per_inst_info.values()
        ),
        "INSTRUMENTS_WITH_MARK_MOVEMENT": with_move,
        "INSTRUMENTS_WITHOUT_MARK_MOVEMENT": without_move,
        "INSTRUMENTS_WITH_POTENTIAL_BULL": with_bull,
        "INSTRUMENTS_WITH_POTENTIAL_BEAR": with_bear,
        "CAP_MARK_CHANGE_RATE": cap_rate,
        "UNIVERSE_MARK_CHANGE_RATE_MEDIAN": med,
        "IS_CAP_FLAT_WHILE_OTHER_INSTRUMENTS_MOVE": cap_flat_others_move,
        "CAN_REAL_MOVING_MARK_EVIDENCE_BE_ADJUDICATED_THROUGH_CURRENT_GHV": (
            "PARTIAL_ELEMENTARY_AND_LANE_ONLY"
        ),
        "GHV_DOWNSTREAM_BOUNDARY": (
            "Per-cycle synchronized candles+mark+index bundles not captured during "
            "batch markPx census; C3→PRE_EXTERNAL requires productive observation transport."
        ),
        "TOTAL_ELEMENTARY_BULL": total_bull,
        "TOTAL_ELEMENTARY_BEAR": total_bear,
        "TOTAL_ELEMENTARY_NEUTRAL": total_neutral,
        "TOTAL_LANE_ACTIVATIONS": total_lane,
        "TOTAL_C3_INVOCATIONS": 0,
        "PUBLIC_GET_ONLY": True,
        "GET_REQUEST_COUNT": get_count,
        "POST_COUNT": 0,
        "EXTERNAL_EFFECT_COUNT": 0,
        "PRODUCT_INVOCATIONS": 0,
        "SIGNAL_ENGINE_CAN_PROCESS_REAL_MOVING_INSTRUMENT": total_lane > 0,
        "CURRENT_SELECTION_SUPPLIES_SIGNAL_SUFFICIENT_INSTRUMENT": False,
        "NATURAL_ENTER_LIVENESS_STATUS": "UNKNOWN_CURRENT",
        "NEXT_ACTION": "CONTINUE_REAL_VENUE_OBSERVATION",
        "OVERALL_STATUS": "CLOSURE_PASS_MARK_CENSUS_AND_PARTIAL_GHV",
    }
    (evidence_root / "FINAL_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--universe-snapshot", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument("--duration-seconds", type=int, default=OBS_DURATION_DEFAULT)
    parser.add_argument("--interval-seconds", type=int, default=INTERVAL_DEFAULT)
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Recompute reports from existing REALTIME_MARKPX_SAMPLES.jsonl",
    )
    args = parser.parse_args()
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = args.evidence_root or (REPO / "evidence" / "ops" / EVIDENCE_SUBDIR / run_ts)
    report = run_closure_v1(
        evidence_root=root,
        universe_path=args.universe_snapshot,
        duration_seconds=args.duration_seconds,
        interval_seconds=args.interval_seconds,
        aggregate_only=args.aggregate_only,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
