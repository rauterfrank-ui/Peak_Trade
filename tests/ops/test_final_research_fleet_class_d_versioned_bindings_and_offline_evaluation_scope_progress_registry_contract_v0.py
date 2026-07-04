"""Contract tests for Final Research Fleet Class D closeout registry v0."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
FINAL_RESEARCH_FLEET = "trend_following,bollinger_bands,momentum_1h"
NEW_COMPLETION_DIGEST = "0610afa34b347abde08768fb2fbfb30fd4bb19ae010f3b2042c67155fb6c0fc4"
HISTORICAL_BLOCKED_DIGEST = "161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


def test_global_summary_reflects_class_d_ratification() -> None:
    assert authoritative_field_value("CURRENT_STATE") == (
        "FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_MATERIALIZED_V0"
    )
    assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
    assert (
        authoritative_field_value("FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_STATUS")
        == "RATIFIED_CLASS_D"
    )
    assert authoritative_field_value("FINAL_RESEARCH_FLEET_CLASS_D_RATIFICATION_CLASS") == "D"
    assert (
        authoritative_field_value("FINAL_RESEARCH_FLEET_CLASS_D_COMPLETION_DIGEST")
        == NEW_COMPLETION_DIGEST
    )
    assert authoritative_field_value("BITCOIN_DRIFT_GUARD") == (
        "PASS_ONLY_IF_BTC_XBT_BITCOIN_ARE_NEGATIVE_GUARD_REFERENCES"
    )
    assert authoritative_field_value("POSITIVE_BITCOIN_BINDINGS_ALLOWED") == "false"
    assert authoritative_field_value("EVALUATION_INSTRUMENT") == "ETH-USDT-SWAP"
    assert authoritative_field_value("PANEL") == "OKX_LINEAR_PERPETUALS_NON_BITCOIN"
    assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
    assert authoritative_field_value("ECONOMIC_EVALUATION_EXECUTED") == "false"


def test_closeout_section_records_class_d_pass_without_authority() -> None:
    section = _closeout_section(read_registry())
    assert _field_value(section, "STATUS") == "COMPLETE"
    assert _field_value(section, "RATIFICATION_CLASS") == "D"
    assert _field_value(section, "RATIFICATION_STATUS") == "RATIFIED_BY_OPERATOR"
    assert _field_value(section, "FINAL_RESEARCH_FLEET") == FINAL_RESEARCH_FLEET
    assert _field_value(section, "NEW_COMPLETION_DIGEST") == NEW_COMPLETION_DIGEST
    assert (
        _field_value(section, "HISTORICAL_BLOCKED_COMPLETION_DIGEST") == HISTORICAL_BLOCKED_DIGEST
    )
    assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
    assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
    assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
    assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
    assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
