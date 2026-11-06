"""Contract tests for trend_following/v1 terminal negative economic evidence governance closeout v0."""

from __future__ import annotations

import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/TREND_FOLLOWING_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### TREND_FOLLOWING_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_V0"
)
MERGE_COMMIT = "2e354a30803324fee158325fb00fcb0b343ae1dd"
BINDING_DIGEST = "ea3bde558a2ffd903ed7b7f678cb0cf0a8a4b1f1bb7f5978f7b5bc8f69ab8478"
EVAL_BUNDLE_SUFFIX = (
    "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
)
CLOSEOUT_BUNDLE_SUFFIX = "trade_ledger_equity_curve_persistence_offline_evaluation_execution_pr_squash_merge_closeout_v0_20260705T083950Z"


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


class TestTrendFollowingV1TerminalNegativeEconomicEvidenceCloseoutV0Contract:
    def test_governance_doc_has_docs_token_and_terminal_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_TREND_FOLLOWING_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0"
            )
            in body
        )
        assert f"`PR4860_MERGE_COMMIT` | `{MERGE_COMMIT}`" in body
        assert "trend_following&#47;v1" in body
        assert f"`STRATEGY_BINDING_DIGEST` | `{BINDING_DIGEST}`" in body
        assert "`EVIDENCE_STATUS` | `ROBUSTNESS_FAILED`" in body
        assert "`PRIMARY_FAILURE_CLASS` | `NEGATIVE_RAW_EDGE`" in body
        assert "`economic_validity_offline_gate_pass` | `false`" in body
        assert "`PROMOTION_ELIGIBLE` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert "NEXT_ACTION=NO_RUNTIME_OR_PROMOTION_ACTION" in body
        assert EVAL_BUNDLE_SUFFIX in body
        assert CLOSEOUT_BUNDLE_SUFFIX in body
        assert "| Evaluation MANIFEST_VERIFY_RC | `0` |" in body
        assert "| Closeout MANIFEST_VERIFY_RC | `0` |" in body
        assert "`NO_OUTPUT_JSONL_MATERIALIZED_IN_REPO` | `true`" in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "TREND_FOLLOWING_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0_STATUS",
            )
            == "NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "TREND_FOLLOWING_V1_ECONOMIC_VALIDITY_OFFLINE_GATE_PASS",
            )
            == "false"
        )
        assert _field_value(text, "TREND_FOLLOWING_V1_EVIDENCE_STATUS") == "ROBUSTNESS_FAILED"
        assert _field_value(text, "TREND_FOLLOWING_V1_PRIMARY_FAILURE_CLASS") == "NEGATIVE_RAW_EDGE"
        assert _field_value(text, "TREND_FOLLOWING_V1_PROCESS_EXECUTION_PASS") == "true"
        assert _field_value(text, "TREND_FOLLOWING_V1_PROMOTION_ELIGIBLE") == "false"
        assert _field_value(text, "TREND_FOLLOWING_V1_RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(text, "TREND_FOLLOWING_V1_NO_RUNTIME_OR_PROMOTION_ACTION") == "true"
        assert _field_value(text, "TREND_FOLLOWING_V1_AUTHORITY_EFFECT") == "NONE"
        assert _field_value(text, "PR4860_MERGE_COMMIT") == MERGE_COMMIT
        assert _field_value(text, "TREND_FOLLOWING_V1_STRATEGY_BINDING_DIGEST") == BINDING_DIGEST
        assert "trend_following&#47;v1" in _field_value(
            text, "TREND_FOLLOWING_V1_STRATEGY_BINDING_REF"
        )
        assert EVAL_BUNDLE_SUFFIX in _field_value(text, "TREND_FOLLOWING_V1_EVALUATION_BUNDLE")
        assert CLOSEOUT_BUNDLE_SUFFIX in _field_value(text, "TREND_FOLLOWING_V1_CLOSEOUT_BUNDLE")

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_COMPLETE"
        )
        assert _field_value(section, "PROCESS_EXECUTION_PASS") == "true"
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "EVIDENCE_STATUS") == "ROBUSTNESS_FAILED"
        assert _field_value(section, "PRIMARY_FAILURE_CLASS") == "NEGATIVE_RAW_EDGE"
        assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "NO_RUNTIME_OR_PROMOTION_ACTION") == "true"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "NO_OUTPUT_JSONL_MATERIALIZED_IN_REPO") == "true"
        assert _field_value(section, "PR4860_MERGE_COMMIT") == MERGE_COMMIT
        assert "trend_following&#47;v1" in _field_value(section, "STRATEGY_BINDING_REF")
        assert _field_value(section, "STRATEGY_BINDING_DIGEST") == BINDING_DIGEST
        assert _field_value(section, "NEXT_ACTION") == "NO_RUNTIME_OR_PROMOTION_ACTION"
        assert EVAL_BUNDLE_SUFFIX in _field_value(section, "EVIDENCE_BUNDLE_PATH")
        assert CLOSEOUT_BUNDLE_SUFFIX in _field_value(section, "PR4860_CLOSEOUT_EVIDENCE_REF")
