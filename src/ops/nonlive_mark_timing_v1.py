"""Opt-in, thread-local observation at the original non-live consumer calls."""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
import time
from contextlib import contextmanager
from functools import wraps
from inspect import unwrap
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def observe_demo_call_v1(method):
    @wraps(method)
    def wrapped(host, *, observation, **kwargs):
        if not os.environ.get("PEAK_TRADE_NONLIVE_TIMING_DIR"):
            return method(host, observation=observation, **kwargs)
        native = host.budget.bound.venue_native_id
        try:
            rows = [r for r in observation.mark_price_payload["data"] if r["instId"] == native]
            (row,) = rows
            scope = observe_nonlive_mark_v1(
                mode="TESTNET",
                session=host.writer_session_id,
                lane="LANE_3",
                native=native,
                canonical=host.budget.bound.instrument_id,
                event_ms=int(row["ts"]),
                price=row["markPx"],
                receipt=observation.mark_acquired_at_utc,
            )
        except (ValueError, TypeError, KeyError, AttributeError):
            # Let the original Demo owner handle missing or invalid observations.
            return method(host, observation=observation, **kwargs)
        with scope:
            return method(host, observation=observation, **kwargs)

    return wrapped


def _receive_ns(stamp):
    if isinstance(stamp, str):
        value = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if value.tzinfo is None:
            raise ValueError("receipt requires timezone")
        stamp = value.timestamp()
    return round(stamp * 1_000_000_000)


@contextmanager
def observe_nonlive_mark_v1(
    *, mode, session, lane, native, event_ms, price, receipt, canonical, paper_episode_id=None
):
    directory = os.environ.get("PEAK_TRADE_NONLIVE_TIMING_DIR")
    if not directory:
        yield
        return
    if mode not in {"PAPER", "SHADOW", "TESTNET"}:
        raise ValueError("non-live timing scope required")

    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
        immutable_json_v1,
    )

    detail = os.environ.get("PEAK_TRADE_NONLIVE_TIMING_STAGES") == "1"
    trace = dict(
        schema="nonlive_mark_timing.v1",
        mode=mode,
        session=session,
        lane=lane,
        native_id=native,
        canonical_id=canonical,
        event_ms=event_ms,
        mark_px=str(price),
        receipt=receipt,
        clock_host=platform.node(),
        calls=[],
        profile_status="HOST_ONLY",
    )
    if mode == "PAPER" and paper_episode_id:
        trace["paper_episode_id"] = paper_episode_id
    try:
        trace["host_start_unix_ns"] = time.time_ns()
        trace["host_start_mono_ns"] = time.perf_counter_ns()
        if detail:
            with _observe_stages(trace, canonical):
                yield
        else:
            yield
    finally:
        trace["host_end_mono_ns"] = time.perf_counter_ns()
        trace["host_end_unix_ns"] = time.time_ns()
        try:
            trace["receipt_unix_ns"] = _receive_ns(receipt)
            immutable_json_v1(Path(directory) / "consumer" / (uuid4().hex + ".json"), trace)
        except (ValueError, OSError, TypeError, OverflowError) as exc:
            logging.getLogger(__name__).warning("Mark timing record unavailable: %s", exc)


@contextmanager
def _observe_stages(trace, canonical):
    # Observe the original calls on this thread. Detailed profiling affects latency.
    mode, native, session = trace["mode"], trace["native_id"], trace["session"]
    event_ms, price = trace["event_ms"], trace["mark_px"]
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        run_current_productive_master_v2_runtime_cycle_v1,
    )
    from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
        execute_naked_layered_core_mechanical_step_v1,
    )
    from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1 import (
        apply_l10_bull_bear_switch_v1,
    )

    stages = {
        run_current_productive_master_v2_runtime_cycle_v1.__code__: "master_v2",
        execute_naked_layered_core_mechanical_step_v1.__code__: "double_play_scope_l6_l10",
        apply_l10_bull_bear_switch_v1.__code__: "double_play_l10",
    }
    if mode == "PAPER":
        from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_continuation_v1 import (
            ZkpPaperContinuationV1,
        )

        stages[ZkpPaperContinuationV1._publish_booking.__code__] = "paper_reversal_publication"
    if mode == "SHADOW":
        from trading.master_v2.deterministic_scope_event_generator_v1 import (
            generate_deterministic_scope_event,
        )
        from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
            run_integrated_offline_trading_logic_replay_v1,
        )

        stages = {
            unwrap(
                run_integrated_offline_trading_logic_replay_v1
            ).__code__: "shadow_master_v2_replay",
            unwrap(generate_deterministic_scope_event).__code__: "shadow_scope_event",
        }
    calls = trace["calls"]
    active = {}
    previous = sys.getprofile()
    trace["profile_status"] = "ACTIVE" if previous is None else "EXISTING_PROFILER"
    cycle_id = None

    def profile(frame, event, result):
        nonlocal cycle_id
        stage = stages[frame.f_code]
        now = time.perf_counter_ns()
        if event == "call":
            if stage == "paper_reversal_publication":
                args = frame.f_locals
                if args["self"].root.name != session or args["self"].slot.native_id != native:
                    return
                record = args["record"]
                row = dict(
                    stage=stage,
                    cycle_id=record["plan"]["cycle_id"],
                    decision_id=record["plan"]["decision_id"],
                    fill_id=record["fill"]["fill_id"],
                    start_mono_ns=now,
                )
                calls.append(row)
                active[frame] = row
                return
            if stage == "master_v2":
                args = frame.f_locals
                bound = args["bound_instrument"]
                if getattr(bound, "instrument_id", None) != canonical:
                    return
                if getattr(bound, "venue_native_id", None) != native or args["mark_px"] != float(
                    price
                ):
                    return
                provenance = args["canonical_price_provenance"]
                try:
                    original = json.loads(provenance.mark_clock_json)["payload"]["data"]
                    matches = [r for r in original if r.get("instId") == native]
                    if (
                        len(matches) != 1
                        or int(matches[0]["ts"]) != event_ms
                        or float(matches[0]["markPx"]) != args["mark_px"]
                    ):
                        return
                except (AttributeError, KeyError, ValueError, TypeError):
                    return
                cycle_id = args["cycle_id"]
            if stage == "shadow_master_v2_replay":
                inp = frame.f_locals["inp"]
                ctx = inp.canonical_market_context
                if (
                    ctx.instrument_id != canonical
                    or ctx.mark_price != float(price)
                    or round(_receive_ns(ctx.market_event_time) / 1_000_000) != event_ms
                ):
                    trace["shadow_context_mark_identity_matched"] = False
                    return
                trace["shadow_context_mark_identity_matched"] = True
                cycle_id = inp.replay_id
            if cycle_id is None:
                return
            if stage == "shadow_scope_event":
                inp = frame.f_locals["inp"]
                if inp.instrument_id != canonical or inp.current_price != float(price):
                    return
            if stage == "double_play_scope_l6_l10":
                args = frame.f_locals
                if args["episode"].instrument_key.venue_instrument_id != native or args[
                    "step"
                ].mark_price_m_t != float(price):
                    return
            if stage == "double_play_l10" and not any(
                r["stage"] == "double_play_scope_l6_l10" for r in active.values()
            ):
                return
            row = dict(stage=stage, cycle_id=cycle_id, start_mono_ns=now)
            calls.append(row)
            active[frame] = row
        elif frame in active:
            row = active.pop(frame)
            row.update(
                end_mono_ns=now, duration_ns=now - row["start_mono_ns"], returned=result is not None
            )
            if stage in {"master_v2", "shadow_master_v2_replay"}:
                cycle_id = None
                row["decision"] = getattr(
                    getattr(result, "evidence", result), "decision_outcome", None
                )
            elif stage == "shadow_scope_event":
                row["scope_event"] = getattr(getattr(result, "event_type", None), "value", None)
            elif stage != "paper_reversal_publication":
                row["switch_condition_met"] = getattr(result, "switch_condition_met", None)

    def safe_profile(frame, event, result):
        if event not in ("call", "return") or frame.f_code not in stages:
            return
        try:
            profile(frame, event, result)
        except (AttributeError, ValueError, TypeError, KeyError, OverflowError):
            trace["profile_status"] = "INVALID_TIMING_INPUT"

    if previous is None:
        sys.setprofile(safe_profile)
    try:
        yield
    finally:
        if previous is None:
            sys.setprofile(None)
