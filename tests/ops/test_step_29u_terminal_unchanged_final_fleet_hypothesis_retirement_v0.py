"""Focused tests: Step 29U terminal unchanged Final Fleet hypothesis retirement v0."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0 import (
    CAPABILITY_ID,
    FORBIDDEN_IMPORT_SURFACES,
    PACKAGE_MARKER,
    RETIREMENT_CONFIG_RELPATH,
    RETIREMENT_REASON,
    RETIREMENT_SCOPE,
    SCHEMA_ID,
    SELECTED_RECOVERY_OPTION,
    Step29UTerminalFleetHypothesisRetirementError,
    TerminalFleetHypothesisRetirementOverridesV0,
    assert_no_forbidden_imports_v0,
    assert_unchanged_resubmission_blocked_v0,
    evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0,
    is_hypothesis_retired_v0,
    result_to_machine_lines,
    serialize_result_json_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src/ops/step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.py"
CLI = (
    REPO_ROOT
    / "scripts/ops/run_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.py"
)
FLEET = (
    REPO_ROOT / "config/research/post_pr4940_final_research_fleet_negative_evidence_"
    "terminalization_and_next_material_research_boundary_v0.json"
)
RETIREMENT_CFG = REPO_ROOT / RETIREMENT_CONFIG_RELPATH
EXPECTED_IDS = (
    "trend_following/v1",
    "bollinger_bands/v1",
    "momentum_1h/v1",
)


def test_canonical_retirement_complete_for_final_fleet_only() -> None:
    result = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
        repo_root=REPO_ROOT
    )
    assert result.status == "COMPLETE"
    assert result.retirement_status == "COMPLETE"
    assert result.retirement_inventory_complete is True
    assert result.selected_recovery_option == SELECTED_RECOVERY_OPTION
    assert result.retirement_scope == RETIREMENT_SCOPE
    assert result.retirement_reason == RETIREMENT_REASON
    assert result.retired_hypothesis_count == 3
    assert tuple(result.retired_hypothesis_ids) == EXPECTED_IDS
    assert result.economic_validity_status == "FAIL"
    assert result.economic_validity_proven is False
    assert result.activation_eligible is False
    assert result.activated is False
    assert result.historical_evidence_preserved is True
    assert result.unchanged_rerun_allowed is False
    assert result.unchanged_repromotion_allowed is False
    assert result.automatic_backlog_selection_allowed is False
    assert result.next_research_candidate_selected is False
    assert result.operator_selection_required_for_next_material_research is True


def test_every_retired_hypothesis_exists_in_final_fleet_inventory() -> None:
    fleet = json.loads(FLEET.read_text(encoding="utf-8"))
    authorized = {
        str(x["canonical_candidate_identifier"])
        for x in fleet["terminal_failed_binding_exclusions"]
    }
    result = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
        repo_root=REPO_ROOT
    )
    assert set(result.retired_hypothesis_ids) == authorized
    assert set(result.retired_hypothesis_ids).issubset(authorized)
    for entry in result.retirement_inventory:
        assert entry.strategy_id in set(fleet["final_research_fleet"])
        assert entry.terminal_verdict == "FAIL"
        assert entry.canonical_negative_evidence_ref.endswith(
            "next_material_research_boundary_v0.json"
        )


def test_no_hypothesis_outside_authorized_final_fleet_retired() -> None:
    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                extra_hypothesis_ids=("materially_different_other/v9",),
            ),
        )
    assert "HYPOTHESIS_OUTSIDE_AUTHORIZED_FINAL_FLEET" in str(exc.value)


def test_duplicate_retirement_is_idempotent() -> None:
    a = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
        repo_root=REPO_ROOT
    )
    b = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
        repo_root=REPO_ROOT
    )
    da = a.to_dict()
    db = b.to_dict()
    da["generated_at"] = "FIXED"
    db["generated_at"] = "FIXED"
    assert json.dumps(da, sort_keys=True) == json.dumps(db, sort_keys=True)
    assert a.retired_hypothesis_ids == b.retired_hypothesis_ids == EXPECTED_IDS
    assert a.retired_hypothesis_count == 3


def test_retirement_cannot_convert_fail_to_pass_hold_or_unknown(
    tmp_path: Path,
) -> None:
    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                claim_economic_pass=True,
            ),
        )
    assert "RETIREMENT_CANNOT_CONVERT_FAIL_TO_PASS" in str(exc.value)

    cfg = json.loads(RETIREMENT_CFG.read_text(encoding="utf-8"))
    for bad in ("PASS", "HOLD", "UNKNOWN"):
        bad_cfg = dict(cfg)
        bad_cfg["economic_validity_status"] = bad
        path = tmp_path / f"bad_status_{bad}.json"
        path.write_text(json.dumps(bad_cfg), encoding="utf-8")
        with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc2:
            evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
                repo_root=REPO_ROOT,
                overrides=TerminalFleetHypothesisRetirementOverridesV0(
                    retirement_config_path=path,
                ),
            )
        assert "RETIREMENT_CANNOT_CONVERT_FAIL_STATUS" in str(exc2.value)


def test_retirement_cannot_grant_eligibility_or_activation() -> None:
    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                claim_activation_eligible=True,
            ),
        )
    assert "RETIREMENT_CANNOT_GRANT_ACTIVATION_ELIGIBILITY" in str(exc.value)

    result = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
        repo_root=REPO_ROOT
    )
    assert result.activation_eligible is False
    assert result.activated is False


def test_retired_unchanged_hypotheses_cannot_be_automatically_selected() -> None:
    result = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
        repo_root=REPO_ROOT
    )
    assert result.automatic_backlog_selection_allowed is False
    for hid in result.retired_hypothesis_ids:
        assert is_hypothesis_retired_v0(hid, result=result) is True
        with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc:
            assert_unchanged_resubmission_blocked_v0(hid, result=result)
        assert "UNCHANGED_RESUBMISSION_BLOCKED" in str(exc.value)

    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc2:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                claim_automatic_backlog_selection=True,
            ),
        )
    assert "AUTOMATIC_BACKLOG_SELECTION_FORBIDDEN" in str(exc2.value)


def test_materially_different_identities_are_not_falsely_retired() -> None:
    foreign = "cross_sectional_realized_volatility_rank_rotation/v0"
    result = evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
        repo_root=REPO_ROOT
    )
    assert foreign not in set(result.retired_hypothesis_ids)
    assert is_hypothesis_retired_v0(foreign, result=result) is False
    # Non-retired identity is not blocked by retirement guard.
    assert_unchanged_resubmission_blocked_v0(foreign, result=result)


def test_missing_contradictory_or_malformed_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing_fleet.json"
    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                fleet_closeout_path=missing,
            ),
        )
    assert "CANONICAL_ECONOMIC_EVIDENCE_MISSING" in str(exc.value)

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not-json", encoding="utf-8")
    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc2:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                fleet_closeout_path=malformed,
            ),
        )
    assert "JSON_MALFORMED" in str(exc2.value)

    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc3:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                selected_recovery_option="RETURN_TO_RATIFIED_MATERIAL_DIFFERENT_RESEARCH_BACKLOG",
            ),
        )
    assert "UNAUTHORIZED_RECOVERY_OPTION" in str(exc3.value)


def test_historical_evidence_mutation_forbidden() -> None:
    with pytest.raises(Step29UTerminalFleetHypothesisRetirementError) as exc:
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT,
            overrides=TerminalFleetHypothesisRetirementOverridesV0(
                mutate_historical_evidence=True,
            ),
        )
    assert "HISTORICAL_EVIDENCE_MUTATION_FORBIDDEN" in str(exc.value)
    # Canonical historical fleet closeout remains on disk and unchanged in shape.
    fleet = json.loads(FLEET.read_text(encoding="utf-8"))
    assert fleet["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
    assert fleet["economic_validity_offline_gate_pass"] is False


def test_cli_exit_and_result_semantics(tmp_path: Path) -> None:
    out = tmp_path / "retirement.json"
    proc = subprocess.run(
        [sys.executable, str(CLI), "--output-path", str(out)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "STATUS=COMPLETE" in proc.stdout
    assert "RETIREMENT_STATUS=COMPLETE" in proc.stdout
    assert "RETIRED_HYPOTHESIS_COUNT=3" in proc.stdout
    assert "ECONOMIC_VALIDITY_STATUS=FAIL" in proc.stdout
    assert "ACTIVATION_ELIGIBLE=false" in proc.stdout
    assert "NEXT_RESEARCH_CANDIDATE_SELECTED=false" in proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_id"] == SCHEMA_ID
    assert payload["capability_id"] == CAPABILITY_ID
    assert payload["retired_hypothesis_ids"] == list(EXPECTED_IDS)


def test_cli_missing_evidence_exit_one(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    proc = subprocess.run(
        [sys.executable, str(CLI), "--fleet-closeout", str(missing)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "EVALUATOR_VALID=false" in proc.stderr


def test_canonical_owner_static_boundary() -> None:
    text = SRC.read_text(encoding="utf-8")
    assert_no_forbidden_imports_v0(text)
    tree = ast.parse(text)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for forbidden in FORBIDDEN_IMPORT_SURFACES:
        assert not any(mod.startswith(forbidden) for mod in imported)
    assert PACKAGE_MARKER.endswith("=true")
    assert FLEET.is_file()
    assert RETIREMENT_CFG.is_file()
    lines = result_to_machine_lines(
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT
        )
    )
    assert any(line.startswith("RETIRED_HYPOTHESIS_IDS=") for line in lines)
    assert '"capability_id"' in serialize_result_json_v0(
        evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
            repo_root=REPO_ROOT
        )
    )
