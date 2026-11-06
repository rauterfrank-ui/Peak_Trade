"""Unit/integration/regression/negative tests for Phase 9.2 outcome telemetry binding."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DECISION_AUTHORITY,
    EXECUTION_EFFECT,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.ledger_summary_aggregator_v1 import (
    aggregate_wallclock_outcome_telemetry_from_cycles_v1,
    aggregate_wallclock_outcome_telemetry_from_evidence_root_v1,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.outcome_completeness_verifier_v1 import (
    verify_wallclock_outcome_completeness_v1,
)
from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.terminal_outcome_projection_v1 import (
    project_terminal_outcome_class_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REISSUE_EVIDENCE = (
    REPO_ROOT
    / "docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1"
    / "sessions/phase_9_2_public_md_one_hour_governed_session_reissue_9ba4e31c70c9"
    / "wallclock_run"
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _write_ledger(path: Path, cycles: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(cycle, sort_keys=True) + "\n" for cycle in cycles),
        encoding="utf-8",
    )


def _base_cycle(**overrides: object) -> dict:
    cycle = {
        "cycle_index": 1,
        "decision_outcome": "observe",
        "execution_eligible": False,
        "fill": None,
        "intended_action": {
            "intended_side": "HOLD",
            "intent_action": "NONE",
            "quantity_source": "safety_or_fail_closed",
            "reason_codes": [
                "TYPED_VOLATILITY_ESTIMATE_MISSING",
                "typed_volatility_estimate_missing",
                "observe_only",
            ],
            "safety_blocked": True,
        },
        "reason_codes": [
            "TYPED_VOLATILITY_ESTIMATE_MISSING",
            "typed_volatility_estimate_missing",
            "observe_only",
        ],
        "risk_sizing_result": "NONE",
        "safety_evaluation": {
            "safety_result": "EXIT_ONLY",
            "veto_reason": "WARMUP_OR_REGIME_INCOMPLETE",
            "hard_risk_reduction_signal": {"triggered": False},
        },
        "safety_result": "EXIT_ONLY",
        "double_play_typed_volatility_presence_gate": {
            "alpha_scope_entry_authority_allowed": False,
            "eligibility_new_directional_exposure_allowed": False,
        },
        "market_data_reference": {"mark_px": "1"},
    }
    cycle.update(overrides)
    return cycle


def test_capability_effects_are_non_authoritative() -> None:
    assert CAPABILITY_ID.endswith("COMPLETENESS_BINDING_V1")
    assert CORE_LOGIC_CHANGE is False
    assert DECISION_AUTHORITY is False
    assert EXECUTION_EFFECT is False


def test_projection_warmup_and_missing_volatility() -> None:
    warmup = _base_cycle(
        decision_outcome="blocked",
        intended_action={
            "intended_side": "HOLD",
            "intent_action": "NONE",
            "reason_codes": ["warmup_required"],
            "quantity_source": "insufficient_history",
            "safety_blocked": True,
        },
        reason_codes=["warmup_required"],
    )
    missing = _base_cycle()
    assert project_terminal_outcome_class_v1(warmup) == "SESSION_WARMUP"
    assert project_terminal_outcome_class_v1(missing) == "MISSING_VOLATILITY_OBSERVE_ONLY"


@pytest.mark.skipif(not REISSUE_EVIDENCE.is_dir(), reason="reissue evidence absent")
def test_regression_reissue_session_outcome_accounting() -> None:
    summary = aggregate_wallclock_outcome_telemetry_from_evidence_root_v1(REISSUE_EVIDENCE)
    assert summary.session_cycle_count == 1507
    assert summary.terminal_outcome_counts == {
        "MISSING_VOLATILITY_OBSERVE_ONLY": 1505,
        "SESSION_WARMUP": 2,
    }
    assert summary.terminal_outcome_sum == 1507
    assert summary.terminal_outcome_sum_matches_cycles is True
    assert summary.unaccounted_cycle_count == 0
    assert summary.multi_classified_cycle_count == 0
    assert summary.hold_count == 1507
    assert summary.no_action_count == 1507
    assert summary.entry_fill_count == 0
    assert summary.reduce_fill_count == 0
    assert summary.exit_fill_count == 0
    assert summary.summary_counts_match_ledger is True

    outcome = verify_wallclock_outcome_completeness_v1(evidence_root=REISSUE_EVIDENCE)
    assert outcome.verified is True
    assert outcome.result.endswith("VERIFIED")

    bundle = verify_wallclock_evidence_bundle_v1(evidence_root=REISSUE_EVIDENCE)
    assert bundle.verified is True
    assert any("OUTCOME_COMPLETENESS_VERIFIED=true" in n for n in bundle.notes)


def test_unknown_reason_code_is_counted(tmp_path: Path) -> None:
    cycle = _base_cycle(
        intended_action={
            "intended_side": "HOLD",
            "intent_action": "NONE",
            "reason_codes": [
                "TYPED_VOLATILITY_ESTIMATE_MISSING",
                "CUSTOM_UNKNOWN_REASON_XYZ",
            ],
            "safety_blocked": True,
        },
        reason_codes=[
            "TYPED_VOLATILITY_ESTIMATE_MISSING",
            "CUSTOM_UNKNOWN_REASON_XYZ",
        ],
    )
    summary = aggregate_wallclock_outcome_telemetry_from_cycles_v1([cycle])
    assert summary.reason_code_counts["CUSTOM_UNKNOWN_REASON_XYZ"] == 1
    assert summary.terminal_outcome_counts["MISSING_VOLATILITY_OBSERVE_ONLY"] == 1


def test_negative_unclassified_cycle_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    _write_ledger(
        root / "bridge_cycle_ledger.jsonl",
        [
            {
                "cycle_index": 1,
                "decision_outcome": "weird",
                "intended_action": {
                    "intended_side": "BUY",
                    "intent_action": "UNKNOWN_ACTION",
                    "reason_codes": [],
                },
                "fill": None,
                "reason_codes": [],
            }
        ],
    )
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 1})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(evidence_root=root)
    assert result.verified is False
    assert any("UNACCOUNTED" in b for b in result.blockers)


def test_negative_multi_classified_cycle_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    cycle = _base_cycle(
        terminal_outcome_classes=["SESSION_WARMUP", "MISSING_VOLATILITY_OBSERVE_ONLY"]
    )
    _write_ledger(root / "bridge_cycle_ledger.jsonl", [cycle])
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 1})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(evidence_root=root)
    assert result.verified is False
    assert any("MULTI_CLASSIFIED" in b for b in result.blockers)


def test_negative_terminal_sum_too_small_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    cycles = [_base_cycle(cycle_index=1), _base_cycle(cycle_index=2)]
    cycles[1]["terminal_outcome_classes"] = []
    _write_ledger(root / "bridge_cycle_ledger.jsonl", cycles)
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 2})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(evidence_root=root)
    assert result.verified is False
    assert any("TERMINAL_OUTCOME_SUM_MISMATCH" in b for b in result.blockers)


def test_negative_terminal_sum_too_large_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    cycle = _base_cycle(
        terminal_outcome_classes=["SESSION_WARMUP", "MISSING_VOLATILITY_OBSERVE_ONLY"]
    )
    _write_ledger(root / "bridge_cycle_ledger.jsonl", [cycle])
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 1})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    summary = aggregate_wallclock_outcome_telemetry_from_evidence_root_v1(root)
    # Multi-classified contributes 0 to terminal sum → sum < cycles; craft declared overcount.
    result = verify_wallclock_outcome_completeness_v1(
        evidence_root=root,
        declared_summary={
            "TERMINAL_OUTCOME_SUM": 99,
            "SESSION_CYCLE_COUNT": summary.session_cycle_count,
        },
    )
    assert result.verified is False
    assert any("SUMMARY_COUNTS_MISMATCH" in b or "TERMINAL" in b for b in result.blockers)


def test_negative_manipulated_hold_count_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    _write_ledger(root / "bridge_cycle_ledger.jsonl", [_base_cycle()])
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 1})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(
        evidence_root=root,
        declared_summary={"HOLD_COUNT": 0},
    )
    assert result.verified is False
    assert any("HOLD_COUNT" in b or "SUMMARY_COUNTS_MISMATCH" in b for b in result.blockers)


def test_negative_manipulated_no_action_count_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    _write_ledger(root / "bridge_cycle_ledger.jsonl", [_base_cycle()])
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 1})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(
        evidence_root=root,
        declared_summary={"NO_ACTION_COUNT": 0},
    )
    assert result.verified is False
    assert any("NO_ACTION" in b or "SUMMARY_COUNTS_MISMATCH" in b for b in result.blockers)


def test_negative_manipulated_fill_count_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    _write_ledger(root / "bridge_cycle_ledger.jsonl", [_base_cycle()])
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 1})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(
        evidence_root=root,
        declared_summary={"ENTRY_FILL_COUNT": 1},
    )
    assert result.verified is False
    assert any("FILL" in b or "SUMMARY_COUNTS_MISMATCH" in b for b in result.blockers)


def test_negative_empty_ledger_with_positive_cycle_count_fails(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    root.mkdir(parents=True)
    (root / "bridge_cycle_ledger.jsonl").write_text("", encoding="utf-8")
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 3})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(evidence_root=root)
    assert result.verified is False
    assert any("EMPTY_LEDGER_WITH_POSITIVE_CYCLE_COUNT" in b for b in result.blockers)


def test_negative_zero_cycle_pass_not_implicitly_complete(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    root.mkdir(parents=True)
    (root / "bridge_cycle_ledger.jsonl").write_text("", encoding="utf-8")
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 0})
    _write_json(root / "terminal_verdict.json", {"verdict": "PASS", "incomplete": False})
    result = verify_wallclock_outcome_completeness_v1(evidence_root=root)
    assert result.verified is False
    assert any("ZERO_CYCLE_SESSION_NOT_IMPLICITLY_COMPLETE" in b for b in result.blockers)


def test_zero_cycle_abort_is_explicitly_admissible(tmp_path: Path) -> None:
    root = tmp_path / "ev"
    root.mkdir(parents=True)
    (root / "bridge_cycle_ledger.jsonl").write_text("", encoding="utf-8")
    _write_json(root / "observation_cycle_counters.json", {"cycle_count": 0})
    _write_json(root / "terminal_verdict.json", {"verdict": "ABORT", "incomplete": True})
    result = verify_wallclock_outcome_completeness_v1(evidence_root=root)
    assert result.verified is True


@pytest.mark.skipif(not REISSUE_EVIDENCE.is_dir(), reason="reissue evidence absent")
def test_existing_evidence_files_remain_byte_identical_during_temp_copy(tmp_path: Path) -> None:
    before = {
        path.relative_to(REISSUE_EVIDENCE): path.read_bytes()
        for path in REISSUE_EVIDENCE.rglob("*")
        if path.is_file()
    }
    copy = tmp_path / "copy"
    shutil.copytree(REISSUE_EVIDENCE, copy)
    verify_wallclock_outcome_completeness_v1(evidence_root=copy)
    after = {
        path.relative_to(REISSUE_EVIDENCE): path.read_bytes()
        for path in REISSUE_EVIDENCE.rglob("*")
        if path.is_file()
    }
    assert before == after
