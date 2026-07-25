"""Focused tests: Step 29U economic failure closeout and recovery decision v0."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.step_29u_audit_provenance_v0 import STATUS_COMPLETE as AUDIT_COMPLETE
from src.ops.step_29u_economic_failure_closeout_recovery_decision_v0 import (
    CAPABILITY_ID,
    CLOSEOUT_COMPLETE,
    FORBIDDEN_IMPORT_SURFACES,
    OPTION_BLOCKED,
    OPTION_ELIGIBLE,
    PACKAGE_MARKER,
    SCHEMA_ID,
    EconomicFailureCloseoutOverridesV0,
    Step29UEconomicFailureCloseoutError,
    assert_no_forbidden_imports_v0,
    eligible_recovery_option_ids_v0,
    evaluate_step_29u_economic_failure_closeout_recovery_decision_v0,
    result_to_machine_lines,
    serialize_result_json_v0,
)
from src.ops.step_29u_economic_validity_readiness_v0 import (
    STATUS_FAIL as ECON_FAIL,
    STATUS_PASS as ECON_PASS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src/ops/step_29u_economic_failure_closeout_recovery_decision_v0.py"
CLI = REPO_ROOT / "scripts/ops/run_step_29u_economic_failure_closeout_recovery_decision_v0.py"
FLEET = (
    REPO_ROOT / "config/research/post_pr4940_final_research_fleet_negative_evidence_"
    "terminalization_and_next_material_research_boundary_v0.json"
)
SEALED = (
    REPO_ROOT / "evidence/ops/step_29u_activation_evidence_economic_readiness/"
    "20260726T011500Z_local_pre_pr/economic_validity_result.json"
)


def test_exact_canonical_evidence_resolution() -> None:
    result = evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(repo_root=REPO_ROOT)
    assert result.status == "PASS"
    assert result.economic_closeout_status == CLOSEOUT_COMPLETE
    assert result.economic_validity_status == ECON_FAIL
    assert result.economic_validity_proven is False
    assert result.audit_provenance_status == AUDIT_COMPLETE
    paths = [e["relpath"] for e in result.canonical_economic_evidence]
    assert any("post_pr4940_final_research_fleet" in p for p in paths)
    assert any("economic_validity_result.json" in p for p in paths)
    fleet_ev = next(
        e
        for e in result.canonical_economic_evidence
        if e["relpath"].endswith(".json") and "post_pr4940" in e["relpath"]
    )
    assert fleet_ev["sha256"]
    assert len(fleet_ev["sha256"]) == 64


def test_missing_evidence_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing_fleet.json"
    with pytest.raises(Step29UEconomicFailureCloseoutError) as exc:
        evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=REPO_ROOT,
            overrides=EconomicFailureCloseoutOverridesV0(fleet_closeout_path=missing),
        )
    assert "CANONICAL_ECONOMIC_EVIDENCE_MISSING" in str(exc.value)


def test_contradictory_economic_pass_fail_fails_closed(tmp_path: Path) -> None:
    sealed_pass = tmp_path / "sealed_pass.json"
    payload = json.loads(SEALED.read_text(encoding="utf-8"))
    payload["status"] = ECON_PASS
    payload["economic_validity_proven"] = True
    sealed_pass.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Step29UEconomicFailureCloseoutError) as exc:
        evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=REPO_ROOT,
            overrides=EconomicFailureCloseoutOverridesV0(
                sealed_economic_result_path=sealed_pass,
            ),
        )
    assert "CONTRADICTORY_ECONOMIC_PASS_FAIL" in str(exc.value)


def test_contradictory_live_gate_pass_vs_fleet_fail() -> None:
    with pytest.raises(Step29UEconomicFailureCloseoutError) as exc:
        evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=REPO_ROOT,
            overrides=EconomicFailureCloseoutOverridesV0(
                overlay_gate_pass=True,
                overlay_fleet_verdict="FLEET_ECONOMIC_VALIDITY_FAIL",
            ),
        )
    assert "CONTRADICTORY_ECONOMIC_PASS_FAIL" in str(exc.value)


def test_audit_complete_cannot_produce_economic_ready(tmp_path: Path) -> None:
    sealed_pass = tmp_path / "sealed_pass.json"
    payload = json.loads(SEALED.read_text(encoding="utf-8"))
    payload["status"] = ECON_PASS
    payload["economic_validity_proven"] = True
    sealed_pass.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Step29UEconomicFailureCloseoutError) as exc:
        evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=REPO_ROOT,
            overrides=EconomicFailureCloseoutOverridesV0(
                sealed_economic_result_path=sealed_pass,
                force_economic_status=ECON_PASS,
            ),
        )
    assert "AUDIT_COMPLETE_CANNOT_PRODUCE_ECONOMIC_READY" in str(exc.value)


def test_claim_economic_ready_from_audit_complete_forbidden() -> None:
    with pytest.raises(Step29UEconomicFailureCloseoutError) as exc:
        evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=REPO_ROOT,
            overrides=EconomicFailureCloseoutOverridesV0(
                claim_economic_ready_from_audit_complete=True,
            ),
        )
    assert "AUDIT_COMPLETE_DOES_NOT_IMPLY_ECONOMIC_READY" in str(exc.value)


def test_no_activation_eligibility_while_economic_validity_false() -> None:
    result = evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(repo_root=REPO_ROOT)
    assert result.economic_validity_proven is False
    assert result.activation_eligible is False
    assert result.step_29u_activated is False


def test_no_automatic_recovery_option_selection() -> None:
    result = evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(repo_root=REPO_ROOT)
    assert result.automatic_next_research_action_allowed is False
    assert result.operator_selection_required is True
    assert result.selected_recovery_option_id is None
    eligible = eligible_recovery_option_ids_v0(result)
    assert "RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES" in eligible
    assert "RETURN_TO_RATIFIED_MATERIAL_DIFFERENT_RESEARCH_BACKLOG" in eligible
    assert "IMPROVE_SAMPLE_SUFFICIENCY" not in eligible
    with pytest.raises(Step29UEconomicFailureCloseoutError) as exc:
        evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=REPO_ROOT,
            overrides=EconomicFailureCloseoutOverridesV0(claim_auto_select_recovery=True),
        )
    assert "AUTOMATIC_RECOVERY_SELECTION_FORBIDDEN" in str(exc.value)


def test_stable_deterministic_serialization() -> None:
    a = evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(repo_root=REPO_ROOT)
    b = evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(repo_root=REPO_ROOT)
    da = a.to_dict()
    db = b.to_dict()
    da["generated_at"] = "FIXED"
    db["generated_at"] = "FIXED"
    sa = json.dumps(da, indent=2, sort_keys=True) + "\n"
    sb = json.dumps(db, indent=2, sort_keys=True) + "\n"
    assert sa == sb
    assert '"capability_id"' in serialize_result_json_v0(a)
    lines_a = result_to_machine_lines(a)
    lines_b = result_to_machine_lines(b)
    assert lines_a == lines_b


def test_cli_exit_and_result_semantics(tmp_path: Path) -> None:
    out = tmp_path / "closeout.json"
    proc = subprocess.run(
        [sys.executable, str(CLI), "--output-path", str(out)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "ECONOMIC_CLOSEOUT=COMPLETE" in proc.stdout
    assert "ECONOMIC_VALIDITY_STATUS=FAIL" in proc.stdout
    assert "ACTIVATION_ELIGIBLE=false" in proc.stdout
    assert "AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED=false" in proc.stdout
    assert "OPERATOR_SELECTION_REQUIRED=true" in proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["economic_closeout_status"] == CLOSEOUT_COMPLETE
    assert payload["selected_recovery_option_id"] is None
    assert payload["schema_id"] == SCHEMA_ID
    assert payload["capability_id"] == CAPABILITY_ID


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
    assert "AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED" in text
    assert FLEET.is_file()
    assert SEALED.is_file()


def test_failure_and_recovery_inventories_complete() -> None:
    result = evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(repo_root=REPO_ROOT)
    assert len(result.failure_cause_inventory) >= 3
    assert len(result.recovery_option_inventory) == 5
    statuses = {o.status for o in result.recovery_option_inventory}
    assert OPTION_ELIGIBLE in statuses
    assert OPTION_BLOCKED in statuses
    lines = result_to_machine_lines(result)
    assert any(line.startswith("RECOVERY_OPTIONS=") for line in lines)
