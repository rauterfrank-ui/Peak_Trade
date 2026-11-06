from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def aggregate_post_run_v2(evidence_dir: Path) -> Mapping[str, object]:
    cycles = _load_jsonl(evidence_dir / "cycle_observations_v2.jsonl")
    by_model: dict[str, list] = defaultdict(list)
    for c in cycles:
        by_model[str(c["MODEL_ID"])].append(c)

    def sum_model(model_id: str, key: str) -> int:
        return sum(1 for c in by_model[model_id] if c.get(key))

    summaries = {}
    for mid, rows in by_model.items():
        outcomes = Counter(c.get("DECISION_OUTCOME") for c in rows)
        summaries[mid] = {
            "TOTAL_CYCLES": len(rows),
            "HOLD_COUNT": outcomes.get("hold", 0),
            "ENTER_LONG_COUNT": outcomes.get("enter_long", 0),
            "ENTER_SHORT_COUNT": outcomes.get("enter_short", 0),
            "EXIT_COUNT": sum(v for k, v in outcomes.items() if str(k).startswith("exit")),
            "SWITCH_COUNT": outcomes.get("switch", 0),
            "BLOCKED_COUNT": outcomes.get("blocked", 0),
            "NO_ACTION_COUNT": outcomes.get("no_action", 0),
            "29P_FAIL_COUNT": sum(1 for c in rows if not c.get("REPLAY_PASS")),
            "EXECUTION_ELIGIBLE_COUNT": sum(1 for c in rows if c.get("EXECUTION_ELIGIBLE")),
            "PRE_EXTERNAL_REACHED_COUNT": sum(1 for c in rows if c.get("PRE_EXTERNAL_REACHED")),
        }

    (evidence_dir / "model_b_summary.json").write_text(
        json.dumps(summaries.get("MODEL_B_CURRENT_LAYER_C", {}), indent=2) + "\n", encoding="utf-8"
    )
    (evidence_dir / "model_d_summary.json").write_text(
        json.dumps(summaries.get("MODEL_D_POLICY_HARD_MAX", {}), indent=2) + "\n", encoding="utf-8"
    )

    # B vs D aligned by PAIR_ID + CYCLE_ID
    flights = _load_jsonl(evidence_dir / "flight_manifest.jsonl")
    flight_to_pair = {f["FLIGHT_ID"]: f for f in flights}
    b_rows = by_model.get("MODEL_B_CURRENT_LAYER_C", [])
    d_by_pair_cycle: dict[tuple[str, int], dict] = {}
    for c in by_model.get("MODEL_D_POLICY_HARD_MAX", []):
        fid = c["FLIGHT_ID"]
        pair = flight_to_pair.get(fid, {}).get("PAIR_ID")
        if pair:
            d_by_pair_cycle[(pair, int(c["CYCLE_ID"]))] = c

    raw_equal = 0
    eff_diff = 0
    hard_max = 0
    digest_delta = 0
    outcome_delta = 0
    scope_delta = 0
    hard_max_changed: Counter[str] = Counter()

    for bc in b_rows:
        fid = bc["FLIGHT_ID"]
        pair = flight_to_pair.get(fid, {}).get("PAIR_ID")
        cid = int(bc["CYCLE_ID"])
        dc = d_by_pair_cycle.get((pair, cid)) if pair else None
        if not dc:
            continue
        if bc.get("ADVERSE_DISTANCE_RAW") == dc.get("ADVERSE_DISTANCE_RAW"):
            raw_equal += 1
        if bc.get("ADVERSE_DISTANCE_EFFECTIVE") != dc.get("ADVERSE_DISTANCE_EFFECTIVE"):
            eff_diff += 1
        if dc.get("HARD_MAX_APPLIED"):
            hard_max += 1
        if bc.get("SEMANTIC_DIGEST") != dc.get("SEMANTIC_DIGEST"):
            digest_delta += 1
        if bc.get("DECISION_OUTCOME") != dc.get("DECISION_OUTCOME"):
            outcome_delta += 1
        if bc.get("SCOPE_EVENTS") != dc.get("SCOPE_EVENTS"):
            scope_delta += 1
            if dc.get("HARD_MAX_APPLIED"):
                hard_max_changed["SCOPE"] += 1
        if bc.get("DECISION_OUTCOME") != dc.get("DECISION_OUTCOME") and dc.get("HARD_MAX_APPLIED"):
            hard_max_changed["DP"] += 1

    aligned = min(len(b_rows), len(d_by_pair_cycle))
    delta = {
        "RAW_DISTANCE_EQUAL_COUNT": raw_equal,
        "EFFECTIVE_DISTANCE_DIFFERENT_COUNT": eff_diff,
        "HARD_MAX_ACTIVATED_COUNT": hard_max,
        "HARD_MAX_ACTIVATION_RATE": hard_max / aligned if aligned else 0,
        "SCOPE_EVENT_DELTA_COUNT": scope_delta,
        "MV2_DECISION_DELTA_COUNT": "UNRESOLVED_FROM_EXISTING_EVIDENCE",
        "DP_DECISION_DELTA_COUNT": outcome_delta,
        "SEMANTIC_DIGEST_DELTA_COUNT": digest_delta,
        "MODEL_D_BEHAVIORALLY_EQUIVALENT_IN_OBSERVED_STAGE2": digest_delta == 0 and outcome_delta == 0,
        "HARD_MAX_CHANGED_SCOPE_COUNT": hard_max_changed["SCOPE"],
        "HARD_MAX_CHANGED_DP_COUNT": hard_max_changed["DP"],
    }
    delta["SEMANTIC_DIGEST_DELTA_NOTE"] = (
        "Evidence semantic_digest includes replay_id/flight-specific refs; "
        "not used alone for B/D distance equivalence."
    )
    (evidence_dir / "model_b_vs_d_delta.json").write_text(json.dumps(delta, indent=2) + "\n", encoding="utf-8")

    # price / vol breakdown for MODEL_B
    b_only = by_model.get("MODEL_B_CURRENT_LAYER_C", [])
    price_buckets: dict[str, list] = defaultdict(list)
    vol_buckets: dict[str, list] = defaultdict(list)
    regime_buckets: dict[str, list] = defaultdict(list)
    for c in b_only:
        gp = str(c.get("GENERALIZATION_PROFILE", ""))
        pc = "MICRO" if gp.startswith("MICRO") else gp.split("_")[0]
        price_buckets[pc].append(c)
        vol_buckets[str(c.get("VOL_LEVEL"))].append(c)
        regime_buckets[str(c.get("REGIME"))].append(c)

    def bucket_summary(rows: list) -> dict:
        if not rows:
            return {}
        n = len(rows)
        return {
            "CYCLES": n,
            "ENTERS": sum(1 for r in rows if r.get("NATURAL_ENTER")),
            "29P_FAIL_RATE": sum(1 for r in rows if not r.get("REPLAY_PASS")) / n,
            "EXECUTION_ELIGIBLE_RATE": sum(1 for r in rows if r.get("EXECUTION_ELIGIBLE")) / n,
            "FAIL_CLOSED_RATE": sum(1 for r in rows if r.get("FAIL_CLOSED")) / n,
        }

    (evidence_dir / "price_breakdown.json").write_text(
        json.dumps({k: bucket_summary(v) for k, v in price_buckets.items()}, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "volatility_breakdown.json").write_text(
        json.dumps({k: bucket_summary(v) for k, v in vol_buckets.items()}, indent=2) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "regime_breakdown.json").write_text(
        json.dumps({k: bucket_summary(v) for k, v in regime_buckets.items()}, indent=2) + "\n",
        encoding="utf-8",
    )
    max_raw = max(
        (float(c["ADVERSE_DISTANCE_RAW"]) for c in cycles if isinstance(c.get("ADVERSE_DISTANCE_RAW"), (int, float))),
        default=0,
    )
    (evidence_dir / "hard_max_analysis.json").write_text(
        json.dumps(
            {
                "HARD_MAX_ACTIVATED_COUNT": hard_max,
                "MAX_RAW_ADVERSE_DISTANCE": max_raw,
                "HARD_MAX_500_CLASSIFICATION": "CONSUMER_SAFETY_CONSTRAINT_ONLY"
                if hard_max == 0
                else "BEHAVIORALLY_ACTIVE_CONSTRAINT",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # enters
    enter_rows = [c for c in cycles if c.get("NATURAL_ENTER")]
    flights_with_enter = len({c["FLIGHT_ID"] for c in enter_rows})
    return {
        "summaries": summaries,
        "delta": delta,
        "ENTER_CANDIDATE_COUNT": len(enter_rows),
        "FLIGHTS_WITH_ANY_ENTER": flights_with_enter,
        "HOLD_COUNT": sum(summaries.get("MODEL_B_CURRENT_LAYER_C", {}).get("HOLD_COUNT", 0) for _ in [0]),
        "decision_totals": {
            "MODEL_B": summaries.get("MODEL_B_CURRENT_LAYER_C"),
            "MODEL_D": summaries.get("MODEL_D_POLICY_HARD_MAX"),
        },
    }
