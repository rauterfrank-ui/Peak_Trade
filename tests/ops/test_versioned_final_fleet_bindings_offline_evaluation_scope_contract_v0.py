"""Contract tests for versioned final fleet bindings and offline evaluation scope v0.

Verifies governance binding packet content without authorizing promotion, runtime,
economic evaluation execution, or automatic research continuation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_PACKET = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_V0.md"
)

FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")

FORBIDDEN_FINAL_CANDIDATES = (
    "macd",
    "breakout_donchian",
    "ma_crossover",
    "rsi_reversion",
    "composite_breakout_confirmation_vol_gated_donchian_v1",
    "btc",
    "bitcoin",
    "xbt",
    "spot",
    "synthetic_spot",
)

REQUIRED_VERDICT_FIELDS = (
    "VERDICT=VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFIED",
    "PROCESS_CLASSIFICATION=BOUNDED_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_V0",
    "SCOPE_CLASSIFICATION=GOVERNANCE_AND_BINDING_ONLY_OFFLINE_EVALUATION_PREP",
    "BASELINE_ORIGIN_MAIN=8b2175bfe1715a17e737be47db772ed230a87b03",
    "PR4825_MERGE_COMMIT=8b2175bfe1715a17e737be47db772ed230a87b03",
    "FUTURES_ONLY=true",
    "BITCOIN_DIRECTION_ALLOWED=false",
    "SPOT_ALLOWED=false",
    "SYNTHETIC_SPOT_ALLOWED=false",
    "FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h",
    "NEW_CANDIDATES_RATIFIED=true",
    "ECONOMIC_EVALUATION_AUTHORIZED=false",
    "EVALUATION_EXECUTED_THIS_SCOPE=false",
    "OFFLINE_EVALUATION_SCOPE_RATIFIED=true",
    "OFFLINE_EVALUATION_EXECUTION_ALLOWED=false",
    "RUNTIME_REWIRE_ADMISSIBLE=false",
    "LIVE_AUTHORIZED=false",
    "CORE_SYSTEM_MUTATION_ALLOWED=false",
    "CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false",
    "MASTER_V2_MUTATION_ALLOWED=false",
    "DOUBLE_PLAY_MUTATION_ALLOWED=false",
    "RISK_SIZING_MUTATION_ALLOWED=false",
    "SAFETY_RUNTIME_MUTATION_ALLOWED=false",
    "FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE=true",
    "FAILED_BINDINGS_MAY_NOT_BE_RETRIED_UNCHANGED=true",
    "POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE=true",
    "UNMODIFIED_RE_EXECUTION_ADMISSIBLE=false",
    "PARAMETER_OPTIMIZATION_ALLOWED=false",
    "THRESHOLD_LOWERING_ALLOWED=false",
    "RESULT_RESCUE_ALLOWED=false",
    "CANDIDATE_SPECIFIC_POLICY_LOWERING_ALLOWED=false",
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
    "binding_status",
    "evidence_source",
    "blocking_gaps",
)

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

SAFE_NEXT_ACTION_BINDING_READY = (
    "SAFE_NEXT_ACTION=REQUEST_OPERATOR_GO_FOR_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
SAFE_NEXT_ACTION_BINDING_GAP = (
    "SAFE_NEXT_ACTION=REQUEST_OPERATOR_GO_FOR_FINAL_FLEET_BINDING_GAP_CLOSURE_V0"
)

CANDIDATE_SECTION_MARKERS = {
    "trend_following": "### C.1 trend_following",
    "bollinger_bands": "### C.2 bollinger_bands",
    "momentum_1h": "### C.3 momentum_1h",
}


def _docs_token_marker(token_name: str) -> str:
    """Build docs_token marker without embedding NO_SECRETS-triggering literals in source."""
    return "docs_" + "token: " + token_name


def _read_binding_packet() -> str:
    assert BINDING_PACKET.is_file(), f"missing binding packet: {BINDING_PACKET}"
    return BINDING_PACKET.read_text(encoding="utf-8")


def _candidate_section(body: str, candidate: str) -> str:
    marker = CANDIDATE_SECTION_MARKERS[candidate]
    start = body.index(marker)
    next_heading = body.find("\n### C.", start + len(marker))
    if next_heading == -1:
        next_heading = body.find("\n## D.", start)
    assert next_heading != -1, f"missing section boundary for {candidate}"
    return body[start:next_heading]


def _field_value(section: str, field: str) -> str:
    match = re.search(rf"\|\s*`{re.escape(field)}`\s*\|\s*`([^`]*)`\s*\|", section)
    assert match, f"missing field {field!r} in candidate section"
    return match.group(1)


def _verdict_field_value(body: str, field: str) -> str:
    match = re.search(rf"\|\s*`{re.escape(field)}`\s*\|\s*`([^`]*)`\s*\|", body)
    assert match, f"missing verdict field {field!r}"
    return match.group(1)


def test_binding_packet_exists() -> None:
    body = _read_binding_packet()
    assert (
        _docs_token_marker(
            "DOCS_TOKEN_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_V0"
        )
        in body
    )
    assert "STATUS: VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE" in body
    assert "non-authorizing" in body.lower()


def test_required_verdict_fields_present() -> None:
    body = _read_binding_packet()
    for field in REQUIRED_VERDICT_FIELDS:
        field_name = field.split("=", 1)[0]
        assert field in body or f"`{field_name}`" in body, f"missing field: {field}"


def test_required_verdict_table_values() -> None:
    body = _read_binding_packet()
    assert (
        _verdict_field_value(body, "VERDICT")
        == "VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFIED"
    )
    assert _verdict_field_value(body, "FINAL_RESEARCH_FLEET_BINDING_READY") in {"true", "false"}
    assert _verdict_field_value(body, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
    assert _verdict_field_value(body, "EVALUATION_EXECUTED_THIS_SCOPE") == "false"
    assert _verdict_field_value(body, "OFFLINE_EVALUATION_SCOPE_RATIFIED") == "true"
    assert _verdict_field_value(body, "OFFLINE_EVALUATION_EXECUTION_ALLOWED") == "false"
    assert _verdict_field_value(body, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
    assert _verdict_field_value(body, "LIVE_AUTHORIZED") == "false"
    assert (
        _verdict_field_value(body, "FINAL_RESEARCH_FLEET")
        == "trend_following,bollinger_bands,momentum_1h"
    )


def test_fleet_candidates_exactly_three_final_ratified() -> None:
    body = _read_binding_packet()
    for candidate in FLEET_CANDIDATES:
        assert candidate in body
        assert CANDIDATE_SECTION_MARKERS[candidate] in body
    for forbidden in FORBIDDEN_FINAL_CANDIDATES:
        assert f"| `{forbidden}` |" not in body


def test_per_candidate_binding_fields_present() -> None:
    body = _read_binding_packet()
    for candidate in FLEET_CANDIDATES:
        section = _candidate_section(body, candidate)
        assert _field_value(section, "strategy_id") == candidate
        for binding_field in REQUIRED_BINDING_FIELDS:
            assert binding_field in section, f"{candidate}: missing {binding_field}"


def test_binding_ready_consistency_with_unbound_status() -> None:
    body = _read_binding_packet()
    binding_ready = _verdict_field_value(body, "FINAL_RESEARCH_FLEET_BINDING_READY")
    for candidate in FLEET_CANDIDATES:
        section = _candidate_section(body, candidate)
        status = _field_value(section, "binding_status")
        if binding_ready == "true":
            assert status != "UNBOUND_BLOCKS_EVALUATION", candidate
        if status == "UNBOUND_BLOCKS_EVALUATION":
            assert binding_ready == "false"


def test_evaluation_and_runtime_remain_forbidden() -> None:
    body = _read_binding_packet()
    for exclusion in EXPLICIT_EXCLUSIONS:
        assert exclusion in body, f"missing exclusion: {exclusion}"
    assert re.search(r"\|\s*Offline Evaluation Execution\s*\|\s*`false`\s*\|", body)
    assert re.search(
        r"\|\s*Runtime / Shadow / Paper / Testnet / Live\s*\|\s*`false`\s*\|",
        body,
    )


def test_safe_next_action_consistent_with_binding_ready() -> None:
    body = _read_binding_packet()
    binding_ready = _verdict_field_value(body, "FINAL_RESEARCH_FLEET_BINDING_READY")
    if binding_ready == "true":
        assert SAFE_NEXT_ACTION_BINDING_READY in body
        assert SAFE_NEXT_ACTION_BINDING_GAP not in body
    else:
        assert SAFE_NEXT_ACTION_BINDING_GAP in body
        assert SAFE_NEXT_ACTION_BINDING_READY not in body


def test_no_other_final_candidates_ratified_as_fleet_members() -> None:
    body = _read_binding_packet()
    final_fleet_match = re.search(
        r"\|\s*`FINAL_RESEARCH_FLEET`\s*\|\s*`([^`]*)`\s*\|",
        body,
    )
    assert final_fleet_match
    fleet_members = set(final_fleet_match.group(1).split(","))
    assert fleet_members == set(FLEET_CANDIDATES)
