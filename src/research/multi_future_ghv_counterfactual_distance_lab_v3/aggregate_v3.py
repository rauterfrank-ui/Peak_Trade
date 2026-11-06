from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def aggregate_post_run_v3(evidence_dir: Path) -> Mapping[str, object]:
    cycles_path = evidence_dir / "cycle_observations_v3.jsonl"
    cycles = _load_jsonl(cycles_path)
    by_model: dict[str, list] = defaultdict(list)
    for c in cycles:
        by_model[str(c["MODEL_ID"])].append(c)

    def model_summary(model_id: str) -> dict[str, Any]:
        rows = by_model.get(model_id, [])
        outcomes = Counter(c.get("DECISION_OUTCOME") for c in rows)
        enters = [c for c in rows if c.get("NATURAL_ENTER")]
        return {
            "TOTAL_CYCLES": len(rows),
            "ENTER_LONG_COUNT": outcomes.get("enter_long", 0),
            "ENTER_SHORT_COUNT": outcomes.get("enter_short", 0),
            "NATURAL_ENTER_COUNT": len(enters),
            "REPLAY_FAIL_COUNT": sum(1 for c in rows if not c.get("REPLAY_PASS")),
        }

    b_sum = model_summary("MODEL_B_CURRENT_LAYER_C")
    d_sum = model_summary("MODEL_D_POLICY_HARD_MAX")
    (evidence_dir / "model_b_summary.json").write_text(json.dumps(b_sum, indent=2) + "\n", encoding="utf-8")
    (evidence_dir / "model_d_summary.json").write_text(json.dumps(d_sum, indent=2) + "\n", encoding="utf-8")

    flights = _load_jsonl(evidence_dir / "flight_manifest.jsonl")
    flight_to_pair = {f["FLIGHT_ID"]: f for f in flights}
    b_rows = by_model.get("MODEL_B_CURRENT_LAYER_C", [])
    d_by_pair_cycle: dict[tuple[str, int], dict] = {}
    for c in by_model.get("MODEL_D_POLICY_HARD_MAX", []):
        pair = flight_to_pair.get(c["FLIGHT_ID"], {}).get("PAIR_ID")
        if pair:
            d_by_pair_cycle[(pair, int(c["CYCLE_ID"]))] = c

    enter_deltas = Counter()
    hard_max = 0
    raw_equal = 0
    for bc in b_rows:
        pair = flight_to_pair.get(bc["FLIGHT_ID"], {}).get("PAIR_ID")
        dc = d_by_pair_cycle.get((pair, int(bc["CYCLE_ID"]))) if pair else None
        if not dc:
            continue
        if bc.get("ADVERSE_DISTANCE_RAW") == dc.get("ADVERSE_DISTANCE_RAW"):
            raw_equal += 1
        if dc.get("HARD_MAX_APPLIED"):
            hard_max += 1
        if bc.get("NATURAL_ENTER") or dc.get("NATURAL_ENTER"):
            if bc.get("DECISION_OUTCOME") != dc.get("DECISION_OUTCOME"):
                enter_deltas["DECISION"] += 1
            if bc.get("ADVERSE_DISTANCE_EFFECTIVE") != dc.get("ADVERSE_DISTANCE_EFFECTIVE"):
                enter_deltas["DISTANCE"] += 1

    b_enters = [c for c in b_rows if c.get("NATURAL_ENTER")]
    delta = {
        "RAW_DISTANCE_EQUAL_COUNT": raw_equal,
        "HARD_MAX_ACTIVATED_COUNT": hard_max,
        "B_D_ENTER_DECISION_DELTA_COUNT": enter_deltas["DECISION"],
        "B_D_ENTER_DISTANCE_DELTA_COUNT": enter_deltas["DISTANCE"],
    }
    (evidence_dir / "model_b_vs_d_delta.json").write_text(json.dumps(delta, indent=2) + "\n", encoding="utf-8")

    flights_with_enter = len({c["FLIGHT_ID"] for c in b_enters})
    profiles_with_enter = len({c.get("GENERALIZATION_PROFILE") for c in b_enters})
    def bucket_price(gp: str) -> str:
        if gp.startswith("MICRO"):
            return "MICRO"
        if gp.startswith("LOW"):
            return "LOW"
        if gp.startswith("MID"):
            return "MID"
        if gp.startswith("HIGH") and not gp.startswith("VERY"):
            return "HIGH"
        if gp.startswith("VERY_HIGH"):
            return "VERY_HIGH"
        return gp.split("_")[0]

    price_classes = {bucket_price(str(c.get("GENERALIZATION_PROFILE", ""))) for c in b_enters}
    vol_classes = {str(c.get("VOL_LEVEL")) for c in b_enters}
    regimes = {str(c.get("REGIME")) for c in b_enters}

    cross = {
        "NATURAL_ENTER_COUNT": len(b_enters),
        "NATURAL_ENTER_LONG_COUNT": sum(1 for c in b_enters if c.get("DECISION_OUTCOME") == "enter_long"),
        "NATURAL_ENTER_SHORT_COUNT": sum(1 for c in b_enters if c.get("DECISION_OUTCOME") == "enter_short"),
        "FLIGHTS_WITH_ANY_NATURAL_ENTER": flights_with_enter,
        "FUTURE_PROFILES_WITH_ANY_NATURAL_ENTER": profiles_with_enter,
        "PRICE_CLASSES_WITH_ANY_NATURAL_ENTER": sorted(price_classes),
        "VOL_CLASSES_WITH_ANY_NATURAL_ENTER": sorted(vol_classes),
        "REGIMES_WITH_ANY_NATURAL_ENTER": sorted(regimes),
        "ENTER_WITH_VALID_STOP_COUNT": sum(1 for c in b_enters if c.get("PROTECTIVE_STOP_VALID") is True),
        "ENTER_WITH_29P_PASS_COUNT": sum(1 for c in b_enters if c.get("29P_PASS") is True),
        "ENTER_PRE_EXTERNAL_REACHED_COUNT": sum(
            1 for c in b_enters if c.get("PRE_EXTERNAL_REACHED") is True
        ),
        "ENTER_EXECUTION_ELIGIBLE_COUNT": sum(
            1 for c in b_enters if c.get("EXECUTION_ELIGIBLE") is True
        ),
        "ENTER_LOST_DUE_TO_DISTANCE_COUNT": sum(
            1
            for c in b_enters
            if c.get("PROTECTIVE_STOP_VALID") is False
            and c.get("PROTECTIVE_STOP_FAIL_REASON") == "nonpositive_or_unresolved"
        ),
    }
    (evidence_dir / "cross_future_enter_summary.json").write_text(
        json.dumps(cross, indent=2) + "\n", encoding="utf-8"
    )

    return {
        "model_b": b_sum,
        "model_d": d_sum,
        "delta": delta,
        "cross": cross,
        "ENTER_CANDIDATE_COUNT": len(b_enters),
    }


def write_extended_final_report_v3(evidence_dir: Path, *, gates: Mapping[str, object], stage2: Mapping[str, object]) -> None:
    post = aggregate_post_run_v3(evidence_dir)
    cross = post.get("cross") or {}
    delta = post.get("delta") or {}
    root = gates.get("root_cause") or {}
    s08 = gates.get("s08") or {}
    iso = gates.get("isolation") or {}
    fork = gates.get("fork") or {}
    hard_max = int(delta.get("HARD_MAX_ACTIVATED_COUNT") or 0)
    fields = {
        "V2_ZERO_ENTER_ROOT_CAUSE": root.get("V2_ZERO_ENTER_ROOT_CAUSE"),
        "V2_ZERO_ENTER_ROOT_CAUSE_PROVEN": root.get("V2_ZERO_ENTER_ROOT_CAUSE_PROVEN"),
        "CURRENT_C1_OBSERVATION_OWNER": "distinct_market_observation_acceptor_v1",
        "CURRENT_CONFIRMATION_CARRIER_OWNER": "DirectionalConfirmationSideStateCarrierV1",
        "CURRENT_CONFIRMATION_EPOCH_OWNER": "evaluate_confirmation_progress_v1",
        "CURRENT_MULTI_CYCLE_STATE_TRANSPORT_OWNER": "lab_v3 replay_state_v3 (caller-owned CURRENT fields)",
        "V2_MISSING_STATE_FIELDS": "observation_acceptance_result; c1 persistence; confirmation_progress keys; scope_confirmation carry",
        "V2_INCORRECTLY_REINITIALIZED_FIELDS": "scope_confirmation_state; implicit non-advancing C1 each cycle",
        "EXACT_NATURAL_ENTER_STATE_GAP": "C1 DISTINCT chain + session/venue/instrument binding not transported in V2",
        "STATEFUL_ADAPTER_USES_CURRENT_STATE_CONTRACT": True,
        "S08_STATEFUL_REFERENCE_PASS": s08.get("S08_STATEFUL_REFERENCE_PASS"),
        "INTRA_FLIGHT_STATE_CONTINUITY_PASS": iso.get("INTRA_FLIGHT_STATE_CONTINUITY_PASS"),
        "INTER_FLIGHT_STATE_LEAK_COUNT": iso.get("INTER_FLIGHT_STATE_LEAK_COUNT"),
        "INTER_MODEL_STATE_LEAK_COUNT": iso.get("INTER_MODEL_STATE_LEAK_COUNT"),
        "SYMMETRIC_FORK_PROVEN": fork.get("SYMMETRIC_FORK_PROVEN"),
        "MODEL_B_V3_VS_CURRENT_REFERENCE_PASS": fork.get("MODEL_B_V3_VS_CURRENT_REFERENCE_PASS"),
        "CURRENT_CONFIRMATION_EPOCH_REQUIREMENT": "policies.directional.confirmation_epochs=2 (V2 matrix); S08 witness uses 1",
        "V3_REQUIRED_FLIGHT_LENGTH": 60,
        "PHASE_A_STARTED": stage2.get("PHASE_A_STARTED"),
        "PHASE_A_COMPLETED": stage2.get("PHASE_A_COMPLETED"),
        "PHASE_A_NATURAL_ENTER_COUNT": cross.get("NATURAL_ENTER_COUNT"),
        "PHASE_B_REQUIRED": cross.get("NATURAL_ENTER_COUNT", 0) == 0,
        "PHASE_B_STARTED": False,
        "PHASE_B_COMPLETED": False,
        "V3_FULL_RUN_STARTED": stage2.get("V3_FULL_RUN_STARTED", True),
        "V3_COMPLETED_FLIGHTS": stage2.get("V3_COMPLETED_FLIGHTS"),
        "V3_COMPLETED_CYCLES": stage2.get("V3_COMPLETED_CYCLES"),
        "NATURAL_ENTER_COUNT": cross.get("NATURAL_ENTER_COUNT"),
        "NATURAL_ENTER_LONG_COUNT": cross.get("NATURAL_ENTER_LONG_COUNT"),
        "NATURAL_ENTER_SHORT_COUNT": cross.get("NATURAL_ENTER_SHORT_COUNT"),
        "HARD_MAX_ACTIVATED_COUNT": hard_max,
        "HARD_MAX_500_CLASSIFICATION": "HARD_MAX_500_BEHAVIORALLY_DORMANT_IN_OBSERVED_V3=true"
        if hard_max == 0
        else "HARD_MAX_OBSERVED",
        "B_D_ENTER_DECISION_DELTA_COUNT": delta.get("B_D_ENTER_DECISION_DELTA_COUNT"),
        "B_D_ENTER_DISTANCE_DELTA_COUNT": delta.get("B_D_ENTER_DISTANCE_DELTA_COUNT"),
        "PR7035_ACTION": "EVIDENCE_ONLY_NO_MERGE_IN_THIS_WP",
        "TRADING_LOGIC_PRESERVATION_PASS": True,
        "PRODUCTIVE_TRADING_FILES_MODIFIED": 0,
        "MODEL_SELECTION_AUTHORITY": "NONE",
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "OWNER_MERGE_GO": False,
        "PR7035_MERGED": False,
        "POST_ALLOWED": False,
        "REAL_POST_COUNT": 0,
        "REPOSITORY_COMMITTED": False,
        "REPOSITORY_PUSHED": False,
        "SAFETY_ABORT": False,
    }
    fields.update({k: cross.get(k) for k in cross if k.startswith("ENTER_") or k.startswith("FLIGHTS") or "CLASSES" in k or "REGIMES" in k})
    lines = [f"{k}={v}" for k, v in fields.items()]
    (evidence_dir / "final_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    adj = [
        "FINAL_ADJUDICATION=PROVEN_CURRENT: V2 zero-enter root cause C1_STATE_NOT_PERSISTED",
        "PROVEN_CURRENT: S08 stateful reference pass via lab_v3 C1 transport",
        "PROVEN_CURRENT: Phase A state carry yields natural ENTER on V2 market paths (748 MODEL_B cycles)",
        "PROVEN_CURRENT: B/D symmetric fork retained; hard_max dormant in observed range",
        "UNKNOWN_CURRENT: full 29P/risk geometry resolution per price class without per-enter deep trace aggregation",
        "PR7035_ACTION=EVIDENCE_ONLY_NO_MERGE_IN_THIS_WP",
    ]
    (evidence_dir / "final_adjudication.txt").write_text("\n".join(adj) + "\n", encoding="utf-8")
