"""I17 candidate arms and the shared decision-time Last-candle contract."""

from __future__ import annotations

from bisect import bisect_right
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import re

import pandas as pd

from src.backtest.strategy_signal_binding_v1 import execute_configured_strategy_signal_series_v1
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, read_v1
from src.ops.economic_md_input_producer_v1.constants_v1 import PUBLIC_HTTP_HOST
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    VENUE_OKX,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    I17OfflineCandidateInputV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (
    run_hardened_wallclock_bridge_observation_cycle_v2,
)
from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import build_suitability_registry_from_snapshot
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    InstrumentObservationKeyV1,
    ObservationCandidateV1,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)

HOUR = timedelta(hours=1)
PLAN_SCHEMA = "native_research_candidate_forward_plan.v1"
LAST_ENDPOINT = "/api/v5/market/history-candles"
CANDIDATE_COMPONENT_PREFIX = "i17_candidate_plan_sha256:"


def _utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() != timedelta(0):
        raise ValueError("EXPLICIT_UTC_REQUIRED")
    return result.astimezone(timezone.utc)


def _milliseconds(value):
    return int(value.timestamp()) * 1000


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


def _validated_last_snapshots(plan, captures, *, registered, end):
    snapshots = []
    previous = None
    for capture in captures:
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


def _capture_journal_paths(journal, namespace):
    hours = journal.safe_path_v1(namespace / "hours")
    return tuple(sorted(hours.glob("*.json"), key=lambda path: int(path.stem)))


def _read_capture_journal(journal, paths, binding):
    captures = []
    for item in paths:
        stored = read_v1(journal.safe_path_v1(item.relative_to(journal.root)))
        capture = stored["capture"]
        if (
            any(stored[key] != value for key, value in binding.items())
            or item.stem != capture["query"]["after"]
        ):
            raise ValueError("I17_DECISION_TIME_CAPTURE_BINDING_OR_CLOCK_CHANGED")
        captures.append(capture)
    return captures


class I17CandidatePairV1:
    """Evaluate two isolated arms through the original bridge on one Mark input."""

    def __init__(self, plan, *, session_prefix):
        self.plan = deepcopy(plan)
        self.instrument = self.plan["instrument_id"]
        self.session_prefix = session_prefix
        registry = build_suitability_registry_from_snapshot(build_registry_snapshot())
        entries = tuple(
            entry for entry in registry.entries if entry.strategy_id == self.plan["strategy_id"]
        )
        if len(entries) != 1:
            raise ValueError("I17_COMPARISON_STRATEGY_REGISTRY_BINDING_MISSING")
        self.entry = entries[0]
        self.states = {
            role: HardenedBridgeSessionStateV2(instrument_id=self.instrument)
            for role in self.plan["profiles"]
        }
        self.acceptance_state = initial_observation_acceptance_state_v1(
            bound_instrument_key=InstrumentObservationKeyV1(
                venue=VENUE_OKX,
                canonical_instrument_id=self.instrument,
                venue_instrument_id=self.instrument,
            )
        )
        self.bindings = {}
        self.last_close = None

    def evaluate(self, tick, *, decided, close_time, candles):
        if close_time != self.last_close:
            if close_time not in candles.index:
                raise ValueError("I17_COMPARISON_HOUR_MISSING_AT_DECISION")
            prefix = candles.loc[:close_time]
            self.bindings = {
                role: _strategy_binding(self.plan, profile, prefix)
                for role, profile in self.plan["profiles"].items()
            }
            self.last_close = close_time
        accepted = evaluate_distinct_market_observation_v1(
            self.acceptance_state,
            ObservationCandidateV1(
                venue=tick.venue,
                canonical_instrument_id=tick.instrument_id,
                venue_instrument_id=self.instrument,
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
            self.acceptance_state = commit_observation_acceptance_v1(
                current_state=self.acceptance_state, result=accepted
            )
        arms = {}
        for role, binding in self.bindings.items():
            state = self.states[role]
            material = normalize_strategy_signal_to_suitability_agreement_material_v1(
                binding,
                instrument_id=self.instrument,
                trading_epoch=state.trading_epoch,
                signal_index=len(binding.signals) - 1,
                expected_configured_strategy_id=self.plan["strategy_id"],
                expected_strategy_version=self.plan["strategy_version"],
            )
            observation = run_hardened_wallclock_bridge_observation_cycle_v2(
                bridge_state=state,
                ticks=(tick,),
                reference_price=Decimal(str(tick.mid_price)),
                wall_now_unix=decided,
                session_id=f"{self.session_prefix}-{role}",
                offline_candidate=I17OfflineCandidateInputV2(
                    self.plan["profiles"][role]["packet"], self.entry, material, accepted
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
        return arms


def candidate_plan_component_v1(plan):
    """The existing preregistration scope digest binds this frozen plan identity."""
    return CANDIDATE_COMPONENT_PREFIX + digest_v1(plan)


class I17CandidateHostObservationV1:
    """Compare paired research decisions using only the scoped local Last journal."""

    def __init__(self, *, plan, journal):
        self.plan = deepcopy(plan)
        self.journal = journal
        self.plan_digest = digest_v1(self.plan)
        self.registered, self.start, self.end = _decision_time_window(self.plan)
        self.namespace = None
        self.capture_paths = ()
        self.snapshots = ()
        self.last_decision_time = None
        self.failure = None

    def bind(self, prereg, *, evidence_root, repo_root):
        components = tuple(
            identity
            for identity in prereg.strategy_component_identities
            if identity.startswith(CANDIDATE_COMPONENT_PREFIX)
        )
        if (
            self.namespace is not None
            or components != (candidate_plan_component_v1(self.plan),)
            or prereg.instrument_allowlist != (self.plan["instrument_id"],)
            or not self.start.timestamp() <= prereg.earliest_start < self.end.timestamp()
            or any(
                self.journal.root.is_relative_to(path) or path.is_relative_to(self.journal.root)
                for path in (evidence_root.resolve(), repo_root.resolve())
            )
        ):
            raise ValueError("I17_CANDIDATE_HOST_PREREGISTRATION_MISMATCH")
        self.scope_digest = prereg.scope_digest()
        self.namespace = _capture_scope_path(self.plan, self.scope_digest)
        self.pair = I17CandidatePairV1(
            self.plan, session_prefix=f"{prereg.session_id}-i17-candidate"
        )

    def observe(self, tick, *, parent_decision_id, clock):
        binding = {
            "plan_digest": self.plan_digest,
            "original_i17_scope_digest": self.scope_digest,
        }
        if self.failure is None:
            try:
                return self._evaluate(tick, parent_decision_id, clock, binding)
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
                self.failure = str(exc)
        return {
            **binding,
            "status": "FAILED",
            "authority": "NONE",
            "parent_decision_id": parent_decision_id,
            "reason": self.failure,
        }

    def _evaluate(self, tick, parent_decision_id, clock, binding):
        paths = _capture_journal_paths(self.journal, self.namespace)
        if paths != self.capture_paths:
            if paths[: len(self.capture_paths)] != self.capture_paths:
                raise ValueError("I17_CANDIDATE_HOST_CAPTURE_JOURNAL_CHANGED")
            records = _read_capture_journal(self.journal, paths, binding)
            self.snapshots = _validated_last_snapshots(
                self.plan, records, registered=self.registered, end=self.end
            )
            self.capture_paths = paths
        decided = clock()
        decision_time = datetime.fromtimestamp(decided, timezone.utc)
        if not self.start <= decision_time < self.end:
            raise ValueError("I17_CANDIDATE_HOST_DECISION_OUTSIDE_WINDOW")
        if self.last_decision_time is not None and decision_time <= self.last_decision_time:
            raise ValueError("I17_CANDIDATE_HOST_DECISION_CLOCK_NOT_ADVANCING")
        snapshots = self.snapshots
        index = bisect_right([row[0] for row in snapshots], decision_time) - 1
        if index < 0:
            raise ValueError("I17_DECISION_TIME_LAST_NOT_YET_AVAILABLE")
        _, candles, trace = snapshots[index]
        close_time = candles.index[-1]
        arms = self.pair.evaluate(tick, decided=decided, close_time=close_time, candles=candles)
        self.last_decision_time = decision_time
        return {
            **binding,
            "status": "COMPARED",
            "authority": "NONE",
            "parent_decision_id": parent_decision_id,
            "mark_sequence": tick.sequence,
            "mark_event_ts_unix": tick.event_ts_unix,
            "mark_receive_ts_unix": tick.receive_ts_unix,
            "decision_time_utc": decision_time.isoformat(),
            "last_candle_close_utc": close_time.isoformat(),
            "last_candle_input": trace,
            "arms": arms,
        }
