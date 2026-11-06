"""Contract tests for evidence-only V6 midband exit-efficiency failure attribution.

Read-only. Must never invoke evaluation runners, panel loaders, or mutate source V6 digests.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEST_FILE = Path(__file__).resolve()
EVIDENCE = REPO / "docs/evidence/attribute_bollinger_mr_midband_exit_efficiency_v6_failure"
SOURCE = REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v6"
GOVERNANCE = REPO / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION.md"
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)

HYPOTHESIS_ID = "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6"
PREREG_DIGEST = "9ddcd32d78b3b3f60c168321404b2270a770409d46a3bff036f7dbc5eefd8fa5"
ORIGIN_MAIN = "98aede46fcecc7dffb5b515f4bd87b06fd2eecb7"

REQUIRED_EVIDENCE = (
    "README.md",
    "FAILURE_ATTRIBUTION_REPORT.md",
    "attribution_summary.json",
    "source_artifact_manifest.json",
    "v7_candidate_ranking.json",
    "claims_matrix.json",
    "instrument_loss_concentration.json",
    "safety_attestation.md",
    "MANIFEST.sha256",
)

BANNED_CALLS = {
    "run_development_evaluation",
    "run_arm",
    "load_member_bars",
    "resolve_development_archive_root",
    "verify_development_panel_hashes",
    "included_panel_members",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_unit_tests_do_not_call_evaluation_or_panel_surfaces() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
                raise AssertionError(f"banned_call:{node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in BANNED_CALLS:
                raise AssertionError(f"banned_call:{node.func.attr}")


def test_required_evidence_and_governance_present() -> None:
    missing = [n for n in REQUIRED_EVIDENCE if not (EVIDENCE / n).is_file()]
    assert missing == [], missing
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION" in text
    assert "EVIDENCE_ONLY_FAILURE_ATTRIBUTION_COMPLETE" in text


def test_source_binding_and_run_count_unchanged() -> None:
    summary = _load(SOURCE / "summary.json")
    assert summary["hypothesis_id"] == HYPOTHESIS_ID
    assert summary["result_class"] == "FAIL"
    assert summary["evaluation_run_count"] == 1
    assert summary["decision"]["reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert summary["baseline_metrics"]["trade_count"] == 109
    assert summary["treatment_metrics"]["trade_count"] == 566
    assert _sha256(SOURCE / "summary.json") == (
        "608b1ff80333ffdb3f79566b419e57f3aeb2ac51b4edb98071b571e834bf4330"
    )


def test_attribution_summary_safety_and_consistency() -> None:
    payload = _load(EVIDENCE / "attribution_summary.json")
    report = (EVIDENCE / "FAILURE_ATTRIBUTION_REPORT.md").read_text(encoding="utf-8")
    ranking = _load(EVIDENCE / "v7_candidate_ranking.json")
    claims = _load(EVIDENCE / "claims_matrix.json")
    manifest = _load(EVIDENCE / "source_artifact_manifest.json")

    assert payload["source_hypothesis_id"] == HYPOTHESIS_ID
    assert payload["source_terminal_classification"] == "FAIL"
    assert payload["source_run_count_before"] == 1
    assert payload["source_run_count_after"] == 1
    assert payload["source_preregistration_digest"] == PREREG_DIGEST
    assert payload["source_result_digest"] == (
        "608b1ff80333ffdb3f79566b419e57f3aeb2ac51b4edb98071b571e834bf4330"
    )
    assert payload["origin_main_expected"] == ORIGIN_MAIN
    assert payload["evaluation_runner_executed"] is False
    assert payload["backtest_or_replay_executed"] is False
    assert payload["raw_development_panel_accessed"] is False
    assert payload["holdout_data_accessed"] is False
    assert payload["source_artifacts_mutated"] is False
    assert payload["v7_preregistration_created"] is False
    assert payload["attribution_arithmetic_valid"] is True
    assert payload["totals_reconciliation"]["exits_forced_by_gate"] == 326
    assert payload["totals_reconciliation"]["midband_exit_count"] == 318
    assert payload["totals_reconciliation"]["max_holding_exit_count"] == 10
    assert payload["totals_reconciliation"]["dual_trigger_overlap_count"] == 2
    assert (
        payload["trade_count_increase_explanation"]["label"]
        == "EARLIER_EXIT_FOLLOWED_BY_REENTRY_CHURN"
    )
    assert payload["degradation_decomposition"]["primary_degradation_channel"] == (
        "COST_DRAG_FROM_SHORT_SIDE_REENTRY_CHURN_AFTER_FORCED_MIDBAND_EXITS"
    )
    assert payload["v7_candidate_count"] == 3
    assert ranking["preregistration_created"] is False
    assert ranking["selection_authorized"] is False
    assert len(ranking["candidates"]) == 3
    assert "no new evaluation" in report.lower() or "No new evaluation" in report
    assert (
        "V7_PREREGISTRATION_CREATED` | `false`" in report or "V7_PREREGISTRATION_CREATED" in report
    )
    assert claims["counts"]["PROVEN"] >= 1
    assert claims["counts"]["NOT_OBSERVABLE"] >= 1
    assert manifest["source_result_digest"] == payload["source_result_digest"]


def test_attribution_arithmetic_matches_source_metrics() -> None:
    bm = _load(SOURCE / "baseline_metrics.json")
    tm = _load(SOURCE / "treatment_metrics.json")
    payload = _load(EVIDENCE / "attribution_summary.json")
    deg = payload["degradation_decomposition"]
    assert abs(deg["gross_pnl_delta"] - (tm["gross_pnl"] - bm["gross_pnl"])) < 1e-9
    assert abs(deg["cost_drag_delta"] - (tm["cost_drag"] - bm["cost_drag"])) < 1e-9
    assert abs(deg["net_pnl_delta"] - (tm["net_pnl"] - bm["net_pnl"])) < 1e-9
    assert abs((deg["gross_pnl_delta"] - deg["cost_drag_delta"]) - deg["net_pnl_delta"]) < 1e-9
    assert deg["cost_drag_delta"] > deg["gross_pnl_delta"]


def test_backlog_and_owner_map_register_attribution_without_v7() -> None:
    backlog = _load(BACKLOG)
    v6 = next(e for e in backlog["terminal_hypotheses"] if e["hypothesis_id"] == HYPOTHESIS_ID)
    assert v6["result_class"] == "FAIL"
    assert v6["evaluation_run_count"] == 1
    assert v6["failure_attribution_completed"] is True
    assert v6["failure_attribution_ref"].endswith(
        "attribute_bollinger_mr_midband_exit_efficiency_v6_failure/"
    )
    assert v6["failure_attribution_authorizes_v7"] is False
    assert v6["failure_attribution_mutates_v6_result"] is False
    assert "NO_V7_AUTO_CREATE" in backlog["explicit_non_actions"]
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    assert "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION" in owners


def test_manifest_lists_existing_files_only() -> None:
    lines = (EVIDENCE / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        digest, name = line.split(maxsplit=1)
        path = EVIDENCE / name
        assert path.is_file(), name
        assert _sha256(path) == digest
