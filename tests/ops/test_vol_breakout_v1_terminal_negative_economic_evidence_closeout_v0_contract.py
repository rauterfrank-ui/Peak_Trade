"""Contract tests for vol_breakout/v1 terminal negative economic evidence closeout v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSEOUT_CONFIG = (
    REPO_ROOT
    / "config/research/vol_breakout_v1_terminal_negative_economic_evidence_closeout_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_V0"
)
CLOSEOUT_GO = "GO_VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0"
CURRENT_STATE = "VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE_V0"
PROCESS_CLASSIFICATION = (
    "PERSIST_TERMINAL_NEGATIVE_EVIDENCE_NO_POLICY_RESCUE_AND_CLOSE_RESEARCH_GENERATION_V0"
)
SCOPE_CLASSIFICATION = "VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0"
ORIGIN_MAIN = "5a423b44645f5923985dd0eb660c55c1a065057b"
ECONOMIC_BUNDLE_SUFFIX = (
    "vol_breakout_v1_full_canonical_offline_baseline_economic_evaluation_v0_20260710T080040Z"
)
MERGE_CLOSEOUT_SUFFIX = (
    "pr5074_merge_closeout_vol_breakout_v1_sizing_config_digest_binding_fix_v0_20260710T075844Z"
)
REASON_CODES = (
    "METRIC_MISSING:parameter_neighbor_degradation;"
    "METRIC_MISSING:single_regime_profit_contribution;"
    "MONTE_CARLO_FAILED;"
    "NET_EXPECTANCY_BELOW_THRESHOLD;"
    "OUT_OF_SAMPLE_FAILED;"
    "PROFIT_FACTOR_BELOW_THRESHOLD;"
    "STRESS_FAILED;"
    "WALK_FORWARD_FAILED"
)
AUTHORITY_TRUE_FLAGS = (
    "promotion_eligible",
    "runtime_rewire_admissible",
    "runtime_authority",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "live_authorized",
    "immutable_binding_retry_allowed",
    "same_binding_retry_allowed",
    "policy_rescue_allowed",
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
    next_heading = tail.find("\n---\n\n## PR #4629 Evidence-Drift")
    assert next_heading != -1, "missing closeout section boundary"
    return tail[:next_heading]


class TestVolBreakoutV1TerminalNegativeEconomicEvidenceCloseoutV0Contract:
    def test_closeout_config_exists_and_terminal_gates(self) -> None:
        assert CLOSEOUT_CONFIG.is_file()
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["verdict"] == CURRENT_STATE
        assert payload["status"] == "TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE"
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["scope_classification"] == SCOPE_CLASSIFICATION
        assert payload["go_token"] == CLOSEOUT_GO
        assert payload["binding"] == "vol_breakout/v1"
        assert payload["instrument_id"] == "inst-eth-usdt-perp"
        assert payload["terminal_verdict"] == "FAIL"
        assert payload["failure_class"] == "NEGATIVE_ECONOMIC_BASELINE_AND_ROBUSTNESS_FAIL"
        assert payload["failed_binding_registered"] is True
        assert payload["current_research_generation_closed"] is True
        assert payload["unchanged_retry_blocked"] is True
        assert payload["sufficient_trade_sample"] is True
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["policy_rescue_allowed"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert payload["historical_negative_evidence_mutated"] is False
        assert payload["manifest_verify_rc"] == 0
        assert payload["source_manifest_verify_rc"] == 0
        assert payload["baseline_head"] == ORIGIN_MAIN
        assert payload["baseline_pr"] == 5074
        assert ECONOMIC_BUNDLE_SUFFIX in payload["source_economic_evidence_path"]
        assert MERGE_CLOSEOUT_SUFFIX in payload["merge_closeout_evidence_path"]
        assert payload["metrics"]["trade_count"] == 151
        assert payload["metrics"]["baseline_verdict"] == "FAIL"
        assert payload["reason_codes"] == REASON_CODES.split(";")
        assert (
            payload["reason_code_classification"]["METRIC_MISSING:parameter_neighbor_degradation"]
            == "ADDITIONAL_EVIDENCE_ROBUSTNESS_DEFICIT"
        )
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_governance_doc_has_docs_token_and_terminal_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{CURRENT_STATE}`" in body
        assert "`BINDING` | `vol_breakout&#47;v1`" in body
        assert "`INSTRUMENT` | `inst-eth-usdt-perp`" in body
        assert "`BASELINE_VERDICT` | `FAIL`" in body
        assert "`FAILURE_CLASS` | `NEGATIVE_ECONOMIC_BASELINE_AND_ROBUSTNESS_FAIL`" in body
        assert "`SUFFICIENT_TRADE_SAMPLE` | `true`" in body
        assert "`FAILED_BINDING_REGISTERED` | `true`" in body
        assert "`CURRENT_RESEARCH_GENERATION_CLOSED` | `true`" in body
        assert "`UNCHANGED_RETRY_BLOCKED` | `true`" in body
        assert "`POLICY_RESCUE_ALLOWED` | `false`" in body
        assert "`METRIC_MISSING_DOES_NOT_RECLASSIFY_BASELINE` | `true`" in body
        assert (
            "NEXT_CANONICAL_STEP=NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED" in body
        )
        assert ECONOMIC_BUNDLE_SUFFIX in body
        assert MERGE_CLOSEOUT_SUFFIX in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0_STATUS",
            )
            == "TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0_GO_TOKEN",
            )
            == CLOSEOUT_GO
        )
        assert (
            _field_value(
                text,
                "VOL_BREAKOUT_V1_TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0_CONFIG_REF",
            )
            == "config/research/vol_breakout_v1_terminal_negative_economic_evidence_closeout_v0.json"
        )
        assert _field_value(text, "VOL_BREAKOUT_V1_CURRENT_RESEARCH_GENERATION_CLOSED") == "true"
        assert _field_value(text, "VOL_BREAKOUT_V1_FAILED_BINDING_REGISTERED") == "true"
        assert _field_value(text, "VOL_BREAKOUT_V1_UNCHANGED_RETRY_BLOCKED") == "true"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE"
        )
        assert _field_value(section, "VERDICT") == CURRENT_STATE
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "GO_TOKEN") == CLOSEOUT_GO
        assert "vol_breakout&#47;v1" in _field_value(section, "BINDING")
        assert _field_value(section, "INSTRUMENT") == "inst-eth-usdt-perp"
        assert _field_value(section, "BASELINE_VERDICT") == "FAIL"
        assert (
            _field_value(section, "FAILURE_CLASS")
            == "NEGATIVE_ECONOMIC_BASELINE_AND_ROBUSTNESS_FAIL"
        )
        assert _field_value(section, "SUFFICIENT_TRADE_SAMPLE") == "true"
        assert _field_value(section, "FAILED_BINDING_REGISTERED") == "true"
        assert _field_value(section, "CURRENT_RESEARCH_GENERATION_CLOSED") == "true"
        assert _field_value(section, "UNCHANGED_RETRY_BLOCKED") == "true"
        assert _field_value(section, "POLICY_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "TRADE_COUNT") == "151"
        assert _field_value(section, "REASON_CODES") == REASON_CODES
        assert ECONOMIC_BUNDLE_SUFFIX in _field_value(section, "ECONOMIC_EVIDENCE_REF")
        assert MERGE_CLOSEOUT_SUFFIX in _field_value(section, "PR5074_CLOSEOUT_EVIDENCE_REF")
        assert (
            _field_value(section, "NEXT_CANONICAL_STEP")
            == "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
        )
