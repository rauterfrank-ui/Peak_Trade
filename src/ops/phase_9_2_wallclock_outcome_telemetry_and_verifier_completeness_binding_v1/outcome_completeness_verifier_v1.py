"""Fail-closed completeness verifier for wallclock decision-outcome accounting."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.constants_v1 import (
    BRIDGE_CYCLE_LEDGER_FILENAME,
    CAPABILITY_ID,
    EMPTY_LEDGER_WITH_CYCLES_BLOCKER,
    FILL_COUNT_MISMATCH_BLOCKER,
    HOLD_COUNT_MISMATCH_BLOCKER,
    MULTI_CLASSIFIED_CYCLES_BLOCKER,
    NO_ACTION_COUNT_MISMATCH_BLOCKER,
    OBSERVATION_COUNTERS_FILENAME,
    OWNER,
    RESULT_FAIL,
    RESULT_PASS,
    SUMMARY_MISMATCH_BLOCKER,
    TERMINAL_SUM_MISMATCH_BLOCKER,
    TERMINAL_VERDICT_FILENAME,
    UNACCOUNTED_CYCLES_BLOCKER,
    ZERO_CYCLE_PASS_BLOCKER,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.ledger_summary_aggregator_v1 import (
    WallclockOutcomeTelemetrySummaryV1,
    aggregate_wallclock_outcome_telemetry_from_evidence_root_v1,
    compare_declared_summary_to_ledger_v1,
)


@dataclass
class WallclockOutcomeCompletenessVerificationResultV1:
    result: str
    verified: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    capability_id: str = CAPABILITY_ID
    owner: str = OWNER
    validates_outcome_completeness: bool = True
    can_pass_with_unaccounted_outcomes: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _declared_cycle_count_v1(evidence_root: Path, ledger_len: int) -> int:
    counters_path = evidence_root / OBSERVATION_COUNTERS_FILENAME
    if counters_path.is_file():
        payload = json.loads(counters_path.read_text(encoding="utf-8"))
        if isinstance(payload, Mapping) and "cycle_count" in payload:
            return int(payload["cycle_count"])
    return ledger_len


def _terminal_verdict_payload_v1(evidence_root: Path) -> dict[str, Any]:
    path = evidence_root / TERMINAL_VERDICT_FILENAME
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def verify_wallclock_outcome_completeness_v1(
    *,
    evidence_root: Path,
    declared_summary: Mapping[str, Any] | None = None,
) -> WallclockOutcomeCompletenessVerificationResultV1:
    root = Path(evidence_root)
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"OWNER={OWNER}",
        "VERIFIER_VALIDATES_OUTCOME_COMPLETENESS=true",
        "VERIFIER_CAN_PASS_WITH_UNACCOUNTED_OUTCOMES=false",
        "VERIFIER_NO_NETWORK",
        "VERIFIER_NO_MUTATION",
    ]
    blockers: list[str] = []

    if not root.is_dir():
        return WallclockOutcomeCompletenessVerificationResultV1(
            result=RESULT_FAIL,
            verified=False,
            blockers=["EVIDENCE_ROOT_MISSING"],
            notes=notes,
        )

    ledger_path = root / BRIDGE_CYCLE_LEDGER_FILENAME
    ledger_exists = ledger_path.is_file()
    summary = aggregate_wallclock_outcome_telemetry_from_evidence_root_v1(
        root,
        declared_summary=declared_summary,
    )
    declared_cycle_count = _declared_cycle_count_v1(root, summary.session_cycle_count)
    terminal = _terminal_verdict_payload_v1(root)
    verdict = str(terminal.get("verdict") or "")
    incomplete = bool(terminal.get("incomplete"))

    if declared_cycle_count > 0 and ((not ledger_exists) or summary.session_cycle_count == 0):
        blockers.append(EMPTY_LEDGER_WITH_CYCLES_BLOCKER)

    if declared_cycle_count == 0 and summary.session_cycle_count == 0:
        # Explicit empty-session contract: never treat 0==0 as implicit completeness.
        # Only ABORT or incomplete empty sessions are admissible.
        if not (incomplete or verdict == "ABORT"):
            blockers.append(ZERO_CYCLE_PASS_BLOCKER)
        notes.append("ZERO_CYCLE_SESSION_EXPLICIT_CONTRACT_APPLIED")
        unique = sorted(set(blockers))
        return WallclockOutcomeCompletenessVerificationResultV1(
            result=RESULT_FAIL if unique else RESULT_PASS,
            verified=not unique,
            blockers=unique,
            notes=notes
            + [
                "ZERO_CYCLE_NOT_IMPLICITLY_COMPLETE",
                f"TERMINAL_VERDICT={verdict or 'MISSING'}",
                f"INCOMPLETE={incomplete}",
            ],
            summary=summary.to_dict(),
        )

    if summary.session_cycle_count != declared_cycle_count and declared_cycle_count > 0:
        blockers.append(
            f"CYCLE_COUNT_LEDGER_MISMATCH:{summary.session_cycle_count}!={declared_cycle_count}"
        )

    if summary.unaccounted_cycle_count != 0:
        blockers.append(UNACCOUNTED_CYCLES_BLOCKER)
    if summary.multi_classified_cycle_count != 0:
        blockers.append(MULTI_CLASSIFIED_CYCLES_BLOCKER)
    if summary.terminal_outcome_sum != summary.session_cycle_count:
        blockers.append(TERMINAL_SUM_MISMATCH_BLOCKER)
    if not summary.terminal_outcome_sum_matches_cycles:
        blockers.append("TERMINAL_OUTCOME_SUM_MATCHES_CYCLES=false")

    fill_sum = summary.entry_fill_count + summary.reduce_fill_count + summary.exit_fill_count
    if fill_sum != summary.productive_fill_count:
        blockers.append(FILL_COUNT_MISMATCH_BLOCKER)

    if declared_summary is not None:
        mismatches = compare_declared_summary_to_ledger_v1(summary, declared_summary)
        if mismatches or not summary.summary_counts_match_ledger:
            blockers.append(SUMMARY_MISMATCH_BLOCKER)
            for item in mismatches:
                if "HOLD_COUNT" in item or "hold_count" in item:
                    blockers.append(HOLD_COUNT_MISMATCH_BLOCKER)
                if "NO_ACTION_COUNT" in item or "no_action_count" in item:
                    blockers.append(NO_ACTION_COUNT_MISMATCH_BLOCKER)
                if "FILL_COUNT" in item or "fill_count" in item:
                    blockers.append(FILL_COUNT_MISMATCH_BLOCKER)

    if not summary.summary_counts_match_ledger:
        blockers.append(SUMMARY_MISMATCH_BLOCKER)

    unique = sorted(set(blockers))
    return WallclockOutcomeCompletenessVerificationResultV1(
        result=RESULT_FAIL if unique else RESULT_PASS,
        verified=not unique,
        blockers=unique,
        notes=notes
        + [
            f"SESSION_CYCLE_COUNT={summary.session_cycle_count}",
            f"TERMINAL_OUTCOME_SUM={summary.terminal_outcome_sum}",
            f"UNACCOUNTED_CYCLE_COUNT={summary.unaccounted_cycle_count}",
            f"MULTI_CLASSIFIED_CYCLE_COUNT={summary.multi_classified_cycle_count}",
            f"SUMMARY_COUNTS_MATCH_LEDGER={summary.summary_counts_match_ledger}",
        ],
        summary=summary.to_dict(),
    )


def assert_summary_internal_invariants_v1(
    summary: WallclockOutcomeTelemetrySummaryV1,
) -> list[str]:
    """Pure invariant checks used by unit tests and optional declared summaries."""
    blockers: list[str] = []
    if summary.hold_count < 0 or summary.no_action_count < 0:
        blockers.append("NEGATIVE_COUNT")
    if summary.terminal_outcome_sum != sum(summary.terminal_outcome_counts.values()):
        blockers.append(TERMINAL_SUM_MISMATCH_BLOCKER)
    fill_sum = summary.entry_fill_count + summary.reduce_fill_count + summary.exit_fill_count
    if fill_sum != summary.productive_fill_count:
        blockers.append(FILL_COUNT_MISMATCH_BLOCKER)
    return blockers
