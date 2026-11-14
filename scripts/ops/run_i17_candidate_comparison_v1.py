#!/usr/bin/env python3
"""Replay the I17 decision bridge on one sealed mark sequence for both GVEF profiles."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import re
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
    CANONICAL_INSTRUMENT_ID,
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (  # noqa: E402
    parse_preregistration_contract_v1,
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
from trading.market_state.distinct_market_observation_acceptor_v1 import (  # noqa: E402
    InstrumentObservationKeyV1,
    ObservationCandidateV1,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)

LAST_ENDPOINT = ROLE_PATHS["last"]
DECISION_TIME_LAST_SCHEMA = "i17_decision_time_last_captures.v1"


def _pinned_i17_file(root, manifest, name):
    pins = dict(line.split("  ", 1)[::-1] for line in manifest.decode().splitlines() if line)
    path = root / name
    if path.is_symlink():
        raise ValueError("I17_COMPARISON_UNSAFE_ORIGINAL_FILE")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != pins.get(name):
        raise ValueError("I17_COMPARISON_ORIGINAL_LEDGER_CHANGED")
    return raw


def _read_i17(root, instrument):
    manifest = (root / "evidence_manifest.sha256").read_bytes()
    check = verify_wallclock_evidence_bundle_v1(evidence_root=root)
    if not check.typed_ddo_requirement_met:
        raise ValueError("I17_COMPARISON_REQUIRES_VERIFIED_TYPED_ARCHIVE")

    def read_rows(name):
        raw = _pinned_i17_file(root, manifest, name)
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


def _read_i17_scope(root, manifest_sha):
    manifest = (root / "evidence_manifest.sha256").read_bytes()
    if sha256(manifest).hexdigest() != manifest_sha:
        raise ValueError("I17_COMPARISON_ORIGINAL_MANIFEST_CHANGED")
    prereg = parse_preregistration_contract_v1(
        json.loads(_pinned_i17_file(root, manifest, "prereg.json"))
    )
    scope = _pinned_i17_file(root, manifest, "scope_digest.txt").decode().strip()
    if scope != prereg.scope_digest():
        raise ValueError("I17_DECISION_TIME_ORIGINAL_SCOPE_MISMATCH")
    return scope


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


def _capture_last_response(query, *, fetch, clock, requested):
    raw = fetch(LAST_ENDPOINT, query.copy())
    received = clock()
    return {
        "host": PUBLIC_HTTP_HOST,
        "endpoint": LAST_ENDPOINT,
        "query": query,
        "requested_at_utc": requested.isoformat(),
        "received_at_utc": received.isoformat(),
        "raw_sha256": sha256(raw).hexdigest(),
        "raw_hex": raw.hex(),
    }


def _last_source(workspace, query, *, capture_last, fetch=_public_get):
    path = workspace.safe_path_v1("last-candles.json")
    if path.exists() or not capture_last:
        record = read_v1(path)
        return record, _parse_last(record, query)
    record = _capture_last_response(query, fetch=fetch, clock=_clock, requested=_clock())
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


def _decision_time_window(plan):
    start = _utc(plan["start_utc"])
    end = _utc(plan["end_utc"])
    registered = _utc(plan["registered_at_utc"])
    if (
        plan["schema_version"] != PLAN_SCHEMA
        or plan["authority"] != "NONE"
        or plan["mode"] != "PROSPECTIVE_PUBLIC_DATA_OFFLINE_REPLAY"
        or plan["instrument_id"] != CANONICAL_INSTRUMENT_ID
        or plan["strategy_id"] != "ma_crossover"
        or set(plan["profiles"]) != {"reference", "candidate"}
        or not max(_utc(plan["candidate_known_at_utc"]), _utc(plan["parent_data_known_at_utc"]))
        <= registered
        < start
        < end
    ):
        raise ValueError("I17_DECISION_TIME_WINDOW_OR_PLAN_MISMATCH")
    return registered, start, end


def _capture_scope_path(plan, scope_digest):
    if not isinstance(scope_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", scope_digest):
        raise ValueError("I17_DECISION_TIME_SCOPE_DIGEST_REQUIRED")
    return Path(digest_v1(plan)) / scope_digest


def _assert_capture_journal_separate(journal, *sources):
    if any(
        journal.root.is_relative_to(path) or path.is_relative_to(journal.root)
        for path in (REPO, *sources)
    ):
        raise ValueError("I17_DECISION_TIME_JOURNAL_MUST_BE_SEPARATE")


def capture_decision_time_last_v1(journal, *, plan, scope_digest, fetch, clock):
    """Record one finalized hour from an explicitly injected capture transport and clock."""
    _assert_capture_journal_separate(journal)
    registered, _, end = _decision_time_window(plan)
    namespace = _capture_scope_path(plan, scope_digest)
    binding = {"plan_digest": namespace.parts[0], "original_i17_scope_digest": scope_digest}
    with journal.lease_v1():
        selected = _utc(clock().isoformat())
        if not registered <= selected < end:
            raise ValueError("I17_DECISION_TIME_CAPTURE_OUTSIDE_WINDOW")
        query = _last_query(plan["instrument_id"], selected.timestamp())
        target = journal.safe_path_v1(namespace / "hours" / f"{query['after']}.json")
        if target.exists():
            stored = read_v1(target)
            if (
                any(stored[key] != value for key, value in binding.items())
                or _utc(stored["capture"]["received_at_utc"]) > selected
            ):
                raise ValueError("I17_DECISION_TIME_CAPTURE_BINDING_OR_CLOCK_CHANGED")
            _parse_last(stored["capture"], query)
            return stored["capture"]
        if journal.safe_path_v1(namespace / "captures.json").exists():
            raise ValueError("I17_DECISION_TIME_CAPTURES_ALREADY_SEALED")
        requested = _utc(clock().isoformat())
        if not selected <= requested < end:
            raise ValueError("I17_DECISION_TIME_CAPTURE_CLOCK_INVALID")
        capture = _capture_last_response(query, fetch=fetch, clock=clock, requested=requested)
        if not requested <= _utc(capture["received_at_utc"]) < end:
            raise ValueError("I17_DECISION_TIME_CAPTURE_CLOCK_INVALID")
        candles = _parse_last(capture, query)
        for profile in plan["profiles"].values():
            _strategy_binding(plan, profile, candles)
        publish_v1(target, {**binding, "capture": capture})
        return capture


def seal_decision_time_last_v1(journal, *, plan, evidence_root):
    """Join the pre-bound capture receipts to their sealed I17 session archive."""
    _assert_capture_journal_separate(journal, evidence_root.resolve())
    manifest_sha, rows = _read_i17(evidence_root, plan["instrument_id"])
    scope = _read_i17_scope(evidence_root, manifest_sha)
    namespace = _capture_scope_path(plan, scope)
    binding = {"plan_digest": namespace.parts[0], "original_i17_scope_digest": scope}
    with journal.lease_v1():
        hours = journal.safe_path_v1(namespace / "hours")
        captures = []
        for item in sorted(hours.glob("*.json"), key=lambda path: int(path.stem)):
            stored = read_v1(journal.safe_path_v1(item.relative_to(journal.root)))
            capture = stored["capture"]
            if (
                any(stored[key] != value for key, value in binding.items())
                or item.stem != capture["query"]["after"]
            ):
                raise ValueError("I17_DECISION_TIME_CAPTURE_BINDING_OR_CLOCK_CHANGED")
            captures.append(capture)
        archive = {
            "schema_version": DECISION_TIME_LAST_SCHEMA,
            "original_i17_manifest_sha256": manifest_sha,
            **binding,
            "captures": captures,
        }
        snapshots = _decision_time_last_snapshots(plan, rows, archive, manifest_sha=manifest_sha)
        if snapshots[0][0].timestamp() > rows[0][0]:
            raise ValueError("I17_DECISION_TIME_LAST_NOT_YET_AVAILABLE")
        target = journal.safe_path_v1(namespace / "captures.json")
        publish_v1(target, archive)
        return target


def _decision_time_last_snapshots(plan, rows, archive, *, manifest_sha):
    registered, start, end = _decision_time_window(plan)
    if (
        archive["schema_version"] != DECISION_TIME_LAST_SCHEMA
        or archive["plan_digest"] != digest_v1(plan)
        or archive["original_i17_manifest_sha256"] != manifest_sha
        or not rows
        or not start.timestamp() <= rows[0][0] <= rows[-1][0] < end.timestamp()
    ):
        raise ValueError("I17_DECISION_TIME_WINDOW_OR_PLAN_MISMATCH")

    snapshots = []
    previous = None
    for capture in archive["captures"]:
        requested = _utc(capture["requested_at_utc"])
        received = _utc(capture["received_at_utc"])
        cutoff = int(capture["query"]["after"])
        if (
            not registered <= requested <= received < end
            or not 0 < cutoff <= _milliseconds(requested)
            or (snapshots and received <= snapshots[-1][0])
        ):
            raise ValueError("I17_DECISION_TIME_CAPTURE_CLOCK_INVALID")
        query = _last_query(plan["instrument_id"], cutoff / 1000)
        frame = _parse_last(capture, query)
        if previous is not None:
            overlap = frame.index.intersection(previous.index)
            new_bars = frame.loc[frame.index > previous.index[-1]]
            if (
                overlap.empty
                or new_bars.empty
                or new_bars.index[0] - previous.index[-1] != HOUR
                or not previous.loc[overlap].equals(frame.loc[overlap])
            ):
                raise ValueError("I17_DECISION_TIME_LAST_PREFIX_CHANGED_OR_NOT_EXTENDED")
            frame = pd.concat([previous, new_bars])
        snapshots.append(
            (
                received,
                frame,
                {
                    "received_at_utc": received.isoformat(),
                    "source_capture_digest": digest_v1(capture),
                },
            )
        )
        previous = frame
    if not snapshots:
        raise ValueError("I17_DECISION_TIME_LAST_CAPTURES_REQUIRED")
    return snapshots


def _compare(plan, rows, candles, *, identifier, decision_time_last=None):
    strategy = plan["strategy_id"]
    scope = plan["instrument_id"]
    registry = build_suitability_registry_from_snapshot(build_registry_snapshot())
    entries = tuple(entry for entry in registry.entries if entry.strategy_id == strategy)
    if len(entries) != 1:
        raise ValueError("I17_COMPARISON_STRATEGY_REGISTRY_BINDING_MISSING")
    entry = entries[0]
    profiles = plan["profiles"]
    states = {role: HardenedBridgeSessionStateV2(instrument_id=scope) for role in profiles}
    acceptance_state = initial_observation_acceptance_state_v1(
        bound_instrument_key=InstrumentObservationKeyV1(
            venue=VENUE_OKX, canonical_instrument_id=scope, venue_instrument_id=scope
        )
    )
    first_received = rows[0][1]["receive_ts_unix"]
    bindings = {}
    prior_close = None
    compared = []
    receipt_times = [] if decision_time_last is None else [row[0] for row in decision_time_last]
    for decided, original, decision_id in rows:
        decision_time = datetime.fromtimestamp(decided, timezone.utc)
        close_time = decision_time.replace(minute=0, second=0, microsecond=0)
        candle_input = {}
        if decision_time_last is not None:
            available_index = bisect_right(receipt_times, decision_time) - 1
            if available_index < 0:
                raise ValueError("I17_DECISION_TIME_LAST_NOT_YET_AVAILABLE")
            _, candles, trace = decision_time_last[available_index]
            close_time = candles.index[-1]
            candle_input = {"last_candle_input": trace}
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
        accepted = evaluate_distinct_market_observation_v1(
            acceptance_state,
            ObservationCandidateV1(
                venue=tick.venue,
                canonical_instrument_id=tick.instrument_id,
                venue_instrument_id=scope,
                venue_event_time=tick.event_ts_unix,
                mark_price=tick.mid_price,
                transport=ObservationTransportMetadataV1(
                    receive_time=tick.receive_ts_unix, wallclock_now=decided
                ),
            ),
        )
        if accepted.fail_closed:
            raise ValueError(f"I17_COMPARISON_C1_REJECTED:{accepted.reason_code}")
        if accepted.strategy_advance_allowed:
            acceptance_state = commit_observation_acceptance_v1(
                current_state=acceptance_state, result=accepted
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
                    profiles[role]["packet"], entry, material, accepted
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
                "decision_reason_codes": cycle["reason_codes"],
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
                **candle_input,
                "arms": arms,
            }
        )
    return compared


def compare_v1(
    workspace,
    *,
    plan,
    evidence_root,
    code_sha,
    capture_last=False,
    verify=False,
    decision_time_archive=None,
):
    manifest_sha, rows = _read_i17(evidence_root, plan["instrument_id"])
    output = workspace.safe_path_v1("result.json")
    with workspace.lease_v1():
        scope = "HISTORICAL_I17_COMPARISON"
        snapshots = None
        if decision_time_archive is None:
            query = _last_query(plan["instrument_id"], rows[-1][0])
            source, candles = _last_source(
                workspace, query, capture_last=capture_last and not verify
            )
            last_received = source["received_at_utc"]
        else:
            if capture_last:
                raise ValueError("I17_DECISION_TIME_PREFLIGHT_REQUIRES_OFFLINE_INPUT")
            scope = "I17_DECISION_TIME_OFFLINE_PREFLIGHT"
            source, candles = decision_time_archive, None
            if "original_i17_scope_digest" in source and source[
                "original_i17_scope_digest"
            ] != _read_i17_scope(evidence_root, manifest_sha):
                raise ValueError("I17_DECISION_TIME_ORIGINAL_SCOPE_MISMATCH")
            snapshots = _decision_time_last_snapshots(plan, rows, source, manifest_sha=manifest_sha)
            last_received = snapshots[-1][0].isoformat()
        binding = {
            "plan_digest": digest_v1(plan),
            "original_i17_manifest_sha256": manifest_sha,
            "last_candle_archive_digest": digest_v1(source),
            "code_sha": code_sha,
        }
        if decision_time_archive is not None and "original_i17_scope_digest" in source:
            binding["original_i17_scope_digest"] = source["original_i17_scope_digest"]
        if output.exists() and not verify:
            saved = read_v1(output)
            if any(saved[key] != value for key, value in binding.items()):
                raise ValueError("I17_COMPARISON_ORIGINAL_BINDING_CHANGED")
            return saved
        cycles = _compare(
            plan, rows, candles, identifier=digest_v1(binding), decision_time_last=snapshots
        )
        results = [(row["arms"]["reference"], row["arms"]["candidate"]) for row in cycles]
        result = {
            "schema_version": "i17_offline_candidate_comparison.v1",
            "authority": "NONE",
            "scope": scope,
            "last_inputs_captured_at_utc": last_received,
            "strategy_id": plan["strategy_id"],
            "strategy_version": plan["strategy_version"],
            "parameters": {
                role: profile["parameters"] for role, profile in plan["profiles"].items()
            },
            **binding,
            "cycle_count": len(cycles),
            "market_observation_classifications": dict(
                Counter(a["market_observation_classification"] for a, _ in results)
            ),
            "typed_volatility_cycles": sum(a["typed_volatility_present"] for a, _ in results),
            "directional_confirmation_cycles": {
                role: sum(
                    row["arms"][role]["directional_confirmation_progress"] is not None
                    for row in cycles
                )
                for role in plan["profiles"]
            },
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
    parser.add_argument("--decision-time-last-captures", type=Path)
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
        if args.decision_time_last_captures is not None:
            if args.capture_public_last:
                raise ValueError("I17_DECISION_TIME_PREFLIGHT_REQUIRES_OFFLINE_INPUT")
            source_paths.append(_absolute(args.decision_time_last_captures))
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
            decision_time_archive=(
                None
                if args.decision_time_last_captures is None
                else read_v1(args.decision_time_last_captures)
            ),
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
