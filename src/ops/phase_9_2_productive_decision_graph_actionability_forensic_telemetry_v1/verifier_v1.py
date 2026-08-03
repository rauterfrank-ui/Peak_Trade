"""Verifier for actionability forensic telemetry evidence bundles."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    ACTIONABILITY_CALL_ORDER_V1,
    ENTRY_FUNNEL_KEYS,
    PRIMARY_REASON_STAGE_INDEX,
    TERMINAL_OUTCOMES,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.counters_v1 import (
    counters_match_raw_events_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.funnel_v1 import (
    funnel_counts_monotonic_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    CycleTerminalRecordV1,
)


def _terminal_from_dict(d: Mapping[str, Any]) -> CycleTerminalRecordV1:
    return CycleTerminalRecordV1(
        schema_version=str(d.get("schema_version") or ""),
        repository_sha=str(d.get("repository_sha") or ""),
        config_digest=str(d.get("config_digest") or ""),
        runtime_session_id=str(d.get("runtime_session_id") or ""),
        decision_cycle_id=str(d.get("decision_cycle_id") or ""),
        instrument_id=str(d.get("instrument_id") or ""),
        market_event_time=d.get("market_event_time"),
        terminal_outcome=str(d.get("terminal_outcome") or ""),
        primary_reason=d.get("primary_reason"),
        secondary_reasons=tuple(d.get("secondary_reasons") or ()),
        terminal_blocking_stage=d.get("terminal_blocking_stage"),
        terminal_blocking_stage_index=d.get("terminal_blocking_stage_index"),
        event_digest=str(d.get("event_digest") or ""),
    )


def verify_actionability_telemetry_bundle_v1(
    *,
    stage_events: Sequence[Mapping[str, Any]],
    cycle_terminals: Sequence[Mapping[str, Any]],
    counters: Mapping[str, int],
    entry_funnel: Mapping[str, int],
    claims: Mapping[str, Any] | None = None,
    decision_mutation_detected: bool = False,
    config_mutation_detected: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    terminals = [_terminal_from_dict(t) for t in cycle_terminals]

    all_cycles_terminal = (
        all(t.terminal_outcome in TERMINAL_OUTCOMES for t in terminals) and len(terminals) > 0
    )
    if not all_cycles_terminal:
        blockers.append("ALL_CYCLES_HAVE_TERMINAL_OUTCOME_FALSE")

    non_intent = [
        t
        for t in terminals
        if t.terminal_outcome not in {"ENTRY_INTENT", "REDUCE_INTENT", "EXIT_INTENT"}
    ]
    all_non_intent_primary = all(bool(t.primary_reason) for t in non_intent)
    if not all_non_intent_primary:
        blockers.append("ALL_NON_INTENT_CYCLES_HAVE_PRIMARY_REASON_FALSE")

    primary_matches_call_order = True
    for t in non_intent:
        if not t.primary_reason:
            primary_matches_call_order = False
            break
        expected_idx = PRIMARY_REASON_STAGE_INDEX.get(str(t.primary_reason))
        if expected_idx is None:
            continue
        if t.terminal_blocking_stage_index is not None and int(
            t.terminal_blocking_stage_index
        ) != int(expected_idx):
            # Allow HOLD reasons to map to canonical_intent index.
            if t.primary_reason not in {
                "HOLD_BY_CANONICAL_DECISION",
                "NO_ACTIONABLE_CHANGE",
                "FAIL_CLOSED_INTERNAL_ERROR",
            }:
                # Still accept if stage name matches expected stage.
                expected_stage = ACTIONABILITY_CALL_ORDER_V1[expected_idx]
                if t.terminal_blocking_stage not in {expected_stage, None}:
                    primary_matches_call_order = False
                    break
    if not primary_matches_call_order:
        blockers.append("PRIMARY_REASON_MATCHES_CALL_ORDER_FALSE")

    counters_ok = counters_match_raw_events_v1(counters, terminals)
    if not counters_ok:
        blockers.append("COUNTERS_MATCH_RAW_EVENTS_FALSE")

    funnel_mono = funnel_counts_monotonic_v1(entry_funnel, ENTRY_FUNNEL_KEYS)
    if not funnel_mono:
        blockers.append("FUNNEL_COUNTS_MONOTONIC_FALSE")

    # No stage count may exceed predecessor where funnel-applicable.
    pred = None
    for key in ENTRY_FUNNEL_KEYS:
        val = int(entry_funnel.get(key, 0))
        if pred is not None and val > pred:
            blockers.append("NO_STAGE_COUNT_EXCEEDS_PREDECESSOR_FALSE")
            break
        pred = val

    digests = [str(t.get("event_digest") or "") for t in cycle_terminals]
    digests = [d for d in digests if d]
    no_dup = len(digests) == len(set(digests))
    if not no_dup:
        blockers.append("NO_DUPLICATE_EVENT_APPLICATION_FALSE")

    if decision_mutation_detected:
        blockers.append("NO_DECISION_MUTATION_FALSE")
    if config_mutation_detected:
        blockers.append("NO_CONFIG_MUTATION_FALSE")

    claims_ok = True
    if claims:
        for key in (
            "CORE_LOGIC_CHANGED",
            "CONFIG_CHANGED",
            "PARALLEL_DECISION_ENGINE_CREATED",
        ):
            if claims.get(key) is True:
                claims_ok = False
                blockers.append(f"CLAIMS_MATCH_TELEMETRY_FALSE:{key}")
                break
        if int(claims.get("TOTAL_CYCLES", -1)) not in {-1, len(terminals)}:
            # allow missing; if present must match
            if "TOTAL_CYCLES" in claims and int(claims["TOTAL_CYCLES"]) != len(terminals):
                claims_ok = False
                blockers.append("CLAIMS_MATCH_TELEMETRY_FALSE:TOTAL_CYCLES")

    # Stage event integrity: every cycle should emit exactly one event per stage.
    expected_per_cycle = len(ACTIONABILITY_CALL_ORDER_V1)
    if len(terminals) and len(stage_events) != len(terminals) * expected_per_cycle:
        blockers.append("STAGE_EVENT_COUNT_MISMATCH")

    ok = not blockers
    return {
        "ok": ok,
        "ALL_CYCLES_HAVE_TERMINAL_OUTCOME": all_cycles_terminal,
        "ALL_NON_INTENT_CYCLES_HAVE_PRIMARY_REASON": all_non_intent_primary,
        "PRIMARY_REASON_MATCHES_CALL_ORDER": primary_matches_call_order,
        "COUNTERS_MATCH_RAW_EVENTS": counters_ok,
        "FUNNEL_COUNTS_MONOTONIC": funnel_mono,
        "NO_STAGE_COUNT_EXCEEDS_PREDECESSOR_WHERE_APPLICABLE": "NO_STAGE_COUNT_EXCEEDS_PREDECESSOR_FALSE"
        not in blockers,
        "NO_DUPLICATE_EVENT_APPLICATION": no_dup,
        "NO_DECISION_MUTATION": not decision_mutation_detected,
        "NO_CONFIG_MUTATION": not config_mutation_detected,
        "CLAIMS_MATCH_TELEMETRY": claims_ok,
        "blockers": blockers,
        "cycle_count": len(terminals),
        "stage_event_count": len(stage_events),
    }
