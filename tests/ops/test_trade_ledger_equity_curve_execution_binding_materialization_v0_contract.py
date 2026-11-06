"""Contract tests for trade ledger equity curve execution binding materialization v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/trade_ledger_equity_curve_execution_binding_materialization_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0"
OPERATOR_GO = "GO_TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_PR_V0"
EVIDENCE_CLASS_ID = "TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0"
SCOPE_STATUS = "EXECUTION_BINDING_MATERIALIZED_NOT_EXECUTED"
SCOPE_VERDICT = "EXECUTION_BINDING_MATERIALIZATION_DEFINED_NOT_EXECUTED"
STRATEGY_BINDING_REF = "trend_following/v1"
STRATEGY_BINDING_REF_DOCS = "trend_following&#47;v1"
STRATEGY_BINDING_DIGEST = "ea3bde558a2ffd903ed7b7f678cb0cf0a8a4b1f1bb7f5978f7b5bc8f69ab8478"
ALLOWED_ARTIFACTS = ("TRADE_LEDGER_V1.jsonl", "EQUITY_CURVE_V1.jsonl")
MATERIALIZED_REFS = (
    "execution_owner_ref",
    "execution_runner_ref",
    "trade_ledger_v1_jsonl_export_owner_ref",
    "equity_curve_v1_jsonl_export_owner_ref",
)
INADMISSIBLE_OWNER_HINTS = (
    "final_research_fleet_offline_economic_evaluation_execution_v0",
    "run_final_research_fleet_offline_economic_evaluation_v0",
)
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
    "SHADOW",
    "PAPER",
    "TESTNET",
    "SCHEDULER",
    "ORDERS",
    "CREDENTIALS",
    "ARMING",
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_PR",
    "NO_LEDGER_PERSISTENCE_IN_THIS_PR",
    "NO_EQUITY_CURVE_PERSISTENCE_IN_THIS_PR",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_SHADOW",
    "NO_PAPER",
    "NO_TESTNET",
    "NO_SCHEDULER",
    "NO_ORDERS",
    "NO_CREDENTIALS",
    "NO_ARMING",
    "Keine Evaluation in diesem Scope",
    "Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt unverändert",
    "REQUIRES_SEPARATE_OPERATOR_GO_ONLY_AFTER_THIS_BINDING_PR_MERGED_AND_CHECKS_GREEN",
)
LARGE_EVIDENCE_GLOBS = (
    "**/TRADE_LEDGER_V1.jsonl",
    "**/EQUITY_CURVE_V1.jsonl",
)
LIVE_CLAIM_PHRASES = (
    "LIVE_AUTHORIZED: true",
    "TESTNET_AUTHORIZED: true",
    "PAPER_AUTHORIZED: true",
    "SHADOW_AUTHORIZED: true",
    "ORDERS_ALLOWED: true",
    "CREDENTIALS_REQUIRED: true",
    "ARMING_AUTHORIZED: true",
    "SCHEDULER_RUNTIME_ALLOWED: true",
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


def _resolve_repo_path(ref: str) -> Path:
    path_part = ref.split("#", 1)[0]
    return REPO_ROOT / path_part


class TestTradeLedgerEquityCurveExecutionBindingMaterializationV0Contract:
    def test_scope_config_fail_closed_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["offline_only"] is True
        assert payload["status"] == SCOPE_STATUS
        assert payload["verdict"] == SCOPE_VERDICT
        assert payload["binding_selection_status"] == "BINDING_MATERIALIZATION_COMPLETE"
        assert payload["authority_effect"] == "NONE"
        assert payload["execution_authorized"] is False
        assert payload["evaluation_authorized"] is False
        assert payload["runtime_authorized"] is False
        assert payload["orders_allowed"] is False
        assert payload["credentials_required"] is False
        assert payload["evaluation_execution"] is False
        assert payload["ledger_persistence_execution"] is False
        assert payload["equity_curve_persistence_execution"] is False
        assert payload["promotion_authorized"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["allowed_bundle_only"] is True
        assert payload["repo_evidence_files_allowed"] is False
        assert payload["no_output_jsonl_materialized_in_repo"] is True
        assert payload["primary_failure_class"] == "NEGATIVE_RAW_EDGE"
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["repo_mutation_scope"] == "GOVERNANCE_ONLY"

    def test_scope_config_materialized_binding_and_refs(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["strategy_binding_ref"] == STRATEGY_BINDING_REF
        assert payload["strategy_binding_digest"] == STRATEGY_BINDING_DIGEST
        binding_set = payload["binding_set"]
        assert binding_set["candidate_id"] == STRATEGY_BINDING_REF
        assert binding_set["binding_digest"] == STRATEGY_BINDING_DIGEST
        for field in MATERIALIZED_REFS:
            ref = payload[field]
            assert isinstance(ref, str) and ref.strip(), f"missing or empty ref: {field}"
            assert _resolve_repo_path(ref).is_file(), (
                f"ref must resolve to existing file: {field}={ref}"
            )
            for hint in INADMISSIBLE_OWNER_HINTS:
                assert hint not in ref, f"inadmissible fleet owner ref for {field}: {ref}"
        manifest_ref = payload["manifest_policy_ref"]
        assert manifest_ref
        assert _resolve_repo_path(manifest_ref).is_file()
        output_contracts = payload["output_contract_refs"]
        for artifact in ALLOWED_ARTIFACTS:
            assert artifact in output_contracts
            assert _resolve_repo_path(output_contracts[artifact]).is_file()
        assert payload["allowed_output_artifacts"] == list(ALLOWED_ARTIFACTS)
        forbidden = payload["forbidden_actions"]
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_VERDICT}`" in body
        assert f"`strategy_binding_ref` | `{STRATEGY_BINDING_REF_DOCS}`" in body
        assert STRATEGY_BINDING_DIGEST in body
        for artifact in ALLOWED_ARTIFACTS:
            assert f"`{artifact}`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"
        for phrase in LIVE_CLAIM_PHRASES:
            assert phrase not in body, f"forbidden live claim in governance doc: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0_VERDICT",
            )
            == SCOPE_VERDICT
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0_GO_TOKEN",
            )
            == OPERATOR_GO
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0_STRATEGY_BINDING_REF",
            )
            == STRATEGY_BINDING_REF_DOCS
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_V0_STRATEGY_BINDING_DIGEST",
            )
            == STRATEGY_BINDING_DIGEST
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_VERDICT
        assert _field_value(section, "STRATEGY_BINDING_REF") == STRATEGY_BINDING_REF_DOCS
        assert _field_value(section, "STRATEGY_BINDING_DIGEST") == STRATEGY_BINDING_DIGEST
        assert _field_value(section, "EVALUATION_EXECUTION") == "false"
        assert _field_value(section, "EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "LEDGER_PERSISTENCE_EXECUTION") == "false"
        assert _field_value(section, "EQUITY_CURVE_PERSISTENCE_EXECUTION") == "false"
        assert _field_value(section, "NO_OUTPUT_JSONL_MATERIALIZED_IN_REPO") == "true"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"

    def test_no_large_evidence_files_in_repo(self) -> None:
        for pattern in LARGE_EVIDENCE_GLOBS:
            matches = list(REPO_ROOT.glob(pattern))
            assert not matches, f"large evidence file must not be in repo: {pattern}"

    def test_fail_closed_runner_exits_non_zero(self) -> None:
        import subprocess

        runner = REPO_ROOT / (
            "scripts/ops/run_trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0.py"
        )
        result = subprocess.run(
            ["python3", str(runner)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "EXECUTION_BINDING_MATERIALIZED_NOT_AUTHORIZED" in result.stderr
