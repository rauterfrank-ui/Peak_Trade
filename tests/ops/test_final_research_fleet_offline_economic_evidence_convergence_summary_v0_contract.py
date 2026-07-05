"""Contract tests for final research fleet offline economic evidence convergence summary v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SUMMARY_CONFIG = (
    REPO_ROOT
    / "config/research/final_research_fleet_offline_economic_evidence_convergence_summary_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVIDENCE_CONVERGENCE_SUMMARY_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVIDENCE_CONVERGENCE_SUMMARY_V0"
)
FLEET_STATUS = "FINAL_RESEARCH_FLEET_ECONOMIC_EVIDENCE_COMPLETE_NO_PASS"
GO_TOKEN = "GO_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVIDENCE_CONVERGENCE_SUMMARY_V0"
EXPECTED_CANDIDATES = (
    ("trend_following", "v1"),
    ("bollinger_bands", "v1"),
    ("momentum_1h", "v1"),
)
BUNDLE_SUFFIXES = (
    "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z",
    "bollinger_bands_v1_offline_economic_evaluation_execution_v0_20260705T143018Z",
    "momentum_1h_v1_offline_economic_evaluation_execution_v0_20260705T145530Z",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    tail = text[start + len(CLOSEOUT_SECTION_PREFIX) :]
    next_heading = tail.find("\n---\n\n## Post-PR-4847 Verification Binding")
    assert next_heading != -1, "missing closeout section boundary"
    return tail[:next_heading]


def _load_summary() -> dict:
    return json.loads(SUMMARY_CONFIG.read_text(encoding="utf-8"))


class TestFinalResearchFleetOfflineEconomicEvidenceConvergenceSummaryV0Contract:
    def test_summary_config_fleet_status_and_safety_flags(self) -> None:
        payload = _load_summary()
        assert payload["fleet_status"] == FLEET_STATUS
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["final_research_fleet_promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["authority_effect"] == "NONE"
        assert payload["new_candidates_ratified"] is False
        assert payload["unchanged_retry_allowed"] is False
        assert payload["go_token"] == GO_TOKEN
        for flag in (
            "no_runtime",
            "no_orders",
            "no_credentials",
            "no_scheduler",
            "no_shadow",
            "no_paper",
            "no_testnet",
            "no_jsonl_evidence_in_repo",
        ):
            assert payload[flag] is True
        constraints = payload["system_constraints"]
        assert constraints["futures_only"] is True
        assert constraints["bitcoin_direction_allowed"] is False
        assert constraints["spot_allowed"] is False

    def test_summary_config_candidates_complete_and_unique(self) -> None:
        payload = _load_summary()
        candidates = payload["candidates"]
        assert len(candidates) == 3
        keys = [(c["strategy_id"], c["strategy_version"]) for c in candidates]
        assert keys == list(EXPECTED_CANDIDATES)
        assert len(set(keys)) == 3
        for candidate in candidates:
            assert candidate["authority_effect"] == "NONE"
            assert candidate["promotion_eligible"] is False
            assert candidate["runtime_rewire_admissible"] is False
            assert candidate["economic_validity_offline_gate_pass"] is False
            assert candidate["durable_evidence_bundle_path"]
            assert candidate["manifest_verify_rc"] == 0
            assert candidate["pr_number"] in (4860, 4862, 4864)

    def test_governance_doc_has_docs_token_and_fleet_status(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVIDENCE_CONVERGENCE_SUMMARY_V0"
            )
            in body
        )
        assert f"`FLEET_STATUS` | `{FLEET_STATUS}`" in body
        assert f"`GO_TOKEN` | `{GO_TOKEN}`" in body
        assert "`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false`" in body
        assert "`UNCHANGED_RETRY_ALLOWED` | `false`" in body
        assert "`NEW_CANDIDATES_RATIFIED` | `false`" in body
        assert "trend_following&#47;v1" in body
        assert "bollinger_bands&#47;v1" in body
        assert "momentum_1h&#47;v1" in body
        for suffix in BUNDLE_SUFFIXES:
            assert suffix in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVIDENCE_CONVERGENCE_SUMMARY_V0_STATUS",
            )
            == "FINAL_RESEARCH_FLEET_ECONOMIC_EVIDENCE_COMPLETE_NO_PASS"
        )
        assert (
            _field_value(text, "FINAL_RESEARCH_FLEET_ECONOMIC_EVIDENCE_CONVERGENCE_COMPLETE")
            == "true"
        )
        assert _field_value(text, "FINAL_RESEARCH_FLEET_FLEET_STATUS") == FLEET_STATUS
        assert _field_value(text, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(text, "FINAL_RESEARCH_FLEET_PROMOTION_ELIGIBLE") == "false"
        assert _field_value(text, "UNCHANGED_RETRY_ALLOWED") == "false"
        assert _field_value(text, "NEW_CANDIDATES_RATIFIED") == "false"
        assert _field_value(text, "FUTURES_ONLY") == "true"
        assert _field_value(text, "BITCOIN_DIRECTION_ALLOWED") == "false"
        assert _field_value(text, "SPOT_ALLOWED") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "FINAL_RESEARCH_FLEET_ECONOMIC_EVIDENCE_COMPLETE_NO_PASS"
        )
        assert _field_value(section, "GO_TOKEN") == GO_TOKEN
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "NO_OUTPUT_JSONL_MATERIALIZED_IN_REPO") == "true"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
        for suffix in BUNDLE_SUFFIXES:
            assert suffix in section
