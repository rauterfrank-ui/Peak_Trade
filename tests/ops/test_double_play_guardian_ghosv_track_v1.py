"""Independent tests for the Double Play GHOSV binding verifier."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.double_play_guardian_binding_verifier_v1.ghosv_track_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    verify_double_play_ghosv_v1,
)

PACKAGE = ROOT / "scripts/ops/double_play_guardian_binding_verifier_v1"
SHA = EXPECTED_BASELINE_SHA
TREE = EXPECTED_BASELINE_TREE


def _current() -> dict[str, str]:
    return {
        "ghosv_contract_text": (ROOT / "docs/ops/specs/MASTER_V2_GHOSV_CONTRACT_V1.md").read_text(),
        "decision_path_text": (
            ROOT / "docs/ops/specs/MV2_DECISION_PATH_BOUNDARY_V1.md"
        ).read_text(),
        "hardening_source": (
            ROOT / "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py"
        ).read_text(),
        "ghosv_constants_source": (
            ROOT / "scripts/ops/ghosv_master_v2_bounded_context_v1/constants_v1.py"
        ).read_text(),
        "persistence_constants_source": (
            ROOT / "src/ops/dynamic_scope_persistence_binding_v1/constants_v1.py"
        ).read_text(),
        "replay_source": (
            ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
        ).read_text(),
        "policy_source": (
            ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
        ).read_text(),
        "host_binding_source": (
            ROOT / "src/ops/dynamic_scope_persistence_binding_v1/host_binding_v1.py"
        ).read_text(),
    }


def _verify(claims: dict | None = None, **overrides: object):
    payload = _current()
    for key, value in overrides.items():
        payload[key] = value
    return verify_double_play_ghosv_v1(
        current_sha=SHA,
        current_tree=TREE,
        claims=claims,
        ghosv_contract_text=payload["ghosv_contract_text"],
        decision_path_text=payload["decision_path_text"],
        hardening_source=payload["hardening_source"],
        ghosv_constants_source=payload["ghosv_constants_source"],
        persistence_constants_source=payload["persistence_constants_source"],
        replay_source=payload["replay_source"],
        policy_source=payload["policy_source"],
        host_binding_source=payload["host_binding_source"],
    )


def _row(report: dict, requirement_id: str) -> dict:
    return next(row for row in report["FINDINGS"] if row["REQUIREMENT_ID"] == requirement_id)


def test_four_current_checks_stay_not_tested_and_not_ready() -> None:
    report = _verify()
    assert report["VERIFICATION_STATUS"] == "REPORTED"
    assert report["REJECTION_REASONS"] == []
    assert report["GHOSV_READY"] is False
    assert report["DOMAIN"] == "DOUBLE_PLAY"
    assert report["TOOL_IDENTITY"] == "DOUBLE_PLAY_GHOSV"
    assert report["EXISTING_CHECKER_EXECUTED"] is False
    assert report["OBSERVED_GHOSV_CODE_PIN"] == "7628005ae495c115ff341d32fa932b7f4642f456"
    assert report["GHOSV_PIN_IS_CURRENT_BASELINE"] is False
    assert report["TRADING_AUTHORITY"] == "NONE"
    assert [row["REQUIREMENT_ID"] for row in report["FINDINGS"]] == [
        "MV2-04",
        "MV2-05",
        "MV2-06",
        "MV2-08",
    ]
    assert all(row["EXISTING_CHECKER_STATUS"] == "NOT_TESTED" for row in report["FINDINGS"])
    assert all(row["DOMAIN"] == "DOUBLE_PLAY" for row in report["FINDINGS"])
    role = _row(report, "MV2-04")
    assert role["OBSERVATION_STATUS"] == "INTERNAL_ROLE_OBSERVED"
    assert role["STATE_IMPORTS_OBSERVED"] is True
    assert role["DECISION_AUTHORITY_GRANTED"] is False
    lock = _row(report, "MV2-05")
    assert lock["LOCK_TOKENS_OBSERVED"] is True
    assert lock["PYTHON_ENFORCEMENT"] == "ENFORCEMENT_ABSENT"
    assert lock["REPOSITORY_WIDE_ENFORCEMENT"] == "NOT_ASSESSED"
    assert lock["TOOL_RUN_IS_OWNER_GO"] is False
    effect = _row(report, "MV2-06")
    assert effect["ENTRY_EXIT_EFFECT"] == "NOT_PROVEN"
    assert effect["EFFECT_PASS"] is False
    assert effect["AUTHORITY_EFFECT_DEFAULT"] == "NONE"
    assert effect["CALL_PRESENCE_IS_NOT_REACHABILITY"] is True
    writer = _row(report, "MV2-08")
    assert writer["PRODUCTIVE_WRITER"] == "NOT_PROVEN"
    assert writer["DYNAMIC_SCOPE_STATE_PERSISTED"] is True
    assert writer["BINDER_RUNTIME_ACTIVATED"] is False
    assert writer["RUNTIME_ACTIVATED_IS_WRITER_ABSENCE_PROOF"] is False
    assert writer["CONSTANT_IS_WRITER_PROOF"] is False
    assert writer["WRITER_CONDITION"] == "persist and binding.state_root"
    assert "overall_pass" not in report


def test_universe_and_lock_claims_reject() -> None:
    universe = _verify({"separate_universe_claimed": True})
    authority = _verify({"decision_authority_claimed": True})
    lock = _verify({"lock_mutation_requested": True})
    tool_go = _verify({"tool_run_claimed_as_owner_go": True})
    assert "DYNAMIC_SCOPE_ROLE_VIOLATION" in universe["REJECTION_REASONS"]
    assert _row(universe, "MV2-04")["DECISION_AUTHORITY_GRANTED"] is False
    assert _row(authority, "MV2-04")["REACTION"] == "DYNAMIC_SCOPE_ROLE_VIOLATION"
    assert "OWNER_LOCK_VIOLATION" in lock["REJECTION_REASONS"]
    assert "OWNER_LOCK_VIOLATION" in tool_go["REJECTION_REASONS"]
    assert _row(tool_go, "MV2-05")["TOOL_RUN_IS_OWNER_GO"] is False
    assert universe["GHOSV_READY"] is False


def test_effect_pass_and_writer_claims_stay_not_proven() -> None:
    effect = _verify({"effect_pass_requested": True})
    writer = _verify({"persists_claimed": True})
    constants = _verify({"writer_proven_from_constants": True})
    refuted = _verify({"writer_refutation_requested": True})
    assert "EFFECT_PASS_BLOCKED" in effect["REJECTION_REASONS"]
    assert _row(effect, "MV2-06")["ENTRY_EXIT_EFFECT"] == "NOT_PROVEN"
    assert _row(effect, "MV2-06")["EFFECT_PASS"] is False
    assert "PERSISTENCE_EVIDENCE_ABSENT" in writer["REJECTION_REASONS"]
    assert _row(writer, "MV2-08")["PRODUCTIVE_WRITER"] == "NOT_PROVEN"
    assert _row(constants, "MV2-08")["REACTION"] == "PERSISTENCE_EVIDENCE_ABSENT"
    assert _row(constants, "MV2-08")["CONSTANT_IS_WRITER_PROOF"] is False
    assert "WRITER_REFUTATION_BLOCKED" in refuted["REJECTION_REASONS"]
    assert _row(refuted, "MV2-08")["RUNTIME_ACTIVATED_IS_WRITER_ABSENCE_PROOF"] is False


def test_older_pin_represented_as_current_rejects() -> None:
    report = _verify({"treat_older_pin_as_current": True})
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "OLDER_PIN_TREATED_AS_CURRENT" in report["REJECTION_REASONS"]
    assert report["GHOSV_PIN_IS_CURRENT_BASELINE"] is False
    assert all(row["EXISTING_CHECKER_STATUS"] == "NOT_TESTED" for row in report["FINDINGS"])


def test_domain_identity_stays_out_of_master_v2_findings() -> None:
    for path in PACKAGE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "make_finding_v1" not in text
        assert "run_ghosv_master_v2_bounded_context_v1" not in text
        assert "traverse_forensic_graph_v1" not in text
    report = _verify()
    assert report["DOMAIN"] == "DOUBLE_PLAY"
    parsed = ast.parse((PACKAGE / "ghosv_track_v1.py").read_text(encoding="utf-8"))
    for node in ast.walk(parsed):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith(
                "scripts.ops.ghosv_master_v2_bounded_context_v1"
            )
            assert not (node.module or "").startswith("trading")
