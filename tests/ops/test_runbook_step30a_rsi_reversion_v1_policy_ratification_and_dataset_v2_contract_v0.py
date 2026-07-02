"""Runbook contract for STEP30A policy ratification and dataset v2 binding."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"


def _field_value(text: str, field: str) -> str:
    match = re.search(
        rf"\| `{re.escape(field)}` \| `([^`]*)`(?: <!--.*?-->)? \|",
        text,
    )
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_30a_section(text: str) -> str:
    start = text.index(
        "#### RUNBOOK_STEP_30A — RSI Reversion v1 Extended Holdout-Separated Futures Economic Research v0"
    )
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_step30a_section_has_required_ratification_fields() -> None:
    section = _step_30a_section(PROGRESS_REGISTRY.read_text(encoding="utf-8"))
    assert _field_value(section, "STEP30A_OPERATOR_POLICY_RATIFIED") == "true"
    assert _field_value(section, "STEP30A_GO_TOKEN") == (
        "GO_BOUNDED_STEP30A_RSI_REVERSION_V1_EXTENDED_HOLDOUT_SEPARATED_FUTURES_ECONOMIC_RESEARCH_V0"
    )
    assert _field_value(section, "STEP30A_EVALUATION_AUTHORIZED") == "false"
    assert _field_value(section, "STEP30A_PROMOTION_AUTHORIZED") == "false"
    assert _field_value(section, "STEP30A_RUNTIME_AUTHORIZED") == "false"


def test_step30a_section_binds_dataset_v2_and_frozen_holdout() -> None:
    section = _step_30a_section(PROGRESS_REGISTRY.read_text(encoding="utf-8"))
    assert _field_value(section, "STEP30A_DATASET_VERSION") == "v2"
    assert _field_value(section, "STEP30A_HOLDOUT_FROZEN_REF") == (
        "2026-06-17 10:07:00+00:00..2026-07-01 10:07:00+00:00"
    )
    assert _field_value(section, "STEP30A_REGISTERED_ECONOMIC_EVALUATION_CONFIGS").replace(
        "&#47;", "/"
    ) == "config/ops/step30a_okx_inst_eth_usdt_perp_rsi_reversion_v1_economic_evaluation_v1.json"
    assert _field_value(section, "NEXT_CANONICAL_STEP") == (
        "SEPARATE_EVALUATION_GO_REQUIRED_AFTER_PRE_PR_AND_IMPLEMENTATION_CLOSEOUT"
    )
