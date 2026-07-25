"""Focused tests: Step 29U activation eligibility inventory v0."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.step_29u_activation_eligibility_inventory_v0 import (
    CAPABILITY_ID,
    EXPECTED_SOAK_TESTED_HEAD_SHA,
    FORBIDDEN_IMPORT_SURFACES,
    PACKAGE_MARKER,
    PREREQUISITE_IDS,
    SCHEMA_ID,
    STATE_ABSENT,
    STATE_INVALID,
    STATE_SATISFIED,
    STATE_UNSATISFIED,
    EligibilityInventoryOverridesV0,
    Step29UActivationEligibilityInventoryError,
    evaluate_step_29u_activation_eligibility_inventory_v0,
    serialize_result_json_v0,
)
from src.ops.step_29u_audit_provenance_v0 import STATUS_COMPLETE as AUDIT_COMPLETE
from src.ops.step_29u_economic_validity_readiness_v0 import (
    STATUS_FAIL as ECON_FAIL,
    EconomicValidityReadinessOverridesV0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SOAK = REPO_ROOT / "evidence/ops/step_29u_post_merge_shadow_soak/20260725T222915Z"
CLI = REPO_ROOT / "scripts/ops/run_step_29u_activation_eligibility_inventory_v0.py"
SRC = REPO_ROOT / "src/ops/step_29u_activation_eligibility_inventory_v0.py"


def _by_id(result):
    return {p.prerequisite_id: p for p in result.prerequisites}


def _copy_soak(tmp_path: Path) -> Path:
    dest = tmp_path / "soak"
    shutil.copytree(CANONICAL_SOAK, dest)
    return dest


def _rewrite_summary(soak_dir: Path, **updates):
    path = soak_dir / "soak_summary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Refresh manifest digest for soak_summary.json only when requested by caller.


def _refresh_manifest_entry(soak_dir: Path, rel: str) -> None:
    import hashlib

    manifest = soak_dir / "evidence_manifest.sha256"
    lines = []
    digest = hashlib.sha256((soak_dir / rel).read_bytes()).hexdigest()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d, name = line.split(None, 1)
        if name.strip() == rel:
            lines.append(f"{digest}  {rel}")
        else:
            lines.append(line)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_normal_current_state_ineligible() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert result.evaluator_valid is True
    assert result.status == "PASS"
    assert result.activation_eligible is False
    assert result.step_29u_activated is False
    assert result.schema_id == SCHEMA_ID
    assert result.capability_id == CAPABILITY_ID
    assert PACKAGE_MARKER.startswith("STEP_29U_ACTIVATION_ELIGIBILITY")
    assert result.summary["prerequisite_count"] == len(PREREQUISITE_IDS)
    assert "ECONOMIC_VALIDITY_PROVEN:UNSATISFIED" in result.blockers
    assert "EXPLICIT_FUTURE_OPERATOR_GO_PRESENT:ABSENT" in result.blockers
    assert result.audit_provenance_status == AUDIT_COMPLETE
    assert result.audit_provenance_complete is True
    assert result.economic_validity_status == ECON_FAIL
    assert result.economic_validity_proven is False
    assert result.future_operator_go_present is False
    assert result.non_operator_prerequisites_complete is False
    by = _by_id(result)
    assert by["STEP_29U_BINDING_PROVEN"].state == STATE_SATISFIED
    assert by["STEP_29U_POST_MERGE_SOAK_PROVEN"].state == STATE_SATISFIED
    assert by["STEP_29U_AUDIT_PROVENANCE_COMPLETE"].state == STATE_SATISFIED
    assert by["ECONOMIC_VALIDITY_PROVEN"].state == STATE_UNSATISFIED
    assert by["ECONOMIC_VALIDITY_PROVEN"].reason_code == "ECONOMIC_VALIDITY_FAIL"
    assert by["EXPLICIT_FUTURE_OPERATOR_GO_PRESENT"].state == STATE_ABSENT
    # Counts must match classifications.
    assert result.summary["satisfied_count"] == sum(
        1 for p in result.prerequisites if p.state == STATE_SATISFIED
    )
    assert result.summary["unsatisfied_count"] == sum(
        1 for p in result.prerequisites if p.state == STATE_UNSATISFIED
    )
    assert result.summary["absent_count"] == sum(
        1 for p in result.prerequisites if p.state == STATE_ABSENT
    )
    assert result.summary["invalid_count"] == sum(
        1 for p in result.prerequisites if p.state == STATE_INVALID
    )


def test_audit_false_blocks_eligibility(tmp_path: Path) -> None:
    empty = tmp_path / "no_soak"
    empty.mkdir()
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(soak_dir=empty),
    )
    assert result.activation_eligible is False
    assert result.audit_provenance_complete is False
    assert any("AUDIT" in b for b in result.blockers)


def test_economic_false_blocks_eligibility() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert result.economic_validity_proven is False
    assert result.activation_eligible is False
    assert any("ECONOMIC_VALIDITY" in b for b in result.blockers)


def test_operator_go_absent_always_blocks_eligibility() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert result.future_operator_go_present is False
    assert result.activation_eligible is False
    assert "EXPLICIT_FUTURE_OPERATOR_GO_PRESENT:ABSENT" in result.blockers


def test_non_operator_complete_plus_go_absent_remains_ineligible() -> None:
    # Even if economic were forced PASS, GO absence keeps activation ineligible.
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(
            economic_overrides=EconomicValidityReadinessOverridesV0(force_status="PASS"),
        ),
    )
    assert result.economic_validity_proven is True
    assert result.future_operator_go_present is False
    assert result.activation_eligible is False
    assert "EXPLICIT_FUTURE_OPERATOR_GO_PRESENT:ABSENT" in result.blockers


def test_no_blocker_silently_disappears() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    # Economic FAIL and Operator-GO ABSENT must remain visible.
    assert any(b.startswith("ECONOMIC_VALIDITY_PROVEN:") for b in result.blockers)
    assert "EXPLICIT_FUTURE_OPERATOR_GO_PRESENT:ABSENT" in result.blockers


def test_binding_alone_cannot_establish_eligibility(tmp_path: Path) -> None:
    empty_soak = tmp_path / "no_soak"
    empty_soak.mkdir()
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(soak_dir=empty_soak),
    )
    assert result.activation_eligible is False
    assert _by_id(result)["STEP_29U_BINDING_PROVEN"].state == STATE_SATISFIED
    assert _by_id(result)["STEP_29U_POST_MERGE_SOAK_PROVEN"].state in {
        STATE_ABSENT,
        STATE_UNSATISFIED,
        STATE_INVALID,
    }
    assert any("SOAK" in b or "STEP_29U_POST_MERGE_SOAK" in b for b in result.blockers)


def test_soak_alone_cannot_establish_eligibility(tmp_path: Path) -> None:
    # Binding evidence override to empty dir → binding not proven; soak still canonical.
    empty_bind = tmp_path / "no_bind"
    empty_bind.mkdir()
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(binding_evidence_dir=empty_bind),
    )
    assert result.activation_eligible is False
    assert _by_id(result)["STEP_29U_POST_MERGE_SOAK_PROVEN"].state == STATE_SATISFIED
    assert _by_id(result)["STEP_29U_BINDING_PROVEN"].state != STATE_SATISFIED
    assert any("BINDING" in b for b in result.blockers)


def test_5551_soak_recognized_with_manifest_digest_and_head() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    soak = _by_id(result)["STEP_29U_POST_MERGE_SOAK_PROVEN"]
    assert soak.state == STATE_SATISFIED
    assert soak.evidence_digest
    assert EXPECTED_SOAK_TESTED_HEAD_SHA in soak.observed_value
    exact = (CANONICAL_SOAK / "exact_head.txt").read_text(encoding="utf-8").strip()
    assert exact == EXPECTED_SOAK_TESTED_HEAD_SHA


def test_audit_provenance_complete_when_chain_valid() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert _by_id(result)["STEP_29U_AUDIT_PROVENANCE_COMPLETE"].state == STATE_SATISFIED
    assert result.audit_provenance_complete is True


def test_economic_validity_not_proven_blocks() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert _by_id(result)["ECONOMIC_VALIDITY_PROVEN"].state == STATE_UNSATISFIED
    assert any("ECONOMIC_VALIDITY" in b for b in result.blockers)
    assert result.economic_validity_status == ECON_FAIL


def test_future_operator_go_absent_blocks() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert result.operator_go_present is False
    assert _by_id(result)["EXPLICIT_FUTURE_OPERATOR_GO_PRESENT"].state == STATE_ABSENT
    assert "EXPLICIT_FUTURE_OPERATOR_GO_PRESENT:ABSENT" in result.blockers


@pytest.mark.parametrize(
    ("flag", "prereq"),
    [
        ("RUNTIME_ACTIVATED", "RUNTIME_REMAINS_NOT_ACTIVATED"),
        ("SCHEDULER_ACTIVATED", "SCHEDULER_REMAINS_LOCKED"),
        ("NETWORK_USED", "NETWORK_REMAINS_PROHIBITED"),
        ("ORDERS_CREATED", "ORDERS_REMAIN_PROHIBITED"),
        ("ORDERS_SUBMITTED", "ORDERS_REMAIN_PROHIBITED"),
    ],
)
def test_unsafe_soak_flags_invalid(tmp_path: Path, flag: str, prereq: str) -> None:
    soak = _copy_soak(tmp_path)
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(
            soak_dir=soak,
            soak_summary_overlay={flag: True},
        ),
    )
    assert result.activation_eligible is False
    assert result.step_29u_activated is False
    assert _by_id(result)[prereq].state == STATE_INVALID
    # Soak proven also invalid when safety flags true.
    assert _by_id(result)["STEP_29U_POST_MERGE_SOAK_PROVEN"].state == STATE_INVALID


@pytest.mark.parametrize(
    ("flag", "prereq"),
    [
        ("BTC_OBSERVED", "BTC_EXCLUDED"),
        ("SPOT_OBSERVED", "SPOT_EXCLUDED"),
        ("KRAKEN_LEGACY_OBSERVED", "KRAKEN_LEGACY_EXCLUDED"),
    ],
)
def test_inclusion_flags_block(tmp_path: Path, flag: str, prereq: str) -> None:
    soak = _copy_soak(tmp_path)
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(
            soak_dir=soak,
            soak_summary_overlay={flag: True},
        ),
    )
    assert result.activation_eligible is False
    assert _by_id(result)[prereq].state == STATE_INVALID


def test_missing_canonical_source_absent(tmp_path: Path) -> None:
    missing_cfg = tmp_path / "missing.toml"
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(readiness_config_path=missing_cfg),
    )
    assert _by_id(result)["RUNTIME_BRIDGE_BOUND"].state == STATE_ABSENT
    assert _by_id(result)["ECONOMIC_VALIDITY_PROVEN"].state == STATE_ABSENT


def test_malformed_canonical_source_invalid(tmp_path: Path) -> None:
    soak = _copy_soak(tmp_path)
    (soak / "soak_summary.json").write_text("{not-json", encoding="utf-8")
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(soak_dir=soak),
    )
    assert _by_id(result)["STEP_29U_POST_MERGE_SOAK_PROVEN"].state == STATE_INVALID


def test_digest_mismatch_invalid(tmp_path: Path) -> None:
    soak = _copy_soak(tmp_path)
    _rewrite_summary(soak, VERDICT="TAMPERED_FOR_DIGEST_MISMATCH")
    # Intentionally do not refresh manifest → digest mismatch.
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(soak_dir=soak),
    )
    assert _by_id(result)["STEP_29U_POST_MERGE_SOAK_PROVEN"].state == STATE_INVALID
    assert "DIGEST" in _by_id(result)["STEP_29U_POST_MERGE_SOAK_PROVEN"].reason_code


def test_unknown_prerequisite_fails_closed() -> None:
    with pytest.raises(Step29UActivationEligibilityInventoryError) as exc:
        evaluate_step_29u_activation_eligibility_inventory_v0(
            repo_root=REPO_ROOT,
            overrides=EligibilityInventoryOverridesV0(force_unknown_prerequisite=True),
        )
    assert "UNKNOWN_PREREQUISITE" in str(exc.value)


def test_output_ordering_and_serialization_deterministic() -> None:
    a = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(evaluated_main_sha="deadbeef"),
    )
    b = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(evaluated_main_sha="deadbeef"),
    )
    assert [p.prerequisite_id for p in a.prerequisites] == list(PREREQUISITE_IDS)
    assert [p.prerequisite_id for p in b.prerequisites] == list(PREREQUISITE_IDS)
    # Stabilize generated_at by comparing structural fields
    da, db = a.to_dict(), b.to_dict()
    da["generated_at"] = db["generated_at"] = "FIXED"
    assert json.dumps(da, sort_keys=True) == json.dumps(db, sort_keys=True)
    assert serialize_result_json_v0(a).count("\n") > 10


def test_activation_eligible_false_while_blockers_exist() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert result.blockers
    assert result.activation_eligible is False


def test_step_29u_activated_always_false(tmp_path: Path) -> None:
    soak = _copy_soak(tmp_path)
    result = evaluate_step_29u_activation_eligibility_inventory_v0(
        repo_root=REPO_ROOT,
        overrides=EligibilityInventoryOverridesV0(
            soak_dir=soak,
            soak_summary_overlay={"RUNTIME_ACTIVATED": True},
        ),
    )
    assert result.step_29u_activated is False
    assert result.runtime_activated is False


def test_no_network_runtime_scheduler_order_imports_or_calls() -> None:
    src = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
    for forbidden in FORBIDDEN_IMPORT_SURFACES:
        assert forbidden not in imported
    # Forbidden surfaces may appear only as deny-list string constants.
    assert "from src.orders" not in src
    assert "import socket" not in src
    assert "import requests" not in src
    assert "create_order(" not in src
    assert "socket" not in imported
    assert "requests" not in imported


def test_cli_pass_with_eligibility_false(tmp_path: Path) -> None:
    out = tmp_path / "inventory.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--repo-root",
            str(REPO_ROOT),
            "--output-path",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    assert "STATUS=PASS" in proc.stdout
    assert "EVALUATOR_VALID=true" in proc.stdout
    assert "ACTIVATION_ELIGIBLE=false" in proc.stdout
    assert "STEP_29U_ACTIVATED=false" in proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["activation_eligible"] is False
    assert payload["evaluator_valid"] is True


def test_canonical_exclusions_satisfied() -> None:
    result = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=REPO_ROOT)
    assert result.btc_excluded is True
    assert result.spot_excluded is True
    assert result.kraken_legacy_excluded is True
    by = _by_id(result)
    assert by["BTC_EXCLUDED"].state == STATE_SATISFIED
    assert by["SPOT_EXCLUDED"].state == STATE_SATISFIED
    assert by["KRAKEN_LEGACY_EXCLUDED"].state == STATE_SATISFIED
