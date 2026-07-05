"""Contract tests for momentum_1h/v1 offline economic evaluation scope and binding materialization v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/momentum_1h_v1_offline_economic_evaluation_scope_and_binding_materialization_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0.md"
)
FLEET_BINDING_COMPLETION = (
    REPO_ROOT / "config/research/final_research_fleet_versioned_binding_completion_v0.json"
)
PARAMETER_BINDING = (
    REPO_ROOT
    / "config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0"
)
OPERATOR_GO = "GO_MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0"
SCOPE_CLASSIFICATION = (
    "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0"
)
EVIDENCE_CLASS_ID = "TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
SCOPE_VERDICT = "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_DEFINED_NOT_EXECUTED"
STRATEGY_BINDING_REF = "momentum_1h/v1"
STRATEGY_BINDING_REF_DOCS = "momentum_1h&#47;v1"
STRATEGY_BINDING_DIGEST = "a8b7d87100d7167205258056144690273cda54769c9c29fcf8e91d4477318730"
CONFIG_DIGEST = "d92f0542eb680df599cfac4cc7b3dadc2a7d17ffa0ebe963ea75a30d2714c244"
DATA_DIGEST = "815b33162adaa2ffd0834f129621f1942b8cb61bc19a6d6220b81b15b65578cc"
IMPLEMENTATION_DIGEST = "a31f196354e1fac7f7d5f56e1d02c5b2d466c7dde935b0d8fb26985f40cd4c38"
ORIGIN_MAIN_SHA = "92f56df1a12b915437b868d7fff33d3dd078fb82"
ALLOWED_FUTURE_ARTIFACTS = ("TRADE_LEDGER_V1.jsonl", "EQUITY_CURVE_V1.jsonl")
FORBIDDEN_ACTIONS_MINIMUM = (
    "EVALUATION_EXECUTION",
    "BACKTEST_RERUN",
    "LEDGER_PERSISTENCE_EXECUTION",
    "EQUITY_CURVE_PERSISTENCE_EXECUTION",
    "SAME_BINDING_RETRY",
    "PARAMETER_OPTIMIZATION",
    "PROMOTION",
    "RUNTIME",
    "RUNTIME_REWIRE",
    "ORDERS",
    "CREDENTIALS",
)
REQUIRED_BINDING_FIELDS = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "parameter_binding_ref",
    "dataset_binding",
    "dataset_binding_ref",
    "period_binding",
    "period_binding_ref",
    "instrument_binding",
    "instrument_binding_ref",
    "fee_model_binding",
    "fee_model_binding_ref",
    "slippage_model_binding",
    "slippage_model_binding_ref",
    "funding_model_binding",
    "funding_model_binding_ref",
    "execution_model_binding",
    "execution_model_binding_ref",
    "economic_policy_binding",
    "economic_policy_binding_ref",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "binding_digest",
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_PR",
    "NO_LEDGER_PERSISTENCE_IN_THIS_PR",
    "NO_EQUITY_CURVE_PERSISTENCE_IN_THIS_PR",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_RUNTIME_REWIRE",
    "NO_PARAMETER_OPTIMIZATION",
    "Scope-Materialisierung = Evaluation authorization",
    "authority_effect=NONE",
)
LARGE_EVIDENCE_GLOBS = (
    "**/TRADE_LEDGER_V1.jsonl",
    "**/EQUITY_CURVE_V1.jsonl",
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
    return tail if next_heading == -1 else tail[:next_heading]


def _fleet_candidate(identifier: str) -> dict:
    payload = json.loads(FLEET_BINDING_COMPLETION.read_text(encoding="utf-8"))
    for candidate in payload["candidates"]:
        if candidate["canonical_candidate_identifier"] == identifier:
            return candidate
    raise AssertionError(f"missing fleet candidate: {identifier}")


class TestMomentum1hV1OfflineEconomicEvaluationScopeAndBindingMaterializationV0Contract:
    def test_scope_config_safety_flags_and_status(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["offline_only"] is True
        assert payload["status"] == SCOPE_STATUS
        assert payload["verdict"] == SCOPE_VERDICT
        assert payload["evidence_status"] == SCOPE_STATUS
        assert payload["authority_effect"] == "NONE"
        assert payload["evaluation_execution"] is False
        assert payload["evaluation_execution_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["promotion_authorized"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["runtime_authorized"] is False
        assert payload["ledger_persistence_execution"] is False
        assert payload["equity_curve_persistence_execution"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["futures_only"] is True
        assert payload["strategy_registry_verified"] is True
        assert payload["binding_selection_status"] == "BINDING_MATERIALIZATION_COMPLETE"
        assert payload["missing_binding_artifacts"] == []
        assert payload["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["go_token"] == OPERATOR_GO
        assert payload["scope_classification"] == SCOPE_CLASSIFICATION
        assert payload["origin_main_sha"] == ORIGIN_MAIN_SHA

    def test_scope_config_binding_set_required_fields(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        binding = payload["binding_set"]
        assert binding["candidate_id"] == STRATEGY_BINDING_REF
        assert binding["strategy_id"] == "momentum_1h"
        assert binding["strategy_version"] == "v1"
        assert binding["binding_digest"] == STRATEGY_BINDING_DIGEST
        assert binding["config_digest"] == CONFIG_DIGEST
        assert binding["data_digest"] == DATA_DIGEST
        assert binding["implementation_digest"] == IMPLEMENTATION_DIGEST
        for field in REQUIRED_BINDING_FIELDS:
            assert field in binding, f"missing binding field: {field}"
        instrument = binding["instrument_binding"]
        assert instrument["futures_only"] is True
        assert instrument["spot_allowed"] is False
        forbidden = payload["forbidden_actions"]
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"
        assert payload["allowed_future_output_artifacts"] == list(ALLOWED_FUTURE_ARTIFACTS)

    def test_binding_digests_match_fleet_completion_and_registry(self) -> None:
        candidate = _fleet_candidate(STRATEGY_BINDING_REF)
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        binding = payload["binding_set"]
        assert binding["binding_digest"] == candidate["binding_semantic_digest"]
        assert binding["config_digest"] == candidate["config_digest"]
        assert binding["data_digest"] == candidate["data_digest"]
        assert binding["implementation_digest"] == candidate["implementation_digest"]
        assert PARAMETER_BINDING.is_file()
        param_payload = json.loads(PARAMETER_BINDING.read_text(encoding="utf-8"))
        assert param_payload["economic_evaluation_v1"]["strategy_id"] == "momentum_1h"
        assert param_payload["economic_evaluation_v1"]["strategy_version"] == "v1"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_VERDICT}`" in body
        assert f"`candidate_id` | `{STRATEGY_BINDING_REF_DOCS}`" in body or (
            f"`strategy_binding_ref` | `{STRATEGY_BINDING_REF_DOCS}`" in body
        )
        assert f"`strategy_binding_digest` | `{STRATEGY_BINDING_DIGEST}`" in body
        assert "`EVALUATION_EXECUTION` | `false`" in body
        assert "`EVALUATION_EXECUTION_AUTHORIZED` | `false`" in body
        assert "`PROMOTION_ELIGIBLE` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert "`FUTURES_ONLY` | `true`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0_VERDICT",
            )
            == SCOPE_VERDICT
        )
        assert (
            _field_value(
                text,
                "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_AND_BINDING_MATERIALIZATION_V0_GO_TOKEN",
            )
            == OPERATOR_GO
        )
        assert (
            _field_value(text, "MOMENTUM_1H_V1_STRATEGY_BINDING_REF") == STRATEGY_BINDING_REF_DOCS
        )
        assert (
            _field_value(text, "MOMENTUM_1H_V1_STRATEGY_BINDING_DIGEST") == STRATEGY_BINDING_DIGEST
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_VERDICT
        assert _field_value(section, "STRATEGY_BINDING_REF") == STRATEGY_BINDING_REF_DOCS
        assert _field_value(section, "EVALUATION_EXECUTION") == "false"
        assert _field_value(section, "EVALUATION_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "FUTURES_ONLY") == "true"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"

    def test_no_large_evidence_files_in_repo(self) -> None:
        for pattern in LARGE_EVIDENCE_GLOBS:
            matches = list(REPO_ROOT.glob(pattern))
            assert not matches, f"large evidence file must not be in repo: {pattern}"
