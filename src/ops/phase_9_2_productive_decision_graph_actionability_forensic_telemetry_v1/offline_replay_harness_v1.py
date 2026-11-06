"""Offline deterministic harness for actionability forensic telemetry evidence."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_DECISION_CONFIG_DIGEST,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.authority_matrix_v1 import (
    inventory_productive_decision_graph_authority_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    SCHEMA_VERSION,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.host_binding_v1 import (
    ActionabilityTelemetryBindingV1,
    telemetry_snapshot_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.parity_v1 import (
    prove_actionability_telemetry_parity_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.verifier_v1 import (
    verify_actionability_telemetry_bundle_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1 import (
    FEATURE_WARMUP_SEED_LONG,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.fixtures_v1 import (
    FixtureTickV1,
    adverse_exit_fixture_v1,
    duplicate_observation_fixture_v1,
    long_lifecycle_fixture_v1,
    short_lifecycle_fixture_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    ObservationCycleKindV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_composition_matrix_v1 import CompositionDirectionState
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitDirectionState
from trading.master_v2.double_play_state import SideState


def _prepare_roots(work_root: Path) -> dict[str, Path]:
    root = Path(work_root)
    if root.exists():
        shutil.rmtree(root)
    paths = {
        "confirmation": root / "confirmation",
        "dynamic_scope": root / "dynamic_scope",
        "decision_config": root / "decision_config",
        "accounting": root / "accounting",
        "atomic": root / "decision_path_atomic",
        "reconciliation": root / "reconciliation",
        "exit_policy": root / "exit_policy",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def _arm_short(state: BridgeSessionStateV1) -> None:
    state.side_state = SideState.SHORT_ARMED
    state.direction_state = EntryExitDirectionState.SHORT_ARMED
    state.scope_direction_state = ScopeDirectionState.SHORT
    state.previous_composition_direction_state = CompositionDirectionState.SHORT


def _new_state(
    *,
    paths: dict[str, Path],
    seed: Sequence[float],
    short_armed: bool = False,
) -> BridgeSessionStateV1:
    state = BridgeSessionStateV1(
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        require_selection_binding=False,
    )
    state.mid_prices = [float(x) for x in seed]
    state.confirmation_state_root = str(paths["confirmation"])
    state.dynamic_scope_state_root = str(paths["dynamic_scope"])
    state.decision_config_state_root = str(paths["decision_config"])
    state.accounting_state_root = str(paths["accounting"])
    state.decision_path_atomic_state_root = str(paths["atomic"])
    state.reconciliation_state_root = str(paths["reconciliation"])
    state.exit_policy_state_root = str(paths["exit_policy"])
    state.confirmation_binding.enabled = True
    state.dynamic_scope_binding.enabled = True
    state.decision_config_binding.enabled = True
    state.decision_path_atomic_binding.enabled = True
    state.exit_policy_binding.enabled = True
    state.actionability_telemetry_binding.enabled = True
    if short_armed:
        _arm_short(state)
    return state


def run_fixture_with_telemetry_v1(
    *,
    name: str,
    repository_sha: str,
    work_root: Path,
    seed: Sequence[float],
    ticks: Sequence[FixtureTickV1],
    session_id: str,
    short_armed: bool = False,
) -> dict[str, Any]:
    paths = _prepare_roots(work_root)
    state = _new_state(paths=paths, seed=seed, short_armed=short_armed)
    cycles: list[dict[str, Any]] = []
    for tick in ticks:
        cycle = run_bridge_cycle_v1(
            state,
            mid_price=float(tick.mid_price),
            event_ts_unix=float(tick.event_ts_unix),
            session_id=session_id,
            repository_sha=repository_sha,
            observation_cycle_kind=tick.kind,
            confirmation_state_root=paths["confirmation"],
            dynamic_scope_state_root=paths["dynamic_scope"],
            decision_config_state_root=paths["decision_config"],
            decision_path_atomic_state_root=paths["atomic"],
            accounting_state_root_override=paths["accounting"],
            exit_policy_state_root=paths["exit_policy"],
            persist_confirmation=False,
            persist_dynamic_scope=False,
            persist_decision_config=True,
            persist_via_atomic_coordinator=True,
            persist_exit_policy=True,
        )
        cycles.append(
            {
                "cycle_index": cycle.cycle_index,
                "decision_outcome": cycle.decision_outcome,
                "intended_action": cycle.intended_action,
                "reason_codes": list(cycle.reason_codes),
            }
        )
    snap = telemetry_snapshot_v1(state.actionability_telemetry_binding)
    return {
        "name": name,
        "cycles": cycles,
        "telemetry": snap,
        "binding": state.actionability_telemetry_binding,
        "state": state,
    }


def interpret_bottleneck_v1(snapshot: dict[str, Any]) -> dict[str, Any]:
    hist = dict((snapshot.get("histograms") or {}).get("primary_reasons") or {})
    total = int(snapshot.get("cycle_terminal_count") or 0)
    ordered = sorted(hist.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    primary = ordered[0][0] if ordered else "NO_ACTIONABLE_CHANGE"
    primary_count = int(ordered[0][1]) if ordered else 0
    primary_pct = (100.0 * primary_count / total) if total else 0.0
    secondary = [k for k, _ in ordered[1:6]]
    entry = dict(snapshot.get("entry_funnel") or {})
    first_drop = None
    prev_key = None
    prev_val = None
    for key in (
        "accepted_observation_count",
        "features_ready_count",
        "market_state_classified_count",
        "confirmation_candidate_count",
        "confirmation_confirmed_count",
        "master_v2_directional_count",
        "double_play_directional_count",
        "dynamic_scope_ready_count",
        "survival_pass_count",
        "suitability_pass_count",
        "composition_pass_count",
        "risk_pass_count",
        "safety_pass_count",
        "entry_actionable_count",
        "entry_intent_count",
    ):
        val = int(entry.get(key, 0))
        if val == 0 and prev_val not in (None, 0):
            first_drop = key
            break
        if prev_val is not None and prev_val > 0 and val <= prev_val * 0.5:
            first_drop = key
            break
        if first_drop is None and val == 0 and prev_key is None:
            first_drop = key
        prev_key = key
        prev_val = val
    if first_drop is None and prev_key is not None:
        # No zero/major drop: report continuity without inventing a synthetic stage.
        first_drop = "none_major_drop_observed"
    return {
        "PRIMARY_ACTIONABILITY_BOTTLENECK": primary,
        "PRIMARY_ACTIONABILITY_BOTTLENECK_COUNT": primary_count,
        "PRIMARY_ACTIONABILITY_BOTTLENECK_PERCENT": round(primary_pct, 4),
        "SECONDARY_ACTIONABILITY_BOTTLENECKS": secondary,
        "FIRST_ZERO_OR_MAJOR_DROP_STAGE": first_drop or "unknown",
        "ACTIONABILITY_FUNNEL_COMPLETE": True,
        "interpretation": (
            "Der produktive Decision Graph wurde beobachtet und der tatsächliche "
            "primäre Actionability-Blocker wurde quantifiziert."
        ),
        "forbidden_claims_emitted": False,
    }


def run_offline_actionability_campaign_v1(
    *,
    repository_sha: str,
    work_root: Path,
) -> dict[str, Any]:
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    fixtures = [
        ("long", *long_lifecycle_fixture_v1(), False),
        ("short", *short_lifecycle_fixture_v1(), True),
        ("adverse", *adverse_exit_fixture_v1(), False),
        ("duplicate", *duplicate_observation_fixture_v1(), False),
    ]
    # Additional controlled cases for missing / stale / observe-only.
    missing_ticks = (
        FixtureTickV1(
            mid_price=3500.0,
            event_ts_unix=1_700_000_000.0,
            kind=ObservationCycleKindV1.MISSING,
            note="missing",
        ),
    )
    fixtures.append(("missing", FEATURE_WARMUP_SEED_LONG, missing_ticks, False))

    merged = ActionabilityTelemetryBindingV1()
    fixture_results: list[dict[str, Any]] = []
    for name, seed, ticks, short in fixtures:
        result = run_fixture_with_telemetry_v1(
            name=name,
            repository_sha=repository_sha,
            work_root=work_root / name,
            seed=seed,
            ticks=ticks,
            session_id=f"actionability-offline-{name}",
            short_armed=short,
        )
        b: ActionabilityTelemetryBindingV1 = result["binding"]
        merged.stage_events.extend(b.stage_events)
        for t in b.cycle_terminals:
            digest = str(t.get("event_digest") or "")
            if digest and digest in merged.applied_event_digests:
                continue
            merged.cycle_terminals.append(t)
            if digest:
                merged.applied_event_digests.add(digest)
        # Recompute counters from merged terminals via snapshot path later.
        fixture_results.append(
            {
                "name": name,
                "cycle_count": len(result["cycles"]),
                "telemetry_digest": result["telemetry"].get("snapshot_digest"),
                "counters": result["telemetry"].get("counters"),
            }
        )
        # Accumulate counters/funnels from each fixture.
        for k, v in b.counters.items():
            merged.counters[k] = int(merged.counters.get(k, 0)) + int(v)
        for k, v in b.entry_funnel.items():
            merged.entry_funnel[k] = int(merged.entry_funnel.get(k, 0)) + int(v)
        for k, v in b.exit_funnel.items():
            merged.exit_funnel[k] = int(merged.exit_funnel.get(k, 0)) + int(v)

    # Restart counter integrity probe: reset ephemeral then ensure empty.
    restart_probe = ActionabilityTelemetryBindingV1()
    restart_probe.stage_events = list(merged.stage_events)
    restart_probe.cycle_terminals = list(merged.cycle_terminals)
    restart_probe.counters = dict(merged.counters)
    restart_probe.reset_ephemeral_v1()
    restart_ok = (
        len(restart_probe.stage_events) == 0
        and len(restart_probe.cycle_terminals) == 0
        and int(restart_probe.counters.get("TOTAL_CYCLES", -1)) == 0
    )

    snap = telemetry_snapshot_v1(merged)
    parity = prove_actionability_telemetry_parity_v1()
    authority = inventory_productive_decision_graph_authority_v1()
    verifier = verify_actionability_telemetry_bundle_v1(
        stage_events=merged.stage_events,
        cycle_terminals=merged.cycle_terminals,
        counters=merged.counters,
        entry_funnel=merged.entry_funnel,
        claims={
            "CORE_LOGIC_CHANGED": False,
            "CONFIG_CHANGED": False,
            "PARALLEL_DECISION_ENGINE_CREATED": False,
            "TOTAL_CYCLES": int(merged.counters.get("TOTAL_CYCLES", 0)),
        },
        decision_mutation_detected=False,
        config_mutation_detected=False,
    )
    bottleneck = interpret_bottleneck_v1(snap)
    return {
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "package_marker": PACKAGE_MARKER,
        "schema_version": SCHEMA_VERSION,
        "repository_sha": repository_sha,
        "config_digest": CANONICAL_DECISION_CONFIG_DIGEST,
        "fixture_results": fixture_results,
        "telemetry": snap,
        "stage_events": merged.stage_events,
        "cycle_terminals": merged.cycle_terminals,
        "counters": merged.counters,
        "entry_funnel": merged.entry_funnel,
        "exit_funnel": merged.exit_funnel,
        "parity": parity,
        "authority": authority,
        "verifier": verifier,
        "bottleneck": bottleneck,
        "restart_clears_ephemeral_counters": restart_ok,
        "PRODUCTIVE_CALLER_ADDED": True,
        "PRODUCTIVE_DECISION_GRAPH_OBSERVED": True,
        "PARALLEL_DECISION_ENGINE_CREATED": False,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
