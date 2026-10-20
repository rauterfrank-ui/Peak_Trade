"""Independent tests for the Double Play GHV binding verifier."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.double_play_guardian_binding_verifier_v1.ghv_track_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    verify_double_play_ghv_v1,
)

MODULE = ROOT / "scripts/ops/double_play_guardian_binding_verifier_v1/ghv_track_v1.py"
SHA = EXPECTED_BASELINE_SHA
TREE = EXPECTED_BASELINE_TREE


def _texts() -> dict[str, str]:
    return {
        "ghosv_contract_text": (
            "OWNER > MASTER V2 > FULL AUTONOMOUS STACK\n"
            "MASTER V2 > DOUBLE PLAY > DYNAMIC SCOPE\n"
            "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3\n"
        ),
        "decision_path_text": (
            "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA=true\n"
            "DOUBLE_PLAY_SEPARATE_UNIVERSE=false\n"
            "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3\n"
            f"Alle folgenden Symbole existieren auf `{SHA}`.\n"
        ),
        "hardening_source": "\n".join(
            [
                'DOWNSTREAM_REDECISION_AUTHORITY = "NONE"',
                'LEARNING_TRADING_DECISION_AUTHORITY = "NONE"',
                'OPTIMIZATION_TRADING_DECISION_AUTHORITY = "NONE"',
                'META_LEARNING_TRADING_DECISION_AUTHORITY = "NONE"',
                'AUTONOMY_TRADING_DECISION_AUTHORITY = "NONE"',
                'EXECUTION_TRADING_DECISION_AUTHORITY = "NONE"',
                'DOUBLE_PLAY_FULL_OWNER_LOCK = "LEVEL_3"',
            ]
        ),
        "ghosv_constants_source": (
            f'CURRENT_CODE_PIN: str = "{SHA}"\nCONTRACT_DOCUMENT_PROVENANCE = "{SHA}"\n'
        ),
    }


def _verify(**kwargs: object):
    texts = _texts()
    texts.update({key: value for key, value in kwargs.items() if key in texts})
    claims = kwargs.get("claims")
    sha = str(kwargs.get("current_sha", SHA))
    tree = str(kwargs.get("current_tree", TREE))
    return verify_double_play_ghv_v1(
        current_sha=sha,
        current_tree=tree,
        ghosv_contract_text=texts["ghosv_contract_text"],
        decision_path_text=texts["decision_path_text"],
        hardening_source=texts["hardening_source"],
        ghosv_constants_source=texts["ghosv_constants_source"],
        claims=claims if isinstance(claims, dict) else None,
    )


def _result(report: dict, check: str) -> str:
    return next(row["RESULT"] for row in report["FINDINGS"] if row["CHECK"] == check)


def test_matching_tokens_do_not_make_the_tool_ready() -> None:
    report = _verify()
    assert report["VERIFICATION_STATUS"] == "REPORTED"
    assert report["REJECTION_REASONS"] == []
    assert report["GHV_READY"] is False
    assert report["TRADING_AUTHORITY"] == "NONE"
    assert report["SAFETY_AUTHORITY"] == "NONE"
    assert report["EXECUTION_AUTHORITY"] == "NONE"
    assert _result(report, "HIERARCHY") == "TOKEN_MATCH"
    assert _result(report, "INTERNAL_ROLE") == "TOKEN_MATCH"
    assert _result(report, "LOCK_TOKEN") == "TOKEN_MATCH"
    assert _result(report, "AUTHORITY_CONSTANTS") == "TOKEN_MATCH"
    assert _result(report, "GHOSV_CODE_PIN") == "TOKEN_MATCH"
    assert _result(report, "DECISION_PATH_PROVENANCE") == "TOKEN_MATCH"
    assert _result(report, "PYTHON_LOCK_ENFORCEMENT") == "TOKEN_MATCH"
    assert report["REPOSITORY_WIDE_ENFORCEMENT"] == "NOT_ASSESSED"
    assert report["CONTRACT_TEXT_IS_EXECUTABLE_PROTECTION"] is False
    assert report["VERIFIER_EXECUTION_IS_OWNER_AUTHORIZATION"] is False
    assert "overall_pass" not in report
    assert "guardian_pass" not in report


def test_current_files_report_pin_drift_and_absent_enforcement() -> None:
    report = verify_double_play_ghv_v1(
        current_sha=SHA,
        current_tree=TREE,
        ghosv_contract_text=(ROOT / "docs/ops/specs/MASTER_V2_GHOSV_CONTRACT_V1.md").read_text(),
        decision_path_text=(ROOT / "docs/ops/specs/MV2_DECISION_PATH_BOUNDARY_V1.md").read_text(),
        hardening_source=(
            ROOT / "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py"
        ).read_text(),
        ghosv_constants_source=(
            ROOT / "scripts/ops/ghosv_master_v2_bounded_context_v1/constants_v1.py"
        ).read_text(),
    )
    assert report["VERIFICATION_STATUS"] == "REPORTED"
    assert report["GHV_READY"] is False
    assert _result(report, "HIERARCHY") == "TOKEN_MATCH"
    assert _result(report, "LOCK_TOKEN") == "TOKEN_MATCH"
    assert _result(report, "AUTHORITY_CONSTANTS") == "TOKEN_MATCH"
    assert _result(report, "GHOSV_CODE_PIN") == "PIN_DRIFT"
    assert _result(report, "DECISION_PATH_PROVENANCE") == "PIN_DRIFT"
    enforcement = next(
        row for row in report["FINDINGS"] if row["CHECK"] == "PYTHON_LOCK_ENFORCEMENT"
    )
    assert enforcement["RESULT"] == "ENFORCEMENT_ABSENT"
    assert enforcement["REPOSITORY_WIDE_ENFORCEMENT"] == "NOT_ASSESSED"


def test_lock_mismatch_rejects() -> None:
    report = _verify(
        ghosv_contract_text=(
            "OWNER > MASTER V2 > FULL AUTONOMOUS STACK\n"
            "MASTER V2 > DOUBLE PLAY > DYNAMIC SCOPE\n"
            "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_1\n"
        )
    )
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "LOCK_TOKEN_MISMATCH" in report["REJECTION_REASONS"]
    assert _result(report, "LOCK_TOKEN") == "TOKEN_MISMATCH"
    assert report["GHV_READY"] is False


def test_authority_drift_rejects() -> None:
    source = _texts()["hardening_source"].replace(
        'EXECUTION_TRADING_DECISION_AUTHORITY = "NONE"',
        'EXECUTION_TRADING_DECISION_AUTHORITY = "GRANTED"',
    )
    report = _verify(hardening_source=source)
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "AUTHORITY_DRIFT" in report["REJECTION_REASONS"]
    assert _result(report, "AUTHORITY_CONSTANTS") == "TOKEN_MISMATCH"


def test_older_pin_represented_as_current_rejects() -> None:
    report = _verify(
        ghosv_constants_source=(
            'CURRENT_CODE_PIN = "7628005ae495c115ff341d32fa932b7f4642f456"\n'
            f'CONTRACT_DOCUMENT_PROVENANCE = "{SHA}"\n'
        ),
        claims={"treat_older_pin_as_current": True},
    )
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "OLDER_PIN_TREATED_AS_CURRENT" in report["REJECTION_REASONS"]
    assert _result(report, "GHOSV_CODE_PIN") == "PIN_DRIFT"
    assert report["GHV_READY"] is False


def test_missing_source_rejects() -> None:
    report = _verify(hardening_source=None)
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "MISSING_REQUIRED_EVIDENCE" in report["REJECTION_REASONS"]
    assert _result(report, "PYTHON_LOCK_ENFORCEMENT") == "UNKNOWN"
    assert report["GHV_READY"] is False


def test_unsupported_enforcement_claim_rejects() -> None:
    source = _texts()["hardening_source"].replace(
        'DOUBLE_PLAY_FULL_OWNER_LOCK = "LEVEL_3"',
        "",
    )
    report = _verify(hardening_source=source, claims={"python_enforcement_claimed": True})
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "UNSUPPORTED_ENFORCEMENT_CLAIM" in report["REJECTION_REASONS"]
    assert _result(report, "PYTHON_LOCK_ENFORCEMENT") == "ENFORCEMENT_ABSENT"


def test_track_does_not_import_checkers_or_trading() -> None:
    parsed = ast.parse(MODULE.read_text(encoding="utf-8"))
    banned = ("trading", "execution", "risk", "traverse_forensic_graph_v1", "make_finding_v1")
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert not any(name.startswith(item) for item in banned)
    assert "write_text" not in MODULE.read_text(encoding="utf-8")
