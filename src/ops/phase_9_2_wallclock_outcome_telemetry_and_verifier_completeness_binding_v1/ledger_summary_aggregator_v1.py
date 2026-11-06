"""Aggregate wallclock session outcome telemetry exclusively from bridge_cycle_ledger."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.constants_v1 import (
    BRIDGE_CYCLE_LEDGER_FILENAME,
    CAPABILITY_ID,
    OBSERVATION_COUNTERS_FILENAME,
    OWNER,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SUMMARY_SOURCE_OF_TRUTH,
    TERMINAL_OUTCOME_PROJECTION_OWNER,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.terminal_outcome_projection_v1 import (
    classify_intent_bucket_v1,
    cycle_decision_outcome_v1,
    cycle_fill_present_v1,
    cycle_intent_action_v1,
    cycle_intended_side_v1,
    cycle_quantity_source_v1,
    cycle_reason_codes_v1,
    cycle_risk_sizing_result_v1,
    cycle_safety_result_v1,
    is_alpha_blocked_v1,
    is_entry_blocked_v1,
    is_risk_veto_v1,
    is_safety_veto_v1,
    project_terminal_outcome_class_v1,
)


@dataclass(frozen=True)
class WallclockOutcomeTelemetrySummaryV1:
    capability_id: str
    schema_version: str
    producer_version: str
    owner: str
    package_marker: str
    summary_source_of_truth: str
    terminal_outcome_projection_owner: str
    session_cycle_count: int
    distinct_observation_count: int
    terminal_outcome_classes: list[str]
    terminal_outcome_counts: dict[str, int]
    terminal_outcome_sum: int
    terminal_outcome_sum_matches_cycles: bool
    unaccounted_cycle_count: int
    multi_classified_cycle_count: int
    hold_count: int
    no_action_count: int
    entry_intent_count: int
    reduce_intent_count: int
    exit_intent_count: int
    entry_fill_count: int
    reduce_fill_count: int
    exit_fill_count: int
    productive_fill_count: int
    alpha_blocked_count: int
    entry_blocked_count: int
    risk_veto_count: int
    safety_veto_count: int
    reason_code_counts: dict[str, int]
    decision_outcome_counts: dict[str, int]
    safety_result_counts: dict[str, int]
    risk_result_counts: dict[str, int]
    quantity_source_counts: dict[str, int]
    summary_counts_match_ledger: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        # Stable uppercase aliases for machine status blocks.
        payload.update(
            {
                "SESSION_CYCLE_COUNT": self.session_cycle_count,
                "DISTINCT_OBSERVATION_COUNT": self.distinct_observation_count,
                "TERMINAL_OUTCOME_CLASSES": list(self.terminal_outcome_classes),
                "TERMINAL_OUTCOME_COUNTS": dict(self.terminal_outcome_counts),
                "TERMINAL_OUTCOME_SUM": self.terminal_outcome_sum,
                "TERMINAL_OUTCOME_SUM_MATCHES_CYCLES": self.terminal_outcome_sum_matches_cycles,
                "UNACCOUNTED_CYCLE_COUNT": self.unaccounted_cycle_count,
                "MULTI_CLASSIFIED_CYCLE_COUNT": self.multi_classified_cycle_count,
                "HOLD_COUNT": self.hold_count,
                "NO_ACTION_COUNT": self.no_action_count,
                "ENTRY_INTENT_COUNT": self.entry_intent_count,
                "REDUCE_INTENT_COUNT": self.reduce_intent_count,
                "EXIT_INTENT_COUNT": self.exit_intent_count,
                "ENTRY_FILL_COUNT": self.entry_fill_count,
                "REDUCE_FILL_COUNT": self.reduce_fill_count,
                "EXIT_FILL_COUNT": self.exit_fill_count,
                "ALPHA_BLOCKED_COUNT": self.alpha_blocked_count,
                "ENTRY_BLOCKED_COUNT": self.entry_blocked_count,
                "RISK_VETO_COUNT": self.risk_veto_count,
                "SAFETY_VETO_COUNT": self.safety_veto_count,
                "REASON_CODE_COUNTS": dict(self.reason_code_counts),
                "DECISION_OUTCOME_COUNTS": dict(self.decision_outcome_counts),
                "SAFETY_RESULT_COUNTS": dict(self.safety_result_counts),
                "RISK_RESULT_COUNTS": dict(self.risk_result_counts),
                "QUANTITY_SOURCE_COUNTS": dict(self.quantity_source_counts),
                "SUMMARY_COUNTS_MATCH_LEDGER": self.summary_counts_match_ledger,
            }
        )
        return payload


def load_bridge_cycle_ledger_v1(ledger_path: Path) -> list[dict[str, Any]]:
    if not ledger_path.is_file():
        return []
    cycles: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError(f"BRIDGE_CYCLE_LEDGER_NON_OBJECT:{ledger_path}")
        cycles.append(payload)
    return cycles


def _distinct_observation_count_v1(
    cycles: Sequence[Mapping[str, Any]],
    *,
    evidence_root: Path | None,
) -> int:
    if evidence_root is not None:
        counters_path = evidence_root / OBSERVATION_COUNTERS_FILENAME
        if counters_path.is_file():
            payload = json.loads(counters_path.read_text(encoding="utf-8"))
            if isinstance(payload, Mapping):
                for key in ("distinct_observation_count", "accepted_ticks", "cycle_count"):
                    if key in payload:
                        return int(payload[key])
    refs: set[str] = set()
    for cycle in cycles:
        refs.add(json.dumps(cycle.get("market_data_reference"), sort_keys=True, default=str))
    return len(refs)


def _explicit_class_list_v1(cycle: Mapping[str, Any]) -> list[str] | None:
    multi = cycle.get("terminal_outcome_classes")
    if isinstance(multi, (list, tuple)):
        return [str(x) for x in multi if str(x).strip()]
    singular = cycle.get("terminal_outcome_class")
    if singular is not None and str(singular).strip():
        return [str(singular).strip()]
    return None


def aggregate_wallclock_outcome_telemetry_from_cycles_v1(
    cycles: Iterable[Mapping[str, Any]],
    *,
    evidence_root: Path | None = None,
    declared_summary: Mapping[str, Any] | None = None,
) -> WallclockOutcomeTelemetrySummaryV1:
    cycle_list = list(cycles)
    session_cycle_count = len(cycle_list)

    terminal_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    safety_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    quantity_counts: Counter[str] = Counter()

    unaccounted = 0
    multi_classified = 0
    hold_count = 0
    no_action_count = 0
    entry_intent_count = 0
    reduce_intent_count = 0
    exit_intent_count = 0
    entry_fill_count = 0
    reduce_fill_count = 0
    exit_fill_count = 0
    productive_fill_count = 0
    alpha_blocked_count = 0
    entry_blocked_count = 0
    risk_veto_count = 0
    safety_veto_count = 0

    for cycle in cycle_list:
        explicit = _explicit_class_list_v1(cycle)
        if explicit is not None:
            if len(explicit) == 0:
                unaccounted += 1
            elif len(explicit) > 1:
                multi_classified += 1
            else:
                terminal_counts[explicit[0]] += 1
        else:
            projected = project_terminal_outcome_class_v1(cycle)
            if projected is None:
                unaccounted += 1
            else:
                terminal_counts[projected] += 1

        side = cycle_intended_side_v1(cycle)
        action = cycle_intent_action_v1(cycle)
        if side == "HOLD":
            hold_count += 1
        if action == "NONE":
            no_action_count += 1

        bucket = classify_intent_bucket_v1(cycle)
        if bucket == "ENTRY":
            entry_intent_count += 1
        elif bucket == "REDUCE":
            reduce_intent_count += 1
        elif bucket == "EXIT":
            exit_intent_count += 1

        fill_present = cycle_fill_present_v1(cycle)
        if fill_present:
            productive_fill_count += 1
            if bucket == "ENTRY":
                entry_fill_count += 1
            elif bucket == "REDUCE":
                reduce_fill_count += 1
            elif bucket == "EXIT":
                exit_fill_count += 1

        if is_alpha_blocked_v1(cycle):
            alpha_blocked_count += 1
        if is_entry_blocked_v1(cycle):
            entry_blocked_count += 1
        if is_risk_veto_v1(cycle):
            risk_veto_count += 1
        if is_safety_veto_v1(cycle):
            safety_veto_count += 1

        for reason in cycle_reason_codes_v1(cycle):
            reason_counts[reason] += 1
        decision_counts[cycle_decision_outcome_v1(cycle) or ""] += 1
        safety_counts[cycle_safety_result_v1(cycle) or ""] += 1
        risk_counts[cycle_risk_sizing_result_v1(cycle) or ""] += 1
        quantity_counts[cycle_quantity_source_v1(cycle) or ""] += 1

    terminal_outcome_sum = int(sum(terminal_counts.values()))
    terminal_outcome_sum_matches = (
        terminal_outcome_sum == session_cycle_count and unaccounted == 0 and multi_classified == 0
    )
    distinct = _distinct_observation_count_v1(cycle_list, evidence_root=evidence_root)

    summary = WallclockOutcomeTelemetrySummaryV1(
        capability_id=CAPABILITY_ID,
        schema_version=SCHEMA_VERSION,
        producer_version=PRODUCER_VERSION,
        owner=OWNER,
        package_marker=PACKAGE_MARKER,
        summary_source_of_truth=SUMMARY_SOURCE_OF_TRUTH,
        terminal_outcome_projection_owner=TERMINAL_OUTCOME_PROJECTION_OWNER,
        session_cycle_count=session_cycle_count,
        distinct_observation_count=distinct,
        terminal_outcome_classes=sorted(terminal_counts),
        terminal_outcome_counts={k: int(terminal_counts[k]) for k in sorted(terminal_counts)},
        terminal_outcome_sum=terminal_outcome_sum,
        terminal_outcome_sum_matches_cycles=terminal_outcome_sum_matches,
        unaccounted_cycle_count=unaccounted,
        multi_classified_cycle_count=multi_classified,
        hold_count=hold_count,
        no_action_count=no_action_count,
        entry_intent_count=entry_intent_count,
        reduce_intent_count=reduce_intent_count,
        exit_intent_count=exit_intent_count,
        entry_fill_count=entry_fill_count,
        reduce_fill_count=reduce_fill_count,
        exit_fill_count=exit_fill_count,
        productive_fill_count=productive_fill_count,
        alpha_blocked_count=alpha_blocked_count,
        entry_blocked_count=entry_blocked_count,
        risk_veto_count=risk_veto_count,
        safety_veto_count=safety_veto_count,
        reason_code_counts={k: int(reason_counts[k]) for k in sorted(reason_counts)},
        decision_outcome_counts={k: int(decision_counts[k]) for k in sorted(decision_counts)},
        safety_result_counts={k: int(safety_counts[k]) for k in sorted(safety_counts)},
        risk_result_counts={k: int(risk_counts[k]) for k in sorted(risk_counts)},
        quantity_source_counts={k: int(quantity_counts[k]) for k in sorted(quantity_counts)},
        summary_counts_match_ledger=True,
        notes=[
            "SUMMARY_DERIVED_EXCLUSIVELY_FROM_BRIDGE_CYCLE_LEDGER",
            "PROJECTION_DECISION_AUTHORITY=false",
            "PROJECTION_RUNTIME_BEHAVIOR_EFFECT=false",
        ],
    )

    if declared_summary is not None:
        mismatches = compare_declared_summary_to_ledger_v1(summary, declared_summary)
        if mismatches:
            return WallclockOutcomeTelemetrySummaryV1(
                **{
                    **asdict(summary),
                    "summary_counts_match_ledger": False,
                    "notes": list(summary.notes)
                    + ["SUMMARY_COUNTS_MATCH_LEDGER=false"]
                    + mismatches,
                }
            )
    return summary


def compare_declared_summary_to_ledger_v1(
    ledger_summary: WallclockOutcomeTelemetrySummaryV1,
    declared: Mapping[str, Any],
) -> list[str]:
    checks = {
        "HOLD_COUNT": ledger_summary.hold_count,
        "hold_count": ledger_summary.hold_count,
        "NO_ACTION_COUNT": ledger_summary.no_action_count,
        "no_action_count": ledger_summary.no_action_count,
        "ENTRY_FILL_COUNT": ledger_summary.entry_fill_count,
        "entry_fill_count": ledger_summary.entry_fill_count,
        "REDUCE_FILL_COUNT": ledger_summary.reduce_fill_count,
        "reduce_fill_count": ledger_summary.reduce_fill_count,
        "EXIT_FILL_COUNT": ledger_summary.exit_fill_count,
        "exit_fill_count": ledger_summary.exit_fill_count,
        "SESSION_CYCLE_COUNT": ledger_summary.session_cycle_count,
        "session_cycle_count": ledger_summary.session_cycle_count,
        "TERMINAL_OUTCOME_SUM": ledger_summary.terminal_outcome_sum,
        "terminal_outcome_sum": ledger_summary.terminal_outcome_sum,
        "UNACCOUNTED_CYCLE_COUNT": ledger_summary.unaccounted_cycle_count,
        "unaccounted_cycle_count": ledger_summary.unaccounted_cycle_count,
        "MULTI_CLASSIFIED_CYCLE_COUNT": ledger_summary.multi_classified_cycle_count,
        "multi_classified_cycle_count": ledger_summary.multi_classified_cycle_count,
        "RISK_VETO_COUNT": ledger_summary.risk_veto_count,
        "risk_veto_count": ledger_summary.risk_veto_count,
        "SAFETY_VETO_COUNT": ledger_summary.safety_veto_count,
        "safety_veto_count": ledger_summary.safety_veto_count,
    }
    mismatches: list[str] = []
    for key, expected in checks.items():
        if key in declared and int(declared[key]) != int(expected):
            mismatches.append(f"DECLARED_MISMATCH:{key}:{declared[key]}!={expected}")
    if "TERMINAL_OUTCOME_COUNTS" in declared or "terminal_outcome_counts" in declared:
        raw = declared.get("TERMINAL_OUTCOME_COUNTS", declared.get("terminal_outcome_counts"))
        if isinstance(raw, Mapping):
            normalized = {str(k): int(v) for k, v in raw.items()}
            if normalized != ledger_summary.terminal_outcome_counts:
                mismatches.append("DECLARED_MISMATCH:TERMINAL_OUTCOME_COUNTS")
    return mismatches


def aggregate_wallclock_outcome_telemetry_from_evidence_root_v1(
    evidence_root: Path,
    *,
    declared_summary: Mapping[str, Any] | None = None,
) -> WallclockOutcomeTelemetrySummaryV1:
    root = Path(evidence_root)
    cycles = load_bridge_cycle_ledger_v1(root / BRIDGE_CYCLE_LEDGER_FILENAME)
    optional_declared = declared_summary
    if optional_declared is None:
        optional_path = root / "wallclock_outcome_telemetry_summary_v1.json"
        if optional_path.is_file():
            payload = json.loads(optional_path.read_text(encoding="utf-8"))
            if isinstance(payload, Mapping):
                optional_declared = payload
    return aggregate_wallclock_outcome_telemetry_from_cycles_v1(
        cycles,
        evidence_root=root,
        declared_summary=optional_declared,
    )
