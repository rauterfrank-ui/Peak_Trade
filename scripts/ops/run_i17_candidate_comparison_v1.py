#!/usr/bin/env python3
"""Replay the I17 decision bridge on one sealed mark sequence for both GVEF profiles."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

from scripts.ops.run_research_candidate_shadow_v1 import (  # noqa: E402
    HOUR,
    PLAN_SCHEMA,
    ROLE_PATHS,
    _absolute,
    _clock,
    _head,
    _milliseconds,
    _pair,
    _public_get,
    _utc,
)
from src.backtest.strategy_signal_binding_v1 import execute_configured_strategy_signal_series_v1  # noqa: E402
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (  # noqa: E402
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (  # noqa: E402
    EvaluationReceiptArchiveV1,
)
from src.experiments.canonical_research_prepared_execution_v1 import (  # noqa: E402
    digest_v1,
    publish_v1,
    read_v1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import PUBLIC_HTTP_HOST  # noqa: E402
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (  # noqa: E402
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (  # noqa: E402
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (  # noqa: E402
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (  # noqa: E402
    HardenedBridgeSessionStateV2,
    I17OfflineCandidateInputV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (  # noqa: E402
    run_hardened_wallclock_bridge_observation_cycle_v2,
)
from src.strategies.registry import build_registry_snapshot  # noqa: E402
from src.strategies.suitability_registry_adapter_v1 import (  # noqa: E402
    build_suitability_registry_from_snapshot,
)

LAST_ENDPOINT = ROLE_PATHS["last"]


def _read_i17(root, instrument):
    manifest = (root / "evidence_manifest.sha256").read_bytes()
    check = verify_wallclock_evidence_bundle_v1(evidence_root=root)
    if not check.typed_ddo_requirement_met:
        raise ValueError("I17_COMPARISON_REQUIRES_VERIFIED_TYPED_ARCHIVE")
    pins = dict(line.split("  ", 1)[::-1] for line in manifest.decode().splitlines() if line)

    def read_rows(name):
        raw = (root / name).read_bytes()
        if sha256(raw).hexdigest() != pins[name]:
            raise ValueError("I17_COMPARISON_ORIGINAL_LEDGER_CHANGED")
        return [json.loads(line) for line in raw.splitlines() if line]

    ticks = read_rows("market_data_sequence.jsonl")
    cycles = read_rows("bridge_cycle_ledger.jsonl")
    rows = []
    for tick, cycle in zip(ticks, cycles, strict=True):
        timing = cycle["shadow_decision_timing"]
        decided = timing["decision_cycle_ts_unix"]
        if (
            tick["canonical_instrument_id"] != instrument
            or tick["venue_instrument_id"] != instrument
            or cycle["instrument_id"] != instrument
            or timing["market_sequence"] != tick["sequence"]
            or timing["mark_event_ts_unix"] != tick["event_ts_unix"]
            or tick["event_ts_unix"] > tick["receive_ts_unix"]
            or tick["receive_ts_unix"] > decided
            or (rows and decided <= rows[-1][0])
        ):
            raise ValueError("I17_COMPARISON_TICK_DECISION_MISMATCH")
        rows.append((decided, tick, cycle["decision_id"]))
    return sha256(manifest).hexdigest(), rows


def _last_query(instrument, last_decision):
    cutoff = datetime.fromtimestamp(last_decision, timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )
    return {"instId": instrument, "bar": "1H", "after": str(_milliseconds(cutoff)), "limit": "100"}


def _parse_last(capture, query):
    raw = bytes.fromhex(capture["raw_hex"])
    if (
        capture["host"] != PUBLIC_HTTP_HOST
        or capture["endpoint"] != LAST_ENDPOINT
        or capture["query"] != query
        or sha256(raw).hexdigest() != capture["raw_sha256"]
        or _utc(capture["received_at_utc"]) < _utc(capture["requested_at_utc"])
    ):
        raise ValueError("I17_COMPARISON_LAST_ARCHIVE_MISMATCH")
    payload = json.loads(raw)
    if payload["code"] != "0" or not isinstance(payload["data"], list):
        raise ValueError("I17_COMPARISON_LAST_SOURCE_REJECTED")
    rows = {}
    for row in payload["data"]:
        if not isinstance(row, list) or len(row) != 9:
            raise ValueError("I17_COMPARISON_LAST_CANDLE_SHAPE")
        opened = int(row[0])
        if opened >= int(query["after"]):
            continue
        close_time = datetime.fromtimestamp(opened / 1000, timezone.utc) + HOUR
        o, high, low, close = map(float, row[1:5])
        volume = float(row[6])
        if (
            row[-1] != "1"
            or opened % 3_600_000
            or close_time in rows
            or close_time > _utc(capture["received_at_utc"])
            or not all(math.isfinite(value) and value > 0 for value in (o, high, low, close))
            or not low <= min(o, close) <= max(o, close) <= high
            or not math.isfinite(volume)
            or volume < 0
        ):
            raise ValueError("I17_COMPARISON_LAST_CANDLE_INVALID")
        rows[close_time] = (o, high, low, close, volume)
    times = sorted(rows)
    if (
        not times
        or _milliseconds(times[-1]) != int(query["after"])
        or any(right - left != HOUR for left, right in zip(times, times[1:]))
    ):
        raise ValueError("I17_COMPARISON_LAST_CANDLE_COVERAGE")
    return pd.DataFrame(
        [rows[time] for time in times],
        index=pd.DatetimeIndex(times),
        columns=("open", "high", "low", "close", "volume"),
    )


def _last_source(workspace, query, *, capture_last, fetch=_public_get):
    path = workspace.safe_path_v1("last-candles.json")
    if path.exists() or not capture_last:
        record = read_v1(path)
        return record, _parse_last(record, query)
    requested = _clock()
    raw = fetch(LAST_ENDPOINT, query)
    record = {
        "host": PUBLIC_HTTP_HOST,
        "endpoint": LAST_ENDPOINT,
        "query": query,
        "requested_at_utc": requested.isoformat(),
        "received_at_utc": _clock().isoformat(),
        "raw_sha256": sha256(raw).hexdigest(),
        "raw_hex": raw.hex(),
    }
    frame = _parse_last(record, query)
    publish_v1(path, record)
    return record, frame


def _strategy_binding(plan, profile, bars):
    if len(bars) < profile["parameters"]["slow_window"]:
        raise ValueError("I17_COMPARISON_MA_WARMUP_INCOMPLETE")
    binding = execute_configured_strategy_signal_series_v1(
        bars, strategy_id=plan["strategy_id"], cfg=profile["config"]
    )
    provenance = binding.provenance
    if (
        dict(provenance.effective_strategy_params) != profile["parameters"]
        or dict(provenance.configured_strategy_params) != profile["parameters"]
        or provenance.strategy_version != plan["strategy_version"]
    ):
        raise ValueError("I17_COMPARISON_EFFECTIVE_PARAMETERS_MISMATCH")
    return binding


def _compare(plan, rows, candles, *, identifier):
    strategy = plan["strategy_id"]
    scope = plan["instrument_id"]
    registry = build_suitability_registry_from_snapshot(build_registry_snapshot())
    entries = tuple(entry for entry in registry.entries if entry.strategy_id == strategy)
    if len(entries) != 1:
        raise ValueError("I17_COMPARISON_STRATEGY_REGISTRY_BINDING_MISSING")
    entry = entries[0]
    profiles = plan["profiles"]
    states = {role: HardenedBridgeSessionStateV2(instrument_id=scope) for role in profiles}
    first_received = rows[0][1]["receive_ts_unix"]
    bindings = {}
    prior_close = None
    compared = []
    for decided, original, decision_id in rows:
        decision_time = datetime.fromtimestamp(decided, timezone.utc)
        close_time = decision_time.replace(minute=0, second=0, microsecond=0)
        if close_time != prior_close:
            if close_time not in candles.index:
                raise ValueError("I17_COMPARISON_HOUR_MISSING_AT_DECISION")
            prefix = candles.loc[:close_time]
            bindings = {
                role: _strategy_binding(plan, profile, prefix) for role, profile in profiles.items()
            }
            prior_close = close_time
        tick = ObservationMarketTickV1(
            instrument_id=scope,
            venue=VENUE_OKX,
            market_type=MARKET_TYPE_FUTURES,
            sequence=original["sequence"],
            event_ts_unix=original["event_ts_unix"],
            receive_ts_unix=original["receive_ts_unix"],
            mono_ts=original["receive_ts_unix"] - first_received,
            mid_price=original["mid_price"],
            source="caller_supplied_offline",
        )
        arms = {}
        for role, binding in bindings.items():
            state = states[role]
            material = normalize_strategy_signal_to_suitability_agreement_material_v1(
                binding,
                instrument_id=scope,
                trading_epoch=state.trading_epoch,
                signal_index=len(binding.signals) - 1,
                expected_configured_strategy_id=strategy,
                expected_strategy_version=plan["strategy_version"],
            )
            observation = run_hardened_wallclock_bridge_observation_cycle_v2(
                bridge_state=state,
                ticks=(tick,),
                reference_price=Decimal(str(tick.mid_price)),
                wall_now_unix=decided,
                session_id=f"i17-offline-{identifier[:20]}-{role}",
                offline_candidate=I17OfflineCandidateInputV2(
                    profiles[role]["packet"], entry, material
                ),
            )
            cycle = observation.bridge_cycle
            if not observation.ok or cycle is None or cycle["execution_eligible"]:
                raise ValueError(f"I17_COMPARISON_BRIDGE_REJECTED:{observation.md_blockers}")
            arms[role] = {
                **cycle["offline_candidate"],
                "decision_outcome": cycle["decision_outcome"],
                "selected_side": cycle["selected_side"],
                "intended_action": cycle["intended_action"]["intent_action"],
                "safety_result": cycle["safety_result"],
                "analytical_equity": cycle["economic_metrics"]["equity"],
                "typed_volatility_present": cycle[
                    "canonical_market_context_typed_estimate_present"
                ],
            }
        if arms["reference"]["governed_seam_digest"] != arms["candidate"]["governed_seam_digest"]:
            raise ValueError("I17_COMPARISON_GOVERNED_SEAM_MISMATCH")
        compared.append(
            {
                "observed_mark_sequence": tick.sequence,
                "historical_decision_id": decision_id,
                "decision_time_utc": decision_time.isoformat(),
                "last_candle_close_utc": close_time.isoformat(),
                "arms": arms,
            }
        )
    return compared


def compare_v1(workspace, *, plan, evidence_root, code_sha, capture_last=False, verify=False):
    manifest_sha, rows = _read_i17(evidence_root, plan["instrument_id"])
    query = _last_query(plan["instrument_id"], rows[-1][0])
    output = workspace.safe_path_v1("result.json")
    with workspace.lease_v1():
        source, candles = _last_source(workspace, query, capture_last=capture_last and not verify)
        binding = {
            "plan_digest": digest_v1(plan),
            "original_i17_manifest_sha256": manifest_sha,
            "last_candle_archive_digest": digest_v1(source),
            "code_sha": code_sha,
        }
        if output.exists() and not verify:
            saved = read_v1(output)
            if any(saved[key] != value for key, value in binding.items()):
                raise ValueError("I17_COMPARISON_ORIGINAL_BINDING_CHANGED")
            return saved
        cycles = _compare(plan, rows, candles, identifier=digest_v1(binding))
        results = [(row["arms"]["reference"], row["arms"]["candidate"]) for row in cycles]
        result = {
            "schema_version": "i17_offline_candidate_comparison.v1",
            "authority": "NONE",
            "scope": "HISTORICAL_I17_COMPARISON",
            "last_inputs_captured_at_utc": source["received_at_utc"],
            "strategy_id": plan["strategy_id"],
            "strategy_version": plan["strategy_version"],
            "parameters": {
                role: profile["parameters"] for role, profile in plan["profiles"].items()
            },
            **binding,
            "cycle_count": len(cycles),
            "typed_volatility_cycles": sum(a["typed_volatility_present"] for a, _ in results),
            "suitability_cycles": {
                "reference": sum(bool(a["suitability"]) for a, _ in results),
                "candidate": sum(bool(b["suitability"]) for _, b in results),
            },
            "different_strategy_states": sum(
                a["material"]["cycle_signal_value"] != b["material"]["cycle_signal_value"]
                for a, b in results
            ),
            "different_suitability_cycles": sum(
                a["suitability"] != b["suitability"] for a, b in results
            ),
            "different_decision_cycles": sum(
                (a["decision_outcome"], a["selected_side"], a["intended_action"])
                != (b["decision_outcome"], b["selected_side"], b["intended_action"])
                for a, b in results
            ),
            "cycles": cycles,
        }
        if verify:
            if digest_v1(read_v1(output)) != digest_v1(result):
                raise ValueError("I17_COMPARISON_READBACK_MISMATCH")
        else:
            publish_v1(output, result)
        return read_v1(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--pair-plan", type=Path, required=True)
    parser.add_argument("--campaign-state", type=Path, required=True)
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--i17-evidence", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--capture-public-last", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    try:
        state = _absolute(args.state)
        source_paths = [
            REPO,
            _absolute(args.pair_plan).parent,
            _absolute(args.campaign_state),
            _absolute(args.base_config),
            _absolute(args.i17_evidence),
        ]
        if any(state.is_relative_to(path) or path.is_relative_to(state) for path in source_paths):
            raise ValueError("I17_COMPARISON_STATE_MUST_BE_SEPARATE")
        plan = read_v1(args.pair_plan)
        pair = _pair(
            args.campaign_state, plan["learning_digest"], json.loads(args.base_config.read_bytes())
        )
        if (
            plan["schema_version"] != PLAN_SCHEMA
            or plan["authority"] != "NONE"
            or any(plan[key] != value for key, value in pair.items())
            or plan["strategy_id"] != "ma_crossover"
        ):
            raise ValueError("I17_COMPARISON_GVEF_PLAN_MISMATCH")
        result = compare_v1(
            EvaluationReceiptArchiveV1(state),
            plan=plan,
            evidence_root=args.i17_evidence,
            code_sha=_head(),
            capture_last=args.capture_public_last,
            verify=args.verify,
        )
        print(
            json.dumps(
                {key: value for key, value in result.items() if key != "cycles"}, sort_keys=True
            )
        )
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(2, f"I17 candidate comparison stopped: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
