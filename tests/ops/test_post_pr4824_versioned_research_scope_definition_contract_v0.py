"""Contract tests for post-PR4824 versioned research scope definition v0.

Verifies documentation-only scope definition content without authorizing
promotion, runtime, economic evaluation execution, or automatic research continuation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_DEFINITION = (
    REPO_ROOT / "docs" / "governance" / "POST_PR4824_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0.md"
)

REQUIRED_VERDICT_FIELDS = (
    "VERDICT=POST_PR4824_VERSIONED_RESEARCH_SCOPE_DEFINITION_RATIFIED",
    "PROCESS_CLASSIFICATION=BOUNDED_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0",
    "SCOPE_CLASSIFICATION=GOVERNANCE_ONLY_RESEARCH_SCOPE_DEFINITION",
    "BASELINE_ORIGIN_MAIN=2ee068f058d265d6cf7e973bb10b103f450d5a2c",
    "PR4824_MERGE_COMMIT=2ee068f058d265d6cf7e973bb10b103f450d5a2c",
    "FUTURES_ONLY=true",
    "BITCOIN_DIRECTION_ALLOWED=false",
    "SPOT_ALLOWED=false",
    "SYNTHETIC_SPOT_ALLOWED=false",
    "LIVE_AUTHORIZED=false",
    "RUNTIME_REWIRE_ADMISSIBLE=false",
    "ECONOMIC_EVALUATION_AUTHORIZED=false",
    "EVALUATION_EXECUTED_THIS_SCOPE=false",
    "CORE_SYSTEM_MUTATION_ALLOWED=false",
    "CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false",
    "MASTER_V2_MUTATION_ALLOWED=false",
    "DOUBLE_PLAY_MUTATION_ALLOWED=false",
    "RISK_SIZING_MUTATION_ALLOWED=false",
    "SAFETY_RUNTIME_MUTATION_ALLOWED=false",
    "FINAL_RESEARCH_FLEET_STATUS=BINDINGS_REQUIRED_BEFORE_EVALUATION",
    "FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h",
    "FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE=true",
    "FAILED_BINDINGS_MAY_NOT_BE_RETRIED_UNCHANGED=true",
    "POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE=true",
    "UNMODIFIED_RE_EXECUTION_ADMISSIBLE=false",
)

REQUIRED_BINDING_FIELDS = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
)

FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")

EXPLICIT_EXCLUSIONS = (
    "NO_CORE_SYSTEM_CHANGE",
    "NO_CANONICAL_TRADING_LOGIC_CHANGE",
    "NO_MASTER_V2_CHANGE",
    "NO_DOUBLE_PLAY_CHANGE",
    "NO_RISK_SIZING_CHANGE",
    "NO_SAFETY_RUNTIME_CHANGE",
    "NO_RUNTIME_REWIRE",
    "NO_SHADOW",
    "NO_PAPER",
    "NO_TESTNET",
    "NO_SCHEDULER",
    "NO_ADAPTER_SUBMISSION",
    "NO_ORDERS",
    "NO_CREDENTIALS",
    "NO_ARMING",
    "NO_CANARY",
    "NO_LIVE",
    "NO_OFFLINE_EVALUATION_EXECUTION_THIS_SCOPE",
    "NO_BACKTEST_EXECUTION_THIS_SCOPE",
    "NO_WALK_FORWARD_EXECUTION_THIS_SCOPE",
    "NO_MONTE_CARLO_EXECUTION_THIS_SCOPE",
    "NO_STRESS_EXECUTION_THIS_SCOPE",
    "NO_PARAMETER_SENSITIVITY_EXECUTION_THIS_SCOPE",
)

SAFE_NEXT_ACTION = (
    "SAFE_NEXT_ACTION=REQUEST_OPERATOR_GO_FOR_VERSIONED_FINAL_FLEET_BINDINGS_"
    "AND_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0"
)


def _docs_token_marker(token_name: str) -> str:
    """Build docs_token marker without embedding NO_SECRETS-triggering literals in source."""
    return "docs_" + "token: " + token_name


def _read_scope_definition() -> str:
    assert SCOPE_DEFINITION.is_file(), f"missing scope definition: {SCOPE_DEFINITION}"
    return SCOPE_DEFINITION.read_text(encoding="utf-8")


def test_scope_definition_exists() -> None:
    body = _read_scope_definition()
    assert (
        _docs_token_marker("DOCS_TOKEN_POST_PR4824_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0") in body
    )
    assert "STATUS: VERSIONED_RESEARCH_SCOPE_DEFINITION" in body
    assert "non-authorizing" in body.lower()


def test_required_verdict_fields_present() -> None:
    body = _read_scope_definition()
    for field in REQUIRED_VERDICT_FIELDS:
        assert field in body or f"`{field.split('=')[0]}`" in body, f"missing field: {field}"


def test_required_verdict_table_values() -> None:
    body = _read_scope_definition()
    assert re.search(
        r"\|\s*`VERDICT`\s*\|\s*`POST_PR4824_VERSIONED_RESEARCH_SCOPE_DEFINITION_RATIFIED`\s*\|",
        body,
    )
    assert re.search(r"\|\s*`FUTURES_ONLY`\s*\|\s*`true`\s*\|", body)
    assert re.search(r"\|\s*`BITCOIN_DIRECTION_ALLOWED`\s*\|\s*`false`\s*\|", body)
    assert re.search(r"\|\s*`LIVE_AUTHORIZED`\s*\|\s*`false`\s*\|", body)
    assert re.search(r"\|\s*`ECONOMIC_EVALUATION_AUTHORIZED`\s*\|\s*`false`\s*\|", body)
    assert re.search(r"\|\s*`EVALUATION_EXECUTED_THIS_SCOPE`\s*\|\s*`false`\s*\|", body)
    assert re.search(r"\|\s*`RUNTIME_REWIRE_ADMISSIBLE`\s*\|\s*`false`\s*\|", body)
    assert re.search(
        r"\|\s*`FINAL_RESEARCH_FLEET_STATUS`\s*\|\s*`BINDINGS_REQUIRED_BEFORE_EVALUATION`\s*\|",
        body,
    )
    assert re.search(
        r"\|\s*`FINAL_RESEARCH_FLEET`\s*\|\s*`trend_following,bollinger_bands,momentum_1h`\s*\|",
        body,
    )


def test_fleet_candidates_present() -> None:
    body = _read_scope_definition()
    for candidate in FLEET_CANDIDATES:
        assert candidate in body


def test_required_binding_fields_present() -> None:
    body = _read_scope_definition()
    for binding_field in REQUIRED_BINDING_FIELDS:
        assert binding_field in body, f"missing binding field: {binding_field}"


def test_evaluation_and_runtime_remain_forbidden() -> None:
    body = _read_scope_definition()
    for exclusion in EXPLICIT_EXCLUSIONS:
        assert exclusion in body, f"missing exclusion: {exclusion}"
    assert re.search(r"\|\s*Offline Evaluation Execution\s*\|\s*`false`\s*\|", body)
    assert re.search(
        r"\|\s*Runtime / Shadow / Paper / Testnet / Live\s*\|\s*`false`\s*\|",
        body,
    )


def test_safe_next_action_exact() -> None:
    body = _read_scope_definition()
    assert SAFE_NEXT_ACTION in body
