"""Contract tests for realized-volatility rank rotation v0 negative economic evidence terminalization."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
TERMINALIZATION_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_realized_volatility_rank_rotation_v0_negative_economic_evidence_terminalization_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/"
    "CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_NEGATIVE_ECONOMIC_EVIDENCE_TERMINALIZATION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_"
    "NEGATIVE_ECONOMIC_EVIDENCE_TERMINALIZATION_V0"
)
GO_TOKEN = (
    "GO_TERMINALIZE_NEGATIVE_ECONOMIC_EVIDENCE_FOR_CROSS_SECTIONAL_"
    "REALIZED_VOLATILITY_RANK_ROTATION_V0_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
VERDICT = "FAIL"
TERMINAL_ECONOMIC_DECISION = "FAIL"
EVIDENCE_BUNDLE_SUFFIX = "cross_sectional_realized_volatility_rank_rotation_v0_offline_economic_evaluation_20260706T190441Z"
EXACT_METRICS = {
    "net_return": -0.922791,
    "net_expectancy": -7.298122,
    "profit_factor": 0.617736,
    "sharpe": -7.714277,
    "sortino": -6.968245,
    "max_drawdown": -0.933418,
    "calmar": -1.070795,
    "trade_count": 726,
    "turnover": 726.0,
    "fee_drag": 3925.54,
    "funding_drag": None,
    "slippage_impact": 1962.77,
    "long_contribution": -0.003629,
    "short_contribution": 1.003629,
    "walk_forward_status": "PASS",
    "monte_carlo_status": "FAIL",
    "stress_status": "FAIL",
    "parameter_sensitivity_status": "PASS",
    "evidence_manifest_rc": 0,
}
AUTHORITY_TRUE_FLAGS = (
    "promotion_granted",
    "runtime_authority_touched",
    "runtime_authority",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "live_authorized",
    "immutable_binding_retry_allowed",
    "unchanged_retry_allowed",
    "orders_allowed",
    "scheduler_runtime_allowed",
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
    next_heading = tail.find("\n#### ")
    if next_heading == -1:
        next_heading = tail.find("\n---\n\n## PR #4629")
    return tail if next_heading == -1 else tail[:next_heading]


class TestRealizedVolatilityRankRotationV0NegativeEconomicEvidenceTerminalizationV0Contract:
    def test_terminalization_config_exists_and_terminal_gates(self) -> None:
        assert TERMINALIZATION_CONFIG.is_file()
        payload = json.loads(TERMINALIZATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["verdict"] == VERDICT
        assert payload["terminal_economic_decision"] == TERMINAL_ECONOMIC_DECISION
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["promotion_granted"] is False
        assert payload["runtime_authority_touched"] is False
        assert payload["unchanged_retry_allowed"] is False
        assert payload["immutable_binding_retry_allowed"] is False
        assert payload["new_evidence_class_required_for_further_evaluation"] is True
        assert payload["evidence_manifest_rc"] == 0
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["no_runtime_or_promotion_action"] is True
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert EVIDENCE_BUNDLE_SUFFIX in payload["evidence_bundle_path"]
        assert payload["metrics"] == EXACT_METRICS
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_governance_doc_has_docs_token_and_terminal_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_"
                "NEGATIVE_ECONOMIC_EVIDENCE_TERMINALIZATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{VERDICT}`" in body
        assert f"`TERMINAL_ECONOMIC_DECISION` | `{TERMINAL_ECONOMIC_DECISION}`" in body
        assert "`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false`" in body
        assert "`PROMOTION_GRANTED` | `false`" in body
        assert "`RUNTIME_AUTHORITY_TOUCHED` | `false`" in body
        assert "`UNCHANGED_RETRY_ALLOWED` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert (
            "NEXT_CANONICAL_STEP=NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED" in body
        )
        assert EVIDENCE_BUNDLE_SUFFIX in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_NEGATIVE_ECONOMIC_EVIDENCE_TERMINALIZATION_V0_STATUS",
            )
            == "NEGATIVE_ECONOMIC_EVIDENCE_TERMINALIZATION_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_NEGATIVE_ECONOMIC_EVIDENCE_TERMINALIZATION_V0_GO_TOKEN",
            )
            == GO_TOKEN
        )
        assert (
            _field_value(
                text,
                "CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_TERMINAL_ECONOMIC_DECISION",
            )
            == TERMINAL_ECONOMIC_DECISION
        )
        assert (
            _field_value(
                text,
                "CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_NO_RUNTIME_OR_PROMOTION_ACTION",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "CROSS_SECTIONAL_REALIZED_VOLATILITY_RANK_ROTATION_V0_UNCHANGED_RETRY_ALLOWED",
            )
            == "false"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS") == "NEGATIVE_ECONOMIC_EVIDENCE_TERMINALIZATION_COMPLETE"
        )
        assert _field_value(section, "VERDICT") == VERDICT
        assert _field_value(section, "TERMINAL_ECONOMIC_DECISION") == TERMINAL_ECONOMIC_DECISION
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "PROMOTION_GRANTED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY_TOUCHED") == "false"
        assert _field_value(section, "UNCHANGED_RETRY_ALLOWED") == "false"
        assert _field_value(section, "IMMUTABLE_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "NO_RUNTIME_OR_PROMOTION_ACTION") == "true"
        assert _field_value(section, "TERMINAL_NEGATIVE_EVIDENCE_FOR_UNCHANGED_BINDING") == "true"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "NET_RETURN") == "-0.922791"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == (
            "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
        )
        assert EVIDENCE_BUNDLE_SUFFIX in _field_value(section, "SOURCE_EVIDENCE_DIR")
