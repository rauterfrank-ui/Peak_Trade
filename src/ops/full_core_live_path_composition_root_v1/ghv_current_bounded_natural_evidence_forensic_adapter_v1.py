"""GHV forensic adapter for bounded CURRENT Natural Evidence (AUTHORITY=NONE).

Consumes canonical PRE_EXTERNAL convergence evidence only. Does not inject market data,
decisions, signals, or runtime configuration into Product Runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

OWNER = (
    "full_core_live_path_composition_root_v1."
    "ghv_current_bounded_natural_evidence_forensic_adapter_v1"
)

WORK_PACKAGE_ID = "GHV_CURRENT_BOUNDED_NATURAL_EVIDENCE_INTEGRATION_V1"
GHV_AUTHORITY = "NONE"
COMBINED_REPORT_SCHEMA_VERSION = "ghv_current_bounded_natural_evidence_combined_report.v1"
COMBINED_REPORT_FILENAME = "GHV_CURRENT_BOUNDED_NATURAL_EVIDENCE_COMBINED_REPORT_V1.json"

CURRENT_REPORT_FILENAME = "PRE_EXTERNAL_CONVERGENCE_REPORT.json"

BOUNDED_DEFAULT_MAX_CYCLES = 4
BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS = 180.0

CLASSIFICATION_FACT = "FACT"
CLASSIFICATION_INFERENCE = "INFERENCE"
CLASSIFICATION_HYPOTHESIS = "HYPOTHESIS"

DISPOSITION_HOLD_CLOSED = "HOLD_CLOSED"
S5_PRE_EXTERNAL = "PRE_EXTERNAL_EFFECT"

ECONOMIC_QUALIFICATION_FIXPOINT_REL = (
    "evidence/ops/integrated_offline_economic_evidence_v1/"
    "CURRENT_ECONOMIC_QUALIFICATION_FIXPOINT_V1.json"
)


@dataclass(frozen=True)
class GhvForensicMaterializationResultV1:
    attempted: bool
    status: str
    blocker: str
    causal_analysis_complete: bool
    root_blockers: tuple[str, ...]


@dataclass(frozen=True)
class HoldClosedCycleExplanationV1:
    cycle_index: int
    s5_disposition: str
    classification: str
    statement: str
    supporting_artifact: str


def _parse_bool_field(raw: object) -> bool:
    return str(raw or "").strip().lower() in {"true", "1", "yes"}


def load_current_pre_external_report_v1(evidence_root: Path) -> dict[str, Any]:
    path = Path(evidence_root) / CURRENT_REPORT_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"MISSING_{CURRENT_REPORT_FILENAME}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def explain_hold_closed_cycles_v1(
    *,
    cycle_summaries: Sequence[Mapping[str, Any]],
    evidence_root: Path,
) -> tuple[HoldClosedCycleExplanationV1, ...]:
    """Explain HOLD_CLOSED cycles using CURRENT evidence; GHV supplements are inference-only."""
    signal_rows = _read_jsonl(evidence_root / "directional_signal_observability_v1.jsonl")
    signal_by_cycle: dict[int, dict[str, Any]] = {}
    for row in signal_rows:
        raw_cycle = row.get("cycle_index")
        try:
            cycle_index = int(raw_cycle) if raw_cycle is not None else 0
        except (TypeError, ValueError):
            cycle_index = 0
        if cycle_index > 0:
            signal_by_cycle[cycle_index] = row

    explanations: list[HoldClosedCycleExplanationV1] = []
    for summary in cycle_summaries:
        cycle_index = int(summary.get("cycle_index") or 0)
        disposition = str(summary.get("s5_disposition") or "").strip()
        if disposition != DISPOSITION_HOLD_CLOSED:
            continue
        explanations.append(
            HoldClosedCycleExplanationV1(
                cycle_index=cycle_index,
                s5_disposition=disposition,
                classification=CLASSIFICATION_FACT,
                statement=(
                    "CURRENT S5 terminal disposition for this cycle was HOLD_CLOSED "
                    "(authoritative productive cycle outcome)."
                ),
                supporting_artifact=CURRENT_REPORT_FILENAME,
            )
        )
        sig = signal_by_cycle.get(cycle_index)
        if sig:
            strength = sig.get("signal_strength")
            threshold = sig.get("confirmation_threshold")
            side = sig.get("directional_side") or sig.get("signal_side")
            explanations.append(
                HoldClosedCycleExplanationV1(
                    cycle_index=cycle_index,
                    s5_disposition=disposition,
                    classification=CLASSIFICATION_INFERENCE,
                    statement=(
                        "GHV directional signal observability row present for cycle; "
                        f"side={side!s} signal_strength={strength!s} threshold={threshold!s}. "
                        "Does not override CURRENT disposition."
                    ),
                    supporting_artifact="directional_signal_observability_v1.jsonl",
                )
            )
        elif not (evidence_root / "directional_signal_observability_v1.jsonl").is_file():
            explanations.append(
                HoldClosedCycleExplanationV1(
                    cycle_index=cycle_index,
                    s5_disposition=disposition,
                    classification=CLASSIFICATION_HYPOTHESIS,
                    statement=(
                        "Absence of Natural Enter on this cycle is not classified as a system "
                        "defect without contract evidence; GHV signal ledger absent."
                    ),
                    supporting_artifact="",
                )
            )
    return tuple(explanations)


def materialize_ghv_forensic_artifacts_v1(
    *,
    evidence_root: Path,
    skip_continuation_harness: bool = False,
) -> GhvForensicMaterializationResultV1:
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
        FLIGHT_RECORD_FILENAME,
    )

    flight_path = evidence_root / FLIGHT_RECORD_FILENAME
    if not flight_path.is_file():
        return GhvForensicMaterializationResultV1(
            attempted=False,
            status="SKIPPED",
            blocker="MISSING_FLIGHT_RECORD",
            causal_analysis_complete=False,
            root_blockers=(),
        )

    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_continuation_harness_v1 import (
        run_ghv_pre_external_continuation_harness_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_whole_cycle_causal_observability_v1 import (
        build_whole_cycle_observability_v1,
        persist_whole_cycle_observability_artifacts_v1,
    )

    snapshot_root = evidence_root / "ghv_pre_external_continuation_snapshot_v1"
    harness_report: dict[str, Any] | None = None
    if not skip_continuation_harness and snapshot_root.is_dir():
        harness_report = run_ghv_pre_external_continuation_harness_v1(
            snapshot_root=snapshot_root,
            output_dir=evidence_root,
        )
        (evidence_root / "ghv_pre_external_offline_continuation_harness_report_v1.json").write_text(
            json.dumps(harness_report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    bundle = build_whole_cycle_observability_v1(
        evidence_root=evidence_root,
        harness_report=harness_report,
    )
    persist_whole_cycle_observability_artifacts_v1(evidence_root=evidence_root, bundle=bundle)
    root_blockers = tuple(str(x) for x in (harness_report or {}).get("ROOT_BLOCKERS") or [])
    return GhvForensicMaterializationResultV1(
        attempted=True,
        status="PASS",
        blocker="",
        causal_analysis_complete=bool(bundle.get("CAUSAL_ANALYSIS_COMPLETE")),
        root_blockers=root_blockers,
    )


def _load_economic_qualification_status_v1(repo_root: Path) -> str:
    fixpoint = repo_root / ECONOMIC_QUALIFICATION_FIXPOINT_REL
    if not fixpoint.is_file():
        return "UNKNOWN_FIXPOINT_ABSENT"
    try:
        payload = json.loads(fixpoint.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "UNKNOWN_FIXPOINT_UNREADABLE"
    policy = payload.get("current_integrated_offline_economic_policy_v1")
    if isinstance(policy, Mapping):
        return "CLOSED_REFERENCED_FIXPOINT"
    return "CLOSED_REFERENCED_FIXPOINT"


def assess_evidence_completeness_v1(
    *,
    evidence_root: Path,
    current_report: Mapping[str, Any],
    ghv: GhvForensicMaterializationResultV1,
) -> dict[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
        FLIGHT_RECORD_FILENAME,
    )

    required_current = CURRENT_REPORT_FILENAME
    optional_ghv = (
        FLIGHT_RECORD_FILENAME,
        "ghv_pre_external_causal_blocker_report_v1.json",
        "ghv_pre_external_runtime_state_graph_v1.json",
    )
    present = {
        "current_pre_external_report": (evidence_root / required_current).is_file(),
        "flight_record": (evidence_root / FLIGHT_RECORD_FILENAME).is_file(),
        "ghv_causal_blocker_report": (
            evidence_root / "ghv_pre_external_causal_blocker_report_v1.json"
        ).is_file(),
    }
    cycles = int(current_report.get("CYCLE_COUNT") or 0)
    summaries = current_report.get("S5_CYCLE_SUMMARIES") or []
    cycle_records_match = len(summaries) == cycles or cycles == 0
    ghv_complete = ghv.causal_analysis_complete if ghv.attempted else None
    overall = (
        present["current_pre_external_report"]
        and cycle_records_match
        and (ghv_complete is not False if ghv.attempted else True)
    )
    return {
        "schema_version": "ghv_current_bounded_evidence_completeness.v1",
        "overall_complete": overall,
        "cycle_summaries_align_with_cycle_count": cycle_records_match,
        "artifacts_present": present,
        "optional_ghv_artifacts_checked": list(optional_ghv),
        "ghv_materialization": {
            "attempted": ghv.attempted,
            "status": ghv.status,
            "blocker": ghv.blocker,
        },
    }


def detect_safety_violations_v1(current_report: Mapping[str, Any]) -> tuple[str, ...]:
    violations: list[str] = []
    post_count = int(current_report.get("POST_COUNT") or 0)
    external_effects = int(current_report.get("EXTERNAL_EFFECT_COUNT") or 0)
    if post_count > 0:
        violations.append("UNEXPECTED_POST_COUNT_GT_ZERO")
    if external_effects > 0:
        violations.append("UNEXPECTED_EXTERNAL_EFFECT_COUNT_GT_ZERO")
    if _parse_bool_field(current_report.get("PERMIT_CREATED")):
        violations.append("UNEXPECTED_PERMIT_CREATED")
    return tuple(violations)


def build_combined_bounded_natural_evidence_report_v1(
    *,
    evidence_root: Path,
    repo_root: Path,
    runtime_started: bool,
    runtime_completed: bool,
    ghv: GhvForensicMaterializationResultV1,
    current_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report = dict(current_report or load_current_pre_external_report_v1(evidence_root))
    summaries = list(report.get("S5_CYCLE_SUMMARIES") or [])
    s5_dispositions = [
        {
            "cycle_index": int(s.get("cycle_index") or 0),
            "s5_disposition": str(s.get("s5_disposition") or ""),
        }
        for s in summaries
    ]
    hold_explanations = explain_hold_closed_cycles_v1(
        cycle_summaries=summaries,
        evidence_root=evidence_root,
    )
    completeness = assess_evidence_completeness_v1(
        evidence_root=evidence_root,
        current_report=report,
        ghv=ghv,
    )
    safety_violations = detect_safety_violations_v1(report)

    if ghv.attempted and ghv.status == "PASS":
        ghv_causal_status = (
            "CAUSAL_ANALYSIS_COMPLETE"
            if ghv.causal_analysis_complete
            else "CAUSAL_ANALYSIS_PARTIAL"
        )
    elif ghv.attempted:
        ghv_causal_status = f"GHV_MATERIALIZATION_{ghv.status}"
    else:
        ghv_causal_status = "GHV_SKIPPED_NO_FLIGHT_RECORD"

    contract_violations: list[str] = list(safety_violations)
    if not completeness["overall_complete"]:
        contract_violations.append("EVIDENCE_COMPLETENESS_GAP")

    natural_enter = _parse_bool_field(report.get("NATURAL_ENTER_OBSERVED"))
    pre_external = _parse_bool_field(report.get("PRE_EXTERNAL_REACHED"))

    if pre_external and natural_enter:
        next_action = "REVIEW_PRE_EXTERNAL_EVIDENCE_AND_PENDING_OUTCOME_CLOSURE"
    elif (
        all(str(s.get("s5_disposition") or "") == DISPOSITION_HOLD_CLOSED for s in summaries)
        and summaries
    ):
        next_action = "CONTINUE_BOUNDED_OBSERVATION_WITH_FRESH_OWNER_RUN_GO"
    elif not runtime_completed:
        next_action = "RESOLVE_RUNTIME_BLOCKER_BEFORE_REOBSERVATION"
    else:
        next_action = "REVIEW_COMBINED_REPORT_AND_GHV_CAUSAL_ARTIFACTS"

    return {
        "schema_version": COMBINED_REPORT_SCHEMA_VERSION,
        "work_package": WORK_PACKAGE_ID,
        "owner": OWNER,
        "CURRENT_AUTHORITY_SHA": str(
            report.get("BASELINE_SHA") or report.get("EXECUTION_HEAD_SHA") or ""
        ),
        "GHV_AUTHORITY": GHV_AUTHORITY,
        "EVIDENCE_ROOT": str(evidence_root.resolve()),
        "RUNTIME_STARTED": runtime_started,
        "RUNTIME_COMPLETED": runtime_completed,
        "CYCLES_EXECUTED": int(report.get("CYCLE_COUNT") or len(summaries)),
        "NATURAL_ENTER_OBSERVED": natural_enter,
        "PRE_EXTERNAL_REACHED": pre_external,
        "TOTAL_WALLCLOCK_SECONDS": report.get("TOTAL_WALLCLOCK_SECONDS"),
        "PREFLIGHT_ELAPSED_SECONDS": report.get("PREFLIGHT_ELAPSED_SECONDS"),
        "SEQUENCER_ELAPSED_SECONDS": report.get("SEQUENCER_ELAPSED_SECONDS"),
        "FINALIZATION_ELAPSED_SECONDS": report.get("FINALIZATION_ELAPSED_SECONDS"),
        "MAX_RUN_DURATION_SECONDS_SCOPE": report.get("MAX_RUN_DURATION_SECONDS_SCOPE"),
        "S5_DISPOSITIONS": s5_dispositions,
        "HOLD_CLOSED_EXPLANATIONS": [
            {
                "cycle_index": e.cycle_index,
                "s5_disposition": e.s5_disposition,
                "classification": e.classification,
                "statement": e.statement,
                "supporting_artifact": e.supporting_artifact,
            }
            for e in hold_explanations
        ],
        "GHV_CAUSAL_CHAIN_STATUS": ghv_causal_status,
        "GHV_ROOT_BLOCKERS": list(ghv.root_blockers),
        "GHV_CONTRACT_VIOLATIONS": contract_violations,
        "EVIDENCE_COMPLETENESS": completeness,
        "POST_COUNT": int(report.get("POST_COUNT") or 0),
        "ORDER_COUNT": int(report.get("EXTERNAL_EFFECT_COUNT") or 0),
        "SAFETY_VIOLATIONS": list(safety_violations),
        "ECONOMIC_QUALIFICATION_STATUS": _load_economic_qualification_status_v1(repo_root),
        "NEXT_RECOMMENDED_ACTION": next_action,
        "CURRENT_TERMINAL_DISPOSITION": str(report.get("TERMINAL_DISPOSITION") or ""),
        "NATURAL_ENTER_ACCOUNTING": {
            "natural_pre_external_reached": _parse_bool_field(
                report.get("NATURAL_PRE_EXTERNAL_REACHED")
            ),
            "reporting_s5_disposition": str(report.get("REPORTING_S5_DISPOSITION") or ""),
            "dpo_decision_outcome": str((report.get("DPO") or {}).get("decision_outcome") or ""),
        },
    }


def persist_combined_report_v1(*, evidence_root: Path, report: Mapping[str, Any]) -> Path:
    out = Path(evidence_root) / COMBINED_REPORT_FILENAME
    out.write_text(json.dumps(dict(report), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return out


def build_bounded_natural_evidence_launcher_argv_v1(
    *,
    repo_root: Path,
    launcher_script: Path,
    evidence_root: Path,
    lane_state_root: Path,
    productivity_root: Path,
    max_cycles: int = BOUNDED_DEFAULT_MAX_CYCLES,
    max_run_duration_seconds: float = BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS,
    enable_ghv_forensic_capture: bool = True,
) -> list[str]:
    argv = [
        str(repo_root / "scripts/pt"),
        str(launcher_script),
        "--evidence-root",
        str(evidence_root),
        "--lane-state-root",
        str(lane_state_root),
        "--productivity-root",
        str(productivity_root),
        "--max-cycles",
        str(int(max_cycles)),
        "--max-run-duration-seconds",
        str(float(max_run_duration_seconds)),
        "--wp-branch-evidence-run",
    ]
    if enable_ghv_forensic_capture:
        argv.extend(
            [
                "--enable-golden-happy-vector-forensic-observability-v1",
                "--enable-ghv-pre-external-runtime-flight-recorder-v1",
            ]
        )
    return argv


__all__ = [
    "BOUNDED_DEFAULT_MAX_CYCLES",
    "BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS",
    "COMBINED_REPORT_FILENAME",
    "GHV_AUTHORITY",
    "OWNER",
    "WORK_PACKAGE_ID",
    "GhvForensicMaterializationResultV1",
    "HoldClosedCycleExplanationV1",
    "build_bounded_natural_evidence_launcher_argv_v1",
    "build_combined_bounded_natural_evidence_report_v1",
    "explain_hold_closed_cycles_v1",
    "load_current_pre_external_report_v1",
    "materialize_ghv_forensic_artifacts_v1",
    "persist_combined_report_v1",
]
