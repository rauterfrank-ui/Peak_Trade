"""Contract: full canonical system backtest parity gap assessment v0 (offline only)."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import json

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER,
    NEXT_RECOMMENDED_SLICE,
    normalize_matrix_status_v0,
    parity_gap_records_v0,
    parity_status_counts_v0,
    parity_surface_assessments_v0,
    render_parity_gap_matrix_json_v0,
    render_parity_gap_matrix_markdown_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
POST_MERGE_GUARD = REPO_ROOT / "scripts/ops/squash_merge_post_merge_closeout_guard_v0.sh"

_SLICE_SOURCE_PATHS = tuple(
    REPO_ROOT / p for p in ALLOWED_SLICE_CHANGED_PATH_PREFIXES if p.endswith(".py")
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def test_gap_assessment_owner_and_surface_count_v0() -> None:
    assessments = parity_surface_assessments_v0()
    assert len(assessments) == 16
    ids = [item.surface_id for item in assessments]
    assert ids == [chr(ord("A") + i) for i in range(16)]
    assert all(item.forbidden_runtime_authority_confirmed for item in assessments)
    assert FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER.endswith(
        "full_canonical_system_backtest_parity_gap_assessment_v0"
    )


def test_gap_assessment_status_distribution_v0() -> None:
    counts = parity_status_counts_v0()
    assert counts["PASS"] == 15
    assert counts["PARTIAL"] >= 1
    assert counts["GAP"] == 0
    assert counts["NOT_APPLICABLE"] == 0
    assert sum(counts.values()) == 16


def test_bull_bear_state_switch_surface_pass_v0() -> None:
    state_switch = next(item for item in parity_surface_assessments_v0() if item.surface_id == "A")
    assert state_switch.parity_status == "PASS"
    assert state_switch.missing_binding_if_any == ""
    assert "evaluate_scenario_state_switch_v0" in state_switch.current_scenario_replay_binding


def test_scope_adverse_exit_surface_pass_v0() -> None:
    scope_adverse = next(item for item in parity_surface_assessments_v0() if item.surface_id == "B")
    assert scope_adverse.parity_status == "PASS"
    assert scope_adverse.missing_binding_if_any == ""
    assert "evaluate_scenario_scope_event_v0" in scope_adverse.current_scenario_replay_binding
    assert "generate_deterministic_scope_event" in scope_adverse.current_scenario_replay_binding


def test_reversal_preparation_surface_pass_v0() -> None:
    reversal = next(item for item in parity_surface_assessments_v0() if item.surface_id == "C")
    assert reversal.parity_status == "PASS"
    assert reversal.missing_binding_if_any == ""
    assert "evaluate_scenario_reversal_preparation_entry_exit_v0" in (
        reversal.current_scenario_replay_binding
    )


def test_flat_before_opposite_side_surface_pass_v0() -> None:
    flat_invariant = next(
        item for item in parity_surface_assessments_v0() if item.surface_id == "D"
    )
    assert flat_invariant.parity_status == "PASS"
    assert flat_invariant.missing_binding_if_any == ""
    assert "evaluate_scenario_flat_before_opposite_side_entry_exit_v0" in (
        flat_invariant.current_scenario_replay_binding
    )


def test_survival_suitability_surface_pass_v0() -> None:
    survival_suit = next(item for item in parity_surface_assessments_v0() if item.surface_id == "E")
    assert survival_suit.parity_status == "PASS"
    assert survival_suit.missing_binding_if_any == ""
    assert "evaluate_scenario_survival_suitability_v0" in (
        survival_suit.current_scenario_replay_binding
    )


def test_composition_surface_pass_v0() -> None:
    composition = next(item for item in parity_surface_assessments_v0() if item.surface_id == "F")
    assert composition.parity_status == "PASS"
    assert composition.missing_binding_if_any == ""


def test_capital_risk_sizing_surface_pass_v0() -> None:
    sizing = next(item for item in parity_surface_assessments_v0() if item.surface_id == "H")
    assert sizing.parity_status == "PASS"
    assert sizing.missing_binding_if_any == ""
    assert "bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0" in (
        sizing.current_backtest_binding
    )


def test_canonical_order_intent_surface_pass_v0() -> None:
    order_intent = next(item for item in parity_surface_assessments_v0() if item.surface_id == "I")
    assert order_intent.parity_status == "PASS"
    assert order_intent.missing_binding_if_any == ""
    assert "bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0" in (
        order_intent.current_backtest_binding
    )
    assert order_intent.recommended_next_slice == NEXT_RECOMMENDED_SLICE


def test_safety_kernel_surface_pass_v0() -> None:
    safety = next(item for item in parity_surface_assessments_v0() if item.surface_id == "J")
    assert safety.parity_status == "PASS"
    assert safety.missing_binding_if_any == ""
    assert "bind_safety_kernel_boundary_backtest_state_file_evidence_v0" in (
        safety.current_backtest_binding
    )
    assert safety.recommended_next_slice == NEXT_RECOMMENDED_SLICE


def test_entry_exit_surface_pass_after_pr4948_v0() -> None:
    entry_exit = next(item for item in parity_surface_assessments_v0() if item.surface_id == "G")
    assert entry_exit.parity_status == "PASS"
    assert entry_exit.missing_binding_if_any == ""


def test_reconciliation_unknown_outcome_surface_pass_v0() -> None:
    reconciliation = next(
        item for item in parity_surface_assessments_v0() if item.surface_id == "L"
    )
    assert reconciliation.parity_status == "PASS"
    assert (
        "bind_reconciliation_unknown_outcome_offline_replay_evidence_v0"
        in reconciliation.current_integrated_offline_replay_binding
    )
    assert (
        "evaluate_scenario_reconciliation_unknown_outcome_v0"
        in reconciliation.current_scenario_replay_binding
    )


def test_killswitch_boundary_surface_pass_v0() -> None:
    killswitch = next(item for item in parity_surface_assessments_v0() if item.surface_id == "K")
    assert killswitch.parity_status == "PASS"
    assert (
        "bind_killswitch_boundary_offline_replay_evidence_v0"
        in killswitch.current_integrated_offline_replay_binding
    )
    assert "evaluate_scenario_killswitch_boundary_v0" in killswitch.current_scenario_replay_binding


def test_gap_matrix_markdown_renders_v0() -> None:
    md = render_parity_gap_matrix_markdown_v0()
    assert "FULL_CANONICAL_CHAIN_WIRED=false" in md
    assert "Double Play composition" in md
    assert NEXT_RECOMMENDED_SLICE in md


def test_gap_matrix_json_machine_readable_v0() -> None:
    payload = json.loads(render_parity_gap_matrix_json_v0())
    assert payload["assessment_owner"] == FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER
    assert payload["next_recommended_slice"] == NEXT_RECOMMENDED_SLICE
    assert len(payload["surfaces"]) == 16
    assert payload["summary"]["full_canonical_chain_wired"] is False
    matrix_statuses = {item["matrix_status"] for item in payload["surfaces"]}
    assert matrix_statuses <= {
        "PASS",
        "GAP",
        "NOT_APPLICABLE_BOUNDARY_ONLY",
        "BLOCKED",
        "UNKNOWN",
    }
    for record in payload["gap_records"]:
        assert record["matrix_status"] == "GAP"
        assert record["missing_binding"]
        assert record["owner"]
        assert record["narrow_reuse_first_remediation"] == NEXT_RECOMMENDED_SLICE


def test_parity_gap_records_align_with_partial_surfaces_v0() -> None:
    partial_ids = {
        item.surface_id
        for item in parity_surface_assessments_v0()
        if item.parity_status == "PARTIAL"
    }
    gap_record_ids = {record["surface_id"] for record in parity_gap_records_v0()}
    assert partial_ids == gap_record_ids
    assert normalize_matrix_status_v0("NOT_APPLICABLE") == "NOT_APPLICABLE_BOUNDARY_ONLY"
    assert normalize_matrix_status_v0("PASS") == "PASS"


def test_pr4951_post_merge_guard_preflight_v0() -> None:
    assert POST_MERGE_GUARD.is_file()
    text = POST_MERGE_GUARD.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    assert "set -o pipefail" in text
    assert 'return "${PIPESTATUS[0]}"' in text
    assert "SQUASH_MERGE_POST_MERGE_CLOSEOUT_GUARD_V0=true" in text


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
    assert ok is True
    assert violations == ()


def test_slice_sources_exclude_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _SLICE_SOURCE_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_pr4946_parity_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0 as pr4946,
    )

    pr4946.test_harness_and_replay_owner_constants_v0()
    pr4946.test_1_long_bull_path_parity_v0()
    pr4946.test_3_both_confirmed_chop_guard_parity_v0()
    pr4946.test_5_reversal_preparation_boundary_parity_v0()
    pr4946.test_scenario_replay_e2e_composition_and_zero_order_boundary_v0()


def test_prometheus_client_importable_v0() -> None:
    assert importlib.util.find_spec("prometheus_client") is not None
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import prometheus_client; print('PROMETHEUS_CLIENT_IMPORTABLE=true')",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "PROMETHEUS_CLIENT_IMPORTABLE=true" in proc.stdout
