"""Registry contract for STEP 29M macd v1 real economic evaluation v2 reevaluation and v3 policy."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
V2_CONFIG = (
    REPO_ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v2.json"
)
V3_CONFIG = (
    REPO_ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json"
)
POLICY_DECISION_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning_or_validation/step29m_read_only_policy_owner_and_sizing_contract_decision_v0_20260701T235959Z"
)
EXPECTED_V2_FILE_SHA256 = "fe5b3ed1ea174e242f5a821971d94b47eb544c6fe4ec3eb99a8ceef06e3e094b"
EXPECTED_V3_CONFIG_DIGEST = "e1d923de8e5f44bc873c15008bc895b8b3542a326e9c39521e4860ba091b6b82"
V2_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/step29m_macd_v1_real_admissible_futures_economic_reevaluation_v2_20260701T212345Z"
)
INVALIDATED_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/step29m_macd_v1_real_admissible_futures_economic_evaluation_v1_20260701T161757Z"
)


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file()
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_macd_v1_real_evaluation_registry_truth_v2_complete() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    for scope in (text, section):
        assert _field_value(scope, "REAL_EVALUATION_PERFORMED") == "true"
        assert _field_value(scope, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "true"
        assert _field_value(scope, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
        assert _field_value(scope, "PROFITABILITY_CLAIM_ALLOWED") == "false"
        assert (
            _field_value(scope, "REAL_EVALUATION_INPUT_STATUS")
            == "MACD_V1_EVALUATION_V2_INVALIDATED_SIZING_ADMISSIBILITY_DEFECT"
        )
        assert _field_value(scope, "LAST_EVALUATED_STRATEGY_ID") == "macd"
        assert _field_value(scope, "LAST_EVALUATED_STRATEGY_VERSION") == "v1"
        assert _field_value(scope, "LAST_EVALUATED_CONFIG_VERSION") == "v2"


def test_macd_v1_real_evaluation_evidence_ref_bound() -> None:
    section = _step_29m_section(_read_registry())
    assert str(V2_EVIDENCE_DIR) in _field_value(section, "MACD_V1_REAL_EVALUATION_EVIDENCE_REF")
    assert str(INVALIDATED_EVIDENCE_DIR) in _field_value(section, "INVALIDATED_EVALUATION_REF")
    assert str(V2_EVIDENCE_DIR) in _field_value(section, "INVALIDATED_V2_EVALUATION_REF")


def test_macd_v1_v3_policy_registry_ratified_historical_and_breakout_next() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "OPERATOR_POLICY_DECISION") == "RATIFIED"
    assert _field_value(section, "POLICY_INVARIANT") == (
        "risk_per_trade <= max_position_pct * stop_pct"
    )
    assert _field_value(section, "NEXT_EVALUATION_STRATEGY_ID") == "breakout_donchian"
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_VERSION") == "v1"
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_STATUS") == (
        "POLICY_RATIFIED_CONFIG_ADMISSIBLE_AWAITING_SEPARATE_RUN"
    )
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_PATH") == (
        "config/ops/step29m_okx_inst_eth_usdt_perp_breakout_donchian_v1_economic_evaluation_v1.json"
    )
    assert _field_value(section, "ECONOMIC_REEVALUATION_ALLOWED") == "false"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "V2_CONFIG_DISPOSITION") == (
        "RETAIN_AS_NEGATIVE_INFEASIBILITY_FIXTURE"
    )
    assert _field_value(section, "V3_RISK_PER_TRADE") == "0.005"
    assert _field_value(section, "V3_REQUESTED_NOTIONAL_PCT") == "0.20"
    assert _field_value(section, "V3_FEASIBILITY_HEADROOM_PCT_OF_EQUITY") == "0.05"


def test_v2_config_file_digest_unchanged_for_negative_fixture() -> None:
    digest = hashlib.sha256(V2_CONFIG.read_bytes()).hexdigest()
    assert digest == EXPECTED_V2_FILE_SHA256


def test_v3_config_path_exists_with_expected_digest() -> None:
    assert V3_CONFIG.is_file()
    from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
        compute_evaluation_config_digest_v1,
    )

    cfg = json.loads(V3_CONFIG.read_text(encoding="utf-8"))
    assert compute_evaluation_config_digest_v1(cfg) == EXPECTED_V3_CONFIG_DIGEST


def test_macd_v1_real_evaluation_evidence_manifest_immutable() -> None:
    if not V2_EVIDENCE_DIR.is_dir():
        return
    summary = json.loads(
        (V2_EVIDENCE_DIR / "EVALUATION_RUN_SUMMARY.json").read_text(encoding="utf-8")
    )
    assert summary["REAL_EVALUATION_PERFORMED"] is True
    assert summary["ECONOMIC_VALIDITY_RESULT"] == "FAIL"
    assert summary["PROFITABILITY_CLAIM_ALLOWED"] is False
    assert summary["MANIFEST_VERIFY_RC"] == 0
    assert summary["LAST_EVALUATED_CONFIG_VERSION"] == "v2"
